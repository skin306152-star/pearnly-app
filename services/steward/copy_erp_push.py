# -*- coding: utf-8 -*-
"""写工具 erp_push 的文案(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因只有一个:体积闸(单文件 <500 行),不是语义分家 —— copy.py 仍是
唯一入口,reply/error/fail_reason 按工具/错误码委派到这里,调用方一律只 import copy。

写工具的文案有两条硬要求,与只读工具不同:
  ① 授权卡上摆的是会计看得懂的事实(票号/方向/记账方式/金额),不是工具槽名 —— 批准键
     按下去就真写客户的账,把 direction=sales、history_id=<uuid> 摆给人签等于让她闭眼签;
  ② 失败面必须指路,尤其「小助手离线」和「还在写入」:后者绝不能建议重推(= 双写),
     只给作业号让人去对账。

对外一律说 Express / 小助手,不说「桥」——「桥」是我们内部对 companion 那一段链路的叫法,
会计只知道自己电脑上装了个小助手,同一句里桥与小助手并列会让她以为那是两样东西。
指路只写侧栏上真有的那一项(「推送日志」/「集成」),不拼父子路径:推送日志 2026-07-01
已从集成页搬成独立导航项,照「集成 · 推送日志」找找不到;「集成 · ERP 桥」更是从来没有过。
tests/unit/test_ui_copy_signposts.py 拿真侧栏标记逐条核对。
"""

from __future__ import annotations

from typing import Optional

from services.erp.express_push.posting_profile import ESCALATE_REASON_PREFIX
from services.steward.copy_lang import t as _t

# ฿ 的墨迹比字宽宽半像素,紧跟数字会糊成一团(粗体大字最明显)。垫一个窄空格分开。
BAHT = "฿\u2009"  # ฿ + 窄空格 U+2009

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
    "zh": "把 {doc_count} 张票推进 Express 账套 {account_set}",
    "th": "ส่ง {doc_count} ใบเข้า Express ชุดบัญชี {account_set}",
}

# 卡面明细行的标签(顺序即行序)。account_set 已在标题里,不再重复一行;history_id 一律不上卡
# —— 会计对不上一串 uuid,摆出来只会让她跳过整块参数直接点批准。
_ARG_LABELS = (
    ("invoice_no", {"zh": "票号", "th": "เลขที่ใบ"}),
    ("seller_name", {"zh": "对方", "th": "คู่ค้า"}),
    ("direction", {"zh": "方向", "th": "ทิศทาง"}),
    ("posting_kind", {"zh": "记账方式", "th": "วิธีลงบัญชี"}),
    ("total_amount", {"zh": "金额", "th": "จำนวนเงิน"}),
)

_REPLY_DONE = {
    "zh": "推好了:{invoice_no} 已写进账套 {account_set}({doctype} · "
    + BAHT
    + "{total_amount}){docnum}。",
    "th": "ส่งเข้าเรียบร้อย: {invoice_no} เข้าชุดบัญชี {account_set} แล้ว ({doctype} · "
    + BAHT
    + "{total_amount}){docnum}",
}
_DOCNUM = {"zh": ",Express 单号 {n}", "th": " เลขที่ในระบบ {n}"}

