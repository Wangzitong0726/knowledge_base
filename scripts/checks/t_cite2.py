# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
for row in (38831, 41207, 41206, 41037):
    m = R._meta(row)
    print(f"\n{'='*70}\nrow={row}  {m['source']}/{m['company']}  §{m['section']}  p{m['page_start']}  {m['date']}")
    print(f"title={m['title'][:70]}")
    print(f"url={m['url']}")
    print("-"*70)
    print(m['text'][:700])
