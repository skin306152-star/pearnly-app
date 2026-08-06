# -*- coding: utf-8 -*-
"""HEIC/HEIF 解码注册(单一事实源)。

iPhone 相册原生是 HEIC,Pillow 默认解不开,靠 pillow-heif 的 register_heif_opener 挂上
opener。此前 image_store / workorder.intake_prep / 两处测试各自内嵌同一段 try-import +
注册,注册动作本身要幂等:重复注册只是把同一 opener 再挂一遍,不该再碰。统一走这里,
注册前先看 Pillow 的已注册扩展表,已带 .heic/.heif 就不重复挂;依赖没装静默跳过
(HEIC 会按「解不开」走 not_an_image 兜底,别的格式不受影响)。
"""

from __future__ import annotations

from PIL import Image


def register_heif() -> None:
    """幂等注册 pillow-heif 的 Pillow opener。"""
    try:
        from pillow_heif import register_heif_opener
    except ImportError:
        return
    known = Image.registered_extensions()
    if ".heic" in known or ".heif" in known:
        return
    register_heif_opener()
