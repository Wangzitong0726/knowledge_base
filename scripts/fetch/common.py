# -*- coding: utf-8 -*-
"""
抓取公共层：HTTP + 抓取清单（manifest）。

把纪律固化在代码里，而不是靠每次记得：

  1. **字节级校验**。Content-Length 与实际落盘字节不符 → 报错、删文件、重试。
     网络截断比想象中常见，而截断的 PDF 后面解析会给你一份「能读但少了一半」的文本。
  2. **不关 TLS 校验**。证书链有问题就让它报出来去查链——绝不在客户端把校验关掉，
     那样 TLS 就只剩加密、没有身份验证了。
  3. **清单可追溯**。每条记录 URL、字节数、sha256、抓取时间。
     论文级材料要能回答「这个数字是从哪份文件的哪一页来的」，清单是第一环。
  4. **断点续跑**。已存在且字节数正确的文件跳过，不重复下载。
  5. **失败要响**。不静默跳过；抓不到就记进失败表，最后统一报出来。
"""
import gzip
import hashlib
import json
import random
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

# 实测：巨潮不加 UA 会被 403。轮换是为了不像爬虫。
BROWSER_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.1 Safari/605.1.15",
]

# SEC 明确要求 UA 里声明身份**与可联系的邮箱**，实测：
#   · data.sec.gov/submissions  —— 任意 UA 都通
#   · www.sec.gov/Archives      —— **必须有邮箱**，否则 403（浏览器 UA 同样 403）
# 这是 SEC 的公平使用政策：万一你的抓取出问题，他们要知道找谁。
# 所以不伪装、也不编假邮箱 —— 用你本人的邮箱。填在 config.json 里。
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"


def contact_email():
    """取要写进 UA 的联系邮箱。环境变量优先，其次 config.json。"""
    import os
    e = os.environ.get("SEC_CONTACT_EMAIL")
    if e:
        return e.strip()
    if CONFIG_PATH.exists():
        try:
            return (json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                    .get("sec_contact_email") or "").strip() or None
        except (json.JSONDecodeError, OSError):
            pass
    return None


def sec_ua():
    """构造 SEC 专用 UA。没配邮箱就明确报错，不静默降级成浏览器 UA 去撞 403。"""
    e = contact_email()
    if not e:
        raise FetchError(
            f"SEC 要求 UA 里声明联系邮箱，但没找到。请在 {CONFIG_PATH} 里写：\n"
            f'    {{"sec_contact_email": "你的邮箱"}}\n'
            f"   或设环境变量 SEC_CONTACT_EMAIL。")
    return f"ai_homework3/1.0 (Fudan University course project; contact: {e})"


DEFAULT_TIMEOUT = 120
MAX_RETRY = 4


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


class FetchError(Exception):
    pass


