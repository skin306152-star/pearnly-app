# -*- coding: utf-8 -*-
"""业态预设 — business_type → 该开的模块组合(平台业态套餐 · docs/platform-onboarding/02)。

调用方(注册流默认静默套用 firm / Earn 运营侧开通 POS)调 apply_preset:把 KNOWN_MODULES
7 个模块逐个按预设翻开关(在预设里→开,不在→关),并记录 business_type。只翻 enabled
(config=None),不动既有 config、不建 POS 硬件(终端/收银员/默认仓走 services/pos/onboarding 屏8)。
平台业态自选板块已下架(Zihao 2026-07-11 拍板)——本函数不再由客户自选触发。

注意两层「预设」互不替代:
  - 本模块 = 平台【模块】预设(哪些模块出现)。
  - services/pos/onboarding.BUSINESS_PRESETS = POS【能力块】预设(POS 模块内开哪些行为)。
两者都按 business_type 索引,语义独立。
"""

from __future__ import annotations

from services.modules import store

# business_type → 默认开的 module_key 列表(canonical 6 业态 · 02 表)。
# sales 在所有业态都开(平台主线尖刀)。未列业态拒绝(onboarding 报 unknown_business_type)。
# accounting(自动做账)全业态都开:经营动作即输入是平台主线(docs/product-vision/00)。
#
# pos_only = POS 独立板块商家(Earn 邀请制 · Zihao 2026-07-11 拍板:被邀请即全功能可用,
# 不再有二道开关)。模块集合须覆盖 POS 老板后台壳(src/home/nav-presets.ts POS_PRESET 侧栏
# 白名单)暴露的全部功能——商品/发票(sales)、费用/采购(expense)、库存、收银、
# 无头记账引擎(accounting · 全业态惯例,后台记账不进侧栏)。knowledge/recon/receivable
# 不在壳内,仍不开。不进自助业态选择器(平台业态自选板块已下架)——只走运营侧
# Earn 开通,不给客户自选。
BUSINESS_PRESETS: dict[str, list[str]] = {
    "firm": ["sales", "expense", "recon", "knowledge", "accounting"],
    "retail": ["sales", "inventory", "pos", "accounting"],
    "pharmacy": ["sales", "inventory", "pos", "accounting"],
    "restaurant": ["sales", "inventory", "pos", "accounting"],
    "service": ["sales", "expense", "accounting"],
    "b2b": ["sales", "inventory", "receivable", "expense", "accounting"],
    "pos_only": ["pos", "inventory", "sales", "expense", "accounting"],
}


def is_known(business_type: str) -> bool:
    return business_type in BUSINESS_PRESETS


def _pos_provision_allowed(cur, tenant_id: str) -> bool:
    """PS-3 锁闸放行判据(懒导入避免 presets↔entitlements 循环)。任何异常一律放行:
    锁闸是加限功能,基建抖动绝不该把 pos 从既有客户手里锁没(fail-open · 与钥匙闸相反的安全方向)。"""
    try:
        from services.pos.entitlements import pos_provision_allowed

        return pos_provision_allowed(cur, tenant_id=str(tenant_id))
    except Exception:
        return True


def apply_preset(cur, *, tenant_id: str, business_type: str) -> dict:
    """应用业态预设:7 模块按预设翻开关 + 记录 business_type。

    未知 business_type 抛 ValueError(路由翻 platform.unknown_business_type)。
    只翻 enabled(set_module config=None 保留既有 config)。调用方负责事务(commit)。
    返回 {business_type, modules}(回写后的全模块态)。
    """
    if business_type not in BUSINESS_PRESETS:
        raise ValueError(f"unknown business_type: {business_type}")

    enabled_keys = set(BUSINESS_PRESETS[business_type])
    # PS-3 新租户开通锁闸:闸开且未放行(非存量/无授权/无订阅)时,pos 即便在预设里也不真开
    # (「预备但锁定」)。默认闸关 → pos_provision_allowed 恒 True → 与历史逐字节一致。
    pos_locked = "pos" in enabled_keys and not _pos_provision_allowed(cur, tenant_id)
    for module_key in store.KNOWN_MODULES:
        enabled = module_key in enabled_keys
        if module_key == "pos" and pos_locked:
            enabled = False
        store.set_module(
            cur,
            tenant_id=tenant_id,
            module_key=module_key,
            enabled=enabled,
            config=None,
        )
    store.set_business_type(cur, tenant_id=tenant_id, business_type=business_type)
    # onboarding 完成 → 清「待选业态」标记,前端不再自动弹。
    store.set_needs_onboarding(cur, tenant_id=tenant_id, value=False)

    return {
        "business_type": business_type,
        "modules": store.get_modules(cur, tenant_id=tenant_id),
    }
