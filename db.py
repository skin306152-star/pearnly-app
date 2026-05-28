# -*- coding: utf-8 -*-
"""
Mr.Pearnly · 数据库模块(v3)
第 3.5 批:支持新权限字段 + ensure_demo 更新字段
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

logger = logging.getLogger(__name__)

# v4.10.14 · Gemini 2.5 Flash 计费单价(USD · 2026-05)
OCR_PRICING = {
    "input_per_m_usd": 0.30,
    "output_per_m_usd": 2.50,
    "usd_thb": 36.5,  # v4.10.14 过渡 · v4.10.15 admin 改造时统一砍
}

_pool: Optional[SimpleConnectionPool] = None


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "❌ DATABASE_URL 未设置。请在 HF Space Secrets 添加 "
            "DATABASE_URL=postgresql://... (Pooler 模式)"
        )
    return url


def get_pool() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        url = _get_database_url()
        # v118.35.0.21 · maxconn 5 → 30 · 修 v0.20 部署后全站超时的真因
        # 老 maxconn=5 在 v0.20 加 credits 检查后(每个 OCR 多 3 次 DB 查询)
        # 5 个并发 OCR 就把连接池打满 · 后续请求阻塞 → 累积 → 全站超时
        # Supabase 默认允许 ~60 个连接 · 30 安全有冗余
        _pool = SimpleConnectionPool(
            minconn=2,
            maxconn=30,
            dsn=url,
            connect_timeout=10,
            sslmode="require",
        )
        logger.info("✅ PostgreSQL 连接池已建立(minconn=2 maxconn=30)")
    return _pool


@contextmanager
def get_cursor(commit: bool = False):
    conn = get_pool().getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        get_pool().putconn(conn)


def ensure_google_sub_column():
    """v118.27.5 · 启动时自动加 google_sub 列(幂等 · IF NOT EXISTS)
    v118.27.5.3 · 同时加 avatar_url 列(Google OAuth picture URL)
    P1b(2026-05-26)· 同时加 erp_push_mode 列(ERP 自动处理方式 · 账户级默认)·
      复用本 users 多列 ensure(铁律 #21/#23:不新增 ensure_* · 进现有 ensure)·
      值 smart(智能分拣) / fixed(固定当前账套) / ocr_only(只识别不推送)· 默认 smart。
      留档迁移见 alembic/versions/006_users_erp_push_mode.py(生产不跑 alembic · 双跑范式)。"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub TEXT")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL"
            )
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT")
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS " "erp_push_mode TEXT DEFAULT 'smart'"
            )
        logger.info("[v118.27.5.3] users.google_sub + avatar_url + erp_push_mode 列就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.27.5.3] 加列失败: {e}")
        return False


# ============================================================
# v118.28.9 · 改密后旧 JWT 失效
# users 表加 password_changed_at TIMESTAMPTZ DEFAULT NOW()
# auth.get_current_user_from_request 比对 token.iat 和该列 · 旧 token 自动作废
# ============================================================
def ensure_password_changed_at_column():
    """v118.28.9 · 启动时自动加 password_changed_at 列(幂等 · IF NOT EXISTS)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                "password_changed_at TIMESTAMPTZ DEFAULT NOW()"
            )
        logger.info("[v118.28.9] users.password_changed_at 列就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.28.9] 加 password_changed_at 列失败: {e}")
        return False


def ensure_line_uid_column():
    """v118.28.4 · 启动时自动加 line_uid 列(幂等 · IF NOT EXISTS)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS line_uid TEXT")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_line_uid ON users(line_uid) WHERE line_uid IS NOT NULL"
            )
        logger.info("[v118.28.4] users.line_uid 列就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.28.4] line_uid 加列失败: {e}")
        return False


# ============================================================
# v118.28.4.1 · LINE 用户补邮箱 · 合并老账号 / 更新临时账号
# ============================================================
def is_line_placeholder_username(username: str) -> bool:
    """判断是否是 line_xxx@line.local 临时占位"""
    return bool(username and username.startswith("line_") and username.endswith("@line.local"))


def update_user_email_and_username(user_id: str, new_email: str) -> bool:
    """LINE 临时账号填完真邮箱后 · 把 username/email/email_normalized 都更新成真邮箱"""
    if not user_id or not new_email:
        return False
    try:
        from auth_signup import normalize_email as _norm_email
    except Exception:
        _norm_email = lambda x: (x or "").strip().lower()
    new_email_clean = (new_email or "").strip().lower()
    new_email_norm = _norm_email(new_email_clean)
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE users SET username = %s, email = %s, email_normalized = %s
                WHERE id = %s
            """,
                (new_email_clean, new_email_clean, new_email_norm, user_id),
            )
        return True
    except Exception as e:
        logger.error(f"更新 email/username 失败 (user_id={user_id}): {e}")
        return False


def merge_line_account_into_existing(temp_user_id: str, target_user_id: str, line_uid: str) -> bool:
    """LINE 补邮箱发现该 email 已绑定老账号 · 把 line_uid 转移到老账号 + 删临时账号
    注意:临时账号只是刚创建的 · 没有发票/客户/任何业务数据 · 直接删
    """
    if not temp_user_id or not target_user_id or not line_uid:
        return False
    try:
        with get_cursor(commit=True) as cur:
            # 1) 先从临时账号摘掉 line_uid(防 unique 冲突)
            cur.execute("UPDATE users SET line_uid = NULL WHERE id = %s", (temp_user_id,))
            # 2) 绑到老账号
            cur.execute("UPDATE users SET line_uid = %s WHERE id = %s", (line_uid, target_user_id))
            # 3) 删临时账号的示例 client(create_user_via_line_oauth 建的 1 个)
            cur.execute("DELETE FROM clients WHERE user_id = %s", (temp_user_id,))
            # 4) 删订阅日志
            try:
                cur.execute("DELETE FROM subscription_log WHERE user_id = %s", (temp_user_id,))
            except Exception:
                pass  # 表可能不存在 · 安全跳过
            # 5) 删临时账号
            cur.execute("DELETE FROM users WHERE id = %s", (temp_user_id,))
        logger.info(
            f"[v118.28.4.1] merged line_uid={line_uid} from temp={temp_user_id} → target={target_user_id}"
        )
        return True
    except Exception as e:
        logger.error(f"合并 LINE 账号失败 (temp={temp_user_id} → target={target_user_id}): {e}")
        return False


def ensure_email_codes_table():
    """v118.27.6 · 邮箱验证码表(注册前验证 · 6 位数字 · 10 分钟有效)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS email_codes (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    code TEXT NOT NULL,
                    purpose TEXT NOT NULL DEFAULT 'signup',
                    expires_at TIMESTAMPTZ NOT NULL,
                    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    used BOOLEAN NOT NULL DEFAULT FALSE,
                    used_at TIMESTAMPTZ,
                    sender_ip TEXT
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_codes_email ON email_codes(email, purpose, used)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_codes_expires ON email_codes(expires_at)"
            )
        logger.info("[v118.27.6] email_codes 表就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.27.6] email_codes 建表失败: {e}")
        return False


def update_last_login(user_id: str):
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user_id,))
    except Exception as e:
        logger.error(f"更新登录时间失败: {e}")


