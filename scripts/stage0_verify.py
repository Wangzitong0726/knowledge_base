# -*- coding: utf-8 -*-
"""
阶段 0 验收：证明这个向量器**真的能用**，而不是"没报错"。

三关：
  关 1  语义近似度——同义/近义文本的相似度必须显著高于无关文本。
        这一关能抓住"pooling 取错位置""没归一化"这类静默故障：
        向量是常数或方向错乱时，三个相似度会挤在一起（≈0.99 或全乱）。
  关 2  padding 不变性——同一句话单独编码 vs 与长句同批编码，
        结果必须几乎一致。这一关专门抓"右 padding 导致 last-token 取到 pad"。
        这是我给 tokenizer 设 left padding 的理由，必须验证。
  关 3  吞吐量——真实长度的中文块，测块/秒，用来估全库耗时。
"""
import sys
import time
from pathlib import Path

import numpy as np

# 本机控制台默认 GBK，中文/符号会乱码甚至直接抛 UnicodeEncodeError。
# 统一强制 UTF-8 输出，别让编码问题伪装成程序错误。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed import Embedder

# 真实内存产业文本（不是造的玩具句）
A = "美国商务部工业与安全局发布最终规则，将高带宽内存（HBM）纳入出口管制清单，新增 ECCN 3A090.c。"
B = "BIS 出台新规，把 HBM 列入管制，管制门槛以内存带宽密度是否低于 3.3 GB/s/mm² 划定。"
C = "本公司 2026 年上半年营业收入较上年同期增长 12%，主要系存储产品出货量增加所致。"
D = "上海市生活垃圾管理条例自 2019 年 7 月 1 日起施行，单位未将生活垃圾分别投放的，责令改正。"

INSTRUCTION = "Given a web search query about semiconductor export controls and memory markets, retrieve relevant passages"


def cos(a, b):
    return float(np.dot(a, b))


def main():
    print("=" * 72)
    print("阶段 0 验收")
    print("=" * 72)
    e = Embedder()

    # ---------------- 关 1：语义近似度 ----------------
    print("\n--- 关 1 · 语义近似度 ---")
    docs = [A, B, C, D]
    V = e.encode(docs, batch_size=4)
    print(f"向量矩阵 {V.shape}  范数={np.linalg.norm(V, axis=1).round(6)}")

    ab, ac, ad = cos(V[0], V[1]), cos(V[0], V[2]), cos(V[0], V[3])
    print(f"\n  同一件事（管制 HBM 的两句不同说法）  sim(A,B) = {ab:.4f}")
    print(f"  同领域不同事（A vs 财报营收句）      sim(A,C) = {ac:.4f}")
    print(f"  完全无关（A vs 上海垃圾分类条例）    sim(A,D) = {ad:.4f}")

    ok1 = ab > ac > ad and (ab - ad) > 0.15
    spread = max(ab, ac, ad) - min(ab, ac, ad)
    print(f"\n  排序 A-B > A-C > A-D：{'✅ 成立' if ab > ac > ad else '❌ 不成立'}")
    print(f"  最大最小差 {spread:.4f}（>0.15 才算向量有分辨力）"
          f"：{'✅' if spread > 0.15 else '❌ 三值挤在一起，疑似向量退化'}")
    print(f"  关 1 判定：{'通过' if ok1 else '不通过'}")

    # ---------------- 关 2：padding 不变性 ----------------
    print("\n--- 关 2 · padding 不变性（抓 last-token 取错位置）---")
    # 必须测到**被 pad 的那一条**，不能只测最长的那条。
    # 旧版这一关只比了 A 一句，而 A 恰是组里最长、没被 pad 的，
    # 于是漏掉了「左 padding 用了右 padding 公式」的 bug——直到分桶自检才炸出来。
    group = [A, D, C, B]                     # 长度不一，必有短句被 pad
    solo = np.vstack([e.encode([t], batch_size=1)[0] for t in group])
    mixed = e.encode(group, batch_size=4, length_bucket=False)   # 一个 batch 里长短混排
    n_tok = [len(e.tok(t)["input_ids"]) for t in group]
    per = np.sum(solo * mixed, axis=1)       # 都已归一化
    longest = max(n_tok)
    for i in range(len(group)):
        tag = "最长(无 pad)" if n_tok[i] == longest else "被 pad"
        print(f"  第{i}条  {n_tok[i]:>3} token  {tag:<12}  cos = {per[i]:.8f}")
    ok2 = per.min() > 0.9999
    print(f"  关 2 判定："
          f"{'通过（长短混批不影响任何一条）' if ok2 else f'不通过 —— 最小 cos={per.min():.6f}，有序列取错位置了'}")

    # ---------------- 关 3：吞吐量 ----------------
    print("\n--- 关 3 · 吞吐量（估全库耗时）---")
    # 造 32 个真实长度（约 800 字）的中文块
    block = (A + B + C) * 3
    block = block[:800]
    corpus = [f"[第{i}块] {block}" for i in range(32)]
    e.encode(corpus[:2], batch_size=2)                 # 预热
    for bs in (4, 8, 16):
        t0 = time.time()
        e.encode(corpus, batch_size=bs)
        el = time.time() - t0
        rate = len(corpus) / el
        est = 14000 / rate / 60
        print(f"  batch={bs:2d}  {len(corpus)} 块 {el:.1f}s  →  {rate:5.1f} 块/秒"
              f"  →  1.4 万块约 {est:4.1f} 分钟")

    print("\n" + "=" * 72)
    print(f"结论：关 1 {'通过' if ok1 else '不通过'} / 关 2 {'通过' if ok2 else '不通过'}"
          f" / 关 3 见上")
    print("=" * 72)
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
