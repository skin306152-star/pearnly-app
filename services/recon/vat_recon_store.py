# -*- coding: utf-8 -*-
"""销项税对账三张表(vat_report + reconciliation_task + reconciliation_row)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。P0-VAT 对账底座:
VAT 报告原始/解析结构化 + 对账任务(1 任务=1 客户×1 纳税期间)+ 逐行对账明细 ·
外加屏 B 自动建客户的内嵌 client helper(find_client_by_tax_id/auto_create_client/
get_client_by_id/find_or_create_client_by_tax_id)。tenant 隔离矩阵。
find_or_create_client_by_tax_id 复用 db.create_client(已迁 services/clients/store.py)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import json
import logging
from typing import Optional, Dict, Any, List

from core import db

# facade re-export(REFACTOR-WA-B1 · 实现已抽到同包子模块 · db.X/store.X 单一对象不变)
from services.recon.vat_recon_schema import ensure_vat_recon_tables  # noqa: F401,E402
from services.recon.recon_resolve import (  # noqa: F401,E402
    list_invoices_for_recon,
    find_client_by_tax_id,
    auto_create_client,
    get_client_by_id,
    find_or_create_client_by_tax_id,
)

logger = logging.getLogger(__name__)


# ── CRUD · vat_report ──────────────────────────────────────


def create_vat_report(
    tenant_id,
    client_id: int,
    period_year: int,
    period_month: int,
    parsed_rows: list,
    meta: dict,
    source_filename: str = "",
    parser_version: str = "",
) -> Optional[int]:
    import json as _j

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO vat_report (
                    tenant_id, client_id, period_year, period_month,
                    source_file_ids, parsed_rows,
                    total_amount_pre_vat, total_vat, total_amount,
                    parser_version
                ) VALUES (
                    %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb,
                    %s, %s, %s,
                    %s
                ) RETURNING id
            """,
                (
                    str(tenant_id) if tenant_id else None,
                    client_id,
                    period_year,
                    period_month,
                    _j.dumps([source_filename], ensure_ascii=False),
                    _j.dumps(parsed_rows, ensure_ascii=False, default=str),
                    meta.get("total_amount_pre_vat"),
                    meta.get("total_vat"),
                    meta.get("total_amount"),
                    parser_version,
                ),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_vat_report failed: {e}")
        return None


def get_vat_report(report_id: int) -> Optional[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT * FROM vat_report WHERE id = %s", (report_id,))
            row = cur.fetchone()
            if not row:
                return None
            r = dict(row)
            import json as _j

            if isinstance(r.get("parsed_rows"), str):
                r["parsed_rows"] = _j.loads(r["parsed_rows"])
            return r
    except Exception as e:
        logger.error(f"get_vat_report failed: {e}")
        return None


# ── CRUD · reconciliation_task ─────────────────────────────


def create_recon_task(
    tenant_id, user_id: str, client_id: int, period_year: int, period_month: int, vat_report_id: int
) -> Optional[int]:
    """创建对账任务 · 同 client+period 唯一约束失败时返回 None"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO reconciliation_task (
                    tenant_id, user_id, client_id,
                    period_year, period_month, vat_report_id
                ) VALUES (%s, %s::uuid, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    str(tenant_id) if tenant_id else None,
                    user_id,
                    client_id,
                    period_year,
                    period_month,
                    vat_report_id,
                ),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_recon_task failed: {e}")
        return None


def get_recon_task(task_id: int) -> Optional[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT * FROM reconciliation_task WHERE id = %s", (task_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_recon_task failed: {e}")
        return None


def update_recon_task_status(task_id: int, status: str):
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE reconciliation_task SET status = %s WHERE id = %s", (status, task_id)
            )
    except Exception as e:
        logger.error(f"update_recon_task_status failed: {e}")


def update_recon_task_completed(task_id: int, data: dict):
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE reconciliation_task SET
                    status                   = %s,
                    matched_count            = %s,
                    mismatched_count         = %s,
                    invoice_orphan_count     = %s,
                    report_orphan_count      = %s,
                    invoice_count_archived   = %s,
                    report_row_count         = %s,
                    completed_at             = NOW()
                WHERE id = %s
            """,
                (
                    data.get("status", "completed"),
                    data.get("matched_count", 0),
                    data.get("mismatched_count", 0),
                    data.get("invoice_orphan_count", 0),
                    data.get("report_orphan_count", 0),
                    data.get("invoice_count_archived", 0),
                    data.get("report_row_count", 0),
                    task_id,
                ),
            )
    except Exception as e:
        logger.error(f"update_recon_task_completed failed: {e}")


