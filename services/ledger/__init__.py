# -*- coding: utf-8 -*-
"""账簿配方生成器:一批已识别的单据 → 会计能核对、改完能塞回来的工作簿。

「配方」是这一层的组织单位:一个配方 = 一种单据 + 一组产出表。第一个配方是销售票的
四表账簿(明细/日记账/分类账/试算平衡);进项台账、银行流水、费用明细各自是后面的
一个新文件,不是往这个文件里加分支 —— 见 services/ledger/registry.py 的注册表。

三条本层特有的硬约束(都是踩过的坑):

1. **科目码不臆造。** 印在账簿上的码优先取该账套的科目桥(coa_erp_bridge);桥没接就退回
   coa_preset 通用码,并在表头明写「未接账套 · 科目码待确认」。桥接了却没映到的角色如实
   列出来交会计裁,不静默拿一个她账套里不存在的码顶上。
2. **公式删行不炸。** 会计核对的标准动作是把核对无误的行删掉,所以跨表一律按票号 SUMIF,
   绝不用绝对单元格引用 —— 那种引用一删行就整表 #REF!。
3. **表里的自检格不是闸。** 「借贷平」那一格只给眼睛看;权威判定由回导时我们的代码重算。
   一个能显示假绿的格子当闸,比没有自检更坏。
"""

from services.ledger.accounts import AccountRef, ChartResolution, resolve_chart
from services.ledger.doc_date import REASON_CROSS_MONTH, REASON_NO_DATE
from services.ledger.models import (
    REASON_DUPLICATE_INVOICE,
    REASON_NO_INVOICE_NUMBER,
    REASON_NO_LINES,
    REASON_NO_SETTLEMENT,
    REASON_TOTAL_MISMATCH,
    SalesDoc,
    SalesLine,
    parse_sales_docs,
)
from services.ledger.registry import RecipeResult, RecipeSpec, get_recipe, list_recipes

__all__ = [
    "AccountRef",
    "ChartResolution",
    "REASON_CROSS_MONTH",
    "REASON_DUPLICATE_INVOICE",
    "REASON_NO_DATE",
    "REASON_NO_INVOICE_NUMBER",
    "REASON_NO_LINES",
    "REASON_NO_SETTLEMENT",
    "REASON_TOTAL_MISMATCH",
    "RecipeResult",
    "RecipeSpec",
    "SalesDoc",
    "SalesLine",
    "get_recipe",
    "list_recipes",
    "parse_sales_docs",
    "resolve_chart",
]
