# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import serve_qa as S

def hit(**kw):
    d = dict(row=0, score=0.5, channels="", bm25_rank=None, dense_rank=None,
             dense_sim=None, company="", source="fedreg", title="90 FR",
             file="x.txt", section="3A090", page_start=227, page_end=227,
             date="2025-01-16", url="https://example.gov/x", text="材料原文在这里")
    d.update(kw); return d

html = S.page("测试问题",
    hits=[hit(channels="改写"), hit(channels="bm25+dense", bm25_rank=5, dense_rank=7, dense_sim=0.61)],
    answer="根据材料，阈值是 [1]；例外上限见 [2]。\n材料未覆盖的部分：合约价。",
    err=None, note="注")
print("页面字节数:", len(html))
checks = [
    ('改写 标签出现', '改写' in html),
    ('bm25+dense 出现', 'bm25+dense' in html),
    ('模型作答徽章', '模型作答' in html),
    ('语料原文徽章', '语料原文' in html),
    ('[1] 锚点', 'href="#hit1"' in html),
    ('材料未覆盖标红', 'class="miss"' in html),
    ('无 None 泄漏', 'None' not in html),
    ('无未转义尖括号', '<script' not in html),
]
for name, ok in checks:
    print(f"   {'✅' if ok else '❌'} {name}")
# 出错路径
h2 = S.page("q", hits=[], answer=None, err="RuntimeError: x < y", note="")
print(f"   {'✅' if '作答失败' in h2 else '❌'} 错误分支渲染")
# 空检索路径
h3 = S.page("q", hits=[], answer="材料未覆盖", err=None, note="检索无命中")
print(f"   {'✅' if '检索无命中' in h3 else '❌'} 空命中提示")
