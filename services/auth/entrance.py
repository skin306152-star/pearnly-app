# -*- coding: utf-8 -*-
"""登录入口(会话级)准入 —— 「各是各的」的授权判据单一事实源。

一套账号被授权从哪些门登录(main / pos / ai / dms / daily / cowork / erp)。登录时校验「这个门是否在授权集」,
不在即当作账号密码错误拒登(不泄漏账号存在、无「去别处登录」指向文案)。

授权来源(Phase1 从现有数据推导 · Phase2 将换成读 tenant_entrances 表,只改本模块):
  - main  : 业态非 pos_only(会计站自由注册的账号天然是 main;pos_only 是 Earn 直建的纯收银租户)
  - pos   : 开通了 pos 模块(Earn 发放)
  - ai    : 在 pearnly_ai_m1 白名单(Earn 邀请)
  - dms   : 在 dms_portal 白名单(Earn 邀请 · MR.ERP 身份证订车单入口)
  - daily : 在 daily_finance 白名单(Earn 邀请 · 个人周记账应用)
  - cowork: 业态非 pos_only(随 main 同源 · 协同工作台)
  - erp   : 在 erp_portal 白名单(Earn 邀请 · ERP 入口)

超管任意门放行(平台运营);回退闸 entrance_gate 关时一律不拦(上线前/回退=现状,任何门都通);
推导异常默认 fail-open(登录可用性优先,绝不因基建抖动把人锁在门外,与 auth.py 改密比对同款容错)
—— 仅 erp 门 fail-closed:ERP 为对外敏感入口,宁可拦。
"""

from __future__ import annotations

import logging
from typing import Callable, Optional, Set

from fastapi import HTTPException

logger = logging.getLogger(__name__)

MAIN = "main"
POS = "pos"
AI = "ai"
DMS = "dms"
DAILY = "daily"
COWORK = "cowork"
ERP = "erp"
ALL_ENTRANCES = (MAIN, POS, AI, DMS, DAILY, COWORK, ERP)

# 权限码前缀 → 允许的登录入口【集合】(Phase3 API 作用域闸判据,按前缀判而非 URL)。
# 一码可跨多门(业务功能被多个壳共用),故以集合建模;未知/横切中性前缀返 None,由 _check
# 短路放行,否则 /api/me 系列 bootstrap 全崩:
#   - pos = {pos}:收银专属。
#   - tax = {main, ai, cowork}:会计主壳报税中心与 AI SPA 工单都调 tax.*;cowork 随 main;ERP 不碰。
#   - acct/recon = {main, cowork}:做账/对账主壳专属(AI 工单内部对账走 tax.filing.*);ERP 不碰。
#   - stockcard/kb/ar = {main, cowork, erp}:应收/知识库/商品收发存按客户账套出的主壳能力;ERP 获此三前缀。
#   - sales/inv/intake = {main, pos, cowork, erp}:POS 商户也做销售开票 / 盘点 / 收料。
#   - purchase = {main, pos, ai, cowork, erp}:采购/供应商数据跨会计/POS/AI(AI 客户画像也调 purchase.*)。
#   - cowork 与 main 等价:凡原来含 main 的集合都并入 cowork(协同工作台继承会计主壳能力)。
#   - ERP 门仅获 sales/purchase/inv/intake/stockcard/kb/ar 七前缀(erp_portal 邀请业务作用域),
#     不碰 pos/tax/acct/recon;ai/dms/daily 是各自独立门,不在 ERP 派生范围。
_ENTRANCE_BY_PREFIX: dict[str, frozenset[str]] = {
    "pos": frozenset({POS}),
    "tax": frozenset({MAIN, AI, COWORK}),
    "acct": frozenset({MAIN, COWORK}),
    "recon": frozenset({MAIN, COWORK}),
    "stockcard": frozenset({MAIN, COWORK, ERP}),
    "kb": frozenset({MAIN, COWORK, ERP}),
    "ar": frozenset({MAIN, COWORK, ERP}),
    "sales": frozenset({MAIN, POS, COWORK, ERP}),
    "purchase": frozenset(
        {MAIN, POS, AI, COWORK, ERP}
    ),  # AI 客户画像供应商档案(ai-profile.js)也调 purchase.*
    "inv": frozenset({MAIN, POS, COWORK, ERP}),
    "intake": frozenset({MAIN, POS, COWORK, ERP}),
}


# registry 里 module_of=None 的横切中性前缀(未归任何入口 · entrance_of_code 返 None 短路放行)。
# 与 _ENTRANCE_BY_PREFIX 互补:test_entrance_scope 断言 registry 每个码前缀二者必居其一,防新增
# 模块前缀漏分类导致 entrance_of_code 静默 fail-open。仅服务测试断言,不进 entrance_of_code 运行判定。
_NEUTRAL_PREFIXES: frozenset[str] = frozenset(
    {"team", "billing", "ownership", "settings", "audit", "field"}
)


def entrance_of_code(code: str) -> Optional[frozenset[str]]:
    """该权限码允许哪些登录入口(授权入口集合);横切中性码/未知前缀返 None(不归任何入口)。"""
    return _ENTRANCE_BY_PREFIX.get(code.split(".", 1)[0])


