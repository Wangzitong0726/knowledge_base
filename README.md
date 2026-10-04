# 内存（DRAM/HBM）产业问答知识库

《人工智能与数据分析》作业三·方向 A。把内存产业的一手材料做成**带出处的问答知识库**：检索到原文，模型只依据原文作答，每个论断都带 `[n]` 可点回原文核对。

本仓库**一料两用**：同一份语料也服务《国际金融理论与实务》课程论文《美国出口管制下内存市场的价格决定机制》。两者共用检索层，产出物分开。

---

## 交付物在哪

| 文件 | 是什么 |
|---|---|
| `outputs/一页结论.pdf` | **一页结论（交作业用 PDF）**——由 `outputs/一页结论.md` 排成 |
| `outputs/一页结论.md` | 一页结论源文件：哪类题答得好、哪类翻车、为什么 |
| `outputs/十道题-检索记录.md` | 十道题逐题记录：实际用的改写查询、来源/公司构成、判据命中、模型作答、召回原文 |
| `outputs/管制侧引注表.md` | 论文衔接：库 B 规则**原文逐字 + 出处**，可直接进脚注 |
| `outputs/截图/` | 问答页**整页**截图 10 张，十道题各一张（成功、失败、必败题都在里面）；按页面实际高度裁切，不切底部 |
| `outputs/问答页-*.html` | 截图对应的静态页面存档 |
| `data/stage3_切块报告.md`、`data/stage2_报告.md`、`data/stage1_报告.md` | 各阶段报告 |

## 怎么交 / 怎么把仓库传上去

作业要求：文本框写三行（方向 / 代码仓库 URL / 一句话结论），附件交**一页结论 PDF + 截图**。

**重出 PDF**（改了 `一页结论.md` 之后）：

```bash
./.venv/Scripts/python.exe scripts/md2pdf.py outputs/一页结论.md
```

**上传仓库**：本目录**还不是 git 仓库**，需要你自己建仓并推（我不会替你 `git init`/`commit`）。

```bash
cd /d/ai_homework3
git init && git add -A && git commit -m "内存产业问答知识库"
git remote add origin <你的仓库URL> && git push -u origin main
```

`.gitignore` 已排掉**两类东西**，见文件里的注释：① 凭据与个人配置（`.env`、`config.json` ← 含个人邮箱，SEC 的 UA 要用，但那是本地配置）；② 体积大又能重跑出来的语料与中间产物（`data/raw|extracted|index/`、`data/*.jsonl`、`data/*.npy`、`models/`）。**按此规则，仓库约 119 个文件 / 2.8 MB**，无大二进制。财报 PDF 不进仓库——下载脚本在 `scripts/fetch/`，重建顺序见上「跑起来」。

**要重建语料**：复制 `config.example.json` 为 `config.json` 填上你的联系邮箱（SEC 的公平使用政策要求在 User-Agent 里声明可联系邮箱，不填会 403），再依次跑阶段 1→5。

## 跑起来

**⚠️ 两个解释器**——依赖分散在两边，用错解释器会 `ModuleNotFoundError`：

```bash
# ① 抓取 / 抽取 / 切块 —— 用系统 Python（装了 PyMuPDF 1.28.2 + lxml）
C:/Python314/python.exe scripts/run_stage1.py
C:/Python314/python.exe scripts/run_stage2.py
C:/Python314/python.exe scripts/chunk.py

# ② 建索引 / 向量 / 页面 / 十题 —— 用项目 venv（装了 torch/transformers/jieba/numpy）
./.venv/Scripts/python.exe scripts/build_store.py       # BM25 + sqlite
./.venv/Scripts/python.exe scripts/embed_corpus.py      # 向量（GPU 上跑过，CPU 也能跑）
./.venv/Scripts/python.exe scripts/serve_qa.py          # 问答页 http://127.0.0.1:8848/
./.venv/Scripts/python.exe scripts/run_questions.py     # 重写 outputs/十道题-检索记录.md
./.venv/Scripts/python.exe scripts/retrieve.py "你的问题"   # 命令行检索，带通道诊断
```

（抽取要 pymupdf/lxml、检索要 torch，两个环境互不包含——不是疏忽，是各自装各自的。）

模型配置走**进程环境优先、`.env` 补缺**（见 `scripts/llm.py`）。API Key 只进 `.env`，**`config.json` 含个人邮箱，不要提交**。

⚠️ 命令行 `retrieve.py` 默认 **不开查询改写**（`expand=False`，且只取 top-6），问法是「抽象概括」（如第 1 题那种）时会看不到改写机制的效果；页面与十题脚本走的都是 `expand=True`。

---

## 流水线

