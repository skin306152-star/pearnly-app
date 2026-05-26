"""MR.ERP allview.php 列表全量分页抓取(showdata.js 实证机制)。

背景:`<module>/allview.php` 的 `#showdata` 列表由站点脚本
`component/javascript/showdata.js` **滚动驱动**填充——首屏只有 30 条,
往下滚才 AJAX 取下一页。导致 `_fetch_listing` 只读到首页 ~30 条:
客户/商品 > 30 个时第 31+ 个在 picker 下拉里看不到、匹配兜底也扫不到。

showdata.js 实证逻辑(2026-05-26 · TEST2019 · test01 抓的真样本):

    var showdata_numrows = 30;
    var showdata_pages   = 1;
    // 滚到底 → POST <module>/component/showdata.php
    //   { showdata_numrows:30, showdata_pages:N, searchdataval:'' }
    // 返回当页 <p> 行(offset=(N-1)*30)· append 到 #showdata · pages+=1
    // result 无 <p> 也无 id="nodata" → pages=0(没有更多页 · 停)

实测:pages=1 → 首 30 条;pages=2 → 次 30 条(本测试库 28 条);
pages=3 → 空 body → 停。offset 干净、无跨页重叠。

本 helper 照搬该机制:用已登录会话(page.request 带 cookie)直接 POST
showdata.php 逐页累计,绕开"滚动才加载"的浏览器交互,把列表拉全量。
解析仍交给各模块自带的 parse_fn(parse_armas_listing / parse_stkmas_listing)。
"""

from __future__ import annotations

import logging
import re
from typing import Callable, List, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# showdata.js 写死的每页行数。
SHOWDATA_NUMROWS = 30
# 硬上限防死循环:400 页 × 30 = 12000 行,远超任何真实主数据规模。
_MAX_PAGES = 400

_P_TAG = re.compile(r"<p\b", re.IGNORECASE)


def _count_rows(body: str) -> int:
    """页面里顶层 <p> 行数(每条客户/商品 = 一个 <p> · 内层只有 span)。"""
    return len(_P_TAG.findall(body or ""))


def fetch_all_listing_pages(
    request_post,
    login_url: str,
    listing_path: str,
    parse_fn: Callable[[str], List[T]],
    *,
    max_pages: int = _MAX_PAGES,
    searchdataval: str = "",
) -> List[T]:
    """逐页 POST showdata.php 把 allview.php 列表(可带搜索过滤)拉全量。

    Args:
        request_post: Playwright `page.request.post` 可调用对象
            (签名 `(url, *, form=...) -> APIResponse`,response 有 `.text()`)。
            传函数而非整个 page,便于单测注入假实现。
        login_url:   adapter.login_url(已去尾斜杠)。
        listing_path: 模块列表路径,如 "/armas/allview.php" / "/stkmas/allview.php"。
        parse_fn:    把一页 HTML 解析成行对象列表(各模块自带的 parser)。
        max_pages:   分页硬上限(防死循环)。
        searchdataval: showdata.php 的搜索过滤值(空=全量)· 传月份码前缀(如 "P2605")
            可只翻该前缀的少量行 → 自动建码找真实 max **完整且轻量**(不必翻整本 2060)。

    Returns:
        全部页累计的行对象列表(顺序 = MR.ERP 列表顺序)。
    """
    # /armas/allview.php → 模块前缀 /armas → showdata 端点同模块的 component/ 下。
    module = listing_path.rsplit("/", 1)[0]
    endpoint = f"{login_url}{module}/component/showdata.php"

    rows: List[T] = []
    pages_fetched = 0
    for pg in range(1, max_pages + 1):
        resp = request_post(
            endpoint,
            form={
                "showdata_numrows": str(SHOWDATA_NUMROWS),
                "showdata_pages": str(pg),
                "searchdataval": searchdataval or "",
            },
        )
        body = resp.text() or ""
        pages_fetched = pg
        n_p = _count_rows(body)
        # showdata.js 终止条件:本页无 <p> → 没有更多页。
        if n_p == 0:
            break
        rows.extend(parse_fn(body))
        # 不足整页 = 末页(LIMIT 30 只返 < 30 → 后面必空)· 提前停省一次空 POST。
        if n_p < SHOWDATA_NUMROWS:
            break

    logger.info(
        "fetched full listing %s: %d rows across %d page(s)",
        listing_path,
        len(rows),
        pages_fetched,
    )
    return rows


__all__ = ["fetch_all_listing_pages", "SHOWDATA_NUMROWS"]
