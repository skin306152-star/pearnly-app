# -*- coding: utf-8 -*-
"""
Mr.Pilot · Gemini Flash 引擎(v0.4.0)
- 用 Gemini 2.0 Flash Vision 识别发票
- 结构化抽取:发票号 / 日期 / 金额 / 买卖方 / 商品明细 / VAT
- 对应 Plus / Pro 套餐
- 返回格式与 ocr_engine.py 的 recognize_pdf 兼容
"""

import os
import io
import json
import time
import logging
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

_gemini_model_cache = {}
_gemini_lock = threading.Lock()

# 默认使用的模型(速度/成本最优)
# 注意:gemini-2.0-flash 已弃用(2026-06-01),且免费层配额为 0
# gemini-2.5-flash 是目前免费层可用的替代,500 RPD / 10 RPM
GEMINI_MODEL_DEFAULT = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# 识别用的 Prompt(System Instruction)
# v105.3 · 精简版 · 字符数从 ~4500 → ~2400 · 省约 40% input token
# 保留所有关键规则:Schema / 日期 / WHT / 公司名严格抄写 / 多页去重
SYSTEM_PROMPT = """Extract invoice data as JSON. Return ONE JSON object only, no markdown, no explanation.

Schema:
{
  "invoice_number": "string|null",
  "date": "YYYY-MM-DD Gregorian|null",
  "date_raw": "exact text on invoice",
  "seller_name": "string", "seller_tax": "13-digit|''",
  "seller_addr": "string",
  "buyer_name": "string", "buyer_tax": "13-digit|''",
  "buyer_addr": "string",
  "subtotal": "string", "vat": "string", "total_amount": "string",
  "wht_rate": "number-only string|''", "wht_amount": "string|''",
  "items": [{"name":"...", "qty":"...", "price":"...", "subtotal":"..."}],
  "notes": "remark text|''",
  "category": "3-5 char summary in items language (e.g. 餐饮, ค่าขนส่ง)|''",
  "is_copy_or_duplicate": "true if shows สำเนา/COPY/DUPLICATE marker"
}

CRITICAL RULES:
1. DATE: Buddhist year (>=2400) MUST convert to Gregorian by subtract 543. e.g. 2569→2026. Always fill date_raw with original text.
2. NAMES & ADDRESSES: Transcribe Thai company names and addresses EXACTLY as printed character-by-character. NEVER auto-correct to "look more standard" (e.g. keep คะแฟ as คะแฟ, do NOT change to คาเฟ่). For ambiguous chars, pick the one matching the printed glyph visually, not semantically.
3. ITEMS: Extract all unique line items. If same name+qty+price appears on multiple pages (delivery note + receipt are common in Thai invoices), keep ONE copy only.
4. NUMBERS: No currency symbols, no commas. e.g. "12450.00".
5. TAX IDs: Exactly 13 digits, no dashes/spaces.
6. WHT (หัก ณ ที่จ่าย / ภ.ง.ด.3 / ภ.ง.ด.53): Common rates 1/2/3/5%. wht_rate is number only ("3" not "3%"). Don't guess · only extract what's printed.
"""


def _get_model(api_key: Optional[str] = None):
    """按 API key 缓存 model 实例"""
    key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("gemini.no_api_key")

    with _gemini_lock:
        if key in _gemini_model_cache:
            return _gemini_model_cache[key]

        import google.generativeai as genai
        from google.api_core.client_options import ClientOptions
        genai.configure(
            api_key=key,
            client_options=ClientOptions(api_endpoint="gemini-proxy.skin306152.workers.dev"),
            transport="rest",
        )
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_DEFAULT,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
        )
        # 缓存最多 10 个(防止 Pro 用户 key 太多占内存)
        if len(_gemini_model_cache) >= 10:
            _gemini_model_cache.pop(next(iter(_gemini_model_cache)))
        _gemini_model_cache[key] = model
        logger.info(f"✅ Gemini model 初始化 (key=***{key[-4:]}, model={GEMINI_MODEL_DEFAULT})")
        return model


def is_gemini_available() -> bool:
    """检查系统默认 key 是否配置"""
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


