# -*- coding: utf-8 -*-
"""
本地模板推断引擎(ADR-006 · S1)。

职责:只决定"这文件的哪几列是 日期/描述/存/取/余额/带符号金额",产出与
bank_recon_v2._parse_stmt_sheet 完全兼容的 col_map:

    {"date": i, "description": i, "withdrawal": i, "deposit": i, "balance": i, "amount": i}

_parse_stmt_sheet 至少需要 date + balance(+ withdrawal|deposit|amount 之一)。
本引擎自包含(不 import bank_recon_v2 · 防循环 + 保持轻量可离线测)· 只共享 col_map 这个"格式契约"。

三步:
  1. 表头同义词命中(中/英/泰/日/越)—— 覆盖比现有 _find_stmt_header 更全。
  2. 数据形状补缺 —— 日期列(多数行像日期)、金额列(多数行像钱)、余额列(钱列且几乎每行有值)、
     描述列(文本)。
  3. 余额链校验 —— 上一行余额 + 存 − 取 ≈ 这一行余额,≥80% 行对得上 = 高信心。
高信心可自动套用;否则交回上层走"用户确认一次"。AI 建议是可选 hook(本地低信心时调一次)。
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from services.importer.keys import _STMT_KEYS, _GL_KEYS, build_header_signature  # noqa: F401
from services.importer.ai_mapping import ai_mapping_enabled, suggest_mapping_with_ai  # noqa: F401
from services.importer.synonyms import (  # noqa: F401
    DATE_H,
    DESC_H,
    DEPOSIT_H,
    WITHDRAWAL_H,
    BALANCE_H,
    AMOUNT_H,
)
from services.importer.gl_inference import (  # noqa: F401
    _map_gl_by_header,
    _fill_gl_by_shape,
    infer_gl_col_map,
    validate_gl_shape,
)

# 值coercion 原语已抽到 services/importer/coerce.py(REFACTOR-WA-B1 · 2026-05-29)· 叶子模块防循环
from services.importer.coerce import (
    _norm,
    hit,
    to_float,
    parse_date,
    is_date_like,
    is_amount_like,
)  # noqa: F401


# ── 读文件 ──────────────────────────────────────────────────────────
def load_tabular_sheets(file_bytes: bytes, filename: str) -> List[Tuple[str, List[List[Any]]]]:
    """csv/xlsx/xls → [(sheet_name, rows)]。读不了返 []。"""
    ext = Path(filename or "").suffix.lower()
    try:
        if ext == ".csv":
            text = file_bytes.decode("utf-8-sig", errors="replace")
            return [("csv", [row for row in csv.reader(io.StringIO(text))])]
        if ext in {".xlsx", ".xlsm"}:
            import openpyxl

            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
            try:
                return [
                    (ws.title, [list(r) for r in ws.iter_rows(values_only=True)])
                    for ws in wb.worksheets
                ]
            finally:
                try:
                    wb.close()
                except Exception:
                    pass
        if ext == ".xls":
            import xlrd

            wb = xlrd.open_workbook(file_contents=file_bytes)
            return [
                (
                    wb.sheet_by_index(i).name,
                    [wb.sheet_by_index(i).row_values(r) for r in range(wb.sheet_by_index(i).nrows)],
                )
                for i in range(wb.nsheets)
            ]
    except Exception:
        return []
    return []


# ── 指纹 + 预览 ─────────────────────────────────────────────────────


def preview_rows(raw_rows: List[List[Any]], start: int, limit: int = 20) -> List[List[str]]:
    return [
        [str(c if c is not None else "").strip()[:120] for c in row]
        for row in raw_rows[start : start + limit]
    ]


# ── statement 列推断 ────────────────────────────────────────────────


def _map_by_header(header_row: List[Any]) -> Dict[str, int]:
    """同义词命中(顺序与现有 _map_bank_stmt_cols 一致 · 优先 withdrawal 再 deposit)。"""
    cm: Dict[str, int] = {}
    for i, cell in enumerate(header_row):
        h = _norm(cell)
        if not h:
            continue
        if "date" not in cm and hit(h, DATE_H):
            cm["date"] = i
        elif "description" not in cm and hit(h, DESC_H):
            cm["description"] = i
        elif "withdrawal" not in cm and hit(h, WITHDRAWAL_H):
            cm["withdrawal"] = i
        elif "deposit" not in cm and hit(h, DEPOSIT_H):
            cm["deposit"] = i
        elif "balance" not in cm and hit(h, BALANCE_H):
            cm["balance"] = i
        elif "amount" not in cm and hit(h, AMOUNT_H):
            cm["amount"] = i
    return cm


def _fill_by_shape(raw_rows: List[List[Any]], header_idx: int, cm: Dict[str, int]) -> None:
    """用数据形状补 header 没命中的列(只用强信号 · 保守)。"""
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

    # 钱列:多数行像金额
    money = []
    for c in range(max_cols):
        if c in used:
            continue
        n = sum(1 for v in col(c) if is_amount_like(v))
        if n >= 3:
            money.append((c, n, sum(1 for v in col(c) if str(v or "").strip() != "")))

    if "balance" not in cm and money:
        # 余额列:钱列里"几乎每行都有值"的那列(余额每行都印)
        bal_c = max(money, key=lambda m: (m[2], m[1]))[0]
        cm["balance"] = bal_c
        used.add(bal_c)

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
            used.add(best)

    # 方向/金额列:剩下的钱列
    if "deposit" not in cm and "withdrawal" not in cm and "amount" not in cm:
        rest = [c for c, _n, _nv in money if c not in used]
        if len(rest) >= 2:
            # 两列方向(谁存谁取由余额链定 · 先给个猜测交用户/校验)
            cm["deposit"], cm["withdrawal"] = rest[0], rest[1]
        elif len(rest) == 1:
            cm["amount"] = rest[0]  # 单一带符号金额列


def validate_by_balance(
    raw_rows: List[List[Any]], header_idx: int, cm: Dict[str, int], min_checked: int = 3
) -> Tuple[bool, float]:
    """余额链校验:上一行余额 + 存 − 取 ≈ 这一行余额。返回 (是否通过, 命中率)。

    没有 balance 列 → 无法校验 → (False, 0)。两列方向若读反,链会对不上 → 促使走用户确认。
    """
    if "balance" not in cm or "date" not in cm:
        return False, 0.0
    d_idx, b_idx = cm["date"], cm["balance"]
    wd_idx, dp_idx, amt_idx = cm.get("withdrawal", -1), cm.get("deposit", -1), cm.get("amount", -1)

    def cell(r, idx):
        return r[idx] if 0 <= idx < len(r) else ""

    prev: Optional[float] = None
    checked = ok = 0
    for raw in raw_rows[header_idx + 1 :]:
        if not any(c is not None and str(c).strip() != "" for c in raw):
            continue
        if parse_date(cell(raw, d_idx)) is None:
            continue
        bal = to_float(cell(raw, b_idx))
        wd = to_float(cell(raw, wd_idx)) if wd_idx >= 0 else 0.0
        dp = to_float(cell(raw, dp_idx)) if dp_idx >= 0 else 0.0
        if amt_idx >= 0 and wd_idx < 0 and dp_idx < 0:
            a = to_float(cell(raw, amt_idx))
            dp, wd = (a, 0.0) if a > 0 else (0.0, abs(a))
        if wd == 0.0 and dp == 0.0:
            continue
        if prev is not None:
            checked += 1
            if abs(round(prev + dp - wd, 2) - bal) <= 1.0:
                ok += 1
        prev = bal
    if checked < min_checked:
        return False, 0.0
    rate = ok / checked
    return rate >= 0.8, round(rate, 3)


def _rescue_direction_by_balance(
    raw_rows: List[List[Any]], header_idx: int, cm: Dict[str, int]
) -> Dict[str, int]:
    """方向列救援搜索:已知 date+balance 但当前映射余额链对不上时,在剩余数字列里
    枚举『单列净额 / 存-取两种顺序』· 用余额链验证选命中率最高的分配。

    解决:小文件 / 怪表头(F1/F2..)里存/取列各只有 1-2 个值 → 被 _fill_by_shape 的『≥3 行有钱』
    阈值漏掉 → 方向列没识别 → 余额链没机会跑(README #2 期望"余额链对就自动识别")。
    安全性:余额链验证是闸门 —— 搜错了 rate 仍低,调用方只在『严格更优』时采用(见 infer_stmt_col_map),
    已能验证通过的真实文件根本不进本函数,零回归。
    """
    if "date" not in cm or "balance" not in cm:
        return cm
    body = raw_rows[header_idx + 1 : header_idx + 31]
    max_cols = max((len(r) for r in body), default=0)
    fixed = {cm["date"], cm["balance"]}
    if "description" in cm:
        fixed.add(cm["description"])

    def col(idx: int) -> List[Any]:
        return [r[idx] if idx < len(r) else "" for r in body]

    cands = [
        c
        for c in range(max_cols)
        if c not in fixed and sum(1 for v in col(c) if is_amount_like(v)) >= 1
    ]
    base = {k: cm[k] for k in ("date", "balance", "description") if k in cm}
    best_cm, best_rate = cm, validate_by_balance(raw_rows, header_idx, cm)[1]
    trials: List[Dict[str, int]] = [{**base, "amount": c} for c in cands]
    for a in cands:
        for b in cands:
            if a != b:
                trials.append({**base, "deposit": a, "withdrawal": b})
    for t in trials:
        _passed, rate = validate_by_balance(raw_rows, header_idx, t)
        if rate > best_rate:
            best_cm, best_rate = t, rate
    return best_cm


def score_stmt(cm: Dict[str, int]) -> float:
    s = 0.0
    if "date" in cm:
        s += 0.25
    if "balance" in cm:
        s += 0.25
    if "description" in cm:
        s += 0.15
    if "deposit" in cm or "withdrawal" in cm or "amount" in cm:
        s += 0.30
    if "deposit" in cm and "withdrawal" in cm:
        s += 0.05
    return round(min(s, 1.0), 2)


def infer_stmt_col_map(
    raw_rows: List[List[Any]], max_scan: int = 30
) -> Tuple[int, Dict[str, int], str, float, List[str]]:
    """扫前 max_scan 行找最优表头 · 返回 (header_idx, col_map, confidence, balance_rate, reasons)。

    confidence:
      high   = 余额链校验通过(列对应数学可证)
      medium = 关键列齐全但无法用余额链证明(没余额列 / 校验样本不足)
      low    = 关键列不齐 · 交用户确认
    """
    best = (-1, {}, "low", 0.0, ["no header found"])
    # (balance_rate, header_not_data, header_word_hits, score)
    best_key = (-1.0, -1, -1, -1.0)
    for i, row in enumerate(raw_rows[:max_scan]):
        cm = _map_by_header(row)
        header_signal = len(cm)  # 表头词命中数(真表头行远多于数据行 · 优先级高于 score)
        _fill_by_shape(raw_rows, i, cm)
        # 必备:date + (wd|dep|amount)。balance 缺则后面无法校验/解析,信心下调。
        # 方向列救援:有 date+balance 但方向列没识别全(怪表头小文件 ≥3 阈值漏掉)·
        # 在剩余数字列里搜余额链能验证通过的存/取分配。先于"必备列"判定 · 让被漏掉的方向列补回来。
        if "balance" in cm and "date" in cm and not validate_by_balance(raw_rows, i, cm)[0]:
            cm = _rescue_direction_by_balance(raw_rows, i, cm)
        if "date" not in cm or not any(k in cm for k in ("withdrawal", "deposit", "amount")):
            continue
        passed, rate = validate_by_balance(raw_rows, i, cm)
        score = score_stmt(cm)
        if passed:
            conf = "high"
        elif "balance" in cm and header_signal >= 2 and score >= 0.85:
            conf = "medium"
        elif header_signal >= 2 and score >= 0.7:
            conf = "medium"
        else:
            conf = "low"
        # 候选『表头行』的日期列若本身解析成真日期 → 这是数据行(描述里碰巧含 รายการ/balance 等
        # 同义词会误得 header_signal),不能盖过真正的标签表头(压测 bank_large_3000:Column A..F 真表头
        # signal=0,数据行描述含 รายการ signal=1 → 误选数据行当表头 → 静默吞掉首笔交易 + 期初错)。
        d_idx = cm.get("date")
        hdr_cell = row[d_idx] if (d_idx is not None and 0 <= d_idx < len(row)) else ""
        header_not_data = 0 if parse_date(hdr_cell) is not None else 1
        reasons = [
            f"header_idx={i}",
            f"header_hits={header_signal}",
            f"header_not_data={header_not_data}",
            f"score={score}",
            f"bal_rate={rate}",
        ]
        # 排序键:余额链(数学可证)> 真标签表头(非数据行)> 表头词命中数 > score
        key = (rate, header_not_data, header_signal, score)
        if key > best_key:
            best_key = key
            best = (i, {k: cm[k] for k in _STMT_KEYS if k in cm}, conf, rate, reasons)
    return best


# ── GL 总账列推断(无余额链 · 靠表头词 + 形状)──────────────────────
