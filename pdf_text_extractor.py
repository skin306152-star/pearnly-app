# -*- coding: utf-8 -*-
"""
Pearnly · v118.20.4.3 · PDF 文本预筛(完整字段抽取版)
==========================================
对电子发票(SAP / 飞书 / 印发票宝 / 国税局电子票务等)用 pypdf 抽 text → 结构化抽字段。
速度 0.3 秒一张 · 跳过 Gemini · 节省 API 配额 5-10 倍。

抽取的字段(与 Gemini 输出 schema 一致):
  · invoice_number / date / total_amount / subtotal / vat
  · seller_name / seller_addr / seller_tax
  · buyer_name / buyer_addr / buyer_tax
  · items[] · name / qty / unit / unit_price / subtotal

判定原则:
  1. 平均每页 text > 200 字符 · 否则视为扫描件 fallback Gemini
  2. 必须抽到 invoice_no + total_amount + seller_tax 三字段才算成功
  3. 任何异常都静默 fallback Gemini · 零回退副作用
  4. 多发票拼一起(多个不同 invoice_no)→ fallback Gemini · 由 invoice_grouper 处理

抽取算法:
  · 13 位泰国 RD 税号作为切块锚点(seller / buyer 各一个)
  · 行级匹配公司名(`บริษัท ...` 开头 · 排除「ในนาม」签名段)
  · items 用「数量 单位 单价 总价」格式抓 · 描述从前行回看
"""
import io
import re
import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ============================================================
# 阈值
# ============================================================
MIN_TEXT_PER_PAGE = 200
MAX_NAME_LEN = 120
MAX_ADDR_LEN = 200
MAX_ITEMS = 50

# ============================================================
# 正则集合
# ============================================================
RE_INVOICE_NO = re.compile(
    r'(?:Invoice\s*(?:No\.?|Number|#)|Tax\s*Invoice\s*No\.?|Inv\.?\s*No\.?|'
    r'เลขที่(?:ใบกำกับ)?|เลขที่|发票号码?|発票号码|請求書番号)'
    r'\s*[:.：]?\s*([A-Z0-9][A-Z0-9\-/]{2,})',
    re.IGNORECASE
)
RE_DATE_ISO = re.compile(r'\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b')
RE_DATE_DMY = re.compile(r'\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b')
RE_TAX_ID_TH = re.compile(r'\b(\d{13})\b')
RE_TAX_ID_LABELED = re.compile(
    r'เลข(?:ประจำำ?าตัว|ประจำตัว|)?ผู้เสียภาษี[\s:]*(\d{13})'
)

RE_TOTAL = re.compile(
    r'(?:\bGrand\s*Total|\bTotal\s*Amount|\bTotal(?!\s*VAT)|'
    r'จำ?านวนเงินรวม(?:ทั้งสิ้น|ทัง้สิน้)?|รวมทั้งสิ้น|รวมทัง้สิน้|'
    r'总金额|合计金额|合計金額|総額)'
    r'\s*[:.：฿$¥]?\s*([\d,]+\.\d{2})',
    re.IGNORECASE
)
RE_SUBTOTAL = re.compile(
    r'(?:Sub\s*[-]?\s*Total|Subtotal|Net\s*(?:Amount|Total)|Amount\s*before\s*VAT|'
    r'รวมเป็นเงิน|ยอดก่อน(?:\s*VAT)?|มูลค่าก่อนภาษี|未税(?:金额)?|税抜)'
    r'\s*[:.：฿$¥]?\s*([\d,]+\.\d{2})',
    re.IGNORECASE
)
RE_VAT = re.compile(
    r'(?:VAT|Tax\s*Amount|ภาษีมูลค่าเพิ่ม|ภาษีมูลค่า|税额|消費税(?:額)?)'
    r'(?:\s+\d+\s*%?)?'
    r'\s*[:.：฿$¥]?\s*([\d,]+\.\d{2})',
    re.IGNORECASE
)

RE_ITEM_PRICE_LINE = re.compile(
    r'^\s*(\d+)\s+(\S{1,12})\s+([\d,]+\.\d{2,3})\s+([\d,]+\.\d{2,3})\s*$'
)
# 单行完整 items:行号 描述 数量 单位 单价 总价(常见于服务类发票 1-2 行 items)
RE_ITEM_INLINE = re.compile(
    r'^\s*\d+\s+(.{2,80}?)\s+(\d+)\s+(\S{1,12})\s+([\d,]+\.\d{2,3})\s+([\d,]+\.\d{2,3})\s*$'
)
RE_ITEM_DESC_LINE = re.compile(
    r'^\s*(\d+)\s+([A-Za-zก-๙][^\n]{2,200})$'
)