def increment_user_monthly_usage(user_id: str, n: int = 1) -> int:
    """
    Plus 用户识别后累加本月用量。
    如果已经跨月(last_usage_month != 本月),会重置为 n 而不是累加。
    返回最新的 used_this_month 值。
    """
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE users SET
                    used_this_month = CASE
                        WHEN last_usage_month IS NULL
                          OR last_usage_month < DATE_TRUNC('month', NOW())::date
                        THEN %s
                        ELSE COALESCE(used_this_month, 0) + %s
                    END,
                    last_usage_month = DATE_TRUNC('month', NOW())::date
                WHERE id = %s
                RETURNING used_this_month
            """,
                (n, n, user_id),
            )
            row = cur.fetchone()
            return row["used_this_month"] if row else 0
    except Exception as e:
        logger.error(f"更新用户月用量失败 (user_id={user_id}): {e}")
        return 0


# ============================================================
# v0.6.0 · ERP 端点 + 推送日志 DAL → services/erp/push_store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · 重试常量/错误分类器随域搬走 · db.py 文件尾 re-export
# 对外函数 + 公共常量(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v0.7 · 智能归档 DAL → services/archive/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v0.8 · RD 校验日限 DAL → services/rd/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v0.8.1 · 过期历史清理
# ============================================================
def cleanup_expired_history(free_days: int = 7, plus_days: int = 90, pro_days: int = 365) -> int:
    """按 plan 删除过期历史 · 返回删除条数"""
    total = 0
    try:
        with get_cursor(commit=True) as cur:
            # Free
            cur.execute(
                """
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'free')
                  AND created_at < NOW() - (%s || ' days')::interval
            """,
                (str(free_days),),
            )
            total += cur.rowcount
            # Plus
            cur.execute(
                """
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'plus')
                  AND created_at < NOW() - (%s || ' days')::interval
            """,
                (str(plus_days),),
            )
            total += cur.rowcount
            # Pro
            cur.execute(
                """
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'pro')
                  AND created_at < NOW() - (%s || ' days')::interval
            """,
                (str(pro_days),),
            )
            total += cur.rowcount
        return total
    except Exception as e:
        logger.error(f"cleanup_expired_history failed: {e}")
        return 0


# ============================================================
# v0.17 · M6 · 邮箱抓取 DAL → services/email_ingest/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export 回本命名空间(所有 db.xxx() 调用点不变)
# ============================================================


# ════════════════════════════════════════════════════════════════════
# v0.18 · M10 · 银行对账 v1 DAL → services/recon/bank_recon_v1_store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ════════════════════════════════════════════════════════════════════


# ============================================================
# v22 多租户 · 租户管理函数
# ============================================================
# 设计原则:
# - 所有业务函数保持按 user_id 查(不破坏现有代码)
# - 下面这批新函数供超级管理员后台使用
# - 租户数据隔离通过"每个用户只属于一个租户"来保证
# ============================================================


# ============================================================
# v23 · 用户(老板)管理 + 员工 + 操作日志
# ============================================================
# ============================================================
# 操作/审计日志 operation_logs DAL → services/audit/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# 员工管理(老板自助 · users role=member)DAL → services/team/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · tenant 隔离 · add_employee 复用 db.find_user_by_username
# db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v106 · 成本追踪 ocr_cost_log DAL → services/cost/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · 只读聚合(成本面板)+ 成本记账 · 不涉扣费逻辑
# db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v107 · 客户(clients)+ 供应商分类(supplier_categories)+ 买家→客户(buyer_to_client_memory)
#        DAL → services/clients/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · tenant 隔离矩阵 · db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v108 · Google AI Studio 余额追踪 billing_balance_log DAL → services/billing/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · 保留 ensure_billing_balance_table/get_latest_balance(calibration 兜底)
# add_balance_log/get_balance_summary 已于 2026-05-25 Earn 后台改造删除
# db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v118.20.1 · 异常栏(exceptions + exception_whitelist)DAL → services/exceptions/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · tenant 隔离矩阵(同 tenant 共享异常池/白名单)
# db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v118.22.1 · 智能提醒 DAL → services/notification/store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export 回本命名空间(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v118.27.7 · 多租户改造 P0 · 数据层重构
# ============================================================
# 目标:
#   - 建 memberships / client_assignments / roles 三表(底层骨架)
#   - 提供 get_user_tenant_id() 兼容层(优先 memberships · 回退 users.tenant_id)
#   - 提供 migrate_to_membership_model(dry_run) 迁移函数(超管手动触发)
# 约束:
#   - 不动 users.tenant_id 字段(双写过渡期 · 至少 2 版)
#   - 老代码继续 work · ensure_membership_tables() 仅建表 · 不自动迁移
#   - Q1 决定:1 人 1 事务所 · UNIQUE(user_id) · 未来放宽改成 (user_id, tenant_id)
#   - Q2 决定:client 不需要登录 · client_assignments 仅约束员工可见客户
# ============================================================


def ensure_membership_tables():
    """启动时建 3 张表 + 灌系统角色 + ALTER 老表加列 · 幂等"""
    try:
        with get_cursor(commit=True) as cur:
            # ── 1. roles 表(RBAC 预留 · 现在不接逻辑只建表)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL UNIQUE,
                    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
                    is_system BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            # 灌 3 个系统角色(幂等)
            cur.execute("""
                INSERT INTO roles (name, permissions, is_system) VALUES
                    ('owner',   '{"all": true}'::jsonb,                                              TRUE),
                    ('manager', '{"manage_team": true, "view_all_clients": true}'::jsonb,           TRUE),
                    ('staff',   '{"view_assigned_clients": true}'::jsonb,                           TRUE)
                ON CONFLICT (name) DO NOTHING;
            """)

            # ── 2. memberships 表(用户挂事务所 + 角色 + 状态)
            # Q1 砍 M:N · UNIQUE(user_id) · 1 人 1 事务所
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memberships (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    role_id UUID NOT NULL REFERENCES roles(id),
                    status TEXT NOT NULL DEFAULT 'active',
                    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id)
                );
                CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON memberships(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_memberships_status ON memberships(status) WHERE status = 'active';
            """)

            # ── 3. client_assignments 表(谁能看哪个客户 · 所长授权)
            # 注意:clients.id 是 BIGSERIAL(BIGINT)· 不是 UUID
            cur.execute("""
                CREATE TABLE IF NOT EXISTS client_assignments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    assigned_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, client_id)
                );
                CREATE INDEX IF NOT EXISTS idx_client_assign_user ON client_assignments(user_id);
                CREATE INDEX IF NOT EXISTS idx_client_assign_client ON client_assignments(client_id);
            """)

            # ── 4. tenants 加 tenant_type 列(区分事务所/SME/freelancer)
            cur.execute("""
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tenant_type_v2 TEXT DEFAULT 'firm';
            """)
            # 注意:tenants 表已经有老的 tenant_type(shared_api/byo_api/admin · 计费类型)
            # 不能覆盖 · 用新列 tenant_type_v2 区分(firm/sme/freelancer · 业务类型)

            # ── 5. clients 表 · tenant_id 列已存在(v107 ensure_clients_table 已建)· 不重复 ALTER

            logger.info(
                "✅ v118.27.7 · memberships / client_assignments / roles 表已就绪 · 3 系统角色已灌入"
            )
    except Exception as e:
        logger.error(f"ensure_membership_tables failed: {e}")


# ============================================================
# v118.28.1 · 客户分配(老板分客户给员工)· 业务工具
# ============================================================


# ============================================================
# v118.27.7.1 · 孤立用户(tenant_id IS NULL)盘点 + 修复
#   - 给每个孤立用户建一个独立 tenant + 写 membership
#   - 完整继承 user.plan / monthly_quota / expires(防付费用户掉级)
#   - 单用户独立事务 · 一个失败不影响其他
# ============================================================


