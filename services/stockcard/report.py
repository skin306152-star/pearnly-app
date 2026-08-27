# -*- coding: utf-8 -*-
"""收发存报表装配:groups(全商品逐笔长表 · 网页唯一主视图)/ summary(全商品期间汇总)/
card(单商品逐笔明细)/ excluded(未入账清单)。

期间口径(拍板):期初一次性填表 + date_from 之前的全部流水,先滚出一行「期初结转」合成
首行;期间内([date_from, date_to])逐笔展示。有期初记录时只重放 as_of_date 之后的流水
(期初已经把它之前的东西吸收掉了,重放会重复计 —— 这条边界对"as_of_date 之前/之后"
统一生效,不论落在 date_from 哪一侧,防止期初与期间流水在交界处重复计);没有期初记录
就从 0 滚起,可能诚实进入"成本未知"态直到第一笔真实购入。

summary()/card() 保留给 Steward 内部汇报(services/steward/tools_stockcard.py);网页主视图
只走 groups() —— 一次 load_context、一次批量取商品名/名字轨单位,再逐 key 纯计算,
绝不按每个商品重复查库(N+1)。

数字字段一律输出字符串(Decimal 经 JSON 会被前端当 float 解析,精度会漂)。desc/kind
不夹带中文/泰文展示文案 —— i18n 由前端按 kind 挑语言,后端只吐语义。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from services.stockcard import grouping
from services.stockcard import movements as mv_svc
from services.stockcard import opening as opening_svc
from services.stockcard import rolling


def _str(v) -> Optional[str]:
    return None if v is None else str(v)


def iso_or_raw(v):
    """date/datetime → ISO 字符串;非日期值原样透传。报表内部与 routes/stock_card_routes.py
    的 _public_opening 共用同一个判等值(此前两处各自写一份 hasattr(isoformat) 三元)。"""
    return v.isoformat() if hasattr(v, "isoformat") else v


def _covered_by_opening(d, start_date) -> bool:
    """流水日期是否已被期初(as_of_date)吸收 —— 吸收掉的绝不重放,防与期初重复计。"""
    return start_date is not None and d <= start_date


def _split(movs: list, opening_row: Optional[dict], date_from, date_to) -> tuple[list, list]:
    """一个 key 的全部流水(已按时间排好序)→ (滚进期初的, 期间内逐笔展示的)。"""
    start_date = opening_row["as_of_date"] if opening_row else None
    remaining = [m for m in movs if not _covered_by_opening(m.date, start_date)]
    before = [m for m in remaining if m.date < date_from]
    period = [m for m in remaining if date_from <= m.date <= date_to]
    return before, period


def _base_balance(opening_row: Optional[dict]) -> rolling.Balance:
    if not opening_row:
        return rolling.ZERO_BALANCE
    return rolling.opening_balance(opening_row["qty"], opening_row["unit_cost"])


def _roll_key(movs: list, opening_row: Optional[dict], date_from, date_to):
    """→ (期初结转态, 期末结存态, 期间逐笔行)。"""
    before, period = _split(movs, opening_row, date_from, date_to)
    carried, _ = rolling.roll(_base_balance(opening_row), before)
    final, rows = rolling.roll(carried, period)
    return carried, final, rows


def _fmt_row(r: dict) -> dict:
    return {
        "date": iso_or_raw(r["date"]),
        "doc_no": r["doc_no"],
        "kind": r["kind"],
        "desc": r["desc"],
        "qty": str(r["qty"]),
        "unit_price": _str(r["unit_price"]),
        "amount": _str(r["amount"]),
        "bal_qty": str(r["bal_qty"]),
        "bal_unit_cost": _str(r["bal_unit_cost"]),
        "bal_value": _str(r["bal_value"]),
    }


def _opening_row(carried: rolling.Balance, date_from) -> dict:
    """合成一行「期初结转」(该 key 在 date_from 前全部流水 + 用户期初滚出的起算态)。

    报表的主视图/单品卡都把它当第一行展示 —— 期初作为每个商品的第一行流水参与计算,
    不额外给表格加列。date 用 date_from,让首行落在所选期间起点。"""
    return {
        "date": iso_or_raw(date_from),
        "doc_no": "",
        "kind": "open",
        "desc": "",
        "qty": str(carried.qty),
        "unit_price": None,
        "amount": None,
        "bal_qty": str(carried.qty),
        "bal_unit_cost": _str(carried.unit),
        "bal_value": _str(carried.value),
    }


def _sum_qty(rows: list, kind: str) -> Decimal:
    return sum((r["qty"] for r in rows if r["kind"] == kind), Decimal("0"))


def _sum_amount_known(rows: list, kind: str) -> Optional[Decimal]:
    """某方向金额合计的诚实口径:任一行的金额未知(None)则整组置 None,不拿已知部分的
    和顶替 —— 混几行已知几行未知时,只加已知的会把「不知道」印成一个看着精确的数,踩
    「成本未知不以 0 冒充」红线。全都没该方向行则回落 0(合计就是 0,不是未知)。"""
    total = Decimal("0")
    has = False
    for r in rows:
        if r["kind"] != kind:
            continue
        if r["amount"] is None:
            return None
        total += r["amount"]
        has = True
    return total if has else Decimal("0")


def load_context(cur, *, tenant_id: str, workspace_client_id: int, date_to) -> tuple:
    """movements + openings 一次装载,供 summary()/card() 共用同一次全表扫描结果。

    同一次提问常先答 summary 再钻某个商品的 card(services/steward/tools_stockcard.py 的
    关键词命中路径)——两次各自 load() 是对同一账套同一 date_to 的重复全表扫描,调用方
    装一次传下去即可省掉第二遍。"""
    data = mv_svc.load(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
    )
    openings = opening_svc.load_by_key(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    return data, openings


def _display_context(cur, *, tenant_id: str, workspace_client_id: int, date_to, keys: list):
    product_ids = [grouping.key_product_id(k) for k in keys if grouping.is_product_key(k)]
    products = mv_svc.product_names(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, product_ids=product_ids
    )
    name_units = {}
    if any(not grouping.is_product_key(k) for k in keys):
        name_units = mv_svc.purchase_units(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
        )
    return products, name_units


def _product_meta(key: str, products: dict, name_units: dict) -> dict:
    name, unit = mv_svc.key_display_name(key, products, name_units)
    return {
        "key": key,
        "product_id": grouping.key_product_id(key),
        "name": name,
        "unit": unit,
    }


def summary(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from,
    date_to,
    context: Optional[tuple] = None,
) -> dict:
    data, openings = context or load_context(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
    )

    keys = sorted(set(data.by_key) | set(openings))
    products, name_units = _display_context(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_to=date_to,
        keys=keys,
    )

    out = []
    for key in keys:
        carried, final, period_rows = _roll_key(
            data.by_key.get(key, []), openings.get(key), date_from, date_to
        )
        out.append(
            {
                **_product_meta(key, products, name_units),
                "opening_qty": str(carried.qty),
                "in_qty": str(_sum_qty(period_rows, "in")),
                "out_qty": str(_sum_qty(period_rows, "out")),
                "bal_qty": str(final.qty),
                "bal_unit_cost": _str(final.unit),
                "bal_value": _str(final.value),
                "negative": final.qty < 0,
                "matched": grouping.is_product_key(key),
            }
        )
    excluded_count = len(mv_svc.filter_excluded_by_period(data.excluded, date_from, date_to))
    return {"products": out, "excluded_count": excluded_count}


def card(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    key: str,
    date_from,
    date_to,
    context: Optional[tuple] = None,
) -> Optional[dict]:
    data, openings = context or load_context(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
    )
    opening_row = openings.get(key)
    movs = data.by_key.get(key, [])
    if not movs and not opening_row:
        return None  # 路由层翻 404:这个 key 在本账套从未出现过

    products, name_units = _display_context(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_to=date_to,
        keys=[key],
    )

    carried, final, period_rows = _roll_key(movs, opening_row, date_from, date_to)
    rows = [_opening_row(carried, date_from)]
    rows.extend(_fmt_row(r) for r in period_rows)

    return {
        "product": _product_meta(key, products, name_units),
        "rows": rows,
        "totals": {
            "in_qty": str(_sum_qty(period_rows, "in")),
            "in_amount": _str(_sum_amount_known(period_rows, "in")),
            "out_qty": str(_sum_qty(period_rows, "out")),
            "out_amount": _str(_sum_amount_known(period_rows, "out")),
            "bal_qty": str(final.qty),
            "bal_unit_cost": _str(final.unit),
            "bal_value": _str(final.value),
        },
    }


def groups(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from,
    date_to,
    context: Optional[tuple] = None,
) -> list:
    """网页主视图:一次装好 movements/openings,一次批量取商品名/名字轨单位,再逐 key
    纯计算,返回按商品连续排列的完整 13 列表格(每组的期初行 + 期间逐笔 + 该组合计)。

    product 只带主表标题与期初录入所需的 key/编码/名称/单位,不掺状态/归并等附加字段
    —— 参考图没有那些交互,报表不做。数字字段一律字符串;金额合计走诚实口径(见
    _sum_amount_known),未知成本不冒充 0。"""
    data, openings = context or load_context(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
    )

    keys = sorted(set(data.by_key) | set(openings))
    products, name_units = _display_context(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_to=date_to,
        keys=keys,
    )

    out = []
    for key in keys:
        carried, final, period_rows = _roll_key(
            data.by_key.get(key, []), openings.get(key), date_from, date_to
        )
        rows = [_opening_row(carried, date_from)]
        rows.extend(_fmt_row(r) for r in period_rows)
        out.append(
            {
                "product": _product_meta(key, products, name_units),
                "rows": rows,
                "totals": {
                    "in_qty": str(_sum_qty(period_rows, "in")),
                    "in_amount": _str(_sum_amount_known(period_rows, "in")),
                    "out_qty": str(_sum_qty(period_rows, "out")),
                    "out_amount": _str(_sum_amount_known(period_rows, "out")),
                    "bal_qty": str(final.qty),
                    "bal_unit_cost": _str(final.unit),
                    "bal_value": _str(final.value),
                },
            }
        )
    return out


def excluded(cur, *, tenant_id: str, workspace_client_id: int, date_from, date_to) -> list:
    rows = mv_svc.excluded_only(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_from=date_from,
        date_to=date_to,
    )
    return [
        {
            "date": iso_or_raw(r["date"]),
            "doc_no": r["doc_no"],
            "desc": r["desc"],
            "amount": _str(r["amount"]),
            "reason": r["reason"],
            "side": r["side"],
        }
        for r in rows
    ]
