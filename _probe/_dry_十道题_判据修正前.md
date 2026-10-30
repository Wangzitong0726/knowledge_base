# 十道题 · 逐题检索记录

- 生成：2026-10-15 19:56:55，总用时 150 秒
- 检索三件套：① BM25 + 稠密向量双通道，**RRF 融合**（K=60，每通道先各取前 100）；② **查询改写**——原问题 1 票、改写查询每票 0.6，把「抽象的管制说法」翻成条文实际用词；③ **同文档限 3 块**——防一份文件霸榜。
- ②③ 都是实测逼出来的，不是先验设计：去掉②，第 1 题的判据原文进不了前 8；去掉③，前 8 里 5 块来自同一份《联邦公报》，把定义块挤到 24 名开外。
- 作答模型：`deepseek-v4-flash-vision-exp`（配置来源：进程环境）
- **召回一本账、答案另一本账**（课件 p94 的工具账本：`search 23 / read 14 / find_table 2 / graph 1`）——
  召回判的挂在**检索到的原文**上（答案通顺只证明会写话，不证明检索对）；
  答案判的是**答案有没有真的用上、有没有自己造数**（数字归属核对）。
  两本账合成一个「通过」是上一版的错：第 4 题答案诚实写了「材料未覆盖」，
  而判据照样判「过」——混在一起就看不见答案这一本。

## 总览

| # | 库 | 召回判定 | 答案判定 | 席位数 | 用时 | 题目 |
|---|---|---|---|---:|---:|---|
| 1 | B | ✅ 召回命中 | ✅ 答案合规 | 8 | 22.0s | 3A090.c 的管制门槛是什么？ |
| 2 | A | ❌ 美光 只占 0/8 席（需 ≥4） | ✅ 答案合规 | 8 | 5.2s | 美光最近一期财报里，关于 HBM 的收入、产能或资本… |
| 3 | B | ✅ 召回命中 | ❌ 答案有 1 个数在语料里找不到出处：96790 | 8 | 10.4s | 2024 年 12 月以前 HBM 受出口管制吗？是… |
| 4 | A | ❌ 缺判据原文 ['营业总收入'] | ✅ 答案合规 | 8 | 7.3s | 江波龙的年报里，「营业收入」和「营业总收入」这两个口… |
| 5 | A+B | ✅ 召回命中 | ✅ 答案合规 | 10 | 25.1s | 出口管制对内存市场的影响涉及哪几个方面？ |
| 6 | A+B | ✅ 召回命中 | ✅ 答案合规 | 10 | 15.5s | 我最近在看内存这块，感觉这两年 HBM 突然就热起来… |
| 7 | A | ✅ 召回命中 | ❌ 答案未点名 ['三星', '海力士', '美光'] | 14 | 26.6s | 三星、SK 海力士、美光三家最近一期报告对 HBM … |
| 8 | A | ✅ 召回命中 | ✅ 答案合规 | 14 | 22.0s | A 股内存产业链公司如何披露出口管制对自身经营的影响… |
| 9 | A+B | ✅ 召回命中 | ❌ 答案有 2 个数在语料里找不到出处：80080、96790 | 10 | 10.8s | 出口管制规则的历次修订时点，与厂商财报里提到的价格或… |
| 10 | A+B | ✅ 必败题：判据在答案侧（语料里没有一手价格，本来就不该有这句话） | ✅ 诚实承认未覆盖 | 10 | 5.4s | HBM3E 现在的合约价是多少美元？ |

**召回通过 8/10　答案通过 7/10　两本都过 5/10**

> 「答案通过」只统计**设了答案判据的**题（`must_ans` 与必败题）加上数字归属核对；
> 没设答案判据的题，答案栏只做数字归属核对，记录里逐题写明，**不冒充「已判过」**。

---

## 第 1 题 · 召回 ✅ 召回命中｜答案 ✅ 答案合规

**问题**：3A090.c 的管制门槛是什么？

- 库：B｜考察：基础事实。判据要的是**管制门槛**（2），不是例外上限（3.3）——两个数混了就答反了。
- 实际进检索的查询（原问题 + 模型改写）：`3A090.c 的管制门槛是什么？` ｜ `3A090.c 管制门槛 memory bandwidth density` ｜ `ECCN 3A090.c performance parameters threshold EAR` ｜ `3A090.c export control threshold high bandwidth memory`
- 判据原文：`['greater than 2 gigabytes per second per square millimeter']` → 命中 ['greater than 2 gigabytes per second per square millimeter']
- 附加结构判据：无
- 实际来源构成：['ecfr', 'fedreg', 'govinfo']
- 实际公司构成：['BIS']
- 召回 8 条，用时 22.0s

### 模型作答（非原文，须逐条核 [n]）

```
3A090.c 的管制门槛是：**High bandwidth memory (HBM) having a `memory bandwidth density' greater than 2 gigabytes per second per square millimeter**。[6][7][8]

相关定义同条材料给出：

- **Technical Note 1 to 3A090.c: `Memory bandwidth density' is the memory bandwidth measured in gigabytes per second divided by the area of the package or stack measured in square millimeters**。[6][7][8]
- **In the case where a stack is contained in a package, use the memory bandwidth of the packaged device and the area of the package**。[6][7][8]
- **High bandwidth memory (HBM) includes dynamic random access memory integrated circuits, regardless of whether they conform to the JEDEC standards for high bandwidth memory (HBM), provided they have a `memory bandwidth density' greater than 2 gigabytes per second per square millimeter**。[6][7][8]

另需区分：**License Exception HBM** 下，只有 3A090.c item 的 **memory bandwidth density less than 3.3 GB/s/mm^2** 且满足条件时才授权；这是许可例外门槛，不是 3A090.c 的管制门槛。[3]
```

### 判分（两本账）

- **召回判定**：✅ 召回命中
- **答案判定**：✅ 答案合规
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - `3.3` → 第 2、3 席
- **未覆盖项**：无
- ⚠️ **本题未设答案专名判据**（问题没有要求点名某个对象），答案栏只做数字归属核对——**不冒充「答案已判过」**。

### 检索到的语料原文

**[1]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p65
`rrf=0.0852 通道=bm25+dense bm25#14 dense#15 sim=0.5920`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> Also, under the advanced computing FDP rule in Sec.
> 734.9(h), foreign-produced 3A090.c items will be subject to the EAR if they meet the scope of that FDP rule.
> Under new 3A090.c, this IFR will control HBM having a `memory bandwidth density' greater than 2 GB per second per square millimeter (mm).
> All HBM stacks currently in production exceed this threshold.
> This IFR also adds a technical note to 3A090.c to define for purposes of this ECCN that `memory bandwidth density' is the memory bandwidth of the package or stack measured in GB per second divided by the area of the package or stack measured in square mm.

**[2]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p174
`rrf=0.0724 通道=bm25+dense bm25#6 dense#0 sim=0.6608`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> The following exports, reexports, or transfers (in- country) are only authorized under this License Exception HBM if the 3A090.c item has a memory bandwidth density less than 3.3 GB/s/ mm[supcaret]2 and both of the following conditions apply: (1) The 3A090.c items exported, reexported, or transferred to or within Macau or a destination specified in Country Group D:5 must be directly purchased by the designer of the co-packaged commodity not otherwise prohibited from receipt of the item; and (2) The 3A090.c items must be exported, reexported, or transferred (in-country) directly to the packaging site.

**[3]** BIS · 15 CFR 年度版（含 part 774 CCL） · § 740.25 License Exception High Bandwidth Memory · p332
`rrf=0.0717 通道=bm25+dense bm25#5 dense#2 sim=0.6606`
<https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml>

> The following exports, reexports, or transfers (in-country) are only authorized under this License Exception HBM if the 3A090.c item has a memory bandwidth density less than 3.3 GB/s/mm^2 and both of the following conditions apply: (1) The 3A090.c items exported, reexported, or transferred to or within Macau or a destination specified in Country Group D:5 must be directly purchased by the designer of the co-packaged commodity not otherwise prohibited from receipt of the item; and (2) The 3A090.c items must be exported, reexported, or transferred (in-country) directly to the packaging site.

**[4]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p67
`rrf=0.0626 通道=bm25+dense bm25#3 dense#79 sim=0.5461`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> Paragraph (a)(6)(i) (Exports, reexports, transfers (in- country) to or within Macau or Country Group D:5) is revised to designate the text in paragraph (a)(6)(i) as paragraph (a)(6)(i)(A) and add a new paragraph (a)(6)(i)(B) to set forth license requirements for high bandwidth memory (HBM) items specified in ECCNs 3A090.c, 3D001 (for 3A090.c), and 3E001 (for 3A090.c) when exported, reexported, or transferred (in-country) to or within Macau or a destination specified in Country Group D:5 in supplement no.
> 1 to part 740 of the EAR.

**[5]** BIS · 15 CFR 年度版（含 part 774 CCL） · § 742.6 Regional stability · p339
`rrf=0.0574 通道=bm25+dense bm25#8 dense#81 sim=0.5459`
<https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml>

> For the purposes of this paragraph, 'equivalent' means the item is listed on the country's export control list and the country applies the same license review policy.
> To receive assistance in determining countries with equivalent controls, you may submit an advisory opinion request in accordance with § 748.3(c) of the EAR.
> (B) High Bandwidth Memory (HBM).
> A license is required for items specified in ECCNs 3A090.c, 3D001 (for 3A090.c), and 3E001 (for 3A090.c) when exported, reexported, or transferred (in-country) to or within Macau or a destination specified in Country Group D:5 in supplement no.
> 1 to part 740 of the EAR.
> The license requirements in this paragraph (a)(6)(i)(B) do not apply to deemed exports or deemed reexports.

**[6]** BIS · Implementation of Additional Due Diligence Measures for Advanced Computing Integrated Circuits; Amendments and Clarifications; and Extension of Comment Period · p227
`rrf=0.0335 通道=改写 bm25#— dense#— sim=—`
<https://www.federalregister.gov/documents/full_text/text/2025/01/16/2025-00711.txt>

> High bandwidth memory (HBM) having a `memory bandwidth density' greater than 2 gigabytes per second per square millimeter.
> Technical Note 1 to 3A090.c: `Memory bandwidth density' is the memory bandwidth measured in gigabytes per second divided by the area of the package or stack measured in square millimeters.
> In the case where a stack is contained in a package, use the memory bandwidth of the packaged device and the area of the package.
> High bandwidth memory (HBM) includes dynamic random access memory integrated circuits, regardless of whether they conform to the JEDEC standards for high bandwidth memory (HBM), provided they have a `memory bandwidth density' greater than 2 gigabytes per second per square millimeter.

**[7]** BIS · Implementation of Additional Due Diligence Measures for Advanced Computing Integrated Circuits; Amendments and Clarifications; and Extension of Comment Period; Correction · p45
`rrf=0.0332 通道=改写 bm25#— dense#— sim=—`
<https://www.federalregister.gov/documents/full_text/text/2025/02/14/2025-02655.txt>

> High bandwidth memory (HBM) having a `memory bandwidth density' greater than 2 gigabytes per second per square millimeter.
> Technical Note 1 to 3A090.c: `Memory bandwidth density' is the memory bandwidth measured in gigabytes per second divided by the area of the package or stack measured in square millimeters.
> In the case where a stack is contained in a package, use the memory bandwidth of the packaged device and the area of the package.
> High bandwidth memory (HBM) includes dynamic random access memory integrated circuits, regardless of whether they conform to the JEDEC standards for high bandwidth memory (HBM), provided they have a `memory bandwidth density' greater than 2 gigabytes per second per square millimeter.

**[8]** BIS · 15 CFR 774 现行版（2026-09-24） · 3A090 · p319
`rrf=0.0331 通道=改写 bm25#— dense#— sim=—`
<https://www.ecfr.gov/api/versioner/v1/full/2026-09-24/title-15.xml?part=774>

> High bandwidth memory (HBM) having a 'memory bandwidth density' greater than 2 gigabytes per second per square millimeter.
> Technical Note 1 to 3A090.c: 'Memory bandwidth density' is the memory bandwidth measured in gigabytes per second divided by the area of the package or stack measured in square millimeters.
> In the case where a stack is contained in a package, use the memory bandwidth of the packaged device and the area of the package.
> High bandwidth memory (HBM) includes dynamic random access memory integrated circuits, regardless of whether they conform to the JEDEC standards for high bandwidth memory (HBM), provided they have a 'memory bandwidth density' greater than 2 gigabytes per second per square millimeter.

---

## 第 2 题 · 召回 ❌ 美光 只占 0/8 席（需 ≥4）｜答案 ✅ 答案合规

**问题**：美光最近一期财报里，关于 HBM 的收入、产能或资本开支有哪些表述？

- 库：A｜考察：表格块召回（课程 p24）。**`min_from_company={'美光':4}` 是 2026-10-04 才补上的**：原先这里写的是 `require_company=['美光']`，但 `judge()` **从来没读它**（结构判据只实现了 `min_companies`/`need_lib`/`forbid_lib`）——又是一个「声明了却没接线的开关」。于是本题实际只判 `HBM`，而 `HBM` 在库里 538 块，**任何块都能让判据过**。实测：8 个席里 SK 海力士占 6、三星 1、**美光只占 1**，而问题问的就是美光一家。补上后改为「美光须占 ≥4 席」——只要求「出现过」不够：8 条里出现 1 条也算出现。
- 实际进检索的查询（原问题 + 模型改写）：`美光最近一期财报里，关于 HBM 的收入、产能或资本开支有哪些表述？` ｜ `Micron HBM revenue capacity capex latest quarterly earnings` ｜ `Micron HBM3E HBM4 revenue outlook earnings call transcript` ｜ `美光 HBM 收入 产能 资本开支 财报`
- 判据原文：`['HBM']` → 命中 ['HBM']
- 附加结构判据：指定公司占席下限：美光≥4
- 实际来源构成：['cninfo', 'skhynix']
- 实际公司构成：['SK 海力士', '佰维存储']
- 召回 8 条，用时 5.2s

### 模型作答（非原文，须逐条核 [n]）

```
## 材料未覆盖

给定材料中**没有任何一份美光（Micron）的财报**，因此无法回答"美光最近一期财报中关于 HBM 收入、产能或资本开支的表述"。缺的是：美光自身的业绩发布材料（如财报新闻稿、季度业绩演示或 10-Q/10-K）。

材料中仅有两处提到美光，且都不是来自美光财报，也没有 HBM 收入/产能/资本开支的口径：

- 【材料 8】给出的是第三方统计的份额数据：「季度的DRAM 市场上，三星、SK 海力士、美光、南亚科技的市场份额分别为42.1%、30.8%、21.7%、1.7%」，以及「2023 年，SK 海力士以53%的市场份额领先HBM 市场，其次是三星（38%）和美光（9%）」。这是 TrendForce 集邦咨询的 HBM 市场份额，不是美光的收入或资本开支数字。

材料中所有 HBM 相关的产能、资本开支、收入表述均出自 SK 海力士（【材料 1】至【材料 6】），与美光无关。建议补充美光最近一期财报原文。
```

### 判分（两本账）

- **召回判定**：❌ 美光 只占 0/8 席（需 ≥4）
- **答案判定**：✅ 答案合规
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - `42.1` → 第 8 席
  - `30.8` → 第 8 席
  - `21.7` → 第 8 席
  - `1.7` → 第 8 席
- **未覆盖项**：召回：❌ 美光 只占 0/8 席（需 ≥4）
- 答案须点名的对象：美光（匹配域已抠掉问题原文，防判据被问题自己满足）

### 检索到的语料原文

**[1]** SK 海力士 · SK hynix FY2024 Q4 Earnings Results · p13
`rrf=0.0613 通道=+dense bm25#— dense#2 sim=0.6072`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/81727201766385339.pdf>

> ‘25, with target opening in Q2’27
> CapEx will be focused on products that have
> secured profitability, will flexibly adjust
> investments based on mkt.
> conditions
> At end of Yr.
> ‘24, finalized funding of approx.
> KRW 660bn under CHIPS Act
> 13
> Expect Yr.
> ‘25 revenue to grow over 100% YoY
> Rising demand from ASIC customers
> HBM3E 12Hi product support well in progress, expect 12Hi bit volume
> to crossover with 8Hi in 1H’25, as scheduled
> Developed industry’s 1st HBM3E 16Hi using Adv.
> MR-MUF in Nov.
> ‘24
> Will complete development and secure mass production readiness in
> Yr.
> ’25 for HBM4 12Hi, which will be mainstream product in Yr.
> ‘26
> Tech migration to adv.
> nodes for production of DDR5/LPDDR5
> Preparing various product lines, such as LPCAMM2 & ZUFS, that

**[2]** SK 海力士 · SK hynix FY2025 Q4 Earnings Results · p12
`rrf=0.0590 通道=+dense bm25#— dense#4 sim=0.5988`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/116964051831620258.pdf>

> Rapid progression of Yong-in Phase 1 Fab construction
> Cheong-ju P&T7 and Indiana Adv.
> PKG Fab on track
> Expect considerable increase in Yr.
> ’26 CapEx, but will
> continue to adhere to CapEx discipline
> 12
> Capable of reliably delivering both HBM3E & HBM4
> HBM4 mass production in progress in line with customer-agreed schedule
> Preparing to deliver optimized Custom HBM by strengthening collaboration with
> customers and partners
> Expanding production of high-value products including high-density SV DRAM
> Accelerating 1cnm migration to expand AI memory portfolio, including
> SoCAMM2 and GDDR7
> Maximizing product competitiveness with 321L migration
> Expanding AI storage capabilities leveraging Solidigm QLC eSSD
> Aiming to lead ultra-high-density AI storage mkt.
> with next-gen.
> 245TB product development
> 13

**[3]** SK 海力士 · SK hynix FY2024 Q3 Earnings Results · p10
`rrf=0.0576 通道=+dense bm25#— dense#41 sim=0.5417`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/77045741902433810.pdf>

> DRAM
> Q4 B/G: Mid-single% increase QoQ
> Through higher sales of HBM & SV DRAM
> Production will be focused on products that
> the company has clear competitive edge
> NAND
> Accelerate transition to leading-edge
> Q4 B/G: Low-teen% increase QoQ
> products while reducing production of legacy
> (incl.
> Solidigm)
> products that are showing slower demand
> Increase sales of eSSD products
> Yr.
> ‘25 infra capex to increase YoY due to
> construction of M15X & 1st fab in Yong-in
> M15X will be able to contribute to DRAM
> production from Yr.
> ‘26
> 10
> DRAM revenue share reached 30% in Q3, expect to reach 40% in Q4
> Bit shipment crossover between HBM3E and HBM3 in Q3
> HBM3E 12Hi shipments to start in Q4 as scheduled, expect 12Hi
> share to exceed half of total HBM3E shipments during 1H’25

**[4]** SK 海力士 · SK hynix FY2025 Q1 Earnings Results · p11
`rrf=0.0559 通道=+dense bm25#— dense#3 sim=0.6049`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/5001632852769028.pdf>

> Shipped world’s first HBM4 12Hi samples to customers in March ’25,
> will be ready for mass production within ’25, in time for customers’ demand
> Began shipping high-perform.
> memory module for AI PC, LPCAMM2, in Q1’25
> Preparing to support LP DRAM module for AI SV, SOCAMM, in time for
> market demand
> For NAND, continue profit-oriented operational decisions, and maintain
> prudent approach in CapEx spending
> 11
> Profitability
> Income Statement
> (Unit : KRW Billion)
> Revenue | ’25 Q1 17,639 | ’24 Q4 19,767 | ’24 Q1 12,430 | Q/Q -11% | Y/Y +42%
> Gross Profit | ’25 Q1 10,102 | ’24 Q4 10,366 | ’24 Q1 4,795 | Q/Q -3% | Y/Y +111%
> Operating Profit | ’25 Q1 7,441 | ’24 Q4 8,083 | ’24 Q1 2,886 | Q/Q -8% | Y/Y +158%
> EBITDA* | ’25 Q1 10,769 | ’24 Q4 11,249 | ’24 Q1 6,073 | Q/Q -4% | Y/Y +77%

**[5]** SK 海力士 · SK hynix FY2025 Q3 Earnings Results · p10
`rrf=0.0532 通道=+dense bm25#— dense#12 sim=0.5796`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/3127648149034921.pdf>

> products including HBM through Yr.
> ‘26
> Opened M15X ahead of schedule and begun equipment
> installation.
> Plan to speed up new capacity expansion
> We will accelerate tech migration to support demand for
> Conv.
> DRAM and NAND
> Yr.
> ‘26 Capex to increase YoY, we will continue optimal
> investment to meet demand while maintaining Capex
> discipline
> 10
> Completed Yr.
> ‘26 supply discussions with key customers
> Ready to supply HBM4, which fully meets customer performance requirements
> and supports highest speed in the industry
> Will start shipments of HBM4 in Q4 and further expand in Yr.
> ‘26
> 1cnm, which we have full product line-up, will expand in Yr.
> ’26 to support
> increasing customers’ demand
> 1cnm mass production progressing smoothly, and planning to accelerate
> migration to 1cnm in Yr.

**[6]** SK 海力士 · SK hynix FY2024 Q1 Earnings Results · p10
`rrf=0.0531 通道=+dense bm25#— dense#16 sim=0.5741`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/61321621157035970.pdf>

> Expect limited DRAM/NAND production
> growth in ‘24, as a result of conservative
> investments in ‘23, and more capa.
> allocated
> to produce HBM which has larger die size
> 10
> In March, began mass production/supply of 1bnm HBM3E
> Increase HBM3E supply in-line with customers’ demand
> Expand customer base using increased production capability
> Signed MOU with TSMC for development of HBM4 and
> collaboration on next generation packaging technology
> Represent 45%+ of PC, 60%+ of SV bit sales
> Strong sales of 128GB+ modules contributed to DDR5 sales
> 1bnm 32Gb DDR5 product to be launched to support high-
> density SV DRAM demand
> Sales of high-performance 16ch eSSD increased in Q1
> Solidigm’s QLC based high density eSSD will increase in
> demand due to growing needs for high performance, high

