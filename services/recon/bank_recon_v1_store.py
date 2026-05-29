# -*- coding: utf-8 -*-
"""银行对账 v1(M10 · bank_reconcile_sessions + 交易匹配候选)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
session CRUD + 解析结果存储 + 发票候选匹配(_find_candidates_from_pages_jsonb 私有)+
匹配结果/统计 + 测试数据 seed/clear。datetime 各函数本就局部 import。
db.py 文件尾 re-export 对外函数 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

import db

# facade re-export(REFACTOR-WA-B1 · 匹配实现下沉 bank_recon_match · db.X/store.X 单一对象不变)
from services.recon.bank_recon_match import (  # noqa: F401,E402
    find_invoice_candidates_for_tx,
    _find_candidates_from_pages_jsonb,
    save_match_result,
    get_tx_candidates,
    update_session_match_stats,
    override_tx_match,
)

logger = logging.getLogger(__name__)


# v118.26.2 · 给 bank_reconcile_sessions 加 client_id 列(幂等)
#   行业标配:Xero/QB 一个 bank account 属于一个 organisation
#   我们事务所多客户 → session 必须带 client_id · 用于 v28.1 client filter
def ensure_bank_recon_client_id_column():
    """启动时调一次 · 给 bank_reconcile_sessions 加 client_id 列"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                ALTER TABLE bank_reconcile_sessions
                ADD COLUMN IF NOT EXISTS client_id INTEGER
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_bank_recon_sessions_client
                ON bank_reconcile_sessions(client_id)
            """)
            logger.info("[v118.26.2] bank_reconcile_sessions.client_id 列已就绪")
    except Exception as e:
        logger.warning(f"ensure_bank_recon_client_id_column failed: {e}")


def create_bank_recon_session(
    user_id: str, bank_code: str, filename: str, pages: int
) -> Optional[str]:
    """创建一条会话 · 返回 id"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO bank_reconcile_sessions
                    (user_id, bank_code, source_filename, source_pages, parse_status)
                VALUES (%s, %s, %s, %s, 'pending')
                RETURNING id
            """,
                (str(user_id), bank_code, (filename or "")[:200], int(pages)),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_bank_recon_session failed: {e}")
        return None


def save_bank_recon_parse(session_id: str, parsed: Dict[str, Any]) -> bool:
    """解析完成后把会话 + 流水批量落库"""
    try:
        with db.get_cursor(commit=True) as cur:
            tx_n = len(parsed.get("transactions") or [])
            # 更新会话头信息
            # v118.26.1 · 补 unmatched_count = tx_n / matched_count = 0
            #   因为流水落库默认 match_status='unmatched' · 不写这俩字段会让顶部 chip 计数永远 0
            cur.execute(
                """
                UPDATE bank_reconcile_sessions SET
                    bank_code       = %s,
                    account_last4   = %s,
                    statement_month = %s,
                    period_start    = %s,
                    period_end      = %s,
                    opening_balance = %s,
                    closing_balance = %s,
                    total_inflow    = %s,
                    total_outflow   = %s,
                    tx_count        = %s,
                    matched_count   = 0,
                    unmatched_count = %s,
                    parse_status    = 'parsed',
                    updated_at      = NOW()
                WHERE id = %s
                RETURNING user_id
            """,
                (
                    parsed.get("bank_code") or "OTHER",
                    parsed.get("account_last4"),
                    parsed.get("statement_month"),
                    parsed.get("period_start"),
                    parsed.get("period_end"),
                    parsed.get("opening_balance"),
                    parsed.get("closing_balance"),
                    parsed.get("total_inflow") or 0,
                    parsed.get("total_outflow") or 0,
                    tx_n,
                    tx_n,  # unmatched_count = 全部初始未匹配
                    session_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                return False
            user_id = row["user_id"]

            # 批量插入流水
            txs = parsed.get("transactions") or []
            for tx in txs:
                cur.execute(
                    """
                    INSERT INTO bank_reconcile_transactions
                        (session_id, user_id, row_no, tx_date, value_date, direction,
                         amount, balance_after, description, counterparty, ref_no, channel)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        session_id,
                        user_id,
                        tx.get("row_no"),
                        tx.get("tx_date"),
                        tx.get("value_date") or tx.get("tx_date"),
                        tx.get("direction"),
                        tx.get("amount"),
                        tx.get("balance_after"),
                        (tx.get("description") or "")[:500],
                        (tx.get("counterparty") or "")[:200] if tx.get("counterparty") else None,
                        (tx.get("ref_no") or "")[:100] if tx.get("ref_no") else None,
                        (tx.get("channel") or "")[:50] if tx.get("channel") else None,
                    ),
                )
            return True
    except Exception as e:
        logger.error(f"save_bank_recon_parse failed: {e}")
        return False


