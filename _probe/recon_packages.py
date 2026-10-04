# -*- coding: utf-8 -*-
"""
阶段 0 侦察：在装任何东西之前，先查清 cp314 上哪些预编译包真的存在。

为什么先查：Python 3.14 很新，C 扩展包（torch / onnxruntime / tokenizers）
的 cp314 wheel 经常滞后甚至没有。先 pip install 再看报错，等于把
"能不能装" 变成一个漫长的试错；查 PyPI 的文件名只要几秒。

同时测三条下载通路的可达性：PyPI / GitHub Releases / ModelScope。
"""
import json
import re
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36"
_out = []


def rec(n, ok, note):
    _out.append((n, ok, note))
    print(f"[{'OK ' if ok else 'FAIL'}] {n} :: {note}")


def get(url, timeout=40, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), time.time() - t0


# --------------------------------------------------- 1. PyPI 上的 cp314 wheel
PKGS = ["torch", "onnxruntime", "llama-cpp-python", "tokenizers", "transformers",
        "sentence-transformers", "jieba", "modelscope", "huggingface-hub", "safetensors"]


def check_pypi(pkg):
    for base in ["https://pypi.org/pypi/{}/json", "https://pypi.tuna.tsinghua.edu.cn/pypi/{}/json"]:
        try:
            raw, el = get(base.format(pkg))
            js = json.loads(raw)
            ver = js["info"]["version"]
            files = js["releases"].get(ver, [])
            names = [f["filename"] for f in files]
            cp314 = [n for n in names if "cp314" in n]
            cp313 = [n for n in names if "cp313" in n]
            anyw = [n for n in names if "py3-none-any" in n or "-any.whl" in n]
            kind = ("纯 Python（任意版本可装）" if anyw and not cp314 and not cp313
                    else "有 cp314 wheel" if cp314
                    else "仅到 cp313（**3.14 装不上**）" if cp313
                    else "只有源码包（要编译器）")
            rec(f"PyPI {pkg}", bool(cp314 or anyw),
                f"最新 {ver}｜{kind}｜cp314={len(cp314)} cp313={len(cp313)} any={len(anyw)}")
            if cp314:
                rec(f"   └ {pkg} 的 cp314 文件名示例", True, cp314[0])
            return
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:60]}"
    rec(f"PyPI {pkg}", False, last)


# --------------------------------------------------- 2. 三条下载通路
def check_reach():
    tests = [
        ("PyPI 官方", "https://pypi.org/simple/", {}),
        ("清华 PyPI 镜像", "https://pypi.tuna.tsinghua.edu.cn/simple/", {}),
        ("GitHub Releases（llama.cpp）",
         "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest", {}),
        ("ModelScope 模型页", "https://modelscope.cn/api/v1/models/Qwen/Qwen3-Embedding-0.6B", {}),
        ("ModelScope 文件树",
         "https://modelscope.cn/api/v1/models/Qwen/Qwen3-Embedding-0.6B/repo/files?Revision=master", {}),
        ("HuggingFace 镜像 hf-mirror", "https://hf-mirror.com/Qwen/Qwen3-Embedding-0.6B/resolve/main/config.json", {}),
    ]
    for label, url, hdr in tests:
        try:
            raw, el = get(url, timeout=30, headers=hdr)
            note = f"{len(raw)/1e3:.0f}KB {el:.1f}s " + raw[:100].decode("utf-8", "replace").replace("\n", " ")
            if "llama.cpp" in label:
                js = json.loads(raw)
                assets = [a["name"] for a in js.get("assets", [])]
                wins = [a for a in assets if "win" in a.lower() or "windows" in a.lower()]
                note = f"最新 tag={js.get('tag_name')}｜资产 {len(assets)} 个｜Windows 相关={wins[:4]}"
            if "文件树" in label:
                js = json.loads(raw)
                fs = js.get("Data", {}).get("Files", [])
                note = f"文件 {len(fs)} 个：" + ", ".join(f["Path"] for f in fs)[:220]
            rec(label, True, note)
        except urllib.error.HTTPError as e:
            rec(label, e.code in (401, 403, 404), f"HTTP {e.code}（可达）")
        except Exception as e:
            rec(label, False, f"{type(e).__name__}: {str(e)[:70]}")


def main():
    print("=" * 70)
    print("阶段 0 侦察：包可用性 + 下载通路")
    print("=" * 70)
    print("\n--- PyPI cp314 wheel 可用性 ---")
    for p in PKGS:
        check_pypi(p)
    print("\n--- 下载通路可达性 ---")
    check_reach()
    lines = ["# 阶段 0 侦察报告", "", f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| 检查项 | 结果 | 记录 |", "|---|---|---|"]
    for n, ok, note in _out:
        lines.append(f"| {n} | {'✅' if ok else '❌'} | {note} |")
    from pathlib import Path
    (Path(__file__).resolve().parent / "stage0_recon.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
