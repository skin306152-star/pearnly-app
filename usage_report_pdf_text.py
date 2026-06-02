# -*- coding: utf-8 -*-
"""使用明细报告 · PDF 字体注册 + 泰文/CJK script-aware 文本渲染(reportlab 辅助)。"""

import os

_FONTS_REGISTERED = False
_BASE_FONT = "Helvetica"
_BOLD_FONT = "Helvetica-Bold"
_HAS_CJK = False
_HAS_THAI = False


def _try_register(name: str, path: str, subfont_index=None) -> bool:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if not os.path.exists(path):
        return False
    try:
        if subfont_index is not None:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont_index))
        else:
            pdfmetrics.registerFont(TTFont(name, path))
        return True
    except Exception:
        return False


def _register_fonts():
    """
    Register fonts. Reportlab can NOT consume PostScript-outline (CFF) TTC/OTF
    such as NotoSansCJK; we use TrueType-outline TTC/TTF instead:
      - WQY Zenhei (TTC, TrueType) — CJK
      - Noto Sans Thai (TTF) — Thai (covers ฿ U+0E3F)
      - Helvetica — Latin (built-in)
    """
    global _FONTS_REGISTERED, _BASE_FONT, _BOLD_FONT, _HAS_CJK, _HAS_THAI
    if _FONTS_REGISTERED:
        return _BASE_FONT, _BOLD_FONT

    # CJK
    cjk_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    for p in cjk_paths:
        if _try_register("PR-CJK", p, subfont_index=0):
            _HAS_CJK = True
            break

    # Thai
    thai_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/usr/share/fonts/truetype/tlwg/Norasi.ttf",
        "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
    ]
    thai_bold_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
        "/usr/share/fonts/truetype/tlwg/Norasi-Bold.ttf",
        "/usr/share/fonts/truetype/tlwg/Garuda-Bold.ttf",
    ]
    for p in thai_paths:
        if _try_register("PR-Thai", p):
            _HAS_THAI = True
            break
    for p in thai_bold_paths:
        if _try_register("PR-ThaiBold", p):
            break

    # Use CJK as base since it also covers Latin (WQY Zenhei has full ASCII).
    if _HAS_CJK:
        _BASE_FONT = "PR-CJK"
        _BOLD_FONT = "PR-CJK"  # WQY Zenhei TTC doesn't have a separate bold
    elif _HAS_THAI:
        _BASE_FONT = "PR-Thai"
        _BOLD_FONT = "PR-ThaiBold" if os.path.exists(thai_bold_paths[0]) else "PR-Thai"

    _FONTS_REGISTERED = True
    return _BASE_FONT, _BOLD_FONT


# --- character ranges for script-aware font switching ---
def _is_thai(cp: int) -> bool:
    return 0x0E00 <= cp <= 0x0E7F


def _is_cjk(cp: int) -> bool:
    # CJK Unified, Hiragana, Katakana, Halfwidth/Fullwidth, CJK Symbols
    return (0x3000 <= cp <= 0x9FFF) or (0xFF00 <= cp <= 0xFFEF) or (0x20000 <= cp <= 0x2FFFF)


def _script_runs(s: str):
    """Yield (script, text) runs where script in {'cjk','thai','latin'}."""
    if not s:
        return
    cur_script = None
    cur_text = []
    for ch in s:
        cp = ord(ch)
        if _is_thai(cp):
            sc = "thai"
        elif _is_cjk(cp):
            sc = "cjk"
        else:
            sc = "latin"
        if sc != cur_script and cur_text:
            yield (cur_script, "".join(cur_text))
            cur_text = []
        cur_script = sc
        cur_text.append(ch)
    if cur_text:
        yield (cur_script, "".join(cur_text))


def _xml_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_paragraph_text(s: str, bold: bool = False) -> str:
    """Return reportlab Paragraph markup with per-script <font> tags."""
    if not s:
        return ""
    cjk_font = (
        "PR-CJK"
        if _HAS_CJK
        else ("PR-Thai" if _HAS_THAI else ("Helvetica-Bold" if bold else "Helvetica"))
    )
    thai_font = "PR-ThaiBold" if (bold and _HAS_THAI) else ("PR-Thai" if _HAS_THAI else cjk_font)
    latin_font = "Helvetica-Bold" if bold else "Helvetica"
    parts = []
    for sc, txt in _script_runs(s):
        if sc == "thai":
            fn = thai_font
        elif sc == "cjk":
            fn = cjk_font
        else:
            fn = latin_font
        parts.append(f'<font name="{fn}">{_xml_escape(txt)}</font>')
    return "".join(parts)
