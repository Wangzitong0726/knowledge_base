# -*- coding: utf-8 -*-
"""
下载 Qwen3-Embedding-0.6B（ModelScope 源，国内直连快）。

纪律：
  - 每个文件落盘后**按字节数校验**，不匹配就删掉重下（网络截断比想象中常见）
  - 已存在且大小正确的文件跳过，可断点续跑
  - 中文路径一律走 ASCII 变量，命令行不留中文

用法：python scripts/download_model.py
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
DEST = Path(r"D:\ai_homework3\models") / "Qwen3-Embedding-0.6B"
BASE = "https://modelscope.cn/api/v1/models/{}/repo".format(MODEL_ID)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")

# 需要哪些文件：模型权重 + 分词器 + ST 配置（含 Pooling 说明）
WANT = [
    "config.json", "configuration.json", "generation_config.json",
    "config_sentence_transformers.json", "modules.json",
    "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt",
    "model.safetensors", "1_Pooling/config.json", "README.md",
]


def http_get(url, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)


def remote_sizes():
    """问 ModelScope 要文件清单与大小，用来校验。"""
    raw = http_get(BASE + "/files?Revision=master&Recursive=True", timeout=60).read()
    js = json.loads(raw)
    out = {}
    for f in js["Data"]["Files"]:
        if f["Type"] == "tree":
            continue
        out[f["Path"]] = f["Size"]
    return out


def download(path, expect_size):
    dest = DEST / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and expect_size and dest.stat().st_size == expect_size:
        print(f"  跳过（已完整） {path}  {expect_size/1e6:.2f}MB")
        return True
    url = f"{BASE}?Revision=master&FilePath={path}"
    for attempt in range(3):
        try:
            t0 = time.time()
            got = 0
            with http_get(url) as r, open(dest, "wb") as fh:
                total = int(r.headers.get("Content-Length") or expect_size or 0)
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    fh.write(chunk)
                    got += len(chunk)
                    if total:
                        pct = got / total * 100
                        sys.stdout.write(f"\r    {path}  {got/1e6:8.2f}/{total/1e6:.2f}MB  {pct:5.1f}%")
                        sys.stdout.flush()
            el = time.time() - t0
            ok = (expect_size == 0) or (got == expect_size)
            print(f"\r  {'OK  ' if ok else '大小不符'} {path}  {got/1e6:.2f}MB  {el:.1f}s"
                  f"  ({got/max(el,1e-9)/1e6:.1f}MB/s)")
            if ok:
                return True
            dest.unlink(missing_ok=True)
        except Exception as e:
            print(f"\n  ! 第{attempt+1}次失败 {path}: {type(e).__name__}: {str(e)[:70]}")
            time.sleep(3)
    return False


def main():
    print(f"下载 {MODEL_ID} → {DEST}")
    sizes = remote_sizes()
    print(f"远端清单 {len(sizes)} 个文件\n")
    bad = []
    for p in WANT:
        exp = sizes.get(p, 0)
        if p not in sizes:
            print(f"  !! 远端没有 {p}")
            bad.append(p)
            continue
        if not download(p, exp):
            bad.append(p)
    total = sum((DEST / f).stat().st_size for f in WANT if (DEST / f).exists())
    print(f"\n合计落盘 {total/1e6:.1f}MB")
    if bad:
        print(f"未完成：{bad}")
        sys.exit(1)
    print("全部文件校验通过")


if __name__ == "__main__":
    main()