# ============================================================
# v118.27.8.0 · RLS 行级安全基础设施(P1 试点)
#   - ENABLE_RLS 环境变量:0 关 / 1 开(默认 0)
#   - get_cursor_rls(tenant_id, bypass) · 自动 SET LOCAL app.current_tenant_id
#   - run_rls_isolation_tests · 临时启用 clients 表 RLS 跑 5 条穿透测试 · 测完关
#   - 不改任何现有 db 函数 · 现有代码继续工作 · v27.8.1 才永久启用
# ============================================================


def _is_rls_enabled() -> bool:
    """RLS 总开关 · ENABLE_RLS 环境变量 · 默认关"""
    return os.environ.get("ENABLE_RLS", "0").strip() == "1"


@contextmanager
def get_cursor_rls(tenant_id: Optional[str] = None, bypass: bool = False, commit: bool = False):
    """v27.8.0 · 带 RLS 上下文的游标 · 自动 SET LOCAL session 变量
    tenant_id:当前 user 所属 tenant · 用于 RLS policy 过滤
    bypass:超管 / migration 操作跳过 RLS(SET app.bypass_rls = 'on')
    commit:是否自动 commit
    """
    conn = get_pool().getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            if bypass:
                cur.execute("SET LOCAL app.bypass_rls = 'on';")
            elif tenant_id:
                cur.execute("SET LOCAL app.current_tenant_id = %s;", (str(tenant_id),))
            # 否则不 SET · 严格 policy 会拒绝(对 RLS 启用的表)
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        get_pool().putconn(conn)


def get_clients_rls_status() -> Dict[str, Any]:
    """查 clients 表 RLS 当前状态 · 给超管面板"""
    out = {
        "enable_rls_env": _is_rls_enabled(),
        "clients_rls_active": False,
        "policies": [],
    }
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT relrowsecurity FROM pg_class
                WHERE relname = 'clients' AND relkind = 'r' LIMIT 1
            """)
            r = cur.fetchone()
            out["clients_rls_active"] = bool(r and r.get("relrowsecurity"))
            cur.execute("""
                SELECT polname AS name FROM pg_policy
                WHERE polrelid = 'clients'::regclass
            """)
            out["policies"] = [r["name"] for r in cur.fetchall()]
    except Exception as e:
        out["error"] = str(e)[:200]
    return out


def run_rls_isolation_tests() -> Dict[str, Any]:
    """v27.8.0 · RLS 穿透测试 · 5 条
    流程:临时启用 clients 表 RLS + policy → 跑测试 → 关 RLS 恢复(不论结果)
    完整测试不影响线上现有代码(测前测后 RLS 状态一致 · 默认关)
    """
    out = {
        "passed": 0,
        "failed": 0,
        "tests": [],
        "preflight": {},
        "rls_state_before": get_clients_rls_status(),
    }
    rls_was_off_before = not out["rls_state_before"]["clients_rls_active"]

    # 准备 · 找 2 个有 client 的 tenant
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT t.id AS tenant_id, t.name AS tenant_name,
                       c.id AS client_id, c.name AS client_name
                FROM tenants t
                JOIN LATERAL (
                    SELECT id, name FROM clients WHERE tenant_id = t.id LIMIT 1
                ) c ON TRUE
                LIMIT 2
            """)
            samples = cur.fetchall() or []
        if len(samples) < 2:
            out["preflight"] = {
                "ok": False,
                "reason": f"需要至少 2 个 tenant 各有 client 才能跑测试 · 实际找到 {len(samples)} 个",
                "hint": "可在 admin 后台给某个孤立用户建 1 个客户(/api/clients POST)再跑",
            }
            out["failed"] = 1
            return out
        out["preflight"] = {
            "ok": True,
            "tenant_a": {
                "id": str(samples[0]["tenant_id"]),
                "name": samples[0].get("tenant_name"),
                "client_id": int(samples[0]["client_id"]),
                "client_name": samples[0].get("client_name"),
            },
            "tenant_b": {
                "id": str(samples[1]["tenant_id"]),
                "name": samples[1].get("tenant_name"),
                "client_id": int(samples[1]["client_id"]),
                "client_name": samples[1].get("client_name"),
            },
        }
        tenant_a_id = str(samples[0]["tenant_id"])
        tenant_b_id = str(samples[1]["tenant_id"])
        client_b_id = int(samples[1]["client_id"])
        client_b_name = samples[1].get("client_name")
    except Exception as e:
        out["preflight"] = {"ok": False, "reason": f"preflight 查询失败: {str(e)[:200]}"}
        out["failed"] = 1
        return out

    # 临时启用 RLS(测完关)
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("ALTER TABLE clients ENABLE ROW LEVEL SECURITY;")
            cur.execute("DROP POLICY IF EXISTS tenant_isolation_test ON clients;")
            cur.execute("""
                CREATE POLICY tenant_isolation_test ON clients
                FOR ALL
                USING (
                    tenant_id::text = current_setting('app.current_tenant_id', true)
                    OR current_setting('app.bypass_rls', true) = 'on'
                );
            """)
        logger.info("[v27.8.0 rls_test] 临时启用 clients RLS + tenant_isolation_test policy")

        def _record(name, ok, expected, actual):
            out["tests"].append({"name": name, "ok": ok, "expected": expected, "actual": actual})
            if ok:
                out["passed"] += 1
            else:
                out["failed"] += 1

        # ── Test 1:tenant_a 视角不能看 tenant_b 的 client(穿透核心)
        try:
            with get_cursor_rls(tenant_id=tenant_a_id) as cur:
                cur.execute("SELECT id, name FROM clients WHERE id = %s", (client_b_id,))
                row = cur.fetchone()
            _record(
                "Test 1 · tenant_a 不能看 tenant_b 的 client",
                row is None,
                "查询返空(防穿透)",
                "返空 ✓" if row is None else f"看到了 {row.get('name')!r}",
            )
        except Exception as e:
            _record("Test 1", False, "查询返空", f"异常: {str(e)[:200]}")

        # ── Test 2:tenant_b 视角能看自己的 client(基本可用)
        try:
            with get_cursor_rls(tenant_id=tenant_b_id) as cur:
                cur.execute("SELECT id, name FROM clients WHERE id = %s", (client_b_id,))
                row = cur.fetchone()
            ok = row is not None and row.get("name") == client_b_name
            _record(
                "Test 2 · tenant_b 能看自己的 client",
                ok,
                f"看到 {client_b_name!r}",
                row.get("name") if row else "返空",
            )
        except Exception as e:
            _record("Test 2", False, f"看到 {client_b_name!r}", f"异常: {str(e)[:200]}")

        # ── Test 3:无 tenant 上下文 · RLS policy 必须拒绝(老代码忘 SET 时的兜底)
        try:
            with get_cursor_rls(tenant_id=None) as cur:
                cur.execute("SELECT COUNT(*) AS n FROM clients")
                n = int((cur.fetchone() or {}).get("n") or 0)
            _record(
                "Test 3 · 无 tenant 上下文 · RLS 拒绝(防代码忘记 SET)",
                n == 0,
                "0",
                str(n),
            )
        except Exception as e:
            _record("Test 3", False, "0", f"异常: {str(e)[:200]}")

        # ── Test 4:bypass 模式能看所有(超管 / migration 通道)
        try:
            with get_cursor_rls(bypass=True) as cur:
                cur.execute("SELECT COUNT(*) AS n FROM clients")
                n_bypass = int((cur.fetchone() or {}).get("n") or 0)
            with get_cursor_rls(tenant_id=tenant_a_id) as cur:
                cur.execute("SELECT COUNT(*) AS n FROM clients")
                n_a = int((cur.fetchone() or {}).get("n") or 0)
            ok = n_bypass >= n_a and n_bypass > 0
            _record(
                "Test 4 · bypass 模式能看所有 tenant 的数据",
                ok,
                f"bypass({n_bypass}) >= tenant_a({n_a}) 且 > 0",
                "通过" if ok else f"bypass={n_bypass} tenant_a={n_a}",
            )
        except Exception as e:
            _record("Test 4", False, "bypass 看所有", f"异常: {str(e)[:200]}")

        # ── Test 5:伪造 tenant_id(随机 UUID · 数据库里不存在)· 必须返空
        try:
            fake_uuid = "00000000-0000-0000-0000-000000000000"
            with get_cursor_rls(tenant_id=fake_uuid) as cur:
                cur.execute("SELECT COUNT(*) AS n FROM clients")
                n_fake = int((cur.fetchone() or {}).get("n") or 0)
            _record(
                "Test 5 · 伪造 tenant_id 必须返空(防 UUID 猜测攻击)",
                n_fake == 0,
                "0",
                str(n_fake),
            )
        except Exception as e:
            _record("Test 5", False, "0", f"异常: {str(e)[:200]}")

    except Exception as e:
        logger.error(f"run_rls_isolation_tests fatal: {e}")
        out["tests"].append(
            {"name": "fatal", "ok": False, "expected": "test 框架正常", "actual": str(e)[:300]}
        )
        out["failed"] += 1
    finally:
        # 永远关 RLS(无论测试结果) · 恢复测前状态
        if rls_was_off_before:
            try:
                with get_cursor(commit=True) as cur:
                    cur.execute("DROP POLICY IF EXISTS tenant_isolation_test ON clients;")
                    cur.execute("ALTER TABLE clients DISABLE ROW LEVEL SECURITY;")
                logger.info("[v27.8.0 rls_test] 测试完成 · 已关 clients RLS · 恢复测前状态")
            except Exception as e:
                logger.error(
                    f"[v27.8.0 rls_test] 关 RLS 失败 · 需手动:ALTER TABLE clients DISABLE ROW LEVEL SECURITY; · 错误: {e}"
                )
                out["cleanup_error"] = str(e)[:200]

    out["rls_state_after"] = get_clients_rls_status()
    out["all_passed"] = out["failed"] == 0 and out["passed"] == 5
    return out


