# -*- coding: utf-8 -*-
"""bank_recon_utils.py · Pearnly · shared reconciliation constants, OCR result
cache (in-memory LRU + disk) and primitive parsing helpers.

Split verbatim from bank_recon_v2.py. Leaf module: stdlib only, imported by the
facade and the statement / GL parsing submodules. DATE_TOL_DAYS deliberately stays
in bank_recon_v2 (coupled to reconcile/scoring).
"""

import hashlib
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

AMOUNT_TOL = 0.02  # baht tolerance for amount matching
MIN_PLUMBER_ROWS = 3  # fallback to Gemini if pdfplumber yields < this
# Layer-2 date tolerance for reconcile + invoice-candidate matching. Single
# source of truth: the legacy module defined it twice (a dead =3 shadowed by a
# load-time =7); the runtime value has always been 7.
DATE_TOL_DAYS = 7

# v118.33.13.1 · in-memory cache for Gemini OCR results, keyed by SHA-256 of file bytes.
# Same PDF re-uploaded -> instant. Capped at 256 entries (~80 MB worst case), LRU eviction.
import collections as _collections

_GEMINI_STMT_CACHE: "_collections.OrderedDict[str, Dict[str, Any]]" = _collections.OrderedDict()
_GEMINI_GL_CACHE: "_collections.OrderedDict[str, Dict[str, Any]]" = _collections.OrderedDict()
_GEMINI_CACHE_MAX = 256


def _cache_get(
    cache: "_collections.OrderedDict[str, Dict[str, Any]]", key: str
) -> Optional[Dict[str, Any]]:
    if key in cache:
        cache.move_to_end(key)
        return cache[key]
    return None


def _cache_put(
    cache: "_collections.OrderedDict[str, Dict[str, Any]]", key: str, value: Dict[str, Any]
) -> None:
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > _GEMINI_CACHE_MAX:
        cache.popitem(last=False)


# v118.35.0.64 · 持久化磁盘缓存:跨进程/重启/多 worker 都一致。
# temp=0 保证『同图每次识别结果相同』· 磁盘缓存进一步保证『同图永不重算 + 永久一致』
# (内存缓存随进程重启清空 · 服务重启/多 worker 时会重新掷一次;磁盘缓存补这个洞)。
# 目录可用 PEARNLY_OCR_CACHE_DIR 覆盖 · 默认 cwd/.ocr_cache(生产 /opt/mrpilot · 跨重启持久)。
import os as _os
import json as _json

_OCR_DISK_CACHE_DIR = _os.environ.get("PEARNLY_OCR_CACHE_DIR", "").strip() or _os.path.join(
    _os.getcwd(), ".ocr_cache"
)


def _disk_cache_path(key: str) -> str:
    safe = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return _os.path.join(_OCR_DISK_CACHE_DIR, safe + ".json")


def _disk_cache_get(key: str) -> Optional[Dict[str, Any]]:
    try:
        p = _disk_cache_path(key)
        if _os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return _json.load(f)
    except Exception:
        pass
    return None


def _disk_cache_put(key: str, value: Dict[str, Any]) -> None:
    try:
        _os.makedirs(_OCR_DISK_CACHE_DIR, exist_ok=True)
        p = _disk_cache_path(key)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            _json.dump(value, f, ensure_ascii=False)
        _os.replace(tmp, p)  # 原子替换 · 防并发写半截
    except Exception:
        pass


