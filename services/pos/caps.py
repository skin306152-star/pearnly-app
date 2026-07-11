# -*- coding: utf-8 -*-
"""收银员按人权限(caps)语义 + 解析(PC-1a · docs/pos/05 §1)。

授权单一事实源:收银员绑主账号(pos_cashiers.user_id 非空)→ caps 由该主账号 RBAC 生效码集
换算(持 pos.refund.approve/admin.manage 的老板店长 = 全放开、无上限),本人 caps 列忽略;纯
收银员(未绑)→ 读本人 caps 列并按最严默认补齐缺键。前台令牌不自持权限,caps 列只是纯收银员
这一类的载体。所有默认取最严(fail-closed):缺列/坏值/跨租户绑定一律回落最小权限。
"""

from __future__ import annotations

import json
from typing import Any, Optional

from services.authz.resolver import resolve

# caps 键 → 最严默认(缺键/未知键/坏值一律回落到此)
CAP_DEFAULTS: dict[str, Any] = {
    "discount_limit_pct": 0,
    "can_refund": False,
    "can_void": False,
    "can_override_price": False,
    "cost_visible": False,
}

# 绑主账号的授权人持这两码之一 = 全权(店长/老板),无上限
_FULL_CODES = ("pos.refund.approve", "pos.admin.manage")

_FULL_CAPS: dict[str, Any] = {
    "discount_limit_pct": 100,
    "can_refund": True,
    "can_void": True,
    "can_override_price": True,
    "cost_visible": True,
}

_BOOL_KEYS = ("can_refund", "can_void", "can_override_price", "cost_visible")


def full_caps() -> dict:
    return dict(_FULL_CAPS)


def _coerce_dict(raw: Any) -> dict:
    """jsonb 回读可能是 dict(RealDictCursor 已解析)或字符串;坏值回空 dict。"""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _clamp_pct(v: Any) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, n))


def merge_defaults(raw: Any) -> dict:
    """原始 caps(dict/str/None)→ 补齐缺键并规整类型的完整 caps。未知键丢弃。"""
    parsed = _coerce_dict(raw)
    out = dict(CAP_DEFAULTS)
    if "discount_limit_pct" in parsed:
        out["discount_limit_pct"] = _clamp_pct(parsed["discount_limit_pct"])
    for k in _BOOL_KEYS:
        if k in parsed:
            out[k] = bool(parsed[k])
    return out


def sanitize_caps(raw: Any) -> dict:
    """后台写入前的白名单 + 类型校验。未知键 / pct 越界 → ValueError(路由译成 4xx)。

    只允许 CAP_DEFAULTS 的键;pct 限 0–100 的整数;其余键强制布尔。返回可直接落库的 caps。
    """
    if not isinstance(raw, dict):
        raise ValueError("caps must be an object")
    unknown = set(raw) - set(CAP_DEFAULTS)
    if unknown:
        raise ValueError(f"unknown cap keys: {sorted(unknown)}")
    out: dict[str, Any] = {}
    if "discount_limit_pct" in raw:
        v = raw["discount_limit_pct"]
        if isinstance(v, bool) or not isinstance(v, int) or not (0 <= v <= 100):
            raise ValueError("discount_limit_pct must be an int in 0..100")
        out["discount_limit_pct"] = v
    for k in _BOOL_KEYS:
        if k in raw:
            if not isinstance(raw[k], bool):
                raise ValueError(f"{k} must be a boolean")
            out[k] = raw[k]
    return merge_defaults(out)


def load_user_min(cur, tenant_id: str, user_id: str) -> Optional[dict]:
    """按 (id, tenant) 取主账号最小字段(RBAC 解析 + 超管短路用)。跨租户取不到 → None。"""
    cur.execute(
        "SELECT id, role, tenant_id, invited_by, "
        "COALESCE(is_super_admin, FALSE) AS is_super_admin "
        "FROM users WHERE id = %s AND tenant_id = %s",
        (str(user_id), str(tenant_id)),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _caps_from_authz(authz) -> dict:
    """RBAC 生效码集 → caps。全权码 = 全放开;否则仅成本可见随 field.cost.view。"""
    if any(authz.has(c) for c in _FULL_CODES):
        return dict(_FULL_CAPS)
    return {
        "discount_limit_pct": 0,
        "can_refund": False,
        "can_void": False,
        "can_override_price": False,
        "cost_visible": authz.has("field.cost.view"),
    }


def resolve_caps(cur, tenant_id: str, subject: Any) -> dict:
    """subject 的生效 caps(单一事实源)。

    subject = pos_cashiers 行(含 caps 列)时:绑主账号 → 用其 RBAC 换算;未绑 → 读 caps 列。
    subject = 主账号 user dict(老板切到收银台,无 caps 列)时:直接按其 RBAC 换算。
    """
    if not isinstance(subject, dict):
        return dict(CAP_DEFAULTS)
    if subject.get("is_super_admin"):
        return dict(_FULL_CAPS)
    if "caps" in subject:  # pos_cashiers 行
        user_id = subject.get("user_id")
        if not user_id:
            return merge_defaults(subject.get("caps"))
        u = load_user_min(cur, tenant_id, str(user_id))
        if not u:
            return dict(CAP_DEFAULTS)  # 绑了却跨租户/已删 → 最严
        if u.get("is_super_admin"):
            return dict(_FULL_CAPS)
        return _caps_from_authz(resolve(u, cur=cur))
    return _caps_from_authz(resolve(subject, cur=cur))


def operator_caps(cur, *, user: dict, tenant_id: str, workspace_client_id: int) -> dict:
    """收银前台操作者的生效 caps。收银员令牌 → 载入其 pos_cashiers 行再解析;主账号 → 按 RBAC。"""
    from services.pos import cashier as cashier_dal

    if user.get("role") == "cashier":
        cid = user.get("cashier_id")
        if not cid:
            return dict(CAP_DEFAULTS)
        row = cashier_dal.get_cashier(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, cashier_id=cid
        )
        if not row:
            return dict(CAP_DEFAULTS)
        return resolve_caps(cur, tenant_id, dict(row))
    return resolve_caps(cur, tenant_id, user)
