# -*- coding: utf-8 -*-
"""操作员花名册编排(波3 · DL-8)。

老板租户下每个操作员 = member 用户 + 自己的 mrerp_dms endpoint(凭据 kms 加密)+ 角色档案行。
现有机制全部复用:erp_endpoints 按 user_id 隔离(每人一条自己的 DMS 连接)、line_dms_bindings
一 user 一 LINE、binding.user_id 天然驱动凭据解析/台账/计费(租户级余额)。本层只负责编排 +
凭据加密 + 事务化/补偿,不新增隔离机制。

返回契约:成功 {"ok": True, ...},失败 {"error": "<code>"}。路由层据 code 映射 HTTP 状态。
"""

from __future__ import annotations

import logging
import secrets
from typing import Optional

from services.dms_roster import advisors, store

logger = logging.getLogger("mr-pilot")

VALID_ROLES = ("sales", "admin")
VALID_STATUS = ("active", "inactive")


def _tenant(owner_user: dict) -> Optional[str]:
    return str(owner_user["tenant_id"]) if owner_user.get("tenant_id") else None


def _dms_endpoint(user_id: str, *, enabled_only: bool) -> Optional[dict]:
    """取某 user 的 mrerp_dms endpoint(enabled_only=True 只认启用的 · 作老板模板用;
    False 含停用的 · 供停用操作员的启停/改配复用)。"""
    from core import db

    for ep in db.list_erp_endpoints(str(user_id)) or []:
        if (ep.get("adapter") or "").strip().lower() != "mrerp_dms":
            continue
        if enabled_only and ep.get("enabled") is False:
            continue
        return ep
    return None


def _encrypt(value: str) -> str:
    from core.kms_helper import encrypt_str

    return encrypt_str(value)


def _clean(value: Optional[str]) -> str:
    return str(value or "").strip()


def _resolve_pin(owner_user: dict, advisor_id: str):
    """请求里的顾问 id → (顾问 {id,name}, 错误码);名字服务端解,不信客户端传的。

    名册取老板端点(操作员端点的主档缓存可能从没暖过),故老板未连 DMS 时连钉都钉不了。
    """
    owner_ep = _dms_endpoint(owner_user["id"], enabled_only=True)
    if not owner_ep:
        return None, "dms_roster.no_endpoint"
    options = advisors.list_options(owner_ep)
    if options is None:
        return None, "dms_roster.advisors_unavailable"
    hit = advisors.pick(options, advisor_id)
    if hit is None:
        return None, "dms_roster.invalid_advisor"
    return hit, None


def list_advisors(owner_user: dict) -> dict:
    """顾问下拉选项。四态靠 ok/code 分:未连 DMS / 取数失败 / 空名册 / 正常。

    不走 {"error": ...} → 4xx 那条路:下拉的失败不是操作失败,前端要按 code 分别指路,
    统一 4xx 只会被吞成一句「加载失败」。
    """
    owner_ep = _dms_endpoint(owner_user["id"], enabled_only=True)
    if not owner_ep:
        return {"ok": False, "code": "no_endpoint", "advisors": []}
    options = advisors.list_options(owner_ep)
    if options is None:
        return {"ok": False, "code": "fetch_failed", "advisors": []}
    return {"ok": True, "advisors": options}


def list_operators(owner_user: dict) -> dict:
    """列表:档案 + 用户名 + LINE 绑定态 + endpoint 配置态(四态诚实由前端按字段渲染)。"""
    tenant_id = _tenant(owner_user)
    if not tenant_id:
        return {"error": "dms_roster.no_tenant"}
    rows = store.list_profiles(tenant_id)
    items = []
    for r in rows:
        bound_at = r.get("bound_at")
        items.append(
            {
                "user_id": str(r["user_id"]),
                "display_name": r.get("display_name") or "",
                "dms_role": r.get("dms_role") or "sales",
                "status": r.get("status") or "active",
                "username": r.get("username") or "",
                "line_bound": bool(r.get("bound_at")),
                "line_display_name": r.get("line_name") or "",
                "line_bound_at": (
                    bound_at.isoformat() if hasattr(bound_at, "isoformat") else bound_at
                ),
                "endpoint_ready": r.get("ep_enabled") is True,
                "can_query_dms": r.get("can_query_dms") is True,
                # 提成归属:空 = 没钉死 = 走自动匹配。id 给编辑弹窗回显当前选中项。
                "advisor_id": r.get("advisor_id") or "",
                "advisor_name": r.get("advisor_name") or "",
            }
        )
    return {"ok": True, "items": items}