```
抓取 → 抽取 → 切块 → 建索引（向量 + BM25）→ 检索 → 作答
```

| 阶段 | 入口（解释器） | 产物 | 规模 |
|---|---|---|---|
| 1 抓取 | `scripts/run_stage1.py`（每源一个 `fetch/*.py`）· 系统 py | `data/raw/` | **184 份**（含 44 对跨通道重复，唯一 140）/ ~602 MB / 0 失败 |
| 2 抽取 | `scripts/run_stage2.py`（`extract/{pdf,html,plain,tablefmt}.py`）· 系统 py | `data/extracted/**/*.jsonl` | 184/184 份、45,279 页、27,511 张表 |
| 3a 切块 | `scripts/chunk.py` · 系统 py | `knowledge_base/chunks.jsonl` | **81,895 块 / 54,443,766 字**（800 字 / 重合 120 / 句末收尾） |
| 3b BM25 | `scripts/bm25.py` → `scripts/build_store.py` · venv | `knowledge_base/index/`（`bm25.npz` + `chunks.sqlite`） | 词表 100,238，nnz 5,401,243 |
| 3c 向量 | `scripts/embed_corpus.py`（GPU）/ `build_vectors.py`（校验）· venv | `knowledge_base/vectors.npy` | 81,895 × 1024 fp32，335 MB |
| 4 页面 | `scripts/serve_qa.py` · venv | — | 标准库 `http.server`，不用 flask |
| 5 十题 | `scripts/run_questions.py` · venv | `outputs/十道题-检索记录.md` | **6/10**（见一页结论） |

**`row` 贯穿全程**：`chunks.sqlite` 的 `row` = `chunks.jsonl` 的行号 = `vectors.npy` 的行号。`build_store.py` 会在向量行数 ≠ 块数时**硬失败**——错位的向量不会报错，只会让答案引用隔壁块的出处。

## 检索层（`scripts/retrieve.py`）

**BM25 与稠密向量各自排序后融合**，用 **RRF**（倒数排名融合，K=60）而非分数相加：BM25 分无上界、余弦在 [-1,1]，**两者没有可通约的刻度**，相加等于让 BM25 的量纲单方面决定排序。

在此之上有两个**实测逼出来的**机制，不是先验设计：

1. **查询改写**（`expand_queries`）。条文里没有「门槛」这个词，它写的是 `memory bandwidth density`——**用户问抽象概括，条文用具体物理量**。改写把这层转换做掉，原问题 1 票、改写查询每票 0.6。注意这**不是中英翻译问题**：问「HBM 的内存带宽密度阈值」时稠密已排第 6，问「管制门槛」时排第 6,729。
2. **同文档限 3 块**（`DOC_CAP`）。第 1 题原本前 8 里 5 块来自同一份《联邦公报》，把定义块挤到 24 名外。限席**不动任何权重**即解决；调权重、max 融合都治不了（席位被占满）。

两者都去掉的话，第 1 题的判据原文进不了前 8。

## 已验证 / 已知缺陷

