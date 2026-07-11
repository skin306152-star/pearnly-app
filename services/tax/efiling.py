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
from datetime import date
from decimal import Decimal
from typing import Mapping

from core.pos_api import PosError
from services.accounting.books_pdf import _render_table
from services.sales import wht as wht_presets
from services.tax import rdprep
from services.tax.aggregate import PND3, PND53, _dec

EXPORT_FORMATS = ("pdf", "xml", "zip", "rdprep")

# RD Prep 常量档(方案 §2.3 M1 口径):商业 WHT 主条款恒真,其余法条位恒假;媒介寄档
# 报送人固定代码;PAY_CON 绝大多数走"扣缴"(§G2 边缘代付场景留人工,M1 不猜)。
_RDPREP_SENDER_ID = "0000"
_RDPREP_SENDER_ROLE = "1"
_RDPREP_DEPT_NAME_HQ = "สำนักงานใหญ่"
_RDPREP_SECTION3 = "1"
_RDPREP_SECTION_OFF = "0"
_RDPREP_LTO = "0"
_RDPREP_FORM_TYPE = "00"
_RDPREP_FORM_FLAG_MEDIA = "1"
_RDPREP_TIN_LEGACY = "0000000000"
_RDPREP_PAY_CON_STANDARD = "1"
_RDPREP_USER_ID_PLACEHOLDER = "PLACEHOLDER"  # §G7:登记参考号未接,诚实占位待客户 RD 账号
_RDPREP_TITLE_JURISTIC = "บริษัท"
_RDPREP_TITLE_INDIVIDUAL = "-"
_RDPREP_DEFAULT_BRANCH = "000000"
_RDPREP_ZERO = Decimal("0")

# PND3 收款人地址法定必填三项(官方 PDF §1.5 字段 36-38);缺一即不可导入 RD Prep,
# 该行剔除而非臆造拆分(方案 §2.3 G5)。
_RDPREP_ADDRESS_REQUIRED = ("amphur", "province", "postal_code")

# 收入类型文字 = wht_rate → WHT_PRESETS 泰文档位(方案 §2.3 G1),单一事实源在
# services.sales.wht,这里只取泰文部分(标签含 " / 英文" 与 RD Prep 分隔符 "|" 无关但
# 保持记录纯泰文更贴官方示例)。未命中档位(如自定义税率)落 3% 服务档,与
# purchase_settings.default_wht_service_rate 口径一致。
_RDPREP_INC_TYPE_BY_RATE = {
    Decimal(rate): label.split(" / ", 1)[0] for rate, label in wht_presets.WHT_PRESETS
}
_RDPREP_DEFAULT_INC_TYPE = _RDPREP_INC_TYPE_BY_RATE[Decimal("3")]

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


def _rdprep_inc_type(rate) -> str:
    if rate is None:
        return _RDPREP_DEFAULT_INC_TYPE
    return _RDPREP_INC_TYPE_BY_RATE.get(Decimal(str(rate)), _RDPREP_DEFAULT_INC_TYPE)


def _rdprep_address_complete(addr: Mapping | None) -> bool:
    if not addr:
        return False
    return all((addr.get(k) or "").strip() for k in _RDPREP_ADDRESS_REQUIRED)


def _rdprep_paid_date(period: str, line: Mapping) -> date:
    """支付日取源单 doc_date;filing_lines 现无此列(未来接线口),缺失退期初日,
    不臆造具体日期(方案 §附:关键坐标速查·filing_lines schema 无 doc_date)。"""
    raw = line.get("doc_date")
    if raw:
        return raw if isinstance(raw, date) else date.fromisoformat(str(raw))
    return date(int(period[:4]), int(period[5:7]), 1)


def _rdprep_detail_values(
    form: str, seq_no: int, branch_no: str, period: str, line: Mapping
) -> dict:
    payee_type = line.get("payee_type") or "juristic"
    addr = line.get("payee_address") or {}
    values = {
        "SEQ_NO": seq_no,
        "BRANCH_NO": branch_no,
        "TIN": _RDPREP_TIN_LEGACY,
        "TITLE_NAME": (
            _RDPREP_TITLE_JURISTIC if payee_type == "juristic" else _RDPREP_TITLE_INDIVIDUAL
        ),
        "FNAME": line.get("payee_name") or "",
        "PAID_DATE1": rdprep.to_buddhist_paid_date(_rdprep_paid_date(period, line)),
        "TAX_RATE1": line.get("wht_rate"),
        "PAID_AMT1": line.get("base_amount"),
        "TAX_AMT1": line.get("wht_amount"),
        "INC_TYPE_PND1": _rdprep_inc_type(line.get("wht_rate")),
        "PAY_CON1": _RDPREP_PAY_CON_STANDARD,
        "AMPHUR": addr.get("amphur", ""),
        "PROVINCE": addr.get("province", ""),
        "POSTAL_CODE": addr.get("postal_code", ""),
        "TAMBON": addr.get("tambon", ""),
        "ADD_NO": addr.get("add_no", ""),
        "MOO_NO": addr.get("moo_no", ""),
        "SOI": addr.get("soi", ""),
        "STREET_NAME": addr.get("street_name", ""),
        "BUILD_NAME": addr.get("build_name", ""),
        "ROOM_NO": addr.get("room_no", ""),
        "FLOOR_NO": addr.get("floor_no", ""),
        "VILLAGE_NAME": addr.get("village_name", ""),
    }
    values["NID" if form == rdprep.PND53 else "PIN"] = line.get("payee_tax_id") or ""
    return values


