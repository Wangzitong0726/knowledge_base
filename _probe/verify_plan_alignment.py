# -*- coding: utf-8 -*-
"""核对：`vectors_incremental/missing.npy` 里已算好的行，**行序**还与冻结计划一致吗？

为什么非测不可：本次发现 `missing.npy` 的 mtime（10-12 22:39）**早于**
`chunks.jsonl` 的 mtime（10-12 22:45）。而 `missing` 的顺序是从 `chunks.jsonl`
推导的。若那份 `chunks.jsonl` 在 missing.npy 之后被重写过，则现在这份
missing.npy 的第 j 行，可能已经不是 `missing[j]` 的向量了。

这种错位**不报任何错**：检索照常返回结果，只是每条引用指向隔壁块的出处。
而且行数一样、形状一样，任何看数量/看形状的检查都发现不了。

判据（直接、不看形状）：
  取冻结计划 `_probe/missing_texts.jsonl` 里既在**已算范围**内、又**彼此不同**的若干条，
  本机重算它们的向量，与 missing.npy 对应行比余弦。
  同文本同向量（fp32、无随机性），所以对齐则余弦 ≈ 1.0；错位则明显低于 1。

样本**必须**落在「已算」的行号内（progress.json 的 done），否则取到的是
全零的未算区，会得到 0 余弦——那是「还没算」，不是「错位」，两者不能混。
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORK = ROOT / "knowledge_base" / "vectors_incremental"
N_SAMPLE = 12

plan = [json.loads(l) for l in
        open(ROOT / "_probe" / "gpu_pack" / "missing_texts.jsonl", encoding="utf-8")]
fp_want = (ROOT / "_probe" / "gpu_pack" / "missing_texts.jsonl.sha1"
           ).read_text(encoding="utf-8").strip()
done = json.loads((WORK / "progress.json").read_text(encoding="utf-8"))["done"]
mm = np.load(WORK / "missing.npy", mmap_mode="r")

print("冻结计划 %d 条；missing.npy %s；已算 %d 行" % (len(plan), mm.shape, done))
print("冻结指纹 %s…\n" % fp_want[:16])

if len(plan) != mm.shape[0]:
    raise SystemExit("！计划条数 %d ≠ missing.npy 行数 %d，直接不对" % (len(plan), mm.shape))

# 在「已算范围」内均匀取样，且**去重**——重复文本看不出错位（两条一样，比了也白比）
step = max(1, done // (N_SAMPLE * 3))
idx, seen = [], set()
for i in range(0, done, step):
    t = plan[i]
    if t in seen:
        continue
    seen.add(t)
    idx.append(i)
    if len(idx) >= N_SAMPLE:
        break
print("取样行号（均在已算范围内）：%s\n" % idx)

from embed import Embedder                                          # noqa: E402

e = Embedder(verbose=True)
got = e.encode([plan[i] for i in idx], batch_size=4, max_length=2048)
want = np.asarray(mm[idx])
cos = (got * want).sum(axis=1)

print()
for i, c in zip(idx, cos):
    print("  行 %5d  余弦 %.8f   %s" % (i, c, "✅" if c > 0.9999 else "❌"))
ok = bool((cos > 0.9999).all())
print("\n判定：%s" % ("✅ 行序对齐，missing.npy 与冻结计划一致，出机安全"
                      if ok else
                      "❌ 行序**不对齐**——这份 missing.npy 已过期，绝不能拿来续算或出机"))
raise SystemExit(0 if ok else 1)
