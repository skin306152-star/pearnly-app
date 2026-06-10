# -*- coding: utf-8 -*-
"""提交 / 导出(docs/tax-filing/02 §提交)。

e-Tax 直报:RD e-filing 开放度未确认(05 已知坑「别假设能直连」)→ method=etax 诚实
返回 tax.efiling_failed(detail=etax_not_available),接通后此处换真提交拿回执。
兜底主路径 = 导出合规文件(PDF 申报底稿 + XML 结构化数据,可照抄手报 RD 门户),
手报完 mark-filed 回填回执号。PDF 复用 books_pdf 表格渲染(泰文/CJK 字体同源)。
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile

from core.pos_api import PosError
from services.accounting.books_pdf import _render_table
from services.tax.aggregate import _dec

EXPORT_FORMATS = ("pdf", "xml", "zip")

_L = {
    "title.pp30": {
        "zh": "增值税申报表(PP30)",
        "th": "แบบแสดงรายการภาษีมูลค่าเพิ่ม (ภ.พ.30)",
        "en": "VAT Return (PP30)",
        "ja": "付加価値税申告書(PP30)",
    },
    "title.pnd53": {
        "zh": "预扣税申报表(PND53 · 法人)",
        "th": "แบบยื่นภาษีเงินได้หัก ณ ที่จ่าย (ภ.ง.ด.53)",
        "en": "Withholding Tax Return (PND53)",
        "ja": "源泉徴収税申告書(PND53)",
    },
    "title.pnd3": {
        "zh": "预扣税申报表(PND3 · 个人)",
        "th": "แบบยื่นภาษีเงินได้หัก ณ ที่จ่าย (ภ.ง.ด.3)",
        "en": "Withholding Tax Return (PND3)",
        "ja": "源泉徴収税申告書(PND3)",
    },
    "h.item": {"zh": "项目", "th": "รายการ", "en": "Item", "ja": "項目"},
    "h.amount": {"zh": "金额", "th": "จำนวนเงิน", "en": "Amount", "ja": "金額"},
    "h.payee": {"zh": "收款人", "th": "ผู้รับเงิน", "en": "Payee", "ja": "受取人"},
    "h.tax_id": {
        "zh": "税号",
        "th": "เลขประจำตัวผู้เสียภาษี",
        "en": "Tax ID",
        "ja": "納税者番号",
    },
    "h.base": {"zh": "付款基数", "th": "เงินได้ที่จ่าย", "en": "Base", "ja": "支払基数"},
    "h.rate": {"zh": "税率%", "th": "อัตรา%", "en": "Rate%", "ja": "税率%"},
    "h.wht": {"zh": "代扣额", "th": "ภาษีที่หัก", "en": "WHT", "ja": "源泉額"},
    "h.total": {"zh": "合计", "th": "รวม", "en": "Total", "ja": "合計"},
    "r.output_vat": {"zh": "本期销项税", "th": "ภาษีขาย", "en": "Output VAT", "ja": "売上VAT"},
    "r.input_gross": {
        "zh": "本期进项税(账面)",
        "th": "ภาษีซื้อ (ตามบัญชี)",
        "en": "Input VAT (books)",
        "ja": "仕入VAT(帳簿)",
    },
    "r.excl_expired": {
        "zh": "剔除:超 6 个月失效",
        "th": "หัก: เกิน 6 เดือน",
        "en": "Excluded: over 6 months",
        "ja": "除外:6ヶ月超",
    },
    "r.excl_no_taxid": {
        "zh": "剔除:缺供应商税号",
        "th": "หัก: ไม่มีเลขผู้เสียภาษี",
        "en": "Excluded: missing tax ID",
        "ja": "除外:税番号なし",
    },
    "r.input_claimable": {
        "zh": "可抵进项税",
        "th": "ภาษีซื้อที่ขอคืนได้",
        "en": "Claimable input VAT",
        "ja": "控除可能仕入VAT",
    },
    "r.net_payable": {
        "zh": "应交税额(销项−进项)",
        "th": "ภาษีที่ต้องชำระ",
        "en": "VAT payable",
        "ja": "納付税額",
    },
    "r.carry_forward": {
        "zh": "留抵下月",
        "th": "ภาษีชำระเกินยกไป",
        "en": "Carry forward",
        "ja": "繰越控除",
    },
}


def _t(key: str, lang: str) -> str:
    d = _L[key]
    return d.get(lang) or d["th"]


def submit_etax(filing: dict, settings: dict) -> dict:
    """RD e-filing 直报。开放度未确认 → 诚实失败,前端引导走导出手报。"""
    raise PosError("tax.efiling_failed", 502, detail="etax_not_available")


def export_pdf(filing: dict, *, lang: str = "th") -> bytes:
    kind, period = filing["kind"], filing["period"]
    title = _t(f"title.{kind}", lang)
    if kind == "pp30":
        b = filing["breakdown"]
        rows = [
            ([_t("r.output_vat", lang), _dec(b.get("output_vat"))], ""),
            ([_t("r.input_gross", lang), _dec(b.get("input_vat_gross"))], ""),
            ([_t("r.excl_expired", lang), _dec(b.get("input_vat_excluded_expired"))], ""),
            ([_t("r.excl_no_taxid", lang), _dec(b.get("input_vat_excluded_missing_tax_id"))], ""),
            ([_t("r.input_claimable", lang), _dec(b.get("input_vat_claimable"))], "section"),
        ]
        net = _dec(b.get("net"))
        if net >= 0:
            rows.append(([_t("r.net_payable", lang), net], "total"))
        else:
            rows.append(([_t("r.carry_forward", lang), -net], "total"))
        headers = [_t("h.item", lang), _t("h.amount", lang)]
        return _render_table(title, period, headers, rows, [120, 62])

    rows = [
        (
            [
                ln["payee_name"] or "—",
                ln["payee_tax_id"] or "—",
                _dec(ln["base_amount"]),
                _dec(ln["wht_rate"]) if ln["wht_rate"] is not None else "—",
                _dec(ln["wht_amount"]),
            ],
            "",
        )
        for ln in filing.get("lines") or []
    ]
    rows.append(([_t("h.total", lang), "", "", "", _dec(filing["net_amount"])], "total"))
    headers = [
        _t("h.payee", lang),
        _t("h.tax_id", lang),
        _t("h.base", lang),
        _t("h.rate", lang),
        _t("h.wht", lang),
    ]
    return _render_table(title, period, headers, rows, [52, 38, 30, 18, 30])


def export_xml(filing: dict, *, taxpayer: dict | None = None) -> bytes:
    """结构化导出(全字段·机器可读)。RD 官方 e-filing 上传格式待 RD 规格确认后对齐。"""
    root = ET.Element(
        "tax_filing",
        {"kind": filing["kind"], "period": filing["period"], "status": filing["status"]},
    )
    tp = ET.SubElement(root, "taxpayer")
    for k in ("name", "tax_id", "branch_type", "branch_no"):
        v = (taxpayer or {}).get(k)
        if v:
            ET.SubElement(tp, k).text = str(v)
    ET.SubElement(root, "net_amount").text = str(filing["net_amount"])
    ET.SubElement(root, "due_date").text = str(filing["due_date"] or "")
    breakdown = ET.SubElement(root, "breakdown")
    for k, v in (filing.get("breakdown") or {}).items():
        ET.SubElement(breakdown, k).text = str(v)
    lines = filing.get("lines") or []
    if lines:
        lines_el = ET.SubElement(root, "lines")
        for ln in lines:
            le = ET.SubElement(lines_el, "line")
            for k in (
                "payee_name",
                "payee_tax_id",
                "payee_type",
                "income_type",
                "base_amount",
                "wht_rate",
                "wht_amount",
                "source_purchase_id",
            ):
                if ln.get(k) is not None:
                    ET.SubElement(le, k).text = str(ln[k])
    buf = io.BytesIO()
    ET.ElementTree(root).write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue()


def export_bundle(filing: dict, *, lang: str = "th", taxpayer: dict | None = None) -> bytes:
    """PDF + XML 打包(手报文件包)。"""
    name = f"{filing['kind']}_{filing['period']}"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{name}.pdf", export_pdf(filing, lang=lang))
        zf.writestr(f"{name}.xml", export_xml(filing, taxpayer=taxpayer))
    return buf.getvalue()
