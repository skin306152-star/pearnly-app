# -*- coding: utf-8 -*-
"""Native payment field questions shared by the booking conversation."""

TXT_ASK_PAY_SRC_DETAIL = (
    "ข้อมูลต้นทาง — พิมพ์ ชื่อบัญชี | เลขบัญชี | สาขา | เวลาโอน\n"
    "เช่น สมชาย ใจดี | 1234567890 | ระยอง | 14:36\n"
    "กรอกข้อมูลจริงให้ครบตามรายการโอน ไม่ใช้ - เพื่อข้าม"
)
TXT_ASK_PAY_DST_DETAIL = (
    "บัญชีบริษัทที่ได้รับเงิน — พิมพ์ ชื่อบัญชีบริษัท | เลขบัญชี | สาขา\n"
    "เช่น บริษัท ตัวอย่าง จำกัด | 1234567890 | ระยอง\n"
    "ใช้บัญชีที่ลูกค้าโอนเข้าจริง รายชื่อธนาคารไม่ได้ระบุบัญชีบริษัท"
)


def ask_payment_bank(banks: list, page: int = 0) -> dict:
    from services.line_dms.qa_cards import _msg, _option_text, _pick_rows, TXT_NO_COMPANY_BANK
    from services.erp.mrerp_dms_company_banks import company_bank_label

    if not banks:
        return _msg(TXT_NO_COMPANY_BANK)
    return _msg(
        _option_text("เลือกธนาคาร", banks, company_bank_label, page),
        _pick_rows(banks, "paybank", company_bank_label, page),
    )


def ask_transfer_details(destination: bool) -> dict:
    return {
        "type": "text",
        "text": TXT_ASK_PAY_DST_DETAIL if destination else TXT_ASK_PAY_SRC_DETAIL,
    }


def ask_pay_src(banks: list, page: int = 0) -> dict:
    from services.line_dms.qa_cards import (
        _msg,
        _option_text,
        _pick_rows,
        TXT_NO_COMPANY_BANK,
        TXT_ASK_PAY_SRC,
    )
    from services.erp.mrerp_dms_company_banks import company_bank_label

    if not banks:
        return _msg(TXT_NO_COMPANY_BANK)
    return _msg(
        _option_text(TXT_ASK_PAY_SRC, banks, company_bank_label, page),
        _pick_rows(banks, "srcbank", company_bank_label, page),
    )
