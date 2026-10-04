# -*- coding: utf-8 -*-
"""
阶段 3 ② · BM25 索引（**本机 CPU 建，不用 GPU**）

为什么知识库要同时有向量和 BM25：两者**失败的方式不一样**，
所以「一起用」不是保险，是覆盖面互补。

  · 向量按语义召回 —— 问「管制门槛是多少」能召回写着 `2 GB/s/mm²` 的段，
    但它会把 `3A090.c` 和 `3A001` 认成近亲（都是「出口管制编号」），
    也会把 `2 GB/s/mm²` 和 `3.3 GB/s/mm²` 看成几乎一样（数字在语义空间里很弱）。
  · BM25 按字面命中 —— 查 `3A090` 只会回含 `3A090` 的块，**不会回 3A001**；
    查 `3.3` 不会回 `2`。但问「为什么韩国厂商难受」它一个都召不回。

本课件的口径里，**数字和型号就是论文的论点**，认错了等于论点错。
所以型号/阈值这类查询必须以 BM25 的**字面**为准，向量的语义近似反而危险——
这不是「哪个更好」，是**两类查询走两条路**。

三条实现约束（都是踩过的）：

1. **中文走 jieba，型号/英文/数字走正则整体保留，绝不交给 jieba**。
   jieba 会把 `3A090` 切成 `3` / `A` / `090`，把 `HBM3E` 切成 `HBM` / `3` / `E`——
   那么查 `3A090` 就召回了所有含「3」的块（等于没过滤），
   而 `3A001` 与 `3A090` 反而互相命中。**关键型号必须原子化。**

   ⚠️ 这条**第一次实现时做错了，而且错得看不出**：我用 `\x00` 把型号包起来、
   再按 `\x00` 切分，本意是「型号段留着、其余走英文正则」，实际却把型号段也送进了
   英文正则 —— `3A090` 里没有「连续 2 个字母」，正则返回空，**整个型号被静默丢弃**。
   症状：`tokenize('3A090') == []`、`tokenize('HBM3E') == ['hbm']`（丢了 `3E`）。
   索引照建、检索照出结果，只是**查 3A090 永远召不回 3A090**。
   修法：`_TOKEN` 一条正则交替匹配三类原子，用 `lastgroup` 分流，**不做字符串拼接与再切分**。

2. **不用 scipy**（本机没装，也不必装）。倒排表手搓成 numpy 的 CSR-by-term：
   三个平行数组 `term_ptr` / `doc_idx` / `term_tf`。81589 块的库用不着稀疏矩阵库。

3. **重合块要在检索层去重**。切块是 800 字 / 重合 120 字，
   相邻块本来就共享文字，一个答案会连着占满 top-k。
   去重键取 `(doc_id, 页区间重叠)` —— 同一份文件、页相邻的结果只留分最高的那条。
"""
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "knowledge_base" / "chunks.jsonl"
OUTDIR = ROOT / "knowledge_base" / "index"

K1 = 1.5
B = 0.75

# ── 切词 ────────────────────────────────────────────────────────────
_CJK = r"一-鿿㐀-䶿"

# 三类原子，**一次扫描**取出，顺序即优先级。
#   model：含数字的混排整段（3A090、HBM3E、DDR5-5600、774.1、10-K）
#   unit ：斜杠连写的单位（GB/s/mm、m/s）—— `²` 不在类里，会被丢掉，无所谓
#   word ：普通英文词
_TOKEN = re.compile(r"""
    (?P<model>[A-Za-z0-9][A-Za-z0-9\-\./_]*(?:\d[A-Za-z0-9\-\./_]*)+)
  | (?P<unit>[A-Za-z]{1,8}(?:/[A-Za-z]{1,8})+)
  | (?P<word>[A-Za-z]{2,})
""", re.X)

# 型号里的**字母前缀**，用来补一条召回路径（见 _keep_model 下方说明）
_ALPHA_PREFIX = re.compile(r"^([A-Za-z]{2,})(?=\d)")


