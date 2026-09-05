# -*- coding: utf-8 -*-
"""Image/PDF OCR bridge preserving ledger validation and ConvertResult contracts.

Enterprise bank/GL uses the frozen financial pipeline. Other grids keep their
specialized schema. Truncated or unavailable OCR never returns a partial success.
"""

from __future__ import annotations

import logging
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
from services.ocr.direct_read import _sniff_mime
from services.cost.usage_context import reset_usage_context, set_usage_context

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
    # pages=1:本桥一次调用恰好一页图,逐调用记 1 页,SUM(pages) 即 fileconv 的真实页数
    # (此前不记,引擎成本页 cost_per_page 对 fileconv 恒显「—」)。
    usage_token = set_usage_context("fileconv", pages=1)
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
        reset_usage_context(usage_token)
        attribution.reset_attribution(token)


from services.fileconv.ocr_images import rasterize_pdf as _rasterize_pdf


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
    """网关调用 + 异常收敛。截断(MAX_TOKENS)已在 provider 层收敛为 error_kind='parse'
    (见 providers/aistudio._safe_raw),此处只兜未知异常 —— 任何炸法都不许 500 用户。"""
    try:
        return call(
            prompt, image_bytes, tenant_id=tenant_id, api_key=api_key, max_tokens=max_tokens
        )
    except Exception as e:  # noqa: BLE001
        logger.info("ocr_bridge: provider raise 收敛 · %s: %s", type(e).__name__, e)
        return _FailedOutcome("provider")


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
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    _pdf_bytes: Optional[bytes] = None,
) -> ConvertResult:
    """Run image OCR under the Earn-selected fileconv engine."""
    if provider_call is not None:
        return _convert_images_active(images, source_name, tenant_id, api_key, provider_call)

    from services.ocr.engine_policy import engine_context
    from services.cost.usage_context import usage_context
    from services.ai_gateway.attribution import set_attribution, reset_attribution

    token = set_attribution(TASK_FILECONV_OCR, tenant_id=tenant_id)
    try:
        with (
            engine_context(TASK_FILECONV_OCR, plan_code=plan_code, is_exempt=is_exempt),
            usage_context("fileconv", pages=len(images)),
        ):
            return _convert_images_active(
                images,
                source_name,
                tenant_id,
                api_key,
                _default_provider_call,
                pdf_bytes=_pdf_bytes,
            )
    finally:
        reset_attribution(token)


def _convert_images_active(
    images: List[bytes],
    source_name: str,
    tenant_id: Optional[str],
    api_key: Optional[str],
    provider_call: ProviderCall,
    *,
    pdf_bytes: Optional[bytes] = None,
) -> ConvertResult:
    """一批页图(单图=一页)→ ConvertResult。分类 → 逐页直吐 → 适配 → 守恒校验。"""
    if not images:
        return _reject(STATUS_OCR_UNAVAILABLE, source_name, "无可识别页面")
    call = provider_call

    ocr_doc_type = _classify(images[0], call, tenant_id, api_key)
    if ocr_doc_type not in _LEDGER_DOC_TYPES:
        return _convert_generic(images, source_name, ocr_doc_type, call, tenant_id, api_key)

    is_gl = ocr_doc_type == "general_ledger"
    from services.ocr.enterprise_pipeline import category_for, run as enterprise_run

    candidate = None
    if category_for(ocr_doc_type):
        try:
            candidate = enterprise_run(images, "gl" if is_gl else "bank", pdf=pdf_bytes)
        except Exception:
            return _reject(STATUS_OCR_UNAVAILABLE, source_name, "Enterprise OCR 引擎不可用")
    rows: List[LedgerRow] = []
    first_doc = last_doc = None
    for index, image_bytes in enumerate(images):
        page = (
            _PageOutcome(True, document=candidate.pages[index].document)
            if candidate
            else _read_page(image_bytes, ocr_doc_type, call, tenant_id, api_key)
        )
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
    if candidate:
        stats.update(
            engine=candidate.engine,
            extraction_audit=[p.extraction_audit for p in candidate.pages],
            estimated_cost_thb=candidate.estimated_cost_thb,
            elapsed_ms=candidate.elapsed_ms,
        )
        if any(p.needs_manual_review for p in candidate.pages):
            issues.append(
                Issue(kind="ocr_review", line_no=0, message="OCR 待复核 / ต้องตรวจสอบผล OCR")
            )
    table = Table(
        name="GL Ledger" if is_gl else "Bank Statement",
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


from services.fileconv.ocr_generic import convert_generic as _convert_generic


def convert_image(
    image_bytes: bytes,
    source_name: str = "",
    *,
    tenant_id: Optional[str] = None,
    api_key: Optional[str] = None,
    provider_call: Optional[ProviderCall] = None,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
) -> ConvertResult:
    """单张图片(jpg/png/webp)→ ConvertResult。"""
    return convert_images(
        [image_bytes],
        source_name,
        tenant_id=tenant_id,
        api_key=api_key,
        provider_call=provider_call,
        plan_code=plan_code,
        is_exempt=is_exempt,
    )


def convert_scanned_pdf(
    pdf_bytes: bytes,
    source_name: str = "",
    *,
    tenant_id: Optional[str] = None,
    api_key: Optional[str] = None,
    provider_call: Optional[ProviderCall] = None,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
) -> ConvertResult:
    """无文字层 PDF(扫描件)→ 逐页栅格化 → OCR → ConvertResult。栅格化失败诚实拒绝。"""
    from services.ocr.engine_policy import engine_context, active_mode

    with engine_context(TASK_FILECONV_OCR, plan_code=plan_code, is_exempt=is_exempt):
        enterprise_selected = active_mode() == "enterprise" and provider_call is None
    pages = _rasterize_pdf(pdf_bytes, dpi=200) if enterprise_selected else _rasterize_pdf(pdf_bytes)
    if not pages:
        return _reject(STATUS_OCR_UNAVAILABLE, source_name, "扫描件无法栅格化(疑损坏 PDF)")
    return convert_images(
        pages,
        source_name,
        tenant_id=tenant_id,
        api_key=api_key,
        provider_call=provider_call,
        plan_code=plan_code,
        is_exempt=is_exempt,
        _pdf_bytes=pdf_bytes,
    )