**[7]** 佰维存储 · 2026年半年度报告 · (二) 所属行业情况 · p25
`rrf=0.0515 通道=+dense bm25#— dense#8 sim=0.5909`
<http://static.cninfo.com.cn/finalpage/2026-08-25/1225497235.PDF>

> 深圳佰维存储科技股份有限公司 2026 年半年度报告
> 进行堆叠，并与GPU 一同进行封装，形成大容量、高带宽的DDR 组合阵列。
> HBM 可显著提高
> 带宽、容量和能效，已成为高性能GPU、AI 加速器及云厂商自研ASIC 的重要配套存储产品。
> Gartner 数据显示，2026 年HBM 市场规模将达到792.35 亿美元，同比增长超过130%。
> 随着
> AI 训练和推理负载增长，以及英伟达、AMD 和大型云服务商自研AI 芯片持续放量，预计HBM
> 市场规模在2027 年将超过1,000 亿美元，2028 年将达到1,527.69 亿美元，2026 年至2028 年复合
> 增速达到38.9%。
> HBM 具有超高带宽、3D 堆叠集成等特点，是AI 加速计算的核心内存方案。
> 随着AI 训练与
> 推理负载持续增长，AI 数据中心扩张带动HBM 容量与带宽需求上行，HBM3E 等高端服务器内
> 存需求保持旺盛。
> 在先进封装与HBM 标准升级的推动下，HBM 正从HBM3E 快速演进至HBM4，
> 公开路线图显示，下一代GPU/AI 加速器平台已开始导入HBM4，以提升系统内存带宽与能效表
> 现。
> 3、行业发展趋势
> （1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容
> 存储器产业链下游涵盖服务器/数据中心、智能手机、平板、电脑、网络通信设备、可穿戴设
> 备、物联网硬件、安防监控、工业控制、汽车电子等行业以及个人移动存储等多个领域，随着多
> 模态与Agent 应用渗透率提升，推动大模型推理需求上行，带来AI 服务器/数据中心侧对存储与
> 内存配置的结构性升级与需求增长。
> 与此同时，随着以OpenClaw 等为代表的代理式AI 能力不断
> 提升，端侧AI 应用有望加速落地，终端设备对存储与内存容量、带宽及能效的要求同步提高。
> 综

**[8]** 佰维存储 · 2024年半年度报告 · (二) 所属行业情况 · p35
`rrf=0.0506 通道=+dense bm25#— dense#0 sim=0.6192`
<http://static.cninfo.com.cn/finalpage/2024-08-23/1220952257.PDF>

> 季度的DRAM 市场上，三星、SK 海力士、美光、南亚科技的市场份额分别为42.1%、30.8%、
> 21.7%、1.7%。
> 受益于DRAM 价格的全面回升，以及HBM、DDR5 等产品的出货增长，2024 年
> 一季度全球DRAM 市场规模为170.6 亿美元，同比增长74.8%。
> （3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能Memory，打破了内存带宽
> 及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用晶圆级封装技术将多个DRAM 芯片进行堆叠，
> 形成大容量、高带宽的HBM 模块。
> HBM 与GPU/CPU 之间通过2.5D 晶圆级封装技术进行整合
> 互联，构建高性能计算芯片。
> 在高性能GPU 需求的推动下，HBM 已经成为AI 计算芯片的标
> 配。
> 根据Gartner 数据显示，2024 年，HBM 市场规模预计将达到123.2 亿美元，同比增长
> 284.2%。
> 随着AI 大模型的兴起，海量算力需求催生了对芯片内存容量和传输带宽的更高要求，
> 预计到2028 年，HBM 市场规模将增长至300.2 亿美元，年复合增长率为24.9%。
> TrendForce 集
> 邦咨询报告显示，2023 年，SK 海力士以53%的市场份额领先HBM 市场，其次是三星（38%）
> 和美光（9%）。
> HBM 广泛应用于高性能GPU 和AI 计算芯片中，以满足大规模数据处理和高速
> 传输的需求。
> AI 服务器对内存容量和带宽的要求推动了HBM 在各类高性能计算中的普及。
> 3、行业发展趋势
> 2024 年半年度报告
> （1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容
> 存储器产业链下游涵盖智能手机、平板电脑、计算机、网络通信设备、可穿戴设备、物联网
> 硬件、安防监控、工业控制、汽车电子等行业以及个人移动存储等多个领域，其中多个细分市场

---

## 第 3 题 · 召回 ✅ 召回命中｜答案 ❌ 答案有 1 个数在语料里找不到出处：96790

**问题**：2024 年 12 月以前 HBM 受出口管制吗？是哪一份规则改变了这一点？

- 库：B｜考察：版本陷阱（课程 p50）：管制前后是**两份不同的规则文本**，得说清是哪一份改的。判据用 FR 文号 **96790**（全库仅 5 块）而不是 `2024`——后者出现 20,831 次，**写「2024」等于没写**，任何块都能让它过。
- 实际进检索的查询（原问题 + 模型改写）：`2024 年 12 月以前 HBM 受出口管制吗？是哪一份规则改变了这一点？` ｜ `HBM export controls before December 2024 EAR` ｜ `BIS advanced computing semiconductor export controls HBM December 2024 rule` ｜ `3A090 high bandwidth memory HBM export control rule change`
- 判据原文：`['96790']` → 命中 ['96790']
- 附加结构判据：必须含 库B≥1
- 实际来源构成：['ecfr', 'fedreg', 'govinfo']
- 实际公司构成：['BIS']
- 召回 8 条，用时 10.4s

### 模型作答（非原文，须逐条核 [n]）

```
**直接回答：材料未覆盖「2024 年 12 月以前 HBM 是否受出口管制」这一点**，也没有任何一条材料明确说「是哪一份规则（日期/联邦公报引文）新增了 HBM 管制」。缺的是：① 说明 HBM 在新增 3A090.c 之前管制状态的文本；② 把 HBM 新增管制与某个具体日期或联邦公报引文对应起来的表述。所以不能给出「有/没有」的结论。

材料能支持的部分只有「新增了管制」这一事实，以及新增的载体：

- 材料 1：BIS added a control on HBM，目的是 prevent the PRC, as well as other destinations of concern, from producing advanced computing ICs incorporating HBM。[1]
- 材料 2：Under ECCN 3A090, this IFR adds a new items paragraph .c to impose a new CCL-based control for certain HBM commodities；foreign-produced 3A090.c items 受 advanced computing FDP rule（Sec. 734.9(h)）约束。[2]
- 材料 4：BIS imposed new controls on certain high- bandwidth memory (HBM) commodities, which are critical to AI training and inference at scale and a key component of advanced computing ICs。[4]

关于时间，材料里唯一出现的 2024 年 12 月是：

- 材料 7：Mostly recently, BIS updated these controls in December 2024 (89 FR 96790, December 5, 2024)。[7]

但材料 7 这句是在讲 advanced computing 相关管制的整体更新，**没有提到 HBM**。含 材料 1、材料 2 的那份文件标题是《Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items》，但材料中**没有给出该文件的联邦公报引文或日期**，因此不能据此把它等同于 材料 7 中的 89 FR 96790。这一步对应关系需要材料之外的证据，我不做。

补充两条材料中确实存在的 HBM 门槛（供参考，不用于回答上述时间问题）：

- 材料 8：HBM 指 'memory bandwidth density' greater than 2 gigabytes per second per square millimeter 的 DRAM 集成电路。[8]
- 材料 3：License Exception HBM 仅授权 3A090.c item 的 memory bandwidth density less than 3.3 GB/s/mm[supcaret]2。[3]
```

### 判分（两本账）

- **召回判定**：✅ 召回命中
- **答案判定**：❌ 答案有 1 个数在语料里找不到出处：96790
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - `734.9` → 第 2 席
  - `96790,` → 第 7 席
  - `5,` → 第 7 席
  - `3.3` → 第 3 席
  - ⚠️ `96790` → **语料里找不到出处**（模型自己带来的数）
- **未覆盖项**：答案里无出处的数：96790
- ⚠️ **本题未设答案专名判据**（问题没有要求点名某个对象），答案栏只做数字归属核对——**不冒充「答案已判过」**。

### 检索到的语料原文

**[1]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p65
`rrf=0.0653 通道=bm25+dense bm25#61 dense#2 sim=0.7193`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> In order to more effectively address the national security and foreign policy concerns which are being addressed under ECCN 3A090, BIS added a control on HBM to prevent the PRC, as well as other destinations of concern, from producing advanced computing ICs incorporating HBM.
> If these HBM stacks are incorporated into an IC or a higher-level commodity, such as a computer or electronic assembly, then ECCN 3A090.a, .b, 4A090.a or .b, or the respective .z controls may impose controls on the commodities containing HBM.
> The national security and foreign policy concerns are focused on HBM, as covered under 3A090.c, that is exported as a stand-alone commodity (i.e., when not incorporated into a higher-level commodity).

**[2]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p63
`rrf=0.0608 通道=+dense bm25#— dense#13 sim=0.6427`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> BIS uses the bandwidth density--rather than just the bandwidth--to ensure controls will still apply if an IC uses a larger quantity of smaller HBM chips at little additional cost.
> As indigenous PRC advanced computing ICs rely upon imported HBM, new ECCN 3A090.c implements restrictions to slow PRC attempts to indigenize advanced AI chip production, which, as explained above,
> [[Page 96800]]
> raises national security and foreign policy concerns.
> Under ECCN 3A090, this IFR adds a new items paragraph .c to impose a new CCL-based control for certain HBM commodities.
> Also, under the advanced computing FDP rule in Sec.
> 734.9(h), foreign-produced 3A090.c items will be subject to the EAR if they meet the scope of that FDP rule.

**[3]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p69
`rrf=0.0590 通道=bm25+dense bm25#43 dense#0 sim=0.7423`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> 1 to part 740, without an ultimate parent headquartered in Macau or a destination specified in Country Group D:5 of supplement no.
> 1 to part 740.
> No other exporter, reexporter, or transferor may use License Exception HBM.
> This IFR adds paragraph (c) (Conditions) to specify that exports, reexports, or transfers (in-country) are authorized under this License Exception HBM only when the 3A090.c item has a memory bandwidth density less than 3.3 GB/s/mm[supcaret]2.
> Only HBM at less than this parameter may be authorized under License Exception HBM.
> HBM at equal to or greater than this parameter referenced under paragraph (c) are of greater sensitivity, so those HBM of greater sensitivity are not eligible for HBM to ensure U.S.
> national security and foreign policy interests are protected.

**[4]** BIS · Framework for Artificial Intelligence Diffusion · p45
`rrf=0.0565 通道=+dense bm25#— dense#15 sim=0.6405`
<https://www.federalregister.gov/documents/full_text/text/2025/01/15/2025-00636.txt>

> Specifically, BIS imposed new controls on certain high- bandwidth memory (HBM) commodities, which are critical to AI training and inference at scale and a key component of advanced computing ICs.
> BIS also imposed controls on additional SME capable of producing advanced computing ICs (e.g., certain etch, deposition, lithography tools, etc.) and on software that can enhance the capabilities of such SME or can be used to design advanced computing ICs.
> These previous controls reflect BIS's determination--made in conjunction with experts from across the U.S.
> government--that the export of even small quantities of advanced computing ICs to specific destinations and end users of concern pose significant risks to U.S.
> national security and foreign policy interests.

**[5]** BIS · 15 CFR 年度版（含 part 774 CCL） · § 740.25 License Exception High Bandwidth Memory · p332
`rrf=0.0556 通道=+dense bm25#— dense#1 sim=0.7314`
<https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml>

> § 740.25 License Exception High Bandwidth Memory (HBM).
> (a) Scope.
> This License Exception High Bandwidth Memory (HBM) authorizes the export, reexport, or transfer (in-country) of items specified in ECCN 3A090.c on the Commerce Control List (CCL) in supplement no.
> 1 to part 774 if all terms and conditions within this section are met.
> (b) Exporter, reexporter, transferor.
> The exporter, reexporter, or transferor must be headquartered in the United States or a destination specified in Country Group A:5 of supplement no.
> 1 to this part, without an ultimate parent headquartered in Macau or a destination specified in Country Group D:5 of supplement no.
> 1 to this part.
> (c) Conditions.

**[6]** BIS · 15 CFR 年度版（含 part 774 CCL） · § 742.6 Regional stability · p339
`rrf=0.0552 通道=+dense bm25#— dense#9 sim=0.6696`
<https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml>

> For the purposes of this paragraph, 'equivalent' means the item is listed on the country's export control list and the country applies the same license review policy.
> To receive assistance in determining countries with equivalent controls, you may submit an advisory opinion request in accordance with § 748.3(c) of the EAR.
> (B) High Bandwidth Memory (HBM).
> A license is required for items specified in ECCNs 3A090.c, 3D001 (for 3A090.c), and 3E001 (for 3A090.c) when exported, reexported, or transferred (in-country) to or within Macau or a destination specified in Country Group D:5 in supplement no.
> 1 to part 740 of the EAR.
> The license requirements in this paragraph (a)(6)(i)(B) do not apply to deemed exports or deemed reexports.

**[7]** BIS · Framework for Artificial Intelligence Diffusion · p43
`rrf=0.0487 通道=+dense bm25#— dense#21 sim=0.6053`
<https://www.federalregister.gov/documents/full_text/text/2025/01/15/2025-00636.txt>

> 748.15 to facilitate the export of advanced computing ICs and related items to qualified data centers (89 FR 80080, October 2, 2024).
> Mostly recently, BIS updated these controls in December 2024 (89 FR 96790, December 5, 2024).
> Specifically, in October 2022, BIS published an interim final rule (87 FR 62186) which made critical changes to the EAR in two areas.
> First, the rule imposed additional export controls on certain advanced computing ICs, computer commodities that contain such ICs, and certain SME and parts and components needed to produce those and other advanced ICs.
> Specifically,
> [[Page 4548]]
> the controls required a license before exporting or reexporting those items to the PRC or to certain entities on the Entity List (supplement no.
> 4 to part 744).

**[8]** BIS · 15 CFR 774 现行版（2026-09-24） · 3A090 · p319
`rrf=0.0395 通道=bm25+dense bm25#74 dense#38 sim=0.5802`
<https://www.ecfr.gov/api/versioner/v1/full/2026-09-24/title-15.xml?part=774>

> High bandwidth memory (HBM) includes dynamic random access memory integrated circuits, regardless of whether they conform to the JEDEC standards for high bandwidth memory (HBM), provided they have a 'memory bandwidth density' greater than 2 gigabytes per second per square millimeter.
> This control does not cover co-packaged integrated circuits with both HBM and logic integrated circuit where the dominant function of the co-packaged integrated circuit is processing.
> It does include HBM permanently affixed to a logic integrated circuit designed as a control interface and incorporating a physical layer (PHY) function.

---

## 第 4 题 · 召回 ❌ 缺判据原文 ['营业总收入']｜答案 ✅ 答案合规

**问题**：江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？

- 库：A｜考察：口径陷阱（课程 p29）。判据从 `营业`（6,269 块）收窄到 `营业总收入`（101 块）——口径题要的是那个具体科目名，不是「营业」两个字。**`must_ans` 要求答案里两个科目名都出现**：问的是**两者的差别**，答案只说其中一个，等于把问题答了一半。（2026-10-12 加：这两个名字相近，必须**各说各的**，见 data/口径表.md）
- 实际进检索的查询（原问题 + 模型改写）：`江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？` ｜ `江波龙 年报 营业收入 营业总收入 口径差异` ｜ `江波龙 财务报表附注 营业收入 营业总收入 确认标准` ｜ `Longsys annual report operating revenue total operating revenue difference`
- 判据原文：`['营业总收入']` → 命中 无
- 附加结构判据：无
- 实际来源构成：['cninfo']
- 实际公司构成：['江波龙']
- 表格定位通道（按**行标签**锚定，正文提到科目名不算）：锚 `营业总收入`、`营业收入`；限定公司 江波龙；进前 8 的 2 席
- 召回 8 条，用时 7.3s

### 模型作答（非原文，须逐条核 [n]）

```
## 结论：材料未覆盖

全部 8 条材料中**没有出现「营业总收入」这个词**，也没有任何对「营业收入」与「营业总收入」两个口径差异的说明或定义。因此无法回答两者差在哪里。

### 材料里实际出现的只有「营业收入」

- 材料 1：江波龙 / 2025年年度报告 / 四、 主营业务分析 / p29 中出现「（1） 营业收入构成 营业收入整体情况 单位：元」，并按境内、直销、经销列示 [1]
- 材料 2：江波龙 / 2025年半年度报告 / 三、 主营业务分析 / p25 中出现「营业收入 | 本报告期 10,195,655,370.19 | 上年同期 9,038,807,150.58 | 同比增减 12.80%」 [2]
- 材料 5：江波龙 / 2025年半年度报告 / 八、 每股收益： / p80 的母公司利润表中出现「一、营业收入 | 2025 年半年度 2,996,680,598.97 | 2024 年半年度 3,305,722,155.10」 [5]

### 材料中唯一提到「口径」的地方，与此问题无关

材料 1 和材料 3 中有一句：「公司主营业务数据统计口径在报告期发生调整的情况下，公司最近1 年按报告期末口径调整后的主营业务数据 □适用 不适用」[1][3]。这里说的是**主营业务数据统计口径**，不是「营业总收入」口径，也未对口径内容作任何展开。

### 缺什么

要回答本问题，至少需要材料中包含以下之一，而目前都没有：

1. 利润表或「主要会计数据」中「营业总收入」这一行的数值或列示（材料 1、2、5 的表格中均未出现该项）[1][2][5]；
2. 年报中对「营业收入」与「营业总收入」定义/包含范围差异的文字说明。

因此，任何关于两者差异（例如是否含利息收入、其他业务收入等）的说法，材料均未覆盖，不能给出。
```

### 判分（两本账）

- **召回判定**：❌ 缺判据原文 ['营业总收入']
- **答案判定**：✅ 答案合规
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - `10,195,655,370.19` → 第 2 席
  - `9,038,807,150.58` → 第 2 席
  - `12.80` → 第 2 席
  - `2,996,680,598.97` → 第 5 席
  - `3,305,722,155.10` → 第 5 席
- **未覆盖项**：召回：❌ 缺判据原文 ['营业总收入']
- 答案须点名的对象：营业收入、营业总收入（匹配域已抠掉问题原文，防判据被问题自己满足）

### 检索到的语料原文

**[1]** 江波龙 · 2025年年度报告 · 四、 主营业务分析 · p29
`rrf=0.0617 通道=bm25+dense bm25#4 dense#0 sim=0.6421`
<http://static.cninfo.com.cn/finalpage/2026-04-28/1225214128.PDF>

> （1） 营业收入构成
> 营业收入整体情况
> 单位：元
> 29
> 深圳市江波龙电子股份有限公司2025 年年度报告全文
> 境内 | 7,547,874,360.03 | 33.15% | 5,038,831,399.50 | 28.85% | 49.79%
> 分销售模式
> 直销 | 14,558,302,002.05 | 63.95% | 10,055,717,804.16 | 57.58% | 44.78%
> 经销 | 8,207,867,988.50 | 36.05% | 7,407,932,467.98 | 42.42% | 10.80%
> （2） 占公司营业收入或营业利润10%以上的行业、产品、地区、销售模式的情况
> 适用 □不适用
> 单位：元
> 公司主营业务数据统计口径在报告期发生调整的情况下，公司最近1 年按报告期末口径调整后的主营业务数据
> □适用 不适用
> （3） 公司实物销售收入是否大于劳务收入
> 是 □否
> 相关数据同比发生变动30%以上的原因说明
> □适用 不适用
> （4） 公司已签订的重大销售合同、重大采购合同截至本报告期的履行情况
> □适用 不适用
> 30
> 深圳市江波龙电子股份有限公司2025 年年度报告全文
> （5） 营业成本构成
> 产品分类
> 单位：元
> 说明
> 无
> （6） 报告期内合并范围是否发生变动
> 是 □否
> 详见本报告“第八节财务报告”之“九、合并范围的变更”。
> （7） 公司报告期内业务、产品或服务发生重大变化或调整有关情况
> □适用 不适用
> （8） 主要销售客户和主要供应商情况
> 公司主要销售客户情况
> 前五名客户合计销售金额（元） | 6,593,526,982.34
> 前五名客户合计销售金额占年度销售总额比例 | 28.96%
> 前五名客户销售额中关联方销售额占年度销售总额比例 | 1.36%
> 公司前5 大客户资料
> 主要客户其他情况说明
> □适用 不适用
> 公司主要供应商情况

**[2]** 江波龙 · 2025年半年度报告 · 三、 主营业务分析 · p25
`rrf=0.0519 通道=+dense+锚定 bm25#— dense#1 sim=0.6356`
<http://static.cninfo.com.cn/finalpage/2025-08-23/1224559911.PDF>

> 三、主营业务分析
> 概述
> 参见“一、报告期内公司从事的主要业务”相关内容。
> 主要财务数据同比变动情况
> 单位：元
> 营业收入 | 本报告期 10,195,655,370.19 | 上年同期 9,038,807,150.58 | 同比增减 12.80%
> 营业成本 | 本报告期 8,874,758,785.95 | 上年同期 6,913,848,654.64 | 同比增减 28.36%
> 销售费用 | 本报告期 415,501,277.58 | 上年同期 343,401,450.66 | 同比增减 21.00%
> 管理费用 | 本报告期 260,240,844.20 | 上年同期 306,447,854.51 | 同比增减 -15.08%
> 财务费用 | 本报告期 68,963,675.89 | 上年同期 165,830,784.24 | 同比增减 -58.41% | 变动原因 主要系汇兑损益变动的影响所致
> 所得税费用 | 本报告期 15,644,647.88 | 上年同期 111,333,239.86 | 同比增减 -85.95% | 变动原因 主要系利润减少导致所得税减少
> 研发投入 | 本报告期 445,738,812.10 | 上年同期 475,449,778.38 | 同比增减 -6.25%
> 经营活动产生的现金流量净额 | 本报告期 692,900,395.33 | 上年同期 -1,415,184,933.34 | 同比增减 148.96% | 变动原因 主要系销售商品提供劳务收到的现金增加以及购买商品、接受劳务支付的现金减少所致
> 投资活动产生的现金流量净额 | 本报告期 -528,251,120.68 | 上年同期 -461,452,861.44 | 同比增减 -14.48%
> 25
> 深圳市江波龙电子股份有限公司2025 年半年度报告全文

