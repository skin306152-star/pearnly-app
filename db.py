# -*- coding: utf-8 -*-
"""
Mr.Pearnly · 数据库模块(v3)
第 3.5 批:支持新权限字段 + ensure_demo 更新字段
"""

import os
import logging
import bcrypt
from typing import Optional, Dict, Any, List
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


def ensure_demo_account():
    """启动时确保 demo (Free) 和 demo_plus (Plus 200) 账号存在 · 幂等"""
    _ensure_one_account(
        username=os.environ.get("DEMO_USERNAME", "demo"),
        password=os.environ.get("DEMO_PASSWORD", "demo2026"),
        plan="free",
        monthly_quota=0,
        can_use_gemini=False,
        can_edit_fields=False,
        can_verify_tax=False,
        can_use_custom_template=False,
        can_view_history=False,
        can_use_typhoon=False,
        can_push_erp=False,
        can_use_automation=False,
        can_manage_api_keys=False,
        typhoon_quota_monthly=0,
        history_retention_days=0,
        custom_template_limit=0,
        notes="公共测试账号 · Free · 按 IP 每天限流",
    )
    _ensure_one_account(
        username=os.environ.get("DEMO_PLUS_USERNAME", "demo_plus"),
        password=os.environ.get("DEMO_PLUS_PASSWORD", "demoplus2026"),
        plan="plus",
        monthly_quota=200,  # 最低档 Plus 200
        can_use_gemini=True,
        can_edit_fields=True,
        can_verify_tax=True,
        can_use_custom_template=True,
        can_view_history=True,
        can_use_typhoon=False,  # 下批再做
        can_push_erp=True,
        can_use_automation=True,
        can_manage_api_keys=False,
        typhoon_quota_monthly=0,
        history_retention_days=90,
        custom_template_limit=3,
        notes="Plus 测试账号 · 200 张/月 · Gemini Flash",
    )


def _ensure_one_account(
    username,
    password,
    plan,
    monthly_quota,
    can_use_gemini,
    can_edit_fields,
    can_verify_tax,
    can_use_custom_template,
    can_view_history,
    can_use_typhoon,
    can_push_erp,
    can_use_automation,
    can_manage_api_keys,
    typhoon_quota_monthly,
    history_retention_days,
    custom_template_limit,
    notes,
):
    correct_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    try:
        with get_cursor(commit=True) as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            row = cur.fetchone()

            if row:
                cur.execute(
                    """
                    UPDATE users SET
                        password_hash = %s,
                        plan = %s,
                        monthly_quota = %s,
                        can_use_gemini = %s,
                        can_edit_fields = %s,
                        can_verify_tax = %s,
                        can_use_custom_template = %s,
                        can_view_history = %s,
                        can_use_typhoon = %s,
                        can_push_erp = %s,
                        can_use_automation = %s,
                        can_manage_api_keys = %s,
                        typhoon_quota_monthly = %s,
                        history_retention_days = %s,
                        custom_template_limit = %s,
                        is_active = TRUE
                    WHERE id = %s
                """,
                    (
                        correct_hash,
                        plan,
                        monthly_quota,
                        can_use_gemini,
                        can_edit_fields,
                        can_verify_tax,
                        can_use_custom_template,
                        can_view_history,
                        can_use_typhoon,
                        can_push_erp,
                        can_use_automation,
                        can_manage_api_keys,
                        typhoon_quota_monthly,
                        history_retention_days,
                        custom_template_limit,
                        row["id"],
                    ),
                )
                logger.info(f"✅ {username} 账号已同步({plan} 权限)")
            else:
                cur.execute(
                    """
                    INSERT INTO users (
                        username, password_hash, plan, monthly_quota,
                        can_use_gemini, can_edit_fields, can_verify_tax,
                        can_use_custom_template, can_view_history, can_use_typhoon,
                        can_push_erp, can_use_automation, can_manage_api_keys,
                        typhoon_quota_monthly, history_retention_days, custom_template_limit,
                        notes, is_active
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, TRUE
                    )
                """,
                    (
                        username,
                        correct_hash,
                        plan,
                        monthly_quota,
                        can_use_gemini,
                        can_edit_fields,
                        can_verify_tax,
                        can_use_custom_template,
                        can_view_history,
                        can_use_typhoon,
                        can_push_erp,
                        can_use_automation,
                        can_manage_api_keys,
                        typhoon_quota_monthly,
                        history_retention_days,
                        custom_template_limit,
                        notes,
                    ),
                )
                logger.info(f"✅ {username} 账号已创建({plan})")
    except Exception as e:
        logger.error(f"❌ 初始化账号失败 ({username}): {e}")
        raise


def find_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (username,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询用户失败 ({username}): {e}")
        return None


def find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询用户失败 (id={user_id}): {e}")
        return None


# ============================================================
# v118.27.5 · Google OAuth 关联(google_sub = Google 用户唯一 ID)
# ============================================================
def find_user_by_google_sub(google_sub: str) -> Optional[Dict[str, Any]]:
    if not google_sub:
        return None
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE google_sub = %s LIMIT 1", (google_sub,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询用户失败 (google_sub={google_sub}): {e}")
        return None


def link_google_sub_to_user(user_id: str, google_sub: str) -> bool:
    if not user_id or not google_sub:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET google_sub = %s WHERE id = %s", (google_sub, user_id))
        return True
    except Exception as e:
        logger.error(f"绑定 google_sub 失败 (user_id={user_id}): {e}")
        return False


def ensure_google_sub_column():
    """v118.27.5 · 启动时自动加 google_sub 列(幂等 · IF NOT EXISTS)
    v118.27.5.3 · 同时加 avatar_url 列(Google OAuth picture URL)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub TEXT")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL"
            )
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT")
        logger.info("[v118.27.5.3] users.google_sub + avatar_url 列就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.27.5.3] 加列失败: {e}")
        return False


def update_user_avatar(user_id: str, avatar_url: str) -> bool:
    if not user_id or not avatar_url:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (avatar_url, user_id))
        return True
    except Exception as e:
        logger.error(f"更新 avatar_url 失败 (user_id={user_id}): {e}")
        return False


# ============================================================
# v118.28.4 · LINE Login OAuth 关联(line_uid = LINE user ID · sub claim)
# ============================================================
def find_user_by_line_uid(line_uid: str) -> Optional[Dict[str, Any]]:
    if not line_uid:
        return None
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE line_uid = %s LIMIT 1", (line_uid,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询用户失败 (line_uid={line_uid}): {e}")
        return None


def link_line_uid_to_user(user_id: str, line_uid: str) -> bool:
    if not user_id or not line_uid:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET line_uid = %s WHERE id = %s", (line_uid, user_id))
        return True
    except Exception as e:
        logger.error(f"绑定 line_uid 失败 (user_id={user_id}): {e}")
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


def get_ip_usage_today(ip: str) -> int:
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT count FROM ip_usage
                WHERE ip_address = %s AND usage_date = CURRENT_DATE LIMIT 1
            """,
                (ip,),
            )
            row = cur.fetchone()
            return row["count"] if row else 0
    except Exception as e:
        logger.error(f"查询 IP 用量失败: {e}")
        return 0


def increment_ip_usage(ip: str, n: int = 1) -> int:
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO ip_usage (ip_address, usage_date, count)
                VALUES (%s, CURRENT_DATE, %s)
                ON CONFLICT (ip_address, usage_date)
                DO UPDATE SET count = ip_usage.count + %s
                RETURNING count
            """,
                (ip, n, n),
            )
            row = cur.fetchone()
            return row["count"] if row else 0
    except Exception as e:
        logger.error(f"更新 IP 用量失败: {e}")
        return 0


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


def increment_typhoon_usage(user_id: str, n: int = 1) -> int:
    """
    v0.12 · 累加本月 Typhoon 增援次数(独立配额)
    跨月自动重置 · 失败返回 0(不影响主流程)
    """
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE users SET
                    typhoon_used_this_month = CASE
                        WHEN typhoon_last_usage_month IS NULL
                          OR typhoon_last_usage_month < DATE_TRUNC('month', NOW())::date
                        THEN %s
                        ELSE COALESCE(typhoon_used_this_month, 0) + %s
                    END,
                    typhoon_last_usage_month = DATE_TRUNC('month', NOW())::date
                WHERE id = %s
                RETURNING typhoon_used_this_month
            """,
                (n, n, user_id),
            )
            row = cur.fetchone()
            return row["typhoon_used_this_month"] if row else 0
    except Exception as e:
        logger.warning(f"更新 Typhoon 用量失败 · 但不影响识别 (user_id={user_id}): {e}")
        return 0


def get_user_monthly_usage(user_id: str) -> int:
    """查询某用户本月已用次数(若跨月返回 0)"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    CASE
                        WHEN last_usage_month IS NULL
                          OR last_usage_month < DATE_TRUNC('month', NOW())::date
                        THEN 0
                        ELSE COALESCE(used_this_month, 0)
                    END AS used
                FROM users WHERE id = %s LIMIT 1
            """,
                (user_id,),
            )
            row = cur.fetchone()
            return row["used"] if row else 0
    except Exception as e:
        logger.error(f"查询用户月用量失败 (user_id={user_id}): {e}")
        return 0


# ============================================================
# 第 5 批 · 历史记录(ocr_history 表)
# ============================================================

import json as _json
from datetime import datetime as _datetime


