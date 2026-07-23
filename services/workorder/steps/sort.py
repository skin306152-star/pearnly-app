# -*- coding: utf-8 -*-
"""sort 步:给 pending 的料定堆(任务包 §5 步 2)。

零成本信号当场定堆:表格(xlsx/csv)默认销项 POS 汇总,文件名像银行(复用 bank_recon
的签名表——文件名是人读的高精度信号,正文里满屏对手行名不可靠)或表头像流水
(ถอน/ฝาก/ยอดคงเหลือ 列)则归银行单;不支持的格式 = 无税务要素,non_tax 排除并留原因。
PDF 除 GL/银行外再认一类销售汇总表(文件名或首页文字层报表抬头,票据名反证优先)——它交
OCR 既烧钱又产不出 sales_read。图片和认不出的 PDF 在这一步不动(kind 留 unknown),等
classify 过 OCR 拿到票面字段后调 bin_ocr_fields 归堆——sort 自己不起 OCR,重活全在 classify。

bin_ocr_fields 是给 classify 用的纯函数:税号锚点判方向,规则与
services/erp/express_push/direction.py 同口径(自家==买方→进项;脏税号归空绝不误路由),
但只借规则不 import 推送模块(任务包 §5 明令,推送域不进工单依赖树)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from services.fileconv import text_layer
from services.purchase.field_clean import clean_tax_id
from services.recon.bank_recon_utils import _BANK_SIGNATURES, _bank_from_filename
from services.workorder import decisions, kinds, storage
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps.reconcile_gates import unreadable_money_fields

# classify 会过 OCR 的图片扩展名(单一事实源:sort 定堆时判「留给 classify」用,api 的
# 逐件进度投影也据此认「哪些件要过 OCR」——同一份定义,不各写一套)。
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".bmp"}
_SHEET_EXTS = {".xlsx", ".xlsm", ".xls", ".csv"}
# 流水表头列名:命中 ≥2 个不同关键词才算银行(POS 汇总也有「วันที่」,单词不作数)。
_BANK_HEADER_KW = ("ถอน", "ฝาก", "ยอดคงเหลือ", "withdrawal", "deposit", "balance")

# GL 台账关键词(T4a):泰文报表名子串命中即认;ASCII "GL" 按词边界防 GLOBAL 之类误粘。
# GL 判据先于银行判据——银行科目的 GL(文件名带行名)仍是 GL 佐证件,不是流水。
_GL_NAME_KW = ("สมุดแยกประเภท", "แยกประเภท")
_GL_ASCII_RE = re.compile(r"(?<![a-z])gl(?![a-z])")

# 销售汇总表判据(PDF 分流)。PDF 现状是「非 GL 非银行 → 交 classify 过 OCR」,汇总表走这条
# 既烧 OCR 钱又永远产不出 sales_read(OCR 出的是票面字段,不是表格)——月度销项因此归零。
# 判据保守:票据名反证优先,宁可漏归(走原 OCR 路)也绝不把发票误归成汇总表。
_SALES_SUMMARY_NAME_KW = (
    "สรุปยอดขาย",
    "รายงานการขาย",
    "รายงานขาย",
    "ยอดขาย",
    "sales summary",
    "sales report",
    "daily sales",
    "销售汇总",
    "销售报表",
)
# 正文判据只认报表抬头这类强标记,不认裸「ยอดขาย」——它也可能是一张发票里的小计行文字。
_SALES_SUMMARY_TEXT_KW = (
    "สรุปยอดขาย",
    "รายงานการขาย",
    "รายงานขาย",
    "sales summary",
    "sales report",
)
# 票据名/票面反证词:命中即不认汇总表(单张税票/收据永远不是汇总表)。
_INVOICE_KW = (
    "ใบกำกับภาษี",
    "ใบเสร็จ",
    "ใบแจ้งหนี้",
    "ใบส่งของ",
    "tax invoice",
    "invoice",
    "receipt",
)
_PDF_TEXT_SCAN_PAGES = 1  # 报表抬头只会在首页;多扫一页只多花时间不多认一张表

# EDC 日终结算票标记(SA-2a):只有商户自己机器的日切汇总打印 SETTLEMENT 独立词——单笔
# SALE 支付条(BATCH/TRACE/APPR 脚注)和银行 Statement 页都没有,词边界防 Statement 误粘。
_EDC_SETTLEMENT_RE = re.compile(r"(?<![a-z])settlement(?![a-z])")

# 对账单标题白名单(SA3R-a):整月对账单页印的报表抬头,真付款截图/转账凭证不印。用于把被
# OCR 误判 payment_evidence 的对账单续页救回 bank_statement(闸 pearnly_ai_stmt_regroup)。
# 词表从金标 KBANK 18 页与真付款样本对撞得出(见 SA3R 侦察单/方案):真 K PLUS 转账截图的
# notes 是动作词(รายงานการโอนเงิน/Thai QR Payment/BATCH… 脚注),不含这些报表抬头;边界模糊页
# (如 รายงานการโอนเงิน)有意不进白名单=不救回,交第 2 层自报总数闸兜(方案 §二)。
_STMT_TITLE_KEYWORDS = (
    "รายการเดินบัญชี",  # 存折/流水标题(passbook/statement listing)
    "ความเคลื่อนไหวทางบัญชี",  # 账户动态报表(account movement)
    "เคลื่อนไหวบัญชีเงินฝาก",  # 储蓄账户动态(deposit-account movement)
    "bank statement",
    "statement of account",  # 英文对账单标题(通用,别家行英文页兜底)
)
# 标题只落在报表抬头相关字段,不扫全票面(与 _mentions_bank 的宽域故意分开:标题要窄)。
_STMT_TITLE_FIELDS = ("notes", "document_type", "category")

# 正文判银行用的词表:复用银行签名表(泰/英各家行名)+ 通用「ธนาคาร(银行)」。
# 文件名判银行走 _bank_from_filename(ASCII 词边界);IMG_xxxx 无名照片走这里的内容判。
_BANK_TEXT_KEYWORDS = {kw.lower() for kws in _BANK_SIGNATURES.values() for kw in kws} | {"ธนาคาร"}
_BANK_TEXT_FIELDS = ("seller_name", "buyer_name", "seller_addr", "buyer_addr", "notes", "category")

# 归一化公司名时剥掉的泰/英法人前后缀,只留可比对的字号主体。
_COMPANY_AFFIXES = (
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญ",
    "ห้างหุ้นส่วน",
    "บริษัท",
    "จำกัด",
    "มหาชน",
    "หจก.",
    "หจก",
    "บมจ.",
    "บมจ",
    "สาขา",
    "สำนักงานใหญ่",
    "company limited",
    "co.,ltd.",
    "co., ltd.",
    "co.,ltd",
    "co. ltd",
    "co ltd",
    "co.ltd",
    "public",
    "ltd.",
    "ltd",
    "part.",
)


def _scan_xlsx_head(path: Path) -> list[str]:
    """xlsx 前 15 行逐行拼文本(小写),给表头判据用。读不了 → 空列表。"""
    try:
        import openpyxl

        # read_only 模式持有文件句柄,必须显式 close(Windows 下不关会锁住语料文件)。
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        try:
            return [
                " ".join(str(c) for c in row if c is not None).lower()
                for row in wb.active.iter_rows(min_row=1, max_row=15, values_only=True)
            ]
        finally:
            wb.close()
    except Exception:
        return []


def _xlsx_header_is_bank(path: Path) -> bool:
    """扫前 15 行找流水列名(照 vat_file_classifier._excel_quick_meta 的轻量先例)。读不了 → False。"""
    hits = set()
    for text in _scan_xlsx_head(path):
        hits.update(kw for kw in _BANK_HEADER_KW if kw in text)
    return len(hits) >= 2


def _xlsx_header_is_gl(path: Path) -> bool:
    """扫前 15 行找 GL 报表名(สมุดแยกประเภท 标题行)。读不了 → False。"""
    return any(kw in text for text in _scan_xlsx_head(path) for kw in _GL_NAME_KW)


# 销项汇总表的表头正面判据(与 _GL_NAME_KW / _BANK_HEADER_KW 对称)。此前没有这一条:表格类
# 文件在 GL、银行都不像时一律兜底归销项汇总(B-1)。兜底本身多半对(会计上传的就是它),但
# 「猜的」和「认出来的」不该长得一样——一份 GL 或流水的表头没被认出来时走的是同一条兜底路,
# 它的数字直接进 R2 销售额且不留任何痕迹。词表只收强判据(带「销售」语义的词),不收 amount/
# 金额这类任何表都有的通用列名,免得把认不出的表也认成销项。
_SALES_HEADER_KW = ("ยอดขาย", "ภาษีขาย", "รายงานการขาย", "sales", "销售", "销项")


def _xlsx_header_is_sales(path: Path) -> bool:
    """扫前 15 行找销售语义的列名/标题。读不了 → False(读不了由 classify 的解析闸点名)。"""
    return any(kw in text for text in _scan_xlsx_head(path) for kw in _SALES_HEADER_KW)


def _is_gl_name(name: str) -> bool:
    """文件名像 GL 台账:泰文报表名子串,或 ASCII 'GL' 独立词(大小写不论)。"""
    return any(kw in name for kw in _GL_NAME_KW) or bool(_GL_ASCII_RE.search(name.lower()))


def _is_sales_summary_name(name: str) -> bool:
    """文件名像销售汇总表。票据名反证优先——「ใบกำกับภาษี ยอดขาย.pdf」是票不是表。"""
    low = (name or "").lower()
    if any(kw in low for kw in _INVOICE_KW):
        return False
    return any(kw in low for kw in _SALES_SUMMARY_NAME_KW)


def _pdf_head_is_sales_summary(file_ref: str) -> bool:
    """PDF 首页文字层里有报表抬头 → 销售汇总表。扫描件/读不了/依赖缺 → False,走原 OCR 路。"""
    try:
        pages = text_layer.extract_pages(storage.read_bytes(file_ref))
    except Exception:  # noqa: BLE001 · 读盘/解密/解析任一环节炸都只是「认不出」,不该拖垮定堆
        return False
    head = " ".join(pages[:_PDF_TEXT_SCAN_PAGES]).lower() if pages else ""
    if not head.strip() or any(kw in head for kw in _INVOICE_KW):
        return False
    return any(kw in head for kw in _SALES_SUMMARY_TEXT_KW)


def _bin_by_file(file_ref: str) -> Optional[tuple[str, str, Optional[str]]]:
    """文件名/表头可判的堆 → (kind, status, flag_reason);要过 OCR 才知道的 → None。"""
    path = Path(file_ref or "")
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return None
    if ext in _SHEET_EXTS:
        if _is_gl_name(path.name):
            return (kinds.GL_LEDGER, "pending", None)
        if ext in (".xlsx", ".xlsm") and _xlsx_header_is_gl(path):
            return (kinds.GL_LEDGER, "pending", None)
        if _bank_from_filename(path.name):
            return (kinds.BANK_STATEMENT, "pending", None)
        if ext in (".xlsx", ".xlsm") and _xlsx_header_is_bank(path):
            return (kinds.BANK_STATEMENT, "pending", None)
        # B-1:认出来是销项汇总 → 照常归堆。三家都不像 → 这就是一次盲猜,不许无痕:归销项
        # 汇总(下游口径不变)但标 flagged 交人确认一次。xlsx 之外(csv/xls)扫不了表头,只能
        # 维持原兜底 —— 如实记债,不假装也判过。
        if _is_sales_summary_name(path.name):
            return (kinds.SALES_SUMMARY, "pending", None)
        if ext in (".xlsx", ".xlsm"):
            if _xlsx_header_is_sales(path):
                return (kinds.SALES_SUMMARY, "pending", None)
            return (kinds.SALES_SUMMARY, "flagged", f"table_kind_unclear:{ext.lstrip('.')}")
        return (kinds.SALES_SUMMARY, "pending", None)
    if ext == ".pdf":
        if _is_gl_name(path.name):
            return (kinds.GL_LEDGER, "pending", None)
        if _bank_from_filename(path.name):
            return (kinds.BANK_STATEMENT, "pending", None)
        if _is_sales_summary_name(path.name) or _pdf_head_is_sales_summary(file_ref):
            return (kinds.SALES_SUMMARY, "pending", None)
        return None
    return (kinds.NON_TAX, "excluded", f"unsupported_format:{ext or '(none)'}")


def run(ctx: StepContext) -> StepResult:
    """把还没定堆的 pending 料按规则归堆;归不了的留给 classify(计入 pending_ocr)。"""
    items = ctx.store.list_items(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id, status="pending"
    )
    bins: dict[str, int] = {}
    pending_ocr = 0
    for item in items:
        if item["kind"] != kinds.UNKNOWN:
            continue
        decided = _bin_by_file(item["file_ref"])
        if decided is None:
            pending_ocr += 1
            continue
        kind, status, reason = decided
        ctx.store.update_item(
            ctx.cur,
            tenant_id=ctx.tenant_id,
            item_id=item["id"],
            kind=kind,
            status=status,
            flag_reason=reason,
        )
        bins[kind] = bins.get(kind, 0) + 1
    return StepResult.ok(bins=bins, pending_ocr=pending_ocr)


def bin_ocr_fields(
    fields: dict, *, own_tax_id, own_name=None, own_names=None, stmt_regroup=False
) -> tuple[str, Optional[str]]:
    """图片过 OCR 后归堆 → (kind, flag_reason)。classify 步(T4)拿到票面字段后调。

    支付/订单截图与「无 VAT 且两头税号都没有」的票据 = 无税务要素 → non_tax 留原因。
    EDC 日终结算票(SETTLEMENT 独立词 + 无税票结构 + 毛额可解 + 商户名命中本账套名集)
    → edc_settlement,佐证件不进税额(SA-2a,判据详见 _is_edc_settlement)。
    银行流水页(正文出现行名且无 VAT 税票结构)→ bank_statement,不进方向判据、不进数学闸。
    有税务要素的按税号锚点判向:自家==买方 → purchase_invoice;自家==卖方 → 自动归本方销项
    堆 sales_doc(status=flagged 留人工过目 · MC1-c.1,替代此前判死为 unknown 的 sales_direction_
    unhandled)。税号锚对不上任何一方(买方税号 OCR 读花/缺失)时退到公司名称锚点;名称也对不上
    才留 ambiguous。

    名称锚有两条入口(precedence 不变,税号仍第一优先):
      own_name(单名,向后兼容)——法定名单锚,子串 ≥4 现状,不做税号/名称冲突检测。
      own_names(名集,别名闸 pearnly_ai_m1 开时走)——[(name, mode)] 序列(法定名 legal +
        active human_confirmed 别名 exact/substring),遍历买方优先命中;并做冲突检测
        (税号锚与名集锚指向不同客户 → ambiguous 不猜,方案 §4.6 闸4)。
    """
    f = fields or {}
    dtype = (f.get("document_type") or "").strip().lower() or "unknown"
    seller = clean_tax_id(f.get("seller_tax") or f.get("seller_tax_id"))
    buyer = clean_tax_id(f.get("buyer_tax") or f.get("buyer_tax_id"))
    has_vat = _has_vat(f)
    own = clean_tax_id(own_tax_id)

    # own_names(名集)是别名闸开时的新路;缺省 own_name 是闸关的现状路,行为逐字节不变。
    if own_names is not None:
        entries = list(own_names)
        conflict = _NameConflict(own=own, seller=seller, buyer=buyer)
    else:
        entries = [(own_name, "legal")] if own_name else []
        conflict = None

    # EDC 日终结算票(SA-2a):先于支付凭证排除判——结算票的 OCR document_type 散落在
    # payment_evidence/other/receipt 三种,判据靠票面特征不靠 dtype。认不出的原样走后面
    # 的现状路(宁窄勿宽,错归堆=错进销项聚合)。
    if _is_edc_settlement(f, seller=seller, buyer=buyer, has_vat=has_vat, entries=entries):
        return (kinds.EDC_SETTLEMENT, None)

    # 对账单续页救回(SA3R-a · 闸 pearnly_ai_stmt_regroup,由 classify 传入 stmt_regroup)。整月
    # 对账单的续页(满纸转账行、无账号表头)OCR 常把 document_type 判成 payment_evidence,会在
    # 下面的短路支被当「无税务要素」踢掉——尸检实锤金标 KBANK 18 页里 6 页这样丢失。收窄双条件
    # 救回:银行名或 OCR 粗分类明说 bank,且命中对账单标题白名单 → bank_statement。续页页眉
    # 常只剩分行名,不能要求银行名永远在场。
    # 真付款截图 notes 是动作词不含报表抬头,双条件保它仍归 non_tax(守门测试锁零误吸)。排在
    # payment_evidence 短路之前才拦得住;闸关(默认 stmt_regroup=False)不进此支,逐字节维持现状。
    if (
        stmt_regroup
        and not has_vat
        and (_mentions_bank(f) or _category_is_bank(f))
        and _is_statement_title(f)
    ):
        return (kinds.BANK_STATEMENT, None)

    # 支付/订单截图:确定无税务要素,先排除,免得被下面的银行/方向判据接管。
    if dtype in ("payment_evidence", "order_evidence"):
        return (kinds.NON_TAX, f"no_tax_elements:{dtype}")

    # B-2:VAT 印了但读不出 → 下面两个出口都不能走。它们的前提是「这张票没有 VAT」,而这里
    # 的真相是「有没有 VAT 我没看清」——按无 VAT 处理会把税票判成流水页或无税务要素的
    # non_tax,后者还会被 classify 直接 excluded(B-3:零人复核的终态,进项税就这么没了)。
    # 交人定向:无裁决 R1 停机点名,裁成进项后票面税额再过 A-5 那道读花闸。
    if _vat_unreadable(f):
        return (kinds.UNKNOWN, f"{decisions.VAT_UNREADABLE}:{dtype}")

    # 银行流水页:排在 non_tax 兜底之前——流水页两头税号常缺,否则会被当「无税务要素」排除。
    # 只在无 VAT 税票结构时认,防真税票里印付款银行(带 VAT)被误判成流水。
    if not has_vat and _mentions_bank(f):
        return (kinds.BANK_STATEMENT, None)

    if not has_vat and not seller and not buyer:
        return (kinds.NON_TAX, f"no_tax_elements:{dtype}")

    match_seller = bool(seller) and seller == own
    match_buyer = bool(buyer) and buyer == own
    if match_buyer and not match_seller:
        return (kinds.PURCHASE_INVOICE, None)
    if match_seller and not match_buyer:
        return (decisions.SALES_DOC, decisions.SALES_DOC_REVIEW)

    by_name = _direction_by_name(f, entries, conflict=conflict)
    if by_name:
        return by_name
    return (kinds.UNKNOWN, decisions.DIRECTION_AMBIGUOUS)


def _is_edc_settlement(f: dict, *, seller: str, buyer: str, has_vat: bool, entries) -> bool:
    """EDC 日终结算票(merchant copy)四联判据,全中才归堆(SA-2a · 宁窄勿宽):

    ① 无税票结构:无 VAT 且两头无干净税号——结算票不带税务要素,带了就不是裸结算票;
    ② SETTLEMENT 独立词(notes/invoice_number):日切汇总才打印;单笔 SALE 支付条只有
       BATCH/TRACE/APPR 脚注(它是某张销售小票的收款凭证,归堆会与税票/结算双计),
       银行 Statement 页词形不同,词边界挡误粘;
    ③ 毛额可解(>0):解不出毛额的结算票对销项聚合无用,留在现状排除队列;
    ④ 商户名命中本账套名集:结算票只在自家收单机打印,名锚防串客户料。按 substring
       门槛(≥6)比对——票面商户名带分店/城市后缀(如 SISTER MAKEUP SAPHAN SUNG, BKK),
       exact 别名对不上;①②③ 已把面收窄,此处放宽不回宽整体。
    """
    if has_vat or seller or buyer:
        return False
    blob = " ".join(str(f.get(k) or "") for k in ("notes", "invoice_number")).lower()
    if not _EDC_SETTLEMENT_RE.search(blob):
        return False
    if not _edc_gross_usable(f):
        return False
    merchant = f.get("seller_name")
    return any(_company_name_match(name, merchant, "substring") for name, _mode in entries)


def _edc_gross_usable(f: dict) -> bool:
    """结算毛额可解:total_amount(缺则 subtotal)能转正数。与 classify._edc_fields 的
    取值序一致——判「可归堆」与「归堆后快照什么」必须看同一个数。"""
    try:
        raw = str(f.get("total_amount") or f.get("subtotal") or "").replace(",", "").strip()
        return bool(raw) and Decimal(raw) > 0
    except InvalidOperation:
        return False


def _mentions_bank(fields: dict) -> bool:
    """票面文字里出现银行名(泰/英行名或通用「ธนาคาร」)。ASCII 短码(ttb/scb…)按词边界
    匹配防误粘进别的词;泰文行名直接子串命中。"""
    blob = " ".join(str(fields.get(k) or "") for k in _BANK_TEXT_FIELDS).lower()
    if not blob.strip():
        return False
    for kw in _BANK_TEXT_KEYWORDS:
        if kw.isascii():
            if re.search(rf"(?<![a-z]){re.escape(kw)}(?![a-z])", blob):
                return True
        elif kw in blob:
            return True
    return False


def _is_statement_title(fields: dict) -> bool:
    """报表抬头字段里出现对账单标题白名单词(SA3R-a)。只扫 _STMT_TITLE_FIELDS(notes/
    document_type/category),不扫全票面——标题判据要窄,配合 _mentions_bank 双锁防误吸真付款截图。"""
    blob = " ".join(str(fields.get(k) or "") for k in _STMT_TITLE_FIELDS).lower()
    return any(kw.lower() in blob for kw in _STMT_TITLE_KEYWORDS)


def _category_is_bank(fields: dict) -> bool:
    """OCR 粗分类明说 bank；单独不作准，必须与对账单标题双锁。"""
    return str(fields.get("category") or "").strip().lower() == "bank"


@dataclass(frozen=True)
class _NameConflict:
    """名集锚的税号冲突判据(方案 §4.6 闸4)。own/seller/buyer 都是已 clean_tax_id 的值。

    某一侧名集命中,但同侧印着一个 clean 且非自家的税号 → 税号说「这侧不是自家」、名称说
    「是自家」,两锚打架 → 不猜,返回 ambiguous+冲突旗。空/脏税号无意见,不触发冲突。
    """

    own: str
    seller: str
    buyer: str

    def contradicts(self, side: str) -> bool:
        tax = self.seller if side == "seller" else self.buyer
        return bool(tax) and tax != self.own


_AMBIGUOUS_TAXID_CONFLICT = f"{decisions.DIRECTION_AMBIGUOUS}:name_taxid_conflict"


def _direction_by_name(
    fields: dict, entries, *, conflict: Optional["_NameConflict"] = None
) -> Optional[tuple[str, Optional[str]]]:
    """税号锚失灵时的名称兜底:名集任一命中买方名 → 进项;任一命中卖方名 → 本方销项堆
    sales_doc(MC1-c.1);都不命中 → None(交回 ambiguous)。买方优先:进项是工单主线,先认
    买方少漏票。

    entries = [(name, mode)] 序列(法定名 legal / 别名 exact|substring)。conflict 非空且
    命中侧的税号与自家矛盾 → ambiguous+冲突旗(闸关的单名路 conflict=None,不做此检测,现状不变)。
    """
    if not entries:
        return None
    if _name_set_hits(entries, fields.get("buyer_name")):
        if conflict is not None and conflict.contradicts("buyer"):
            return (kinds.UNKNOWN, _AMBIGUOUS_TAXID_CONFLICT)
        return (kinds.PURCHASE_INVOICE, None)
    if _name_set_hits(entries, fields.get("seller_name")):
        if conflict is not None and conflict.contradicts("seller"):
            return (kinds.UNKNOWN, _AMBIGUOUS_TAXID_CONFLICT)
        return (decisions.SALES_DOC, decisions.SALES_DOC_REVIEW)
    return None


def _name_set_hits(entries, candidate) -> bool:
    """名集中任一 (name, mode) 命中候选名即真(遍历顺序不影响买方优先——买方整集先过)。"""
    return any(_company_name_match(name, candidate, mode) for name, mode in entries)


def _normalize_company_name(name) -> str:
    """公司名归一化:小写、剥法人前后缀(บริษัท/จำกัด/co.,ltd…)、去空格标点,留字号主体。"""
    s = str(name or "").lower().strip()
    if not s:
        return ""
    for affix in _COMPANY_AFFIXES:
        s = s.replace(affix, " ")
    # 去掉标点/括号/空白,只留字母数字与泰文字符(折叠成可比对的连续主体)。
    return re.sub(r"[^0-9a-z฀-๿]+", "", s)


def _company_name_match(a, b, mode: str = "legal") -> bool:
    """两公司名归一化后判同,匹配严格度按 mode(默认 legal = 现状,别名接线传 exact/substring):
    legal     相等或一方是另一方子串(短边 ≥4)——法定名现状,容差覆盖分店后缀 OCR 差异。
    exact     仅归一等值——别名默认,最防污染(完全解 Ocha「Sister Makeup」精确命中)。
    substring 相等或子串(短边 ≥6)——别名显式放宽时用,门槛更高防泛词误扫。
    """
    na, nb = _normalize_company_name(a), _normalize_company_name(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if mode == "exact":
        return False
    short, long = (na, nb) if len(na) <= len(nb) else (nb, na)
    min_len = 6 if mode == "substring" else 4
    return len(short) >= min_len and short in long


def _has_vat(fields: dict) -> bool:
    try:
        return Decimal(str(fields.get("vat") or "0").replace(",", "").strip()) > 0
    except InvalidOperation:
        return False


def _vat_unreadable(fields: dict) -> bool:
    """票面 VAT 印了但读不出 —— 与「这张票本来就没 VAT」不是一回事(B-2)。

    _has_vat 对两者一律返 False,于是读花一个字符(7O.00)的税票会走「无 VAT」的两个静默
    出口:判成银行流水页,或判成无税务要素的 non_tax 被自动排除(B-3:零人复核的终态)。
    判据复用 reconcile_gates 那份单一事实源(含 NaN/Infinity 守卫),不另写一套。
    """
    return bool(unreadable_money_fields({"vat": fields.get("vat")}))
