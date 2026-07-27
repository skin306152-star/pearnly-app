# -*- coding: utf-8 -*-
"""写工具 erp_push 的文案(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因只有一个:体积闸(单文件 <500 行),不是语义分家 —— copy.py 仍是
唯一入口,reply/error/fail_reason 按工具/错误码委派到这里,调用方一律只 import copy。

写工具的文案有两条硬要求,与只读工具不同:
  ① 授权卡的标题必须一眼看出「对哪个账套做什么、影响几条」——批准键按下去就真写客户的账,
     卡上摆一串 uuid 等于让人闭眼签字;
  ② 失败面必须指路,尤其「小助手离线」和「还在写入」:后者绝不能建议重推(= 双写),
     只给作业号让人去对账。

对外一律说 Express / 小助手,不说「桥」——「桥」是我们内部对 companion 那一段链路的叫法,
会计只知道自己电脑上装了个小助手,同一句里桥与小助手并列会让她以为那是两样东西。
"""

from __future__ import annotations

from typing import Optional

DEFAULT_LANG = "zh"

_DIRECTION = {
    "purchase": {"zh": "进项", "th": "ซื้อ"},
    "sales": {"zh": "销项", "th": "ขาย"},
    "": {"zh": "方向自动判定", "th": "ระบบจะดูทิศทางให้"},
}

# 过账去向必须上卡面:同一张票按库存记 = 真扣客户库存并结转 COGS,按服务记 = 不动库存,
# 两者不可逆且互不相同。卡上不印,批准的人看不出这一批把「库存」办成了「服务」。
_POSTING_KIND = {
    "stock": {"zh": "按库存记账", "th": "ลงแบบสต๊อก"},
    "service": {"zh": "按服务记账", "th": "ลงแบบบริการ"},
    "": {"zh": "未声明过账去向", "th": "ยังไม่ระบุวิธีลงบัญชี"},
}

_CARD_TITLE = {
    "zh": "把 {doc_count} 张票推进 Express 账套 {account_set} · {direction} · {posting_kind} · {invoice_no} ฿{total_amount}",
    "th": "ส่ง {doc_count} ใบเข้า Express ชุดบัญชี {account_set} · {direction} · {posting_kind} · {invoice_no} ฿{total_amount}",
}

_REPLY_DONE = {
    "zh": "推好了:{invoice_no} 已写进账套 {account_set}({doctype} · ฿{total_amount}){docnum}。",
    "th": "ส่งเข้าเรียบร้อย: {invoice_no} เข้าชุดบัญชี {account_set} แล้ว ({doctype} · ฿{total_amount}){docnum}",
}
_DOCNUM = {"zh": ",Express 单号 {n}", "th": " เลขที่ในระบบ {n}"}

# 任务级失败原因的写工具版本(copy.fail_reason 按 tool 覆盖只读版)。
# 只读工具超时可以说"再说一次让我重跑",写工具绝不能——那句话会让会计把同一张票推两遍。
FAIL_REASON = {
    "steward.timeout": {
        "zh": "等了 {seconds} 秒没有结果,已停止。不要重推 —— Express 可能已写入,先去「集成 · 推送日志」看这张票的状态。",
        "th": "รอเกิน {seconds} วินาทีแล้วไม่มีผล จึงหยุด อย่าส่งซ้ำ — Express อาจเขียนเข้าไปแล้ว ดูสถานะใบนี้ที่「การเชื่อมต่อ · ประวัติการส่ง」ก่อน",
    },
    "steward.worker_lost": {
        "zh": "执行中断(服务重启),这条没跑完。不要重推 —— 先去「集成 · 推送日志」确认这张票有没有进账套。",
        "th": "งานถูกขัดจังหวะ (ระบบรีสตาร์ต) ยังทำไม่เสร็จ อย่าส่งซ้ำ — ตรวจที่「การเชื่อมต่อ · ประวัติการส่ง」ก่อนว่าใบนี้เข้าชุดบัญชีแล้วหรือยัง",
    },
    "steward.task_crashed": {
        "zh": "执行时出错,这条没跑完。不要重推 —— 出错可能在投单之后,先去「集成 · 推送日志」确认这张票有没有进账套。",
        "th": "เกิดข้อผิดพลาดระหว่างทำงาน ยังทำไม่เสร็จ อย่าส่งซ้ำ — ข้อผิดพลาดอาจเกิดหลังส่งงานแล้ว ตรวจที่「การเชื่อมต่อ · ประวัติการส่ง」ก่อนว่าใบนี้เข้าชุดบัญชีแล้วหรือยัง",
    },
    "steward.cancelled": {
        "zh": "你取消了这条任务。若已批准过,Express 可能已在写入 —— 不要重推,去「集成 · 推送日志」看这张票的最终状态。",
        "th": "คุณยกเลิกงานนี้แล้ว ถ้าอนุมัติไปก่อนหน้านี้ Express อาจกำลังเขียนอยู่ อย่าส่งซ้ำ ดูสถานะสุดท้ายที่「การเชื่อมต่อ · ประวัติการส่ง」",
    },
}

