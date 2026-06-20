# -*- coding: utf-8 -*-
"""本月「凭证 PDF」整月打包(Phase C-1):封面汇总 + 当月所有已入账票图合成一个多页 PDF。

诚实边界(铁律):只打包【已入账 posted】真票图(草稿/作废不进);封面诚实写「N 笔·M 笔有图·
K 笔无图」;这是【凭证打包给会计核对】,不是报税、不是已申报——文案不越级。复用现成件:
reports.summary(封面汇总)· archive._posted_doc_ids(月度已入账)· docs.get_bill_image_ref(遍历所有
idx/所有 bill 附件)· ocr.pdf_storage(读字节/落盘)· reportlab(封面 · 复用 usage 字体多脚本)· fitz
(图/PDF → 合并页)。下载链接走时效签名 token(verify_token),不暴露登录态。
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
from decimal import Decimal
from typing import Optional

import fitz  # PyMuPDF

from services.export import archive
from services.ocr import pdf_storage
from services.purchase import docs as docs_svc
from services.purchase import reports as reports_svc

logger = logging.getLogger(__name__)

_MAX_BILLS_PER_DOC = 50  # 单票图片张数安全上限(防异常数据无限循环)

# 封面文案(本地 4 语池·与 line_i18n 解耦·不进 check_i18n)。
_T = {
    "title": {
        "zh": "凭证打包 · {period}",
        "th": "ชุดหลักฐาน · {period}",
        "en": "Proof bundle · {period}",
        "ja": "証憑パック · {period}",
    },
    "count": {
        "zh": "共 {n} 笔已入账 · {m} 笔有凭证图 · {k} 笔无图",
        "th": "ทั้งหมด {n} รายการที่บันทึกแล้ว · มีรูปหลักฐาน {m} · ไม่มีรูป {k}",
        "en": "{n} posted entries · {m} with proof image · {k} without",
        "ja": "計 {n} 件(記帳済)· 証憑画像あり {m} · なし {k}",
    },
    "total": {
        "zh": "合计:฿{v}",
        "th": "รวม: ฿{v}",
        "en": "Total: ฿{v}",
        "ja": "合計: ฿{v}",
    },
    "vat": {
        "zh": "可抵进项税:฿{v}",
        "th": "ภาษีซื้อที่ขอคืนได้: ฿{v}",
        "en": "Claimable input VAT: ฿{v}",
        "ja": "控除可能仕入VAT: ฿{v}",
    },
    "period": {
        "zh": "期间:{a} ~ {b}",
        "th": "ช่วง: {a} ~ {b}",
        "en": "Period: {a} ~ {b}",
        "ja": "期間: {a} ~ {b}",
    },
    "noimg_head": {
        "zh": "无凭证图的记录(仅列于此·未附图):",
        "th": "รายการที่ไม่มีรูปหลักฐาน (แสดงในหน้านี้เท่านั้น):",
        "en": "Entries without a proof image (listed here only):",
        "ja": "証憑画像がない記録(ここにのみ記載):",
    },
    "disclaimer": {
        "zh": "※ 本文件为凭证打包,供会计核对,非报税、非已申报。",
        "th": "※ เอกสารนี้คือชุดหลักฐานสำหรับให้บัญชีตรวจสอบ ไม่ใช่การยื่นภาษีหรือยื่นแล้ว",
        "en": "* This is a proof bundle for the accountant to review — not a tax filing.",
        "ja": "※ 本書類は会計確認用の証憑パックで、税務申告ではありません。",
    },
}


def _t(key: str, lang: str, **kw) -> str:
    pool = _T[key]
    return (pool.get((lang or "th").lower()) or pool["th"]).format(**kw)


def _money(v) -> str:
    return f"{Decimal(str(v or 0)):,.2f}"


def _doc_label(detail: dict) -> str:
    """单据一行摘要(封面「无图」清单 + 排序用):日期 · 卖家 · ฿总额。"""
    doc = detail.get("doc") or {}
    sup = detail.get("supplier") or {}
    seller = (sup.get("name") or "—").strip() or "—"
    return f"{doc.get('doc_date') or ''} · {seller} · ฿{_money(doc.get('grand_total'))}"


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
    """把一张票图(图片或 PDF)落盘文件 append 进 target(图→整页·PDF→全页)。成功→True。"""
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
        else:  # 图片(jpg/png…)→ 转 PDF 页
            with fitz.open(stream=data) as img:
                pdf_bytes = img.convert_to_pdf()
            with fitz.open(stream=pdf_bytes, filetype="pdf") as src:
                target.insert_pdf(src)
        return True
    except Exception as e:  # noqa: BLE001 — 单张坏图不拖垮整月打包
        logger.warning("[proof_pdf] skip bill ref=%s: %s", ref, str(e)[:120])
        return False


def _cover_pdf(summ: dict, *, n: int, m: int, no_image: list, period: str, lang: str) -> bytes:
    """封面汇总页(reportlab·复用 usage 多脚本字体)。N 笔/合计/可抵 VAT/期间 + 无图清单 + 诚实声明。"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    from services.usage.usage_report_pdf_text import _build_paragraph_text, _register_fonts

    base, bold = _register_fonts()
    body = ParagraphStyle("c", fontName=base, fontSize=12, leading=18)
    h1 = ParagraphStyle("h1", fontName=bold, fontSize=18, leading=24)
    small = ParagraphStyle("s", fontName=base, fontSize=9, leading=13, textColor="#6b7280")

    def P(s, st=body, b=False):
        return Paragraph(_build_paragraph_text(s, bold=b), st)

    total = (summ.get("goods_total") or 0) + (summ.get("expense_total") or 0)
    story = [
        P(_t("title", lang, period=period), h1, b=True),
        Spacer(1, 8 * mm),
        P(_t("count", lang, n=n, m=m, k=len(no_image))),
        P(_t("total", lang, v=_money(total))),
        P(_t("vat", lang, v=_money(summ.get("vat_claimable")))),
        P(_t("period", lang, a=summ.get("from") or "—", b=summ.get("to") or "—")),
    ]
    if no_image:
        story += [Spacer(1, 6 * mm), P(_t("noimg_head", lang), b=True)]
        story += [P("· " + lbl) for lbl in no_image]
    story += [Spacer(1, 8 * mm), P(_t("disclaimer", lang), small)]

    buf = io.BytesIO()
    SimpleDocTemplate(
        buf, pagesize=A4, topMargin=20 * mm, leftMargin=18 * mm, rightMargin=18 * mm
    ).build(story)
    return buf.getvalue()


