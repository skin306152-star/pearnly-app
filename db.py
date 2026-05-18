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

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

logger = logging.getLogger(__name__)

# v4.10.14 · Gemini 2.5 Flash 计费单价(USD · 2026-05)
OCR_PRICING = {
    "input_per_m_usd":  0.30,
    "output_per_m_usd": 2.50,
    "usd_thb":          36.5,   # v4.10.14 过渡 · v4.10.15 admin 改造时统一砍
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
        _pool = SimpleConnectionPool(
            minconn=1, maxconn=5, dsn=url,
            connect_timeout=10, sslmode="require",
        )
        logger.info("✅ PostgreSQL 连接池已建立")
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
        notes='公共测试账号 · Free · 按 IP 每天限流',
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
        notes='Plus 测试账号 · 200 张/月 · Gemini Flash',
    )


def _ensure_one_account(
    username, password, plan, monthly_quota,
    can_use_gemini, can_edit_fields, can_verify_tax,
    can_use_custom_template, can_view_history, can_use_typhoon,
    can_push_erp, can_use_automation, can_manage_api_keys,
    typhoon_quota_monthly, history_retention_days, custom_template_limit,
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
                cur.execute("""
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
                """, (
                    correct_hash, plan, monthly_quota,
                    can_use_gemini, can_edit_fields, can_verify_tax,
                    can_use_custom_template, can_view_history, can_use_typhoon,
                    can_push_erp, can_use_automation, can_manage_api_keys,
                    typhoon_quota_monthly, history_retention_days, custom_template_limit,
                    row["id"],
                ))
                logger.info(f"✅ {username} 账号已同步({plan} 权限)")
            else:
                cur.execute("""
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
                """, (
                    username, correct_hash, plan, monthly_quota,
                    can_use_gemini, can_edit_fields, can_verify_tax,
                    can_use_custom_template, can_view_history, can_use_typhoon,
                    can_push_erp, can_use_automation, can_manage_api_keys,
                    typhoon_quota_monthly, history_retention_days, custom_template_limit,
                    notes,
                ))
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
            cur.execute(
                "UPDATE users SET google_sub = %s WHERE id = %s",
                (google_sub, user_id)
            )
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
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL")
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
            cur.execute(
                "UPDATE users SET avatar_url = %s WHERE id = %s",
                (avatar_url, user_id)
            )
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
            cur.execute(
                "UPDATE users SET line_uid = %s WHERE id = %s",
                (line_uid, user_id)
            )
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
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_line_uid ON users(line_uid) WHERE line_uid IS NOT NULL")
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
            cur.execute("""
                UPDATE users SET username = %s, email = %s, email_normalized = %s
                WHERE id = %s
            """, (new_email_clean, new_email_clean, new_email_norm, user_id))
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
                pass
            # 5) 删临时账号
            cur.execute("DELETE FROM users WHERE id = %s", (temp_user_id,))
        logger.info(f"[v118.28.4.1] merged line_uid={line_uid} from temp={temp_user_id} → target={target_user_id}")
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
            cur.execute("CREATE INDEX IF NOT EXISTS idx_email_codes_email ON email_codes(email, purpose, used)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_email_codes_expires ON email_codes(expires_at)")
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
            cur.execute("""
                SELECT count FROM ip_usage
                WHERE ip_address = %s AND usage_date = CURRENT_DATE LIMIT 1
            """, (ip,))
            row = cur.fetchone()
            return row["count"] if row else 0
    except Exception as e:
        logger.error(f"查询 IP 用量失败: {e}")
        return 0


def increment_ip_usage(ip: str, n: int = 1) -> int:
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO ip_usage (ip_address, usage_date, count)
                VALUES (%s, CURRENT_DATE, %s)
                ON CONFLICT (ip_address, usage_date)
                DO UPDATE SET count = ip_usage.count + %s
                RETURNING count
            """, (ip, n, n))
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
            cur.execute("""
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
            """, (n, n, user_id))
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
            cur.execute("""
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
            """, (n, n, user_id))
            row = cur.fetchone()
            return row["typhoon_used_this_month"] if row else 0
    except Exception as e:
        logger.warning(f"更新 Typhoon 用量失败 · 但不影响识别 (user_id={user_id}): {e}")
        return 0


def get_user_monthly_usage(user_id: str) -> int:
    """查询某用户本月已用次数(若跨月返回 0)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    CASE
                        WHEN last_usage_month IS NULL
                          OR last_usage_month < DATE_TRUNC('month', NOW())::date
                        THEN 0
                        ELSE COALESCE(used_this_month, 0)
                    END AS used
                FROM users WHERE id = %s LIMIT 1
            """, (user_id,))
            row = cur.fetchone()
            return row["used"] if row else 0
    except Exception as e:
        logger.error(f"查询用户月用量失败 (user_id={user_id}): {e}")
        return 0


# ============================================================
# 第 5 批 · 历史记录(ocr_history 表)
# ============================================================

import json as _json
from datetime import datetime as _datetime, timedelta as _timedelta


def _extract_summary_fields(pages: list) -> dict:
    """从 pages 抽出列表展示用的核心字段
    v106.2 修复:多联发票(底单/发票/收据 3 页) Gemini 可能把所有页都标 is_copy=true · 
    导致摘要字段全 None · 列表显示「未识别到 · 金额 · 发票号 · 日期 · 卖方」误报
    改进:先找非副本主页 · 找不到再用 is_duplicate=False 的页 · 最后兜底用第 1 页
    """
    pages = pages or []
    
    def _build_from_page(p):
        f = (p.get("fields") or {})
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
        if f.get("invoice_number"): s += 1
        if f.get("total_amount"): s += 1
        if f.get("seller_name"): s += 1
        if f.get("date"): s += 1
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
) -> Optional[str]:
    """写入一条历史记录,返回新记录的 id(失败返回 None,不影响主流程)"""
    summary = _extract_summary_fields(pages)
    # v27.8.1.13a · 客户归属:校验 client_id 真属于该 user 的 tenant,防越权
    safe_client_id = None
    if client_id is not None:
        try:
            cid = int(client_id)
            with get_cursor() as cur:
                cur.execute("""
                    SELECT id FROM clients
                    WHERE id = %s
                      AND user_id IN (
                          SELECT id FROM users
                          WHERE tenant_id = (SELECT tenant_id FROM users WHERE id = %s)
                            OR id = %s
                      )
                    LIMIT 1
                """, (cid, user_id, user_id))
                if cur.fetchone():
                    safe_client_id = cid
        except Exception as e:
            logger.warning(f"insert_ocr_history client_id 校验失败 (user_id={user_id}, client_id={client_id}): {e}")
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO ocr_history (
                    user_id, filename, page_count, file_size_kb, file_hash,
                    pages, confidence, elapsed_ms,
                    invoice_no, invoice_date, seller_name, total_amount,
                    archive_name, category_tag, archived_at,
                    source_pdf_id, source_page_indices, source_index, source_total,
                    source, source_ref,
                    pdf_storage_path, pdf_size_bytes,
                    client_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s::jsonb, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, CASE WHEN %s IS NOT NULL THEN NOW() ELSE NULL END,
                    %s, %s::jsonb, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s
                )
                RETURNING id
            """, (
                user_id, filename, page_count, file_size_kb, file_hash,
                _json.dumps(pages, ensure_ascii=False), confidence, elapsed_ms,
                summary["invoice_no"], summary["invoice_date"],
                summary["seller_name"], summary["total_amount"],
                archive_name, category_tag, archive_name,
                source_pdf_id,
                _json.dumps(source_page_indices) if source_page_indices else None,
                source_index, source_total,
                source, source_ref,
                pdf_storage_path, pdf_size_bytes,
                safe_client_id,
            ))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"写入历史记录失败 (user_id={user_id}, file={filename}): {e}")
        return None


def get_history_pdf_info(user_id: str, record_id: str, tenant_id: Optional[str] = None) -> Optional[dict]:
    """v114 · 取一条历史的 PDF 留底信息(只查路径 · 鉴权用 user_id)
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可下载 PDF
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT pdf_storage_path, pdf_size_bytes, filename
                    FROM ocr_history
                    WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    LIMIT 1
                """, (record_id, tenant_id))
            else:
                cur.execute("""
                    SELECT pdf_storage_path, pdf_size_bytes, filename
                    FROM ocr_history
                    WHERE id = %s AND user_id = %s
                    LIMIT 1
                """, (record_id, user_id))
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


def find_ocr_by_hash(user_id: str, file_hash: str, max_age_hours: int = 24 * 30, tenant_id: Optional[str] = None) -> Optional[dict]:
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
                cur.execute("""
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
                """ % ("%s", "%s", int(max_age_hours)), (tenant_id, file_hash))
            else:
                cur.execute("""
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
                """ % ("%s", "%s", int(max_age_hours)), (user_id, file_hash))
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
                cur.execute(f"""
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
                """, params)
                row = cur.fetchone()
                if row:
                    return {
                        "level": "exact",
                        "matched_fields": ["invoice_no"],
                        "match": {
                            "id": str(row["id"]),
                            "filename": row["filename"],
                            "invoice_no": row["invoice_no"],
                            "invoice_date": row["invoice_date"].isoformat() if row["invoice_date"] else None,
                            "seller_name": row["seller_name"],
                            "total_amount": float(row["total_amount"]) if row["total_amount"] is not None else None,
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
                cur.execute(f"""
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
                """, params)
                row = cur.fetchone()
                if row:
                    return {
                        "level": "likely",
                        "matched_fields": ["invoice_date", "seller_name", "total_amount"],
                        "match": {
                            "id": str(row["id"]),
                            "filename": row["filename"],
                            "invoice_no": row["invoice_no"],
                            "invoice_date": row["invoice_date"].isoformat() if row["invoice_date"] else None,
                            "seller_name": row["seller_name"],
                            "total_amount": float(row["total_amount"]) if row["total_amount"] is not None else None,
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
            cur.execute("UPDATE users SET dup_check_enabled = %s WHERE id = %s",
                        (bool(enabled), user_id))
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
            cur.execute("UPDATE users SET gemini_api_key = %s WHERE id = %s",
                        (val, user_id))
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
            cur.execute(f"""
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
            """, params + [limit, offset])
            items = []
            for r in cur.fetchall():
                items.append({
                    "id": str(r["id"]),
                    "filename": r["filename"],
                    "page_count": r["page_count"],
                    "confidence": r["confidence"],
                    "elapsed_ms": r["elapsed_ms"],
                    "invoice_no": r["invoice_no"],
                    "invoice_date": r["invoice_date"].isoformat() if r["invoice_date"] else None,
                    "seller_name": r["seller_name"],
                    "total_amount": float(r["total_amount"]) if r["total_amount"] is not None else None,
                    "archive_name": r["archive_name"],
                    "category_tag": r["category_tag"],
                    "edited": r["fields_edited_at"] is not None,
                    "edit_count": r["edit_count"],
                    "created_at": r["created_at"].isoformat(),
                    # v0.11 · 多发票拆分字段
                    "source_pdf_id": str(r["source_pdf_id"]) if r.get("source_pdf_id") else None,
                    "source_index": r.get("source_index"),
                    "source_total": r.get("source_total"),
                    # v95 · 来源标识
                    "source": r.get("source") or "manual",
                    "source_ref": r.get("source_ref"),
                    # v114 · 是否有 PDF 留底(前端用来决定是否显示「下载 PDF」按钮)
                    "has_pdf": bool(r.get("pdf_storage_path")),
                })
            return {"items": items, "total": total}
    except Exception as e:
        logger.error(f"查询历史失败 (user_id={user_id}): {e}")
        return {"items": [], "total": 0}


def get_ocr_history_detail(user_id: str, record_id: str, tenant_id: Optional[str] = None) -> Optional[dict]:
    """取单条详情(含完整 pages)
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可查 · 否则只能查自己的
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT id, filename, page_count, confidence, elapsed_ms,
                           pages, invoice_no, invoice_date, seller_name, total_amount,
                           archive_name, category_tag,
                           fields_edited_at, edit_count, created_at, updated_at,
                           client_id
                    FROM ocr_history
                    WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    LIMIT 1
                """, (record_id, tenant_id))
            else:
                cur.execute("""
                    SELECT id, filename, page_count, confidence, elapsed_ms,
                           pages, invoice_no, invoice_date, seller_name, total_amount,
                           archive_name, category_tag,
                           fields_edited_at, edit_count, created_at, updated_at,
                           client_id
                    FROM ocr_history
                    WHERE id = %s AND user_id = %s
                    LIMIT 1
                """, (record_id, user_id))
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


def update_ocr_history_pages(user_id: str, record_id: str, new_pages: list, tenant_id: Optional[str] = None) -> bool:
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
            merged = (p.get("fields") or {})
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
            cur.execute(f"""
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
            """, (
                _json.dumps(new_pages, ensure_ascii=False),
                summary["invoice_no"], summary["invoice_date"],
                summary["seller_name"], summary["total_amount"],
                new_archive_name, new_category_tag, new_archive_name,
                *where_params,
            ))
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


def delete_ocr_history_with_pdf_paths(user_id: str, record_ids: list, tenant_id: Optional[str] = None) -> tuple:
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
# v0.6.0 · ERP 端点 + 推送日志
# ============================================================

def list_erp_endpoints(user_id: str, auto_push_only: bool = False) -> List[Dict[str, Any]]:
    """列出用户的所有 ERP 端点(默认排前面)· auto_push_only=True 时只返回开启自动推且 enabled 的"""
    try:
        with get_cursor() as cur:
            sql = """
                SELECT id, name, adapter, config, is_default, auto_push, enabled,
                       last_used_at, last_status, success_count, failure_count,
                       created_at, updated_at
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
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, name, adapter, config, is_default, auto_push, enabled,
                       last_used_at, last_status, success_count, failure_count,
                       created_at, updated_at, user_id
                FROM erp_endpoints
                WHERE user_id = %s AND id = %s
                LIMIT 1
            """, (user_id, endpoint_id))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_erp_endpoint failed: {e}")
        return None


def get_default_erp_endpoint(user_id: str) -> Optional[Dict[str, Any]]:
    """拿用户默认且启用的端点"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, name, adapter, config, is_default, auto_push, enabled
                FROM erp_endpoints
                WHERE user_id = %s AND enabled = true
                ORDER BY is_default DESC, created_at ASC
                LIMIT 1
            """, (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_default_erp_endpoint failed: {e}")
        return None


def create_erp_endpoint(user_id: str, name: str, adapter: str, config: Dict[str, Any],
                        is_default: bool = False, auto_push: bool = False) -> Optional[str]:
    """创建端点。如果 is_default=True,会自动取消其他端点的默认状态。返回新 id"""
    import json as _json
    try:
        with get_cursor(commit=True) as cur:
            if is_default:
                cur.execute("UPDATE erp_endpoints SET is_default = false WHERE user_id = %s", (user_id,))
            cur.execute("""
                INSERT INTO erp_endpoints (user_id, name, adapter, config, is_default, auto_push)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                RETURNING id
            """, (user_id, name, adapter, _json.dumps(config), is_default, auto_push))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_erp_endpoint failed: {e}")
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
        with get_cursor(commit=True) as cur:
            # 如果设为默认,先取消其他默认
            if fields.get("is_default"):
                cur.execute("UPDATE erp_endpoints SET is_default = false WHERE user_id = %s AND id <> %s",
                            (user_id, endpoint_id))
            sql = f"UPDATE erp_endpoints SET {', '.join(sets)} WHERE user_id = %s AND id = %s"
            vals.extend([user_id, endpoint_id])
            cur.execute(sql, tuple(vals))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_erp_endpoint failed: {e}")
        return False


def delete_erp_endpoint(user_id: str, endpoint_id: str) -> bool:
    try:
        with get_cursor(commit=True) as cur:
            # v118.25.0.2 · 删端点前 · 先把这个端点所有挂起的重试停掉(避免 worker 继续跑)
            cur.execute("""
                UPDATE erp_push_logs
                SET next_retry_at = NULL
                WHERE user_id = %s AND endpoint_id = %s AND next_retry_at IS NOT NULL
            """, (user_id, endpoint_id))
            cur.execute("DELETE FROM erp_endpoints WHERE user_id = %s AND id = %s",
                        (user_id, endpoint_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_endpoint failed: {e}")
        return False


def insert_push_log(user_id: str, endpoint_id: Optional[str], history_id: Optional[str],
                    invoice_no: Optional[str], seller_name: Optional[str],
                    total_amount: Optional[float],
                    status: str, http_status: Optional[int],
                    request_body: Optional[Dict], response_body: Optional[str],
                    error_msg: Optional[str], attempt: int, elapsed_ms: int,
                    trigger: str = "manual") -> Optional[str]:
    import json as _json
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO erp_push_logs (
                    user_id, endpoint_id, history_id, invoice_no, seller_name,
                    total_amount, status, http_status, request_body, response_body,
                    error_msg, attempt, elapsed_ms, trigger
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, endpoint_id, history_id, invoice_no, seller_name,
                  total_amount, status, http_status,
                  _json.dumps(request_body) if request_body else None,
                  response_body, error_msg, attempt, elapsed_ms, trigger))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"insert_push_log failed: {e}")
        return None


def update_endpoint_stats(endpoint_id: str, success: bool):
    """推送完成后更新端点的成功/失败计数 + last_used_at + last_status"""
    try:
        with get_cursor(commit=True) as cur:
            if success:
                cur.execute("""
                    UPDATE erp_endpoints
                    SET success_count = success_count + 1,
                        last_used_at = NOW(),
                        last_status = 'success'
                    WHERE id = %s
                """, (endpoint_id,))
            else:
                cur.execute("""
                    UPDATE erp_endpoints
                    SET failure_count = failure_count + 1,
                        last_used_at = NOW(),
                        last_status = 'failed'
                    WHERE id = %s
                """, (endpoint_id,))
    except Exception as e:
        logger.error(f"update_endpoint_stats failed: {e}")


def update_history_push_status(history_id: str, status: str):
    """更新 ocr_history 的 last_push_status / last_pushed_at"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE ocr_history
                SET last_pushed_at = NOW(), last_push_status = %s
                WHERE id = %s
            """, (status, history_id))
    except Exception as e:
        logger.error(f"update_history_push_status failed: {e}")


# ============================================================
# v118.25 · ERP 推送失败自动重试(指数退避)
# ============================================================
def ensure_erp_retry_columns():
    """启动时给 erp_push_logs 表加 retry 相关列 · 幂等(列已存在则跳过)"""
    try:
        with get_cursor(commit=True) as cur:
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
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE erp_push_logs
                SET next_retry_at = NOW() + (%s * INTERVAL '1 second')
                WHERE id = %s AND status = 'failed'
            """, (int(delay_sec), log_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"schedule_log_retry failed: {e}")
        return False


def clear_retry_schedule(log_id: str):
    """重试成功 / 达到上限后调用 · 清空 next_retry_at(从队列里摘出来)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE erp_push_logs
                SET next_retry_at = NULL
                WHERE id = %s
            """, (log_id,))
    except Exception as e:
        logger.error(f"clear_retry_schedule failed: {e}")


def list_logs_due_for_retry(limit: int = 20) -> List[Dict[str, Any]]:
    """找到当下到期需要重试的失败日志 · 按到期时间正序"""
    try:
        with get_cursor() as cur:
            cur.execute("""
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
            """, (int(limit),))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_logs_due_for_retry failed: {e}")
        return []


def increment_retry_count(log_id: str) -> int:
    """重试一次后自增 retry_count · 返回新值"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE erp_push_logs
                SET retry_count = retry_count + 1
                WHERE id = %s
                RETURNING retry_count
            """, (log_id,))
            row = cur.fetchone()
            return int(row["retry_count"]) if row else 0
    except Exception as e:
        logger.error(f"increment_retry_count failed: {e}")
        return 0


def update_log_status_after_retry(log_id: str, success: bool,
                                  http_status: Optional[int],
                                  response_body: Optional[str],
                                  error_msg: Optional[str],
                                  elapsed_ms: int):
    """重试完成后更新原 log 的 status / http_status / response · 不写新行"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE erp_push_logs
                SET status = %s,
                    http_status = %s,
                    response_body = %s,
                    error_msg = %s,
                    elapsed_ms = %s
                WHERE id = %s
            """, ("success" if success else "failed",
                  http_status, response_body, error_msg, int(elapsed_ms), log_id))
    except Exception as e:
        logger.error(f"update_log_status_after_retry failed: {e}")


def list_push_logs(user_id: str, history_id: Optional[str] = None,
                   endpoint_id: Optional[str] = None,
                   status_filter: Optional[str] = None,
                   trigger_filter: Optional[str] = None,
                   limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """查询推送日志,支持按 history/endpoint/status/trigger 过滤"""
    try:
        with get_cursor() as cur:
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
            cur.execute(f"SELECT COUNT(*) AS n FROM erp_push_logs WHERE {where_sql}", tuple(params))
            total = cur.fetchone()["n"]
            cur.execute(f"""
                SELECT id, endpoint_id, history_id, invoice_no, seller_name,
                       total_amount, status, http_status, error_msg, attempt,
                       elapsed_ms, trigger, created_at,
                       retry_count, max_retries, next_retry_at
                FROM erp_push_logs
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, tuple(params) + (limit, offset))
            items = [dict(r) for r in cur.fetchall()]
            return {"items": items, "total": total}
    except Exception as e:
        logger.error(f"list_push_logs failed: {e}")
        return {"items": [], "total": 0}


def get_push_log_detail(user_id: str, log_id: str) -> Optional[Dict[str, Any]]:
    """单条推送日志完整详情(含 request_body / response_body)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, endpoint_id, history_id, invoice_no, seller_name,
                       total_amount, status, http_status,
                       request_body, response_body, error_msg,
                       attempt, elapsed_ms, trigger, created_at,
                       retry_count, max_retries, next_retry_at
                FROM erp_push_logs
                WHERE id = %s AND user_id = %s
            """, (log_id, user_id))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_push_log_detail failed: {e}")
        return None


def get_push_stats_today(user_id: str) -> Dict[str, Any]:
    """今日推送统计(总数 · 成功 · 失败)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status='success') AS success,
                    COUNT(*) FILTER (WHERE status='failed') AS failed,
                    COUNT(*) FILTER (WHERE trigger='auto') AS auto_cnt
                FROM erp_push_logs
                WHERE user_id = %s
                  AND created_at >= CURRENT_DATE
            """, (user_id,))
            row = cur.fetchone()
            return dict(row) if row else {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0}
    except Exception as e:
        logger.error(f"get_push_stats_today failed: {e}")
        return {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0}


