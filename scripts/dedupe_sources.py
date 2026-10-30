# -*- coding: utf-8 -*-
"""语料去重：同一份文件被两个官方来源各取一次时，只留一份。

**为什么非做不可**（实测，见 `outputs/来源清单.md` 第三节）：
`data/manifest.jsonl` 里有 44 份文件同时挂在 `cninfo`（巨潮资讯网）与 `szse`（深交所）下，
**文件字节与 sha256 完全相同**——是同一份 PDF 从两个官网各下了一次。
落到切块上是 **13,960 块逐字重复，占全库 17.0%**。

它们造成的害处不是「多占点磁盘」：

  · **出处会骗人**。同一段话以两个「官方来源」出现，看起来像是两份**独立**材料
    互相印证，其实是同一份。这正好踩在老师那句「**先核对口径与出处**」上。
  · **席位被浪费**。`DOC_CAP` 限的是「同一份**文件**」，而两份副本的 `doc_id` 不同，
    限不住——一套席位里可能有两席是同一段话。
  · **公司被虚胖**。按公司统计块数时，这 7 家公司凭空多出一倍（如兴森科技 2,635 → 1,317）。

去重键：**文件内容的 sha256**（经 `data/manifest.jsonl` 把 `doc_id` 对回去）。
⚠️ 不能按文件名归并——两份副本的**文件名本身也不同**（见 `build_sha_map` 的注释）。
同一枚 sha256 下若有多个来源，只留 `SOURCE_PRIORITY` 里靠前的那个。

**为什么留 cninfo 不留 szse**：巨潮资讯网是深交所**指定**信息披露网站，
`static.cninfo.com.cn` 是公告的正规发布地址；深交所站上是同一份文件。
两者都是官方的，这里不是判「谁更权威」，而是**同一份材料只该登记一次**。

⚠️ **占用与顺序**：
   1. 必须在 `scripts/build_vectors_reuse.py` **跑完之后**再跑——那个脚本用 mmap 读
      `vectors.npy`，中途换文件会让它写不出去（Windows 上文件被占用）。
   2. 跑完必须用 `build_store.py --force` 重建 `chunks.sqlite`，
      否则 sqlite 行数仍是旧的，检索会**错位**（错位的向量不报错，只会让答案引到隔壁块）。
   3. 跑完**还必须** `bm25.py build --force` 重建字面索引。
      ⚠️ 这一条是 2026-10-30 补的：2026-10-15 那次 `--apply` 只重建了 sqlite，
      BM25 停在 81,895 块的旧语料上，于是「旧文本的 BM25 + 新语料的向量」一起跑了
      十道题（索引里 14,948 个块已不存在，现行语料里 263 块不在索引里）。
      **对账脚本：`scripts/checks/t_index_consistency.py`**——四份产物行数/ID 不一致就报错。

用法：
    C:/Python314/python.exe scripts/dedupe_sources.py              # 只报账，不动文件
    C:/Python314/python.exe scripts/dedupe_sources.py --apply       # 真改（先备份）
"""
import argparse
import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "knowledge_base" / "chunks.jsonl"
VECTORS = ROOT / "knowledge_base" / "vectors.npy"
MANIFEST = ROOT / "data" / "manifest.jsonl"

# 同一份文件有多个来源时留哪个。靠前的赢。
SOURCE_PRIORITY = ("cninfo", "szse", "sec", "samsung", "skhynix",
                   "fedreg", "ecfr", "govinfo")


