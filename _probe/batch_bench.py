# -*- coding: utf-8 -*-
"""基准：**线程数**与**批大小**对吞吐的影响（在本机这颗 CPU 上）。

动机：`embed.py:53` 无条件设 `torch.set_num_threads(os.cpu_count())`。
本机 os.cpu_count() = **16**，但物理核只有 **8**（Ryzen 7 5800U，8C16T，15W 低压 U）。
往 8 个核上开 16 个计算线程 = 超线程打架，GEMM 类负载上常常**更慢**。
这个脚本量它，不猜。

模型只载入一次（重复载入既慢又吃内存，本机只剩 5.7GB 可用）；
`torch.set_num_threads` 可在运行中改，改完对后续算子立即生效。

样本是 `_probe/missing_texts.jsonl` 里**真实待算**的前 32 条，不是造的数据。
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import torch                                                       # noqa: E402

TEXTS = [json.loads(l) for l in
         open(ROOT / "_probe" / "gpu_pack" / "missing_texts.jsonl",
              encoding="utf-8")][:32]
NTOTAL = 14172
print("样本 %d 条，平均 %.0f 字符，最长 %d 字符"
      % (len(TEXTS), sum(map(len, TEXTS)) / len(TEXTS), max(map(len, TEXTS))))
print("物理核 8 / 逻辑核 %d\n" % (torch.get_num_threads() * 2 or 16))

from embed import Embedder                                         # noqa: E402

e = Embedder(verbose=True)                                         # 载入一次
print()

base = None
for nthread, b in ((16, 8), (8, 8), (8, 16), (8, 32), (4, 8)):
    torch.set_num_threads(nthread)
    e.encode(TEXTS[:8], batch_size=8, max_length=2048)             # 预热，不计时
    t0 = time.time()
    e.encode(TEXTS, batch_size=b, max_length=2048)
    el = time.time() - t0
    rate = len(TEXTS) / el
    if base is None:
        base = rate
    print("  线程 %2d  BATCH %-3d  %6.1fs  →  %.3f 块/秒  （相对首行 %+.0f%%）"
          "  全库 14172 条 = %5.1f 小时"
          % (nthread, b, el, rate, 100 * (rate / base - 1), NTOTAL / rate / 3600),
          flush=True)
