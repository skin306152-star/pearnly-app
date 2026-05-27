# -*- coding: utf-8 -*-
"""用户级设置/偏好(users 表上的开关与 key)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
覆盖:重复检测开关 dup_check · ERP 自动处理方式 erp_push_mode · 用户自带 Gemini API Key。
所有游标访问走 db.get_cursor(...) · 确保测试可 mock.patch("db.get_cursor")。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional

import db

logger = logging.getLogger(__name__)


def get_user_dup_check_enabled(user_id: str) -> bool:
    """读取用户的重复检测开关(默认 True)"""
    try:
        with db.get_cursor() as cur:
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
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET dup_check_enabled = %s WHERE id = %s", (bool(enabled), user_id)
            )
        return True
    except Exception as e:
        logger.error(f"更新重复检测开关失败: {e}")
        return False


# ── P1b(2026-05-26)· ERP 自动处理方式(账户级默认 · 上传可临时覆盖本批)──
#   smart    = 智能分拣(按发票卖方→账套→ERP 端点 · 新用户默认推荐)
#   fixed    = 固定当前账套(全推 auto_push 端点 · 现行为)
#   ocr_only = 只识别不推送(完全跳过 auto-push)
# mirror dup_check 范式 · 容错读默认 smart。
ERP_PUSH_MODES = ("smart", "fixed", "ocr_only")


def get_erp_push_mode(user_id: str) -> str:
    """读取用户的 ERP 自动处理方式(默认 'smart')。任何异常/缺列 → 'smart'。"""
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT erp_push_mode FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return "smart"
            v = (row.get("erp_push_mode") or "").strip()
            return v if v in ERP_PUSH_MODES else "smart"
    except Exception:
        return "smart"


def set_erp_push_mode(user_id: str, mode: str) -> bool:
    """存 ERP 自动处理方式。非法值拒写(返 False)。"""
    mode = (mode or "").strip()
    if mode not in ERP_PUSH_MODES:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET erp_push_mode = %s WHERE id = %s", (mode, user_id))
        return True
    except Exception as e:
        logger.error(f"更新 ERP 自动处理方式失败: {e}")
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
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET gemini_api_key = %s WHERE id = %s", (val, user_id))
        return True
    except Exception as e:
        logger.error(f"保存 Gemini key 失败: {e}")
        return False


def get_user_gemini_key(user_id: str) -> Optional[str]:
    """读取明文(后端内部用 · 不返回给前端)"""
    try:
        with db.get_cursor() as cur:
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