def _parse_money(s: Optional[str]) -> Optional[float]:
    if not s: return None
    try:
        v = float(str(s).replace(",", "").strip())
        # pypdf 字符顺序 bug 可能让 .80 变成 .803 · 强制 round 到 2 位
        return round(v, 2)
    except Exception:
        return None


def _extract_basic_fields(text: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}

    # invoice_no(过滤地址 / 短账号)
    candidates = []
    for m in RE_INVOICE_NO.finditer(text):
        v = m.group(1).strip()
        if re.match(r'^\d+/\d{1,3}$', v): continue
        if v.isdigit() and len(v) < 6: continue
        candidates.append(v)
    if candidates:
        with_alpha = [v for v in candidates if any(c.isalpha() for c in v)]
        fields["invoice_number"] = (with_alpha or candidates)[0]

    m = RE_DATE_ISO.search(text) or RE_DATE_DMY.search(text)
    if m:
        fields["date"] = m.group(1).strip()

    m = RE_TOTAL.search(text)
    if m: fields["total_amount"] = m.group(1).replace(",", "")
    m = RE_SUBTOTAL.search(text)
    if m: fields["subtotal"] = m.group(1).replace(",", "")
    m = RE_VAT.search(text)
    if m: fields["vat"] = m.group(1).replace(",", "")

    return fields


def _extract_seller(text: str):
    """从第 1 个 13 位税号之前反向找 บริษัท ... 行(seller 几乎都是公司)
    v118.32.5.5.8 · BAKELAB 兼容:pypdf 抽泰文字符顺序乱时 · RE_TAX_ID_LABELED 关键词匹配失败 ·
    fallback 找文本里第 1 个 13 位数字作锚点(税号 / 个人 13 位身份证都行)"""
    tm = RE_TAX_ID_LABELED.search(text)
    if tm:
        tax_pos = tm.start()
        tax_id = tm.group(1)
    else:
        m = re.search(r'\b(\d{13})\b', text)
        if not m:
            return None
        tax_pos = m.start()
        tax_id = m.group(1)
    block = text[:tax_pos]
    lines = block.split("\n")
    company_name = None
    company_idx = -1
    for li, line in enumerate(lines):
        stripped = line.strip()
        if not stripped: continue
        if not stripped.startswith("บริษัท"): continue
        if "ในนาม" in stripped: continue
        if stripped.count("บริษัท") > 1: continue
        company_name = stripped[:MAX_NAME_LEN]
        company_idx = li
        # 不 break · 取最后一个匹配(最靠近 tax_id · 最准确)
    if company_name is None:
        # 没找到 บริษัท · 用 ลูกค้า 标记前的最后一行作 name(店家发票场景)
        return {"name": None, "address": None, "tax_id": tax_id}

    addr_lines = []
    for line in lines[company_idx + 1:]:
        stripped = line.strip()
        if not stripped: continue
        if re.match(r'^(โทร|Tel|Fax|www\.|http|email|@)', stripped, re.I): continue
        # 遇到「ลูกค้า」标志 · seller 块到此结束
        if stripped == "ลูกค้า" or stripped.startswith("ลูกค้า"):
            break
        addr_lines.append(stripped)
        if len(addr_lines) >= 5: break

    return {
        "name": company_name,
        "address": (" ".join(addr_lines).strip()[:MAX_ADDR_LEN]) or None,
        "tax_id": tax_id,
    }


