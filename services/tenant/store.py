# -*- coding: utf-8 -*-
"""账套/租户管理(超管后台 · tenants 表 + owner users)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
覆盖:租户查询/创建/配额/状态/用量 + owner 用户列表/创建 + 级联删除预览/执行。
所有游标访问走 db.get_cursor(...) · 跨域 db 函数(find_user_by_username 等)走 db.* 调用 ·
确保测试可 mock.patch("db.get_cursor") / mock.patch("db.find_user_by_username")。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

import bcrypt as _bcrypt

import db

logger = logging.getLogger(__name__)


def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    """根据 tenant_id 查租户信息"""
    if not tenant_id:
        return None
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT * FROM tenants WHERE id = %s LIMIT 1",
                (str(tenant_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_tenant failed (id={tenant_id}): {e}")
        return None


def get_user_tenant(user_id: str) -> Optional[Dict[str, Any]]:
    """根据 user_id 查他所属的租户信息"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT t.*
                FROM tenants t
                JOIN users u ON u.tenant_id = t.id
                WHERE u.id = %s
                LIMIT 1
            """,
                (str(user_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_user_tenant failed (user_id={user_id}): {e}")
        return None


def list_all_tenants(limit: int = 200) -> List[Dict[str, Any]]:
    """
    超级管理员用 · 列出所有租户 + 每家当前用户数 + 用量概况
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.*,
                    (SELECT COUNT(*) FROM users WHERE tenant_id = t.id) AS actual_member_count,
                    (SELECT COUNT(*) FROM ocr_history oh
                      JOIN users u ON u.id = oh.user_id
                     WHERE u.tenant_id = t.id
                       AND oh.created_at >= DATE_TRUNC('month', NOW())
                    ) AS ocr_this_month
                FROM tenants t
                ORDER BY t.created_at DESC
                LIMIT %s
            """,
                (int(limit),),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_all_tenants failed: {e}")
        return []


def create_tenant(
    name: str,
    owner_user_id: Optional[str] = None,
    tenant_type: str = "shared_api",
    monthly_quota: int = 100,
    notes: Optional[str] = None,
) -> Optional[str]:
    """
    超级管理员用 · 创建一个新租户
    tenant_type:
        'shared_api' = 月付 · 共用系统 Gemini key
        'byo_api'    = 买断 · 用户自带 Gemini key
        'admin'      = 超级管理员租户
    返回新建 tenant 的 id · 失败返回 None
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO tenants (
                    name, owner_user_id, tenant_type,
                    monthly_quota, used_this_month, status,
                    notes, member_count
                ) VALUES (
                    %s, %s, %s,
                    %s, 0, 'active',
                    %s, 0
                )
                RETURNING id
            """,
                (
                    name,
                    str(owner_user_id) if owner_user_id else None,
                    tenant_type,
                    int(monthly_quota) if monthly_quota else 0,
                    notes,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_tenant failed (name={name}): {e}")
        return None


def update_tenant_quota(tenant_id: str, monthly_quota: int) -> bool:
    """
    超级管理员用 · 改租户月度限额
    传 0 = 不限额(买断类 tenant 用)
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE tenants SET monthly_quota = %s, updated_at = NOW() WHERE id = %s",
                (int(monthly_quota), str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_tenant_quota failed: {e}")
        return False


def update_tenant_status(tenant_id: str, status: str) -> bool:
    """
    超级管理员用 · 改租户状态
    可选:active / warning / suspended / frozen
    """
    if status not in ("active", "warning", "suspended", "frozen"):
        logger.warning(f"update_tenant_status 无效状态: {status}")
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE tenants SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_tenant_status failed: {e}")
        return False


def get_tenant_monthly_usage(tenant_id: str) -> Dict[str, Any]:
    """
    查租户当月用量(跨月显示层重置)
    返回 { used, quota, remaining, percent }
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT monthly_quota, used_this_month, quota_reset_at
                FROM tenants WHERE id = %s LIMIT 1
            """,
                (str(tenant_id),),
            )
            row = cur.fetchone()
            if not row:
                return {"used": 0, "quota": 0, "remaining": 0, "percent": 0}

            quota = int(row["monthly_quota"] or 0)
            used = int(row["used_this_month"] or 0)

            # 跨月显示层检查
            reset_at = row.get("quota_reset_at")
            from datetime import date

            today = date.today()
            if reset_at and hasattr(reset_at, "year"):
                if reset_at.year != today.year or reset_at.month != today.month:
                    used = 0

            remaining = max(quota - used, 0) if quota > 0 else -1  # -1 = 不限
            percent = round(used / quota * 100, 1) if quota > 0 else 0
            return {
                "used": used,
                "quota": quota,
                "remaining": remaining,
                "percent": percent,
            }
    except Exception as e:
        logger.error(f"get_tenant_monthly_usage failed: {e}")
        return {"used": 0, "quota": 0, "remaining": 0, "percent": 0}


