# 探测第二轮报告

生成时间：2026-10-04 15:24:19

| 检查项 | 结果 | 实测记录 |
|---|---|---|
| eCFR 重试（默认 UA + Accept: application/xml） | ❌ | HTTP 406 |
| eCFR 重试（默认 UA + Accept: */*） | ❌ | HTTP 406 |
| eCFR 重试（浏览器 UA + Accept: application/xml） | ❌ | HTTP 406 |
| eCFR 重试（默认 UA + Accept: application/xml + Accept-Encoding: identity） | ❌ | HTTP 406 |
| eCFR 目录树 API | ✅ | 200 5.7s 8KB '{"titles":[{"number":1,"name":"General Provisions","latest_amended_on":"2022-12-29","latest_issue_date":"2026-08-10","up' |
| eCFR 单节 JSON | ❌ | HTTPError: HTTP Error 406: Not Acceptable |
| MOPS 首页（正常校验） | ❌ | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed cer |
| MOPS 证书本身 | ❌ | 握手阶段就失败：[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl |
| 台湾证交所 www.twse.com.tw（正常校验） | ❌ | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get l |
| 公开资讯观测站 openapi（正常校验） | ❌ | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed cer |
| DART 英文检索接口（SK hynix） | ✅ | 200 0.8s 5KB '<!DOCTYPE html>\r\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\r\n\r\n<head>\r\n<title>DART - Repository of Korea\'s Corporate Filings<' |
| DART 中文站检索接口（SK하이닉스） | ✅ | 200 1.0s 5KB '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8" />\n<meta name="viewport" content="width=device-width,initial-scale=1.0,minimum-scale=1.0,maximum-scale=1.0,user-scalable=no" />\n<meta http-equiv="X-' |
| Federal Register 搜 'high bandwidth memory' | ✅ | count=153；1994-01-04 Government-Owned Inventions; Availability for Licensing；1994-04-19 Government-owned Inventions; Availability for Licensing；1994-05-16 Export Administration Regulations: Changes in Categorie；1994-11-17 Public Mobile Services; Final Rule FEDERAL COMMUNICATIO；1994-11-18 National Institute on Disability and Rehabilitation Res |
| 最早一篇正文 | ✅ | 48KB 标题=Government-Owned Inventions; Availability for Licensing；含'3A090'=False 含'HBM'=False 含'Comment'=True |
| 巨潮 PDF 二进制落盘（修正第一轮 bug） | ✅ | 200 3.29MB 头=b'%PDF' 澜起科技2026年半年度报告 |
| PDF 文字层提取 | ✅ | 196 页 / 有文字页 196 / 共 171446 字 → 平均 875 字/页 |
| PDF 表格按行列还原（find_tables） | ✅ | 第12页 检出 4 张表；首表 4行×2列；首行=['公司选定的信息披露报纸名称', '上海证券报（www.cnstock.com）、证券时报\n（www.stcn.com）、中国证券报（www.cs.com.cn）'] |
| 正文抽样（第11页） | ✅ | '澜起科技股份有限公司 2026 年半年度报告 11 / 196 上海临骥 指 上海临骥投资合伙企业（有限合伙） 上海临利 指 上海临利投资合伙企业（有限合伙） 上海临国 指 上海临国投资合伙企业（有限合伙） 临桐建发 指 上海临桐建发投资合伙企业（有限合伙） 上海临齐 指 上海临齐投资合伙企业（有限合伙） 嘉兴宏越 指 嘉兴宏越投资合伙企业（有限合伙） 嘉兴莫奈 指 嘉兴莫奈股权投资合伙企业（有限' |
| SEC 10-K 落盘 | ✅ | 10-K 2025-10-03 2.44MB 主文档=mu-20250828.htm |
| SEC HTML 文字提取（lxml） | ✅ | 389245 字 / 72 张 <table> |
|   · 关键词 'HBM' | ✅ | 命中 35 次 |
|   · 关键词 'high bandwidth memory' | ✅ | 命中 0 次 |
|   · 关键词 'export control' | ✅ | 命中 2 次 |
|   · 关键词 'Entity List' | ✅ | 命中 0 次 |
|   · 关键词 'China' | ✅ | 命中 39 次 |