def create_operator(
    owner_user: dict,
    *,
    display_name: str,
    dms_username: str,
    dms_password: str,
    dms_role: str,
    dms_advisor_id: Optional[str] = None,
    can_query_dms: bool = False,
) -> dict:
    """建操作员:①老板须已有自己的 mrerp_dms 连接(取模板)②建 member 用户 + 档案(同事务)
    ③给该用户建 mrerp_dms endpoint(凭据加密 · 不写 admin_ 键)。③失败补偿清理 ②,不留半成品。

    dms_advisor_id 可选:给了就在 endpoint 上钉死提成归属(空/缺省 = 走自动匹配)。"""
    tenant_id = _tenant(owner_user)
    if not tenant_id:
        return {"error": "dms_roster.no_tenant"}
    display_name = _clean(display_name)
    dms_username = _clean(dms_username)
    dms_password = str(dms_password or "")
    if not display_name or not dms_username or not dms_password:
        return {"error": "dms_roster.required_fields"}
    if dms_role not in VALID_ROLES:
        return {"error": "dms_roster.invalid_role"}

    template = _dms_endpoint(owner_user["id"], enabled_only=True)
    if not template:
        return {"error": "dms_roster.no_endpoint"}
    tcfg = template.get("config") or {}

    pinned = None
    if _clean(dms_advisor_id):
        pinned, err = _resolve_pin(owner_user, dms_advisor_id)
        if err:  # 归属解不出就别建号:半个操作员比没有更难收拾
            return {"error": err}

    username = "dmsop-" + secrets.token_hex(4)
    op_password = secrets.token_urlsafe(18)  # 随机 · 不回显不外传(操作员只走 LINE)
    try:
        op_user_id = store.create_operator_records(
            tenant_id=tenant_id,
            username=username,
            password=op_password,
            company_name=owner_user.get("company_name"),
            display_name=display_name,
            dms_role=dms_role,
            can_query_dms=bool(can_query_dms),
        )
    except Exception as e:
        logger.error(f"[dms_roster] create user/profile failed: {e}")
        return {"error": "dms_roster.create_failed"}

    config = advisors.merge_into_config(
        {
            "system_url": tcfg.get("system_url"),
            "username_enc": _encrypt(dms_username),
            "password_enc": _encrypt(dms_password),
        },
        pinned,
    )
    from core import db

    ep_id = db.create_erp_endpoint(
        str(op_user_id), "MR.ERP DMS", "mrerp_dms", config, is_default=True, auto_push=False
    )
    if not ep_id:
        store.delete_operator_records(tenant_id=tenant_id, user_id=op_user_id)  # 补偿:不留半成品
        return {"error": "dms_roster.endpoint_failed"}
    return {"ok": True, "user_id": str(op_user_id)}


def _require_profile(owner_user: dict, user_id: str):
    """校验 {user_id} 属本租户且有档案行(防跨租户/防对 owner 自身操作)· 返回 (tenant_id, profile) 或 None。"""
    tenant_id = _tenant(owner_user)
    if not tenant_id:
        return None
    prof = store.get_profile(tenant_id, user_id)
    if not prof:
        return None
    return tenant_id, prof


def update_operator(
    owner_user: dict,
    user_id: str,
    *,
    display_name: Optional[str] = None,
    dms_role: Optional[str] = None,
    dms_username: Optional[str] = None,
    dms_password: Optional[str] = None,
    dms_advisor_id: Optional[str] = None,
    can_query_dms: Optional[bool] = None,
) -> dict:
    """改显示名/角色(档案)+ 换 DMS 账密 + 钉/清提成归属(同一次 endpoint 写)。空字段不动。

    dms_advisor_id:缺省=不动归属,空串=清除钉死回自动匹配,其余按 id 服务端解析。
    校验全部前置:归属 id 非法时档案也不该已经被改了一半。"""
    ctx = _require_profile(owner_user, user_id)
    if not ctx:
        return {"error": "dms_roster.not_found"}
    tenant_id, _prof = ctx

    role = None
    if dms_role is not None:
        if dms_role not in VALID_ROLES:
            return {"error": "dms_roster.invalid_role"}
        role = dms_role
    name = _clean(display_name) if display_name is not None else None
    if display_name is not None and not name:
        return {"error": "dms_roster.required_fields"}

    pinned = None
    if _clean(dms_advisor_id):
        pinned, err = _resolve_pin(owner_user, dms_advisor_id)
        if err:
            return {"error": err}

    if name is not None or role is not None or can_query_dms is not None:
        store.update_profile(
            tenant_id,
            user_id,
            display_name=name,
            dms_role=role,
            can_query_dms=can_query_dms,
        )

    new_user = _clean(dms_username) if dms_username is not None else None
    new_pass = dms_password if dms_password is not None else None
    if new_user or new_pass or dms_advisor_id is not None:
        ep = _dms_endpoint(user_id, enabled_only=False)
        if not ep:
            return {"error": "dms_roster.endpoint_missing"}
        cfg = dict(ep.get("config") or {})
        if new_user:
            cfg["username_enc"] = _encrypt(new_user)
        if new_pass:
            cfg["password_enc"] = _encrypt(new_pass)
        if dms_advisor_id is not None:
            cfg = advisors.merge_into_config(cfg, pinned)
        from core import db

        # update_erp_endpoint 吞异常返 False——不核对就回 ok 会让老板看到「已换密码」的假成功,
        # 而操作员仍拿旧密码推单失败(状态诚实)。
        if not db.update_erp_endpoint(str(user_id), str(ep["id"]), config=cfg):
            return {"error": "dms_roster.endpoint_update_failed"}
    return {"ok": True}


