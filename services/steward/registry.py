# -*- coding: utf-8 -*-
"""管家工具注册表 —— 闭集插头目录(照 services/agent/manifest.py 范式)。

闭集:大脑只能从 TOOLS 里选,表外的名字物理调不到(tools.run 按本表查执行器,查不到直接
拒;planner 解析时枚举外一律归 out_of_scope)。加一个能力 = 加一个 StewardTool + tools.py
里一个薄封装函数,提示词自动跟着变(catalog() 从本表现生成)。

参数槽复用 services.steward.contracts.SlotSpec,由 services/steward/slots.py 接地。
(source=user_text 的值必须出现在用户原话里,编造值进 rejected 绝不流到执行)。为什么不直接
用 manifest.ToolSpec:它的 bucket/confirm/writes/gate 是 LINE 写工具的语义(M1 全只读用不上),
desc_th 字段名钉死泰文而管家提示词走中文(同 front_desk.interpret 先例,同一个 /ai 面、同一
条 taxops.intent 车道)—— 硬塞会让字段名说谎。槽契约共用,工具契约各自诚实。

每个工具的 desc 都要写「什么时候【不】用它」并点名该用哪个邻居 —— 大脑挑错工具的成因不是
它不知道这个工具能干嘛,而是相邻两个都像(client_status vs close_readiness、push_log_query
vs period_invoices)。选错一次 = 白跑一步 + 白花一次模型钱,还得再问一轮。守门测试
tests/unit/test_steward_registry.py 锁「每条 desc 至少点名另一个工具」。

体积闸(单文件 <500 行)下的两次分居,本模块是门面,不是唯一真身:
  registry_slots    工具的型(StewardTool/风险等级/requires_authorization)+ 参数槽工厂 +
                     执行身份(ToolContext)—— 叶子模块,不依赖本模块也不依赖 registry_catalog。
  registry_catalog   23 个 StewardTool 的数据本体(TOOLS 元组、工具名常量、timeout 常量)+
                     由 TOOLS 现生成的 catalog()/slot_hints()。

本模块把两边的公共名逐个显式 re-export(不用 `import *`),调用方一律 `registry.XXX` 引用,
拆分对全仓调用方物理透明。为什么型放 registry_slots 而不是留在本模块:TOOLS(数据)要用
StewardTool(型)现造 23 个实例,数据模块因此必须能 import 到型;型要是留在本模块,
registry_catalog 就得反过来 import 本模块,而本模块又要 import registry_catalog 的 TOOLS
——两边互相 import 成环。型挪去两边都能单向依赖的叶子模块,闭环物理上不存在。
"""

from __future__ import annotations

from typing import Any, Optional

from services.steward.contracts import SlotSpec as SlotSpec  # 再导出:调用方一律 registry.SlotSpec
from services.steward.registry_catalog import (
    ATTACHMENT_TOOLS as ATTACHMENT_TOOLS,
    BANK_RECON_STATUS as BANK_RECON_STATUS,
    CLIENT_LOOKUP as CLIENT_LOOKUP,
    CLIENT_STATUS as CLIENT_STATUS,
    CLOSE_READINESS as CLOSE_READINESS,
    DELIVERABLES_LIST as DELIVERABLES_LIST,
    DOC_READ_QA as DOC_READ_QA,
    DUE_SOON as DUE_SOON,
    ERP_PUSH as ERP_PUSH,
    ERP_PUSH_TIMEOUT_S as ERP_PUSH_TIMEOUT_S,
    FILE_CONVERT as FILE_CONVERT,
    FILE_TOOL_TIMEOUT_S as FILE_TOOL_TIMEOUT_S,
    HISTORY_QUERY as HISTORY_QUERY,
    INVOICE_DETAIL as INVOICE_DETAIL,
    MATRIX_OVERVIEW as MATRIX_OVERVIEW,
    MODEL_CALL_TOOLS as MODEL_CALL_TOOLS,
    PERIOD_INVOICES as PERIOD_INVOICES,
    PUSH_LOG_QUERY as PUSH_LOG_QUERY,
    REVIEW_QUEUE as REVIEW_QUEUE,
    STOCK_CARD_LOOKUP as STOCK_CARD_LOOKUP,
    TABLE_GENERATE as TABLE_GENERATE,
    TAX_MATRIX as TAX_MATRIX,
    TAX_NUMBERS as TAX_NUMBERS,
    TODAY_BRIEF as TODAY_BRIEF,
    TOOLS as TOOLS,
    TOOLS_BY_NAME as TOOLS_BY_NAME,
    VAT_CALC as VAT_CALC,
    VAT_REPORT_CHECK as VAT_REPORT_CHECK,
    WORKORDER_LIST as WORKORDER_LIST,
    catalog as catalog,
    slot_hints as slot_hints,
)
from services.steward.registry_slots import (
    RISK_DANGER as RISK_DANGER,
    RISK_LEVELS as RISK_LEVELS,
    RISK_READ as RISK_READ,
    RISK_WRITE as RISK_WRITE,
    StewardTool as StewardTool,
    ToolContext as ToolContext,  # 再导出:调用方一律 registry.ToolContext(搬家只为体积闸)
    client_name_slot as client_name_slot,
    keyword_slot as keyword_slot,
    period_slot as period_slot,
    requires_authorization as requires_authorization,
)

# 闭集全集 + 哨兵:planner 解析时枚举外一律归 OUT_OF_SCOPE(诚实拒,绝不装懂)。
ALL_NAMES: tuple[str, ...] = tuple(TOOLS_BY_NAME)
OUT_OF_SCOPE = "out_of_scope"


def get(name: Optional[str]) -> Optional[StewardTool]:
    return TOOLS_BY_NAME.get(name or "")


def is_known(name: Optional[str]) -> bool:
    return (name or "") in TOOLS_BY_NAME


def public_catalog() -> list[dict[str, Any]]:
    """能力清单(拒绝时告诉用户「目前能帮你查这些」;探针端点也用它对外声明闭集)。"""
    return [{"name": t.name, "desc": t.desc, "readonly": t.readonly} for t in TOOLS]
