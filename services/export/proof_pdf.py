# -*- coding: utf-8 -*-
"""本月「凭证 PDF」整月打包(Phase C-1 / C-1b):专业封面 + 当月所有已入账票图合成多页 PDF。

诚实边界(铁律):只打包【已入账 posted】真票图(草稿/作废不进);封面诚实写「N 笔·M 笔有图·
K 笔无图」;文案写明「供会计核对·非报税/已申报」不越级。标签固定泰语(给泰国会计看·不做多语切换)。

字体(C-1b 修):prod 无系统泰文字体 → 旧 reportlab 走 Helvetica 致泰文不渲染(只剩数字)。改为
【嵌入 Sarabun】(本片 fonts/·OFL·含泰+拉丁+数字)。封面=reportlab(Table 排版:页眉/汇总卡/明细表/
页脚)·票图合并=PyMuPDF(图→整页·PDF→全页)·票图页加页眉条 + 全页页码(fitz·Sarabun 嵌入)。
下载链接走时效签名 token(verify_token),不暴露登录态。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional

import fitz  # PyMuPDF

from services.export import archive
from services.ocr import pdf_storage
from services.purchase import categories as cat_svc
from services.purchase import docs as docs_svc
from services.purchase import reports as reports_svc

logger = logging.getLogger(__name__)

_MAX_BILLS_PER_DOC = 50
_FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

# 固定泰语标签(给泰国会计·不做多语切换)。
_TITLE_TH = "หลักฐานค่าใช้จ่าย"
_TITLE_EN = "Expense Proof"
_COLS = ["วันที่", "ผู้ขาย", "หมวดหมู่", "จำนวนเงิน", "ภาพ"]
_DISCLAIMER = "จัดทำโดย Pearnly · เพื่อให้นักบัญชีตรวจสอบ · ไม่ใช่เอกสารยื่นภาษี"
_TH_MONTH = [
    "",
    "ม.ค.",
    "ก.พ.",
    "มี.ค.",
    "เม.ย.",
    "พ.ค.",
    "มิ.ย.",
    "ก.ค.",
    "ส.ค.",
    "ก.ย.",
    "ต.ค.",
    "พ.ย.",
    "ธ.ค.",
]

_BRAND = "#0f766e"
_ZEBRA = "#f3f4f6"
_BORDER = "#d1d5db"
_MUTED = "#6b7280"

_FONT_OK = None


def _register_thai_font():
    """注册嵌入 Sarabun(reportlab)→ (base, bold) 字体名。失败回落 Helvetica(英文/数字仍可)。"""
    global _FONT_OK
    if _FONT_OK is None:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            pdfmetrics.registerFont(
                TTFont("Sarabun", os.path.join(_FONT_DIR, "Sarabun-Regular.ttf"))
            )
            pdfmetrics.registerFont(
                TTFont("Sarabun-Bold", os.path.join(_FONT_DIR, "Sarabun-Bold.ttf"))
            )
            _FONT_OK = True
        except Exception as e:  # noqa: BLE001
            logger.warning("[proof_pdf] Sarabun register failed: %s", str(e)[:120])
            _FONT_OK = False
    return ("Sarabun", "Sarabun-Bold") if _FONT_OK else ("Helvetica", "Helvetica-Bold")


def _fitz_fontfile() -> Optional[str]:
    p = os.path.join(_FONT_DIR, "Sarabun-Regular.ttf")
    return p if os.path.exists(p) else None


def _money(v) -> str:
    return f"{Decimal(str(v or 0)):,.2f}"


def grand_total(summ: dict):
    """期间合计(进货 + 费用)· 封面与下载卡共用同一口径(单一定义,不两处各算)。"""
    return (summ.get("goods_total") or 0) + (summ.get("expense_total") or 0)


def _period_label(period: str) -> str:
    """'2026-06' → 'มิ.ย. 2026'(泰文月缩写·公历年)。解析失败 → 原样。"""
    try:
        y, mo = period.split("-")
        return f"{_TH_MONTH[int(mo)]} {y}"
    except (ValueError, IndexError, AttributeError):
        return period or ""


def _all_bill_refs(cur, *, tenant_id, workspace_client_id, doc_id) -> list:
    """一票的【所有】bill 票图 ref(遍历 idx 直到取不到·不止 idx=0)。"""
    refs = []
    for idx in range(_MAX_BILLS_PER_DOC):
        ref = docs_svc.get_bill_image_ref(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            idx=idx,
        )
        if not ref:
            break
        refs.append(ref)
    return refs


def _append_ref(target: "fitz.Document", ref: str) -> bool:
    """把一张票图(图片或 PDF)落盘文件 append 进 target。成功→True。"""
    abs_path = pdf_storage.get_pdf_abs_path(ref)
    if not abs_path or not abs_path.exists():
        return False
    try:
        data = abs_path.read_bytes()
    except OSError:
        return False
    try:
        if data[:5] == b"%PDF-":
            with fitz.open(stream=data, filetype="pdf") as src:
                target.insert_pdf(src)
        else:
            with fitz.open(stream=data) as img:
                pdf_bytes = img.convert_to_pdf()
            with fitz.open(stream=pdf_bytes, filetype="pdf") as src:
                target.insert_pdf(src)
        return True
    except Exception as e:  # noqa: BLE001 — 单张坏图不拖垮整月打包
        logger.warning("[proof_pdf] skip bill ref=%s: %s", ref, str(e)[:120])
        return False


def _stamp_text_band(page, text, *, top: bool, fontfile, size=9):
    """在页顶/页脚画白底窄条 + 文字(票图页眉条 / 页码)。fontfile 缺 → 回落内置(英文/数字)。"""
    r = page.rect
    h = size + 9
    band = fitz.Rect(r.x0, r.y0, r.x1, r.y0 + h) if top else fitz.Rect(r.x0, r.y1 - h, r.x1, r.y1)
    page.draw_rect(band, color=None, fill=(1, 1, 1))
    pt = fitz.Point(band.x0 + 8, band.y0 + size + 3)  # 基线点(insert_text 总绘·无溢出丢字)
    kw = {"fontfile": fontfile, "fontname": "sarabun"} if fontfile else {}
    try:
        page.insert_text(pt, text, fontsize=size, color=(0.1, 0.12, 0.15), **kw)
    except Exception:  # noqa: BLE001 — 字体/形状异常不拖垮整包
        page.insert_text(pt, text, fontsize=size, color=(0.1, 0.12, 0.15))


def _cover_pdf(summ, rows, *, m, k, period, subject) -> bytes:
    """封面:页眉(Pearnly+标题+套账+期间)+ 汇总卡 + 明细表(斑马纹/边框)+ 页脚声明。reportlab+Sarabun。"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    base, bold = _register_thai_font()
    brand = ParagraphStyle(
        "brand",
        fontName=bold,
        fontSize=20,
        leading=26,
        spaceAfter=4,
        textColor=colors.HexColor(_BRAND),
    )
    h1 = ParagraphStyle("h1", fontName=bold, fontSize=15, leading=20, spaceAfter=2)
    sub = ParagraphStyle("sub", fontName=base, fontSize=10, textColor=colors.HexColor(_MUTED))
    cell = ParagraphStyle("cell", fontName=base, fontSize=9, leading=12)
    cellr = ParagraphStyle("cellr", parent=cell, alignment=2)  # 金额右对齐
    cellc = ParagraphStyle("cellc", parent=cell, alignment=1)
    hd = ParagraphStyle("hd", fontName=bold, fontSize=9, leading=12, textColor=colors.white)
    klbl = ParagraphStyle("klbl", fontName=base, fontSize=8, textColor=colors.HexColor(_MUTED))
    kval = ParagraphStyle("kval", fontName=bold, fontSize=13, leading=16)
    foot = ParagraphStyle("foot", fontName=base, fontSize=8, textColor=colors.HexColor(_MUTED))

    total = grand_total(summ)
    story = [
        Paragraph("Pearnly", brand),
        Paragraph(f"{_TITLE_TH} · {_TITLE_EN}", h1),
        Paragraph(f"{subject} · {_period_label(period)}", sub),
        Spacer(1, 5 * mm),
    ]

    def _kpi(label, value):
        return [Paragraph(label, klbl), Paragraph(value, kval)]

    card = Table(
        [
            [
                _kpi("รายการ", str(len(rows))),
                _kpi("มีภาพ", str(m)),
                _kpi("ไม่มีภาพ", str(k)),
                _kpi("ยอดรวม", f"฿{_money(total)}"),
                _kpi("VAT ที่ขอคืนได้", f"฿{_money(summ.get('vat_claimable'))}"),
            ]
        ],
        colWidths=[95, 70, 75, 140, 145],
    )
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(_BRAND)),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#a7f3d0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story += [card, Spacer(1, 6 * mm)]

    data = [[Paragraph(c, hd) for c in _COLS]]
    for r in rows:
        data.append(
            [
                Paragraph(r["date"], cell),
                Paragraph(r["seller"], cell),
                Paragraph(r["category"], cell),
                Paragraph(f"฿{_money(r['amount'])}", cellr),
                Paragraph(
                    "มี" if r["has_img"] else "—", cellc
                ),  # Sarabun 无 ✓ glyph → 用泰文「มี」
            ]
        )
    table = Table(data, colWidths=[70, 160, 145, 90, 45], repeatRows=1)
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_BRAND)),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(_BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(_ZEBRA)))
    table.setStyle(TableStyle(ts))
    story += [table, Spacer(1, 6 * mm)]
    story += [
        Paragraph(_DISCLAIMER, foot),
        Paragraph(f"สร้างเมื่อ {datetime.now().strftime('%Y-%m-%d %H:%M')}", foot),
    ]

    buf = io.BytesIO()
    SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=16 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        bottomMargin=16 * mm,
    ).build(story)
    return buf.getvalue()