def increment_tenant_monthly_usage(tenant_id: str, n: int = 1) -> int:
    """
    租户级配额累加 · 跨月自动重置
    返回最新 used_this_month · 失败返回 -1
    """
    if not tenant_id:
        return -1
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE tenants SET
                    used_this_month = CASE
                        WHEN quota_reset_at IS NULL
                          OR quota_reset_at < DATE_TRUNC('month', NOW())::date
                        THEN %s
                        ELSE COALESCE(used_this_month, 0) + %s
                    END,
                    quota_reset_at = DATE_TRUNC('month', NOW())::date,
                    last_active_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING used_this_month
            """,
                (n, n, str(tenant_id)),
            )
            row = cur.fetchone()
            return int(row["used_this_month"]) if row else -1
    except Exception as e:
        logger.warning(f"increment_tenant_monthly_usage failed (id={tenant_id}): {e}")
        return -1


def list_tenant_members(tenant_id: str) -> List[Dict[str, Any]]:
    """
    列出某租户的所有用户(老板 + 员工)
    超管后台 / 租户管理页用
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, username, email, role, is_active, is_super_admin,
                       last_login_at, created_at, invited_by
                FROM users
                WHERE tenant_id = %s
                ORDER BY
                    CASE WHEN role = 'owner' THEN 0 ELSE 1 END,
                    created_at ASC
            """,
                (str(tenant_id),),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_tenant_members failed (tenant_id={tenant_id}): {e}")
        return []


def get_tenant_usage_summary(tenant_id: str) -> Dict[str, Any]:
    """
    租户运营面板用 · 返回完整概况
    - 配额 / 用量 / 剩余 / 百分比
    - 本月识别数
    - 用户数
    - 最近活跃
    """
    try:
        quota = get_tenant_monthly_usage(tenant_id)

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM users WHERE tenant_id = %s) AS user_count,
                    (SELECT COUNT(*) FROM ocr_history oh
                      JOIN users u ON u.id = oh.user_id
                     WHERE u.tenant_id = %s
                       AND oh.created_at >= DATE_TRUNC('month', NOW())
                    ) AS ocr_this_month,
                    (SELECT MAX(last_login_at) FROM users WHERE tenant_id = %s) AS last_login
            """,
                (str(tenant_id), str(tenant_id), str(tenant_id)),
            )
            stats = cur.fetchone()

        return {
            "quota": quota,
            "user_count": stats["user_count"] if stats else 0,
            "ocr_this_month": stats["ocr_this_month"] if stats else 0,
            "last_login": (
                stats["last_login"].isoformat() if stats and stats.get("last_login") else None
            ),
        }
    except Exception as e:
        logger.error(f"get_tenant_usage_summary failed: {e}")
        return {
            "quota": {"used": 0, "quota": 0, "remaining": 0, "percent": 0},
            "user_count": 0,
            "ocr_this_month": 0,
            "last_login": None,
        }


def list_all_owner_users(limit: int = 200) -> List[Dict[str, Any]]:
    """
    超管用 · 列所有 owner 用户(每个对应一家公司)
    返回含:用户名 / 公司名称 / 类型 / 配额 / 用量 / 员工数 / 状态
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.id AS user_id,
                    u.username,
                    u.company_name,
                    u.is_active,
                    u.is_super_admin,
                    u.last_login_at,
                    u.created_at,
                    t.id AS tenant_id,
                    t.name AS tenant_name,
                    t.tenant_type,
                    t.status AS tenant_status,
                    t.monthly_quota,
                    t.used_this_month,
                    (SELECT COUNT(*) FROM users u2 WHERE u2.tenant_id = t.id AND u2.role = 'member') AS employees_count
                FROM users u
                JOIN tenants t ON t.id = u.tenant_id
                WHERE u.role = 'owner'
                ORDER BY u.created_at DESC
                LIMIT %s
            """,
                (int(limit),),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_all_owner_users failed: {e}")
        return []


