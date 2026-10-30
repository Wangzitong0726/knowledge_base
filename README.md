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
| `outputs/来源清单.md` | **官方来源台账**（老师要求「≥10 家官方全文来源」的凭据）：**18 家公司 / 131 份唯一文档** × 官方站点 × 覆盖期间 × 官方 URL × sha256；库 B 规则条文 9 份单列；并把**同一份文件被巨潮与深交所各取一次的 44 份**逐条列出，写明**它们不是两个独立来源** |
| `outputs/截图/` | 问答页**整页**截图 10 张，十道题各一张（成功、失败、必败题都在里面）；按页面实际高度裁切，不切底部 |
| `outputs/问答页-*.html` | 截图对应的静态页面存档 |
| `data/stage3_切块报告.md`、`data/stage2_报告.md`、`data/stage1_报告.md` | 各阶段报告 |

## 怎么交 / 怎么把仓库传上去

作业要求：文本框写三行（方向 / 代码仓库 URL / 一句话结论），附件交**一页结论 PDF + 截图**。

**重出 PDF**（改了 `一页结论.md` 之后）：

```bash
./.venv/Scripts/python.exe scripts/md2pdf.py outputs/一页结论.md
```

**上传仓库**：本目录**已有 git 仓库**（`git log` 可见 4 次提交），但**有未提交的改动**——需要你自己 `git add -A && git commit` 并推（我不替你 `commit`）。

```bash
cd /d/ai_homework3
git status --short          # 先看这次改了什么
git add -A && git commit -m "第四次修正：索引对账、表头全库归因、语料去重"
git push
```

`.gitignore` 已排掉**两类东西**，见文件里的注释：① 凭据与个人配置（`.env`、`config.json` ← 含个人邮箱，SEC 的 UA 要用，但那是本地配置）；② 体积大又能重跑出来的语料与中间产物（`data/raw|extracted|index/`、`data/*.jsonl`、`data/*.npy`、`models/`）。**按此规则，下次 `git add -A` 会提交 208 个文件 / 11.6 MB**（`git ls-files -co --exclude-standard` 实测 12,187,634 字节：已跟踪 128 个 4.7 MB，另有 80 个未跟踪但未被忽略的探针脚本与运行记录），**单文件最大 1.1 MB**（截图），无大二进制。财报 PDF 不进仓库——下载脚本在 `scripts/fetch/`，重建顺序见上「跑起来」。

**要重建语料**：复制 `config.example.json` 为 `config.json` 填上你的联系邮箱（SEC 的公平使用政策要求在 User-Agent 里声明可联系邮箱，不填会 403），再依次跑阶段 1→5。

## 跑起来

**⚠️ 两个解释器**——依赖分散在两边，用错解释器会 `ModuleNotFoundError`：

```bash
# ① 抓取 / 抽取 / 切块 —— 用系统 Python（装了 PyMuPDF 1.28.2 + lxml）
C:/Python314/python.exe scripts/run_stage1.py
C:/Python314/python.exe scripts/run_stage2.py
C:/Python314/python.exe scripts/chunk.py

# ② 建索引 / 向量 / 页面 / 十题 —— 用项目 venv（装了 torch/transformers/jieba/numpy）
./.venv/Scripts/python.exe scripts/bm25.py build --force  # BM25 倒排表（词表 + 倒排 + docs）
./.venv/Scripts/python.exe scripts/build_store.py --force # chunks.sqlite（块元数据，按 row 对齐向量）
./.venv/Scripts/python.exe scripts/embed_corpus.py      # 向量（GPU 上跑过，CPU 也能跑）
./.venv/Scripts/python.exe scripts/serve_qa.py          # 问答页 http://127.0.0.1:8848/
./.venv/Scripts/python.exe scripts/run_questions.py     # 重写 outputs/十道题-检索记录.md
./.venv/Scripts/python.exe scripts/retrieve.py "你的问题"   # 命令行检索，带通道诊断
```

（抽取要 pymupdf/lxml、检索要 torch，两个环境互不包含——不是疏忽，是各自装各自的。）

### 改了语料之后：重跑顺序（有硬约束）

顺序错了**不会报错**，只会让答案引到隔壁块的出处。照下面走：

