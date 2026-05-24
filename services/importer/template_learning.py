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
import hashlib
import io
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── 表头同义词(比 bank_recon_v2 现有词典更全 · 学习层专用)──────────────
DATE_H = {
    "วันที่",
    "วัน",
    "วันที่ทำรายการ",
    "วันที่เอกสาร",
    "date",
    "trans date",
    "transaction date",
    "posting date",
    "value date",
    "日期",
    "交易日",
    "交易日期",
    "记账日期",
    "ngày",
    "取引日",
}
DESC_H = {
    "รายการ",
    "รายละเอียด",
    "รายละเอียดรายการ",
    "description",
    "detail",
    "details",
    "particulars",
    "narration",
    "memo",
    "remark",
    "remarks",
    "note",
    "摘要",
    "描述",
    "交易摘要",
    "备注",
    "摘要说明",
    "diễn giải",
    "摘要・備考",
}
DEPOSIT_H = {
    "รายรับ",
    "รับ",
    "เงินรับ",
    "ฝากเงิน",
    "ฝาก",
    "เงินฝาก",
    "deposit",
    "deposits",
    "credit",
    "credit amount",
    "cr",
    "income",
    "receipt",
    "receipts",
    "in",
    "paid in",
    "money in",
    "存款",
    "存入",
    "入账",
    "收入",
    "贷方",
    "贷方金额",
    "gửi",
    "入金",
}
WITHDRAWAL_H = {
    "รายจ่าย",
    "จ่าย",
    "เงินจ่าย",
    "ถอนเงิน",
    "ถอน",
    "เงินถอน",
    "withdrawal",
    "withdrawals",
    "debit",
    "debit amount",
    "dr",
    "expense",
    "payment",
    "payments",
    "out",
    "paid out",
    "money out",
    "取款",
    "支取",
    "出账",
    "支出",
    "借方",
    "借方金额",
    "rút",
    "出金",
}
BALANCE_H = {
    "ยอดคงเหลือ",
    "คงเหลือ",
    "ยอด",
    "balance",
    "running balance",
    "closing balance",
    "available balance",
    "余额",
    "结余",
    "账户余额",
    "số dư",
    "残高",
}
AMOUNT_H = {
    "amount",
    "จำนวนเงิน",
    "จำนวน",
    "net amount",
    "金额",
    "金額",
    "số tiền",
    "金额(±)",
}
# GL 总账专用(借/贷/凭证/科目)· 借≈取(debit) 贷≈存(credit)
GL_DEBIT_H = {"เดบิต", "เดบิท", "debit", "debit amount", "dr", "借方", "借方金额", "ถอน", "จ่าย"}
GL_CREDIT_H = {"เครดิต", "credit", "credit amount", "cr", "贷方", "贷方金额", "ฝาก", "รับ"}
GL_DOC_H = {
    "เลขที่เอกสาร",
    "เอกสาร",
    "ใบสำคัญ",
    "doc",
    "doc no",
    "doc_no",
    "document no",
    "voucher",
    "voucher no",
    "reference",
    "ref",
    "凭证号",
    "凭证",
    "单据号",
}
GL_ACCOUNT_H = {
    "รหัสบัญชี",
    "เลขที่บัญชี",
    "บัญชี",
    "รหัส",
    "account",
    "account code",
    "account no",
    "acct",
    "gl account",
    "科目",
    "科目代码",
    "账号",
    "会计科目",
}


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def hit(header: Any, hints) -> bool:
    """短 ASCII 词(in/out/cr/dr)整词匹配防误命中;长词/泰中日越用子串。"""
    h = _norm(header)
    if not h:
        return False
    tokens = None
    for hint in hints:
        hl = hint.lower()
        if hl.isascii() and len(hl) <= 3:
            if tokens is None:
                tokens = set(re.split(r"[\s/().,_\-]+", h))
            if hl in tokens:
                return True
        elif hl in h:
            return True
    return False


def to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "").replace(" ", "").replace(" ", "")
    if not s or s in {"-", "–", "—"}:
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s.startswith("-"):
        neg, s = True, s[1:]
    if s.count(".") > 1:  # 1.234.56 千分点
        first, *rest = s.split(".")
        s = first + "".join(rest[:-1]) + "." + rest[-1]
    try:
        out = float(s)
        return -out if neg else out
    except Exception:
        return 0.0