# ============================================================
# v0.7 · 智能归档
# ============================================================
def get_archive_settings(user_id: str) -> Optional[Dict[str, Any]]:
    """读用户的归档设置。没配过就返回 None(调用方用默认)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT user_id, name_template, folder_strategy
                FROM archive_settings WHERE user_id = %s
            """, (user_id,))
            r = cur.fetchone()
            return dict(r) if r else None
    except Exception as e:
        logger.error(f"get_archive_settings failed: {e}")
        return None


def get_archive_template(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """只读命名模板。给识别流程用的快捷方法"""
    s = get_archive_settings(user_id)
    if not s:
        return None
    tpl = s.get("name_template") or []
    return tpl if isinstance(tpl, list) and tpl else None


def upsert_archive_settings(user_id: str,
                            name_template: List[Dict[str, Any]],
                            folder_strategy: str) -> bool:
    """创建或更新归档设置"""
    if folder_strategy not in ("none", "by_month", "by_seller", "by_month_seller"):
        folder_strategy = "by_month_seller"
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO archive_settings (user_id, name_template, folder_strategy)
                VALUES (%s, %s::jsonb, %s)
                ON CONFLICT (user_id) DO UPDATE
                  SET name_template = EXCLUDED.name_template,
                      folder_strategy = EXCLUDED.folder_strategy,
                      updated_at = NOW()
            """, (user_id, _json.dumps(name_template or []), folder_strategy))
            return True
    except Exception as e:
        logger.error(f"upsert_archive_settings failed: {e}")
        return False


# ============================================================
# v0.8 · RD 校验日限(Free 5/天)
# ============================================================
def get_rd_daily_usage(user_id: str) -> int:
    """返回今天用户已调 RD 的次数"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT count FROM rd_daily_usage
                WHERE user_id = %s AND day = CURRENT_DATE
            """, (user_id,))
            r = cur.fetchone()
            return int(r["count"]) if r else 0
    except Exception as e:
        logger.error(f"get_rd_daily_usage failed: {e}")
        return 0


def increment_rd_daily_usage(user_id: str, n: int = 1) -> int:
    """RD 调用成功后 +1 · 自动按当天聚合"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO rd_daily_usage (user_id, day, count)
                VALUES (%s, CURRENT_DATE, %s)
                ON CONFLICT (user_id, day) DO UPDATE
                SET count = rd_daily_usage.count + EXCLUDED.count
                RETURNING count
            """, (user_id, n))
            r = cur.fetchone()
            return int(r["count"]) if r else n
    except Exception as e:
        logger.error(f"increment_rd_daily_usage failed: {e}")
        return 0


# ============================================================
# v0.8.1 · 过期历史清理
# ============================================================
def cleanup_expired_history(free_days: int = 7, plus_days: int = 90, pro_days: int = 365) -> int:
    """按 plan 删除过期历史 · 返回删除条数"""
    total = 0
    try:
        with get_cursor(commit=True) as cur:
            # Free
            cur.execute("""
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'free')
                  AND created_at < NOW() - (%s || ' days')::interval
            """, (str(free_days),))
            total += cur.rowcount
            # Plus
            cur.execute("""
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'plus')
                  AND created_at < NOW() - (%s || ' days')::interval
            """, (str(plus_days),))
            total += cur.rowcount
            # Pro
            cur.execute("""
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'pro')
                  AND created_at < NOW() - (%s || ' days')::interval
            """, (str(pro_days),))
            total += cur.rowcount
        return total
    except Exception as e:
        logger.error(f"cleanup_expired_history failed: {e}")
        return 0


# ============================================================
# v0.17 · M6 · 邮箱抓取
# ============================================================
def get_email_account(user_id: str) -> Optional[Dict[str, Any]]:
    """读当前用户绑定的邮箱账号(第一版一人一个)· 返回完整行(含 password_enc)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, user_id, email_address, imap_host, imap_port, imap_use_ssl,
                       password_enc, folder, filter_subject, filter_sender, mark_as_read,
                       enabled, last_check_at, last_error,
                       success_count, failure_count, last_fetched_at,
                       interval_min,
                       created_at, updated_at
                FROM email_ingest_accounts
                WHERE user_id = %s
                LIMIT 1
            """, (str(user_id),))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_email_account failed: {e}")
        return None


def get_email_account_safe(user_id: str) -> Optional[Dict[str, Any]]:
    """前端用 · 不返回 password_enc · 返回 has_password 标志"""
    row = get_email_account(user_id)
    if not row:
        return None
    password_enc = row.pop("password_enc", None)
    row["has_password"] = bool(password_enc)
    return row


def upsert_email_account(user_id: str, email_address: str, imap_host: str,
                          imap_port: int, imap_use_ssl: bool,
                          password_enc: Optional[bytes],
                          folder: str = "INBOX",
                          filter_subject: Optional[str] = None,
                          filter_sender: Optional[str] = None,
                          mark_as_read: bool = True,
                          enabled: bool = True,
                          interval_min: int = 15) -> Optional[str]:
    """新增或更新邮箱账号 · 返回 id(若未传 password_enc 则保留旧密码)"""
    # 限制 interval_min 只能是 5/15/60 · 其他值兜底成 15
    if interval_min not in (5, 15, 60):
        interval_min = 15
    try:
        with get_cursor(commit=True) as cur:
            if password_enc is not None:
                cur.execute("""
                    INSERT INTO email_ingest_accounts
                        (user_id, email_address, imap_host, imap_port, imap_use_ssl,
                         password_enc, folder, filter_subject, filter_sender,
                         mark_as_read, enabled, interval_min)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email_address = EXCLUDED.email_address,
                        imap_host     = EXCLUDED.imap_host,
                        imap_port     = EXCLUDED.imap_port,
                        imap_use_ssl  = EXCLUDED.imap_use_ssl,
                        password_enc  = EXCLUDED.password_enc,
                        folder        = EXCLUDED.folder,
                        filter_subject= EXCLUDED.filter_subject,
                        filter_sender = EXCLUDED.filter_sender,
                        mark_as_read  = EXCLUDED.mark_as_read,
                        enabled       = EXCLUDED.enabled,
                        interval_min  = EXCLUDED.interval_min,
                        updated_at    = NOW()
                    RETURNING id
                """, (str(user_id), email_address, imap_host, int(imap_port),
                       bool(imap_use_ssl), password_enc, folder,
                       filter_subject, filter_sender, bool(mark_as_read),
                       bool(enabled), interval_min))
            else:
                # 不改密码的更新(用户只改配置)
                cur.execute("""
                    INSERT INTO email_ingest_accounts
                        (user_id, email_address, imap_host, imap_port, imap_use_ssl,
                         password_enc, folder, filter_subject, filter_sender,
                         mark_as_read, enabled, interval_min)
                    VALUES (%s, %s, %s, %s, %s, ''::bytea, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email_address = EXCLUDED.email_address,
                        imap_host     = EXCLUDED.imap_host,
                        imap_port     = EXCLUDED.imap_port,
                        imap_use_ssl  = EXCLUDED.imap_use_ssl,
                        folder        = EXCLUDED.folder,
                        filter_subject= EXCLUDED.filter_subject,
                        filter_sender = EXCLUDED.filter_sender,
                        mark_as_read  = EXCLUDED.mark_as_read,
                        enabled       = EXCLUDED.enabled,
                        interval_min  = EXCLUDED.interval_min,
                        updated_at    = NOW()
                    RETURNING id
                """, (str(user_id), email_address, imap_host, int(imap_port),
                       bool(imap_use_ssl), folder,
                       filter_subject, filter_sender, bool(mark_as_read),
                       bool(enabled), interval_min))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_email_account failed: {e}")
        return None


def delete_email_account(user_id: str) -> bool:
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                DELETE FROM email_ingest_accounts WHERE user_id = %s
            """, (str(user_id),))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_email_account failed: {e}")
        return False


def list_enabled_email_accounts() -> List[Dict[str, Any]]:
    """定时任务用 · 列出所有启用的账号(含 password_enc 供解密)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, user_id, email_address, imap_host, imap_port, imap_use_ssl,
                       password_enc, folder, filter_subject, filter_sender,
                       mark_as_read, last_check_at, last_fetched_at, interval_min
                FROM email_ingest_accounts
                WHERE enabled = TRUE
                ORDER BY last_check_at NULLS FIRST, created_at
            """)
            return [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.error(f"list_enabled_email_accounts failed: {e}")
        return []


def update_email_account_status(account_id: str, success: bool,
                                 error_msg: Optional[str] = None,
                                 fetched_any: bool = False):
    """每次抓取完更新账号状态"""
    try:
        with get_cursor(commit=True) as cur:
            if success:
                if fetched_any:
                    cur.execute("""
                        UPDATE email_ingest_accounts
                        SET last_check_at   = NOW(),
                            last_fetched_at = NOW(),
                            last_error      = NULL,
                            success_count   = success_count + 1,
                            updated_at      = NOW()
                        WHERE id = %s
                    """, (account_id,))
                else:
                    cur.execute("""
                        UPDATE email_ingest_accounts
                        SET last_check_at = NOW(),
                            last_error    = NULL,
                            updated_at    = NOW()
                        WHERE id = %s
                    """, (account_id,))
            else:
                cur.execute("""
                    UPDATE email_ingest_accounts
                    SET last_check_at   = NOW(),
                        last_error      = %s,
                        failure_count   = failure_count + 1,
                        updated_at      = NOW()
                    WHERE id = %s
                """, (error_msg, account_id))
    except Exception as e:
        logger.error(f"update_email_account_status failed: {e}")


def insert_email_ingest_log(account_id: str, user_id: str, stats: Dict[str, Any],
                             trigger: str = "auto") -> Optional[str]:
    """写一条抓取日志"""
    import json as _json
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO email_ingest_logs
                    (account_id, user_id, status, emails_scanned, attachments_found,
                     ocr_succeeded, ocr_failed, elapsed_ms, error_message, error_details, trigger)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                RETURNING id
            """, (
                account_id, user_id,
                stats.get("status"),
                int(stats.get("emails_scanned") or 0),
                int(stats.get("attachments_found") or 0),
                int(stats.get("ocr_succeeded") or 0),
                int(stats.get("ocr_failed") or 0),
                int(stats.get("elapsed_ms") or 0),
                stats.get("error_message"),
                _json.dumps(stats.get("error_details") or [], ensure_ascii=False),
                trigger,
            ))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"insert_email_ingest_log failed: {e}")
        return None


def list_email_ingest_logs(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """前端用 · 最近的抓取日志"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, status, emails_scanned, attachments_found,
                       ocr_succeeded, ocr_failed, elapsed_ms,
                       error_message, trigger, created_at
                FROM email_ingest_logs
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (str(user_id), int(limit)))
            return [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.error(f"list_email_ingest_logs failed: {e}")
        return []


def is_email_uid_seen(account_id: str, uid: str) -> bool:
    """查这封邮件是否抓过"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT 1 FROM email_ingest_seen_uids
                WHERE account_id = %s AND uid = %s LIMIT 1
            """, (account_id, uid))
            return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"is_email_uid_seen failed: {e}")
        return False


def mark_email_uid_seen(account_id: str, uid: str, history_id: Optional[str],
                         subject: Optional[str], sender: Optional[str]) -> bool:
    """标记这封邮件处理过 · history_id 可为空(无附件/OCR 失败场景)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO email_ingest_seen_uids
                    (account_id, uid, history_id, subject, sender)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (account_id, uid) DO NOTHING
            """, (account_id, uid, history_id, (subject or "")[:500], (sender or "")[:200]))
            return True
    except Exception as e:
        logger.error(f"mark_email_uid_seen failed: {e}")
        return False


# ============================================================
# v0.18 · M10 · 银行对账
# ============================================================

# v118.26.2 · 给 bank_reconcile_sessions 加 client_id 列(幂等)
#   行业标配:Xero/QB 一个 bank account 属于一个 organisation
#   我们事务所多客户 → session 必须带 client_id · 用于 v28.1 client filter
def ensure_bank_recon_client_id_column():
    """启动时调一次 · 给 bank_reconcile_sessions 加 client_id 列"""
    try:
        with get_cursor(commit=True) as cur:
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


def create_bank_recon_session(user_id: str, bank_code: str, filename: str,
                               pages: int) -> Optional[str]:
    """创建一条会话 · 返回 id"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO bank_reconcile_sessions
                    (user_id, bank_code, source_filename, source_pages, parse_status)
                VALUES (%s, %s, %s, %s, 'pending')
                RETURNING id
            """, (str(user_id), bank_code, (filename or "")[:200], int(pages)))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_bank_recon_session failed: {e}")
        return None


def save_bank_recon_parse(session_id: str, parsed: Dict[str, Any]) -> bool:
    """解析完成后把会话 + 流水批量落库"""
    try:
        with get_cursor(commit=True) as cur:
            tx_n = len(parsed.get("transactions") or [])
            # 更新会话头信息
            # v118.26.1 · 补 unmatched_count = tx_n / matched_count = 0
            #   因为流水落库默认 match_status='unmatched' · 不写这俩字段会让顶部 chip 计数永远 0
            cur.execute("""
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
            """, (
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
                tx_n,           # unmatched_count = 全部初始未匹配
                session_id,
            ))
            row = cur.fetchone()
            if not row:
                return False
            user_id = row["user_id"]

            # 批量插入流水
            txs = parsed.get("transactions") or []
            for tx in txs:
                cur.execute("""
                    INSERT INTO bank_reconcile_transactions
                        (session_id, user_id, row_no, tx_date, value_date, direction,
                         amount, balance_after, description, counterparty, ref_no, channel)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id, user_id, tx.get("row_no"),
                    tx.get("tx_date"), tx.get("value_date") or tx.get("tx_date"),
                    tx.get("direction"), tx.get("amount"),
                    tx.get("balance_after"),
                    (tx.get("description") or "")[:500],
                    (tx.get("counterparty") or "")[:200] if tx.get("counterparty") else None,
                    (tx.get("ref_no") or "")[:100] if tx.get("ref_no") else None,
                    (tx.get("channel") or "")[:50] if tx.get("channel") else None,
                ))
            return True
    except Exception as e:
        logger.error(f"save_bank_recon_parse failed: {e}")
        return False


def mark_recon_parse_failed(session_id: str, error_msg: str) -> bool:
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE bank_reconcile_sessions
                SET parse_status = 'parse_failed',
                    parse_error  = %s,
                    updated_at   = NOW()
                WHERE id = %s
            """, ((error_msg or "")[:500], session_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"mark_recon_parse_failed failed: {e}")
        return False


def get_bank_recon_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """获取会话头(鉴权)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT * FROM bank_reconcile_sessions
                WHERE id = %s AND user_id = %s
            """, (session_id, str(user_id)))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_bank_recon_session failed: {e}")
        return None


def list_bank_recon_sessions(user_id: str, limit: int = 30,
                              restrict_client_ids: Optional[List[int]] = None
                              ) -> List[Dict[str, Any]]:
    """列最近会话
    v118.26.2 · 加 restrict_client_ids 参数(v28.1 客户分配 filter)
      None       → 不限(老板/超管)
      []         → 没分到任何客户 · 只能看自己上传未归属(client_id IS NULL)
      [1,2,3]    → (client_id IN list) OR (user_id = self AND client_id IS NULL)
    """
    try:
        with get_cursor() as cur:
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
def update_bank_recon_session_client(user_id: str, session_id: str,
                                      client_id: Optional[int]) -> bool:
    """
    更新 session 的 client_id · None 表示解绑
    鉴权:session 必须属于本 user
    返回:成功 True / 不存在 False
    """
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE bank_reconcile_sessions
                SET client_id = %s, updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """, (client_id, session_id, str(user_id)))
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

        with get_cursor() as cur:
            cur.execute("""
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
            """, (str(user_id), month_start_bkk))
            row = cur.fetchone()
            if not row:
                return default
            d = dict(row)
            return {
                "pending": int(d.get("pending") or 0),
                "matched": int(d.get("matched") or 0),
                "unmatched": int(d.get("unmatched") or 0),
                "total_sessions": int(d.get("total_sessions") or 0),
                "last_activity_at": d["last_activity_at"].isoformat() if d.get("last_activity_at") else None,
            }
    except Exception as e:
        # v118.26.0.1 · 完整 traceback 进日志 · 方便定位
        logger.exception(f"get_bank_recon_stats failed for user={user_id}: {e}")
        return default


def list_bank_recon_transactions(session_id: str, user_id: str,
                                  match_filter: Optional[str] = None,
                                  limit: int = 500) -> List[Dict[str, Any]]:
    """列一个会话下的流水 · 可按 match_status 过滤"""
    try:
        with get_cursor() as cur:
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
        with get_cursor(commit=True) as cur:
            cur.execute("""
                DELETE FROM bank_reconcile_sessions
                WHERE id = %s AND user_id = %s
            """, (session_id, str(user_id)))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_bank_recon_session failed: {e}")
        return False


def find_invoice_candidates_for_tx(user_id: str, amount: float,
                                    tx_date: str,
                                    amount_tol: float = 10.0,
                                    date_tol_days: int = 7) -> List[Dict[str, Any]]:
    """
    匹配算法用 · 在 ocr_history 里粗筛候选发票(用索引高效过滤)
    条件:同用户 · 金额差 ≤ amount_tol · 日期差 ≤ date_tol_days
    返回:[{id, amount_total, invoice_date, vendor, invoice_no, category_tag}, ...]
    """
    if not amount or not tx_date:
        return []
    try:
        with get_cursor() as cur:
            # pages 字段里 JSON 可能保存了 amount / total / invoice_date / vendor
            # 我们从 history 表的标量字段取(status=success 的)· 容忍 JSONB 结构
            cur.execute("""
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
            """, (
                str(user_id),
                float(amount) - float(amount_tol),
                float(amount) + float(amount_tol),
                tx_date, f"{date_tol_days} days",
                tx_date, f"{date_tol_days} days",
            ))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        # 如果 ocr_history 里没有这些标量字段(旧版),降级从 pages JSONB 查
        logger.warning(f"find_invoice_candidates_for_tx SQL 降级: {e}")
        return _find_candidates_from_pages_jsonb(user_id, amount, tx_date,
                                                  amount_tol, date_tol_days)


def _find_candidates_from_pages_jsonb(user_id: str, amount: float,
                                       tx_date: str, amount_tol: float,
                                       date_tol_days: int) -> List[Dict[str, Any]]:
    """降级查询:从 pages JSONB 里找 · 效率稍低 · 适合历史数据少(< 5000)"""
    try:
        from datetime import timedelta
        d = date.fromisoformat(tx_date)
        d_start = (d - timedelta(days=date_tol_days)).isoformat()
        d_end   = (d + timedelta(days=date_tol_days)).isoformat()

        with get_cursor() as cur:
            cur.execute("""
                SELECT id, pages, filename, category_tag, created_at
                FROM ocr_history
                WHERE user_id = %s
                  AND status = 'success'
                  AND created_at BETWEEN %s::date - interval '60 days'
                                   AND %s::date + interval '30 days'
                LIMIT 500
            """, (str(user_id), d_start, d_end))
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
                amt = (p.get("amount_total") or p.get("total")
                       or p.get("amount"))
                inv_date = (p.get("invoice_date") or p.get("date"))
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
                        pass
                out.append({
                    "id": row["id"],
                    "amount_total": amt_f,
                    "invoice_date": inv_date,
                    "vendor":       p.get("vendor") or p.get("seller"),
                    "invoice_no":   p.get("invoice_no") or p.get("number"),
                    "category_tag": row.get("category_tag"),
                    "filename":     row.get("filename"),
                })
                break  # 一份历史只取一次
        return out
    except Exception as e:
        logger.error(f"_find_candidates_from_pages_jsonb failed: {e}")
        return []


def save_match_result(tx_id: str, scored: List[Dict[str, Any]],
                       thresh_auto: float = 85, thresh_suggest: float = 60) -> str:
    """
    写入匹配结果
    - 清空该 tx 之前的 candidates
    - 按分数阶梯决定 match_status
    返回:最终 match_status(matched / suggested / unmatched)
    """
    try:
        with get_cursor(commit=True) as cur:
            # 清旧候选
            cur.execute("DELETE FROM bank_reconcile_candidates WHERE tx_id = %s", (tx_id,))

            if not scored:
                cur.execute("""
                    UPDATE bank_reconcile_transactions
                    SET match_status = 'unmatched',
                        matched_history_id = NULL,
                        match_score = NULL,
                        match_reason = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                """, (tx_id,))
                return "unmatched"

            best = scored[0]
            best_score = best["score"]

            # 写所有候选
            for i, c in enumerate(scored):
                is_picked = (i == 0 and best_score >= thresh_suggest)
                cur.execute("""
                    INSERT INTO bank_reconcile_candidates
                        (tx_id, history_id, score, reason, is_auto_picked)
                    VALUES (%s, %s, %s, %s, %s)
                """, (tx_id, c["history_id"], c["score"], c["reason"], is_picked))

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

            cur.execute("""
                UPDATE bank_reconcile_transactions
                SET match_status = %s,
                    matched_history_id = %s,
                    match_score = %s,
                    match_reason = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (status, matched_id,
                   best_score if matched_id else None,
                   best["reason"] if matched_id else None,
                   tx_id))
            return status
    except Exception as e:
        logger.error(f"save_match_result failed: {e}")
        return "unmatched"


# v118.26.2 · 获取一条流水的所有候选发票(JOIN ocr_history 拿展示字段)
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
        with get_cursor() as cur:
            # 鉴权 + JOIN
            cur.execute("""
                SELECT c.history_id, c.score, c.reason, c.is_auto_picked,
                       h.invoice_no, h.vendor, h.amount_total, h.invoice_date,
                       h.filename, h.category_tag, h.created_at AS h_created_at
                FROM bank_reconcile_candidates c
                JOIN bank_reconcile_transactions t ON t.id = c.tx_id
                LEFT JOIN ocr_history h ON h.id = c.history_id
                WHERE c.tx_id = %s AND t.user_id = %s
                ORDER BY c.score DESC
                LIMIT 5
            """, (tx_id, str(user_id)))
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
        with get_cursor(commit=True) as cur:
            cur.execute("""
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
            """, (session_id,))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_session_match_stats failed: {e}")
        return False