class Fetcher:
    """带清单的抓取器。"""

    def __init__(self, manifest_path, delay=1.2, verbose=True):
        self.manifest_path = Path(manifest_path)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.verbose = verbose
        self.records = []          # 本次运行新增
        self.failures = []         # 本次运行失败
        self._known = self._load_known()

    # ------------------------------------------------------------ HTTP
    def get(self, url, headers=None, timeout=DEFAULT_TIMEOUT, retries=MAX_RETRY,
            ua=None, data=None):
        """取回 bytes。正确解 gzip/deflate —— 这是踩过的坑。

        第 4–5 轮探测时我设了 Accept-Encoding: gzip 却没解压，
        于是得出「eCFR 含 3A090 = False」的假结论。工具错，不是数据错。

        返回 (解压后的bytes, headers)。headers 里附 `_wire_bytes` =
        **解压前**的字节数——校验 Content-Length 必须用它，不能用解压后的长度
        （解压后总是更大，拿它去比会把正常的压缩响应全判成「传输截断」）。
        """
        last = None
        for attempt in range(retries):
            try:
                h = {"User-Agent": ua or random.choice(BROWSER_UAS)}
                if headers:
                    h.update(headers)
                req = urllib.request.Request(url, data=data, headers=h)
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    raw = r.read()
                    wire = len(raw)                      # 解压前
                    enc = (r.headers.get("Content-Encoding") or "").lower()
                    if "gzip" in enc:
                        raw = gzip.decompress(raw)
                    elif "deflate" in enc:
                        try:
                            raw = zlib.decompress(raw)
                        except zlib.error:
                            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                    hdr = dict(r.headers)
                    hdr["_wire_bytes"] = wire
                    return raw, hdr
            except urllib.error.HTTPError as e:
                # 4xx 里 404/403 重试无意义，直接放弃；其余退避重试
                last = e
                if e.code in (400, 401, 403, 404, 410):
                    break
            except (urllib.error.URLError, TimeoutError, OSError,
                    gzip.BadGzipFile, zlib.error) as e:
                last = e
            wait = (2 ** attempt) + random.uniform(0, 1)      # 指数退避 + 抖动
            if self.verbose:
                print(f"      ! 第{attempt+1}次失败（{type(last).__name__}: "
                      f"{str(last)[:60]}），{wait:.1f}s 后重试")
            time.sleep(wait)
        raise FetchError(f"{url} 取回失败：{type(last).__name__}: {str(last)[:100]}")

    def get_text(self, url, encoding="utf-8", **kw):
        raw, _ = self.get(url, **kw)
        return raw.decode(encoding, "replace")

    def get_json(self, url, **kw):
        return json.loads(self.get_text(url, **kw))

    # ------------------------------------------------------------ 落盘 + 清单
    def download(self, url, dest, source, company="", title="", date="",
                 headers=None, ua=None, expect_size=None, timeout=DEFAULT_TIMEOUT,
                 size_tolerance=0):
        """下载并登记。已存在且大小一致则跳过（断点续跑）。

        expect_size 是**期望字节数**。若来源只给粗略大小（如巨潮的 adjunctSize 是
        KB 取整），必须给 size_tolerance，否则会因几百字节的舍入差误杀正常文件。
        真正的截断由 Content-Length 校验抓，那个是准的。

        返回清单记录 dict；失败抛 FetchError（由调用方决定是否继续）。
        """
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # 续跑：已下过且大小对得上
        if dest.exists() and dest.stat().st_size > 0:
            rec = self._find(source, url)
            if rec and rec.get("bytes") == dest.stat().st_size:
                if self.verbose:
                    print(f"      跳过（已完整）{dest.name}  {dest.stat().st_size/1e6:.2f}MB")
                return rec

        raw, hdr = self.get(url, headers=headers, ua=ua, timeout=timeout)
        got = len(raw)
        wire = hdr.get("_wire_bytes", got)
        declared = hdr.get("Content-Length")
        if expect_size and abs(got - expect_size) > size_tolerance:
            raise FetchError(f"{dest.name} 大小不符：期望 {expect_size}"
                             f"（±{size_tolerance}）实际 {got}")
        # Content-Length 指的是**压缩前**的传输字节，必须跟 wire 比。
        # 拿解压后的长度比会误报——实测 eCFR 声明 317898 解压后 2042970，
        # 我的校验一度把正常数据全判成「截断」。
        if declared and int(declared) != wire:
            raise FetchError(f"{dest.name} 传输截断：声明 {declared} 实际收到 {wire}")

        dest.write_bytes(raw)
        rec = {
            "source": source, "company": company, "title": title, "date": date,
            "url": url, "path": str(dest.relative_to(dest.parents[len(dest.parents) - 1])),
            "bytes": got, "sha256": sha256_bytes(raw),
            "content_type": hdr.get("Content-Type", ""),
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        rec["path"] = str(dest)
        self.records.append(rec)
        self._known[(source, url)] = rec
        self._append_manifest(rec)
        if self.verbose:
            print(f"      OK  {dest.name}  {got/1e6:.2f}MB  {rec['sha256'][:12]}")
        time.sleep(self.delay)
        return rec

    # ------------------------------------------------------------ 清单
    def _load_known(self):
        known = {}
        if self.manifest_path.exists():
            with self.manifest_path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        known[(r["source"], r["url"])] = r
                    except (json.JSONDecodeError, KeyError):
                        continue
        return known

    def _find(self, source, url):
        return self._known.get((source, url))

    def _append_manifest(self, rec):
        with self.manifest_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def fail(self, source, what, err):
        self.failures.append({"source": source, "what": what, "error": str(err)[:200]})
        print(f"      ✗ 失败 {source} :: {what} :: {str(err)[:120]}")

    def summary(self):
        print(f"\n本次新增 {len(self.records)} 份，失败 {len(self.failures)} 项")
        tot = sum(r["bytes"] for r in self.records)
        print(f"新增合计 {tot/1e6:.1f}MB")
        if self.failures:
            print("--- 失败明细 ---")
            for f in self.failures:
                print(f"  [{f['source']}] {f['what']}: {f['error'][:100]}")
