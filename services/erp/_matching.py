# -*- coding: utf-8 -*-
"""
services/erp/_matching.py

String matching helpers for master-data sync (P1-B Phase 1).

What's here:
- `normalize_company_name(s)`  — strip legal suffixes (Thai / English /
  Chinese), drop punctuation + extra whitespace, casefold
- `normalize_item_name(s)`     — looser normalization for products
- `levenshtein(a, b)`          — classical DP edit distance
- `levenshtein_ratio(a, b)`    — 1 - distance / max(len_a, len_b)
- `fuzzy_match(query, candidates, threshold)` — returns the best
  candidate above the threshold or None

Levenshtein thresholds (Zihao 2026-05-18 拍板):
- customer name : 0.82  (relaxed from 0.88 to catch more typos)
- product name  : 0.90  (tightened from 0.92 wait no, relaxed to catch typos)

These thresholds live in `mrerp_customer_sync` / `mrerp_product_sync`,
not here, so this module stays generic.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Tuple


# ============================================================
# Legal suffix patterns (case-insensitive)
# ============================================================

_THAI_LEGAL_SUFFIXES = (
    "บริษัทมหาชนจำกัด",
    "บริษัทมหาชน",
    "บริษัทจำกัด(มหาชน)",
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญ",
    "ห้างหุ้นส่วน",
    "ห.จ.ก.",
    "หจก.",
    "บริษัท",
    "จำกัด",
    "(จำกัด)",
    "(มหาชน)",
    "มหาชน",
)

# English legal suffixes — ordered longest-first so 'co.,ltd' is stripped
# before 'co.' would partially match.
_ENGLISH_LEGAL_SUFFIXES = (
    "private limited company",
    "limited liability company",
    "limited partnership",
    "public limited company",
    "incorporated",
    "corporation",
    "company limited",
    "co.,ltd.,part",
    "co.,ltd.",
    "co., ltd.",
    "co.,ltd",
    "co., ltd",
    "co ltd",
    "co.ltd",
    "co.",
    "company",
    "limited",
    "ltd.",
    "ltd",
    "corp.",
    "corp",
    "inc.",
    "inc",
    "llc",
    "llp",
    "lp",
    "plc",
)

_CHINESE_LEGAL_SUFFIXES = (
    "股份有限公司",
    "有限责任公司",
    "有限公司",
    "集团有限公司",
    "集团",
    "公司",
    "(集团)",
)

# Punctuation we always strip from normalized names.
_PUNCT_RE = re.compile(
    r"[\s\.,\-_/\\()&\"'`*\[\]{}!?:;@#$%\^+=<>|~・·、。]+"
)


def _strip_suffix_set(s: str, suffixes: Tuple[str, ...]) -> str:
    """Strip any matching suffix (case-insensitive) from end; repeat
    until no more match (catches double-suffix like
    'XYZ Co., Ltd. Company')."""
    low = s.lower()
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            sfx = suffix.lower()
            if low.endswith(sfx):
                s = s[: len(s) - len(suffix)].rstrip(" .,")
                low = s.lower()
                changed = True
                break
    return s


def normalize_company_name(s: Optional[str]) -> str:
    """Return a canonical form suitable for both exact and fuzzy matching.

    Steps:
      1. trim, casefold (Unicode-aware)
      2. NFKC unicode normalize (so half-width / full-width digits unify)
      3. strip Thai legal suffixes
      4. strip English legal suffixes
      5. strip Chinese legal suffixes
      6. collapse punctuation/whitespace runs into a single space
      7. strip leading/trailing whitespace
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).strip()
    if not s:
        return ""

    # Suffix stripping is case-insensitive but we keep the original
    # casing for the rest until the final casefold step.
    s = _strip_suffix_set(s, _THAI_LEGAL_SUFFIXES)
    s = _strip_suffix_set(s, _ENGLISH_LEGAL_SUFFIXES)
    s = _strip_suffix_set(s, _CHINESE_LEGAL_SUFFIXES)

    # Collapse punctuation to single space (don't drop entirely — names
    # with embedded punctuation like "T-Net" should still differ from
    # "TNet" but match each other after this step).
    s = _PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()


def normalize_item_name(s: Optional[str]) -> str:
    """Looser normalization for product names — no legal-suffix stripping
    (which is meaningless for products), just punctuation + casefold."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).strip()
    if not s:
        return ""
    s = _PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()


# ============================================================
# Levenshtein
# ============================================================

def levenshtein(a: str, b: str) -> int:
    """Edit distance between two strings (substitution / insertion /
    deletion all cost 1). O(len(a) * len(b)) time, O(min(len(a), len(b)))
    space."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # Make `a` the shorter string so we use less memory.
    if len(a) > len(b):
        a, b = b, a
    prev = list(range(len(a) + 1))
    cur = [0] * (len(a) + 1)
    for j, cb in enumerate(b, start=1):
        cur[0] = j
        for i, ca in enumerate(a, start=1):
            if ca == cb:
                cur[i] = prev[i - 1]
            else:
                cur[i] = 1 + min(prev[i], prev[i - 1], cur[i - 1])
        prev, cur = cur, prev
    return prev[-1]


def levenshtein_ratio(a: str, b: str) -> float:
    """Similarity ratio in [0.0, 1.0]; 1.0 = identical. Returns 1.0 when
    BOTH strings are empty; 0.0 when one is empty and the other isn't."""
    if not a and not b:
        return 1.0
    longest = max(len(a), len(b))
    if longest == 0:
        return 1.0
    return 1.0 - (levenshtein(a, b) / longest)


# ============================================================
# Convenience: best fuzzy match in a list
# ============================================================

def fuzzy_match(
    query: str,
    candidates: List[str],
    threshold: float,
) -> Optional[Tuple[str, float]]:
    """Return (best_candidate, ratio) where ratio >= threshold, or None.

    Ties on ratio go to the FIRST candidate in `candidates` order. The
    caller should sort candidates by some sensible priority (e.g. most
    recently used) before invoking.
    """
    if not query or not candidates:
        return None
    best: Optional[Tuple[str, float]] = None
    for c in candidates:
        if c is None:
            continue
        r = levenshtein_ratio(query, c)
        if r >= threshold and (best is None or r > best[1]):
            best = (c, r)
    return best
