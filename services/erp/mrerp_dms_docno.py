# -*- coding: utf-8 -*-
"""DMS 订车单自动编号与已占用号扫描。

MR.ERP 原生取号协议(2026-09-13 只读实测 · drfcbc 模块):

* ``component/php/autonum.php`` → ``[idautonum, enabled, prefix, digits, format]``;
  当前实例返回 ``[16, 1, "BK", 6, 1]`` —— ``prefix`` 来自配置(不是写死的 BK),
  ``digits`` 是流水位宽,启用位不是 ``"1"`` 表示没开自动编号。
* ``component/php/autonumdetail.php`` → ``[idautonumdetail, nextautonum, lastautonum]``;
  当前分店返回 ``[27, 1, "BK000002609000001"]``。DMS 自带 ``mtform.js`` 把三个值写进
  隐藏字段 ``idatndt`` / ``natn``,并把 ``lastautonum`` 拆成「前缀栏 + 数字主体栏」
  (``txtprefixautonum`` + ``txtdocno``),保存时按这两栏分别提交。

所以本模块把「取号」表达成一个显式的原生状态(前缀 + 完整号 + 数字主体 + 隐藏字段),
而不是一个丢了隐藏字段的裸字符串:提交时必须原样带上 ``idatndt``/``natn`` 才会推进
计数器,否则下一次取号又回同一个号(当前实例 1~7 已占用却仍回 ...000001 就是这个原因)。
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

BOOKING_DOCNO_MAX_TRIES = 25
BOOKING_LIST_PAGE_SIZE = 100
BOOKING_LIST_MAX_PAGES = 100

# 隐藏字段名 —— 与 DMS 自带 mtform.js 一致。
HIDDEN_IDAUTNUMDETAIL = "idatndt"
HIDDEN_NEXTAUTONUM = "natn"


@dataclass(frozen=True)
class DMSAutonumDetail:
    """autonumdetail.php 的原始三元组(保留形状,便于对照真机)。"""

    idautonumdetail: Any
    nextautonum: Any
    lastautonum: Any


@dataclass(frozen=True)
class DMSBookingAutonumState:
    """DMS 原生取号状态 —— 建单 POST 与回读所需的全部编号契约。

    ``prefix`` 来自 ``autonum.php`` 的配置值(当前实例是 ``BK``,但绝不写死);
    ``docno`` 是完整号(``cfg[2]`` + 数字主体),原生表单里存成
    ``txtprefixautonum=prefix`` + ``txtdocno=body`` 两栏。
    """

    prefix: str
    docno: str
    digits: int
    idautonumdetail: str
    nextautonum: int

    @property
    def body(self) -> str:
        """原生表单 ``txtdocno`` 栏的值:完整号去掉精确前缀后的数字主体。"""
        return self.docno[len(self.prefix) :]

    @property
    def tail_serial(self) -> str:
        """完整号末尾 ``digits`` 位流水(autonum 计数器实际推进的那一段)。"""
        return self.docno[-self.digits :]

    def with_docno(self, docno: str, *, digits: Optional[int] = None) -> "DMSBookingAutonumState":
        """换号的唯一入口:完整号换成 ``docno``,``natn`` 只按尾号差前移,绝不被重置。

        原生语义:``natn``(隐藏字段 ``natn`` = ``autonumdetail.php`` 的
        ``detail[1]``)是 DMS 自己的取号计数器基数,它只保证「比已占用号大」,
        **不保证等于当前单号的尾号** —— 同一实例可以 ``natn=101`` 而单号尾号是 ``1``。
        所以换号只能加上「新尾号 - 旧尾号」的 delta(= 计数器为跨过多少号而前进的步数),
        用新号的尾号绝对值覆盖它会把计数器基数抹掉,下一次取号直接倒回旧区间。

        两条硬约束:换一次号只调用一次(重复调用会把同一个 delta 推两次,号段推过头);
        ``nextautonum + delta`` 一旦为负说明调用方拿到的状态已经不自洽,直接抛错而不是
        写一个无效计数器。

        ``digits`` 只用于按新号重新切尾号,默认沿用本状态的位宽。
        """
        width = self.digits if digits is None else digits
        old_serial = int(self.tail_serial)
        new_serial = int(docno[-width:])
        nextautonum = self.nextautonum + (new_serial - old_serial)
        if nextautonum < 0:
            raise ValueError("autonum nextautonum would become negative")
        return replace(self, docno=docno, digits=width, nextautonum=nextautonum)


def parse_autonum_detail(detail_body: str) -> DMSAutonumDetail:
    """autonumdetail.php 响应 → 原始三元组;形状不对即抛 ``ValueError``。"""
    detail = json.loads(detail_body)
    if not isinstance(detail, list) or len(detail) < 3:
        raise ValueError("autonumdetail is not the native 3-field tuple")
    return DMSAutonumDetail(idautonumdetail=detail[0], nextautonum=detail[1], lastautonum=detail[2])


def autonum_state(cfg_body: str, detail_body: str) -> DMSBookingAutonumState:
    """解析 ``autonum.php`` + ``autonumdetail.php`` 响应为原生取号状态。

    任一必需字段缺失/无效即抛 ``ValueError``,由调用方 fail closed —— 绝不拿空串兜底,
    也绝不自行拼一个 ``booking_no``。校验项:

    * ``cfg[0]`` 编号器 id 存在;``cfg[1]`` 必须是启用位 ``1``;
    * ``cfg[2]`` 前缀非空(任意字符,不假定 ASCII 字母、不假定长度);
    * ``cfg[3]`` 流水位宽是正整数;
    * ``detail[2]`` 完整号以 ``cfg[2]`` 开头、余下主体非空、末 ``digits`` 位是数字;
    * ``detail[0]`` / ``detail[1]``(隐藏字段 ``idatndt`` / ``natn``)存在且有效。
    """
    cfg = json.loads(cfg_body)
    if not isinstance(cfg, list) or len(cfg) < 5:
        raise ValueError("autonum config is not the native 5-field tuple")
    if cfg[0] is None or str(cfg[0]) == "":
        raise ValueError("autonum id is missing")
    if str(cfg[1]) != "1":
        raise ValueError("autonum is disabled for this menu")
    prefix = str(cfg[2] or "")
    if not prefix:
        raise ValueError("autonum prefix is empty")
    try:
        digits = int(cfg[3])
    except (TypeError, ValueError) as exc:
        raise ValueError("autonum digit width is not an integer") from exc
    if digits <= 0:
        raise ValueError("autonum digit width must be positive")

    detail = parse_autonum_detail(detail_body)
    idautonumdetail = str(detail.idautonumdetail or "").strip()
    if not idautonumdetail:
        raise ValueError("autonumdetail idatndt is missing")
    try:
        nextautonum = int(str(detail.nextautonum).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("autonumdetail natn is not a non-negative integer") from exc
    if nextautonum < 0:
        raise ValueError("autonumdetail natn must not be negative")
    docno = str(detail.lastautonum or "").strip()
    if not docno.startswith(prefix) or len(docno) <= len(prefix):
        raise ValueError("autonumdetail number does not start with the configured prefix")
    if not docno[-digits:].isdigit():
        raise ValueError("autonumdetail number does not end with the configured digit width")
    return DMSBookingAutonumState(
        prefix=prefix,
        docno=docno,
        digits=digits,
        idautonumdetail=idautonumdetail,
        nextautonum=nextautonum,
    )


def is_duplicate_docno_error(body: str) -> bool:
    """DMS 单号重复报错(err::"เลขที่ใบจอง" ซ้ำ)。"""
    return body.startswith("err::") and "ซ้ำ" in body


def bump_docno(docno: str) -> str:
    """末尾连续数字段加一并保持位宽。"""
    index = len(docno)
    while index > 0 and docno[index - 1].isdigit():
        index -= 1
    head, tail = docno[:index], docno[index:]
    if not tail:
        return docno + "1"
    return head + str(int(tail) + 1).zfill(len(tail))


def listing_docnos(body: str, prefix: str, digits: int) -> set[str]:
    """订车列表 HTML 中与当前自动编号系列完全同形的单号。"""
    if not prefix or digits <= 0:
        return set()
    pattern = rf"(?<![A-Z0-9]){re.escape(prefix)}\d{{{digits}}}(?!\d)"
    return set(re.findall(pattern, body or ""))


@dataclass(frozen=True)
class DMSBookingDocnoScan:
    """列表扫描结果:绕过跟全局唯一约束失步的 DMS 自动编号器。

    ``docno`` 是本次要提交的完整号,``numeric_tail`` 是它末尾 ``digits`` 位流水,
    ``delta`` 是相对 DMS 候选号的流水前移量(natn 必须同量前移)。
    """

    docno: str
    numeric_tail: str
    delta: int


def scan_unoccupied_docno(
    candidate: str,
    digits: int,
    post_text: Callable[[str, Dict[str, str]], str],
) -> DMSBookingDocnoScan:
    """从订车列表现有最大流水号之后开始，绕过失步的 DMS 自动编号器。

    只读:仅调 ``showdata.php`` 列表。拿不到列表(瞬时故障)或候选号形状不合协议时
    原样返回候选号(``delta=0``),绝不为了「顺号」去猜一个号。

    ``delta`` 只作为 ``DMSBookingAutonumState.with_docno`` 的输入(它把 ``natn`` 前移
    这个差值);本函数不碰计数器,也不假设 ``natn`` 等于候选号尾号。
    """
    if digits <= 0 or len(candidate) <= digits:
        return DMSBookingDocnoScan(candidate, candidate[-digits:] if digits > 0 else "", 0)
    prefix, suffix = candidate[:-digits], candidate[-digits:]
    if not suffix.isdigit():
        return DMSBookingDocnoScan(candidate, suffix, 0)

    highest = int(suffix) - 1
    seen: set[str] = set()
    try:
        for page in range(1, BOOKING_LIST_MAX_PAGES + 1):
            body = post_text(
                "drfcbc/component/showdata.php",
                {
                    "sdtamt": str(BOOKING_LIST_PAGE_SIZE),
                    "sdtpage": str(page),
                    "sd": prefix,
                    "ftd": "1",
                    "selcolsort": "1",
                    "selcolsorttype": "2",
                },
            )
            page_docnos = listing_docnos(body, prefix, digits)
            new_docnos = page_docnos - seen
            if not new_docnos:
                break
            seen.update(new_docnos)
            highest = max(highest, *(int(value[-digits:]) for value in new_docnos))
            if len(page_docnos) < BOOKING_LIST_PAGE_SIZE:
                break
    except Exception as exc:
        logger.warning("[dms] booking docno listing failed; use autonum candidate: %s", exc)
        return DMSBookingDocnoScan(candidate, suffix, 0)

    next_number = max(int(suffix), highest + 1)
    return DMSBookingDocnoScan(
        f"{prefix}{str(next_number).zfill(digits)}",
        str(next_number).zfill(digits),
        next_number - int(suffix),
    )


__all__ = [
    "BOOKING_DOCNO_MAX_TRIES",
    "DMSAutonumDetail",
    "DMSBookingAutonumState",
    "DMSBookingDocnoScan",
    "HIDDEN_IDAUTNUMDETAIL",
    "HIDDEN_NEXTAUTONUM",
    "autonum_state",
    "bump_docno",
    "is_duplicate_docno_error",
    "listing_docnos",
    "parse_autonum_detail",
    "scan_unoccupied_docno",
]
