# -*- coding: utf-8 -*-
"""会计手录四类单据(收款/付款/手工凭证/库存调整)载荷的共用校验原语。

与 mapper.py / sales_mapper.py 的差别在输入源:那两条路吃 OCR 抽取结果,这四类吃会计
在录入台填的表单 —— 没有票面可回头对,所有金额恒等式必须在组装当场闭合,错了退回给
填表的人;等推到内网再炸,那边已经在改别人的发票单头了(45 号契约 P0-1)。

钱全程 Decimal(与 common._d/_s 同一套);定宽列按 cp874 字节数,不按字符数。
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Dict, List, Optional

from services.erp.express_push.common import _d, _q, _s, parse_invoice_date, thai_dbf_safe

ZERO = Decimal("0")
_QTY_STEP = Decimal("0.0001")  # STCRD.TRNQTY / TFACTOR 是 B(8,4)

# 分录方向,与老链路 lines[].side 同字面(桥端 TRNTYP:D→'0' 借 / C→'1' 贷)。
SIDE_DEBIT = "D"
SIDE_CREDIT = "C"
# 分录行的科目列名。桥端 doc_journal 读 `account`,老链路读 `acc` —— 常量化是为了让
# 「改名」这件事只发生在一处,而不是散在校验与组装两侧各写一个字面量。
ACCOUNT_KEY = "account"


def money(value: Any) -> Optional[Decimal]:
    """字符串/数字 → Decimal。解析不了 → None(钱不碰 float)。"""
    return _d(value)


def money_str(value: Decimal) -> str:
    """Decimal → 定点两位字符串(载荷里的钱一律字符串化)。"""
    return _s(value)


def quantize_qty(value: Decimal) -> Decimal:
    """数量/换算系数按四位小数落位。

    数量不能跟着钱走分位:按两位落位,0.0625 公斤会变成 0.06、TFACTOR 1.408 会变成
    1.41,库存余额靠 XTRNQTY = TRNQTY × TFACTOR 移动,两处各歪一点就再也对不回去。
    """
    return value.quantize(_QTY_STEP, rounding=ROUND_HALF_EVEN)


def qty_str(value: Decimal) -> str:
    """Decimal → 定点四位字符串(载荷里的数量一律字符串化)。"""
    return format(quantize_qty(value), "f")


def same(left: Decimal, right: Decimal) -> bool:
    """分位对齐后严格相等。

    45 号契约里的 0.005 容差只属于【读回】那一侧 —— 那边比的是 VFP double 存出来的
    26319.219999999972。组装侧的钱从表单进来就是 Decimal,放松容差只会放过录入笔误。
    """
    return _q(left) == _q(right)


def within(left: Decimal, right: Decimal, tol: Decimal) -> bool:
    """带容差比较。只用于【派生值】(如预扣税额 = 税基×税率)。

    派生值的舍入口径是 Express 那边的,数据上没证实是 half-up 还是 half-even;为一分钱
    退回一张合法的付款单,比放过它更糟。差超过一分说明税基或税率本身填错了。
    """
    return abs(_q(left) - _q(right)) <= tol


def cp874_len(text: Any) -> int:
    """定宽列 C(n) 数的是 cp874 字节:泰文在 cp874 单字节、在 UTF-8 三字节。

    按 len(str) 判宽会放过超长值,写盘时被 Express 静默截成半个泰文词。
    """
    return len(thai_dbf_safe(str(text or "")).encode("cp874", errors="ignore"))


def cp874_trim(text: Any, limit: int) -> str:
    """按 cp874 字节截断(摘要类自由文本用;主键类超长一律拒,不截)。"""
    raw = thai_dbf_safe(str(text or ""))
    encoded = raw.encode("cp874", errors="ignore")
    if len(encoded) <= limit:
        return raw
    return encoded[:limit].decode("cp874", errors="ignore")


def width_error(label: str, text: Any, limit: int) -> Optional[str]:
    """定宽超长 → 错误文案;合规 → None。"""
    if cp874_len(text) > limit:
        return f"{label} 超出 Express 定宽 C({limit})"
    return None


def iso_docdate(raw: Any) -> Optional[str]:
    """公历 ISO / DD-MM-YYYY → 公历 ISO YYYY-MM-DD。解析不出 → None。

    四类手录单据的日期走公历 ISO,不走老链路的佛历 `docdate_be`:桥端
    `writepath/doc_payload.iso_date` 只认 `date.fromisoformat`,佛历串在那边一律
    INVALID_DOC_DATE。佛历只出现在桥端自己拼的单号里。
    """
    d = parse_invoice_date(raw)
    return d.isoformat() if d else None


def lines_error(lines: Any, *, min_lines: int = 1, positive: bool = False) -> Optional[str]:
    """复式分录形状 + 借贷平衡。返回错误文案或 None。

    科目列名是 `account`(桥端 `writepath/doc_journal` 逐行读它;老链路那套走
    `bridge.client._assert_lines_balanced` 的 `acc`,两条路不共用这一份)。
    positive=True 时另钉 AMOUNT>0(GLJNLIT.AMOUNT 恒为正,方向只由 TRNTYP 表达 ——
    负数进去 Express 会当反方向记)。
    """
    floor = max(1, min_lines)
    if not isinstance(lines, list) or len(lines) < floor:
        return f"lines 须为至少 {floor} 行的数组"
    sums = {SIDE_DEBIT: ZERO, SIDE_CREDIT: ZERO}
    for i, line in enumerate(lines):
        if not isinstance(line, dict) or not str(line.get(ACCOUNT_KEY) or "").strip():
            return f"lines[{i}] 缺科目 {ACCOUNT_KEY}"
        side = line.get("side")
        if side not in sums:
            return f"lines[{i}].side 须为 D/C: {side!r}"
        amount = money(line.get("amount"))
        if amount is None:
            return f"lines[{i}].amount 解析不了: {line.get('amount')!r}"
        if positive and amount <= ZERO:
            return f"lines[{i}].amount 须为正数: {line.get('amount')!r}"
        sums[side] += amount
    if not same(sums[SIDE_DEBIT], sums[SIDE_CREDIT]):
        return f"借贷不平: D={sums[SIDE_DEBIT]} C={sums[SIDE_CREDIT]}"
    return None


def rows_error(
    rows: Any,
    label: str,
    *,
    min_rows: int = 1,
    amount_key: str = "amount",
    positive: bool = True,
) -> Optional[str]:
    """子表行(allocations/settlements/channels/lines)通用形状闸:数组 + 金额可解析。"""
    if not isinstance(rows, list):
        return f"{label} 须为数组"
    if len(rows) < min_rows:
        return f"{label} 须为至少 {min_rows} 行的数组"
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            return f"{label}[{i}] 须为对象"
        amount = money(row.get(amount_key))
        if amount is None:
            return f"{label}[{i}].{amount_key} 解析不了: {row.get(amount_key)!r}"
        if positive and amount <= ZERO:
            return f"{label}[{i}].{amount_key} 须为正数: {row.get(amount_key)!r}"
    return None


def sum_rows(rows: Any, key: str = "amount") -> Decimal:
    """行金额求和(调用方须先过 rows_error,这里解析不了按 0 计)。"""
    total = ZERO
    for row in rows or []:
        if isinstance(row, dict):
            total += money(row.get(key)) or ZERO
    return total


def required_error(payload: Dict[str, Any], keys: tuple) -> Optional[str]:
    """载荷必填键闸(空串/None/空数组都算缺)。"""
    for key in keys:
        value = payload.get(key)
        if value is None or (isinstance(value, (str, list, dict)) and len(value) == 0):
            return f"缺必填字段: {key}"
    return None


def money_fields_error(payload: Dict[str, Any], keys: tuple) -> Optional[str]:
    """载荷顶层钱字段可解析闸。"""
    for key in keys:
        if key in payload and money(payload.get(key)) is None:
            return f"{key} 解析不了: {payload.get(key)!r}"
    return None


def docdate_error(payload: Dict[str, Any], key: str) -> Optional[str]:
    """单据日形状闸:必须是桥端 `date.fromisoformat` 认的公历 YYYY-MM-DD。

    形状错了桥端当场 INVALID_DOC_DATE;更坏的是形状"看着对"但不是那天(佛历 690115 被
    当公历读),落进已申报月就是污染 ภ.พ.30,比直接报错难查得多。所以严格钉 10 位 ISO
    而不是"能解析出来就行"。
    """
    raw = str(payload.get(key) or "")
    if len(raw) != 10 or iso_docdate(raw) != raw:
        return f"{key} 须为公历 ISO YYYY-MM-DD: {payload.get(key)!r}"
    return None


def clean_rows(rows: Any) -> List[Dict[str, Any]]:
    """把可能为 None 的子表规整成 list[dict](组装侧统一入口)。"""
    return [row for row in (rows or []) if isinstance(row, dict)]
