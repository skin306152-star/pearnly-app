# -*- coding: utf-8 -*-
"""
Pearnly · 通用导入器 · GL 总账列推断(REFACTOR-WA-B1 · 2026-05-29 从 template_learning 抽出)

纯搬家 0 逻辑改 · 叶子(只依赖 coerce / keys / synonyms 叶子 · 不 import template_learning · 防循环)。
GL 没有余额链可做数学校验 → 只能靠表头词命中 + 数据形状(日期可解析 + 借/贷/金额有值)。
AI 兜底(suggest_mapping_with_ai)由调用方 bank_recon_v2 编排 · 本模块不涉。

  · _map_gl_by_header  GL 表头同义词命中
  · _fill_gl_by_shape  形状补列(date / 借贷或 amount / description)
  · infer_gl_col_map   主入口 · 返 (header_idx, col_map, confidence, reasons)
  · validate_gl_shape  给 AI 建议 col_map 把关(同 infer 内联口径抽出复用)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from services.importer.coerce import _norm, hit, is_date_like, is_amount_like, parse_date, to_float
from services.importer.keys import _GL_KEYS
from services.importer.synonyms import (
    DATE_H,
    DESC_H,
    BALANCE_H,
    AMOUNT_H,
    GL_DEBIT_H,
    GL_CREDIT_H,
    GL_DOC_H,
    GL_ACCOUNT_H,
)


def _map_gl_by_header(header_row: List[Any]) -> Dict[str, int]:
    """GL 表头同义词命中(顺序与 bank_recon_v2._map_gl_cols 一致)。"""
    cm: Dict[str, int] = {}
    for i, cell in enumerate(header_row):
        h = _norm(cell)
        if not h:
            continue
        if "date" not in cm and hit(h, DATE_H):
            cm["date"] = i
        elif "doc_no" not in cm and hit(h, GL_DOC_H):
            cm["doc_no"] = i
        elif "description" not in cm and hit(h, DESC_H):
            cm["description"] = i
        elif "debit" not in cm and hit(h, GL_DEBIT_H):
            cm["debit"] = i
        elif "credit" not in cm and hit(h, GL_CREDIT_H):
            cm["credit"] = i
        elif "account" not in cm and hit(h, GL_ACCOUNT_H):
            cm["account"] = i
        elif "balance" not in cm and hit(h, BALANCE_H):
            cm["balance"] = i
        elif "amount" not in cm and hit(h, AMOUNT_H):
            cm["amount"] = i
    return cm


def _fill_gl_by_shape(raw_rows: List[List[Any]], header_idx: int, cm: Dict[str, int]) -> None:
    body = raw_rows[header_idx + 1 : header_idx + 31]
    max_cols = max((len(r) for r in body), default=0)
    used = set(cm.values())

    def col(idx: int) -> List[Any]:
        return [r[idx] if idx < len(r) else "" for r in body]

    if "date" not in cm:
        best, best_n = None, 0
        for c in range(max_cols):
            n = sum(1 for v in col(c) if is_date_like(v))
            if n > best_n:
                best, best_n = c, n
        if best is not None and best_n >= 3:
            cm["date"] = best
            used.add(best)
    # 钱列 → 借/贷(两列)或 amount(单列)
    if not any(k in cm for k in ("debit", "credit", "amount")):
        money = [
            c
            for c in range(max_cols)
            if c not in used and sum(1 for v in col(c) if is_amount_like(v)) >= 3
        ]
        if len(money) >= 2:
            cm["debit"], cm["credit"] = money[0], money[1]
        elif len(money) == 1:
            cm["amount"] = money[0]
    if "description" not in cm:
        best, best_n = None, 0
        for c in range(max_cols):
            if c in used:
                continue
            vals = [str(v or "").strip() for v in col(c)]
            n = sum(
                1 for v in vals if len(v) >= 3 and not is_amount_like(v) and not is_date_like(v)
            )
            if n > best_n:
                best, best_n = c, n
        if best is not None and best_n >= 3:
            cm["description"] = best


def infer_gl_col_map(
    raw_rows: List[List[Any]], max_scan: int = 30
) -> Tuple[int, Dict[str, int], str, List[str]]:
    """GL 列推断 · 返回 (header_idx, col_map, confidence, reasons)。

    GL 没有余额链可做数学校验 → 只能靠表头词命中 + 数据形状:
      high   = 表头明确命中 date + (debit&credit 或 amount)(+ account/doc 更好)· 列对应基本确定
      medium = 关键列齐但靠形状补 · 让用户确认更稳
      low    = 不齐 · 必须用户确认
    保守:GL 读反借贷/科目错代价高,拿不准一律交用户确认(不自动套用)。
    """
    best = (-1, {}, "low", ["no gl header found"])
    best_key = (-1, -1, -1.0)  # (header_not_data, header_word_hits, score)
    for i, row in enumerate(raw_rows[:max_scan]):
        cm = _map_gl_by_header(row)
        header_signal = len(cm)
        _fill_gl_by_shape(raw_rows, i, cm)
        # 必备:date + (debit|credit|amount)
        if "date" not in cm or not any(k in cm for k in ("debit", "credit", "amount")):
            continue
        # 形状校验:大部分数据行 日期可解析 + 借贷有钱
        body = raw_rows[i + 1 : i + 31]

        def _cell(r, idx):
            return r[idx] if 0 <= idx < len(r) else ""

        date_hits = sum(1 for r in body if parse_date(_cell(r, cm["date"])) is not None)
        money_hits = 0
        for r in body:
            vals = [to_float(_cell(r, cm[k])) for k in ("debit", "credit", "amount") if k in cm]
            if any(v != 0 for v in vals):
                money_hits += 1
        shape_ok = date_hits >= 3 and money_hits >= 3
        score = (
            0.2 * ("date" in cm)
            + 0.15 * ("description" in cm)
            + 0.2 * ("account" in cm)
            + 0.3 * any(k in cm for k in ("debit", "credit", "amount"))
            + 0.1 * ("doc_no" in cm)
        )
        # high 只在表头词明确(借+贷 或 amount,且 date 是表头词命中)时给
        strong_header = (
            "date" in _map_gl_by_header(row)
            and (("debit" in cm and "credit" in cm) or "amount" in cm)
            and header_signal >= 3
            and shape_ok
        )
        if strong_header:
            conf = "high"
        elif header_signal >= 2 and shape_ok:
            conf = "medium"
        else:
            conf = "low"
        # 同账单:候选表头行的日期列若本身是真日期 → 数据行(描述含同义词会误得 signal)· 不盖过真标签表头
        d_idx = cm.get("date")
        hdr_cell = row[d_idx] if (d_idx is not None and 0 <= d_idx < len(row)) else ""
        header_not_data = 0 if parse_date(hdr_cell) is not None else 1
        reasons = [
            f"header_idx={i}",
            f"header_hits={header_signal}",
            f"header_not_data={header_not_data}",
            f"date={date_hits}",
            f"money={money_hits}",
        ]
        key = (header_not_data, header_signal, score)
        if shape_ok and key > best_key:
            best_key = key
            best = (i, {k: cm[k] for k in _GL_KEYS if k in cm}, conf, reasons)
    return best


def validate_gl_shape(
    raw_rows: List[List[Any]], header_idx: int, cm: Dict[str, int], min_checked: int = 3
) -> Tuple[bool, float]:
    """GL 形状校验(GL 无余额链 · 用数据形状代替):大部分数据行 日期可解析 + 借/贷/金额有值。

    给 AI 建议的 col_map 把关用 —— 同 infer_gl_col_map 内联的 shape_ok 口径,抽出来复用。
    返回 (是否通过, 命中率)。没有 date 或没有钱列 → (False, 0)。
    """
    if "date" not in cm or not any(k in cm for k in ("debit", "credit", "amount")):
        return False, 0.0
    body = raw_rows[header_idx + 1 : header_idx + 31]

    def _cell(r, idx):
        return r[idx] if 0 <= idx < len(r) else ""

    date_hits = sum(1 for r in body if parse_date(_cell(r, cm["date"])) is not None)
    money_hits = 0
    for r in body:
        vals = [to_float(_cell(r, cm[k])) for k in ("debit", "credit", "amount") if k in cm]
        if any(v != 0 for v in vals):
            money_hits += 1
    checked = min(len(body), date_hits)  # 以可解析日期行做分母(空尾行不计)
    if checked < min_checked or date_hits < min_checked or money_hits < min_checked:
        return False, 0.0
    rate = min(date_hits, money_hits) / max(checked, 1)
    return True, round(rate, 3)
