# -*- coding: utf-8 -*-
"""管家的现场算账工具(零 I/O · 纯 Decimal)。

vat_calc 只做一件事:会计嘴里报出来的那个数,在 含税 / 税前 / 税额 三者之间互算,并在她
自己报了预扣税率时一并算出预扣与实付。

三条硬线,写在这里免得后人放宽:
  ① 数只能来自会计的原话(slots 的 user_text 接地闸先过一遍),这里再解析成 Decimal——
     全程不碰 float,也不去库里找任何数(查账套里已经算好的税额是 tax_numbers 的活);
  ② 算法复用既有的两处权威实现(purchase.totals.vat_from_inclusive / excel.erp_money.vat_of),
     不在管家侧另写一套 7%——两套舍入会让对话里的数和票面/推 ERP 的数差分币;
  ③ 预扣税率必须由会计说出口。工具绝不替她挑该扣几个点:那是税务判断,不是算账。
     基准(含税还是未含税)同理,判不出来就问,绝不默认一个方向 —— 猜错方向答案照样是
     两位小数的、看不出错的假数。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from services.steward.contracts import ToolResult
from services.excel.erp_money import VAT_RATE, quantize_money, to_money, vat_of
from services.purchase.totals import vat_from_inclusive
from services.steward.registry import ToolContext

BASIS_INCLUSIVE = "inclusive"
BASIS_EXCLUSIVE = "exclusive"

ERR_AMOUNT_UNREADABLE = "steward.calc_amount_unreadable"
ERR_BASIS_UNCLEAR = "steward.calc_basis_unclear"
ERR_RATE_UNREADABLE = "steward.calc_rate_unreadable"

# 能算的量级上限。再大就超出真实票面的范围,而 Decimal 默认 28 位有效数字之外会开始
# 悄悄丢精度 —— 与其给一个看起来对的数,不如说没看懂。
_MAX_AMOUNT = Decimal("1e15")
_PERCENT = Decimal("100")

# 基准词表。判不出来 → 追问,所以词表只收明确的说法,不收「大概是」。
# 先判未含税:泰文「ยังไม่รวม」含「รวม」、中文「不含税」含「含税」,顺序反了会一律判成含税。
_EXCLUSIVE_WORDS = (
    "exclusive",
    "exclude",
    "excl",
    "net",
    "before",
    BASIS_EXCLUSIVE,
    "未含",
    "不含",
    "税前",
    "ยังไม่",
    "ไม่รวม",
    "ก่อนภาษี",
)
_INCLUSIVE_WORDS = (
    "inclusive",
    "include",
    "incl",
    "gross",
    BASIS_INCLUSIVE,
    "含税",
    "รวม",
    "หลังภาษี",
)


def vat_calc(ctx: ToolContext, args: dict) -> ToolResult:
    """含税 ↔ 税前 ↔ 税额 互算(+ 会计报了税率时的预扣与实付)。

    ctx 用不上是本工具的属性而非疏漏:它不查任何账套的数据,因此也没有可越的界。
    """
    amount = _amount(args.get("amount"))
    if amount is None:
        return ToolResult(
            ok=False, error_code=ERR_AMOUNT_UNREADABLE, data={"raw": _short(args.get("amount"))}
        )
    basis = _basis(args.get("basis"))
    if basis is None:
        return ToolResult(ok=False, error_code=ERR_BASIS_UNCLEAR, data={"amount": _money(amount)})
    rate_raw = args.get("wht_rate")
    wht_rate = _rate(rate_raw)
    if rate_raw not in (None, "") and wht_rate is None:
        return ToolResult(ok=False, error_code=ERR_RATE_UNREADABLE, data={"raw": _short(rate_raw)})
    return ToolResult(ok=True, data=breakdown(amount, basis, wht_rate))


def breakdown(amount: Decimal, basis: str, wht_rate: Optional[Decimal] = None) -> dict:
    """税基/税额/含税合计(+ 预扣与实付)。纯函数:同样的入参永远同样的出参。

    含税拆解走「先算税额、税基取差」:税基 = 合计 − 税额 保证三个数首尾恒等,反过来
    (税基×7% 再相加)在 .005 边界上会拼不回票面合计,而会计正是拿这三个数去对票面的。
    预扣税基是税前额(泰国 หัก ณ ที่จ่าย 按不含 VAT 的金额扣),不是含税合计。
    """
    if basis == BASIS_INCLUSIVE:
        total = quantize_money(amount)
        vat = quantize_money(vat_from_inclusive(total))
        base = quantize_money(total - vat)
    else:
        base = quantize_money(amount)
        vat = vat_of(base)
        total = quantize_money(base + vat)
    data = {
        "basis": basis,
        "vat_rate": _rate_text(VAT_RATE * _PERCENT),
        "base": _money(base),
        "vat": _money(vat),
        "total": _money(total),
        "wht_rate": None,
        "wht": None,
        "net_payable": None,
    }
    if wht_rate is not None:
        wht = quantize_money(base * wht_rate / _PERCENT)
        data.update(
            {
                "wht_rate": _rate_text(wht_rate),
                "wht": _money(wht),
                "net_payable": _money(quantize_money(total - wht)),
            }
        )
    return data


def _amount(raw) -> Optional[Decimal]:
    """会计报的金额 → Decimal。负数照收(退货/贷记单是真场景),量级越界当没看懂。"""
    value = to_money(_clean(raw))
    if value is None or not value.is_finite() or abs(value) > _MAX_AMOUNT:
        return None
    return value


def _rate(raw) -> Optional[Decimal]:
    """预扣税率 → Decimal 百分点。0–100 之外一律当没听清(绝不替会计挑一个率)。"""
    if raw in (None, ""):
        return None
    value = to_money(_clean(raw))
    if value is None or not value.is_finite() or value < 0 or value > _PERCENT:
        return None
    return value


def _clean(raw) -> str:
    """去掉排版噪音(百分号 / 千分位 / 泰铢符 by to_money)后再解析。"""
    return str(raw if raw is not None else "").strip().replace("%", "").replace("บาท", "")


def _basis(raw) -> Optional[str]:
    text = str(raw or "").strip().lower()
    if not text:
        return None
    if any(w in text for w in _EXCLUSIVE_WORDS):
        return BASIS_EXCLUSIVE
    if any(w in text for w in _INCLUSIVE_WORDS):
        return BASIS_INCLUSIVE
    return None


def _money(value: Decimal) -> str:
    return str(quantize_money(value))


def _rate_text(rate: Decimal) -> str:
    """税率给人看:7.00 印成 7、1.50 印成 1.5(normalize 会把 100 印成 1E+2,故走定点格式)。"""
    try:
        return format(rate.normalize(), "f")
    except (InvalidOperation, ValueError):
        return str(rate)


def _short(raw) -> str:
    """回显会计原话里那截读不出来的东西(截断:错误数据不该把答复撑爆)。"""
    return str(raw if raw is not None else "")[:40]
