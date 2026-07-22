# -*- coding: utf-8 -*-
"""销售明细导出「新建 vs 复用」动作回填(只读侧)。

小助手推送成功后,DbfWriteResult 把「客户是否新建(created_party)」与「每行商品是否新建
(line_modes[].created)」如实回传,落进 erp_push_logs.response_body(meta.created_customer +
line_modes)。导出销售明细(excel_template_th)时按单据回查这些动作,填 customer_erp_action /
items[].erp_action,让用户在表格里一眼看清哪些客户/商品是本次新建、哪些复用既有档。

匹配键两路(都 user_id scope · erp_push_logs 的 RLS 维度):
- history_id:export-by-history-ids 从单据记录组 records,天然有 hid;
- invoice_no:向导内导出的 records 无 hid,按票面发票号回查(多票 PDF 每票各自匹配)。
无成功推送记录的单据不填(模板留 '-'),不假装。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.erp.external_ref import _coerce_body

logger = logging.getLogger(__name__)


def _parse_erp_actions(response_body: Any) -> Dict[str, Any]:
    """从一条成功推送的 response_body 解出新建-复用动作。

    返回 {"customer": bool|None, "items": [bool|None, ...]}:
    customer = meta.created_customer(建客户=True · 复用=False · 缺=None);
    items = line_modes 按 seq 升序的 created(True 新建 / False 复用 / None 直接科目行)。
    """
    body = _coerce_body(response_body)
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    customer = meta.get("created_customer")
    items: List[Any] = []
    line_modes = body.get("line_modes")
    if isinstance(line_modes, list):
        clean = [m for m in line_modes if isinstance(m, dict)]
        for m in sorted(clean, key=lambda x: int(x.get("seq") or 0)):
            items.append(m.get("created"))
    return {
        "customer": customer if isinstance(customer, bool) else None,
        "items": items,
    }


def erp_actions_by_history_ids(
    user_id: str, history_ids: List[str], tenant_id: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """回查这些单据「最近一次成功推送」的新建-复用动作。返回 {history_id: {customer, items}}。

    只读 · user_id scope。无成功推送的单据不在返回里(导出侧留 '-')。查询失败整体降级为空。
    """
    from core import db

    hids = [str(h) for h in (history_ids or []) if str(h or "").strip()]
    if not hids:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            cur.execute(
                """
                WITH ranked AS (
                    SELECT l.history_id, l.response_body,
                        ROW_NUMBER() OVER (
                            PARTITION BY l.history_id
                            ORDER BY l.created_at DESC, l.id DESC
                        ) AS _rn
                    FROM erp_push_logs l
                    WHERE l.user_id = %s
                      AND l.history_id = ANY(%s::uuid[])
                      AND l.status = 'success'
                )
                SELECT history_id, response_body FROM ranked WHERE _rn = 1
                """,
                (user_id, hids),
            )
            rows = cur.fetchall() or []
    except Exception as e:
        logger.warning(f"erp_actions_by_history_ids failed: {e}")
        return {}
    for r in rows:
        row = dict(r)
        out[str(row["history_id"])] = _parse_erp_actions(row.get("response_body"))
    return out


def erp_actions_by_invoice_nos(
    user_id: str, invoice_nos: List[str], tenant_id: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """按票面发票号回查最近一次成功推送的新建-复用动作(向导内导出无 history_id 时用)。

    返回 {invoice_no: {customer, items}}。只读 · user_id scope · 每票取最新成功一条。
    """
    from core import db

    nos = [str(n).strip() for n in (invoice_nos or []) if str(n or "").strip()]
    if not nos:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (l.invoice_no) l.invoice_no, l.response_body
                FROM erp_push_logs l
                WHERE l.user_id = %s
                  AND l.invoice_no = ANY(%s::text[])
                  AND l.status = 'success'
                ORDER BY l.invoice_no, l.created_at DESC, l.id DESC
                """,
                (user_id, nos),
            )
            rows = cur.fetchall() or []
    except Exception as e:
        logger.warning(f"erp_actions_by_invoice_nos failed: {e}")
        return {}
    for r in rows:
        row = dict(r)
        key = str(row["invoice_no"] or "").strip()
        if key:
            out[key] = _parse_erp_actions(row.get("response_body"))
    return out


def apply_erp_actions(merged_fields: Dict[str, Any], action: Optional[Dict[str, Any]]) -> None:
    """把回查到的动作填进 merged_fields(原地改)。action 为 None/缺字段 → 不填(模板留 '-')。

    customer → customer_erp_action('new'/'reused');items 按顺序对齐 line_modes 的 created →
    items[i].erp_action。行数不齐(OCR 明细数 ≠ 推送行数)时只填对得上的,不瞎补。
    """
    if not action or not isinstance(merged_fields, dict):
        return
    cust = action.get("customer")
    if isinstance(cust, bool):
        merged_fields["customer_erp_action"] = "new" if cust else "reused"
    items = merged_fields.get("items")
    line_created = action.get("items") or []
    if isinstance(items, list):
        for i, it in enumerate(items):
            if isinstance(it, dict) and i < len(line_created):
                c = line_created[i]
                if isinstance(c, bool):
                    it["erp_action"] = "new" if c else "reused"
