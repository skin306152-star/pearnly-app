# -*- coding: utf-8 -*-
"""中心化 Gemini 模型选择 + 失败兜底升级(所有 OCR/Gemini 入口统一从这里取模型)。

目的:
  1. 一处可配(env)· 各入口不再硬编码模型名 —— grep "gemini-[0-9]" 应只剩本文件。
  2. 糊图/长文档解析失败(返回空、非法 JSON、截断)时,自动升级到更强兜底模型重试一次
     (默认 gemini-3.5-flash)· 把"换模型救不了的结构问题"和"换模型能救的图质问题"分开处理。

env 开关(都给了默认值,不配也能跑):
  OCR_FLASH_MODEL       默认 gemini-2.5-flash       (视觉/解析主力)
  OCR_FLASHLITE_MODEL   默认 gemini-2.5-flash-lite  (轻量文字)
  OCR_FALLBACK_MODEL    默认 gemini-3.5-flash       (兜底升级;设为空串关闭兜底)
"""

import logging
import os
from typing import Callable, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def flash() -> str:
    return os.environ.get("OCR_FLASH_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def flash_lite() -> str:
    return (
        os.environ.get("OCR_FLASHLITE_MODEL", "gemini-2.5-flash-lite").strip()
        or "gemini-2.5-flash-lite"
    )


def fallback() -> str:
    """更强兜底模型;设 OCR_FALLBACK_MODEL="" 可关闭兜底。"""
    return os.environ.get("OCR_FALLBACK_MODEL", "gemini-3.5-flash").strip()


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
