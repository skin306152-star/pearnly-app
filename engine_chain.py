# -*- coding: utf-8 -*-
"""
Mr.Pilot · v103 · OCR 引擎降级链
保证 Gemini 失败 / 配额满 / 全空时 · 不再返回 503 / 全空 · 自动切到备用引擎

层级:
  Layer 1 · Gemini Flash(主 · 99% 场景走这条)
  Layer 2 · Typhoon 提文字 + NVIDIA chat 抽字段(Gemini 挂时)
  Layer 3 · EasyOCR + regex(最后兜底 · 本地不依赖网络 · 永不失败)

产物 · result 多两个字段:
  - engine_chain · 走过的所有层 · 例 ["gemini_429","typhoon_nvidia_ok"]
  - fallback_used · True 表示用了备用引擎 · 前端可显示提示
"""
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# ============================================================
# 公开入口
# ============================================================
def recognize_with_fallback(
    pdf_bytes: bytes,
    max_pages: int,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    多层引擎降级链 · 替代直接调用 gemini_engine.recognize_pdf
    与 gemini_engine.recognize_pdf 返回结构兼容 · 多 engine_chain / fallback_used 字段
    """
    chain = []
    t0 = time.time()

    # ---------- Layer 1 · Gemini ----------
    try:
        from gemini_engine import recognize_pdf as gemini_recognize, is_gemini_available
        if api_key or is_gemini_available():
            chain.append("gemini_try")
            result = gemini_recognize(pdf_bytes, max_pages=max_pages, api_key=api_key)
            if _result_is_usable(result):
                chain[-1] = "gemini_ok"
                result["engine_chain"] = chain
                result["fallback_used"] = False
                return result
            else:
                chain[-1] = "gemini_empty"
                logger.warning(f"[Chain] Gemini 返回全空 · 触发降级")
        else:
            chain.append("gemini_no_key")
            logger.info(f"[Chain] Gemini 不可用(无 key)· 直接降级")
    except Exception as e:
        err_name = type(e).__name__
        err_msg = str(e)[:200]
        is_quota = ("ResourceExhausted" in err_name
                    or "429" in err_msg
                    or "quota" in err_msg.lower()
                    or "TooManyRequests" in err_name)
        if chain and chain[-1] == "gemini_try":
            chain[-1] = "gemini_429" if is_quota else f"gemini_err"
        else:
            chain.append("gemini_429" if is_quota else "gemini_err")
        logger.warning(f"[Chain] Gemini 失败 ({err_name}) · 触发降级: {err_msg}")

    # ---------- Layer 2 · Typhoon + NVIDIA chat ----------
    try:
        import typhoon_engine
        import nvidia_engine
        if typhoon_engine.is_available() and nvidia_engine.is_available():
            chain.append("typhoon_nvidia_try")
            t2 = time.time()
            result = _typhoon_nvidia_recognize(pdf_bytes, max_pages)
            logger.info(f"[Chain] Typhoon+NVIDIA 耗时 {int((time.time()-t2)*1000)}ms")
            if _result_is_usable(result):
                chain[-1] = "typhoon_nvidia_ok"
                result["engine_chain"] = chain
                result["fallback_used"] = True
                result["elapsed_ms"] = int((time.time() - t0) * 1000)
                return result
            else:
                chain[-1] = "typhoon_nvidia_empty"
                logger.warning(f"[Chain] Typhoon+NVIDIA 也返回全空 · 继续降级到 EasyOCR")
        else:
            chain.append("typhoon_nvidia_unavailable")
            logger.info(f"[Chain] Typhoon/NVIDIA 未配置 · 跳过 Layer 2 直接到 EasyOCR")
    except Exception as e:
        chain.append(f"typhoon_nvidia_err")
        logger.warning(f"[Chain] Typhoon+NVIDIA 失败: {type(e).__name__}: {e}")

    # ---------- Layer 3 · EasyOCR(永远兜底)----------
    try:
        from ocr_engine import recognize_pdf as easy_recognize
        chain.append("easyocr_try")
        t3 = time.time()
        result = easy_recognize(pdf_bytes, max_pages=max_pages)
        logger.info(f"[Chain] EasyOCR 耗时 {int((time.time()-t3)*1000)}ms")
        # EasyOCR 总能给出文本 · 即便字段不全也算成功
        chain[-1] = "easyocr_ok"
        # EasyOCR 字段是英文 key (invoice_number/date/total_amount/tax_ids)
        # 转成与 Gemini 兼容的字段名
        for p in result.get("pages", []):
            f = p.get("fields") or {}
            p["fields"] = _easyocr_fields_to_gemini_compatible(f, p.get("text", ""))
        result["engine_chain"] = chain
        result["fallback_used"] = True
        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        return result
    except Exception as e:
        chain.append("easyocr_err")
        logger.exception(f"[Chain] EasyOCR 也失败 · 全链路失败: {type(e).__name__}: {e}")
        # 全链路失败 · 抛原始异常让 app.py 处理
        raise RuntimeError(f"all_engines_failed · chain={chain}") from e


# ============================================================
# 私有 · 质量检查 / 工具
# ============================================================
def _result_is_usable(result: Dict[str, Any]) -> bool:
    """至少一页有任一关键字段非空 · 才算可用"""
    if not result or not result.get("pages"):
        return False
    for p in result["pages"]:
        if p.get("error"):
            continue
        f = p.get("fields") or {}
        if (_nonblank(f.get("invoice_number"))
                or _nonblank(f.get("total_amount"))
                or _nonblank(f.get("seller_name"))
                or _nonblank(f.get("date"))):
            return True
    return False


def _nonblank(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s not in ("", "null", "none", "n/a", "-", "—")


# ============================================================
# Layer 2 · Typhoon + NVIDIA chat 实现
# ============================================================
def _typhoon_nvidia_recognize(pdf_bytes: bytes, max_pages: int) -> Dict[str, Any]:
    """Typhoon 提取文字 → NVIDIA Reasoning 模型抽字段"""
    import typhoon_engine
    t0 = time.time()
    typhoon_texts = typhoon_engine.extract_text_from_pdf_bytes(pdf_bytes)

    if not typhoon_texts:
        return {"pages": [], "page_count": 0, "elapsed_ms": 0, "engine": "typhoon_nvidia"}

    pages_result = []
    sorted_indices = sorted(typhoon_texts.keys())
    for idx in sorted_indices[:max_pages]:
        text = typhoon_texts[idx]
        if not text or not text.strip():
            pages_result.append(_make_empty_page(idx + 1, "typhoon_no_text"))
            continue
        t_page = time.time()
        fields = _nvidia_extract_fields(text)
        page_result = {
            "page_number": idx + 1,
            "text": text[:3000],
            "lines": [ln for ln in text.split("\n") if ln.strip()],
            "fields": fields or _empty_fields(),
            "elapsed_ms": int((time.time() - t_page) * 1000),
        }
        pages_result.append(page_result)

    return {
        "pages": pages_result,
        "page_count": len(pages_result),
        "elapsed_ms": int((time.time() - t0) * 1000),
        "engine": "typhoon_nvidia",
    }


def _nvidia_extract_fields(text: str) -> Optional[Dict[str, Any]]:
    """从 Typhoon 提取的纯文字 · 用 NVIDIA Reasoning 模型抽字段"""
    import nvidia_engine

    prompt = f"""Extract invoice fields from this Thai/English invoice text and return ONLY valid JSON (no markdown, no explanation).

Schema:
{{
  "invoice_number": "string or null",
  "date": "YYYY-MM-DD Gregorian (convert Buddhist year by -543) or null",
  "date_raw": "exact date as printed",
  "seller_name": "string or empty",
  "seller_tax": "13-digit Thai tax ID or empty",
  "seller_addr": "string or empty",
  "buyer_name": "string or empty",
  "buyer_tax": "13-digit Thai tax ID or empty",
  "buyer_addr": "string or empty",
  "subtotal": "number as string or empty",
  "vat": "number as string or empty",
  "total_amount": "number as string or empty",
  "items": [],
  "notes": "string or empty"
}}

Rules:
- Numbers only (no commas, no currency).
- Buddhist year (>=2400) MUST -543 to Gregorian.
- If field missing in text, use null/empty as specified.

Invoice text:
{text[:3000]}

Output ONLY the JSON object."""

    response = nvidia_engine.chat(
        messages=[{"role": "user", "content": prompt}],
        model=nvidia_engine.MODEL_REASONING,
        temperature=0.0,
        max_tokens=1024,
        json_mode=True,
    )
    if not response:
        return None
    parsed = nvidia_engine.parse_json_response(response)
    if not parsed:
        return None
    # 字段标准化 · 跟 Gemini 出来的格式对齐
    return _normalize_basic_fields(parsed)


def _normalize_basic_fields(d: Dict[str, Any]) -> Dict[str, Any]:
    """简单 normalize · 把 NVIDIA 返回的字段对齐 Gemini 风格"""
    if not isinstance(d, dict):
        return _empty_fields()
    out = _empty_fields()
    for k in out.keys():
        if k in d:
            out[k] = d[k]
    # total_amount 有可能是字符串 · 尝试转数字字符串(去逗号)
    for num_k in ("total_amount", "subtotal", "vat"):
        v = out.get(num_k)
        if isinstance(v, str):
            v_clean = v.replace(",", "").strip()
            try:
                float(v_clean)  # 验证能转浮点
                out[num_k] = v_clean
            except ValueError:
                pass  # 保留原字符串
    return out


# ============================================================
# Layer 3 · EasyOCR 字段格式适配
# ============================================================
def _easyocr_fields_to_gemini_compatible(easy_fields: Dict[str, Any], text: str) -> Dict[str, Any]:
    """EasyOCR 字段(invoice_number/date/total_amount/tax_ids) → Gemini 风格字段"""
    out = _empty_fields()
    if easy_fields.get("invoice_number"):
        out["invoice_number"] = easy_fields["invoice_number"]
    if easy_fields.get("date"):
        out["date_raw"] = easy_fields["date"]
        # 不强行转 Gregorian · 保留原值在 date_raw · date 留 null 让用户复核
    if easy_fields.get("total_amount") is not None:
        out["total_amount"] = str(easy_fields["total_amount"])
    # tax_ids · 取第一个作 seller_tax(粗略 · 用户可在抽屉里改)
    tax_ids = easy_fields.get("tax_ids") or []
    if tax_ids:
        out["seller_tax"] = tax_ids[0]
        if len(tax_ids) > 1:
            out["buyer_tax"] = tax_ids[1]
    out["notes"] = "EasyOCR 兜底识别 · 字段较粗 · 建议人工复核"
    return out


def _empty_fields() -> Dict[str, Any]:
    return {
        "invoice_number": None,
        "date": None,
        "date_raw": "",
        "seller_name": "",
        "seller_tax": "",
        "seller_addr": "",
        "buyer_name": "",
        "buyer_tax": "",
        "buyer_addr": "",
        "subtotal": "",
        "vat": "",
        "total_amount": None,
        "items": [],
        "notes": "",
    }


def _make_empty_page(page_number: int, reason: str) -> Dict[str, Any]:
    return {
        "page_number": page_number,
        "text": "",
        "lines": [],
        "fields": _empty_fields(),
        "error": reason,
        "elapsed_ms": 0,
    }