**[3]** 江波龙 · 2024年年度报告 · 三、 核心竞争力分析 · p28
`rrf=0.0400 通道=bm25+dense bm25#0 dense#50 sim=0.5860`
<http://static.cninfo.com.cn/finalpage/2025-03-21/1222976786.pdf>

> 外客户的优势，以及自研技术、综合存储产品和海外制造的能力，扩大公司的海外市场份额，为公司国际业务的中长期发展奠
> 定坚实基础。
> 从更长期的角度来看，Zilia 为代表的江波龙国际供应链平台，将为我国国产存储晶圆产能参与国际市场竞争提供
> 全新的解决思路及支撑平台。
> 28
> 深圳市江波龙电子股份有限公司2024 年年度报告全文
> 四、主营业务分析
> 1、概述
> 参见“二、报告期内公司从事的主要业务”相关内容。
> 2、收入与成本
> （1） 营业收入构成
> 营业收入整体情况
> 单位：元
> （2） 占公司营业收入或营业利润10%以上的行业、产品、地区、销售模式的情况
> 适用 □不适用
> 单位：元
> 29
> 深圳市江波龙电子股份有限公司2024 年年度报告全文
> 公司主营业务数据统计口径在报告期发生调整的情况下，公司最近1 年按报告期末口径调整后的主营业务数据
> □适用 不适用
> （3） 公司实物销售收入是否大于劳务收入
> 是 □否
> 相关数据同比发生变动30%以上的原因说明
> 适用 □不适用
> 公司 2024 年产品销售量、生产量、库存量较 2023 年有较大幅度增加，主要系公司报告期内销售收入增加所致。
> （4） 公司已签订的重大销售合同、重大采购合同截至本报告期的履行情况
> □适用 不适用
> （5） 营业成本构成
> 产品分类
> 单位：元
> 说明
> 无
> （6） 报告期内合并范围是否发生变动
> 是 □否
> 详见本报告“第十节财务报告”之“九、合并范围的变更”。
> （7） 公司报告期内业务、产品或服务发生重大变化或调整有关情况
> □适用 不适用
> 30
> 深圳市江波龙电子股份有限公司2024 年年度报告全文
> （8） 主要销售客户和主要供应商情况
> 公司主要销售客户情况
> 会计师事务所名称 前五名客户合计销售金额（元） | 安永华明会计师事务所（特殊普通合伙） 6,417,957,307.62

**[4]** 江波龙 · 深圳市江波龙电子股份有限公司2024年年度报告（更正后） · 三、 核心竞争力分析 · p28
`rrf=0.0397 通道=bm25+dense bm25#1 dense#49 sim=0.5860`
<http://static.cninfo.com.cn/finalpage/2025-05-30/1223733785.PDF>

> 外客户的优势，以及自研技术、综合存储产品和海外制造的能力，扩大公司的海外市场份额，为公司国际业务的中长期发展奠
> 定坚实基础。
> 从更长期的角度来看，Zilia 为代表的江波龙国际供应链平台，将为我国国产存储晶圆产能参与国际市场竞争提供
> 全新的解决思路及支撑平台。
> 28
> 深圳市江波龙电子股份有限公司2024 年年度报告全文
> 四、主营业务分析
> 1、概述
> 参见“二、报告期内公司从事的主要业务”相关内容。
> 2、收入与成本
> （1） 营业收入构成
> 营业收入整体情况
> 单位：元
> （2） 占公司营业收入或营业利润10%以上的行业、产品、地区、销售模式的情况
> 适用 □不适用
> 单位：元
> 29
> 深圳市江波龙电子股份有限公司2024 年年度报告全文
> 公司主营业务数据统计口径在报告期发生调整的情况下，公司最近1 年按报告期末口径调整后的主营业务数据
> □适用 不适用
> （3） 公司实物销售收入是否大于劳务收入
> 是 □否
> 相关数据同比发生变动30%以上的原因说明
> 适用 □不适用
> 公司 2024 年产品销售量、生产量、库存量较 2023 年有较大幅度增加，主要系公司报告期内销售收入增加所致。
> （4） 公司已签订的重大销售合同、重大采购合同截至本报告期的履行情况
> □适用 不适用
> （5） 营业成本构成
> 产品分类
> 单位：元
> 说明
> 无
> （6） 报告期内合并范围是否发生变动
> 是 □否
> 详见本报告“第十节财务报告”之“九、合并范围的变更”。
> （7） 公司报告期内业务、产品或服务发生重大变化或调整有关情况
> □适用 不适用
> 30
> 深圳市江波龙电子股份有限公司2024 年年度报告全文
> （8） 主要销售客户和主要供应商情况
> 公司主要销售客户情况
> 会计师事务所名称 前五名客户合计销售金额（元） | 安永华明会计师事务所（特殊普通合伙） 6,417,957,307.62

**[5]** 江波龙 · 2025年半年度报告 · 八、 每股收益： · p80
`rrf=0.0350 通道=+dense+锚定 bm25#— dense#48 sim=0.5864`
<http://static.cninfo.com.cn/finalpage/2025-08-23/1224559911.PDF>

> 本期发生同一控制下企业合并的，被合并方在合并前实现的净利润为：0.00 元，上期被合并方实现的净利润为：0.00 元。
> 法定代表人：蔡华波主管会计工作负责人：朱宇会计机构负责人：黎玉华
> 4、母公司利润表
> 单位：元
> 一、营业收入 | 2025 年半年度 2,996,680,598.97 | 2024 年半年度 3,305,722,155.10
> 80
> 深圳市江波龙电子股份有限公司2025 年半年度报告全文
> 减：营业成本 | 2025 年半年度 2,822,417,082.49 | 2024 年半年度 2,764,412,842.00
> 税金及附加 | 2025 年半年度 1,891,768.49 | 2024 年半年度 2,797,963.89
> 销售费用 | 2025 年半年度 77,364,873.43 | 2024 年半年度 94,995,198.78
> 管理费用 | 2025 年半年度 76,676,340.14 | 2024 年半年度 88,294,549.19
> 研发费用 | 2025 年半年度 64,071,997.12 | 2024 年半年度 84,027,696.91
> 财务费用 | 2025 年半年度 79,955,032.80 | 2024 年半年度 67,717,828.49
> 其中：利息费用 | 2025 年半年度 78,588,510.76 | 2024 年半年度 67,139,011.89
> 利息收入 | 2025 年半年度 1,473,468.71 | 2024 年半年度 582,022.17
> 加：其他收益 | 2025 年半年度 7,739,262.31 | 2024 年半年度 9,843,586.58
> 投资收益（损失以“—”号填列） | 2025 年半年度 -12,183.57
> 其中：对联营企业和合营企业的投资收益
> 以摊余成本计量的金融资产终止确认收益

**[6]** 江波龙 · 2025年半年度报告 · 十、 在其他主体中的权益 · p155
`rrf=0.0347 通道=+dense bm25#— dense#2 sim=0.6252`
<http://static.cninfo.com.cn/finalpage/2025-08-23/1224559911.PDF>

> 元成 | 营业收入 244,620,94 2.64 | 净利润 - 2,425,508.3 6 | 经营活动现金流量 - 25,336,711. 42 | 营业收入 210,782,62 5.51 | 净利润 4,346,569.0 5 | 经营活动现金流量 4,454,079.1 2
> zilia | 营业收入 1,387,853,4 03.42 | 净利润 142,160,54 2.97 | 经营活动现金流量 73,437,480. 10 | 营业收入 991,261,27 1.59 | 净利润 27,895,908. 47 | 经营活动现金流量 - 36,569,785. 01
> 其他说明：
> 无
> （4）使用企业集团资产和清偿企业集团债务的重大限制
> 无
> （5）向纳入合并财务报表范围的结构化主体提供的财务支持或其他支持
> 无
> 其他说明：
> 无
> 2、在合营企业或联营企业中的权益
> （1）重要的合营企业或联营企业
> 持股比例 直接 | 持股比例 间接
> 155
> 深圳市江波龙电子股份有限公司2025 年半年度报告全文
> 在合营企业或联营企业的持股比例不同于表决权比例的说明：
> 持有20%以下表决权但具有重大影响，或者持有20%或以上表决权但不具有重大影响的依据：
> （2）不重要的合营企业和联营企业的汇总财务信息
> 单位：元
> 合营企业：
> 下列各项按持股比例计算的合计数
> 联营企业：
> 投资账面价值合计 | 期末余额/本期发生额 30,000,000.00
> 下列各项按持股比例计算的合计数
> --净利润 | 期末余额/本期发生额 0.00
> --其他综合收益 | 期末余额/本期发生额 0.00
> --综合收益总额 | 期末余额/本期发生额 0.00
> 其他说明
> 无
> 十一、政府补助
> 1、报告期末按应收金额确认的政府补助
> □适用不适用
> 未能在预计时点收到预计金额的政府补助的原因
> □适用不适用

**[7]** 江波龙 · 深圳市江波龙电子股份有限公司2024年年度报告（更正后） · p1
`rrf=0.0341 通道=+dense bm25#— dense#6 sim=0.6201`
<http://static.cninfo.com.cn/finalpage/2025-05-30/1223733785.PDF>

> 深圳市江波龙电子股份有限公司
> 2024 年年度报告
> 公告编号：2025-010
> 2025 年3 月
> 1

**[8]** 江波龙 · 2024年年度报告 · p1
`rrf=0.0340 通道=+dense bm25#— dense#5 sim=0.6201`
<http://static.cninfo.com.cn/finalpage/2025-03-21/1222976786.pdf>

> 深圳市江波龙电子股份有限公司
> 2024 年年度报告
> 公告编号：2025-010
> 2025 年3 月
> 1

---

## 第 5 题 · 召回 ✅ 召回命中｜答案 ✅ 答案合规

**问题**：出口管制对内存市场的影响涉及哪几个方面？

- 库：A+B｜考察：多主题揉成一个向量（课程 p36）。既然问「影响涉及哪几个方面」，就得**同时**有规则文本和厂商财报两边，否则答案只有管制条文的半边。
- 实际进检索的查询（原问题 + 模型改写）：`出口管制对内存市场的影响涉及哪几个方面？` ｜ `export controls memory market impact DRAM HBM supply chain` ｜ `EAR CCL memory bandwidth density performance parameters 3A090.c` ｜ `内存出口管制 市场影响 供给 价格 产能`
- 判据原文：`['HBM']` → 命中 ['HBM']
- 附加结构判据：必须含 库A≥1、库B≥1
- 实际来源构成：['cninfo', 'fedreg', 'govinfo', 'samsung']
- 实际公司构成：['BIS', '三星电子', '佰维存储']
- 召回 10 条，用时 25.1s

### 模型作答（非原文，须逐条核 [n]）

> ⚠️ 作答失败：思考链吃光了 max_tokens，没留下正文（max_tokens=4000，思考 9179 字）——调大 max_tokens

```
(无)
```

### 判分（两本账）

- **召回判定**：✅ 召回命中
- **答案判定**：✅ 答案合规
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - 本答案没有给出数值型数字（年份、个数这类不算——它们不进这项核对）
- **未覆盖项**：无
- ⚠️ **本题未设答案专名判据**（问题没有要求点名某个对象），答案栏只做数字归属核对——**不冒充「答案已判过」**。

### 检索到的语料原文

**[1]** BIS · 15 CFR 年度版（含 part 774 CCL） · § 740.25 License Exception High Bandwidth Memory · p332
`rrf=0.0503 通道=+dense bm25#— dense#9 sim=0.6145`
<https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml>

> § 740.25 License Exception High Bandwidth Memory (HBM).
> (a) Scope.
> This License Exception High Bandwidth Memory (HBM) authorizes the export, reexport, or transfer (in-country) of items specified in ECCN 3A090.c on the Commerce Control List (CCL) in supplement no.
> 1 to part 774 if all terms and conditions within this section are met.
> (b) Exporter, reexporter, transferor.
> The exporter, reexporter, or transferor must be headquartered in the United States or a destination specified in Country Group A:5 of supplement no.
> 1 to this part, without an ultimate parent headquartered in Macau or a destination specified in Country Group D:5 of supplement no.
> 1 to this part.
> (c) Conditions.

**[2]** BIS · Implementation of Additional Due Diligence Measures for Advanced Computing Integrated Circuits; Amendments and Clarifications; and Extension of Comment Period · p70
`rrf=0.0479 通道=+dense bm25#— dense#0 sim=0.6636`
<https://www.federalregister.gov/documents/full_text/text/2025/01/16/2025-00711.txt>

> As such, it does not restrict exports, reexports and transfers (in-country) of items covered by Sec.
> 744.23(a)(2) and the activities of U.S.
> persons Sec.
> 744.6 (c)(2)(i) to high bandwidth memory and other advanced DRAM applications.
> Accordingly, this update revises the cell area and memory density parameters to be consistent with production standards in the DRAM industry for the 18 nm half-pitch node, rather than the IRDS definition of ``18 nm half-pitch,'' which is based on a theoretical model, rather than actual, physical characteristics of DRAM memory.
> This revision imposes end use and U.S.
> persons controls at DRAM facilities not previously controlled by the definition of DRAM in the December 5, 2024 FDP IFR.
> c.

**[3]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p67
`rrf=0.0479 通道=+dense bm25#— dense#3 sim=0.6244`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> Paragraph (a)(6)(i) (Exports, reexports, transfers (in- country) to or within Macau or Country Group D:5) is revised to designate the text in paragraph (a)(6)(i) as paragraph (a)(6)(i)(A) and add a new paragraph (a)(6)(i)(B) to set forth license requirements for high bandwidth memory (HBM) items specified in ECCNs 3A090.c, 3D001 (for 3A090.c), and 3E001 (for 3A090.c) when exported, reexported, or transferred (in-country) to or within Macau or a destination specified in Country Group D:5 in supplement no.
> 1 to part 740 of the EAR.

**[4]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p171
`rrf=0.0465 通道=+dense bm25#— dense#20 sim=0.5876`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> These license exceptions may be used provided the export, reexport, or transfer (in-country) meets all of the applicable criteria identified under this paragraph (a) and none of the restrictions in paragraph (b) of this section.
> * * * * *
> 0 13.
> Sections 740.25 and 740.26 are added to read as follows:
> Sec.
> 740.25 License Exception High Bandwidth Memory (HBM).
> (a) Scope.
> This License Exception High Bandwidth Memory (HBM) authorizes the export, reexport, or transfer (in-country) of items specified in ECCN 3A090.c on the Commerce Control List (CCL) in supplement no.
> 1 to part 774 if all terms and conditions within this section are met.
> (b) Exporter, reexporter, transferor.

**[5]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p69
`rrf=0.0444 通道=+dense bm25#— dense#6 sim=0.6177`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> 1 to part 740, without an ultimate parent headquartered in Macau or a destination specified in Country Group D:5 of supplement no.
> 1 to part 740.
> No other exporter, reexporter, or transferor may use License Exception HBM.
> This IFR adds paragraph (c) (Conditions) to specify that exports, reexports, or transfers (in-country) are authorized under this License Exception HBM only when the 3A090.c item has a memory bandwidth density less than 3.3 GB/s/mm[supcaret]2.
> Only HBM at less than this parameter may be authorized under License Exception HBM.
> HBM at equal to or greater than this parameter referenced under paragraph (c) are of greater sensitivity, so those HBM of greater sensitivity are not eligible for HBM to ensure U.S.
> national security and foreign policy interests are protected.

**[6]** 佰维存储 · 2024年年度报告 · (三) 所处行业情况 · p48
`rrf=0.0409 通道=bm25+dense bm25#61 dense#7 sim=0.6168`
<http://static.cninfo.com.cn/finalpage/2025-04-30/1223427605.PDF>

> 电子设备/服务器需要存储的数据量也越来越庞大，NAND Flash 需求量巨大，市场前景广阔。
> 2）DRAM 行业概况
> DRAM 是动态随机存取存储器，DRAM 的特征是读写速度快、延迟低，但掉电后数据会丢失，
> 常用于计算系统的运行内存（Memory）。
> 目前全球主要的DRAM IDM 原厂为三星、SK 海力士
> 和美光。
> 根据CFM 数据显示，2024 年第三季度的DRAM 市场上，三星、SK 海力士、美光、南
> 亚科技的市场份额分别为39.5%、34.7%、20.6%、1.0%。
> 根据TrendForce 报告，得益于数据中心
> 的DDR5 及HBM（高带宽内存）需求上升，2024 年全球DRAM 市场规模为958.63 亿美元，同
> 比增长85%。
> 3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能Memory，打破了内存带宽
> 及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用先进封装将多个DRAM 芯片进行堆叠，并与GPU
> 一同进行封装，形成大容量、高带宽的DDR 组合阵列。
> 在高性能GPU 需求的推动下，HBM 已
> 经成为AI 计算芯片的标配。
> 根据Gartner 数据显示，2024 年，HBM 市场规模为118.69 亿美元，同比增长超过300%。
> 随
> 着AI 大模型的兴起，海量算力需求对芯片内存容量和传输带宽提出更高要求，预计HBM 市场规
> 模在2025 年同比增长超过66%，接近200 亿美元，2028 年将达到316 亿美元，2024 至2028 年
> 复合增速达到27.8%。
> 在竞争格局方面，2024 年，SK 海力士继续保持超过50%的份额领先市场，
> 三星以32%~35%的份额次之，美光的份额约为13%~15%。
> （3）行业发展趋势
> 1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容

**[7]** BIS · 15 CFR 年度版（含 part 774 CCL） · § 742.6 Regional stability · p339
`rrf=0.0361 通道=+dense bm25#— dense#23 sim=0.5845`
<https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml>

> For the purposes of this paragraph, 'equivalent' means the item is listed on the country's export control list and the country applies the same license review policy.
> To receive assistance in determining countries with equivalent controls, you may submit an advisory opinion request in accordance with § 748.3(c) of the EAR.
> (B) High Bandwidth Memory (HBM).
> A license is required for items specified in ECCNs 3A090.c, 3D001 (for 3A090.c), and 3E001 (for 3A090.c) when exported, reexported, or transferred (in-country) to or within Macau or a destination specified in Country Group D:5 in supplement no.
> 1 to part 740 of the EAR.
> The license requirements in this paragraph (a)(6)(i)(B) do not apply to deemed exports or deemed reexports.

**[8]** 佰维存储 · 2025年年度报告 · (三) 所处行业情况 · p30
`rrf=0.0357 通道=+dense bm25#— dense#5 sim=0.6181`
<http://static.cninfo.com.cn/finalpage/2026-03-20/1225020225.PDF>

> 根据TrendForce 数
> 据，2025 年第三季度的DRAM 市场上，SK 海力士、三星、美光、长鑫存储的市场份额分别为33.2%、
> 32.6%、25.7%、5.8%。
> 根据TrendForce 报告，得益于数据中心的DDR5 及HBM（高带宽内存）
> 需求上升，2025 年全球DRAM 市场规模（含HBM）为1,657 亿美元，预计2026 年市场规模（含
> HBM）将同比增长144%，增长至4,043 亿美元。
> DRAM 具有读写延迟低、随机访问快、带宽持续提升等特点，是电子设备与服务器的关键运
> 行内存（Memory），主要应用于AI 服务器/通用服务器、PC、智能手机等。
> 随着生成式人工智能
> 应用加速渗透，电子设备/服务器对于内存的带宽以及容量的要求越来越高，DRAM 需求量持续提
> 升，市场前景广阔。
> 3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能内存（Memory），打破了
> 内存带宽及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用先进封装工艺，将多个DRAM 芯片进
> 行堆叠，并与GPU 一同进行封装，形成大容量、高带宽的DDR 组合阵列。
> 在高性能GPU 需求
> 的推动下，HBM 已经成为AI 计算芯片的标配。
> 根据Gartner 数据显示，2025 年，HBM 市场规模为307.5 亿美元，同比增长超过100%。
> 随
> 着AI 大模型的兴起，海量算力需求对芯片内存容量和传输带宽提出更高要求，预计HBM 市场规
> 模在2026 年同比增长超过90%，市场规模接近600 亿美元，预计2029 年市场规模约为1,100 亿
> 美元，2025 年-2029 年复合增速达到37.5%。
> HBM具有超高带宽、3D堆叠集成等特点，是AI加速计算的核心内存方案，主要应用于GPU/AI
> 加速卡及AI 训练、推理服务器。

**[9]** 三星电子 · 2024_4Q_Interim_Report.pdf · V. Treasury shares · p257
`rrf=0.0356 通道=+dense bm25#— dense#1 sim=0.6472`
<https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2024_4Q_Interim_Report.pdf>

> In 2025, we expect the memory industry to weaken in the short term and then recover from the second half, but it is necessary to continuously monitor variables that may widely impact the memory market, such as semiconductor export controls and macroeconomic trends.
> We will focus on expanding the production capacity of advanced technologies of DRAM and NAND to actively address future demand for high-value-added products.
> For DRAM, we will expand sales of improved HBM3E products and develop and mass-produce HBM4 by the second half of the year to strengthen our competitiveness in the AI market.
> Moreover, we will work to increase DDR5 supply for servers and lead the market trend toward higher capacity with products such as 128GB and 256GB, which are required for AI servers.

**[10]** 三星电子 · 2025_Half_Interim_Report.pdf · VI. Outstanding shares · p34
`rrf=0.0350 通道=+dense bm25#— dense#2 sim=0.6326`
<https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_Half_Interim_Report.pdf>