def _extract_summary_fields(pages: list) -> dict:
    """从 pages 抽出列表展示用的核心字段
    v106.2 修复:多联发票(底单/发票/收据 3 页) Gemini 可能把所有页都标 is_copy=true ·
    导致摘要字段全 None · 列表显示「未识别到 · 金额 · 发票号 · 日期 · 卖方」误报
    改进:先找非副本主页 · 找不到再用 is_duplicate=False 的页 · 最后兜底用第 1 页
    """
    pages = pages or []

    def _build_from_page(p):
        f = p.get("fields") or {}
        raw_date = f.get("date")
        invoice_date = None
        if raw_date:
            try:
                s = str(raw_date).replace("/", "-")[:10]
                _datetime.strptime(s, "%Y-%m-%d")
                invoice_date = s
            except Exception:
                invoice_date = None
        raw_amt = f.get("total_amount")
        total = None
        if raw_amt is not None:
            try:
                total = float(str(raw_amt).replace(",", ""))
            except Exception:
                total = None
        return {
            "invoice_no": (f.get("invoice_number") or "")[:200] or None,
            "invoice_date": invoice_date,
            "seller_name": (f.get("seller_name") or "")[:200] or None,
            "total_amount": total,
        }

    # 1. 优先 · 非副本主页(是非 is_copy 也非 is_duplicate)
    for p in pages:
        if not p.get("is_copy") and not p.get("is_duplicate"):
            f = p.get("fields") or {}
            if f.get("invoice_number") or f.get("total_amount") or f.get("seller_name"):
                return _build_from_page(p)

    # 2. 兜底 · 全部 is_copy/is_duplicate 时 · 选有最多关键字段的那页
    def _score(p):
        f = p.get("fields") or {}
        s = 0
        if f.get("invoice_number"):
            s += 1
        if f.get("total_amount"):
            s += 1
        if f.get("seller_name"):
            s += 1
        if f.get("date"):
            s += 1
        return s

    if pages:
        best = max(pages, key=_score)
        if _score(best) > 0:
            return _build_from_page(best)

    return {"invoice_no": None, "invoice_date": None, "seller_name": None, "total_amount": None}


def insert_ocr_history(
    user_id: str,
    filename: str,
    page_count: int,
    pages: list,
    confidence: str,
    elapsed_ms: int,
    file_size_kb: Optional[int] = None,
    file_hash: Optional[str] = None,
    archive_name: Optional[str] = None,
    category_tag: Optional[str] = None,
    # v0.11 · 多发票拆分字段
    source_pdf_id: Optional[str] = None,
    source_page_indices: Optional[list] = None,
    source_index: Optional[int] = None,
    source_total: Optional[int] = None,
    # v0.17 · M6 · 来源标识
    source: str = "manual",
    source_ref: Optional[str] = None,
    # v114 · PDF 留底
    pdf_storage_path: Optional[str] = None,
    pdf_size_bytes: Optional[int] = None,
    # v27.8.1.13a · 上传时自动归属客户(右上角客户切换器选中 / 文件夹绑定 / 邮件别名等)
    client_id: Optional[int] = None,
    # 2026-05-24 · 多租户:历史归属租户(原缺失 → tenant_id 恒 NULL → 按租户查历史/对账漏)
    tenant_id: Optional[str] = None,
) -> Optional[str]:
    """写入一条历史记录,返回新记录的 id(失败返回 None,不影响主流程)"""
    summary = _extract_summary_fields(pages)
    # v27.8.1.13a · 客户归属:校验 client_id 真属于该 user 的 tenant,防越权
    safe_client_id = None
    if client_id is not None:
        try:
            cid = int(client_id)
            with get_cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM clients
                    WHERE id = %s
                      AND user_id IN (
                          SELECT id FROM users
                          WHERE tenant_id = (SELECT tenant_id FROM users WHERE id = %s)
                            OR id = %s
                      )
                    LIMIT 1
                """,
                    (cid, user_id, user_id),
                )
                if cur.fetchone():
                    safe_client_id = cid
        except Exception as e:
            logger.warning(
                f"insert_ocr_history client_id 校验失败 (user_id={user_id}, client_id={client_id}): {e}"
            )
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO ocr_history (
                    user_id, tenant_id, filename, page_count, file_size_kb, file_hash,
                    pages, confidence, elapsed_ms,
                    invoice_no, invoice_date, seller_name, total_amount,
                    archive_name, category_tag, archived_at,
                    source_pdf_id, source_page_indices, source_index, source_total,
                    source, source_ref,
                    pdf_storage_path, pdf_size_bytes,
                    client_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s::jsonb, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, CASE WHEN %s IS NOT NULL THEN NOW() ELSE NULL END,
                    %s, %s::jsonb, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s
                )
                RETURNING id
            """,
                (
                    user_id,
                    str(tenant_id) if tenant_id else None,
                    filename,
                    page_count,
                    file_size_kb,
                    file_hash,
                    _json.dumps(pages, ensure_ascii=False),
                    confidence,
                    elapsed_ms,
                    summary["invoice_no"],
                    summary["invoice_date"],
                    summary["seller_name"],
                    summary["total_amount"],
                    archive_name,
                    category_tag,
                    archive_name,
                    source_pdf_id,
                    _json.dumps(source_page_indices) if source_page_indices else None,
                    source_index,
                    source_total,
                    source,
                    source_ref,
                    pdf_storage_path,
                    pdf_size_bytes,
                    safe_client_id,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"写入历史记录失败 (user_id={user_id}, file={filename}): {e}")
        return None


def get_history_pdf_info(
    user_id: str, record_id: str, tenant_id: Optional[str] = None
) -> Optional[dict]:
    """v114 · 取一条历史的 PDF 留底信息(只查路径 · 鉴权用 user_id)
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可下载 PDF
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT pdf_storage_path, pdf_size_bytes, filename
                    FROM ocr_history
                    WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    LIMIT 1
                """,
                    (record_id, tenant_id),
                )
            else:
                cur.execute(
                    """
                    SELECT pdf_storage_path, pdf_size_bytes, filename
                    FROM ocr_history
                    WHERE id = %s AND user_id = %s
                    LIMIT 1
                """,
                    (record_id, user_id),
                )
            r = cur.fetchone()
            if not r or not r.get("pdf_storage_path"):
                return None
            return {
                "pdf_storage_path": r["pdf_storage_path"],
                "pdf_size_bytes": r.get("pdf_size_bytes"),
                "filename": r.get("filename"),
            }
    except Exception as e:
        logger.error(f"get_history_pdf_info 失败 (record_id={record_id}): {e}")
        return None


def find_ocr_by_hash(
    user_id: str, file_hash: str, max_age_hours: int = 24 * 30, tenant_id: Optional[str] = None
) -> Optional[dict]:
    """
    按文件哈希查最近的识别结果。
    用于避免重复识别相同文件(省 Gemini 额度)

    v92 · 窗口从 24h 扩到 30 天 · 会计真实场景下月末才会复核上月票 · 24h 太短
    v92 · 只返回有效结果 · 识别失败(关键字段全空)的记录视为未命中 · 配合第 1 层防御
    v118.14 · tenant_id 给了 → 同 tenant 内任意成员上传过此文件就能复用结果(省额度)
    """
    if not file_hash:
        return None
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, filename, page_count, confidence, elapsed_ms, pages,
                           archive_name, category_tag, created_at
                    FROM ocr_history
                    WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                      AND file_hash = %s
                      AND created_at >= NOW() - INTERVAL '%s hours'
                      AND pages IS NOT NULL
                      AND jsonb_array_length(pages) > 0
                      AND (total_amount IS NOT NULL OR invoice_no IS NOT NULL OR seller_name IS NOT NULL)
                    ORDER BY created_at DESC
                    LIMIT 1
                """ % ("%s", "%s", int(max_age_hours)),
                    (tenant_id, file_hash),
                )
            else:
                cur.execute(
                    """
                    SELECT id, filename, page_count, confidence, elapsed_ms, pages,
                           archive_name, category_tag, created_at
                    FROM ocr_history
                    WHERE user_id = %s
                      AND file_hash = %s
                      AND created_at >= NOW() - INTERVAL '%s hours'
                      AND pages IS NOT NULL
                      AND jsonb_array_length(pages) > 0
                      AND (total_amount IS NOT NULL OR invoice_no IS NOT NULL OR seller_name IS NOT NULL)
                    ORDER BY created_at DESC
                    LIMIT 1
                """ % ("%s", "%s", int(max_age_hours)),
                    (user_id, file_hash),
                )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "id": str(r["id"]),
                "filename": r["filename"],
                "page_count": r["page_count"],
                "confidence": r["confidence"],
                "elapsed_ms": r["elapsed_ms"],
                "pages": r["pages"],
                "archive_name": r.get("archive_name"),
                "category_tag": r.get("category_tag"),
                "created_at": r["created_at"].isoformat(),
            }
    except Exception as e:
        logger.error(f"查缓存失败 (hash={file_hash[:12]}): {e}")
        return None


def check_duplicate_invoice(
    user_id: str,
    invoice_no: Optional[str],
    invoice_date: Optional[str],
    seller_name: Optional[str],
    total_amount: Optional[float],
    exclude_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    v0.13 · 重复发票检测 · 仅当前用户的历史
    返回 None 表示无重复 · 返回 dict 表示有重复 · 含:
      {
        "level": "exact" | "likely",   # exact=发票号严格匹配 / likely=字段组合匹配
        "match": { id, filename, invoice_no, invoice_date, seller_name, total_amount, created_at },
        "matched_fields": [...]         # 匹配上的字段
      }

    第 1 层 · invoice_no 严格匹配(大小写不敏感)
    第 2 层 · 发票号缺失时 · 用 (date+seller+amount) 三字段匹配
    """
    try:
        with get_cursor() as cur:
            # ─────────────────────────────────────────
            # 第 1 层 · 发票号严格匹配
            # ─────────────────────────────────────────
            inv = (invoice_no or "").strip()
            if inv:
                where_extra = ""
                params = [user_id, inv.lower()]
                if exclude_id:
                    where_extra = " AND id != %s"
                    params.append(exclude_id)
                cur.execute(
                    f"""
                    SELECT id, filename, invoice_no, invoice_date, seller_name,
                           total_amount, created_at
                    FROM ocr_history
                    WHERE user_id = %s
                      AND invoice_no IS NOT NULL
                      AND invoice_no != ''
                      AND LOWER(invoice_no) = %s
                      {where_extra}
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    params,
                )
                row = cur.fetchone()
                if row:
                    return {
                        "level": "exact",
                        "matched_fields": ["invoice_no"],
                        "match": {
                            "id": str(row["id"]),
                            "filename": row["filename"],
                            "invoice_no": row["invoice_no"],
                            "invoice_date": (
                                row["invoice_date"].isoformat() if row["invoice_date"] else None
                            ),
                            "seller_name": row["seller_name"],
                            "total_amount": (
                                float(row["total_amount"])
                                if row["total_amount"] is not None
                                else None
                            ),
                            "created_at": row["created_at"].isoformat(),
                        },
                    }

            # ─────────────────────────────────────────
            # 第 2 层 · 字段组合(发票号缺失时)
            # 必须 3 个字段都有 · 才查
            # ─────────────────────────────────────────
            if invoice_date and total_amount is not None and (seller_name or "").strip():
                where_extra = ""
                params = [user_id, invoice_date, float(total_amount), (seller_name or "").strip()]
                if exclude_id:
                    where_extra = " AND id != %s"
                    params.append(exclude_id)
                cur.execute(
                    f"""
                    SELECT id, filename, invoice_no, invoice_date, seller_name,
                           total_amount, created_at
                    FROM ocr_history
                    WHERE user_id = %s
                      AND invoice_date = %s
                      AND total_amount = %s
                      AND seller_name IS NOT NULL
                      AND LOWER(seller_name) = LOWER(%s)
                      {where_extra}
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    params,
                )
                row = cur.fetchone()
                if row:
                    return {
                        "level": "likely",
                        "matched_fields": ["invoice_date", "seller_name", "total_amount"],
                        "match": {
                            "id": str(row["id"]),
                            "filename": row["filename"],
                            "invoice_no": row["invoice_no"],
                            "invoice_date": (
                                row["invoice_date"].isoformat() if row["invoice_date"] else None
                            ),
                            "seller_name": row["seller_name"],
                            "total_amount": (
                                float(row["total_amount"])
                                if row["total_amount"] is not None
                                else None
                            ),
                            "created_at": row["created_at"].isoformat(),
                        },
                    }
        return None
    except Exception as e:
        logger.warning(f"重复检测失败(不影响识别): {e}")
        return None