# 任务级失败原因的写工具版本(copy.fail_reason 按 tool 覆盖只读版)。
# 只读工具超时可以说"再说一次让我重跑",写工具绝不能——那句话会让会计把同一张票推两遍。
FAIL_REASON = {
    "steward.timeout": {
        "zh": "等了 {seconds} 秒没有结果,已停止。不要重推 —— Express 可能已写入,先去「推送日志」看这张票的状态。",
        "th": "รอเกิน {seconds} วินาทีแล้วไม่มีผล จึงหยุด อย่าส่งซ้ำ — Express อาจเขียนเข้าไปแล้ว ดูสถานะใบนี้ที่「บันทึกการส่ง」ก่อน",
    },
    "steward.worker_lost": {
        "zh": "执行中断(服务重启),这条没跑完。不要重推 —— 先去「推送日志」确认这张票有没有进账套。",
        "th": "งานถูกขัดจังหวะ (ระบบรีสตาร์ต) ยังทำไม่เสร็จ อย่าส่งซ้ำ — ตรวจที่「บันทึกการส่ง」ก่อนว่าใบนี้เข้าชุดบัญชีแล้วหรือยัง",
    },
    "steward.task_crashed": {
        "zh": "执行时出错,这条没跑完。不要重推 —— 出错可能在投单之后,先去「推送日志」确认这张票有没有进账套。",
        "th": "เกิดข้อผิดพลาดระหว่างทำงาน ยังทำไม่เสร็จ อย่าส่งซ้ำ — ข้อผิดพลาดอาจเกิดหลังส่งงานแล้ว ตรวจที่「บันทึกการส่ง」ก่อนว่าใบนี้เข้าชุดบัญชีแล้วหรือยัง",
    },
    "steward.cancelled": {
        "zh": "你取消了这条任务。若已批准过,Express 可能已在写入 —— 不要重推,去「推送日志」看这张票的最终状态。",
        "th": "คุณยกเลิกงานนี้แล้ว ถ้าอนุมัติไปก่อนหน้านี้ Express อาจกำลังเขียนอยู่ อย่าส่งซ้ำ ดูสถานะสุดท้ายที่「บันทึกการส่ง」",
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
        "zh": "{invoice_no} 已在 {pushed_at} 推进账套 {account_set},不会再推第二遍(同一张票记两遍就是重复入账)。结果见「推送日志」。",
        "th": "{invoice_no} ส่งเข้าชุดบัญชี {account_set} ไปแล้วเมื่อ {pushed_at} จะไม่ส่งซ้ำ (ใบเดียวลงสองครั้ง = บันทึกซ้ำ) ดูผลได้ที่「บันทึกการส่ง」",
    },
    "steward.erp_direction_conflict": {
        "zh": "你说按「{asked_label}」推,按税号比对出来是「{detected_label}」。方向反了整张票的税会记到另一侧,系统不会自行更改,确认后再说一次。",
        "th": "คุณบอกให้ลงเป็น「{asked_label}」แต่เทียบเลขผู้เสียภาษีแล้วได้「{detected_label}」ถ้าทิศทางกลับด้าน ภาษีทั้งใบจะไปลงอีกฝั่ง ระบบจะไม่แก้ให้เอง ตรวจสอบแล้วสั่งใหม่",
    },
    "steward.write_tool_failed": {
        "zh": "这条没跑完(错误码 {code}),无法确认 Express 写没写进去。不要重推 —— 先去「推送日志」看这张票的状态,确认没进账套再说一次。",
        "th": "งานนี้ทำไม่สำเร็จ (รหัส {code}) และยังไม่แน่ใจว่า Express เขียนเข้าไปแล้วหรือยัง อย่าส่งซ้ำ — ดูสถานะใบนี้ที่「บันทึกการส่ง」ก่อน ถ้ายังไม่เข้าค่อยสั่งใหม่",
    },
    "steward.erp_push_blocked": {
        "zh": "这张票过不了推送前的体检({reason}),没有写进账套。去「推送日志」看这一项要补什么。",
        "th": "ใบนี้ไม่ผ่านการตรวจก่อนส่ง ({reason}) จึงยังไม่ได้เขียนเข้าชุดบัญชี ดูที่「บันทึกการส่ง」ว่าต้องเติมอะไร",
    },
    "steward.bridge_offline": {
        "zh": "小助手离线,{account_set} 没有写入。小助手上线后再说一次。",
        "th": "ตัวช่วยออฟไลน์ ยังไม่ได้เขียนเข้าชุดบัญชี {account_set} สั่งใหม่เมื่อตัวช่วยออนไลน์",
    },
    "steward.erp_push_rejected": {
        "zh": "这张单被退回({reason}),没有写进账套。多为票面数据或账套配置不符,详情见「推送日志」。",
        "th": "ใบนี้ถูกตีกลับ ({reason}) จึงยังไม่ได้เขียนเข้าชุดบัญชี ส่วนใหญ่เป็นข้อมูลในใบหรือการตั้งค่าชุดบัญชีไม่ตรงกัน ดูรายละเอียดที่「บันทึกการส่ง」",
    },
    "steward.erp_push_failed": {
        "zh": "写入 Express 失败({reason}),作业号 {job_id}。查清原因后再说一次,不要在没查清前重推。",
        "th": "เขียนเข้า Express ไม่สำเร็จ ({reason}) เลขงาน {job_id} แก้ต้นเหตุแล้วค่อยสั่งใหม่ อย่าส่งซ้ำก่อนตรวจสอบ",
    },
    # 唯一一条敢说「再说一次」的写失败:桥在备份之前就快拒(或写到一半拿不到锁已回滚),
    # 一个字节都没写,而挡路的东西会计自己抬手就能挪开。别说「稍后自动重试」—— 桥直写这条
    # 路没有任何后台会替她再推一次(erp_push_tool._log_push 不设 next_retry_at),
    # 那句话会让她一直等一个不会来的重试。
    "steward.erp_push_account_busy": {
        "zh": "有人正在 Express 里开着账套 {account_set},这张一个字节都没写进去。系统不会自己再推 —— 把 Express 里这个账套关掉,再跟我说一次。",
        "th": "มีคนเปิดชุดบัญชี {account_set} ค้างไว้ใน Express ใบนี้จึงยังไม่ได้เขียนเข้าไปแม้แต่ไบต์เดียว ระบบจะไม่ส่งซ้ำให้เอง — ปิดชุดบัญชีนี้ใน Express แล้วบอกผมอีกครั้ง",
    },
    "steward.erp_push_expired": {
        "zh": "没有小助手来领这张单,已过期(作业号 {job_id})。多为小助手一直不在线,上线后再说一次。",
        "th": "ไม่มีตัวช่วยมารับงานนี้ หมดอายุแล้ว (เลขงาน {job_id}) ส่วนใหญ่เพราะตัวช่วยไม่ได้ออนไลน์ เมื่อออนไลน์แล้วค่อยสั่งใหม่",
    },
    "steward.erp_push_uncertain": {
        "zh": "小助手领走了这张单({ref_no})却没回结果:可能已经写进 Express,也可能没有,系统不会自动再推。先去 Express 看有没有这张,没有再说一次;作业号 {job_id}。",
        "th": "ตัวช่วยรับงานใบนี้ไป ({ref_no}) แต่ไม่ได้ส่งผลกลับมา: อาจเขียนเข้า Express แล้วหรืออาจยังไม่ได้ ระบบจะไม่ส่งซ้ำให้เอง ไปดูใน Express ก่อนว่ามีใบนี้หรือยัง ถ้ายังไม่มีค่อยสั่งใหม่ เลขงาน {job_id}",
    },
    "steward.erp_push_pending": {
        "zh": "Express 还在写这张单(作业号 {job_id}),等不到结果先回复。不要重推 —— 过几分钟去「推送日志」看这张票的最终状态。",
        "th": "Express ยังเขียนใบนี้อยู่ (เลขงาน {job_id}) รอผลไม่ทันจึงตอบก่อน อย่าส่งซ้ำ — อีกสักครู่ดูสถานะสุดท้ายที่「บันทึกการส่ง」",
    },
    "steward.posting_kind_write_failed": {
        "zh": "这次说的过账去向没能存到票上,推送没有执行。稍后再说一次;如果一直不行,去「推送日志」反馈。",
        "th": "บันทึกวิธีลงบัญชีที่บอกไว้ลงในใบไม่สำเร็จ จึงยังไม่ได้ส่งใบนี้ ลองสั่งใหม่อีกครั้ง ถ้ายังไม่ได้ให้แจ้งที่「บันทึกการส่ง」",
    },
}