def _pdf_to_pil_images(pdf_bytes: bytes, dpi: int = 150) -> List:
    """PDF → PIL Image 列表(Gemini 需要 PIL)
    
    v105.3 · DPI 默认从 180 → 150
    - Gemini Vision 对发票文字识别在 150 DPI 已足够清晰
    - 图像 token 数减少约 30% · 单张成本从 ~THB 0.20 降到 ~THB 0.13
    - 高复杂度发票若识别质量下降 · 调用方可显式传 dpi=180
    """
    import fitz
    from PIL import Image

    images = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            images.append(img)
    return images


def _parse_json_safely(text: str) -> Dict[str, Any]:
    """尝试从响应里解析 JSON,容忍多种异常情况:
    - ``` 代码块包裹
    - 数组形式(取第一个)
    - JSON 后有多余文字
    - JSON 截断
    """
    if not text:
        return {}
    s = text.strip()
    # 去掉 markdown 代码块
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
        if s.startswith("json"):
            s = s[4:].strip()

    # 步骤 1:尝试直接解析
    try:
        parsed = json.loads(s)
        # 数组形式 → 取第一个对象
        if isinstance(parsed, list):
            if parsed and isinstance(parsed[0], dict):
                logger.info(f"  Gemini 返回数组形式,取第一个对象({len(parsed)} 个中的 1)")
                return parsed[0]
            return {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    # 步骤 2:raw_decode 提取第一个合法 JSON 对象/数组(丢弃后面的垃圾)
    #   这能处理「对象 + 末尾说明文字」和「数组的第一个元素完整但后面被截」两种情况
    try:
        decoder = json.JSONDecoder()
        # 先找第一个 { 或 [
        for i, ch in enumerate(s):
            if ch in "{[":
                obj, _ = decoder.raw_decode(s[i:])
                if isinstance(obj, list):
                    if obj and isinstance(obj[0], dict):
                        logger.info(f"  raw_decode 从数组首元素取 1 条")
                        return obj[0]
                    return {}
                if isinstance(obj, dict):
                    logger.info(f"  raw_decode 成功(跳过 {i} 字节前缀 + {len(s) - i - decoder.raw_decode(s[i:])[1]} 字节后缀)")
                    return obj
                break
    except Exception:
        pass

    # 步骤 3:走正则兜底
    logger.warning(f"Gemini JSON 全部解析方案失败,启用正则兜底")
    return _fallback_regex_extract(s)


def _fallback_regex_extract(text: str) -> Dict[str, Any]:
    """JSON 截断/损坏时用正则抠出顶层标量字段(不包括 items 数组)"""
    import re
    result = {}
    # 匹配 "key": "value" 或 "key": null/number
    patterns = [
        ("invoice_number", r'"invoice_number"\s*:\s*"([^"]*)"'),
        ("date",           r'"date"\s*:\s*"([^"]*)"'),
        ("seller_name",    r'"seller_name"\s*:\s*"([^"]*)"'),
        ("seller_tax",     r'"seller_tax"\s*:\s*"([^"]*)"'),
        ("seller_addr",    r'"seller_addr"\s*:\s*"([^"]*)"'),
        ("buyer_name",     r'"buyer_name"\s*:\s*"([^"]*)"'),
        ("buyer_tax",      r'"buyer_tax"\s*:\s*"([^"]*)"'),
        ("buyer_addr",     r'"buyer_addr"\s*:\s*"([^"]*)"'),
        ("subtotal",       r'"subtotal"\s*:\s*"([^"]*)"'),
        ("vat",            r'"vat"\s*:\s*"([^"]*)"'),
        ("total_amount",   r'"total_amount"\s*:\s*"([^"]*)"'),
        ("notes",          r'"notes"\s*:\s*"([^"]*)"'),
    ]
    for key, pat in patterns:
        m = re.search(pat, text)
        if m:
            result[key] = m.group(1)
    # is_copy 标记
    m_copy = re.search(r'"is_copy_or_duplicate"\s*:\s*(true|false)', text)
    if m_copy:
        result["is_copy_or_duplicate"] = (m_copy.group(1) == "true")

    # items:只要能解析多少就要多少,逐个找 {"name": "...", "qty": "...", ...}
    items = []
    item_pattern = re.compile(
        r'\{\s*"name"\s*:\s*"([^"]*)"\s*,\s*'
        r'"qty"\s*:\s*"([^"]*)"\s*,\s*'
        r'"price"\s*:\s*"([^"]*)"\s*,\s*'
        r'"subtotal"\s*:\s*"([^"]*)"\s*\}',
        re.DOTALL,
    )
    for m in item_pattern.finditer(text):
        items.append({
            "name": m.group(1),
            "qty": m.group(2),
            "price": m.group(3),
            "subtotal": m.group(4),
        })
    if items:
        result["items"] = items

    if result:
        logger.info(f"  正则兜底成功抠出 {len(result)} 个字段 + {len(items)} 个明细")
    return result


def _normalize_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """把 Gemini 返回的数据标准化成 Mr.Pilot 前端期望的 fields 结构"""
    # v0.17 · M7 · 佛历兜底转公历(Gemini 偶尔会漏 · 后端再保一道)
    raw_date = data.get("date_raw") or ""
    norm_date = _normalize_thai_date(data.get("date"), raw_date)

    result = {
        "invoice_number": data.get("invoice_number") or None,
        "date": norm_date,
        "date_raw": raw_date,              # v0.17 · 保留原始字符串供审计
        "total_amount": None,
        "subtotal": data.get("subtotal") or "",
        "vat": data.get("vat") or "",
        # v0.17 · M8 · 泰国预扣税(หัก ณ ที่จ่าย)
        "wht_rate": str(data.get("wht_rate") or "").strip(),
        "wht_amount": str(data.get("wht_amount") or "").strip().replace(",", ""),
        "seller_name": data.get("seller_name") or "",
        "seller_tax": data.get("seller_tax") or "",
        "seller_addr": data.get("seller_addr") or "",
        "buyer_name": data.get("buyer_name") or "",
        "buyer_tax": data.get("buyer_tax") or "",
        "buyer_addr": data.get("buyer_addr") or "",
        "notes": data.get("notes") or "",
        "items": data.get("items") or [],
        "tax_ids": [],
    }
    # total_amount 转数字(前端期望数字或字符串数字)
    total = data.get("total_amount")
    if total:
        try:
            result["total_amount"] = str(total).replace(",", "").strip()
        except Exception:
            result["total_amount"] = None
    # tax_ids 兼容老前端
    if result["seller_tax"]:
        result["tax_ids"].append(result["seller_tax"])
    if result["buyer_tax"] and result["buyer_tax"] not in result["tax_ids"]:
        result["tax_ids"].append(result["buyer_tax"])
    # items 字段统一格式
    normalized_items = []
    for it in result["items"]:
        if not isinstance(it, dict):
            continue
        normalized_items.append({
            "name": str(it.get("name", "")),
            "qty": str(it.get("qty", it.get("quantity", ""))),
            "price": str(it.get("price", it.get("unit_price", ""))),
            "subtotal": str(it.get("subtotal", it.get("total", ""))),
        })
    # v87 · 兜底去重:多页发票可能重复打印同样明细(ใบส่งสินค้า + ใบเสร็จรับเงิน)
    # 用 (name, qty, price) 元组做 key · 保留首次出现 · Gemini prompt 有时会漏删
    seen = set()
    deduped_items = []
    dup_count = 0
    for it in normalized_items:
        key = (it["name"].strip(), it["qty"].strip(), it["price"].strip())
        # 空行(纯 '' tuple)不算重复 · 保留
        if key == ("", "", "") or key not in seen:
            seen.add(key)
            deduped_items.append(it)
        else:
            dup_count += 1
    if dup_count > 0:
        logger.info(f"  🔁 items 去重:删掉 {dup_count} 行重复明细")
    result["items"] = deduped_items
    return result


# v0.17 · M7 · 佛历→公历转换兜底
# Gemini 已在 prompt 里被要求转换 · 这里再过一遍防漏
import re as _re_date
_DATE_YMD_RE = _re_date.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_DATE_DMY_RE = _re_date.compile(r"^(\d{1,2})[/\-.\s]+(\d{1,2})[/\-.\s]+(\d{4})$")

def _normalize_thai_date(gemini_date, raw_date):
    """
    输入:Gemini 返回的 date(可能已转也可能没转) + date_raw(原始字符串)
    输出:YYYY-MM-DD(公历)或 None

    规则:
    - 年份 >= 2400 视为佛历,减 543 得到公历
    - 年份 < 2400 视为公历,不修改
    - 支持 YYYY-MM-DD / YYYY/MM/DD / DD/MM/YYYY / DD-MM-YYYY 等常见格式
    """
    # 优先处理 gemini_date · 没有再尝试 raw_date
    for src in (gemini_date, raw_date):
        if not src:
            continue
        s = str(src).strip()
        if not s:
            continue

        # 先把 / . 空格统一成 -
        s_norm = _re_date.sub(r"[/\.\s]+", "-", s)

        # YYYY-MM-DD
        m = _DATE_YMD_RE.match(s_norm)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y >= 2400:
                y -= 543
            if 1 <= mo <= 12 and 1 <= d <= 31 and 1900 <= y <= 2100:
                return f"{y:04d}-{mo:02d}-{d:02d}"
            continue

        # DD-MM-YYYY(泰国常见写法)
        m = _DATE_DMY_RE.match(s_norm)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y >= 2400:
                y -= 543
            if 1 <= mo <= 12 and 1 <= d <= 31 and 1900 <= y <= 2100:
                return f"{y:04d}-{mo:02d}-{d:02d}"
            continue

    # 都解析不出 · 尝试直接返回 gemini_date(如果看起来已经是 ISO)
    if gemini_date and _re_date.match(r"^\d{4}-\d{2}-\d{2}$", str(gemini_date).strip()):
        return str(gemini_date).strip()
    return None


def recognize_pdf(
    pdf_bytes: bytes,
    max_pages: int = 20,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    用 Gemini Flash 识别 PDF,返回与 ocr_engine.recognize_pdf 兼容的结构
    api_key=None 时使用环境变量 GEMINI_API_KEY(Plus 模式)
    api_key=xxx 时使用传入的 key(Pro 模式,用户自带)
    """
    t0 = time.time()

    try:
        images = _pdf_to_pil_images(pdf_bytes)  # v105.3 · 走默认 dpi=150
    except Exception as e:
        logger.error(f"PDF 转图片失败: {e}")
        raise ValueError("ocr.invalid_pdf")

    if not images:
        raise ValueError("ocr.empty_pdf")
    if len(images) > max_pages:
        raise ValueError("ocr.too_many_pages")

    model = _get_model(api_key)

    def _recognize_one_page(idx_img):
        idx, img = idx_img
        t_page = time.time()
        raw_response = ""
        try:
            resp = model.generate_content(
                [SYSTEM_PROMPT, img, "Now extract the invoice data from this image and return ONLY the JSON object."],
                request_options={"timeout": 60},
            )
            raw_response = resp.text if hasattr(resp, "text") else ""
            
            # v106 · 提取 token 使用量(用于成本追踪)
            input_tokens = 0
            output_tokens = 0
            try:
                if hasattr(resp, "usage_metadata") and resp.usage_metadata:
                    input_tokens = int(getattr(resp.usage_metadata, "prompt_token_count", 0) or 0)
                    output_tokens = int(getattr(resp.usage_metadata, "candidates_token_count", 0) or 0)
            except Exception:
                pass
            
            logger.info(
                f"  [Gemini] 第 {idx} 页原始响应前 500 字符: "
                f"{raw_response[:500]}"
            )
            data = _parse_json_safely(raw_response)
            if not data:
                logger.warning(
                    f"  [Gemini] 第 {idx} 页 JSON 解析为空;"
                    f"完整响应: {raw_response[:2000]}"
                )
            fields = _normalize_fields(data)

            summary_lines = []
            if fields.get("invoice_number"): summary_lines.append(f"Invoice: {fields['invoice_number']}")
            if fields.get("date"): summary_lines.append(f"Date: {fields['date']}")
            if fields.get("seller_name"): summary_lines.append(f"Seller: {fields['seller_name']}")
            if fields.get("buyer_name"): summary_lines.append(f"Buyer: {fields['buyer_name']}")
            if fields.get("total_amount"): summary_lines.append(f"Total: {fields['total_amount']}")
            for it in (fields.get("items") or []):
                nm = it.get("name", "")
                qty = it.get("qty", "")
                sub = it.get("subtotal", "")
                summary_lines.append(f"  - {nm} × {qty} = {sub}")
            if fields.get("notes"): summary_lines.append(f"Notes: {fields['notes']}")
            summary_text = "\n".join(summary_lines)

            page_result = {
                "page_number": idx,
                "text": summary_text,
                "lines": summary_lines,
                "fields": fields,
                "is_copy": bool(data.get("is_copy_or_duplicate")),
                "elapsed_ms": int((time.time() - t_page) * 1000),
                # v106 · token 计费信息
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
            logger.info(
                f"  [Gemini] 第 {idx}/{len(images)} 页完成 "
                f"(发票号={fields.get('invoice_number')}, "
                f"总额={fields.get('total_amount')}, "
                f"明细={len(fields.get('items', []))} 项, "
                f"{int((time.time()-t_page)*1000)}ms)"
            )
            return page_result
        except Exception as e:
            logger.exception(
                f"[Gemini] 第 {idx} 页识别失败: {type(e).__name__}: {e}"
            )
            if raw_response:
                logger.error(f"  响应截断: {raw_response[:500]}")
            return {
                "page_number": idx,
                "text": "",
                "lines": [],
                "fields": _normalize_fields({}),
                "error": f"{type(e).__name__}: {str(e)[:200]}",
                "elapsed_ms": int((time.time() - t_page) * 1000),
            }

    # 并行识别页(单 PDF 内 3 并发,Gemini Flash 10 RPM 安全裕度)
    from concurrent.futures import ThreadPoolExecutor
    page_concurrency = min(3, len(images))
    if page_concurrency <= 1:
        pages_result = [_recognize_one_page((1, images[0]))] if images else []
    else:
        with ThreadPoolExecutor(max_workers=page_concurrency) as executor:
            pages_result = list(executor.map(_recognize_one_page, [(i + 1, img) for i, img in enumerate(images)]))
        # 按 page_number 排序(executor.map 已保序,但保险起见)
        pages_result.sort(key=lambda p: p["page_number"])

    return {
        "pages": pages_result,
        "page_count": len(pages_result),
        "elapsed_ms": int((time.time() - t0) * 1000),
        "engine": "gemini",
    }


# ============================================================
# v0.12 · Gemini 二次结构化(配合 Typhoon 文字 hint)
# ============================================================
def restructure_with_text_hint(
    pil_image,
    typhoon_text: str,
    previous_fields: Dict[str, Any],
    missing_fields: List[str],
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    第一次 Gemini 识别质量不够时 · 调用此函数:
      - 把 Typhoon 提取的原始文字 + 原图 + 缺失字段 提示 一起送 Gemini
      - 让 Gemini 重点关注缺失的字段
      - 返回更新后的 fields(失败返回 None)
    """
    try:
        model = _get_model(api_key)
    except Exception as e:
        logger.warning(f"[Gemini二次] 模型加载失败: {e}")
        return None

    missing_hint = ", ".join(missing_fields) if missing_fields else "(none)"
    prev_json = json.dumps(previous_fields, ensure_ascii=False)
    typhoon_excerpt = (typhoon_text or "")[:3000]  # 防止 prompt 过长

    enhanced_prompt = f"""You previously extracted invoice data, but some critical fields were missing or incorrect.

Previous extraction:
{prev_json}

Missing/uncertain fields: {missing_hint}

Below is the same image processed by a Thai-specialized OCR engine. Use this auxiliary text together with the image to re-extract a complete and accurate JSON.

=== Auxiliary OCR text ===
{typhoon_excerpt}
=== end of OCR text ===

Pay special attention to the missing fields. Re-output the COMPLETE JSON in the same schema as before. Output ONLY valid JSON, no markdown."""

    try:
        t0 = time.time()
        resp = model.generate_content(
            [SYSTEM_PROMPT, pil_image, enhanced_prompt],
            request_options={"timeout": 60},
        )
        raw = resp.text if hasattr(resp, "text") else ""
        elapsed = int((time.time() - t0) * 1000)
        data = _parse_json_safely(raw)
        if not data:
            logger.warning(f"[Gemini二次] 解析为空 · {elapsed}ms")
            return None
        fields = _normalize_fields(data)
        logger.info(f"[Gemini二次] 完成 · {elapsed}ms · 原缺失={missing_hint}")
        return fields
    except Exception as e:
        logger.warning(f"[Gemini二次] 失败: {type(e).__name__}: {str(e)[:200]}")
        return None