def mark_recon_parse_failed(session_id: str, error_msg: str) -> bool:
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE bank_reconcile_sessions
                SET parse_status = 'parse_failed',
                    parse_error  = %s,
                    updated_at   = NOW()
                WHERE id = %s
            """,
                ((error_msg or "")[:500], session_id),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"mark_recon_parse_failed failed: {e}")
        return False


def get_bank_recon_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """获取会话头(鉴权)"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT * FROM bank_reconcile_sessions
                WHERE id = %s AND user_id = %s
            """,
                (session_id, str(user_id)),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_bank_recon_session failed: {e}")
        return None


def list_bank_recon_sessions(
    user_id: str, limit: int = 30, restrict_client_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """列最近会话
    v118.26.2 · 加 restrict_client_ids 参数(v28.1 客户分配 filter)
      None       → 不限(老板/超管)
      []         → 没分到任何客户 · 只能看自己上传未归属(client_id IS NULL)
      [1,2,3]    → (client_id IN list) OR (user_id = self AND client_id IS NULL)
    """
    try:
        with db.get_cursor() as cur:
            base_sql = """
                SELECT id, bank_code, account_last4, statement_month,
                       period_start, period_end, total_inflow, total_outflow,
                       tx_count, matched_count, unmatched_count,
                       parse_status, match_status, source_filename, created_at,
                       client_id
                FROM bank_reconcile_sessions
                WHERE user_id = %s
            """
            params: list = [str(user_id)]

            if restrict_client_ids is None:
                pass  # 老板/超管 · 不加 filter
            elif len(restrict_client_ids) == 0:
                # 员工没分到任何客户 · 只看自己上传未归属
                base_sql += " AND client_id IS NULL"
            else:
                base_sql += " AND (client_id = ANY(%s) OR client_id IS NULL)"
                params.append([int(c) for c in restrict_client_ids])

            base_sql += " ORDER BY created_at DESC LIMIT %s"
            params.append(int(limit))

            cur.execute(base_sql, tuple(params))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_bank_recon_sessions failed: {e}")
        return []


# v118.26.2 · 给一个 session 绑客户(老板分客户给员工 · 流水进 client filter)
def update_bank_recon_session_client(
    user_id: str, session_id: str, client_id: Optional[int]
) -> bool:
    """
    更新 session 的 client_id · None 表示解绑
    鉴权:session 必须属于本 user
    返回:成功 True / 不存在 False
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE bank_reconcile_sessions
                SET client_id = %s, updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """,
                (client_id, session_id, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_bank_recon_session_client failed: {e}")
        return False


# v118.26.0 · 对账中心首页统计(当月 · BKK 时区)
def get_bank_recon_stats(user_id: str) -> Dict[str, Any]:
    """
    对账中心首页用 · 当月概览
    pending = suggested(系统推荐 · 等会计点确认)
    matched = matched(已确认匹配)
    unmatched = unmatched(找不到候选发票)
    ignored 状态不计入(会计主动忽略 · 如老板私事)
    v118.26.0.1 · 月初按 BKK 时区在 Python 里算(避开 SQL 时区兼容性)
    """
    default = {
        "pending": 0,
        "matched": 0,
        "unmatched": 0,
        "total_sessions": 0,
        "last_activity_at": None,
    }
    try:
        # BKK 月初 · 转 UTC 给 PG(s.created_at 是 timestamptz)
        from datetime import datetime, timezone, timedelta

        bkk = timezone(timedelta(hours=7))
        now_bkk = datetime.now(bkk)
        month_start_bkk = now_bkk.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) FILTER (WHERE t.match_status = 'suggested') AS pending,
                  COUNT(*) FILTER (WHERE t.match_status = 'matched')   AS matched,
                  COUNT(*) FILTER (WHERE t.match_status = 'unmatched') AS unmatched,
                  COUNT(DISTINCT s.id)                                  AS total_sessions,
                  MAX(s.created_at)                                     AS last_activity_at
                FROM bank_reconcile_sessions s
                LEFT JOIN bank_reconcile_transactions t
                  ON t.session_id = s.id AND t.user_id = s.user_id
                WHERE s.user_id = %s
                  AND s.created_at >= %s
            """,
                (str(user_id), month_start_bkk),
            )
            row = cur.fetchone()
            if not row:
                return default
            d = dict(row)
            return {
                "pending": int(d.get("pending") or 0),
                "matched": int(d.get("matched") or 0),
                "unmatched": int(d.get("unmatched") or 0),
                "total_sessions": int(d.get("total_sessions") or 0),
                "last_activity_at": (
                    d["last_activity_at"].isoformat() if d.get("last_activity_at") else None
                ),
            }
    except Exception as e:
        # v118.26.0.1 · 完整 traceback 进日志 · 方便定位
        logger.exception(f"get_bank_recon_stats failed for user={user_id}: {e}")
        return default


