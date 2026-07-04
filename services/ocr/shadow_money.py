# -*- coding: utf-8 -*-
"""影子双跑:B 档(economy/2.5-lite)发票识别正常出结果后,后台异步再用 3.5 只读钱字段复核,
逐字段比对落库(shadow_money_log),量 B 真错率 + 现有置信闸抓取率。一个月后拍板 C 档。

铁律:fire-and-forget —— 超时/报错只落 status=failed,绝不改用户结果、不延迟、不计用户费、
不触发人工复核、不发通知。影子调用成本进 ocr_cost_log(mode=shadow_money_check,纯内部)。
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_SETTING_KEY = "shadow_money_check"
# 精简 prompt:只要四个钱字段、轻输出省 token(不复用完整管线 prompt)。
_PROMPT = (
    "You are auditing a Thai purchase receipt/tax invoice image. Read ONLY the money "
    "fields and return strict JSON with numbers only (no currency symbol, no thousands "
    'separator), use null when a field is absent: {"total_amount":<number|null>,'
    '"vat":<number|null>,"discount":<number|null>,"subtotal":<number|null>}. '
    "total_amount = the grand total actually paid."
)
_IMAGE_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
# 落库 short 名 → invoice_fields / 3.5 JSON 里的键。
_FIELD_KEYS = (
    ("total", "total_amount"),
    ("vat", "vat"),
    ("discount", "discount"),
    ("subtotal", "subtotal"),
)


def _switch() -> tuple[bool, float]:
    """(开?, min_amount)。env SHADOW_MONEY_CHECK=off 运维急停优先;否则读后台配置,默认 on。"""
    if os.environ.get("SHADOW_MONEY_CHECK", "").strip().lower() == "off":
        return False, 0.0
    try:
        from services.platform_settings import store

        row = store.get_setting(_SETTING_KEY) or {}
        if row.get("enabled") is False:
            return False, 0.0
        val = row.get("value") if isinstance(row.get("value"), dict) else {}
        return True, float(val.get("min_amount") or 0)
    except Exception:
        return True, 0.0  # 配置读不到默认 on(拍板直接开)· 故障不静默关掉采样


def _num(v) -> Optional[float]:
    """钱字段归一(复用单一事实源 money.normalize_money)+ 四舍五入到分:
    两侧同法归一后按 2dp 比对,防多余尾数造成假不一致。"""
    from services.ocr.money import normalize_money

    n = normalize_money(v)
    return round(n, 2) if n is not None else None


def _mime_for(filename: str) -> Optional[str]:
    name = (filename or "").lower()
    for ext, mime in _IMAGE_MIME.items():
        if name.endswith(ext):
            return mime
    return None


def schedule(
    *, content, filename, invoice_groups, confidence, history_id, tenant_id, user_id
) -> None:
    """挂后台影子(loop-safe 双分发)。前置不满足或调度故障 → 静默跳过,绝不抛。

    v1 只跑单票单图:多票(分组歧义)/ PDF(需渲染)跳过,保持比对干净、影子轻。"""
    try:
        on, min_amount = _switch()
        if not on or not tenant_id or not history_id:
            return
        if not invoice_groups or len(invoice_groups) != 1:
            return
        mime = _mime_for(filename)
        if not mime:
            return
        b_fields = (invoice_groups[0] or {}).get("invoice_fields") or {}
        if min_amount:
            b_total = _num(b_fields.get("total_amount"))
            if b_total is None or b_total < min_amount:
                return

        import asyncio

        args = (content, mime, b_fields, confidence, str(history_id), str(tenant_id), str(user_id))
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            loop.create_task(asyncio.to_thread(_run, *args))  # async 路由:后台线程,不堵 loop
        else:
            _run(*args)  # 缺口④ worker 线程(无运行中 loop)→ 直接同步
    except Exception:
        logger.warning("[shadow_money] schedule skipped", exc_info=True)


def _run(content, mime, b_fields, confidence, history_id, tenant_id, user_id) -> None:
    """后台工作体:调 3.5 只读钱字段 → 逐字段比对 → 落库。失败落 status=failed,全程不抛。"""
    from services.ocr import shadow_money_store

    status = "ok"
    s_fields: dict = {}
    try:
        s_fields = _call_35(content, mime, tenant_id, user_id, history_id)
    except Exception:
        status = "failed"
        logger.warning("[shadow_money] 3.5 shadow call failed", exc_info=True)

    if status == "ok":
        values, matches, match_all = _compare(b_fields, s_fields)
    else:
        values, matches, match_all = _b_only(b_fields)

    shadow_money_store.insert(
        tenant_id,
        history_id,
        values=values,
        matches=matches,
        match_all=match_all,
        b_confidence=str(confidence or ""),
        status=status,
    )


def _call_35(content, mime, tenant_id, user_id, history_id) -> dict:
    """强制 3.5(Vertex asia-se1)只读钱字段;成本进 ocr_cost_log(mode=shadow_money_check,不计用户费)。"""
    import time

    from core import db
    from services.ai_gateway import costing, transport
    from services.ocr import gemini_models

    tok = gemini_models.set_model_override({"flash": "gemini-3.5-flash"})
    t0 = time.time()
    try:
        outcome = transport.multimodal_to_json(
            _PROMPT,
            [(content, mime)],
            tier="flash",
            task=_SETTING_KEY,
            max_tokens=256,
            timeout_s=30,
            tenant_id=tenant_id,
            user_id=user_id,
        )
    finally:
        gemini_models.reset_model_override(tok)

    elapsed = int((time.time() - t0) * 1000)
    model = getattr(outcome, "model", "") or "gemini-3.5-flash"
    itok = int(getattr(outcome, "input_tokens", 0) or 0)
    otok = int(getattr(outcome, "output_tokens", 0) or 0)
    ok = bool(getattr(outcome, "ok", False))
    try:
        db.log_ocr_cost(
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            history_id=str(history_id),
            engine="shadow_money_check",
            pages=1,
            input_tokens=itok,
            output_tokens=otok,
            cost_thb=costing.estimate_thb(model, itok, otok),
            elapsed_ms=elapsed,
            model=model,
            mode=_SETTING_KEY,
            status="ok" if ok else "error",
        )
    except Exception:
        logger.warning("[shadow_money] cost log failed", exc_info=True)

    data = getattr(outcome, "data", None)
    if not ok or not isinstance(data, dict):
        raise RuntimeError(f"shadow 3.5 not ok: {getattr(outcome, 'error_kind', '?')}")
    return data


def _compare(b_fields, s_fields):
    """逐字段归一比对。both None→一致(都无值);一有一无→不一致;数值相等→一致。"""
    values, matches = {}, {}
    match_all = True
    for short, key in _FIELD_KEYS:
        b = _num(b_fields.get(key))
        s = _num(s_fields.get(key))
        m = b == s
        values[short] = (b, s)
        matches[short] = m
        match_all = match_all and m
    return values, matches, match_all


def _b_only(b_fields):
    """影子调用失败:只留 B 值,3.5 侧 None,match 记 None(不判一致/不一致)。"""
    values = {short: (_num(b_fields.get(key)), None) for short, key in _FIELD_KEYS}
    matches = {short: None for short, _ in _FIELD_KEYS}
    return values, matches, None
