# -*- coding: utf-8 -*-
"""image-direct 直读主路(2026-07-05 Vision 消融定案·S2 分流)。

图片/扫描短文档(≤3 页,非多页对账件)不再过 L1 Vision:原图直喂档位多模态模型
(tier=flash_lite → economy=3.1-lite / direct35=3.5),用与 L2 相同的 doc-type
提示词出同一套 schema。六轮 411 样本实测:钱字段零损失、越糊越稳、省约一半。

Vision 路(page_runner)整建制保留,承担两件事:
  1. 长表/多页对账件的主路(路由器直接分给它——B 吐几百行 JSON 会顶爆 token);
  2. 直读的回落兜底:parse 失败/勾稽穿底/结构硬伤 → 抛 DirectReadFallback,
     调用方(pipeline)整件转回 Vision 路重跑。路由阈值判错也不丢件。

确定性闸替代 Vision 词级置信(实测该信号在真图上基本沉睡:L3 仅触发 2/32):
  硬闸(回落)= 金额勾稽(_check_amount_math)· 总额缺失 · sanity 结构硬伤
  (sanity 自带税号 mod-11 校验——校验位不符即回落,与实测"A 读税号微好"对齐);
  软闸(标注)= 单号缺失(实测 B 单号反而比 Vision 路更准,回落救不了,不回落)。

秒级回退:env OCR_IMAGE_DIRECT=0 → 全量走原 Vision 链,零迁移。
"""

from __future__ import annotations

import contextvars
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from pydantic import ValidationError

from .cost import _compute_total_cost
from .gl_balance_chain import repair_gl_document
from .layer2_prompts import _SYSTEM_PROMPT
from .layer2_structure import _DOC_PROMPTS, _DOC_SCHEMAS
from .sanity import credit_note_review_reason, evaluate_sanity, infer_missing_discount
from .schemas import BusinessDocumentType, PipelinePageResult, PipelineResult, ThaiInvoice
from .triggers import _bucket_confidence, _check_amount_math
from .validators import validate_invoice_date

logger = logging.getLogger(__name__)

ENGINE_DIRECT = "image_direct"
# 回落后走的仍是 pipeline_v1,engine 打上标记 → ocr_cost_log 可直接量回落率
ENGINE_FALLBACK = "pipeline_v1_id_fb"

# 路由阈值:崩点是【单页行数】不是页数——run_file 逐页独立调用,每页自带 output 预算
# (实测发票每页 ~900 tok,远低于上限),多装几页不会顶爆。真正吐几百行的是长表,由
# _TABLE_DOC_TYPES 单独挡。上限只用来兜住"页数离谱到并发也扛不住"的件,回落兜底不丢件。
MAX_DIRECT_PAGES = int(os.environ.get("OCR_IMAGE_DIRECT_MAX_PAGES", "20"))
_TABLE_DOC_TYPES = ("bank_statement", "general_ledger")

# 多页并发 · 与 Vision 路 OCR_PDF_PAGE_WORKERS 同口径(各页独立无跨页依赖)。
# 串行时 8 页要 82s,用户等不起;Vision 路正是靠并发把 8 页压到 14s。
DIRECT_PAGE_WORKERS = int(os.environ.get("OCR_IMAGE_DIRECT_WORKERS", "4"))

_TIMEOUT_S = 60
_MAX_RETRIES = 1

_IMAGE_INPUT_NOTE = (
    "\n\nINPUT CHANGE: the input is the document IMAGE attached to this request, "
    "not pre-extracted OCR text. Read every character directly from the image "
    "and fill the exact same JSON schema. Same rules apply."
)

_BANK_STATEMENT_IMAGE_PROMPT = """Read EVERY visible transaction row from this Thai bank-statement IMAGE. Return one compact JSON object only; never summarize, sample, merge, or omit rows.

Schema:
{
  "document_type": "bank_statement",
  "bank_name": "",
  "opening_balance": "number string or empty",
  "closing_balance": "number string or empty",
  "entries": [{
    "transaction_date": "YYYY-MM-DD or empty",
    "transaction_date_raw": "exact printed date",
    "description": "printed description, max 80 characters",
    "deposit": "number string or empty",
    "withdrawal": "number string or empty",
    "balance": "running balance or empty"
  }]
}

Use one entry per printed row. Put a balance-forward value in opening_balance, not entries, and the final visible running balance in closing_balance. Amounts may only come from printed Deposit, Withdrawal, or Balance columns; never treat reference, account, or description digits as money. Dates ending in two-digit year 26 mean 2026. For four-digit Buddhist years subtract 543. Preserve the exact printed date in transaction_date_raw. Remove commas and currency symbols. Keep each description under 80 characters. Skip headers and totals."""


