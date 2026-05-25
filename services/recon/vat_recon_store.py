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

import db

logger = logging.getLogger(__name__)


def ensure_vat_recon_tables():
    """v118.32.0 · 销项税对账 3 张表 · 启动时幂等建"""
    try:
        with db.get_cursor(commit=True) as cur:

            # ── 1. vat_report(先建 · 被 reconciliation_task 外键引用)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vat_report (
                    id              BIGSERIAL PRIMARY KEY,
                    tenant_id       UUID,
                    client_id       BIGINT REFERENCES clients(id) ON DELETE SET NULL,
                    period_year     INTEGER NOT NULL,
                    period_month    INTEGER NOT NULL CHECK (period_month BETWEEN 1 AND 12),
                    issuer_tax_id   TEXT,
                    issuer_name     TEXT,
                    issuer_branch   TEXT DEFAULT '00000',
                    source_file_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
                    parsed_rows     JSONB NOT NULL DEFAULT '[]'::jsonb,
                    total_amount_pre_vat NUMERIC(18, 2),
                    total_vat       NUMERIC(18, 2),
                    total_amount    NUMERIC(18, 2),
                    parser_version  TEXT,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_vat_report_tenant
                    ON vat_report(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_vat_report_client_period
                    ON vat_report(client_id, period_year, period_month);
                CREATE INDEX IF NOT EXISTS idx_vat_report_tax_id
                    ON vat_report(issuer_tax_id) WHERE issuer_tax_id IS NOT NULL;
            """)

            # ── 2. reconciliation_task
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reconciliation_task (
                    id                       BIGSERIAL PRIMARY KEY,
                    tenant_id                UUID,
                    user_id                  UUID NOT NULL,
                    client_id                BIGINT REFERENCES clients(id) ON DELETE SET NULL,
                    period_year              INTEGER NOT NULL,
                    period_month             INTEGER NOT NULL CHECK (period_month BETWEEN 1 AND 12),
                    vat_report_id            BIGINT REFERENCES vat_report(id) ON DELETE SET NULL,
                    invoice_count_archived   INTEGER NOT NULL DEFAULT 0,
                    invoice_count_supplement INTEGER NOT NULL DEFAULT 0,
                    report_row_count         INTEGER NOT NULL DEFAULT 0,
                    status                   TEXT NOT NULL DEFAULT 'created',
                    matched_count            INTEGER NOT NULL DEFAULT 0,
                    mismatched_count         INTEGER NOT NULL DEFAULT 0,
                    invoice_orphan_count     INTEGER NOT NULL DEFAULT 0,
                    report_orphan_count      INTEGER NOT NULL DEFAULT 0,
                    confidence_score         REAL,
                    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    completed_at             TIMESTAMPTZ
                );
                CREATE INDEX IF NOT EXISTS idx_recon_task_tenant
                    ON reconciliation_task(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_recon_task_user
                    ON reconciliation_task(user_id);
                CREATE INDEX IF NOT EXISTS idx_recon_task_client_period
                    ON reconciliation_task(client_id, period_year, period_month);
                CREATE INDEX IF NOT EXISTS idx_recon_task_status
                    ON reconciliation_task(status);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_recon_task_unique_period
                    ON reconciliation_task(client_id, period_year, period_month)
                    WHERE status <> 'failed';
            """)

            # ── 3. reconciliation_row
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reconciliation_row (
                    id                BIGSERIAL PRIMARY KEY,
                    task_id           BIGINT NOT NULL
                                        REFERENCES reconciliation_task(id) ON DELETE CASCADE,
                    invoice_id        UUID REFERENCES ocr_history(id) ON DELETE SET NULL,
                    report_row_no     INTEGER,
                    pair_confidence   REAL,
                    status            TEXT NOT NULL DEFAULT 'pending',
                    diff_fields       JSONB NOT NULL DEFAULT '{}'::jsonb,
                    diff_categories   TEXT,
                    ai_analysis       TEXT,
                    accountant_action TEXT NOT NULL DEFAULT 'pending',
                    notes             TEXT,
                    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_recon_row_task
                    ON reconciliation_row(task_id);
                CREATE INDEX IF NOT EXISTS idx_recon_row_task_status
                    ON reconciliation_row(task_id, status);
                CREATE INDEX IF NOT EXISTS idx_recon_row_invoice
                    ON reconciliation_row(invoice_id) WHERE invoice_id IS NOT NULL;
            """)

            logger.info(
                "✅ vat_report + reconciliation_task + reconciliation_row 已就绪 (v118.32.0)"
            )
    except Exception as e:
        logger.error(f"ensure_vat_recon_tables failed: {e}")


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


def list_invoices_for_recon(
    tenant_id=None,
    client_id: int = None,
    period_year: int = None,
    period_month: int = None,
    source_ref: str = None,
) -> List[Dict[str, Any]]:
    """
    拉取指定客户 × 纳税期间内已归档发票
    从 ocr_history 顶层字段 + pages[0].fields 提取买方信息
    v118.32.4.3 · source_ref(=task_id 字符串) 传了就只取本次 task 关联的发票
    用于屏 B 流程隔离 · 不传时是屏 A 老逻辑(按客户+期间扫全部历史)
    """
    try:
        with db.get_cursor() as cur:
            # 按 invoice_date 的年月过滤
            # v118.32.2.4 · 期间过滤宽容化 · invoice_date NULL 的发票也进对账
            # (OCR 没识别出日期不该把发票排除 · 让匹配引擎用发票号/金额/税号补救)
            base_where = ""
            params: list = []
            if source_ref:
                base_where += " AND h.source_ref = %s"
                params.append(str(source_ref))
            if tenant_id:
                base_where += " AND h.user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)"
                params.append(str(tenant_id))
            if client_id:
                base_where += " AND h.client_id = %s"
                params.append(client_id)
            if period_year and period_month:
                # 日期不为空时按期间过滤 · 为空时一律通过(让匹配引擎处理)
                base_where += """ AND (
                    h.invoice_date IS NULL
                    OR (EXTRACT(YEAR  FROM h.invoice_date::date) = %s
                    AND EXTRACT(MONTH FROM h.invoice_date::date) = %s)
                )"""
                params.extend([period_year, period_month])
            elif period_year:
                base_where += (
                    " AND (h.invoice_date IS NULL OR EXTRACT(YEAR FROM h.invoice_date::date) = %s)"
                )
                params.append(period_year)
            elif period_month:
                base_where += (
                    " AND (h.invoice_date IS NULL OR EXTRACT(MONTH FROM h.invoice_date::date) = %s)"
                )
                params.append(period_month)

            cur.execute(
                f"""
                SELECT
                    h.id::text                                    AS id,
                    h.invoice_no,
                    h.invoice_date,
                    h.seller_name,
                    h.total_amount,
                    -- 买方信息从 pages[0].fields 提取(OCR 输出字段)
                    h.pages->0->'fields'->>'buyer_name'           AS buyer_name,
                    h.pages->0->'fields'->>'buyer_tax'            AS buyer_tax_id,
                    h.pages->0->'fields'->>'buyer_branch'         AS buyer_branch,
                    h.pages->0->'fields'->>'subtotal'             AS amount_pre_vat,
                    h.pages->0->'fields'->>'vat'                  AS vat_amount,
                    h.filename,
                    h.client_id
                FROM ocr_history h
                WHERE h.invoice_no IS NOT NULL
                  AND h.invoice_no != ''
                  {base_where}
                ORDER BY h.invoice_date, h.invoice_no
                LIMIT 2000
            """,
                params,
            )

            rows = cur.fetchall() or []
            result = []
            for r in rows:
                d = dict(r)
                # 数值字段做类型转换
                for field in ("total_amount", "amount_pre_vat", "vat_amount"):
                    try:
                        d[field] = float(str(d[field] or 0).replace(",", "")) if d[field] else None
                    except Exception:
                        d[field] = None
                result.append(d)
            return result
    except Exception as e:
        logger.error(f"list_invoices_for_recon failed: {e}")
        return []


# ============================================================
# v118.32.x · 销项税对账模块扩展 CRUD
# ============================================================


def find_client_by_tax_id(tenant_id, tax_id: str) -> Optional[Dict[str, Any]]:
    """按税号找客户 · 跨 tenant 隔离"""
    if not tax_id:
        return None
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT * FROM clients
                    WHERE tax_id = %s AND tenant_id = %s::uuid
                    LIMIT 1
                """,
                    (tax_id, str(tenant_id)),
                )
            else:
                cur.execute("SELECT * FROM clients WHERE tax_id = %s LIMIT 1", (tax_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"find_client_by_tax_id failed: {e}")
        return None


def auto_create_client(
    user_id: str, tenant_id, tax_id: str, name: str, color: str = "#3b82f6"
) -> Optional[int]:
    """v118.32.x · 屏 B 遇到陌生税号自动建客户 · 名字从发票/报告 OCR 出来"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO clients (
                    user_id, tenant_id, name, tax_id, color, is_active, notes
                ) VALUES (%s::uuid, %s, %s, %s, %s, TRUE,
                          'v118.32.x · 自动创建 · 请确认信息')
                RETURNING id
            """,
                (
                    user_id,
                    str(tenant_id) if tenant_id else None,
                    (name or f"客户 {tax_id[:5]}")[:200],
                    tax_id,
                    color,
                ),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"auto_create_client failed: {e}")
        return None


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


