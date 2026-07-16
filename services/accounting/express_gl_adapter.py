# -*- coding: utf-8 -*-
"""Express 总账分录(GLJNLIT csv)→ GlRow 适配器(T4b · F2 对平 erp 侧 · Decimal 全程)。

Express GLJNLIT 每行一条分录:TRNTYP 0=借 1=贷,AMOUNT 恒正(方向只看 TRNTYP)。本层把它
整形成 GlRow(account_code=四段码、debit/credit 按 TRNTYP 定向)。AMOUNT 以字符串直进
Decimal(不经 float 中转),仅在 GlRow 边界转 float(GlRow 是展示型 float 契约,下游
shadow_gl_recon 经 str() 回 Decimal 清算,两位小数往返无损——与 gl_upload_adapter 同口径)。

csv 编码 utf-8-sig(Express 导出带 BOM,cp874 兜底);日期 YYYYMMDD 佛历(年减 543)如实解析,
但不参与对平(F2 只聚合科目发生额)。识别 = 表头含 VOUCHER/ACCNUM/TRNTYP 三列(分流入口)。
"""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable

from services.recon.bank_recon_types import GlRow

_ZERO = Decimal("0")
_BE_OFFSET = 543  # 佛历年 → 公历年

_COL_ACCOUNT = "ACCNUM"
_COL_TRNTYP = "TRNTYP"
_COL_VOUCHER = "VOUCHER"
_COL_AMOUNT = "AMOUNT"
_REQUIRED_COLS = (_COL_VOUCHER, _COL_ACCOUNT, _COL_TRNTYP)
_DATE_COLS = ("TRNDATE", "JVDATE", "DOCDATE", "JDATE", "DATE")
_DESC_COLS = ("REMARK", "DETAIL", "DESCRIPT", "DESC", "NARRATE")


def _decode(data: bytes) -> str:
    """Express 导出 csv 解码:utf-8-sig 优先(去 BOM),cp874 兜底(泰文旧编码)。"""
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp874", errors="replace")


def _dec(value) -> Decimal:
    """金额字符串 → Decimal(去千分位,空/解不出 → 0)。不经 float 中转。"""
    if value is None:
        return _ZERO
    if isinstance(value, Decimal):
        return value
    try:
        s = str(value).replace(",", "").strip()
        return Decimal(s) if s else _ZERO
    except InvalidOperation:
        return _ZERO


def _be_date(value) -> date | None:
    """YYYYMMDD 佛历字符串 → 公历 date(年减 543);格式不符 → None(不编日期)。"""
    s = str(value or "").strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        return date(int(s[:4]) - _BE_OFFSET, int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


def _first(row: dict, keys: Iterable[str]) -> str:
    """按候选键序取首个非空值(列名兼容多套 Express 导出)。"""
    for k in keys:
        v = row.get(k)
        if v not in (None, ""):
            return str(v).strip()
    return ""


def _header_set(data: bytes) -> set[str]:
    """读 csv 首行表头 → 大写规范列名集合(识别用)。"""
    for row in csv.reader(io.StringIO(_decode(data))):
        return {str(c).strip().upper() for c in row}
    return set()


def is_express_gl(data: bytes, filename: str) -> bool:
    """csv 且表头含 VOUCHER/ACCNUM/TRNTYP → Express GLJNLIT(分流到本适配器)。"""
    if (filename or "").rsplit(".", 1)[-1].lower() != "csv":
        return False
    header = _header_set(data)
    return all(c in header for c in _REQUIRED_COLS)


def gljnlit_rows_to_gl_rows(rows: Iterable[dict], source_file: str = ""):
    """GLJNLIT 字典行 → (GlRow 列表, 行级丢弃清单)。

    TRNTYP 0=借 1=贷,AMOUNT 恒正定向。无科目码 / TRNTYP 非 0/1 = 方向未知,如实丢一条
    issue 不臆造(状态诚实)。金额全程 Decimal,仅 GlRow 边界转 float。
    """
    out: list[GlRow] = []
    issues: list[str] = []
    for i, raw in enumerate(rows, start=1):
        r = {str(k).strip().upper(): v for k, v in raw.items()}
        code = str(r.get(_COL_ACCOUNT) or "").strip()
        trntyp = str(r.get(_COL_TRNTYP) or "").strip()
        if not code:
            issues.append(f"line {i}: 无 ACCNUM 科目码,如实丢弃")
            continue
        if trntyp not in ("0", "1"):
            issues.append(f"line {i}: TRNTYP={trntyp!r} 非 0/1,方向未知,如实丢弃")
            continue
        amount = _dec(r.get(_COL_AMOUNT))
        debit = amount if trntyp == "0" else _ZERO
        credit = amount if trntyp == "1" else _ZERO
        out.append(
            GlRow(
                date=_be_date(_first(r, _DATE_COLS)),
                doc_no=str(r.get(_COL_VOUCHER) or "").strip(),
                account_code=code,
                description=_first(r, _DESC_COLS),
                debit=float(debit),
                credit=float(credit),
                source_file=source_file,
            )
        )
    return out, issues


def parse_express_gl_csv(data: bytes, filename: str = ""):
    """Express GLJNLIT csv 字节 → (GlRow 列表, 行级丢弃清单)。"""
    reader = csv.DictReader(io.StringIO(_decode(data)))
    return gljnlit_rows_to_gl_rows(reader, source_file=filename)
