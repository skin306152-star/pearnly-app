# -*- coding: utf-8 -*-
"""应用层 feature flags，默认 fail-closed。"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# M1 客户建档收严子闸(B2 · 见 L2-验收.md 真语料坐实):默认关。关 → 建档/编辑校验
# 现状逐字节不变;开 → 建档强收泰文注册名(OCR 方向判定的名称锚),编辑不许清空
# 已登记的泰文名。判定域 = 账套主体归属(有 tenant_id 走 tenant 共享闸 · 个人套账退回
# user_id · 与 workspace_clients 其余隔离口径一致),不是单个用户。
PEARNLY_AI_M1_KEY = "pearnly_ai_m1"
# DMS 订车单入口邀请闸(MR.ERP 身份证→客户库 · 照 pearnly_ai_m1 邀请制范式):默认关
# fail-closed。关 = /dms 门不授权(登录准入推导不含 dms)、/api/dms/* 四端点 404;开 = 被邀请
# 租户从 /dms 门登录得该入口 + 四端点放行。判定域=账套主体归属(有 tenant_id 走 tenant 共享闸,
# 个人套账退回 user_id · 与 pearnly_ai_m1 同口径)。消费在 services/auth/entrance._derive_entrances
# (登录准入)与 routes/dms_routes._authorize(API 守卫)。
DMS_PORTAL_KEY = "dms_portal"
# ERP 入口邀请闸:名单成员即开,不叠加总闸;邀请/收回是超管后台唯一写入口。
# 判定域=账套主体归属(tenant_id 用 tenant · 个人套账退回 user_id),与 Daily 一致。
ERP_PORTAL_KEY = "erp_portal"
# DMS LINE 通道邀请闸(独立 LINE OA · 经销商销售员绑定/会话):默认关 fail-closed。
# 关 = /api/line/dms/webhook 收到事件一律 200 静默零回复、DMS 侧 /api/dms/line/* 绑定端点
# 判定域内不放行(现状零变化,老会计站 OA 逐字节不受影响);开 = 被邀请租户可从 DMS LINE OA
# 绑定 + 收发。判定域=账套主体归属(有 tenant_id 走 tenant · 个人套账退回 user_id),与
# dms_portal 同口径。消费在 routes/line_dms_webhook_routes(webhook)与 routes/dms_routes(DMS 闸)。
DMS_LINE_KEY = "dms_line"
# Daily 周记账入口邀请闸(个人收入/支出记录应用 · pearnly.com/daily):名单成员即开,
# 不走总闸灰度(2026-08-15 Zihao 拍板:邀请即用,不搞「总闸+名单」两段式——邀请/收回
# 是名单唯一写入口,超管后台独占,名单本身可信)。判定域=账套主体归属(有 tenant_id 走
# tenant 共享闸 · 个人套账退回 user_id · 与 pearnly_ai_m1 同口径)。消费在
# services/auth/entrance._derive_entrances(登录准入)与 routes/daily_routes._authorize(API 守卫)。
DAILY_KEY = "daily_finance"
# POS 退货/作废店长授权闸(PS-1 · 防内盗):默认关。关 → 退货/作废路由逐字节走历史
# (任何持效 POS 令牌的收银员都能退,现网 metta 行为不变);开 → 操作者须持 pos.refund.approve,
# 收银员无此码 → 必须店长 PIN 覆盖(校验店长确有该码)才放行,并把授权人写进审计。
# 按账套主体(tenant)判定 —— 一家店整体开/关,与操作的收银员是谁无关。
POS_REFUND_APPROVAL_KEY = "pos_refund_approval"
# POS 收银员按人权限(caps)闸(PC-1a · 防内盗):默认关。关 → 建单折扣/改价逐字节走历史
# (任何收银员任意折扣/改价,现网行为不变);开 → 按操作者 caps 卡折扣上限/改价,超限须店长
# PIN 覆盖(校验店长全权账号)并写审计。按账套主体(tenant)判定,一家店整体开/关。
POS_CASHIER_CAPS_KEY = "pos_cashier_caps"
# POS 新租户开通锁闸(PS-3 · 灰度闸后默认关):默认关 → 现网零变化(apply_preset 照旧开 pos)。
# 开 → 新注册租户业态即便选出 pos 模块也「预备但锁定」(apply_preset 不真开 pos),须持
# pos_entitlement 或有效订阅才放行;存量租户(建租户时间早于本闸开启时刻)永久豁免。
# 按 tenant 判定(与 pos_refund_approval 同款,tenant_id 当作灰度主体)· 消费在
# services/pos/entitlements.pos_provision_allowed。
POS_PROVISION_LOCK_KEY = "pos_provision_lock"
# 工单四权分立 SoD 强制闸(C3 · 多角色审批):默认关。关 = 分权判定整体跳过,现状单人流
# 不变(一人所全兼:开单/裁决/复核/冻结/回执全程无阻,与 pos_refund_approval 同款 fail-closed)。
# 开(事务所)= 强制复核签批人∉制单集、冻结授权人∉制单集且须已有有效复核在场。按 tenant
# 判定(单所整体开/关);消费在 services/workorder/sod.py。
PEARNLY_AI_SOD_KEY = "pearnly_ai_sod"
# 工单银行对账逐笔真对平闸(E1 · 佐证层):默认关 fail-closed。关 = reconcile 步 R3 逐字节
# 维持现状(只判 bank_statement 材料存在性,不跑对平);开 = 有 bank_statement 件时,把流水
# 与工单事件流的票据逐笔打分对平,产出缺票/未达两张清单进 R3 gate + 证据链(不 stuck、不阻断
# package——银行对账是佐证层,税额来自 R1/R2 不来自它)。按 tenant 判定(单所整体开/关,与
# pearnly_ai_sod 同款);消费在 services/workorder/steps/reconcile.py。
PEARNLY_AI_BANK_RECON_KEY = "pearnly_ai_bank_recon"
# 工单影子底稿闸(F1 · 佐证层):默认关 fail-closed。关 = reconcile 步逐字节维持现状
# (gates 无 r5_shadow 键);开 = R4 试算平衡通过后,把已裁的进项分录 + 聚合销项过纯函数复式
# 规则引擎,产出建议分录/科目余额/试算平衡三样影子底稿挂进 r5_shadow(不 stuck、不阻断
# package——影子只算不落法定表)。按 tenant 判定(单所整体开/关,与 pearnly_ai_bank_recon 同款);
# 消费在 services/workorder/steps/reconcile.py。
PEARNLY_AI_SHADOW_DRAFT_KEY = "pearnly_ai_shadow_draft"
# 银行流水倒推销项建议闸(SA-3a · 建议层):默认关 fail-closed。关 = order_detail 无
# bank_sales_suggestion 键、bank-sales/run·decide 端点 404、倒推引擎不跑,现有人工填销项路径
# 逐字节不变;开 = 从工单事件流的银行流水行倒推销项建议(逐行销售/非销售/待定分类 + 含税
# 合计 ÷1.07 税前销售额/VAT · 只建议不落申报数,人在环)。钱数只由确定性代码算,大脑只判
# 「这行是不是销售」。按 tenant 判定(单所整体开/关,与 pearnly_ai_shadow_draft 同款);消费在
# services/workorder/steps/bank_sales_suggest.py(引擎/投影)+ bank_sales_brain.py(大脑分类)。
PEARNLY_AI_BANK_SALES_SUGGEST_KEY = "pearnly_ai_bank_sales_suggest"
# 对账单续页回收闸(SA3R-a · 分类正确性修复):默认关 fail-closed。关 = classify 归堆逐字节
# 维持现状(被 OCR 误判 payment_evidence 的对账单续页照旧踢 non_tax);开 = 命中银行名且命中
# 对账单标题白名单的续页救回 bank_statement(收窄双条件,真付款截图不误吸)。与 SA-3 倒推建议
# 闸(pearnly_ai_bank_sales_suggest)分开控——回收是分类层修复,金标过验后独立放量。按 tenant
# 判定(单所整体开/关,与 pearnly_ai_bank_recon 同款);消费在
# services/workorder/steps/classify.py(传 stmt_regroup 给 sort.bin_ocr_fields)。
PEARNLY_AI_STMT_REGROUP_KEY = "pearnly_ai_stmt_regroup"
# 工单大脑影子闸(裁决预判/审核建议 · brain_shadow):默认关 fail-closed。关 = run_shadow
# 直接 no-op(零构题/零网关调用/零落库,零支出);开 = 对 flagged 未裁项影子出建议,唯一
# 落点 brain_shadow_log(只建议不落账,业务表写路径 grep 为零)。按 tenant 判定(单所整体
# 开/关,与 pearnly_ai_shadow_draft 同款);消费在 services/workorder/brain_shadow.py。
PEARNLY_AI_BRAIN_SHADOW_KEY = "pearnly_ai_brain_shadow"
# 登录入口准入门(各是各的)· 回退开关。关 = 不拦,任何门都通(上线前/回退=现状);
# 开 = 未被授权该入口的账号从该门登录,按账号密码错误拒登。按 tenant 判定。测稳后 rollout=all。
ENTRANCE_GATE_KEY = "entrance_gate"
# 入口级 API 纵深隔离闸(Phase3)· 与登录准入(entrance_gate)分开控,各自独立放量。关 = API
# 不按 token.entry 卡作用域(现状);开 = token.entry 不在码允许入口集则拒(403/PosError)。
# 按 tenant 判定;消费在 services/authz/deps._entrance_scope_deny。默认关,测稳后 rollout=all。
ENTRANCE_API_SCOPE_KEY = "entrance_api_scope"
# 目标驱动前门闸(FD-0 · 万能投料口):默认关 fail-closed。关 = /api/ai/front-desk/* 四端点
# 一律 404、#/desk 不渲染(/ai 与今天逐字节一致);开 = 前门总台生效(草稿合同/盘点/确认开工单)。
# 双闸:pearnly_ai_m1 在场才有效。按 tenant 判定;
# 消费在 routes/front_desk_routes.py。默认关,测稳后 rollout=all。
PEARNLY_AI_FRONT_DESK_KEY = "pearnly_ai_front_desk"
# 智能管家闸(B2-M1 · /ai 顶部对话入口):默认关 fail-closed。关 = /api/ai/steward/* 五端点
# 一律 404(status 探针除外,它回 {enabled:false} 供前端三态挂载)、管家页不渲染;开 = 用户
# 一句话派工具查数(M1 全只读:查询/汇总/深链,写与授权卡归 B3)。双闸:pearnly_ai_m1 在场
# 才有效(组合闸,同 pearnly_ai_front_desk 先例)。按 tenant 判定;消费在 routes/steward_routes.py。
PEARNLY_AI_STEWARD_KEY = "pearnly_ai_steward"
# 管家大脑循环闸(B6 · 一条消息可串多个工具):默认关 fail-closed。
# 关 = 逐字节走 B3 的单次意图分类路(一次模型调用挑一个工具),线上行为零变化;
# 开 = 大脑在 worker 里循环(观测 → 下一步),步骤流水逐条落库,写动作照旧停在授权卡上。
# 双闸:pearnly_ai_steward 在场才有效。按 tenant 判定;消费在 services/steward/brain_entry.py。
STEWARD_BRAIN_LOOP_KEY = "steward_brain_loop"


def _enabled(key: str, user_id: Optional[str], label: str) -> bool:
    """钥匙闸统一读法:任何异常一律 fail-closed 回 False(安全阀,绝不因基建抖动误放)。"""
    try:
        from services.platform_settings import store

        return store.is_enabled_for_user(key, user_id)
    except Exception as e:
        logger.warning(f"{label} fail-closed: {e}")
        return False


def _allowlisted(key: str, subject_id: Optional[str], label: str) -> bool:
    """邀请制直判:名单是授权事实,读取异常 fail-closed。"""
    if not subject_id:
        return False
    try:
        from services.platform_settings import store

        return store.is_allowlisted(key, subject_id)
    except Exception as e:
        logger.warning(f"{label} fail-closed: {e}")
        return False


def pearnly_ai_m1_enabled_for(tenant_id: Optional[str], user_id: Optional[str]) -> bool:
    """M1 客户建档收严子闸。关 = 建档/编辑校验现状不变。

    按账套主体归属判定,不按单个操作人:有 tenant_id 用 tenant(团队共享同一开关
    状态,跟其余 workspace_clients 隔离口径一致);个人套账(无 tenant)退回 user_id。
    """
    return _enabled(PEARNLY_AI_M1_KEY, tenant_id or user_id, "pearnly_ai_m1_enabled_for")


def dms_portal_enabled_for(tenant_id: Optional[str], user_id: Optional[str]) -> bool:
    """DMS 订车单入口邀请闸。关 = /dms 门不授权、四端点 404(现状零变化)。

    按账套主体归属判定(有 tenant_id 用 tenant · 个人套账退回 user_id),与 pearnly_ai_m1 同口径。
    """
    return _enabled(DMS_PORTAL_KEY, tenant_id or user_id, "dms_portal_enabled_for")


def erp_portal_enabled_for(tenant_id: Optional[str], user_id: Optional[str]) -> bool:
    """ERP 邀请制直判:名单是授权事实,不叠加 platform_settings.enabled 总闸。"""
    return _allowlisted(ERP_PORTAL_KEY, tenant_id or user_id, "erp_portal_enabled_for")


def daily_enabled_for(tenant_id: Optional[str], user_id: Optional[str]) -> bool:
    """Daily 邀请制直判:名单成员即开,判定域为 tenant_id 或个人 user_id。"""
    return _allowlisted(DAILY_KEY, tenant_id or user_id, "daily_enabled_for")


def dms_line_enabled_for(tenant_id: Optional[str], user_id: Optional[str]) -> bool:
    """DMS LINE 通道邀请闸。关 = webhook 静默 200、绑定端点不放行(现状零变化)。

    按账套主体归属判定(有 tenant_id 用 tenant · 个人套账退回 user_id),与 dms_portal 同口径。
    """
    return _enabled(DMS_LINE_KEY, tenant_id or user_id, "dms_line_enabled_for")


def erp_line_enabled_for(tenant_id: Optional[str], user_id: Optional[str]) -> bool:
    return _allowlisted(ERP_PORTAL_KEY, tenant_id or user_id, "erp_line_enabled_for")


def pos_refund_approval_enabled_for(tenant_id: Optional[str]) -> bool:
    """POS 退货/作废店长授权(PS-1 · 防内盗)· 已验收上线 → 全店恒开(测完就全开 · 不灰度)。

    收银员须持 pos.refund.approve 或 caps.can_refund 才能直退,否则店长 PIN 覆盖;owner 主账号
    直放。这是已上线的产品行为,不再走 platform_settings allowlist 灰度;要整体停用改这一行(20s 部署)。
    """
    return True


def pos_cashier_caps_enabled_for(tenant_id: Optional[str]) -> bool:
    """POS 收银员按人权限 caps(PC-1 · 防内盗)· 已验收上线 → 全店恒开(测完就全开 · 不灰度)。

    建单折扣/改价按操作者 caps 卡上限,超限须店长 PIN 覆盖;caps 由老板在收银员页按人配。
    这是已上线的产品行为,不再走 platform_settings allowlist 灰度;要整体停用改这一行(20s 部署)。
    """
    return True


def pos_provision_lock_enabled_for(tenant_id: Optional[str]) -> bool:
    """POS 新租户开通锁闸。关 = apply_preset 照旧开 pos(现网零变化);开 = 新租户 pos 预备但锁定。

    按 tenant 判定;放行判据(存量豁免 / 授权 / 订阅)在 entitlements.pos_provision_allowed。
    """
    return _enabled(POS_PROVISION_LOCK_KEY, tenant_id, "pos_provision_lock_enabled_for")


def entrance_gate_enabled_for(tenant_id: Optional[str]) -> bool:
    """登录入口准入门(各是各的)总闸/回退开关 · 已验收开闸(2026-07-16)→ 全租户恒开(测完就全开)。

    6 个真账号从各自门登录推导入口集均含该门·无锁(开闸安全)。这是已上线的产品行为,不再走
    platform_settings allowlist 灰度;要整体停用改这一行回
    `return _enabled(ENTRANCE_GATE_KEY, tenant_id, "entrance_gate_enabled_for")`(20s 部署急停)。
    """
    return True


def entrance_api_scope_enabled_for(tenant_id: Optional[str]) -> bool:
    """入口级 API 纵深隔离闸(Phase3)· 已验收开闸(2026-07-16)→ 全租户恒开(测完就全开)。

    purchase 映射已补 ai(客户画像供应商档案),静态核三壳(main/pos/ai)正常调用全放行。这是已
    上线的产品行为,不再走 platform_settings allowlist 灰度;要整体停用改这一行回
    `return _enabled(ENTRANCE_API_SCOPE_KEY, tenant_id, "entrance_api_scope_enabled_for")`(20s 部署急停)。
    """
    return True


def pearnly_ai_sod_enabled_for(tenant_id: Optional[str]) -> bool:
    """工单 SoD 强制闸。关 = 分权判定整体跳过,单人所全兼现状不变。

    按 tenant 判定(单所整体开/关,与 pos_refund_approval 同款);超管在平台后台把该
    事务所 tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(PEARNLY_AI_SOD_KEY, tenant_id, "pearnly_ai_sod_enabled_for")


