# -*- coding: utf-8 -*-
"""ERP 端点 + 推送日志 + 重试调度 · 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
ERP endpoint CRUD + push_logs 写/查/统计 + 重试调度(指数退避)+ 用户数据错误
分类器(is_user_data_error)+ adapter/status CHECK 约束幂等扩展。
db.py 文件尾 re-export 对外函数 + 公共常量 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

from core import db

# facade re-export(REFACTOR-WA-B1 · 推送日志查询实现下沉 push_log_queries · db.X/store.X 单一对象不变)
from services.erp.push_log_queries import (  # noqa: F401,E402
    delete_push_logs,
    list_push_logs,
    get_push_log_detail,
    classify_push_exception,
    derive_account_fix,
    derive_bind_fix,
    get_push_stats_today,
)

logger = logging.getLogger(__name__)


def list_erp_endpoints(user_id: str, auto_push_only: bool = False) -> List[Dict[str, Any]]:
    """列出用户的所有 ERP 端点(默认排前面)· auto_push_only=True 时只返回开启自动推且 enabled 的"""
    try:
        with db.get_cursor_rls(user_id=user_id) as cur:
            # ERP-1 修(2026-05-25):SELECT 补 user_id · 此前缺它 → 自动推送(_auto_push_history
            #   用本函数 auto_push_only=True 取端点)拿不到 user_id → tenant_id None → mappings 空
            #   → 误报 ERR_NO_CUSTOMER_MAPPING(手动推送走 get_erp_endpoint 含 user_id 故正常)。
            sql = """
                SELECT id, name, adapter, config, is_default, auto_push, enabled,
                       last_used_at, last_status, success_count, failure_count,
                       created_at, updated_at, user_id
                FROM erp_endpoints
                WHERE user_id = %s
            """
            if auto_push_only:
                sql += " AND auto_push = TRUE AND enabled = TRUE"
            sql += " ORDER BY is_default DESC, created_at ASC"
            cur.execute(sql, (user_id,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_erp_endpoints failed: {e}")
        return []


def get_erp_endpoint(user_id: str, endpoint_id: str) -> Optional[Dict[str, Any]]:
    try:
        with db.get_cursor_rls(user_id=user_id) as cur:
            cur.execute(
                """
                SELECT id, name, adapter, config, is_default, auto_push, enabled,
                       last_used_at, last_status, success_count, failure_count,
                       created_at, updated_at, user_id
                FROM erp_endpoints
                WHERE user_id = %s AND id = %s
                LIMIT 1
            """,
                (user_id, endpoint_id),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_erp_endpoint failed: {e}")
        return None


def get_default_erp_endpoint(user_id: str) -> Optional[Dict[str, Any]]:
    """拿用户默认且启用的端点"""
    try:
        with db.get_cursor_rls(user_id=user_id) as cur:
            cur.execute(
                """
                SELECT id, name, adapter, config, is_default, auto_push, enabled, user_id
                FROM erp_endpoints
                WHERE user_id = %s AND enabled = true
                ORDER BY is_default DESC, created_at ASC
                LIMIT 1
            """,
                (user_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_default_erp_endpoint failed: {e}")
        return None


# v118.34.13 · 暴露 create_erp_endpoint 失败时的具体 DB 错误。
# 路由层在 new_id 为 None 时读这个 module global · 把错误一并写到
# /api/version.last_500_traceback,避免用户看到一片空白。
_last_create_endpoint_error: Optional[str] = None


def _existing_express_id(cur, user_id: str) -> Optional[str]:
    """该用户已有的 express 端点 id(有则复用 · 保 express 单例)。"""
    cur.execute(
        "SELECT id FROM erp_endpoints WHERE user_id = %s AND adapter = 'express' "
        "ORDER BY created_at LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    return str(row["id"]) if row else None


def _disable_other_auto_push(cur, user_id: str, keep_endpoint_id) -> None:
    """自动推送单例(2026-07-01 · 防双推):关掉除 keep 外该用户所有端点的 auto_push。
    与 is_default 单选同思路 · create/update 共用单一实现(单一事实源)。"""
    cur.execute(
        "UPDATE erp_endpoints SET auto_push = false WHERE user_id = %s AND id <> %s",
        (user_id, str(keep_endpoint_id)),
    )


def create_erp_endpoint(
    user_id: str,
    name: str,
    adapter: str,
    config: Dict[str, Any],
    is_default: bool = False,
    auto_push: bool = False,
) -> Optional[str]:
    """创建端点。如果 is_default=True,会自动取消其他端点的默认状态。返回新 id"""
    import json as _json
    import traceback as _tb

    global _last_create_endpoint_error
    is_express = (adapter or "").strip().lower() == "express"
    try:
        with db.get_cursor_rls(user_id=user_id, commit=True) as cur:
            # express 单例:已有就复用,绝不建第二条(向导竞态/多标签会重复 POST)。
            if is_express:
                existing = _existing_express_id(cur, user_id)
                if existing:
                    _last_create_endpoint_error = None
                    return existing
            if is_default:
                cur.execute(
                    "UPDATE erp_endpoints SET is_default = false WHERE user_id = %s", (user_id,)
                )
            cur.execute(
                """
                INSERT INTO erp_endpoints (user_id, name, adapter, config, is_default, auto_push)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                RETURNING id
            """,
                (user_id, name, adapter, _json.dumps(config), is_default, auto_push),
            )
            row = cur.fetchone()
            # 自动推送单例(2026-07-01 Zihao 拍板 · 防双推):同一用户只能有一个端点开自动推
            # → 新端点设自动时,把其它端点的 auto_push 全关掉。手动/停用不受影响。
            if auto_push and row:
                _disable_other_auto_push(cur, user_id, row["id"])
            _last_create_endpoint_error = None
            return str(row["id"]) if row else None
    except Exception as e:
        # 并发越过上面的查重后撞唯一索引 → 复用已存在的 express,不当失败。
        if is_express:
            try:
                with db.get_cursor_rls(user_id=user_id) as cur:
                    existing = _existing_express_id(cur, user_id)
                if existing:
                    _last_create_endpoint_error = None
                    return existing
            except Exception:
                pass
        _last_create_endpoint_error = (
            f"{type(e).__name__}: {str(e)[:200]} | " + _tb.format_exc()[-400:]
        )
        # logger.exception captures the full stack — visible in
        # journalctl. The module global gives the route a short
        # version to surface in the 500 response.
        logger.exception("create_erp_endpoint failed")
        return None


def update_erp_endpoint(user_id: str, endpoint_id: str, **fields) -> bool:
    """支持改 name/config/is_default/auto_push/enabled"""
    import json as _json

    allowed = {"name", "config", "is_default", "auto_push", "enabled"}
    sets = []
    vals = []
    for k, v in fields.items():
        if k not in allowed:
            continue
        if k == "config":
            sets.append("config = %s::jsonb")
            vals.append(_json.dumps(v))
        else:
            sets.append(f"{k} = %s")
            vals.append(v)
    if not sets:
        return False
    try:
        with db.get_cursor_rls(user_id=user_id, commit=True) as cur:
            # 如果设为默认,先取消其他默认
            if fields.get("is_default"):
                cur.execute(
                    "UPDATE erp_endpoints SET is_default = false WHERE user_id = %s AND id <> %s",
                    (user_id, endpoint_id),
                )
            # 自动推送单例(2026-07-01 · 防双推):设自动时先关掉其它端点的 auto_push。
            if fields.get("auto_push"):
                _disable_other_auto_push(cur, user_id, endpoint_id)
            sql = f"UPDATE erp_endpoints SET {', '.join(sets)} WHERE user_id = %s AND id = %s"
            vals.extend([user_id, endpoint_id])
            cur.execute(sql, tuple(vals))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_erp_endpoint failed: {e}")
        return False


def delete_erp_endpoint(user_id: str, endpoint_id: str) -> bool:
    try:
        with db.get_cursor_rls(user_id=user_id, commit=True) as cur:
            # v118.25.0.2 · 删端点前 · 先把这个端点所有挂起的重试停掉(避免 worker 继续跑)
            cur.execute(
                """
                UPDATE erp_push_logs
                SET next_retry_at = NULL
                WHERE user_id = %s AND endpoint_id = %s AND next_retry_at IS NOT NULL
            """,
                (user_id, endpoint_id),
            )
            cur.execute(
                "DELETE FROM erp_endpoints WHERE user_id = %s AND id = %s", (user_id, endpoint_id)
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_endpoint failed: {e}")
        return False


def insert_push_log(
    user_id: str,
    endpoint_id: Optional[str],
    history_id: Optional[str],
    invoice_no: Optional[str],
    seller_name: Optional[str],
    total_amount: Optional[float],
    status: str,
    http_status: Optional[int],
    request_body: Optional[Dict],
    response_body: Optional[str],
    error_msg: Optional[str],
    attempt: int,
    elapsed_ms: int,
    trigger: str = "manual",
) -> Optional[str]:
    import json as _json

    try:
        with db.get_cursor_rls(user_id=user_id, commit=True) as cur:
            cur.execute(
                """
                INSERT INTO erp_push_logs (
                    user_id, endpoint_id, history_id, invoice_no, seller_name,
                    total_amount, status, http_status, request_body, response_body,
                    error_msg, attempt, elapsed_ms, trigger
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    user_id,
                    endpoint_id,
                    history_id,
                    invoice_no,
                    seller_name,
                    total_amount,
                    status,
                    http_status,
                    _json.dumps(request_body) if request_body else None,
                    response_body,
                    error_msg,
                    attempt,
                    elapsed_ms,
                    trigger,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"insert_push_log failed: {e}")
        return None