> The foundry market is forecast to keep growing as AI-related industries, now seen as vital to national competitiveness, are driving global investment and support.
> However, concerns over global demand have intensified amid US-China technological competition and rising protectionism, including domestic industry support measures, export controls, and tariffs.
> < Market share of DRAM >
> DRAM | 1H25 32.7% | 2024 41.5% | 2023 42.2%
> ※ Global market share in revenue; data from research firm DRAMeXchange.
> (Figure for 1H25 is a Company estimate.)
> □ Business condition
> In the Memory Business, for DRAM, we increased the share of HBM3E and high-capacity DDR5 sales in line with the strong server demand in the second quarter.

---

## 第 6 题 · 召回 ✅ 召回命中｜答案 ✅ 答案合规

**问题**：我最近在看内存这块，感觉这两年 HBM 突然就热起来了，好多做存储的公司都在讲。我想知道，美国那边的出口管制到底卡的是什么？是卡整个 DRAM，还是只卡 HBM？卡的具体是哪一类，有没有一个明确的技术线？

- 库：A+B｜考察：长口语问题，铺垫在投票（课程 p38）——真正的问句在最后一句。「卡的是什么」必须落到 ECCN 上，故判 `3A090`（516 块，够窄）。
- 实际进检索的查询（原问题 + 模型改写）：`我最近在看内存这块，感觉这两年 HBM 突然就热起来了，好多做存储的公司都在讲。我想知道，美国那边的出口管制到底卡的是什么？是卡整个 DRAM，还是只卡 HBM？卡的具体是哪一类，有没有一个明确的技术线？` ｜ `HBM 出口管制 EAR 3A090.c memory bandwidth density 技术门槛` ｜ `美国出口管制 是否限制整个 DRAM 还是仅 HBM 高带宽内存` ｜ `US export controls HBM DRAM distinction ECCN 3A090 performance parameters`
- 判据原文：`['3A090']` → 命中 ['3A090']
- 附加结构判据：必须含 库B≥1
- 实际来源构成：['cninfo', 'fedreg', 'govinfo']
- 实际公司构成：['BIS', '佰维存储']
- 召回 10 条，用时 15.5s

### 模型作答（非原文，须逐条核 [n]）

```
## 管的是 HBM，不是整个 DRAM

材料中这批新增管制针对的是 HBM，而不是笼统的 DRAM。

- 材料 2：「This IFR imposes these new controls on HBM stacks under ECCN 3A090.c」，并说明「BIS added a control on HBM to prevent the PRC, as well as other destinations of concern, from producing advanced computing ICs incorporating HBM」[2]
- 材料 1：在 ECCN 3A090 下「adds a new items paragraph .c to impose a new CCL-based control for certain HBM commodities」[1]

材料未提及对普通 DRAM 新增管制，也未覆盖其他 DRAM 品类是否受控。

## 归在哪一档

新增条目为 ECCN `3A090.c` [1][2]。与之配套的还有 `3D001 (for 3A090.c)` 和 `3E001 (for 3A090.c)`：向澳门或 Country Group D:5 目的地出口、再出口或境内转移时需许可 [9]。此外，`3A090.c` 项下的外国生产物项若符合 Sec. 734.9(h) 的 advanced computing FDP rule 范围，也受 EAR 管辖 [1]。

注意一个例外：材料 2 明确「Advanced computing ICs containing co-packaged logic and HBM are not controlled by 3A090.c, though they may be controlled by other ECCNs such as 3A090.a or 3A090.b depending on their Total Processing Performance (TPP) and performance density」[2]。

## 技术线是「带宽密度」，材料里出现的那个数字不是管制门槛

思路层面，材料 1 说 BIS「uses the bandwidth density--rather than just the bandwidth--to ensure controls will still apply if an IC uses a larger quantity of smaller HBM chips at little additional cost」[1]。

材料中唯一出现的数字是 License Exception HBM 的条件：出口、再出口或境内转移只有在 `3A090.c` 物项「has a memory bandwidth density less than 3.3 GB/s/mm[supcaret]2」时才能在该许可例外下获授权，且「Only HBM at less than this parameter may be authorized under License Exception HBM」；等于或高于该参数的 HBM「are not eligible for HBM」[4]。授权方还须为总部位于美国或 Country Group A:5 目的地、且最终母公司不在澳门或 Country Group D:5 目的地的出口商、再出口商或转移方 [3][4]。

**重要区分**：`3.3 GB/s/mm[supcaret]2` 是 § 740.25 许可例外的适用条件，不等于 `3A090.c` 条文本身的管制参数。**材料未覆盖** `3A090.c` 条文里对 HBM 的完整参数定义（例如其自身的带宽密度、容量或堆叠层数门槛）。因此不能把这个数字当作"管制红线"引用。

## 管制意图

材料 1 说明，因中国本土 advanced computing ICs 依赖进口 HBM，新增 `3A090.c` 是为「slow PRC attempts to indigenize advanced AI chip production」[1]；材料 2 表述为「these commodities are an important part of the ``production'' process for making advanced computing ICs」[2]。

---

**材料未覆盖**：`3A090.c` 的完整条文参数；除 HBM 外其他 DRAM 产品是否另受其他 ECCN 管辖；许可审查的具体标准。
```

### 判分（两本账）

- **召回判定**：✅ 召回命中
- **答案判定**：✅ 答案合规
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - `734.9` → 第 1 席
  - `3.3` → 第 4 席
  - `740.25` → 第 3 席
- **未覆盖项**：无
- ⚠️ **本题未设答案专名判据**（问题没有要求点名某个对象），答案栏只做数字归属核对——**不冒充「答案已判过」**。

### 检索到的语料原文

**[1]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p63
`rrf=0.0550 通道=+dense bm25#— dense#8 sim=0.6728`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> BIS uses the bandwidth density--rather than just the bandwidth--to ensure controls will still apply if an IC uses a larger quantity of smaller HBM chips at little additional cost.
> As indigenous PRC advanced computing ICs rely upon imported HBM, new ECCN 3A090.c implements restrictions to slow PRC attempts to indigenize advanced AI chip production, which, as explained above,
> [[Page 96800]]
> raises national security and foreign policy concerns.
> Under ECCN 3A090, this IFR adds a new items paragraph .c to impose a new CCL-based control for certain HBM commodities.
> Also, under the advanced computing FDP rule in Sec.
> 734.9(h), foreign-produced 3A090.c items will be subject to the EAR if they meet the scope of that FDP rule.

**[2]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p65
`rrf=0.0531 通道=+dense bm25#— dense#9 sim=0.6713`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> Advanced computing ICs containing co-packaged logic and HBM are not controlled by 3A090.c, though they may be controlled by other ECCNs such as 3A090.a or 3A090.b depending on their Total Processing Performance (TPP) and performance density.
> This IFR imposes these new controls on HBM stacks under ECCN 3A090.c because these commodities are an important part of the ``production'' process for making advanced computing ICs, which prior to this IFR were not being controlled under ECCN 3A090.
> In order to more effectively address the national security and foreign policy concerns which are being addressed under ECCN 3A090, BIS added a control on HBM to prevent the PRC, as well as other destinations of concern, from producing advanced computing ICs incorporating HBM.

**[3]** BIS · 15 CFR 年度版（含 part 774 CCL） · § 740.25 License Exception High Bandwidth Memory · p332
`rrf=0.0527 通道=+dense bm25#— dense#2 sim=0.7410`
<https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml>

> § 740.25 License Exception High Bandwidth Memory (HBM).
> (a) Scope.
> This License Exception High Bandwidth Memory (HBM) authorizes the export, reexport, or transfer (in-country) of items specified in ECCN 3A090.c on the Commerce Control List (CCL) in supplement no.
> 1 to part 774 if all terms and conditions within this section are met.
> (b) Exporter, reexporter, transferor.
> The exporter, reexporter, or transferor must be headquartered in the United States or a destination specified in Country Group A:5 of supplement no.
> 1 to this part, without an ultimate parent headquartered in Macau or a destination specified in Country Group D:5 of supplement no.
> 1 to this part.
> (c) Conditions.

**[4]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p69
`rrf=0.0526 通道=+dense bm25#— dense#0 sim=0.7492`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> 1 to part 740, without an ultimate parent headquartered in Macau or a destination specified in Country Group D:5 of supplement no.
> 1 to part 740.
> No other exporter, reexporter, or transferor may use License Exception HBM.
> This IFR adds paragraph (c) (Conditions) to specify that exports, reexports, or transfers (in-country) are authorized under this License Exception HBM only when the 3A090.c item has a memory bandwidth density less than 3.3 GB/s/mm[supcaret]2.
> Only HBM at less than this parameter may be authorized under License Exception HBM.
> HBM at equal to or greater than this parameter referenced under paragraph (c) are of greater sensitivity, so those HBM of greater sensitivity are not eligible for HBM to ensure U.S.
> national security and foreign policy interests are protected.

**[5]** 佰维存储 · 2025年年度报告 · (三) 所处行业情况 · p30
`rrf=0.0525 通道=bm25+dense bm25#11 dense#13 sim=0.6601`
<http://static.cninfo.com.cn/finalpage/2026-03-20/1225020225.PDF>

> 根据TrendForce 数
> 据，2025 年第三季度的DRAM 市场上，SK 海力士、三星、美光、长鑫存储的市场份额分别为33.2%、
> 32.6%、25.7%、5.8%。
> 根据TrendForce 报告，得益于数据中心的DDR5 及HBM（高带宽内存）
> 需求上升，2025 年全球DRAM 市场规模（含HBM）为1,657 亿美元，预计2026 年市场规模（含
> HBM）将同比增长144%，增长至4,043 亿美元。
> DRAM 具有读写延迟低、随机访问快、带宽持续提升等特点，是电子设备与服务器的关键运
> 行内存（Memory），主要应用于AI 服务器/通用服务器、PC、智能手机等。
> 随着生成式人工智能
> 应用加速渗透，电子设备/服务器对于内存的带宽以及容量的要求越来越高，DRAM 需求量持续提
> 升，市场前景广阔。
> 3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能内存（Memory），打破了
> 内存带宽及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用先进封装工艺，将多个DRAM 芯片进
> 行堆叠，并与GPU 一同进行封装，形成大容量、高带宽的DDR 组合阵列。
> 在高性能GPU 需求
> 的推动下，HBM 已经成为AI 计算芯片的标配。
> 根据Gartner 数据显示，2025 年，HBM 市场规模为307.5 亿美元，同比增长超过100%。
> 随
> 着AI 大模型的兴起，海量算力需求对芯片内存容量和传输带宽提出更高要求，预计HBM 市场规
> 模在2026 年同比增长超过90%，市场规模接近600 亿美元，预计2029 年市场规模约为1,100 亿
> 美元，2025 年-2029 年复合增速达到37.5%。
> HBM具有超高带宽、3D堆叠集成等特点，是AI加速计算的核心内存方案，主要应用于GPU/AI
> 加速卡及AI 训练、推理服务器。

**[6]** 佰维存储 · 2024年半年度报告 · (二) 所属行业情况 · p35
`rrf=0.0515 通道=bm25+dense bm25#19 dense#17 sim=0.6436`
<http://static.cninfo.com.cn/finalpage/2024-08-23/1220952257.PDF>

> 季度的DRAM 市场上，三星、SK 海力士、美光、南亚科技的市场份额分别为42.1%、30.8%、
> 21.7%、1.7%。
> 受益于DRAM 价格的全面回升，以及HBM、DDR5 等产品的出货增长，2024 年
> 一季度全球DRAM 市场规模为170.6 亿美元，同比增长74.8%。
> （3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能Memory，打破了内存带宽
> 及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用晶圆级封装技术将多个DRAM 芯片进行堆叠，
> 形成大容量、高带宽的HBM 模块。
> HBM 与GPU/CPU 之间通过2.5D 晶圆级封装技术进行整合
> 互联，构建高性能计算芯片。
> 在高性能GPU 需求的推动下，HBM 已经成为AI 计算芯片的标
> 配。
> 根据Gartner 数据显示，2024 年，HBM 市场规模预计将达到123.2 亿美元，同比增长
> 284.2%。
> 随着AI 大模型的兴起，海量算力需求催生了对芯片内存容量和传输带宽的更高要求，
> 预计到2028 年，HBM 市场规模将增长至300.2 亿美元，年复合增长率为24.9%。
> TrendForce 集
> 邦咨询报告显示，2023 年，SK 海力士以53%的市场份额领先HBM 市场，其次是三星（38%）
> 和美光（9%）。
> HBM 广泛应用于高性能GPU 和AI 计算芯片中，以满足大规模数据处理和高速
> 传输的需求。
> AI 服务器对内存容量和带宽的要求推动了HBM 在各类高性能计算中的普及。
> 3、行业发展趋势
> 2024 年半年度报告
> （1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容
> 存储器产业链下游涵盖智能手机、平板电脑、计算机、网络通信设备、可穿戴设备、物联网
> 硬件、安防监控、工业控制、汽车电子等行业以及个人移动存储等多个领域，其中多个细分市场

**[7]** 佰维存储 · 2024年年度报告 · (三) 所处行业情况 · p50
`rrf=0.0485 通道=bm25+dense bm25#0 dense#19 sim=0.6368`
<http://static.cninfo.com.cn/finalpage/2025-04-30/1223427605.PDF>

> 公司在目前的产品中积极采用各大原厂最新制程的NAND Flash，在嵌入式存储产品方面，
> 公司已推出eMMC 到UFS 全系列产品；
> 在SSD 产品方面，公司已推出SATA 到PCIe 5.0 全系列
> 产品。
> NAND Flash 技术发展
> 来源：CFM 闪存市场，佰维存储编制
> （2）DRAM 推出1β或1b 制程节点，生成式AI 推动HBM 需求增长
> 随着DRAM 制程技术逼近物理极限，进入20nm 级别后微缩难度剧增，导致DRAM 技术升
> 级节奏有所放缓。
> 目前，三星、SK 海力士、美光均已进入10nm 第五代（1b/1β nm）阶段，下一
> 代（1c 或1γnm）技术研发及量产准备正在进行。
> HBM 作为基于3D 堆栈工艺的高性能DRAM，
> 深圳佰维存储科技股份有限公司 2024 年年度报告
> 打破内存带宽及功耗瓶颈。
> HBM 即高带宽存储器，通过使用先进封装将多个DRAM 芯片进行堆
> 叠，并与GPU 一同进行封装，形成大容量、高带宽的存储应用。
> 2024 年，以ChatGPT 为代表的
> 生成式AI 带动AI 服务器需求激增，进而带动对HBM 需求的急剧增长。
> 目前，SK 海力士、三星
> 和美光的HBM 销售收入均持续大幅增长，市场需求旺盛且暂无放缓迹象。
> 伴随英伟达Blackwell
> 系列GPU 及AMD MI 系列GPU 产品的持续放量，以HBM3e 为代表的高性能HBM 产品需求将
> 进一步攀升。
> 2024 年，公司DDR5 内存模组和LPDDR5X 嵌入式存储产品持续导入市场。
> DRAM 技术发展
> 来源：CFM 闪存市场，佰维存储编制
> （3）AI 手机
> 第十四届全国人大三次会议审议的政府工作报告中提出“大力发展智能网联新能源汽车、人
> 工智能手机和电脑、智能机器人等新一代智能终端以及智能制造装备”，其中，“人工智能手机
> 和电脑”作为新词，首次出现在政府工作报告中。

**[8]** 佰维存储 · 2023年年度报告 · (三) 所处行业情况 · p46
`rrf=0.0478 通道=bm25+dense bm25#1 dense#29 sim=0.6224`
<http://static.cninfo.com.cn/finalpage/2024-04-30/1219921152.PDF>

> 备需要存储器具有低功耗、高可靠性和足够的存储容量，同时还需要小巧的封装。
> 而高性能计算
> 2023 年年度报告
> 领域则需要存储器具有更高的读写速度、更低的延迟、更好的QoS 和更大的存储容量，并且还需
> 要具备更强的数据保护能力。
> 公司在目前的产品中积极采用各大原厂最新制程的NAND Flash，在
> 嵌入式存储产品方面，覆盖从eMMC 到UFS 3.1 全系列；
> 在SSD 产品方面，覆盖从SATA 到PCIe
> 4.0 全系列。
> NAND Flash 技术发展
> （2）DRAM 推出1β 或1b 制程节点，生成式AI 推动HBM 需求增长
> 随着DRAM 制程技术逼近物理极限，20nm 级别之后微缩难度剧增导致DRAM 制程技术升
> 级节奏减缓。
> 目前，三星、SK 海力士、美光均已推出1β 或1b 节点的DRAM 技术，下一代技术
> 研发正在进行。
> HBM 作为基于3D 堆栈工艺的高性能DRAM，打破内存带宽及功耗瓶颈。
> HBM(High Bandwidth Memory)即高带宽存储器，通过使用先进封装将多个DRAM 芯片进行堆叠，
> 并与GPU 一同进行封装，形成大容量、高带宽的存储应用。
> 2023 年，以ChatGPT 为代表的生成
> 式AI 带动AI 服务器需求激增，进而带动对HBM 需求的急剧增长。
> 目前，三星、SK 海力士、美
> 光的第四代HBM3 产品均已量产，第五代HBM3E 亦计划于2024 年开始量产。
> 对于最先进的第
> 六代HBM4，SK 海力士计划在2024 年启动开发，三星和美光则计划分别于2025 和2026 年推出。
> 2023 年，公司DDR5 内存模组和LPDDR5 嵌入式存储产品持续导入市场。
> DRAM 技术发展
> 2023 年年度报告
> （3）企业级存储市场需求逐渐好转
> 根据CFM 闪存市场分析，受国内外经济不确定性影响，2023 年全球服务器市场下滑。
> 在高

**[9]** BIS · 15 CFR 年度版（含 part 774 CCL） · § 742.6 Regional stability · p339
`rrf=0.0465 通道=+dense bm25#— dense#10 sim=0.6686`
<https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml>

> For the purposes of this paragraph, 'equivalent' means the item is listed on the country's export control list and the country applies the same license review policy.
> To receive assistance in determining countries with equivalent controls, you may submit an advisory opinion request in accordance with § 748.3(c) of the EAR.
> (B) High Bandwidth Memory (HBM).
> A license is required for items specified in ECCNs 3A090.c, 3D001 (for 3A090.c), and 3E001 (for 3A090.c) when exported, reexported, or transferred (in-country) to or within Macau or a destination specified in Country Group D:5 in supplement no.
> 1 to part 740 of the EAR.
> The license requirements in this paragraph (a)(6)(i)(B) do not apply to deemed exports or deemed reexports.

**[10]** 佰维存储 · 2024年年度报告 · (三) 所处行业情况 · p48
`rrf=0.0454 通道=bm25+dense bm25#14 dense#27 sim=0.6302`
<http://static.cninfo.com.cn/finalpage/2025-04-30/1223427605.PDF>

> 电子设备/服务器需要存储的数据量也越来越庞大，NAND Flash 需求量巨大，市场前景广阔。
> 2）DRAM 行业概况
> DRAM 是动态随机存取存储器，DRAM 的特征是读写速度快、延迟低，但掉电后数据会丢失，
> 常用于计算系统的运行内存（Memory）。
> 目前全球主要的DRAM IDM 原厂为三星、SK 海力士
> 和美光。
> 根据CFM 数据显示，2024 年第三季度的DRAM 市场上，三星、SK 海力士、美光、南
> 亚科技的市场份额分别为39.5%、34.7%、20.6%、1.0%。
> 根据TrendForce 报告，得益于数据中心
> 的DDR5 及HBM（高带宽内存）需求上升，2024 年全球DRAM 市场规模为958.63 亿美元，同
> 比增长85%。
> 3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能Memory，打破了内存带宽
> 及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用先进封装将多个DRAM 芯片进行堆叠，并与GPU
> 一同进行封装，形成大容量、高带宽的DDR 组合阵列。
> 在高性能GPU 需求的推动下，HBM 已
> 经成为AI 计算芯片的标配。
> 根据Gartner 数据显示，2024 年，HBM 市场规模为118.69 亿美元，同比增长超过300%。
> 随
> 着AI 大模型的兴起，海量算力需求对芯片内存容量和传输带宽提出更高要求，预计HBM 市场规
> 模在2025 年同比增长超过66%，接近200 亿美元，2028 年将达到316 亿美元，2024 至2028 年
> 复合增速达到27.8%。
> 在竞争格局方面，2024 年，SK 海力士继续保持超过50%的份额领先市场，
> 三星以32%~35%的份额次之，美光的份额约为13%~15%。
> （3）行业发展趋势
> 1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容

---

## 第 7 题 · 召回 ✅ 召回命中｜答案 ❌ 答案未点名 ['三星', '海力士', '美光']

**问题**：三星、SK 海力士、美光三家最近一期报告对 HBM 供需与产能的表述有哪些共性和差异？

- 库：A｜考察：全景题 1：**碎块拼不出全景**（课程 p63）。判据必须是**结构性的**，而且**要点名**——`min_companies=3` 数的是「任意三家」，实测 14 席实得 {SK海力士, 东芯股份, 佰维存储, 美光}=4 家就判过了，**可三星一条都没有**（模型自己都在答案里写「三星的表述材料完全未覆盖」）。这与最初那个「假 10/10」是同一个病，所以 2026-10-04 补 `require_companies`，要求**问题点名的三家逐一出现**。
- 实际进检索的查询（原问题 + 模型改写）：`三星、SK 海力士、美光三家最近一期报告对 HBM 供需与产能的表述有哪些共性和差异？` ｜ `Samsung SK Hynix Micron HBM supply demand capacity earnings call latest quarter` ｜ `HBM 供需 产能 三星 SK海力士 美光 财报 表述 对比` ｜ `HBM3E HBM4 capacity expansion supply agreement memory makers quarterly report`
- 判据原文：`['HBM']` → 命中 ['HBM']
- 附加结构判据：跨 ≥3 家公司；点名公司须出现且**切题**：三星（正文须含「HBM」）、SK 海力士（正文须含「HBM」）、美光（正文须含「HBM」）
- 实际来源构成：['cninfo', 'samsung', 'sec', 'skhynix']
- 实际公司构成：['SK 海力士', '三星电子', '佰维存储', '美光 Micron']
- **按公司取证**：点名 3 家（三星电子、美光 Micron、SK 海力士），出得起证 **3 家**
  - 各得席位：三星电子×4、美光 Micron×4、SK 海力士×4；补位（未被点名）佰维存储×2
  - ⚠️ **缺席**：（无）
