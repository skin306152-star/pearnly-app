# -*- coding: utf-8 -*-
"""表格生成的文案层(zh + th · 纯函数)。数字全部来自 tools_table.execute 的 Decimal 结果,
本层只取值填空,不做任何计算(与全站其余 copy_* 模块同一条铁律)。
"""

from __future__ import annotations

from typing import Optional

from services.steward import registry
from services.steward.copy_lang import t as _t

TITLES = {registry.TABLE_GENERATE: {"zh": "表格生成", "th": "สร้างตารางใหม่"}}

_DOWNLOAD_LABEL = {"zh": "下载生成的表", "th": "ดาวน์โหลดตารางที่สร้าง"}
_PREVIEW_LABEL = {"zh": "预览(前 {n} 行)", "th": "ตัวอย่าง ({n} แถวแรก)"}

_REPLY_OK = {
    "zh": "「{filename}」按「{instruction}」整理好了:{rows} 行,已生成新表。",
    "th": "จัดตาราง「{filename}」ตาม「{instruction}」เสร็จแล้ว: {rows} แถว สร้างตารางใหม่แล้ว",
}
_REPLY_EMPTY = {
    "zh": "「{filename}」按「{instruction}」整理后没有符合条件的行,没有生成表。",
    "th": "จัดตาราง「{filename}」ตาม「{instruction}」แล้วไม่มีแถวที่ตรงเงื่อนไข จึงไม่ได้สร้างตาราง",
}

ERRORS = {
    "steward.table_gen_unreadable": {
        "zh": "「{filename}」读不出表格内容({status}),换一份可读的表格重传。",
        "th": "「{filename}」อ่านเนื้อหาตารางไม่ได้ ({status}) ส่งไฟล์ตารางที่อ่านได้มาใหม่",
    },
    "steward.table_gen_no_instruction": {
        "zh": "没看到整理要求——连着表格一起把想怎么整理打出来,比如「按供应商汇总金额」。",
        "th": "ไม่เห็นคำสั่งจัดตาราง พิมพ์วิธีที่อยากจัดมาพร้อมไฟล์ เช่น「สรุปยอดตามผู้ขาย」",
    },
    "steward.table_gen_model_failed": {
        "zh": "这次没生成规格,服务暂时不可用,再说一次。",
        "th": "รอบนี้สร้างข้อกำหนดไม่ได้ ระบบขัดข้องชั่วคราว ลองใหม่อีกครั้ง",
    },
    "steward.table_gen_spec_rejected": {
        "zh": "整理要求里提到的列或算法认不出来,换个说法(直接说列名,比如「按供应商汇总金额」)。",
        "th": (
            "คอลัมน์หรือวิธีคำนวณในคำสั่งไม่รู้จัก "
            "ลองพูดใหม่ (ระบุชื่อคอลัมน์ตรง ๆ เช่น「สรุปยอดตามผู้ขาย」)"
        ),
    },
}


def error(code: str, data: Optional[dict], lang: str) -> str:
    table = ERRORS.get(code)
    if not table:
        return ""
    data = data or {}
    return _t(table, lang).format(filename=data.get("filename", ""), status=data.get("status", ""))


def reply(data: dict, lang: str) -> str:
    table = _REPLY_OK if data.get("row_count") else _REPLY_EMPTY
    return _t(table, lang).format(
        filename=data.get("filename", ""),
        instruction=data.get("instruction", ""),
        rows=data.get("row_count", 0),
    )


REPLIES = {registry.TABLE_GENERATE: reply}


def artifacts(data: dict, lang: str) -> list[dict]:
    if not data.get("row_count"):
        return []  # 诚实空态:过滤后零行不出下载链、不出空表(与 tools_table 的空态口径同一件事)
    out: list[dict] = []
    download = data.get("download") or {}
    if download.get("attachment_id"):
        out.append(
            {
                "kind": "deeplink",
                "label": _t(_DOWNLOAD_LABEL, lang),
                "href": f"/api/ai/steward/attachments/{download['attachment_id']}/download",
            }
        )
    columns = data.get("columns") or []
    preview = data.get("preview") or []
    if columns and preview:
        out.append(
            {
                "kind": "table",
                "label": _t(_PREVIEW_LABEL, lang).format(n=len(preview)),
                "columns": [{"key": c, "label": c} for c in columns],
                "rows": preview,
            }
        )
    return out