def get_user_dup_check_enabled(user_id: str) -> bool:
    """读取用户的重复检测开关(默认 True)"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT dup_check_enabled FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return True
            v = row.get("dup_check_enabled")
            return True if v is None else bool(v)
    except Exception:
        return True


def set_user_dup_check_enabled(user_id: str, enabled: bool) -> bool:
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET dup_check_enabled = %s WHERE id = %s", (bool(enabled), user_id)
            )
        return True
    except Exception as e:
        logger.error(f"更新重复检测开关失败: {e}")
        return False


# ============================================================
# v0.15 · 用户自带 Gemini API Key(买断用户)
# ============================================================
def set_user_gemini_key(user_id: str, api_key: Optional[str]) -> bool:
    """
    保存用户自带的 Gemini API Key
    api_key 为空串 / None 时 → 清空(切回系统 key)
    """
    val = (api_key or "").strip() or None
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET gemini_api_key = %s WHERE id = %s", (val, user_id))
        return True
    except Exception as e:
        logger.error(f"保存 Gemini key 失败: {e}")
        return False


def get_user_gemini_key(user_id: str) -> Optional[str]:
    """读取明文(后端内部用 · 不返回给前端)"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT gemini_api_key FROM users WHERE id = %s", (user_id,))
            r = cur.fetchone()
            if r and r.get("gemini_api_key"):
                return r["gemini_api_key"]
    except Exception as e:
        logger.warning(f"读 Gemini key 失败: {e}")
    return None


def get_user_gemini_key_masked(user_id: str) -> dict:
    """
    给前端用 · 只返回遮罩信息
    {has_key: bool, preview: str}  preview 例:'AIza***...x9Y2'
    """
    k = get_user_gemini_key(user_id)
    if not k:
        return {"has_key": False, "preview": ""}
    # 只显示前 4 + 后 4
    if len(k) <= 8:
        preview = "*" * len(k)
    else:
        preview = f"{k[:4]}...{k[-4:]}"
    return {"has_key": True, "preview": preview}


