# -*- coding: utf-8 -*-
"""本机 CPU 嵌入吞吐：抽**有代表性**的一批块（不是最长的那些），量块/秒。

上一版 parity 探针的样本被 8 个最长块(3800+字)拉低了，外推出的「全库 106 小时」
偏高。这里等间隔抽，字数分布贴近全库。

用法：
    ./.venv/Scripts/python.exe _probe/cpu_rate.py [抽多少块] [线程数]
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main(n_sample=64, threads=0):
    if threads:
        os.environ["OMP_NUM_THREADS"] = str(threads)
    import torch
    if threads:
        torch.set_num_threads(threads)

    rows = []
    with open(ROOT / "knowledge_base" / "chunks.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    step = max(1, len(rows) // n_sample)
    sample = rows[::step][:n_sample]
    lens = sorted(len(r["text"]) for r in sample)
    print("全库 %d 块；抽样 %d 块，字数 min=%d 中位=%d p90=%d max=%d"
          % (len(rows), len(sample), lens[0], lens[len(lens) // 2],
             lens[int(len(lens) * 0.9)], lens[-1]))

    from embed import Embedder
    e = Embedder()
    print("torch threads = %d" % torch.get_num_threads())
    t0 = time.time()
    e.encode([r["text"] for r in sample], batch_size=8, max_length=2048)
    dt = time.time() - t0
    rate = len(sample) / dt
    print("编码 %d 块用时 %.1f s → %.3f 块/秒" % (len(sample), dt, rate))
    for k in (5000, 14172, 25000, 81340):
        print("    %6d 块 ≈ %6.2f 小时" % (k, k / rate / 3600))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 64,
         int(sys.argv[2]) if len(sys.argv) > 2 else 0)