def build_monthly_proof_pdf(
    cur, *, tenant_id, workspace_client_id, date_from, date_to, lang="th", period="", summ=None
) -> bytes:
    """整月已入账票 → 多页 PDF:封面(汇总卡+明细表)+ 每票所有票图页(页眉条标注对应笔)+ 全页页码。

    只含 status='posted';租户+套账隔离;无图的笔只在明细表标「—」不占图页(诚实)。lang 仅影响数据
    取值上下文,标签固定泰语。summ 可由调用方传入复用(避免同一流程重复查汇总)。"""
    if summ is None:
        summ = reports_svc.summary(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            date_from=date_from,
            date_to=date_to,
        )
    doc_ids = archive._posted_doc_ids(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_from=date_from,
        date_to=date_to,
    )
    cat_map = {}
    for p in cat_svc.get_tree(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id):
        cat_map[str(p.get("id"))] = p.get("name") or ""
        for c in p.get("children") or []:
            cat_map[str(c.get("id"))] = c.get("name") or ""

    fontfile = _fitz_fontfile()
    images = fitz.open()
    rows, m = [], 0
    for i, did in enumerate(doc_ids):
        detail = docs_svc.get_doc(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=did
        )
        if not detail:
            continue
        doc = detail.get("doc") or {}
        sup = detail.get("supplier") or {}
        info = {
            "seq": i + 1,
            "date": str(doc.get("doc_date") or ""),
            "seller": (sup.get("name") or "—").strip() or "—",
            "category": cat_map.get(str(doc.get("category_id")), "") or "—",
            "amount": doc.get("grand_total"),
        }
        refs = _all_bill_refs(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=did
        )
        start = images.page_count
        appended = sum(1 for ref in refs if _append_ref(images, ref))
        info["has_img"] = appended > 0
        if appended:
            m += 1
            strip = (
                f"#{info['seq']} · {info['date']} · {info['seller']} · ฿{_money(info['amount'])}"
            )
            _stamp_text_band(images[start], strip, top=True, fontfile=fontfile)
        rows.append(info)

    cover = _cover_pdf(
        summ,
        rows,
        m=m,
        k=len(rows) - m,
        period=period,
        subject=_subject(cur, tenant_id, workspace_client_id),
    )
    out = fitz.open(stream=cover, filetype="pdf")
    if images.page_count:
        out.insert_pdf(images)
    total_pages = out.page_count
    for idx in range(total_pages):
        _stamp_text_band(
            out[idx], f"Pearnly · {idx + 1} / {total_pages}", top=False, fontfile=fontfile
        )
    data = out.tobytes()
    out.close()
    images.close()
    return data