ERRORS = {
    "steward.erp_endpoint_missing": {
        "zh": "还没连 Express 账套,这张推不了。去「集成」页建好 Express 连接(要选目标账套)再说一次。",
        "th": "ยังไม่ได้เชื่อมชุดบัญชี Express จึงส่งไม่ได้ ตั้งการเชื่อมต่อ Express ในหน้า「การเชื่อมต่อ」(ต้องเลือกชุดบัญชีปลายทาง) แล้วสั่งใหม่",
    },
    "steward.account_set_mismatch": {
        "zh": "你说的账套是「{asked}」,连接配的是「{account_set}」。系统不会自行改账套,去「集成」页改连接,或换个说法。",
        "th": 'คุณบอกชุดบัญชี "{asked}" แต่การเชื่อมต่อนี้ตั้งไว้ที่ "{account_set}" ระบบจะไม่เปลี่ยนชุดบัญชีให้เอง แก้ที่หน้า「การเชื่อมต่อ」หรือพิมพ์ใหม่',
    },
    "steward.invoice_not_found": {
        "zh": "识别记录里找不到「{keyword}」这张票。换个说法(单号/店名/文件名),或先查这张票。",
        "th": 'ไม่พบใบ "{keyword}" ในเอกสารที่สแกน บอกเลขที่ใบ/ชื่อร้าน/ชื่อไฟล์ หรือค้นหาใบนี้ก่อน',
    },
    "steward.invoice_ambiguous": {
        "zh": "「{keyword}」对上了 {n} 张票:{names}。指明是哪一张,单号最准。",
        "th": 'คำว่า "{keyword}" ตรงกับ {n} ใบ: {names} ระบุว่าใบไหน บอกเลขที่ใบจะตรงที่สุด',
    },
    "steward.invoice_changed": {
        "zh": "这张票在等你批准期间被改过({field}),授权作废,未执行任何操作。重新说一次再批。",
        "th": "ใบนี้ถูกแก้ระหว่างรออนุมัติ ({field}) ใบอนุมัติจึงเป็นโมฆะ ยังไม่ได้ทำอะไรเลย สั่งใหม่แล้วอนุมัติอีกครั้ง",
    },
    "steward.erp_already_pushed": {
        "zh": "{invoice_no} 已在 {pushed_at} 推进账套 {account_set},不会再推第二遍(同一张票记两遍就是重复入账)。结果见「集成 · 推送日志」。",
        "th": "{invoice_no} ส่งเข้าชุดบัญชี {account_set} ไปแล้วเมื่อ {pushed_at} จะไม่ส่งซ้ำ (ใบเดียวลงสองครั้ง = บันทึกซ้ำ) ดูผลได้ที่「การเชื่อมต่อ · ประวัติการส่ง」",
    },
    "steward.erp_direction_conflict": {
        "zh": "你说按「{asked_label}」推,按税号比对出来是「{detected_label}」。方向反了整张票的税会记到另一侧,系统不会自行更改,确认后再说一次。",
        "th": "คุณบอกให้ลงเป็น「{asked_label}」แต่เทียบเลขผู้เสียภาษีแล้วได้「{detected_label}」ถ้าทิศทางกลับด้าน ภาษีทั้งใบจะไปลงอีกฝั่ง ระบบจะไม่แก้ให้เอง ตรวจสอบแล้วสั่งใหม่",
    },
    "steward.write_tool_failed": {
        "zh": "这条没跑完(错误码 {code}),无法确认 Express 写没写进去。不要重推 —— 先去「集成 · 推送日志」看这张票的状态,确认没进账套再说一次。",
        "th": "งานนี้ทำไม่สำเร็จ (รหัส {code}) และยังไม่แน่ใจว่า Express เขียนเข้าไปแล้วหรือยัง อย่าส่งซ้ำ — ดูสถานะใบนี้ที่「การเชื่อมต่อ · ประวัติการส่ง」ก่อน ถ้ายังไม่เข้าค่อยสั่งใหม่",
    },
    "steward.erp_push_blocked": {
        "zh": "这张票过不了推送前的体检({reason}),没有写进账套。去「集成 · 推送日志」看这一项要补什么。",
        "th": "ใบนี้ไม่ผ่านการตรวจก่อนส่ง ({reason}) จึงยังไม่ได้เขียนเข้าชุดบัญชี ดูที่「การเชื่อมต่อ · ประวัติการส่ง」ว่าต้องเติมอะไร",
    },
    "steward.bridge_offline": {
        "zh": "小助手离线,账套 {account_set} 现在写不进,未执行任何操作。在「集成 · ERP 桥」确认小助手在线(需「写」权限)后再说一次。",
        "th": "ตัวช่วยออฟไลน์ ยังเขียนชุดบัญชี {account_set} ไม่ได้ และยังไม่ได้ทำอะไร ตรวจที่「การเชื่อมต่อ · สะพาน ERP」ว่าตัวช่วยออนไลน์ (ต้องเป็นบทบาท「เขียน」) แล้วสั่งใหม่",
    },
    "steward.erp_push_rejected": {
        "zh": "这张单被退回({reason}),没有写进账套。多为票面数据或账套配置不符,详情见「集成 · 推送日志」。",
        "th": "ใบนี้ถูกตีกลับ ({reason}) จึงยังไม่ได้เขียนเข้าชุดบัญชี ส่วนใหญ่เป็นข้อมูลในใบหรือการตั้งค่าชุดบัญชีไม่ตรงกัน ดูรายละเอียดที่「การเชื่อมต่อ · ประวัติการส่ง」",
    },
    "steward.erp_push_failed": {
        "zh": "写入 Express 失败({reason}),作业号 {job_id}。查清原因后再说一次,不要在没查清前重推。",
        "th": "เขียนเข้า Express ไม่สำเร็จ ({reason}) เลขงาน {job_id} แก้ต้นเหตุแล้วค่อยสั่งใหม่ อย่าส่งซ้ำก่อนตรวจสอบ",
    },
    "steward.erp_push_expired": {
        "zh": "没有小助手来领这张单,已过期(作业号 {job_id})。多为小助手一直不在线,上线后再说一次。",
        "th": "ไม่มีตัวช่วยมารับงานนี้ หมดอายุแล้ว (เลขงาน {job_id}) ส่วนใหญ่เพราะตัวช่วยไม่ได้ออนไลน์ เมื่อออนไลน์แล้วค่อยสั่งใหม่",
    },
    "steward.erp_push_pending": {
        "zh": "Express 还在写这张单(作业号 {job_id}),等不到结果先回复。不要重推 —— 过几分钟去「集成 · 推送日志」看这张票的最终状态。",
        "th": "Express ยังเขียนใบนี้อยู่ (เลขงาน {job_id}) รอผลไม่ทันจึงตอบก่อน อย่าส่งซ้ำ — อีกสักครู่ดูสถานะสุดท้ายที่「การเชื่อมต่อ · ประวัติการส่ง」",
    },
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def direction_label(direction: Optional[str], lang: str) -> str:
    return _t(_DIRECTION.get(str(direction or ""), _DIRECTION[""]), lang)


def posting_kind_label(posting_kind: Optional[str], lang: str) -> str:
    return _t(_POSTING_KIND.get(str(posting_kind or ""), _POSTING_KIND[""]), lang)


def card_title(facts: dict, lang: str) -> str:
    """授权卡标题:对哪个账套、做什么、影响几条、多少钱(数字全来自接地结果,模板不算账)。"""
    return _t(_CARD_TITLE, lang).format(
        doc_count=facts.get("doc_count", 1),
        account_set=facts.get("account_set", ""),
        direction=direction_label(facts.get("direction"), lang),
        posting_kind=posting_kind_label(facts.get("posting_kind"), lang),
        invoice_no=facts.get("invoice_no") or "-",
        total_amount=facts.get("total_amount", "0.00"),
    )


def reply(data: dict, lang: str) -> str:
    """推成功的一句人话。Express 单号有才说 —— 没拿到就不编一个(状态诚实)。"""
    docnum = data.get("docnum") or ""
    return _t(_REPLY_DONE, lang).format(
        invoice_no=data.get("ref_no") or "-",
        account_set=data.get("account_set", ""),
        doctype=data.get("doctype", ""),
        total_amount=data.get("total_amount", "0.00"),
        docnum=_t(_DOCNUM, lang).format(n=docnum) if docnum else "",
    )


def error(code: str, data: dict, lang: str) -> str:
    """写工具的错误 → 人话 + 下一步。候选票列表原样列出来让人挑,不替他选一张。"""
    candidates = data.get("candidates") or []
    names = ", ".join(
        " ".join(x for x in (c.get("invoice_no"), c.get("seller_name")) if x)
        for c in candidates[:5]
    )
    return _t(ERRORS[code], lang).format(
        keyword=data.get("keyword", ""),
        n=data.get("total", len(candidates)),
        names=names,
        asked=data.get("asked", ""),
        account_set=data.get("account_set", ""),
        field=data.get("field", ""),
        reason=data.get("reason", ""),
        job_id=data.get("job_id", ""),
        code=code,
        invoice_no=data.get("invoice_no", ""),
        pushed_at=data.get("pushed_at", ""),
        # 方向冲突要说人话("进项/销项"),不是把机器词 purchase/sales 甩给会计。
        asked_label=direction_label(data.get("asked"), lang),
        detected_label=direction_label(data.get("detected"), lang),
    )
