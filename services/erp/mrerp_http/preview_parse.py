# -*- coding: utf-8 -*-
"""MR.ERP 导入预览页(formrdpc)HTML 解析 · 纯函数(adapter 从此取用)。

标准库正则,不引 bs4:bs4 非 prod 依赖,直写运行期不能靠它。
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

_FORM_RE = re.compile(
    r'<form\b[^>]*\bid=["\'](frmimport\d+)["\'][^>]*>(.*?)</form>', re.IGNORECASE | re.DOTALL
)
_TAG_RE = re.compile(r"<(input|select|textarea)\b([^>]*?)/?>", re.IGNORECASE)
_ATTR_RE = re.compile(r'([\w-]+)\s*=\s*"([^"]*)"')
TAGSTRIP_RE = re.compile(r"<[^>]+>")
_HINT_KEYWORDS = ("ไม่พบ", "ผิดพลาด", "ไม่ถูกต้อง", "ซ้ำ", "ไม่ครบ")


def preview_hints(html: str) -> List[str]:
    """预览页里的泰文错误线索行(ไม่พบ/ผิดพลาด…)· 供「无可导入行」报错带上下文。"""
    if not html:
        return []
    hints: List[str] = []
    for line in TAGSTRIP_RE.sub("\n", html).split("\n"):
        line = line.strip()
        if not line or len(line) > 200 or line in hints:
            continue
        if any(k in line for k in _HINT_KEYWORDS):
            hints.append(line)
    return hints[:5]


def parse_preview_form(html: str) -> Tuple[List[Tuple[str, str]], List[str], Optional[str]]:
    """从预览 HTML 抽 form#frmimport1 的全部字段 + cbimport row_ids + 该 form 的 idus。

    确认表(sales_credit)只含 hidden input + cbimport 复选框,无 <select>。
    """
    mform = _FORM_RE.search(html)
    scope = mform.group(2) if mform else html
    fields: List[Tuple[str, str]] = []
    row_ids: List[str] = []
    idus_form: Optional[str] = None
    for _tag, attrs_str in _TAG_RE.findall(scope):
        attrs = {k.lower(): v for k, v in _ATTR_RE.findall(attrs_str)}
        name = attrs.get("name")
        if not name:
            continue
        if attrs.get("type", "").lower() == "checkbox":
            # 预览默认勾选的行才提交(cbimport[N])
            if "checked" in attrs_str.lower() or name.startswith("cbimport"):
                fields.append((name, attrs.get("value", "on")))
                key = name[len("cbimport") :].strip("[]")
                if name.startswith("cbimport") and key.isdigit():
                    row_ids.append(key)
            continue
        val = attrs.get("value", "")
        fields.append((name, val))
        if name in ("idus", "idus1") and val.strip():
            idus_form = val.strip()
    return fields, row_ids, idus_form