def list_recon_tasks(
    tenant_id=None, user_id: str = None, client_id: int = None
) -> List[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT t.*, c.name AS client_name, c.color AS client_color
                    FROM reconciliation_task t
                    LEFT JOIN clients c ON c.id = t.client_id
                    WHERE t.tenant_id = %s::uuid
                    ORDER BY t.created_at DESC LIMIT 100
                """,
                    (str(tenant_id),),
                )
            else:
                cur.execute(
                    """
                    SELECT t.*, c.name AS client_name, c.color AS client_color
                    FROM reconciliation_task t
                    LEFT JOIN clients c ON c.id = t.client_id
                    WHERE t.user_id = %s::uuid
                    ORDER BY t.created_at DESC LIMIT 100
                """,
                    (str(user_id),),
                )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_recon_tasks failed: {e}")
        return []


# ── CRUD · reconciliation_row ──────────────────────────────


def bulk_insert_recon_rows(rows: List[Dict[str, Any]]):
    import json as _j

    if not rows:
        return
    try:
        with db.get_cursor(commit=True) as cur:
            for r in rows:
                cur.execute(
                    """
                    INSERT INTO reconciliation_row (
                        task_id, invoice_id, report_row_no,
                        pair_confidence, status,
                        diff_fields, diff_categories
                    ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                    (
                        r["task_id"],
                        str(r["invoice_id"]) if r.get("invoice_id") else None,
                        r.get("report_row_no"),
                        r.get("pair_confidence"),
                        r["status"],
                        _j.dumps(r.get("diff_fields") or {}, ensure_ascii=False, default=str),
                        r.get("diff_categories", ""),
                    ),
                )
    except Exception as e:
        logger.error(f"bulk_insert_recon_rows failed: {e}")


def list_recon_rows(task_id: int) -> List[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT r.*,
                       h.invoice_no, h.invoice_date, h.seller_name, h.total_amount,
                       h.filename AS invoice_filename
                FROM reconciliation_row r
                LEFT JOIN ocr_history h ON h.id = r.invoice_id
                WHERE r.task_id = %s
                ORDER BY r.id
            """,
                (task_id,),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_recon_rows failed: {e}")
        return []


# ── 发票查询(供对账引擎使用)────────────────────────────────


# ============================================================
# v118.32.x · 销项税对账模块扩展 CRUD
# ============================================================


def get_recon_row(row_id: int) -> Optional[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT r.*,
                       h.invoice_no, h.invoice_date, h.seller_name, h.total_amount,
                       h.filename AS invoice_filename,
                       h.pages->0->'fields'->>'buyer_name'   AS buyer_name,
                       h.pages->0->'fields'->>'buyer_tax'    AS buyer_tax_id,
                       h.pages->0->'fields'->>'buyer_branch' AS buyer_branch,
                       h.pages->0->'fields'->>'subtotal'     AS amount_pre_vat,
                       h.pages->0->'fields'->>'vat'          AS vat_amount,
                       vr.parsed_rows AS report_rows
                FROM reconciliation_row r
                LEFT JOIN ocr_history h         ON h.id = r.invoice_id
                LEFT JOIN reconciliation_task t ON t.id = r.task_id
                LEFT JOIN vat_report vr         ON vr.id = t.vat_report_id
                WHERE r.id = %s
            """,
                (row_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            r = dict(row)
            # 把对应的 report row 也提出来
            try:
                if r.get("report_rows") and r.get("report_row_no"):
                    rows = (
                        r["report_rows"]
                        if isinstance(r["report_rows"], list)
                        else json.loads(r["report_rows"])
                    )
                    matching = next((x for x in rows if x.get("row_no") == r["report_row_no"]), {})
                    r.update({k: v for k, v in matching.items() if k.startswith("report_")})
            except Exception:
                pass  # report_rows JSON 解析 / 匹配失败 · 跳过该行 enrich
            # field_overrides jsonb 解开(P1.2-M2)
            if isinstance(r.get("field_overrides"), str):
                try:
                    r["field_overrides"] = json.loads(r["field_overrides"])
                except Exception:
                    r["field_overrides"] = {}
            return r
    except Exception as e:
        logger.error(f"get_recon_row failed: {e}")
        return None


def update_recon_row_ai_analysis(row_id: int, analysis: dict) -> bool:
    import json as _j

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE reconciliation_row
                SET ai_analysis = %s, updated_at = NOW()
                WHERE id = %s
            """,
                (_j.dumps(analysis, ensure_ascii=False), row_id),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_recon_row_ai_analysis failed: {e}")
        return False


def update_recon_row_action(row_id: int, action: str, notes: str = "") -> bool:
    """会计师操作:resolved/customer_issue/accepted_diff/pending"""
    if action not in ("pending", "resolved", "customer_issue", "accepted_diff"):
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE reconciliation_row
                SET accountant_action = %s, notes = %s, updated_at = NOW()
                WHERE id = %s
            """,
                (action, notes[:500], row_id),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_recon_row_action failed: {e}")
        return False


def list_recon_rows_detailed(task_id: int) -> List[Dict[str, Any]]:
    """v118.32.x · 拉取完整明细 · 含发票字段 + 报告字段 · 给屏 C 用"""
    import json as _j

    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT t.vat_report_id FROM reconciliation_task t WHERE t.id = %s
            """,
                (task_id,),
            )
            t = cur.fetchone()
            report_rows_map = {}
            if t and t.get("vat_report_id"):
                cur.execute(
                    "SELECT parsed_rows FROM vat_report WHERE id = %s", (t["vat_report_id"],)
                )
                vr = cur.fetchone()
                if vr and vr.get("parsed_rows"):
                    rows = (
                        vr["parsed_rows"]
                        if isinstance(vr["parsed_rows"], list)
                        else _j.loads(vr["parsed_rows"])
                    )
                    report_rows_map = {r.get("row_no"): r for r in rows if isinstance(r, dict)}

            cur.execute(
                """
                SELECT r.*,
                       h.invoice_no, h.invoice_date, h.seller_name, h.total_amount,
                       h.filename AS invoice_filename,
                       h.pages->0->'fields'->>'buyer_name'   AS buyer_name,
                       h.pages->0->'fields'->>'buyer_tax'    AS buyer_tax_id,
                       h.pages->0->'fields'->>'buyer_branch' AS buyer_branch,
                       h.pages->0->'fields'->>'subtotal'     AS amount_pre_vat,
                       h.pages->0->'fields'->>'vat'          AS vat_amount
                FROM reconciliation_row r
                LEFT JOIN ocr_history h ON h.id = r.invoice_id
                WHERE r.task_id = %s
                ORDER BY r.id
            """,
                (task_id,),
            )
            rows = cur.fetchall() or []
            result = []
            for r in rows:
                d = dict(r)
                # 合并报告侧数据
                if d.get("report_row_no") and d["report_row_no"] in report_rows_map:
                    rep = report_rows_map[d["report_row_no"]]
                    for k, v in rep.items():
                        if k.startswith("report_") or k == "is_individual":
                            d[k] = v
                # 数值字段转 float
                for nf in ("total_amount", "amount_pre_vat", "vat_amount"):
                    try:
                        d[nf] = float(str(d[nf]).replace(",", "")) if d.get(nf) else None
                    except Exception:
                        d[nf] = None
                # diff_fields jsonb 解开
                if isinstance(d.get("diff_fields"), str):
                    try:
                        d["diff_fields"] = _j.loads(d["diff_fields"])
                    except Exception:
                        d["diff_fields"] = {}
                # ai_analysis jsonb 解开
                if isinstance(d.get("ai_analysis"), str):
                    try:
                        d["ai_analysis"] = _j.loads(d["ai_analysis"])
                    except Exception:
                        pass
                # field_overrides jsonb 解开(P1.2-M2 · 发票侧字段用户校正)
                if isinstance(d.get("field_overrides"), str):
                    try:
                        d["field_overrides"] = _j.loads(d["field_overrides"])
                    except Exception:
                        d["field_overrides"] = {}
                result.append(d)
            return result
    except Exception as e:
        logger.error(f"list_recon_rows_detailed failed: {e}")
        return []


# ============================================================
# v118.32.2 · VAT 对账增强(只保留新增 · 已有的不复制)
# ============================================================
