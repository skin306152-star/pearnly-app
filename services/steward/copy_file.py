# -*- coding: utf-8 -*-
"""万能口的文案层:两个附件工具的答复/产物 + 收到料之后那张回执卡(zh + th · 纯函数)。

回执卡上的每一个字、每一个数都由本模块按确定性数据渲染,模型一个字都不写 —— 它连文件内容
都看不到(prompt 里只有 manifest)。认不出就写「认不出是什么」,不写「其他」这种假装认过的词。

分居理由同 copy_close/copy_calc:copy.py 撞 500 行闸。语义边界仍是 copy —— 调用方走
copy.reply / copy.artifacts / copy.error,本模块不被外部直接 import(attach_turn 除外:
回执卡是它现造的,不经过工具执行路径)。
"""

from __future__ import annotations

from typing import Any, Optional

from services.steward import attach_kinds as ak, registry, store

DEFAULT_LANG = "zh"

TITLES = {
    registry.FILE_CONVERT: {"zh": "转成 Excel", "th": "แปลงเป็น Excel"},
    registry.VAT_REPORT_CHECK: {"zh": "销项报告三查", "th": "ตรวจรายงานภาษีขาย 3 ข้อ"},
}

RECEIPT_TITLE = {"zh": "收到的文件", "th": "ไฟล์ที่ได้รับ"}
_RECEIPT_STEP = {"zh": "认一下这是什么料", "th": "ดูว่าเป็นเอกสารอะไร"}
_AWAIT_PICK = {"zh": "等你选一个", "th": "รอคุณเลือก"}

KIND_LABEL = {
    ak.GL_LEDGER: {"zh": "GL 台账", "th": "บัญชีแยกประเภท"},
    ak.BANK_STATEMENT: {"zh": "银行流水", "th": "รายการเดินบัญชี"},
    ak.SALES_SUMMARY: {"zh": "销售汇总表", "th": "สรุปยอดขาย"},
    ak.VAT_REPORT: {"zh": "销项 VAT 报告", "th": "รายงานภาษีขาย"},
    ak.INVOICE: {"zh": "票据照片", "th": "รูปใบกำกับ"},
    ak.UNSUPPORTED: {"zh": "不支持的格式", "th": "ไฟล์ที่ไม่รองรับ"},
    ak.UNKNOWN: {"zh": "认不出是什么", "th": "ยังไม่รู้ว่าเป็นเอกสารอะไร"},
    "converted": {"zh": "转出来的表", "th": "ตารางที่แปลงแล้ว"},
    # fileconv 引擎自己的 doc_type(转换结果里回来的),与上面的料名共用一张表。
    "generic_table": {"zh": "通用表格", "th": "ตารางทั่วไป"},
    "financials_report": {"zh": "月度报表", "th": "งบการเงินรายเดือน"},
}

_ACTIONS_LABEL = {"zh": "你想让我做哪一样", "th": "ให้ทำอะไรดีคะ"}
_FILES_LABEL = {"zh": "收到的文件", "th": "ไฟล์ที่ได้รับ"}
_ISSUES_LABEL = {"zh": "对不平的行", "th": "แถวที่ยอดไม่ตรง"}
_MISSING_LABEL = {"zh": "缺的号", "th": "เลขที่ขาด"}
_BUYERS_LABEL = {"zh": "买家分组", "th": "สรุปตามผู้ซื้อ"}
_INTAKE_LABEL = {"zh": "去上传页做识别入库", "th": "ไปหน้าอัปโหลดเพื่อสแกนเข้าระบบ"}
_DOWNLOAD_LABEL = {"zh": "下载转出来的 Excel", "th": "ดาวน์โหลด Excel ที่แปลงแล้ว"}