def get_client_by_id(client_id: int) -> Optional[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_client_by_id failed: {e}")
        return None


# ============================================================
# v118.32.2 · VAT 对账增强(只保留新增 · 已有的不复制)
# ============================================================


def find_or_create_client_by_tax_id(
    user_id: str, tenant_id: Optional[str], tax_id: str, name: str = ""
) -> Optional[int]:
    """v118.32.2 · 屏 B 自动建客户:按税号找 · 找不到就建 · 复用 create_client"""
    if not tax_id or len(tax_id) != 13:
        return None
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    "SELECT id FROM clients WHERE tenant_id = %s AND tax_id = %s "
                    "AND is_active = TRUE LIMIT 1",
                    (str(tenant_id), tax_id),
                )
            else:
                cur.execute(
                    "SELECT id FROM clients WHERE user_id = %s AND tax_id = %s "
                    "AND is_active = TRUE LIMIT 1",
                    (str(user_id), tax_id),
                )
            row = cur.fetchone()
            if row:
                return int(row["id"])
    except Exception as e:
        logger.error(f"find_or_create_client_by_tax_id lookup failed: {e}")
        return None

    # 没找到 · 建一个 · 复用现有 create_client
    palette = [
        "#3b82f6",
        "#10b981",
        "#f59e0b",
        "#ef4444",
        "#8b5cf6",
        "#ec4899",
        "#14b8a6",
        "#f97316",
        "#06b6d4",
        "#a855f7",
    ]
    color = palette[hash(tax_id) % len(palette)]
    new_id = db.create_client(
        user_id=str(user_id),
        tenant_id=str(tenant_id) if tenant_id else None,
        name=(name or f"客户 {tax_id[-4:]}"),
        tax_id=tax_id,
        color=color,
    )
    if new_id:
        logger.info(f"[v118.32.2] auto-created client id={new_id} tax_id={tax_id} name={name}")
    return new_id
