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
