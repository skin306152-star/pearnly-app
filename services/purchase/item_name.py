# -*- coding: utf-8 -*-
"""明细名称展示清洗(P2C · 确定性纯函数 · LINE 卡片与网页详情共用同一套规则)。

OCR 抽到的泰文细品名常带 POS 噪声(Cafe Amazon 的「TW」「T-」外带/堂食标记、「original」)、空/
纯数字括号,或整段读不出返「?????」/替换符。本层只清洗*展示名*,不改金额/VAT/复式账、不让 LLM
编名、不把不确定品名猜成具体商品:

  clean(raw)              去前导符号 + POS 噪声前缀 + 空/数字括号 + 乱码字符(?,�)
  is_unclear(raw)         清洗后有效字符 < 2 → True(整名不可读)
  display(raw, i, ph)     可读 → 清洗名;不可读 → 编号占位 ph.format(n=i)(语言由调用方传入)
  clean_doc_lines(lines)  get_doc 用:就地清洗每行 description(unclear → 空 + name_unclear 标记)

POS 噪声前缀按「独立 token + 后接分隔符」剥除,保护真名开头(TWG/T-Bone 不误伤)。raw 仍留库/日志
供调试,只在展示出口收口(对齐 P1F field_clean.serialize_supplier 范式)。
"""

from __future__ import annotations

import re

_GARBLE_RE = re.compile(r"[?�]")
# 空括号 / 纯数字·百分号括号:「()」「( )」「(0%)」「[25]」→ 噪声;「(ไม่หวาน)」「(Large)」保留。
_BRACKET_NOISE_RE = re.compile(r"[（(\[【]\s*[\d%.,\s]*\s*[)）\]】]")
_MEANINGFUL_RE = re.compile(r"[^\W_]", re.UNICODE)  # 字母/数字/泰文等真实字符(不含标点/下划线)
_LEADING_PUNCT = " \t-–—•·*●○▪‣:.|/"

# POS 噪声前缀(小写比对·须后接分隔符或结尾才剥 → 保护 TWG/T-Bone/Originality 等真名开头)。
_NOISE_PREFIXES = (
    "takeaway",
    "take away",
    "take-away",
    "dine in",
    "dine-in",
    "dinein",
    "to go",
    "togo",
    "tw",
    "t-",
    "original",
    "orig",
)


def _strip_leading_noise(s: str) -> str:
    while s:
        low = s.lower()
        for w in _NOISE_PREFIXES:
            if not low.startswith(w):
                continue
            rest = s[len(w) :]
            if rest and rest[0] not in _LEADING_PUNCT:
                continue  # 词后紧跟字母(TWG/T-Bone)→ 是真名一部分,不剥
            s = rest.lstrip(_LEADING_PUNCT)
            break
        else:
            break
    return s


def clean(raw) -> str:
    """清洗展示名:剔乱码字符 + 空/数字括号 + 前导符号 + POS 噪声前缀。可能返回 ''(整名不可读)。"""
    s = _GARBLE_RE.sub("", str(raw or ""))
    s = _BRACKET_NOISE_RE.sub(" ", s)
    s = s.strip().lstrip(_LEADING_PUNCT)
    s = _strip_leading_noise(s)
    return re.sub(r"\s{2,}", " ", s).strip()


def is_unclear(raw) -> bool:
    """清洗后真实字符 < 2 → 整名不可读(纯问号/纯符号/纯序号/空 → True)。"""
    return len(_MEANINGFUL_RE.findall(clean(raw))) < 2


def display_with_flag(raw, i: int, placeholder: str) -> tuple[str, bool]:
    """一次清洗 → (展示名, 是否不可读)。渲染循环用此一处,避免对同一 raw 跑两遍 clean()。"""
    cleaned = clean(raw)
    unclear = len(_MEANINGFUL_RE.findall(cleaned)) < 2
    return (placeholder.format(n=i) if unclear else cleaned), unclear


def display(raw, i: int, placeholder: str) -> str:
    """展示名:可读 → 清洗名;不可读 → 编号占位(placeholder 形如「รายการที่ {n}」,语言由调用方定)。"""
    return display_with_flag(raw, i, placeholder)[0]


def clean_doc_lines(lines: list) -> None:
    """get_doc 出口收口:就地清洗每行 description(POS 噪声/乱码 → 清洗名;整名不可读 → '' + 标记)。

    详情页/复核屏共用 get_doc → 一次收口三处(详情读 description 或占位、编辑表单灌空值待用户补)。
    name_unclear 仅当原值有内容却读不出(空名的已配产品行不误标),前端据此显「รายการที่ N」占位。
    """
    for ln in lines or []:
        raw = ln.get("description")
        cleaned = clean(raw)
        ln["description"] = cleaned
        ln["name_unclear"] = bool(str(raw or "").strip()) and not cleaned
