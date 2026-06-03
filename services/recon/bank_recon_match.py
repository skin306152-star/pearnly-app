# -*- coding: utf-8 -*-
"""银行对账 v1 · 交易↔发票候选匹配 DAL(REFACTOR-WA-B1 · 2026-05-29 从 bank_recon_v1_store 抽出 · 纯搬家 0 逻辑改)

发票候选检索(find_invoice_candidates_for_tx + 私有 _find_candidates_from_pages_jsonb)+
匹配结果/统计/覆盖(save_match_result / get_tx_candidates / update_session_match_stats / override_tx_match)。
组内自洽(只依赖 db + 组内函数)· bank_recon_v1_store 顶部 re-import 当 facade · db.X/store.X 单一对象不变。
"""

import logging
from typing import Optional, Dict, Any, List  # noqa: F401

logger = logging.getLogger(__name__)


def find_invoice_candidates_for_tx(
    user_id: str, amount: float, tx_date: str, amount_tol: float = 10.0, date_tol_days: int = 7
) -> List[Dict[str, Any]]:
    """
    匹配算法用 · 在 ocr_history 里粗筛候选发票(用索引高效过滤)
    条件:同用户 · 金额差 ≤ amount_tol · 日期差 ≤ date_tol_days
    返回:[{id, amount_total, invoice_date, vendor, invoice_no, category_tag}, ...]
    """
    if not amount or not tx_date:
        return []
    try:
        with db.get_cursor() as cur:
            # pages 字段里 JSON 可能保存了 amount / total / invoice_date / vendor
            # 我们从 history 表的标量字段取(status=success 的)· 容忍 JSONB 结构
            cur.execute(
                """
                SELECT h.id, h.pages, h.filename, h.category_tag, h.created_at,
                       h.amount_total, h.invoice_date, h.vendor, h.invoice_no
                FROM ocr_history h
                WHERE h.user_id = %s
                  AND h.status = 'success'
                  AND h.amount_total IS NOT NULL
                  AND h.amount_total BETWEEN %s AND %s
                  AND (h.invoice_date IS NULL
                       OR h.invoice_date BETWEEN %s::date - %s::interval
                                             AND %s::date + %s::interval)
                LIMIT 200
            """,
                (
                    str(user_id),
                    float(amount) - float(amount_tol),
                    float(amount) + float(amount_tol),
                    tx_date,
                    f"{date_tol_days} days",
                    tx_date,
                    f"{date_tol_days} days",
                ),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        # 如果 ocr_history 里没有这些标量字段(旧版),降级从 pages JSONB 查
        logger.warning(f"find_invoice_candidates_for_tx SQL 降级: {e}")
        return _find_candidates_from_pages_jsonb(
            user_id, amount, tx_date, amount_tol, date_tol_days
        )


def _find_candidates_from_pages_jsonb(
    user_id: str, amount: float, tx_date: str, amount_tol: float, date_tol_days: int
) -> List[Dict[str, Any]]:
    """降级查询:从 pages JSONB 里找 · 效率稍低 · 适合历史数据少(< 5000)"""
    try:
        from datetime import date, timedelta

        d = date.fromisoformat(tx_date)
        d_start = (d - timedelta(days=date_tol_days)).isoformat()
        d_end = (d + timedelta(days=date_tol_days)).isoformat()

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, pages, filename, category_tag, created_at
                FROM ocr_history
                WHERE user_id = %s
                  AND status = 'success'
                  AND created_at BETWEEN %s::date - interval '60 days'
                                   AND %s::date + interval '30 days'
                LIMIT 500
            """,
                (str(user_id), d_start, d_end),
            )
            rows = cur.fetchall()

        out = []
        for row in rows:
            pages = row.get("pages") or []
            if not isinstance(pages, list):
                continue
            # 合并所有页的 total / amount
            for p in pages:
                if not isinstance(p, dict):
                    continue
                amt = p.get("amount_total") or p.get("total") or p.get("amount")
                inv_date = p.get("invoice_date") or p.get("date")
                if amt is None:
                    continue
                try:
                    amt_f = float(amt)
                except (ValueError, TypeError):
                    continue
                if abs(amt_f - float(amount)) > float(amount_tol):
                    continue
                # 日期过滤
                if inv_date:
                    try:
                        id_d = date.fromisoformat(str(inv_date)[:10])
                        if abs((id_d - d).days) > date_tol_days:
                            continue
                    except ValueError:
                        pass  # 日期格式异常 · 跳过日期过滤(保留候选)
                out.append(
                    {
                        "id": row["id"],
                        "amount_total": amt_f,
                        "invoice_date": inv_date,
                        "vendor": p.get("vendor") or p.get("seller"),
                        "invoice_no": p.get("invoice_no") or p.get("number"),
                        "category_tag": row.get("category_tag"),
                        "filename": row.get("filename"),
                    }
                )
                break  # 一份历史只取一次
        return out
    except Exception as e:
        logger.error(f"_find_candidates_from_pages_jsonb failed: {e}")
        return []


def save_match_result(
    tx_id: str, scored: List[Dict[str, Any]], thresh_auto: float = 85, thresh_suggest: float = 60
) -> str:
    """
    写入匹配结果
    - 清空该 tx 之前的 candidates
    - 按分数阶梯决定 match_status
    返回:最终 match_status(matched / suggested / unmatched)
    """
    try:
        with db.get_cursor(commit=True) as cur:
            # 清旧候选
            cur.execute("DELETE FROM bank_reconcile_candidates WHERE tx_id = %s", (tx_id,))

            if not scored:
                cur.execute(
                    """
                    UPDATE bank_reconcile_transactions
                    SET match_status = 'unmatched',
                        matched_history_id = NULL,
                        match_score = NULL,
                        match_reason = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                """,
                    (tx_id,),
                )
                return "unmatched"

            best = scored[0]
            best_score = best["score"]

            # 写所有候选
            for i, c in enumerate(scored):
                is_picked = i == 0 and best_score >= thresh_suggest
                cur.execute(
                    """
                    INSERT INTO bank_reconcile_candidates
                        (tx_id, history_id, score, reason, is_auto_picked)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                    (tx_id, c["history_id"], c["score"], c["reason"], is_picked),
                )

            # 决定 tx 的 match_status
            if best_score >= thresh_auto:
                status = "matched"
                matched_id = best["history_id"]
            elif best_score >= thresh_suggest:
                status = "suggested"
                matched_id = best["history_id"]
            else:
                status = "unmatched"
                matched_id = None

            cur.execute(
                """
                UPDATE bank_reconcile_transactions
                SET match_status = %s,
                    matched_history_id = %s,
                    match_score = %s,
                    match_reason = %s,
                    updated_at = NOW()
                WHERE id = %s
            """,
                (
                    status,
                    matched_id,
                    best_score if matched_id else None,
                    best["reason"] if matched_id else None,
                    tx_id,
                ),
            )
            return status
    except Exception as e:
        logger.error(f"save_match_result failed: {e}")
        return "unmatched"