def _keep_model(tok):
    """这个「型号」原子值不值得进词表。

    ⚠️ `_TOKEN` 的 model 分支同时匹配**纯数字**（`89`、`2024`、`96790`），
    因为分不清「`89 FR` 里的 89」和表里的「89」是同一个正则——**一律留下会把
    财务报表里成千上万的裸数字灌进索引**，idf 全被拉平，检索质量反降。
    所以只留三类：含字母（3a090、hbm3e）、含小数点（3.3、774.1）、
    长到不像普通账面数字的纯数字（FR 引文 96790、份号 0000723125）。
    **代价写在这里：单独一个 `2` 不进词表。** 所以「阈值 2」和「例外 3.3」
    不能靠查数字区分——`3.3` 可查，`2` 不可查。
    想反查例外通道那一支，查 `3.3`；想拿管制门槛，查 `bandwidth`/`density`/`带宽 密度`
    再由块内原文给出数字。**数字必须由原文提供，系统不许自己补**，这一条不影响该纪律。
    """
    if any(ch.isalpha() for ch in tok):
        return True
    if "." in tok:
        return True
    if not tok.isdigit():
        return False
    # 年份单独放行：本课题是**时间序列**的（管制生效 12-02 / 公布 12-05 /
    # HBM 合规 12-31），年-月不能一起丢。年份 df 大、idf 低，
    # 只在查询本身带年份时才计分，加了它不会污染不带年份的查询。
    return len(tok) >= 5 or 1900 <= int(tok) <= 2099


def _tokens_non_cjk(seg):
    out = []
    for m in _TOKEN.finditer(seg):
        tok = m.group(0).lower()
        if m.lastgroup != "model":
            out.append(tok)
            continue
        if not _keep_model(tok):
            continue
        out.append(tok)
        # 型号**还额外发一遍字母前缀**，否则会丢召回：
        # `HBM3E` 整段成一个原子后，含 `HBM3E` 的块词表里就**没有 `hbm`**，
        # 于是查「HBM」召回不到它们——而「HBM」恰恰是论文里最常用的那个词。
        # `hbm3e` → 另发 `hbm`；`ddr5-5600` → 另发 `ddr`（无害，`ddr5` 仍在，照样能区分代际）。
        pre = _ALPHA_PREFIX.match(tok)
        if pre:
            out.append(pre.group(1).lower())
    return out

# ⚠️ 这些词在库里出现在**每个**块里（页眉、页脚、「第X节」），idf 近 0 但不为 0，
# 会在查询里贡献一堆噪声分。直接进停用表，比靠 idf 自然压制更干净。
STOP = set("""
的 了 和 与 及 在 是 为 对 有 不 也 等 中 上 下 之 其 该 本 各 这 那 年 月 日 元 万元 亿元
company the and for of to in a an is are was were be been on at by with as or from that this
these those it its we our us they their he she his her not no all any may can will would could
""".split())


def tokenize(text):
    """中文 jieba + 型号/英文原子化。返回 list[str]（已小写、已过滤）。"""
    import jieba
    out = []
    # 先按「中文段」切成若干片段，非中文段交给型号/英文正则
    for seg in re.split(rf"([{_CJK}]+)", text):
        if not seg:
            continue
        if re.fullmatch(rf"[{_CJK}]+", seg):
            out.extend(w for w in jieba.cut(seg) if w.strip())
        else:
            out.extend(_tokens_non_cjk(seg))
    return [w for w in (t.strip().lower() for t in out) if w and w not in STOP]