| 步 | 干什么 | 解释器 | 为什么必须在这个位置 |
|---|---|---|---|
| 1 | `run_stage2.py` → `chunk.py` | 系统 py | 重抽取、重切块 |
| 2 | `build_vectors_reuse.py` | venv | 文本没变的行**按哈希复用旧向量**，只算变了的。可随时中断、重跑续算（进度落在 `knowledge_base/vectors_incremental/progress.json`）。**必须在第 3 步之前**——旧行号只存在于那份旧 `chunks.sqlite` 里 |
| 3 | `dedupe_sources.py --apply` | 系统 py | 同一份文件被巨潮与深交所各取一次的，只留一份。**必须在第 2 步之后**——它要重写 `vectors.npy`，而第 2 步正用 mmap 读着它（Windows 上文件被占用会写不出去） |
| 4 | `build_store.py --force` + `bm25.py build --force` | venv | 重建 `chunks.sqlite` **和** BM25 **两样**。**必须跟在 3 后面**：sqlite 行数旧了，检索错位；BM25 没重建，块就永远进不了字面通道（2026-10-15 就漏了这一步，见下「对账」） |
| 4.5 | `checks/t_index_consistency.py` | 系统 py | **对账**：块 / 向量 / sqlite / BM25 四份必须同为 67,210。不一致就报错并指出该重建哪个 |
| 5 | `run_questions.py`、`source_roster.py` | venv | 重出十题记录、来源清单 |
| 6 | `save_qa_snapshots.py`（先起 `serve_qa.py`）、`save_static_snapshots.py` | 系统 py | 重出截图 |
| 7 | `md2pdf.py outputs/一页结论.md` | venv | 重出一页结论 PDF |

⚠️ **`make_header_beforeafter.py`（表头修复前后对照）要在第 4 步之前跑**，
或者依赖事先备好的 `knowledge_base/index/chunks_20261004_修前.sqlite`——
`build_store.py --force` 一覆盖，「修前」的原文就没了。那个脚本会自动优先用这份备份。

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
| 3a 切块 | `scripts/chunk.py` · 系统 py | `knowledge_base/chunks.jsonl` | 81,340 块（800 字 / 重合 120 / 句末收尾） |
| 3b 向量 | `scripts/embed_corpus.py`（GPU）/ `build_vectors.py`（校验）· venv | `knowledge_base/vectors.npy` | 81,340 × 1024 fp32 |
| 3c 去重 | `scripts/dedupe_sources.py --apply` · 系统 py | 原地改写 `chunks.jsonl` + `vectors.npy`（先备份） | **81,340 → 67,210 块**（减 14,130，17.4%）：44 对巨潮/深交所同 sha256 的副本只留巨潮 |
| 3d BM25 | `scripts/bm25.py build --force` · venv | `knowledge_base/index/bm25.npz` + `bm25_docs.json` | 67,210 块，词表 **89,698**，nnz **4,213,545**，avgdl 128.8 |
| 3e sqlite | `scripts/build_store.py --force` · venv | `knowledge_base/index/chunks.sqlite` | 67,210 行，`row` = 块行号 |
| 4 页面 | `scripts/serve_qa.py` · venv | — | 标准库 `http.server`，不用 flask |
| 5 十题 | `scripts/run_questions.py` · venv | `outputs/十道题-检索记录.md` | **召回 10/10 · 答案 10/10**（两本账，见一页结论） |

**`row` 贯穿全程**：`chunks.sqlite` 的 `row` = `chunks.jsonl` 的行号 = `vectors.npy` 的行号。`build_store.py` 会在向量行数 ≠ 块数时**硬失败**——错位的向量不会报错，只会让答案引用隔壁块的出处。

## 检索层（`scripts/retrieve.py`）

**BM25 与稠密向量各自排序后融合**，用 **RRF**（倒数排名融合，K=60）而非分数相加：BM25 分无上界、余弦在 [-1,1]，**两者没有可通约的刻度**，相加等于让 BM25 的量纲单方面决定排序。

在此之上是四个**实测逼出来的**机制，不是先验设计：

