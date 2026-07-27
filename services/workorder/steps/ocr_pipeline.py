# -*- coding: utf-8 -*-
"""工单一件料 → 生产 OCR 管线读数(classify 的 _ocr_image 真实现)。

从 classify 抽出(单文件 <500 铁律 + 单一职责):classify 编排「取 OCR / 归堆 / 查重 / 落库」,
本模块只管「怎么调管线、怎么把它的产物拍平成 classify 认的那份契约」——两者变化的理由不同
(前者随裁决规则变,后者随管线契约与计费口径变)。

计费口径钉死在这里:max_pages = ocr_balance.PAGES_PER_ITEM。默认 max_pages=50 会把 30 页 PDF
整本跑完、全额落 ai_usage.cost_thb,而下面只取 pages[0] —— 烧 30 页收 1 页,既是收入漏损也是
「同一份票从 /home 挪到 /ai 就打 1/30」的可套利定价洞。收几页就烧几页,两个数一起改。
"""

from __future__ import annotations

from pathlib import Path

from services.workorder import storage
from services.workorder.steps import ocr_balance


def read_first_page(path: str) -> dict:
    """跑管线取第一页读数。api_key=None 与 tests/eval 的现成用法同口径(交由 ai_gateway 按调用
    环境解析),业务码本身不读取任何密钥文件。

    把 legacy 页字典的 fields 与闸报警字段(_needs_review / _validation_warnings /
    _confidence_band)拍平成一个 dict,供 sort.bin_ocr_fields 和 gate_reason 共用同一份契约。
    单测全部 patch 掉调用方绑定(classify._ocr_image),绝不触达真实付费调用。
    """
    from services.ocr.entrypoints import run_pipeline_for_file
    from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

    data = storage.read_bytes(path)  # 落盘密文解回明文再喂 OCR(双轨读)
    result = run_pipeline_for_file(
        data,
        Path(path).name,
        api_key=None,
        max_pages=ocr_balance.PAGES_PER_ITEM,
        document_type="invoice",
    )
    legacy = pipeline_result_to_legacy_dict(result)
    pages = legacy.get("pages") or []
    if not pages:
        return {}
    page = pages[0]
    fields = dict(page.get("fields") or {})
    fields["_needs_review"] = bool(page.get("_needs_manual_review") or legacy.get("_needs_review"))
    fields["_validation_warnings"] = list(page.get("_validation_warnings") or [])
    fields["_confidence_band"] = page.get("_confidence_band") or legacy.get("_confidence_band")
    fields["_ocr_engine"] = legacy.get("engine")  # 管线版本 → item_classified 证据(冻结用)
    return fields