- 召回 14 条，用时 26.6s

### 模型作答（非原文，须逐条核 [n]）

> ⚠️ 作答失败：思考链吃光了 max_tokens，没留下正文（max_tokens=4000，思考 9622 字）——调大 max_tokens

```
(无)
```

### 判分（两本账）

- **召回判定**：✅ 召回命中
- **答案判定**：❌ 答案未点名 ['三星', '海力士', '美光']
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - 本答案没有给出数值型数字（年份、个数这类不算——它们不进这项核对）
- **未覆盖项**：答案未点名：三星、海力士、美光
- 答案须点名的对象：三星、海力士、美光（匹配域已抠掉问题原文，防判据被问题自己满足）

### 检索到的语料原文（**按公司分组**——全景题的证据要按公司看，不是一串扁平编号）

#### 三星电子

**[1]** 三星电子 · 2026_Half_Interim_Report.pdf · VI. Outstanding shares · p36
`rrf=0.0654 通道=+dense+公司 bm25#— dense#20 sim=0.6378`
<https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_Half_Interim_Report.pdf>

> As a result, both DRAM and NAND achieved record-high bit sales, while the proportion of bit sales for server applications also reached an all-time high.
> The Company expanded the supply of its differentiated HBM4 and further strengthened its technology competitiveness with the industry’s first shipments of HBM4E samples to key customers.
> In the second half, demand growth is expected to outpace the Company’s efforts to increase production capacity.
> In light of this, we will monitor any shifts in demand and optimize our product mix accordingly.
> In addition, we will address AI-related demand by leveraging our industry-leading technology competitiveness and diversified product lineup, further strengthening our market leadership.

#### 美光 Micron

**[2]** 美光 Micron · 10-Q 2025-06-26 · PART II . OTHER INFORMATION · p509
`rrf=0.0628 通道=+dense+公司 bm25#— dense#5 sim=0.6751`
<https://www.sec.gov/Archives/edgar/data/723125/000072312525000021/mu-20250529.htm>

> If we or our competitors increase HBM supply at a rate that outpaces HBM demand, conversion of HBM capacity to supply other DRAM products could result in significant supply-demand imbalances.
> Due to the higher performance and more complex manufacturing process, HBM requires a higher number of wafers to produce the same number of bits as conventional DRAM in the same technology node.
> This could lead to declines in average selling prices for our DRAM products and could materially affect our business.
> Our product demand forecasts may also be impacted significantly by the strategic actions of our customers.
> In addition, our ability to successfully introduce new products often requires us to make product specification decisions multiple years in advance of when new products enter the market.

#### SK 海力士

**[3]** SK 海力士 · SK hynix FY2024 Q1 Earnings Results · p10
`rrf=0.0740 通道=+dense+公司 bm25#— dense#8 sim=0.6715`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/61321621157035970.pdf>

> Expect limited DRAM/NAND production
> growth in ‘24, as a result of conservative
> investments in ‘23, and more capa.
> allocated
> to produce HBM which has larger die size
> 10
> In March, began mass production/supply of 1bnm HBM3E
> Increase HBM3E supply in-line with customers’ demand
> Expand customer base using increased production capability
> Signed MOU with TSMC for development of HBM4 and
> collaboration on next generation packaging technology
> Represent 45%+ of PC, 60%+ of SV bit sales
> Strong sales of 128GB+ modules contributed to DDR5 sales
> 1bnm 32Gb DDR5 product to be launched to support high-
> density SV DRAM demand
> Sales of high-performance 16ch eSSD increased in Q1
> Solidigm’s QLC based high density eSSD will increase in
> demand due to growing needs for high performance, high

#### 三星电子

**[4]** 三星电子 · 2024_Half_Interim_Report.pdf · VI. Outstanding shares · p39
`rrf=0.0567 通道=+dense+公司 bm25#— dense#16 sim=0.6440`
<https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2024_Half_Interim_Report.pdf>

> Regarding industry supply, chances are rising that conventional bit supply for advanced technology products for PC and mobile applications will be further constrained as capacity concentrates on HBM and server DRAM/SSD to address AI sever demand.
> With strong demand, especially for server, we will actively respond to the demand for high-value-added products for AI; and we will further hone our completive edge in the HBM3E and high-density DDR5 markets and increase supply for server SSDs to expand sales.
> For System LSI, we expect to see growth in the global smartphone market—the business’s primary market—centering on OEMs in China.

#### 美光 Micron

**[5]** 美光 Micron · 10-Q 2025-03-21 · PART II . OTHER INFORMATION · p497
`rrf=0.0570 通道=+dense+公司 bm25#— dense#6 sim=0.6751`
<https://www.sec.gov/Archives/edgar/data/723125/000072312525000009/mu-20250227.htm>

> If we or our competitors increase HBM supply at a rate that outpaces HBM demand, conversion of HBM capacity to supply other DRAM products could result in significant supply-demand imbalances.
> Due to the higher performance and more complex manufacturing process, HBM requires a higher number of wafers to produce the same number of bits as conventional DRAM in the same technology node.
> This could lead to declines in average selling prices for our DRAM products and could materially affect our business.
> Our product demand forecasts may also be impacted significantly by the strategic actions of our customers.
> In addition, our ability to successfully introduce new products often requires us to make product specification decisions multiple years in advance of when new products enter the market.

#### SK 海力士

**[6]** SK 海力士 · SK hynix FY2026 Q2 Earnings Results · p10
`rrf=0.0643 通道=+dense+公司 bm25#— dense#9 sim=0.6706`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/13571040283022005.pdf>

> deposits) incorporated to support contract
> fulfillment, thereby enhancing mid-to-long-term demand visibility
> DRAM
> Q3 B/G : Approx.
> 10% increase QoQ
> Active response centered on SV products
> NAND
> Q3 B/G : Low-single% increase QoQ
> (including Solidigm)
> Increase sales of 321L products and SSD
> 10
> Began HBM4 shipment in Q2, with customer-required speeds · industry-leading
> power efficiency · cost competitiveness.
> Full ramp up planned in 2H
> Supplied 1cnm- based HBM4E samples to a major customer in 1H
> Committed to maintaining HBM leadership through comprehensive
> competitiveness across performance, stable supply capability, and cost
> Fully commenced supply of SOCAMM2 products based on 1cnm
> Optimizing product lineup aligned with customer development schedules

#### 三星电子

**[7]** 三星电子 · 2024_Half_Interim_Report.pdf · XII. Appendix · p10
`rrf=0.0462 通道=+dense+公司 bm25#— dense#23 sim=0.6268`
<https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2024_Half_Interim_Report.pdf>

> Products Developed 32Gb DDR5 DRAM, the largest capacity currently available
> Samsung Electronics Business Report 10

#### 美光 Micron

**[8]** 美光 Micron · 10-Q 2025-12-18 · PART II . OTHER INFORMATION · p494
`rrf=0.0529 通道=+dense+公司 bm25#— dense#12 sim=0.6642`
<https://www.sec.gov/Archives/edgar/data/723125/000072312525000046/mu-20251127.htm>

> Due to the higher performance and more complex manufacturing process, HBM requires a higher number of wafers and more cleanroom space to produce the same number of bits as conventional DRAM in the same technology node.
> If demand for HBM weakens and suppliers shift capacity from HBM to conventional DRAM, this could result in a significant increase in conventional DRAM supply.
> An oversupplied DRAM market may lead to downward pressure on pricing, which could adversely impact our financial results.
> Conversely, as the demand for DRAM, HBM, or any of our other products has increased and may continue to increase, we may be unable to increase supply sufficiently to meet such demand.

#### SK 海力士

**[9]** SK 海力士 · SK hynix FY2025 Q4 Earnings Results · p12
`rrf=0.0542 通道=+dense+公司 bm25#— dense#31 sim=0.6072`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/116964051831620258.pdf>

> Rapid progression of Yong-in Phase 1 Fab construction
> Cheong-ju P&T7 and Indiana Adv.
> PKG Fab on track
> Expect considerable increase in Yr.
> ’26 CapEx, but will
> continue to adhere to CapEx discipline
> 12
> Capable of reliably delivering both HBM3E & HBM4
> HBM4 mass production in progress in line with customer-agreed schedule
> Preparing to deliver optimized Custom HBM by strengthening collaboration with
> customers and partners
> Expanding production of high-value products including high-density SV DRAM
> Accelerating 1cnm migration to expand AI memory portfolio, including
> SoCAMM2 and GDDR7
> Maximizing product competitiveness with 321L migration
> Expanding AI storage capabilities leveraging Solidigm QLC eSSD
> Aiming to lead ultra-high-density AI storage mkt.
> with next-gen.
> 245TB product development
> 13

#### 三星电子

**[10]** 三星电子 · 2025_4Q_Interim_Report.pdf · VI. Outstanding shares · p41
`rrf=0.0447 通道=+dense+公司 bm25#— dense#32 sim=0.6062`
<https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_4Q_Interim_Report.pdf>

> DRAM | 2025 34.0% | 2024 41.5% | 2023 42.2%
> ※ Global market share in revenue; data from research firm DRAMeXchange.
> □ Business condition
> In the Memory Business, under low inventory levels and supply constraints, we expanded HBM sales and concentrated on improving profitability by addressing the demand for high value-added products for servers, such as high-density DDR5, LPDDR5x, and server SSDs.
> In 2026, we aim to continue leading the AI era by leveraging our product competitiveness.
> For DRAM, we plan to actively address customer demand with the timely and expanded supply of competitive HBM4 targeting new GPU and ASIC markets within the AI sector.
> Also, we will continue increasing the sales proportion of AI-related products, such as high-capacity DDR5, SOCAMM2, and GDDR7.

#### 美光 Micron

**[11]** 美光 Micron · 10-Q 2026-06-25 · PART II . OTHER INFORMATION · p495
`rrf=0.0526 通道=+dense+公司 bm25#— dense#10 sim=0.6642`
<https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/mu-20260528.htm>

> Due to the higher performance and more complex manufacturing process, HBM requires a higher number of wafers and more cleanroom space to produce the same number of bits as conventional DRAM in the same technology node.
> If demand for HBM weakens and suppliers shift capacity from HBM to conventional DRAM, this could result in a significant increase in conventional DRAM supply.
> An oversupplied DRAM market may lead to downward pressure on pricing, which could adversely impact our financial results.
> Conversely, as the demand for DRAM, HBM, or any of our other products has increased and may continue to increase, we may be unable to increase supply sufficiently to meet such demand.

#### SK 海力士

**[12]** SK 海力士 · SK hynix FY2025 Q2 Earnings Results · p9
`rrf=0.0500 通道=+dense+公司 bm25#— dense#18 sim=0.6391`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/40103454849895488.pdf>

> spending despite macro uncertainties
> SSDs for high-perform., high-capacity
> More widespread AI functions to drive
> General purpose SV demand to grow,
> storage solutions as energy efficiency
> both set demand and contents growth
> due to replacement cycles and new CPU
> becomes more critical
> adoption
> 9
> Company Plan
> DRAM
> Q3 B/G: Low-to-Mid Single% increase QoQ
> NAND
> Q3 B/G: Limited increase QoQ
> (incl.
> Solidigm)
> M15X to open Q4’25 as scheduled, to produce DRAM
> products including HBM from Yr.
> ’26
> Yong-in 1st fab construction to finish in Q2’27
> Yr.
> ‘25 CapEx expected to increase from previous plans
> Proactive investment needed this year to ensure timely
> support for HBM customers, in Yr.
> ‘26
> 10
> Maintain plan to double HBM sales YoY, and deliver stable performance

#### 佰维存储

**[13]** 佰维存储 · 2024年半年度报告 · (二) 所属行业情况 · p35
`rrf=0.0696 通道=bm25+dense bm25#5 dense#0 sim=0.7220`
<http://static.cninfo.com.cn/finalpage/2024-08-23/1220952257.PDF>

> 季度的DRAM 市场上，三星、SK 海力士、美光、南亚科技的市场份额分别为42.1%、30.8%、
> 21.7%、1.7%。
> 受益于DRAM 价格的全面回升，以及HBM、DDR5 等产品的出货增长，2024 年
> 一季度全球DRAM 市场规模为170.6 亿美元，同比增长74.8%。
> （3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能Memory，打破了内存带宽
> 及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用晶圆级封装技术将多个DRAM 芯片进行堆叠，
> 形成大容量、高带宽的HBM 模块。
> HBM 与GPU/CPU 之间通过2.5D 晶圆级封装技术进行整合
> 互联，构建高性能计算芯片。
> 在高性能GPU 需求的推动下，HBM 已经成为AI 计算芯片的标
> 配。
> 根据Gartner 数据显示，2024 年，HBM 市场规模预计将达到123.2 亿美元，同比增长
> 284.2%。
> 随着AI 大模型的兴起，海量算力需求催生了对芯片内存容量和传输带宽的更高要求，
> 预计到2028 年，HBM 市场规模将增长至300.2 亿美元，年复合增长率为24.9%。
> TrendForce 集
> 邦咨询报告显示，2023 年，SK 海力士以53%的市场份额领先HBM 市场，其次是三星（38%）
> 和美光（9%）。
> HBM 广泛应用于高性能GPU 和AI 计算芯片中，以满足大规模数据处理和高速
> 传输的需求。
> AI 服务器对内存容量和带宽的要求推动了HBM 在各类高性能计算中的普及。
> 3、行业发展趋势
> 2024 年半年度报告
> （1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容
> 存储器产业链下游涵盖智能手机、平板电脑、计算机、网络通信设备、可穿戴设备、物联网
> 硬件、安防监控、工业控制、汽车电子等行业以及个人移动存储等多个领域，其中多个细分市场

**[14]** 佰维存储 · 2023年年度报告 · (三) 所处行业情况 · p46
`rrf=0.0680 通道=bm25+dense bm25#4 dense#3 sim=0.6788`
<http://static.cninfo.com.cn/finalpage/2024-04-30/1219921152.PDF>

> 备需要存储器具有低功耗、高可靠性和足够的存储容量，同时还需要小巧的封装。
> 而高性能计算
> 2023 年年度报告
> 领域则需要存储器具有更高的读写速度、更低的延迟、更好的QoS 和更大的存储容量，并且还需
> 要具备更强的数据保护能力。
> 公司在目前的产品中积极采用各大原厂最新制程的NAND Flash，在
> 嵌入式存储产品方面，覆盖从eMMC 到UFS 3.1 全系列；
> 在SSD 产品方面，覆盖从SATA 到PCIe
> 4.0 全系列。
> NAND Flash 技术发展
> （2）DRAM 推出1β 或1b 制程节点，生成式AI 推动HBM 需求增长
> 随着DRAM 制程技术逼近物理极限，20nm 级别之后微缩难度剧增导致DRAM 制程技术升
> 级节奏减缓。
> 目前，三星、SK 海力士、美光均已推出1β 或1b 节点的DRAM 技术，下一代技术
> 研发正在进行。
> HBM 作为基于3D 堆栈工艺的高性能DRAM，打破内存带宽及功耗瓶颈。
> HBM(High Bandwidth Memory)即高带宽存储器，通过使用先进封装将多个DRAM 芯片进行堆叠，
> 并与GPU 一同进行封装，形成大容量、高带宽的存储应用。
> 2023 年，以ChatGPT 为代表的生成
> 式AI 带动AI 服务器需求激增，进而带动对HBM 需求的急剧增长。
> 目前，三星、SK 海力士、美
> 光的第四代HBM3 产品均已量产，第五代HBM3E 亦计划于2024 年开始量产。
> 对于最先进的第
> 六代HBM4，SK 海力士计划在2024 年启动开发，三星和美光则计划分别于2025 和2026 年推出。
> 2023 年，公司DDR5 内存模组和LPDDR5 嵌入式存储产品持续导入市场。
> DRAM 技术发展
> 2023 年年度报告
> （3）企业级存储市场需求逐渐好转
> 根据CFM 闪存市场分析，受国内外经济不确定性影响，2023 年全球服务器市场下滑。
> 在高

---

## 第 8 题 · 召回 ✅ 召回命中｜答案 ✅ 答案合规

**问题**：A 股内存产业链公司如何披露出口管制对自身经营的影响？

- 库：A｜考察：全景题 2：同上，且考察中文语料里的同类表述。`forbid_lib=B` 是必须的——问的是**A 股公司怎么披露**，若前 k 被 BIS 规则文本占住，答案就答成了「管制是什么」而不是「公司怎么说」。
- 实际进检索的查询（原问题 + 模型改写）：`A 股内存产业链公司如何披露出口管制对自身经营的影响？` ｜ `A股 内存 上市公司 出口管制 风险披露 经营影响 公告` ｜ `memory chip company China export controls disclosure annual report risk factors` ｜ `EAR 3A090 memory bandwidth density performance parameters disclosure impact Chinese listed company`
- 判据原文：`['管制']` → 命中 ['管制']
- 附加结构判据：跨 ≥3 家公司；不得含库B
- 实际来源构成：['cninfo']
- 实际公司构成：['东芯股份', '佰维存储', '兆易创新', '兴森科技', '太极实业', '安集科技', '德明利', '普冉股份', '江波龙', '深科技', '澜起科技', '聚辰股份', '雅克科技', '香农芯创']
- **按公司取证**：点名 15 家（东芯股份、佰维存储、兆易创新、兴森科技、太极实业、安集科技、德明利、普冉股份、江波龙、深科技、澜起科技、聚辰股份、雅克科技、香农芯创、鼎龙股份），出得起证 **14 家**
  - 各得席位：东芯股份×1、佰维存储×1、兆易创新×1、兴森科技×1、太极实业×1、安集科技×1、德明利×1、普冉股份×1、江波龙×1、深科技×1、澜起科技×1、聚辰股份×1、雅克科技×1、香农芯创×1
  - ⚠️ **缺席**：鼎龙股份　← 库里有材料却挤不进来，属覆盖缺口；没有材料则是出证来源缺口
- 召回 14 条，用时 22.0s

### 模型作答（非原文，须逐条核 [n]）

```
## 一、材料中确实出现出口管制相关披露的公司（共 3 家）

**1. 东芯股份（材料 1，年报「(七) 宏观环境风险」）**

- 定性描述地缘政治与管制趋势：「近年来，全球宏观环境复杂多变，地缘政治博弈加剧，部分国家和地区持续出台贸易保护主义政策与出口管制措施，对我国集成电路等高新技术产业的发展带来挑战」[1]
- 指出行业特征放大传导：「集成电路行业具有全球化分工协作程度深、产业链条长的显著特征」[1]
- 后果链条（条件式）：「若未来国际贸易环境进一步恶化、相关国家贸易摩擦与科技限制持续升级，可能加剧全球半导体产业链的波动与重构，导致公司面临上游供应链阻滞、产业链上下游交易成本增加以及更为严格的国际贸易合规要求等风险，进而对公司的正常采购、生产、销售及整体经营业绩产生不利影响」[1]
- 该材料中提到公司产品包含「NAND Flash、NOR Flash 及DRAM」[1]

**2. 普冉股份（材料 8，风险提示段）——材料中唯一直接点「实体清单」的一家**

- 管制事实描述：「随着美国商务部将多家中国企业和机构列入美国出口管制的"实体清单"，并且不断扩大"实体清单"名单，加强对"实体清单"的限制，加强对中国在先进制程领域发展的限制」[8]
- 客户端敞口：「公司的客户主要以境内企业为主，上述外部因素可能导致公司为若干客户提供芯片产品和服务受到限制」[8]
- 供应链/工具端敞口：「公司及公司部分供应商无可避免地使用了美国设备、技术或工业软件等，可能导致其为公司供货或提供服务受到限制」[8]
- 极端情形：「一旦国际贸易摩擦的状况持续或进一步加剧，公司可能面临研发及经营受限、订单减少或供应商无法供货等局面，若公司未能及时成功拓展新客户或供应商，极端情况下可能出现公司的营业收入下滑，令公司的经营业绩出现较大下降，并且陷入知识产权争端，阻滞公司的业务发展」[8]
- 结论句：「因此，公司存在生产经营受国际贸易摩擦影响的风险」[8]
- 注：该材料未标明公司产品品类[8]

**3. 澜起科技（材料 11，年报「(七) 宏观环境风险」）**

- 「如果全球贸易摩擦进一步升级，有可能造成产业链上下游交易成本增加，下游需求受限，上游供给不畅，从而将对公司的经营造成不利影响」[11]
- 明确指向管制政策与人员：「假如相关半导体出口管制政策进一步升级，不排除未来对公司业务及相关人员产生不利影响」[11]
- 应对表述：「公司将持续关注相关规则的更新并积极做好应对措施」[11]

## 二、这 3 家的披露写法有共同点（仅据上述材料归纳）

- **位置**：放在宏观环境风险 / 国际贸易摩擦风险条目下，而非经营数据章节[1][8][11]
- **语气**：全部为条件式、假设式（「若」「假如」「可能」「不排除」），不陈述已发生的具体损失[1][8][11]
- **传导路径**：上游供给（供应链阻滞、无法供货、美国设备/技术/工业软件受限）→ 成本与合规（交易成本增加、更严格的国际贸易合规要求）→ 客户与订单 → 经营业绩[1][8][11]
- **应对**：关注规则更新、做好应对措施、拓展新客户或供应商[8][11]
- **颗粒度**：均为定性描述，未给出任何量化敞口[1][8][11]

## 三、材料未覆盖的部分

- **其他内存相关公司的披露**：材料 2（佰维存储）、材料 3（兆易创新）、材料 5（太极实业）、材料 7（德明利）、材料 9（江波龙）、材料 10（深科技）、材料 12（聚辰股份）、材料 14（香农芯创）在所给片段中**未见**出口管制对自身经营影响的披露内容。注意这是就所给节选而言，不能据此判断这些公司全文中是否披露。
- **具体管制规则**：材料未给出任何管制条款编号、技术阈值、管制清单名称或生效日期。
- **量化影响**：材料未给出因出口管制导致的营收、订单、成本变动的任何数字。
- **HBM 相关**：材料 2 包含 HBM 市场规模与竞争格局的内容，但**未覆盖**出口管制对 HBM 的影响。
- **受影响产品型号**：材料未给出被限制或被影响的具体存储产品型号。
```