def _extract_buyer(text: str):
    """
    用 'ลูกค้า\\n' 标记定位 buyer 块 · 第 1 行 = name(任意格式:公司/店家/个人/姓名)
    后续行 = address · 直到 เลขประจำตัว <13位> 收尾
    """
    bm = re.search(r'\bลูกค้า\s*\n', text)
    if not bm:
        return None
    after = text[bm.end():bm.end() + 800]
    lines = after.split("\n")
    name = None
    addr_lines = []
    tax_id = None
    for line in lines:
        line = line.strip()
        if not line: continue
        # 遇到税号行 → buyer 块结束
        # v118.32.5.5.8 · BAKELAB 兼容:pypdf 抽泰文字符顺序乱 · 关键词匹配易失败 ·
        # 改成简单 13 位匹配(buyer 块内只有税号是 13 位 · 邮编 5 位 / 电话 10 位 不冲突)
        tm = re.search(r'\b(\d{13})\b', line)
        if tm:
            tax_id = tm.group(1)
            break
        # 第 1 个非空行 = name(无格式限制)
        if name is None:
            name = line[:MAX_NAME_LEN]
        else:
            addr_lines.append(line)
        if len(addr_lines) >= 6: break

    if not name:
        return None
    return {
        "name": name,
        "address": (" ".join(addr_lines).strip()[:MAX_ADDR_LEN]) or None,
        "tax_id": tax_id,
    }


def _extract_parties(text: str):
    """
    抽 seller / buyer 块。
      seller:第 1 个 13 位税号前找 บริษัท + 地址
      buyer:'ลูกค้า\\n' 标记后第 1 行 = name(任意格式)+ 后续 = address
    返回 (seller_dict, buyer_dict) · 任一可为 None
    """
    seller = _extract_seller(text)
    buyer = _extract_buyer(text)
    return seller, buyer


def _extract_items(text: str) -> List[Dict[str, Any]]:
    items = []
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        # 模式 B:单行完整(行号 描述 数量 单位 单价 总价)· 优先匹配
        mb = RE_ITEM_INLINE.match(ln)
        if mb:
            unit_price = _parse_money(mb.group(4))
            subtotal = _parse_money(mb.group(5))
            if unit_price is None or subtotal is None: continue
            items.append({
                "name": re.sub(r'\s{2,}', ' ', mb.group(1).strip())[:80] or "(明细)",
                "qty": int(mb.group(2)),
                "unit": mb.group(3),
                "unit_price": unit_price,
                "subtotal": subtotal,
            })
            if len(items) >= MAX_ITEMS: break
            continue

        # 模式 A:数量 单位 单价 总价(描述从前行回看)
        m = RE_ITEM_PRICE_LINE.match(ln)
        if not m: continue
        qty = int(m.group(1))
        unit = m.group(2)
        unit_price = _parse_money(m.group(3))
        subtotal = _parse_money(m.group(4))
        if unit_price is None or subtotal is None: continue

        desc = ""
        for back in range(1, 5):
            if i - back < 0: break
            prev = lines[i - back].strip()
            if not prev: continue
            if RE_ITEM_PRICE_LINE.match(prev): break
            md = RE_ITEM_DESC_LINE.match(prev)
            if md:
                desc = re.sub(r'\s{2,}', ' ', md.group(2).strip())
                break
            if not desc and len(prev) > 3:
                desc = re.sub(r'\s{2,}', ' ', prev[:80])

        items.append({
            "name": (desc or "(明细)")[:80],
            "qty": qty,
            "unit": unit,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })
        if len(items) >= MAX_ITEMS:
            break

    # 同发票多页 · 去重(qty + unit_price + subtotal + name 完全相同 = 重复)
    seen = set()
    unique = []
    for it in items:
        key = (it["qty"], it["unit_price"], it["subtotal"], it["name"][:30])
        if key in seen: continue
        seen.add(key)
        unique.append(it)
    return unique


def _extract_notes(text: str) -> Optional[str]:
    """抽 หมายเหตุ(备注)段:标记后到下一个空行/关键词为止
    过滤:过敏原标注 / 联系电话 / 引号包围段(BAKELAB 模板自带噪音)"""
    m = re.search(r'หมายเหตุ\s*\n', text)
    if not m:
        return None
    after = text[m.end():m.end() + 400]
    lines = []
    saw_content = False
    for ln in after.split("\n"):
        s = ln.strip()
        if not s:
            if saw_content: break
            continue
        # 撞到下一段关键词 = 备注结束
        if any(kw in s for kw in ["บริษัท", "ในนาม", "ลูกค้า", "เลขประจำ", "ธนาคาร"]):
            break
        # 过滤模板噪音(过敏原 / 联系信息)
        if any(kw in s for kw in ["แพ้", "อาจมี", "ข้อมูลเพิ่มเติม", "ข้อมูลเพิม่เติม", "ข้อมูลสำำ?าหรับ"]):
            continue
        # 跳过纯引号 / 短噪音
        if s in ('"', "'") or len(s) < 3:
            continue
        lines.append(s)
        saw_content = True
        if len(lines) >= 3: break
    out = " ".join(lines).strip()[:200]
    return out or None


