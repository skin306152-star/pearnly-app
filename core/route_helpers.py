# -*- coding: utf-8 -*-
"""
Pearnly · 路由公共 helper 模块(REFACTOR-B1 · 2026-05-24 抽出)

把散在 app.py 里、被多个路由组共用的鉴权 / 日志 / 校验 helper 集中到这里 ·
让后续抽 team / history / admin 等 router 时直接 import · 不再各自复制一份。

纯搬家 · 不改业务逻辑 / 返回值 / 异常 code。app.py 与已抽出的
billing_routes / admin_diagnostics_routes 改成从这里 import(去掉各自的拷贝)。

依赖:
  - db.*(insert_operation_log / create_tenant / get_cursor)
  - auth.get_current_user_from_request
  不 import app.py · 防循环 import。

覆盖:
  _tid                       · 取 user 的 tenant_id 字符串(多租户共享过滤)
  _require_super_admin       · 超管守门(非超管 403 · 平台层 · 不走 require_perm)
  _log_op                    · 写操作日志便捷函数
  _get_client_ip             · 从 X-Forwarded-For / client.host 取真实 IP
  _check_password_strength   · 密码强度校验(返 None 通过 / code 拒绝)
  _WEAK_PASSWORDS            · 常见弱密码黑名单
  _tid                       · 取 user tenant_id(2026-05-25 第十七会话搬入)
  _plan_permissions          · plan 权限(扁平化全开 · 2026-05-25 搬入)
  _record_500 / _read_last_500 / _last_500_event · 最近 500 现场摘要(共享状态 · 2026-05-25 搬入)
  authorize_pearnly_ai / assert_owns_workspace · pearnly_ai_m1 闸群共享鉴权(workorder_routes /
  tax_profile_routes 曾字节级复制各一份 · 2026-07-10 批次 B simplify 收敛)
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional
from urllib.parse import quote

import psycopg2
from fastapi import HTTPException, Request, status

from core import db
from core.auth import get_current_user_from_request
from core.feature_flags import pearnly_ai_m1_enabled_for
from services.authz.deps import check_workspace_scope, require_perm

logger = logging.getLogger("mr-pilot")


def content_disposition(filename: str, fallback: str) -> str:
    """泰文原名走 RFC 5987 filename*(HTTP 头只认 latin-1,裸塞泰文会 500),
    ASCII 兜底名给不认 filename* 的老客户端——fileconv_routes / payroll_routes /
    vat_excel_routes 曾各自维护字节级相同的实现(2026-07-13 simplify 收敛于此)。"""
    encoded = quote(filename.encode("utf-8"))
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"


_LANGS = ("th", "zh", "en", "ja")


def lang_or_default(lang) -> str:
    """?lang= 查询参归一:四语白名单,兜底 th(用户主力语)。fileconv_routes /
    accounting_books_routes 曾各自维护逐字节相同的实现(2026-07-13 simplify 收敛于此)。"""
    return lang if lang in _LANGS else "th"


@contextmanager
def translate_unique_violation(code: str):
    """把 DB 唯一约束冲突翻成干净 409(而非裸 500)。

    面向用户的创建/改名接口在写 DB 那段包一层:用户重复输入唯一键(商品编码/规则主题等)
    本是可预期的客户端错误,该回 409 + 明确码,不该 500。务必包在打开事务的游标块内,
    让 UniqueViolation 先在此翻成 HTTPException,再由 get_cursor_rls 回滚已 abort 的事务。
    """
    try:
        yield
    except psycopg2.errors.UniqueViolation as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=code) from exc


def _require_super_admin(request: Request) -> Dict[str, Any]:
    """超级管理员守门员 · 非超管 403"""
    user = get_current_user_from_request(request)
    if not user.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin.not_super_admin",
        )
    return user


def _tid(user: dict) -> Optional[str]:
    """v118.14 · 多租户共享:返回用户的 tenant_id 字符串(用于 db 函数过滤同 tenant 数据)
    给 list_ocr_history / get_ocr_history_detail / find_ocr_by_hash 等的 tenant_id 参数使用
    传了 → 同 tenant 所有成员共享数据(老板看员工的发票)
    没传 / NULL → fallback 单 user 老逻辑(向前兼容)

    REFACTOR-B1(2026-05-25):从 app.py 搬到 route_helpers ·
    让 categories / connectors-status 等 router 抽出时可直接 import · 不再绑 app.py。
    """
    if not user:
        return None
    tid = user.get("tenant_id")
    return str(tid) if tid else None


def _get_client_ip(request):
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


def _log_op(
    request: Request, user, action, target_type=None, target_id=None, target_name=None, details=None
):
    """记操作日志的便捷函数"""
    try:
        db.insert_operation_log(
            tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
            actor_user_id=str(user["id"]),
            actor_username=user.get("username"),
            actor_is_super=bool(user.get("is_super_admin")),
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            details=details,
            ip=_get_client_ip(request),
            ua=request.headers.get("User-Agent", "")[:300],
        )
    except Exception as e:
        logger.warning(f"_log_op failed: {e}")


_WEAK_PASSWORDS = {
    "111111",
    "112233",
    "121212",
    "123123",
    "123321",
    "123456",
    "1234567",
    "12345678",
    "123456789",
    "1234567890",
    "131313",
    "147258",
    "159753",
    "654321",
    "666666",
    "888888",
    "987654",
    "abc123",
    "abcd1234",
    "admin",
    "admin123",
    "iloveyou",
    "letmein",
    "monkey",
    "password",
    "password1",
    "password123",
    "qazwsx",
    "qwerty",
    "qwerty123",
    "qwertyuiop",
    "welcome",
    "zxcvbnm",
}


def _plan_permissions(plan: str = None) -> dict:
    """
    v0.15 · 彻底扁平化 · 不再有套餐概念
    所有用户功能完全一样 · 配额由 user.monthly_quota 单独控制
    plan 参数保留仅为兼容 · 忽略其值 · 永远返回全开权限

    REFACTOR-B1(2026-05-25):从 app.py 搬到 route_helpers ·
    让 rd / archive / history 等 router 抽出时可直接 import · 不再绑 app.py。
    """
    return {
        # 这里的 monthly_quota 是 "权限层默认值" · 实际配额以 user.monthly_quota 为准
        # 下游代码应读 user.monthly_quota · 而不是 perms["monthly_quota"]
        "monthly_quota": None,  # 权限层不限 · 实际配额看 user
        "max_pages_per_upload": 50,
        "max_file_size_mb": 100,
        "can_edit_fields": True,
        "can_verify_tax": True,
        "rd_daily_limit": None,
        "can_extract_items": True,
        "can_view_history": True,
        "history_retention_days": 365,
        "can_push_erp": True,
        "can_auto_push_erp": True,
        "endpoints_limit": -1,
        "can_archive": True,
        "can_customize_archive": True,
        "zip_batch_limit": -1,
        "can_use_email_ingest": True,
        "can_use_folder_watch": True,
        "can_use_smart_alert": True,
        "can_use_custom_template": True,
        "custom_template_limit": -1,
        "typhoon_quota_monthly": 500,
        "can_manage_api_keys": True,
        "can_auto_classify": True,
        "can_duplicate_detect": True,
        "can_ai_query": True,
        "can_voucher_draft": True,
    }


def _check_password_strength(password: str) -> Optional[str]:
    """
    返回 None 表示通过 · 返回错误 code 表示拒绝
    code: pwd.too_short / pwd.too_weak_numeric / pwd.too_weak_common / pwd.too_weak
    """
    if not password or len(password) < 8:
        return "pwd.too_short"
    if password.lower() in _WEAK_PASSWORDS:
        return "pwd.too_weak_common"
    if password.isdigit():
        return "pwd.too_weak_numeric"
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        return "pwd.too_weak"
    return None


# v118.34.13 (Zihao 2026-05-19 拍板) · 最近 500 错误的现场摘要 ·
# 通过 /api/version 直接读 · 用户不用 SSH 看 journalctl 也能拿到根因。
# 内容控制在 1500 字符内,堆栈尾巴优先(异常点附近)。
# REFACTOR-B1(2026-05-25):从 app.py 搬来 · app.py(全局异常处理器)、erp_routes
# (endpoints 创建/更新 500 兜底)、admin_diagnostics_routes(读 last_500)共享同一
# _last_500_event 状态 → 必须单一来源,不能各持副本。
_last_500_event: Dict[str, Any] = {}


def _record_500(*, path: str = "", method: str = "", detail: str = ""):
    """Capture the current traceback (if any) + request context into the
    module-level snapshot that /api/version surfaces. Safe to call from
    anywhere — uses sys.exc_info() to grab the active traceback, falls
    back to a synthetic message when no exception is in flight."""
    import sys as _sys
    import time as _t
    import traceback as _tb

    tb_str = ""
    exc_type = ""
    try:
        et, ev, etb = _sys.exc_info()
        if et is not None and ev is not None:
            exc_type = et.__name__
            tb_str = "".join(_tb.format_exception(et, ev, etb))
    except Exception:
        pass
    if not tb_str and detail:
        tb_str = f"(no traceback) {detail}"
    # Trim to last 1500 chars — the tail is where the actual error is.
    _last_500_event.clear()
    _last_500_event.update(
        {
            "ts": int(_t.time()),
            "path": str(path or "")[:200],
            "method": str(method or "")[:10],
            "detail": str(detail or "")[:200],
            "exc_type": exc_type,
            "traceback": (tb_str or "")[-1500:],
        }
    )


def _read_last_500() -> Dict[str, Any]:
    """Snapshot copy of the last captured 500 event."""
    if not _last_500_event:
        return {}
    return dict(_last_500_event)


def authorize_pearnly_ai(request: Request, perm: str, *, not_found: str) -> tuple:
    """pearnly_ai_m1 闸群共享鉴权:登录 + M1 闸(关→404 fail-closed)+ 动作权限。
    返回 (user, tenant_id)。

    workorder_routes 与 tax_profile_routes 曾各自维护一份字节级相同的 `_authorize`
    (2026-07-10 批次 B simplify 收敛于此)。not_found 文案两路由组不同(workorder.
    not_found / workspace.not_found),调用方各传各的,行为不变。
    """
    user = get_current_user_from_request(request)
    tenant_id = _tid(user)
    if not pearnly_ai_m1_enabled_for(tenant_id, str(user["id"])):
        raise HTTPException(404, detail=not_found)
    require_perm(request, perm)
    if not tenant_id:
        raise HTTPException(403, detail="authz.forbidden")
    return user, tenant_id


def assert_owns_workspace(
    cur, request: Request, user: dict, tenant_id: str, ws_id: int, *, not_found: str
) -> None:
    """越权/不存在的账套主体一律 404(不泄漏存在性)。workorder_routes / tax_profile_routes
    共用(2026-07-10 批次 B simplify 收敛),not_found 文案调用方各传各的。"""
    cur.execute(
        "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (ws_id, tenant_id),
    )
    if not cur.fetchone():
        raise HTTPException(404, detail=not_found)
    check_workspace_scope(request, user, ws_id)