def delete_operator(owner_user: dict, user_id: str) -> dict:
    """删除操作员:解绑 LINE + 作废绑定码 + 禁 endpoint + 删档案 + 置用户停用(member 行保留)。

    次序「先外围后档案」:LINE 解绑/作废码 → endpoint 软禁(不裸 DELETE:erp_push_logs 等外键
    行 + 审计)——ep 不存在则跳过 → 删 dms_operator_profiles 行 → users.is_active=false(行保留)。
    任一步失败如实返错不装成功(解绑失败即中止,绝不留「显示已删除、LINE 还能推单」的假删除)。"""
    ctx = _require_profile(owner_user, user_id)
    if not ctx:
        return {"error": "dms_roster.not_found"}
    tenant_id, _prof = ctx
    uid = str(user_id)

    from services.line_dms import store as line_dms_store

    if not line_dms_store.unbind_by_user(uid):
        return {"error": "dms_roster.delete_failed"}
    if not line_dms_store.void_bind_codes_for_user(uid):
        return {"error": "dms_roster.delete_failed"}

    from core import db

    ep = _dms_endpoint(user_id, enabled_only=False)
    if ep and not db.update_erp_endpoint(uid, str(ep["id"]), enabled=False):
        return {"error": "dms_roster.endpoint_update_failed"}

    if not store.delete_operator_profile(tenant_id=tenant_id, user_id=uid):
        return {"error": "dms_roster.delete_failed"}
    if not store.disable_operator_user(tenant_id=tenant_id, user_id=uid):
        return {"error": "dms_roster.delete_failed"}
    logger.info(f"[dms_roster] delete operator user_id={uid} tenant_id={tenant_id}")
    return {"ok": True}


def set_status(owner_user: dict, user_id: str, status: str) -> dict:
    """停用=endpoint 禁 + 解绑 LINE + 作废未用绑定码;启用=endpoint 启(LINE 需重新发码绑)。

    收权动作先行且逐步核对返回值:endpoint 禁失败即中止报错(绝不出现「显示已停用、
    实际还能推单」);档案状态最后写,写失败异常上抛成 5xx(诚实失败,老板重试即可)。"""
    if status not in VALID_STATUS:
        return {"error": "dms_roster.invalid_status"}
    ctx = _require_profile(owner_user, user_id)
    if not ctx:
        return {"error": "dms_roster.not_found"}
    tenant_id, _prof = ctx

    ep = _dms_endpoint(user_id, enabled_only=False)
    from core import db

    if ep and not db.update_erp_endpoint(str(user_id), str(ep["id"]), enabled=(status == "active")):
        return {"error": "dms_roster.endpoint_update_failed"}
    if status == "inactive":
        from services.line_dms import store as line_dms_store

        line_dms_store.unbind_by_user(str(user_id))
        line_dms_store.void_bind_codes_for_user(str(user_id))
    store.set_profile_status(tenant_id, user_id, status)
    return {"ok": True}


def issue_bind_code(owner_user: dict, user_id: str) -> dict:
    """为某操作员发 LINE 绑定码(复用 line_dms store · 老板逐行发码给该销售)。

    停用的操作员拒发(前端已置灰,这里是 API 层收权闸——停用语义不能被直连 API 绕开)。"""
    ctx = _require_profile(owner_user, user_id)
    if not ctx:
        return {"error": "dms_roster.not_found"}
    tenant_id, prof = ctx
    if (prof.get("status") or "active") != "active":
        return {"error": "dms_roster.inactive"}
    from services.line_dms import store as line_dms_store

    out = line_dms_store.generate_bind_code(tenant_id, user_id)
    if not out:
        return {"error": "dms_roster.bind_code_failed"}
    return {"ok": True, "code": out["code"], "expires_at": out["expires_at"]}