def pearnly_ai_front_desk_enabled_for(tenant_id: Optional[str]) -> bool:
    """目标驱动前门闸(FD-0)。关 = 前门四端点 404、总台不渲染,/ai 现状逐字节不变。

    双闸:pearnly_ai_m1 在场才有效;任一关或异常均
    fail-closed。按 tenant 判定(单所整体开/关);超管在平台后台把 tenant_id 加进 allowlist 即灰度。
    """
    if not pearnly_ai_m1_enabled_for(tenant_id, None):
        return False
    return _enabled(PEARNLY_AI_FRONT_DESK_KEY, tenant_id, "pearnly_ai_front_desk_enabled_for")


def pearnly_ai_steward_enabled_for(tenant_id: Optional[str]) -> bool:
    """智能管家闸(B2-M1)。关 = 管家五端点 404(status 探针照回 {enabled:false}),/ai 现状不变。

    双闸:pearnly_ai_m1 在场才有效(组合闸,同 pearnly_ai_front_desk);任一关或异常均
    fail-closed。按 tenant 判定(单所整体开/关);超管在平台后台把 tenant_id 加进 allowlist 即灰度。
    """
    if not pearnly_ai_m1_enabled_for(tenant_id, None):
        return False
    return _enabled(PEARNLY_AI_STEWARD_KEY, tenant_id, "pearnly_ai_steward_enabled_for")