### 判分（两本账）

- **召回判定**：✅ 召回命中
- **答案判定**：✅ 答案合规
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - 本答案没有给出数值型数字（年份、个数这类不算——它们不进这项核对）
- **未覆盖项**：无
- ⚠️ **本题未设答案专名判据**（问题没有要求点名某个对象），答案栏只做数字归属核对——**不冒充「答案已判过」**。

### 检索到的语料原文（**按公司分组**——全景题的证据要按公司看，不是一串扁平编号）

#### 东芯股份

**[1]** 东芯股份 · 2025年年度报告 · (七) 宏观环境风险 · p28
`rrf=0.0234 通道=bm25 bm25#1 dense#— sim=—`
<http://static.cninfo.com.cn/finalpage/2026-04-23/1225153903.PDF>

> 虽然公司NAND Flash、NOR Flash 及DRAM 等产品已广泛应用于网络通信、安防监控、消费电子、工业控制与智能化、汽车电子等多个领域，应用场景的多元化在一定程度上增强了公司抵御单一市场波动的能力，但如果未来宏观经济发生较大波动或存在下行趋势，导致下游终端市场整体需求低迷或出现行业性的增长放缓，仍将不可避免地传导至存储芯片市场，进而对公司的经营业绩造成不利影响。
> 此外，受国家产业政策鼓励及市场需求驱动，国内存储芯片行业快速发展，市场参与者数量不断增多，市场竞争日益加剧。
> 一方面，行业内现有企业不断结合自身优势拓展市场边界；
> 另一方面，同质化竞争可能对公司产品的综合毛利率水平带来挑战。
> 如果未来公司无法准确把握市场动态及行业发展态势，在日益加剧的行业竞争格局中未能有效巩固和提升自身的市场地位与份额，将对公司的经营规模和盈利能力产生一定影响。
> (七) 宏观环境风险
> √适用□不适用
> 近年来，全球宏观环境复杂多变，地缘政治博弈加剧，部分国家和地区持续出台贸易保护主义政策与出口管制措施，对我国集成电路等高新技术产业的发展带来挑战。
> 集成电路行业具有全球化分工协作程度深、产业链条长的显著特征，若未来国际贸易环境进一步恶化、相关国家贸易摩擦与科技限制持续升级，可能加剧全球半导体产业链的波动与重构，导致公司面临上游供应链
> 东芯半导体股份有限公司2025 年年度报告
> 阻滞、产业链上下游交易成本增加以及更为严格的国际贸易合规要求等风险，进而对公司的正常采购、生产、销售及整体经营业绩产生不利影响。
> (八) 存托凭证相关风险
> □适用√不适用
> (九) 其他重大风险
> □适用√不适用
> 五、报告期内主要经营情况
> 报告期内，公司实现营业收入92,142.53 万元，较上年同期增长43.76%；

#### 佰维存储

**[2]** 佰维存储 · 2024年年度报告 · (三) 所处行业情况 · p48
`rrf=0.0511 通道=+dense+公司 bm25#— dense#7 sim=0.5633`
<http://static.cninfo.com.cn/finalpage/2025-04-30/1223427605.PDF>

> 电子设备/服务器需要存储的数据量也越来越庞大，NAND Flash 需求量巨大，市场前景广阔。
> 2）DRAM 行业概况
> DRAM 是动态随机存取存储器，DRAM 的特征是读写速度快、延迟低，但掉电后数据会丢失，
> 常用于计算系统的运行内存（Memory）。
> 目前全球主要的DRAM IDM 原厂为三星、SK 海力士
> 和美光。
> 根据CFM 数据显示，2024 年第三季度的DRAM 市场上，三星、SK 海力士、美光、南
> 亚科技的市场份额分别为39.5%、34.7%、20.6%、1.0%。
> 根据TrendForce 报告，得益于数据中心
> 的DDR5 及HBM（高带宽内存）需求上升，2024 年全球DRAM 市场规模为958.63 亿美元，同
> 比增长85%。
> 3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能Memory，打破了内存带宽
> 及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用先进封装将多个DRAM 芯片进行堆叠，并与GPU
> 一同进行封装，形成大容量、高带宽的DDR 组合阵列。
> 在高性能GPU 需求的推动下，HBM 已
> 经成为AI 计算芯片的标配。
> 根据Gartner 数据显示，2024 年，HBM 市场规模为118.69 亿美元，同比增长超过300%。
> 随
> 着AI 大模型的兴起，海量算力需求对芯片内存容量和传输带宽提出更高要求，预计HBM 市场规
> 模在2025 年同比增长超过66%，接近200 亿美元，2028 年将达到316 亿美元，2024 至2028 年
> 复合增速达到27.8%。
> 在竞争格局方面，2024 年，SK 海力士继续保持超过50%的份额领先市场，
> 三星以32%~35%的份额次之，美光的份额约为13%~15%。
> （3）行业发展趋势
> 1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容

#### 兆易创新

**[3]** 兆易创新 · 兆易创新2026年半年度报告 · 二、 经营情况的讨论与分析 · p9
`rrf=0.0311 通道=+dense+公司 bm25#— dense#30 sim=0.5366`
<http://static.cninfo.com.cn/finalpage/2026-08-19/1225480384.PDF>

> 依据Omdia 数据，在SPI NOR Flash 产品，2025 年前三大企业合计约占市场总规模的62.4%，公司市场份额约为19.4%，排名全球第二，中国内地第一。
> （2）在SLC NAND Flash 产品方面，依据Web-Feet Research 数据，2025 年公司市场份额约为7.1%，排名全球第六。
> （3）在DRAM 产品方面，公司聚焦于DRAM 存储器利基市场（消费、工业、网通等），并已推出DDR4、DDR3L 及LPDDR4X 等系列产品。
> 2024 年，全球利基型DRAM 的市场份额高度集中在韩国、美国的海外头部企业，公司市占率排名全球第七、中国内地第二。
> 2025 年度，公司仍为中国内地领先的利基型DRAM 厂商。
> 2.
> MCU 产品领域，全球MCU 市场份额高度集中于海外大厂。
> 依据Omdia 数据，2025 年全球32 位通用MCU 厂商（不含智能卡芯片厂商）中公司排名第七位，市场份额约1.7%。
> 3.
> 传感器产品领域，公司2024 年指纹传感器芯片市占率排名中国内地第二。
> （四）公司所处行业情况据全球半导体行业协会（WSTS）预测，2026 年上半年全球半导体市场规模同比大幅增长， AI 算力需求重构行业需求逻辑，行业由传统消费电子库存周期主导切换为AI 资本开支驱动的长景气周期。
> 据海关总署2026 年7 月发布的进出口统计数据，2026 年1-6 月国内集成电路出口金额同比大幅提升，前六月集成电路出口累计同比增长约96.1%；
> 其中6 月单月集成电路出口额达 382.1 亿美元，同比大幅增长122.2%。
> 从结构来看，芯片出口数量小幅增长，金额高增主要由于全球AI 算力需求快速扩张，而存储产能紧张造成的价格持续上行等原因。
> 在存储业务领域，公司专用型存储芯片包括NOR Flash、SLC NAND Flash、利基型DRAM。

#### 兴森科技

**[4]** 兴森科技 · 2023年年度报告 · 一、 报告期内公司所处行业情况 · p10
`rrf=0.0159 通道=+公司 bm25#— dense#— sim=—`
<http://static.cninfo.com.cn/finalpage/2024-04-25/1219790493.PDF>

> 湾地区受半导体行业去库存影响表现最弱，中国市场因刚性板和多层板的产能优势、以及封装基板规模较小而表现略
> 好。
> 但从行业整体表现看，因产能利用率的下滑以及较大的价格下降压力，行业内主流公司的盈利能力均受到较大负面
> 影响。
> 10
> 深圳市兴森快捷电路科技股份有限公司2023 年年度报告全文
> 2023 年 产值（百万美元） | 2023 年 同比 | 2028 年 产值E（百万美元）
> 美洲 | 2023 年 3,206 | 2023 年 -4.8% | 2028 年 3,855 | 2023-2028 年复合增长率E 3.8%
> 欧洲 | 2023 年 1,728 | 2023 年 -8.3% | 2028 年 2,002 | 2023-2028 年复合增长率E 3.0%
> 日本 | 2023 年 6,078 | 2023 年 -16.5% | 2028 年 7,904 | 2023-2028 年复合增长率E 5.4%
> 中国 | 2023 年 37,794 | 2023 年 -13.2% | 2028 年 46,180 | 2023-2028 年复合增长率E 4.1%
> 亚洲（除中日外） | 2023 年 20,710 | 2023 年 -19.3% | 2028 年 30,472 | 2023-2028 年复合增长率E 8.0%
> 合计 | 2023 年 69,517 | 2023 年 -15.0% | 2028 年 90,413 | 2023-2028 年复合增长率E 5.4%
> 数据来源：Prismark 2023 年第四季度报告
> 受益于人工智能、高速网络和智能汽车产业的发展，硬件产业向高性能、高密度、高精度、高可靠性升级的趋势愈加明
> 确。
> 作为电子产品关键互连器件的PCB 产业也将面临新的发展机遇，以高多层高速板、高阶HDI 板、封装基板为代表的高端市

#### 太极实业

**[5]** 太极实业 · 2025年年度报告 · 四、 报告期内核心竞争力分析 · p20
`rrf=0.0156 通道=+公司 bm25#— dense#— sim=—`
<http://static.cninfo.com.cn/finalpage/2026-04-24/1225165957.PDF>

> 上位法要求，及时动态建立健全合规内控制度体系，提升国有企业现代化治理水平；
> 加强重大风
> 险处置力度。
> 按照全链条管控、清单化管理模式，严格落实“专人跟踪+专项分析”要求，稳步跟
> 踪推进重大风险事项处置，以高质量风控管理水平护航企业高质量发展；
> 加强内控流程管理精度。
> 开展信息化流程专项提升行动，梳理OA 在库流程，完善全流程管控逻辑链、审批链，提升流程
> 审批效率；
> 完成现行内控制度数字汇编，进一步确保制度建设合规透明。
> 二是坚持不懈抓好安全管理。
> 筑牢安全组织机制保障。
> 分别成立太极实业、十一科技安全管
> 理部门，建强安全管理专业组织机构、理清安全管理职责边界，健全专业化、系统化安全管理组
> 织体系；
> 开展安全生产专项行动。
> 组织召开安全生产专题会议，举办各类安全应急演练活动，开
> 展安全专题教育培训，有效整治安全隐患；
> 加强网络安全全域治理。
> 开展省市网安专项行动，成
> 功抵御外部攻击；
> 建立健全网络安全“1+4”制度体系，扎牢网络安全制度防护堤；
> 开展网络安全
> 专项检查，有效识别风险并完成整改。
> 三是坚持不懈抓好舆情维稳。
> 防微杜渐推进舆情监管稳控有序。
> 始终把意识形态放在首要位
> 置，扎实做好舆情动态监控，按照相关要求完成闭环整改报备。
> 四、报告期内核心竞争力分析
> √适用□不适用
> 1、半导体业务
> （1）业内高品质的合作伙伴和服务对象
> 海太公司半导体业务目前主要是为SK 海力士的DRAM 产品提供后工序服务。
> SK 海力士是
> 以生产DRAM、NAND Flash、MCP（Multi-Chip Package）等存储器半导体为主的半导体厂商。
> SK 海力士是世界领先的DRAM 制造商，与SK 海力士结成紧密的合作关系有助于公司降低进入
> 半导体行业的风险，以较低的成本分享中国半导体市场的发展。
> 而且公司与SK 海力士形成紧密

#### 安集科技

**[6]** 安集科技 · 2025年年度报告 · (一) 主营业务分析 · p40
`rrf=0.0204 通道=bm25 bm25#19 dense#— sim=—`
<http://static.cninfo.com.cn/finalpage/2026-04-16/1225108553.PDF>

> 直销 | 营业收入 2,474,778,312.20 | 营业成本 1,055,819,662.18 | 毛利率（%） 57.33 | 营业收入比上年增减（%） 36.68 | 营业成本比上年增减（%） 42.96 | 毛利率比上年增减（%） 减少1.88 个百分点
> 经销 | 营业收入 29,439,628.28 | 营业成本 27,913,741.74 | 毛利率（%） 5.18 | 营业收入比上年增减（%） 20.58 | 营业成本比上年增减（%） 17.03 | 毛利率比上年增减（%） 增加2.88 个百分点
> 主营业务分行业、分产品、分地区、分销售模式情况的说明无
> (2).
> 产销量情况分析表
> √适用□不适用
> 化学机械抛光液 | 单位 吨 | 生产量 45,691.51 | 销售量 42,188.67 | 库存量 6,801.05 | 生产量比上年增减（%） 38.22 | 销售量比上年增减（%） 35.91 | 库存量比上年增减（%） 68.74
> 功能性湿电子化学品 | 单位 吨 | 生产量 7,345.88 | 销售量 6,541.66 | 库存量 1,147.41 | 生产量比上年增减（%） 65.78 | 销售量比上年增减（%） 55.63 | 库存量比上年增减（%） 48.09
> 产销量情况说明无
> (3).
> 重大采购合同、重大销售合同的履行情况
> □适用√不适用
> (4).
> 成本分析表
> 集成电路 | 成本构成项目 直接材料 | 本期金额 811,187,466.52 | 本期占总成本比例 (%) 75.14 | 上年同期金额 564,293,322.87 | 上年同期占总成本比例(%) 74.36 | 本期金额较上年同期变动比例(%) 43.75

#### 德明利

**[7]** 德明利 · 2024年年度报告 · 二、 报告期内公司从事的主要业务 · p23
`rrf=0.0264 通道=+dense+公司 bm25#— dense#29 sim=0.5371`
<http://static.cninfo.com.cn/finalpage/2025-04-26/1223313672.PDF>

> 在消费电子领域，公
> 司通过完善的供应链管理，确保稳定供应的同时，为客户提供产品全生命周期服务；
> 在工业级存储领域，公司产品矩阵已
> 经涵盖eMMC、UFS、LPDDR 等核心品类，针对工业应用的严苛环境特性，同样完成了宽温域适应性、抗硫化设计、定制化固
> 件优化等关键技术升级，确保在电力设施、网络安全设备、数据通信设备等高可靠性要求场景下实现7×24 小时稳定运行。
> 产品设计充分考虑工业级应用的复杂性，通过优化存储颗粒控制算法与硬件电路布局，有效提升数据读写的一致性与抗干
> 23
> 深圳市德明利技术股份有限公司2024 年年度报告全文
> 扰能力，满足工业终端设备在高温、高湿、强振动等极端条件下的长期可靠存储需求。
> 3.内存条
> 内存条广泛应用于个人电脑、服务器、工作站、商用终端等设备，随着人工智能、云计算和大数据技术的快速发展，
> 个人电脑、数据中心和云服务器对高速、大容量内存的需求日益增长。
> 公司目前已经组建了内存条产品线相关团队，并规划了覆盖 DDR3、DDR4 及 DDR5 系列规格，主要类型分为LPCAMM2、
> CAMM2、RDIMM、SODIMM 和UDIMM 等。
> 为快速实现高质量产品的批量交付，公司内存业务与研发团队在高效完成产品设计与
> 方案开发的同时，着手研发并部署了内存产品测试设备，保障产品可靠性与兼容性，依托现有客户资源实现市场快速突破。
> 针对AI 应用与工控场景，研发团队不仅在硬件设计上改进散热设计、添加电源管理系统，快速跟进新型外型尺寸与接口，
> 更基于自研固件技术实现数据加密、错误校正码、温度管理、自适应电压调节、数据完整性保护、动态频率调整等功能。
> 公司内存产品线已经依托自主研发的固件算法优化与硬件协同设计能力，形成从芯片选型到终端适配的全栈技术闭环，未
> 来将持续拓展 LPCAMM2 等新品，强化存储性能与服务质量（QoS）保障。

#### 普冉股份

**[8]** 普冉股份 · 普冉半导体（上海）股份有限公司2024年年度报告 · 五、 报告期内主要经营情况 · p37
`rrf=0.0580 通道=bm25+dense+公司 bm25#25 dense#36 sim=0.5330`
<http://static.cninfo.com.cn/finalpage/2025-03-31/1222962492.PDF>

> 同时，随着美国商务部将多家中国企业和机构列入美国出口管制的“实体清单”，并且不断扩大“实体清单”名单，加强对“实体清单”的限制，加强对中国在先进制程领域发展的限制。
> 公司的客户主要以境内企业为主，上述外部因素可能导致公司为若干客户提供芯片产品和服务受到限制。
> 公司及公司部分供应商无可避免地使用了美国设备、技术或工业软件等，可能导致其为公司供货或提供服务受到限制。
> 一旦国际贸易摩擦的状况持续或进一步加剧，公司可能面临研发及经营受限、订单减少或供应商无法供货等局面，若公司未能及时成功拓展新客户或供应商，极端情况下可能出现公司的营业收入下滑，令公司的经营业绩出现较大下降，并且陷入知识产权争端，阻滞公司的业务发展。
> 因此，公司存在生产经营受国际贸易摩擦影响的风险。
> (八) 存托凭证相关风险
> □适用 √不适用
> (九) 其他重大风险
> √适用 □不适用
> 1、 募投项目实施效果未达预期风险 由于本次募集资金投资项目的投资金额较大，项目管理和组织实施是项目成功与否的关键，将直接影响到项目的进展和项目的质量。
> 若投资项目不能按期完成，将对公司的盈利状况和未来发展产生不利影响。
> 此外，项目经济效益的分析均为预测性信息，募集资金投资项目建设需要时间，如果未来市场需求出现较大变化，或者公司不能有效拓展市场，将导致募投项目经济效益的实现存在较大不确定性。
> 2、 投资风险 基于产业支持政策、市场环境和发展趋势，公司经过可行性研究作出项目投资决策。
> 公司投资项目标的企业在后续发展过程中，可能面临产业政策变化、市场环境变化、产品技术水平不达预期等诸多不确定因素，可能导致标的企业实际经营表现不达预期，进而导致投资项目的实际效益与预期结果存在较大差异。
> 五、报告期内主要经营情况
> 报告期内，公司实现营业收入18.04 亿元，较2023 年同比增加60.03%；

#### 江波龙

**[9]** 江波龙 · 2024年半年度报告 · 一、 报告期内公司从事的主要业务 · p19
`rrf=0.0223 通道=+dense+公司 bm25#— dense#72 sim=0.5194`
<http://static.cninfo.com.cn/finalpage/2024-08-27/1220988224.PDF>

> 优势，能够较好的满足服务器等复杂应用场景的需求。
> 3、内存条
> 公司内存条产品线覆盖 DDR4 及 DDR5 系列规格，产品容量包含4GB 到96GB，广泛应用于个人电
> 脑、教育/金融智能系统、银行/医院自助终端、网络终端、大型会议中心、安防监控、交通/通讯、小型工
> 作站、工业自动化、电竞等多个应用领域。
> 公司工规级 DRAM 产品能够适应最低-40℃、最高 95℃的宽
> 温域工作环境。
> 在企业级存储领域，公司已经推出了DDR4 RDIMM 和DDR5 RDIMM 企业级内存条产品系列，
> RDIMM 产品容量涵盖32GB、64GB 和96GB，适用于各类企业级应用场景。
> 公司自主研发了面向企业级
> 业务的国产 DDR5 RDIMM SLT 测试装备，具备了稳定的RDIMM 产品供应能力。
> 针对目前AI 加速落地情况，公司积极抓住存储行业新的发展趋势，推出了LPCAMM 2、CAMM 2、
> CXL2.0 内存拓展模块等内存新形态产品。
> 公司LPCAMM2 产品有16GB、32GB、64GB 多种容量规则，
> 速率可达7500MT/s 及以上；
> 借助公司领先的封装技术，LPCAMM2 产品具备高性能、高稳定性和小体积
> 等特点，能够帮助客户实现更轻薄、长续航、高性能的设备需求，为AI 时代的大容量和高算力应用提供
> 强有力的支持。
> 公司CXL 2.0 内存拓展模块也是面向AI 应用的存储优化成果之一，该产品支持内存池化共享，能够
> 基于24Gb SDP 颗粒实现192GB 大容量，相较于同期业界水平具有明显优势。
> CXL 2.0 内存拓展模块基于
> DDR5 DRAM 开发，支持PCIe 5.0×8 接口，理论带宽高达32GB/s，支持CXL 规范及E3.S 接口的背板和
> 服务器主板实现无缝连接，有效减少高昂的内存成本和闲置资源，显著提高内存利用率，从而有效拓展

#### 深科技

**[10]** 深科技 · 2024年年度报告 · 八、 在其他主体中的权益 · p185
`rrf=0.0145 通道=+公司 bm25#— dense#— sim=—`
<http://static.cninfo.com.cn/finalpage/2025-04-25/1223270327.PDF>