class DirectReadFallback(Exception):
    """直读不可信/失败 → 调用方整件回落 Vision 路。"""


def enabled() -> bool:
    return os.environ.get("OCR_IMAGE_DIRECT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def route_direct(page_count: int, document_type: BusinessDocumentType) -> bool:
    """确定性路由:长表/多页对账件 → Vision 路;其余 → 直读。

    判据是文档类型不是页数:一份 PDF 装 8 张独立发票,页数虽多但每页各自成篇,逐页直读
    没有跨页依赖;而对账单/总账哪怕 2 页也要跨页续表(余额链、表头),逐页读会切断上下文。
    早期按纯页数一刀切,把多票打包的进项/销项批误判成长表推去 Vision 路——那条路 L2 只吃
    L1 文本看不到原图,Vision 读错就无从纠正(2026-07-20 佛历年 2569→2559 事故)。
    """
    if document_type in _TABLE_DOC_TYPES:
        return page_count < 2
    return page_count <= MAX_DIRECT_PAGES


def _sniff_mime(image_bytes: bytes) -> str:
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:2] == b"\xff\xd8":
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes[:3] == b"GIF":
        return "image/gif"
    return "image/png"  # PDF 渲染页就是 PNG;未知类型按 PNG 送,模型端自会报错


def _call_model(
    image_bytes: bytes,
    document_type: BusinessDocumentType,
    api_key: Optional[str],
    tier: str = "flash_lite",
):
    from services.ai_gateway import backends

    if document_type == "bank_statement":
        sys_prompt = _BANK_STATEMENT_IMAGE_PROMPT
    else:
        base_prompt = (
            _SYSTEM_PROMPT if document_type in ("auto", "invoice") else _DOC_PROMPTS[document_type]
        )
        sys_prompt = base_prompt + _IMAGE_INPUT_NOTE
    # 与 L2 同口径兜 env:aistudio provider 只认显式 key(vertex 走 SA 忽略此参)
    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    request_options = {}
    if document_type == "bank_statement":
        request_options["max_tokens"] = 16384
    return backends.get_provider().multimodal_to_json(
        sys_prompt,
        [(image_bytes, _sniff_mime(image_bytes))],
        tier=tier,
        api_key=key,
        timeout_s=_TIMEOUT_S,
        max_retries=_MAX_RETRIES,
        **request_options,
    )


# ── 双读一致性(台账 #3 · 04 号方案 B 档:金额分级)────────────────────
# 治自洽性幻觉:整套数字编错但勾稽自平,确定性闸全绿(实证 trap05 508.97→5518897)。
# 两次独立读撞出同一套错数字概率极低;不一致 → 人工,不机器仲裁谁对。
# 只覆盖"直读一次过闸"的票——回落票走 Vision 链整套重跑,天然已是双读。
BIG_TICKET_THB = float(os.environ.get("OCR_DOUBLE_READ_BIG_THB", "2000"))
_VERIFY_FIELDS = ("total_amount", "vat", "subtotal", "seller_tax")
_VERIFY_TOL_THB = 0.5  # 与勾稽闸同容差


def double_read_enabled() -> bool:
    # 默认关(2026-07-06 ROI 实验:双读对钱字段独家保护=0·与确定性闸完全冗余·且是成本贵尾巴,
    # 见记忆 double-read-roi-experiment)。需要时 env OCR_DOUBLE_READ=1 一键恢复。
    return os.environ.get("OCR_DOUBLE_READ", "0").strip().lower() not in ("0", "false", "no", "off")


def _perturb_jpeg(image_bytes: bytes) -> bytes:
    """小票二读用同档模型 → 图像轻微重压缩打破确定性重复错(同族共病对策)。失败原图。"""
    try:
        import io as _io

        from PIL import Image

        buf = _io.BytesIO()
        Image.open(_io.BytesIO(image_bytes)).convert("RGB").save(buf, format="JPEG", quality=85)
        out = buf.getvalue()
        return out or image_bytes
    except Exception:  # noqa: BLE001 — 扰动只是加强项,绝不因它断链
        return image_bytes