def _subject(cur, tenant_id, workspace_client_id) -> str:
    try:
        return archive._subject_name(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
    except Exception:  # noqa: BLE001
        return ""


# ── 时效签名 token(下载链接防他人访问·不暴露登录态)────────────────────────────
def _secret() -> bytes:
    return (
        os.environ.get("JWT_SECRET") or os.environ.get("LINE_CHANNEL_SECRET") or "pearnly-proof-dev"
    ).encode("utf-8")


def _b64(b: bytes) -> bytes:
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def sign_token(*, tenant_id: str, workspace_client_id, period: str, rel: str, ttl_s=86400) -> str:
    """签名下载 token(payload 含 tenant/ws/period/落盘 rel/exp)。默认 24h 有效。"""
    body = {
        "t": str(tenant_id),
        "w": str(workspace_client_id),
        "p": period,
        "r": rel,
        "exp": int(time.time()) + int(ttl_s),
    }
    raw = _b64(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    sig = _b64(hmac.new(_secret(), raw, hashlib.sha256).digest())
    return (raw + b"." + sig).decode("ascii")


def verify_token(token: str) -> Optional[dict]:
    """校验下载 token:签名不符/过期/格式坏 → None;有效 → payload dict。常量时间比对。"""
    try:
        raw, sig = (token or "").encode("ascii").split(b".", 1)
    except (ValueError, AttributeError):
        return None
    expected = _b64(hmac.new(_secret(), raw, hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        body = json.loads(base64.urlsafe_b64decode(raw + b"=" * (-len(raw) % 4)))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(body.get("exp", 0)) < int(time.time()):
        return None
    return body