def export_rdprep_txt(filing: dict, *, taxpayer: dict | None = None) -> dict:
    """RD Prep 中央格式 .txt 导出(方案 §5.4/D1-4):filing(aggregate.pnd 装出的
    filing_lines 结构)→ rdprep.assemble 纯装配,钱/字段序单一事实源留在 rdprep.py,
    这里只做取数映射,不重算。

    PND3(个人)法定地址三项(AMPHUR/PROVINCE/POSTAL_CODE)未存 → 该行剔除出 txt,
    在返回结构 excluded 里点名(方案 §2.3 G5,诚实不臆造拆分)。
    """
    kind = filing["kind"]
    if kind not in (PND53, PND3):
        raise PosError("tax.efiling_failed", 422, detail="rdprep_unsupported_kind")
    form = rdprep.PND53 if kind == PND53 else rdprep.PND3
    taxpayer = taxpayer or {}
    nid = taxpayer.get("tax_id") or ""
    branch_no = taxpayer.get("branch_no") or _RDPREP_DEFAULT_BRANCH
    period = filing["period"]
    year, month = int(period[:4]), int(period[5:7])

    included, excluded = [], []
    for line in filing.get("lines") or []:
        if form == rdprep.PND3 and not _rdprep_address_complete(line.get("payee_address")):
            excluded.append(
                {
                    "payee_name": line.get("payee_name"),
                    "payee_tax_id": line.get("payee_tax_id"),
                    "reason": "missing_address",
                }
            )
            continue
        included.append(line)

    details = [
        rdprep.build_detail(form, _rdprep_detail_values(form, i, branch_no, period, ln))
        for i, ln in enumerate(included, start=1)
    ]
    tot_amt = sum((_dec(ln.get("base_amount")) for ln in included), _RDPREP_ZERO)
    tot_tax = sum((_dec(ln.get("wht_amount")) for ln in included), _RDPREP_ZERO)
    header_values = {
        "SENDER_ID": _RDPREP_SENDER_ID,
        "SENDER_NID": nid,
        "SENDER_BRANCH": branch_no,
        "SENDER_ROLE": _RDPREP_SENDER_ROLE,
        "NID": nid,
        "BRANCH_NO": branch_no,
        "DEPT_NAME": _RDPREP_DEPT_NAME_HQ,
        "SECTION3": _RDPREP_SECTION3,
        "SECTION_B": _RDPREP_SECTION_OFF,
        "SECTION_C": _RDPREP_SECTION_OFF,
        "LTO": _RDPREP_LTO,
        "TAX_MONTH": f"{month:02d}",
        "TAX_YEAR": rdprep.to_buddhist_year(year),
        "BRANCH_TYPE": (
            taxpayer.get("branch_type") if taxpayer.get("branch_type") in ("V", "S") else ""
        ),
        "FORM_TYPE": _RDPREP_FORM_TYPE,
        "TOT_NUM": len(details),
        "TOT_AMT": tot_amt,
        "TOT_TAX": tot_tax,
        "SUR_AMT": _RDPREP_ZERO,
        "GTOT_TAX": tot_tax,
        "TRANS_AMT": _RDPREP_ZERO,
        "USER_ID": taxpayer.get("user_id") or _RDPREP_USER_ID_PLACEHOLDER,
        "FORM_FLAG": _RDPREP_FORM_FLAG_MEDIA,
    }
    text = rdprep.assemble(rdprep.build_header(form, header_values), details)
    filename = rdprep.build_filename(
        form=form,
        nid=nid,
        branch_no=branch_no,
        tax_year_be=rdprep.to_buddhist_year(year),
        tax_month=f"{month:02d}",
    )
    return {"text": text, "filename": filename, "excluded": excluded}
