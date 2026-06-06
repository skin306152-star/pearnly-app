# -*- coding: utf-8 -*-
"""发票品牌图渲染(logo / 印章 / 签名 · docs/16 §L4 / H)。

把账套上传的品牌图(存储 URL)解成**本地文件**画进 PDF:抬头 logo + 底部签字区(印章/签名)。
**只读已存本地文件,绝不渲染时 live-fetch 远程 URL**(慢 + 易失败);外链 / 缺图 / 坏图一律
优雅跳过(返空,不抛)。把图相关从 pdf.py 抽出,保各文件 <500。纯渲染叶子。
"""

from __future__ import annotations

from services.imaging.image_store import local_path_from_url


def brand_image(url, max_w_mm: float, max_h_mm: float):
    """品牌图 URL → 缩放进框(保宽高比)的 reportlab Image flowable;不可用返 None。"""
    path = local_path_from_url(url)
    if not path:
        return None
    try:
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.platypus import Image as RLImage

        iw, ih = ImageReader(str(path)).getSize()
        if not iw or not ih:
            return None
        ratio = min(max_w_mm * mm / iw, max_h_mm * mm / ih)
        return RLImage(str(path), width=iw * ratio, height=ih * ratio)
    except Exception:
        return None


def logo_flowables(seller: dict, mm, Spacer) -> list:
    """抬头 logo(居中)+ 间距;无 logo 返空。"""
    logo = brand_image((seller or {}).get("logo_url"), 50, 22)
    return [logo, Spacer(1, 2 * mm)] if logo else []


def signature_flowables(seller, P, cw, Table, TableStyle, colors, mm, Spacer, align_center) -> list:
    """底部签字区:印章 + 签名 + 授权签字标签,右对齐;两图都无返空。"""
    seal = brand_image((seller or {}).get("seal_url"), 26, 26)
    sign = brand_image((seller or {}).get("signature_url"), 42, 16)
    if not seal and not sign:
        return []
    stack = []
    if sign:
        stack.append([sign])
    if seal:
        stack.append([seal])
    stack.append([P("ผู้มีอำนาจลงนาม / Authorized Signature", align=align_center, size=8)])
    inner = Table(
        stack,
        style=[
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ],
    )
    holder = Table([["", inner]], colWidths=cw(120, 60))
    holder.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return [Spacer(1, 6 * mm), holder]