# ============================================================
# v118.27.8.1 · tenant_id 回填(P0 数据修补)
#   - v27.7.1 建 tenant 时只填了 user.tenant_id · 现有数据表的 tenant_id 列还是 NULL
#   - 自动扫 public schema 所有有 (user_id, tenant_id) 双列的表 · 按 user 回填
#   - 影响:clients / ocr_cost_log / supplier_categories / exceptions / 等等
#   - 不论 RLS 启不启用 · 这个 bug 都该修(否则跨 tenant 统计可能不准)
# ============================================================


# ============================================================
# v118.27.0 · ERP 映射底座 DAL → services/erp/mappings_store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · 校验常量(ERP_TYPES_VALID/PEARNLY_TAX_KINDS_VALID)随域搬走 ·
# db.py 文件尾 re-export 对外函数(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v118.27.4 · ERP OAuth 2.0 token DAL → services/erp/oauth_store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export 回本命名空间(所有 db.xxx() 调用点不变)
# ============================================================


# ============================================================
# v118.32.0 · 销项税对账三张表(vat_report+reconciliation_task+reconciliation_row)
#   + 屏 B 内嵌 client helper(find_client_by_tax_id/auto_create_client/get_client_by_id/find_or_create_client_by_tax_id)
#   DAL → services/recon/vat_recon_store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · tenant 隔离矩阵 · find_or_create 复用 db.create_client
# db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ============================================================


# ════════════════════════════════════════════════════════════════════
# vat_recon_tasks DAL → services/recon/vat_recon_tasks_store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════
# GL vs 销项税报告对账任务 DAL → services/recon/gl_vat_store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════
# Bank Reconciliation v2(Statement vs GL)对账任务 DAL → services/recon/bank_recon_v2_store.py (REFACTOR-B2)
# 纯搬家 0 逻辑改 · db.py 文件尾 re-export(所有 db.xxx() 调用点不变)
# ════════════════════════════════════════════════════════════════════