def _extract_fields_from_text(text: str) -> Dict[str, Any]:
    fields = _extract_basic_fields(text)
    seller, buyer = _extract_parties(text)
    if seller:
        if seller.get("name"):    fields["seller_name"] = seller["name"]
        if seller.get("address"): fields["seller_addr"] = seller["address"]
        if seller.get("tax_id"):  fields["seller_tax"] = seller["tax_id"]
    if buyer:
        if buyer.get("name"):     fields["buyer_name"] = buyer["name"]
        if buyer.get("address"):  fields["buyer_addr"] = buyer["address"]
        if buyer.get("tax_id"):   fields["buyer_tax"] = buyer["tax_id"]
    items = _extract_items(text)
    if items:
        fields["items"] = items
    notes = _extract_notes(text)
    if notes:
        fields["notes"] = notes
    return fields


def try_text_extraction(pdf_bytes: bytes, strict: bool = True) -> Optional[Dict[str, Any]]:
    t0 = time.time()
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except ImportError:
        logger.info("[text_path] pypdf 未安装 · fallback Gemini")
        return None
    except Exception as e:
        logger.info(f"[text_path] pypdf 解析失败 · fallback Gemini · {type(e).__name__}: {e}")
        return None

    n_pages = len(reader.pages)
    if n_pages == 0:
        return None

    page_texts: List[str] = []
    total_text = 0
    for p in reader.pages:
        try:
            t = p.extract_text() or ""
        except Exception:
            t = ""
        page_texts.append(t)
        total_text += len(t)

    avg_per_page = total_text / max(n_pages, 1)
    if avg_per_page < MIN_TEXT_PER_PAGE:
        logger.info(
            f"[text_path] 平均字符 {avg_per_page:.0f} < {MIN_TEXT_PER_PAGE} · 视为扫描件 · fallback Gemini"
        )
        return None

    full_text = "\n".join(page_texts)

    all_inv_nos = set()
    for m in RE_INVOICE_NO.finditer(full_text):
        v = m.group(1).strip()
        if any(c.isalpha() for c in v):
            all_inv_nos.add(v)
    if len(all_inv_nos) > 1:
        logger.info(
            f"[text_path] 检测到多张发票({len(all_inv_nos)} 个 invoice_no)· fallback Gemini · {sorted(all_inv_nos)}"
        )
        return None

    full_fields = _extract_fields_from_text(full_text)

    # 严格门槛:invoice_no + total + seller_tax + buyer_tax 四件套
    # buyer_tax 必须有 = ลูกค้า 块抽取成功 = buyer 信息完整(name + addr + tax)
    # 抽不到 buyer_tax → fallback Gemini(让 Gemini 兜底边界场景)
    # v118.32.5.5.9 · strict=False(销项税核查用):放宽到 invoice_no + total · buyer_tax 散客可空
    if strict:
        ok = bool(
            full_fields.get("invoice_number")
            and full_fields.get("total_amount")
            and full_fields.get("seller_tax")
            and full_fields.get("buyer_tax")
        )
    else:
        ok = bool(
            full_fields.get("invoice_number")
            and full_fields.get("total_amount")
        )
    if not ok:
        logger.info(
            f"[text_path] 关键字段缺失 · fallback Gemini · 已抽:{sorted(full_fields.keys())}"
        )
        return None

    pages_out = []
    for idx, text in enumerate(page_texts):
        pages_out.append({
            "page": idx + 1,
            "fields": dict(full_fields),
            "raw_text": text,
            "input_tokens": 0,
            "output_tokens": 0,
            "is_copy": False,
            "is_duplicate": False,
        })

    elapsed = int((time.time() - t0) * 1000)
    n_fields = len(full_fields)
    n_items = len(full_fields.get("items", []))
    logger.info(
        f"✅ [text_path] 文本路径成功 · {n_pages} 页 · {elapsed} ms · "
        f"{n_fields} 字段 · {n_items} items · 跳过 Gemini · 省 ~{n_pages * 8} 秒"
    )
    return {
        "pages": pages_out,
        "page_count": n_pages,
        "elapsed_ms": elapsed,
        "engine": "text",
    }