# 被拦原因是「没声明过账去向」(posting_profile.ESCALATE_REASON_PREFIX 族)时,补一句怎么
# 解开 —— 别的拦截原因(账套没配 / 单据防呆没过 / GLACC 没有科目组...)加这句是瞎指路,
# 只在这一族追加(error() 按 reason 前缀判断)。
_BLOCKED_POSTING_COACH = {
    "zh": "直接告诉我「按库存过账」或「按服务过账」,再推一次就行。",
    "th": "บอกผมว่า「ลงแบบสต๊อก」หรือ「ลงแบบบริการ」แล้วสั่งส่งใหม่ได้เลย",
}


def direction_label(direction: Optional[str], lang: str) -> str:
    return _t(_DIRECTION.get(str(direction or ""), _DIRECTION[""]), lang)


def posting_kind_label(posting_kind: Optional[str], lang: str) -> str:
    return _t(_POSTING_KIND.get(str(posting_kind or ""), _POSTING_KIND[""]), lang)


def card_title(facts: dict, lang: str) -> str:
    """授权卡标题:对哪个账套推几张(票面明细由 arg_rows 逐行摆,标题不再复述一遍)。"""
    return _t(_CARD_TITLE, lang).format(
        doc_count=facts.get("doc_count", 1),
        account_set=facts.get("account_set", ""),
    )


def arg_rows(args: dict, lang: str) -> list[dict]:
    """卡面明细行:机器槽名 → 会计的说法,机器值 → 人话(sales→销项,stock→按库存记账)。

    值为空的行整行不摆 —— 一行「对方 —」不提供任何信息,只是让人多扫一行。
    """
    values = {
        "direction": direction_label(args.get("direction"), lang),
        "posting_kind": posting_kind_label(args.get("posting_kind"), lang),
        "total_amount": BAHT + str(args.get("total_amount") or "0.00"),
    }
    rows = []
    for key, label in _ARG_LABELS:
        value = values.get(key) or str(args.get(key) or "").strip()
        if value:
            rows.append({"label": _t(label, lang), "value": value})
    return rows


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
    text = _t(ERRORS[code], lang).format(
        keyword=data.get("keyword", ""),
        n=data.get("total", len(candidates)),
        names=names,
        asked=data.get("asked", ""),
        account_set=data.get("account_set", ""),
        field=data.get("field", ""),
        reason=data.get("reason", ""),
        job_id=data.get("job_id", ""),
        code=code,
        # 投桥那一路的票号叫 ref_no(载荷字段名),接地失败那一路叫 invoice_no(记录列名)。
        # 两个都摆出来 —— 少一个,句子里的占位符就会 KeyError 把整条回复炸掉。
        ref_no=data.get("ref_no", ""),
        invoice_no=data.get("invoice_no", ""),
        pushed_at=data.get("pushed_at", ""),
        # 方向冲突要说人话("进项/销项"),不是把机器词 purchase/sales 甩给会计。
        asked_label=direction_label(data.get("asked"), lang),
        detected_label=direction_label(data.get("detected"), lang),
    )
    if code == "steward.erp_push_blocked" and str(data.get("reason") or "").startswith(
        ESCALATE_REASON_PREFIX
    ):
        text += " " + _t(_BLOCKED_POSTING_COACH, lang)
    return text