def create_owner_user(
    username: str,
    password: str,
    company_name: str,
    tenant_type: str = "shared_api",
    monthly_quota: int = 100,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    超管用 · 一步完成:建 tenant + 建老板 user
    - 自动 bcrypt 加密密码
    - user.tenant_id = 新 tenant.id
    - user.role = 'owner'
    返回 {ok: True, user_id, tenant_id} 或 {ok: False, error: '...'}
    """
    try:
        # 校验用户名唯一
        existing = db.find_user_by_username(username)
        if existing:
            logger.warning(f"create_owner_user: username {username} 已存在")
            return {"ok": False, "error": "username_exists"}

        pw_hash = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

        with db.get_cursor(commit=True) as cur:
            # 1. 建 tenant
            cur.execute(
                """
                INSERT INTO tenants (
                    name, tenant_type, monthly_quota, used_this_month,
                    status, notes, member_count
                ) VALUES (%s, %s, %s, 0, 'active', %s, 1)
                RETURNING id
            """,
                (company_name, tenant_type, int(monthly_quota), notes),
            )
            tenant_id = str(cur.fetchone()["id"])

            # 2. 建老板 user
            cur.execute(
                """
                INSERT INTO users (
                    username, password_hash, plan, is_active, is_super_admin,
                    tenant_id, role, company_name
                ) VALUES (%s, %s, 'credits', TRUE, FALSE, %s, 'owner', %s)
                RETURNING id
            """,
                (username, pw_hash, tenant_id, company_name),
            )
            user_id = str(cur.fetchone()["id"])

            # 3. 把 tenant.owner_user_id 回填
            cur.execute("UPDATE tenants SET owner_user_id = %s WHERE id = %s", (user_id, tenant_id))

            return {"ok": True, "user_id": user_id, "tenant_id": tenant_id}
    except Exception as e:
        logger.error(f"create_owner_user failed: {e}")
        return {"ok": False, "error": "db_error"}


def preview_owner_cascade(user_id: str) -> Optional[Dict[str, Any]]:
    """v118.16 · 预查删除老板的影响范围 · 给超管一个清单 · 防误删
    返回各表受影响行数 · 让超管在 modal 里看到"删了会失去什么"
    v118.16.1 · 兼容老用户 role IS NULL(对齐 admin_list_users 筛选规则)
    v118.16.2 · 兼容孤立用户 tenant_id IS NULL(老注册流程遗留 · 只按 user_id 删)
    """
    try:
        with db.get_cursor() as cur:
            # 取 tenant_id + 老板信息(role='owner' 或 NULL 都视为老板 · 兼容老数据)
            cur.execute(
                """SELECT id, username, email, company_name, tenant_id, created_at
                           FROM users WHERE id = %s AND (role = 'owner' OR role IS NULL) LIMIT 1""",
                (str(user_id),),
            )
            owner = cur.fetchone()
            if not owner:
                return None
            tenant_id = str(owner["tenant_id"]) if owner.get("tenant_id") else None

            # tenant 名(如果有)
            tenant = {}
            if tenant_id:
                cur.execute("SELECT name, tenant_type FROM tenants WHERE id = %s", (tenant_id,))
                tenant = cur.fetchone() or {}

            counts = {}
            # 按 tenant_id(完整 cascade) 还是 按 user_id(孤立用户)选不同 SQL
            if tenant_id:
                queries = [
                    (
                        "employees",
                        "SELECT COUNT(*) AS n FROM users WHERE tenant_id = %s AND role = 'member'",
                        (tenant_id,),
                    ),
                    (
                        "ocr_records",
                        "SELECT COUNT(*) AS n FROM ocr_history WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                        (tenant_id,),
                    ),
                    (
                        "clients",
                        "SELECT COUNT(*) AS n FROM clients WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                        (tenant_id,),
                    ),
                    (
                        "erp_endpoints",
                        "SELECT COUNT(*) AS n FROM erp_endpoints WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                        (tenant_id,),
                    ),
                    (
                        "erp_push_logs",
                        "SELECT COUNT(*) AS n FROM erp_push_logs WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                        (tenant_id,),
                    ),
                    (
                        "email_accounts",
                        "SELECT COUNT(*) AS n FROM email_ingest_accounts WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                        (tenant_id,),
                    ),
                    (
                        "bank_recon_sessions",
                        "SELECT COUNT(*) AS n FROM bank_reconcile_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                        (tenant_id,),
                    ),
                ]
            else:
                # 孤立用户 · 只数自己的数据 · 没有 employees(没有 tenant)
                uid_p = (str(user_id),)
                queries = [
                    ("employees", None, None),  # 跳过 · 反正是 0
                    (
                        "ocr_records",
                        "SELECT COUNT(*) AS n FROM ocr_history WHERE user_id = %s",
                        uid_p,
                    ),
                    ("clients", "SELECT COUNT(*) AS n FROM clients WHERE user_id = %s", uid_p),
                    (
                        "erp_endpoints",
                        "SELECT COUNT(*) AS n FROM erp_endpoints WHERE user_id = %s",
                        uid_p,
                    ),
                    (
                        "erp_push_logs",
                        "SELECT COUNT(*) AS n FROM erp_push_logs WHERE user_id = %s",
                        uid_p,
                    ),
                    (
                        "email_accounts",
                        "SELECT COUNT(*) AS n FROM email_ingest_accounts WHERE user_id = %s",
                        uid_p,
                    ),
                    (
                        "bank_recon_sessions",
                        "SELECT COUNT(*) AS n FROM bank_reconcile_sessions WHERE user_id = %s",
                        uid_p,
                    ),
                ]
            for k, sql, params in queries:
                if sql is None:
                    counts[k] = 0
                    continue
                try:
                    cur.execute(sql, params)
                    r = cur.fetchone()
                    counts[k] = int(r["n"]) if r else 0
                except Exception as e:
                    logger.warning(f"preview cascade · skip {k}: {e}")
                    counts[k] = 0

            return {
                "owner": {
                    "id": str(owner["id"]),
                    "username": owner.get("username"),
                    "email": owner.get("email"),
                    "company_name": owner.get("company_name"),
                    "created_at": (
                        owner["created_at"].isoformat() if owner.get("created_at") else None
                    ),
                },
                "tenant": {
                    "id": tenant_id,
                    "name": tenant.get("name") if tenant_id else None,
                    "tenant_type": tenant.get("tenant_type") if tenant_id else None,
                    "is_orphan": not tenant_id,  # v118.16.2 · 标记孤立用户(前端可显示)
                },
                "counts": counts,
            }
    except Exception as e:
        logger.error(f"preview_owner_cascade failed: {e}")
        return None


def delete_owner_user_cascade(user_id: str) -> bool:
    """
    超管用 · 删除老板 + 他整个 tenant + 所有员工 + 所有数据(ocr_history / erp / email / line 绑定...)
    依赖 FK ON DELETE CASCADE · 以及手动清理
    v118.16.1 · 兼容老用户 role IS NULL · 全程详细日志便于排查
    v118.16.2 · 兼容孤立用户 tenant_id IS NULL · 只删自己 + 自己的数据
    v118.16.3 · 改用 SAVEPOINT 模式 · 修 PostgreSQL 事务 ABORTED 问题
                (单条 DELETE 失败时 · ROLLBACK TO SAVEPOINT · 主事务保持 active · 后续能继续)
    """
    import traceback

    try:
        with db.get_cursor(commit=True) as cur:
            # 取 tenant_id(role='owner' 或 NULL 都视为老板)
            cur.execute(
                "SELECT tenant_id, username FROM users WHERE id = %s AND (role = 'owner' OR role IS NULL) LIMIT 1",
                (str(user_id),),
            )
            row = cur.fetchone()
            if not row:
                logger.warning(f"delete_owner_user_cascade: user {user_id} 不是 owner 或不存在")
                return False
            tenant_id = str(row["tenant_id"]) if row.get("tenant_id") else None
            target_username = row.get("username")
            logger.info(
                f"[cascade-delete] 开始删除 owner={target_username} tenant_id={tenant_id or '(orphan)'}"
            )

            # ============================================================
            # SAVEPOINT 工具 · 每条 DELETE 独立成可回滚的子事务
            # 否则 PostgreSQL 一条错 · 后续全部 ignored(事务 aborted)
            # ============================================================
            sp_counter = [0]

            def _safe_delete(sql, params, label):
                sp_counter[0] += 1
                sp_name = f"sp_{sp_counter[0]}"
                try:
                    cur.execute(f"SAVEPOINT {sp_name}")
                    cur.execute(sql, params)
                    rc = cur.rowcount
                    cur.execute(f"RELEASE SAVEPOINT {sp_name}")
                    if rc > 0:
                        logger.info(f"[cascade-delete] {label}: 删 {rc} 条")
                    return True
                except Exception as e:
                    try:
                        cur.execute(f"ROLLBACK TO SAVEPOINT {sp_name}")
                    except Exception:
                        pass  # savepoint 已不存在 · 忽略
                    logger.warning(
                        f"[cascade-delete] {label} · 跳过(savepoint 已回滚): {str(e)[:200]}"
                    )
                    return False

            if tenant_id:
                # ========== 完整路径(有 tenant)· 按 tenant 维度级联 ==========
                tables = [
                    (
                        "ocr_history",
                        "DELETE FROM ocr_history WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "ocr_cost_log",
                        "DELETE FROM ocr_cost_log WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "erp_push_logs",
                        "DELETE FROM erp_push_logs WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "erp_endpoints",
                        "DELETE FROM erp_endpoints WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "clients",
                        "DELETE FROM clients WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "archive_settings",
                        "DELETE FROM archive_settings WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "rd_daily_usage",
                        "DELETE FROM rd_daily_usage WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "email_ingest_seen_uids",
                        "DELETE FROM email_ingest_seen_uids WHERE account_id IN (SELECT id FROM email_ingest_accounts WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s))",
                    ),
                    (
                        "email_ingest_logs",
                        "DELETE FROM email_ingest_logs WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "email_ingest_accounts",
                        "DELETE FROM email_ingest_accounts WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "bank_reconcile_candidates",
                        "DELETE FROM bank_reconcile_candidates WHERE session_id IN (SELECT id FROM bank_reconcile_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s))",
                    ),
                    (
                        "bank_reconcile_transactions",
                        "DELETE FROM bank_reconcile_transactions WHERE session_id IN (SELECT id FROM bank_reconcile_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s))",
                    ),
                    (
                        "bank_reconcile_sessions",
                        "DELETE FROM bank_reconcile_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "line_bindings",
                        "DELETE FROM line_bindings WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "line_binding_codes",
                        "DELETE FROM line_binding_codes WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "user_settings",
                        "DELETE FROM user_settings WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "api_keys",
                        "DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "automation_rules",
                        "DELETE FROM automation_rules WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                    (
                        "excel_templates",
                        "DELETE FROM excel_templates WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                    ),
                ]
                for label, sql in tables:
                    _safe_delete(sql, (tenant_id,), label)

                # 关键步骤
                _safe_delete("DELETE FROM users WHERE tenant_id = %s", (tenant_id,), "users")
                _safe_delete(
                    "DELETE FROM operation_logs WHERE tenant_id = %s",
                    (tenant_id,),
                    "operation_logs",
                )
                ok_tenant = _safe_delete(
                    "DELETE FROM tenants WHERE id = %s", (tenant_id,), "tenants"
                )
                logger.info(f"[cascade-delete] ✅ 完成 owner={target_username}")
                return ok_tenant
            else:
                # ========== 孤立用户路径(无 tenant)· 只按 user_id 删自己 ==========
                logger.info(f"[cascade-delete] 孤立用户模式 · user_id={user_id}")
                tables = [
                    ("ocr_history", "DELETE FROM ocr_history WHERE user_id = %s"),
                    ("ocr_cost_log", "DELETE FROM ocr_cost_log WHERE user_id = %s"),
                    ("erp_push_logs", "DELETE FROM erp_push_logs WHERE user_id = %s"),
                    ("erp_endpoints", "DELETE FROM erp_endpoints WHERE user_id = %s"),
                    ("clients", "DELETE FROM clients WHERE user_id = %s"),
                    ("archive_settings", "DELETE FROM archive_settings WHERE user_id = %s"),
                    ("rd_daily_usage", "DELETE FROM rd_daily_usage WHERE user_id = %s"),
                    (
                        "email_ingest_seen_uids",
                        "DELETE FROM email_ingest_seen_uids WHERE account_id IN (SELECT id FROM email_ingest_accounts WHERE user_id = %s)",
                    ),
                    ("email_ingest_logs", "DELETE FROM email_ingest_logs WHERE user_id = %s"),
                    (
                        "email_ingest_accounts",
                        "DELETE FROM email_ingest_accounts WHERE user_id = %s",
                    ),
                    (
                        "bank_reconcile_candidates",
                        "DELETE FROM bank_reconcile_candidates WHERE session_id IN (SELECT id FROM bank_reconcile_sessions WHERE user_id = %s)",
                    ),
                    (
                        "bank_reconcile_transactions",
                        "DELETE FROM bank_reconcile_transactions WHERE session_id IN (SELECT id FROM bank_reconcile_sessions WHERE user_id = %s)",
                    ),
                    (
                        "bank_reconcile_sessions",
                        "DELETE FROM bank_reconcile_sessions WHERE user_id = %s",
                    ),
                    ("line_bindings", "DELETE FROM line_bindings WHERE user_id = %s"),
                    ("line_binding_codes", "DELETE FROM line_binding_codes WHERE user_id = %s"),
                    ("user_settings", "DELETE FROM user_settings WHERE user_id = %s"),
                    ("api_keys", "DELETE FROM api_keys WHERE user_id = %s"),
                    ("automation_rules", "DELETE FROM automation_rules WHERE user_id = %s"),
                    ("excel_templates", "DELETE FROM excel_templates WHERE user_id = %s"),
                ]
                for label, sql in tables:
                    _safe_delete(sql, (str(user_id),), label)
                ok_user = _safe_delete(
                    "DELETE FROM users WHERE id = %s", (str(user_id),), "users-orphan"
                )
                logger.info(f"[cascade-delete] ✅ 完成 orphan owner={target_username}")
                return ok_user
    except Exception as e:
        logger.error(
            f"delete_owner_user_cascade failed (user_id={user_id}): {e}\n{traceback.format_exc()}"
        )
        return False


# ============================================================
# 多公司成员 / 当前账套切换(REFACTOR-B2 · 从 db.py 搬入 · 纯搬家 0 逻辑改)
# user_company_roles 表 · active_tenant_id · billing_routes 用
# ============================================================
def list_user_companies(user_id: str) -> list:
    """Return all companies a user belongs to.

    Each item: {tenant_id, name, role, balance_thb, pages_this_month, is_active}
    Uses Asia/Bangkok timezone for year_month.
    """
    try:
        year_month = db._bkk_year_month()
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    ucr.tenant_id::text AS tenant_id,
                    t.name AS name,
                    ucr.role AS role,
                    ucr.is_active AS is_active,
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_this_month
                FROM user_company_roles ucr
                JOIN tenants t ON t.id = ucr.tenant_id
                LEFT JOIN tenant_credits tc ON tc.tenant_id = ucr.tenant_id
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = ucr.tenant_id AND mpu.year_month = %s
                WHERE ucr.user_id = %s::uuid AND ucr.is_active = TRUE
                ORDER BY t.name
            """,
                (year_month, str(user_id)),
            )
            rows = cur.fetchall() or []
        out = []
        for r in rows:
            out.append(
                {
                    "tenant_id": r["tenant_id"],
                    "name": r["name"] or "",
                    "role": r["role"] or "member",
                    "balance_thb": float(r["balance_thb"] or 0),
                    "pages_this_month": int(r["pages_this_month"] or 0),
                    "is_active": bool(r["is_active"]),
                }
            )
        return out
    except Exception as e:
        logger.error(f"list_user_companies failed: {e}")
        return []


def set_user_active_tenant(user_id: str, tenant_id: str) -> bool:
    """Validate user belongs to tenant; if yes set active_tenant_id."""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                SELECT 1 FROM user_company_roles
                WHERE user_id = %s::uuid AND tenant_id = %s::uuid AND is_active = TRUE
                LIMIT 1
            """,
                (str(user_id), str(tenant_id)),
            )
            if not cur.fetchone():
                return False
            cur.execute(
                """
                UPDATE users SET active_tenant_id = %s::uuid
                WHERE id = %s::uuid
            """,
                (str(tenant_id), str(user_id)),
            )
        return True
    except Exception as e:
        logger.error(f"set_user_active_tenant failed: {e}")
        return False
