# -*- coding: utf-8 -*-
"""前门意图闭集 · 单一事实源(纯常量叶子模块 · 照 workorder/kinds.py 范式)。

大脑只准从这里的枚举里选一个意图,选不到 = UNSUPPORTED(诚实拒绝,绝不装懂)。每个意图
声明:id / 人话名(四语 i18n key,前端 at() 消费)/ 执行计划(映射到工单 intent)/ 需料清单 /
交付物清单 / 审批点 / 是否已开放。首发只开 monthly_vat;其余在册但 enabled=False——「加新
必删旧」:digitize/vat_report_check/payroll_filing 在 FD-1 各自金标验收通过的同批次开放并
摘对应老菜单,bank_match 同期。

零依赖:不 import 任何本包/工单模块(前端无法 import,故人话名只存 key 字符串,真翻译在
static/ai i18n 分片)。校验(枚举外意图/编造客户 id)是 interpret.py(FD-0b)的机器闸,不在此。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# 大脑输出闭集外的哨兵:听不懂/不支持 → 前端出拒绝卡(能力发现)。永不进 _REGISTRY。
UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class Intent:
    """一个可被前门消化的目标。work_order_intent 是执行计划的落点(开工单用的 intent),
    needs/deliverables 存四语 key(合同卡按 key 渲染需料对照与交付物清单)。"""

    id: str
    name_key: str
    work_order_intent: str
    needs: tuple[str, ...]
    deliverables: tuple[str, ...]
    approval: str
    enabled: bool


# 月度 VAT(ภ.พ.30):首发唯一开放意图,直接落既有 monthly_vat 工单(classify/reconcile/算税)。
MONTHLY_VAT = Intent(
    id="monthly_vat",
    name_key="fd.intent.monthly_vat",
    work_order_intent="monthly_vat",
    needs=("fd.need.purchase_invoices", "fd.need.sales_summary", "fd.need.bank_statement"),
    deliverables=("fd.deliver.pp30_draft", "fd.deliver.workpaper"),
    approval="review_signoff",
    enabled=True,
)

# 以下四意图在册但未开放(enabled=False):路由/合同层认得它们(校验、拒绝话术区分「暂不支持」
# 与「不认识」),但大脑不会建议、confirm 不放行,直到各自 FD-1 批次金标验收通过再翻开。
DIGITIZE = Intent(
    id="digitize",
    name_key="fd.intent.digitize",
    work_order_intent="digitize",
    needs=("fd.need.raw_files",),
    deliverables=("fd.deliver.organized_excel",),
    approval="review_signoff",
    enabled=False,
)
VAT_REPORT_CHECK = Intent(
    id="vat_report_check",
    name_key="fd.intent.vat_report_check",
    work_order_intent="vat_report_check",
    needs=("fd.need.sales_vat_report",),
    deliverables=("fd.deliver.report_check_result",),
    approval="review_signoff",
    enabled=False,
)
PAYROLL_FILING = Intent(
    id="payroll_filing",
    name_key="fd.intent.payroll_filing",
    work_order_intent="payroll_filing",
    needs=("fd.need.payroll_sheet",),
    deliverables=("fd.deliver.pnd1_draft",),
    approval="review_signoff",
    enabled=False,
)
BANK_MATCH = Intent(
    id="bank_match",
    name_key="fd.intent.bank_match",
    work_order_intent="bank_match",
    needs=("fd.need.bank_statement", "fd.need.purchase_invoices"),
    deliverables=("fd.deliver.match_result", "fd.deliver.missing_slips"),
    approval="review_signoff",
    enabled=False,
)

_REGISTRY: dict[str, Intent] = {
    i.id: i for i in (MONTHLY_VAT, DIGITIZE, VAT_REPORT_CHECK, PAYROLL_FILING, BANK_MATCH)
}

# 闭集全集(含未开放),供 interpret 机器校验「是否枚举内」;开放子集供合同确认放行。
ALL_IDS = tuple(_REGISTRY)


def get(intent_id: Optional[str]) -> Optional[Intent]:
    """按 id 取意图定义,未知(含 UNSUPPORTED)返 None。"""
    return _REGISTRY.get(intent_id or "")


def is_known(intent_id: Optional[str]) -> bool:
    """是否闭集内(含未开放意图)。大脑输出不在此集 = 应判 UNSUPPORTED。"""
    return (intent_id or "") in _REGISTRY


def is_enabled(intent_id: Optional[str]) -> bool:
    """是否已开放(confirm 只放行开放意图)。未知/未开放均 False。"""
    intent = get(intent_id)
    return bool(intent and intent.enabled)


def enabled_ids() -> tuple[str, ...]:
    """已开放意图 id(首发 = 仅 monthly_vat)。"""
    return tuple(i.id for i in _REGISTRY.values() if i.enabled)


def enabled_intents() -> tuple[Intent, ...]:
    """已开放意图定义(拒绝卡「目前能帮你…」按此渲染)。"""
    return tuple(i for i in _REGISTRY.values() if i.enabled)
