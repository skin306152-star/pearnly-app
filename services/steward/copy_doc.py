# -*- coding: utf-8 -*-
"""读文问答的文案层(zh + th · 纯函数)。

答案本身是 tools_doc_qa 里模型的产物,不是本层拼出来的——这是全站唯一一处答复正文不是
纯模板填空的工具,例外是有意的:「答文中写了什么」这件事的本体就是自然语言复述,数字与
引用的诚实闸已经在 tools_doc_qa.parse_answer 过了(reply_guard.sane + 逐条引用核对原文),
这里只负责把已核对过的 answer/citations 摆上台面,不再二次改写。
"""

from __future__ import annotations

from typing import Optional

from services.steward import registry
from services.steward.copy_lang import t as _t

TITLES = {registry.DOC_READ_QA: {"zh": "读文问答", "th": "ถามตอบจากไฟล์"}}

_CITATIONS_LABEL = {"zh": "引用原文", "th": "อ้างอิงจากต้นฉบับ"}
_COL_PAGE = {"zh": "页", "th": "หน้า"}
_COL_QUOTE = {"zh": "原文", "th": "ข้อความ"}
_NO_CITATION_HINT = {
    "zh": "(这份答案没有能核对的原文引用,谨慎采信。)",
    "th": "(คำตอบนี้ไม่มีข้ออ้างอิงจากต้นฉบับที่ตรวจสอบได้ ใช้อย่างระมัดระวัง)",
}

ERRORS = {
    # 这条是防御性回检的口(attach_turn 已按 detect 时的 needs_model 先弹过一次计费卡;
    # 真到这里说明那次判断与工具实际所需不一致),文案说清「要点确认才能继续」而不是「没法读」
    # ——扫描件/图片不是永久拒绝,补一次点击就能过(见 tools_doc_qa._ocr_pages)。
    "steward.doc_qa_needs_model": {
        "zh": "「{filename}」是扫描件或图片,要回答你的问题需先过一次 OCR 识别——点确认按钮授权这次识别。",
        "th": (
            "「{filename}」เป็นไฟล์สแกนหรือรูปภาพ ต้องอ่านด้วย OCR ก่อนจึงตอบคำถามได้ "
            "กดยืนยันเพื่ออนุญาตให้อ่านครั้งนี้"
        ),
    },
    "steward.doc_qa_unreadable": {
        "zh": "「{filename}」取不出内容({status}),换一份可读的文件重传。",
        "th": "「{filename}」ดึงเนื้อหาไม่ได้ ({status}) ส่งไฟล์ที่อ่านได้มาใหม่",
    },
    "steward.doc_qa_unsupported_type": {
        "zh": "「{filename}」暂不支持读文问答({ext})。目前支持:PDF(含扫描件,经 OCR)/"
        "图片(经 OCR)/Excel/CSV/TSV/TXT。",
        "th": (
            "「{filename}」ยังไม่รองรับถามตอบจากไฟล์ ({ext}) "
            "ตอนนี้รองรับ: PDF(รวมไฟล์สแกน ผ่าน OCR)/รูปภาพ(ผ่าน OCR)/Excel/CSV/TSV/TXT"
        ),
    },
    "steward.doc_qa_no_question": {
        "zh": "没看到问题——连着文件一起把想问的话打出来。",
        "th": "ไม่เห็นคำถาม พิมพ์สิ่งที่อยากถามมาพร้อมกับไฟล์",
    },
    "steward.doc_qa_model_failed": {
        "zh": "这次没读出答案,服务暂时不可用,再问一次。",
        "th": "รอบนี้อ่านคำตอบไม่ได้ ระบบขัดข้องชั่วคราว ลองถามใหม่อีกครั้ง",
    },
}


def error(code: str, data: Optional[dict], lang: str) -> str:
    table = ERRORS.get(code)
    if not table:
        return ""
    data = data or {}
    return _t(table, lang).format(
        filename=data.get("filename", ""), status=data.get("status", ""), ext=data.get("ext", "")
    )


def reply(data: dict, lang: str) -> str:
    answer = str(data.get("answer") or "").strip()
    if answer and not data.get("citations"):
        return f"{answer}{_t(_NO_CITATION_HINT, lang)}"
    return answer


REPLIES = {registry.DOC_READ_QA: reply}


def artifacts(data: dict, lang: str) -> list[dict]:
    citations = data.get("citations") or []
    if not citations:
        return []
    return [
        {
            "kind": "table",
            "label": _t(_CITATIONS_LABEL, lang),
            "columns": [
                {"key": "page", "label": _t(_COL_PAGE, lang)},
                {"key": "quote", "label": _t(_COL_QUOTE, lang)},
            ],
            "rows": [{"page": c.get("page"), "quote": c.get("quote")} for c in citations],
        }
    ]
