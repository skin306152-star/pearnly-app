# -*- coding: utf-8 -*-
"""收发存原始流水装配:读 purchase_lines/sales_document_lines,分类成"能归组的流水"或
"未入账清单"行(报表不碰 ocr_history / inventory_transactions,单一事实源=已过账/已开出
的正式单据本身)。

隔离铁律:进项按 purchase_docs.status='posted' + tenant_id/workspace_client_id 双显式
参数过滤;销项按 sales_documents.status='issued' + seller_workspace_client_id **严格等于**
过滤 —— 绝不 OR IS NULL(services/sales/document.py 的 _ws_and 是 fail-open 反例,本报表
故意不抄它:老单据的账套没归属就不该出现在任何一本账套的报表里)。

成本口径:进项 line_total 已经是"折扣后、不含 VAT"的净额(services/purchase/totals.py
逐行算:net = gross − line_discount,VAT 另按 net 算不并进 line_total)——净单价直接
= line_total / qty,不需要再动 vat_rate。销项行不参与定价(出库按结存均价计,见
rolling.py),这里只取它的 qty 当移动量。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from services.stockcard import grouping
from services.stockcard.rolling import Movement, q2

REASON_SERVICE = "service"
REASON_NO_QTY_PRICE = "no_qty_price"
REASON_TOTAL_ONLY = "total_only"

_GOODS_KINDS = ("purchase_invoice", "purchase_order")


@dataclass
class MovementSet:
    by_key: dict = field(default_factory=dict)  # key -> list[Movement]
    excluded: list = field(default_factory=list)  # list[dict]

    def add_movement(self, key: str, m: Movement) -> None:
        self.by_key.setdefault(key, []).append(m)

    def add_excluded(self, *, date, doc_no, desc, amount, reason, side) -> None:
        self.excluded.append(
            {
                "date": date,
                "doc_no": doc_no or "",
                "desc": desc or "",
                "amount": amount,
                "reason": reason,
                "side": side,
            }
        )


_PURCHASE_SQL = (
    "SELECT d.doc_kind, d.doc_no, d.doc_date, d.created_at AS doc_created_at, d.grand_total, "
    "l.id AS line_id, l.line_no, l.item_type, l.product_id, l.description, l.qty, l.line_total "
    "FROM purchase_docs d "
    "LEFT JOIN purchase_lines l ON l.purchase_doc_id = d.id AND l.tenant_id = d.tenant_id "
    "WHERE d.tenant_id = %s AND d.workspace_client_id = %s AND d.status = 'posted' "
    "AND d.doc_date IS NOT NULL AND d.doc_date <= %s "
    "ORDER BY d.doc_date, d.created_at, l.line_no"
)

_SALES_SQL = (
    "SELECT d.doc_type, d.doc_number, d.issue_date, d.created_at AS doc_created_at, d.grand_total, "
    "l.id AS line_id, l.line_no, l.product_id, l.description, l.qty, l.line_total "
    "FROM sales_documents d "
    "LEFT JOIN sales_document_lines l ON l.document_id = d.id AND l.tenant_id = d.tenant_id "
    "WHERE d.tenant_id = %s AND d.seller_workspace_client_id = %s AND d.status = 'issued' "
    "AND d.doc_type <> 'quotation' "
    "AND d.issue_date IS NOT NULL AND d.issue_date <= %s "
    "ORDER BY d.issue_date, d.created_at, l.line_no"
)


def _classify_purchase(row: dict, out: MovementSet) -> None:
    if row["line_id"] is None:
        out.add_excluded(
            date=row["doc_date"], doc_no=row["doc_no"], desc="", amount=row["grand_total"],
            reason=REASON_TOTAL_ONLY, side="purchase",
        )
        return
    if row["doc_kind"] not in _GOODS_KINDS or row["item_type"] != "goods":
        out.add_excluded(
            date=row["doc_date"], doc_no=row["doc_no"], desc=row["description"],
            amount=row["line_total"], reason=REASON_SERVICE, side="purchase",
        )
        return
    qty = row["qty"]
    if qty is None or Decimal(qty) <= 0 or row["line_total"] is None:
        out.add_excluded(
            date=row["doc_date"], doc_no=row["doc_no"], desc=row["description"],
            amount=row["line_total"], reason=REASON_NO_QTY_PRICE, side="purchase",
        )
        return
    key = grouping.group_key(product_id=row["product_id"], description=row["description"])
    if key is None:
        out.add_excluded(
            date=row["doc_date"], doc_no=row["doc_no"], desc=row["description"],
            amount=row["line_total"], reason=REASON_NO_QTY_PRICE, side="purchase",
        )
        return
    qty_d = Decimal(qty)
    price = q2(Decimal(row["line_total"]) / qty_d)
    out.add_movement(
        key,
        Movement(
            date=row["doc_date"], doc_no=row["doc_no"] or "", desc=row["description"] or "",
            direction="in", qty=qty_d, price=price,
            sort_key=(row["doc_date"], row["doc_created_at"], row["line_no"] or 0),
        ),
    )


def _classify_sale(row: dict, out: MovementSet) -> None:
    if row["line_id"] is None:
        out.add_excluded(
            date=row["issue_date"], doc_no=row["doc_number"], desc="", amount=row["grand_total"],
            reason=REASON_TOTAL_ONLY, side="sale",
        )
        return
    qty = row["qty"]
    if qty is None or Decimal(qty) <= 0:
        out.add_excluded(
            date=row["issue_date"], doc_no=row["doc_number"], desc=row["description"],
            amount=row["line_total"], reason=REASON_NO_QTY_PRICE, side="sale",
        )
        return
    key = grouping.group_key(product_id=row["product_id"], description=row["description"])
    if key is None:
        out.add_excluded(
            date=row["issue_date"], doc_no=row["doc_number"], desc=row["description"],
            amount=row["line_total"], reason=REASON_NO_QTY_PRICE, side="sale",
        )
        return
    direction = "in" if row["doc_type"] == "credit_note" else "out"
    out.add_movement(
        key,
        Movement(
            date=row["issue_date"], doc_no=row["doc_number"] or "", desc=row["description"] or "",
            direction=direction, qty=Decimal(qty), price=None,
            sort_key=(row["issue_date"], row["doc_created_at"], row["line_no"] or 0),
        ),
    )


def load(cur, *, tenant_id: str, workspace_client_id: int, date_to) -> MovementSet:
    """读到 date_to 为止的全部可入账流水(date_from 的切分留给 report.py:同一批流水在
    "期初结转"与"期间明细"两种视图间复用,不必按不同 date_from 重复查库)。"""
    out = MovementSet()
    cur.execute(_PURCHASE_SQL, (tenant_id, workspace_client_id, date_to))
    for row in cur.fetchall():
        _classify_purchase(row, out)
    cur.execute(_SALES_SQL, (tenant_id, workspace_client_id, date_to))
    for row in cur.fetchall():
        _classify_sale(row, out)
    for movs in out.by_key.values():
        movs.sort(key=lambda m: m.sort_key)
    return out


def product_names(cur, *, tenant_id: str, workspace_client_id: int, product_ids: list) -> dict:
    """批量取商品展示名(name_th 优先 · th→en→zh 兜底链)+ 计量单位,供 summary/card 组名字段。"""
    if not product_ids:
        return {}
    # id 是 uuid 列:不转型的裸 ANY 会被 psycopg2 把入参适配成 text[] 去比 uuid,炸
    # "operator does not exist: uuid = text"(仓库血泪·同 test_workorder_uuid_any_cast.py)。
    cur.execute(
        "SELECT id, name_th, name_en, name_zh, unit FROM products "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = ANY(%s::uuid[])",
        (tenant_id, workspace_client_id, product_ids),
    )
    out = {}
    for r in cur.fetchall():
        name = r["name_th"] or r["name_en"] or r["name_zh"] or ""
        out[str(r["id"])] = {"name": name, "unit": r["unit"]}
    return out


def purchase_units(cur, *, tenant_id: str, workspace_client_id: int, date_to) -> dict:
    """name_key 轨没有商品主档,单位只能从最近一笔进项行的原始 unit 文本带出(展示性质,
    不参与算价)。取每个清洗名最新一笔 posted 进项行的 unit。"""
    cur.execute(
        "SELECT l.description, l.unit, d.doc_date "
        "FROM purchase_lines l "
        "JOIN purchase_docs d ON d.id = l.purchase_doc_id AND d.tenant_id = l.tenant_id "
        "WHERE l.tenant_id = %s AND d.workspace_client_id = %s AND d.status = 'posted' "
        "AND l.product_id IS NULL AND l.unit IS NOT NULL AND d.doc_date <= %s "
        "ORDER BY d.doc_date, d.created_at",
        (tenant_id, workspace_client_id, date_to),
    )
    out: dict = {}
    for r in cur.fetchall():
        key = grouping.name_key(r["description"])
        if key:
            out[key] = r["unit"]  # 后面的覆盖前面的:保留"最近一笔"
    return out


def filter_excluded_by_period(rows: list, date_from, date_to) -> list:
    """未入账清单按期间过滤(date 为 None 的行两边都不数)。excluded_only 与 report.summary
    的 excluded_count 共用同一口径 —— 两处各算各的,前端 tab 徽章数会跟清单行数对不上。"""
    return [r for r in rows if r["date"] is not None and date_from <= r["date"] <= date_to]


def excluded_only(cur, *, tenant_id: str, workspace_client_id: int, date_from, date_to) -> list:
    """/excluded 端点专用:未入账清单不分账期滚存,直接按 [date_from, date_to] 过滤展示。"""
    full = load(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to)
    return filter_excluded_by_period(full.excluded, date_from, date_to)


def key_display_name(key: str, product_lookup: dict, name_unit_lookup: dict) -> tuple:
    """key → (展示名, 计量单位)。"""
    pid = grouping.key_product_id(key)
    if pid:
        info = product_lookup.get(pid) or {}
        return info.get("name") or "", info.get("unit")
    name = grouping.key_name(key) or ""
    return name, name_unit_lookup.get(name)
