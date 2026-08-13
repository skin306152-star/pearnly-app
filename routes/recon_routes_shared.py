# -*- coding: utf-8 -*-
"""recon 路由跨组共享:user key · 上传预检估价 · 计费闸骨架与 402 信封。

计费判据(扩展名分类 / 字符与页估算 / 阶梯价)单一事实源在 services/billing/pricing;
这里只做 HTTP 层包装:UploadFile 读流估价、查不出计费状态 503(fail-closed)、盖不住
预估 402。402 信封的字段形状是前端契约(static/ai/ai-fail-render.js 逐字段读),
code / balance / estimated_cost / pages_used_this_month 一个都不能动。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Tuple

from fastapi import HTTPException

from core import db
from services.billing import account_status, pricing

logger = logging.getLogger(__name__)


def _user_key(user):
    return (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip() or None


async def estimate_upload_units(uploads) -> Tuple[int, int]:
    """UploadFile 版预检估价 (pdf_units, excel_chars) · 读流后 seek(0) 还原,不干扰后续解析重读。

    PDF 也读:预检按物理页数计,多页 PDF 不再按「1 件 1 页」低估打穿余额。"""
    pdf_units = 0
    excel_chars = 0
    for u in uploads or []:
        content = await u.read()
        await u.seek(0)
        p, c = pricing.estimate_recon_units([(content, getattr(u, "filename", None) or "")])
        pdf_units += p
        excel_chars += c
    return pdf_units, excel_chars


def insufficient_balance_detail(billing: dict, est_cost) -> dict:
    """402 信封(detail 体)· 前端契约,字段不许增删改名。"""
    return {
        "code": "insufficient_balance",
        "balance": billing.get("balance_thb", 0.0),
        "estimated_cost": float(est_cost),
        "pages_used_this_month": billing.get("pages_used_this_month", 0),
    }


def require_coverage_or_raise(billing: dict, pdf_units: int, excel_chars: int) -> None:
    """余额/套餐额度盖不住这批预估 → 402(信封带同一口径估价)。豁免由调用方先判。"""
    covers, est_cost = account_status.can_cover_estimate(billing, pdf_units, excel_chars)
    if not covers:
        raise HTTPException(402, detail=insufficient_balance_detail(billing, est_cost))


async def precheck_upload_billing(user_id, tenant_id, uploads, *, log_tag: str) -> dict:
    """同步 run 入口的计费预检闸 · 返回 billing dict(含 is_exempt 供扣费段复用)。

    查不出计费状态 → 503(fail-closed,与「余额不足 402」两条码绝不合并:一个叫用户
    稍后再试,一个叫用户去充值,见 account_status);豁免直接放行不读文件;其余按上传
    估价,盖不住 → 402。拒绝发生在读文件/花钱之前(lookup 失败时一个字节都没读)。
    """
    try:
        billing = db.get_billing_status_combined(str(user_id), tenant_id)
        if account_status.lookup_failed(billing):
            raise HTTPException(503, detail={"code": account_status.LOOKUP_ERROR})
        if not billing.get("is_exempt"):
            pdf_units, excel_chars = await estimate_upload_units(uploads)
            require_coverage_or_raise(billing, pdf_units, excel_chars)
        return billing
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[{log_tag}] billing pre-check failed: {e}", exc_info=True)
        raise HTTPException(503, detail={"code": account_status.LOOKUP_ERROR}) from e


def schedule_parse_charges(user_id, tenant_id, pairs, desc_label: str) -> None:
    """同步 run 入口的事后扣费(fire-and-forget)· 失败只记 log 不打断响应。

    pairs 形状与计费判据见 pricing.billed_units_for_parses(失败件/0 行件不收钱)。"""
    try:
        pdf_units, excel_chars = pricing.billed_units_for_parses(pairs)
        if pdf_units > 0:
            asyncio.create_task(
                asyncio.to_thread(
                    db.charge_ocr_async,
                    str(user_id),
                    tenant_id,
                    "pdf",
                    pdf_units,
                    None,
                    f"{desc_label} PDF · {pdf_units} 页",
                )
            )
        if excel_chars > 0:
            asyncio.create_task(
                asyncio.to_thread(
                    db.charge_ocr_async,
                    str(user_id),
                    tenant_id,
                    "excel",
                    excel_chars,
                    None,
                    f"{desc_label} Excel · {excel_chars} 字符",
                )
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"💳 {desc_label} async charge skip: {e}")