def has_recent_successful_push(
    history_id: str,
    endpoint_id: str,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """批 2 改动 2 (Zihao 2026-05-19 拍板 · v118.34.34) · 推送去重 check.
    返回最近一次 success log (含 mrerp_bill_no 等)· 没有返 None.

    用于 push_to_endpoint 之前 check:同 history × endpoint 之前已经
    success 过 · 别再推一次 · 写一条 skipped_dup log 静默跳过.

    严格 user_id scope · 防跨账号 false positive.
    """
    if not history_id or not endpoint_id:
        return None
    try:
        with db.get_cursor_rls(user_id=str(user_id)) as cur:
            cur.execute(
                """
                SELECT id, response_body, created_at, invoice_no
                FROM erp_push_logs
                WHERE history_id = %s AND endpoint_id = %s
                  AND user_id = %s AND status = 'success'
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (history_id, endpoint_id, str(user_id)),
            )
            r = cur.fetchone()
            return dict(r) if r else None
    except Exception as e:
        logger.error(f"has_recent_successful_push failed: {e}")
        return None


def update_endpoint_stats(endpoint_id: str, success: bool):
    """推送完成后更新端点的成功/失败计数 + last_used_at + last_status"""
    try:
        with db.get_cursor(commit=True) as cur:
            if success:
                cur.execute(
                    """
                    UPDATE erp_endpoints
                    SET success_count = success_count + 1,
                        last_used_at = NOW(),
                        last_status = 'success'
                    WHERE id = %s
                """,
                    (endpoint_id,),
                )
            else:
                cur.execute(
                    """
                    UPDATE erp_endpoints
                    SET failure_count = failure_count + 1,
                        last_used_at = NOW(),
                        last_status = 'failed'
                    WHERE id = %s
                """,
                    (endpoint_id,),
                )
    except Exception as e:
        logger.error(f"update_endpoint_stats failed: {e}")


def update_history_push_status(history_id: str, status: str):
    """更新 ocr_history 的 last_push_status / last_pushed_at"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE ocr_history
                SET last_pushed_at = NOW(), last_push_status = %s
                WHERE id = %s
            """,
                (status, history_id),
            )
    except Exception as e:
        logger.error(f"update_history_push_status failed: {e}")


# facade re-export(REFACTOR-WA-B2 · 2026-05-29 R17)· 启动期 schema/约束迁移下沉 push_schema ·
# 重试调度/错误分类下沉 push_retry · db.X/store.X/子模块.X 单一对象不变(所有 db.xxx() 调用点零改)。
from services.erp.push_schema import (  # noqa: F401,E402
    ensure_erp_endpoints_adapter_constraint,
    ensure_erp_push_logs_adapter_constraint,
    ensure_erp_push_logs_status_constraint,
    ensure_erp_push_rls,
    ensure_erp_retry_columns,
    ensure_single_express_endpoint,
)
from services.erp.push_retry import (  # noqa: F401,E402
    _ERP_RETRY_DELAYS_SEC,
    ERP_MAX_RETRIES,
    USER_DATA_ERROR_CODES,
    USER_DATA_ERROR_THAI_PATTERNS,
    is_already_pushed_error,
    classify_push_status,
    counts_as_endpoint_success,
    is_user_data_error,
    get_erp_retry_delay_sec,
    schedule_log_retry,
    clear_retry_schedule,
    list_logs_due_for_retry,
    increment_retry_count,
    update_log_status_after_retry,
)
