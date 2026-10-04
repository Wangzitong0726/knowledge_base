# -*- coding: utf-8 -*-
"""
模型逐文件哈希清单：生成 / 校验

用途：云端从 ModelScope 下载模型后，**必须逐字节核对**与本机已验证副本一致。
「下载成功」不等于「下对了」——镜像可能有不同 revision，也可能传输出错。
本机副本是阶段 0 已逐字节校验过的基准，这里把它固化成清单。

    python scripts/model_manifest.py make   [模型目录] [清单路径]
    python scripts/model_manifest.py verify [模型目录] [清单路径]

verify 会报：缺失、多出、大小不符、sha256 不符，任一非零即退出码 2。
"""
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_DIR = r"D:\ai_homework3\models\Qwen3-Embedding-0.6B"
DEFAULT_MAN = "model_sha256.json"


def sha(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def scan(root):
    root = Path(root)
    rows = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({
                "rel": p.relative_to(root).as_posix(),
                "size": p.stat().st_size,
                "sha256": sha(p),
            })
    return rows


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "make"
    root = Path(argv[2]) if len(argv) > 2 else Path(DEFAULT_DIR)
    man = Path(argv[3]) if len(argv) > 3 else Path(__file__).resolve().parent.parent / "_probe" / DEFAULT_MAN

    if cmd == "make":
        rows = scan(root)
        man.parent.mkdir(parents=True, exist_ok=True)
        man.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
        tot = sum(r["size"] for r in rows)
        print(f"已写 {man}：{len(rows)} 个文件，{tot:,} 字节")
        for r in rows:
            print(f"  {r['size']:>12,}  {r['sha256'][:16]}  {r['rel']}")
        return 0

    if cmd == "verify":
        want = {r["rel"]: r for r in json.loads(man.read_text(encoding="utf-8"))}
        got = {r["rel"]: r for r in scan(root)}
        missing = sorted(set(want) - set(got))
        extra = sorted(set(got) - set(want))
        bad_size = [k for k in want if k in got and got[k]["size"] != want[k]["size"]]
        bad_hash = [k for k in want if k in got and got[k]["size"] == want[k]["size"]
                    and got[k]["sha256"] != want[k]["sha256"]]
        print(f"基准 {len(want)} 个文件" + (f"（基准合计 {sum(r['size'] for r in want.values()):,} 字节）" if want else ""))
        for label, lst in [("缺失", missing), ("多出", extra),
                           ("大小不符", bad_size), ("sha256 不符", bad_hash)]:
            if lst:
                print(f"  ✗ {label} {len(lst)}: {lst[:6]}")
        ok = not (missing or bad_size or bad_hash)
        print("✓ 逐字节一致" if ok else "✗ 与基准不一致")
        return 0 if ok else 2

    raise SystemExit(f"未知命令 {cmd}，用 make / verify")


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(main(sys.argv))
