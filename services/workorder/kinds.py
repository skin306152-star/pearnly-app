# -*- coding: utf-8 -*-
"""work_order_items.kind 的唯一词汇表(纯常量叶子模块 · T4a 收口)。

此前 sort/classify/reconcile/conservation/evidence/sod/api 各自重声明同一批 kind 字面量,
改一处极易漏改另一处(decisions.py 收敛裁决动词的同款病根)。收敛到此成真·单一事实源;
与 decisions.py 的 assign_kind 裁定词(purchase_invoice/sales_doc/non_tax)分属两套命名空间:
那边是「人工把方向票裁成什么」,这边是「一件料本身是什么」,值有重叠但语义不同,不合并。

零依赖:不 import 任何本包模块。static/ai 前端无法 import,字面量旁有同步注释。
"""

from __future__ import annotations

UNKNOWN = "unknown"  # 未定堆(intake 默认;方向不明票也停在此 kind + 方向 flag_reason)
PURCHASE_INVOICE = "purchase_invoice"  # 进项票(R1 计税主料)
SALES_SUMMARY = "sales_summary"  # 销项汇总表(R2 直读源)
BANK_STATEMENT = "bank_statement"  # 银行流水(R3 佐证件,不进税额)
NON_TAX = "non_tax"  # 无税务要素,排除
DUPLICATE = "duplicate"  # 票面级重复件,排除
GL_LEDGER = "gl_ledger"  # 上传 GL 台账(F2 影子对平佐证件,不进税额;T4a 新增)
EDC_SETTLEMENT = "edc_settlement"  # EDC 日终结算票(SA-2 销项聚合佐证件,不进税额)

ALL_KINDS = (
    UNKNOWN,
    PURCHASE_INVOICE,
    SALES_SUMMARY,
    BANK_STATEMENT,
    NON_TAX,
    DUPLICATE,
    GL_LEDGER,
    EDC_SETTLEMENT,
)
