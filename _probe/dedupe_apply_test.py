# -*- coding: utf-8 -*-
"""在**副本**上真跑一遍 `dedupe_sources.py --apply`，验它改得对不对。

为什么非测不可：那个脚本之后要**无人值守地**改写 142MB 的 `chunks.jsonl` 和
335MB 的 `vectors.npy`。它的正确性条件是「块与向量的行序始终对齐」——
一旦错位，检索**不报错**，只会让每条引用指向隔壁块的出处。这种错没人会当场发现。
所以：拿一份小的合成语料，抄两个来源的同一份文件，跑 --apply，逐条核对。

判据：
  ① 该丢的行丢了（同一 sha256 下优先级低的那份来源）
  ② 其余行**一行不少、一行不动、顺序不变**
  ③ 向量按同一组下标切片（用「第 i 行向量的第 0 个分量 == 1000+i」这种哨兵验证）
  ④ 备份文件存在
  ⑤ 行数对齐（脚本自己的硬检查）
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

tmp = Path(tempfile.mkdtemp(prefix="dedupe_test_"))

# ── 造一份合成语料：44 对里的 2 对（巨潮 vs 深交所，同名不同 sha 的不同文件）──
SHA_A = "a" * 64
SHA_B = "b" * 64
rows = []
manifest = []


def add(doc_id, source, company, stem, sha, n):
    for i in range(n):
        rows.append({"doc_id": "%s/%s/%s" % (source, company, stem),
                     "source": source, "company": company, "text": "%s#%d" % (doc_id, i)})
        manifest.append({"source": source, "company": company,
                         "path": "data/raw/%s/%s/%s.pdf" % (source, company, stem),
                         "sha256": sha})


# 一对重复：cninfo 先入（应留），szse 后入（应丢）；文件名不同，sha 相同
add("cninfo", "cninfo", "兴森科技", "002436_2023年年度报告", SHA_A, 5)
add("szse", "szse", "兴森科技", "002436_兴森科技：2023年年度报告", SHA_A, 5)
# 一对重复：德明利
add("cninfo", "cninfo", "德明利", "001309_2025年半年度报告", SHA_B, 3)
add("szse", "szse", "德明利", "001309_德明利：2025年半年度报告", SHA_B, 3)
# 一份不重复的：必须原样留下
add("sec", "sec", "Micron", "mu-10k-2024", "c" * 64, 4)

chunks = tmp / "chunks.jsonl"
with open(chunks, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

man = tmp / "manifest.jsonl"
with open(man, "w", encoding="utf-8") as f:
    for m in manifest:
        f.write(json.dumps(m, ensure_ascii=False) + "\n")

# 哨兵向量：第 i 行第一个分量 = 1000+i，能一眼看出切口在哪
n = len(rows)
v = np.zeros((n, 4), dtype=np.float32)
for i in range(n):
    v[i, 0] = 1000 + i
vec = tmp / "vectors.npy"
np.save(vec, v)

print("合成语料：%d 块（其中 8 块属于两对重复），向量 %s" % (n, v.shape))

# ── 跑真脚本（--apply）──
r = subprocess.run([PY, str(ROOT / "scripts" / "dedupe_sources.py"),
                    "--chunks", str(chunks), "--vectors", str(vec),
                    "--manifest", str(man), "--apply"],
                   capture_output=True, encoding="utf-8", errors="replace")
print(r.stdout.strip()[-900:])
if r.returncode != 0:
    print("！退出码", r.returncode, r.stderr[-400:])

# ── 核对 ──
kept = [json.loads(l) for l in open(chunks, encoding="utf-8") if l.strip()]
newv = np.load(vec)
lost = n - len(kept)

ok = []
ok.append(("丢的行数 = 8（两对重复各 4 + 3，szse 侧）", lost == 8))
ok.append(("留下的里没有 szse 重复件",
           not any(x["source"] == "szse" and x["company"] in ("兴森科技", "德明利")
                   for x in kept)))
ok.append(("cninfo 重复件留下了",
           sum(1 for x in kept if x["source"] == "cninfo") == 8))
ok.append(("不重复的那份（Micron，4 块）原样留下",
           [x["text"] for x in kept if x["source"] == "sec"]
           == ["sec#%d" % i for i in range(4)]))
# 哨兵：留下的每行的向量第一个分量必须等于 1000+它原来在 rows 里的位置
pos = {json.dumps(x, ensure_ascii=False, sort_keys=True): i for i, x in enumerate(rows)}
ok.append(("向量与块**逐行对齐**（哨兵校验）",
           all(abs(newv[j, 0] - (1000 + pos[json.dumps(x, ensure_ascii=False, sort_keys=True)])) < 1e-3
               for j, x in enumerate(kept))))
ok.append(("向量行数 = 块行数", newv.shape[0] == len(kept)))
ok.append(("块顺序未变（仍是原序的子序）",
           [pos[json.dumps(x, ensure_ascii=False, sort_keys=True)] for x in kept]
           == sorted(pos[json.dumps(x, ensure_ascii=False, sort_keys=True)] for x in kept)))
ok.append(("备份文件已生成",
           len(list(tmp.glob("chunks.jsonl.bak_*"))) == 1
           and len(list(tmp.glob("vectors.npy.bak_*"))) == 1))

print()
for name, good in ok:
    print("  %s %s" % ("✅" if good else "❌", name))
bad = sum(1 for _n, g in ok if not g)
print("\n%s" % ("全部通过（%d/%d）" % (len(ok) - bad, len(ok)) if not bad else "**有 %d 条不对**" % bad))

shutil.rmtree(tmp, ignore_errors=True)
raise SystemExit(1 if bad else 0)
