# 作业三 · 语料来源探测报告

生成时间：2026-10-04 15:21:40

| 来源 | 结果 | 实测记录 |
|---|---|---|
| 巨潮 topSearch（取 orgId） | ✅ 可用 | 200 0.2s 296B → code=688008 orgId=9900039002 zwjc=澜起科技 category=A股 |
| 巨潮 hisAnnouncement（按年报/半年报类别筛） | ✅ 可用 | 200 0.1s 5216B total=8 命中=8；前几条=['澜起科技2026年半年度报告', '澜起科技2026年半年度报告摘要', '澜起科技2025年年度报告', '澜起科技2025年年度报告摘要', '澜起科技2025年半年度报告'] |
| 巨潮 PDF 全文下载 | ✅ 可用 | 200 0.2s 3.29MB '%PDF' 文件=澜起科技2026年半年度报告 |
| SEC company_tickers.json | ✅ 可用 | 200 0.9s 799085B → MU cik=0000723125 MICRON TECHNOLOGY INC |
| SEC submissions（美光申报清单） | ✅ 可用 | 200 0.5s 0.16MB name=MICRON TECHNOLOGY INC sic=Semiconductors & Related Devices；最近=[('10-Q', '2026-06-25', '2026-05-28'), ('10-Q', '2026-03-19', '2026-02-26'), ('10-Q', '2025-12-18', '2025-11-27'), ('10-K', '2025-10-03', '2025-08-28')] |
| SEC 主文档（10-K/10-Q）下载 | ✅ 可用 | 200 0.7s 1.53MB 10-Q 2026-06-25 报告期=2026-05-28 html="<?xml version='" |
| Federal Register API（BIS 文件检索） | ✅ 可用 | 200 0.8s 20186B count=69；最近=[('2026-07-14', 'Enhanced Favorable Treatment for the United Arab E'), ('2026-01-15', 'Revision to License Review Policy for Advanced Com'), ('2025-09-16', 'Additions and Revisions to the Entity List')] |
| Federal Register 单篇正文 | ✅ 可用 | 200 1.2s 119KB 提HBM=False 标题=Enhanced Favorable Treatment for the United Arab Emirates Un |
| eCFR API（15 CFR 774 商业管制清单全文） | ❌ 不可用 | HTTPError: HTTP Error 406: Not Acceptable |
| eCFR 按 section 精确取 | ❌ 不可用 | HTTPError: HTTP Error 406: Not Acceptable |
| BIS 官网首页 | ✅ 可用 | 200 1.2s 76KB |
| BIS EAR 页 | ✅ 可用 | 200 2.4s 12788KB |
| DART 英文站首页 | ✅ 可用 | 200 1.0s 97KB 首80字='<!DOCTYPE html>\r\n<html xmlns="http://www.w3.org/1999/x' |
| DART 中文站首页 | ✅ 可用 | 200 0.6s 157KB 首80字='<!DOCTYPE html>\r\n<html xmlns="http://www.w3.org/1999/xhtml" xml' |
| OpenDART API 无 key 探测 | ❌ 不可用 | 200 0.5s 0KB 首80字='{"status":"010","message":"등록되지 않은 인증키입니다."}' |
| MOPS 首页 | ❌ 不可用 | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self- |
| MOPS 年报查询页 | ❌ 不可用 | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self- |
| TWSE OpenAPI | ❌ 不可用 | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self- |
| TrendForce 新闻中心 | ✅ 可用 | 200 1.4s 232KB 提DRAM/HBM/NAND=True |
| TrendForce 首页 | ✅ 可用 | 200 0.6s 144KB 提DRAM/HBM/NAND=True |
| A 股内存产业链 orgId 批量取号 | ✅ 可用 | 成功 15/16；未命中=['北京君正'] |

**小结：15/21 项通过。**