def build_sha_map(manifest_path=None):
    """`doc_id → sha256`，经由 manifest 对回去。

    **为什么不能按文件名分组**（第一版就是这么写的，一组都没分出来）：两份副本
    **文件名也不一样**——巨潮那份叫 `002436_2024-04-25_2023年年度报告.pdf`，
    深交所那份叫 `002436_2024-04-25_兴森科技：2023年年度报告.pdf`（前缀挂了公司名）。
    **文件名是下载时按站点规矩起的，不是文件的性质**；文件的性质是 sha256。
    这跟「拿正则去剥型号」是同一个坑：把假设的命名规矩当成事实。

    chunk 的 `doc_id` 是 `来源/公司/文件名主干`，manifest 的 `path` 是
    `data/raw/来源/公司/文件名.pdf`，两边正好对得上。对不上的 doc_id 记下来报账，
    不猜、不静默丢弃。

    ⚠️ 这个键的**全部依据都在 manifest 里**，所以路径必须可覆盖
       （`--manifest`）：否则拿一份合成语料去测，键永远对不上、
       脚本报「0 份重复」并放行——看着像「本来就没有重复」。
       这不是假设出来的场景，是 `_probe/dedupe_apply_test.py` 实测撞到的。
    """
    m = {}
    with open(manifest_path or MANIFEST, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            m["%s/%s/%s" % (r["source"], r["company"], Path(r["path"]).stem)] = r["sha256"]
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=str(CHUNKS))
    ap.add_argument("--vectors", default=str(VECTORS))
    ap.add_argument("--manifest", default=str(MANIFEST),
                    help="去重键的依据（doc_id → sha256）；测试时可换一份合成 manifest")
    ap.add_argument("--apply", action="store_true", help="真写文件（默认只报账）")
    args = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    chunks = Path(args.chunks)
    rows = [json.loads(l) for l in open(chunks, encoding="utf-8") if l.strip()]
    print("读入 %d 块" % len(rows))

    # ── 按**内容 sha256** 归并（不是按文件名）──
    sha_map = build_sha_map(args.manifest)
    by_sha = defaultdict(lambda: defaultdict(list))
    docs_of = defaultdict(set)
    missing = set()
    for i, r in enumerate(rows):
        d = r.get("doc_id") or ""
        s = sha_map.get(d)
        if s is None:
            missing.add(d)                 # 报账，不静默丢
            continue
        by_sha[s][r.get("source") or ""].append(i)
        docs_of[s].add(d)
    if missing:
        print("！%d 个 doc_id 在 manifest 里对不上 sha256，这些块原样保留：" % len(missing))
        for d in sorted(missing)[:5]:
            print("    %s" % d)

    drop, keep_plan = set(), []
    n_multi = 0
    for sha, bysrc in sorted(by_sha.items()):
        if len(bysrc) < 2:
            continue
        n_multi += 1
        order = sorted(bysrc, key=lambda s: (SOURCE_PRIORITY.index(s)
                                             if s in SOURCE_PRIORITY else 99, s))
        win = order[0]
        for lose in order[1:]:
            drop |= set(bysrc[lose])
            keep_plan.append((sha, lose, win, len(bysrc[lose]), sorted(docs_of[sha])))

    print("同一份文件有多个来源的：%d 份；涉及要丢的块 %d 块（占 %.1f%%）"
          % (n_multi, len(drop), 100.0 * len(drop) / max(len(rows), 1)))
    from collections import Counter
    c = Counter(l for _s, l, _w, _n, _d in keep_plan)
    print("  丢掉的来源分布：%s" % dict(c))
    for sha, l, w, n, docs in keep_plan[:6]:
        print("    sha256 %s…  丢 %s（%d 块），留 %s" % (sha[:16], l, n, w))
        print("        同一份文件的两个 doc_id：%s" % "  ｜  ".join(docs))
    if len(keep_plan) > 6:
        print("    …共 %d 条" % len(keep_plan))

    kept = [r for i, r in enumerate(rows) if i not in drop]
    print("去重后 %d 块（减 %d）" % (len(kept), len(rows) - len(kept)))

    if not args.apply:
        print("\n（只报账。加 --apply 才真改。）")
        return 0

    # 向量行数与块行数必须一致，否则不动——宁可不去重，也不许错位
    vec = Path(args.vectors)
    if vec.exists():
        shape = np.load(vec, mmap_mode="r").shape
        if shape[0] != len(rows):
            print("！向量 %d 行 ≠ 块 %d 行，拒绝去重。先跑 build_vectors_reuse.py。"
                  % (shape[0], len(rows)))
            return 2

    idx = np.array(sorted(set(range(len(rows))) - drop), dtype=np.int64)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(chunks, chunks.with_suffix(".jsonl.bak_" + stamp))
    print("已备份 %s" % chunks.with_suffix(".jsonl.bak_" + stamp).name)

    tmp = chunks.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(chunks)

    if vec.exists():
        v = np.load(vec, mmap_mode="r")
        shape = (len(idx), v.shape[1])
        out = np.empty(shape, dtype=v.dtype)
        for s in range(0, len(idx), 20000):        # 分块取，别一次把 260MB 读进内存再写一遍
            blk = idx[s:s + 20000]
            out[s:s + len(blk)] = np.asarray(v[blk])
        del v
        shutil.copy2(vec, vec.with_suffix(".npy.bak_" + stamp))
        tmpv = Path(str(vec) + ".tmp")
        with open(tmpv, "wb") as fh:
            np.save(fh, out)                       # np.save(路径) 会补 `.npy`，这里传文件对象
        del out
        tmpv.replace(vec)
        got = np.load(vec, mmap_mode="r").shape[0]
        print("已备份 %s 并写出去重后的向量 %s" % (vec.name + ".bak_" + stamp, shape))
        print("核对：向量 %d 行 = 块 %d 行 → %s"
              % (got, len(kept), "✅" if got == len(kept) else "❌"))

    print("\n⚠️ 下一步必须：① `build_store.py --force` 重建 chunks.sqlite；"
          "② `bm25.py build --force` 重建 BM25。"
          "\n   缺任何一步都不报错：前者让答案引到隔壁块的出处，后者让块永远不进字面通道。"
          "\n   核一遍：`scripts/checks/t_index_consistency.py`"
          "（块 / 向量 / sqlite / BM25 必须同为 %d）" % len(kept))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
