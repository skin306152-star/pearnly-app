# -*- coding: utf-8 -*-
"""VAT 对账 · 客户/发票解析 DAL(REFACTOR-WA-B1 · 2026-05-29 从 vat_recon_store 抽出 · 纯搬家 0 逻辑改)

屏 B 自动建客户 + 对账可选发票清单:list_invoices_for_recon / find_client_by_tax_id /
auto_create_client / get_client_by_id / find_or_create_client_by_tax_id(复用 db.create_client)。
vat_recon_store 顶部 re-import 回去当 facade · db.py / 调用点 / 契约测试零改。
"""

import logging
from typing import Optional, Dict, Any, List  # noqa: F401

logger = logging.getLogger(__name__)


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


def get_client_by_id(client_id: int) -> Optional[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_client_by_id failed: {e}")
        return None


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


from core import db  # noqa: E402 · 循环 import 解法
