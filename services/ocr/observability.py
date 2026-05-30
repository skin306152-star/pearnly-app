# -*- coding: utf-8 -*-
"""
services/ocr/observability.py · REFACTOR-WA-OCRPERF Step0(观测先行)

结构化 per-page 计时观测 · 【纯观测 · 0 逻辑改 · 不碰抽取/扣费/模型调用】。
PipelinePageResult 已带 layer1_ms/layer2_ms/layer3_ms/total_ms/layer_chain/
trigger_reasons/layerN_input/output_tokens(见 pipeline.py PipelinePageResult)·
但 app.py recognize 此前只写总 elapsed。本模块把每页 layer 墙钟 + chain + 触发原因 +
token + 是否走 L3 结构化 logger.info 出来,供 OCRPERF 后续每步量化【改前 vs 改后】。

设计:
  - format_pipeline_timing(pipe_res) 纯函数 · 从 PipelineResult.pages 抽每页计时 dict ·
    【绝不抛】(观测崩了绝不能影响识别热路径)。
  - log_pipeline_timing(...) 逐页 logger.info 一行 JSON · 同样绝不抛。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("ocr.timing")


def _page_timing(pr: Any) -> Dict[str, Any]:
    chain = list(getattr(pr, "layer_chain", None) or [])
    return {
        "page": getattr(pr, "page_number", None),
        "chain": chain,
        "triggers": list(getattr(pr, "trigger_reasons", None) or []),
        "l1_ms": getattr(pr, "layer1_ms", None),
        "l2_ms": getattr(pr, "layer2_ms", None),
        "l3_ms": getattr(pr, "layer3_ms", None),
        "total_ms": getattr(pr, "total_ms", None),
        "l2_in": getattr(pr, "layer2_input_tokens", None),
        "l2_out": getattr(pr, "layer2_output_tokens", None),
        "l3_in": getattr(pr, "layer3_input_tokens", None),
        "l3_out": getattr(pr, "layer3_output_tokens", None),
        # 走没走 L3(疑难票视觉兜底)· chain 里出现 L3* 即算(含 L3_failed/L3_quota 等)
        "l3": any(str(c).startswith("L3") for c in chain),
    }


def format_pipeline_timing(pipe_res: Any) -> List[Dict[str, Any]]:
    """从 PipelineResult 抽每页计时 dict 列表 · 绝不抛(观测不影响识别)。"""
    out: List[Dict[str, Any]] = []
    try:
        pages = list(getattr(pipe_res, "pages", None) or [])
    except Exception:
        return out
    for pr in pages:
        try:
            out.append(_page_timing(pr))
        except Exception:
            continue
    return out


def log_pipeline_timing(pipe_res: Any, *, source: str = "recognize", filename: str = "") -> None:
    """逐页 logger.info 结构化 JSON 一行 · 失败静默(绝不影响识别热路径)。"""
    try:
        rows = format_pipeline_timing(pipe_res)
        for row in rows:
            entry = dict(row)
            entry["source"] = source
            entry["file"] = filename
            logger.info("ocr_timing %s", json.dumps(entry, ensure_ascii=False, default=str))
    except Exception as e:  # 观测绝不影响识别
        logger.debug("log_pipeline_timing failed (non-fatal): %s", e)
