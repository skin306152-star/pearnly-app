# -*- coding: utf-8 -*-
"""
Pearnly · 通用导入器 · AI 列映射建议(REFACTOR-WA-B1 · 2026-05-29 从 template_learning 抽出)

纯搬家 0 逻辑改 · ADR-006 §7:本地推断拿不准时,把『表头 + 前 20 行预览 + 本地猜测』发给
Gemini 要 col_map 建议,再用余额链(账单)/形状(GL)本地校验;校验过才用并自动存。
绝不发整份文件 / 密钥。temp=0 · 按 signature 磁盘缓存(同模板第二次不再烧钱)·
RECON_AI_MAPPING flag 可关(默认开)· 失败/超时静默返 None(退回用户确认 · 不阻断)。

叶子依赖:keys(_GL_KEYS/_STMT_KEYS/build_header_signature)· 不 import template_learning(防循环)。
template_learning 顶部 `from .ai_mapping import ai_mapping_enabled, suggest_mapping_with_ai` re-import
(推断层 bare 调 + 下游 bank_recon_v2 `_tl.suggest_mapping_with_ai` + test patch
`services.importer.template_learning.suggest_mapping_with_ai` 都靠它仍是 template_learning 模块属性)。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from services.importer.keys import _GL_KEYS, _STMT_KEYS, build_header_signature

_AI_MAPPING_MODEL = os.environ.get("RECON_AI_MAPPING_MODEL", "gemini-2.5-flash-lite")
_AI_MAPPING_PROMPT_VER = "v1"
_AI_MAPPING_CACHE_DIR = os.environ.get("RECON_AI_MAPPING_CACHE_DIR", "").strip() or os.path.join(
    os.getcwd(), ".ai_mapping_cache"
)


def ai_mapping_enabled() -> bool:
    """RECON_AI_MAPPING 默认开 · 设 0/false/no/off 关闭。"""
    return os.environ.get("RECON_AI_MAPPING", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _ai_cache_path(cache_key: str) -> str:
    safe = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    return os.path.join(_AI_MAPPING_CACHE_DIR, safe + ".json")


def _ai_cache_get(cache_key: str) -> Optional[Dict[str, int]]:
    try:
        p = _ai_cache_path(cache_key)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 缓存命中也可能是『AI 当时回了 None』· 用哨兵区分,避免反复重试烧钱
            return data if isinstance(data, dict) else None
    except Exception:
        return None
    return None


def _ai_cache_has(cache_key: str) -> bool:
    try:
        return os.path.exists(_ai_cache_path(cache_key))
    except Exception:
        return False


def _ai_cache_put(cache_key: str, value: Any) -> None:
    try:
        os.makedirs(_AI_MAPPING_CACHE_DIR, exist_ok=True)
        p = _ai_cache_path(cache_key)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False)
        os.replace(tmp, p)
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
            + f"HEADER (col:name): {json.dumps(indexed_headers, ensure_ascii=False)}\n"
            + f"PREVIEW (first rows): {json.dumps(preview, ensure_ascii=False)}\n"
            + f"LOCAL_GUESS: {json.dumps(local_guess or {}, ensure_ascii=False)}\n"
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
        result = _coerce_ai_cm(json.loads(text), document_type, n_cols)
    except Exception:
        result = None

    # 缓存结果(含 None → 存 {} 哨兵 · 同模板第二次不再调 API)
    _ai_cache_put(cache_key, result if result else {})
    return result
