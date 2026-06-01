# -*- coding: utf-8 -*-
"""bank_stmt_extract.py · Pearnly · pdfplumber table + word-coordinate bank statement extractors (split from bank_recon_v2)."""

import logging
import re
from typing import Dict, List, Tuple

from services.recon.bank_recon_types import StatementRow
from services.recon.bank_recon_utils import (
    MIN_PLUMBER_ROWS,
    _to_float,
    _parse_date,
)
from services.recon.bank_stmt_balance import _stmt_bad_ratio

logger = logging.getLogger(__name__)


def _parse_kbank_pages(tables: List) -> Tuple[List[StatementRow], float, float]:
    """Parse KBank statement tables. Returns (rows, opening, closing)."""
    rows = []
    opening = 0.0
    closing = 0.0

    for table in tables:
        if not table or len(table) < 2:
            continue
        # Find header row
        header_idx = None
        col_date = col_desc = col_wd = col_dep = col_bal = -1
        for i, row in enumerate(table):
            cells = [str(c or "").strip().lower() for c in row]
            row_txt = " ".join(cells)
            if any(k in row_txt for k in ["วันที่", "date"]):
                header_idx = i
                for j, c in enumerate(cells):
                    if any(k in c for k in ["วันที่", "date"]) and col_date < 0:
                        col_date = j
                    if any(k in c for k in ["รายการ", "description", "detail"]) and col_desc < 0:
                        col_desc = j
                    if any(k in c for k in ["ถอน", "withdraw"]) and col_wd < 0:
                        col_wd = j
                    if any(k in c for k in ["ฝาก", "deposit", "credit"]) and col_dep < 0:
                        col_dep = j
                    if any(k in c for k in ["คงเหลือ", "balance"]) and col_bal < 0:
                        col_bal = j
                break

        if header_idx is None or col_date < 0:
            continue

        for row in table[header_idx + 1 :]:
            if not row or len(row) <= max(col_date, col_bal):
                continue
            raw_date = str(row[col_date] or "").strip()
            if not raw_date or raw_date.lower() in ("วันที่", "date", ""):
                continue
            desc = str(row[col_desc] or "").strip() if col_desc >= 0 else ""
            # Skip opening/closing balance marker rows
            if any(kw in desc.lower() for kw in ["ยอดยกมา", "ยอดยกไป", "brought forward"]):
                bal = _to_float(row[col_bal] if col_bal >= 0 else 0)
                if not opening:
                    opening = bal
                closing = bal
                continue
            d = _parse_date(raw_date)
            if d is None:
                continue
            wd = _to_float(row[col_wd]) if col_wd >= 0 and col_wd < len(row) else 0.0
            dep = _to_float(row[col_dep]) if col_dep >= 0 and col_dep < len(row) else 0.0
            bal = _to_float(row[col_bal]) if col_bal >= 0 and col_bal < len(row) else 0.0
            if wd == 0.0 and dep == 0.0 and bal == 0.0:
                continue
            if not opening and rows:
                pass  # will compute from first balance - first txn
            closing = bal
            rows.append(
                StatementRow(
                    date=d, description=desc, withdrawal=abs(wd), deposit=abs(dep), balance=bal
                )
            )
    # Infer opening from first transaction
    if rows and opening == 0.0:
        first = rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    return rows, opening, closing


def _parse_bbl_pages(tables: List) -> Tuple[List[StatementRow], float, float]:
    """Parse BBL statement tables (both printed and activity report formats)."""
    rows = []
    opening = 0.0
    closing = 0.0

    for table in tables:
        if not table or len(table) < 2:
            continue
        col_date = col_desc = col_wd = col_dep = col_bal = -1
        header_idx = None

        for i, row in enumerate(table):
            cells = [str(c or "").strip().lower() for c in row]
            row_txt = " ".join(cells)
            if any(k in row_txt for k in ["วันที่", "date", "รายการ"]):
                header_idx = i
                for j, c in enumerate(cells):
                    if any(k in c for k in ["วันที่", "date", "tran date"]) and col_date < 0:
                        col_date = j
                    if (
                        any(k in c for k in ["รายการ", "description", "particular", "detail"])
                        and col_desc < 0
                    ):
                        col_desc = j
                    if any(k in c for k in ["ถอน", "debit", "withdrawal"]) and col_wd < 0:
                        col_wd = j
                    if any(k in c for k in ["ฝาก", "credit", "deposit"]) and col_dep < 0:
                        col_dep = j
                    if any(k in c for k in ["คงเหลือ", "balance"]) and col_bal < 0:
                        col_bal = j
                break

        if header_idx is None or col_date < 0:
            continue

        for row in table[header_idx + 1 :]:
            if not row:
                continue
            raw_date = str(row[col_date] if col_date < len(row) else "").strip()
            if not raw_date:
                continue
            desc = str(row[col_desc] if col_desc >= 0 and col_desc < len(row) else "").strip()
            if any(
                kw in desc.lower() for kw in ["ยอดยกมา", "ยอดนำมา", "brought forward", "opening"]
            ):
                bal = _to_float(row[col_bal] if col_bal >= 0 and col_bal < len(row) else 0)
                if not opening:
                    opening = bal
                continue
            d = _parse_date(raw_date)
            if d is None:
                continue
            wd = _to_float(row[col_wd] if col_wd >= 0 and col_wd < len(row) else 0)
            dep = _to_float(row[col_dep] if col_dep >= 0 and col_dep < len(row) else 0)
            bal = _to_float(row[col_bal] if col_bal >= 0 and col_bal < len(row) else 0)
            if wd == 0.0 and dep == 0.0:
                continue
            closing = bal
            rows.append(
                StatementRow(
                    date=d, description=desc, withdrawal=abs(wd), deposit=abs(dep), balance=bal
                )
            )

    if rows and opening == 0.0:
        first = rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    return rows, opening, closing


