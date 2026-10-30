# -*- coding: utf-8 -*-
"""核对：从 GPU 传回来的 `missing.npy`，能不能顶替本机那份？

**为什么在替换之前查，而不是替换之后**：替换是覆盖写，一旦传回来的文件有问题，
本机已算好的那 2048 行就没了。所以先比、再换。

**为什么这个检查比 `--check` 更强**：`--check` 验的是「协议一致」——12 条样本、
模型加载在同一个进程里。这里验的是**真实交付物**：58 MB 的文件，逐行比本机
已算过的那些行。跨设备（CUDA cuBLAS vs 本机 CPU BLAS）、跨 `transformers`
次版本（5.19.0 vs 5.18.0）、跨传输（scp）之后，结果还在不在。

判据：
  ① 形状 (14172, 1024)、dtype float32、无 NaN/Inf
  ② 每行 L2 范数 = 1（本脚本按 L2 归一化输出）
  ③ **已算范围内**（本机那份非零的行）逐行余弦 ≈ 1
  ④ 未算范围（本机那份全零的行）在新文件里**必须是真向量**，不是零

⚠️ ③ 的取样只能落在本机那份**已算过**的行内。取到未算区会拿到全零行，
   余弦恒为 0——那是「本机还没算」，不是「云端算错了」，两者不能混。
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORK = ROOT / "knowledge_base" / "vectors_incremental"
OLD = WORK / "missing.npy"
NEW = ROOT / "_probe" / "staging" / "missing_gpu.npy"

old = np.load(OLD, mmap_mode="r")
new = np.load(NEW, mmap_mode="r")
done = json.loads((WORK / "progress.json").read_text(encoding="utf-8"))["done"]
print("本机那份 %s（已算 %d 行）" % (old.shape, done))
print("云端那份 %s\n" % (new.shape,))

checks = []


def chk(name, ok, detail=""):
    checks.append((name, bool(ok)))
    print("  %s %s%s" % ("✅" if ok else "❌", name, ("  — " + detail) if detail else ""))


# ① 形状 / dtype / 非有限值
chk("形状 (14172, 1024)", new.shape == (14172, 1024), str(new.shape))
chk("dtype = float32", new.dtype == np.float32, str(new.dtype))

arr = np.asarray(new)                                    # 58 MB，读进内存没问题
chk("无 NaN / Inf", np.isfinite(arr).all())

# ② L2 范数
nrm = np.linalg.norm(arr, axis=1)
chk("每行 L2 范数 = 1", abs(nrm - 1).max() < 1e-5,
    "最大偏差 %.2e，最小 %.6f 最大 %.6f" % (abs(nrm - 1).max(), nrm.min(), nrm.max()))

# ③ 已算范围内逐行比（取样落在 [0, done)，且**去重**——重复文本看不出错位）
texts = [json.loads(l) for l in
         open(ROOT / "_probe" / "gpu_pack" / "missing_texts.jsonl", encoding="utf-8")]
step = max(1, done // 32)
idx, seen = [], set()
for i in range(0, done, step):
    if texts[i] in seen:
        continue
    seen.add(texts[i])
    idx.append(i)
cos = (np.asarray(new[idx]) * np.asarray(old[idx])).sum(axis=1)
chk("已算范围内 %d 行余弦 ≈ 1" % len(idx), (cos > 0.9999).all(),
    "min=%.8f mean=%.8f" % (cos.min(), cos.mean()))

# ④ 未算范围：本机那份是零，云端那份必须是真向量
tail = np.asarray(new[done:])
old_tail_zero = bool(np.abs(np.asarray(old[done:])).max() < 1e-9)
chk("本机未算区确实是零（对照成立）", old_tail_zero)
chk("云端补齐了未算区（无零行）",
    bool(np.abs(tail).max() > 1e-6) and not bool((np.linalg.norm(tail, axis=1) < 1e-6).any()),
    "补了 %d 行" % len(tail))

bad = sum(1 for _n, ok in checks if not ok)
print("\n%s" % ("全部通过（%d/%d）——可以替换" % (len(checks) - bad, len(checks))
                if not bad else "**有 %d 条不对，不要替换**" % bad))
raise SystemExit(1 if bad else 0)
