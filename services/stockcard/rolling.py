# -*- coding: utf-8 -*-
"""移动加权平均滚存(金标算法 · 纯函数 · 无 SQL · 与仓库其余金额模块的 ROUND_HALF_EVEN
分位刻意不同,本报表按拍板口径用 ROUND_HALF_UP 保留 2 位)。

三种流水:
  入库(购入)   按行净单价(不含 VAT)重算加权平均 —— receive_priced
  退货入库(credit_note 反向)按当前结存单价入,同入库公式只是价格来源换成结存 —— receive_at_cost
  出库(销售)   按当前结存单价计费,不动均价 —— issue

结存单价从未确立(没入过库就先出/先退)时诚实返 None,不假造成本:qty 照记(可为负,
负库存是拍板允许的真实业务状态),金额/单价留白由前端显示"—"。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

_CENT = Decimal("0.01")


def _d(v: Any) -> Decimal:
    return Decimal(str(v if v is not None else 0))


def q2(v: Decimal) -> Decimal:
    """分位量化 · 四舍五入向上(商户报表拍板口径)。"""
    return v.quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Balance:
    """滚存态。qty 恒记(含负库存);value/unit 在成本从未确立前诚实为 None。"""

    qty: Decimal
    value: Optional[Decimal]
    unit: Optional[Decimal]


@dataclass(frozen=True)
class Movement:
    """一笔待滚存流水(由 report.py 从 purchase_lines/sales_document_lines 组装)。"""

    date: Any
    doc_no: str
    desc: str
    direction: str  # 'in' | 'out'(credit_note 对外仍是 'in',内部靠 price 是否给出分派公式)
    qty: Decimal
    price: Optional[Decimal]  # 入库票面净单价;None = 按当前结存单价计(退货入/所有出库)
    sort_key: tuple  # (doc_date, doc_created_at, line_no) —— 查询侧算好的稳定排序键


ZERO_BALANCE = Balance(qty=Decimal("0"), value=None, unit=None)


def opening_balance(qty, unit_cost) -> Balance:
    """期初结转态。期初量为 0 视同未确立成本(与从未发生过流水等价)。"""
    q = _d(qty)
    if q == 0:
        return ZERO_BALANCE
    value = q2(q * _d(unit_cost))
    return Balance(qty=q, value=value, unit=q2(value / q))


def _row(bal: Balance, *, price, amount) -> dict:
    return {
        "unit_price": price,
        "amount": amount,
        "bal_qty": bal.qty,
        "bal_unit_cost": bal.unit,
        "bal_value": bal.value,
    }


def _receive(bal: Balance, qty: Decimal, price: Decimal) -> tuple[Balance, dict]:
    """入库通用分支(购入 / 退货入库共用):按 price 把 qty 计入,重算加权平均单价。"""
    amount = q2(qty * price)
    new_qty = bal.qty + qty
    base_value = bal.value if bal.value is not None else Decimal("0.00")
    new_value = q2(base_value + amount)
    new_unit = q2(new_value / new_qty) if new_qty != 0 else bal.unit
    new_bal = Balance(new_qty, new_value, new_unit)
    return new_bal, _row(new_bal, price=price, amount=amount)


def _unknown_cost_move(bal: Balance, qty: Decimal, sign: int) -> tuple[Balance, dict]:
    """成本从未确立时的诚实分支:qty 照记(sign=+1 退货入/−1 出库),不猜金额。"""
    new_bal = Balance(bal.qty + sign * qty, bal.value, bal.unit)
    return new_bal, _row(new_bal, price=None, amount=None)


def receive_priced(bal: Balance, qty, price) -> tuple[Balance, dict]:
    """购入:price 是票面净单价(不含 VAT · 由调用方从 line_total/qty 算好传入)。"""
    return _receive(bal, _d(qty), _d(price))


def receive_at_cost(bal: Balance, qty) -> tuple[Balance, dict]:
    """退货入库(credit_note 反向)· 按当前结存单价入账,理论上均价不因此漂移。"""
    q = _d(qty)
    if bal.unit is None:
        return _unknown_cost_move(bal, q, sign=1)
    return _receive(bal, q, bal.unit)


def issue(bal: Balance, qty) -> tuple[Balance, dict]:
    """出库(销售)· 按当前结存单价计价,不重算均价(均价只在入库时变动)。"""
    q = _d(qty)
    if bal.unit is None:
        return _unknown_cost_move(bal, q, sign=-1)
    price = bal.unit
    amount = q2(q * price)
    new_bal = Balance(bal.qty - q, q2(bal.value - amount), bal.unit)
    return new_bal, _row(new_bal, price=price, amount=amount)


def apply(bal: Balance, m: Movement) -> tuple[Balance, dict]:
    """按流水方向分派到对应公式。direction='in' 且 price 给出 = 购入;price=None = 退货入。"""
    if m.direction == "in":
        if m.price is not None:
            return receive_priced(bal, m.qty, m.price)
        return receive_at_cost(bal, m.qty)
    return issue(bal, m.qty)


def roll(opening: Balance, movements: list[Movement]) -> tuple[Balance, list[dict]]:
    """按调用方给定顺序逐笔滚存,返回 (期末结存态, 逐笔明细行)。movements 须已排好序
    (排序钥匙依赖数据库读出的 doc 时间戳,属查询职责,不下沉进这个纯函数)。"""
    bal = opening
    rows = []
    for m in movements:
        bal, r = apply(bal, m)
        rows.append(
            {
                "date": m.date,
                "doc_no": m.doc_no,
                "kind": m.direction,
                "desc": m.desc,
                "qty": m.qty,
                **r,
            }
        )
    return bal, rows