def list_ocr_history(
    user_id: str,
    retention_days: Optional[int] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant_id: Optional[str] = None,
    client_id: Optional[int] = None,
    restrict_client_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    分页列表查询。
    retention_days: None=自动从 user 表拉(向后兼容老调用方漏传)
                    0=不可查 / 90=Plus 90 天 / -1=Pro 永久
    keyword: 在 filename / invoice_no / seller_name 里模糊匹配
    v118.14 · tenant_id 给了 → 多租户共享:看同 tenant 所有用户的发票(老板看员工的)
              没给 → 老逻辑:只看自己的(向前兼容)
    v118.28.0 · client_id 给了 → 仅看该客户的发票(顶栏客户切换器)· None 则不过滤
    v118.28.1 · restrict_client_ids: List[int] = 员工只能看分到的客户;None = 不限制
                空列表 = 没分到任何客户(只能看自己上传未归属的)
    v118.27.7.1 · retention_days 改 Optional · 兼容 reports_router 等老调用方漏传
                  None 时从 user 表 history_retention_days 字段自动拉(权限不被绕过)
    """
    # v118.27.7.1 · 自动 fallback:调用方漏传 retention_days 时从 user 表拉真实保留期
    if retention_days is None:
        try:
            user = find_user_by_id(user_id)
            if user and user.get("history_retention_days") is not None:
                retention_days = int(user["history_retention_days"])
            else:
                # 兜底:90 天(平衡安全 + 可用 · 比 -1 永久全开稳)
                retention_days = 90
                logger.warning(
                    f"list_ocr_history 自动 fallback: user_id={user_id} 没填 history_retention_days · 用 90 天兜底"
                )
        except Exception as e:
            logger.error(f"list_ocr_history 自动拉 retention_days 失败 (user_id={user_id}): {e}")
            retention_days = 90

    if retention_days == 0:
        return {"items": [], "total": 0}

    # v118.14 · 多租户过滤:tenant 视图(同 tenant 所有人共享)优先 · 否则 fallback 单 user
    if tenant_id:
        where = ["user_id IN (SELECT id FROM users WHERE tenant_id = %s)"]
        params: list = [tenant_id]
    else:
        where = ["user_id = %s"]
        params: list = [user_id]

    if retention_days > 0:
        where.append("created_at >= NOW() - INTERVAL '%s days'" % int(retention_days))

    if keyword:
        where.append("(filename ILIKE %s OR invoice_no ILIKE %s OR seller_name ILIKE %s)")
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])

    # v118.28.0 · 客户切换器过滤
    if client_id is not None:
        where.append("client_id = %s")
        params.append(int(client_id))

    # v118.28.1 · 员工分配过滤(restrict_client_ids = 员工分到的客户;None = 不限制)
    if restrict_client_ids is not None:
        if len(restrict_client_ids) == 0:
            # 没分到任何客户 · 只能看自己上传的未归属发票
            where.append("(user_id = %s AND client_id IS NULL)")
            params.append(user_id)
        else:
            where.append("(client_id = ANY(%s::bigint[]) OR (user_id = %s AND client_id IS NULL))")
            params.append([int(c) for c in restrict_client_ids])
            params.append(user_id)

    where_sql = " AND ".join(where)

    try:
        with get_cursor() as cur:
            # 总数
            cur.execute(f"SELECT COUNT(*) AS c FROM ocr_history WHERE {where_sql}", params)
            total = cur.fetchone()["c"]

            # 列表(不带 pages 字段,省流量)
            cur.execute(
                f"""
                SELECT id, filename, page_count, confidence, elapsed_ms,
                       invoice_no, invoice_date, seller_name, total_amount,
                       archive_name, category_tag,
                       fields_edited_at, edit_count, created_at,
                       source_pdf_id, source_index, source_total,
                       source, source_ref,
                       pdf_storage_path
                FROM ocr_history
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """,
                params + [limit, offset],
            )
            items = []
            for r in cur.fetchall():
                items.append(
                    {
                        "id": str(r["id"]),
                        "filename": r["filename"],
                        "page_count": r["page_count"],
                        "confidence": r["confidence"],
                        "elapsed_ms": r["elapsed_ms"],
                        "invoice_no": r["invoice_no"],
                        "invoice_date": (
                            r["invoice_date"].isoformat() if r["invoice_date"] else None
                        ),
                        "seller_name": r["seller_name"],
                        "total_amount": (
                            float(r["total_amount"]) if r["total_amount"] is not None else None
                        ),
                        "archive_name": r["archive_name"],
                        "category_tag": r["category_tag"],
                        "edited": r["fields_edited_at"] is not None,
                        "edit_count": r["edit_count"],
                        "created_at": r["created_at"].isoformat(),
                        # v0.11 · 多发票拆分字段
                        "source_pdf_id": (
                            str(r["source_pdf_id"]) if r.get("source_pdf_id") else None
                        ),
                        "source_index": r.get("source_index"),
                        "source_total": r.get("source_total"),
                        # v95 · 来源标识
                        "source": r.get("source") or "manual",
                        "source_ref": r.get("source_ref"),
                        # v114 · 是否有 PDF 留底(前端用来决定是否显示「下载 PDF」按钮)
                        "has_pdf": bool(r.get("pdf_storage_path")),
                    }
                )
            return {"items": items, "total": total}
    except Exception as e:
        logger.error(f"查询历史失败 (user_id={user_id}): {e}")
        return {"items": [], "total": 0}


def get_ocr_history_detail(
    user_id: str, record_id: str, tenant_id: Optional[str] = None
) -> Optional[dict]:
    """取单条详情(含完整 pages)
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可查 · 否则只能查自己的
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, filename, page_count, confidence, elapsed_ms,
                           pages, invoice_no, invoice_date, seller_name, total_amount,
                           archive_name, category_tag,
                           fields_edited_at, edit_count, created_at, updated_at,
                           client_id
                    FROM ocr_history
                    WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    LIMIT 1
                """,
                    (record_id, tenant_id),
                )
            else:
                cur.execute(
                    """
                    SELECT id, filename, page_count, confidence, elapsed_ms,
                           pages, invoice_no, invoice_date, seller_name, total_amount,
                           archive_name, category_tag,
                           fields_edited_at, edit_count, created_at, updated_at,
                           client_id
                    FROM ocr_history
                    WHERE id = %s AND user_id = %s
                    LIMIT 1
                """,
                    (record_id, user_id),
                )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "id": str(r["id"]),
                "filename": r["filename"],
                "page_count": r["page_count"],
                "confidence": r["confidence"],
                "elapsed_ms": r["elapsed_ms"],
                "pages": r["pages"],
                "invoice_no": r["invoice_no"],
                "invoice_date": r["invoice_date"].isoformat() if r["invoice_date"] else None,
                "seller_name": r["seller_name"],
                "total_amount": float(r["total_amount"]) if r["total_amount"] is not None else None,
                "archive_name": r["archive_name"],
                "category_tag": r["category_tag"],
                "edited": r["fields_edited_at"] is not None,
                "edit_count": r["edit_count"],
                "created_at": r["created_at"].isoformat(),
                "updated_at": r["updated_at"].isoformat(),
                # v107 · 客户归属
                "client_id": int(r["client_id"]) if r.get("client_id") else None,
            }
    except Exception as e:
        logger.error(f"查询历史详情失败 (id={record_id}): {e}")
        return None


def update_ocr_history_pages(
    user_id: str, record_id: str, new_pages: list, tenant_id: Optional[str] = None
) -> bool:
    """会计修改字段后保存。同步刷新冗余字段 + v0.7 重算归档名
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可改 · 否则只能改自己的
    """
    summary = _extract_summary_fields(new_pages)

    # v0.7 · 重算归档名(按用户当前模板)
    new_archive_name = None
    new_category_tag = None
    try:
        import archive as _archive

        merged = {}
        for p in new_pages or []:
            if p.get("is_duplicate") or p.get("is_copy"):
                continue
            merged = p.get("fields") or {}
            break
        template = get_archive_template(user_id) or _archive.DEFAULT_TEMPLATE
        new_archive_name = _archive.preview_name(merged, template)
        new_category_tag = (merged.get("category") or "").strip() or None
    except Exception as e:
        logger.warning(f"重算归档名失败(不影响保存): {e}")

    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                where_sql = "id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
                where_params = [record_id, tenant_id]
            else:
                where_sql = "id = %s AND user_id = %s"
                where_params = [record_id, user_id]
            cur.execute(
                f"""
                UPDATE ocr_history
                SET pages = %s::jsonb,
                    invoice_no = %s,
                    invoice_date = %s,
                    seller_name = %s,
                    total_amount = %s,
                    archive_name = COALESCE(%s, archive_name),
                    category_tag = COALESCE(%s, category_tag),
                    archived_at = CASE WHEN %s IS NOT NULL THEN NOW() ELSE archived_at END,
                    fields_edited_at = NOW(),
                    edit_count = edit_count + 1,
                    updated_at = NOW()
                WHERE {where_sql}
            """,
                (
                    _json.dumps(new_pages, ensure_ascii=False),
                    summary["invoice_no"],
                    summary["invoice_date"],
                    summary["seller_name"],
                    summary["total_amount"],
                    new_archive_name,
                    new_category_tag,
                    new_archive_name,
                    *where_params,
                ),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"更新历史失败 (id={record_id}): {e}")
        return False


def delete_ocr_history(user_id: str, record_id: str, tenant_id: Optional[str] = None) -> bool:
    """v118.14 · tenant_id 给了 → 同 tenant 任意成员可删 · 否则只能删自己的
    v118.20.4.4 · 修 UUID cast(id 列是 UUID · 字符串需 ::uuid)"""
    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    "DELETE FROM ocr_history WHERE id = %s::uuid AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)",
                    (record_id, tenant_id),
                )
            else:
                cur.execute(
                    "DELETE FROM ocr_history WHERE id = %s::uuid AND user_id = %s::uuid",
                    (record_id, user_id),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"删除历史失败 (id={record_id}): {e}")
        return False


def delete_ocr_history_with_pdf_paths(
    user_id: str, record_ids: list, tenant_id: Optional[str] = None
) -> tuple:
    """
    v114 · 批量删除 + 返回被删记录的 PDF 路径列表(给上层清理本地文件)
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可删
    v118.20.4.4 · 修 UUID cast(id 列是 UUID · text[] 需 ::uuid[])
    Returns: (deleted_count, [pdf_path1, pdf_path2, ...])
    """
    if not record_ids:
        return 0, []
    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                # 先查路径
                cur.execute(
                    "SELECT pdf_storage_path FROM ocr_history WHERE id = ANY(%s::uuid[]) AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid) AND pdf_storage_path IS NOT NULL",
                    (record_ids, tenant_id),
                )
                paths = [r["pdf_storage_path"] for r in cur.fetchall() if r.get("pdf_storage_path")]
                # 再删
                cur.execute(
                    "DELETE FROM ocr_history WHERE id = ANY(%s::uuid[]) AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)",
                    (record_ids, tenant_id),
                )
            else:
                cur.execute(
                    "SELECT pdf_storage_path FROM ocr_history WHERE id = ANY(%s::uuid[]) AND user_id = %s::uuid AND pdf_storage_path IS NOT NULL",
                    (record_ids, user_id),
                )
                paths = [r["pdf_storage_path"] for r in cur.fetchall() if r.get("pdf_storage_path")]
                cur.execute(
                    "DELETE FROM ocr_history WHERE id = ANY(%s::uuid[]) AND user_id = %s::uuid",
                    (record_ids, user_id),
                )
            return cur.rowcount, paths
    except Exception as e:
        logger.error(f"批量删除历史失败: {e}")
        return 0, []


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
# T1 · LINE Bot · 绑定 / 绑定码 CRUD
# v0.19.0 · 2026-04-23
# ============================================================

import secrets
from datetime import datetime, timedelta, timezone


def generate_line_binding_code(user_id: str, ttl_minutes: int = 10) -> Optional[Dict[str, Any]]:
    """
    为用户生成 6 位数字绑定码 · 10 分钟有效 · 重复生成会覆盖旧码。
    返回 {"code": "123456", "expires_at": "..."} 或 None
    """
    try:
        # 6 位随机数字码(避免 0 开头在 LINE 里看起来像字母)
        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

        with get_cursor(commit=True) as cur:
            # 先把该用户之前未使用的码作废(只保留最新一个)
            cur.execute(
                """
                UPDATE line_binding_codes
                   SET used_at = NOW()
                 WHERE user_id = %s
                   AND used_at IS NULL
            """,
                (str(user_id),),
            )

            # 插入新码
            cur.execute(
                """
                INSERT INTO line_binding_codes (code, user_id, expires_at)
                VALUES (%s, %s, %s)
                RETURNING code, expires_at
            """,
                (code, str(user_id), expires_at),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "code": row["code"],
                "expires_at": row["expires_at"].isoformat(),
            }
    except Exception as e:
        logger.error(f"generate_line_binding_code failed: {e}")
        return None


def consume_line_binding_code(code: str) -> Optional[str]:
    """
    验证绑定码 · 合法则标记为已用 · 返回对应 user_id。
    不合法(不存在 / 已用 / 已过期)返回 None。
    T1 轮 2 webhook 收到 LINE 文字消息时调用。
    """
    try:
        code = (code or "").strip()
        if not code or len(code) != 6 or not code.isdigit():
            return None
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE line_binding_codes
                   SET used_at = NOW()
                 WHERE code = %s
                   AND used_at IS NULL
                   AND expires_at > NOW()
                RETURNING user_id
            """,
                (code,),
            )
            row = cur.fetchone()
            return str(row["user_id"]) if row else None
    except Exception as e:
        logger.error(f"consume_line_binding_code failed: {e}")
        return None


