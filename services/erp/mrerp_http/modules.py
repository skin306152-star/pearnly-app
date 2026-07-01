# -*- coding: utf-8 -*-
"""MR.ERP 导入模块表 · doc_type → 端点/子类型/xlsx 模板。

所有单据(销/采/库存/主数据)走**同一 xlsx 导入机制**
(formupload → component/uploadexcel → formrdpc → component/importpc → component/report),
仅 path / idmenu / selmenu / sheet_kind 不同。本表是单一事实源。

端点来源:docs/integrations/mrerp-known-facts.md §4-§5 +
2026-07-01 test01 实测捕获(scratchpad/mrerp_import_endpoint_map_2026-07-01.md)。
`verified` = 已在真站点端到端跑通;False 者端点已知但 selmenu/模板待补(S3)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class MrErpModule:
    doc_type: str
    path: str  # 导入模块目录:impartran / imparse / impaptran / impstk* ...
    idmenu: int  # formupload.php 路由 id
    selmenu: Optional[int]  # 业务子类型字典 id(None = 待抓)
    sheet_kind: str  # 交给 mrerp_xlsx_generator.generate_xlsx 的模板名
    listing_module: str  # 回读/查重用的 allview 模块
    listing_idmenu: int  # 回读列表 idmenu
    verified: bool = False


# 交易单据
MODULES: Dict[str, MrErpModule] = {
    "sales_credit": MrErpModule(
        "sales_credit", "impartran", 370, 118, "sales_credit", "artran", 118, verified=True
    ),
    # 2026-07-01 实测捕获 selmenu=125(ใบขายเงินสด)· sheet_kind 模板待补(S3)
    "sales_cash": MrErpModule(
        "sales_cash", "imparse", 371, 125, "sales_cash", "artran", 118, verified=False
    ),
    # 采购(AP tran)· 2026-07-01 实测 selmenu=67(ซื้อ)/453(ซื้อ-ค่าใช้จ่าย)· 模板/生成器待补 S3
    "purchase": MrErpModule(
        "purchase", "impaptran", 363, 67, "purchase_credit", "aptran", 67, verified=False
    ),
    # 库存进出(仅数量)· S4
    "stock_receive": MrErpModule(
        "stock_receive",
        "impstktranrec",
        355,
        None,
        "stock_receive",
        "stktranrec",
        28,
        verified=False,
    ),
    "stock_issue": MrErpModule(
        "stock_issue", "impstktraniss", 356, None, "stock_issue", "stktraniss", 32, verified=False
    ),
    # 主数据自建(走导入,非 Playwright 表单)· S2
    "master_customer": MrErpModule(
        "master_customer", "imparmas", 367, None, "customer_master", "armas", 105, verified=False
    ),
    "master_supplier": MrErpModule(
        "master_supplier", "impapmas", 359, None, "supplier_master", "apmas", 59, verified=False
    ),
    "master_product": MrErpModule(
        "master_product", "impstkmas", 353, None, "product_master", "stkmas", 24, verified=False
    ),
}


def get_module(doc_type: str) -> MrErpModule:
    m = MODULES.get(doc_type)
    if not m:
        raise ValueError(f"unknown mrerp doc_type={doc_type!r}; known={list(MODULES)}")
    return m
