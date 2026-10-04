# -*- coding: utf-8 -*-
"""验收：`knowledge_base/vectors.npy` 能不能被本机 CPU 重算出来。

**为什么要这个脚本**：库里那 335MB 向量是在云端 RTX 3090 上算的，
本机只验过「形状对、有归一化」。而 README/一页结论里写了一句
「云端 GPU 与本机 CPU 逐行余弦 min = 0.9999998」——**这句话当时没有任何留痕**，
属于本项目一路在打的「尺子错」。所以补一个能随时重跑的探针，把这句话
从「我记得」变成「可复现」。

**口径必须与全库一致，否则比出来的差异是假差异**：
  · max_length=2048（不是 embed.encode 的默认 1024——全库跑的是 2048）
  · fp32、last-token pooling、L2 归一化（都在 Embedder 里）
  · 嵌入的文本是 chunk 的 `text` **原文**，不加任何前缀
    （依据 embed_corpus.py: `texts = [r["text"] for r in rows]`）
  · 查 `vectors.npy[row]`——row 就是 chunks.jsonl 的行号

**抽样**：等间隔取 28 行（跨全部来源与长度）× 再加 4 个最长的块
（截断边界在最长处，必须覆盖）。
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

N_SAMPLE = 28


def main():
    rows = []
    with open(ROOT / "knowledge_base" / "chunks.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    N = len(rows)
    print(f"语料 {N:,} 块")

    idx = sorted(range(0, N, max(1, N // N_SAMPLE))[:N_SAMPLE])
    longest = sorted(range(N), key=lambda i: len(rows[i]["text"]))[-4:]
    idx = sorted(set(idx) | set(longest))
    print(f"抽样 {len(idx)} 行（含 4 个最长块，长度 "
          f"{min(len(rows[i]['text']) for i in idx)}–"
          f"{max(len(rows[i]['text']) for i in idx)} 字）")

    V = np.load(ROOT / "knowledge_base" / "vectors.npy", mmap_mode="r")
    print(f"vectors.npy  {V.shape}  {V.dtype}")

    from embed import Embedder
    e = Embedder()
    texts = [rows[i]["text"] for i in idx]
    t0 = time.time()
    got = e.encode(texts, batch_size=4, max_length=2048)
    print(f"CPU 重算 {len(texts)} 块，用时 {time.time()-t0:.1f}s")

    print()
    print(f"{'row':>8}  {'余弦':>10}  {'最大分量差':>12}  来源 / 标题")
    print("-" * 88)
    sims = []
    for k, i in enumerate(idx):
        a, b = got[k], np.asarray(V[i])
        sim = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
        dmax = float(np.abs(a - b).max())
        sims.append(sim)
        r = rows[i]
        print(f"{i:>8}  {sim:>10.8f}  {dmax:>12.3e}  "
              f"{r.get('source','?')}/{r.get('company') or '-'}/"
              f"{(r.get('title') or r.get('file') or '')[:34]}")

    sims = np.array(sims)
    print()
    print(f"余弦 min = {sims.min():.8f}   mean = {sims.mean():.8f}   "
          f"max = {sims.max():.8f}")
    print(f"逐位相同(余弦==1.0)的块：{int((sims == 1.0).sum())}/{len(sims)}")
    print(f"余弦 ≥ 0.9999 的块：{int((sims >= 0.9999).sum())}/{len(sims)}")
    ok = sims.min() >= 0.9999
    print()
    print("✓ 通过：本机 CPU 可复现云端向量" if ok
          else "✗ 不通过：两端向量不可比，全库向量的来源存疑")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