def create_or_update_line_binding(
    user_id: str,
    line_user_id: str,
    display_name: Optional[str] = None,
    picture_url: Optional[str] = None,
) -> bool:
    """
    绑定 mrpilot user ↔ LINE user。
    一个 mrpilot user 只能绑一个 LINE 账号(UNIQUE user_id)
    一个 LINE 账号只能绑一个 mrpilot user(UNIQUE line_user_id)
    重复绑同一对会更新昵称/头像。
    """
    try:
        with get_cursor(commit=True) as cur:
            # 检查冲突:该 LINE 账号是否已绑到别的 mrpilot user
            cur.execute(
                """
                SELECT user_id FROM line_bindings
                 WHERE line_user_id = %s
                 LIMIT 1
            """,
                (line_user_id,),
            )
            row = cur.fetchone()
            if row and str(row["user_id"]) != str(user_id):
                logger.warning(
                    f"LINE {line_user_id} 已绑到 user {row['user_id']} · "
                    f"拒绝绑到 user {user_id}"
                )
                return False

            # 先清空该 mrpilot user 已有的其他 LINE 绑定(换绑场景)
            cur.execute(
                """
                DELETE FROM line_bindings
                 WHERE user_id = %s
                   AND line_user_id != %s
            """,
                (str(user_id), line_user_id),
            )

            # upsert
            cur.execute(
                """
                INSERT INTO line_bindings
                    (user_id, line_user_id, line_display_name, line_picture_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (line_user_id) DO UPDATE SET
                    user_id            = EXCLUDED.user_id,
                    line_display_name  = EXCLUDED.line_display_name,
                    line_picture_url   = EXCLUDED.line_picture_url,
                    last_active_at     = NOW()
            """,
                (str(user_id), line_user_id, display_name, picture_url),
            )
            return True
    except Exception as e:
        logger.error(f"create_or_update_line_binding failed: {e}")
        return False