def override_tx_match(tx_id: str, user_id: str,
                       history_id: Optional[str],
                       status: str) -> bool:
    """用户手动重指派 · 或忽略一条流水
    status: matched / unmatched / ignored
    """
    if status not in ("matched", "unmatched", "ignored"):
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE bank_reconcile_transactions
                SET match_status = %s,
                    matched_history_id = %s,
                    match_reviewed_by = %s,
                    match_reviewed_at = NOW(),
                    match_reason = COALESCE(match_reason, 'user_override'),
                    updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """, (status, history_id, str(user_id), tx_id, str(user_id)))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"override_tx_match failed: {e}")
        return False


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
        with get_cursor(commit=True) as cur:
            # 1. 建 session(标记 source_filename 含 _MOCK_ 易识别 · 用户能看到一目了然)
            today = datetime.now()
            period_start = (today.replace(day=1) - timedelta(days=30)).date()
            period_end = today.replace(day=1).date() - timedelta(days=1)
            cur.execute("""
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
            """, (
                str(user_id),
                f"_MOCK_KBANK_statement_{period_end.strftime('%Y%m')}.pdf",
                period_end.strftime('%Y-%m'),
                period_start, period_end,
            ))
            session_id = str(cur.fetchone()["id"])

            # 2. 8 条流水(混合金额 · 跨 30 天 · 让候选评分有变化)
            mock_txs = [
                # (天偏移, 方向, 金额, 描述, 频道)
                (-28, 'IN',  12500.00, 'TRF FROM ABC TRADING CO LTD',         'Mobile'),
                (-25, 'OUT',  3200.00, 'PAY OFFICE RENT',                     'ATM'),
                (-22, 'IN',   8900.00, 'XFER from XYZ Logistics',             'Mobile'),
                (-18, 'IN',  21000.00, 'INWARD REMIT - DELTA SERVICES',       'Counter'),
                (-14, 'OUT',  4800.00, 'BILL PAY - electricity',              'AutoDeb'),
                (-10, 'IN',   3520.50, 'TRF FROM SOMCHAI ENTERPRISE',         'Mobile'),
                (-6,  'OUT',  7100.00, 'PAY VENDOR - office supplies',        'Mobile'),
                (-2,  'IN',  12500.00, 'TRF FROM ABC TRADING',                'Mobile'),  # 跟 -28 同金额 · 测多候选
            ]
            for off, direction, amt, desc, channel in mock_txs:
                tx_date = (today + timedelta(days=off)).date()
                cur.execute("""
                    INSERT INTO bank_reconcile_transactions
                        (session_id, user_id, tx_date, direction, amount,
                         description, channel, match_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'unmatched')
                """, (session_id, str(user_id), tx_date, direction,
                       amt, desc, channel))
            return {"ok": True, "session_id": session_id, "tx_count": 8}
    except Exception as e:
        logger.error(f"seed_bank_recon_test_data failed: {e}")
        return {"ok": False, "error": str(e)[:200]}


def clear_bank_recon_test_data(user_id: str) -> int:
    """清掉 skin 名下所有 _MOCK_ 开头的 session(含其下流水/候选 · 走 ON DELETE CASCADE)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                DELETE FROM bank_reconcile_sessions
                WHERE user_id = %s AND source_filename LIKE '_MOCK_%%'
            """, (str(user_id),))
            return cur.rowcount or 0
    except Exception as e:
        logger.error(f"clear_bank_recon_test_data failed: {e}")
        return 0


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
            cur.execute("""
                UPDATE line_binding_codes
                   SET used_at = NOW()
                 WHERE user_id = %s
                   AND used_at IS NULL
            """, (str(user_id),))

            # 插入新码
            cur.execute("""
                INSERT INTO line_binding_codes (code, user_id, expires_at)
                VALUES (%s, %s, %s)
                RETURNING code, expires_at
            """, (code, str(user_id), expires_at))
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
            cur.execute("""
                UPDATE line_binding_codes
                   SET used_at = NOW()
                 WHERE code = %s
                   AND used_at IS NULL
                   AND expires_at > NOW()
                RETURNING user_id
            """, (code,))
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
            cur.execute("""
                SELECT user_id FROM line_bindings
                 WHERE line_user_id = %s
                 LIMIT 1
            """, (line_user_id,))
            row = cur.fetchone()
            if row and str(row["user_id"]) != str(user_id):
                logger.warning(
                    f"LINE {line_user_id} 已绑到 user {row['user_id']} · "
                    f"拒绝绑到 user {user_id}"
                )
                return False

            # 先清空该 mrpilot user 已有的其他 LINE 绑定(换绑场景)
            cur.execute("""
                DELETE FROM line_bindings
                 WHERE user_id = %s
                   AND line_user_id != %s
            """, (str(user_id), line_user_id))

            # upsert
            cur.execute("""
                INSERT INTO line_bindings
                    (user_id, line_user_id, line_display_name, line_picture_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (line_user_id) DO UPDATE SET
                    user_id            = EXCLUDED.user_id,
                    line_display_name  = EXCLUDED.line_display_name,
                    line_picture_url   = EXCLUDED.line_picture_url,
                    last_active_at     = NOW()
            """, (str(user_id), line_user_id, display_name, picture_url))
            return True
    except Exception as e:
        logger.error(f"create_or_update_line_binding failed: {e}")
        return False


def get_line_binding_by_user(user_id: str) -> Optional[Dict[str, Any]]:
    """查某 mrpilot 用户当前的 LINE 绑定信息"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT line_user_id, line_display_name, line_picture_url,
                       bound_at, last_active_at
                  FROM line_bindings
                 WHERE user_id = %s
                 LIMIT 1
            """, (str(user_id),))
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
            cur.execute("""
                UPDATE line_bindings SET last_active_at = NOW()
                 WHERE line_user_id = %s
                RETURNING user_id
            """, (line_user_id,))
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
            cur.execute("""
                DELETE FROM line_bindings WHERE user_id = %s
            """, (str(user_id),))
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
            cur.execute("""
                UPDATE users SET preferred_lang = %s WHERE id = %s
            """, (lang, str(user_id)))
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
            cur.execute("""
                SELECT t.*
                FROM tenants t
                JOIN users u ON u.tenant_id = t.id
                WHERE u.id = %s
                LIMIT 1
            """, (str(user_id),))
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
            cur.execute("""
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
            """, (int(limit),))
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
            cur.execute("""
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
            """, (
                name,
                str(owner_user_id) if owner_user_id else None,
                tenant_type,
                int(monthly_quota) if monthly_quota else 0,
                notes,
            ))
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
            cur.execute("""
                SELECT monthly_quota, used_this_month, quota_reset_at
                FROM tenants WHERE id = %s LIMIT 1
            """, (str(tenant_id),))
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
            cur.execute("""
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
            """, (n, n, str(tenant_id)))
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
            cur.execute("""
                SELECT id, username, email, role, is_active, is_super_admin,
                       last_login_at, created_at, invited_by
                FROM users
                WHERE tenant_id = %s
                ORDER BY
                    CASE WHEN role = 'owner' THEN 0 ELSE 1 END,
                    created_at ASC
            """, (str(tenant_id),))
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
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users WHERE tenant_id = %s) AS user_count,
                    (SELECT COUNT(*) FROM ocr_history oh
                      JOIN users u ON u.id = oh.user_id
                     WHERE u.tenant_id = %s
                       AND oh.created_at >= DATE_TRUNC('month', NOW())
                    ) AS ocr_this_month,
                    (SELECT MAX(last_login_at) FROM users WHERE tenant_id = %s) AS last_login
            """, (str(tenant_id), str(tenant_id), str(tenant_id)))
            stats = cur.fetchone()

        return {
            "quota": quota,
            "user_count": stats["user_count"] if stats else 0,
            "ocr_this_month": stats["ocr_this_month"] if stats else 0,
            "last_login": stats["last_login"].isoformat() if stats and stats.get("last_login") else None,
        }
    except Exception as e:
        logger.error(f"get_tenant_usage_summary failed: {e}")
        return {"quota": {"used": 0, "quota": 0, "remaining": 0, "percent": 0},
                "user_count": 0, "ocr_this_month": 0, "last_login": None}


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
            cur.execute("""
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
            """, (int(limit),))
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
            cur.execute("""
                INSERT INTO tenants (
                    name, tenant_type, monthly_quota, used_this_month,
                    status, notes, member_count
                ) VALUES (%s, %s, %s, 0, 'active', %s, 1)
                RETURNING id
            """, (company_name, tenant_type, int(monthly_quota), notes))
            tenant_id = str(cur.fetchone()["id"])

            # 2. 建老板 user
            cur.execute("""
                INSERT INTO users (
                    username, password_hash, plan, is_active, is_super_admin,
                    tenant_id, role, company_name
                ) VALUES (%s, %s, 'plus', TRUE, FALSE, %s, 'owner', %s)
                RETURNING id
            """, (username, pw_hash, tenant_id, company_name))
            user_id = str(cur.fetchone()["id"])

            # 3. 把 tenant.owner_user_id 回填
            cur.execute("UPDATE tenants SET owner_user_id = %s WHERE id = %s",
                        (user_id, tenant_id))

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
            cur.execute("""SELECT id, username, email, company_name, tenant_id, created_at
                           FROM users WHERE id = %s AND (role = 'owner' OR role IS NULL) LIMIT 1""", (str(user_id),))
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
                    ("employees", "SELECT COUNT(*) AS n FROM users WHERE tenant_id = %s AND role = 'member'", (tenant_id,)),
                    ("ocr_records", "SELECT COUNT(*) AS n FROM ocr_history WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)", (tenant_id,)),
                    ("clients", "SELECT COUNT(*) AS n FROM clients WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)", (tenant_id,)),
                    ("erp_endpoints", "SELECT COUNT(*) AS n FROM erp_endpoints WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)", (tenant_id,)),
                    ("erp_push_logs", "SELECT COUNT(*) AS n FROM erp_push_logs WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)", (tenant_id,)),
                    ("email_accounts", "SELECT COUNT(*) AS n FROM email_ingest_accounts WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)", (tenant_id,)),
                    ("bank_recon_sessions", "SELECT COUNT(*) AS n FROM bank_reconcile_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)", (tenant_id,)),
                ]
            else:
                # 孤立用户 · 只数自己的数据 · 没有 employees(没有 tenant)
                uid_p = (str(user_id),)
                queries = [
                    ("employees", None, None),  # 跳过 · 反正是 0
                    ("ocr_records", "SELECT COUNT(*) AS n FROM ocr_history WHERE user_id = %s", uid_p),
                    ("clients", "SELECT COUNT(*) AS n FROM clients WHERE user_id = %s", uid_p),
                    ("erp_endpoints", "SELECT COUNT(*) AS n FROM erp_endpoints WHERE user_id = %s", uid_p),
                    ("erp_push_logs", "SELECT COUNT(*) AS n FROM erp_push_logs WHERE user_id = %s", uid_p),
                    ("email_accounts", "SELECT COUNT(*) AS n FROM email_ingest_accounts WHERE user_id = %s", uid_p),
                    ("bank_recon_sessions", "SELECT COUNT(*) AS n FROM bank_reconcile_sessions WHERE user_id = %s", uid_p),
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
                    "created_at": owner["created_at"].isoformat() if owner.get("created_at") else None,
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
            cur.execute("SELECT tenant_id, username FROM users WHERE id = %s AND (role = 'owner' OR role IS NULL) LIMIT 1",
                        (str(user_id),))
            row = cur.fetchone()
            if not row:
                logger.warning(f"delete_owner_user_cascade: user {user_id} 不是 owner 或不存在")
                return False
            tenant_id = str(row["tenant_id"]) if row.get("tenant_id") else None
            target_username = row.get("username")
            logger.info(f"[cascade-delete] 开始删除 owner={target_username} tenant_id={tenant_id or '(orphan)'}")

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
                        pass
                    logger.warning(f"[cascade-delete] {label} · 跳过(savepoint 已回滚): {str(e)[:200]}")
                    return False

            if tenant_id:
                # ========== 完整路径(有 tenant)· 按 tenant 维度级联 ==========
                tables = [
                    ("ocr_history", "DELETE FROM ocr_history WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("ocr_cost_log", "DELETE FROM ocr_cost_log WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("erp_push_logs", "DELETE FROM erp_push_logs WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("erp_endpoints", "DELETE FROM erp_endpoints WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("clients", "DELETE FROM clients WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("archive_settings", "DELETE FROM archive_settings WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("rd_daily_usage", "DELETE FROM rd_daily_usage WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("email_ingest_seen_uids", "DELETE FROM email_ingest_seen_uids WHERE account_id IN (SELECT id FROM email_ingest_accounts WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s))"),
                    ("email_ingest_logs", "DELETE FROM email_ingest_logs WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("email_ingest_accounts", "DELETE FROM email_ingest_accounts WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("bank_reconcile_candidates", "DELETE FROM bank_reconcile_candidates WHERE session_id IN (SELECT id FROM bank_reconcile_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s))"),
                    ("bank_reconcile_transactions", "DELETE FROM bank_reconcile_transactions WHERE session_id IN (SELECT id FROM bank_reconcile_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s))"),
                    ("bank_reconcile_sessions", "DELETE FROM bank_reconcile_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("line_bindings", "DELETE FROM line_bindings WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("line_binding_codes", "DELETE FROM line_binding_codes WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("user_settings", "DELETE FROM user_settings WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("api_keys", "DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("automation_rules", "DELETE FROM automation_rules WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                    ("excel_templates", "DELETE FROM excel_templates WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)"),
                ]
                for label, sql in tables:
                    _safe_delete(sql, (tenant_id,), label)

                # 关键步骤
                _safe_delete("DELETE FROM users WHERE tenant_id = %s", (tenant_id,), "users")
                _safe_delete("DELETE FROM operation_logs WHERE tenant_id = %s", (tenant_id,), "operation_logs")
                ok_tenant = _safe_delete("DELETE FROM tenants WHERE id = %s", (tenant_id,), "tenants")
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
                    ("email_ingest_seen_uids", "DELETE FROM email_ingest_seen_uids WHERE account_id IN (SELECT id FROM email_ingest_accounts WHERE user_id = %s)"),
                    ("email_ingest_logs", "DELETE FROM email_ingest_logs WHERE user_id = %s"),
                    ("email_ingest_accounts", "DELETE FROM email_ingest_accounts WHERE user_id = %s"),
                    ("bank_reconcile_candidates", "DELETE FROM bank_reconcile_candidates WHERE session_id IN (SELECT id FROM bank_reconcile_sessions WHERE user_id = %s)"),
                    ("bank_reconcile_transactions", "DELETE FROM bank_reconcile_transactions WHERE session_id IN (SELECT id FROM bank_reconcile_sessions WHERE user_id = %s)"),
                    ("bank_reconcile_sessions", "DELETE FROM bank_reconcile_sessions WHERE user_id = %s"),
                    ("line_bindings", "DELETE FROM line_bindings WHERE user_id = %s"),
                    ("line_binding_codes", "DELETE FROM line_binding_codes WHERE user_id = %s"),
                    ("user_settings", "DELETE FROM user_settings WHERE user_id = %s"),
                    ("api_keys", "DELETE FROM api_keys WHERE user_id = %s"),
                    ("automation_rules", "DELETE FROM automation_rules WHERE user_id = %s"),
                    ("excel_templates", "DELETE FROM excel_templates WHERE user_id = %s"),
                ]
                for label, sql in tables:
                    _safe_delete(sql, (str(user_id),), label)
                ok_user = _safe_delete("DELETE FROM users WHERE id = %s", (str(user_id),), "users-orphan")
                logger.info(f"[cascade-delete] ✅ 完成 orphan owner={target_username}")
                return ok_user
    except Exception as e:
        logger.error(f"delete_owner_user_cascade failed (user_id={user_id}): {e}\n{traceback.format_exc()}")
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
                (pw_hash, str(user_id))
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"reset_user_password failed: {e}")
        return False


def insert_operation_log(
    tenant_id: Optional[str],
    actor_user_id: Optional[str],
    actor_username: Optional[str],
    actor_is_super: bool,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    target_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
    ua: Optional[str] = None,
) -> bool:
    """记一条操作日志 · 失败不阻塞主流程"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO operation_logs (
                    tenant_id, actor_user_id, actor_username, actor_is_super,
                    action, target_type, target_id, target_name, details, ip, ua
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            """, (
                str(tenant_id) if tenant_id else None,
                str(actor_user_id) if actor_user_id else None,
                actor_username, bool(actor_is_super),
                action, target_type, str(target_id) if target_id else None, target_name,
                _json.dumps(details or {}, ensure_ascii=False),
                ip, (ua or "")[:300],
            ))
            return True
    except Exception as e:
        logger.warning(f"insert_operation_log failed (action={action}): {e}")
        return False


def list_operation_logs(
    tenant_id: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    查操作日志
    - tenant_id 传则过滤该租户 · 不传则全局(仅超管用全局)
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT * FROM operation_logs
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (str(tenant_id), int(limit)))
            else:
                cur.execute("""
                    SELECT * FROM operation_logs
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (int(limit),))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_operation_logs failed: {e}")
        return []


# v118.29.0 · 操作日志分页 + 搜索 + 时间过滤
def list_operation_logs_paged(
    tenant_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    q: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit_all: int = 0,  # >0 时返回全部(给 CSV 导出用 · 不分页)
    actor_is_super: Optional[bool] = None,  # v118.28.8 · 给客户老板看 Pearnly 访问日志用
) -> Dict[str, Any]:
    page = max(1, int(page or 1))
    per_page = max(1, min(500, int(per_page or 50)))
    offset = (page - 1) * per_page

    where = []
    params: List[Any] = []
    if tenant_id:
        where.append("tenant_id = %s"); params.append(str(tenant_id))
    if q:
        where.append("(LOWER(COALESCE(actor_username, '')) LIKE %s OR LOWER(COALESCE(action, '')) LIKE %s OR LOWER(COALESCE(target_name, '')) LIKE %s)")
        like = f"%{q.lower()}%"
        params += [like, like, like]
    if action:
        where.append("action = %s"); params.append(action)
    if date_from:
        where.append("created_at >= %s"); params.append(date_from)
    if date_to:
        where.append("created_at <= %s"); params.append(date_to)
    if actor_is_super is True:
        where.append("COALESCE(actor_is_super, false) = true")
    elif actor_is_super is False:
        where.append("COALESCE(actor_is_super, false) = false")
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    try:
        with get_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS c FROM operation_logs{where_sql}", params)
            total_row = cur.fetchone()
            total = int((total_row.get("c") if isinstance(total_row, dict) else total_row[0]) or 0)

            if limit_all and limit_all > 0:
                cur.execute(
                    f"SELECT * FROM operation_logs{where_sql} ORDER BY created_at DESC LIMIT %s",
                    params + [int(limit_all)]
                )
            else:
                cur.execute(
                    f"SELECT * FROM operation_logs{where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    params + [per_page, offset]
                )
            rows = [dict(r) for r in cur.fetchall()]
        return {"rows": rows, "total": total, "page": page, "per_page": per_page}
    except Exception as e:
        logger.error(f"list_operation_logs_paged failed: {e}")
        return {"rows": [], "total": 0, "page": page, "per_page": per_page}


# ============================================================
# 员工管理(老板自助)
# ============================================================
def list_employees(tenant_id: str) -> List[Dict[str, Any]]:
    """列某 tenant 下的员工(role=member)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, username, role, is_active, last_login_at, created_at, invited_by
                FROM users
                WHERE tenant_id = %s AND role = 'member'
                ORDER BY created_at ASC
            """, (str(tenant_id),))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_employees failed: {e}")
        return []


def add_employee(
    tenant_id: str,
    username: str,
    password: str,
    invited_by: Optional[str] = None,
) -> Optional[str]:
    """
    老板给自家公司加员工
    - 用户名全局唯一
    - tenant_id 必填
    - role 固定 = 'member'
    返回新员工 user_id · 失败返回 None
    """
    try:
        existing = find_user_by_username(username)
        if existing:
            return None

        pw_hash = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

        # 取 tenant 的 company_name
        with get_cursor(commit=True) as cur:
            cur.execute("SELECT name FROM tenants WHERE id = %s", (str(tenant_id),))
            row = cur.fetchone()
            company_name = row["name"] if row else None

            cur.execute("""
                INSERT INTO users (
                    username, password_hash, plan, is_active, is_super_admin,
                    tenant_id, role, invited_by, company_name
                ) VALUES (%s, %s, 'plus', TRUE, FALSE, %s, 'member', %s, %s)
                RETURNING id
            """, (username, pw_hash, str(tenant_id),
                  str(invited_by) if invited_by else None, company_name))
            return str(cur.fetchone()["id"])
    except Exception as e:
        logger.error(f"add_employee failed: {e}")
        return None


def remove_employee(tenant_id: str, employee_user_id: str) -> bool:
    """
    老板删员工
    安全校验:只删 tenant_id 匹配 + role=member 的 user
    """
    try:
        with get_cursor(commit=True) as cur:
            # 先看员工是否存在且属于该 tenant
            cur.execute("""
                SELECT id FROM users
                WHERE id = %s AND tenant_id = %s AND role = 'member'
                LIMIT 1
            """, (str(employee_user_id), str(tenant_id)))
            if not cur.fetchone():
                return False

            # 级联删员工相关数据
            for sql in [
                "DELETE FROM ocr_history WHERE user_id = %s",
                "DELETE FROM erp_push_logs WHERE user_id = %s",
                "DELETE FROM line_bindings WHERE user_id = %s",
                "DELETE FROM line_binding_codes WHERE user_id = %s",
                "DELETE FROM user_settings WHERE user_id = %s",
            ]:
                try:
                    cur.execute(sql, (str(employee_user_id),))
                except Exception:
                    pass

            cur.execute("DELETE FROM users WHERE id = %s", (str(employee_user_id),))
            return True
    except Exception as e:
        logger.error(f"remove_employee failed: {e}")
        return False


def toggle_employee_active(
    tenant_id: str,
    employee_user_id: str,
    is_active: bool,
) -> bool:
    """老板启用/停用员工"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE users SET is_active = %s
                WHERE id = %s AND tenant_id = %s AND role = 'member'
            """, (bool(is_active), str(employee_user_id), str(tenant_id)))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"toggle_employee_active failed: {e}")
        return False


# ============================================================
# v106 · 成本追踪 ocr_cost_log 表
# 每次识别完成后写入一条 · 用于管理员成本面板
# ============================================================

def ensure_ocr_cost_log_table():
    """启动时建表 · 幂等 · v108.2 修 history_id 类型 BIGINT → TEXT(ocr_history.id 是 UUID)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ocr_cost_log (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    history_id TEXT,
                    engine TEXT NOT NULL DEFAULT 'gemini',
                    pages INTEGER NOT NULL DEFAULT 1,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cost_thb NUMERIC(10, 4) NOT NULL DEFAULT 0,
                    elapsed_ms INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_cost_log_user ON ocr_cost_log(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_cost_log_created ON ocr_cost_log(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_cost_log_tenant ON ocr_cost_log(tenant_id, created_at DESC);
            """)
            # v108.2 · 已建表的迁移:把 history_id 从 BIGINT 改 TEXT
            try:
                cur.execute("""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'ocr_cost_log'
                              AND column_name = 'history_id'
                              AND data_type = 'bigint'
                        ) THEN
                            ALTER TABLE ocr_cost_log ALTER COLUMN history_id TYPE TEXT USING history_id::TEXT;
                        END IF;
                    END $$;
                """)
            except Exception as _me:
                logger.warning(f"ocr_cost_log.history_id 类型迁移失败(不致命): {_me}")
            logger.info("✅ ocr_cost_log 表已就绪")
    except Exception as e:
        logger.error(f"ensure_ocr_cost_log_table failed: {e}")


def log_ocr_cost(
    user_id: str,
    tenant_id: Optional[str],
    history_id: Optional[Any],   # v108.2 · 接受 str/UUID/int 都可
    engine: str,
    pages: int,
    input_tokens: int,
    output_tokens: int,
    cost_thb: float,
    elapsed_ms: int,
) -> bool:
    """每次识别完写一条成本记录"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO ocr_cost_log
                (user_id, tenant_id, history_id, engine, pages,
                 input_tokens, output_tokens, cost_thb, elapsed_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(user_id), str(tenant_id) if tenant_id else None,
                str(history_id) if history_id is not None else None,   # v108.2 · 强制转 str
                engine, pages,
                input_tokens, output_tokens, round(float(cost_thb), 4), elapsed_ms,
            ))
            new_id = cur.fetchone()["id"]
            logger.info(f"  ✅ ocr_cost_log 写入 id={new_id} user={user_id[:8]} engine={engine} cost=฿{cost_thb:.4f}")
        return True
    except Exception as e:
        import traceback
        logger.error(f"  ❌ log_ocr_cost FAILED: {e}\n{traceback.format_exc()}")
        return False


def get_cost_overview() -> Dict[str, Any]:
    """成本面板 · 顶部 KPI · 今日 / 本月 / 总计"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN created_at::date = CURRENT_DATE THEN cost_thb END), 0) AS today_cost,
                    COALESCE(SUM(CASE WHEN created_at::date = CURRENT_DATE THEN pages END), 0) AS today_pages,
                    COALESCE(COUNT(CASE WHEN created_at::date = CURRENT_DATE THEN 1 END), 0) AS today_invoices,
                    COALESCE(SUM(CASE WHEN date_trunc('month', created_at) = date_trunc('month', NOW()) THEN cost_thb END), 0) AS month_cost,
                    COALESCE(SUM(CASE WHEN date_trunc('month', created_at) = date_trunc('month', NOW()) THEN pages END), 0) AS month_pages,
                    COALESCE(COUNT(CASE WHEN date_trunc('month', created_at) = date_trunc('month', NOW()) THEN 1 END), 0) AS month_invoices,
                    COALESCE(SUM(cost_thb), 0) AS total_cost,
                    COALESCE(SUM(pages), 0) AS total_pages,
                    COALESCE(COUNT(*), 0) AS total_invoices
                FROM ocr_cost_log
            """)
            row = cur.fetchone() or {}
            # 引擎占比
            cur.execute("""
                SELECT engine, COUNT(*) AS cnt, COALESCE(SUM(cost_thb), 0) AS cost
                FROM ocr_cost_log
                WHERE date_trunc('month', created_at) = date_trunc('month', NOW())
                GROUP BY engine
            """)
            engines = [dict(r) for r in cur.fetchall()]
            return {
                "today": {
                    "cost_thb": float(row.get("today_cost") or 0),
                    "pages": int(row.get("today_pages") or 0),
                    "invoices": int(row.get("today_invoices") or 0),
                },
                "month": {
                    "cost_thb": float(row.get("month_cost") or 0),
                    "pages": int(row.get("month_pages") or 0),
                    "invoices": int(row.get("month_invoices") or 0),
                },
                "total": {
                    "cost_thb": float(row.get("total_cost") or 0),
                    "pages": int(row.get("total_pages") or 0),
                    "invoices": int(row.get("total_invoices") or 0),
                },
                "engines": [
                    {"engine": e["engine"], "count": int(e["cnt"]), "cost_thb": float(e["cost"])}
                    for e in engines
                ],
            }
    except Exception as e:
        logger.error(f"get_cost_overview failed: {e}")
        return {"today": {}, "month": {}, "total": {}, "engines": []}


def get_cost_by_user(limit: int = 50) -> List[Dict[str, Any]]:
    """按用户分组 · 找烧钱多的"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    c.user_id,
                    u.username,
                    u.plan,
                    COALESCE(SUM(CASE WHEN c.created_at::date = CURRENT_DATE THEN c.cost_thb END), 0) AS today_cost,
                    COALESCE(SUM(CASE WHEN date_trunc('month', c.created_at) = date_trunc('month', NOW()) THEN c.cost_thb END), 0) AS month_cost,
                    COALESCE(SUM(c.cost_thb), 0) AS total_cost,
                    COALESCE(SUM(c.pages), 0) AS total_pages,
                    COUNT(*) AS total_invoices,
                    MAX(c.created_at) AS last_used_at
                FROM ocr_cost_log c
                LEFT JOIN users u ON u.id = c.user_id
                GROUP BY c.user_id, u.username, u.plan
                ORDER BY month_cost DESC, total_cost DESC
                LIMIT %s
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"get_cost_by_user failed: {e}")
        return []


def get_cost_daily_trend(days: int = 30) -> List[Dict[str, Any]]:
    """每天趋势 · 最近 N 天"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    created_at::date AS day,
                    COALESCE(SUM(cost_thb), 0) AS cost,
                    COALESCE(SUM(pages), 0) AS pages,
                    COUNT(*) AS invoices
                FROM ocr_cost_log
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY day
                ORDER BY day ASC
            """ % int(days))
            return [
                {
                    "day": str(r["day"]),
                    "cost_thb": float(r["cost"] or 0),
                    "pages": int(r["pages"] or 0),
                    "invoices": int(r["invoices"] or 0),
                }
                for r in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"get_cost_daily_trend failed: {e}")
        return []


# ============================================================
# v107 · 客户(Client)实体 · 多客户事务所核心功能
# 会计 / 事务所给多家公司做账时 · 把每张发票归属到客户
# ============================================================

def ensure_clients_table():
    """启动时建客户表 · 加 client_id 列到 ocr_history · 幂等"""
    try:
        with get_cursor(commit=True) as cur:
            # 1. 客户表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    name TEXT NOT NULL,
                    short_name TEXT,
                    tax_id TEXT,
                    address TEXT,
                    contact_person TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    notes TEXT,
                    color TEXT DEFAULT '#3b82f6',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_clients_user ON clients(user_id, is_active);
                CREATE INDEX IF NOT EXISTS idx_clients_tenant ON clients(tenant_id, is_active);
                CREATE INDEX IF NOT EXISTS idx_clients_tax_id ON clients(tax_id) WHERE tax_id IS NOT NULL;
            """)
            # 2. ocr_history 加 client_id 字段
            cur.execute("""
                ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS client_id BIGINT;
                CREATE INDEX IF NOT EXISTS idx_ocr_history_client ON ocr_history(client_id) WHERE client_id IS NOT NULL;
            """)
            logger.info("✅ clients 表 + ocr_history.client_id 已就绪")
    except Exception as e:
        logger.error(f"ensure_clients_table failed: {e}")


# ============================================================
# v118.18 · 推荐分类「学习」表 · 用户给某供应商打了分类后系统记忆 · 下次自动建议
# 唯一性:同 tenant(或孤立用户)下 · 同 seller_name 只有 1 条
# ============================================================

def ensure_supplier_categories_table():
    """启动时建表 · 幂等"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS supplier_categories (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id UUID,
                    user_id UUID NOT NULL,
                    seller_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    use_count INTEGER NOT NULL DEFAULT 1,
                    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_supcat_unique
                    ON supplier_categories (COALESCE(tenant_id::text, user_id::text), LOWER(seller_name));
                CREATE INDEX IF NOT EXISTS idx_supcat_tenant ON supplier_categories(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_supcat_user ON supplier_categories(user_id);
            """)
            logger.info("✅ supplier_categories 表已就绪")
    except Exception as e:
        logger.error(f"ensure_supplier_categories_table failed: {e}")


def get_category_for_seller(seller_name: Optional[str], user_id: str, tenant_id: Optional[str] = None) -> Optional[str]:
    """识别时调:查同 seller 之前用过的 category(同 tenant 共享 · 否则查自己)"""
    if not seller_name or not seller_name.strip():
        return None
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT category FROM supplier_categories
                    WHERE tenant_id = %s AND LOWER(seller_name) = LOWER(%s)
                    ORDER BY last_used_at DESC LIMIT 1
                """, (tenant_id, seller_name.strip()))
            else:
                cur.execute("""
                    SELECT category FROM supplier_categories
                    WHERE user_id = %s AND tenant_id IS NULL AND LOWER(seller_name) = LOWER(%s)
                    ORDER BY last_used_at DESC LIMIT 1
                """, (str(user_id), seller_name.strip()))
            r = cur.fetchone()
            return r["category"] if r else None
    except Exception as e:
        logger.warning(f"get_category_for_seller failed: {e}")
        return None


def upsert_supplier_category(seller_name: Optional[str], category: Optional[str],
                             user_id: str, tenant_id: Optional[str] = None) -> bool:
    """保存编辑时调:记忆这个映射 · 已存在则更新 use_count 和 category"""
    if not seller_name or not seller_name.strip():
        return False
    if not category or not category.strip():
        return False
    s = seller_name.strip()[:200]
    c = category.strip()[:80]
    try:
        with get_cursor(commit=True) as cur:
            # 用 ON CONFLICT 利用 unique index
            if tenant_id:
                cur.execute("""
                    INSERT INTO supplier_categories (tenant_id, user_id, seller_name, category)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (COALESCE(tenant_id::text, user_id::text), LOWER(seller_name))
                    DO UPDATE SET category = EXCLUDED.category,
                                  use_count = supplier_categories.use_count + 1,
                                  last_used_at = NOW()
                """, (tenant_id, str(user_id), s, c))
            else:
                cur.execute("""
                    INSERT INTO supplier_categories (tenant_id, user_id, seller_name, category)
                    VALUES (NULL, %s, %s, %s)
                    ON CONFLICT (COALESCE(tenant_id::text, user_id::text), LOWER(seller_name))
                    DO UPDATE SET category = EXCLUDED.category,
                                  use_count = supplier_categories.use_count + 1,
                                  last_used_at = NOW()
                """, (str(user_id), s, c))
            return True
    except Exception as e:
        logger.warning(f"upsert_supplier_category failed: {e}")
        return False


def list_used_categories(user_id: str, tenant_id: Optional[str] = None, limit: int = 30) -> List[str]:
    """列出用户/tenant 用过的所有 category(去重 · 按使用次数倒序)· 给前端 datalist 自动补全"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT category, SUM(use_count) AS total FROM supplier_categories
                    WHERE tenant_id = %s
                    GROUP BY category ORDER BY total DESC LIMIT %s
                """, (tenant_id, limit))
            else:
                cur.execute("""
                    SELECT category, SUM(use_count) AS total FROM supplier_categories
                    WHERE user_id = %s AND tenant_id IS NULL
                    GROUP BY category ORDER BY total DESC LIMIT %s
                """, (str(user_id), limit))
            return [r["category"] for r in cur.fetchall()]
    except Exception as e:
        logger.warning(f"list_used_categories failed: {e}")
        return []


def count_supplier_mappings(user_id: str, tenant_id: Optional[str] = None) -> int:
    """统计已记忆的供应商→科目映射数量(给前端 '已记住 N 个供应商' 提示)"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("SELECT COUNT(*) AS n FROM supplier_categories WHERE tenant_id = %s", (tenant_id,))
            else:
                cur.execute("SELECT COUNT(*) AS n FROM supplier_categories WHERE user_id = %s AND tenant_id IS NULL", (str(user_id),))
            r = cur.fetchone()
            return int(r["n"]) if r else 0
    except Exception as e:
        return 0


def list_clients(user_id: str, include_inactive: bool = False, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出某用户的所有客户(按名字排序)
    v118.15 · tenant_id 给了 → 同 tenant 共享(老板员工看到同一份客户档案)
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                where = "user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
                params = [tenant_id]
            else:
                where = "user_id = %s"
                params = [user_id]
            if not include_inactive:
                where += " AND is_active = TRUE"
            cur.execute(f"""
                SELECT c.*,
                    (SELECT COUNT(*) FROM ocr_history WHERE client_id = c.id) AS invoice_count,
                    (SELECT COALESCE(SUM(total_amount), 0) FROM ocr_history 
                     WHERE client_id = c.id AND total_amount IS NOT NULL) AS total_amount,
                    (SELECT MAX(created_at) FROM ocr_history WHERE client_id = c.id) AS last_invoice_at
                FROM clients c
                WHERE {where}
                ORDER BY c.is_active DESC, c.name ASC
            """, params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_clients failed: {e}")
        return []


def get_client(user_id: str, client_id: int, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """获取单个客户
    v118.15 · tenant_id 给了 → 同 tenant 任意成员可查
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT * FROM clients WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                """, (client_id, tenant_id))
            else:
                cur.execute("""
                    SELECT * FROM clients WHERE id = %s AND user_id = %s
                """, (client_id, user_id))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_client failed: {e}")
        return None


def create_client(user_id: str, tenant_id: Optional[str], name: str, **kwargs) -> Optional[int]:
    """创建客户 · 返回新 ID"""
    if not name or not name.strip():
        return None
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO clients (user_id, tenant_id, name, short_name, tax_id, 
                    address, contact_person, contact_phone, contact_email, notes, color)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id,
                tenant_id,
                name.strip()[:200],
                (kwargs.get("short_name") or "").strip()[:80] or None,
                (kwargs.get("tax_id") or "").strip()[:20] or None,
                (kwargs.get("address") or "").strip()[:500] or None,
                (kwargs.get("contact_person") or "").strip()[:100] or None,
                (kwargs.get("contact_phone") or "").strip()[:50] or None,
                (kwargs.get("contact_email") or "").strip()[:200] or None,
                (kwargs.get("notes") or "").strip()[:1000] or None,
                kwargs.get("color") or "#3b82f6",
            ))
            return cur.fetchone()["id"]
    except Exception as e:
        import traceback
        logger.error(f"create_client failed: {e}\n{traceback.format_exc()}")
        return None


def update_client(user_id: str, client_id: int, tenant_id: Optional[str] = None, **kwargs) -> bool:
    """更新客户信息 · 部分字段更新
    v118.15 · tenant_id 给了 → 同 tenant 任意成员可改
    """
    allowed_fields = ["name", "short_name", "tax_id", "address",
                      "contact_person", "contact_phone", "contact_email",
                      "notes", "color", "is_active"]
    updates = []
    params = []
    for k in allowed_fields:
        if k in kwargs and kwargs[k] is not None:
            updates.append(f"{k} = %s")
            v = kwargs[k]
            if isinstance(v, str):
                v = v.strip()
                # 字段长度限制
                limits = {"name": 200, "short_name": 80, "tax_id": 20,
                          "address": 500, "contact_person": 100,
                          "contact_phone": 50, "contact_email": 200,
                          "notes": 1000, "color": 20}
                if k in limits:
                    v = v[:limits[k]] or None
            params.append(v)
    if not updates:
        return False
    updates.append("updated_at = NOW()")
    if tenant_id:
        where_sql = "id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
        params.extend([client_id, tenant_id])
    else:
        where_sql = "id = %s AND user_id = %s"
        params.extend([client_id, user_id])
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(f"""
                UPDATE clients SET {', '.join(updates)}
                WHERE {where_sql}
            """, params)
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_client failed: {e}")
        return False


def delete_client(user_id: str, client_id: int, cascade_unlink: bool = True, tenant_id: Optional[str] = None) -> bool:
    """删除客户 · 默认级联解绑发票(把发票的 client_id 置 NULL · 不删发票)
    v118.15 · tenant_id 给了 → 同 tenant 任意成员可删
    """
    try:
        with get_cursor(commit=True) as cur:
            # 先解绑发票
            if cascade_unlink:
                cur.execute("""
                    UPDATE ocr_history SET client_id = NULL
                    WHERE client_id = %s
                """, (client_id,))
            # 再删客户
            if tenant_id:
                cur.execute("""
                    DELETE FROM clients WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                """, (client_id, tenant_id))
            else:
                cur.execute("""
                    DELETE FROM clients WHERE id = %s AND user_id = %s
                """, (client_id, user_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_client failed: {e}")
        return False


def assign_invoice_to_client(user_id: str, history_id: str, client_id: Optional[int], tenant_id: Optional[str] = None) -> bool:
    """把发票归属到客户(client_id=None 表示移除归属)
    v108.2 · history_id 是 UUID 字符串(ocr_history 主键是 UUID)
    v118.15 · tenant_id 给了 → 同 tenant 任意成员可标 · 客户和发票都按 tenant 过滤
    """
    try:
        with get_cursor(commit=True) as cur:
            # 验证客户属于该用户/tenant(防越权)
            if client_id is not None:
                if tenant_id:
                    cur.execute("SELECT id FROM clients WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                               (client_id, tenant_id))
                else:
                    cur.execute("SELECT id FROM clients WHERE id = %s AND user_id = %s",
                               (client_id, user_id))
                if not cur.fetchone():
                    return False
            # 更新发票归属(同样按 tenant 过滤)
            if tenant_id:
                cur.execute("""
                    UPDATE ocr_history SET client_id = %s
                    WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                """, (client_id, str(history_id), tenant_id))
            else:
                cur.execute("""
                    UPDATE ocr_history SET client_id = %s
                    WHERE id = %s AND user_id = %s
                """, (client_id, str(history_id), str(user_id)))
            return cur.rowcount > 0
    except Exception as e:
        import traceback
        logger.error(f"assign_invoice_to_client failed: {e}\n{traceback.format_exc()}")
        return False


# ============================================================
# v108 · Google AI Studio 余额追踪 · 半自动校准
# 管理员每周更新一次真实余额 · 系统自动反推校准系数
# ============================================================

def ensure_billing_balance_table():
    """启动时建余额追踪表 · 幂等"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS billing_balance_log (
                    id BIGSERIAL PRIMARY KEY,
                    real_balance_thb NUMERIC(12, 4) NOT NULL,
                    notes TEXT,
                    estimated_used_since_last NUMERIC(12, 4) DEFAULT 0,
                    real_used_since_last NUMERIC(12, 4) DEFAULT 0,
                    calibration_factor NUMERIC(6, 4) DEFAULT 1.0,
                    updated_by_user_id UUID,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_billing_log_created ON billing_balance_log(created_at DESC);
            """)
            logger.info("✅ billing_balance_log 表已就绪")
    except Exception as e:
        logger.error(f"ensure_billing_balance_table failed: {e}")


def get_latest_balance() -> Optional[Dict[str, Any]]:
    """拿最新一条余额记录"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT * FROM billing_balance_log
                ORDER BY created_at DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_latest_balance failed: {e}")
        return None


def add_balance_log(real_balance: float, user_id: str, notes: Optional[str] = None, calibration_override: Optional[float] = None) -> Optional[int]:
    """添加一条余额记录 · 自动算估算消耗 + 校准系数
    calibration_override: 不为 None 时跳过自动计算，直接使用该值（管理员手动覆盖）
    返回新记录 ID
    """
    try:
        with get_cursor(commit=True) as cur:
            # 1. 拿上一条记录 + 上次时间
            cur.execute("""
                SELECT real_balance_thb, created_at FROM billing_balance_log
                ORDER BY created_at DESC LIMIT 1
            """)
            prev = cur.fetchone()

            estimated_used = 0.0
            real_used = 0.0
            calibration = 1.0

            if calibration_override is not None:
                # 管理员手动覆盖 · 仍然统计消耗数据用于记录
                calibration = round(max(0.5, min(float(calibration_override), 2.0)), 4)
                if prev:
                    real_used = float(prev["real_balance_thb"]) - float(real_balance)
                    cur.execute("""
                        SELECT COALESCE(SUM(cost_thb), 0) AS estimated FROM ocr_cost_log
                        WHERE created_at > %s
                    """, (prev["created_at"],))
                    est_row = cur.fetchone()
                    estimated_used = float(est_row["estimated"]) if est_row else 0.0
            elif prev:
                # 算这段时间真实消耗
                real_used = float(prev["real_balance_thb"]) - float(real_balance)
                # 算这段时间我们估算的消耗
                cur.execute("""
                    SELECT COALESCE(SUM(cost_thb), 0) AS estimated FROM ocr_cost_log
                    WHERE created_at > %s
                """, (prev["created_at"],))
                est_row = cur.fetchone()
                estimated_used = float(est_row["estimated"]) if est_row else 0.0
                # 反推校准系数(防 0 除)
                if estimated_used > 0.001 and real_used > 0:
                    calibration = round(real_used / estimated_used, 4)
                    # 限制范围 · 避免异常数据(如手抖输错)
                    calibration = max(0.5, min(calibration, 2.0))
            
            # 2. 写新记录
            cur.execute("""
                INSERT INTO billing_balance_log
                (real_balance_thb, notes, estimated_used_since_last,
                 real_used_since_last, calibration_factor, updated_by_user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                round(real_balance, 4),
                (notes or "")[:500] or None,
                round(estimated_used, 4),
                round(real_used, 4),
                calibration,
                user_id,
            ))
            return cur.fetchone()["id"]
    except Exception as e:
        import traceback
        logger.error(f"add_balance_log failed: {e}\n{traceback.format_exc()}")
        return None


def get_balance_summary() -> Dict[str, Any]:
    """成本面板用 · 拿余额 + 估算 vs 真实对比 + 当前校准系数"""
    try:
        latest = get_latest_balance()
        if not latest:
            return {
                "has_balance": False,
                "real_balance_thb": None,
                "last_updated_at": None,
                "calibration_factor": 1.0,
                "estimated_since_last": 0,
                "real_since_last": 0,
                "accuracy_pct": None,
            }
            
            
            
        # 算自上次更新以来 · 我们当前估算了多少
        with get_cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(cost_thb), 0) AS estimated_since FROM ocr_cost_log
                WHERE created_at > %s
            """, (latest["created_at"],))
            est_since = float(cur.fetchone()["estimated_since"] or 0)
        
        # 当前预估实际余额
        current_estimated_balance = float(latest["real_balance_thb"]) - est_since
        
        # 准确度(上次)
        accuracy = None
        if latest.get("estimated_used_since_last") and float(latest["estimated_used_since_last"]) > 0.001:
            real = float(latest.get("real_used_since_last") or 0)
            est = float(latest["estimated_used_since_last"])
            if real > 0:
                accuracy = round(min(est, real) / max(est, real) * 100, 1)
        
        return {
            "has_balance": True,
            "real_balance_thb": float(latest["real_balance_thb"]),
            "current_estimated_balance_thb": round(current_estimated_balance, 4),
            "last_updated_at": latest["created_at"].isoformat(),
            "calibration_factor": float(latest.get("calibration_factor") or 1.0),
            "estimated_since_last": round(est_since, 4),
            "real_used_since_last": float(latest.get("real_used_since_last") or 0),
            "estimated_used_since_last": float(latest.get("estimated_used_since_last") or 0),
            "accuracy_pct": accuracy,
        }
    except Exception as e:
        logger.error(f"get_balance_summary failed: {e}")
        return {"has_balance": False, "error": str(e)}


# ============================================================
# v118.20.1 · 异常栏(Exceptions)数据层
#   - exceptions:每条被规则拦截的单据(关联 ocr_history)
#   - exception_whitelist:用户「忽略此类」后写入 · 同供应商+同规则下次不再拦
#   设计:同 tenant 共享视图(老板员工看同一份异常池 + 同一份白名单)
# ============================================================

def ensure_exceptions_tables():
    """启动时建异常栏 2 张表 · 幂等 + 老 schema 自动迁移
    v118.20.1.6 · 修复 history_id 应为 UUID(原写成 BIGINT 导致所有 insert 失败)
    """
    try:
        with get_cursor(commit=True) as cur:
            # ── 老 schema 修复(v118.20.1 部署过 BIGINT 版本 · 探测后 DROP 重建 · 因为 insert 全失败,无真数据)
            cur.execute("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'exceptions' AND column_name = 'history_id'
            """)
            row = cur.fetchone()
            if row and (row.get("data_type") or "").lower() == "bigint":
                logger.warning("⚠️ exceptions 表是老 BIGINT schema · DROP 重建为 UUID")
                cur.execute("DROP TABLE IF EXISTS exceptions CASCADE;")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS exceptions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    history_id UUID NOT NULL,
                    rule_code TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    seller_name TEXT,
                    invoice_no TEXT,
                    total_amount NUMERIC(18, 2),
                    detail_json JSONB,
                    status TEXT NOT NULL DEFAULT 'pending',
                    resolved_by UUID,
                    resolved_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_exc_user_status ON exceptions(user_id, status);
                CREATE INDEX IF NOT EXISTS idx_exc_tenant_status ON exceptions(tenant_id, status) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_exc_history ON exceptions(history_id);
                CREATE INDEX IF NOT EXISTS idx_exc_rule ON exceptions(rule_code);
                CREATE INDEX IF NOT EXISTS idx_exc_created ON exceptions(created_at DESC);
                -- 同一张单 + 同一类规则 · 只允许 1 条 pending(防重复拦)
                CREATE UNIQUE INDEX IF NOT EXISTS idx_exc_unique_pending
                    ON exceptions(history_id, rule_code) WHERE status = 'pending';
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exception_whitelist (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    seller_name TEXT NOT NULL,
                    rule_code TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                -- 同 tenant(或孤立用户)下 · 同 seller + 同 rule 唯一
                CREATE UNIQUE INDEX IF NOT EXISTS idx_exc_wl_unique
                    ON exception_whitelist (COALESCE(tenant_id::text, user_id::text), LOWER(seller_name), rule_code);
                CREATE INDEX IF NOT EXISTS idx_exc_wl_tenant ON exception_whitelist(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_exc_wl_user ON exception_whitelist(user_id);
            """)
            logger.info("✅ exceptions + exception_whitelist 表已就绪(history_id=UUID)")
    except Exception as e:
        logger.error(f"ensure_exceptions_tables failed: {e}")


def is_exception_whitelisted(user_id: str, tenant_id: Optional[str],
                              seller_name: Optional[str], rule_code: str) -> bool:
    """检查 (seller, rule) 是否在白名单 · 命中则跳过该规则"""
    if not seller_name or not seller_name.strip() or not rule_code:
        return False
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT 1 FROM exception_whitelist
                    WHERE tenant_id = %s AND LOWER(seller_name) = LOWER(%s) AND rule_code = %s
                    LIMIT 1
                """, (tenant_id, seller_name.strip(), rule_code))
            else:
                cur.execute("""
                    SELECT 1 FROM exception_whitelist
                    WHERE user_id = %s AND tenant_id IS NULL
                      AND LOWER(seller_name) = LOWER(%s) AND rule_code = %s
                    LIMIT 1
                """, (user_id, seller_name.strip(), rule_code))
            return cur.fetchone() is not None
    except Exception as e:
        logger.warning(f"is_exception_whitelisted failed: {e}")
        return False


def insert_exception(user_id: str, tenant_id: Optional[str], history_id: str,
                     rule_code: str, severity: str = "medium",
                     seller_name: Optional[str] = None,
                     invoice_no: Optional[str] = None,
                     total_amount: Optional[float] = None,
                     detail: Optional[Dict[str, Any]] = None) -> Optional[int]:
    """写入一条异常 · 同 history+rule 已有 pending 时直接 no-op(unique 索引保护)
    v118.20.1.6 · history_id 用 UUID 字符串(原 int 转换全失败)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO exceptions
                    (user_id, tenant_id, history_id, rule_code, severity,
                     seller_name, invoice_no, total_amount, detail_json, status)
                VALUES (%s, %s, %s::uuid, %s, %s, %s, %s, %s, %s::jsonb, 'pending')
                ON CONFLICT (history_id, rule_code) WHERE status = 'pending'
                DO NOTHING
                RETURNING id
            """, (
                str(user_id), tenant_id, str(history_id), rule_code, severity,
                seller_name, invoice_no, total_amount,
                _json.dumps(detail or {}, ensure_ascii=False, default=str),
            ))
            row = cur.fetchone()
            if row:
                ex_id = int(row["id"])
                logger.info(f"[exception] +1 ex_id={ex_id} rule={rule_code} sev={severity} hid={history_id} seller={seller_name!r}")
                return ex_id
            else:
                # ON CONFLICT 触发 · 同 history+rule 已存在 pending · 静默忽略
                return None
    except Exception as e:
        logger.warning(f"[exception] insert FAIL (rule={rule_code}, hid={history_id}): {e}")
        return None


def list_exceptions(user_id: str, tenant_id: Optional[str] = None,
                    status: str = "pending", rule_code: Optional[str] = None,
                    limit: int = 100, offset: int = 0,
                    client_id: Optional[int] = None,
                    restrict_client_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """列异常 · 同 tenant 共享视图 · 默认只看 pending
    v118.28.1 · restrict_client_ids = 员工只看分到的客户;None = 不限制
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                where = ["e.tenant_id = %s"]
                params: list = [tenant_id]
            else:
                where = ["e.user_id = %s", "e.tenant_id IS NULL"]
                params = [user_id]
            if status and status != "all":
                where.append("e.status = %s")
                params.append(status)
            if rule_code:
                where.append("e.rule_code = %s")
                params.append(rule_code)
            # v118.21.0 · 客户筛选 · client_id 来自 ocr_history(JOIN 后字段)
            if client_id:
                where.append("h.client_id = %s")
                params.append(int(client_id))
            # v118.28.1 · 员工分配过滤
            if restrict_client_ids is not None:
                if len(restrict_client_ids) == 0:
                    where.append("(e.user_id = %s AND h.client_id IS NULL)")
                    params.append(user_id)
                else:
                    where.append("(h.client_id = ANY(%s::bigint[]) OR (e.user_id = %s AND h.client_id IS NULL))")
                    params.append([int(c) for c in restrict_client_ids])
                    params.append(user_id)
            where_sql = " AND ".join(where)
            cur.execute(f"""
                SELECT e.id, e.history_id, e.rule_code, e.severity,
                       e.seller_name, e.invoice_no, e.total_amount, e.detail_json,
                       e.status, e.created_at, e.resolved_at,
                       h.filename, h.invoice_date, h.confidence, h.client_id
                FROM exceptions e
                INNER JOIN ocr_history h ON h.id = e.history_id
                WHERE {where_sql}
                ORDER BY
                  CASE e.severity WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                  e.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [int(limit), int(offset)])
            items = []
            for r in cur.fetchall():
                items.append({
                    "id": int(r["id"]),
                    "history_id": str(r["history_id"]),
                    "rule_code": r["rule_code"],
                    "severity": r["severity"],
                    "seller_name": r["seller_name"],
                    "invoice_no": r["invoice_no"],
                    "total_amount": float(r["total_amount"]) if r["total_amount"] is not None else None,
                    "detail": r["detail_json"] or {},
                    "status": r["status"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "resolved_at": r["resolved_at"].isoformat() if r["resolved_at"] else None,
                    "filename": r.get("filename"),
                    "invoice_date": r["invoice_date"].isoformat() if r.get("invoice_date") else None,
                    "confidence": r.get("confidence"),
                    "client_id": int(r["client_id"]) if r.get("client_id") else None,
                })
            return items
    except Exception as e:
        logger.error(f"list_exceptions failed: {e}")
        return []


def get_exception(user_id: str, exception_id: int, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """取单条异常详情"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT e.*, h.filename, h.invoice_date, h.confidence
                    FROM exceptions e
                    LEFT JOIN ocr_history h ON h.id = e.history_id
                    WHERE e.id = %s AND e.tenant_id = %s
                """, (int(exception_id), tenant_id))
            else:
                cur.execute("""
                    SELECT e.*, h.filename, h.invoice_date, h.confidence
                    FROM exceptions e
                    LEFT JOIN ocr_history h ON h.id = e.history_id
                    WHERE e.id = %s AND e.user_id = %s
                """, (int(exception_id), user_id))
            r = cur.fetchone()
            if not r:
                return None
            return {
                "id": int(r["id"]),
                "history_id": str(r["history_id"]),
                "rule_code": r["rule_code"],
                "severity": r["severity"],
                "seller_name": r["seller_name"],
                "invoice_no": r["invoice_no"],
                "total_amount": float(r["total_amount"]) if r["total_amount"] is not None else None,
                "detail": r["detail_json"] or {},
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "resolved_at": r["resolved_at"].isoformat() if r["resolved_at"] else None,
                "filename": r.get("filename"),
                "confidence": r.get("confidence"),
            }
    except Exception as e:
        logger.error(f"get_exception failed: {e}")
        return None


def resolve_exception(user_id: str, exception_id: int, tenant_id: Optional[str] = None,
                      new_status: str = "resolved") -> bool:
    """标记异常为已处理(resolved 或 ignored) · 同 tenant 内任意成员可处理"""
    if new_status not in ("resolved", "ignored", "pending"):
        return False
    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute("""
                    UPDATE exceptions
                    SET status = %s, resolved_by = %s, resolved_at = NOW()
                    WHERE id = %s AND tenant_id = %s
                """, (new_status, str(user_id), int(exception_id), tenant_id))
            else:
                cur.execute("""
                    UPDATE exceptions
                    SET status = %s, resolved_by = %s, resolved_at = NOW()
                    WHERE id = %s AND user_id = %s
                """, (new_status, str(user_id), int(exception_id), user_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"resolve_exception failed: {e}")
        return False


def add_exception_whitelist(user_id: str, tenant_id: Optional[str],
                             seller_name: Optional[str], rule_code: str) -> bool:
    """加入「忽略此类」白名单 · 下次同供应商同规则不再拦"""
    if not seller_name or not seller_name.strip() or not rule_code:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO exception_whitelist (user_id, tenant_id, seller_name, rule_code)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (str(user_id), tenant_id, seller_name.strip(), rule_code))
            return True
    except Exception as e:
        logger.error(f"add_exception_whitelist failed: {e}")
        return False


# v118.21.2 · 学习规则面板 · 列表 + 删除(撤销学过的白名单)
def list_exception_whitelist(user_id: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出当前 user/tenant 下所有学过的白名单规则"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT id, seller_name, rule_code, created_at
                    FROM exception_whitelist
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                """, (tenant_id,))
            else:
                cur.execute("""
                    SELECT id, seller_name, rule_code, created_at
                    FROM exception_whitelist
                    WHERE user_id = %s AND tenant_id IS NULL
                    ORDER BY created_at DESC
                """, (str(user_id),))
            items = []
            for r in cur.fetchall():
                items.append({
                    "id": int(r["id"]),
                    "seller_name": r["seller_name"],
                    "rule_code": r["rule_code"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                })
            return items
    except Exception as e:
        logger.error(f"list_exception_whitelist failed: {e}")
        return []


def delete_exception_whitelist(user_id: str, wl_id: int, tenant_id: Optional[str] = None) -> bool:
    """删除一条白名单规则 · 同 tenant 内任意成员可删"""
    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute("""
                    DELETE FROM exception_whitelist
                    WHERE id = %s AND tenant_id = %s
                """, (int(wl_id), tenant_id))
            else:
                cur.execute("""
                    DELETE FROM exception_whitelist
                    WHERE id = %s AND user_id = %s AND tenant_id IS NULL
                """, (int(wl_id), str(user_id)))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_exception_whitelist failed: {e}")
        return False


# v118.21.3 · 字段编辑后清 pending 异常 · 让 hook 重跑写入新结果
def delete_pending_exceptions_by_history(history_id: str, tenant_id: Optional[str] = None,
                                          user_id: Optional[str] = None) -> int:
    """删除某 history 下的所有 pending 异常 · 保留 resolved/ignored
    返回:删除的条数
    """
    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute("""
                    DELETE FROM exceptions
                    WHERE history_id = %s::uuid AND tenant_id = %s AND status = 'pending'
                """, (history_id, tenant_id))
            else:
                cur.execute("""
                    DELETE FROM exceptions
                    WHERE history_id = %s::uuid AND user_id = %s AND tenant_id IS NULL AND status = 'pending'
                """, (history_id, str(user_id)))
            return cur.rowcount
    except Exception as e:
        logger.error(f"delete_pending_exceptions_by_history failed: {e}")
        return 0


def count_exceptions_by_status_and_rule(user_id: str, tenant_id: Optional[str] = None,
                                          client_id: Optional[int] = None,
                                          by_rule_status: str = "pending") -> Dict[str, Any]:
    """统计 · 给前端筛选 chip 和顶部 KPI 用
    返回:{ pending: N, resolved: N, ignored: N,
           by_rule: { rule_code: count_at_by_rule_status } ,
           high_severity: N (pending 内的高危) }
    by_rule_status:控制 by_rule 字典统计哪个状态下的规则分布(默认 pending)
    """
    try:
        with get_cursor() as cur:
            if tenant_id:
                where = "e.tenant_id = %s"
                params: list = [tenant_id]
            else:
                where = "e.user_id = %s AND e.tenant_id IS NULL"
                params = [user_id]
            # v118.21.0 · 客户筛选
            if client_id:
                where = where + " AND h.client_id = %s"
                params = list(params) + [int(client_id)]
            cur.execute(f"""
                SELECT e.status, e.rule_code, e.severity, COUNT(*) AS n
                FROM exceptions e
                INNER JOIN ocr_history h ON h.id = e.history_id
                WHERE {where}
                GROUP BY e.status, e.rule_code, e.severity
            """, params)
            by_status = {"pending": 0, "resolved": 0, "ignored": 0}
            by_rule: Dict[str, int] = {}
            high = 0
            for r in cur.fetchall():
                st = r["status"]
                rc = r["rule_code"]
                sv = r["severity"]
                n = int(r["n"])
                by_status[st] = by_status.get(st, 0) + n
                # v118.21.1 · by_rule 跟随 by_rule_status(默认 pending)· high_severity 始终算 pending
                if st == by_rule_status:
                    by_rule[rc] = by_rule.get(rc, 0) + n
                if st == "pending" and sv == "high":
                    high += n
            return {
                "pending": by_status.get("pending", 0),
                "resolved": by_status.get("resolved", 0),
                "ignored": by_status.get("ignored", 0),
                "high_severity": high,
                "by_rule": by_rule,
            }
    except Exception as e:
        logger.error(f"count_exceptions_by_status_and_rule failed: {e}")
        return {"pending": 0, "resolved": 0, "ignored": 0, "high_severity": 0, "by_rule": {}}


def count_whitelist_rules(user_id: str, tenant_id: Optional[str] = None) -> int:
    """统计当前已学习的「忽略此类」规则数 · 给 KPI 卡用"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("SELECT COUNT(*) AS n FROM exception_whitelist WHERE tenant_id = %s", (tenant_id,))
            else:
                cur.execute("SELECT COUNT(*) AS n FROM exception_whitelist WHERE user_id = %s AND tenant_id IS NULL", (user_id,))
            r = cur.fetchone()
            return int(r["n"]) if r else 0
    except Exception as e:
        return 0


# ============================================================
# v118.20.5 · 异常栏 P0-3 · 批量复核
# ============================================================
def batch_resolve_exceptions(user_id: str, exception_ids: List[int],
                             tenant_id: Optional[str] = None,
                             new_status: str = "resolved") -> Dict[str, Any]:
    """批量标记异常状态 · 一次性 UPDATE + 同时拿 (seller, rule) 给白名单调用方用
    返回 { processed: N, ids_done: [...], whitelist_pairs: [(seller, rule), ...] }
    whitelist_pairs 仅 new_status=='ignored' 且 seller_name 非空时返回 · 调用方自行去重写白名单
    """
    if new_status not in ("resolved", "ignored"):
        return {"processed": 0, "ids_done": [], "whitelist_pairs": []}
    if not exception_ids:
        return {"processed": 0, "ids_done": [], "whitelist_pairs": []}
    # 强制 int 类型 · 防注入
    safe_ids = [int(x) for x in exception_ids if x is not None]
    if not safe_ids:
        return {"processed": 0, "ids_done": [], "whitelist_pairs": []}
    try:
        with get_cursor(commit=True) as cur:
            # 先查满足条件的 (id, seller, rule) · 过滤掉跨 tenant 的(防越权)
            if tenant_id:
                cur.execute("""
                    SELECT id, seller_name, rule_code
                    FROM exceptions
                    WHERE id = ANY(%s) AND tenant_id = %s AND status = 'pending'
                """, (safe_ids, tenant_id))
            else:
                cur.execute("""
                    SELECT id, seller_name, rule_code
                    FROM exceptions
                    WHERE id = ANY(%s) AND user_id = %s AND tenant_id IS NULL AND status = 'pending'
                """, (safe_ids, user_id))
            rows = cur.fetchall()
            ids_done = [int(r["id"]) for r in rows]
            if not ids_done:
                return {"processed": 0, "ids_done": [], "whitelist_pairs": []}
            # 批量 UPDATE
            if tenant_id:
                cur.execute("""
                    UPDATE exceptions
                    SET status = %s, resolved_by = %s, resolved_at = NOW()
                    WHERE id = ANY(%s) AND tenant_id = %s AND status = 'pending'
                """, (new_status, str(user_id), ids_done, tenant_id))
            else:
                cur.execute("""
                    UPDATE exceptions
                    SET status = %s, resolved_by = %s, resolved_at = NOW()
                    WHERE id = ANY(%s) AND user_id = %s AND tenant_id IS NULL AND status = 'pending'
                """, (new_status, str(user_id), ids_done, user_id))
            # 收集 ignored 对应的 (seller, rule) · 缺 seller 的不进白名单
            wl_pairs: List[tuple] = []
            if new_status == "ignored":
                seen = set()
                for r in rows:
                    seller = (r.get("seller_name") or "").strip()
                    rc = r.get("rule_code")
                    if seller and rc:
                        key = (seller, rc)
                        if key not in seen:
                            seen.add(key)
                            wl_pairs.append(key)
            return {
                "processed": cur.rowcount,
                "ids_done": ids_done,
                "whitelist_pairs": wl_pairs,
            }
    except Exception as e:
        logger.error(f"batch_resolve_exceptions failed: {e}")
        return {"processed": 0, "ids_done": [], "whitelist_pairs": [], "error": str(e)}


# ============================================================
# v118.22.1 · 智能提醒数据底座(notification_rules + notification_logs)
# ============================================================

def ensure_notification_tables():
    """启动时建智能提醒 2 张表 · 幂等 + IF NOT EXISTS · 风格对齐异常栏"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notification_rules (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    name TEXT NOT NULL,
                    template_code TEXT NOT NULL,
                    params JSONB DEFAULT '{}'::jsonb,
                    enabled BOOLEAN DEFAULT true,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_notif_rules_user
                    ON notification_rules(user_id);
                CREATE INDEX IF NOT EXISTS idx_notif_rules_tenant
                    ON notification_rules(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_notif_rules_active
                    ON notification_rules(template_code) WHERE enabled = true;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    rule_id BIGINT,
                    template_code TEXT NOT NULL,
                    event_type TEXT,
                    event_ref TEXT,
                    line_user_id TEXT,
                    status TEXT NOT NULL,
                    error TEXT,
                    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_notif_logs_user
                    ON notification_logs(user_id, sent_at DESC);
                CREATE INDEX IF NOT EXISTS idx_notif_logs_rule
                    ON notification_logs(rule_id, sent_at DESC) WHERE rule_id IS NOT NULL;
            """)
            logger.info("✅ notification_rules + notification_logs 表已就绪")
    except Exception as e:
        logger.error(f"ensure_notification_tables failed: {e}")


def list_notification_rules(user_id: str,
                            tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """列规则 · 同 tenant 共享视图(老板员工同租户共看共改)· 同异常栏隔离规则"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT id, user_id, tenant_id, name, template_code, params,
                           enabled, created_at, updated_at
                      FROM notification_rules
                     WHERE tenant_id = %s
                     ORDER BY created_at DESC
                """, (tenant_id,))
            else:
                cur.execute("""
                    SELECT id, user_id, tenant_id, name, template_code, params,
                           enabled, created_at, updated_at
                      FROM notification_rules
                     WHERE user_id = %s AND tenant_id IS NULL
                     ORDER BY created_at DESC
                """, (str(user_id),))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_notification_rules failed: {e}")
        return []


def get_notification_rule(rule_id: int, user_id: str,
                          tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """取一条规则 · 鉴权:必须属于本人或本租户"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT id, user_id, tenant_id, name, template_code, params,
                           enabled, created_at, updated_at
                      FROM notification_rules
                     WHERE id = %s AND tenant_id = %s
                     LIMIT 1
                """, (int(rule_id), tenant_id))
            else:
                cur.execute("""
                    SELECT id, user_id, tenant_id, name, template_code, params,
                           enabled, created_at, updated_at
                      FROM notification_rules
                     WHERE id = %s AND user_id = %s AND tenant_id IS NULL
                     LIMIT 1
                """, (int(rule_id), str(user_id)))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_notification_rule failed: {e}")
        return None


def create_notification_rule(user_id: str, tenant_id: Optional[str],
                             name: str, template_code: str,
                             params: Optional[Dict[str, Any]] = None,
                             enabled: bool = True) -> Optional[int]:
    """新建规则 · 返回新 id"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO notification_rules
                    (user_id, tenant_id, name, template_code, params, enabled)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                RETURNING id
            """, (
                str(user_id), tenant_id, name.strip(), template_code,
                _json.dumps(params or {}, ensure_ascii=False), bool(enabled),
            ))
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_notification_rule failed: {e}")
        return None


def update_notification_rule(rule_id: int, user_id: str,
                             tenant_id: Optional[str],
                             name: Optional[str] = None,
                             params: Optional[Dict[str, Any]] = None,
                             enabled: Optional[bool] = None) -> bool:
    """改规则 · 任一字段非 None 即更新 · 鉴权同 get"""
    sets = []
    vals: list = []
    if name is not None:
        sets.append("name = %s"); vals.append(name.strip())
    if params is not None:
        sets.append("params = %s::jsonb"); vals.append(_json.dumps(params, ensure_ascii=False))
    if enabled is not None:
        sets.append("enabled = %s"); vals.append(bool(enabled))
    if not sets:
        return True  # 没要改的 · 直接 OK
    sets.append("updated_at = NOW()")
    set_sql = ", ".join(sets)
    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    f"UPDATE notification_rules SET {set_sql} "
                    f"WHERE id = %s AND tenant_id = %s",
                    (*vals, int(rule_id), tenant_id),
                )
            else:
                cur.execute(
                    f"UPDATE notification_rules SET {set_sql} "
                    f"WHERE id = %s AND user_id = %s AND tenant_id IS NULL",
                    (*vals, int(rule_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_notification_rule failed: {e}")
        return False


def delete_notification_rule(rule_id: int, user_id: str,
                             tenant_id: Optional[str]) -> bool:
    """删规则 · 同 get 鉴权 · 同时删 logs 里的引用(SET NULL · 保留发送历史)"""
    try:
        with get_cursor(commit=True) as cur:
            # 先把 logs 的 rule_id 置空(保留历史发送记录)
            cur.execute(
                "UPDATE notification_logs SET rule_id = NULL WHERE rule_id = %s",
                (int(rule_id),),
            )
            if tenant_id:
                cur.execute(
                    "DELETE FROM notification_rules WHERE id = %s AND tenant_id = %s",
                    (int(rule_id), tenant_id),
                )
            else:
                cur.execute(
                    "DELETE FROM notification_rules "
                    "WHERE id = %s AND user_id = %s AND tenant_id IS NULL",
                    (int(rule_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_notification_rule failed: {e}")
        return False


def log_notification(user_id: str, tenant_id: Optional[str],
                     rule_id: Optional[int], template_code: str,
                     event_type: Optional[str], event_ref: Optional[str],
                     line_user_id: Optional[str], status: str,
                     error: Optional[str] = None) -> Optional[int]:
    """写一条发送记录 · 失败也吞(不影响主流程)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO notification_logs
                    (user_id, tenant_id, rule_id, template_code,
                     event_type, event_ref, line_user_id, status, error)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(user_id), tenant_id,
                int(rule_id) if rule_id is not None else None,
                template_code,
                event_type, event_ref, line_user_id, status, error,
            ))
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.warning(f"log_notification failed: {e}")
        return None


def list_notification_logs(user_id: str, tenant_id: Optional[str] = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
    """列发送日志 · 同 tenant 共享 · 默认最近 50 条"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT id, user_id, tenant_id, rule_id, template_code,
                           event_type, event_ref, line_user_id, status, error, sent_at
                      FROM notification_logs
                     WHERE tenant_id = %s
                     ORDER BY sent_at DESC LIMIT %s
                """, (tenant_id, int(limit)))
            else:
                cur.execute("""
                    SELECT id, user_id, tenant_id, rule_id, template_code,
                           event_type, event_ref, line_user_id, status, error, sent_at
                      FROM notification_logs
                     WHERE user_id = %s AND tenant_id IS NULL
                     ORDER BY sent_at DESC LIMIT %s
                """, (str(user_id), int(limit)))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_notification_logs failed: {e}")
        return []


def list_active_notification_rules_by_template(template_code: str) -> List[Dict[str, Any]]:
    """v118.22.1.1 hook 用 · 取所有启用的某模板规则(跨 user 全表 · 异步触发匹配)"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, user_id, tenant_id, name, template_code, params, enabled
                  FROM notification_rules
                 WHERE template_code = %s AND enabled = true
            """, (template_code,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_active_notification_rules_by_template failed: {e}")
        return []


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

            logger.info("✅ v118.27.7 · memberships / client_assignments / roles 表已就绪 · 3 系统角色已灌入")
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
            cur.execute(
                "SELECT client_id FROM client_assignments WHERE user_id = %s",
                (user_id,)
            )
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
            cur.execute("""
                SELECT ca.user_id, ca.client_id
                FROM client_assignments ca
                JOIN users u ON u.id = ca.user_id
                WHERE u.tenant_id = %s
            """, (str(tenant_id),))
            for r in (cur.fetchall() or []):
                uid = str(r["user_id"] if isinstance(r, dict) else r[0])
                cid = int(r["client_id"] if isinstance(r, dict) else r[1])
                out.setdefault(uid, []).append(cid)
    except Exception as e:
        logger.error(f"list_assignments_by_employees failed: {e}")
    return out


def set_employee_assignments(employee_user_id: str, client_ids,
                              assigned_by: str, tenant_id: str) -> bool:
    """覆盖式设置员工的客户列表
    安全:校验员工和所有 client_id 都在 tenant_id 内 · 防跨租户
    """
    if not employee_user_id or not assigned_by or not tenant_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            # 校验员工属于本租户
            cur.execute("SELECT tenant_id FROM users WHERE id = %s LIMIT 1",
                       (str(employee_user_id),))
            row = cur.fetchone()
            if not row:
                return False
            row_tid = row["tenant_id"] if isinstance(row, dict) else row[0]
            if str(row_tid) != str(tenant_id):
                return False

            # 删现有所有
            cur.execute("DELETE FROM client_assignments WHERE user_id = %s",
                       (str(employee_user_id),))

            # 校验要分配的 client_ids 都在本租户(防越权写)
            valid_ids = []
            if client_ids:
                int_ids = [int(c) for c in client_ids if c is not None]
                if int_ids:
                    cur.execute("""
                        SELECT id FROM clients
                        WHERE id = ANY(%s::bigint[])
                          AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    """, (int_ids, str(tenant_id)))
                    valid_ids = [int(r["id"] if isinstance(r, dict) else r[0])
                                for r in (cur.fetchall() or [])]

            # 批插
            for cid in valid_ids:
                cur.execute("""
                    INSERT INTO client_assignments (user_id, client_id, assigned_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, client_id) DO NOTHING
                """, (str(employee_user_id), cid, str(assigned_by)))
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
            cur.execute("""
                INSERT INTO client_assignments (user_id, client_id, assigned_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, client_id) DO NOTHING
            """, (str(creator_user_id), int(client_id), str(creator_user_id)))
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
            cur.execute("""
                SELECT tenant_id FROM memberships
                WHERE user_id = %s AND status = 'active'
                LIMIT 1
            """, (str(user_id),))
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
                eligible_rows.append({
                    "user_id": str(r["id"]),
                    "username": r.get("username"),
                    "tenant_id": str(r["tenant_id"]),
                    "role": new_role_name,
                    "role_id": role_map[new_role_name],
                })

            out["eligible"] = len(eligible_rows)
            out["role_distribution"] = role_count
            out["missing_role"] = sorted(missing_set)
            out["sample_inserts"] = [
                {"user_id": e["user_id"], "username": e["username"],
                 "tenant_id": e["tenant_id"], "role": e["role"]}
                for e in eligible_rows[:5]
            ]

            if dry_run:
                out["ok"] = True
                logger.info(f"[v27.7 migration] DRY-RUN · scanned={out['scanned']} eligible={out['eligible']} already={out['already_migrated']}")
                return out

            # 真执行 · 逐条插入(批量插入风险大 · 单条可继续)
            inserted = 0
            for e in eligible_rows:
                try:
                    cur.execute("""
                        INSERT INTO memberships (user_id, tenant_id, role_id, status)
                        VALUES (%s, %s, %s, 'active')
                        ON CONFLICT (user_id) DO NOTHING
                    """, (e["user_id"], e["tenant_id"], e["role_id"]))
                    if cur.rowcount > 0:
                        inserted += 1
                except Exception as e_one:
                    out["errors"].append({"user_id": e["user_id"], "msg": str(e_one)[:200]})

            out["inserted"] = inserted
            out["ok"] = True
            logger.info(f"[v27.7 migration] EXECUTED · inserted={inserted}/{len(eligible_rows)} errors={len(out['errors'])}")
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
                out.append({
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
                    "trial_expires_at": r["trial_expires_at"].isoformat() if r.get("trial_expires_at") else None,
                    "plan_expires_at": r["plan_expires_at"].isoformat() if r.get("plan_expires_at") else None,
                    "last_login_at": r["last_login_at"].isoformat() if r.get("last_login_at") else None,
                    "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
                    "ocr_count": int(r.get("ocr_count") or 0),
                    "client_count": int(r.get("client_count") or 0),
                    "erp_count": int(r.get("erp_count") or 0),
                })
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
                out["errors"].append({"user_id": None, "msg": "owner_role_not_found · run ensure_membership_tables() first"})
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
            logger.info(f"[v27.7.1 fix_orphan] DRY-RUN · scanned={out['scanned']} plans={len(out['plan'])}")
            return out

        # 真执行 · 每个用户独立事务
        for p in out["plan"]:
            try:
                with get_cursor(commit=True) as cur:
                    # 1. 建 tenant · v27.7.2 修:tenants 表只有 subscription_expires_at · 没有 trial_expires_at
                    # 用户的 trial / plan 到期都收敛到 tenant.subscription_expires_at(优先 plan_expires_at)
                    cur.execute("""
                        INSERT INTO tenants (
                            name, owner_user_id, tenant_type, monthly_quota,
                            used_this_month, status, member_count,
                            tenant_type_v2, subscription_expires_at
                        )
                        VALUES (%s, %s, 'shared_api', %s, 0, 'active', 1,
                                'firm', %s)
                        RETURNING id
                    """, (
                        p["tenant_name_to_create"],
                        p["user_id"],
                        p["quota_inherit"],
                        p.get("plan_expires_at") or p.get("trial_expires_at"),
                    ))
                    new_tenant_id = str(cur.fetchone()["id"])

                    # 2. UPDATE user.tenant_id + role(竞态保护:tenant_id 必须仍是 NULL)
                    cur.execute("""
                        UPDATE users SET tenant_id = %s, role = COALESCE(role, 'owner')
                        WHERE id = %s AND tenant_id IS NULL
                    """, (new_tenant_id, p["user_id"]))
                    if cur.rowcount == 0:
                        # 用户在我们处理过程中被别的流程绑了 tenant · 删掉刚建的孤儿 tenant · 跳过
                        cur.execute("DELETE FROM tenants WHERE id = %s", (new_tenant_id,))
                        out["errors"].append({"user_id": p["user_id"], "msg": "user_already_has_tenant_skip"})
                        continue

                    # 3. 写 membership
                    cur.execute("""
                        INSERT INTO memberships (user_id, tenant_id, role_id, status)
                        VALUES (%s, %s, %s, 'active')
                        ON CONFLICT (user_id) DO NOTHING
                    """, (p["user_id"], new_tenant_id, owner_role_id))

                    out["executed"] += 1
                    p["new_tenant_id"] = new_tenant_id
                    logger.info(f"[v27.7.1 fix_orphan] +tenant {new_tenant_id[:8]}.. for user {p.get('username')!r} email={p.get('email')!r}")
            except Exception as e_one:
                logger.error(f"[v27.7.1 fix_orphan] user_id={p['user_id']} failed: {e_one}")
                out["errors"].append({"user_id": p["user_id"], "msg": str(e_one)[:200]})

        out["ok"] = True
        logger.info(f"[v27.7.1 fix_orphan] EXECUTED · executed={out['executed']}/{len(out['plan'])} errors={len(out['errors'])}")
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
            "tenant_a": {"id": str(samples[0]["tenant_id"]), "name": samples[0].get("tenant_name"),
                          "client_id": int(samples[0]["client_id"]), "client_name": samples[0].get("client_name")},
            "tenant_b": {"id": str(samples[1]["tenant_id"]), "name": samples[1].get("tenant_name"),
                          "client_id": int(samples[1]["client_id"]), "client_name": samples[1].get("client_name")},
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
        out["tests"].append({"name": "fatal", "ok": False,
                              "expected": "test 框架正常", "actual": str(e)[:300]})
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
                logger.error(f"[v27.8.0 rls_test] 关 RLS 失败 · 需手动:ALTER TABLE clients DISABLE ROW LEVEL SECURITY; · 错误: {e}")
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
            logger.info(f"[v27.8.1 backfill] EXECUTED · total updated={out['total_updated']} errors={len(out['errors'])}")
        return out
    except Exception as e:
        import traceback
        logger.error(f"backfill_tenant_ids fatal: {e}\n{traceback.format_exc()}")
        out["errors"].append({"table": None, "msg": str(e)[:300]})
        return out


# ============================================================
# v118.27.0 · ERP 映射底座(客户 / 科目 / 税码 3 张表)
# ============================================================
# 设计:
#   - 3 张表都带 erp_type · 同一 Pearnly 客户/分类/税种在不同 ERP 编码可不同
#   - erp_client_mappings 接 client_assignments filter(员工只看自己客户)
#   - erp_account_mappings / erp_tax_mappings tenant 共享(员工只读)
#   - erp_code 用 VARCHAR 不用 INT(MR.ERP "7%" 字符串 / FlowAccount 数字 ID 都通吃)
# ============================================================

ERP_TYPES_VALID = {"flowaccount", "peak", "xero", "quickbooks", "express"}
PEARNLY_TAX_KINDS_VALID = {
    "vat_7", "vat_0", "vat_exempt",
    "wht_1", "wht_3", "wht_5",
    "non_vat",
}


def ensure_erp_mapping_tables():
    """v118.27.0 · ERP 映射底座 3 张表 · 启动时幂等建"""
    try:
        with get_cursor(commit=True) as cur:
            # ── 客户映射(Pearnly client_id → ERP customer 编号 · 按 erp_type 区分)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_client_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    erp_code VARCHAR(128) NOT NULL,
                    notes TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, client_id, erp_type)
                );
                CREATE INDEX IF NOT EXISTS idx_erp_cli_map_tenant ON erp_client_mappings(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_erp_cli_map_client ON erp_client_mappings(client_id);
                CREATE INDEX IF NOT EXISTS idx_erp_cli_map_erp ON erp_client_mappings(erp_type);
            """)
            # ── 科目映射(Pearnly category → ERP GL code · tenant 共享)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_account_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    pearnly_category VARCHAR(64) NOT NULL,
                    erp_code VARCHAR(128) NOT NULL,
                    erp_name TEXT,
                    notes TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, erp_type, pearnly_category)
                );
                CREATE INDEX IF NOT EXISTS idx_erp_acc_map_tenant ON erp_account_mappings(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_erp_acc_map_erp ON erp_account_mappings(erp_type);
            """)
            # ── 税码映射(Pearnly tax_kind → ERP tax_code · tenant 共享)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_tax_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    pearnly_tax_kind VARCHAR(32) NOT NULL,
                    erp_code VARCHAR(64) NOT NULL,
                    notes TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, erp_type, pearnly_tax_kind)
                );
                CREATE INDEX IF NOT EXISTS idx_erp_tax_map_tenant ON erp_tax_mappings(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_erp_tax_map_erp ON erp_tax_mappings(erp_type);
            """)
            # ── v27.8.1.17 · 商品映射(OCR item_name → ERP product code · tenant 级)
            # key 是 OCR 抽到的明细行 name(归一化前)· 用 norm 字段建索引方便查
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_product_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    item_name_norm VARCHAR(256) NOT NULL,
                    erp_code VARCHAR(128) NOT NULL,
                    erp_name TEXT,
                    notes TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, erp_type, item_name_norm)
                );
                CREATE INDEX IF NOT EXISTS idx_erp_prod_map_tenant ON erp_product_mappings(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_erp_prod_map_erp ON erp_product_mappings(erp_type);
                CREATE INDEX IF NOT EXISTS idx_erp_prod_map_norm ON erp_product_mappings(tenant_id, erp_type, item_name_norm);
            """)
            logger.info("✅ v118.27.0 · erp_client/account/tax_mappings 三张映射表已就绪")
    except Exception as e:
        logger.error(f"ensure_erp_mapping_tables failed: {e}")


# ─── 客户映射 CRUD(接 client_assignments filter)──────────────
def list_erp_client_mappings(tenant_id, restrict_client_ids=None):
    """列客户映射
    - restrict_client_ids=None → 不限制(老板/超管)
    - restrict_client_ids=[...] → 只看分配给员工的客户
    - restrict_client_ids=[]   → 没分配 → 空列表
    """
    if not tenant_id:
        return []
    try:
        with get_cursor() as cur:
            sql = """
                SELECT m.id, m.tenant_id, m.client_id, m.erp_type, m.erp_code,
                       m.notes, m.created_at, m.updated_at,
                       c.name AS client_name
                FROM erp_client_mappings m
                JOIN clients c ON c.id = m.client_id
                WHERE m.tenant_id = %s
            """
            params = [str(tenant_id)]
            if restrict_client_ids is not None:
                if not restrict_client_ids:
                    return []
                sql += " AND m.client_id = ANY(%s)"
                params.append([int(x) for x in restrict_client_ids])
            sql += " ORDER BY c.name ASC, m.erp_type ASC"
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_erp_client_mappings failed: {e}")
        return []


def upsert_erp_client_mapping(tenant_id, client_id, erp_type, erp_code, notes, user_id):
    """加/更新客户映射 · 校验 client_id 属于 tenant · 同 (tenant, client, erp_type) 覆盖"""
    if not tenant_id or not client_id or not erp_type or not erp_code:
        return None
    erp_type = (erp_type or "").strip().lower()
    if erp_type not in ERP_TYPES_VALID:
        return None
    erp_code = (erp_code or "").strip()[:128]
    if not erp_code:
        return None
    notes_clean = (notes or "").strip()[:500]
    try:
        with get_cursor(commit=True) as cur:
            # 校验 client 属于 tenant
            cur.execute("""
                SELECT 1 FROM clients c
                JOIN users u ON u.id = c.user_id
                WHERE c.id = %s AND u.tenant_id = %s
            """, (int(client_id), str(tenant_id)))
            if not cur.fetchone():
                return None
            cur.execute("""
                INSERT INTO erp_client_mappings
                    (tenant_id, client_id, erp_type, erp_code, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, client_id, erp_type)
                DO UPDATE SET
                    erp_code = EXCLUDED.erp_code,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id
            """, (
                str(tenant_id), int(client_id), erp_type, erp_code,
                notes_clean, str(user_id) if user_id else None,
            ))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_erp_client_mapping failed: {e}")
        return None


def delete_erp_client_mapping(tenant_id, mapping_id):
    if not tenant_id or not mapping_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_client_mappings WHERE id = %s AND tenant_id = %s",
                (str(mapping_id), str(tenant_id))
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_client_mapping failed: {e}")
        return False


# ─── 科目映射 CRUD(tenant 共享 · 不接 client_assignments)─────
def list_erp_account_mappings(tenant_id):
    if not tenant_id:
        return []
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, tenant_id, erp_type, pearnly_category, erp_code,
                       erp_name, notes, created_at, updated_at
                FROM erp_account_mappings
                WHERE tenant_id = %s
                ORDER BY erp_type ASC, pearnly_category ASC
            """, (str(tenant_id),))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_erp_account_mappings failed: {e}")
        return []


def upsert_erp_account_mapping(tenant_id, erp_type, pearnly_category, erp_code, erp_name, notes, user_id):
    if not tenant_id or not erp_type or not pearnly_category or not erp_code:
        return None
    erp_type = (erp_type or "").strip().lower()
    if erp_type not in ERP_TYPES_VALID:
        return None
    cat = (pearnly_category or "").strip()[:64]
    code = (erp_code or "").strip()[:128]
    if not cat or not code:
        return None
    name_clean = (erp_name or "").strip()[:200]
    notes_clean = (notes or "").strip()[:500]
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO erp_account_mappings
                    (tenant_id, erp_type, pearnly_category, erp_code, erp_name, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, erp_type, pearnly_category)
                DO UPDATE SET
                    erp_code = EXCLUDED.erp_code,
                    erp_name = EXCLUDED.erp_name,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id
            """, (
                str(tenant_id), erp_type, cat, code, name_clean, notes_clean,
                str(user_id) if user_id else None,
            ))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_erp_account_mapping failed: {e}")
        return None


def delete_erp_account_mapping(tenant_id, mapping_id):
    if not tenant_id or not mapping_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_account_mappings WHERE id = %s AND tenant_id = %s",
                (str(mapping_id), str(tenant_id))
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_account_mapping failed: {e}")
        return False


# ─── 税码映射 CRUD(tenant 共享)──────────────────────────
def list_erp_tax_mappings(tenant_id):
    if not tenant_id:
        return []
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, tenant_id, erp_type, pearnly_tax_kind, erp_code,
                       notes, created_at, updated_at
                FROM erp_tax_mappings
                WHERE tenant_id = %s
                ORDER BY erp_type ASC, pearnly_tax_kind ASC
            """, (str(tenant_id),))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_erp_tax_mappings failed: {e}")
        return []


def upsert_erp_tax_mapping(tenant_id, erp_type, pearnly_tax_kind, erp_code, notes, user_id):
    if not tenant_id or not erp_type or not pearnly_tax_kind or not erp_code:
        return None
    erp_type = (erp_type or "").strip().lower()
    if erp_type not in ERP_TYPES_VALID:
        return None
    kind = (pearnly_tax_kind or "").strip()
    if kind not in PEARNLY_TAX_KINDS_VALID:
        return None
    code = (erp_code or "").strip()[:64]
    if not code:
        return None
    notes_clean = (notes or "").strip()[:500]
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO erp_tax_mappings
                    (tenant_id, erp_type, pearnly_tax_kind, erp_code, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, erp_type, pearnly_tax_kind)
                DO UPDATE SET
                    erp_code = EXCLUDED.erp_code,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id
            """, (
                str(tenant_id), erp_type, kind, code, notes_clean,
                str(user_id) if user_id else None,
            ))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_erp_tax_mapping failed: {e}")
        return None


def delete_erp_tax_mapping(tenant_id, mapping_id):
    if not tenant_id or not mapping_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_tax_mappings WHERE id = %s AND tenant_id = %s",
                (str(mapping_id), str(tenant_id))
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_tax_mapping failed: {e}")
        return False


# ─── 商品映射 CRUD(v27.8.1.17 · tenant 级 · key 是 OCR item_name 的归一化形式)─
def _product_name_norm_for_db(s):
    """v27.8.1.17 · 商品名归一化(给数据库 unique key 用)· 小写 + 去空白标点
    跟 app.py 的 _normalize_buyer_name 同理 · 这里不调用避免循环引用
    """
    if not s:
        return ""
    import re as _re
    out = _re.sub(r"[\s\.,\-_/\\()&\"'`*]+", '', str(s))
    return out.lower().strip()[:256]


def list_erp_product_mappings(tenant_id, erp_type=None):
    """列商品映射(全部 / 单 ERP 类型)"""
    if not tenant_id:
        return []
    try:
        with get_cursor() as cur:
            if erp_type:
                cur.execute("""
                    SELECT id, tenant_id, erp_type, item_name, erp_code, erp_name, notes,
                           created_by, created_at, updated_at
                    FROM erp_product_mappings
                    WHERE tenant_id = %s AND erp_type = %s
                    ORDER BY created_at DESC
                """, (str(tenant_id), erp_type.strip().lower()))
            else:
                cur.execute("""
                    SELECT id, tenant_id, erp_type, item_name, erp_code, erp_name, notes,
                           created_by, created_at, updated_at
                    FROM erp_product_mappings
                    WHERE tenant_id = %s
                    ORDER BY erp_type, created_at DESC
                """, (str(tenant_id),))
            return cur.fetchall() or []
    except Exception as e:
        logger.error(f"list_erp_product_mappings failed: {e}")
        return []


def upsert_erp_product_mapping(tenant_id, erp_type, item_name, erp_code, erp_name, notes, user_id):
    """加/更新商品映射 · 同 (tenant, erp_type, item_name_norm) 覆盖"""
    if not tenant_id or not erp_type or not item_name or not erp_code:
        return None
    erp_type = (erp_type or "").strip().lower()
    if erp_type not in ERP_TYPES_VALID:
        return None
    item_name = (item_name or "").strip()[:512]
    item_name_norm = _product_name_norm_for_db(item_name)
    if not item_name_norm:
        return None
    erp_code_clean = (erp_code or "").strip()[:128]
    if not erp_code_clean:
        return None
    erp_name_clean = (erp_name or "").strip()[:256] if erp_name else None
    notes_clean = (notes or "").strip()[:500]
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO erp_product_mappings
                    (tenant_id, erp_type, item_name, item_name_norm, erp_code, erp_name, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, erp_type, item_name_norm)
                DO UPDATE SET
                    item_name = EXCLUDED.item_name,
                    erp_code = EXCLUDED.erp_code,
                    erp_name = EXCLUDED.erp_name,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id
            """, (
                str(tenant_id), erp_type, item_name, item_name_norm, erp_code_clean,
                erp_name_clean, notes_clean, str(user_id) if user_id else None,
            ))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_erp_product_mapping failed: {e}")
        return None


def delete_erp_product_mapping(tenant_id, mapping_id):
    if not tenant_id or not mapping_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_product_mappings WHERE id = %s AND tenant_id = %s",
                (str(mapping_id), str(tenant_id))
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_product_mapping failed: {e}")
        return False


def find_erp_product_mappings_batch(tenant_id, erp_type, item_names):
    """v27.8.1.17 · 批量查多个 item_name 的映射状态(推送前预检 / 自动注入用)
    返回:dict[item_name_norm → {erp_code, erp_name, item_name}]
    """
    if not tenant_id or not erp_type or not item_names:
        return {}
    erp_type = (erp_type or "").strip().lower()
    norms = []
    for n in item_names:
        nm = _product_name_norm_for_db(n)
        if nm:
            norms.append(nm)
    if not norms:
        return {}
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT item_name, item_name_norm, erp_code, erp_name
                FROM erp_product_mappings
                WHERE tenant_id = %s AND erp_type = %s AND item_name_norm = ANY(%s)
            """, (str(tenant_id), erp_type, norms))
            rows = cur.fetchall() or []
            out = {}
            for r in rows:
                out[r["item_name_norm"]] = {
                    "erp_code": r["erp_code"],
                    "erp_name": r["erp_name"] or "",
                    "item_name": r["item_name"],
                }
            return out
    except Exception as e:
        logger.error(f"find_erp_product_mappings_batch failed: {e}")
        return {}


# ─── skin 白名单 · 演示数据(用 notes 'DEMO' 标记 · 一键清掉)─
def clear_erp_test_mappings(tenant_id):
    """清掉所有 notes='DEMO' 或 'DEMO ...' 开头的映射"""
    if not tenant_id:
        return 0
    n = 0
    try:
        with get_cursor(commit=True) as cur:
            for tbl in ("erp_client_mappings", "erp_account_mappings", "erp_tax_mappings"):
                cur.execute(
                    f"DELETE FROM {tbl} WHERE tenant_id = %s "
                    f"AND (notes = 'DEMO' OR notes LIKE 'DEMO %%')",
                    (str(tenant_id),)
                )
                n += cur.rowcount
    except Exception as e:
        logger.error(f"clear_erp_test_mappings failed: {e}")
    return n


def get_mrerp_mappings_bundle(tenant_id):
    """通用 ERP 映射束 · 一次拿 4 张映射表(clients / accounts / taxes / products)
    供推送引擎(Xero 等)使用
    """
    if not tenant_id:
        return {'clients': [], 'accounts': [], 'taxes': [], 'products': []}
    try:
        return {
            'clients':  list_erp_client_mappings(tenant_id, restrict_client_ids=None),
            'accounts': list_erp_account_mappings(tenant_id),
            'taxes':    list_erp_tax_mappings(tenant_id),
            'products': list_erp_product_mappings(tenant_id),
        }
    except Exception as e:
        logger.error(f"get_mrerp_mappings_bundle failed: {e}")
        return {'clients': [], 'accounts': [], 'taxes': [], 'products': []}


# ============================================================
# v118.27.4 · ERP OAuth 2.0 token 表(Xero / FlowAccount / QuickBooks 共用)
# ============================================================
# 设计:
#   - 1 个 tenant 在 1 家 ERP 可有多个 organisation/company token(UNIQUE 含 org_id)
#   - 但有 1 个 is_default 行 · 用于推送时拿默认
#   - token_version=1 → base64 编码 · 升 AES 时改 2(P1 安全债务)
# ============================================================

def ensure_erp_oauth_tables():
    """v118.27.4 · OAuth token 表 + state 临时表 · 启动时幂等建
    v27.8.1.3 加 auto_push 字段(端到端自动推开关 · tenant 级别)"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_oauth_tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    organisation_id TEXT NOT NULL,
                    organisation_name TEXT,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    scope TEXT,
                    is_default BOOLEAN NOT NULL DEFAULT FALSE,
                    token_version INT NOT NULL DEFAULT 1,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, erp_type, organisation_id)
                );
                CREATE INDEX IF NOT EXISTS idx_oauth_tokens_tenant ON erp_oauth_tokens(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_oauth_tokens_default ON erp_oauth_tokens(is_default) WHERE is_default = TRUE;
            """)
            # v27.8.1.3 · 幂等加 auto_push 字段
            cur.execute("""
                ALTER TABLE erp_oauth_tokens
                ADD COLUMN IF NOT EXISTS auto_push BOOLEAN NOT NULL DEFAULT FALSE;
            """)
            # OAuth state 防 CSRF · 5 分钟过期
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_oauth_states (
                    state TEXT PRIMARY KEY,
                    tenant_id UUID NOT NULL,
                    user_id UUID NOT NULL,
                    erp_type TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_oauth_states_created ON erp_oauth_states(created_at);
            """)
            logger.info("✅ v118.27.4 · erp_oauth_tokens / erp_oauth_states 表已就绪(含 v27.8.1.3 auto_push)")
    except Exception as e:
        logger.error(f"ensure_erp_oauth_tables failed: {e}")