def ensure_credits_tables():
    """按量付费系统 - 新增表结构，不影响任何现有逻辑"""
    try:
        with get_cursor(commit=True) as cur:
            # 2026-05-24 · 事务级 advisory lock 串行化建表 DDL · 防多 worker 并发启动时
            #   CREATE/ALTER 互锁 deadlock(原现象:启动日志 ensure_credits_tables failed:
            #   deadlock detected)· 第二个 worker 等第一个建完再跑 IF NOT EXISTS 空操作。
            cur.execute("SELECT pg_advisory_xact_lock(906024)")

            # 1. 用户-公司多对多关系表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_company_roles (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('admin','member')),
                    is_active BOOLEAN DEFAULT TRUE,
                    joined_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(user_id, tenant_id)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ucr_user ON user_company_roles(user_id)")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_ucr_tenant ON user_company_roles(tenant_id)"
            )

            # 2. 公司钱包余额
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tenant_credits (
                    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
                    balance_thb NUMERIC(12,2) NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # 3. 充值/扣费流水
            cur.execute("""
                CREATE TABLE IF NOT EXISTS credit_transactions (
                    id SERIAL PRIMARY KEY,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    type TEXT NOT NULL CHECK (type IN ('topup','usage','adjustment')),
                    amount_thb NUMERIC(12,2) NOT NULL,
                    pages INT DEFAULT 0,
                    balance_after NUMERIC(12,2) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_ctx_tenant ON credit_transactions(tenant_id, created_at DESC)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_ctx_user ON credit_transactions(user_id, created_at DESC)"
            )

            # 4. 月用量统计（月初重置）
            cur.execute("""
                CREATE TABLE IF NOT EXISTS monthly_page_usage (
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    year_month TEXT NOT NULL,
                    pages_used INT NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (tenant_id, year_month)
                )
            """)

            # 5. 充值申请表（用户上传转账截图）
            cur.execute("""
                CREATE TABLE IF NOT EXISTS topup_requests (
                    id SERIAL PRIMARY KEY,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    requested_by UUID NOT NULL REFERENCES users(id),
                    amount_thb NUMERIC(12,2) NOT NULL,
                    slip_path TEXT,
                    payer_name TEXT,
                    note TEXT,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','approved','rejected')),
                    reviewed_by UUID REFERENCES users(id),
                    reviewed_at TIMESTAMPTZ,
                    review_note TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # 6. users 表新增豁免字段
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_billing_exempt BOOLEAN NOT NULL DEFAULT FALSE
            """)

            # 6a. v118.35.0.6 · users 表新增 active_tenant_id(multi-company 切换 ·
            #     auth.py 在 JWT.tenant_id 上 overlay 这个字段 · 不动 token)
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS active_tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL
            """)

            # 7. 迁移现有用户归属到 user_company_roles
            cur.execute("""
                INSERT INTO user_company_roles (user_id, tenant_id, role)
                SELECT
                    id,
                    tenant_id,
                    CASE WHEN role = 'owner' THEN 'admin' ELSE 'member' END
                FROM users
                WHERE tenant_id IS NOT NULL AND is_active = TRUE
                ON CONFLICT (user_id, tenant_id) DO NOTHING
            """)

            # 8. 为每个现有公司建初始钱包（余额0）
            cur.execute("""
                INSERT INTO tenant_credits (tenant_id)
                SELECT id FROM tenants
                ON CONFLICT (tenant_id) DO NOTHING
            """)

            # 9. 设置豁免账号
            cur.execute("""
                UPDATE users SET is_billing_exempt = TRUE
                WHERE email IN ('skin306152@gmail.com','mrerp@outlook.co.th')
            """)

        logger.info("[credits] 新表结构初始化完成")
    except Exception as e:
        logger.error(f"ensure_credits_tables failed: {e}")
        raise


# v118.35.0.4 · 给新建公司初始化 0 余额的 tenant_credits 行
# 调用点: auth_signup 的 3 个注册路径(email / google / line)
# 幂等 · 已存在不覆盖 · 失败 log warning 不抛 · 让注册主流程不受影响
def ensure_tenant_credits(tenant_id) -> None:
    if not tenant_id:
        return
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO tenant_credits (tenant_id, balance_thb) "
                "VALUES (%s, 0) ON CONFLICT (tenant_id) DO NOTHING",
                (str(tenant_id),),
            )
        logger.info(f"[credits] ensure_tenant_credits tenant={str(tenant_id)[:8]}.. balance=0")
    except Exception as e:
        logger.warning(f"ensure_tenant_credits skip tenant={tenant_id}: {e}")


# ============================================================
# v118.35.0.6 · credits 系统 multi-company 支持
# 从 legacy/credits-system-5de6cc5 cherry-pick · 只接 routes 用到的两个 ·
# 其他 check/deduct/owner/state 等下个版本 v36 拉前端 + OCR 扣费时一起接
# ============================================================
from datetime import datetime as _v36_dt, timedelta as _v36_td, timezone as _v36_tz

_BKK_TZ_V36 = _v36_tz(_v36_td(hours=7))


def _bkk_year_month() -> str:
    """Asia/Bangkok timezone · YYYY-MM · 月度统计锚定 UTC+7."""
    return _v36_dt.now(_BKK_TZ_V36).strftime("%Y-%m")


# ============================================================================
# v118.35.0.21 · Credits 计费业务层(v0.21 修正版 · 修 v0.20 部署后超时)
#
# v0.20 教训:
#   - 每个 OCR 加 3 次独立 DB 查询(is_exempt + balance + pages_used)
#   - maxconn=5 连接池被并发 OCR 撑爆 → 全站超时 → 回滚
#
# v0.21 修正:
#   1. maxconn 5→30(见上面 get_pool · 真凶)
#   2. get_billing_status_combined: 一次 SELECT 拿 3 个字段(取代 v0.20 三次查询)
#   3. is_user_billing_exempt: 加 5 分钟 LRU cache(白名单极少变)
#   4. charge_ocr: 由调用端 asyncio.create_task 异步触发(不阻塞 OCR 返回)
#
# 价格规则(Korn 拍板 2026-05-21):
#   PDF: 当月 ≤ 200 张 → ฿1.50/张 · > 200 张 → ฿0.75/张(跨界自动拆段)
#   Excel/Word/CSV: 50 字符 = 1 satang(฿0.01)· 向上取整
# 白名单: users.is_billing_exempt = TRUE 自动跳过
# ============================================================================
from decimal import Decimal as _DecV21
import time as _time_v21

# 白名单 LRU cache(进程内 · 5 分钟 TTL · 减少 DB 压力)
_EXEMPT_CACHE_V21: dict = {}
_EXEMPT_CACHE_TTL_V21 = 300


def is_user_billing_exempt(user_id) -> bool:
    """v0.21 · 5 分钟 cache · 白名单极少变 · 减少 DB roundtrip"""
    if not user_id:
        return False
    key = str(user_id)
    now = _time_v21.time()
    hit = _EXEMPT_CACHE_V21.get(key)
    if hit and hit[1] > now:
        return hit[0]
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT COALESCE(is_billing_exempt, FALSE) AS x "
                "FROM users WHERE id = %s::uuid LIMIT 1",
                (str(user_id),),
            )
            row = cur.fetchone()
            result = bool(row["x"]) if row else False
            _EXEMPT_CACHE_V21[key] = (result, now + _EXEMPT_CACHE_TTL_V21)
            if len(_EXEMPT_CACHE_V21) > 5000:
                # 限制 cache 体积 · 简单清理
                _EXEMPT_CACHE_V21.clear()
            return result
    except Exception as e:
        logger.warning(f"is_user_billing_exempt error user={user_id}: {e}")
        return False


def get_billing_status_combined(user_id, tenant_id) -> dict:
    """v0.21 · 一次 SELECT 拿 is_exempt + balance + pages_used_this_month
    取代 v0.20 的 3 次独立查询 · DB roundtrip 从 3 → 1。
    返: {allowed, is_exempt, balance_thb, pages_used_this_month, error_code}
    """
    # 白名单走 cache(不查 DB · 0 RTT)
    if is_user_billing_exempt(user_id):
        return {
            "allowed": True,
            "is_exempt": True,
            "balance_thb": 0.0,
            "pages_used_this_month": 0,
            "error_code": None,
        }
    if not tenant_id:
        return {
            "allowed": False,
            "is_exempt": False,
            "balance_thb": 0.0,
            "pages_used_this_month": 0,
            "error_code": "no_tenant",
        }
    try:
        ym = _bkk_year_month()
        with get_cursor() as cur:
            # 一次 SELECT 合并两个 LEFT JOIN · 一次 DB roundtrip
            cur.execute(
                """
                SELECT
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_used
                FROM (SELECT 1) AS dummy
                LEFT JOIN tenant_credits tc ON tc.tenant_id = %s::uuid
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = %s::uuid AND mpu.year_month = %s
                LIMIT 1
            """,
                (str(tenant_id), str(tenant_id), ym),
            )
            row = cur.fetchone()
            bal = float(row["balance_thb"] if row else 0)
            used = int(row["pages_used"] if row else 0)
        if bal <= 0:
            return {
                "allowed": False,
                "is_exempt": False,
                "balance_thb": bal,
                "pages_used_this_month": used,
                "error_code": "insufficient_balance",
            }
        return {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": bal,
            "pages_used_this_month": used,
            "error_code": None,
        }
    except Exception as e:
        logger.warning(f"get_billing_status_combined error tenant={tenant_id}: {e}")
        # 失败时不阻塞 OCR(降级到允许 · 但 log 警报)
        return {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": 0.0,
            "pages_used_this_month": 0,
            "error_code": "lookup_error",
        }


