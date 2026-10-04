# -*- coding: utf-8 -*-
"""
本机向量化 · Qwen3-Embedding-0.6B

设计要点（都由实测确定，勿凭猜改）：

  1. **pooling 必须用 last-token**，不是 mean。
     依据：模型自带的 `1_Pooling/config.json` 里 `"pooling_mode_lasttoken": true`。
     用 mean 不会报错，只会让向量质量静默变差——所以这个文件要读出来，不能想当然。

  2. **查询侧加指令前缀，文档侧不加**。官方用法：
        查询："Instruct: {任务描述}\nQuery:{问题}"
        文档：原文
  3. **用 float32 加载**。模型卡写的是 bfloat16，但本机是 AMD CPU，
     无 BF16 加速，fp32 反而更快更准。代价是约 2.4GB 内存。
  4. 载入后**自检维度**：必须等于 1024（来自 config.json 的 hidden_size）。
     对不上直接抛错，不静默继续。
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

# 本机控制台默认 GBK：中文会乱码，符号会直接抛 UnicodeEncodeError。
# 这是环境问题不是程序问题，但会伪装成崩溃，所以在模块入口统一修掉。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 模型目录可用环境变量覆盖：同一份代码在本机和云端都能跑
MODEL_DIR = Path(os.environ.get("EMBED_MODEL_DIR")
                 or r"D:\ai_homework3\models\Qwen3-Embedding-0.6B")
EXPECTED_DIM = 1024


def pick_device():
    """有 CUDA 用 CUDA，否则 CPU。

    dtype 两边都**固定 fp32**，不因设备而变：
    本机已按 fp32 验收过（bf16 在这台 AMD CPU 上慢 6 倍），
    云端若擅自换精度，产出的向量就与本机验收基准不可比了。
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


# 中文语料较多，线程给满
torch.set_num_threads(max(1, (os.cpu_count() or 4)))


def _pooling_is_lasttoken(model_dir):
    """把 pooling 方式读出来核对——这是本项目的一条硬纪律。"""
    cfg = Path(model_dir) / "1_Pooling" / "config.json"
    if not cfg.exists():
        raise RuntimeError(f"缺少 {cfg}，无法确认 pooling 方式；拒绝猜测")
    js = json.loads(cfg.read_text(encoding="utf-8"))
    if not js.get("pooling_mode_lasttoken"):
        raise RuntimeError(f"pooling 配置不是 last-token，实际为 {js}；请核对模型")
    return js["word_embedding_dimension"]


class Embedder:
    def __init__(self, model_dir=MODEL_DIR, dtype=torch.float32, verbose=True):
        from transformers import AutoModel, AutoTokenizer
        self.dir = Path(model_dir)
        dim = _pooling_is_lasttoken(self.dir)
        if dim != EXPECTED_DIM:
            raise RuntimeError(f"模型维度 {dim} 与预期 {EXPECTED_DIM} 不符")
        t0 = time.time()
        self.tok = AutoTokenizer.from_pretrained(str(self.dir), padding_side="left")
        # 左 padding 是 last-token pooling 的前提：右 padding 会让“最后一个位置”
        # 落在 pad 上，取出来就是常数向量（又一个不会报错的坑）。
        try:
            self.model = AutoModel.from_pretrained(str(self.dir), dtype=dtype)
        except TypeError:                       # 老版 transformers 用 torch_dtype
            self.model = AutoModel.from_pretrained(str(self.dir), torch_dtype=dtype)
        self.device = pick_device()
        self.model.to(self.device)
        self.model.eval()
        self.dim = dim
        if verbose:
            n = sum(p.numel() for p in self.model.parameters())
            print(f"[Embedder] 载入 {self.dir.name}  {n/1e6:.0f}M 参数  "
                  f"dtype={dtype}  维度={dim}  设备={self.device}  {time.time()-t0:.1f}s")

    @torch.no_grad()
    def encode(self, texts, batch_size=8, is_query=False, instruction=None,
               verbose=False, length_bucket=True, max_length=1024):
        """返回 (n, 1024) 的 float32 数组，已做 L2 归一化。

        length_bucket：按文本长度排序后再分批。真实语料块长参差，
        长短混在同一批里会被 padding 白白拖慢；排序后同批长度相近。
        结果会还原成输入顺序，**不影响语义**，只是快慢。
        """
        if isinstance(texts, str):
            texts = [texts]
        if is_query and instruction:
            texts = [f"Instruct: {instruction}\nQuery:{t}" for t in texts]
        n_all = len(texts)

        # 长度分桶：order[pos] = 原始下标；inv[原始下标] = 排完后的位置
        bucket = length_bucket and n_all > batch_size
        if bucket:
            order = sorted(range(n_all), key=lambda i: len(texts[i]))
        else:
            order = list(range(n_all))
        inv = [0] * n_all
        for pos, i in enumerate(order):
            inv[i] = pos
        work = [texts[i] for i in order]

        out, n_trunc = [], 0
        t0 = time.time()
        for i in range(0, n_all, batch_size):
            batch = work[i:i + batch_size]
            enc = self.tok(batch, padding=True, truncation=True,
                           max_length=max_length, return_tensors="pt").to(self.device)
            # 截断会**静默丢内容**，必须数出来报，不能默默吞掉
            n_trunc += int((enc["attention_mask"].sum(dim=1) >= max_length).sum())
            hidden = self.model(**enc).last_hidden_state          # (B, L, 1024)
            # last-token pooling：取每行**最后一个 mask==1** 的位置。
            #
            # 这里必须找位置，不能写 `attention_mask.sum(dim=1) - 1`：
            # 那是**右 padding** 的公式。左 padding 下真实 token 在尾部，
            # 最后一个真实 token 恒为最后一列，而 sum-1 会落到序列中间，
            # 取到一个合法的、带语义的**错**向量 —— 不报错、还「看着能用」。
            # 本项目真的踩过一次：一批里只有最长的那个（不被 pad）是对的。
            mask = enc["attention_mask"]
            last = mask.size(1) - 1 - mask.flip(dims=[1]).long().argmax(dim=1)
            vec = hidden[torch.arange(hidden.size(0), device=hidden.device), last]
            vec = torch.nn.functional.normalize(vec, p=2, dim=1)
            out.append(vec.float().cpu().numpy())
            if verbose and (i // batch_size) % 10 == 0:
                done = i + len(batch)
                el = time.time() - t0
                print(f"  {done}/{n_all}  {done/el:.1f} 块/秒", flush=True)

        arr = np.vstack(out).astype(np.float32)
        if bucket:                       # 还原成输入顺序
            arr = arr[np.array(inv)]
        if arr.shape[1] != self.dim:
            raise RuntimeError(f"输出维度 {arr.shape} 与模型维度 {self.dim} 不符")
        if n_trunc:
            print(f"  !! 有 {n_trunc} 条被截断到 {max_length} token，内容有丢失，"
                  f"请核对切块大小", flush=True)
        return arr


if __name__ == "__main__":
    e = Embedder()
    print("自检 OK")