def list_bank_recon_transactions(
    session_id: str, user_id: str, match_filter: Optional[str] = None, limit: int = 500
) -> List[Dict[str, Any]]:
    """列一个会话下的流水 · 可按 match_status 过滤"""
    try:
        with db.get_cursor() as cur:
            q = """
                SELECT id, row_no, tx_date, value_date, direction, amount,
                       balance_after, description, counterparty, ref_no, channel,
                       match_status, matched_history_id, match_score, match_reason
                FROM bank_reconcile_transactions
                WHERE session_id = %s AND user_id = %s
            """
            params: List[Any] = [session_id, str(user_id)]
            if match_filter in ("unmatched", "matched", "suggested", "ignored"):
                q += " AND match_status = %s"
                params.append(match_filter)
            q += " ORDER BY row_no LIMIT %s"
            params.append(int(limit))
            cur.execute(q, tuple(params))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_bank_recon_transactions failed: {e}")
        return []


def delete_bank_recon_session(user_id: str, session_id: str) -> bool:
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                DELETE FROM bank_reconcile_sessions
                WHERE id = %s AND user_id = %s
            """,
                (session_id, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_bank_recon_session failed: {e}")
        return False


# v118.26.2 · 获取一条流水的所有候选发票(JOIN ocr_history 拿展示字段)


# v118.26.2 · 测试数据生成(skin OAuth 白名单专用 · 让对账 UI 能立即可测)
#   场景:v118.26.4 才做 Excel/CSV 解析 · 此版没现成数据
#   行业惯例:Xero Demo Company / QB Sample Data 的轻量替代
def seed_bank_recon_test_data(user_id: str) -> Dict[str, Any]:
    """
    给 skin 测试账号塞一份 mock 银行对账 session
      - 1 个 KBANK session(2026-04 月份)
      - 8 条流水(5 条正常 IN/OUT · 跨 30 天)
      - 用户名下已有 OCR 发票(直接复用 ocr_history)· 跑匹配后能命中部分流水
    返回 {session_id, tx_count, ok}
    """
    from datetime import datetime, timedelta

    try:
        with db.get_cursor(commit=True) as cur:
            # 1. 建 session(标记 source_filename 含 _MOCK_ 易识别 · 用户能看到一目了然)
            today = datetime.now()
            period_start = (today.replace(day=1) - timedelta(days=30)).date()
            period_end = today.replace(day=1).date() - timedelta(days=1)
            cur.execute(
                """
                INSERT INTO bank_reconcile_sessions
                    (user_id, bank_code, source_filename, source_pages,
                     parse_status, account_last4, statement_month,
                     period_start, period_end,
                     opening_balance, closing_balance,
                     total_inflow, total_outflow,
                     tx_count, matched_count, unmatched_count)
                VALUES (%s, 'KBANK', %s, 1,
                        'parsed', '8821', %s,
                        %s, %s,
                        125000.00, 168320.50,
                        58420.50, 15100.00,
                        8, 0, 8)
                RETURNING id
            """,
                (
                    str(user_id),
                    f"_MOCK_KBANK_statement_{period_end.strftime('%Y%m')}.pdf",
                    period_end.strftime("%Y-%m"),
                    period_start,
                    period_end,
                ),
            )
            session_id = str(cur.fetchone()["id"])

            # 2. 8 条流水(混合金额 · 跨 30 天 · 让候选评分有变化)
            mock_txs = [
                # (天偏移, 方向, 金额, 描述, 频道)
                (-28, "IN", 12500.00, "TRF FROM ABC TRADING CO LTD", "Mobile"),
                (-25, "OUT", 3200.00, "PAY OFFICE RENT", "ATM"),
                (-22, "IN", 8900.00, "XFER from XYZ Logistics", "Mobile"),
                (-18, "IN", 21000.00, "INWARD REMIT - DELTA SERVICES", "Counter"),
                (-14, "OUT", 4800.00, "BILL PAY - electricity", "AutoDeb"),
                (-10, "IN", 3520.50, "TRF FROM SOMCHAI ENTERPRISE", "Mobile"),
                (-6, "OUT", 7100.00, "PAY VENDOR - office supplies", "Mobile"),
                (-2, "IN", 12500.00, "TRF FROM ABC TRADING", "Mobile"),  # 跟 -28 同金额 · 测多候选
            ]
            for off, direction, amt, desc, channel in mock_txs:
                tx_date = (today + timedelta(days=off)).date()
                cur.execute(
                    """
                    INSERT INTO bank_reconcile_transactions
                        (session_id, user_id, tx_date, direction, amount,
                         description, channel, match_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'unmatched')
                """,
                    (session_id, str(user_id), tx_date, direction, amt, desc, channel),
                )
            return {"ok": True, "session_id": session_id, "tx_count": 8}
    except Exception as e:
        logger.error(f"seed_bank_recon_test_data failed: {e}")
        return {"ok": False, "error": str(e)[:200]}


def clear_bank_recon_test_data(user_id: str) -> int:
    """清掉 skin 名下所有 _MOCK_ 开头的 session(含其下流水/候选 · 走 ON DELETE CASCADE)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                DELETE FROM bank_reconcile_sessions
                WHERE user_id = %s AND source_filename LIKE '_MOCK_%%'
            """,
                (str(user_id),),
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.error(f"clear_bank_recon_test_data failed: {e}")
        return 0
