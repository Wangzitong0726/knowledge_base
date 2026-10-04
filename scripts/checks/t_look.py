# -*- coding: utf-8 -*-
import sys, json, sqlite3
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
con = R.con
print("== Q1 的 must 判据（run_questions.py）==")
try:
    src = open("scripts/run_questions.py", encoding="utf-8").read()
    i = src.find("3A090.c")
    print(src[max(0,i-400):i+700])
except Exception as e:
    print("  读不到:", e)