_RECEIPT = {
    "zh": "收到 {n} 份:{breakdown}。{tail}",
    "th": "รับไฟล์ {n} ไฟล์: {breakdown} {tail}",
}
_RECEIPT_PICK = {"zh": "下面挑一个,我就开干。", "th": "เลือกด้านล่างได้เลย เดี๋ยวจัดให้ค่ะ"}
_RECEIPT_NO_ACTION = {
    "zh": "这几份我这边还接不上活,直接说你想做什么也行。",
    "th": "ไฟล์ชุดนี้ยังต่อกับงานในแชตไม่ได้ค่ะ บอกมาได้เลยว่าอยากให้ทำอะไร",
}
_RECEIPT_PICK_FILE = {
    "zh": "这一轮有 {n} 份能做「{title}」,挑一份吧 —— 我不替你猜挑哪份。",
    "th": "รอบนี้มี {n} ไฟล์ที่ทำ「{title}」ได้ เลือกมาสักไฟล์นะคะ ไม่เดาให้ค่ะ",
}
# 措辞不写死「没有文字层」:有文字层但表抽不出行的电子版 PDF 同样会落到模型上(见
# attach_kinds.vat_check_needs_model),照旧措辞会说出一句当场就能被戳破的假话。
_SPEND_CONFIRM = {
    "zh": "「{name}」不过模型读不出内容(扫描件,或表格抽不出行)。要我过一次模型读吗?",
    "th": "「{name}」ถ้าไม่เรียกโมเดลจะอ่านเนื้อหาไม่ได้ (เป็นไฟล์สแกน หรือดึงตารางไม่ออก) ให้เรียกโมเดลหนึ่งรอบไหมคะ",
}
_SPEND_LABEL = {"zh": "读吧(会过一次模型)", "th": "อ่านเลย (จะเรียกโมเดลหนึ่งรอบ)"}
_NOTE_NEEDS_MODEL = {"zh": "要过一次模型才读得出", "th": "ต้องให้โมเดลอ่านหนึ่งรอบ"}
_RECEIPT_MORE = {
    "zh": "(还有 {n} 条路没列出来,一次挑一份说给我。)",
    "th": " (ยังมีอีก {n} ตัวเลือกที่ไม่ได้แสดง เลือกทีละไฟล์บอกมาได้ค่ะ)",
}

_REPLY_CONVERT_OK = {
    "zh": "「{filename}」转好了:{doc_type} · {rows} 行,守恒校验全过。",
    "th": "แปลง「{filename}」เสร็จแล้ว: {doc_type} · {rows} แถว ตรวจยอดผ่านทั้งหมด",
}
_REPLY_CONVERT_ISSUES = {
    "zh": "「{filename}」转好了:{doc_type} · {rows} 行,但有 {issue_count} 行对不平,已逐行点名。",
    "th": "แปลง「{filename}」เสร็จแล้ว: {doc_type} · {rows} แถว แต่มี {issue_count} แถวยอดไม่ตรง ระบุไว้ทีละแถวแล้ว",
}
_REPLY_CHECK = {
    "zh": "「{filename}」{period}:{rows} 行 · 缺号 {missing} · 重号 {dup} · 作废 {void} · 跨期 {oop} · 买家 {buyers} 家。",
    "th": "「{filename}」{period}: {rows} แถว · เลขขาด {missing} · ซ้ำ {dup} · ยกเลิก {void} · นอกงวด {oop} · ผู้ซื้อ {buyers} ราย",
}

