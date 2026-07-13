# -*- coding: utf-8 -*-
"""应用层 feature flag · 对话 Agent 总闸的消费侧(WP2 钥匙闸)。

WP5 入口在调 Agent 前先问 agent_enabled_for(user_id):False → 绕过整个 Agent 层、
用户无感回到现状。默认关(表无记录 / 查询异常 → False);开 / 灰度由超管在平台后台
「全局设置」控制(钥匙闸是安全阀,fail-closed)。设置读写见 services/platform_settings。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

AGENT_ENABLED_KEY = "agent_enabled"
# M3 写工具(记账/推 ERP…)子闸:与总闸分开,默认关。开总闸只放只读+确认查询,
# 写能力要单独开(灰度先行·真机验稳才放量)。复用同一套 platform_settings 灰度机制。
AGENT_WRITE_KEY = "agent_write_tools"
# M3 全家桶子闸(撤销/改错工具 + 多笔直分发):与写子闸分开,默认关。
# 开 → 大脑成为记账域唯一决策者(旧 LLM understand 退出灰度路);关 → defer 交旧路,现状不变。
AGENT_M3_KEY = "agent_m3_tools"
# 推 ERP 子闸(唯一 confirm-first 的不可逆写):默认关。关 → 工具对模型不可见,
# 模型硬调只得到 not_available_yet 观测(引导去 App),线上行为零变化。
AGENT_PUSH_KEY = "agent_push_erp"
# LINE 图片意图子闸(LI 框架):默认关。关 → 发图走现状管线逐字节不变;
# 开 → 图片 OCR 后先过意图分流(services/agent/image_intent),用户明说的目的优先。
AGENT_IMAGE_KEY = "agent_image_intent"
# M3 确认握手状态机(LangGraph HITL 范式 · docs/agent/M3-CONFIRM-HANDSHAKE-DESIGN.md):
# 默认关。开 → 确认卡 15 分钟内打"确认/取消"字样与点按钮同效(resume 闸消费同一 nonce)。
AGENT_CONFIRM_KEY = "agent_confirm_machine"
# LINE DMS 身份证推送子闸(LINE-DMS-PUSH-DESIGN):默认关。关 → 身份证图走现状
# (not_invoice 靶向引导仍在,无副作用);开 → 说过"进 DMS"再发身份证 = 复述+确认后建客户。
AGENT_DMS_KEY = "agent_dms_push"
# LINE 对账收件子闸(RECON-3-LINE-PLAN 方案一触发底座):默认关。关 → 说"做银行对账"
# 得 not_available_yet 诚实拒、文件走现状 OCR;开 → 收件配对→异步对账→完成回推。
AGENT_RECON_INTAKE_KEY = "agent_recon_intake"
# 大脑原生 function-calling 子闸(P2):默认关。关 → 手写单行 JSON 协议现状不变;
# 开 → 决策经 provider 原生工具调用(消 JSON 截断/parse 类 crash),后端不支持自动回落 JSON 路。
AGENT_NATIVE_FC_KEY = "agent_native_fc"
# 回复底部 quick-reply chips 子闸(P2):默认关。关 → 纯文本回复现状不变;
# 开 → agent 回复/安全兜底带 2-3 个可点建议(教育用户能问什么)。
AGENT_QUICK_CHIPS_KEY = "agent_quick_chips"
# 跨轮锚点记忆子闸(P2):默认关。关 → 锚点不加载/不采集/不落库,行为逐字节不变;
# 开 → 「把刚才那张推进 ERP」这类不带票号的口头指代能定位上一轮碰过的单据。
AGENT_ANCHOR_KEY = "agent_anchor_memory"
# LINE 语音转写子闸(P2):默认关。关 → 语音消息回 unsupported 现状逐字节不变;
# 开 → 语音经网关 Gemini 逐字转写(回显原文)后走与打字完全相同的文本路。
AGENT_VOICE_KEY = "agent_voice_stt"
# 主动触达子闸(P2):默认关。关 → 一条不发现状不变;开 → 每月 10–15 日窗口
# 给绑定 LINE 用户发一条 VAT 申报截止提醒(每用户每期恰一条·台账去重)。
AGENT_PROACTIVE_KEY = "agent_proactive_nudge"
# 复合续步子闸(P2):默认关。关 → 记账卡出即终轮现状不变;开 → 一句话「记账+提问」
# 出卡后继续答剩余问题(跟进文字入口 push·推 ERP/撤销/改错仍即卡即终)。
AGENT_COMPOUND_KEY = "agent_compound_turn"
# 用户画像子闸(W3):默认关。关 → 提示词逐字节不变;开 → 高频商家/类目/昨日摘要
# 拼进上下文(services/agent/user_profile·fail-open),常客不再被反复问类目。
AGENT_PROFILE_KEY = "agent_user_profile"
# 知识库问答子闸(W3):默认关。关 → 工具硬调得 not_available_yet 诚实拒;
# 开 → confirm-first 确认卡,用户点确认才检索+扣 ฿0.50(no_answer 不扣)。
AGENT_KNOWLEDGE_KEY = "agent_ask_knowledge"
# 月报卡子闸(W4·拍板默认开+可退订):关 → 一条不发;开 → 每月 1–3 日推上月
# 数字月报(带看明细/退订按钮·上月零单不发·台账去重每用户每期恰一条)。
AGENT_MONTHLY_REPORT_KEY = "agent_monthly_report"
# 掉线召回子闸(W4·拍板月最多一条·文案 Zihao 过目后才放):默认关。
# 开 → 有过单据但连续 14 天零单的用户,每自然月最多收一条温和召回。
AGENT_RECALL_KEY = "agent_recall_nudge"
# M1 客户建档收严子闸(B2 · 见 L2-验收.md 真语料坐实):默认关。关 → 建档/编辑校验
# 现状逐字节不变;开 → 建档强收泰文注册名(OCR 方向判定的名称锚),编辑不许清空
# 已登记的泰文名。判定域 = 账套主体归属(有 tenant_id 走 tenant 共享闸 · 个人套账退回
# user_id · 与 workspace_clients 其余隔离口径一致),不是单个用户。
PEARNLY_AI_M1_KEY = "pearnly_ai_m1"
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
# LINE 待问客户池闸(D2 · 审核队列票挂客户经 LINE 问答回写改判):默认关。关 = 客户绑定码
# 分支/暂挂/攒批推送/回答拦截全链不生效,webhook 走既有用户绑定码判定现状不变(fail-closed)。
# 按 tenant 判定(单所整体开/关,与 pearnly_ai_sod 同款);超管在平台后台把该事务所
# tenant_id 加进 allowlist 即单所灰度。
PEARNLY_AI_CLIENT_POOL_KEY = "pearnly_ai_client_pool"
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
# LINE 收料暂存闸(LN-1):默认关 fail-closed。关 = webhook 图片/文件消息与绑定码分支
# 逐字节走现状(对话 Agent/记账 OCR/待问池/单聊客户绑定全不动);开 = 已绑上下文(单聊
# 客户 contact / 已绑群)发的票据下载落 client_intake_staging 暂存池 + 四语确认回执。
# 按 tenant 判定;消费在 services/line_binding/line_intake_staging.py(收料)与
# line_client_bind_intake.py(群绑定形态)。
PEARNLY_AI_LINE_INTAKE_KEY = "pearnly_ai_line_intake"


def _enabled(key: str, user_id: Optional[str], label: str) -> bool:
    """钥匙闸统一读法:任何异常一律 fail-closed 回 False(安全阀,绝不因基建抖动误放)。"""
    try:
        from services.platform_settings import store

        return store.is_enabled_for_user(key, user_id)
    except Exception as e:
        logger.warning(f"{label} fail-closed: {e}")
        return False


def agent_enabled_for(user_id: Optional[str]) -> bool:
    """对话 Agent 总闸。"""
    return _enabled(AGENT_ENABLED_KEY, user_id, "agent_enabled_for")


def agent_write_enabled_for(user_id: Optional[str]) -> bool:
    """写工具(记账等 B 档)子闸。关 = 记账逐字节走旧乐观路。"""
    return _enabled(AGENT_WRITE_KEY, user_id, "agent_write_enabled_for")


def agent_m3_enabled_for(user_id: Optional[str]) -> bool:
    """M3 全家桶(撤销/改错/多笔直分发)子闸。关 = defer 交旧路,现状不变。"""
    return _enabled(AGENT_M3_KEY, user_id, "agent_m3_enabled_for")


def agent_push_enabled_for(user_id: Optional[str]) -> bool:
    """推 ERP confirm-first 子闸。关 = 工具不可见,硬调得 not_available_yet。"""
    return _enabled(AGENT_PUSH_KEY, user_id, "agent_push_enabled_for")


def agent_image_enabled_for(user_id: Optional[str]) -> bool:
    """LINE 图片意图子闸(LI)。关 = 发图走现状管线逐字节不变。"""
    return _enabled(AGENT_IMAGE_KEY, user_id, "agent_image_enabled_for")


def agent_confirm_enabled_for(user_id: Optional[str]) -> bool:
    """确认握手状态机子闸。关 = 文本"确认"走正常对话轮,按钮卡现状不变。"""
    return _enabled(AGENT_CONFIRM_KEY, user_id, "agent_confirm_enabled_for")


def agent_dms_enabled_for(user_id: Optional[str]) -> bool:
    """LINE DMS 身份证推送子闸。关 = 身份证图走现状,plan 的 dms 目标如实拒。"""
    return _enabled(AGENT_DMS_KEY, user_id, "agent_dms_enabled_for")


def agent_recon_intake_enabled_for(user_id: Optional[str]) -> bool:
    """LINE 对账收件子闸。关 = 工具如实拒、文件走现状 OCR。"""
    return _enabled(AGENT_RECON_INTAKE_KEY, user_id, "agent_recon_intake_enabled_for")


def agent_native_fc_enabled_for(user_id: Optional[str]) -> bool:
    """大脑原生 function-calling 子闸。关 = 手写 JSON 协议现状不变。"""
    return _enabled(AGENT_NATIVE_FC_KEY, user_id, "agent_native_fc_enabled_for")


def agent_quick_chips_enabled_for(user_id: Optional[str]) -> bool:
    """quick-reply chips 子闸。关 = 纯文本回复现状不变。"""
    return _enabled(AGENT_QUICK_CHIPS_KEY, user_id, "agent_quick_chips_enabled_for")


def agent_anchor_enabled_for(user_id: Optional[str]) -> bool:
    """跨轮锚点记忆子闸。关 = 锚点全程不流动,现状不变。"""
    return _enabled(AGENT_ANCHOR_KEY, user_id, "agent_anchor_enabled_for")


def agent_voice_enabled_for(user_id: Optional[str]) -> bool:
    """LINE 语音转写子闸。关 = 语音回 unsupported,现状不变。"""
    return _enabled(AGENT_VOICE_KEY, user_id, "agent_voice_enabled_for")


def agent_proactive_enabled_for(user_id: Optional[str]) -> bool:
    """主动触达子闸。关 = 一条不发,现状不变。"""
    return _enabled(AGENT_PROACTIVE_KEY, user_id, "agent_proactive_enabled_for")


def agent_compound_enabled_for(user_id: Optional[str]) -> bool:
    """复合续步子闸。关 = 记账卡出即终轮,现状不变。"""
    return _enabled(AGENT_COMPOUND_KEY, user_id, "agent_compound_enabled_for")


def agent_profile_enabled_for(user_id: Optional[str]) -> bool:
    """用户画像子闸。关 = 画像不算不拼,提示词现状不变。"""
    return _enabled(AGENT_PROFILE_KEY, user_id, "agent_profile_enabled_for")


def agent_knowledge_enabled_for(user_id: Optional[str]) -> bool:
    """知识库问答子闸。关 = 工具诚实拒,不出确认卡不扣费。"""
    return _enabled(AGENT_KNOWLEDGE_KEY, user_id, "agent_knowledge_enabled_for")


def agent_monthly_report_enabled_for(user_id: Optional[str]) -> bool:
    """月报卡子闸。关 = 一条不发,现状不变。"""
    return _enabled(AGENT_MONTHLY_REPORT_KEY, user_id, "agent_monthly_report_enabled_for")


def agent_recall_enabled_for(user_id: Optional[str]) -> bool:
    """掉线召回子闸。关 = 一条不发,现状不变。"""
    return _enabled(AGENT_RECALL_KEY, user_id, "agent_recall_enabled_for")


def pearnly_ai_m1_enabled_for(tenant_id: Optional[str], user_id: Optional[str]) -> bool:
    """M1 客户建档收严子闸。关 = 建档/编辑校验现状不变。

    按账套主体归属判定,不按单个操作人:有 tenant_id 用 tenant(团队共享同一开关
    状态,跟其余 workspace_clients 隔离口径一致);个人套账(无 tenant)退回 user_id。
    """
    return _enabled(PEARNLY_AI_M1_KEY, tenant_id or user_id, "pearnly_ai_m1_enabled_for")


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


def pearnly_ai_sod_enabled_for(tenant_id: Optional[str]) -> bool:
    """工单 SoD 强制闸。关 = 分权判定整体跳过,单人所全兼现状不变。

    按 tenant 判定(单所整体开/关,与 pos_refund_approval 同款);超管在平台后台把该
    事务所 tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(PEARNLY_AI_SOD_KEY, tenant_id, "pearnly_ai_sod_enabled_for")


