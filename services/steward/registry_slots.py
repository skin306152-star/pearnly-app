# -*- coding: utf-8 -*-
"""工具的输入面:参数槽定义(模型该填什么)+ 执行身份(以谁的身份跑)。

从 registry 分出来只为体积闸(单文件 <500 行),不是语义分家 —— registry 仍是唯一入口,
调用方一律 `from services.steward.registry import ToolContext`(registry 再导出)。

槽定义共 3 个工厂函数而不是逐个工具写一份:同一个槽在 3 个工具里各写一遍描述,改一处
另外两处就漂,而槽描述直接进提示词 —— 漂出来的那句就是大脑填错参数的成因。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from services.agent.contracts import SlotSpec
from services.sales.dates import bangkok_today


def period_slot() -> SlotSpec:
    """期间线索槽(共 3 个工具用同一份定义,避免三处各写一遍描述后漂)。

    source=model_freeform:期间允许模型从「上个月」这类相对词换算,但换算结果不作数——
    真正的接地在 orchestrator:线索经 front_desk.interpret.parse_period_hint 解析成公历,
    再经 obligation_engine.be_period_from_ce 折成佛历账期,解不出就追问,绝不猜一个期。
    """
    return SlotSpec(
        "period",
        required=False,
        source="model_freeform",
        desc_th="ช่วงเวลาที่ผู้ใช้พูดถึง เช่น มิ.ย.69 / เดือนที่แล้ว / 2026-06",
        desc_zh="期间线索原文(如「上个月」「6月」「2569-06」)· 没提到给 null",
    )


def keyword_slot(desc_th: str, desc_zh: str) -> SlotSpec:
    """票据关键词槽。source=user_text 同客户名槽:模型编一个单号会把人指到另一张票上。"""
    return SlotSpec("keyword", required=True, source="user_text", desc_th=desc_th, desc_zh=desc_zh)


def client_name_slot(required: bool) -> SlotSpec:
    """客户名槽。source=user_text:名字必须出现在用户原话里(接地闸拦编造),
    随后还要在真实名录里命中才作数(tools 侧二次接地)—— 挂错账套是红线。"""
    return SlotSpec(
        "client_name",
        required=required,
        source="user_text",
        desc_th="ชื่อลูกค้าตามที่ผู้ใช้พิมพ์ (คัดจากข้อความผู้ใช้เท่านั้น)",
        desc_zh="客户名(必须原样出自用户原话·不许改写不许猜)",
    )


@dataclass
class ToolContext:
    """工具以此身份执行 —— 复用现成 RLS/权限口径,绝不 bypass。

    allowed_client_ids=None 表示不限(老板/超管/scope_mode='all');给了集合就是被分派成员
    只看分到的账套,与 /api/tax-profile/matrix 的收窄口径同源(路由算好传进来)。

    today 走曼谷日历日:服务器跑 UTC,date.today() 在曼谷 00:00–07:00 还停在昨天,逾期与
    剩余天数会整体差一天(当天到期的义务被说成"还剩 1 天",简报的头条与桶序跟着错)。

    attachment_ids 走执行上下文而非参数槽:附件 id 根本不经过模型,塞进 slots 只会让
    services/agent/slots.py 的接地闸(source=user_text 的值必须逐字节出现在用户原话里)
    报假阳 —— 那道闸是为「模型编了一个客户名」设计的。与 user_id/allowed_client_ids 同层。
    """

    user: dict
    tenant_id: str
    user_id: str
    allowed_client_ids: Optional[frozenset] = None
    lang: str = "zh"
    today: date = field(default_factory=bangkok_today)
    user_text: str = ""
    session_id: str = ""
    attachment_ids: tuple = ()
