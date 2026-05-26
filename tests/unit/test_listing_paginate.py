"""守门 · MR.ERP allview.php 列表全量分页(_listing_paginate)。

锁定 2026-05-26 实证的 showdata.php 分页机制:逐页 POST 累计、
末页/空页正确终止、端点路径按模块拼对、表单参数照搬 showdata.js。
纯单测 · 注入假 request_post · 不打网络。
"""

import unittest

from services.erp._listing_paginate import (
    SHOWDATA_NUMROWS,
    fetch_all_listing_pages,
)


class _FakeResp:
    def __init__(self, body: str):
        self._body = body

    def text(self) -> str:
        return self._body


def _row_html(code: str) -> str:
    """一条 allview 行(顶层 <p> + 4 span)· 喂给假 parse_fn。"""
    return (
        f"<p><span>{code}</span><span>type</span>" f"<span>pre</span><span>name-{code}</span></p>"
    )


def _page(codes):
    return "<div>" + "".join(_row_html(c) for c in codes) + "</div>"


def _parse(html):
    """假 parser:每个 <span> 里第一个就是 code · 抽出 <p> 里第一个 span。"""
    import re

    out = []
    for m in re.finditer(r"<p\b[^>]*>(.*?)</p>", html, re.DOTALL):
        sm = re.search(r"<span>(.*?)</span>", m.group(1), re.DOTALL)
        if sm:
            out.append(sm.group(1))
    return out


class FetchAllListingPagesTests(unittest.TestCase):
    def _make_post(self, pages):
        """pages = list[list[code]] · 第 N 次 POST 返第 N 页 · 超出 → 空 body。"""
        self.calls = []

        def _post(url, *, form):
            self.calls.append((url, form))
            idx = int(form["showdata_pages"]) - 1
            if 0 <= idx < len(pages):
                return _FakeResp(_page(pages[idx]))
            return _FakeResp("")  # 越界 = 空(showdata.js 收到无 <p> 即停)

        return _post

    def test_single_partial_page_stops(self):
        """只有 1 页且不足 30 条 → 一次 POST 就停。"""
        post = self._make_post([["A", "B", "C"]])
        rows = fetch_all_listing_pages(post, "https://x", "/armas/allview.php", _parse)
        self.assertEqual(rows, ["A", "B", "C"])
        self.assertEqual(len(self.calls), 1)

    def test_multi_page_accumulates(self):
        """整页 30 + 次页部分 → 跨页累计全量。"""
        full = [f"C{i:03d}" for i in range(SHOWDATA_NUMROWS)]  # 30
        tail = ["T1", "T2"]
        post = self._make_post([full, tail])
        rows = fetch_all_listing_pages(post, "https://x", "/armas/allview.php", _parse)
        self.assertEqual(rows, full + tail)
        # 整页后继续翻 · 次页不足 30 即停 → 共 2 次 POST。
        self.assertEqual(len(self.calls), 2)

    def test_exact_multiple_then_empty(self):
        """整 30 + 整 30 + 空页 → 累计 60 · 第 3 次空页终止。"""
        p1 = [f"A{i:03d}" for i in range(SHOWDATA_NUMROWS)]
        p2 = [f"B{i:03d}" for i in range(SHOWDATA_NUMROWS)]
        post = self._make_post([p1, p2])  # 第 3 页越界 → 空
        rows = fetch_all_listing_pages(post, "https://x", "/armas/allview.php", _parse)
        self.assertEqual(len(rows), 60)
        self.assertEqual(len(self.calls), 3)

    def test_endpoint_path_and_form(self):
        """端点 = 模块前缀 + /component/showdata.php · 表单照搬 showdata.js。"""
        post = self._make_post([["X"]])
        fetch_all_listing_pages(post, "https://www.mrerp4sme.com", "/stkmas/allview.php", _parse)
        url, form = self.calls[0]
        self.assertEqual(url, "https://www.mrerp4sme.com/stkmas/component/showdata.php")
        self.assertEqual(form["showdata_numrows"], "30")
        self.assertEqual(form["showdata_pages"], "1")
        self.assertEqual(form["searchdataval"], "")

    def test_max_pages_guard(self):
        """服务端永远返整页(异常)→ max_pages 硬上限兜底防死循环。"""
        big = [f"R{i:03d}" for i in range(SHOWDATA_NUMROWS)]

        def _post(url, *, form):
            return _FakeResp(_page(big))  # 永远整页

        rows = fetch_all_listing_pages(
            _post, "https://x", "/armas/allview.php", _parse, max_pages=5
        )
        self.assertEqual(len(rows), 5 * SHOWDATA_NUMROWS)


if __name__ == "__main__":
    unittest.main()
