# -*- coding: utf-8 -*-
"""ERP 端点 + 推送日志 + 重试调度 · 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
ERP endpoint CRUD + push_logs 写/查/统计 + 重试调度(指数退避)+ 用户数据错误
分类器(is_user_data_error)+ adapter/status CHECK 约束幂等扩展。
db.py 文件尾 re-export 对外函数 + 公共常量 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

import db
from services.erp.external_ref import derive_external_ref

logger = logging.getLogger(__name__)


def list_erp_endpoints(user_id: str, auto_push_only: bool = False) -> List[Dict[str, Any]]:
    """列出用户的所有 ERP 端点(默认排前面)· auto_push_only=True 时只返回开启自动推且 enabled 的"""
    try:
        with db.get_cursor() as cur:
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
        with db.get_cursor() as cur:
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
        with db.get_cursor() as cur:
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
    try:
        with db.get_cursor(commit=True) as cur:
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
            _last_create_endpoint_error = None
            return str(row["id"]) if row else None
    except Exception as e:
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
        with db.get_cursor(commit=True) as cur:
            # 如果设为默认,先取消其他默认
            if fields.get("is_default"):
                cur.execute(
                    "UPDATE erp_endpoints SET is_default = false WHERE user_id = %s AND id <> %s",
                    (user_id, endpoint_id),
                )
            sql = f"UPDATE erp_endpoints SET {', '.join(sets)} WHERE user_id = %s AND id = %s"
            vals.extend([user_id, endpoint_id])
            cur.execute(sql, tuple(vals))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_erp_endpoint failed: {e}")
        return False


def delete_erp_endpoint(user_id: str, endpoint_id: str) -> bool:
    try:
        with db.get_cursor(commit=True) as cur:
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
        with db.get_cursor(commit=True) as cur:
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
        with db.get_cursor() as cur:
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


# ============================================================
# v118.25 · ERP 推送失败自动重试(指数退避)
# ============================================================
def ensure_erp_endpoints_adapter_constraint():
    """v118.34.14 (Zihao 2026-05-19 拍板) · erp_endpoints 的 adapter CHECK
    constraint 之前只列 webhook / xero / flowaccount · MR.ERP 集成代码上线
    时漏写 schema migration · 创建 endpoint 时 PostgreSQL 抛 CheckViolation
    导致 POST /api/erp/endpoints 500("erp_endpoints_adapter_chk violated")。

    这个函数:
      1. 从 pg_catalog 查现存 CHECK 约束(若有)· 不靠固定名字
      2. drop 旧约束 + 加新约束 · adapter 白名单加 'mrerp'
      3. 幂等 — 已经包含 'mrerp' 时跳过

    白名单跟 erp_push.py ADAPTER_REGISTRY 对齐 · 增 adapter 时这里和
    那里一起改。
    """
    canonical = ("webhook", "xero", "flowaccount", "mrerp")
    try:
        with db.get_cursor(commit=True) as cur:
            # 1. 找 adapter 上现存的 CHECK constraint(可能没有 · 也可能多个)
            cur.execute("""
                SELECT con.conname, pg_get_constraintdef(con.oid) AS def
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = 'erp_endpoints'
                  AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) ILIKE '%adapter%'
            """)
            rows = cur.fetchall() or []
            current_def = " ".join((r["def"] or "").lower() for r in rows)
            # 2. 已经包含 'mrerp' 就不动 — 幂等
            if "'mrerp'" in current_def:
                logger.info("✅ erp_endpoints adapter CHECK already includes mrerp (skip)")
                return
            # 3. drop 所有现存 adapter-related CHECK,然后建新的
            for r in rows:
                name = r["conname"]
                cur.execute(f"ALTER TABLE erp_endpoints DROP CONSTRAINT IF EXISTS " f"{name}")
                logger.info("[migration] dropped old erp_endpoints CHECK: %s", name)
            # 4. 建新约束 · 名字回归 canonical
            in_list = ", ".join(f"'{a}'" for a in canonical)
            cur.execute(
                f"ALTER TABLE erp_endpoints "
                f"ADD CONSTRAINT erp_endpoints_adapter_chk "
                f"CHECK (adapter IN ({in_list}))"
            )
            logger.info(
                "✅ erp_endpoints adapter CHECK rewritten · whitelist=%s",
                canonical,
            )
    except Exception:
        logger.exception("ensure_erp_endpoints_adapter_constraint failed")
        # 不抛 · 让启动继续 · 但下一次创建 mrerp endpoint 仍会 500 ·
        # 现场会进 last_500 traceback · 操作者能拿到。


def ensure_erp_push_logs_adapter_constraint():
    """同 erp_endpoints 但针对 erp_push_logs · 若它也有 adapter CHECK
    约束就同步加 mrerp。push log 表不一定带这个约束(取决于建表 DDL),
    所以查 pg_catalog 找到了再 drop+rebuild,没找到就跳过。"""
    canonical = ("webhook", "xero", "flowaccount", "mrerp")
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT con.conname, pg_get_constraintdef(con.oid) AS def
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = 'erp_push_logs'
                  AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) ILIKE '%adapter%'
            """)
            rows = cur.fetchall() or []
            if not rows:
                logger.info("ℹ erp_push_logs has no adapter CHECK constraint (nothing to migrate)")
                return
            current_def = " ".join((r["def"] or "").lower() for r in rows)
            if "'mrerp'" in current_def:
                logger.info("✅ erp_push_logs adapter CHECK already includes mrerp (skip)")
                return
            for r in rows:
                name = r["conname"]
                cur.execute(f"ALTER TABLE erp_push_logs DROP CONSTRAINT IF EXISTS " f"{name}")
                logger.info("[migration] dropped old erp_push_logs CHECK: %s", name)
            in_list = ", ".join(f"'{a}'" for a in canonical)
            cur.execute(
                f"ALTER TABLE erp_push_logs "
                f"ADD CONSTRAINT erp_push_logs_adapter_chk "
                f"CHECK (adapter IN ({in_list}))"
            )
            logger.info(
                "✅ erp_push_logs adapter CHECK rewritten · whitelist=%s",
                canonical,
            )
    except Exception:
        logger.exception("ensure_erp_push_logs_adapter_constraint failed")