def steward_brain_loop_enabled_for(tenant_id: Optional[str]) -> bool:
    """管家大脑循环闸。关 = 单次分类路逐字节现状;开 = 多步循环 + 步骤流水。

    双闸:管家闸在场才有效。急停 = 把这个键关掉,在跑的循环任务由 worker 正常收尾,
    下一条消息就回到单次路 —— 不需要回滚代码。
    """
    if not pearnly_ai_steward_enabled_for(tenant_id):
        return False
    return _enabled(STEWARD_BRAIN_LOOP_KEY, tenant_id, "steward_brain_loop_enabled_for")


def pearnly_ai_bank_recon_enabled_for(tenant_id: Optional[str]) -> bool:
    """工单银行对账逐笔对平闸。关 = R3 只判材料存在性(现状逐字节不变);开 = 跑真对平出两张清单。

    按 tenant 判定(单所整体开/关,与 pearnly_ai_sod 同款);超管在平台后台把该事务所
    tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(PEARNLY_AI_BANK_RECON_KEY, tenant_id, "pearnly_ai_bank_recon_enabled_for")


def pearnly_ai_brain_shadow_enabled_for(tenant_id: Optional[str]) -> bool:
    """工单大脑影子闸。关 = brain_shadow.run_shadow no-op(零调用零落库,现状零变化)。

    按 tenant 判定(单所整体开/关,与 pearnly_ai_shadow_draft 同款);超管在平台后台把该
    事务所 tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(PEARNLY_AI_BRAIN_SHADOW_KEY, tenant_id, "pearnly_ai_brain_shadow_enabled_for")