def _parse_generic_pages(tables: List) -> Tuple[List[StatementRow], float, float]:
    """Generic fallback parser for unknown bank formats."""
    rows = []
    opening = 0.0
    closing = 0.0

    for table in tables:
        if not table or len(table) < 2:
            continue
        # Auto-detect column positions from header
        col_date = col_desc = col_wd = col_dep = col_bal = -1
        header_idx = 0

        for i, row in enumerate(table[:5]):
            cells = [str(c or "").strip().lower() for c in row]
            row_txt = " ".join(cells)
            if sum(1 for k in ["date", "วันที่", "description", "รายการ"] if k in row_txt) >= 2:
                header_idx = i
                for j, c in enumerate(cells):
                    if col_date < 0 and any(k in c for k in ["date", "วันที่", "วัน"]):
                        col_date = j
                    elif col_desc < 0 and any(
                        k in c for k in ["desc", "รายการ", "detail", "particular"]
                    ):
                        col_desc = j
                    elif col_wd < 0 and any(k in c for k in ["withdraw", "debit", "ถอน", "จ่าย"]):
                        col_wd = j
                    elif col_dep < 0 and any(k in c for k in ["deposit", "credit", "ฝาก", "รับ"]):
                        col_dep = j
                    elif col_bal < 0 and any(k in c for k in ["balance", "คงเหลือ", "ยอด"]):
                        col_bal = j
                break

        if col_date < 0:
            continue

        for row in table[header_idx + 1 :]:
            if not row or len(row) < 3:
                continue
            raw_date = str(row[col_date] if col_date < len(row) else "").strip()
            d = _parse_date(raw_date)
            if d is None:
                continue
            desc = str(row[col_desc] if col_desc >= 0 and col_desc < len(row) else "").strip()
            wd = _to_float(row[col_wd] if col_wd >= 0 and col_wd < len(row) else 0)
            dep = _to_float(row[col_dep] if col_dep >= 0 and col_dep < len(row) else 0)
            bal = _to_float(row[col_bal] if col_bal >= 0 and col_bal < len(row) else 0)
            if wd == 0.0 and dep == 0.0:
                continue
            closing = bal
            rows.append(
                StatementRow(
                    date=d, description=desc, withdrawal=abs(wd), deposit=abs(dep), balance=bal
                )
            )

    if rows and opening == 0.0 and rows[0].balance != 0.0:
        first = rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    return rows, opening, closing