def set_xero_auto_push(tenant_id: str, on: bool) -> bool:
    """v27.8.1.3 · 切换 Xero 自动推送开关(tenant 级别 · 影响所有 org)"""
    if not tenant_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE erp_oauth_tokens SET auto_push = %s, updated_at = NOW()
                WHERE tenant_id = %s AND erp_type = 'xero'
            """, (bool(on), tenant_id))
        return True
    except Exception as e:
        logger.error(f"set_xero_auto_push failed: {e}")
        return False


def get_xero_auto_push(tenant_id: str) -> bool:
    """v27.8.1.3 · 拿 Xero 自动推送状态(任一 org auto_push=true 都算开)"""
    if not tenant_id:
        return False
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT 1 FROM erp_oauth_tokens
                WHERE tenant_id = %s AND erp_type = 'xero' AND auto_push = TRUE LIMIT 1
            """, (tenant_id,))
            return cur.fetchone() is not None
    except Exception:
        return False


def list_tenants_xero_auto_push_on() -> list:
    """v27.8.1.3 · 给 OCR hook 用 · 拉所有开了 Xero 自动推的 tenant_id 列表"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT DISTINCT tenant_id::text AS tid
                FROM erp_oauth_tokens
                WHERE erp_type = 'xero' AND auto_push = TRUE
            """)
            return [r["tid"] for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_tenants_xero_auto_push_on failed: {e}")
        return []




def _b64_encode(s: str) -> str:
    """v118.27.4 · token_version=1 · base64 编码(P1 升 AES)"""
    import base64
    return base64.b64encode((s or "").encode("utf-8")).decode("ascii")


def _b64_decode(s: str) -> str:
    import base64
    try:
        return base64.b64decode((s or "").encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def save_oauth_state(state, tenant_id, user_id, erp_type):
    """存 state · 5 分钟过期 · 同 tenant 同 erp 老的会被覆盖"""
    if not state or not tenant_id or not user_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            # 顺手清掉 5 分钟前的 state(轻量 GC)
            cur.execute("DELETE FROM erp_oauth_states WHERE created_at < NOW() - INTERVAL '5 minutes'")
            cur.execute("""
                INSERT INTO erp_oauth_states (state, tenant_id, user_id, erp_type)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (state) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    user_id = EXCLUDED.user_id,
                    erp_type = EXCLUDED.erp_type,
                    created_at = NOW()
            """, (str(state), str(tenant_id), str(user_id), str(erp_type)))
            return True
    except Exception as e:
        logger.error(f"save_oauth_state failed: {e}")
        return False


def consume_oauth_state(state):
    """callback 用 · 验证 + 单次消费"""
    if not state:
        return None
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                DELETE FROM erp_oauth_states
                WHERE state = %s AND created_at >= NOW() - INTERVAL '5 minutes'
                RETURNING tenant_id, user_id, erp_type
            """, (str(state),))
            row = cur.fetchone()
            if not row:
                return None
            return {
                'tenant_id': str(row['tenant_id']),
                'user_id':   str(row['user_id']),
                'erp_type':  str(row['erp_type']),
            }
    except Exception as e:
        logger.error(f"consume_oauth_state failed: {e}")
        return None


def upsert_oauth_token(tenant_id, erp_type, organisation_id, organisation_name,
                       access_token, refresh_token, expires_at, scope,
                       is_default, user_id):
    """存/更新 OAuth token · 同 (tenant, erp, org) 覆盖
    expires_at: datetime aware 或 ISO 字符串
    """
    if not tenant_id or not erp_type or not organisation_id or not access_token or not refresh_token:
        return None
    try:
        with get_cursor(commit=True) as cur:
            if is_default:
                # 同 tenant 同 erp 老的全部 unset is_default
                cur.execute(
                    "UPDATE erp_oauth_tokens SET is_default = FALSE WHERE tenant_id = %s AND erp_type = %s",
                    (str(tenant_id), str(erp_type)),
                )
            cur.execute("""
                INSERT INTO erp_oauth_tokens
                    (tenant_id, erp_type, organisation_id, organisation_name,
                     access_token, refresh_token, expires_at, scope,
                     is_default, token_version, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
                ON CONFLICT (tenant_id, erp_type, organisation_id)
                DO UPDATE SET
                    organisation_name = EXCLUDED.organisation_name,
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at,
                    scope = EXCLUDED.scope,
                    is_default = EXCLUDED.is_default,
                    updated_at = NOW()
                RETURNING id
            """, (
                str(tenant_id), str(erp_type), str(organisation_id),
                (organisation_name or "")[:200],
                _b64_encode(access_token),
                _b64_encode(refresh_token),
                expires_at,
                (scope or "")[:500],
                bool(is_default),
                str(user_id) if user_id else None,
            ))
            row = cur.fetchone()
            return str(row['id']) if row else None
    except Exception as e:
        logger.error(f"upsert_oauth_token failed: {e}")
        return None


def get_default_oauth_token(tenant_id, erp_type):
    """拿默认 organisation 的 token(解码后明文)"""
    if not tenant_id or not erp_type:
        return None
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, organisation_id, organisation_name,
                       access_token, refresh_token, expires_at, scope, is_default,
                       token_version, updated_at
                FROM erp_oauth_tokens
                WHERE tenant_id = %s AND erp_type = %s
                ORDER BY is_default DESC, updated_at DESC
                LIMIT 1
            """, (str(tenant_id), str(erp_type)))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d['access_token']  = _b64_decode(d['access_token'])
            d['refresh_token'] = _b64_decode(d['refresh_token'])
            return d
    except Exception as e:
        logger.error(f"get_default_oauth_token failed: {e}")
        return None


def list_oauth_tokens(tenant_id, erp_type):
    """列出该 tenant 在该 ERP 下所有 organisation(供 UI 切换)"""
    if not tenant_id or not erp_type:
        return []
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, organisation_id, organisation_name, expires_at,
                       is_default, scope, updated_at
                FROM erp_oauth_tokens
                WHERE tenant_id = %s AND erp_type = %s
                ORDER BY is_default DESC, organisation_name ASC
            """, (str(tenant_id), str(erp_type)))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_oauth_tokens failed: {e}")
        return []


def update_oauth_access_token(token_id, access_token, refresh_token, expires_at):
    """refresh 后写回新 access + refresh + expires"""
    if not token_id or not access_token or not refresh_token:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE erp_oauth_tokens
                SET access_token = %s,
                    refresh_token = %s,
                    expires_at = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                _b64_encode(access_token),
                _b64_encode(refresh_token),
                expires_at,
                str(token_id),
            ))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_oauth_access_token failed: {e}")
        return False


def delete_oauth_tokens(tenant_id, erp_type):
    """断开连接 · 删该 tenant 在该 ERP 的所有 token"""
    if not tenant_id or not erp_type:
        return 0
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_oauth_tokens WHERE tenant_id = %s AND erp_type = %s",
                (str(tenant_id), str(erp_type)),
            )
            return cur.rowcount
    except Exception as e:
        logger.error(f"delete_oauth_tokens failed: {e}")
        return 0


def set_default_oauth_token(tenant_id, erp_type, token_id):
    """切换默认 organisation"""
    if not tenant_id or not erp_type or not token_id:
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE erp_oauth_tokens SET is_default = FALSE WHERE tenant_id = %s AND erp_type = %s",
                (str(tenant_id), str(erp_type)),
            )
            cur.execute(
                "UPDATE erp_oauth_tokens SET is_default = TRUE, updated_at = NOW() "
                "WHERE id = %s AND tenant_id = %s AND erp_type = %s",
                (str(token_id), str(tenant_id), str(erp_type)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"set_default_oauth_token failed: {e}")
        return False


# ============================================================
# v118.32.0 · 销项税对账三张表(VAT Reconciliation Bottom Layer)
#   - vat_report            : VAT 报告原始 + 解析后结构化
#   - reconciliation_task   : 对账任务(1 任务 = 1 客户 × 1 纳税期间)
#   - reconciliation_row    : 逐行对账明细(配对 + diff 结果)
# 约束:
#   - vat_report 先建(被 task 外键引用)
#   - ocr_history.id 是 UUID · invoice_id 用 UUID
#   - clients.id 是 BIGSERIAL · client_id 用 BIGINT
#   - tenant_id 用 UUID 对齐全库惯例
#   - 唯一约束:同 client × period 只允许 1 个非 failed 任务
#   - reconciliation_row ON DELETE CASCADE 跟随 task 删除
# ============================================================

def ensure_vat_recon_tables():
    """v118.32.0 · 销项税对账 3 张表 · 启动时幂等建"""
    try:
        with get_cursor(commit=True) as cur:

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

            logger.info("✅ vat_report + reconciliation_task + reconciliation_row 已就绪 (v118.32.0)")
    except Exception as e:
        logger.error(f"ensure_vat_recon_tables failed: {e}")


# ── CRUD · vat_report ──────────────────────────────────────

def create_vat_report(tenant_id, client_id: int, period_year: int, period_month: int,
                      parsed_rows: list, meta: dict,
                      source_filename: str = "", parser_version: str = "") -> Optional[int]:
    import json as _j
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
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
            """, (
                str(tenant_id) if tenant_id else None,
                client_id, period_year, period_month,
                _j.dumps([source_filename], ensure_ascii=False),
                _j.dumps(parsed_rows, ensure_ascii=False, default=str),
                meta.get("total_amount_pre_vat"),
                meta.get("total_vat"),
                meta.get("total_amount"),
                parser_version,
            ))
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_vat_report failed: {e}")
        return None


def get_vat_report(report_id: int) -> Optional[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
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

def create_recon_task(tenant_id, user_id: str, client_id: int,
                      period_year: int, period_month: int,
                      vat_report_id: int) -> Optional[int]:
    """创建对账任务 · 同 client+period 唯一约束失败时返回 None"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO reconciliation_task (
                    tenant_id, user_id, client_id,
                    period_year, period_month, vat_report_id
                ) VALUES (%s, %s::uuid, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(tenant_id) if tenant_id else None,
                user_id, client_id, period_year, period_month, vat_report_id,
            ))
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_recon_task failed: {e}")
        return None


def get_recon_task(task_id: int) -> Optional[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM reconciliation_task WHERE id = %s", (task_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_recon_task failed: {e}")
        return None


def update_recon_task_status(task_id: int, status: str):
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("UPDATE reconciliation_task SET status = %s WHERE id = %s",
                        (status, task_id))
    except Exception as e:
        logger.error(f"update_recon_task_status failed: {e}")


def update_recon_task_completed(task_id: int, data: dict):
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
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
            """, (
                data.get("status", "completed"),
                data.get("matched_count", 0),
                data.get("mismatched_count", 0),
                data.get("invoice_orphan_count", 0),
                data.get("report_orphan_count", 0),
                data.get("invoice_count_archived", 0),
                data.get("report_row_count", 0),
                task_id,
            ))
    except Exception as e:
        logger.error(f"update_recon_task_completed failed: {e}")


def list_recon_tasks(tenant_id=None, user_id: str = None,
                     client_id: int = None) -> List[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT t.*, c.name AS client_name, c.color AS client_color
                    FROM reconciliation_task t
                    LEFT JOIN clients c ON c.id = t.client_id
                    WHERE t.tenant_id = %s::uuid
                    ORDER BY t.created_at DESC LIMIT 100
                """, (str(tenant_id),))
            else:
                cur.execute("""
                    SELECT t.*, c.name AS client_name, c.color AS client_color
                    FROM reconciliation_task t
                    LEFT JOIN clients c ON c.id = t.client_id
                    WHERE t.user_id = %s::uuid
                    ORDER BY t.created_at DESC LIMIT 100
                """, (str(user_id),))
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
        with get_cursor(commit=True) as cur:
            for r in rows:
                cur.execute("""
                    INSERT INTO reconciliation_row (
                        task_id, invoice_id, report_row_no,
                        pair_confidence, status,
                        diff_fields, diff_categories
                    ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                """, (
                    r["task_id"],
                    str(r["invoice_id"]) if r.get("invoice_id") else None,
                    r.get("report_row_no"),
                    r.get("pair_confidence"),
                    r["status"],
                    _j.dumps(r.get("diff_fields") or {}, ensure_ascii=False, default=str),
                    r.get("diff_categories", ""),
                ))
    except Exception as e:
        logger.error(f"bulk_insert_recon_rows failed: {e}")


def list_recon_rows(task_id: int) -> List[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT r.*,
                       h.invoice_no, h.invoice_date, h.seller_name, h.total_amount,
                       h.filename AS invoice_filename
                FROM reconciliation_row r
                LEFT JOIN ocr_history h ON h.id = r.invoice_id
                WHERE r.task_id = %s
                ORDER BY r.id
            """, (task_id,))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_recon_rows failed: {e}")
        return []


# ── 发票查询(供对账引擎使用)────────────────────────────────

def list_invoices_for_recon(tenant_id=None, client_id: int = None,
                            period_year: int = None,
                            period_month: int = None,
                            source_ref: str = None) -> List[Dict[str, Any]]:
    """
    拉取指定客户 × 纳税期间内已归档发票
    从 ocr_history 顶层字段 + pages[0].fields 提取买方信息
    v118.32.4.3 · source_ref(=task_id 字符串) 传了就只取本次 task 关联的发票
    用于屏 B 流程隔离 · 不传时是屏 A 老逻辑(按客户+期间扫全部历史)
    """
    try:
        with get_cursor() as cur:
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
                base_where += " AND (h.invoice_date IS NULL OR EXTRACT(YEAR FROM h.invoice_date::date) = %s)"
                params.append(period_year)
            elif period_month:
                base_where += " AND (h.invoice_date IS NULL OR EXTRACT(MONTH FROM h.invoice_date::date) = %s)"
                params.append(period_month)

            cur.execute(f"""
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
            """, params)

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
import json

def find_client_by_tax_id(tenant_id, tax_id: str) -> Optional[Dict[str, Any]]:
    """按税号找客户 · 跨 tenant 隔离"""
    if not tax_id:
        return None
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT * FROM clients
                    WHERE tax_id = %s AND tenant_id = %s::uuid
                    LIMIT 1
                """, (tax_id, str(tenant_id)))
            else:
                cur.execute("SELECT * FROM clients WHERE tax_id = %s LIMIT 1", (tax_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"find_client_by_tax_id failed: {e}")
        return None


def auto_create_client(user_id: str, tenant_id, tax_id: str, name: str,
                       color: str = "#3b82f6") -> Optional[int]:
    """v118.32.x · 屏 B 遇到陌生税号自动建客户 · 名字从发票/报告 OCR 出来"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO clients (
                    user_id, tenant_id, name, tax_id, color, is_active, notes
                ) VALUES (%s::uuid, %s, %s, %s, %s, TRUE,
                          'v118.32.x · 自动创建 · 请确认信息')
                RETURNING id
            """, (
                user_id,
                str(tenant_id) if tenant_id else None,
                (name or f"客户 {tax_id[:5]}")[:200],
                tax_id, color,
            ))
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"auto_create_client failed: {e}")
        return None


def get_recon_row(row_id: int) -> Optional[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            cur.execute("""
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
            """, (row_id,))
            row = cur.fetchone()
            if not row:
                return None
            r = dict(row)
            # 把对应的 report row 也提出来
            try:
                if r.get("report_rows") and r.get("report_row_no"):
                    rows = r["report_rows"] if isinstance(r["report_rows"], list) else json.loads(r["report_rows"])
                    matching = next((x for x in rows if x.get("row_no") == r["report_row_no"]), {})
                    r.update({k: v for k, v in matching.items() if k.startswith("report_")})
            except Exception:
                pass
            return r
    except Exception as e:
        logger.error(f"get_recon_row failed: {e}")
        return None


def update_recon_row_ai_analysis(row_id: int, analysis: dict) -> bool:
    import json as _j
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE reconciliation_row
                SET ai_analysis = %s, updated_at = NOW()
                WHERE id = %s
            """, (_j.dumps(analysis, ensure_ascii=False), row_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_recon_row_ai_analysis failed: {e}")
        return False


def update_recon_row_action(row_id: int, action: str, notes: str = "") -> bool:
    """会计师操作:resolved/customer_issue/accepted_diff/pending"""
    if action not in ("pending", "resolved", "customer_issue", "accepted_diff"):
        return False
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE reconciliation_row
                SET accountant_action = %s, notes = %s, updated_at = NOW()
                WHERE id = %s
            """, (action, notes[:500], row_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_recon_row_action failed: {e}")
        return False


def list_recon_rows_detailed(task_id: int) -> List[Dict[str, Any]]:
    """v118.32.x · 拉取完整明细 · 含发票字段 + 报告字段 · 给屏 C 用"""
    import json as _j
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT t.vat_report_id FROM reconciliation_task t WHERE t.id = %s
            """, (task_id,))
            t = cur.fetchone()
            report_rows_map = {}
            if t and t.get("vat_report_id"):
                cur.execute("SELECT parsed_rows FROM vat_report WHERE id = %s", (t["vat_report_id"],))
                vr = cur.fetchone()
                if vr and vr.get("parsed_rows"):
                    rows = vr["parsed_rows"] if isinstance(vr["parsed_rows"], list) else _j.loads(vr["parsed_rows"])
                    report_rows_map = {r.get("row_no"): r for r in rows if isinstance(r, dict)}

            cur.execute("""
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
            """, (task_id,))
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
                    try: d["diff_fields"] = _j.loads(d["diff_fields"])
                    except Exception: d["diff_fields"] = {}
                # ai_analysis jsonb 解开
                if isinstance(d.get("ai_analysis"), str):
                    try: d["ai_analysis"] = _j.loads(d["ai_analysis"])
                    except Exception: pass
                result.append(d)
            return result
    except Exception as e:
        logger.error(f"list_recon_rows_detailed failed: {e}")
        return []


def get_client_by_id(client_id: int) -> Optional[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_client_by_id failed: {e}")
        return None




# ============================================================
# v118.32.2 · VAT 对账增强(只保留新增 · 已有的不复制)
# ============================================================


def find_or_create_client_by_tax_id(user_id: str, tenant_id: Optional[str],
                                     tax_id: str, name: str = "") -> Optional[int]:
    """v118.32.2 · 屏 B 自动建客户:按税号找 · 找不到就建 · 复用 create_client"""
    if not tax_id or len(tax_id) != 13:
        return None
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    "SELECT id FROM clients WHERE tenant_id = %s AND tax_id = %s "
                    "AND is_active = TRUE LIMIT 1",
                    (str(tenant_id), tax_id))
            else:
                cur.execute(
                    "SELECT id FROM clients WHERE user_id = %s AND tax_id = %s "
                    "AND is_active = TRUE LIMIT 1",
                    (str(user_id), tax_id))
            row = cur.fetchone()
            if row:
                return int(row["id"])
    except Exception as e:
        logger.error(f"find_or_create_client_by_tax_id lookup failed: {e}")
        return None

    # 没找到 · 建一个 · 复用现有 create_client
    palette = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899",
               "#14b8a6", "#f97316", "#06b6d4", "#a855f7"]
    color = palette[hash(tax_id) % len(palette)]
    new_id = create_client(
        user_id=str(user_id),
        tenant_id=str(tenant_id) if tenant_id else None,
        name=(name or f"客户 {tax_id[-4:]}"),
        tax_id=tax_id,
        color=color,
    )
    if new_id:
        logger.info(f"[v118.32.2] auto-created client id={new_id} tax_id={tax_id} name={name}")
    return new_id



