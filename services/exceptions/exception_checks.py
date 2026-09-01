# -*- coding: utf-8 -*-
"""Pearnly · OCR 异常检测服务模块。

OCR 完成后异步跑异常规则。本模块只保留 confidence_low OCR 质量信号。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from core import db

logger = logging.getLogger("mr-pilot")

# OCR 置信度非 high 的复核信号。它不是发票对错的规则,故不进引擎,留在本 hook 内常跑。
EXC_RULE_CONFIDENCE_LOW = "confidence_low"


# 异常栏 2026-07-26 下线(Zihao 拍板:用下来毫无用处)。引擎默认不跑 —— 五个调用点
# (OCR persist / cache / LINE 两条 fastpath / history PUT 重跑)一律早退:不写 exceptions
# 表、不推 LINE 高危提醒。页面代码 / API / 历史数据全留着,复活置 EXCEPTIONS_ENGINE=1,
# 前端入口另按 src/home/route-table.ts 的下线注释放回。
def _engine_enabled() -> bool:
    """每次调用读一次 env:线上改环境变量重启即生效,测试也能就地 patch。"""
    return os.getenv("EXCEPTIONS_ENGINE", "0") == "1"


def _parse_money(raw) -> Optional[float]:
    """容错解析金额字符串 → float · 解析失败返回 None(history 路由重跑规则时复用)"""
    if raw is None:
        return None
    try:
        s = str(raw).replace(",", "").replace("฿", "").replace("THB", "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


async def _async_run_exception_checks(
    history_id: str,
    user_id: str,
    tenant_id: Optional[str],
    seller_name: Optional[str],
    invoice_no: Optional[str],
    total_amount: Optional[float],
    confidence: Optional[str],
    duplicate: Optional[Dict[str, Any]],
    fields: Optional[Dict[str, Any]] = None,
):
    """OCR 完成后异步跑规则 · 任何失败都吞掉 · 绝不影响主流程"""
    if not _engine_enabled():
        return
    try:
        fields = fields or {}
        logger.debug(
            f"[exception] hook IN hid={history_id} conf={confidence!r} "
            f"sub={fields.get('subtotal')!r} vat={fields.get('vat')!r} "
            f"total={total_amount!r} stax={fields.get('seller_tax')!r} "
            f"all_keys={list(fields.keys())}"
        )
        # ── confidence_low(非 high 即拦 · conf=None/空串 也拦)
        if (not confidence) or confidence != "high":
            if not db.is_exception_whitelisted(
                user_id, tenant_id, seller_name, EXC_RULE_CONFIDENCE_LOW
            ):
                _sev_1 = "medium" if confidence == "medium" else "high"
                db.insert_exception(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    history_id=history_id,
                    rule_code=EXC_RULE_CONFIDENCE_LOW,
                    severity=_sev_1,
                    seller_name=seller_name,
                    invoice_no=invoice_no,
                    total_amount=total_amount,
                    detail={"confidence": confidence},
                )
    except Exception as e:
        logger.warning(f"_async_run_exception_checks failed (hid={history_id}): {e}")