# ── 建索引 ──────────────────────────────────────────────────────────
def _load_chunks():
    rows = []
    with open(CHUNKS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build(force=False, verbose=True):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    tok_cache = OUTDIR / "_tokens.txt"          # 切词结果缓存：重跑不必再切一遍 jieba
    meta_path = OUTDIR / "bm25_meta.json"

    rows = _load_chunks()
    n_doc = len(rows)
    doc_ids = [r["chunk_id"] for r in rows]
    t0 = time.time()

    # ── 第一遍：切词 + 词频统计 ──
    df = Counter()
    if force or not tok_cache.exists():
        if verbose:
            print(f"切词 {n_doc:,} 块 …")
        with open(tok_cache, "w", encoding="utf-8") as f:
            for i, r in enumerate(rows):
                toks = tokenize(r["text"])
                for t in set(toks):
                    df[t] += 1
                f.write(" ".join(toks) + "\n")
                if verbose and (i + 1) % 20000 == 0:
                    print(f"  {i+1:,}/{n_doc:,}  词表 {len(df):,}")
    else:
        if verbose:
            print("复用切词缓存，只重算 df …")
        with open(tok_cache, encoding="utf-8") as f:
            for line in f:
                for t in set(line.split()):
                    df[t] += 1
    if verbose:
        print(f"  切词完成 {time.time()-t0:.0f}s，候选词 {len(df):,}")

    # 词表过滤：只留出现 ≥2 次的。
    # ⚠️ 别把「只出现 1 次的型号」也砍掉——3A090 这类词出现次数不少，不受影响；
    # 而真正的 hapax 多是抽取噪声（乱码、断词残片），留着只增体积不增召回。
    # 但**长度 1 的中文单字**要砍：`的` `和` 之外的大量单字是 jieba 的过度切分。
    vocab_terms = sorted(t for t, c in df.items() if c >= 2 and len(t) > 1)
    vocab = {t: i for i, t in enumerate(vocab_terms)}
    V = len(vocab)
    if verbose:
        print(f"  词表 {V:,}（df≥2 且长度>1）")

    # ── 第二遍：填倒排表（term-major，即按词号排）──
    # 先估 nnz：每块去重后的词数之和
    est = 0
    with open(tok_cache, encoding="utf-8") as f:
        for line in f:
            est += len(set(line.split()))
    if verbose:
        print(f"  非零项约 {est:,}")

    cap = int(est * 1.1) + 1024
    a_term = np.empty(cap, dtype=np.int32)
    a_doc = np.empty(cap, dtype=np.int32)
    a_tf = np.empty(cap, dtype=np.int32)
    pos = 0

    def grow(need):
        nonlocal cap, a_term, a_doc, a_tf
        if need <= cap:
            return
        new = max(cap * 2, need)
        for name in ("a_term", "a_doc", "a_tf"):
            old = locals()[name]
            arr = np.empty(new, dtype=np.int32)
            arr[:pos] = old[:pos]
            if name == "a_term":
                a_term = arr
            elif name == "a_doc":
                a_doc = arr
            else:
                a_tf = arr
        cap = new

    with open(tok_cache, encoding="utf-8") as f:
        for d, line in enumerate(f):
            cnt = Counter(t for t in line.split() if t in vocab)
            grow(pos + len(cnt))
            for t, c in cnt.items():
                a_term[pos] = vocab[t]
                a_doc[pos] = d
                a_tf[pos] = c
                pos += 1
    a_term, a_doc, a_tf = a_term[:pos], a_doc[:pos], a_tf[:pos]
    if verbose:
        print(f"  倒排表 {pos:,} 项，{time.time()-t0:.0f}s")

    # 按词号排序 → 得到 CSR-by-term（term_ptr / doc_idx / term_tf）
    order = np.argsort(a_term, kind="stable")
    term_arr, doc_arr, tf_arr = a_term[order], a_doc[order], a_tf[order]
    df_arr = np.bincount(term_arr, minlength=V).astype(np.int32)
    term_ptr = np.zeros(V + 1, dtype=np.int64)
    np.cumsum(df_arr, out=term_ptr[1:])

    # 块长度（按 token 数）——BM25 的长度归一化用
    doclen = np.zeros(n_doc, dtype=np.int32)
    with open(tok_cache, encoding="utf-8") as f:
        for d, line in enumerate(f):
            doclen[d] = len(line.split())

    np.savez(OUTDIR / "bm25.npz",
             term_ptr=term_ptr, doc_idx=doc_arr.astype(np.int32),
             term_tf=tf_arr.astype(np.int32), doclen=doclen,
             df=df_arr)
    with open(OUTDIR / "bm25_vocab.json", "w", encoding="utf-8") as f:
        json.dump({"terms": vocab_terms, "n_doc": n_doc}, f, ensure_ascii=False)
    with open(OUTDIR / "bm25_docs.json", "w", encoding="utf-8") as f:
        json.dump(doc_ids, f, ensure_ascii=False)

    meta = {
        "n_doc": n_doc, "n_term": V, "nnz": int(pos),
        "avgdl": float(doclen.mean()), "k1": K1, "b": B,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seconds": round(time.time() - t0, 1),
    }
    (OUTDIR / "bm25_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    if verbose:
        print(f"✓ 索引写入 {OUTDIR}，用时 {meta['seconds']}s")
        print(f"  参数 k1={K1} b={B} avgdl={meta['avgdl']:.1f} token/块")
    return meta


# ── 检索 ────────────────────────────────────────────────────────────
class BM25:
    def __init__(self, index_dir=None, verbose=False):
        d = Path(index_dir) if index_dir else OUTDIR
        z = np.load(d / "bm25.npz")
        self.term_ptr, self.doc_idx = z["term_ptr"], z["doc_idx"]
        self.term_tf, self.doclen, self.df = z["term_tf"], z["doclen"], z["df"]
        v = json.loads((d / "bm25_vocab.json").read_text(encoding="utf-8"))
        self.terms, self.n_doc = v["terms"], v["n_doc"]
        self.vocab = {t: i for i, t in enumerate(self.terms)}
        self.doc_ids = json.loads((d / "bm25_docs.json").read_text(encoding="utf-8"))
        m = json.loads((d / "bm25_meta.json").read_text(encoding="utf-8"))
        self.avgdl, self.k1, self.b = m["avgdl"], m["k1"], m["b"]
        # idf：加 0.5 平滑，再取 log。df 越大 idf 越小，命中它贡献越小。
        self.idf = np.log(1.0 + (self.n_doc - self.df + 0.5) / (self.df + 0.5))

    def _postings(self, term):
        i = self.vocab.get(term)
        if i is None:
            # ⚠️ 必须回**三个** None：调用方按三值解包，少一个就 ValueError。
            # 这条路径早先的测试从没跑到过——测的都是「词一定在词表里」的查询，
            # 于是「查询里有个词不在词表」这一**最常见的真实情况**一上来就崩。
            return None, None, None
        s, e = self.term_ptr[i], self.term_ptr[i + 1]
        return self.doc_idx[s:e], self.term_tf[s:e], self.idf[i]

    def search(self, query, k=10, dedup=True, pool=200):
        """返回 [(chunk_id, score, matched_terms), ...]，分高在前。

        pool 是去重前先取的前若干条；去重会把相邻页的重复块压掉，
        所以先多取一些再裁到 k，否则 top-10 可能被去重削到只剩 3 条。
        """
        toks = tokenize(query)
        if not toks:
            return []
        # 同一个词查两次不该算两次分
        seen_t, uniq = set(), []
        for t in toks:
            if t not in seen_t:
                seen_t.add(t)
                uniq.append(t)

        scores, hit = {}, {}
        for t in uniq:
            docs, tfs, idf = self._postings(t)
            if docs is None:
                continue
            dl = self.doclen[docs].astype(np.float32)
            denom = tfs + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            s = idf * (tfs * (self.k1 + 1)) / denom
            for d, sv in zip(docs, s):
                d = int(d)
                scores[d] = scores.get(d, 0.0) + float(sv)
                hit.setdefault(d, []).append(t)
        if not scores:
            return []
        top = sorted(scores.items(), key=lambda x: -x[1])[:pool]
        out = [(self.doc_ids[d], s, hit[d]) for d, s in top]
        if dedup:
            out = _dedup_adjacent(out)
        return out[:k]


def _dedup_adjacent(results):
    """把「同一份文件、页区间相接」的重复块压掉，留分最高的那条。

    为什么必须做：切块重合 120 字，且长文档一页会被切成 2–3 块，
    于是同一个答案的相邻块会同时进 top-k，把别的候选全挤出去——
    看着是「召回了 10 条」，其实只有 2 条独立信息。
    """
    kept, seen = [], []
    for cid, s, terms in results:
        doc = cid.split("::")[0]
        seq = int(cid.split("::")[1])
        if any(d == doc and abs(q - seq) <= 2 for d, q in seen):
            continue
        seen.append((doc, seq))
        kept.append((cid, s, terms))
    return kept


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build(force="--force" in sys.argv)
    else:
        q = " ".join(sys.argv[1:]) or "3A090 memory bandwidth density"
        eng = BM25()
        print(f"\n查询：{q}")
        print(f"切词：{tokenize(q)}\n")
        for cid, s, terms in eng.search(q, k=10):
            print(f"  {s:8.3f}  {cid}")
            print(f"           命中 {terms}")