def pearnly_ai_client_pool_enabled_for(tenant_id: Optional[str]) -> bool:
    """LINE 待问客户池闸。关 = 客户绑定码/暂挂池/攒批推送/回答拦截全链不生效。

    按 tenant 判定(单所整体开/关,与 pearnly_ai_sod 同款);超管在平台后台把该
    事务所 tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(PEARNLY_AI_CLIENT_POOL_KEY, tenant_id, "pearnly_ai_client_pool_enabled_for")


def pearnly_ai_line_intake_enabled_for(tenant_id: Optional[str]) -> bool:
    """LINE 收料暂存闸(LN-1)。关 = webhook 图片/文件与群绑定分支逐字节走现状。

    双闸:pearnly_ai_m1 在场才有效。与 client_pool(两独立闸在各自消费层分别判)不同,这是仓库首个
    flag 内嵌依赖 flag 的组合闸——让每个消费点天然双闸;任一关或异常均 fail-closed。按 tenant 判定(单所整体开/关)。
    """
    if not pearnly_ai_m1_enabled_for(tenant_id, None):
        return False
    return _enabled(PEARNLY_AI_LINE_INTAKE_KEY, tenant_id, "pearnly_ai_line_intake_enabled_for")


def pearnly_ai_bank_recon_enabled_for(tenant_id: Optional[str]) -> bool:
    """工单银行对账逐笔对平闸。关 = R3 只判材料存在性(现状逐字节不变);开 = 跑真对平出两张清单。

    按 tenant 判定(单所整体开/关,与 pearnly_ai_sod 同款);超管在平台后台把该事务所
    tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(PEARNLY_AI_BANK_RECON_KEY, tenant_id, "pearnly_ai_bank_recon_enabled_for")


def pearnly_ai_shadow_draft_enabled_for(tenant_id: Optional[str]) -> bool:
    """工单影子底稿闸。关 = reconcile 逐字节维持现状(gates 无 r5_shadow);开 = 产出影子底稿三件套。

    按 tenant 判定(单所整体开/关,与 pearnly_ai_bank_recon 同款);超管在平台后台把该事务所
    tenant_id 加进 allowlist 即单所灰度。
    """
    return _enabled(PEARNLY_AI_SHADOW_DRAFT_KEY, tenant_id, "pearnly_ai_shadow_draft_enabled_for")
