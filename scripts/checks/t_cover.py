# -*- coding: utf-8 -*-
import sys, importlib.util
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
spec = importlib.util.spec_from_file_location("rq", "scripts/run_questions.py")
rq = importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(rq)
except SystemExit: pass
R = Retriever(verbose=False)
def broad(must):
    if not must: return "-"
    return ", ".join(f"{m}={R.con.execute('SELECT count(*) FROM chunks WHERE text LIKE ?', (f'%{m}%',)).fetchone()[0]}" for m in must)
print(f"{'#':<4}{'判据在库中出现次数':<34}{'前k的公司数':<10}{'公司'}")
for it in rq.Q:
    res = R.search(it["q"], k=it.get("k", 8), expand=True)
    comps = []
    for r in res:
        c = r["company"] or r["source"]
        if c not in comps: comps.append(c)
    print(f"{it['n']:<4}{broad(it.get('must'))[:33]:<34}{len(comps):<10}{', '.join(comps[:6])}")