def parse_date(value: Any) -> Optional[date]:
    """支持常见格式 + 泰历(年>2400 → −543)。"""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        d = value.date()
        return date(d.year - 543, d.month, d.day) if d.year > 2400 else d
    if isinstance(value, date):
        return date(value.year - 543, value.month, value.day) if value.year > 2400 else value
    text = re.sub(r"\s+00:00:00$", "", str(value).strip())
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            d = datetime.strptime(text[:10], fmt).date()
            return date(d.year - 543, d.month, d.day) if d.year > 2400 else d
        except Exception:
            pass
    return None


def is_date_like(v: Any) -> bool:
    return parse_date(v) is not None


def is_amount_like(v: Any) -> bool:
    if v is None or str(v).strip() == "":
        return False
    return to_float(v) != 0.0 or str(v).strip() in {"0", "0.0", "0.00"}


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
def build_header_signature(headers: List[Any]) -> str:
    normalized = [_norm(h) for h in headers if _norm(h)]
    return hashlib.sha1("|".join(normalized).encode("utf-8")).hexdigest()[:16]


def preview_rows(raw_rows: List[List[Any]], start: int, limit: int = 20) -> List[List[str]]:
    return [
        [str(c if c is not None else "").strip()[:120] for c in row]
        for row in raw_rows[start : start + limit]
    ]


# ── statement 列推断 ────────────────────────────────────────────────
_STMT_KEYS = ("date", "description", "withdrawal", "deposit", "balance", "amount")


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
_GL_KEYS = ("date", "doc_no", "account", "description", "debit", "credit", "balance", "amount")


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


# ── S7 · AI 低信心自动建议一次(ADR-006 §7)─────────────────────────
# 本地推断拿不准时,把『表头 + 前 20 行预览 + 本地猜测』发给 Gemini 要 col_map 建议,
# 再用余额链(账单)/ 形状(GL)本地校验;校验过才用并自动存。绝不发整份文件 / 密钥。
#   · temp=0 · 按 signature 磁盘缓存(同模板第二次不再烧钱)
#   · RECON_AI_MAPPING flag 可关(默认开)· 失败/超时静默返 None(退回用户确认 · 不阻断)
import os as _os
import json as _json

_AI_MAPPING_MODEL = _os.environ.get("RECON_AI_MAPPING_MODEL", "gemini-2.5-flash-lite")
_AI_MAPPING_PROMPT_VER = "v1"
_AI_MAPPING_CACHE_DIR = _os.environ.get("RECON_AI_MAPPING_CACHE_DIR", "").strip() or _os.path.join(
    _os.getcwd(), ".ai_mapping_cache"
)


