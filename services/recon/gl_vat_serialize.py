# -*- coding: utf-8 -*-
"""GL/VAT 对账结果 JSON 序列化（DB 存储 & 前端响应·gl_vat_reconciler 拆分）。"""

from typing import List, Dict, Any
from dataclasses import asdict

from services.recon.gl_vat_types import ReconRow, GlVatSummary


def detail_to_json(detail: List[ReconRow]) -> List[Dict[str, Any]]:
    return [asdict(r) for r in detail]


def summary_to_json(summary: GlVatSummary) -> Dict[str, float]:
    return asdict(summary)


def detail_from_json(data: List[Dict[str, Any]]) -> List[ReconRow]:
    return [ReconRow(**r) for r in (data or [])]


def summary_from_json(data: Dict[str, Any]) -> GlVatSummary:
    return GlVatSummary(
        **(
            data
            or {
                "gl_total": 0,
                "gl_only_credit": 0,
                "gl_only_debit": 0,
                "vat_only_positive": 0,
                "vat_only_negative": 0,
                "vat_total": 0,
            }
        )
    )