def charge_ocr(
    user_id, tenant_id, kind: str, units: int, history_id: str = None, description: str = ""
) -> dict:
    """OCR 完成后扣费 · v0.21 由调用端用 asyncio.create_task 异步触发
    单原子事务(SELECT FOR UPDATE 防并发)· 内部仍持有连接 · 但已脱离 OCR 关键路径
    kind: 'pdf' (units=page_count) | 'excel' (units=char_count)
    豁免账号自动跳过返 ok=True charged=0
    """
    if not tenant_id:
        return {"ok": False, "error": "no_tenant"}
    if is_user_billing_exempt(user_id):
        return {
            "ok": True,
            "charged_thb": 0.0,
            "balance_after": None,
            "kind": kind,
            "units": units,
            "transaction_id": None,
            "exempt": True,
        }

    if kind == "pdf":
        used = 0
        try:
            with get_cursor() as _c:
                _c.execute(
                    "SELECT COALESCE(pages_used, 0) AS u FROM monthly_page_usage "
                    "WHERE tenant_id = %s::uuid AND year_month = %s",
                    (str(tenant_id), _bkk_year_month()),
                )
                _r = _c.fetchone()
                used = int(_r["u"]) if _r else 0
        except Exception:
            used = 0
        cost = estimate_pdf_cost_thb(used, units)
        pages_inc = int(units)
    elif kind == "excel":
        cost = estimate_excel_cost_thb(units)
        pages_inc = 0
    else:
        return {"ok": False, "error": f"unknown_kind:{kind}"}

    if cost <= _DecV21("0"):
        return {
            "ok": True,
            "charged_thb": 0.0,
            "balance_after": None,
            "kind": kind,
            "units": units,
            "transaction_id": None,
        }

    ym = _bkk_year_month()
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "SELECT balance_thb FROM tenant_credits " "WHERE tenant_id = %s::uuid FOR UPDATE",
                (str(tenant_id),),
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    "INSERT INTO tenant_credits (tenant_id, balance_thb) "
                    "VALUES (%s::uuid, 0) RETURNING balance_thb",
                    (str(tenant_id),),
                )
                row = cur.fetchone()
            current_bal = _DecV21(str(row["balance_thb"]))
            new_bal = current_bal - cost  # 可扣到负数(OCR 已完成 · 后续充值补)

            cur.execute(
                "UPDATE tenant_credits SET balance_thb = %s, updated_at = NOW() "
                "WHERE tenant_id = %s::uuid",
                (str(new_bal), str(tenant_id)),
            )
            cur.execute(
                "INSERT INTO credit_transactions "
                "(tenant_id, user_id, type, amount_thb, pages, balance_after, description) "
                "VALUES (%s::uuid, %s::uuid, 'usage', %s, %s, %s, %s) RETURNING id",
                (
                    str(tenant_id),
                    str(user_id) if user_id else None,
                    str(-cost),
                    pages_inc,
                    str(new_bal),
                    description or f"OCR {kind} units={units} hid={history_id or ''}",
                ),
            )
            tx_id = cur.fetchone()["id"]

            if kind == "pdf" and pages_inc > 0:
                cur.execute(
                    "INSERT INTO monthly_page_usage (tenant_id, year_month, pages_used, updated_at) "
                    "VALUES (%s::uuid, %s, %s, NOW()) "
                    "ON CONFLICT (tenant_id, year_month) DO UPDATE "
                    "SET pages_used = monthly_page_usage.pages_used + EXCLUDED.pages_used, "
                    "    updated_at = NOW()",
                    (str(tenant_id), ym, pages_inc),
                )
        logger.info(
            f"[charge_ocr] OK tenant={str(tenant_id)[:8]} kind={kind} "
            f"units={units} cost=฿{cost} bal_after=฿{new_bal}"
        )
        return {
            "ok": True,
            "charged_thb": float(cost),
            "balance_after": float(new_bal),
            "kind": kind,
            "units": units,
            "transaction_id": tx_id,
        }
    except Exception as e:
        logger.error(f"[charge_ocr] FAIL tenant={tenant_id} kind={kind} units={units}: {e}")
        return {"ok": False, "error": str(e)[:200]}