# ════════════════════════════════════════════════════════════════════════
# v118.32.4.10.0 · vat_recon_tasks · Excel 对账任务持久化
# ════════════════════════════════════════════════════════════════════════

def ensure_vat_recon_tasks_table():
    """幂等建表 · 启动时调用"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vat_recon_tasks (
                    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id       UUID,
                    user_id         UUID NOT NULL,
                    client_name     TEXT,
                    period          TEXT,
                    invoice_count   INTEGER NOT NULL DEFAULT 0,
                    report_count    INTEGER NOT NULL DEFAULT 0,
                    matched         INTEGER NOT NULL DEFAULT 0,
                    mismatched      INTEGER NOT NULL DEFAULT 0,
                    mismatch_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
                    status          TEXT NOT NULL DEFAULT 'done',
                    elapsed_seconds NUMERIC(8,2),
                    excel_path      TEXT,
                    raw_data_json   JSONB,
                    lang            TEXT NOT NULL DEFAULT 'th',
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_vrt_tenant_created
                    ON vat_recon_tasks(tenant_id, created_at DESC)
                    WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_vrt_tenant_period
                    ON vat_recon_tasks(tenant_id, period)
                    WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_vrt_tenant_status
                    ON vat_recon_tasks(tenant_id, status)
                    WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_vrt_user
                    ON vat_recon_tasks(user_id);
            """)
        logger.info("✅ vat_recon_tasks 表已就绪 (v118.32.4.10.0)")
    except Exception as e:
        logger.error(f"ensure_vat_recon_tasks_table failed: {e}")