def _verify_mismatches(first: ThaiInvoice, second: ThaiInvoice) -> List[str]:
    from .money import normalize_id, normalize_money

    out: List[str] = []
    for f in _VERIFY_FIELDS:
        va = str(getattr(first, f, "") or "").strip()
        vb = str(getattr(second, f, "") or "").strip()
        if f == "seller_tax":
            ok = normalize_id(va) == normalize_id(vb)
        else:
            na, nb = normalize_money(va), normalize_money(vb)
            if na is None and nb is None:
                ok = True
            elif na is None or nb is None:
                ok = False
            else:
                ok = abs(na - nb) <= _VERIFY_TOL_THB
        if not ok:
            out.append(f"double_read: {f} 两读不一致({va or '空'} vs {vb or '空'})")
    return out


def _second_read(image_bytes: bytes, first: ThaiInvoice, api_key: Optional[str], page_number: int):
    """二读:大票(≥阈值)升 3.5 跨模型防共病;小票同档 + 图像扰动。崩了 → 回落 Vision 路
    (它整链重跑,本身就是双读)。返回 (outcome, invoice)。"""
    from .money import normalize_money

    total = normalize_money(first.total_amount)
    big = total is not None and abs(total) >= BIG_TICKET_THB
    tier = "fallback" if big else "flash_lite"
    img = image_bytes if big else _perturb_jpeg(image_bytes)
    try:
        o2 = _call_model(img, "invoice", api_key, tier=tier)
    except Exception as e:  # noqa: BLE001
        raise DirectReadFallback(f"page {page_number}: second read raise: {e}") from e
    if not o2.ok or not isinstance(o2.data, dict):
        raise DirectReadFallback(f"page {page_number}: second read {o2.error_kind or 'empty'}")
    try:
        inv2 = ThaiInvoice(**o2.data)
    except ValidationError as e:
        raise DirectReadFallback(f"page {page_number}: second read schema: {e}") from e
    return o2, inv2


def read_page(
    image_bytes: bytes,
    page_number: int,
    document_type: BusinessDocumentType = "auto",
    api_key: Optional[str] = None,
) -> PipelinePageResult:
    """单页直读 → PipelinePageResult(layer_chain=["ID"])。不可信即抛 DirectReadFallback。"""
    t0 = time.time()
    try:
        outcome = _call_model(image_bytes, document_type, api_key)
    except Exception as e:  # noqa: BLE001 — 直读任何炸法都回落 Vision 路,不让用户看 500
        raise DirectReadFallback(f"provider raise: {type(e).__name__}: {e}") from e
    if not outcome.ok or not isinstance(outcome.data, dict):
        raise DirectReadFallback(f"page {page_number}: {outcome.error_kind or 'empty output'}")

    invoice = ThaiInvoice(is_not_invoice=True)
    document = None
    warnings: List[str] = []
    if document_type in ("auto", "invoice"):
        try:
            invoice = ThaiInvoice(**outcome.data)
        except ValidationError as e:
            raise DirectReadFallback(f"page {page_number}: invoice schema: {e}") from e
        warnings.extend(_invoice_hard_gates(invoice, page_number))
        warnings.extend(_invoice_soft_flags(invoice))
    else:
        try:
            document = _DOC_SCHEMAS[document_type](**outcome.data)
        except ValidationError as e:
            raise DirectReadFallback(f"page {page_number}: {document_type} schema: {e}") from e
        if document_type == "general_ledger":
            # 台账#10 · 与 Vision 路(page_runner)同一套余额链修复,两链不劈叉
            warnings.extend(repair_gl_document(document))

    # 贷记单方向性单据强制人工(两链共判 · sanity.credit_note_review_reason)
    force_review = False
    cn_reason = credit_note_review_reason(invoice)
    if cn_reason:
        warnings.append(cn_reason)
        force_review = True

    # 日期离谱强制人工:降 0.05 置信压不到 needs_review,而年份读错一位会整张票记错
    # 会计期与税期(2026-07-20 事故:2016-05-31 落库并推进 Express 的 2559-05 税期)。
    # 不回落 —— Vision 路读日期更差,回落是净亏,该由人判是补录旧账还是读错年。
    date_issues = validate_invoice_date(invoice)
    if date_issues:
        warnings.extend(date_issues)
        force_review = True

    # 双读一致性:过闸的发票再独立读一遍,钱面四件不一致 → 人工(差异原样进警告)。
    chain = ["ID"]
    l3_in = l3_out = 0
    l3_model = ""
    if (
        document_type in ("auto", "invoice")
        and not invoice.is_not_invoice
        and double_read_enabled()
    ):
        o2, inv2 = _second_read(image_bytes, invoice, api_key, page_number)
        chain = ["ID", "ID2"]
        l3_in, l3_out, l3_model = o2.input_tokens, o2.output_tokens, o2.model
        mismatches = _verify_mismatches(invoice, inv2)
        if mismatches:
            warnings.extend(mismatches)
            force_review = True
            logger.warning(
                "direct-read double-read mismatch page %d: %s", page_number, "; ".join(mismatches)
            )

    # 与 triggers 同口径:0.95 起步、每条软标注 -0.05;≥0.98 才 auto(直读永达不到,
    # 维持发票 confirm-first 现状),0.90-0.98 = yellow_confirm,再低转人工。
    final_confidence = round(max(0.0, 0.95 - 0.05 * len(warnings)), 4)
    band = _bucket_confidence(final_confidence, force_review)
    return PipelinePageResult(
        page_number=page_number,
        invoice=invoice,
        document_type=document_type,
        document=document,
        layer_chain=chain,
        trigger_reasons=[],
        layer1_avg_confidence=0.0,
        layer2_input_tokens=outcome.input_tokens,
        layer2_output_tokens=outcome.output_tokens,
        layer2_model=outcome.model,
        layer3_input_tokens=l3_in,
        layer3_output_tokens=l3_out,
        layer3_model=l3_model if (l3_in or l3_out) else "",
        layer2_ms=int((time.time() - t0) * 1000),
        total_ms=int((time.time() - t0) * 1000),
        needs_manual_review=band == "needs_review",
        confidence_band=band,
        final_confidence=final_confidence,
        field_confidence={},
        validation_warnings=warnings,
    )


