# -*- coding: utf-8 -*-
"""这份料是什么 —— 零成本确定性识别(万能口 F1 的「认料」层)。

一行新识别逻辑都不写:判据全部来自既有识别件,本层只做两件事 ——
  ① 把它们按分层顺序串起来(L1 格式硬闸 → L2 文件名 → L3 内容指纹 → 认不出就说认不出);
  ② 把「路径入参」换成「字节入参」(附件落盘可能是密文,openpyxl/pdfplumber 不能直接吃盘上的
     那份;判据函数本身一个字没改)。

借了谁:
  workorder.steps.sort   _is_gl_name / _bank_from_filename / _is_sales_summary_name /
                         _head_is_gl / _head_is_bank / _head_is_sales / IMAGE_EXTS
  fileconv.classify      PDF 正文型分类(GL/银行/VAT/通用表)
  fileconv.text_layer    有没有文字层(= 走不走模型的唯一判据)
  vat.vat_file_classifier _filename_guess(票 vs 报告的文件名正则)
  ocr.entrypoints        白名单 + billing_quote(页数/格式硬闸,纯本地不烧钱)

红线:模型不参与本层。零成本信号全落空 + 用户也没说 = 【问】,不是让模型猜 ——
猜对省一次点击,猜错烧一次钱且结果全错,这个交换永远不划算。
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from services.steward import registry

logger = logging.getLogger(__name__)

# 判据模块一律函数内 import:本模块被 copy_file(答复文案层)拿去取料名常量,而文案层在
# 每一轮对话上都要 import —— 模块级拉进 ocr.pipeline / workorder.engine 那两棵树,等于给
# 每次答复渲染都背上一次重 import。

# 料的闭集(管家侧语义,不与工单 kinds 混用:工单那套带 status/flag 是产线语义)。
GL_LEDGER = "gl_ledger"
BANK_STATEMENT = "bank_statement"
SALES_SUMMARY = "sales_summary"
VAT_REPORT = "vat_report"
INVOICE = "invoice"
UNSUPPORTED = "unsupported"
UNKNOWN = "unknown"

_SHEET_EXTS = {".xlsx", ".xlsm", ".xls", ".csv"}
_XLSX_EXTS = {".xlsx", ".xlsm"}
_HEAD_ROWS = 15

# 表头里的销项报表强词(_head_is_sales 的词表含 ภาษีขาย,VAT 报表也有这列 —— 报表判据必须
# 排在汇总表之前,否则一份 ภ.พ.30 附表会被归成 POS 销售汇总)。
_VAT_HEADER_KW = ("รายงานภาษีขาย", "ภ.พ.30", "ภพ.30", "vat report", "ภาษีขาย")

# 格式硬闸:这几个码是「这份料进不来」,不是余额问题 —— 当场拒,不落行。
_FORMAT_REJECTS = ("ocr.unsupported_format", "ocr.invalid_pdf", "ocr.too_many_pages")

# 料 → 默认候选动作(F1 只挂两个只读零成本工具;识别入库/工资/汇总建单在 F2/F3)。
_ACTIONS: dict[str, tuple[str, ...]] = {
    GL_LEDGER: (registry.FILE_CONVERT,),
    BANK_STATEMENT: (registry.FILE_CONVERT,),
    SALES_SUMMARY: (registry.FILE_CONVERT,),
    VAT_REPORT: (registry.VAT_REPORT_CHECK,),
    INVOICE: (),
    UNSUPPORTED: (),
}
# 认不出的:两条路都可能,所以恰恰不许自己选一条 —— 摆按钮让人点(§2.3 判据 4)。
_UNKNOWN_ACTIONS = (registry.FILE_CONVERT, registry.VAT_REPORT_CHECK)


@dataclass(frozen=True)
class Detected:
    """一件料的确定性识别结果。auto_runnable 是「传完能不能直接开跑」的唯一判据。"""

    kind: str
    kind_source: str
    kind_reason: str = ""
    page_count: Optional[int] = None
    needs_model: bool = False
    actions: tuple[str, ...] = ()
    quote: dict[str, Any] = field(default_factory=dict)

    @property
    def auto_runnable(self) -> bool:
        """确定性认出来了、只剩一条路、且这条路不烧模型 —— 三条全中才敢不问就跑。
        少一条就出回执卡:猜错的代价(白花钱 + 结果全错)远大于一次点击。"""
        from services.steward.attachments import SOURCE_RULE

        return self.kind_source == SOURCE_RULE and len(self.actions) == 1 and not self.needs_model

    def to_detect(self) -> dict[str, Any]:
        """落库 detect 列(前端契约里 page_count/needs_model 从这里出)。"""
        return {
            "page_count": self.page_count,
            "needs_model": self.needs_model,
            "actions": list(self.actions),
            "quote": self.quote,
        }


def detect(content: bytes, original_name: str, *, user: dict) -> Detected:
    """一件料 → 识别结果。零 I/O 到库(除 billing_quote 的余额读),零模型调用。"""
    from services.ocr import entrypoints
    from services.steward.attachments import SOURCE_RULE, SOURCE_UNKNOWN
    from services.workorder.steps import sort

    ext = Path(original_name or "").suffix.lower()
    if not entrypoints.is_supported_ocr_file(original_name or ""):
        return Detected(
            kind=UNSUPPORTED,
            kind_source=SOURCE_RULE,
            kind_reason=f"unsupported_format:{ext or '(none)'}",
        )

    quote = _quote(content, original_name, user)
    if quote.get("error_code") in _FORMAT_REJECTS:
        return Detected(
            kind=UNSUPPORTED,
            kind_source=SOURCE_RULE,
            kind_reason=str(quote["error_code"]),
            quote=quote,
        )
    pages = quote.get("page_count")

    if ext in sort.IMAGE_EXTS:
        # 图片没有零成本内容信号(不烧钱就读不出内容),但候选动作收敛得很好:它只可能是
        # 一张票。所以不问「这是什么类型」,而是如实标 needs_model —— 要动它就要过模型。
        return _sized(INVOICE, SOURCE_RULE, "image_ext", pages, True, quote)
    if ext in _SHEET_EXTS:
        return _detect_sheet(content, original_name, ext, pages, quote)
    if ext == ".pdf":
        return _detect_pdf(content, original_name, pages, quote)
    # 白名单内的其余格式(docx/txt/tiff…):格式认得但内容判据没有 —— 如实认不出。
    return _sized(
        UNKNOWN, SOURCE_UNKNOWN, f"no_content_signal:{ext.lstrip('.')}", pages, False, quote
    )


def _sized(
    kind: str,
    source: str,
    reason: str,
    pages: Optional[int],
    needs_model: bool,
    quote: dict,
) -> Detected:
    from services.steward.attachments import SOURCE_RULE

    actions = _ACTIONS.get(kind) if source == SOURCE_RULE else _UNKNOWN_ACTIONS
    return Detected(
        kind=kind,
        kind_source=source,
        kind_reason=reason,
        page_count=pages,
        needs_model=needs_model,
        actions=tuple(actions or ()),
        quote=quote,
    )


def _quote(content: bytes, original_name: str, user: dict) -> dict[str, Any]:
    """报价 + 页数 + 格式硬闸(纯本地解 PDF 页数,不烧钱)。

    逐件调是必须的:页数逐件不同,余额状态随之逐件读一次。单批 ≤20 件,而每件的 PDF 页数
    解析本身远重于一次余额 SELECT —— 为省这一次读而在这里另写一份页数逻辑,才是真的漂。
    """
    from services.ocr import entrypoints

    try:
        raw = entrypoints.billing_quote(user, content, original_name or "")
    except Exception:  # noqa: BLE001 — 报价炸了是「报不出价」,不该把整批上传拖垮
        logger.warning("[steward.attach] billing_quote failed for %s", original_name, exc_info=True)
        return {"allowed": None, "error_code": "quote_unavailable"}
    return {
        "allowed": raw.get("allowed"),
        "error_code": raw.get("error_code"),
        "kind": raw.get("kind"),
        "units": raw.get("units"),
        "page_count": raw.get("page_count"),
        "is_exempt": bool(raw.get("is_exempt")),
    }


def _detect_sheet(
    content: bytes, original_name: str, ext: str, pages: Optional[int], quote: dict
) -> Detected:
    """表格件:文件名 + 表头两级判据(表头只扫一次,四家判据共用 —— read_only 也省不掉
    解压 + 读共享字符串表,各扫各的就是四倍时间,而这是上传的同步路径)。"""
    from services.steward.attachments import SOURCE_RULE, SOURCE_UNKNOWN
    from services.vat.vat_file_classifier import _filename_guess
    from services.workorder.steps import sort

    name = Path(original_name or "").name
    head = _xlsx_head(content) if ext in _XLSX_EXTS else []
    if sort._is_gl_name(name) or sort._head_is_gl(head):
        return _sized(GL_LEDGER, SOURCE_RULE, "gl_name_or_head", pages, False, quote)
    if sort._bank_from_filename(name) or sort._head_is_bank(head):
        return _sized(BANK_STATEMENT, SOURCE_RULE, "bank_name_or_head", pages, False, quote)
    if _filename_guess(name) == "vat_report" or _head_has(head, _VAT_HEADER_KW):
        return _sized(VAT_REPORT, SOURCE_RULE, "vat_name_or_head", pages, False, quote)
    if sort._is_sales_summary_name(name) or sort._head_is_sales(head):
        return _sized(SALES_SUMMARY, SOURCE_RULE, "sales_name_or_head", pages, False, quote)
    # 四家都不像 = 这就是一次盲猜。sort.py 对同一情形的纪律是「归堆但标 flagged 交人确认」;
    # 对话口里人就在屏幕前,直接问 —— 问的成本是一秒,猜错的成本是一次不可撤销的白花钱。
    return _sized(
        UNKNOWN, SOURCE_UNKNOWN, f"table_kind_unclear:{ext.lstrip('.')}", pages, False, quote
    )


def _detect_pdf(content: bytes, original_name: str, pages: Optional[int], quote: dict) -> Detected:
    from services.fileconv import model as fc_model, text_layer
    from services.fileconv.classify import classify as classify_text
    from services.steward.attachments import SOURCE_RULE, SOURCE_UNKNOWN
    from services.vat.vat_file_classifier import _filename_guess
    from services.workorder.steps import sort

    name = Path(original_name or "").name
    page_texts = text_layer.extract_pages(content)
    if not text_layer.has_text_layer(page_texts):
        # 扫描件:内容判据在这一层【物理不存在】(不过模型读不出字)。如实标认不出 +
        # needs_model,让人自己点要不要花这份钱 —— 不静默替他决定。
        return _sized(UNKNOWN, SOURCE_UNKNOWN, "pdf_no_text_layer", pages, True, quote)

    doc_type = classify_text("\n".join(page_texts))
    if sort._is_gl_name(name) or doc_type == fc_model.GL_LEDGER:
        return _sized(GL_LEDGER, SOURCE_RULE, "gl_name_or_text", pages, False, quote)
    if sort._bank_from_filename(name) or doc_type == fc_model.BANK_STATEMENT:
        return _sized(BANK_STATEMENT, SOURCE_RULE, "bank_name_or_text", pages, False, quote)
    if _filename_guess(name) == "vat_report" or doc_type == fc_model.VAT_REPORT:
        return _sized(VAT_REPORT, SOURCE_RULE, "vat_name_or_text", pages, False, quote)
    if sort._is_sales_summary_name(name):
        return _sized(SALES_SUMMARY, SOURCE_RULE, "sales_name", pages, False, quote)
    # classify 的 GENERIC_TABLE 是「没认出模板标记词」,不是「认出来是通用表」——
    # 当认出来会让一张发票被当台账去做守恒校验,出一份看着挺像的废表。
    return _sized(UNKNOWN, SOURCE_UNKNOWN, "pdf_kind_unclear", pages, False, quote)


def _xlsx_head(content: bytes) -> list[str]:
    """xlsx 前 15 行逐行拼文本(小写)。判据(_head_is_*)复用 sort 那份,这里只换喂法:
    附件落盘可能是密文,不能像 sort 那样把盘上路径直接交给 openpyxl。读不了 → 空列表。"""
    try:
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
        try:
            return [
                " ".join(str(c) for c in row if c is not None).lower()
                for row in wb.active.iter_rows(min_row=1, max_row=_HEAD_ROWS, values_only=True)
            ]
        finally:
            wb.close()
    except Exception:  # noqa: BLE001 — 读不出表头只是「认不出」,不该拖垮上传
        return []


def _head_has(head: list[str], keywords: tuple[str, ...]) -> bool:
    return any(kw in text for text in head for kw in keywords)