def get_tx_candidates(tx_id: str, user_id: str) -> List[Dict[str, Any]]:
    """
    返回这条流水匹配过后落库的全部候选(已按 score 降序 · 最多 5 个)
    每项:
      history_id     - ocr_history.id
      score          - 0-100
      reason         - 匹配原因短描(中文)
      is_auto_picked - True 表示这是 auto-picked 的(score >= THRESH_AUTO 时是 matched)
      invoice_no / vendor / amount_total / invoice_date / filename - 发票字段
    鉴权:tx 必须属于这个 user_id
    """
    try:
        with db.get_cursor() as cur:
            # 鉴权 + JOIN
            cur.execute(
                """
                SELECT c.history_id, c.score, c.reason, c.is_auto_picked,
                       h.invoice_no, h.vendor, h.amount_total, h.invoice_date,
                       h.filename, h.category_tag, h.created_at AS h_created_at
                FROM bank_reconcile_candidates c
                JOIN bank_reconcile_transactions t ON t.id = c.tx_id
                LEFT JOIN ocr_history h ON h.id = c.history_id
                WHERE c.tx_id = %s AND t.user_id = %s
                ORDER BY c.score DESC
                LIMIT 5
            """,
                (tx_id, str(user_id)),
            )
            out = []
            for r in cur.fetchall():
                d = dict(r)
                # 日期 ISO 字符串化(防 datetime 序列化报错)
                for k in ("invoice_date", "h_created_at"):
                    v = d.get(k)
                    if v is not None and hasattr(v, "isoformat"):
                        d[k] = v.isoformat()
                out.append(d)
            return out
    except Exception as e:
        logger.error(f"get_tx_candidates failed: {e}")
        return []


def update_session_match_stats(session_id: str) -> bool:
    """重算 session 的 matched_count / unmatched_count"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE bank_reconcile_sessions s
                SET matched_count = (
                        SELECT COUNT(*) FROM bank_reconcile_transactions
                        WHERE session_id = s.id AND match_status = 'matched'
                    ),
                    unmatched_count = (
                        SELECT COUNT(*) FROM bank_reconcile_transactions
                        WHERE session_id = s.id AND match_status IN ('unmatched','suggested')
                    ),
                    match_status = 'matched',
                    updated_at = NOW()
                WHERE id = %s
            """,
                (session_id,),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_session_match_stats failed: {e}")
        return False


def override_tx_match(tx_id: str, user_id: str, history_id: Optional[str], status: str) -> bool:
    """用户手动重指派 · 或忽略一条流水
    status: matched / unmatched / ignored
    """
    if status not in ("matched", "unmatched", "ignored"):
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE bank_reconcile_transactions
                SET match_status = %s,
                    matched_history_id = %s,
                    match_reviewed_by = %s,
                    match_reviewed_at = NOW(),
                    match_reason = COALESCE(match_reason, 'user_override'),
                    updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """,
                (status, history_id, str(user_id), tx_id, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"override_tx_match failed: {e}")
        return False


from core import db  # noqa: E402 · 循环 import 解法
