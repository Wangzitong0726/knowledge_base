# -*- coding: utf-8 -*-
"""一次性：本机 CPU 能不能重算出云端那份向量？

`chunks.jsonl` 已被重切覆盖，而 `vectors.npy` 还是旧的——两者此刻**行号对不上**，
所以不能按行号比对。旧块的文本存在 `knowledge_base/index/chunks.sqlite` 里，
逐行哈希与留档一致（已验证），因此从 sqlite 取文本、按行号对 `vectors.npy`，
就是**旧的那一套配对**，正是要验的东西。

用法：
    ./.venv/Scripts/python.exe _probe/parity_now.py
"""
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from embed import Embedder  # noqa: E402

N_EVEN = 24          # 等间隔抽
N_LONG = 8           # 再加最长的几个（截断边界在最长处）


def main():
    con = sqlite3.connect(str(ROOT / "knowledge_base" / "index" / "chunks.sqlite"))
    texts = {r[0]: r[1] for r in con.execute("SELECT row, text FROM chunks")}
    n = len(texts)
    v = np.load(ROOT / "knowledge_base" / "vectors.npy")
    print("sqlite 块数 %d ；vectors.npy 形状 %s" % (n, v.shape))
    if v.shape[0] != n:
        raise SystemExit("行数对不上，后面的比对无意义")

    idx = list(range(0, n, max(1, n // N_EVEN)))[:N_EVEN]
    by_len = sorted(texts, key=lambda k: -len(texts[k]))[:N_LONG]
    idx = sorted(set(idx) | set(by_len))
    lens = [len(texts[i]) for i in idx]
    print("抽样 %d 块，字数 min=%d 中位=%d max=%d" % (
        len(idx), min(lens), sorted(lens)[len(lens) // 2], max(lens)))

    e = Embedder()
    t0 = time.time()
    got = e.encode([texts[i] for i in idx], batch_size=8, max_length=2048)
    dt = time.time() - t0
    print("CPU 编码 %d 块用时 %.1f s（%.2f 块/秒）" % (len(idx), dt, len(idx) / dt))

    cos = (got * v[idx]).sum(axis=1)          # 两边都已 L2 归一化
    print("\n与本机 CPU 重算的余弦：min=%.8f  mean=%.8f  max=%.8f" % (
        cos.min(), cos.mean(), cos.max()))
    worst = int(np.argmin(cos))
    print("最差一行：row=%d  字数=%d  余弦=%.8f" % (idx[worst], len(texts[idx[worst]]), cos[worst]))
    print("余弦 < 0.9999 的行数：%d" % int((cos < 0.9999).sum()))

    # 全库重算的耗时外推
    rate = len(idx) / dt
    print("\n外推：全库 %d 块 ≈ %.1f 小时；变更块按下一条命令的统计另算" % (n, n / rate / 3600))


if __name__ == "__main__":
    main()