def create_vat_recon_task(
    tenant_id,
    user_id: str,
    client_name: str,
    period: str,
    invoice_count: int,
    report_count: int,
    matched: int,
    mismatched: int,
    mismatch_amount: float,
    elapsed_seconds: float,
    excel_path,
    raw_data_json,
    lang: str = "th",
):
    """INSERT · 返回新 task UUID"""
    import json as _json
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO vat_recon_tasks
                    (tenant_id, user_id, client_name, period,
                     invoice_count, report_count, matched, mismatched,
                     mismatch_amount, elapsed_seconds, excel_path, raw_data_json, lang)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(tenant_id) if tenant_id else None,
                str(user_id),
                client_name or "",
                period or "",
                invoice_count,
                report_count,
                matched,
                mismatched,
                round(float(mismatch_amount or 0), 2),
                round(float(elapsed_seconds or 0), 2),
                excel_path,
                _json.dumps(raw_data_json, ensure_ascii=False) if raw_data_json else None,
                lang,
            ))
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_vat_recon_task failed: {e}")
        return None


def list_vat_recon_tasks(
    tenant_id,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    status=None,
    period=None,
):
    """列表查询 · 带分页 · tenant 隔离"""
    try:
        where = []
        params = []
        if tenant_id:
            where.append("tenant_id = %s")
            params.append(str(tenant_id))
        else:
            where.append("user_id = %s::uuid")
            params.append(str(user_id))
        if status:
            where.append("status = %s")
            params.append(status)
        if period:
            where.append("period = %s")
            params.append(period)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        offset = (max(page, 1) - 1) * page_size

        with get_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS n FROM vat_recon_tasks {where_sql}", params)
            total = int(cur.fetchone()["n"] or 0)
            cur.execute(f"""
                SELECT id, tenant_id, user_id, client_name, period,
                       invoice_count, report_count, matched, mismatched,
                       mismatch_amount, status, elapsed_seconds, excel_path,
                       lang, created_at, updated_at
                FROM vat_recon_tasks
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            rows = [dict(r) for r in cur.fetchall()]
        return {"rows": rows, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        logger.error(f"list_vat_recon_tasks failed: {e}")
        return {"rows": [], "total": 0, "page": page, "page_size": page_size}


def get_vat_recon_task(task_id: str, tenant_id, user_id: str):
    """单条详情 · 含 raw_data_json · tenant 隔离"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    "SELECT * FROM vat_recon_tasks WHERE id = %s::uuid AND tenant_id = %s",
                    (task_id, str(tenant_id)))
            else:
                cur.execute(
                    "SELECT * FROM vat_recon_tasks WHERE id = %s::uuid AND user_id = %s::uuid",
                    (task_id, str(user_id)))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_vat_recon_task failed: {e}")
        return None