def ensure_erp_push_logs_status_constraint():
    """ERP-2 修(2026-05-25):若 erp_push_logs.status 有 CHECK 约束且不含 'skipped_dup' ·
    drop + rebuild 放开。此前重复推送写 status='skipped_dup' 被约束拒绝 → insert 抛异常被
    insert_push_log 吞 → 返回 None → 防重日志没落库(log_id=null)。没有该约束则跳过(无需迁移)。"""
    canonical = ("success", "failed", "skipped_dup", "pending", "retrying")
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT con.conname, pg_get_constraintdef(con.oid) AS def
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = 'erp_push_logs'
                  AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) ILIKE '%status%'
            """)
            rows = cur.fetchall() or []
            if not rows:
                logger.info(
                    "ℹ erp_push_logs has no status CHECK constraint (skipped_dup OK · skip)"
                )
                return
            current_def = " ".join((r["def"] or "").lower() for r in rows)
            if "skipped_dup" in current_def:
                logger.info("✅ erp_push_logs status CHECK already includes skipped_dup (skip)")
                return
            for r in rows:
                name = r["conname"]
                cur.execute(f"ALTER TABLE erp_push_logs DROP CONSTRAINT IF EXISTS {name}")
                logger.info("[migration] dropped old erp_push_logs status CHECK: %s", name)
            in_list = ", ".join(f"'{s}'" for s in canonical)
            cur.execute(
                f"ALTER TABLE erp_push_logs "
                f"ADD CONSTRAINT erp_push_logs_status_chk "
                f"CHECK (status IN ({in_list}))"
            )
            logger.info("✅ erp_push_logs status CHECK rewritten · whitelist=%s", canonical)
    except Exception:
        logger.exception("ensure_erp_push_logs_status_constraint failed")


def ensure_erp_retry_columns():
    """启动时给 erp_push_logs 表加 retry 相关列 · 幂等(列已存在则跳过)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 3;
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ NULL;
                CREATE INDEX IF NOT EXISTS idx_erp_logs_retry_due
                    ON erp_push_logs(next_retry_at)
                    WHERE next_retry_at IS NOT NULL AND status = 'failed';
            """)
            logger.info("✅ erp_push_logs retry 列就绪(retry_count / max_retries / next_retry_at)")
    except Exception as e:
        logger.warning(f"ensure_erp_retry_columns failed: {e}")


# 指数退避序列(秒):60s · 5min · 30min · 共 3 次
_ERP_RETRY_DELAYS_SEC = [60, 300, 1800]
ERP_MAX_RETRIES = 3

# 批 1 改动 3 (Zihao 2026-05-19 拍板 · v118.34.33) · 用户数据错不 retry.
# 这些错 retry 没意义 · 用户数据没改之前再推还是失败 · 污染重试队列 +
# 用户看到一堆 "已重试 1/3 · 2 分钟后再试" 噪音.
# 区分:
#   - 用户数据错 → 不入 retry · status 留 'failed' · 用户看到时主动处理
#   - 技术错 (网络/timeout/session) → retry 3 次 (60s/5min/30min)
USER_DATA_ERROR_CODES = {
    "ERR_NO_CLIENT",
    "ERR_NO_CUSTOMER_MAPPING",
    "ERR_NO_INVOICE_NO",
    "ERR_NO_INVOICE_DATE",
    "ERR_NO_TOTAL_AMOUNT",
    "ERR_NEGATIVE_AMOUNT",
    "ERR_TAX_ID_INVALID",
    "ERR_DATE_FUTURE",
    "ERR_INVOICE_NO_TOO_LONG",
    "ERR_BILL_NO_TOO_LONG",
    "ERR_CUSTOMER_CODE_TOO_LONG",
    "ERR_NO_SEED_CUSTOMER",
    "ERR_NO_SEED_PRODUCT",
    # MR.ERP duplicate · 重推还是同一个 bill_no · 没意义
    "ERR_DUPLICATE_INVOICE",
    # Fail-safe 名字复核不匹配(Zihao 2026-05-26 拍板 · P1)· 用户得先改映射 ·
    # 重推同样不匹配 · 不入 retry。注:ERR_*_VERIFY_UNAVAILABLE(网络/超时无法确认)
    # 故意不在此 set · 属技术错 · 走 retry 队列(但永远不显示 success)。
    "ERR_CUSTOMER_NAME_MISMATCH",
    "ERR_PRODUCT_NAME_MISMATCH",
}

# Thai raw error patterns that map to user-data errors (报错可能直接是 raw 泰文)
USER_DATA_ERROR_THAI_PATTERNS = (
    "เลขที่ดังกล่าวมีอยู่ในระบบแล้ว",  # duplicate
    "เลขที่เอกสารซ้ำ",  # duplicate
    "ไม่พบข้อมูลรหัสลูกค้า",  # customer mapping missing
    "ลูกค้าไม่ระบุ",  # client missing
    "เลขที่ต้องไม่เกิน",  # length limit
)


# P2-D(Zihao 2026-05-27 拍板 · B8)· MR.ERP 返「发票号已存在/已推过」不是失败 ·
# 是「已推送过」中性态(skipped_dup)· 不红叉、不计失败、不入重试。
# 两种 MR.ERP 文案 + 我方 ERR_DUPLICATE_INVOICE 码都算。
_ALREADY_PUSHED_THAI_PATTERNS = (
    "เลขที่ดังกล่าวมีอยู่ในระบบแล้ว",  # 该号已存在系统
    "เลขที่เอกสารซ้ำ",  # 单据号重复
)


def is_already_pushed_error(error_msg: Optional[str]) -> bool:
    """这条「失败」其实是「发票号已存在/之前已推过」吗?是 → 应记为 skipped_dup 中性态。"""
    if not error_msg:
        return False
    s = str(error_msg)
    if "ERR_DUPLICATE_INVOICE" in s:
        return True
    for pat in _ALREADY_PUSHED_THAI_PATTERNS:
        if pat in s:
            return True
    return False


def classify_push_status(success: bool, error_msg: Optional[str]) -> str:
    """推送结果 → 单一权威 status(铁律 #12)。
    success → 'success';「发票号已存在」→ 'skipped_dup'(中性·已推送过);其余 → 'failed'。
    """
    if success:
        return "success"
    if is_already_pushed_error(error_msg):
        return "skipped_dup"
    return "failed"


def is_user_data_error(error_msg: Optional[str]) -> bool:
    """判断这条错误是不是"用户数据错"(不应该 retry).
    匹配 ERR_* code 前缀 OR 已知泰文 raw 模式.
    """
    if not error_msg:
        return False
    s = str(error_msg)
    # 任一 ERR_* code 命中
    for code in USER_DATA_ERROR_CODES:
        if code in s:
            return True
    # 任一已知泰文模式命中
    for pat in USER_DATA_ERROR_THAI_PATTERNS:
        if pat in s:
            return True
    return False


def get_erp_retry_delay_sec(retry_count: int) -> Optional[int]:
    """根据已重试次数返回下次重试延迟(秒)· 超过最大次数返回 None"""
    if retry_count < 0 or retry_count >= ERP_MAX_RETRIES:
        return None
    if retry_count >= len(_ERP_RETRY_DELAYS_SEC):
        return _ERP_RETRY_DELAYS_SEC[-1]
    return _ERP_RETRY_DELAYS_SEC[retry_count]


def schedule_log_retry(log_id: str, delay_sec: int) -> bool:
    """把一条失败日志加入重试队列 · next_retry_at = NOW + delay"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_push_logs
                SET next_retry_at = NOW() + (%s * INTERVAL '1 second')
                WHERE id = %s AND status = 'failed'
            """,
                (int(delay_sec), log_id),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"schedule_log_retry failed: {e}")
        return False


def clear_retry_schedule(log_id: str):
    """重试成功 / 达到上限后调用 · 清空 next_retry_at(从队列里摘出来)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_push_logs
                SET next_retry_at = NULL
                WHERE id = %s
            """,
                (log_id,),
            )
    except Exception as e:
        logger.error(f"clear_retry_schedule failed: {e}")


def list_logs_due_for_retry(limit: int = 20) -> List[Dict[str, Any]]:
    """找到当下到期需要重试的失败日志 · 按到期时间正序"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT l.id, l.user_id, l.endpoint_id, l.history_id,
                       l.invoice_no, l.seller_name, l.total_amount,
                       l.retry_count, l.max_retries, l.next_retry_at
                FROM erp_push_logs l
                WHERE l.status = 'failed'
                  AND l.next_retry_at IS NOT NULL
                  AND l.next_retry_at <= NOW()
                  AND l.retry_count < l.max_retries
                ORDER BY l.next_retry_at ASC
                LIMIT %s
            """,
                (int(limit),),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_logs_due_for_retry failed: {e}")
        return []


def increment_retry_count(log_id: str) -> int:
    """重试一次后自增 retry_count · 返回新值"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_push_logs
                SET retry_count = retry_count + 1
                WHERE id = %s
                RETURNING retry_count
            """,
                (log_id,),
            )
            row = cur.fetchone()
            return int(row["retry_count"]) if row else 0
    except Exception as e:
        logger.error(f"increment_retry_count failed: {e}")
        return 0


def update_log_status_after_retry(
    log_id: str,
    success: bool,
    http_status: Optional[int],
    response_body: Optional[str],
    error_msg: Optional[str],
    elapsed_ms: int,
    request_body: Optional[Any] = None,
    final_status: Optional[str] = None,
):
    """更新原 log 的 status / http_status / response(不写新行)。
    重试完成调用;也用于把识别后立刻写的「pending(推送中)」行落定成
    success/failed(2026-05-26)。request_body 仅在传入时覆盖(retry 不传 → 保留原值)。
    P2-D(2026-05-27):final_status 传入时直接用它(支持 'skipped_dup' 中性态);
    不传则沿用 success→'success'/'failed' 老映射(向后兼容所有现有调用)。"""
    import json as _json

    status = final_status if final_status else ("success" if success else "failed")
    try:
        rb = None
        if request_body is not None:
            rb = (
                request_body
                if isinstance(request_body, str)
                else _json.dumps(request_body, ensure_ascii=False)
            )
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_push_logs
                SET status = %s,
                    http_status = %s,
                    response_body = %s,
                    error_msg = %s,
                    elapsed_ms = %s,
                    request_body = COALESCE(%s::jsonb, request_body)
                WHERE id = %s
            """,
                (
                    status,
                    http_status,
                    response_body,
                    error_msg,
                    int(elapsed_ms),
                    rb,
                    log_id,
                ),
            )
    except Exception as e:
        logger.error(f"update_log_status_after_retry failed: {e}")


