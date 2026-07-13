# -*- coding: utf-8 -*-
"""扫描件/图片 → ConvertResult 的 OCR 桥(K1c)。

缝点唯一:convert.py 的 no_text_layer 分支与图片入口把件交到这里,走 multimodal 直吐
结构化行(bank_statement 图片已在生产走通此范式),再复用 K1a 的守恒校验(validate_ledger)
出同一份 ConvertResult 契约。convert_pages 纯函数核心与既有 status 语义不动。

命门 —— 截断硬闸:模型输出被 max_output_tokens 截断时,JSON 在网关侧解析失败收敛为
outcome.ok=False / error_kind='parse'(见 providers/*._gen_json)。本桥据此结构化拒绝
(STATUS_OCR_INCOMPLETE),绝不把半截行集当成功出件 —— 截断尾行会让余额链假自洽,比诚实
拒绝更危险。第二道网:文档印刷期末余额/页脚合计与解析结果对照,不一致进 issues。

契约禁区:OCR 管线本体(pipeline/controller/direct_read)一行不改,只消费网关(transport
.multimodal_to_json)与 schema(layer2_structure 的 _DOC_PROMPTS/_DOC_SCHEMAS)。
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Callable, Dict, List, Optional

from services.fileconv import validate as validate_mod
from services.fileconv.model import (
    BANK_STATEMENT,
    GENERIC_TABLE,
    GL_LEDGER,
    ISSUE_CLOSING_ANCHOR,
    ISSUE_FOOTER_TOTAL,
    STATUS_OCR_INCOMPLETE,
    STATUS_OCR_UNAVAILABLE,
    STATUS_OK,
    VAT_REPORT,
    ConvertResult,
    Issue,
    LedgerRow,
    Table,
)
from services.fileconv.ledger import LEDGER_COLUMNS, to_table_rows

logger = logging.getLogger(__name__)

# 归因标签:成本落 ai_usage 时归到本 task + 租户名下(用户积分扣费本单不做,只观测)。
TASK_FILECONV_OCR = "fileconv_ocr"

# 提取用大 token 预算:schemas_documents L169-171 血泪——80+ 行流水 8192 会截断,16384 压到 0;
# 分类回一个词,但 3.1-lite 思考 token 计入 max_output_tokens(真调实锤 64 必截),给 2048。
# 截断硬闸对两者都在。超时 120s:密表台账页真调实锤 60s 不够(整页 40+ 行结构化输出),
# 宁可诚实慢,不把读得完的页误报成不可用。
_EXTRACT_MAX_TOKENS = 16384
_CLASSIFY_MAX_TOKENS = 2048
_OCR_TIMEOUT_S = 120
_TOL = Decimal("0.01")

# 扫描件栅格化 DPI:144 让泰文热敏/台账小字放大后仍清晰(同 pdf_utils.render_page_png)。
_RENDER_DPI = 144

_IMAGE_INPUT_NOTE = (
    "\n\nINPUT: the document IMAGE is attached to this request, not pre-extracted OCR "
    "text. Read every character directly from the image and fill the exact JSON schema. "
    "Same field-source rules apply."
)

_CLASSIFY_PROMPT = (
    "You are a financial document classifier. Look at the attached document image and "
    'reply ONLY compact JSON: {"document_type": "<type>"} where <type> is exactly one of:\n'
    "- general_ledger : accounting ledger with Debit/Credit and running balance columns\n"
    "- bank_statement : bank account statement with deposit/withdrawal/balance columns\n"
    "- vat_report : VAT input/output tax report (ภาษีซื้อ/ภาษีขาย)\n"
    "- generic_table : anything else / cannot tell\n"
    "Return generic_table when unsure — do not guess a stronger type."
)

# multimodal 直吐路只覆盖带守恒价值的两类;其余落 generic 诚实(不假装能勾稽任意网格)。
_LEDGER_DOC_TYPES = {"general_ledger", "bank_statement"}
_DOC_TYPE_TO_FILECONV = {
    "general_ledger": GL_LEDGER,
    "bank_statement": BANK_STATEMENT,
    "vat_report": VAT_REPORT,
    "generic_table": GENERIC_TABLE,
}


class _PageOutcome:
    """一页 OCR 结果的最小载体(ok + 解析后的 document 或截断/失败原因)。"""

    __slots__ = ("ok", "incomplete", "document")

    def __init__(self, ok: bool, incomplete: bool = False, document=None):
        self.ok = ok
        self.incomplete = incomplete  # True = 读了但截断/不可解析(与够不到模型区分)
        self.document = document


# provider 调用注入点(单一缝):默认走网关 transport;单测注入 fake 全覆盖不触网络。
ProviderCall = Callable[..., object]


def _default_provider_call(
    prompt: str,
    image_bytes: bytes,
    *,
    tenant_id: Optional[str],
    api_key: Optional[str],
    max_tokens: int,
):
    """照 direct_read._call_model 用法调网关多模态直吐;attribution 归因到 fileconv_ocr。

    contextvars 是线程本地(attribution.py L11-13 明警):本桥同线程内 set→finally reset,
    transport 显式再收 task/tenant 兜底,双保险。"""
    import os

    from services.ai_gateway import attribution, transport

    # 与 direct_read 同口径兜 env:aistudio provider 只认显式 key(vertex 走 SA 忽略此参)。
    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    token = attribution.set_attribution(TASK_FILECONV_OCR, tenant_id=tenant_id)
    try:
        return transport.multimodal_to_json(
            prompt,
            [(image_bytes, _sniff_mime(image_bytes))],
            tier="flash_lite",
            api_key=key,
            max_tokens=max_tokens,
            timeout_s=_OCR_TIMEOUT_S,
            task=TASK_FILECONV_OCR,
            tenant_id=tenant_id,
        )
    finally:
        attribution.reset_attribution(token)


def _sniff_mime(image_bytes: bytes) -> str:
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:2] == b"\xff\xd8":
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes[:3] == b"GIF":
        return "image/gif"
    return "image/png"


def _rasterize_pdf(pdf_bytes: bytes) -> Optional[List[bytes]]:
    """扫描件 PDF 逐页栅格化为 PNG(消费 PyMuPDF,不碰 OCR 管线)。失败返回 None。"""
    try:
        import fitz  # PyMuPDF
    except ImportError:  # pragma: no cover
        logger.error("ocr_bridge: PyMuPDF (fitz) 未安装 · 无法栅格化扫描件")
        return None
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        matrix = fitz.Matrix(_RENDER_DPI / 72.0, _RENDER_DPI / 72.0)
        return [
            doc.load_page(i).get_pixmap(matrix=matrix, alpha=False).tobytes("png")
            for i in range(doc.page_count)
        ]
    except Exception as e:  # noqa: BLE001
        logger.info("ocr_bridge: 扫描件栅格化失败 · %s: %s", type(e).__name__, e)
        return None
    finally:
        if doc is not None:
            doc.close()


# ── Decimal 转换(禁 float 中转;OCR 侧 entries 值是 str)──────────────────────
def _dec(raw: str) -> Optional[Decimal]:
    """金额串 → Decimal。空 = None;括号记负(会计惯例);解析不了 = None(不静默造零)。"""
    s = (raw or "").strip().replace(",", "").replace(" ", "")
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    try:
        val = Decimal(s)
    except (InvalidOperation, ValueError):
        return None
    return -val if neg else val


def _dec0(raw: str) -> Decimal:
    v = _dec(raw)
    return v if v is not None else Decimal("0")


# ── 适配器:GLEntry/BankStatementEntry(str) → LedgerRow(Decimal)─────────────
# 统一走借贷三栏形态:GL debit/credit 原样;银行 deposit→debit(入账增余额)、withdrawal→
# credit(出账减余额),使 validate_ledger 的 base+debit-credit=balance 恒等成立。line_no
# 全局回填(跨页连续)保 issues 可定位。
def _gl_rows(entries: list, start_line: int) -> List[LedgerRow]:
    rows: List[LedgerRow] = []
    for i, e in enumerate(entries):
        rows.append(
            LedgerRow(
                line_no=start_line + i,
                account=(e.account_code or "").strip(),
                date=(e.transaction_date_raw or e.transaction_date or "").strip(),
                date_ce=(e.transaction_date or "").strip(),
                doc_no=(e.voucher_no or "").strip(),
                description=(e.description or "").strip(),
                balance=_dec0(e.balance),
                debit=_dec(e.debit),
                credit=_dec(e.credit),
            )
        )
    return rows


def _bank_rows(entries: list, start_line: int) -> List[LedgerRow]:
    rows: List[LedgerRow] = []
    for i, e in enumerate(entries):
        rows.append(
            LedgerRow(
                line_no=start_line + i,
                account="",  # 单账户流水,validate_ledger 按空科目跑一条链
                date=(e.transaction_date_raw or e.transaction_date or "").strip(),
                date_ce=(e.transaction_date or "").strip(),
                doc_no=(e.reference or "").strip(),
                description=(e.description or "").strip(),
                balance=_dec0(e.balance),
                debit=_dec(e.deposit),
                credit=_dec(e.withdrawal),
            )
        )
    return rows


def _build_opening(rows: List[LedgerRow], doc_opening: Optional[Decimal]) -> Dict[str, Decimal]:
    """每科目期初:首科目认印刷期初(能真查首行);其余科目/无印刷期初时用首行回推作锚
    (首行自洽、后续行受真查)。回推不掩错——独立的期末余额锚是治截断的第二道网。"""
    opening: Dict[str, Decimal] = {}
    for r in rows:
        if r.account in opening:
            continue
        if doc_opening is not None and not opening:
            opening[r.account] = doc_opening
        else:
            opening[r.account] = r.balance - (r.debit or Decimal("0")) + (r.credit or Decimal("0"))
    return opening


def _anchor_issues(rows: List[LedgerRow], doc, is_gl: bool) -> List[Issue]:
    """独立锚对照:印刷期末余额 vs 解析末行余额;GL 页脚 Total Debit/Credit vs 明细和。
    截断会砍掉尾行,末行余额与印刷期末余额随之对不上 → 这里点名(治「截断+假自洽」)。"""
    issues: List[Issue] = []
    if not rows:
        return issues
    closing = _dec(getattr(doc, "closing_balance", ""))
    if closing is not None and abs(closing - rows[-1].balance) > _TOL:
        issues.append(
            Issue(
                kind=ISSUE_CLOSING_ANCHOR,
                line_no=rows[-1].line_no,
                message="印刷期末余额 ≠ 解析末行余额(疑漏行/截断)",
                expected=f"{closing}",
                actual=f"{rows[-1].balance}",
            )
        )
    if is_gl:
        for field, side in (("total_debit", "debit"), ("total_credit", "credit")):
            printed = _dec(getattr(doc, field, ""))
            if printed is None:
                continue
            got = sum((getattr(r, side) or Decimal("0")) for r in rows)
            if abs(printed - got) > _TOL:
                issues.append(
                    Issue(
                        kind=ISSUE_FOOTER_TOTAL,
                        line_no=rows[-1].line_no,
                        message=f"页脚印刷 {field} ≠ 明细{side}之和",
                        expected=f"{printed}",
                        actual=f"{got}",
                    )
                )
    return issues


# ── OCR 调用 + 截断硬闸 ────────────────────────────────────────────────────
class _FailedOutcome:
    """provider 异常泄漏时的收敛壳(与 ProviderOutcome 同形只留桥用到的三件)。"""

    __slots__ = ("ok", "data", "error_kind")

    def __init__(self, error_kind: str):
        self.ok = False
        self.data = None
        self.error_kind = error_kind


def _call_safe(
    call: ProviderCall, prompt: str, image_bytes: bytes, *, tenant_id, api_key, max_tokens
):
    """网关调用 + 异常收敛。aistudio 的 resp.text 快取器在 candidates 为空时抛 ValueError
    而非收敛 error_kind(真调实测:finish_reason=2 = MAX_TOKENS 截断走此路)——网关契约
    缺口,桥侧兜住:MAX_TOKENS 归 'parse'(= 截断,上层诚实拒绝),其余归 'provider'。"""
    try:
        return call(
            prompt, image_bytes, tenant_id=tenant_id, api_key=api_key, max_tokens=max_tokens
        )
    except Exception as e:  # noqa: BLE001 — 任何炸法都不许 500 用户,收敛成结构化拒绝
        msg = str(e)
        m = re.search(r"finish_reason\W*\S*\s+is\s+(\d+)", msg)
        truncated = "MAX_TOKENS" in msg.upper() or (m is not None and m.group(1) == "2")
        logger.info(
            "ocr_bridge: provider raise 收敛 · truncated=%s · %s", truncated, type(e).__name__
        )
        return _FailedOutcome("parse" if truncated else "provider")


def _classify(image_bytes: bytes, call: ProviderCall, tenant_id, api_key) -> str:
    """一次轻量分类 → OCR 侧 doc type(_DOC_TYPE_TO_FILECONV 的键)。
    读不到/不可解析/不认得 → generic_table 诚实。"""
    outcome = _call_safe(
        call,
        _CLASSIFY_PROMPT,
        image_bytes,
        tenant_id=tenant_id,
        api_key=api_key,
        max_tokens=_CLASSIFY_MAX_TOKENS,
    )
    if not getattr(outcome, "ok", False) or not isinstance(getattr(outcome, "data", None), dict):
        return "generic_table"
    raw = str(outcome.data.get("document_type", "")).strip().lower()
    return raw if raw in _DOC_TYPE_TO_FILECONV else "generic_table"


def _read_page(
    image_bytes: bytes, ocr_doc_type: str, call: ProviderCall, tenant_id, api_key
) -> _PageOutcome:
    """单页直吐 + schema 校验。截断/解析失败(error_kind='parse')→ incomplete=True(命门:
    上层据此拒绝整件)。够不到模型(auth/quota/timeout/provider)→ ok=False 非 incomplete。"""
    from pydantic import ValidationError

    from services.ocr.layer2_structure import _DOC_PROMPTS, _DOC_SCHEMAS

    outcome = _call_safe(
        call,
        _DOC_PROMPTS[ocr_doc_type] + _IMAGE_INPUT_NOTE,
        image_bytes,
        tenant_id=tenant_id,
        api_key=api_key,
        max_tokens=_EXTRACT_MAX_TOKENS,
    )
    if not getattr(outcome, "ok", False):
        # parse = JSON 不完整/被 max_tokens 截断(命门);其余 = 够不到模型。
        incomplete = getattr(outcome, "error_kind", None) == "parse"
        return _PageOutcome(ok=False, incomplete=incomplete)
    if not isinstance(getattr(outcome, "data", None), dict):
        return _PageOutcome(ok=False, incomplete=True)
    try:
        document = _DOC_SCHEMAS[ocr_doc_type](**outcome.data)
    except ValidationError:
        # schema 不满足 = 输出结构残缺(常由截断致)→ 诚实拒绝,不出半件。
        return _PageOutcome(ok=False, incomplete=True)
    return _PageOutcome(ok=True, document=document)


def _reject(status: str, source_name: str, reason: str) -> ConvertResult:
    return ConvertResult(
        doc_type="", status=status, source_name=source_name, stats={"reason": reason}
    )


# ── 编排:多页逐页调用,跨页余额链衔接 ─────────────────────────────────────
def convert_images(
    images: List[bytes],
    source_name: str,
    *,
    tenant_id: Optional[str] = None,
    api_key: Optional[str] = None,
    provider_call: Optional[ProviderCall] = None,
) -> ConvertResult:
    """一批页图(单图=一页)→ ConvertResult。分类 → 逐页直吐 → 适配 → 守恒校验。"""
    if not images:
        return _reject(STATUS_OCR_UNAVAILABLE, source_name, "无可识别页面")
    call = provider_call or _default_provider_call

    ocr_doc_type = _classify(images[0], call, tenant_id, api_key)
    if ocr_doc_type not in _LEDGER_DOC_TYPES:
        return _convert_generic(images, source_name, ocr_doc_type, call, tenant_id, api_key)

    is_gl = ocr_doc_type == "general_ledger"
    rows: List[LedgerRow] = []
    first_doc = last_doc = None
    for image_bytes in images:
        page = _read_page(image_bytes, ocr_doc_type, call, tenant_id, api_key)
        if not page.ok:
            if page.incomplete:
                return _reject(STATUS_OCR_INCOMPLETE, source_name, "OCR 输出截断/不完整,拒绝出件")
            return _reject(STATUS_OCR_UNAVAILABLE, source_name, "OCR 引擎不可用")
        first_doc = first_doc or page.document
        last_doc = page.document
        new = (_gl_rows if is_gl else _bank_rows)(page.document.entries, len(rows) + 1)
        rows.extend(new)

    opening = _build_opening(rows, _dec(getattr(first_doc, "opening_balance", "")))
    issues = validate_mod.validate_ledger(rows, opening)
    issues.extend(_anchor_issues(rows, last_doc, is_gl))
    stats = validate_mod.ledger_stats(rows, opening)
    stats["engine"] = "ocr_image_direct"
    stats["pages"] = len(images)
    table = Table(
        name={True: "GL Ledger", False: "Bank Statement"}[is_gl],
        columns=LEDGER_COLUMNS,
        rows=to_table_rows(rows),
    )
    return ConvertResult(
        doc_type=_DOC_TYPE_TO_FILECONV[ocr_doc_type],
        status=STATUS_OK,
        source_name=source_name,
        tables=[table],
        issues=issues,
        stats=stats,
    )


def _convert_generic(
    images: List[bytes], source_name: str, ocr_doc_type: str, call, tenant_id, api_key
) -> ConvertResult:
    """非台账/流水类:忠实抽网格,不假装能勾稽任意表(issues 为空 = 无守恒可判,诚实)。"""
    headers: List[str] = []
    grid: List[List] = []
    for image_bytes in images:
        page = _read_page(image_bytes, "generic_table", call, tenant_id, api_key)
        if not page.ok:
            status = STATUS_OCR_INCOMPLETE if page.incomplete else STATUS_OCR_UNAVAILABLE
            return _reject(status, source_name, "OCR 未能读出可用网格")
        doc = page.document
        if not headers and doc.headers:
            headers = list(doc.headers)
        for row in doc.rows:
            grid.append([row.get(h, "") for h in headers] if headers else list(row.values()))
    table = Table(name="Table", columns=headers or ["col1"], rows=grid)
    return ConvertResult(
        doc_type=_DOC_TYPE_TO_FILECONV.get(ocr_doc_type, GENERIC_TABLE),
        status=STATUS_OK,
        source_name=source_name,
        tables=[table],
        issues=[],
        stats={"row_count": len(grid), "engine": "ocr_image_direct", "pages": len(images)},
    )


def convert_image(
    image_bytes: bytes,
    source_name: str = "",
    *,
    tenant_id: Optional[str] = None,
    api_key: Optional[str] = None,
    provider_call: Optional[ProviderCall] = None,
) -> ConvertResult:
    """单张图片(jpg/png/webp)→ ConvertResult。"""
    return convert_images(
        [image_bytes],
        source_name,
        tenant_id=tenant_id,
        api_key=api_key,
        provider_call=provider_call,
    )


def convert_scanned_pdf(
    pdf_bytes: bytes,
    source_name: str = "",
    *,
    tenant_id: Optional[str] = None,
    api_key: Optional[str] = None,
    provider_call: Optional[ProviderCall] = None,
) -> ConvertResult:
    """无文字层 PDF(扫描件)→ 逐页栅格化 → OCR → ConvertResult。栅格化失败诚实拒绝。"""
    pages = _rasterize_pdf(pdf_bytes)
    if not pages:
        return _reject(STATUS_OCR_UNAVAILABLE, source_name, "扫描件无法栅格化(疑损坏 PDF)")
    return convert_images(
        pages,
        source_name,
        tenant_id=tenant_id,
        api_key=api_key,
        provider_call=provider_call,
    )
