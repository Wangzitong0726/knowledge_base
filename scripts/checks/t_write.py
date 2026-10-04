# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import run_questions as RQ

def fake_hit(queries, channels, bm, dn, sim):
    return dict(row=1, chunk_id="a::1", doc_id="d1", source="fedreg", company="BIS",
                title="90 FR", date="2025-01-16", url="https://x", file="f.txt",
                unit="p", page_start=227, page_end=227, section="3A090", seq=1,
                chars=100, text="原文", score=0.08, channels=channels,
                bm25_rank=bm, dense_rank=dn, dense_sim=sim, matched=[],
                queries=queries)

rows = [
  dict(n=1, lib="B", k=8, q="Q1", must=["m1"], why="w", hits=[fake_hit(["Q1","rw1","rw2"], "改写", None, None, None)],
       ans="答案 [1]", err=None, hit=["m1"], ok=True, verdict="✅", secs=1.0),
  dict(n=10, lib="A+B", k=10, q="Q10", must=["材料未覆盖"], why="w", hits=[],
       ans="材料未覆盖", err=None, hit=[], ok=True, verdict="✅ 诚实", secs=1.0),
  dict(n=4, lib="A", k=8, q="Q4", must=["m"], why="w",
       hits=[fake_hit(["Q4"], "bm25+dense", 3, 5, 0.6)],
       ans=None, err="RuntimeError: boom", hit=[], ok=False, verdict="❌", secs=1.0),
]
import pathlib
orig = RQ.OUT
RQ.OUT = pathlib.Path("outputs/_t_十道题.md")
RQ.write(rows, {"ANTHROPIC_MODEL": "test-model"}, "进程环境", 3.0)
txt = RQ.OUT.read_text(encoding="utf-8")
RQ.OUT = orig
print("生成字节:", len(txt))
for name, ok in [
    ("包含 改写 查询列表", "rw1" in txt),
    ("None 已渲染为 —", "None" not in txt),
    ("含 DOC_CAP", "同文档限" in txt),
    ("错误分支", "作答失败" in txt),
    ("空 hits 不炸", "Q10" in txt),
]:
    print(f"   {'✅' if ok else '❌'} {name}")
RQ.OUT = pathlib.Path("outputs/_t_十道题.md")
RQ.OUT.unlink(missing_ok=True)