# ─────────────────────────────────────────────────────────────────────────────
# v118.35.0.66 · 坐标感知内嵌文本解析(密集多页文本 PDF 漏读根治 · 免费 + 确定性)
# ─────────────────────────────────────────────────────────────────────────────
_COORD_WD_KW = ("ถอนเงิน", "ถอน", "withdrawal", "withdraw", "debit")
_COORD_DEP_KW = ("ฝากเงิน", "ฝาก", "deposit", "credit")
_COORD_BAL_KW = ("ยอดเงินในบัญชี", "ยอดคงเหลือ", "balance", "คงเหลือ")
_COORD_DATE = re.compile(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$")
_COORD_AMT = re.compile(r"^\(?-?[\d,]+\.\d{2}\)?-?$")


def _coord_amt(tok: str) -> float:
    """'1,255.00'→1255.0 · '(500.00)'/'500.00-'→-500.0(会计负数记法)。"""
    neg = tok.startswith("(") or tok.rstrip().endswith("-")
    v = float(re.sub(r"[(),\s\-]", "", tok) or 0)
    return -v if neg else v


def _coord_find_columns(words):
    """从『同一文本行同时出现余额列 + 至少一个存/取列关键词』的表头行取各列 x 中心。
    返回 {wd?, dep?, bal} 或 None。要求存/取为分立列(x 间距>20)· 否则(KBank 那种
    『ถอนเงิน / ฝากเงิน』合并列 · 无法靠 x 区分)返回 None · 交回上层走原路径/Gemini。

    用 y 容差(<8px)聚合表头词 · 不用固定分箱(泰文/拉丁字形上沿不同会被错分到相邻箱)。"""
    kw: list = []  # (y0, kind, x_center)
    for w in words:
        t = w[4]
        tl = t.lower()
        cx = (w[0] + w[2]) / 2
        if any(k in t or k in tl for k in _COORD_BAL_KW):
            kw.append((w[1], "bal", cx))
        elif any(k in t or k in tl for k in _COORD_WD_KW):
            kw.append((w[1], "wd", cx))
        elif any(k in t or k in tl for k in _COORD_DEP_KW):
            kw.append((w[1], "dep", cx))
    kw.sort()
    for y0, _k0, _c0 in kw:
        cols: Dict[str, float] = {}
        for y1, k1, c1 in kw:
            if abs(y1 - y0) < 8 and k1 not in cols:  # 同一表头行(y 容差)
                cols[k1] = c1
        if "bal" in cols and ("wd" in cols or "dep" in cols):
            if "wd" in cols and "dep" in cols and abs(cols["wd"] - cols["dep"]) < 20:
                return None  # 存取合并列 · x 无法区分 · 放弃
            return cols
    return None


def _coord_cluster(centers, gap=12):
    """把金额 token 的 x 中心做一维聚类:相邻间距 ≤gap 归同簇。
    返回 [(mean_x, count, min_x, max_x)](按 x 升序)。"""
    cl: List[list] = []
    for x in sorted(centers):
        if cl and x - cl[-1][-1] <= gap:
            cl[-1].append(x)
        else:
            cl.append([x])
    return [(sum(c) / len(c), len(c), min(c), max(c)) for c in cl]


def _coords_by_xcluster(doc):
    """v118.35.0.66 · 数据驱动列检测(表头法拿不到分立列时的兜底 · 主治 KBank 那种
    『ถอนเงิน / ฝากเงิน』合并列 + 表头无独立余额列)。

    思路:金额 token 的 x 一维聚类 → 最右显著簇 = 余额列、其余显著簇 = 金额列(存/取
    挨得近的子列会自然并入同一金额列)。以『余额 token』为行锚(每笔恰一个运行余额)·
    同 y 配金额 · 无配对金额的余额 = 期初/承上行(只更新 prev · 不当交易)· 方向由
    余额涨跌定(不靠 x 区分存取 → 合并列也能切对)。

    安全性:若把余额/金额列认错 → 余额涨跌与金额对不上 → _stmt_bad_ratio 高 → 上层弃用。
    返回 (rows, opening, closing) 或 ([],0,0)。
    """
    per_page = []
    amt_centers: List[float] = []
    for pno in range(doc.page_count):
        words = doc[pno].get_text("words")
        amts = [((w[0] + w[2]) / 2, w[1], w[4]) for w in words if _COORD_AMT.match(w[4])]
        dates = [((w[0] + w[2]) / 2, w[1], w[4]) for w in words if _COORD_DATE.match(w[4])]
        per_page.append((amts, dates))
        amt_centers.extend(a[0] for a in amts)
    if len(amt_centers) < MIN_PLUMBER_ROWS * 2:
        return [], 0.0, 0.0
    clusters = _coord_cluster(amt_centers)
    thr = max(5, len(amt_centers) * 0.02)
    sig = [c for c in clusters if c[1] >= thr]
    if len(sig) < 2:
        return [], 0.0, 0.0  # 至少要『金额列 + 余额列』
    bal_c = sig[-1]
    amt_cs = sig[:-1]

    def in_bal(x):
        return bal_c[2] - 6 <= x <= bal_c[3] + 6

    def in_amt(x):
        return any(c[2] - 6 <= x <= c[3] + 6 for c in amt_cs)

    rows: List[StatementRow] = []
    prev = None
    for amts, dates in per_page:
        bals = sorted([a for a in amts if in_bal(a[0])], key=lambda a: a[1])
        for _bx, by, bv in bals:
            b = _coord_amt(bv)
            paired = [a for a in amts if in_amt(a[0]) and abs(a[1] - by) < 5]
            if not paired:
                if prev is None:
                    prev = b  # 期初 B/F(无配对金额)· 设基准
                continue
            amt = abs(_coord_amt(paired[0][2]))
            dt = [x for x in dates if abs(x[1] - by) < 6]
            d = _parse_date(dt[0][2]) if dt else None
            # 方向按余额涨跌(prev 未知时暂记存款 · 交 _correct_direction 兜底)
            if prev is not None and b < prev:
                rows.append(
                    StatementRow(date=d, description="", withdrawal=amt, deposit=0.0, balance=b)
                )
            else:
                rows.append(
                    StatementRow(date=d, description="", withdrawal=0.0, deposit=amt, balance=b)
                )
            prev = b
    if len(rows) < MIN_PLUMBER_ROWS:
        return [], 0.0, 0.0
    fr = rows[0]
    opening = round((fr.balance or 0) - (fr.deposit - fr.withdrawal), 2)
    closing = rows[-1].balance or 0.0
    return rows, opening, closing


def _coords_by_header(doc):
    """v118.35.0.66 · 表头法:从表头定位 取/存/余额 三列 x · 金额按 x 归到对应列。
    适合存/取分立成列、表头列中心能代表数据列的版式(BAY/SCB)。返回 (rows, opening, closing)。"""
    cols = None
    rows: List[StatementRow] = []
    for pno in range(doc.page_count):
        words = doc[pno].get_text("words")  # (x0,y0,x1,y1,text,block,line,word)
        pg_cols = _coord_find_columns(words)
        if pg_cols:
            cols = pg_cols  # 每页若有表头就刷新 · 否则沿用上一页
        if not cols:
            continue
        bal_x = cols["bal"]
        dates = sorted([(w[1], w[4]) for w in words if _COORD_DATE.match(w[4])])
        amts = [((w[0] + w[2]) / 2, w[1], w[4]) for w in words if _COORD_AMT.match(w[4])]
        texts = [
            (w[0], w[1], w[4])
            for w in words
            if not _COORD_AMT.match(w[4]) and not _COORD_DATE.match(w[4])
        ]
        for i, (dy, dval) in enumerate(dates):
            d = _parse_date(dval)
            if d is None:
                continue
            nxt = dates[i + 1][0] if i + 1 < len(dates) else dy + 9999
            near = [a for a in amts if abs(a[1] - dy) < 14]
            if not near:
                continue  # 表头日期范围 / 无金额行 · 跳过
            wd = dep = 0.0
            bal = None
            for cx, _y, v in near:
                col = min(cols, key=lambda k: abs(cols[k] - cx))
                if col == "bal":
                    bal = _coord_amt(v)
                elif col == "wd":
                    wd = abs(_coord_amt(v))
                else:
                    dep = abs(_coord_amt(v))
            if wd == 0.0 and dep == 0.0:
                continue  # 只有余额没动额(期初/小计)· 不当交易
            # 描述:本行 y 区间内、余额列右侧的文字 token 拼接(best-effort)
            desc = " ".join(t for x, y, t in texts if dy - 2 <= y < nxt - 2 and x > bal_x + 15)[
                :120
            ]
            rows.append(
                StatementRow(
                    date=d,
                    description=desc,
                    withdrawal=wd,
                    deposit=dep,
                    balance=bal if bal is not None else 0.0,
                )
            )
    if len(rows) < MIN_PLUMBER_ROWS:
        return [], 0.0, 0.0
    fr = rows[0]
    opening = round((fr.balance or 0) - (fr.deposit - fr.withdrawal), 2)  # 数学反推期初
    closing = rows[-1].balance or 0.0
    return rows, opening, closing


def _parse_stmt_text_coords(file_bytes: bytes):
    """v118.35.0.66 · 用 PyMuPDF words 的 x 坐标按列还原密集文本 PDF(BAY/SCB/KBank 等)。

    根因:get_text() 线性化丢列位置 → 存/取无法区分(BAY 314 存被全判成取 → 余额链坏
    → 触发 Gemini · 再被 Gemini 漏读 30-40%)。

    两套策略都跑、按『余额链可信度』取优(不靠猜哪套适用):
      A) 表头法 `_coords_by_header`:表头列中心 → 金额按 x 归列(BAY/SCB)。
      B) 数据驱动 `_coords_by_xcluster`:金额 x 聚类找列、方向由余额涨跌定(KBank 那种
         存取子列挨太近、表头列中心代表不了数据列的版式)。
    取 `_stmt_bad_ratio` 更低者(并列取行数更多)· 都拿不到 → 返回空交回上层。
    返回 (rows, opening, closing)。
    """
    try:
        import fitz

        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception:
        return [], 0.0, 0.0
    cands = []
    for fn in (_coords_by_header, _coords_by_xcluster):
        try:
            r, op, cl = fn(doc)
        except Exception:
            r, op, cl = [], 0.0, 0.0
        if len(r) >= MIN_PLUMBER_ROWS:
            # 排序键:余额链坏占比升序 · 再按行数降序(并列取更全)
            cands.append((round(_stmt_bad_ratio(r, op), 3), -len(r), r, op, cl))
    if not cands:
        return [], 0.0, 0.0
    cands.sort(key=lambda c: (c[0], c[1]))
    _bad, _n, rows, opening, closing = cands[0]
    return rows, opening, closing