def delete_vat_recon_task(task_id: str, tenant_id, user_id: str):
    """DELETE · 返回 excel_path 供调用方删文件"""
    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    "DELETE FROM vat_recon_tasks WHERE id = %s::uuid AND tenant_id = %s RETURNING excel_path",
                    (task_id, str(tenant_id)))
            else:
                cur.execute(
                    "DELETE FROM vat_recon_tasks WHERE id = %s::uuid AND user_id = %s::uuid RETURNING excel_path",
                    (task_id, str(user_id)))
            row = cur.fetchone()
            return row["excel_path"] if row else None
    except Exception as e:
        logger.error(f"delete_vat_recon_task failed: {e}")
        return None


def delete_vat_recon_tasks_older_than(days: int, tenant_id, user_id: str):
    """删除 days 天前的任务 · tenant 隔离 · 返回 (deleted_count, excel_paths[])"""
    try:
        with get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute("""
                    DELETE FROM vat_recon_tasks
                    WHERE tenant_id = %s
                      AND created_at < NOW() - (%s || ' days')::interval
                    RETURNING excel_path
                """, (str(tenant_id), str(int(days))))
            else:
                cur.execute("""
                    DELETE FROM vat_recon_tasks
                    WHERE user_id = %s::uuid
                      AND created_at < NOW() - (%s || ' days')::interval
                    RETURNING excel_path
                """, (str(user_id), str(int(days))))
            rows = cur.fetchall()
            paths = [r["excel_path"] for r in rows if r.get("excel_path")]
            return len(rows), paths
    except Exception as e:
        logger.error(f"delete_vat_recon_tasks_older_than failed: {e}")
        return 0, []


