# 探测第五轮报告

生成时间：2026-10-04 15:28:23

| 检查项 | 结果 | 实测记录 |
|---|---|---|
| eCFR full + gzip 正确解压 | ✅ | 2.13MB Content-Encoding=gzip 含3A090=True 含HBM=True |
| govinfo CFR-2025 title15 vol2 | ✅ | 6.96MB 含3A090=True 含'High Bandwidth Memory'=True |
| 抽出 3A090.c 正文 | ✅ | 35 处 |
| 抽出 License Exception HBM | ✅ | 已存 extract_license_exception_hbm.txt |
|   · '3A090.a' 出现次数 | ✅ | 9 次 |
|   · '3A090.b' 出现次数 | ✅ | 4 次 |
|   · '3A090.c' 出现次数 | ✅ | 35 次 |
|   · '3A090.d' 出现次数 | ✅ | 0 次 |
|   · 'HBM' 出现次数 | ✅ | 10 次 |
|   · 'DRAM' 出现次数 | ✅ | 0 次 |
| 根域 | ✅ | 24KB PDF=0 疑似IR链接=['/ir/UI-FR-IR06', '/ir/UI-FR-IR07', '/ir/UI-FR-IR12_T1'] |
| 英文主站 | ❌ | HTTP 404 |
| IR 入口(旧) | ❌ | HTTP 404 |
| 年报页 | ❌ | HTTP 404 |
| SK hynix 全球英文 | ❌ | HTTP 404 |
| SK hynix 会社案内 | ❌ | HTTP 404 |
| newsroom 英文列表 | ✅ | 152KB PDF=0 疑似IR链接=[] |