1. **查询改写**（`expand_queries`）。条文里没有「门槛」这个词，它写的是 `memory bandwidth density`——**用户问抽象概括，条文用具体物理量**。改写把这层转换做掉，原问题 1 票、改写查询每票 0.6。注意这**不是中英翻译问题**：问「HBM 的内存带宽密度阈值」时稠密已排第 6，问「管制门槛」时排第 6,729。
2. **同文档限 3 块**（`DOC_CAP`）。第 1 题原本前 8 里 5 块来自同一份《联邦公报》，把定义块挤到 24 名外。限席**不动任何权重**即解决；调权重、max 融合都治不了（席位被占满）。
3. **行标签锚定通道**（`parse_anchors` / `label_hits`）。问「某科目是多少 / 两个口径差在哪」时，答案不在「整体最像的段落」里，而在**以那个科目为行标签的那一行**里。这条通道不看整块相似度，只看每行的第一个 ` | ` 段对不对得上；命中锚的块在席位分配里**先领 `k//2`**。它只在问题出现口径表里的科目名或引号词时开启，**不认锚的题排序一位不动**。
4. **按公司取证 + 轮转发牌**（`_company_channel` / `_seat_mix`）。问题点名了哪几家公司，就叫每家公司各自出证，席位在点名的公司之间轮转，而不是按总分排——按分排会让排前面那几家吃光席位。这套机制同时治了「跨公司霸榜」（Q2/Q7）与「库边界」（Q8：问公司怎么披露，规则文本挤不进席位）。

1+2 都去掉的话，第 1 题的判据原文进不了前 8；3 去掉，第 4 题召不回 `营业总收入`；4 去掉，第 2 题美光只剩 1/8 席、第 7 题三星 0 条、第 8 题混进 7 条 BIS 规则文本。

## 已验证 / 已知缺陷

- ✅ **向量数值一致（2026-10-30 在现行 67,210 行向量上重跑）**：`vectors.npy` 是在云端 RTX 3090 上算的。本机 CPU 用同一口径（fp32 / last-token / max_length=2048 / 原文不加前缀）重算 **34 块**真实语料——**按来源分层，7/7 个来源全覆盖**（cninfo 16、samsung 5、ecfr 4、govinfo 3、sec 3、fedreg 1、skhynix 1），含**最长 3,214 字**的块——与 `vectors.npy[row]` 逐行比：余弦 **min = 1.00000000、max = 1.00000024**（浮点尾差可越 1），**逐位完全相同 15/34**，其余最大分量差 ≤ 8.9e-7，即 fp32 舍入。探针：`scripts/checks/t_vector_parity_cpu.py`（约 71 秒）。
  - 抽样方式也改过：原为「等间隔 28 行」，那是按去重前的 8 来源语料设计的；去重后 fedreg 只剩 1,906 块，等间隔**一个 fedreg 块都抽不到**，「跨全部来源」这句话就成了空话。现按来源分层（每源保底 2 行），**抽不满全部来源直接 exit 1**。