def get_line_binding_by_user(user_id: str) -> Optional[Dict[str, Any]]:
    """查某 mrpilot 用户当前的 LINE 绑定信息"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT line_user_id, line_display_name, line_picture_url,
                       bound_at, last_active_at
                  FROM line_bindings
                 WHERE user_id = %s
                 LIMIT 1
            """,
                (str(user_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_line_binding_by_user failed: {e}")
        return None


def get_user_by_line_user_id(line_user_id: str) -> Optional[Dict[str, Any]]:
    """
    给定 LINE user_id · 查对应的 mrpilot 用户(含权限字段)。
    T1 轮 2 webhook 收到 LINE 消息 · 用这个反查。
    同时更新 last_active_at。
    """
    try:
        with get_cursor(commit=True) as cur:
            # 更新活跃时间
            cur.execute(
                """
                UPDATE line_bindings SET last_active_at = NOW()
                 WHERE line_user_id = %s
                RETURNING user_id
            """,
                (line_user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            user_id = str(row["user_id"])

            # 查 mrpilot 用户
            cur.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
            urow = cur.fetchone()
            return dict(urow) if urow else None
    except Exception as e:
        logger.error(f"get_user_by_line_user_id failed: {e}")
        return None


def unbind_line_by_user(user_id: str) -> bool:
    """用户主动解绑 LINE"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                DELETE FROM line_bindings WHERE user_id = %s
            """,
                (str(user_id),),
            )
            return True
    except Exception as e:
        logger.error(f"unbind_line_by_user failed: {e}")
        return False


def update_user_preferred_lang(user_id: str, lang: str) -> bool:
    """更新用户偏好语言 · 供 LINE Bot 等场景读取"""
    if lang not in ("zh", "en", "th", "ja"):
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE users SET preferred_lang = %s WHERE id = %s
            """,
                (lang, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_user_preferred_lang failed: {e}")
        return False


# ============================================================
# v22 多租户 · 租户管理函数
# ============================================================
# 设计原则:
# - 所有业务函数保持按 user_id 查(不破坏现有代码)
# - 下面这批新函数供超级管理员后台使用
# - 租户数据隔离通过"每个用户只属于一个租户"来保证
# ============================================================


def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    """根据 tenant_id 查租户信息"""
    if not tenant_id:
        return None
    try:
        with get_cursor() as cur:
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
        with get_cursor() as cur:
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
        with get_cursor() as cur:
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
        with get_cursor(commit=True) as cur:
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
        with get_cursor(commit=True) as cur:
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
        with get_cursor(commit=True) as cur:
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
        with get_cursor() as cur:
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
        with get_cursor(commit=True) as cur:
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
        with get_cursor() as cur:
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

        with get_cursor() as cur:
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


# ============================================================
# v23 · 用户(老板)管理 + 员工 + 操作日志
# ============================================================
import bcrypt as _bcrypt


def list_all_owner_users(limit: int = 200) -> List[Dict[str, Any]]:
    """
    超管用 · 列所有 owner 用户(每个对应一家公司)
    返回含:用户名 / 公司名称 / 类型 / 配额 / 用量 / 员工数 / 状态
    """
    try:
        with get_cursor() as cur:
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
        existing = find_user_by_username(username)
        if existing:
            logger.warning(f"create_owner_user: username {username} 已存在")
            return {"ok": False, "error": "username_exists"}

        pw_hash = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

        with get_cursor(commit=True) as cur:
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
        with get_cursor() as cur:
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
        with get_cursor(commit=True) as cur:
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


def verify_user_password(user_id: str, password: str) -> bool:
    """二次验证用 · 返回密码是否匹配"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s LIMIT 1", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return False
            return _bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))
    except Exception as e:
        logger.error(f"verify_user_password failed: {e}")
        return False


def reset_user_password(user_id: str, new_password: str) -> bool:
    """超管用 · 给指定用户重置密码"""
    try:
        pw_hash = _bcrypt.hashpw(new_password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
        with get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, password_changed_at = NOW() WHERE id = %s",
                (pw_hash, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"reset_user_password failed: {e}")
        return False


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
def get_visible_client_ids_for_user(user: dict):
    """返回用户能看到的 client_id 列表
    - super_admin / owner → None(不限制 · SQL 不加 client filter)
    - member → List[int]:从 client_assignments 拿(空列表 = 没分到任何客户)
    返回 None 时调用方不加 client filter · 返回 list 时加 WHERE client_id IN (list)
    """
    if not user:
        return []
    if user.get("is_super_admin"):
        return None
    role = user.get("role") or "owner"
    if role == "owner":
        return None
    user_id = str(user.get("id") or "")
    if not user_id:
        return []
    try:
        with get_cursor() as cur:
            cur.execute("SELECT client_id FROM client_assignments WHERE user_id = %s", (user_id,))
            rows = cur.fetchall() or []
            return [int(r["client_id"] if isinstance(r, dict) else r[0]) for r in rows]
    except Exception as e:
        logger.error(f"get_visible_client_ids_for_user failed (user={user_id}): {e}")
        return []  # 出错时拒绝访问 · 不暴露


def list_assignments_by_employees(tenant_id: str):
    """老板用 · 拿同 tenant 内每个 member 的 assignments
    返回 {employee_user_id: [client_id, ...]}
    """
    out = {}
    if not tenant_id:
        return out
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT ca.user_id, ca.client_id
                FROM client_assignments ca
                JOIN users u ON u.id = ca.user_id
                WHERE u.tenant_id = %s
            """,
                (str(tenant_id),),
            )
            for r in cur.fetchall() or []:
                uid = str(r["user_id"] if isinstance(r, dict) else r[0])
                cid = int(r["client_id"] if isinstance(r, dict) else r[1])
                out.setdefault(uid, []).append(cid)
    except Exception as e:
        logger.error(f"list_assignments_by_employees failed: {e}")
    return out


def set_employee_assignments(
    employee_user_id: str, client_ids, assigned_by: str, tenant_id: str
) -> bool:
    """覆盖式设置员工的客户列表
    安全:校验员工和所有 client_id 都在 tenant_id 内 · 防跨租户
    """
    if not employee_user_id or not assigned_by or not tenant_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            # 校验员工属于本租户
            cur.execute(
                "SELECT tenant_id FROM users WHERE id = %s LIMIT 1", (str(employee_user_id),)
            )
            row = cur.fetchone()
            if not row:
                return False
            row_tid = row["tenant_id"] if isinstance(row, dict) else row[0]
            if str(row_tid) != str(tenant_id):
                return False

            # 删现有所有
            cur.execute(
                "DELETE FROM client_assignments WHERE user_id = %s", (str(employee_user_id),)
            )

            # 校验要分配的 client_ids 都在本租户(防越权写)
            valid_ids = []
            if client_ids:
                int_ids = [int(c) for c in client_ids if c is not None]
                if int_ids:
                    cur.execute(
                        """
                        SELECT id FROM clients
                        WHERE id = ANY(%s::bigint[])
                          AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    """,
                        (int_ids, str(tenant_id)),
                    )
                    valid_ids = [
                        int(r["id"] if isinstance(r, dict) else r[0])
                        for r in (cur.fetchall() or [])
                    ]

            # 批插
            for cid in valid_ids:
                cur.execute(
                    """
                    INSERT INTO client_assignments (user_id, client_id, assigned_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, client_id) DO NOTHING
                """,
                    (str(employee_user_id), cid, str(assigned_by)),
                )
            return True
    except Exception as e:
        logger.error(f"set_employee_assignments failed: {e}")
        return False


def auto_assign_client_to_creator(creator_user_id: str, client_id: int) -> bool:
    """创建客户时 · 给创建者一个 assignment(让员工身份创建的能看自己建的)
    老板/超管不需要(他们不受 assignment 限制)· 但调用方简单起见统一调用 · 这里幂等 OK"""
    if not creator_user_id or not client_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO client_assignments (user_id, client_id, assigned_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, client_id) DO NOTHING
            """,
                (str(creator_user_id), int(client_id), str(creator_user_id)),
            )
        return True
    except Exception as e:
        logger.error(f"auto_assign_client_to_creator failed: {e}")
        return False


def get_user_tenant_id(user_id: str) -> Optional[str]:
    """v118.27.7 兼容层 · 优先读 memberships · 回退 users.tenant_id
    迁移过渡期老代码继续用 user.tenant_id · 新代码可以用本函数无缝过渡
    """
    if not user_id:
        return None
    try:
        with get_cursor() as cur:
            # 优先读 memberships(新模型)
            cur.execute(
                """
                SELECT tenant_id FROM memberships
                WHERE user_id = %s AND status = 'active'
                LIMIT 1
            """,
                (str(user_id),),
            )
            r = cur.fetchone()
            if r and r.get("tenant_id"):
                return str(r["tenant_id"])
            # 回退 users.tenant_id(老字段 · 过渡期共存)
            cur.execute("SELECT tenant_id FROM users WHERE id = %s LIMIT 1", (str(user_id),))
            r = cur.fetchone()
            if r and r.get("tenant_id"):
                return str(r["tenant_id"])
            return None
    except Exception as e:
        logger.warning(f"get_user_tenant_id failed (user_id={user_id}): {e}")
        return None


def migrate_to_membership_model(dry_run: bool = True) -> Dict[str, Any]:
    """把 users.tenant_id 单一关系迁移到 memberships 表
    dry_run=True · 只统计不写库 · 给超管 admin 看 · 返回结构化 JSON
    dry_run=False · 真执行 · 真写 memberships
    返回:
      {
        ok: bool,
        dry_run: bool,
        scanned: 扫描的 user 数,
        eligible: 需要迁移的 user 数(有 tenant_id 且 memberships 里无记录),
        already_migrated: memberships 已有该用户的数量,
        no_tenant: tenant_id 为 NULL 的用户数(孤立用户 · 跳过),
        role_distribution: { owner: N, member: N, ... },
        missing_role: [role_name, ...] (角色 name 不在 roles 表里 · 需要补),
        sample_inserts: [ {user_id, tenant_id, role} 前 5 条] (dry_run=True 时给一窥),
        inserted: 实际插入条数(dry_run=False 时填),
        errors: [ {user_id, msg}, ... ],
      }
    """
    out: Dict[str, Any] = {
        "ok": False,
        "dry_run": bool(dry_run),
        "scanned": 0,
        "eligible": 0,
        "already_migrated": 0,
        "no_tenant": 0,
        "role_distribution": {},
        "missing_role": [],
        "sample_inserts": [],
        "inserted": 0,
        "errors": [],
    }
    try:
        with get_cursor(commit=not dry_run) as cur:
            # 扫所有用户
            cur.execute("""
                SELECT u.id, u.username, u.tenant_id, u.role,
                       EXISTS(SELECT 1 FROM memberships m WHERE m.user_id = u.id) AS already
                FROM users u
            """)
            rows = cur.fetchall() or []
            out["scanned"] = len(rows)

            # 取 roles 表里所有角色 name → id 映射
            cur.execute("SELECT id, name FROM roles")
            role_map = {r["name"]: str(r["id"]) for r in cur.fetchall()}

            eligible_rows = []
            role_count: Dict[str, int] = {}
            missing_set = set()

            for r in rows:
                if r.get("already"):
                    out["already_migrated"] += 1
                    continue
                if not r.get("tenant_id"):
                    out["no_tenant"] += 1
                    continue
                # 老 users.role 是 'owner' / 'member' / NULL · 映射到新 roles 表
                old_role = (r.get("role") or "owner").strip().lower()
                # member → staff(新模型用 staff 表示员工)
                new_role_name = "staff" if old_role == "member" else old_role
                if new_role_name not in ("owner", "manager", "staff"):
                    new_role_name = "owner"  # 兜底:NULL / 未知都视为 owner
                role_count[new_role_name] = role_count.get(new_role_name, 0) + 1
                if new_role_name not in role_map:
                    missing_set.add(new_role_name)
                    continue
                eligible_rows.append(
                    {
                        "user_id": str(r["id"]),
                        "username": r.get("username"),
                        "tenant_id": str(r["tenant_id"]),
                        "role": new_role_name,
                        "role_id": role_map[new_role_name],
                    }
                )

            out["eligible"] = len(eligible_rows)
            out["role_distribution"] = role_count
            out["missing_role"] = sorted(missing_set)
            out["sample_inserts"] = [
                {
                    "user_id": e["user_id"],
                    "username": e["username"],
                    "tenant_id": e["tenant_id"],
                    "role": e["role"],
                }
                for e in eligible_rows[:5]
            ]

            if dry_run:
                out["ok"] = True
                logger.info(
                    f"[v27.7 migration] DRY-RUN · scanned={out['scanned']} eligible={out['eligible']} already={out['already_migrated']}"
                )
                return out

            # 真执行 · 逐条插入(批量插入风险大 · 单条可继续)
            inserted = 0
            for e in eligible_rows:
                try:
                    cur.execute(
                        """
                        INSERT INTO memberships (user_id, tenant_id, role_id, status)
                        VALUES (%s, %s, %s, 'active')
                        ON CONFLICT (user_id) DO NOTHING
                    """,
                        (e["user_id"], e["tenant_id"], e["role_id"]),
                    )
                    if cur.rowcount > 0:
                        inserted += 1
                except Exception as e_one:
                    out["errors"].append({"user_id": e["user_id"], "msg": str(e_one)[:200]})

            out["inserted"] = inserted
            out["ok"] = True
            logger.info(
                f"[v27.7 migration] EXECUTED · inserted={inserted}/{len(eligible_rows)} errors={len(out['errors'])}"
            )
            return out
    except Exception as e:
        logger.error(f"migrate_to_membership_model failed (dry_run={dry_run}): {e}")
        out["errors"].append({"user_id": None, "msg": str(e)[:300]})
        return out


# ============================================================
# v118.27.7.1 · 孤立用户(tenant_id IS NULL)盘点 + 修复
#   - 给每个孤立用户建一个独立 tenant + 写 membership
#   - 完整继承 user.plan / monthly_quota / expires(防付费用户掉级)
#   - 单用户独立事务 · 一个失败不影响其他
# ============================================================


def list_orphan_users() -> List[Dict[str, Any]]:
    """列出所有 tenant_id IS NULL 的用户(过滤超管)+ 每个用户的数据量统计
    给超管看清楚哪些用户需要补建 tenant
    """
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    u.id, u.username, u.email, u.full_name, u.company_name,
                    u.plan, u.monthly_quota, u.used_this_month,
                    u.trial_expires_at, u.plan_expires_at,
                    u.role, u.signup_country, u.last_login_at, u.created_at,
                    (SELECT COUNT(*) FROM ocr_history WHERE user_id = u.id) AS ocr_count,
                    (SELECT COUNT(*) FROM clients WHERE user_id = u.id) AS client_count,
                    (SELECT COUNT(*) FROM erp_endpoints WHERE user_id = u.id) AS erp_count
                FROM users u
                WHERE u.tenant_id IS NULL
                  AND COALESCE(u.is_super_admin, FALSE) = FALSE
                ORDER BY u.created_at ASC NULLS LAST
            """)
            rows = cur.fetchall() or []
            out = []
            for r in rows:
                out.append(
                    {
                        "user_id": str(r["id"]),
                        "username": r.get("username"),
                        "email": r.get("email"),
                        "full_name": r.get("full_name"),
                        "company_name": r.get("company_name"),
                        "plan": r.get("plan") or "free",
                        "monthly_quota": int(r.get("monthly_quota") or 0),
                        "used_this_month": int(r.get("used_this_month") or 0),
                        "role": r.get("role"),
                        "country": r.get("signup_country"),
                        "trial_expires_at": (
                            r["trial_expires_at"].isoformat() if r.get("trial_expires_at") else None
                        ),
                        "plan_expires_at": (
                            r["plan_expires_at"].isoformat() if r.get("plan_expires_at") else None
                        ),
                        "last_login_at": (
                            r["last_login_at"].isoformat() if r.get("last_login_at") else None
                        ),
                        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
                        "ocr_count": int(r.get("ocr_count") or 0),
                        "client_count": int(r.get("client_count") or 0),
                        "erp_count": int(r.get("erp_count") or 0),
                    }
                )
            return out
    except Exception as e:
        logger.error(f"list_orphan_users failed: {e}")
        return []


def fix_orphan_users(dry_run: bool = True) -> Dict[str, Any]:
    """给孤立用户每人建独立 tenant + 同步写 memberships
    继承 user.plan / monthly_quota / trial_expires_at / plan_expires_at 到新 tenant
    单个用户独立事务 · 失败不影响其他

    返回:
      ok / dry_run / scanned / plan(每个会建的 tenant 详情)/ executed / errors
    """
    out: Dict[str, Any] = {
        "ok": False,
        "dry_run": bool(dry_run),
        "scanned": 0,
        "plan": [],
        "executed": 0,
        "errors": [],
    }
    try:
        orphans = list_orphan_users()
        out["scanned"] = len(orphans)
        if not orphans:
            out["ok"] = True
            return out

        # 取 owner role_id(给 membership 用)
        with get_cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE name = 'owner' AND is_system = TRUE LIMIT 1")
            r = cur.fetchone()
            if not r:
                out["errors"].append(
                    {
                        "user_id": None,
                        "msg": "owner_role_not_found · run ensure_membership_tables() first",
                    }
                )
                return out
            owner_role_id = str(r["id"])

        # 给每个孤立用户做 plan
        for u in orphans:
            user_id = u["user_id"]
            # tenant.name 优先级:company_name > full_name > username > email_prefix
            tenant_name = (u.get("company_name") or "").strip()
            if not tenant_name:
                tenant_name = (u.get("full_name") or "").strip()
            if not tenant_name:
                tenant_name = (u.get("username") or "").strip()
            if not tenant_name and u.get("email"):
                tenant_name = u["email"].split("@")[0]
            tenant_name = (tenant_name or f"user_{user_id[:8]}")[:100]

            preview = {
                "user_id": user_id,
                "username": u.get("username"),
                "email": u.get("email"),
                "tenant_name_to_create": tenant_name,
                "plan_inherit": u.get("plan") or "free",
                "quota_inherit": int(u.get("monthly_quota") or 0),
                "trial_expires_at": u.get("trial_expires_at"),
                "plan_expires_at": u.get("plan_expires_at"),
                "ocr_records": u.get("ocr_count"),
                "client_records": u.get("client_count"),
                "erp_endpoints": u.get("erp_count"),
            }
            out["plan"].append(preview)

        if dry_run:
            out["ok"] = True
            logger.info(
                f"[v27.7.1 fix_orphan] DRY-RUN · scanned={out['scanned']} plans={len(out['plan'])}"
            )
            return out

        # 真执行 · 每个用户独立事务
        for p in out["plan"]:
            try:
                with get_cursor(commit=True) as cur:
                    # 1. 建 tenant · v27.7.2 修:tenants 表只有 subscription_expires_at · 没有 trial_expires_at
                    # 用户的 trial / plan 到期都收敛到 tenant.subscription_expires_at(优先 plan_expires_at)
                    cur.execute(
                        """
                        INSERT INTO tenants (
                            name, owner_user_id, tenant_type, monthly_quota,
                            used_this_month, status, member_count,
                            tenant_type_v2, subscription_expires_at
                        )
                        VALUES (%s, %s, 'shared_api', %s, 0, 'active', 1,
                                'firm', %s)
                        RETURNING id
                    """,
                        (
                            p["tenant_name_to_create"],
                            p["user_id"],
                            p["quota_inherit"],
                            p.get("plan_expires_at") or p.get("trial_expires_at"),
                        ),
                    )
                    new_tenant_id = str(cur.fetchone()["id"])

                    # 2. UPDATE user.tenant_id + role(竞态保护:tenant_id 必须仍是 NULL)
                    cur.execute(
                        """
                        UPDATE users SET tenant_id = %s, role = COALESCE(role, 'owner')
                        WHERE id = %s AND tenant_id IS NULL
                    """,
                        (new_tenant_id, p["user_id"]),
                    )
                    if cur.rowcount == 0:
                        # 用户在我们处理过程中被别的流程绑了 tenant · 删掉刚建的孤儿 tenant · 跳过
                        cur.execute("DELETE FROM tenants WHERE id = %s", (new_tenant_id,))
                        out["errors"].append(
                            {"user_id": p["user_id"], "msg": "user_already_has_tenant_skip"}
                        )
                        continue

                    # 3. 写 membership
                    cur.execute(
                        """
                        INSERT INTO memberships (user_id, tenant_id, role_id, status)
                        VALUES (%s, %s, %s, 'active')
                        ON CONFLICT (user_id) DO NOTHING
                    """,
                        (p["user_id"], new_tenant_id, owner_role_id),
                    )

                    out["executed"] += 1
                    p["new_tenant_id"] = new_tenant_id
                    logger.info(
                        f"[v27.7.1 fix_orphan] +tenant {new_tenant_id[:8]}.. for user {p.get('username')!r} email={p.get('email')!r}"
                    )
            except Exception as e_one:
                logger.error(f"[v27.7.1 fix_orphan] user_id={p['user_id']} failed: {e_one}")
                out["errors"].append({"user_id": p["user_id"], "msg": str(e_one)[:200]})

        out["ok"] = True
        logger.info(
            f"[v27.7.1 fix_orphan] EXECUTED · executed={out['executed']}/{len(out['plan'])} errors={len(out['errors'])}"
        )
        return out
    except Exception as e:
        import traceback

        logger.error(f"fix_orphan_users failed (dry_run={dry_run}): {e}\n{traceback.format_exc()}")
        out["errors"].append({"user_id": None, "msg": str(e)[:300]})
        return out


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


def backfill_tenant_ids(dry_run: bool = True) -> Dict[str, Any]:
    """自动扫所有有 user_id + tenant_id 双列的表 · 把 tenant_id 按 user 回填
    dry_run=True · 只统计每个表会更新几行 · 不真改
    dry_run=False · 真执行
    """
    out = {
        "ok": False,
        "dry_run": bool(dry_run),
        "tables": [],
        "total_updated": 0,
        "errors": [],
    }
    try:
        # 1. 自动发现候选表(public schema · 同时有 user_id + tenant_id 两列 · 排除 users 自身)
        with get_cursor() as cur:
            cur.execute("""
                SELECT a.table_name
                FROM information_schema.columns a
                INNER JOIN information_schema.columns b
                  ON a.table_schema = b.table_schema AND a.table_name = b.table_name
                WHERE a.table_schema = 'public'
                  AND a.column_name = 'tenant_id'
                  AND b.column_name = 'user_id'
                  AND a.table_name <> 'users'
                ORDER BY a.table_name
            """)
            tables = [r["table_name"] for r in cur.fetchall() or []]

        # 2. 逐表回填(每表独立事务 · 一个失败不影响其他)
        for tbl in tables:
            try:
                # 先统计待回填的行数
                with get_cursor() as cur:
                    cur.execute(f"""
                        SELECT COUNT(*) AS n FROM {tbl}
                        WHERE tenant_id IS NULL
                          AND user_id IN (SELECT id FROM users WHERE tenant_id IS NOT NULL)
                    """)
                    pending = int((cur.fetchone() or {}).get("n") or 0)
                info = {"table": tbl, "to_update": pending, "updated": 0}

                if pending > 0 and not dry_run:
                    with get_cursor(commit=True) as cur:
                        cur.execute(f"""
                            UPDATE {tbl} SET tenant_id = u.tenant_id
                            FROM users u
                            WHERE {tbl}.user_id = u.id
                              AND {tbl}.tenant_id IS NULL
                              AND u.tenant_id IS NOT NULL
                        """)
                        info["updated"] = cur.rowcount
                        out["total_updated"] += cur.rowcount
                        logger.info(f"[v27.8.1 backfill] {tbl}: +{cur.rowcount} rows")
                out["tables"].append(info)
            except Exception as e:
                logger.error(f"[v27.8.1 backfill] {tbl} failed: {e}")
                out["errors"].append({"table": tbl, "msg": str(e)[:200]})

        out["ok"] = True
        if dry_run:
            logger.info(f"[v27.8.1 backfill] DRY-RUN · scanned {len(tables)} tables")
        else:
            logger.info(
                f"[v27.8.1 backfill] EXECUTED · total updated={out['total_updated']} errors={len(out['errors'])}"
            )
        return out
    except Exception as e:
        import traceback

        logger.error(f"backfill_tenant_ids fatal: {e}\n{traceback.format_exc()}")
        out["errors"].append({"table": None, "msg": str(e)[:300]})
        return out


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


def list_user_companies(user_id: str) -> list:
    """Return all companies a user belongs to.

    Each item: {tenant_id, name, role, balance_thb, pages_this_month, is_active}
    Uses Asia/Bangkok timezone for year_month.
    """
    try:
        year_month = _bkk_year_month()
        with get_cursor() as cur:
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
        with get_cursor(commit=True) as cur:
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
from decimal import Decimal as _DecV21, ROUND_HALF_UP as _RH_V21
import math as _math_v21
import time as _time_v21

PDF_TIER1_LIMIT_V21 = 200
PDF_TIER1_PRICE_V21 = _DecV21("1.50")
PDF_TIER2_PRICE_V21 = _DecV21("0.75")
EXCEL_CHARS_PER_SATANG_V21 = 50
EXCEL_SATANG_PRICE_V21 = _DecV21("0.01")

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


def estimate_pdf_cost_thb(pages_used_this_month: int, page_count: int) -> _DecV21:
    """估算 PDF N 页的总成本 · 跨界自动拆段
    v0.21 改: 调用端传 pages_used_this_month · 不再查 DB · 与前置 combined 查询复用
    """
    n = max(0, int(page_count or 0))
    if n == 0:
        return _DecV21("0.00")
    used = max(0, int(pages_used_this_month or 0))
    tier1_remaining = max(0, PDF_TIER1_LIMIT_V21 - used)
    tier1_pages = min(n, tier1_remaining)
    tier2_pages = n - tier1_pages
    cost = (PDF_TIER1_PRICE_V21 * tier1_pages) + (PDF_TIER2_PRICE_V21 * tier2_pages)
    return cost.quantize(_DecV21("0.01"), rounding=_RH_V21)


def estimate_excel_cost_thb(char_count: int) -> _DecV21:
    """Excel/Word/CSV 按字符计费 · 50 字符 = 1 satang · 向上取整"""
    n = max(0, int(char_count or 0))
    if n == 0:
        return _DecV21("0.00")
    satang = _math_v21.ceil(n / EXCEL_CHARS_PER_SATANG_V21)
    return (EXCEL_SATANG_PRICE_V21 * satang).quantize(_DecV21("0.01"), rounding=_RH_V21)


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


# ============================================================================
# v118.35.0.22 · Earn 超管面板 · Credits 数据互通(收入流)
# 老 ocr_cost_log = Gemini API 成本(公司支出 · 跟 Google 结算)
# 新 credit_transactions = 用户扣费(公司收入 · 跟用户结算)
# 两套数据互补 · 超管看完整商业全景
# ============================================================================


def get_credits_revenue_overview() -> dict:
    """v0.22 · 收入端 KPI(今日/本月/总计) · 从 credit_transactions 拉
    type='usage'  = 扣费收入(amount_thb 是负数 · 取绝对值)
    type='topup'  = 充值入账(amount_thb 是正数)
    type='adjustment' = 退款(amount_thb 是正数 · 算冲销)
    """
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN type='usage'  AND created_at::date = CURRENT_DATE THEN -amount_thb END), 0) AS today_usage,
                    COALESCE(SUM(CASE WHEN type='topup'  AND created_at::date = CURRENT_DATE THEN  amount_thb END), 0) AS today_topup,
                    COALESCE(SUM(CASE WHEN type='usage'  AND date_trunc('month', created_at) = date_trunc('month', NOW()) THEN -amount_thb END), 0) AS month_usage,
                    COALESCE(SUM(CASE WHEN type='topup'  AND date_trunc('month', created_at) = date_trunc('month', NOW()) THEN  amount_thb END), 0) AS month_topup,
                    COALESCE(SUM(CASE WHEN type='usage'  THEN -amount_thb END), 0) AS total_usage,
                    COALESCE(SUM(CASE WHEN type='topup'  THEN  amount_thb END), 0) AS total_topup,
                    COALESCE(SUM(CASE WHEN type='usage'  AND created_at::date = CURRENT_DATE THEN pages END), 0) AS today_pages,
                    COALESCE(SUM(CASE WHEN type='usage'  AND date_trunc('month', created_at) = date_trunc('month', NOW()) THEN pages END), 0) AS month_pages,
                    COUNT(CASE WHEN type='usage' AND created_at::date = CURRENT_DATE THEN 1 END) AS today_ocr_count,
                    COUNT(CASE WHEN type='usage' AND date_trunc('month', created_at) = date_trunc('month', NOW()) THEN 1 END) AS month_ocr_count
                FROM credit_transactions
            """)
            row = cur.fetchone() or {}

            # 所有 tenant 余额总和
            cur.execute("SELECT COALESCE(SUM(balance_thb), 0) AS total FROM tenant_credits")
            bal_row = cur.fetchone() or {}
            total_balance = float(bal_row.get("total") or 0)

            # 透支公司数(余额 ≤ 0)
            cur.execute("SELECT COUNT(*) AS n FROM tenant_credits WHERE balance_thb <= 0")
            neg_row = cur.fetchone() or {}
            overdraft_count = int(neg_row.get("n") or 0)

            return {
                "today": {
                    "usage_thb": float(row.get("today_usage") or 0),
                    "topup_thb": float(row.get("today_topup") or 0),
                    "pages": int(row.get("today_pages") or 0),
                    "ocr_count": int(row.get("today_ocr_count") or 0),
                },
                "month": {
                    "usage_thb": float(row.get("month_usage") or 0),
                    "topup_thb": float(row.get("month_topup") or 0),
                    "pages": int(row.get("month_pages") or 0),
                    "ocr_count": int(row.get("month_ocr_count") or 0),
                },
                "total": {
                    "usage_thb": float(row.get("total_usage") or 0),
                    "topup_thb": float(row.get("total_topup") or 0),
                },
                "pool_balance_thb": total_balance,
                "overdraft_tenants": overdraft_count,
            }
    except Exception as e:
        logger.error(f"get_credits_revenue_overview failed: {e}")
        return {
            "today": {},
            "month": {},
            "total": {},
            "pool_balance_thb": 0,
            "overdraft_tenants": 0,
        }