# Thai month names (full + abbreviated)
_TH_MONTHS = {
    "มกราคม": 1,
    "กุมภาพันธ์": 2,
    "มีนาคม": 3,
    "เมษายน": 4,
    "พฤษภาคม": 5,
    "มิถุนายน": 6,
    "กรกฎาคม": 7,
    "สิงหาคม": 8,
    "กันยายน": 9,
    "ตุลาคม": 10,
    "พฤศจิกายน": 11,
    "ธันวาคม": 12,
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Bank detection keywords
_BANK_SIGNATURES = {
    "kbank": ["กสิกรไทย", "kasikorn", "kbank", "k-bank"],
    "bbl": ["กรุงเทพ", "bangkok bank", "bbl"],
    "kkp": ["เกียรตินาคิน", "kiatnakin", "kkp"],
    "ktb": ["กรุงไทย", "krungthai", "ktb"],
    "scb": ["ไทยพาณิชย์", "siam commercial", "scb"],
    "bay": ["กรุงศรี", "bank of ayudhya", "bay", "krungsri"],
    "ttb": ["ทหารไทย", "ธนชาต", "tmbthanachart", "tmb", "ttb"],
}

# GL skip rows
_GL_SKIP_KW = {
    "ยอดยกมา",
    "ยอดยกไป",
    "ยอดรวม",
    "balance forward",
    "carried forward",
    "brought forward",
    "subtotal",
    "opening balance",
    "closing balance",
    "รวมประจำเดือน",
    "รวมทั้งสิ้น",
    "รวมแต่ละหน้า",
}


def _to_float(val) -> float:
    if val is None:
        return 0.0
    s = str(val).strip().replace(",", "").replace(" ", "").replace(" ", "")
    if not s or s in {"-", "–", "—"}:
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    if s.startswith("-"):
        neg = True
        s = s[1:]
    # Handle Thai dot-as-thousands-separator: "115.586.50" → "115586.50"
    dot_count = s.count(".")
    if dot_count > 1:
        last_dot = s.rfind(".")
        s = s[:last_dot].replace(".", "") + s[last_dot:]
    try:
        v = round(float(s), 2)
        return -v if neg else v
    except Exception:
        return 0.0


def _parse_date(raw) -> Optional[date]:
    """Parse Thai/English date strings into date objects.

    BUG-FIX-T1 v118.35.0.42 · 加 datetime/date 直通 + ISO 字符串 fallback
    防 openpyxl 返 datetime cell str() 化变 '2568-12-01 00:00:00' · split 出 4 parts 失败
    """
    if raw is None:
        return None
    # datetime / date 类型直接转(佛历 BE 自动转公历 CE · -543)
    if isinstance(raw, datetime):
        y = raw.year
        if y >= 2500:
            y -= 543
        try:
            return date(y, raw.month, raw.day)
        except ValueError:
            return None
    if isinstance(raw, date):
        y = raw.year
        if y >= 2500:
            y -= 543
        try:
            return date(y, raw.month, raw.day)
        except ValueError:
            return None
    raw = str(raw).strip()
    if not raw:
        return None

    # BUG-FIX-T1 v118.35.0.42 · ISO datetime 字符串去掉时分秒部分
    # 处理 'YYYY-MM-DD HH:MM:SS' / 'YYYY-MM-DDTHH:MM:SS' / 'YYYY/MM/DD HH:MM'
    # 防 split 出 4+ parts 让下面 len(parts)==3 检测失败
    if " " in raw or "T" in raw:
        raw = raw.split(" ")[0].split("T")[0]

    # Replace common separators
    clean = raw.replace("/", "-").replace(".", "-").strip()

    # Try Thai month names first
    for th_name, month_num in _TH_MONTHS.items():
        if th_name in raw:
            # e.g. "15 มกราคม 2567" or "15 ม.ค. 67"
            nums = re.findall(r"\d+", raw)
            if len(nums) >= 2:
                day = int(nums[0])
                yr_raw = int(nums[-1])
                # BE to CE conversion
                if yr_raw >= 2500:
                    yr_raw -= 543
                elif yr_raw < 100:
                    # Thai BE short year: 68 → BE 2568 → CE 2025
                    yr_raw += 1957 if yr_raw >= 43 else 2000
                try:
                    return date(yr_raw, month_num, day)
                except ValueError:
                    pass  # 该年月组合非合法日期 · 尝试下一规则

    # Numeric formats: dd-mm-yyyy, yyyy-mm-dd, dd/mm/yy
    parts = re.split(r"[-/\s]", clean)
    if len(parts) == 3:
        p0, p1, p2 = parts
        try:
            # yyyy-mm-dd
            if len(p0) == 4 and int(p0) > 1900:
                yr, mo, dy = int(p0), int(p1), int(p2)
                # BUG-FIX-T1 v118.35.0.42 · yyyy 路径也加佛历 BE → 公历 CE 转换
                # 防 openpyxl 把佛历 datetime str 化变 '2568-12-31' · 直通也要减 543
                if yr >= 2500:
                    yr -= 543
            # dd-mm-yyyy or dd-mm-yy
            elif len(p2) == 4 or len(p2) == 2:
                dy, mo = int(p0), int(p1)
                yr = int(p2)
                if yr >= 2500:
                    yr -= 543
                elif yr < 100:
                    # Thai BE short year: 68 → BE 2568 → CE 2025
                    yr += 1957 if yr >= 43 else 2000
            else:
                return None
            return date(yr, mo, dy)
        except (ValueError, TypeError):
            pass  # 日期/月/年解析失败 · 返回 None

    return None


def _amount_matches(a: float, b: float) -> bool:
    return abs(a - b) <= AMOUNT_TOL


def _day_diff(d1: Optional[date], d2: Optional[date]) -> Optional[int]:
    if d1 is None or d2 is None:
        return None
    return abs((d1 - d2).days)


def _is_gl_skip_row(cells: List) -> bool:
    joined = " ".join(str(c or "").strip().lower() for c in cells[:4])
    return any(kw in joined for kw in _GL_SKIP_KW)


def _detect_bank(text: str) -> str:
    """Detect bank from PDF text content."""
    tl = text.lower()
    for bank_code, keywords in _BANK_SIGNATURES.items():
        if any(kw.lower() in tl for kw in keywords):
            return bank_code
    return "generic"


def _bank_from_filename(filename: str) -> str:
    """Bank code from the filename, or "" if none.

    Content-based detection is unreliable for statements full of interbank QR
    transfers: a TTB statement can name "KBANK"/"SCB" hundreds of times (the
    paying counterparties) while its own brand sits in a logo image, not text.
    The user-supplied filename ("STM TTB.pdf") is the high-precision signal a
    human reads, so it wins over content when present. ASCII keywords are
    matched on word boundaries to avoid incidental substring hits.
    """
    name = (filename or "").lower()
    for bank_code, keywords in _BANK_SIGNATURES.items():
        for kw in keywords:
            kw = kw.lower()
            if not kw.isascii():
                continue  # Thai brand names don't appear in filenames
            if re.search(rf"(?<![a-z]){re.escape(kw)}(?![a-z])", name):
                return bank_code
    return ""