- ✅ **数据源交叉核对**：巨潮与交易所文件 **sha256 100% 相同**（44 对样本）。
- ⚠️ **判分口径栽过三次，第四次才对**：10/10 → 7/10 → 6/10 → 10/10。三种失败形态：**判据太宽**（`HBM` 在 498 块里出现、`2024` 在 16,587 块里出现，任何块都能过）、**声明了没接线**（`require_company` 写了但 `judge()` 没读）、**数错了对象**（数「任意三家」而不是「问的那三家」）。2026-10-15 又撞到第四种，方向相反：**奖励失败、惩罚成功**——第 2 题召回没修好时，模型答「材料未覆盖」、通篇写「美光」→ 判过；修好召回后给出逐条引原文的好答案、引 `[6][5][1]`、不再写「美光」二字 → 判不过。修法是认**引用标记 `[n]` 所声明的内容归属**，并配两个方向的回归测试：`_probe/judge_mustans_test.py`（11/11）、`_probe/judge_number_test.py`（10/10）。当前判据见 `judge_recall()` / `judge_answer()`，**召回判在原文上、答案判在「有没有用上、有没有造数」上，两本账分开记**。
- ✅ **表头错配已修，并做了全库归因（2026-10-12 修 / 2026-10-30 全量复核）**：旧实现把跨页续页顶部的一行**残标签**当成表头，给下面每个数字盖上错名字（江波龙 `二、营业总成本` 被标成「利息收入」）。四处已回原 PDF 逐字核对（`outputs/表头修复对照.md`）。`checks/t_header.py --all -j 8` 把 184 份文档的 **26,864 张表**用旧实现（`git show HEAD` 原样加载）与新实现各跑一遍：**A 未变 84.9%**、**B 修正 1.0%（270 张换到可信表头）**、**C 弃标 14.0%（3,773 张：旧表头不配，新实现宁可无表头也不猜）**、**D 丢标 0（理论不可能出现，出现即回归）**。跨页表头继承实际生效 2,428 张。另查出 **1,143 张（4.3%）「幻影表」**——`table_ok` 把成段文字当表格收了进来，与本次改动无关，**未修**。
- ⚠️ **`section` 字段会标错**：有块正文是三星 ASP 讨论，`section` 却写成 `Outstanding shares`。公司/页码准，章节名会张冠李戴。
- ✅ **语料里的跨通道重复已去掉（2026-10-15）**：184 份里 **44 对**巨潮/交易所文件 sha256 完全相同，按 sha256 只留巨潮那份，块数 81,340 → **67,210**，唯一文档 **140 份**。这一步不只是省空间：两份副本的 `doc_id` 不同，`DOC_CAP` 限不住，一套席位里可能两席是同一段话；按公司统计时那 7 家公司还凭空多出一倍。
- ⚠️ **索引对账（2026-10-30 补）**：去重那天只重建了 sqlite，**BM25 漏了**，于是 10-15 那份 10/10 是「旧文本的 BM25 + 新语料的向量」跑出来的（索引里 14,948 块已不存在，现行语料里 263 块不在索引里）。重建后重跑，十题判定逐题不变。现由 `scripts/checks/t_index_consistency.py` 对账四份产物，去重脚本的收尾提示也补上了这一步。
- ✅ **截图页头数字已改为现算**：原先页头把巨潮 92 + 深交所 44 当成两批写「136 份」（那 44 份**字节相同**），后来又硬编码过一版。现在页头由 `serve_qa.py` 的 `_corpus_stats()` 每次从 `chunks.sqlite` 数出来——「A 股内存产业链公司 15 家、定期报告 92 份 … 共 **140** 份唯一文档 / **67,210** 块」，**写死的数字不会再和库对不上**。
- ⚠️ **截图重出过一次，因为原版四张全是残图**：第一版用固定 1000×3000 的窗口截，而页面实际有 3295–6677px 高，**每一张的底部都被切掉**——Q7 那张切掉的正好是召回的 [4]–[8] 五条原文，图里只剩判词、看不到判词所依据的原文，而这套系统的卖点就是「每条论断带 [n] 回原文」。现改为「按 20000px 渲染 → 量出内容真实底边 → 裁到该高度」，十张全部完整。同时把 **k 与该题记录对齐**（页面原先写死 `k=8`，而 Q7/Q8 用 14、Q5/Q6/Q9/Q10 用 10——**同一个问题在交付物里出现过两个席数**）。
- ⚠️ **截图脚本里的「点名公司」判据连栽两次**，两版都永远通过：① 判 `'三星' in html`——可页面**把问题原样印在顶部**，问题里就写着「三星、SK 海力士、美光」，判据被问题自己满足；② 改成只在「语料原文」之后数公司名出现次数——**仍然是错的**：三星是作为**被引用的词**出现在佰维存储报告的正文里（"…季度的 DRAM 市场上，三星、SK 海力…"，转引 TrendForce 的市场份额表），数出 5 席，而三星**自己的材料是 0 条**。今按**出处公司**统计，Q7 如实报出「三星缺席」。
- ⚠️ **价格一手口径不可得**（付费墙后），论文只写边界、不拼价格数。
- ✅ **四条召回路径已修**（2026-10-15）：跨公司霸榜（Q2 美光只占 1/8、Q7 三星缺席）→ 按公司取证 + 轮转发牌；口径题（`营业总收入`）→ 行标签锚定通道 + 表头修复；库边界（A 股披露混入规则文本）→ 席位属于公司。修法与证据见一页结论与逐题记录。**另外两条是同一天试出来的负结果**：按来源/按库限席**修好一题弄坏另一题**，不可采纳。

## 目录

```
knowledge_base/    **知识库本体**——检索要用到的都在这里，一个目录装完
  chunks.jsonl       67,210 块切好的原文（115MB，已去重）
  vectors.npy        向量 67,210×1024（275MB）
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

**关于「语料出机」**：本机（AMD CPU）能跑，也验过与云端一致（见上）。最初的 81,895 块全库向量是在**租的云端 RTX 3090** 上算的；表头修复后重切块，`build_vectors_reuse.py` 按文本哈希**复用 61,872 行、只新算 19,468 行（14,172 个不同文本）**，新算部分仍在云端 GPU 完成；去重再把 81,340 行按保留行号切到 **67,210 行**。原因是本机太慢：探针实测 **2.98 秒/块**（batch_size=4、含最长块），全库外推 60 小时以上；增量也要 22 小时。也就是说，**向量化这一步语料确实上传到了租用实例**——抓取、切块、BM25、问答页面全在本机——此事经用户在当时明确授权（`cloud/AUTODL.md`）。要完全不出机就在本机重跑 `embed_corpus.py`，结果按上文探针可比。