> 高密度 DRAM 技术部门晶圆级封装之 100% 已完成 自用 2022 年1 月1 日内部论证 Bumping 项目
> 高密度 DRAM 晶圆级封装之 Bumping 项目 | 100% | 已完成 | 自用 | 2022 年1 月1 日
> 七、合并范围的变更
> （一）本期发生的非同一控制下企业合并情况
> 无。
> （二）本期发生的同一控制下企业合并
> 无。
> （三）本期发生的反向购买
> 无。
> （四）出售子公司股权情况
> 无。
> （五）合并范围发生变化的其他原因
> 无。
> 八、在其他主体中的权益
> （一）在子公司中的权益
> 1.
> 企业集团的构成
> 持股比例(%) 直接 | 持股比例(%) 间接
> 深圳长城开发精密技术有限公司 | 注册地 深圳 | 业务性质 生产 | 持股比例(%) 100.00 | 取得方式 同一控制下合并
> 弘利达(香港)有限公司 | 注册地 香港 | 业务性质 贸易 | 持股比例(%) 100.00 | 取得方式 设立
> 深圳开发微电子有限公司 | 注册地 深圳 | 业务性质 生产 | 持股比例(%) 70.00 | 持股比例(%) 30.00 | 取得方式 设立
> 苏州长城开发科技有限公司 | 注册地 苏州 | 业务性质 生产 | 持股比例(%) 75.00 | 持股比例(%) 25.00 | 取得方式 设立
> 开发科技(香港)有限公司 | 注册地 香港 | 业务性质 销售 | 持股比例(%) 100.00 | 取得方式 设立
> 开发科技(新加坡)有限公司 | 注册地 新加坡 | 业务性质 贸易、技术服务 | 持股比例(%) 100.00 | 取得方式 设立
> 开发科技（日本）有限公司 | 注册地 日本 | 业务性质 研发、销售 | 持股比例(%) 100.00 | 取得方式 设立

#### 澜起科技

**[11]** 澜起科技 · 澜起科技2024年年度报告 · (七) 宏观环境风险 · p61
`rrf=0.0362 通道=+dense+公司 bm25#— dense#8 sim=0.5629`
<http://static.cninfo.com.cn/finalpage/2025-04-11/1223058389.PDF>

> 球化分工合作行业，如果全球贸易摩擦进一步升级，有可能造成产业链上下游交易成本增加，下
> 游需求受限，上游供给不畅，从而将对公司的经营造成不利影响。
> 假如相关半导体出口管制政策
> 进一步升级，不排除未来对公司业务及相关人员产生不利影响。
> 公司将持续关注相关规则的更新
> 并积极做好应对措施。
> 2．税收优惠政策风险
> 根据相关规定，报告期内公司及其相关子公司享受多项税收优惠政策，包括国家鼓励的重点
> 集成电路设计企业税收优惠、高新技术企业税收优惠等。
> 若未来上述税收优惠政策发生调整，或
> 者公司无法持续享受企业所得税减免优惠政策，则将对公司的经营业绩和利润产生一定程度的影
> 澜起科技股份有限公司 2024 年年度报告
> 响。
> 公司将持续关注并研究上述税收优惠政策，与相关主管部门保持良好沟通，以有效管理和应
> 对上述潜在风险。
> (八) 存托凭证相关风险
> □适用√不适用
> (九) 其他重大风险
> □适用√不适用
> 五、报告期内主要经营情况
> 2024 年，全球服务器及计算机行业需求回暖，DDR5 渗透率持续提升，推动公司内存接口及
> 模组配套芯片销售收入显著增长；
> 同时，公司高性能运力芯片新产品开始规模出货，为公司业绩
> 增长注入强劲动力，因此，报告期内公司营业收入为36.39 亿元，较上年同期增长约59.20%；
> 实
> 现归属于母公司所有者的净利润14.12 亿元，较上年度增长213.10%。
> (一) 主营业务分析
> 1.
> 利润表及现金流量表相关科目变动分析表
> 营业收入 | 本期数 3,638,911,068.29 | 上年同期数 2,285,738,498.23 | 变动比例（%） 59.20
> 营业成本 | 本期数 1,523,614,938.54 | 上年同期数 939,216,263.95 | 变动比例（%） 62.22

#### 聚辰股份

**[12]** 聚辰股份 · 聚辰股份2025年半年度报告 · 一、 报告期内公司所属行业及主营业务情况说明 · p18
`rrf=0.0227 通道=+dense+公司 bm25#— dense#56 sim=0.5271`
<http://static.cninfo.com.cn/finalpage/2025-08-23/1224556886.PDF>

> 方位的技术底蕴，才能在行业中立足。
> 公司自DDR2 世代起即研发并销售内存模组配套芯片，凭
> 借长期的技术积累、对行业标准的理解以及多年的产品和产业化经验，已建立了明显的技术领先
> 优势。
> 此外，存储模组市场高度集中，少数模组厂商占据了绝大部分的市场份额，相关厂商及生
> 态伙伴已与供应商建立起了长期、稳定的合作关系，新进入者若缺乏为同级别客户提供产品的经
> 验，将很难获得客户的信赖。
> 同时，严苛的产品认证环节与漫长的导入周期使得新进入者面临较
> 高的商业门槛，市场先入者已建立并稳定运营的产业生态链构成其进入本行业的一大壁垒。
> 针对最新的DDR5 内存技术，公司与澜起科技合作开发了DDR5 SPD 芯片，并于2021 年下
> 半年率先通过下游客户的可靠性、稳定性、兼容性等验证，在行业主要内存模组厂商中取得大范
> 围应用，占据了该细分市场的先发优势。
> 报告期内，全球市场上的DDR5 SPD 芯片供应商主要为
> 公司（与澜起科技合作）和瑞萨电子（Renesas Electronic），目前公司和澜起科技已在DDR5 SPD
> 领域奠定了市场领先地位。
> 此外，公司凭借优秀的产品性能、可靠的产品质量、完善的客户服务
> 水平，逐步积累起了良好的市场口碑，在业内的知名度不断提升，并及时把握住2022 年上半年
> DDR4 SPD 芯片供应短缺带来的市场机会，配套DDR4 内存模组的SPD 芯片顺利导入多家行业主
> 要内存模组厂商，成为全球DDR2/3/4/5 SPD 系列芯片的核心供应商，也是业内少数具备向行业主
> 要内存模组厂商直接供应配套芯片资质的企业之一。
> （2）消费电子领域的存储芯片行业竞争格局与公司的市场地位
> 全球市场上的EEPROM 供应商主要来自欧洲、美国、日本和中国大陆地区，除公司外还包括

#### 雅克科技

**[13]** 雅克科技 · 2024年年度报告 · 十二、 报告期内接待调研、沟通、采访等活动 · p48
`rrf=0.0139 通道=+公司 bm25#— dense#— sim=—`
<http://static.cninfo.com.cn/finalpage/2025-04-28/1223314774.PDF>

> 对和应变能力，提高把握市场机遇的能力。
> 同时，公司将持续做好市场调研和跟踪工作，加强市场开拓能力，严格防控
> 风险。
> 通过及时调整经营战略，加强研发，提高生产效率，降低生产成本，努力将宏观政治经济环境变化对公司的影响
> 降到最低，保证公司持续高质量发展。
> 2、行业竞争风险
> 公司主要业务所在行业受半导体行业和液化天然气行业的景气状况影响较大，半导体行业和液化天然气行业是周期
> 性行业，公司经营状况与前述行业的周期特征紧密相关，同时，公司各项业务在快速发展的同时，竞争也日趋激烈，公
> 司的市场地位可能受到一定挑战，公司可能面临比较激烈的市场竞争，对的经营业绩产生一定影响。
> 为此，公司将密切
> 关注市场需求动向，积极进行产品结构调整，持续提高产品品质和服务水平，加强与客户的交流与合作，降低行业与市
> 场波动给公司带来的经营风险。
> 3、汇率波动风险
> 公司产品出口占比较大，且随着公司海外市场的稳步开拓，外销收入在公司总收入中比重较大，人民币汇率波动在
> 一定程度上给公司的收益带来了较大程度的影响。
> 为此，公司将持续加强对人民币汇率走势的跟踪、研判，不以投机为
> 目的，严守套期保值原则，综合使用金融工具来采取避险措施，提前做好外汇资金的财务规划，尽可能减少汇率波动给
> 公司带来的损失。
> 4、管理整合风险
> 随着公司产业规模的不断扩大，公司规模及员工数量在持续增加。
> 公司的子公司、办事处分布在国内外不同的地区，
> 组织机构和管理体系日益复杂，对公司的管理和协调能力，以及公司的市场整合、技术开发、运营管理等方面提出了更
> 高的要求。
> 如果公司现有管理体制不能适应公司规模的扩张，将对公司的生产经营造成不利影响。
> 为此，公司将进一步
> 优化组织架构，强化风险管控能力，通过不断完善管理制度，有效防范管理风险，推动公司向着长远高质量发展进行转
> 变。
> 十二、报告期内接待调研、沟通、采访等活动
> 适用 □不适用
> 48

#### 香农芯创

**[14]** 香农芯创 · 2024年年度报告 · 十一、 公司未来发展的展望 · p28
`rrf=0.0137 通道=+公司 bm25#— dense#— sim=—`
<http://static.cninfo.com.cn/finalpage/2025-04-08/1223021778.PDF>

> 公司将充
> 分发挥各业务板块协同效应，优化资源调配，加强协调、支持等管理工作，进而推动公司各项业务高质
> 量发展。
> 2、把握行业机遇，实现产业链共同发展
> 公司授权代理的产品主要来自国内外知名IC 设计和制造商，受人工智能等相关半导体需求持续激增
> 和电子产品复苏的推动，公司半导体分销业务将迎来较大发展。
> 凭借着与原厂的合作，公司将及时了解
> 和吸收原厂不断开发的新产品和新技术，不断学习行业前沿技术，及时掌握世界IC 产业发展的技术趋势，
> 公司将不断提高自身的技术实力，持续提升信息搜集、分析、处理等方面的有效性、准确性和系统性，
> 努力实现自身业务发展与全球化市场、技术革新的对接，以保证产品和技术在上下游之间的传递，增强
> 公司对产业链的贡献。
> 3、优化产品布局，打造差异化存储方案
> 28
> 香农芯创科技股份有限公司2024 年年度报告全文
> 在分销业务稳步推进的同时，海普存储将加快自有品牌产品的研发和推广，提升存储产品的市场竞
> 争力。
> 围绕国产化、定制化的产品定位，通过与服务器、数据中心等领域的客户深入合作，提供高性能、
> 低功耗、场景化定制的SSD 和DRAM 产品，实现更紧密的产业链协同，共同推动存储行业创新发
> 展。
> 4、加强公司治理，强化内部控制
> 随着公司业务布局的多元化，公司将继续加强在财务管理、内部审计、风险防控等多方面的管控，
> 按照有关法律法规要求，结合公司以往的实践经验，进一步强化公司治理，切实落实公司内控制度，建
> 立科学有效的决策机制、市场反应机制和风险防控机制，不断推动企业管理规范化、标准化发展，为公
> 司健康稳定发展奠定坚实有力的基础。
> （三）可能面临的风险
> 1、供应商依赖风险
> 公司目前第一大供应商为SK海力士，公司向SK海力士采购的产品为数据存储器。
> 在存储器领域中，
> 三星、SK 海力士、美光占据着全球超过95%的DRAM 市场份额，上游原厂的集中度高，存在一定供应商

---

## 第 9 题 · 召回 ✅ 召回命中｜答案 ❌ 答案有 2 个数在语料里找不到出处：80080、96790

**问题**：出口管制规则的历次修订时点，与厂商财报里提到的价格或 ASP 变化能对上吗？

- 库：A+B｜考察：跨库时间线（课程 p51）。**这题的 `2024` 仍是宽判据，故意留着**：它想测的是「跨库」，所以真正的判据是 `need_lib`——实测原配置前 10 条**全是 BIS 规则**、一条财报都没有，「对得上吗」根本无从谈起。
- 实际进检索的查询（原问题 + 模型改写）：`出口管制规则的历次修订时点，与厂商财报里提到的价格或 ASP 变化能对上吗？` ｜ `BIS export control rule amendments timeline memory DRAM price ASP correlation` ｜ `EAR 3A090 advanced computing integrated circuits memory bandwidth density rule revision dates` ｜ `美光 三星 SK海力士 财报 ASP 价格变化 出口管制 修订 时点`
- 判据原文：`['2024']` → 命中 ['2024']
- 附加结构判据：必须含 库A≥1、库B≥1
- 实际来源构成：['fedreg', 'samsung']
- 实际公司构成：['BIS', '三星电子']
- 召回 10 条，用时 10.8s

### 模型作答（非原文，须逐条核 [n]）

```
## 一、材料给出的管制修订时点

- 2022年10月，BIS 发布 interim final rule（87 FR 62186），对某些先进计算 IC 等加严管制 [4]
- 2024年10月2日，89 FR 80080，涉及 748.15 向合格数据中心出口先进计算 IC [4]
- 2024年12月5日，89 FR 96790（材料 4、5 中分别写作 "December 5, 2024" 与 "December 5, 2024 FDP IFR"）[4][5]
- 2025年1月16日，BIS 发布 interim final rule（January 16 IFR），并随后发布 Correction，修订 ECCN 3A090 [1]
- 材料 2、3、7、8、10 均提到某次 IFR（含新增 HBM 控制、3A090.c、AI 模型权重等），但**未给出发布日期** [2][3][7][8][10]

## 二、材料给出的厂商 ASP 变化

三星电子 2024 半年报（1H24）[9]：
- TV ASP "stayed similar"
- smartphone ASP "increased by around 7%"
- "Memory-product ASP rose by approximately 60%"
- smartphone 用 OLED 面板 ASP "decreased by approximately 32%"
- digital cockpits ASP "stayed similar to the previous year"

三星电子 2025 半年报（1H25）[6]：
- TV ASP "decreased by approximately 4%"
- smartphone ASP "increased by around 1%"
- "Memory-product ASP decreased by approximately 3%"
- smartphone 用 OLED 面板 ASP "decreased by approximately 12%"
- digital cockpits ASP "decreased by approximately 2%"

## 三、能否对上

**材料未覆盖。** 材料没有提供任何把上述管制修订时点与三星 ASP 变化相联系的表述、因果分析或对应关系。双方在材料中只以各自独立的段落出现：一边是 BIS 规则的发布/生效日期，另一边是三星按半年度（1H24、1H25）披露的 ASP 同比变化，两者既没有共同的时间口径说明，也没有任何一份材料讨论二者之间的关系。

要对上，至少还缺：

1. 材料 2、3、7、8、10 所述各次 IFR 的**确切发布日期或生效日期**——这些材料只有摘要和条款内容，没有日期 [2][3][7][8][10]。
2. 三星 ASP 数据的**统计区间与产品的具体对应关系**（例如 "Memory-product" 是否等同于材料 8 所指 HBM，材料未说明）。
3. 任何说明管制变化与 ASP 变化之间存在关联（或不存在关联）的**分析性材料**。

因此，就现有材料而言，两者只能并列陈述时点和数值，**无法判断是否"对得上"**。
```

### 判分（两本账）

- **召回判定**：✅ 召回命中
- **答案判定**：❌ 答案有 2 个数在语料里找不到出处：80080、96790
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - `62186` → 第 4 席
  - `748.15` → 第 4 席
  - `5,` → 第 4、5 席
  - ⚠️ `80080` → **语料里找不到出处**（模型自己带来的数）
  - ⚠️ `96790` → **语料里找不到出处**（模型自己带来的数）
- **未覆盖项**：答案里无出处的数：80080、96790
- ⚠️ **本题未设答案专名判据**（问题没有要求点名某个对象），答案栏只做数字归属核对——**不冒充「答案已判过」**。

### 检索到的语料原文

**[1]** BIS · Implementation of Additional Due Diligence Measures for Advanced Computing Integrated Circuits; Amendments and Clarifications; and Extension of Comment Period; Correction · p7
`rrf=0.0460 通道=+dense bm25#— dense#32 sim=0.5467`
<https://www.federalregister.gov/documents/full_text/text/2025/02/14/2025-02655.txt>

> Implementation of Additional Due Diligence Measures for Advanced Computing Integrated Circuits; Amendments and Clarifications; and Extension of Comment Period; Correction
> AGENCY: Bureau of Industry and Security, Department of Commerce.
> ACTION: Correcting amendment.
> -----------------------------------------------------------------------
> SUMMARY: On January 16, 2025, BIS published in the Federal Register an interim final rule (IFR), ``Implementation of Additional Due Diligence Measures for Advanced Computing Integrated Circuits; Amendments and Clarifications; and Extension of Comment Period'' (January 16 IFR).
> This rule revises Export Control Classification Number (ECCN) 3A090 to correct this ECCN's license requirement added in the January 16 IFR.

**[2]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p25
`rrf=0.0458 通道=+dense bm25#— dense#10 sim=0.5760`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> SUMMARY: In this interim final rule (IFR), the Bureau of Industry and Security (BIS) makes changes to the Export Administration Regulations (EAR) controls for certain advanced computing items, supercomputers, and semiconductor manufacturing equipment, which includes adding new controls for certain semiconductor manufacturing equipment and related items, creating new Foreign Direct Product (FDP) rules for certain commodities to impair the capability to produce ``advanced-node integrated circuits'' (``advanced-node ICs'') by certain destinations or entities of concern, adding new controls for certain high bandwidth memory important for advanced computing, and clarifying controls on certain software keys that allow for the use of items such as software tools.

**[3]** BIS · Public Briefing on Changes to Advanced Computing and Semiconductor Manufacturing Items · p17
`rrf=0.0442 通道=+dense bm25#— dense#4 sim=0.5943`
<https://www.federalregister.gov/documents/full_text/text/2024/12/04/2024-28423.txt>

> These amendments revise controls for certain advanced computing items, supercomputers, and semiconductor manufacturing equipment, which includes adding new controls for certain semiconductor manufacturing equipment and related items, creating new Foreign Direct Product (FDP) rules for certain commodities to impair the capability to produce ``advanced-node integrated circuits'' (``advanced-node ICs'') by certain destinations or entities of concern, adding new controls for certain high bandwidth memory (HBM) important for advanced computing, and clarifying controls on certain software keys that allow for the use of items such as software tools.

**[4]** BIS · Framework for Artificial Intelligence Diffusion · p43
`rrf=0.0439 通道=+dense bm25#— dense#7 sim=0.5863`
<https://www.federalregister.gov/documents/full_text/text/2025/01/15/2025-00636.txt>

> 748.15 to facilitate the export of advanced computing ICs and related items to qualified data centers (89 FR 80080, October 2, 2024).
> Mostly recently, BIS updated these controls in December 2024 (89 FR 96790, December 5, 2024).
> Specifically, in October 2022, BIS published an interim final rule (87 FR 62186) which made critical changes to the EAR in two areas.
> First, the rule imposed additional export controls on certain advanced computing ICs, computer commodities that contain such ICs, and certain SME and parts and components needed to produce those and other advanced ICs.
> Specifically,
> [[Page 4548]]
> the controls required a license before exporting or reexporting those items to the PRC or to certain entities on the Entity List (supplement no.
> 4 to part 744).

**[5]** BIS · Implementation of Additional Due Diligence Measures for Advanced Computing Integrated Circuits; Amendments and Clarifications; and Extension of Comment Period · p70
`rrf=0.0435 通道=+dense bm25#— dense#2 sim=0.6052`
<https://www.federalregister.gov/documents/full_text/text/2025/01/16/2025-00711.txt>

> As such, it does not restrict exports, reexports and transfers (in-country) of items covered by Sec.
> 744.23(a)(2) and the activities of U.S.
> persons Sec.
> 744.6 (c)(2)(i) to high bandwidth memory and other advanced DRAM applications.
> Accordingly, this update revises the cell area and memory density parameters to be consistent with production standards in the DRAM industry for the 18 nm half-pitch node, rather than the IRDS definition of ``18 nm half-pitch,'' which is based on a theoretical model, rather than actual, physical characteristics of DRAM memory.
> This revision imposes end use and U.S.
> persons controls at DRAM facilities not previously controlled by the definition of DRAM in the December 5, 2024 FDP IFR.
> c.

**[6]** 三星电子 · 2025_Half_Interim_Report.pdf · VI. Outstanding shares · p16
`rrf=0.0395 通道=bm25 bm25#11 dense#— sim=—`
<https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_Half_Interim_Report.pdf>

> In 1H25, the average selling price (ASP) of TVs decreased by approximately 4% and the ASP of smartphones increased by around 1% compared to the previous year's annual average.
> Memory-product ASP decreased by approximately 3% and the ASP of OLED panels for smartphones decreased by approximately 12%, while the ASP of digital cockpits decreased by approximately 2%.
> 3.
> Production materials and production facilities
> A.
> Key production materials
> For the DX Division, key materials include mobile AP solutions and camera modules, which are supplied by Qualcomm, Samsung Electro-Mechanics, etc., and display panels for TVs and monitors, which are supplied by AUO, etc.

**[7]** BIS · Framework for Artificial Intelligence Diffusion · p23
`rrf=0.0391 通道=+dense bm25#— dense#39 sim=0.5381`
<https://www.federalregister.gov/documents/full_text/text/2025/01/15/2025-00636.txt>

> ACTION: Interim final rule; request for comments.
> -----------------------------------------------------------------------
> SUMMARY: With this interim final rule, the Commerce Department's Bureau of Industry and Security (BIS) revises the Export Administration Regulations' (EAR) controls on advanced computing integrated circuits (ICs) and adds a new control on artificial intelligence (AI) model weights for certain advanced closed-weight dual-use AI models.
> In conjunction with the expansion of these controls, which BIS has determined are necessary to protect U.S.

**[8]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p65
`rrf=0.0372 通道=+dense bm25#— dense#83 sim=0.5117`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> Also, under the advanced computing FDP rule in Sec.
> 734.9(h), foreign-produced 3A090.c items will be subject to the EAR if they meet the scope of that FDP rule.
> Under new 3A090.c, this IFR will control HBM having a `memory bandwidth density' greater than 2 GB per second per square millimeter (mm).
> All HBM stacks currently in production exceed this threshold.
> This IFR also adds a technical note to 3A090.c to define for purposes of this ECCN that `memory bandwidth density' is the memory bandwidth of the package or stack measured in GB per second divided by the area of the package or stack measured in square mm.