def get_tenants_credits_summary(limit: int = 100) -> list:
    """v0.22 · 全公司列表 · 余额 + 当月用量 + 透支警报
    按余额降序 · 让超管看哪家公司钱多 / 哪家透支了
    """
    try:
        ym = _bkk_year_month()
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.id::text AS tenant_id,
                    t.name AS tenant_name,
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_this_month,
                    COALESCE(
                        (SELECT SUM(-ct.amount_thb) FROM credit_transactions ct
                         WHERE ct.tenant_id = t.id AND ct.type='usage'
                         AND date_trunc('month', ct.created_at) = date_trunc('month', NOW())),
                        0
                    ) AS month_usage_thb,
                    COALESCE(
                        (SELECT SUM(ct.amount_thb) FROM credit_transactions ct
                         WHERE ct.tenant_id = t.id AND ct.type='topup'),
                        0
                    ) AS lifetime_topup_thb,
                    (SELECT MAX(ct.created_at) FROM credit_transactions ct
                     WHERE ct.tenant_id = t.id AND ct.type='usage') AS last_usage_at,
                    t.created_at AS tenant_created_at
                FROM tenants t
                LEFT JOIN tenant_credits tc ON tc.tenant_id = t.id
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = t.id AND mpu.year_month = %s
                ORDER BY balance_thb DESC NULLS LAST
                LIMIT %s
            """,
                (ym, limit),
            )
            rows = cur.fetchall() or []

        out = []
        for r in rows:
            bal = float(r["balance_thb"] or 0)
            out.append(
                {
                    "tenant_id": r["tenant_id"],
                    "tenant_name": r["tenant_name"] or "(无名)",
                    "balance_thb": bal,
                    "pages_this_month": int(r["pages_this_month"] or 0),
                    "month_usage_thb": float(r["month_usage_thb"] or 0),
                    "lifetime_topup_thb": float(r["lifetime_topup_thb"] or 0),
                    "last_usage_at": r["last_usage_at"].isoformat() if r["last_usage_at"] else None,
                    "tenant_created_at": (
                        r["tenant_created_at"].isoformat() if r["tenant_created_at"] else None
                    ),
                    "is_overdraft": bal <= 0,
                    "is_low_balance": 0 < bal < 50,
                }
            )
        return out
    except Exception as e:
        logger.error(f"get_tenants_credits_summary failed: {e}")
        return []


def get_tenant_credit_summary(tenant_id: str) -> Dict[str, Any]:
    """单租户 credits 汇总(Earn 用户详情抽屉用)· 余额 + 本月扣费/页数 + 累计充值 + 充值次数。
    取不到/出错返回 {} · 调用方按缺省隐藏(抽屉不做空壳)。"""
    if not tenant_id:
        return {}
    try:
        ym = _bkk_year_month()
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_this_month,
                    COALESCE(
                        (SELECT SUM(-ct.amount_thb) FROM credit_transactions ct
                         WHERE ct.tenant_id = t.id AND ct.type='usage'
                         AND date_trunc('month', ct.created_at) = date_trunc('month', NOW())),
                        0) AS month_usage_thb,
                    COALESCE(
                        (SELECT SUM(ct.amount_thb) FROM credit_transactions ct
                         WHERE ct.tenant_id = t.id AND ct.type='topup'), 0) AS lifetime_topup_thb,
                    (SELECT COUNT(*) FROM credit_transactions ct
                     WHERE ct.tenant_id = t.id AND ct.type='topup') AS topup_count,
                    (SELECT MAX(ct.created_at) FROM credit_transactions ct
                     WHERE ct.tenant_id = t.id AND ct.type='topup') AS last_topup_at
                FROM tenants t
                LEFT JOIN tenant_credits tc ON tc.tenant_id = t.id
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = t.id AND mpu.year_month = %s
                WHERE t.id = %s
                """,
                (ym, tenant_id),
            )
            r = cur.fetchone()
        if not r:
            return {}
        bal = float(r["balance_thb"] or 0)
        return {
            "balance_thb": bal,
            "pages_this_month": int(r["pages_this_month"] or 0),
            "month_usage_thb": float(r["month_usage_thb"] or 0),
            "lifetime_topup_thb": float(r["lifetime_topup_thb"] or 0),
            "topup_count": int(r["topup_count"] or 0),
            "last_topup_at": r["last_topup_at"].isoformat() if r["last_topup_at"] else None,
            "is_overdraft": bal <= 0,
            "is_low_balance": 0 < bal < 50,
        }
    except Exception as e:
        logger.error(f"get_tenant_credit_summary failed: {e}")
        return {}


def get_credits_daily_trend(days: int = 30) -> list:
    """v0.22 · 每日收支趋势 · 用 credit_transactions(替代 ocr_cost_log)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    created_at::date AS day,
                    COALESCE(SUM(CASE WHEN type='usage' THEN -amount_thb END), 0) AS usage_thb,
                    COALESCE(SUM(CASE WHEN type='topup' THEN amount_thb END), 0) AS topup_thb,
                    COALESCE(SUM(CASE WHEN type='usage' THEN pages END), 0) AS pages,
                    COUNT(CASE WHEN type='usage' THEN 1 END) AS ocr_count
                FROM credit_transactions
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY day
                ORDER BY day ASC
            """ % int(max(1, min(days, 365))))
            return [
                {
                    "day": str(r["day"]),
                    "usage_thb": float(r["usage_thb"] or 0),
                    "topup_thb": float(r["topup_thb"] or 0),
                    "pages": int(r["pages"] or 0),
                    "ocr_count": int(r["ocr_count"] or 0),
                }
                for r in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"get_credits_daily_trend failed: {e}")
        return []


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