def authorized_entrances(tenant_id: Optional[str], user_id: Optional[str]) -> Set[str]:
    """该租户/账号被授权的入口集。Phase2 双轨:显式表 tenant_entrances 有行 → 采信表;
    表未建/该租户无行/任何异常 → 回落 Phase1 推导。

    过渡期设计:prod 不自动跑迁移,tenant_entrances 表暂不存在 → 永远走推导,登录行为与
    Phase1 逐字节一致;prod 手动 alembic upgrade 建表 + scripts/backfill_tenant_entrances.py
    回填后,表侧有行才切表(发放侧注册/开 POS/邀请 AI 也已顺带写表,新数据自然落表)。
    """
    if not tenant_id:
        return {MAIN, COWORK}  # 无租户兜底:与推导口径严格等价(main+cowork)

    table_ents = _entrances_from_table(tenant_id)
    if table_ents:
        return table_ents
    return _derive_entrances(tenant_id, user_id)


def _entrances_from_table(tenant_id: str) -> Set[str]:
    """读显式表;表缺失/无行/异常一律返空集(交由调用方回落推导),绝不因此抛错锁登录。"""
    try:
        from core import db
        from services.auth import entrance_store

        with db.get_cursor() as cur:
            return entrance_store.list_entrances(cur, tenant_id)
    except Exception as e:  # noqa: BLE001 · 表未建(prod 过渡期)/基建抖动 → 静默回落推导
        logger.debug("[entrance] table read miss · fall back to derivation: %s", e)
        return set()


def _derive_entrances(tenant_id: str, user_id: Optional[str]) -> Set[str]:
    """Phase1 推导版:business_type 非 pos_only=main+cowork / pos 模块开=pos / m1 名单=ai /
    dms_portal 名单=dms / daily_finance 名单=daily / erp_portal 名单=erp。"""
    ents: Set[str] = set()
    from core import db
    from services.modules import store

    with db.get_cursor() as cur:
        if store.get_business_type(cur, tenant_id=tenant_id) != "pos_only":
            ents.add(MAIN)
            ents.add(COWORK)  # 协同工作台随 main 同源:非 pos_only 天然拥有
        if store.is_enabled(cur, tenant_id=tenant_id, module_key="pos"):
            ents.add(POS)

    from core.feature_flags import (
        daily_enabled_for,
        dms_portal_enabled_for,
        erp_portal_enabled_for,
        pearnly_ai_m1_enabled_for,
    )

    if pearnly_ai_m1_enabled_for(tenant_id, user_id):
        ents.add(AI)
    if dms_portal_enabled_for(tenant_id, user_id):
        ents.add(DMS)
    if daily_enabled_for(tenant_id, user_id):
        ents.add(DAILY)
    if erp_portal_enabled_for(tenant_id, user_id):
        ents.add(ERP)
    return ents


def require_entrance_api(
    user: dict,
    *,
    gate_fn: Callable[[Optional[str], Optional[str]], bool],
    scope_fn: Callable[[Optional[str]], bool],
    entry: str,
    not_found_detail: str = "not_found",
    push_access_fn: Optional[Callable[[dict], None]] = None,
) -> dict:
    """无码路由的通用入口守卫(dms_routes 与波3 花名册路由共用 · 下沉自 dms_routes._authorize)。

    这些路由无权限码,API 作用域闸(authz/deps 按码前缀判)管不到,故守卫落本地。语义与
    原 dms_routes._authorize 逐字节等价:
      - 超管任意门放行(平台运营);
      - gate_fn(邀请闸)关 → 404(fail-closed 不泄漏功能存在);
      - scope_fn(entrance_api_scope)开且 token.entry != 要求的 entry → 403(别的壳会话打不进);
      - push_access_fn 给出则跑 plan 推送闸。
    gate_fn/scope_fn/push_access_fn 由调用方按各自模块名传入 —— 保留调用方模块上现有单测的
    mock.patch 生效(patch 落调用方模块全局,闭包在此按值收到已 patch 的函数)。
    """
    if user.get("is_super_admin"):
        return user
    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    user_id = str(user["id"]) if user.get("id") else None
    if not gate_fn(tenant_id, user_id):
        raise HTTPException(404, detail=not_found_detail)
    if scope_fn(tenant_id) and user.get("entry") != entry:
        raise HTTPException(403, detail="authz.forbidden")
    if push_access_fn is not None:
        push_access_fn(user)
    return user


def login_entrance_allowed(entry: Optional[str], user: dict) -> bool:
    """登录时校验入口准入。返回 False = 该门未授权(调用方按账号密码错误拒)。"""
    entry = entry or MAIN
    if user.get("is_super_admin"):
        return True  # 超管任意门(落 /admin,不受入口约束)

    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    try:
        from core.feature_flags import entrance_gate_enabled_for

        if not entrance_gate_enabled_for(tenant_id):
            return True  # 闸关 = 不拦(现状:任何门都通)

        user_id = str(user["id"]) if user.get("id") else None
        ents = authorized_entrances(tenant_id, user_id)
        if entry not in ents:
            logger.info(
                "[entrance] deny login · user=%s entry=%s authorized=%s",
                user.get("id"),
                entry,
                sorted(ents),
            )
            return False
        return True
    except (
        Exception
    ) as e:  # noqa: BLE001 · 推导异常默认 fail-open(登录可用性优先),仅 erp 门 fail-closed
        logger.warning(
            "[entrance] gate check error · fail-open (erp fail-closed) entry=%s: %s", entry, e
        )
        return entry != ERP
