# -*- coding: utf-8 -*-
"""对账标准模板生成(按 UI 语言出列头 · 供"下载模板"端点)。

设计:列头跟随用户当前语言(zh/en/th/ja);生成的列正是各对账解析器认得的列,
故"导出即模板、模板即可导入"闭环。每个模板:第 1 行列头 + 2 行示例 + 一个『说明』
sheet;sheet 标题写 `Pearnly-<TYPE>` 作模板签名(前端"标准模板读取"可据此确定判定)。

doc_type:
  statement 银行账单 · gl 总账 · vat 税表(VAT 报告)· invoice 销项发票明细
vat 与 invoice 列结构相同(行项)。statement/gl 用于银行对账(+gl 用于收入对账)。
"""

import io
from typing import Dict, List, Tuple

# 每列:(canonical_key, {lang: 列头}) · 列头取自各解析器已认得的关键词(4 语均可解析)。
_COLS: Dict[str, List[Tuple[str, Dict[str, str]]]] = {
    "statement": [
        ("date", {"zh": "日期", "en": "Date", "th": "วันที่", "ja": "日付"}),
        ("desc", {"zh": "摘要", "en": "Description", "th": "รายละเอียด", "ja": "摘要"}),
        ("withdrawal", {"zh": "提款", "en": "Withdrawal", "th": "ถอน", "ja": "出金"}),
        ("deposit", {"zh": "存款", "en": "Deposit", "th": "ฝาก", "ja": "入金"}),
        ("balance", {"zh": "余额", "en": "Balance", "th": "ยอดคงเหลือ", "ja": "残高"}),
    ],
    "gl": [
        ("date", {"zh": "日期", "en": "Date", "th": "วันที่", "ja": "日付"}),
        ("voucher", {"zh": "凭证号", "en": "Voucher No", "th": "เลขที่ใบสำคัญ", "ja": "伝票番号"}),
        (
            "account",
            {"zh": "科目代码", "en": "Account Code", "th": "รหัสบัญชี", "ja": "勘定科目コード"},
        ),
        ("desc", {"zh": "摘要", "en": "Description", "th": "รายละเอียด", "ja": "摘要"}),
        ("debit", {"zh": "借方", "en": "Debit", "th": "เดบิต", "ja": "借方"}),
        ("credit", {"zh": "贷方", "en": "Credit", "th": "เครดิต", "ja": "貸方"}),
    ],
    "vat": [
        ("date", {"zh": "日期", "en": "Date", "th": "วันที่", "ja": "日付"}),
        (
            "invoice_no",
            {"zh": "发票号", "en": "Invoice No", "th": "เลขที่ใบกำกับ", "ja": "請求書番号"},
        ),
        ("buyer_name", {"zh": "买方名称", "en": "Buyer Name", "th": "ชื่อผู้ซื้อ", "ja": "取引先"}),
        (
            "buyer_tax",
            {
                "zh": "买方税号",
                "en": "Buyer Tax ID",
                "th": "เลขประจำตัวผู้เสียภาษี",
                "ja": "納税者番号",
            },
        ),
        ("branch", {"zh": "分支", "en": "Branch", "th": "สาขา", "ja": "支店"}),
        ("net", {"zh": "税前金额", "en": "Net", "th": "มูลค่า", "ja": "税抜金額"}),
        ("vat", {"zh": "税额", "en": "VAT", "th": "ภาษี", "ja": "消費税"}),
        ("total", {"zh": "合计", "en": "Total", "th": "ยอดรวม", "ja": "合計"}),
    ],
}
_COLS["invoice"] = _COLS["vat"]

# 两行示例(列对齐 _COLS 顺序)· 让用户照填;说明里提示删除示例行。
_SAMPLES: Dict[str, List[list]] = {
    "statement": [
        ["02/05/2026", "QR / SCB X1234", "", 1727.46, 806157.82],
        ["02/05/2026", "SIM fee", 107.00, "", 852770.35],
    ],
    "gl": [
        ["02/05/2026", "SVTAX26004029", "C1111", "QR / SCB", 1727.46, ""],
        ["02/05/2026", "FEE-SIM", "10003", "SIM fee", "", 107.00],
    ],
    "vat": [
        [
            "02/05/2026",
            "INV-0001",
            "ABC Co., Ltd.",
            "0105556001234",
            "00000",
            1000.00,
            70.00,
            1070.00,
        ],
        ["02/05/2026", "INV-0002", "Mr. Somchai", "", "", 500.00, 35.00, 535.00],
    ],
}
_SAMPLES["invoice"] = _SAMPLES["vat"]