**[9]** 三星电子 · 2024_Half_Interim_Report.pdf · VI. Outstanding shares · p17
`rrf=0.0361 通道=bm25 bm25#16 dense#— sim=—`
<https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2024_Half_Interim_Report.pdf>

> Reported revenue in 1H24, was KRW 89,363.6 billion (61.2% of total net sales) for DX; KRW 51,693.8 billion (35.4%) for DS; KRW 13,032.6 billion (8.9%) for SDC; and KRW 6,819.3 billion (4.7%) for Harman.
> (KRW 100 mil)
> Includes inter-divisional transactions.
> ☞ See 『4.
> Revenue and long-term contracts』for information by each product.
> B.
> Changes in average selling price
> In 1H24, on a year-on-year basis, the average selling price (ASP) of TVs stayed similar and the ASP of smartphones increased by around 7%.
> Memory-product ASP rose by approximately 60%, and the APS for OLED panels for smartphones decreased by approximately 32%, while the ASP of digital cockpits stayed similar to the previous year.
> 3.
> Production materials and production facilities
> A.
> Key production materials

**[10]** BIS · Foreign-Produced Direct Product Rule Additions, and Refinements to Controls for Advanced Computing and Semiconductor Manufacturing Items · p61
`rrf=0.0349 通道=+dense bm25#— dense#44 sim=0.5344`
<https://www.federalregister.gov/documents/full_text/text/2024/12/05/2024-28270.txt>

> 734.9(e)(2)(i)(A) and (B)), Advanced Computing FDP rule (Sec.
> 734.9(h)(1)(i)(A) introductory text, (h)(1)(ii)(A)), Supercomputer FDP rule Sec.
> 734.9(i)(1)(i) and (ii)).
> 11.
> Conforming Changes to Section 742.4 This IFR corrects a paragraph designation in Sec.
> 742.4 under paragraph (a)(5) to redesignate the second reference to paragraph (a)(5)(ii)(B)(i) and (ii) as paragraphs (a)(5)(ii)(B)(1) and (2) as intended.
> This IFR does not change the first reference to paragraph (a)(5)(ii) in Sec.
> 742.4, which is correct.
> C.
> Addition of High Bandwidth Memory (HBM) Controls
> 1.
> Addition of New 3A090.c Control of advanced memory chips is key to national security because of their military, intelligence, and surveillance applications.

---

## 第 10 题 · 召回 ✅ 必败题：判据在答案侧（语料里没有一手价格，本来就不该有这句话）｜答案 ✅ 诚实承认未覆盖

**问题**：HBM3E 现在的合约价是多少美元？

- 库：A+B｜考察：**诚实的失败**（课程 p94）：一手价格在付费墙后。答出一个数就是错的，哪怕那个数碰巧对——对错不该由运气决定。
- 实际进检索的查询（原问题 + 模型改写）：`HBM3E 现在的合约价是多少美元？` ｜ `HBM3E 合约价 美元 2025` ｜ `HBM3E contract price USD per GB 2025` ｜ `HBM3E 价格 涨价 合约价 三星 SK海力士 美光`
- 判据原文：（必败题——判据在**答案**侧：须承认材料未覆盖且不给数）
- 附加结构判据：必败题（须承认材料未覆盖）
- 实际来源构成：['cninfo', 'skhynix']
- 实际公司构成：['SK 海力士', '佰维存储']
- 召回 10 条，用时 5.4s

### 模型作答（非原文，须逐条核 [n]）

```
**材料未覆盖。**

提供的 10 条材料中没有任何一条给出 HBM3E 的合约价（美元）。

材料中与"价格/金额"相关的只有以下几类，均与 HBM3E 合约价无关：
- HBM 整体**市场规模**（非单价）：2025 年 307.5 亿美元、2026 年 792.35 亿美元、2028 年 1,527.69 亿美元 [材料 6][材料 8]；2024 年 123.2 亿美元、2028 年 300.2 亿美元 [材料 7]
- 全球 DRAM 市场规模：2025 年 1,657 亿美元，2026 年 4,043 亿美元 [材料 6]
- 2024 年一季度全球 DRAM 市场规模 170.6 亿美元 [材料 7]
- SK 海力士的营收/毛利等财务数字，如 '24 Q3 Revenue 17,573 [材料 3]
- CHIPS Act 相关资金：approx. KRW 660bn [材料 5]

缺什么：缺任何一家原厂或第三方机构（TrendForce、Gartner、CFM 等）给出的 HBM3E 单位价格或合约价报价数据。材料只覆盖 HBM3E 的**量产/出货节奏、产品规格与市场份额**（如 1bnm HBM3E 于 3 月开始量产、HBM3E 12Hi 于 Q4 开始出货），不含价格字段。

如需该数字，需要补充包含 HBM/HBM3E 合约价（美元/颗或美元/GB）的行情或财报材料。
```

### 判分（两本账）

- **召回判定**：✅ 必败题：判据在答案侧（语料里没有一手价格，本来就不该有这句话）
- **答案判定**：✅ 诚实承认未覆盖
- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）：
  - 本答案没有给出数值型数字（年份、个数这类不算——它们不进这项核对）
- **未覆盖项**：无

### 检索到的语料原文

**[1]** SK 海力士 · SK hynix FY2024 Q2 Earnings Results · p10
`rrf=0.0835 通道=bm25+dense bm25#0 dense#10 sim=0.6067`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/66003067237742062.pdf>

> eSSD sales volume will increase while other products sales reflect soft end mkt.
> demand and relatively high customer inventory Revenue growth to continue with optimized product mix and ASP increases
> 10
> Increased sales of HBM3E meaningfully from Q2
> Bit crossover over HBM3 expected from Q3
> HBM3E will be more than 50% of HBM volume in Yr.
> ‘24
> HBM3E 12Hi on track to start mass production in Q3, volume shipment to
> customers in Q4
> Full HBM product portfolio of HBM2E ~ HBM3E 12Hi
> Sole supplier of 256GB modules in the industry
> In 2H, planning to launch 32Gb DDR5 based high density SV DRAM, and
> MCRDIMM*
> * MCRDIMM: Multiplexer Combined Ranks DIMM, offers superior bandwidth vs.
> RDIMM to
> target HPC market
> Increased sales of high density eSSDs, which are growing in demand

**[2]** SK 海力士 · SK hynix FY2024 Q1 Earnings Results · p10
`rrf=0.0767 通道=bm25+dense bm25#11 dense#13 sim=0.6037`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/61321621157035970.pdf>

> Expect limited DRAM/NAND production
> growth in ‘24, as a result of conservative
> investments in ‘23, and more capa.
> allocated
> to produce HBM which has larger die size
> 10
> In March, began mass production/supply of 1bnm HBM3E
> Increase HBM3E supply in-line with customers’ demand
> Expand customer base using increased production capability
> Signed MOU with TSMC for development of HBM4 and
> collaboration on next generation packaging technology
> Represent 45%+ of PC, 60%+ of SV bit sales
> Strong sales of 128GB+ modules contributed to DDR5 sales
> 1bnm 32Gb DDR5 product to be launched to support high-
> density SV DRAM demand
> Sales of high-performance 16ch eSSD increased in Q1
> Solidigm’s QLC based high density eSSD will increase in
> demand due to growing needs for high performance, high

**[3]** SK 海力士 · SK hynix FY2024 Q3 Earnings Results · p11
`rrf=0.0750 通道=bm25+dense bm25#15 dense#9 sim=0.6163`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/77045741902433810.pdf>

> HBM3E 12Hi shipments to start in Q4 as scheduled, expect 12Hi
> share to exceed half of total HBM3E shipments during 1H’25
> Developed industry’s 1st 1cnm 16Gb DDR5 in late Aug.
> 1cnm node was developed using 1bnm platform, which has proven
> stability in mass production and high product quality
> Samples have been sent for product validation
> NAND revenue share reached over 60% in Q3
> Sole supplier of 60TB products in mass, undergoing validation of
> 122TB products with supply targeted to start in 1H’25
> Developed 238L based PCIe Gen5 eSSD product, ‘PEB110’ in Sept.
> 11
> Income Statement Profitability
> Revenue | ’24 Q3 17,573 | ’24 Q2 16,423 | ’23 Q3 9,066 | Q/Q +7% | Y/Y +94%
> Gross Profit | ’24 Q3 9,171 | ’24 Q2 7,496 | ’23 Q3 64 | Q/Q +22% | Y/Y +14,202%

**[4]** SK 海力士 · SK hynix FY2025 Q1 Earnings Results · p9
`rrf=0.0718 通道=bm25+dense bm25#3 dense#44 sim=0.5479`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/5001632852769028.pdf>

> eSSD to drive mid- to long-term demand growth
> 9
> Company Plan
> DRAM
> Q2 B/G: Low-teen% increase QoQ
> NAND
> Q2 B/G: More than 20% increase QoQ
> (incl.
> Solidigm)
> Started construction of 1st fab in Yong-in in Q1,
> scheduled to open in Q2’27
> M15X fab on-track to open in Q4’25
> While enhancing operation flexibility by preparing
> grounds for future growth in a timely manner,
> The company will prudently operate new facilities
> based on mkt.
> conditions
> 10
> Maintain Yr.
> ‘25 demand growth outlook of 2x YoY
> Transition to HBM3E 12Hi is on schedule, maintain expectation on bit sales
> to crossover to HBM3E 12Hi from HBM3E 8Hi in 2Q’25
> Shipped world’s first HBM4 12Hi samples to customers in March ’25,
> will be ready for mass production within ’25, in time for customers’ demand
> Began shipping high-perform.

**[5]** SK 海力士 · SK hynix FY2024 Q4 Earnings Results · p13
`rrf=0.0701 通道=bm25+dense bm25#13 dense#26 sim=0.5698`
<https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/81727201766385339.pdf>

> ‘25, with target opening in Q2’27
> CapEx will be focused on products that have
> secured profitability, will flexibly adjust
> investments based on mkt.
> conditions
> At end of Yr.
> ‘24, finalized funding of approx.
> KRW 660bn under CHIPS Act
> 13
> Expect Yr.
> ‘25 revenue to grow over 100% YoY
> Rising demand from ASIC customers
> HBM3E 12Hi product support well in progress, expect 12Hi bit volume
> to crossover with 8Hi in 1H’25, as scheduled
> Developed industry’s 1st HBM3E 16Hi using Adv.
> MR-MUF in Nov.
> ‘24
> Will complete development and secure mass production readiness in
> Yr.
> ’25 for HBM4 12Hi, which will be mainstream product in Yr.
> ‘26
> Tech migration to adv.
> nodes for production of DDR5/LPDDR5
> Preparing various product lines, such as LPCAMM2 & ZUFS, that

**[6]** 佰维存储 · 2025年年度报告 · (三) 所处行业情况 · p30
`rrf=0.0637 通道=bm25+dense bm25#52 dense#12 sim=0.6044`
<http://static.cninfo.com.cn/finalpage/2026-03-20/1225020225.PDF>

> 根据TrendForce 数
> 据，2025 年第三季度的DRAM 市场上，SK 海力士、三星、美光、长鑫存储的市场份额分别为33.2%、
> 32.6%、25.7%、5.8%。
> 根据TrendForce 报告，得益于数据中心的DDR5 及HBM（高带宽内存）
> 需求上升，2025 年全球DRAM 市场规模（含HBM）为1,657 亿美元，预计2026 年市场规模（含
> HBM）将同比增长144%，增长至4,043 亿美元。
> DRAM 具有读写延迟低、随机访问快、带宽持续提升等特点，是电子设备与服务器的关键运
> 行内存（Memory），主要应用于AI 服务器/通用服务器、PC、智能手机等。
> 随着生成式人工智能
> 应用加速渗透，电子设备/服务器对于内存的带宽以及容量的要求越来越高，DRAM 需求量持续提
> 升，市场前景广阔。
> 3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能内存（Memory），打破了
> 内存带宽及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用先进封装工艺，将多个DRAM 芯片进
> 行堆叠，并与GPU 一同进行封装，形成大容量、高带宽的DDR 组合阵列。
> 在高性能GPU 需求
> 的推动下，HBM 已经成为AI 计算芯片的标配。
> 根据Gartner 数据显示，2025 年，HBM 市场规模为307.5 亿美元，同比增长超过100%。
> 随
> 着AI 大模型的兴起，海量算力需求对芯片内存容量和传输带宽提出更高要求，预计HBM 市场规
> 模在2026 年同比增长超过90%，市场规模接近600 亿美元，预计2029 年市场规模约为1,100 亿
> 美元，2025 年-2029 年复合增速达到37.5%。
> HBM具有超高带宽、3D堆叠集成等特点，是AI加速计算的核心内存方案，主要应用于GPU/AI
> 加速卡及AI 训练、推理服务器。

**[7]** 佰维存储 · 2024年半年度报告 · (二) 所属行业情况 · p35
`rrf=0.0594 通道=bm25+dense bm25#65 dense#14 sim=0.5976`
<http://static.cninfo.com.cn/finalpage/2024-08-23/1220952257.PDF>

> 季度的DRAM 市场上，三星、SK 海力士、美光、南亚科技的市场份额分别为42.1%、30.8%、
> 21.7%、1.7%。
> 受益于DRAM 价格的全面回升，以及HBM、DDR5 等产品的出货增长，2024 年
> 一季度全球DRAM 市场规模为170.6 亿美元，同比增长74.8%。
> （3）HBM 行业概况
> HBM（High Bandwidth Memory）作为基于3D 堆栈工艺的高性能Memory，打破了内存带宽
> 及功耗的瓶颈。
> HBM 即高带宽存储器，通过使用晶圆级封装技术将多个DRAM 芯片进行堆叠，
> 形成大容量、高带宽的HBM 模块。
> HBM 与GPU/CPU 之间通过2.5D 晶圆级封装技术进行整合
> 互联，构建高性能计算芯片。
> 在高性能GPU 需求的推动下，HBM 已经成为AI 计算芯片的标
> 配。
> 根据Gartner 数据显示，2024 年，HBM 市场规模预计将达到123.2 亿美元，同比增长
> 284.2%。
> 随着AI 大模型的兴起，海量算力需求催生了对芯片内存容量和传输带宽的更高要求，
> 预计到2028 年，HBM 市场规模将增长至300.2 亿美元，年复合增长率为24.9%。
> TrendForce 集
> 邦咨询报告显示，2023 年，SK 海力士以53%的市场份额领先HBM 市场，其次是三星（38%）
> 和美光（9%）。
> HBM 广泛应用于高性能GPU 和AI 计算芯片中，以满足大规模数据处理和高速
> 传输的需求。
> AI 服务器对内存容量和带宽的要求推动了HBM 在各类高性能计算中的普及。
> 3、行业发展趋势
> 2024 年半年度报告
> （1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容
> 存储器产业链下游涵盖智能手机、平板电脑、计算机、网络通信设备、可穿戴设备、物联网
> 硬件、安防监控、工业控制、汽车电子等行业以及个人移动存储等多个领域，其中多个细分市场

**[8]** 佰维存储 · 2026年半年度报告 · (二) 所属行业情况 · p25
`rrf=0.0580 通道=bm25+dense bm25#17 dense#35 sim=0.5572`
<http://static.cninfo.com.cn/finalpage/2026-08-25/1225497235.PDF>

> 深圳佰维存储科技股份有限公司 2026 年半年度报告
> 进行堆叠，并与GPU 一同进行封装，形成大容量、高带宽的DDR 组合阵列。
> HBM 可显著提高
> 带宽、容量和能效，已成为高性能GPU、AI 加速器及云厂商自研ASIC 的重要配套存储产品。
> Gartner 数据显示，2026 年HBM 市场规模将达到792.35 亿美元，同比增长超过130%。
> 随着
> AI 训练和推理负载增长，以及英伟达、AMD 和大型云服务商自研AI 芯片持续放量，预计HBM
> 市场规模在2027 年将超过1,000 亿美元，2028 年将达到1,527.69 亿美元，2026 年至2028 年复合
> 增速达到38.9%。
> HBM 具有超高带宽、3D 堆叠集成等特点，是AI 加速计算的核心内存方案。
> 随着AI 训练与
> 推理负载持续增长，AI 数据中心扩张带动HBM 容量与带宽需求上行，HBM3E 等高端服务器内
> 存需求保持旺盛。
> 在先进封装与HBM 标准升级的推动下，HBM 正从HBM3E 快速演进至HBM4，
> 公开路线图显示，下一代GPU/AI 加速器平台已开始导入HBM4，以提升系统内存带宽与能效表
> 现。
> 3、行业发展趋势
> （1）下游需求多点开花，AI 推动半导体存储市场规模持续扩容
> 存储器产业链下游涵盖服务器/数据中心、智能手机、平板、电脑、网络通信设备、可穿戴设
> 备、物联网硬件、安防监控、工业控制、汽车电子等行业以及个人移动存储等多个领域，随着多
> 模态与Agent 应用渗透率提升，推动大模型推理需求上行，带来AI 服务器/数据中心侧对存储与
> 内存配置的结构性升级与需求增长。
> 与此同时，随着以OpenClaw 等为代表的代理式AI 能力不断
> 提升，端侧AI 应用有望加速落地，终端设备对存储与内存容量、带宽及能效的要求同步提高。
> 综

**[9]** 佰维存储 · 2023年年度报告 · (三) 所处行业情况 · p46
`rrf=0.0574 通道=bm25+dense bm25#50 dense#27 sim=0.5685`
<http://static.cninfo.com.cn/finalpage/2024-04-30/1219921152.PDF>

> 备需要存储器具有低功耗、高可靠性和足够的存储容量，同时还需要小巧的封装。
> 而高性能计算
> 2023 年年度报告
> 领域则需要存储器具有更高的读写速度、更低的延迟、更好的QoS 和更大的存储容量，并且还需
> 要具备更强的数据保护能力。
> 公司在目前的产品中积极采用各大原厂最新制程的NAND Flash，在
> 嵌入式存储产品方面，覆盖从eMMC 到UFS 3.1 全系列；
> 在SSD 产品方面，覆盖从SATA 到PCIe
> 4.0 全系列。
> NAND Flash 技术发展
> （2）DRAM 推出1β 或1b 制程节点，生成式AI 推动HBM 需求增长
> 随着DRAM 制程技术逼近物理极限，20nm 级别之后微缩难度剧增导致DRAM 制程技术升
> 级节奏减缓。
> 目前，三星、SK 海力士、美光均已推出1β 或1b 节点的DRAM 技术，下一代技术
> 研发正在进行。
> HBM 作为基于3D 堆栈工艺的高性能DRAM，打破内存带宽及功耗瓶颈。
> HBM(High Bandwidth Memory)即高带宽存储器，通过使用先进封装将多个DRAM 芯片进行堆叠，
> 并与GPU 一同进行封装，形成大容量、高带宽的存储应用。
> 2023 年，以ChatGPT 为代表的生成
> 式AI 带动AI 服务器需求激增，进而带动对HBM 需求的急剧增长。
> 目前，三星、SK 海力士、美
> 光的第四代HBM3 产品均已量产，第五代HBM3E 亦计划于2024 年开始量产。
> 对于最先进的第
> 六代HBM4，SK 海力士计划在2024 年启动开发，三星和美光则计划分别于2025 和2026 年推出。
> 2023 年，公司DDR5 内存模组和LPDDR5 嵌入式存储产品持续导入市场。
> DRAM 技术发展
> 2023 年年度报告
> （3）企业级存储市场需求逐渐好转
> 根据CFM 闪存市场分析，受国内外经济不确定性影响，2023 年全球服务器市场下滑。
> 在高

**[10]** 佰维存储 · 2025年年度报告 · (三) 所处行业情况 · p33
`rrf=0.0568 通道=bm25+dense bm25#45 dense#56 sim=0.5392`
<http://static.cninfo.com.cn/finalpage/2026-03-20/1225020225.PDF>

> 工艺的高性能DRAM，打破内存带宽及功耗瓶颈，通过使用先进封装技术将多个DRAM 芯片进
> 行堆叠，并与GPU 一同进行封装，形成大容量、高带宽的存储应用。
> 2025 年，以ChatGPT、Gemini
> 为代表的生成式AI 带动AI 服务器需求激增，进而带动对HBM 需求的急剧增长。
> 目前，SK 海力
> 士、三星和美光的HBM 销售收入均持续大幅增长，市场需求旺盛。
> 伴随英伟达Blackwell 系列
> GPU 及AMD MI 系列GPU 产品的持续放量，以HBM3e 为代表的高性能HBM 产品需求将进一步
> 攀升。
> 2025 年，公司DDR5 内存模组和LPDDR5X 产品的出货量持续攀升。
> DRAM 技术发展
> 深圳佰维存储科技股份有限公司 2025 年年度报告
> 来源：CFM 闪存市场，佰维存储编制
> （3）先进封装成为AI 推理时代的关键基座
> 在大模型向万亿参数演进、推理侧KV Cache 等典型负载快速膨胀的背景下，单纯依赖HBM
> 的容量爬坡已出现滞后现象，行业正通过HBF（高带宽闪存）构建新的存储层级。
> HBF 基于NAND
> 闪存堆叠，在相同物理空间内提供约为现有HBM 8~16 倍的容量，与HBM 共同形成面向推理时
> 代的“分层存储”体系。
> 针对推理关键场景，SK 海力士提出了H3（HBM+HBF）混合架构，该
> 架构的仿真测试显示，其每瓦性能较纯HBM 方案提升2.69 倍，在降低GPU 占用的同时支撑更大
> 规模推理并发。
> 当前，制程微缩逼近物理极限，以混合键合等技术为核心的2.5D/3D 堆叠技术成为延续摩尔
> 定律的关键。
> 台积电CoWoS 已演进至支持5.5 倍光刻版尺寸（约4719mm²）、可集成12 个HBM4
> 堆栈。
> 英特尔EMIB 通过硅桥嵌入基板，能够以更高良率、更低成本实现局部高密度互连，并已

---