def ai_mapping_enabled() -> bool:
    """RECON_AI_MAPPING 默认开 · 设 0/false/no/off 关闭。"""
    return _os.environ.get("RECON_AI_MAPPING", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _ai_cache_path(cache_key: str) -> str:
    safe = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    return _os.path.join(_AI_MAPPING_CACHE_DIR, safe + ".json")


def _ai_cache_get(cache_key: str) -> Optional[Dict[str, int]]:
    try:
        p = _ai_cache_path(cache_key)
        if _os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = _json.load(f)
            # 缓存命中也可能是『AI 当时回了 None』· 用哨兵区分,避免反复重试烧钱
            return data if isinstance(data, dict) else None
    except Exception:
        return None
    return None


def _ai_cache_has(cache_key: str) -> bool:
    try:
        return _os.path.exists(_ai_cache_path(cache_key))
    except Exception:
        return False


def _ai_cache_put(cache_key: str, value: Any) -> None:
    try:
        _os.makedirs(_AI_MAPPING_CACHE_DIR, exist_ok=True)
        p = _ai_cache_path(cache_key)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            _json.dump(value, f, ensure_ascii=False)
        _os.replace(tmp, p)
    except Exception:
        pass


def _valid_keys_for(document_type: str) -> Tuple[str, ...]:
    return _GL_KEYS if document_type == "gl" else _STMT_KEYS


def _coerce_ai_cm(raw: Any, document_type: str, n_cols: int) -> Optional[Dict[str, int]]:
    """把 AI 回的对象规整成 {合法键: 0<=列号<n_cols}。无可用列 → None。"""
    if not isinstance(raw, dict):
        return None
    valid = set(_valid_keys_for(document_type))
    out: Dict[str, int] = {}
    for k, v in raw.items():
        if k not in valid or v is None:
            continue
        try:
            idx = int(v)
        except (TypeError, ValueError):
            continue
        if 0 <= idx < n_cols:
            out[k] = idx
    # 必备:date + 至少一个钱列,否则建议没用
    money_keys = (
        ("debit", "credit", "amount")
        if document_type == "gl"
        else (
            "withdrawal",
            "deposit",
            "amount",
        )
    )
    if "date" not in out or not any(k in out for k in money_keys):
        return None
    return out


def suggest_mapping_with_ai(
    document_type: str,
    sheet_name: str,
    headers: List[Any],
    sample_rows: List[List[Any]],
    local_guess: Optional[Dict[str, int]] = None,
    api_key: str = "",
    signature: str = "",
) -> Optional[Dict[str, int]]:
    """ADR-006 §7 · 本地低信心时调一次 Gemini 要 column mapping 建议(列名→列号)。

    只发:sheet 名 + 表头 + 前 20 行预览(已截断) + 本地猜测。绝不发整份文件 / 密钥。
    返回规整后的 col_map(键见 _STMT_KEYS / _GL_KEYS)· 校验交调用方;任何异常/超时/关闭 → None。
    缓存:按 signature(+doc_type+prompt_ver)· 命中(含『当时回 None』哨兵)直接返回,不再调 API。
    """
    if not ai_mapping_enabled() or not api_key:
        return None
    headers = list(headers or [])
    n_cols = len(headers)
    if n_cols == 0:
        return None

    sig = signature or build_header_signature(headers)
    cache_key = f"{document_type}:{_AI_MAPPING_PROMPT_VER}:{sig}"
    if _ai_cache_has(cache_key):
        cached = _ai_cache_get(cache_key)  # 命中 None 哨兵 → 直接放弃(不重复烧钱)
        return _coerce_ai_cm(cached, document_type, n_cols) if cached else None

    result: Optional[Dict[str, int]] = None
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_AI_MAPPING_MODEL)

        # 表头带列号 · 让 AI 直接回列号(稳健 · 不用再按名字猜位置)
        indexed_headers = [
            {"col": i, "name": str(h if h is not None else "").strip()[:60]}
            for i, h in enumerate(headers)
        ]
        preview = [
            [str(c if c is not None else "").strip()[:60] for c in row[:n_cols]]
            for row in (sample_rows or [])[:20]
        ]
        if document_type == "gl":
            keys_doc = (
                "date, doc_no, account, description, debit, credit, balance, amount. "
                "debit/credit = 借方/贷方两列;若只有一列带符号净额(正=借 负=贷)用 amount(不要同时给 debit/credit)。"
            )
        else:
            keys_doc = (
                "date, description, withdrawal, deposit, balance, amount. "
                "withdrawal/deposit = 取/存两列;若只有一列带符号金额用 amount(不要同时给 withdrawal/deposit)。"
            )
        prompt = (
            "You map spreadsheet columns of a bank STATEMENT or general-ledger (GL) to standard "
            "fields, for financial reconciliation. You are given the header row (each column with "
            "its 0-based index), a preview of the first data rows, and a local heuristic guess.\n"
            f"document_type = {document_type}\n"
            f"sheet_name = {sheet_name!r}\n"
            f"valid field keys = {keys_doc}\n"
            "RULES:\n"
            "1. Return ONLY a JSON object mapping field key -> the 0-based COLUMN INDEX. "
            "Omit a field if no column matches. Do NOT invent columns.\n"
            "2. Use the header names AND the preview data shape to decide (dates look like dates, "
            "money columns hold numbers, balance is a near-every-row running number).\n"
            "3. Indices must be within range [0, {n}). Output JSON only, no markdown fences.\n".format(
                n=n_cols
            )
            + f"HEADER (col:name): {_json.dumps(indexed_headers, ensure_ascii=False)}\n"
            + f"PREVIEW (first rows): {_json.dumps(preview, ensure_ascii=False)}\n"
            + f"LOCAL_GUESS: {_json.dumps(local_guess or {}, ensure_ascii=False)}\n"
            + 'Example output: {"date":0,"description":3,"withdrawal":4,"deposit":5,"balance":6}'
        )
        resp = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "candidate_count": 1,
                "max_output_tokens": 1024,
            },
        )
        text = (getattr(resp, "text", "") or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text).rstrip("`").strip()
        result = _coerce_ai_cm(_json.loads(text), document_type, n_cols)
    except Exception:
        result = None

    # 缓存结果(含 None → 存 {} 哨兵 · 同模板第二次不再调 API)
    _ai_cache_put(cache_key, result if result else {})
    return result
