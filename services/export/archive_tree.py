# -*- coding: utf-8 -*-
"""Drive 归档树路径/命名(纯逻辑 · 照逆向 Paypers schema · 契约 03 §2.2 / 04 §七B)。

归档树(根 Pearnly 替 Paypers · 主体目录 = workspace_client 套账主体):
    Pearnly/<主体>/<年>/
        ├─ 「<主体> - <年>」.gsheet                  报表(sheets.py 写)
        └─ <月: 06_มิถุนายน>/
             ├─ 证据/<日期>_<商户>_<id>/ → 原图.jpg   每票一独立子文件夹
             └─ 交会计/<日期>_<商户>_<id>.pdf          原图转 PDF

doc_id 在 文件夹名 / PDF 名 / Sheet ID 列 三处对得上(可追溯)。本模块只算路径段(list[str]),
不连 Google;drive.py 拿这些段逐层 ensure 文件夹再上传(隔离:主体目录由套账主体派生,
凭据按套账取 → 绝不跨套账串目录)。
"""

from __future__ import annotations

import re
from datetime import date

ROOT = "Pearnly"
EVIDENCE_DIR = "证据"
ACCOUNTANT_DIR = "交会计"

# 泰文月名(逆向 schema 月份夹 = "06_มิถุนายน")。
_TH_MONTHS = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]

# Drive 文件/夹名禁字符(/ \ 控制符)+ 收尾空白点。
_BAD = re.compile(r"[\\/\x00-\x1f]+")


def _safe(name: str, *, fallback: str = "_") -> str:
    """清洗成 Drive 安全的单段名:去 /\ 控制符、压空白、去收尾点空格;空→fallback。"""
    s = _BAD.sub(" ", str(name or "")).strip().strip(".").strip()
    s = re.sub(r"\s+", " ", s)
    return s or fallback


def month_folder(month: int) -> str:
    """月份夹名 "MM_泰文月名"(逆向格式)。month 越界 → 退 "MM"。"""
    if 1 <= month <= 12:
        return f"{month:02d}_{_TH_MONTHS[month - 1]}"
    return f"{int(month):02d}"


def sheet_name(subject: str, year: int) -> str:
    """报表名 "<主体> - <年>"。"""
    return f"{_safe(subject, fallback='主体')} - {year:04d}"


def _parse_date(doc_date) -> date:
    """doc_date(date / 'YYYY-MM-DD' / datetime)→ date。无法解析 → 抛 ValueError 由调用方处理。"""
    if isinstance(doc_date, date):
        return doc_date
    s = str(doc_date or "")[:10]
    return date.fromisoformat(s)


def doc_basename(doc_date, supplier: str, doc_id: str) -> str:
    """单据基名 "<年-月-日>_<商户>_<id>"(证据夹名 / PDF 名共用 · doc_id 三处串联)。"""
    d = _parse_date(doc_date)
    sup = _safe(supplier, fallback="供应商")
    did = _safe(doc_id, fallback="id")
    return f"{d.isoformat()}_{sup}_{did}"


def _subject_year_base(subject: str, year: int) -> list:
    return [ROOT, _safe(subject, fallback="主体"), f"{year:04d}"]


def evidence_folder_path(subject: str, doc_date, supplier: str, doc_id: str) -> list:
    """证据原图子夹路径段:Pearnly/主体/年/月/证据/<日期_商户_id>(每票一夹)。"""
    d = _parse_date(doc_date)
    return _subject_year_base(subject, d.year) + [
        month_folder(d.month),
        EVIDENCE_DIR,
        doc_basename(d, supplier, doc_id),
    ]


def accountant_dir_path(subject: str, doc_date) -> list:
    """交会计 PDF 所在夹路径段:Pearnly/主体/年/月/交会计(扁平·PDF 直放)。"""
    d = _parse_date(doc_date)
    return _subject_year_base(subject, d.year) + [month_folder(d.month), ACCOUNTANT_DIR]


def accountant_pdf_name(doc_date, supplier: str, doc_id: str) -> str:
    """交会计 PDF 文件名 "<日期_商户_id>.pdf"。"""
    return f"{doc_basename(doc_date, supplier, doc_id)}.pdf"


def subject_year_path(subject: str, year: int) -> list:
    """主体×年目录段 Pearnly/主体/年(Sheet 与各月夹的共同父)。"""
    return _subject_year_base(subject, year)
