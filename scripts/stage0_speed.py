# -*- coding: utf-8 -*-
"""
阶段 0 速度诊断：0.8 块/秒 太慢，先查瓶颈，别急着认命。

要回答三个问题：
  1. 耗时随序列长度怎么变？——若近似线性，说明是算力受限（FFN 主导），
     缩短块长能直接换速度；若近似平方，说明 attention 主导，更该缩短。
  2. 这台 CPU 跑 fp32 到底多少 FLOPS？——用理论 FLOPs/实测秒数算出
     实际利用率。利用率正常说明代码没问题，是机器就这样；
     利用率很低说明还有优化空间。
  3. 量化 / bf16 能否换来数倍？——CPU 上 int8 动态量化常能拿 2-3 倍。
"""
import sys
import time
from pathlib import Path

import numpy as np
import torch

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed import Embedder, MODEL_DIR

N_PARAMS = 596e6


def bench(e, texts, batch_size, warm=True):
    if warm:
        e.encode(texts[:batch_size], batch_size=batch_size)
    t0 = time.time()
    e.encode(texts, batch_size=batch_size)
    return time.time() - t0


def main():
    print("=" * 76)
    print("阶段 0 速度诊断")
    print("=" * 76)
    print(f"torch {torch.__version__}  线程 {torch.get_num_threads()}  "
          f"机器核数 {torch.get_num_threads()}")
    try:
        print(f"CPU 支持：AVX2={torch.backends.cpu.get_cpu_capability()}")
    except Exception as ex:
        print(f"CPU 能力查询不可用：{ex}")

    e = Embedder()
    tok_len = lambda s: len(e.tok(s)["input_ids"])
    sample = "美国商务部工业与安全局发布最终规则，将高带宽内存纳入出口管制清单，新增 ECCN 3A090.c，管制门槛以内存带宽密度划定。" * 40

    # ---------- 1. 序列长度 → 速度 ----------
    print("\n--- 1 · 耗时 vs 序列长度（batch=8，各 16 条）---")
    print(f"{'目标字数':>8} {'实际token':>10} {'秒':>8} {'块/秒':>8} {'TFLOPS':>8} {'占比':>7}")
    base = None
    rows = []
    for chars in (100, 200, 400, 800, 1600):
        txt = sample[:chars]
        n = tok_len(txt)
        corpus = [txt] * 16
        el = bench(e, corpus, 8)
        rate = 16 / el
        # FLOPs ≈ 2 * N * tokens（前向）
        tflops = 2 * N_PARAMS * n * 16 / el / 1e12
        rows.append((chars, n, el, rate, tflops))
        print(f"{chars:>8} {n:>10} {el:>8.1f} {rate:>8.2f} {tflops:>8.3f} "
              f"{'—' if base is None else f'{rate/base:.2f}x':>7}")
        if base is None:
            base = rate

    print("\n  读法：若『块/秒』随 token 数近似**反比**（占比每加倍长度掉一半），")
    print("       说明算力受限、非平方复杂度主导 → 缩短块长可线性提速。")

    # ---------- 2. 量化对比 ----------
    print("\n--- 2 · fp32 vs bf16 vs int8 动态量化（800 字块，batch=8，16 条）---")
    txt = sample[:800]
    corpus = [txt] * 16
    n = tok_len(txt)
    results = {}

    el = bench(e, corpus, 8)
    results["fp32"] = (el, 16 / el, 2 * N_PARAMS * n * 16 / el / 1e12)
    print(f"  fp32（当前）      {el:7.1f}s  {16/el:6.2f} 块/秒  {results['fp32'][2]:6.3f} TFLOPS")

    # bf16
    try:
        e16 = Embedder(dtype=torch.bfloat16, verbose=False)
        el = bench(e16, corpus, 8)
        results["bf16"] = (el, 16 / el, 2 * N_PARAMS * n * 16 / el / 1e12)
        print(f"  bf16              {el:7.1f}s  {16/el:6.2f} 块/秒  {results['bf16'][2]:6.3f} TFLOPS")
        del e16
    except Exception as ex:
        print(f"  bf16 失败：{type(ex).__name__}: {str(ex)[:60]}")

    # int8 动态量化（只量化 Linear，CPU 上通常 2-3 倍）
    try:
        import copy
        q = copy.deepcopy(e)
        q.model = torch.ao.quantization.quantize_dynamic(
            q.model, {torch.nn.Linear}, dtype=torch.qint8)
        el = bench(q, corpus, 8)
        results["int8"] = (el, 16 / el, 2 * N_PARAMS * n * 16 / el / 1e12)
        print(f"  int8 动态量化     {el:7.1f}s  {16/el:6.2f} 块/秒  "
              f"（相对 fp32 {results['fp32'][0]/el:.2f}x 提速）")
    except Exception as ex:
        print(f"  int8 失败：{type(ex).__name__}: {str(ex)[:80]}")

    # ---------- 3. 结论 ----------
    print("\n--- 3 · 按 1.4 万块估算全库耗时 ---")
    for k, (el, rate, tf) in results.items():
        print(f"  {k:6s}  {14000/rate/60:6.1f} 分钟")
    print("\n  注意：以上都是 800 字满长块。真实语料块长参差，")
    print("        若同一 batch 内长短混杂，padding 会浪费算力——")
    print("        建索引时应按长度分桶（sort by length）再分批。")


if __name__ == "__main__":
    main()