ERRORS = {
    "steward.attachment_missing": {
        "zh": "这一轮没有可用的文件。先把料拖进来,或者点回形针传一份。",
        "th": "รอบนี้ยังไม่มีไฟล์ที่ใช้ได้ค่ะ ลากไฟล์เข้ามา หรือกดคลิปหนีบเพื่ออัปโหลดก่อนนะคะ",
    },
    "steward.attachment_ambiguous": {
        "zh": "这一轮有 {n} 份文件,我不替你猜做哪一份。说清楚是哪一份,或者一份一份来。",
        "th": "รอบนี้มี {n} ไฟล์ ไม่เดาให้ว่าจะทำไฟล์ไหนค่ะ บอกให้ชัดว่าไฟล์ไหน หรือส่งทีละไฟล์นะคะ",
    },
    "steward.attachment_unreadable": {
        "zh": "「{filename}」在服务器上读不出来了(可能已过期清理)。重新传一份吧。",
        "th": "อ่าน「{filename}」บนเซิร์ฟเวอร์ไม่ได้แล้ว (อาจถูกลบตามอายุไฟล์) อัปโหลดใหม่อีกครั้งนะคะ",
    },
    "steward.convert_rejected": {
        "zh": "「{filename}」转不出来(原因:{status})。它多半是扫描件或空文件 —— 我不会拿半截行凑一张看着挺像的表。",
        "th": "แปลง「{filename}」ไม่ได้ (เหตุผล: {status}) น่าจะเป็นไฟล์สแกนหรือไฟล์ว่าง จะไม่เอาแถวครึ่งๆ มาทำตารางให้ดูเหมือนถูกค่ะ",
    },
    "steward.report_unparsed": {
        "zh": "「{filename}」读不成销项报告,一行都没解出来。确认一下是不是报告文件?",
        "th": "อ่าน「{filename}」เป็นรายงานภาษีขายไม่ได้ ไม่ได้สักแถวค่ะ ช่วยเช็กว่าเป็นไฟล์รายงานจริงไหมคะ",
    },
    "steward.report_needs_model": {
        "zh": "「{filename}」不过模型抽不出行(表格层烂或格式不是 Excel/PDF)。"
        "我没替你调模型 —— 想读就在卡上点「读吧(会过一次模型)」,或者先把它转成 Excel 再传那份表。",
        "th": "「{filename}」ถ้าไม่เรียกโมเดลจะดึงแถวไม่ออก (ชั้นตารางเสีย หรือไม่ใช่ Excel/PDF) "
        "ยังไม่ได้เรียกโมเดลให้นะคะ ถ้าจะอ่านให้กด「อ่านเลย (จะเรียกโมเดลหนึ่งรอบ)」บนการ์ด "
        "หรือแปลงเป็น Excel ก่อนแล้วค่อยส่งไฟล์นั้นมาค่ะ",
    },
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def kind_label(kind: str, lang: str) -> str:
    return _t(KIND_LABEL.get(kind or "", KIND_LABEL[ak.UNKNOWN]), lang)


def action_label(tool: str, lang: str, *, filename: str = "") -> str:
    base = _t(TITLES.get(tool, {}), lang) or tool
    return f"{base} · {filename}" if filename else base


def receipt_title(lang: str) -> str:
    return _t(RECEIPT_TITLE, lang)


def receipt_steps(understand: str, summarize: str, lang: str) -> list[dict[str, Any]]:
    """回执卡的步骤流水:料收了、认过了,活还没派 —— 第三步如实停在「等你选」,不冒领
    「开跑了」(四态诚实:waiting_user 就该看起来像 waiting_user)。前两步的标签由 copy
    传进来,免得两处各写一遍「听懂你要什么」。"""
    return [
        {
            "id": "understand",
            "label": understand,
            "state": store.STEP_DONE,
            "detail": _t(RECEIPT_TITLE, lang),
            "links": [],
        },
        {
            "id": "detect",
            "label": _t(_RECEIPT_STEP, lang),
            "state": store.STEP_DONE,
            "detail": "",
            "links": [],
        },
        {
            "id": "summarize",
            "label": summarize,
            "state": store.STEP_QUEUED,
            "detail": _t(_AWAIT_PICK, lang),
            "links": [],
        },
    ]


def receipt_reply(counts: dict[str, int], total: int, lang: str, *, has_actions: bool) -> str:
    """回执卡的那句话。数字全部来自逐件确定性识别的计数,一个字不经模型。"""
    breakdown = " · ".join(
        f"{kind_label(kind, lang)} {n}" for kind, n in sorted(counts.items()) if n
    )
    tail = _t(_RECEIPT_PICK if has_actions else _RECEIPT_NO_ACTION, lang)
    return _t(_RECEIPT, lang).format(n=total, breakdown=breakdown, tail=tail)


def pick_file_reply(tool: str, n: int, lang: str) -> str:
    return _t(_RECEIPT_PICK_FILE, lang).format(n=n, title=_t(TITLES.get(tool, {}), lang) or tool)


def spend_confirm_reply(filename: str, lang: str) -> str:
    return _t(_SPEND_CONFIRM, lang).format(name=filename)


def spend_confirm_label(lang: str) -> str:
    return _t(_SPEND_LABEL, lang)


def note_needs_model(lang: str) -> str:
    return _t(_NOTE_NEEDS_MODEL, lang)


def receipt_more(dropped: int, lang: str) -> str:
    """按钮摆不下时如实说还有几条 —— 静默截断就是让人以为只有这几条路。"""
    return _t(_RECEIPT_MORE, lang).format(n=dropped)


def files_table(files: list[dict], lang: str) -> dict[str, Any]:
    """收到的文件清单。四态诚实:认不出的那行就写认不出,不回落成一个像样的类型名。"""
    columns = (
        ("name", {"zh": "文件", "th": "ไฟล์"}),
        ("kind", {"zh": "认成什么", "th": "เป็นเอกสารอะไร"}),
        ("pages", {"zh": "页数", "th": "จำนวนหน้า"}),
        ("note", {"zh": "说明", "th": "หมายเหตุ"}),
    )
    return {
        "kind": "table",
        "label": _t(_FILES_LABEL, lang),
        "columns": [{"key": k, "label": _t(label, lang)} for k, label in columns],
        "rows": files,
    }


def actions_block(actions: list[dict], lang: str) -> dict[str, Any]:
    return {"kind": "actions", "label": _t(_ACTIONS_LABEL, lang), "actions": actions}


def intake_link(lang: str) -> dict[str, Any]:
    """图片料在 F1 还没有对话内的识别入库,给一个真存在的落点 —— 不摆点开 404 的按钮。"""
    return {"kind": "deeplink", "label": _t(_INTAKE_LABEL, lang), "href": "/ai#/intake"}


def error(code: str, data: Optional[dict], lang: str) -> str:
    data = data or {}
    table = ERRORS.get(code)
    if not table:
        return ""
    return _t(table, lang).format(
        n=data.get("n", 0), filename=data.get("filename", ""), status=data.get("status", "")
    )


def _reply_convert(data: dict, lang: str) -> str:
    rows = int(data.get("row_count") or 0)
    issue_count = int(data.get("issue_count") or 0)
    table = _REPLY_CONVERT_OK if issue_count == 0 else _REPLY_CONVERT_ISSUES
    return _t(table, lang).format(
        filename=data.get("filename", ""),
        doc_type=kind_label(data.get("doc_type") or "", lang),
        rows=rows,
        issue_count=issue_count,
    )


def _reply_check(data: dict, lang: str) -> str:
    period = data.get("period") or ""
    return _t(_REPLY_CHECK, lang).format(
        filename=data.get("filename", ""),
        period=f" · {period}" if period else "",
        rows=data.get("row_count", 0),
        missing=data.get("missing_count", 0),
        dup=data.get("duplicate_count", 0),
        void=data.get("void_count", 0),
        oop=data.get("out_of_period_count", 0),
        buyers=data.get("buyer_count", 0),
    )


REPLIES = {
    registry.FILE_CONVERT: _reply_convert,
    registry.VAT_REPORT_CHECK: _reply_check,
}


def artifacts(tool: str, data: dict, lang: str) -> list[dict]:
    """左窗产物:转换给下载链 + 不平行点名;三查给缺号表与买家分组表。"""
    if tool == registry.FILE_CONVERT:
        return _convert_artifacts(data, lang)
    if tool == registry.VAT_REPORT_CHECK:
        return _check_artifacts(data, lang)
    return []


def _convert_artifacts(data: dict, lang: str) -> list[dict]:
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
    issues = data.get("issues") or []
    if issues:
        out.append(
            _table(
                _ISSUES_LABEL,
                issues,
                (
                    ("line_no", {"zh": "行", "th": "แถว"}),
                    ("account", {"zh": "科目", "th": "รหัสบัญชี"}),
                    ("expected", {"zh": "应为", "th": "ควรเป็น"}),
                    ("actual", {"zh": "实为", "th": "ที่อ่านได้"}),
                ),
                lang,
            )
        )
    return out


def _check_artifacts(data: dict, lang: str) -> list[dict]:
    out: list[dict] = []
    if data.get("missing"):
        out.append(
            _table(
                _MISSING_LABEL,
                data["missing"],
                (
                    ("family", {"zh": "号族", "th": "กลุ่มเลขที่"}),
                    ("missing", {"zh": "缺", "th": "ที่ขาด"}),
                ),
                lang,
            )
        )
    if data.get("buyers"):
        out.append(
            _table(
                _BUYERS_LABEL,
                data["buyers"],
                (
                    ("buyer_name", {"zh": "买家", "th": "ผู้ซื้อ"}),
                    ("tax_id", {"zh": "税号", "th": "เลขผู้เสียภาษี"}),
                    ("invoice_count", {"zh": "张数", "th": "จำนวนใบ"}),
                    ("amount_total", {"zh": "合计", "th": "รวม"}),
                ),
                lang,
            )
        )
    return out


def _table(label: dict, rows: list, columns: tuple, lang: str) -> dict[str, Any]:
    return {
        "kind": "table",
        "label": _t(label, lang),
        "columns": [{"key": k, "label": _t(text, lang)} for k, text in columns],
        "rows": [{k: r.get(k) for k, _ in columns} for r in rows],
    }
