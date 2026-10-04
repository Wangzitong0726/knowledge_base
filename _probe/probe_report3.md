# 探测第三轮报告

生成时间：2026-10-04 15:25:46

| 检查项 | 结果 | 实测记录 |
|---|---|---|
| eCFR titles.json（title 15 修订日） | ✅ | {'number': 15, 'name': 'Commerce and Foreign Trade', 'latest_amended_on': '2026-09-24', 'latest_issue_date': '2026-09-24', 'up_to_date_as_of': '2026-10-01', 'reserved': False} |
| eCFR full 2026-08-10 Accept=application/xml | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2026-08-10 Accept=text/xml | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2026-08-10 Accept=*/* | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2026-01-01 Accept=application/xml | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2026-01-01 Accept=text/xml | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2026-01-01 Accept=*/* | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2025-06-01 Accept=application/xml | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2025-06-01 Accept=text/xml | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2025-06-01 Accept=*/* | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2024-12-02 Accept=application/xml | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2024-12-02 Accept=text/xml | ❌ | HTTP 406 Not Acceptable |
| eCFR full 2024-12-02 Accept=*/* | ❌ | HTTP 406 Not Acceptable |
| eCFR structure 端点 | ✅ | 200 842KB |
| govinfo CFR-2025 title-15 vol-2 | ✅ | 200 b'<?xm' 6.96MB 含3A090=True |
| govinfo bulkdata 目录 | ❌ | 200 b'<!DO' 0.03MB 含3A090=False |
| BIS EAR 页里的 PDF 链接 | ✅ | 发现 2 个 PDF：['/media/documents/bis-sorn-80-fr-63737.pdf', '/media/documents/qualityguidelines.pdf'] |
| BIS 规则清单（2024-10 起） | ✅ | 共 54 篇最终规则 |
| 在这批规则里 grep 'HBM' | ✅ | 命中 1 篇 |
|   ▶ 2026-01-15 91 FR 1684 | ✅ | HBM×1 high-bandwidth×1 3A090×6 | Revision to License Review Policy for Advanced Computing Commodities |
| SK hynix IR 首页 | ❌ | HTTP 404 Not Found |
| SK hynix IR 公告列表 | ❌ | HTTP 404 Not Found |
| Samsung IR 首页 | ✅ | 200 329KB PDF链接=20 ['//images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_2Q_conference_eng.pdf', '//images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_2Q_conference_eng.pdf', 'https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_Half_Interim_Report.pdf'] |
| Samsung IR 财报页 | ✅ | 200 211KB PDF链接=62 ['//images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_1Q_conference_eng.pdf', '//images.samsung.com/is/content/samsung/assets/global/ir/docs/2026_2Q_conference_eng.pdf', '//images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_1Q_conference_eng.pdf'] |
| Samsung IR 年报页 | ❌ | HTTP 404 Not Found |
| DART 公司检索 JSON | ❌ | 200 5KB JSON=False '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8" />\n<meta name="viewport" content="width=device-width,initial-scale=1' |
| DART 英文站 dartList | ❌ | 200 5KB JSON=False '<!DOCTYPE html>\r\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\r\n\r\n<head>\r\n<title>DART - Repository' |
| TrendForce 新闻列表页 | ✅ | 200 137KB 文章链接 13 条；['/presscenter/news/20260921-13247.html', '/presscenter/news/20260922-13249.html', '/presscenter/news/20260924-13252.html'] |
| TrendForce 单篇文章正文 | ✅ | 36552 字 含涨跌幅表述=False；摘=" (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start': new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0], j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src= 'https://www.goo" |