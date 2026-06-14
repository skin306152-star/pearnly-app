# -*- coding: utf-8 -*-
"""image-first 两阶段抽取编排(灰度开关 · 阶段二 OCR 准)。

默认关(OCR_IMAGE_FIRST 未开)→ 主路径不变(L2 文字主 + L3 触发兜底)。开关开:
  ① 图直喂 gemini-2.5-flash 为主抽取(Vision L1 文字 + L2 草稿仅作 hint);
  ② 关键字段缺(发票号/总额)或低置信 → 升 gemini-3.5-flash 重抽(把①结果当 hint)。

依据 docs/smart-intake/05 附A(2026-06-13 prod 4 票 A/B:image-first 抽得≈Paypers,
3.5-flash 稳抽 tiny 发票号+年份)。**改 OCR 计费主路径**:默认关上线,prod 真 key 跑
scripts/_ocr_ab_probe.py A/B 确认更准再翻 OCR_IMAGE_FIRST=1(零风险灰度)。

refine / field_conf_fn 由 page_runner 注入(解耦 Gemini 调用 → 可纯单测两条路)。
"""

from __future__ import annotations

import os
from typing import Callable

# 关键字段缺/低于此阈值 → 升级臂(与触发 Rule 4 的 CONFIDENCE_THRESHOLD 同档 0.85)。
ESCALATE_CONF = float(os.environ.get("OCR_IMAGE_FIRST_ESCALATE_CONF", "0.85"))
_KEY_FIELDS = ("invoice_number", "total_amount")


def is_enabled() -> bool:
    """OCR_IMAGE_FIRST 开关(默认关 · 主路径不变)。"""
    return os.environ.get("OCR_IMAGE_FIRST", "").strip().lower() in ("1", "true", "yes", "on")


def needs_escalation(field_conf: dict, invoice) -> bool:
    """主抽(2.5-flash)结果是否需升级:关键字段缺 → True;字段在但词级置信 < 阈值 → True。"""
    for f in _KEY_FIELDS:
        val = str(getattr(invoice, f, "") or "").strip()
        if not val:
            return True
        conf = field_conf.get(f)
        if conf is not None and conf < ESCALATE_CONF:
            return True
    return False


def run(
    *,
    image_bytes,
    l1_page,
    l2_invoice,
    trigger_reasons,
    api_key,
    document_type,
    refine: Callable,
    field_conf_fn: Callable,
    primary_model: str,
    escalate_model: str,
) -> dict:
    """两阶段抽取。refine=refine_page(注入)·field_conf_fn=_field_confidences(注入)。

    返回 {invoice, layers, in_tokens, out_tokens, ms, escalated, models}。
    refine 抛 Layer3* 由调用方按现有 L3 错误语义处理(降级 L2 / 上抛)。
    """
    primary = refine(
        image_bytes=image_bytes,
        layer1_page=l1_page,
        layer2_invoice=l2_invoice,
        trigger_reasons=trigger_reasons,
        api_key=api_key,
        model_name=primary_model,
        document_type=document_type,
    )
    invoice = primary.invoice
    in_tok, out_tok, ms = primary.input_tokens, primary.output_tokens, primary.elapsed_ms
    layers = [f"IF:{primary_model}"]
    models = [primary_model]
    escalated = False

    fc = field_conf_fn(l1_page, invoice)
    if escalate_model and escalate_model != primary_model and needs_escalation(fc, invoice):
        esc = refine(
            image_bytes=image_bytes,
            layer1_page=l1_page,
            layer2_invoice=invoice,  # 主抽结果当 hint 喂更强模型
            trigger_reasons=trigger_reasons,
            api_key=api_key,
            model_name=escalate_model,
            document_type=document_type,
        )
        invoice = esc.invoice
        in_tok += esc.input_tokens
        out_tok += esc.output_tokens
        ms += esc.elapsed_ms
        layers.append(f"ESC:{escalate_model}")
        models.append(escalate_model)
        escalated = True

    return {
        "invoice": invoice,
        "layers": layers,
        "in_tokens": in_tok,
        "out_tokens": out_tok,
        "ms": ms,
        "escalated": escalated,
        "models": models,
    }
