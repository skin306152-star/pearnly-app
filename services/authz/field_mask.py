# -*- coding: utf-8 -*-
"""敏感字段遮蔽(G4 · docs/permissions/07 §四)。

读路径序列化层用:没有 field.cost.view 码的角色,成本/进价列一律返 None(前端显 --),
导出同样走这里。判定只读本请求已缓存的权限快照(require_perm 已解析),不另查库。

收银员令牌进不了报表(require_perm 早拦),故缺快照的唯一情形是超管短路 → 全可见。
"""

from __future__ import annotations

from services.authz.deps import peek_authz


def cost_visible(request) -> bool:
    """本请求主体是否可见成本/进价明文。"""
    authz = peek_authz(request)
    if authz is None:
        return True  # 超管短路不落快照 = 全可见
    return authz.has("field.cost.view")


def payroll_visible(request) -> bool:
    """工资数据可见性(模块待建,占位同源)。"""
    authz = peek_authz(request)
    if authz is None:
        return True
    return authz.has("field.payroll.view")


def mask_fields(obj: dict, fields, *, visible: bool) -> dict:
    """visible=False 时把 obj 中 fields 列就地置 None;visible=True 原样返回。"""
    if visible or not isinstance(obj, dict):
        return obj
    for f in fields:
        if f in obj:
            obj[f] = None
    return obj


def mask_rows(rows, fields, *, visible: bool):
    """对一组 dict 行批量遮蔽(visible=True 时零开销直接返回)。"""
    if visible:
        return rows
    for r in rows:
        mask_fields(r, fields, visible=False)
    return rows