def _invoice_hard_gates(invoice: ThaiInvoice, page_number: int) -> List[str]:
    """钱面硬闸:不过 → 回落 Vision 路对质。通过 → 返回留痕(折扣回填说明)。"""
    if invoice.is_not_invoice:
        return []
    notes: List[str] = []
    repaired = infer_missing_discount(invoice)
    if repaired:
        notes.append(repaired)
    if not str(invoice.total_amount or "").strip():
        raise DirectReadFallback(f"page {page_number}: total_amount missing")
    math_issue = _check_amount_math(invoice)
    if math_issue:
        raise DirectReadFallback(f"page {page_number}: {math_issue}")
    sanity_issues = evaluate_sanity(invoice)
    if sanity_issues:
        raise DirectReadFallback(f"page {page_number}: sanity: {'; '.join(sanity_issues)}")
    return notes


def _invoice_soft_flags(invoice: ThaiInvoice) -> List[str]:
    """软标注(降置信不回落):实测 B 读单号反而比 Vision 路准,回落救不了这些。"""
    if invoice.is_not_invoice:
        return []
    if not str(invoice.invoice_number or "").strip():
        return ["direct_read: invoice_number missing"]
    return []


def run_file(
    page_image_bytes_list: List[bytes],
    document_type: BusinessDocumentType = "auto",
    api_key: Optional[str] = None,
) -> PipelineResult:
    """整件直读(调用方已过 enabled()+route_direct())。任一页不可信 → 整件回落。

    多页并发:各页独立无跨页依赖(与 Vision 路 _process_pages 同理),按页序还原结果。
    contextvars 每任务一份独立副本 —— few-shot 注入靠请求级 user/tenant 上下文,
    不复制则多页 PDF 的工作线程读不到(Context 不可并发重入,不能跨 worker 复用)。
    """
    t0 = time.time()

    def _run_page(index: int, image_bytes: bytes) -> PipelinePageResult:
        return read_page(
            image_bytes, page_number=index, document_type=document_type, api_key=api_key
        )

    n_pages = len(page_image_bytes_list)
    if n_pages > 1 and DIRECT_PAGE_WORKERS > 1:
        by_page: dict = {}
        with ThreadPoolExecutor(max_workers=min(DIRECT_PAGE_WORKERS, n_pages)) as ex:
            futs = {
                ex.submit(contextvars.copy_context().run, _run_page, i, ib): i
                for i, ib in enumerate(page_image_bytes_list, start=1)
            }
            for fut in as_completed(futs):
                by_page[futs[fut]] = fut.result()
        pages = [by_page[i] for i in range(1, n_pages + 1)]
    else:
        pages = [_run_page(i, ib) for i, ib in enumerate(page_image_bytes_list, start=1)]
    return PipelineResult(
        pages=pages,
        page_count=len(pages),
        elapsed_ms=int((time.time() - t0) * 1000),
        engine=ENGINE_DIRECT,
        estimated_cost_thb=_compute_total_cost(pages),
    )