def build_monthly_proof_pdf(
    cur, *, tenant_id, workspace_client_id, date_from, date_to, lang="th", period=""
) -> bytes:
    """整月已入账票打包成一个多页 PDF:第 1 页封面汇总 + 之后每票【所有票图页】(按日期序)。

    只含 status='posted'(草稿/未确认不进·_posted_doc_ids 已 posted-only);租户+套账隔离。无图的笔
    只在封面「无图」清单列、不占图页。返回 PDF 字节。"""
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
    images = fitz.open()  # 票图页累积
    no_image, with_image = [], 0
    for did in doc_ids:
        detail = docs_svc.get_doc(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=did
        )
        if not detail:
            continue
        label = _doc_label(detail)
        refs = _all_bill_refs(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=did
        )
        appended = sum(1 for ref in refs if _append_ref(images, ref))
        if appended:
            with_image += 1
        else:
            no_image.append(label)  # 无图 / 图全坏 → 只进封面清单(诚实)
    cover = _cover_pdf(
        summ, n=len(doc_ids), m=with_image, no_image=no_image, period=period or "", lang=lang
    )
    out = fitz.open()
    with fitz.open(stream=cover, filetype="pdf") as c:
        out.insert_pdf(c)
    if images.page_count:
        out.insert_pdf(images)
    data = out.tobytes()
    out.close()
    images.close()
    return data


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