- ✅ **向量数值一致**：`vectors.npy` 是在云端 RTX 3090 上算的。本机 CPU 用同一口径（fp32 / last-token / max_length=2048 / 原文不加前缀）重算 32 块真实语料——**跨全部 8 个来源、含最长的 3821 字块**——逐行余弦 **min = 0.99999988**（15/32 位完全相同，其余差异在 1e-7 量级，即 fp32 舍入）。探针：`scripts/checks/t_vector_parity_cpu.py`（约 95 秒）。
- ✅ **数据源交叉核对**：巨潮与交易所文件 **sha256 100% 相同**（44 对样本）。
- ⚠️ **判分口径栽过两次**：10/10 → 7/10 → **6/10**，每次都是判据太弱（词太常见 / 声明了没接线 / 数「任意三家」而非「问的那三家」）。当前判据见 `judge()`，**每条都在原文上判，不在答案上判**。
- ⚠️ **表格拍平有错位**：部分财报表的标签与数值错配（已确认一例：江波龙合并利润表 `营业总成本` 的数值被标成「利息收入」）。可测指纹命中财报类块的 61.2%，但那是**标志率不是确认的错误率**。**引财报数字前须回原 PDF 核对。**
- ⚠️ **`section` 字段会标错**：有块正文是三星 ASP 讨论，`section` 却写成 `Outstanding shares`。公司/页码准，章节名会张冠李戴。
- ⚠️ **语料含跨通道重复**：184 份里 **44 对**巨潮/交易所文件字节相同，**唯一文档 140 份**；`DOC_CAP` 按文档计数，拦不住这类重复。
- ✅ **截图页头数字已更正**：原先页头写「136 份」是把巨潮 92 + 深交所 44 当成两批（那 44 份**字节相同**）。已改为「136 份（含 44 份交易所同源副本，去重 92）」。
- ⚠️ **截图重出过一次，因为原版四张全是残图**：第一版用固定 1000×3000 的窗口截，而页面实际有 3295–6677px 高，**每一张的底部都被切掉**——Q7 那张切掉的正好是召回的 [4]–[8] 五条原文，图里只剩判词、看不到判词所依据的原文，而这套系统的卖点就是「每条论断带 [n] 回原文」。现改为「按 20000px 渲染 → 量出内容真实底边 → 裁到该高度」，十张全部完整。同时把 **k 与该题记录对齐**（页面原先写死 `k=8`，而 Q7/Q8 用 14、Q5/Q6/Q9/Q10 用 10——**同一个问题在交付物里出现过两个席数**）。
- ⚠️ **截图脚本里的「点名公司」判据连栽两次**，两版都永远通过：① 判 `'三星' in html`——可页面**把问题原样印在顶部**，问题里就写着「三星、SK 海力士、美光」，判据被问题自己满足；② 改成只在「语料原文」之后数公司名出现次数——**仍然是错的**：三星是作为**被引用的词**出现在佰维存储报告的正文里（"…季度的 DRAM 市场上，三星、SK 海力…"，转引 TrendForce 的市场份额表），数出 5 席，而三星**自己的材料是 0 条**。今按**出处公司**统计，Q7 如实报出「三星缺席」。
- ⚠️ **价格一手口径不可得**（付费墙后），论文只写边界、不拼价格数。
- ❌ **未修的四条召回路径**：跨公司霸榜（Q2 美光只占 1/8、Q7 三星缺席）、口径题（`营业总收入`）、库边界（A 股披露混入规则文本）。根因已定位，见一页结论。

## 目录

```
knowledge_base/    **知识库本体**——检索要用到的都在这里，一个目录装完
  chunks.jsonl       81,895 块切好的原文（142MB）
  vectors.npy        向量 81,895×1024（320MB）
  vectors.meta.json  向量是怎么算的（口径存档）
  expand_cache.json  查询改写缓存（让十题记录可复现）
  index/             bm25.npz + chunks.sqlite（BM25 倒排表与块元数据）
data/              语料与中间产物（不含知识库本体）
  raw/               184 份原始 PDF/HTML
  extracted/         阶段 2 抽取产物
  stage*_报告.md     各阶段报告 / manifest.jsonl 等
outputs/           交付物（一页结论 PDF / 十题记录 / 引注表 / 截图）
scripts/           流水线（fetch/ extract/ checks/ 三个子目录）
  fetch/           抓取（urllib，无第三方依赖）
  extract/         抽取（pdf.py→pymupdf，html/plain.py→lxml）
  checks/          验证与取证脚本（判据检查、引用抽取、向量一致性、负结果复现）
_probe/            选源阶段的探测脚本与报告（阶段 0 之前）
cloud/             云端 GPU 那一段的说明（AUTODL.md）
models/            Qwen3-Embedding-0.6B 本地权重
方案.md            实施方案与决策记录
```

## 环境

两个 Python 3.14.7，各装各的：

| 解释器 | 装了 | 负责 |
|---|---|---|
| `C:\Python314\python.exe`（系统） | numpy 2.5.3、**PyMuPDF 1.28.2**、lxml | 抓取 / 抽取 / 切块（阶段 1–3a） |
| `.venv/Scripts/python.exe` | torch 2.14.1+cpu、transformers 5.18.0、jieba 0.42.1、numpy 2.5.3 | 索引 / 向量 / 页面 / 十题（阶段 3b–5） |

向量模型 `Qwen3-Embedding-0.6B`，**必须 last-token pooling + 左 padding + fp32**——三者任一错了都不报错，只是向量静默变差（详见 `scripts/embed.py` 注释）。大文件放 D 盘。

**关于「语料出机」**：本机（AMD CPU）能跑，也验过与云端一致（见上）。但全库 81,895 块的正式向量化是在**租的云端 RTX 3090** 上跑的。原因是本机太慢：上述探针实测 **2.98 秒/块**（batch_size=4、含最长块），按此外推全库约 **60 小时以上**；真实批处理（token 预算 16384、按长度分桶）会快不少，但仍是「数小时 vs 本机整夜」的差距。也就是说，这一步**语料确实上传到了租用实例**——仅向量化这一步，抓取、切块、BM25、问答页面全在本机——此事经用户在当时明确授权（`cloud/AUTODL.md`）。要完全不出机就在本机重跑 `embed_corpus.py`，结果按上文探针可比。