_TITLE = {
    "statement": {
        "zh": "银行账单",
        "en": "Bank Statement",
        "th": "Statement ธนาคาร",
        "ja": "銀行明細",
    },
    "gl": {"zh": "总账 GL", "en": "General Ledger", "th": "บัญชีแยกประเภท GL", "ja": "総勘定元帳"},
    "vat": {"zh": "销项税报告", "en": "VAT Report", "th": "รายงานภาษีขาย", "ja": "消費税レポート"},
    "invoice": {
        "zh": "销项发票明细",
        "en": "Sales Invoices",
        "th": "ใบกำกับภาษีขาย",
        "ja": "売上請求書",
    },
}

# 说明文案(只列要点 · 不出现 OCR/AI 字眼)。
_NOTES = {
    "zh": [
        "Pearnly 标准模板 · {t}",
        "1) 列头勿改,一行一笔。",
        "2) 日期 dd/mm/yyyy(佛历年份自动转)。金额纯数字,勿带逗号或货币符号。",
        "3) 删除下面的示例行后,填入你的数据。请勿保留「合计/小计」等汇总行。",
    ],
    "en": [
        "Pearnly standard template · {t}",
        "1) Keep the header row unchanged. One record per row.",
        "2) Date dd/mm/yyyy. Numbers only (no commas / currency symbols).",
        "3) Delete the sample rows below, then fill in your data. Do not keep total/subtotal rows.",
    ],
    "th": [
        "เทมเพลตมาตรฐาน Pearnly · {t}",
        "1) ห้ามแก้หัวคอลัมน์ · หนึ่งรายการต่อหนึ่งแถว",
        "2) วันที่ dd/mm/yyyy · ตัวเลขล้วน ไม่ใส่จุลภาค/สัญลักษณ์เงิน",
        "3) ลบแถวตัวอย่างด้านล่างแล้วกรอกข้อมูลของคุณ · อย่าทิ้งแถวรวม/ผลรวม",
    ],
    "ja": [
        "Pearnly 標準テンプレート · {t}",
        "1) ヘッダー行は変更しないでください。1行に1件。",
        "2) 日付は dd/mm/yyyy。数字のみ(カンマ・通貨記号なし)。",
        "3) 下のサンプル行を削除してからデータを入力。合計/小計行は残さないでください。",
    ],
}


def template_signature(doc_type: str) -> str:
    return f"Pearnly-{doc_type.upper()}"


def generate_template(doc_type: str, lang: str = "en") -> bytes:
    """生成对账标准模板 xlsx 字节。doc_type ∈ {statement,gl,vat,invoice};lang ∈ {zh,en,th,ja}。"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    if doc_type not in _COLS:
        raise ValueError(f"unknown doc_type: {doc_type!r}")
    if lang not in ("zh", "en", "th", "ja"):
        lang = "en"

    cols = _COLS[doc_type]
    headers = [c[1].get(lang) or c[1]["en"] for c in cols]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = template_signature(doc_type)  # 模板签名(前端可据 sheet 名确定判定)
    ws.append(headers)
    for s in _SAMPLES[doc_type]:
        ws.append(s)
    hf = Font(bold=True, color="FFFFFF")
    fill = PatternFill("solid", fgColor="2563EB")
    for i in range(1, len(headers) + 1):
        c = ws.cell(1, i)
        c.font = hf
        c.fill = fill
        c.alignment = Alignment(horizontal="center")
        ws.column_dimensions[c.column_letter].width = 18

    note = wb.create_sheet(
        {"zh": "说明", "en": "Instructions", "th": "วิธีใช้", "ja": "説明"}[lang]
    )
    title = _TITLE[doc_type].get(lang) or _TITLE[doc_type]["en"]
    for i, line in enumerate(_NOTES[lang], 1):
        note.cell(i, 1, line.replace("{t}", title))
    note.column_dimensions["A"].width = 90

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def template_filename(doc_type: str, lang: str = "en") -> str:
    return f"Pearnly_{doc_type}_{lang}.xlsx"
