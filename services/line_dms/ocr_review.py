# -*- coding: utf-8 -*-
"""身份证 OCR 打回原因 → 泰文话术。

键取自 OCR 归一层真实产出的 missing_fields(services/ocr/id_card_extract)加
dms_id_ocr 追加的校验位标记,与 DMS 建档表单字段名(cards.FIELD_LABELS_TH)是两套
词表。flow 曾拿后者查前者的键,交集为空,括号里的缺项从来没印出来过。

校验位不过单独成文案:13 位已经读到,归因成「拍不清」会让人反复重拍,而每拍一次
都真扣一次 OCR 费。话术要说清是号码本身对不上,让人先核对卡面数字。
"""

from __future__ import annotations

from typing import Dict, Iterable

from services.line_dms import cards

CHECKSUM_KEY = "people_id_checksum"

# 键 = id_card_extract 的 missing_fields 产出(测试按源码机械对账,加字段不会静默掉出去)
MISSING_LABELS_TH: Dict[str, str] = {
    "people_id": "เลขบัตรประชาชน",
    "first_name": "ชื่อ",
    "last_name": "นามสกุล",
    "birthday": "วันเกิด",
}

TXT_ID_CHECKSUM = (
    "อ่านเลขบัตรประชาชนได้ครบ 13 หลัก แต่หลักตรวจสอบไม่ผ่าน "
    "กรุณาตรวจสอบเลขบนบัตรอีกครั้ง แล้วถ่ายใหม่ให้เห็นเลขบัตรชัดเจน"
)


def review_text(missing: Iterable[str]) -> str:
    """OCR 打回时对用户说的话:校验位错说号码对不上,其余才是拍不清 + 列缺项。"""
    keys = list(missing)
    head = TXT_ID_CHECKSUM if CHECKSUM_KEY in keys else cards.TXT_BLURRY
    labels = [MISSING_LABELS_TH[k] for k in keys if k in MISSING_LABELS_TH]
    return head + (" (" + ", ".join(labels) + ")" if labels else "")