def delete_push_logs(user_id: str, log_ids: List[str]) -> int:
    """Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除推送日志.
    严格 user_id scope · 不许跨账号删除 · 返回真删除的行数."""
    if not log_ids:
        return 0
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_push_logs WHERE user_id = %s AND id = ANY(%s::uuid[])",
                (user_id, list(log_ids)),
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.error(f"delete_push_logs failed: {e}")
        return 0


def list_push_logs(
    user_id: str,
    history_id: Optional[str] = None,
    endpoint_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    trigger_filter: Optional[str] = None,
    adapter_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """查询推送日志,支持按 history/endpoint/status/trigger/adapter 过滤

    批 3 改动 6 (Zihao 2026-05-19 拍板 · v118.34.34) · 新增 adapter_filter.
    按 erp_endpoints.adapter (mrerp/xero/webhook 等) 过滤. 已删除的 endpoint
    join 不到 row (endpoint_adapter is NULL),自动不命中任何 adapter filter,
    符合预期 (用户筛 "MR.ERP" 不会带出已删 endpoint 的孤儿 log).
    """
    try:
        with db.get_cursor() as cur:
            where = ["user_id = %s"]
            params: list = [user_id]
            if history_id:
                where.append("history_id = %s")
                params.append(history_id)
            if endpoint_id:
                where.append("endpoint_id = %s")
                params.append(endpoint_id)
            if status_filter == "success":
                where.append("status = 'success'")
            elif status_filter == "retrying":
                # v118.25.1 · 重试中:failed + 仍在重试队列里(next_retry_at 未来/未清)
                where.append("status = 'failed' AND next_retry_at IS NOT NULL")
            elif status_filter == "failed":
                # v118.25.1 · 失败终态:failed + 不在重试队列(已耗尽 / 端点删 / 用户手动停)
                where.append("status = 'failed' AND next_retry_at IS NULL")
            if trigger_filter in ("manual", "auto"):
                where.append("trigger = %s")
                params.append(trigger_filter)
            where_sql = " AND ".join(where)
            # 批 1 改动 5/8 (Zihao 2026-05-19 拍板 · v118.34.33) · JOIN clients
            # 拿 Pearnly 客户名 (改动 5) + JOIN erp_endpoints 拿 endpoint
            # name (改动 8). where_sql 字段全部 prefix 成 l.* 防 join 后 ambig.
            joined_where = (
                where_sql.replace("user_id = %s", "l.user_id = %s")
                .replace("history_id = %s", "l.history_id = %s")
                .replace("endpoint_id = %s", "l.endpoint_id = %s")
                .replace("status = 'success'", "l.status = 'success'")
                .replace(
                    "status = 'failed' AND next_retry_at IS NOT NULL",
                    "l.status = 'failed' AND l.next_retry_at IS NOT NULL",
                )
                .replace(
                    "status = 'failed' AND next_retry_at IS NULL",
                    "l.status = 'failed' AND l.next_retry_at IS NULL",
                )
                .replace("trigger = %s", "l.trigger = %s")
            )
            # 批 3 改动 6 · adapter filter · 走 JOIN 后的 e.adapter (e 是 endpoint).
            # NULL-safe: LOWER(e.adapter) = LOWER(%s) 自动滤掉孤儿 log.
            if adapter_filter:
                joined_where += " AND LOWER(e.adapter) = LOWER(%s)"
                params.append(adapter_filter)

            # COUNT 必须跟主查询走相同 JOIN · 因为 joined_where 可能引用 e.adapter.
            cur.execute(
                f"""SELECT COUNT(*) AS n FROM erp_push_logs l
                    LEFT JOIN ocr_history h ON h.id = l.history_id
                    LEFT JOIN clients c ON c.id = h.client_id
                    LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                    WHERE {joined_where}""",
                tuple(params),
            )
            total = cur.fetchone()["n"]
            cur.execute(
                f"""
                SELECT l.id, l.endpoint_id, l.history_id, l.invoice_no,
                       l.seller_name, l.total_amount, l.status, l.http_status,
                       l.error_msg, l.attempt, l.elapsed_ms, l.trigger,
                       l.created_at, l.retry_count, l.max_retries,
                       l.next_retry_at, l.response_body,
                       h.client_id AS history_client_id,
                       c.name AS client_name,
                       COALESCE((
                           SELECT pg->'fields'->>'buyer_name'
                           FROM jsonb_array_elements(
                               CASE WHEN jsonb_typeof(h.pages)='array'
                                    THEN h.pages ELSE '[]'::jsonb END
                           ) pg
                           WHERE COALESCE(pg->'fields'->>'buyer_name','') <> ''
                           LIMIT 1
                       ), '') AS ocr_buyer_name,
                       e.name AS endpoint_name,
                       e.adapter AS endpoint_adapter,
                       w.name AS workspace_name
                FROM erp_push_logs l
                LEFT JOIN ocr_history h ON h.id = l.history_id
                LEFT JOIN clients c ON c.id = h.client_id
                LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                LEFT JOIN workspace_clients w ON w.id = h.workspace_client_id
                WHERE {joined_where}
                ORDER BY l.created_at DESC
                LIMIT %s OFFSET %s
            """,
                tuple(params) + (limit, offset),
            )
            items = [dict(r) for r in cur.fetchall()]
            # 临时任务 (Zihao 2026-05-26) · 在日志 API 层派生通用 ERP 单号字段
            # (external_doc_no/external_doc_id/external_url + adapter 提示码)。
            # 不动状态机 · 不新增状态源 · 仅从已有 response_body+adapter 读出。
            # 派生后丢掉原始 response_body · 列表 payload 保持轻量(详情接口才回完整体)。
            for it in items:
                ref = derive_external_ref(
                    it.get("endpoint_adapter"), it.pop("response_body", None), it.get("status")
                )
                it.update(ref)
            return {"items": items, "total": total}
    except Exception as e:
        logger.error(f"list_push_logs failed: {e}")
        return {"items": [], "total": 0}


def get_push_log_detail(user_id: str, log_id: str) -> Optional[Dict[str, Any]]:
    """单条推送日志完整详情(含 request_body / response_body)

    临时任务 (Zihao 2026-05-26) · JOIN endpoints 拿 adapter + name,JOIN clients
    拿 Pearnly 客户/买方名,供凭证弹窗显示;并派生通用 ERP 单号字段
    (external_doc_no/external_doc_id/external_url + adapter 提示码)。
    response_body 在详情接口里保留(弹窗"技术详情"折叠区要看原始体)。
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT l.id, l.endpoint_id, l.history_id, l.invoice_no, l.seller_name,
                       l.total_amount, l.status, l.http_status,
                       l.request_body, l.response_body, l.error_msg,
                       l.attempt, l.elapsed_ms, l.trigger, l.created_at,
                       l.retry_count, l.max_retries, l.next_retry_at,
                       h.client_id AS history_client_id,
                       c.name AS client_name,
                       COALESCE((
                           SELECT pg->'fields'->>'buyer_name'
                           FROM jsonb_array_elements(
                               CASE WHEN jsonb_typeof(h.pages)='array'
                                    THEN h.pages ELSE '[]'::jsonb END
                           ) pg
                           WHERE COALESCE(pg->'fields'->>'buyer_name','') <> ''
                           LIMIT 1
                       ), '') AS ocr_buyer_name,
                       e.name AS endpoint_name,
                       e.adapter AS endpoint_adapter
                FROM erp_push_logs l
                LEFT JOIN ocr_history h ON h.id = l.history_id
                LEFT JOIN clients c ON c.id = h.client_id
                LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                WHERE l.id = %s AND l.user_id = %s
            """,
                (log_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            detail = dict(row)
            ref = derive_external_ref(
                detail.get("endpoint_adapter"), detail.get("response_body"), detail.get("status")
            )
            detail.update(ref)
            return detail
    except Exception as e:
        logger.error(f"get_push_log_detail failed: {e}")
        return None


def classify_push_exception(error_msg: Optional[str]) -> str:
    """把 ERP 推送失败错误码归到异常子类(前端 chip 用 · 通用 · 不写死 MR.ERP)。"""
    msg = error_msg or ""
    if "ERR_CUSTOMER_NAME_MISMATCH" in msg or "ERR_NO_CUSTOMER_MAPPING" in msg:
        return "customer_mismatch"
    if "ERR_PRODUCT_NAME_MISMATCH" in msg:
        return "product_mismatch"
    if "ERR_NO_CLIENT" in msg:
        return "no_client"
    if "VERIFY_UNAVAILABLE" in msg:
        return "verify_unavailable"
    return "other"


def list_push_exceptions(
    user_id: str,
    q: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """ERP 推送异常队列(派生自 erp_push_logs · 铁律 #12 单一状态源,不另立异常表)。

    取每个 (history, endpoint) **最近一条** log · 仅保留 status='failed'(已被后续
    success/skipped_dup 解决的自动排除)。每条附:
      - state:batch_view 派生展示态(needs_action / retrying / failed)
      - category:错误码子类(customer_mismatch / product_mismatch / no_client /
        verify_unavailable / other)· 前端 chip 用
      - 发票号 / 发票卖方(seller_name)/ 发票买方(ocr_buyer_name)/ 已归属 Pearnly 客户
        / ERP 端点名 / 错误码 / 原始 error_msg(前端转友好文案)

    支持搜索(q:发票号/卖方/买方 模糊)+ category 过滤 + 分页(limit/offset)。
    返回 {items: 当前页, total: 过滤后总数, categories: 各子类计数(供 chip)}。
    通用层只认统一状态 + 错误码,不写 if adapter=='mrerp'。
    """
    from services.erp import batch_view
    import re as _re

    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (l.history_id, l.endpoint_id)
                    l.id, l.history_id, l.endpoint_id, l.invoice_no, l.seller_name,
                    l.total_amount, l.status, l.error_msg, l.created_at,
                    l.retry_count, l.max_retries, l.next_retry_at,
                    h.client_id AS history_client_id,
                    c.name AS client_name,
                    COALESCE((
                        SELECT pg->'fields'->>'buyer_name'
                        FROM jsonb_array_elements(
                            CASE WHEN jsonb_typeof(h.pages)='array'
                                 THEN h.pages ELSE '[]'::jsonb END
                        ) pg
                        WHERE COALESCE(pg->'fields'->>'buyer_name','') <> ''
                        LIMIT 1
                    ), '') AS ocr_buyer_name,
                    e.name AS endpoint_name, e.adapter AS endpoint_adapter
                FROM erp_push_logs l
                LEFT JOIN ocr_history h ON h.id = l.history_id
                LEFT JOIN clients c ON c.id = h.client_id
                LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                WHERE l.user_id = %s
                ORDER BY l.history_id, l.endpoint_id, l.created_at DESC
                """,
                (str(user_id),),
            )
            rows = [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.error(f"list_push_exceptions failed: {e}")
        return {"items": [], "total": 0, "categories": {}}

    # 1) 仅留最近一条仍 failed 的(已解决的自动排除)+ 附 state/category/code
    base: List[Dict[str, Any]] = []
    for r in rows:
        if (r.get("status") or "") != "failed":
            continue
        r["state"] = batch_view.classify_push_log(r)
        r["category"] = classify_push_exception(r.get("error_msg"))
        m = _re.search(r"ERR_[A-Z0-9_]+", r.get("error_msg") or "")
        r["error_code"] = m.group(0) if m else ""
        base.append(r)

    # 2) 搜索(发票号/卖方/买方 · 大小写不敏感)
    qq = (q or "").strip().lower()
    if qq:
        base = [
            r
            for r in base
            if qq in (r.get("invoice_no") or "").lower()
            or qq in (r.get("seller_name") or "").lower()
            or qq in (r.get("ocr_buyer_name") or "").lower()
        ]

    # 3) category 计数(搜索后 · 过滤前 → chip 显当前搜索范围内各子类数)
    categories: Dict[str, int] = {}
    for r in base:
        c = r.get("category") or "other"
        categories[c] = categories.get(c, 0) + 1

    # 4) category 过滤 + 按时间倒序 + 分页
    if category:
        base = [r for r in base if (r.get("category") or "other") == category]
    base.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    total = len(base)
    off = max(0, int(offset or 0))
    lim = max(1, min(int(limit or 50), 200))
    page = base[off : off + lim]
    return {"items": page, "total": total, "categories": categories}


def get_push_stats_today(user_id: str) -> Dict[str, Any]:
    """今日推送统计(总数 · 成功 · 失败)"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status='success') AS success,
                    COUNT(*) FILTER (WHERE status='failed') AS failed,
                    COUNT(*) FILTER (WHERE trigger='auto') AS auto_cnt
                FROM erp_push_logs
                WHERE user_id = %s
                  AND created_at >= CURRENT_DATE
            """,
                (user_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0}
    except Exception as e:
        logger.error(f"get_push_stats_today failed: {e}")
        return {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0}