def _excel_char_count_estimate(file_bytes: bytes, filename: str) -> int:
    """估算 Excel/CSV/Word 文件的总字符数 · 用于扣费"""
    if not file_bytes:
        return 0
    fn = (filename or "").lower()
    try:
        if fn.endswith(".xlsx") or fn.endswith(".xlsm") or fn.endswith(".xls"):
            try:
                import openpyxl
                import io

                wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
                total = 0
                for ws in wb.worksheets:
                    for row in ws.iter_rows(values_only=True):
                        for c in row:
                            if c is not None:
                                total += len(str(c))
                return total
            except Exception:
                return max(0, len(file_bytes) // 4)  # 粗估降级
        elif fn.endswith(".csv") or fn.endswith(".tsv") or fn.endswith(".txt"):
            try:
                return len(file_bytes.decode("utf-8", errors="ignore"))
            except Exception:
                return 0
        elif fn.endswith(".docx") or fn.endswith(".doc"):
            try:
                import docx
                import io

                doc = docx.Document(io.BytesIO(file_bytes))
                return sum(len(p.text) for p in doc.paragraphs)
            except Exception:
                return max(0, len(file_bytes) // 2)
    except Exception as e:
        logger.warning(f"_excel_char_count_estimate error fn={fn}: {e}")
    return 0


def charge_ocr_async(
    user_id, tenant_id, kind: str, units: int, history_id: str = None, description: str = ""
) -> None:
    """v0.21 · 异步扣费包装 · 调用方:
    asyncio.create_task(asyncio.to_thread(db.charge_ocr_async, ...))
    fire-and-forget · 不阻塞 OCR 关键路径 · 失败仅 log 不影响用户
    """
    try:
        result = charge_ocr(user_id, tenant_id, kind, units, history_id, description)
        if not result.get("ok"):
            logger.warning(f"[charge_ocr_async] failed silently: {result.get('error')}")
    except Exception as e:
        logger.error(f"[charge_ocr_async] exception(swallowed): {e}")


# ============================================================
# REFACTOR-B2 · services/<domain> DAL re-export
# 业务 SQL 已抽到 services/*/store.py · 在此 re-export 回 db 命名空间 ·
# `x as x` 显式 re-export 形式(pyflakes/ruff 不报 F401)。
# ============================================================
from services.email_ingest.store import (
    get_email_account as get_email_account,
    get_email_account_safe as get_email_account_safe,
    upsert_email_account as upsert_email_account,
    delete_email_account as delete_email_account,
    list_enabled_email_accounts as list_enabled_email_accounts,
    update_email_account_status as update_email_account_status,
    insert_email_ingest_log as insert_email_ingest_log,
    list_email_ingest_logs as list_email_ingest_logs,
    is_email_uid_seen as is_email_uid_seen,
    mark_email_uid_seen as mark_email_uid_seen,
)

from services.erp.oauth_store import (
    ensure_erp_oauth_tables as ensure_erp_oauth_tables,
    set_xero_auto_push as set_xero_auto_push,
    get_xero_auto_push as get_xero_auto_push,
    list_tenants_xero_auto_push_on as list_tenants_xero_auto_push_on,
    save_oauth_state as save_oauth_state,
    consume_oauth_state as consume_oauth_state,
    upsert_oauth_token as upsert_oauth_token,
    get_default_oauth_token as get_default_oauth_token,
    list_oauth_tokens as list_oauth_tokens,
    update_oauth_access_token as update_oauth_access_token,
    delete_oauth_tokens as delete_oauth_tokens,
    set_default_oauth_token as set_default_oauth_token,
)

from services.erp.mappings_store import (
    ensure_erp_mapping_tables as ensure_erp_mapping_tables,
    list_erp_client_mappings as list_erp_client_mappings,
    upsert_erp_client_mapping as upsert_erp_client_mapping,
    delete_erp_client_mapping as delete_erp_client_mapping,
    list_erp_account_mappings as list_erp_account_mappings,
    upsert_erp_account_mapping as upsert_erp_account_mapping,
    delete_erp_account_mapping as delete_erp_account_mapping,
    list_erp_tax_mappings as list_erp_tax_mappings,
    upsert_erp_tax_mapping as upsert_erp_tax_mapping,
    delete_erp_tax_mapping as delete_erp_tax_mapping,
    list_erp_product_mappings as list_erp_product_mappings,
    upsert_erp_product_mapping as upsert_erp_product_mapping,
    delete_erp_product_mapping as delete_erp_product_mapping,
    find_erp_product_mappings_batch as find_erp_product_mappings_batch,
    get_mrerp_mappings_bundle as get_mrerp_mappings_bundle,
)

from services.notification.store import (
    ensure_notification_tables as ensure_notification_tables,
    list_notification_rules as list_notification_rules,
    get_notification_rule as get_notification_rule,
    create_notification_rule as create_notification_rule,
    update_notification_rule as update_notification_rule,
    delete_notification_rule as delete_notification_rule,
    log_notification as log_notification,
    list_notification_logs as list_notification_logs,
    list_active_notification_rules_by_template as list_active_notification_rules_by_template,
)

from services.erp.push_store import (
    ERP_MAX_RETRIES as ERP_MAX_RETRIES,
    USER_DATA_ERROR_CODES as USER_DATA_ERROR_CODES,
    USER_DATA_ERROR_THAI_PATTERNS as USER_DATA_ERROR_THAI_PATTERNS,
    list_erp_endpoints as list_erp_endpoints,
    get_erp_endpoint as get_erp_endpoint,
    get_default_erp_endpoint as get_default_erp_endpoint,
    create_erp_endpoint as create_erp_endpoint,
    update_erp_endpoint as update_erp_endpoint,
    delete_erp_endpoint as delete_erp_endpoint,
    insert_push_log as insert_push_log,
    has_recent_successful_push as has_recent_successful_push,
    update_endpoint_stats as update_endpoint_stats,
    update_history_push_status as update_history_push_status,
    ensure_erp_endpoints_adapter_constraint as ensure_erp_endpoints_adapter_constraint,
    ensure_erp_push_logs_adapter_constraint as ensure_erp_push_logs_adapter_constraint,
    ensure_erp_push_logs_status_constraint as ensure_erp_push_logs_status_constraint,
    ensure_erp_retry_columns as ensure_erp_retry_columns,
    is_user_data_error as is_user_data_error,
    is_already_pushed_error as is_already_pushed_error,
    classify_push_status as classify_push_status,
    get_erp_retry_delay_sec as get_erp_retry_delay_sec,
    schedule_log_retry as schedule_log_retry,
    clear_retry_schedule as clear_retry_schedule,
    list_logs_due_for_retry as list_logs_due_for_retry,
    increment_retry_count as increment_retry_count,
    update_log_status_after_retry as update_log_status_after_retry,
    delete_push_logs as delete_push_logs,
    list_push_logs as list_push_logs,
    get_push_log_detail as get_push_log_detail,
    get_push_stats_today as get_push_stats_today,
    list_push_exceptions as list_push_exceptions,
    classify_push_exception as classify_push_exception,
)

from services.recon.bank_recon_v2_store import (
    ensure_bank_recon_v2_table as ensure_bank_recon_v2_table,
    create_bank_recon_v2_task as create_bank_recon_v2_task,
    get_bank_recon_v2_task as get_bank_recon_v2_task,
    list_bank_recon_v2_tasks as list_bank_recon_v2_tasks,
    delete_bank_recon_v2_task as delete_bank_recon_v2_task,
    delete_bank_recon_v2_tasks_batch as delete_bank_recon_v2_tasks_batch,
)

from services.recon.gl_vat_store import (
    ensure_gl_vat_task_table as ensure_gl_vat_task_table,
    create_gl_vat_task as create_gl_vat_task,
    get_gl_vat_task as get_gl_vat_task,
    list_gl_vat_tasks as list_gl_vat_tasks,
    delete_gl_vat_task as delete_gl_vat_task,
    delete_gl_vat_tasks_batch as delete_gl_vat_tasks_batch,
)

from services.recon.vat_recon_tasks_store import (
    ensure_vat_recon_tasks_table as ensure_vat_recon_tasks_table,
    create_vat_recon_task as create_vat_recon_task,
    list_vat_recon_tasks as list_vat_recon_tasks,
    get_vat_recon_task as get_vat_recon_task,
    delete_vat_recon_task as delete_vat_recon_task,
    delete_vat_recon_tasks_older_than as delete_vat_recon_tasks_older_than,
    get_vat_recon_tasks_kpi as get_vat_recon_tasks_kpi,
)

from services.recon.bank_recon_v1_store import (
    ensure_bank_recon_client_id_column as ensure_bank_recon_client_id_column,
    create_bank_recon_session as create_bank_recon_session,
    save_bank_recon_parse as save_bank_recon_parse,
    mark_recon_parse_failed as mark_recon_parse_failed,
    get_bank_recon_session as get_bank_recon_session,
    list_bank_recon_sessions as list_bank_recon_sessions,
    update_bank_recon_session_client as update_bank_recon_session_client,
    get_bank_recon_stats as get_bank_recon_stats,
    list_bank_recon_transactions as list_bank_recon_transactions,
    delete_bank_recon_session as delete_bank_recon_session,
    find_invoice_candidates_for_tx as find_invoice_candidates_for_tx,
    save_match_result as save_match_result,
    get_tx_candidates as get_tx_candidates,
    update_session_match_stats as update_session_match_stats,
    override_tx_match as override_tx_match,
    seed_bank_recon_test_data as seed_bank_recon_test_data,
    clear_bank_recon_test_data as clear_bank_recon_test_data,
)

from services.audit.store import (
    insert_operation_log as insert_operation_log,
    list_operation_logs as list_operation_logs,
    list_operation_logs_paged as list_operation_logs_paged,
)

from services.team.store import (
    list_employees as list_employees,
    add_employee as add_employee,
    remove_employee as remove_employee,
    toggle_employee_active as toggle_employee_active,
)

from services.recon.vat_recon_store import (
    ensure_vat_recon_tables as ensure_vat_recon_tables,
    create_vat_report as create_vat_report,
    get_vat_report as get_vat_report,
    create_recon_task as create_recon_task,
    get_recon_task as get_recon_task,
    update_recon_task_status as update_recon_task_status,
    update_recon_task_completed as update_recon_task_completed,
    list_recon_tasks as list_recon_tasks,
    bulk_insert_recon_rows as bulk_insert_recon_rows,
    list_recon_rows as list_recon_rows,
    list_invoices_for_recon as list_invoices_for_recon,
    find_client_by_tax_id as find_client_by_tax_id,
    auto_create_client as auto_create_client,
    get_recon_row as get_recon_row,
    update_recon_row_ai_analysis as update_recon_row_ai_analysis,
    update_recon_row_action as update_recon_row_action,
    list_recon_rows_detailed as list_recon_rows_detailed,
    get_client_by_id as get_client_by_id,
    find_or_create_client_by_tax_id as find_or_create_client_by_tax_id,
)

from services.archive.store import (
    get_archive_settings as get_archive_settings,
    get_archive_template as get_archive_template,
    upsert_archive_settings as upsert_archive_settings,
)

from services.rd.store import (
    get_rd_daily_usage as get_rd_daily_usage,
    increment_rd_daily_usage as increment_rd_daily_usage,
)

from services.cost.store import (
    ensure_ocr_cost_log_table as ensure_ocr_cost_log_table,
    log_ocr_cost as log_ocr_cost,
    get_cost_overview as get_cost_overview,
    get_cost_by_user as get_cost_by_user,
    get_cost_daily_trend as get_cost_daily_trend,
    get_cost_daily_by_engine as get_cost_daily_by_engine,
)

from services.exceptions.store import (
    ensure_exceptions_tables as ensure_exceptions_tables,
    is_exception_whitelisted as is_exception_whitelisted,
    insert_exception as insert_exception,
    list_exceptions as list_exceptions,
    get_exception as get_exception,
    resolve_exception as resolve_exception,
    add_exception_whitelist as add_exception_whitelist,
    list_exception_whitelist as list_exception_whitelist,
    delete_exception_whitelist as delete_exception_whitelist,
    delete_pending_exceptions_by_history as delete_pending_exceptions_by_history,
    count_exceptions_by_status_and_rule as count_exceptions_by_status_and_rule,
    count_whitelist_rules as count_whitelist_rules,
    batch_resolve_exceptions as batch_resolve_exceptions,
)

from services.billing.store import (
    ensure_billing_balance_table as ensure_billing_balance_table,
    get_latest_balance as get_latest_balance,
)

from services.clients.store import (
    ensure_clients_table as ensure_clients_table,
    ensure_supplier_categories_table as ensure_supplier_categories_table,
    get_category_for_seller as get_category_for_seller,
    ensure_buyer_to_client_table as ensure_buyer_to_client_table,
    learn_buyer_to_client as learn_buyer_to_client,
    try_resolve_buyer_to_client as try_resolve_buyer_to_client,
    resolve_or_create_buyer_client as resolve_or_create_buyer_client,
    update_history_client_id as update_history_client_id,
    upsert_supplier_category as upsert_supplier_category,
    list_used_categories as list_used_categories,
    count_supplier_mappings as count_supplier_mappings,
    list_clients as list_clients,
    get_client as get_client,
    create_client as create_client,
    update_client as update_client,
    delete_client as delete_client,
    assign_invoice_to_client as assign_invoice_to_client,
)

# B0 地基(2026-05-25)· workspace_clients 账套主体 DAL(独立于买方 clients 表)
from services.workspace.store import (
    ensure_workspace_tables as ensure_workspace_tables,
    create_workspace_client as create_workspace_client,
    get_workspace_client as get_workspace_client,
    list_workspace_clients as list_workspace_clients,
    list_workspace_clients_enriched as list_workspace_clients_enriched,
    update_workspace_client as update_workspace_client,
    archive_workspace_client as archive_workspace_client,
    bind_workspace_endpoint as bind_workspace_endpoint,
    get_workspace_endpoint_id as get_workspace_endpoint_id,
    match_workspace_for_seller as match_workspace_for_seller,
    update_history_workspace_client_id as update_history_workspace_client_id,
    ensure_seller_route_table as ensure_seller_route_table,
    learn_seller_workspace_route as learn_seller_workspace_route,
)

# REFACTOR-B2 · membership/tenant DAL re-export(域已抽到 services/ · 调用点零改动)
from services.membership.store import (
    get_visible_client_ids_for_user as get_visible_client_ids_for_user,
    list_assignments_by_employees as list_assignments_by_employees,
    set_employee_assignments as set_employee_assignments,
    auto_assign_client_to_creator as auto_assign_client_to_creator,
    get_user_tenant_id as get_user_tenant_id,
    migrate_to_membership_model as migrate_to_membership_model,
    list_orphan_users as list_orphan_users,
    fix_orphan_users as fix_orphan_users,
    backfill_tenant_ids as backfill_tenant_ids,
)
from services.tenant.store import (
    get_tenant as get_tenant,
    get_user_tenant as get_user_tenant,
    list_all_tenants as list_all_tenants,
    create_tenant as create_tenant,
    update_tenant_quota as update_tenant_quota,
    update_tenant_status as update_tenant_status,
    get_tenant_monthly_usage as get_tenant_monthly_usage,
    increment_tenant_monthly_usage as increment_tenant_monthly_usage,
    list_tenant_members as list_tenant_members,
    get_tenant_usage_summary as get_tenant_usage_summary,
    list_all_owner_users as list_all_owner_users,
    create_owner_user as create_owner_user,
    preview_owner_cascade as preview_owner_cascade,
    delete_owner_user_cascade as delete_owner_user_cascade,
)

# REFACTOR-B2 · user_settings DAL re-export(用户级设置/偏好已抽到 services/user_settings · 调用点零改动)
from services.user_settings.store import (
    ERP_PUSH_MODES as ERP_PUSH_MODES,
    get_user_dup_check_enabled as get_user_dup_check_enabled,
    set_user_dup_check_enabled as set_user_dup_check_enabled,
    get_erp_push_mode as get_erp_push_mode,
    set_erp_push_mode as set_erp_push_mode,
    set_user_gemini_key as set_user_gemini_key,
    get_user_gemini_key as get_user_gemini_key,
    get_user_gemini_key_masked as get_user_gemini_key_masked,
)

# REFACTOR-B2 · ocr_history 读/改/删 DAL re-export(已抽到 services/ocr_history/store · 调用点零改动)
from services.ocr_history.store import (
    list_ocr_history as list_ocr_history,
    get_ocr_history_detail as get_ocr_history_detail,
    update_ocr_history_pages as update_ocr_history_pages,
    delete_ocr_history as delete_ocr_history,
    delete_ocr_history_with_pdf_paths as delete_ocr_history_with_pdf_paths,
)

# REFACTOR-B2 · ocr_history 写入/去重 DAL re-export(已抽到 services/ocr_history/store · 调用点零改动)
from services.ocr_history.store import (
    insert_ocr_history as insert_ocr_history,
    get_history_pdf_info as get_history_pdf_info,
    find_ocr_by_hash as find_ocr_by_hash,
    check_duplicate_invoice as check_duplicate_invoice,
    _extract_summary_fields as _extract_summary_fields,
)

# REFACTOR-B2 · LINE 绑定 DAL re-export(已抽到 services/line_binding/store · 调用点零改动)
from services.line_binding.store import (
    generate_line_binding_code as generate_line_binding_code,
    consume_line_binding_code as consume_line_binding_code,
    create_or_update_line_binding as create_or_update_line_binding,
    get_line_binding_by_user as get_line_binding_by_user,
    get_user_by_line_user_id as get_user_by_line_user_id,
    unbind_line_by_user as unbind_line_by_user,
)

# REFACTOR-B2 · credits 只读分析 DAL re-export(已抽到 services/credits/store · 调用点零改动)
from services.credits.store import (
    get_credits_revenue_overview as get_credits_revenue_overview,
    get_tenants_credits_summary as get_tenants_credits_summary,
    get_tenant_credit_summary as get_tenant_credit_summary,
    get_credits_daily_trend as get_credits_daily_trend,
)

# REFACTOR-B2 · 多公司成员/当前账套 DAL re-export(已抽到 services/tenant/store · 调用点零改动)
from services.tenant.store import (
    list_user_companies as list_user_companies,
    set_user_active_tenant as set_user_active_tenant,
)

# REFACTOR-B2 · 定价/成本估算 re-export(已抽到 services/billing/pricing · charge_ocr 裸名 + 外部 db.* 零改动)
from services.billing.pricing import (
    estimate_pdf_cost_thb as estimate_pdf_cost_thb,
    estimate_excel_cost_thb as estimate_excel_cost_thb,
    PDF_TIER1_LIMIT_V21 as PDF_TIER1_LIMIT_V21,
    PDF_TIER1_PRICE_V21 as PDF_TIER1_PRICE_V21,
    PDF_TIER2_PRICE_V21 as PDF_TIER2_PRICE_V21,
    EXCEL_CHARS_PER_SATANG_V21 as EXCEL_CHARS_PER_SATANG_V21,
    EXCEL_SATANG_PRICE_V21 as EXCEL_SATANG_PRICE_V21,
)

# REFACTOR-B2 · 用户偏好语言 re-export(已抽到 services/user_settings/store · 调用点零改动)
from services.user_settings.store import (
    update_user_preferred_lang as update_user_preferred_lang,
)

# REFACTOR-B2 · 用户查找 + OAuth 关联 re-export(已抽到 services/auth/user_lookup · 调用点零改动)
from services.auth.user_lookup import (
    find_user_by_username as find_user_by_username,
    find_user_by_id as find_user_by_id,
    find_user_by_google_sub as find_user_by_google_sub,
    link_google_sub_to_user as link_google_sub_to_user,
    update_user_avatar as update_user_avatar,
    find_user_by_line_uid as find_user_by_line_uid,
    link_line_uid_to_user as link_line_uid_to_user,
)

# REFACTOR-B2 · 密码 verify/reset re-export(已抽到 services/auth/password · 调用点零改动)
from services.auth.password import (
    verify_user_password as verify_user_password,
    reset_user_password as reset_user_password,
)
