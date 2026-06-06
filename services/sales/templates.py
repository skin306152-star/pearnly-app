# -*- coding: utf-8 -*-
"""发票模板预设(H 模板后端管道 · docs/16 §L4)。

策略 = 多套精选模板 + 每家自定义品牌(不做 upload-and-learn)。每个账套(workspace_clients)
存 template_id + brand_color + 品牌资产;渲染时按 template_id 选版式、套品牌色。视觉细节随
设计稿细化,这里搭管道:把 template_id 解析成 pdf.py 用的样式参数(强调色 / 表格线 / 表头底色)。
纯常量+解析叶子,不连库、不渲染。
"""

from __future__ import annotations

DEFAULT_TEMPLATE = "classic"

# 6 套预设(见 app.html 账套页)。accent=None 表示"用账套 brand_color"(品牌色模板);
# grid:full=全网格 / light=细线 / none=无线。font_scale 收紧紧凑版。
TEMPLATES = {
    "classic": {"accent": "#1A365D", "grid": "full", "font_scale": 1.0},
    "minimal": {"accent": "#374151", "grid": "light", "font_scale": 1.0},
    "brand": {"accent": None, "grid": "full", "font_scale": 1.0},
    "compact": {"accent": "#1A365D", "grid": "light", "font_scale": 0.9},
    "thai_official": {"accent": "#0B3D2E", "grid": "full", "font_scale": 1.0},
    "mono": {"accent": "#000000", "grid": "none", "font_scale": 1.0},
}

_FALLBACK_ACCENT = "#1A365D"


def _norm_hex(value, default: str) -> str:
    """归一化十六进制色:接受 #RGB/#RRGGBB,非法回落 default(防渲染抛错)。"""
    s = str(value or "").strip()
    if not s.startswith("#"):
        s = "#" + s
    body = s[1:]
    if len(body) in (3, 6) and all(c in "0123456789abcdefABCDEF" for c in body):
        return "#" + body.upper()
    return default


def resolve(template_id, brand_color=None) -> dict:
    """把账套的 template_id + brand_color 解析成渲染样式。未知模板回落 classic;
    品牌色模板(accent=None)用 brand_color,无则回落预设强调色。"""
    tpl = TEMPLATES.get(template_id or DEFAULT_TEMPLATE, TEMPLATES[DEFAULT_TEMPLATE])
    accent = tpl["accent"]
    if accent is None:
        accent = _norm_hex(brand_color, _FALLBACK_ACCENT)
    else:
        accent = _norm_hex(accent, _FALLBACK_ACCENT)
    return {
        "template_id": template_id or DEFAULT_TEMPLATE,
        "accent": accent,
        "grid": tpl["grid"],
        "font_scale": tpl["font_scale"],
    }