def get_vat_recon_tasks_kpi(tenant_id, user_id: str):
    """本月 KPI: total / running / done / failed"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())) AS this_month,
                        COUNT(*) FILTER (WHERE status = 'running') AS running,
                        COUNT(*) FILTER (WHERE status = 'done') AS done,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed
                    FROM vat_recon_tasks WHERE tenant_id = %s
                """, (str(tenant_id),))
            else:
                cur.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())) AS this_month,
                        COUNT(*) FILTER (WHERE status = 'running') AS running,
                        COUNT(*) FILTER (WHERE status = 'done') AS done,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed
                    FROM vat_recon_tasks WHERE user_id = %s::uuid
                """, (str(user_id),))
            row = cur.fetchone()
            if row:
                return {k: int(row[k] or 0) for k in ("this_month", "running", "done", "failed")}
            return {"this_month": 0, "running": 0, "done": 0, "failed": 0}
    except Exception as e:
        logger.error(f"get_vat_recon_tasks_kpi failed: {e}")
        return {"this_month": 0, "running": 0, "done": 0, "failed": 0}


# ════════════════════════════════════════════════════════════════════
# v118.32.5 · GL vs 销项税报表 对账（新功能）
# ════════════════════════════════════════════════════════════════════

def ensure_gl_vat_task_table():
    """v118.32.5 · GL对账任务表 · 单表存任务元数据 + 明细JSON + 汇总JSON"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS gl_vat_task (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    gl_filename TEXT,
                    vat_filename TEXT,
                    gl_row_count INT DEFAULT 0,
                    vat_row_count INT DEFAULT 0,
                    matched_count INT DEFAULT 0,
                    unmatched_count INT DEFAULT 0,
                    diff_count INT DEFAULT 0,
                    detail_json JSONB,
                    summary_json JSONB,
                    status TEXT DEFAULT 'done',
                    error TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_gl_vat_task_user ON gl_vat_task(user_id, created_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_gl_vat_task_tenant ON gl_vat_task(tenant_id, created_at DESC)")
        logger.info("[v118.32.5] gl_vat_task 表就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.32.5] gl_vat_task 建表失败: {e}")
        return False


def create_gl_vat_task(
    user_id: str,
    tenant_id,
    gl_filename: str,
    vat_filename: str,
    gl_row_count: int,
    vat_row_count: int,
    detail_json: list,
    summary_json: dict,
    matched_count: int = 0,
    unmatched_count: int = 0,
    diff_count: int = 0,
) -> Optional[int]:
    """落库 GL 对账任务结果 · 返回 task_id"""
    import json as _j
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO gl_vat_task (
                    user_id, tenant_id, gl_filename, vat_filename,
                    gl_row_count, vat_row_count,
                    matched_count, unmatched_count, diff_count,
                    detail_json, summary_json, status
                ) VALUES (
                    %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, 'done'
                )
                RETURNING id
            """, (
                str(user_id),
                str(tenant_id) if tenant_id else None,
                gl_filename, vat_filename,
                int(gl_row_count or 0), int(vat_row_count or 0),
                int(matched_count or 0), int(unmatched_count or 0), int(diff_count or 0),
                _j.dumps(detail_json or [], ensure_ascii=False, default=str),
                _j.dumps(summary_json or {}, ensure_ascii=False, default=str),
            ))
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_gl_vat_task failed: {e}")
        return None


def get_gl_vat_task(task_id: int) -> Optional[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM gl_vat_task WHERE id = %s", (task_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_gl_vat_task failed: {e}")
        return None


def list_gl_vat_tasks(user_id: str, tenant_id=None, limit: int = 50) -> List[Dict[str, Any]]:
    """列出最近的 GL 对账任务（不返回 detail_json/summary_json 减小数据量）"""
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT id, user_id, tenant_id, gl_filename, vat_filename,
                           gl_row_count, vat_row_count,
                           matched_count, unmatched_count, diff_count,
                           status, created_at
                    FROM gl_vat_task
                    WHERE tenant_id = %s::uuid
                    ORDER BY created_at DESC LIMIT %s
                """, (str(tenant_id), int(limit)))
            else:
                cur.execute("""
                    SELECT id, user_id, tenant_id, gl_filename, vat_filename,
                           gl_row_count, vat_row_count,
                           matched_count, unmatched_count, diff_count,
                           status, created_at
                    FROM gl_vat_task
                    WHERE user_id = %s::uuid
                    ORDER BY created_at DESC LIMIT %s
                """, (str(user_id), int(limit)))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_gl_vat_tasks failed: {e}")
        return []


def delete_gl_vat_task(task_id: int, user_id: str) -> bool:
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM gl_vat_task WHERE id = %s AND user_id = %s::uuid",
                (task_id, str(user_id))
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_gl_vat_task failed: {e}")
        return False


# v118.32.5.5.20 · 批量删除 GL 对账任务
def delete_gl_vat_tasks_batch(ids: list, user_id: str) -> int:
    """删除多个 GL 对账任务 · 返回成功删除条数。仅限本人任务。"""
    if not ids:
        return 0
    try:
        clean_ids = [int(i) for i in ids if str(i).isdigit() or isinstance(i, int)]
        if not clean_ids:
            return 0
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM gl_vat_task WHERE id = ANY(%s) AND user_id = %s::uuid",
                (clean_ids, str(user_id))
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.error(f"delete_gl_vat_tasks_batch failed: {e}")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# v118.33.6 · Bank Reconciliation v2 (Statement vs GL)
# ══════════════════════════════════════════════════════════════════════════════

def ensure_bank_recon_v2_table():
    """幂等 DDL · 建 bank_recon_v2_task 表（首次启动时调用）"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bank_recon_v2_task (
                    id          SERIAL PRIMARY KEY,
                    user_id     UUID NOT NULL,
                    tenant_id   UUID,
                    bank_code   TEXT,
                    gl_account  TEXT,
                    stmt_files  TEXT,
                    gl_files    TEXT,
                    stmt_row_count  INTEGER DEFAULT 0,
                    gl_row_count    INTEGER DEFAULT 0,
                    matched_count   INTEGER DEFAULT 0,
                    unmatched_gl    INTEGER DEFAULT 0,
                    unmatched_stmt  INTEGER DEFAULT 0,
                    stmt_opening    NUMERIC(18,2) DEFAULT 0,
                    stmt_closing    NUMERIC(18,2) DEFAULT 0,
                    gl_opening      NUMERIC(18,2) DEFAULT 0,
                    gl_closing      NUMERIC(18,2) DEFAULT 0,
                    formula_diff    NUMERIC(18,2) DEFAULT 0,
                    detail_json     JSONB,
                    summary_json    JSONB,
                    status      TEXT DEFAULT 'done',
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_bank_recon_v2_user
                ON bank_recon_v2_task(user_id, created_at DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_bank_recon_v2_tenant
                ON bank_recon_v2_task(tenant_id, created_at DESC)
                WHERE tenant_id IS NOT NULL
            """)
            logger.info("[v118.33.6] bank_recon_v2_task 表已就绪")
    except Exception as e:
        logger.warning(f"ensure_bank_recon_v2_table failed: {e}")


def create_bank_recon_v2_task(
    user_id: str,
    tenant_id,
    bank_code: str,
    gl_account: str,
    stmt_files: str,
    gl_files: str,
    stmt_row_count: int,
    gl_row_count: int,
    matched_count: int,
    unmatched_gl: int,
    unmatched_stmt: int,
    stmt_opening: float,
    stmt_closing: float,
    gl_opening: float,
    gl_closing: float,
    formula_diff: float,
    detail_json: list,
    summary_json: dict,
) -> Optional[int]:
    import json as _j
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO bank_recon_v2_task (
                    user_id, tenant_id, bank_code, gl_account,
                    stmt_files, gl_files,
                    stmt_row_count, gl_row_count,
                    matched_count, unmatched_gl, unmatched_stmt,
                    stmt_opening, stmt_closing, gl_opening, gl_closing, formula_diff,
                    detail_json, summary_json, status
                ) VALUES (
                    %s::uuid, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, 'done'
                ) RETURNING id
            """, (
                str(user_id),
                str(tenant_id) if tenant_id else None,
                bank_code or "",
                gl_account or "",
                stmt_files or "",
                gl_files or "",
                int(stmt_row_count or 0),
                int(gl_row_count or 0),
                int(matched_count or 0),
                int(unmatched_gl or 0),
                int(unmatched_stmt or 0),
                float(stmt_opening or 0),
                float(stmt_closing or 0),
                float(gl_opening or 0),
                float(gl_closing or 0),
                float(formula_diff or 0),
                _j.dumps(detail_json or [], ensure_ascii=False, default=str),
                _j.dumps(summary_json or {}, ensure_ascii=False, default=str),
            ))
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_bank_recon_v2_task failed: {e}")
        return None


def get_bank_recon_v2_task(task_id: int) -> Optional[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM bank_recon_v2_task WHERE id = %s", (task_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_bank_recon_v2_task failed: {e}")
        return None


def list_bank_recon_v2_tasks(user_id: str, tenant_id=None, limit: int = 50) -> List[Dict[str, Any]]:
    try:
        with get_cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT id, user_id, tenant_id, bank_code, gl_account,
                           stmt_files, gl_files,
                           stmt_row_count, gl_row_count,
                           matched_count, unmatched_gl, unmatched_stmt,
                           stmt_opening, stmt_closing, gl_opening, gl_closing, formula_diff,
                           status, created_at
                    FROM bank_recon_v2_task
                    WHERE tenant_id = %s::uuid
                    ORDER BY created_at DESC LIMIT %s
                """, (str(tenant_id), int(limit)))
            else:
                cur.execute("""
                    SELECT id, user_id, tenant_id, bank_code, gl_account,
                           stmt_files, gl_files,
                           stmt_row_count, gl_row_count,
                           matched_count, unmatched_gl, unmatched_stmt,
                           stmt_opening, stmt_closing, gl_opening, gl_closing, formula_diff,
                           status, created_at
                    FROM bank_recon_v2_task
                    WHERE user_id = %s::uuid
                    ORDER BY created_at DESC LIMIT %s
                """, (str(user_id), int(limit)))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_bank_recon_v2_tasks failed: {e}")
        return []


def delete_bank_recon_v2_task(task_id: int, user_id: str) -> bool:
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM bank_recon_v2_task WHERE id = %s AND user_id = %s::uuid",
                (task_id, str(user_id))
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_bank_recon_v2_task failed: {e}")
        return False


def delete_bank_recon_v2_tasks_batch(ids: list, user_id: str) -> int:
    if not ids:
        return 0
    try:
        clean_ids = [int(i) for i in ids if str(i).isdigit() or isinstance(i, int)]
        if not clean_ids:
            return 0
        with get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM bank_recon_v2_task WHERE id = ANY(%s) AND user_id = %s::uuid",
                (clean_ids, str(user_id))
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.error(f"delete_bank_recon_v2_tasks_batch failed: {e}")
        return 0

