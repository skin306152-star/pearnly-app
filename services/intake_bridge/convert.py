# -*- coding: utf-8 -*-
"""转换编排:逐张 history 判方向 → 派进项/销项腿建单,幂等 + 单张隔离。

调用方管一条共享游标(单事务批处理);每张 history 一个 SAVEPOINT,一张失败/跳过绝不
回滚同批已转换的其它张(仿 services/accounting/hooks.enqueue_posting 的隔离范式)。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.erp.express_push import direction as direction_mod
from services.intake_bridge import purchase_leg, sales_leg
from services.intake_bridge.errors import SkipConversion

logger = logging.getLogger("mr-pilot")

_MAX_HISTORY_IDS = 500
_SAVEPOINT = "intake_bridge_convert"


def erp_declaration_error(fields: dict) -> Optional[str]:
    """Validate the ERP-only user decisions before a draft can become a formal document."""
    if str(fields.get("direction") or "").strip().lower() not in ("purchase", "sales"):
        return "no_direction"
    items = fields.get("items")
    if not isinstance(items, list) or not items:
        return "no_items"
    for item in items:
        if not isinstance(item, dict) or not str(item.get("name") or "").strip():
            return "item_name_required"
        if not str(item.get("qty") or "").strip():
            return "item_qty_required"
        if str(item.get("posting_kind") or "").strip().lower() not in ("stock", "service"):
            return "posting_kind_required"
    return None


def validate_erp_histories(cur, *, tenant_id: str, history_ids: list) -> dict[str, str]:
    """Return invalid ERP history ids and reasons; missing ids fail closed as ``not_found``."""
    ids = list(dict.fromkeys(str(value) for value in history_ids if value))
    if not ids:
        return {}
    cur.execute(
        "SELECT id, pages FROM ocr_history WHERE tenant_id = %s::uuid " "AND id = ANY(%s::uuid[])",
        (tenant_id, ids),
    )
    found = {}
    for row in cur.fetchall() or []:
        pages = row.get("pages") or []
        fields = _primary_fields(pages) or {}
        found[str(row["id"])] = erp_declaration_error(fields)
    invalid = {}
    for history_id in ids:
        if history_id not in found:
            invalid[history_id] = "not_found"
        elif found[history_id]:
            invalid[history_id] = found[history_id]
    return invalid


def convert_histories(cur, *, tenant_id: str, user_id: str, history_ids: list) -> dict:
    """逐张转换。返回 {converted:[{history_id,doc_type,doc_id,doc_no}], skipped:[{history_id,reason}]}。"""
    converted: list = []
    skipped: list = []
    ids = [str(h) for h in (history_ids or []) if h][:_MAX_HISTORY_IDS]
    # 同批常是同一账套的多张票:own_tax_id 按 workspace_client_id 缓存,避免每张都查一遍
    # workspace_clients(批量确认/汇总表导入常见几十张同账套票)。
    tax_id_cache: dict = {}
    for hid in ids:
        try:
            cur.execute(f"SAVEPOINT {_SAVEPOINT}")
        except Exception as e:
            logger.warning(f"intake_bridge savepoint 失败(history_id={hid}): {e}")
            skipped.append({"history_id": hid, "reason": "error:savepoint_failed"})
            continue
        try:
            result = _convert_one(
                cur, tenant_id=tenant_id, user_id=user_id, history_id=hid, tax_id_cache=tax_id_cache
            )
            cur.execute(f"RELEASE SAVEPOINT {_SAVEPOINT}")
            converted.append({"history_id": hid, **result})
        except Exception as e:
            # 单张失败/跳过绝不回滚同批已转换的其它张 —— 只撤这一张的 SAVEPOINT。SkipConversion
            # 是预期内的跳过(no_direction/duplicate 等),不当错误记警告日志;其它异常才记。
            cur.execute(f"ROLLBACK TO SAVEPOINT {_SAVEPOINT}")
            cur.execute(f"RELEASE SAVEPOINT {_SAVEPOINT}")
            if isinstance(e, SkipConversion):
                reason = e.reason
            else:
                logger.warning(f"intake_bridge convert 失败(history_id={hid}): {e}")
                reason = f"error:{e}"[:200]
            skipped.append({"history_id": hid, "reason": reason})
    return {"converted": converted, "skipped": skipped}


def _convert_one(cur, *, tenant_id: str, user_id: str, history_id: str, tax_id_cache: dict) -> dict:
    history = _load_history(cur, tenant_id=tenant_id, history_id=history_id)
    if history is None:
        raise SkipConversion("not_found")
    if _already_converted(cur, tenant_id=tenant_id, history_id=history_id):
        raise SkipConversion("already_converted")

    fields = _primary_fields(history.get("pages") or [])
    if fields is None or not _has_bookable_content(fields):
        raise SkipConversion("no_items")

    workspace_client_id = history.get("workspace_client_id")
    own_tax_id = _cached_own_tax_id(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, cache=tax_id_cache
    )
    direction = direction_mod.resolve_direction(
        {"fields": fields, "workspace_client_id": workspace_client_id},
        history,
        own_tax_id=own_tax_id,
    )
    if direction is None:
        raise SkipConversion("no_direction")
    if not workspace_client_id:
        raise SkipConversion("no_workspace")

    if direction == "purchase":
        doc_id, doc_no = purchase_leg.book_from_history(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=int(workspace_client_id),
            created_by=user_id,
            fields=fields,
            source=str(history.get("source") or ""),
        )
        _stamp_ocr_history_id(
            cur, table="purchase_docs", tenant_id=tenant_id, doc_id=doc_id, history_id=history_id
        )
        return {"doc_type": "purchase", "doc_id": str(doc_id), "doc_no": doc_no}

    doc_id, doc_no = sales_leg.issue_from_history(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=int(workspace_client_id),
        created_by=user_id,
        fields=fields,
    )
    _stamp_ocr_history_id(
        cur, table="sales_documents", tenant_id=tenant_id, doc_id=doc_id, history_id=history_id
    )
    return {"doc_type": "sales", "doc_id": str(doc_id), "doc_no": doc_no}


def _load_history(cur, *, tenant_id: str, history_id: str) -> Optional[dict]:
    cur.execute(
        "SELECT pages, workspace_client_id, source FROM ocr_history "
        "WHERE id = %s::uuid AND tenant_id = %s::uuid",
        (history_id, tenant_id),
    )
    return cur.fetchone()


def _already_converted(cur, *, tenant_id: str, history_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM purchase_docs WHERE tenant_id = %s AND ocr_history_id = %s::uuid "
        "UNION ALL "
        "SELECT 1 FROM sales_documents WHERE tenant_id = %s AND ocr_history_id = %s::uuid "
        "LIMIT 1",
        (tenant_id, history_id, tenant_id, history_id),
    )
    return cur.fetchone() is not None


def history_is_converted(*, tenant_id: str, history_id: str) -> bool:
    """Whether an OCR history already owns a formal purchase or sales document."""
    from core import db

    with db.get_cursor_rls(tenant_id) as cur:
        return _already_converted(cur, tenant_id=tenant_id, history_id=history_id)


def unconverted_owned_history_ids(
    cur, *, tenant_id: str, user_id: str, history_ids: list
) -> list[str]:
    """Return owned OCR histories that still have no formal purchase or sales document."""
    ids = list(dict.fromkeys(str(value) for value in history_ids if value))
    if not ids:
        return []
    cur.execute(
        "SELECT h.id::text AS id FROM ocr_history h "
        "WHERE h.tenant_id = %s::uuid AND h.user_id = %s::uuid "
        "AND h.id = ANY(%s::uuid[]) "
        "AND NOT EXISTS (SELECT 1 FROM purchase_docs p "
        "WHERE p.tenant_id = h.tenant_id AND p.ocr_history_id = h.id) "
        "AND NOT EXISTS (SELECT 1 FROM sales_documents s "
        "WHERE s.tenant_id = h.tenant_id AND s.ocr_history_id = h.id)",
        (tenant_id, user_id, ids),
    )
    return [str(row["id"]) for row in cur.fetchall() or []]


def _primary_fields(pages: list) -> Optional[dict]:
    """一条 history = 一张票(services/ocr/invoice_grouper 已按此粒度拆分),直接取 pages[0]。"""
    if not pages or not isinstance(pages[0], dict):
        return None
    f = pages[0].get("fields")
    return f if isinstance(f, dict) else None


def _has_bookable_content(fields: dict) -> bool:
    """有明细行,或至少有票面总额/税前小计可收敛成单行 —— 两者都没有=这张票真的没数据。"""
    for it in fields.get("items") or []:
        if isinstance(it, dict) and str(it.get("name") or "").strip():
            return True
    for key in ("total_amount", "subtotal"):
        raw = str(fields.get(key) or "").replace(",", "").strip()
        try:
            if raw and float(raw) > 0:
                return True
        except ValueError:
            continue
    return False


def _own_tax_id(cur, *, tenant_id: str, workspace_client_id) -> str:
    if not workspace_client_id:
        return ""
    cur.execute(
        "SELECT tax_id FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (int(workspace_client_id), tenant_id),
    )
    row = cur.fetchone()
    return str((row or {}).get("tax_id") or "").strip()


def _cached_own_tax_id(cur, *, tenant_id: str, workspace_client_id, cache: dict) -> str:
    if workspace_client_id not in cache:
        cache[workspace_client_id] = _own_tax_id(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
    return cache[workspace_client_id]


def _stamp_ocr_history_id(cur, *, table: str, tenant_id: str, doc_id, history_id: str) -> None:
    cur.execute(
        f"UPDATE {table} SET ocr_history_id = %s::uuid WHERE tenant_id = %s AND id = %s",
        (history_id, tenant_id, doc_id),
    )
