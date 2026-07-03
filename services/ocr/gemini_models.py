# -*- coding: utf-8 -*-
"""中心化 Gemini 模型选择 + 失败兜底升级(所有 OCR/Gemini 入口统一从这里取模型)。

目的:
  1. 一处可配(env)· 各入口不再硬编码模型名 —— grep "gemini-[0-9]" 应只剩本文件。
  2. 糊图/长文档解析失败(返回空、非法 JSON、截断)时,自动升级到更强兜底模型重试一次
     (默认 gemini-3.5-flash)· 把"换模型救不了的结构问题"和"换模型能救的图质问题"分开处理。

env 开关(都给了默认值,不配也能跑):
  OCR_FLASH_MODEL       默认 gemini-3.5-flash  (视觉/解析主力)
  OCR_FLASHLITE_MODEL   默认 gemini-3.5-flash  (轻量档;lite 在 vertex 不可用,与主力同模型)
  OCR_FALLBACK_MODEL    默认 gemini-3.5-flash  (兜底升级;设为空串关闭兜底)
  AGENT_BRAIN_MODEL     默认 gemini-2.5-flash  (对话大脑,与 OCR 档独立)

2026-07-03 Zihao 拍板:OCR 主力升 3.5-flash(57 张真件实测:速度 ~5x、总额 29/29 持平、
VAT 更全、单号更干净、token 省 ~23%、零回归);大脑不动,单独档钉 2.5(brain())。
"""

import logging
import os
from contextvars import ContextVar, Token
from typing import Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 请求级模型覆写(engine_policy 按 OCR_MODE 设置):tier 名 → 模型名。
# 非空覆写 > env > 默认;brain 不受覆写(大脑与 OCR 档独立是铁律)。
_OVERRIDE: ContextVar[Optional[Dict[str, str]]] = ContextVar("ocr_model_override", default=None)


def set_model_override(mapping: Optional[Dict[str, str]]) -> Token:
    """设置当前请求上下文的档位覆写;调用方负责用返回的 token reset。"""
    return _OVERRIDE.set(mapping or None)


def reset_model_override(token: Token) -> None:
    _OVERRIDE.reset(token)


def _override_for(tier: str) -> Optional[str]:
    m = _OVERRIDE.get()
    if m:
        v = (m.get(tier) or "").strip()
        if v:
            return v
    return None


def flash() -> str:
    return (
        _override_for("flash")
        or os.environ.get("OCR_FLASH_MODEL", "gemini-3.5-flash").strip()
        or "gemini-3.5-flash"
    )


def flash_lite() -> str:
    return (
        _override_for("flash_lite")
        or os.environ.get("OCR_FLASHLITE_MODEL", "gemini-3.5-flash").strip()
        or "gemini-3.5-flash"
    )


def brain() -> str:
    """LINE/网页对话 Agent 大脑模型——与 OCR 档独立配置,OCR 换模型不牵连大脑。"""
    return os.environ.get("AGENT_BRAIN_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def fallback() -> str:
    """更强兜底模型;设 OCR_FALLBACK_MODEL="" 可关闭兜底。"""
    ov = _override_for("fallback")
    if ov:
        return ov
    return os.environ.get("OCR_FALLBACK_MODEL", "gemini-3.5-flash").strip()


def escalate() -> str:
    """image-first 升级臂模型(低置信/关键字段缺时换更强模型重抽)。

    默认 = fallback()(gemini-3.5-flash · 2026-06-13 实测稳抽 tiny 发票号+年份);
    OCR_ESCALATE_MODEL 显式覆盖。与 fallback 同源,不另起一套档位。
    """
    return (
        _override_for("escalate") or os.environ.get("OCR_ESCALATE_MODEL", "").strip() or fallback()
    )


def best() -> str:
    """最强可用模型(3.5-flash 兜底档;关闭兜底时安全回落 2.5-flash)。

    给【低频单次】调用求最准用:大脑意图/分类/银行单解析等(非每页 OCR·不怕慢/贵)。
    """
    return fallback() or flash()


def tier_for_model(model_name: str) -> str:
    """Reverse of the tier→model resolution: classify a concrete model name back
    into a tier bucket. Guard sites that already hold a model name (bank GL/stmt,
    L2/L3 try_with_fallback) use this to route through the gateway transport,
    which speaks tiers. Unknown names fall back to "flash".

    多档共用同一模型名时(2026-07-03 起默认全 3.5)映到最中性的 "flash"——
    provider 解析回同一模型,行为无差,只影响档位标签。"""
    name = (model_name or "").strip()
    if name == flash():
        return "flash"
    if name == flash_lite():
        return "flash_lite"
    if name and name == fallback():
        return "fallback"
    if name and name == escalate():
        return "escalate"
    return "flash"


def models_with_fallback(primary: Optional[str] = None) -> List[str]:
    """[主模型, 兜底模型](去重去空)。调用方按序尝试:前一个失败/空 → 用下一个。"""
    out = [primary or flash()]
    fb = fallback()
    if fb and fb not in out:
        out.append(fb)
    return out


def try_with_fallback(
    call: Callable[[str], T],
    *,
    primary: Optional[str] = None,
    ok: Optional[Callable[[T], bool]] = None,
    label: str = "gemini",
) -> Optional[T]:
    """按 [主→兜底] 顺序调 call(model_name);返回首个『不抛错且 ok(结果)为真』的结果。

    call:   接收 model_name,执行一次 Gemini 调用并返回结果(失败可抛错或返回假值)。
    ok:     判定结果是否可接受(默认:非 None/非空)· 不可接受则升级到兜底再试。
    全部失败返回 None(调用方决定如何降级)。
    """
    accept = ok or (lambda r: r is not None and r != [] and r != {})
    last_exc: Optional[Exception] = None
    models = models_with_fallback(primary)
    for i, m in enumerate(models):
        try:
            r = call(m)
            if accept(r):
                if i > 0:
                    logger.info("[%s] 兜底模型 %s 成功(主模型未通过)", label, m)
                return r
            logger.warning("[%s] 模型 %s 结果不可接受 · 尝试下一个", label, m)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            logger.warning("[%s] 模型 %s 调用失败: %s", label, m, str(e)[:160])
    if last_exc is not None:
        logger.warning("[%s] 全部模型失败,最后错误: %s", label, str(last_exc)[:160])
    return None
