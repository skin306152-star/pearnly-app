# -*- coding: utf-8 -*-
"""bank_stmt_gemini.py · Pearnly · Gemini OCR fallback for bank statements.

Split verbatim from bank_recon_v2.py. Last-resort parser when the deterministic
extractors fail; results cached (in-memory LRU + disk) by file-bytes hash.
"""

import hashlib
import json
import logging
import re
from typing import Any, Dict

from services.ocr.gemini_models import flash_lite, try_with_fallback
from services.recon.bank_recon_types import StatementRow
from services.recon.bank_recon_utils import (
    _parse_date,
    _GEMINI_STMT_CACHE,
    _cache_get,
    _cache_put,
    _disk_cache_get,
    _disk_cache_put,
)

logger = logging.getLogger(__name__)


def _gemini_parse_statement(file_bytes: bytes, filename: str, api_key: str) -> Dict[str, Any]:
    """
    Gemini fallback: extract bank statement data from scanned PDF.
    Returns {ok, rows, opening, closing, bank_code}.

    v118.33.13.1 · Caches by SHA-256(file_bytes). Same PDF re-uploaded skips the
    API call entirely. Primary model = flash_lite (cheap); on parse failure/empty
    it escalates once to the stronger fallback model via try_with_fallback.
    """
    # Check cache first — instant return if same PDF was OCR'd before
    # v118.35.0.60 · 缓存键带提示词版本 · 改提示词后旧缓存自动失效(否则返回旧结果)
    _STMT_PROMPT_VER = "v63-totals"
    cache_key = hashlib.sha256(file_bytes).hexdigest() + ":" + _STMT_PROMPT_VER
    cached = _cache_get(_GEMINI_STMT_CACHE, cache_key)
    if cached is None:
        # v118.35.0.64 · 内存没有 → 查磁盘(跨重启/多 worker 一致)· 命中则回填内存
        cached = _disk_cache_get(cache_key)
        if cached is not None:
            _cache_put(_GEMINI_STMT_CACHE, cache_key, cached)
            logger.info(f"[stmt_parse][{filename}] gemini DISK cache HIT key={cache_key[:12]}")
    if cached is not None:
        logger.info(f"[stmt_parse][{filename}] gemini cache HIT key={cache_key[:12]}")
        # Re-materialize StatementRow objects (cache stores dicts)
        rebuilt = []
        for d in cached.get("_rows_raw", []):
            rebuilt.append(
                StatementRow(
                    date=_parse_date(d["date"]) if d.get("date") else None,
                    description=d.get("description", ""),
                    withdrawal=float(d.get("withdrawal", 0) or 0),
                    deposit=float(d.get("deposit", 0) or 0),
                    balance=float(d.get("balance", 0) or 0),
                    confidence=d.get("confidence", "high"),
                )
            )
        return {
            "ok": cached.get("ok", True),
            "rows": rebuilt,
            "opening": cached.get("opening", 0.0),
            "closing": cached.get("closing", 0.0),
            "bank_code": cached.get("bank_code", "generic"),
            "printed_totals": cached.get("printed_totals"),  # v118.35.0.63
        }
    try:
        import google.generativeai as genai
        import base64

        genai.configure(api_key=api_key)

        b64 = base64.b64encode(file_bytes).decode()
        # v118.33.13.0 · strict accounting-grade prompt — no guessing, no hallucination
        prompt = (
            "You are extracting EVERY transaction row from a bank statement (scanned PDF) for "
            "FINANCIAL RECONCILIATION. Both ACCURACY and COMPLETENESS matter: never invent "
            "digits, but also never drop a real transaction row.\n"
            "\n"
            "RULES:\n"
            "1. Extract EVERY transaction row, top to bottom, on EVERY page. Do NOT skip a row "
            "just because one field is unclear — extract the row, set only the unclear field to "
            "null, and mark confidence='low'. Missing one real transaction breaks reconciliation.\n"
            "2. NEVER guess or fabricate digits. If a number is blurry/ambiguous, return null "
            "for THAT field (not a guess) and mark confidence='low'.\n"
            "3. NEVER 'fix' the math by adjusting amounts — extract exactly what is printed, "
            "even if the running balance looks off.\n"
            "4. RUNNING-BALANCE SELF-CHECK: normally each row's balance = previous row's balance "
            "± its amount. Use this to verify you did NOT miss a row: if two consecutive balances "
            "differ by more than one transaction's amount, you missed a row in between — look again.\n"
            "5. Do NOT output summary/total rows (e.g. 'Total', 'Total Credit/Debit/Deposit', "
            "'รวมรายการ', 'ยอดรวม', 'grand total', 合计/总计) as transactions. Output ONLY individual "
            "transactions. BUT capture the statement's PRINTED footer summary numbers separately "
            "(see schema: printed_total_*/printed_*_count) — these are the bank's own totals used "
            "to verify completeness. If the footer prints 'No. of Credits 4 / Total Credit 8,000.00', "
            "set printed_credit_count=4 and printed_total_credit=8000.00. null if not printed.\n"
            "6. Thai number formats: '115.586,50' and '115,586.50' both mean 115586.50. "
            "'115.586.50' (dot thousands separator) also means 115586.50.\n"
            "7. withdrawal and deposit are MUTUALLY EXCLUSIVE — one is the amount, the other 0. "
            "Use the printed column; if direction is ambiguous, use the running balance "
            "(balance went DOWN = withdrawal; UP = deposit).\n"
            "\n"
            "Return JSON only (no markdown fences) with this exact schema:\n"
            "{\n"
            '  "bank_code": "kbank"|"bbl"|"kkp"|"ktb"|"scb"|"generic",\n'
            '  "opening_balance": number|null,\n'
            '  "closing_balance": number|null,\n'
            '  "printed_total_debit": number|null,\n'
            '  "printed_total_credit": number|null,\n'
            '  "printed_debit_count": number|null,\n'
            '  "printed_credit_count": number|null,\n'
            '  "rows": [{"date":"YYYY-MM-DD"|null, "description":"text exactly as printed",'
            '"withdrawal":number|null, "deposit":number|null, "balance":number|null,'
            '"confidence":"high"|"medium"|"low"}]\n'
            "}\n"
            "Mark confidence='low' if ANY field in the row required interpretation of "
            "unclear characters. Mark confidence='medium' if mostly clear but you had "
            "minor doubts. Mark 'high' only when every digit is unambiguous."
        )

        # v118.35.0.62 · temperature=0 · 抽取任务要确定性,不要"创造性"。
        # 默认温度~1.0 导致同一扫描件每次识别结果不同(实测 BAY 行数 212↔274 飘)·
        # 设 0 后大幅稳定且通常更准 · top_p=1 candidate_count=1。
        def _call(model_name):
            from services.ai_gateway import backends

            if not backends.is_aistudio():  # vertex / selfhost 经网关;默认 aistudio 走原 base64 路
                from services.ai_gateway import transport
                from services.ocr.gemini_models import tier_for_model

                out = transport.multimodal_to_json(
                    prompt,
                    [(file_bytes, "application/pdf")],
                    tier=tier_for_model(model_name),
                    api_key=None,
                    response_mime=False,
                    max_tokens=32768,
                    temperature=0.0,
                    max_retries=0,
                    task="bank.stmt",
                )
                if not out.ok:  # 让 try_with_fallback 升级到下一档模型
                    raise RuntimeError(f"gateway {out.error_kind}")
                return out.data

            resp = genai.GenerativeModel(model_name).generate_content(
                [{"mime_type": "application/pdf", "data": b64}, prompt],
                generation_config={
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "candidate_count": 1,
                    "max_output_tokens": 32768,
                },
            )
            text = (resp.text or "").strip()
            if text.startswith("```"):
                text = re.sub(r"^```[a-z]*\n?", "", text).rstrip("`").strip()
            return json.loads(text)

        # 主模型(flash-lite)解析失败/截断/空 → 升级到更强兜底模型重试一次(糊图扫描件救场)。
        data = try_with_fallback(_call, primary=flash_lite(), label=f"gemini_stmt[{filename}]")
        if data is None:
            return {"ok": False, "rows": [], "error": "gemini statement parse failed (all models)"}

        raw_rows = data.get("rows") or []
        rows = []
        _OPENING_KW = (
            "ยอดยกมา",
            "brought forward",
            "opening balance",
            "balance b/f",
            "期初余额",
            "上期结转",
        )
        # If Gemini missed opening_balance, try to recover from the first no-movement row
        opening_extracted = float(data.get("opening_balance", 0) or 0)
        last_date = None  # v118.35.0.49 · 同日多笔银行常省略重复日期 · 沿用上一行
        for r in raw_rows:
            d = _parse_date(str(r.get("date", "")))
            if d is not None:
                last_date = d
            else:
                d = last_date  # 缺日期 → 沿用上一行(别丢交易/断余额链)· 首行无可沿用则保持 None
            wd_raw = r.get("withdrawal")
            dep_raw = r.get("deposit")
            bal_raw = r.get("balance")
            # v118.35.0.49 · 纯噪声行(无日期可继承 + 无金额 + 无余额)才跳过 · 有金额/余额必保留
            if d is None and not wd_raw and not dep_raw and bal_raw is None:
                continue
            desc = str(r.get("description", ""))
            conf = (r.get("confidence") or "high").lower()
            if conf not in ("high", "medium", "low"):
                conf = "high"
            if wd_raw is None and dep_raw is None:
                conf = "low"
            if bal_raw is None:
                conf = "low"
            wd_v = float(wd_raw or 0)
            dep_v = float(dep_raw or 0)
            bal_v = float(bal_raw or 0)
            # v118.33.13.1 · Detect opening-balance row: no movement + keyword
            is_opening = (wd_v == 0 and dep_v == 0) and any(
                kw in desc or kw in desc.lower() for kw in _OPENING_KW
            )
            if is_opening:
                # Use as opening balance; do NOT create as transaction row
                if not opening_extracted and bal_v:
                    opening_extracted = bal_v
                continue
            rows.append(
                StatementRow(
                    date=d,
                    description=desc,
                    withdrawal=wd_v,
                    deposit=dep_v,
                    balance=bal_v,
                    confidence=conf,
                )
            )

        result_closing = float(data.get("closing_balance", 0) or 0)
        result_bank = data.get("bank_code", "generic")

        # v118.35.0.63 · 账单印刷页脚汇总(笔数/合计)· 用来交叉校验完整性(抓漏行)
        def _nz(v):
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        printed_totals = {
            "total_debit": _nz(data.get("printed_total_debit")),
            "total_credit": _nz(data.get("printed_total_credit")),
            "debit_count": _nz(data.get("printed_debit_count")),
            "credit_count": _nz(data.get("printed_credit_count")),
        }
        # v118.33.13.1 · Save raw row dicts to cache (StatementRow has datetime — store str)
        try:
            _cache_val = {
                "ok": True,
                "opening": opening_extracted,
                "closing": result_closing,
                "bank_code": result_bank,
                "printed_totals": printed_totals,
                "_rows_raw": [
                    {
                        "date": rr.date.isoformat() if rr.date else None,
                        "description": rr.description,
                        "withdrawal": rr.withdrawal,
                        "deposit": rr.deposit,
                        "balance": rr.balance,
                        "confidence": rr.confidence,
                    }
                    for rr in rows
                ],
            }
            _cache_put(_GEMINI_STMT_CACHE, cache_key, _cache_val)
            _disk_cache_put(cache_key, _cache_val)  # v118.35.0.64 · 落磁盘 · 跨重启持久
            logger.info(
                f"[stmt_parse][{filename}] gemini cache STORED key={cache_key[:12]} rows={len(rows)}"
            )
        except Exception as _e:
            logger.warning(f"[stmt_parse][{filename}] cache store failed: {_e}")

        return {
            "ok": True,
            "rows": rows,
            "opening": opening_extracted,
            "closing": result_closing,
            "bank_code": data.get("bank_code", "generic"),
            "printed_totals": printed_totals,
        }

    except Exception as e:
        logger.warning(f"_gemini_parse_statement failed: {e}")
        return {"ok": False, "rows": []}
