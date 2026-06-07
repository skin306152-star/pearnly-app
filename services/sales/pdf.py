# -*- coding: utf-8 -*-
"""销项单据合规 PDF 生成(PO-6 · docs/sales-module/docs/13)。

reportlab + 复用 usage_report_pdf_text 的泰/中/英混排字体(฿ 已覆盖)。出泰国合规
ใบกำกับภาษี:卖方(账套主体)与买方双方名称·地址·税号,VAT 7% 分列,连号,总/分公司
(Revenue Code §86/4)。纯渲染叶子:输入已组好的 doc/seller/buyer dict,不连库。
"""

from __future__ import annotations

import hashlib
import io
from decimal import Decimal

from services.sales import pdf_brand
from services.sales import templates
from services.sales.dates import to_thai_date
from services.sales.totals import _d
from services.sales.wht import pdf_label as wht_label
from services.usage.usage_report_pdf_text import _build_paragraph_text, _register_fonts

# 标签三元组 + 语言解析拆到 pdf_labels(SRP · 控行数)。re-export 进本模块命名空间,
# 使 pdf_thermal 仍能经 pdf_mod._DOC_LABEL / _COPY_LABEL 等取用。
from services.sales.pdf_labels import _DOC_LABEL  # noqa: F401 (re-export 供测试/兼容)
from services.sales.pdf_labels import (
    _BUYER_TIN_LABEL,
    _COPY_LABEL,
    _PAYMENT_METHOD_LABEL,
    _doc_label,
    _label_fn,
)

_PAYMENT_DOC_TYPES = ("receipt", "tax_invoice_receipt")
PAGE_SIZES = ("A4", "A5")
# 热敏卷纸窄版(§E1):POS 简易票。走 pdf_thermal 单列布局,不套 A4 表格(列宽溢出)。
THERMAL_WIDTHS = {"thermal_80": 80, "thermal_58": 58}


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):,.2f}"


def _discount_cell(ln: dict) -> str:
    """明细折扣列:无折扣显 '-';有则显金额,百分比输入再括注 (x%)。"""
    disc = Decimal(str(ln.get("discount") or 0))
    if disc == 0:
        return "-"
    pct = ln.get("discount_pct")
    if pct not in (None, "", 0, "0"):
        return f"{_money(disc)} ({_money(pct)}%)"
    return _money(disc)


def _total_rows(doc: dict, lang: str = "th_en") -> list:
    """合计区行 [label, value]。价外(默认)= 净额 + VAT 加总;价内(§C)= 标注含税并把
    VAT 从含税额里反算单列(票面仍单独列税额)。标签随 doc_language 出。"""
    L = _label_fn(lang)
    cur = doc.get("currency") or "THB"
    vat_rate = _money(doc.get("vat_rate"))
    subtotal = _d(doc.get("subtotal"))
    header_disc = _d(doc.get("header_discount_amount"))
    vat = _d(doc.get("vat_amount"))
    wht = _d(doc.get("wht_amount"))
    grand = doc.get("grand_total")
    vat_lbl = L("ภาษีมูลค่าเพิ่ม", "VAT", "增值税")
    disc_lbl = L("ส่วนลดท้ายบิล", "Discount", "整单折扣")

    if doc.get("price_includes_vat"):
        net = subtotal - header_disc - vat
        rows = [[L("รวมเป็นเงิน (รวมภาษี)", "Total (VAT incl.)", "价税合计"), _money(subtotal)]]
        if header_disc != 0:
            rows.append([disc_lbl, "-" + _money(header_disc)])
        rows.append([L("มูลค่าก่อนภาษี", "Net (VAT excl.)", "不含税金额"), _money(net)])
        incl = L("รวมในราคา", "incl.", "含于价内")
        rows.append([f"{vat_lbl} {vat_rate}% ({incl})", _money(vat)])
    else:
        rows = [[L("มูลค่า", "Subtotal", "金额"), _money(subtotal)]]
        if header_disc != 0:
            rows.append([disc_lbl, "-" + _money(header_disc)])
        rows.append([f"{vat_lbl} {vat_rate}%", _money(vat)])
    if wht != 0:
        rows.append([wht_label(doc.get("wht_rate"), lang), "-" + _money(wht)])
    rows.append([f"{L('รวมทั้งสิ้น', 'Grand Total', '合计')} ({cur})", _money(grand)])
    return rows


