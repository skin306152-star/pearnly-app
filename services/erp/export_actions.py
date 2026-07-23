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
    """从一条成功推送的 response_body 解出「ERP 里到底发生了什么」。

    返回:
      customer   bool|None   meta.created_customer(建客户=True · 复用=False · 缺=None)
      items      [bool|None] line_modes 按 seq 升序的 created(新建/复用/直接科目行)
      item_codes [str]       同序的 stkcod —— 会计要清理误建的商品档,得知道码
      docnum     str         ERP 真实凭证号。票面号超 12 字符时会退回自编号,此时它
                             ≠ 票面号,不给会计就没法在 ERP 里找到这张单去删
      party_code str         ERP 客户/供应商码(小助手 party_code · 见 meta 白名单)
    """
    body = _coerce_body(response_body)
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    customer = meta.get("created_customer")
    items: List[Any] = []
    item_codes: List[str] = []
    line_modes = body.get("line_modes")
    if isinstance(line_modes, list):
        clean = [m for m in line_modes if isinstance(m, dict)]
        for m in sorted(clean, key=lambda x: int(x.get("seq") or 0)):
            items.append(m.get("created"))
            item_codes.append(str(m.get("stkcod") or "").strip())
    return {
        "customer": customer if isinstance(customer, bool) else None,
        "items": items,
        "item_codes": item_codes,
        "docnum": str(body.get("express_docnum") or meta.get("docnum") or "").strip(),
        "party_code": str(meta.get("party_code") or "").strip(),
        # 小助手如实回报这张单按哪个方向写进的 ERP —— 分表靠它,不靠再猜一次
        "direction": str(meta.get("doc_type") or "").strip().lower(),
        # 对手方是不是本次新建的。码是码、新建与否是新建与否,不编码进同一个字符串的空/非空
        "created_party": bool(meta.get("created_customer") or meta.get("created_supplier")),
    }


def collect_created_masters(
    records: List[Dict[str, Any]], actions: Dict[str, Dict[str, Any]], hids: List[str]
) -> List[Dict[str, Any]]:
    """汇总本批新建的主档 → [{kind, code, name, docnum}]。

    只列【真正新建】的:复用既有档不该出现在清理清单里,否则会计照单去删就把人家
    原有的档删了。商品行按 created 标记逐行判,客户/供应商按 created_customer/supplier。
    """
    out: List[Dict[str, Any]] = []
    seen = set()
    for rec, hid in zip(records or [], hids or []):
        act = actions.get(str(hid))
        if not act:
            continue
        mf = rec.get("merged_fields") if isinstance(rec, dict) else None
        mf = mf if isinstance(mf, dict) else {}
        docnum = str(act.get("docnum") or "")
        items = mf.get("items") if isinstance(mf.get("items"), list) else []
        codes = act.get("item_codes") or []
        for i, created in enumerate(act.get("items") or []):
            code = codes[i] if i < len(codes) else ""
            if not created or not code or ("item", code) in seen:
                continue
            seen.add(("item", code))
            name = ""
            if i < len(items) and isinstance(items[i], dict):
                name = str(items[i].get("description") or items[i].get("name") or "")
            out.append({"kind": "item", "code": code, "name": name, "docnum": docnum})
        party = act.get("party_code") if act.get("created_party") else ""
        if party and ("party", party) not in seen:
            seen.add(("party", party))
            kind = "supplier" if act.get("direction") == "purchase" else "customer"
            name = str(mf.get("seller_name" if kind == "supplier" else "buyer_name") or "")
            out.append({"kind": kind, "code": party, "name": name, "docnum": docnum})
    return out


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


def push_state_by_history_ids(
    user_id: str, history_ids: List[str], tenant_id: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """每单据「最近一次推送」的状态 + 目标 ERP。返回 {history_id: {status, reason, adapter}}。

    与 erp_actions_by_history_ids 的区别:那个只看成功的(为了取新建/复用动作),这个
    不过滤状态 —— 导出的状态列要如实显示失败/排队/转人工。全成功一个样,会计就可能
    跑去 ERP 删一张压根没建成的单。

    adapter 决定导出哪套表(格式跟着 ERP 走):不同 ERP 的列位合同不通用。
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
                    SELECT l.history_id, l.status, l.error_msg, e.adapter,
                        ROW_NUMBER() OVER (
                            PARTITION BY l.history_id
                            ORDER BY l.created_at DESC, l.id DESC
                        ) AS _rn
                    FROM erp_push_logs l
                    LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                    WHERE l.user_id = %s AND l.history_id = ANY(%s::uuid[])
                )
                SELECT history_id, status, error_msg, adapter FROM ranked WHERE _rn = 1
                """,
                (user_id, hids),
            )
            rows = cur.fetchall() or []
    except Exception as e:
        logger.warning(f"push_state_by_history_ids failed: {e}")
        return {}
    for r in rows:
        row = dict(r)
        out[str(row["history_id"])] = {
            "status": row.get("status") or "",
            "reason": row.get("error_msg") or "",
            "adapter": (row.get("adapter") or "").lower(),
        }
    return out


def apply_push_state(merged_fields: Dict[str, Any], state: Optional[Dict[str, Any]]) -> None:
    """推送状态落进 merged_fields。查不到就不填 —— 模板显示 '-',不假装成功。"""
    if not state or not isinstance(merged_fields, dict):
        return
    if state.get("status"):
        merged_fields["push_status"] = state["status"]
    if state.get("reason"):
        merged_fields["push_reason"] = state["reason"]


def apply_erp_actions(merged_fields: Dict[str, Any], action: Optional[Dict[str, Any]]) -> None:
    """把回查到的动作填进 merged_fields(原地改)。action 为 None/缺字段 → 不填(模板留 '-')。

    customer → customer_erp_action('new'/'reused');items 按顺序对齐 line_modes 的 created →
    items[i].erp_action。行数不齐(OCR 明细数 ≠ 推送行数)时只填对得上的,不瞎补。
    单据级的 ERP 凭证号/客户码与每行的商品码一并落位,供导出的回导列使用。
    """
    if not action or not isinstance(merged_fields, dict):
        return
    cust = action.get("customer")
    if isinstance(cust, bool):
        merged_fields["customer_erp_action"] = "new" if cust else "reused"
    for src, dst in (
        ("docnum", "erp_docnum"),
        ("party_code", "erp_party_code"),
        ("direction", "direction"),
    ):
        v = str(action.get(src) or "").strip()
        if v:
            merged_fields[dst] = v
    items = merged_fields.get("items")
    line_created = action.get("items") or []
    line_codes = action.get("item_codes") or []
    if isinstance(items, list):
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                continue
            if i < len(line_created) and isinstance(line_created[i], bool):
                it["erp_action"] = "new" if line_created[i] else "reused"
            if i < len(line_codes) and line_codes[i]:
                it["erp_item_code"] = line_codes[i]
