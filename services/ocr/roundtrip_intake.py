# -*- coding: utf-8 -*-
"""收料口的回导短路:上传的若是我们自己导出的复核工作簿,直接确定性解析,不喂大模型。

会计的闭环最后一步是把改过的表格丢回收料口重录。这张表是我们自己写出去的 ——
每格什么含义我们一清二楚,再让 L2 去"理解"一遍网格,既多花钱又平白引入读错的可能
(实测:那条路把 6 张单据的网格丢给为扫描件写的提示词,它不知道这是多单据多行结构)。

故:表头指纹命中 → 走 erp_roundtrip_reader 逐格读,置信度 1.0、成本 0;
指纹不命中 → 返回 None,调用方照常回落通用表格路,不抢别人的活。

留在「待判」表里的票(会计还没裁决方向)会被带出来但标 needs_manual_review ——
不能悄悄丢掉,会计得知道这几张没处理。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from services.excel.erp_roundtrip_reader import (
    RoundtripParseError,
    parse_roundtrip_workbook,
)
from services.ocr.schemas_invoice import LineItem, ThaiInvoice
from services.ocr.schemas_results import PipelinePageResult, PipelineResult

logger = logging.getLogger(__name__)

ENGINE = "roundtrip_workbook"
_TABLE_EXTS = (".xlsx", ".xlsm", ".xls")


def _s(v: Any) -> str:
    """数值转字符串保持 ThaiInvoice 的「数字也存字符串」约定,并去掉 3.0 这种尾巴。"""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _line_items(items: List[Dict[str, Any]]) -> List[LineItem]:
    return [
        LineItem(
            name=_s(it.get("description")),
            qty=_s(it.get("qty")),
            price=_s(it.get("unit_price")),
            subtotal=_s(it.get("amount")),
        )
        for it in (items or [])
        if isinstance(it, dict)
    ]


def _to_invoice(fields: Dict[str, Any]) -> ThaiInvoice:
    return ThaiInvoice(
        invoice_number=_s(fields.get("invoice_number")) or None,
        date=_s(fields.get("date")) or None,
        seller_name=_s(fields.get("seller_name")),
        seller_tax=_s(fields.get("seller_tax")),
        buyer_name=_s(fields.get("buyer_name")),
        buyer_tax=_s(fields.get("buyer_tax")),
        subtotal=_s(fields.get("amount_before_vat")),
        vat=_s(fields.get("vat_amount")),
        total_amount=_s(fields.get("total_amount")) or None,
        category=_s(fields.get("category")),
        items=_line_items(fields.get("items")),
    )


def _page(n: int, fields: Dict[str, Any], needs_review: bool) -> PipelinePageResult:
    return PipelinePageResult(
        page_number=n,
        invoice=_to_invoice(fields),
        document_type="invoice",
        # 逐格读的,没有 OCR 不确定性;层链如实标成回导解析,别冒充跑过 L1/L2
        layer_chain=[ENGINE],
        layer1_avg_confidence=1.0,
        needs_manual_review=needs_review,
    )


def try_parse_roundtrip(file_bytes: bytes, filename: str) -> Optional[PipelineResult]:
    """是我们导出的复核工作簿 → 直接解析成 PipelineResult;不是 → None(调用方回落)。"""
    name = (filename or "").lower()
    if not file_bytes or not name.endswith(_TABLE_EXTS):
        return None
    t0 = time.time()
    try:
        parsed = parse_roundtrip_workbook(file_bytes)
    except RoundtripParseError:
        return None  # 别人的表格 —— 交回通用路
    except Exception as e:  # noqa: BLE001 — 解析崩了也只该降级,不该让整次上传失败
        logger.warning(f"roundtrip parse failed, falling back: {e}")
        return None

    pages: List[PipelinePageResult] = []
    for d in parsed["documents"]:
        fields = dict(d["fields"])
        # 方向由所在 Sheet 决定(= 会计的分类裁决)· 下游 explicit_direction 认这个键
        fields["direction"] = d["direction"]
        pages.append(_page(len(pages) + 1, fields, needs_review=False))
    for p in parsed["pending"]:
        # 会计没裁决方向的票:带出来但标人工 —— 不能静默丢掉
        pages.append(_page(len(pages) + 1, dict(p["fields"]), needs_review=True))

    if not pages:
        return None  # 空工作簿:当作没识别到,不返回 0 页的假成功

    logger.info(
        f"roundtrip intake: {len(parsed['documents'])} docs + "
        f"{len(parsed['pending'])} pending from {parsed['sheets']}"
    )
    return PipelineResult(
        pages=pages,
        page_count=len(pages),
        elapsed_ms=int((time.time() - t0) * 1000),
        engine=ENGINE,
        estimated_cost_thb=0.0,  # 逐格读 · 不调模型 · 零成本
    )