def pearnly_ai_shadow_draft_enabled_for(tenant_id: Optional[str]) -> bool:
    """工单影子底稿闸。关 = reconcile 逐字节维持现状(gates 无 r5_shadow);开 = 产出影子底稿三件套。

    按 tenant 判定(单所整体开/关,与 pearnly_ai_bank_recon 同款);超管在平台后台把该事务所
    tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(PEARNLY_AI_SHADOW_DRAFT_KEY, tenant_id, "pearnly_ai_shadow_draft_enabled_for")


def pearnly_ai_bank_sales_suggest_enabled_for(tenant_id: Optional[str]) -> bool:
    """银行流水倒推销项建议闸(SA-3a)。关 = order_detail 无 bank_sales_suggestion 键、端点 404、
    引擎不跑(现有人工填销项逐字节不变);开 = 出倒推建议(只建议不落申报数)。

    按 tenant 判定(单所整体开/关,与 pearnly_ai_shadow_draft 同款);超管在平台后台把该事务所
    tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(
        PEARNLY_AI_BANK_SALES_SUGGEST_KEY, tenant_id, "pearnly_ai_bank_sales_suggest_enabled_for"
    )


def pearnly_ai_stmt_regroup_enabled_for(tenant_id: Optional[str]) -> bool:
    """对账单续页回收闸(SA3R-a)。关 = classify 归堆逐字节维持现状(续页照旧踢 non_tax);
    开 = 命中银行名 + 对账单标题的续页救回 bank_statement。

    按 tenant 判定(单所整体开/关,与 pearnly_ai_bank_sales_suggest 同款);fail-closed 在
    _enabled 内部(基建抖动绝不误开回收路)。
    """
    return _enabled(PEARNLY_AI_STMT_REGROUP_KEY, tenant_id, "pearnly_ai_stmt_regroup_enabled_for")