def _grid_style(grid: str, colors, accent) -> list:
    """明细表格线按模板(§L4):full=全网格 / light=逐行细线 / none=仅表头分隔。"""
    if grid == "none":
        return [("LINEBELOW", (0, 0), (-1, 0), 0.6, accent)]
    if grid == "light":
        return [
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, accent),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.lightgrey),
        ]
    return [("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]


def _buyer_branch_text(b: dict, L) -> str:
    """公司买方的总公司/分店标识(§86/4 第 13 项强制字段)。"""
    if b.get("branch_type") == "branch" and b.get("branch_no"):
        no = b["branch_no"]
        return L(f"สาขาที่ {no}", f"Branch {no}", f"分支 {no}")
    return L("สำนักงานใหญ่", "Head Office", "总公司")


def render_invoice_pdf(
    doc: dict,
    seller: dict,
    buyer: dict,
    *,
    page: str = "A4",
    copy_kind: str = "original",
    copies_layout: str = "separate",
    lang: str = "th_en",
    deterministic: bool = False,
) -> bytes:
    """渲染合规 PDF。page=A4|A5(共用布局)/ thermal_80|thermal_58(窄版单列·§E1);
    copy_kind=original|copy(正/副本角标·§E2)。

    copies_layout(§E2 省纸):separate=单联(默认,按 copy_kind 出一联);two_up=正本+副本印
    同一张 A4/A5,上半正本、下半副本,中间虚线裁切线(打一张撕开,上联给客户、下联自留)。
    two_up 仅 A4/A5 适用,其余纸张回落 separate。

    deterministic=True 用 invariant 画布(固定时间戳/文档 ID),同输入字节级可复现——供开票
    存档哈希(§E3 留底)复算核验,不影响常规下载。
    """
    pg = str(page).lower()
    if pg in THERMAL_WIDTHS:
        from services.sales.pdf_thermal import render_thermal_pdf

        return render_thermal_pdf(
            doc,
            seller,
            buyer,
            copy_kind=copy_kind,
            width_mm=THERMAL_WIDTHS[pg],
            lang=lang,
            deterministic=deterministic,
        )
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, A5
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    pagesize = A5 if str(page).upper() == "A5" else A4
    copy_kind = copy_kind if copy_kind in _COPY_LABEL else "original"
    L = _label_fn(lang)
    base, bold = _register_fonts()

    # 列宽按可用页宽等比缩放(A4 基准 180mm),A4/A5 共用同一套布局不溢出。
    sx = (pagesize[0] - 30 * mm) / (180 * mm)

    def cw(*widths):
        return [w * mm * sx for w in widths]

    seller = seller or {}
    buyer = buyer or {}
    # 模板/品牌(§L4):账套 template_id + brand_color 解析成强调色/表格线(随快照冻结)。
    tpl = templates.resolve(seller.get("template_id"), seller.get("brand_color"))
    accent = colors.HexColor(tpl["accent"])

    def P(text, b=False, align=TA_LEFT, size=9, color=None):
        style = ParagraphStyle(
            "c",
            fontName=(bold if b else base),
            fontSize=size,
            leading=size + 3,
            alignment=align,
            textColor=color or colors.black,
        )
        return Paragraph(
            _build_paragraph_text(str(text if text not in (None, "") else "-"), b), style
        )

    def party(title, p, tin_label):
        cell = [P(title, True, size=10), P(p.get("name"), True)]
        if p.get("address"):
            cell.append(P(p.get("address")))
        cell.append(P(f"{tin_label}: {p.get('tax_id') or '-'}"))
        if p.get("branch"):
            cell.append(P(p.get("branch")))
        if p.get("phone"):
            cell.append(P(f"{L('โทร', 'Tel', '电话')}: {p.get('phone')}"))
        return cell

    def buyer_party(title, b):
        """买方块按类型渲染:税号标签随类型,分店仅公司,匿名显散客(docs/15 §4)。"""
        cell = [P(title, True, size=10), P(b.get("name"), True)]
        if b.get("address"):
            cell.append(P(b.get("address")))
        btype = b.get("type")
        if btype == "anonymous":
            cell.append(P(L("ลูกค้าทั่วไป", "Walk-in customer", "散客")))
            return cell
        label = L(*_BUYER_TIN_LABEL.get(btype, ("เลขประจำตัวผู้เสียภาษี", "TIN", "税号")))
        cell.append(P(f"{label}: {b.get('tax_id') or '-'}"))
        if btype == "company":
            cell.append(P(_buyer_branch_text(b, L)))
        return cell

    def build_copy(ck):
        """组一联的 flowable 列表(供单联渲染或省纸两联各拿一份独立实例)。"""
        story = pdf_brand.logo_flowables(seller, mm, Spacer)
        story += [
            P(_doc_label(doc.get("doc_type"), L), True, TA_CENTER, 15, color=accent),
            P(L(*_COPY_LABEL[ck]), True, TA_CENTER, 9),
            Spacer(1, 4 * mm),
        ]
        meta = Table(
            [
                [
                    P(L("เลขที่", "No.", "编号") + ": " + (doc.get("doc_number") or "-"), True),
                    P(
                        L("วันที่", "Date", "日期")
                        + ": "
                        + to_thai_date(doc.get("issue_date"))
                        + " (พ.ศ.)",
                        align=TA_RIGHT,
                    ),
                ]
            ],
            colWidths=cw(90, 90),
        )
        story.append(meta)
        story.append(Spacer(1, 3 * mm))

        if doc.get("due_date") or doc.get("payment_terms"):
            bits = []
            if doc.get("due_date"):
                bits.append(
                    L("ครบกำหนด", "Due", "到期")
                    + ": "
                    + to_thai_date(doc.get("due_date"))
                    + " (พ.ศ.)"
                )
            if doc.get("payment_terms"):
                bits.append(L("เงื่อนไข", "Terms", "条款") + ": " + str(doc.get("payment_terms")))
            story.append(P("    ".join(bits)))
            story.append(Spacer(1, 2 * mm))

        parties = Table(
            [
                [
                    party(
                        L("ผู้ขาย", "Seller", "卖方"),
                        seller,
                        L("เลขประจำตัวผู้เสียภาษี", "TIN", "税号"),
                    ),
                    buyer_party(L("ผู้ซื้อ", "Buyer", "买方"), buyer),
                ]
            ],
            colWidths=cw(90, 90),
        )
        parties.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(parties)
        story.append(Spacer(1, 4 * mm))

        head = [
            "#",
            L("รายการ", "Description", "项目"),
            L("จำนวน", "Qty", "数量"),
            L("ราคา", "Price", "单价"),
            L("ส่วนลด", "Discount", "折扣"),
            L("จำนวนเงิน", "Amount", "金额"),
        ]
        rows = [[P(h, True, TA_CENTER, color=colors.white) for h in head]]
        for ln in doc.get("lines", []):
            rows.append(
                [
                    P(ln.get("line_no"), align=TA_CENTER),
                    P(ln.get("description")),
                    P(_money(ln.get("qty")), align=TA_RIGHT),
                    P(_money(ln.get("unit_price")), align=TA_RIGHT),
                    P(_discount_cell(ln), align=TA_RIGHT),
                    P(_money(ln.get("line_total")), align=TA_RIGHT),
                ]
            )
        items = Table(rows, colWidths=cw(8, 72, 18, 24, 28, 30), repeatRows=1)
        items.setStyle(
            TableStyle(
                [("BACKGROUND", (0, 0), (-1, 0), accent)]
                + _grid_style(tpl["grid"], colors, accent)
                + [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(items)
        story.append(Spacer(1, 3 * mm))

        total_rows = _total_rows(doc, lang)
        trows = [
            [P(a, align=TA_RIGHT), P(b, b=(i == len(total_rows) - 1), align=TA_RIGHT)]
            for i, (a, b) in enumerate(total_rows)
        ]
        totals = Table(trows, colWidths=cw(150, 30))
        totals.setStyle(
            TableStyle(
                [
                    ("LINEABOVE", (0, -1), (-1, -1), 0.7, accent),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(totals)

        pay = _payment_block(doc, P, cw, Table, TableStyle, colors, mm, Spacer, lang)
        if pay:
            story.extend(pay)
        story.extend(
            pdf_brand.signature_flowables(
                seller, P, cw, Table, TableStyle, colors, mm, Spacer, TA_CENTER
            )
        )
        if seller.get("footer_text"):
            story.append(Spacer(1, 4 * mm))
            story.append(P(seller.get("footer_text"), align=TA_CENTER, size=8, color=colors.grey))
        return story

    buf = io.BytesIO()
    title = doc.get("doc_number") or "document"
    cmk = _canvasmaker(deterministic)
    if str(copies_layout).lower() == "two_up" and str(page).upper() in ("A4", "A5"):
        _render_two_up(
            buf, build_copy("original"), build_copy("copy"), pagesize, title=title, canvasmaker=cmk
        )
        return buf.getvalue()
    pdf = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=title,
    )
    pdf.build(build_copy(copy_kind), **({"canvasmaker": cmk} if cmk else {}))
    return buf.getvalue()


def _canvasmaker(deterministic: bool):
    """deterministic 时返回 invariant 画布工厂(固定时间戳/ID),否则 None(用默认画布)。"""
    if not deterministic:
        return None
    from reportlab.pdfgen import canvas

    def make(*a, **k):
        k["invariant"] = 1
        return canvas.Canvas(*a, **k)

    return make


def archival_sha256(doc: dict, seller: dict, buyer: dict) -> str:
    """开票存档哈希(§E3 留底):规范存档件 = A4 / 正本 / 单联,确定性渲染后取 sha256。

    同一张已开票任何时候复算都得同一哈希,可证留底未被篡改。仅审计增强,渲染失败由调用方
    兜底(不阻断开票)。
    """
    data = render_invoice_pdf(
        doc,
        seller,
        buyer,
        page="A4",
        copy_kind="original",
        copies_layout="separate",
        deterministic=True,
    )
    return hashlib.sha256(data).hexdigest()


def _render_two_up(buf, original_flow, copy_flow, pagesize, *, title, canvasmaker=None) -> None:
    """正本 + 副本印同一张纸(§E2 省纸):上下两半幅 Frame,中间虚线裁切线。

    每联用 KeepInFrame(mode=shrink)收进半幅,无论行数都不会顶到对联;两联内容完全一致
    (同号同额),仅角标 ต้นฉบับ vs สำเนา 不同。打一张撕开:上联给客户、下联自留。
    """
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        FrameBreak,
        KeepInFrame,
        PageTemplate,
    )

    pw, ph = pagesize
    margin = 12 * mm
    gap = 8 * mm
    half = (ph - 2 * margin - gap) / 2
    fw = pw - 2 * margin
    top = Frame(margin, margin + half + gap, fw, half, id="top")
    bot = Frame(margin, margin, fw, half, id="bot")

    def cut_line(canvas, _doc):
        y = margin + half + gap / 2
        canvas.saveState()
        canvas.setDash(3, 3)
        canvas.setStrokeColor(colors.grey)
        canvas.line(margin, y, pw - margin, y)
        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(pw / 2, y + 2, "- - - - - -  cut here  - - - - - -")
        canvas.restoreState()

    pdf = BaseDocTemplate(buf, pagesize=pagesize, title=title)
    pdf.addPageTemplates([PageTemplate(id="two_up", frames=[top, bot], onPage=cut_line)])
    pdf.build(
        [
            KeepInFrame(fw, half, original_flow, mode="shrink"),
            FrameBreak(),
            KeepInFrame(fw, half, copy_flow, mode="shrink"),
        ],
        **({"canvasmaker": canvasmaker} if canvasmaker else {}),
    )


def _payment_block(doc, P, cw, Table, TableStyle, colors, mm, Spacer, lang="th_en"):
    """合并单/收据的收款区(docs/16 §J4):方式/日期/已收;partial 时显未收余额。"""
    if doc.get("doc_type") not in _PAYMENT_DOC_TYPES:
        return None
    status = doc.get("payment_status")
    if not status or status == "unpaid":
        return None
    L = _label_fn(lang)
    pm = doc.get("payment_method")
    method = L(*_PAYMENT_METHOD_LABEL.get(pm, (pm or "-", "", "")))
    rows = [
        [P(L("วิธีชำระ", "Method", "付款方式"), True), P(method)],
        [P(L("วันที่ชำระ", "Date", "付款日期"), True), P(doc.get("payment_date") or "-")],
        [P(L("ชำระแล้ว", "Paid", "已付"), True), P(_money(doc.get("paid_amount")))],
    ]
    if status == "partial":
        outstanding = Decimal(str(doc.get("grand_total") or 0)) - Decimal(
            str(doc.get("paid_amount") or 0)
        )
        rows.append([P(L("คงเหลือ", "Outstanding", "未付余额"), True), P(_money(outstanding))])
    table = Table(rows, colWidths=cw(60, 60))
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return [Spacer(1, 4 * mm), P(L("การชำระเงิน", "Payment", "付款"), True, size=10), table]
