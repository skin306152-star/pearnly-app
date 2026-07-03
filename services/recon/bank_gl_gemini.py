# -*- coding: utf-8 -*-
"""
services/recon/bank_gl_gemini.py · Pearnly

Gemini-vision GL fallback, used only when every local parser fails (e.g. a
scanned image-only ledger with no text layer or table geometry).

The model is asked to emit every row as JSON. A long ledger easily exceeds the
output-token ceiling, and a truncated reply is invalid JSON ("Unterminated
string …") that fails the whole job — the original single-shot implementation
hit exactly this on a few-hundred-row Thai GL. We instead split the PDF into
small page chunks and merge the per-chunk rows, so no single reply approaches
the limit and one bad chunk can't sink the rest.
"""

import logging
from typing import Any, Dict, List, Optional

from services.recon.bank_recon_types import GlRow
from services.recon.bank_recon_utils import _parse_date
from services.ocr.gemini_models import try_with_fallback

logger = logging.getLogger(__name__)

# Few pages per request keeps each JSON reply well under Gemini's output cap.
_PAGES_PER_CHUNK = 4

_PROMPT = (
    "This is a General Ledger (GL) document.{hint} "
    "Extract ALL transaction rows as JSON with keys:\n"
    '  "opening_balance": number,\n'
    '  "accounts": [list of account codes found],\n'
    '  "rows": [{{date:"YYYY-MM-DD", doc_no:string, account_code:string, '
    "description:string, debit:number, credit:number}}]\n"
    "debit = money into the account (deposits), credit = money out. "
    "Return ONLY valid JSON."
)


def _page_chunks(file_bytes: bytes, pages_per_chunk: int) -> List[bytes]:
    """Split a PDF into ≤pages_per_chunk-page PDF byte chunks (page order kept)."""
    import fitz

    chunks: List[bytes] = []
    src = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        total = src.page_count
        for start in range(0, total, pages_per_chunk):
            dst = fitz.open()
            dst.insert_pdf(src, from_page=start, to_page=min(start + pages_per_chunk, total) - 1)
            chunks.append(dst.tobytes())
            dst.close()
    finally:
        src.close()
    return chunks


def _call_json(model_name: str, pdf_bytes: bytes, prompt: str) -> dict:
    """One model call returning parsed JSON (temperature 0 for determinism)."""
    from services.ocr.model_client import json_from_pdf

    return json_from_pdf(model_name, pdf_bytes, prompt, "bank.gl")


def _row_from_dict(r: dict, account_code: str) -> Optional[GlRow]:
    d = _parse_date(str(r.get("date", "")))
    if d is None:
        return None
    acct = str(r.get("account_code", "")).strip()
    if account_code and acct and not acct.startswith(account_code):
        return None
    return GlRow(
        date=d,
        doc_no=str(r.get("doc_no", "")),
        account_code=acct,
        description=str(r.get("description", "")),
        debit=float(r.get("debit", 0) or 0),
        credit=float(r.get("credit", 0) or 0),
    )


def gemini_parse_gl(
    file_bytes: bytes, filename: str, account_code: str, api_key: str
) -> Dict[str, Any]:
    """Gemini fallback for GL PDFs. Chunked by page to survive long ledgers."""
    try:
        hint = f" Filter to account code starting with '{account_code}'." if account_code else ""
        prompt = _PROMPT.format(hint=hint)

        try:
            chunks = _page_chunks(file_bytes, _PAGES_PER_CHUNK)
        except Exception as e:  # page split failed — fall back to one whole-file call
            logger.warning(f"[gemini_gl][{filename}] page split failed: {e} · single call")
            chunks = [file_bytes]

        rows: List[GlRow] = []
        accounts_seen: set = set()
        opening = 0.0
        for idx, chunk in enumerate(chunks):
            # 主模型解析失败/截断 → 自动升级到更强兜底模型重试一次(糊图/长文档救场)。
            data = try_with_fallback(
                lambda m, c=chunk: _call_json(m, c, prompt), label=f"gemini_gl[{filename}]#{idx}"
            )
            if data is None:
                # One truncated/failed chunk must not sink the rest.
                logger.warning(f"[gemini_gl][{filename}] chunk {idx} failed (all models)")
                continue
            if idx == 0:
                opening = float(data.get("opening_balance", 0) or 0)
            for raw in data.get("rows") or []:
                row = _row_from_dict(raw, account_code)
                if row is None:
                    continue
                accounts_seen.add(row.account_code or "?")
                rows.append(row)

        if not rows:
            return {"ok": False, "rows": [], "error": "gemini returned no usable rows"}

        # debit = money in (deposits), consistent with the local parsers and the
        # reconciler (stmt.deposit ↔ gl.debit).
        closing = round(opening + sum(r.debit for r in rows) - sum(r.credit for r in rows), 2)
        return {
            "ok": True,
            "rows": rows,
            "accounts": sorted(accounts_seen - {"?"}),
            "opening": opening,
            "closing": closing,
            "row_count": len(rows),
        }
    except Exception as e:
        logger.warning(f"gemini_parse_gl failed: {e}")
        return {"ok": False, "rows": [], "error": str(e)}
