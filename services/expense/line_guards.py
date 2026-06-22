# -*- coding: utf-8 -*-
"""记账前的确定性「拦截守卫」(在 L1 记账之前判·命中即不入账)。

单一职责:把"绝不能当普通费用记"的输入挡在记账机器之前 —— 合规欺诈 / 外币 / 押金。
都是零成本关键词判定,供 replies.detect_smalltalk 在最前调用,返回对应 reply 池 kind。
"""

from __future__ import annotations

# 欺诈(合规红线):伪造票据/篡改金额/逃税。伪造词须与单据词同现 → 避免「买假货」「假设」误伤。
_FRAUD_DOC = "ใบเสร็จ ใบกำกับ บิล เอกสาร ยอด receipt invoice 发票 票据 单据 账".split()
_FRAUD_FAKE = "ปลอม fake forge fabricate falsify 假 伪造 做假".split()
_FRAUD_EVADE = "โกงภาษี เลี่ยงภาษี หนีภาษี evadetax taxevasion 逃税 偷税 漏税 避税".split()
# 外币(非 THB):符号/泰中文名 + 代码(分词避免「used」含「usd」误伤)。
_FX_SYM = "$ ¥ € £ ₩ ดอลลาร์ ยูโร เยน หยวน วอน ริงกิต 美元 欧元 日元 韩元 人民币".split()
_FX_CODE = {"usd", "eur", "cny", "jpy", "krw", "rmb", "sgd", "myr", "hkd"}
# 押金/定金/保证金:不是普通费用。ดาวน์ 用「เงินดาวน์」避免「ดาวน์โหลด」下载误伤。
_DEPOSIT = ("มัดจำ", "เงินดาวน์", "เงินประกัน", "deposit", "押金", "订金", "定金", "保证金")
# 倒签造票:创建动词 + 单据词 + 「ย้อนหลัง倒签」三者同现 = 造倒签票(欺诈)。「บันทึกย้อนหลัง 补记
# 真实过去支出」用 บันทึก(不在创建动词)→ 不拦照记。区分点 = 创建动词(造票) vs 记录动词(补记)。
_DOC_CREATE = "สร้าง ทำ ออก แก้".split()
_BACKDATE = "ย้อนหลัง 倒签 补开".split()
# 未来日期(尚未发生的支出不静默记·应确认):带金额才拦(问句「พรุ่งนี้ว่างไหม」不拦)。
_FUTURE = "พรุ่งนี้ มะรืน ปีหน้า เดือนหน้า อาทิตย์หน้า สัปดาห์หน้า 明天 后天 明年 下个月 下周 tomorrow".split()


def _has_digit(s: str) -> bool:
    return any(c.isdigit() for c in s or "")


def is_fraud_request(text: str) -> bool:
    """伪造单据/篡改金额/逃税/倒签造票请求?(合规红线)。伪造词须与单据词同现,避免买假货误伤。"""
    low = "".join((text or "").lower().split())
    if any(k in low for k in _FRAUD_EVADE):
        return True
    if any(w in low for w in _FRAUD_FAKE) and any(d in low for d in _FRAUD_DOC):
        return True
    # 倒签造票:创建动词 + 单据 + 倒签(「สร้างบิลย้อนหลัง」即便带金额也拒·区别于 บันทึก 补记)。
    return (
        any(b in low for b in _BACKDATE)
        and any(v in low for v in _DOC_CREATE)
        and any(d in low for d in _FRAUD_DOC)
    )


def is_future_dated(text: str) -> bool:
    """未来日期 + 金额?(พรุ่งนี้/ปีหน้า…)→ 尚未发生的支出不静默记·先确认。"""
    low = (text or "").lower()
    return _has_digit(low) and any(w in low for w in _FUTURE)


def is_fx(text: str) -> bool:
    """外币金额(非 THB)?符号/名/代码 + 数字 → 不静默把外币数字当 THB 记。"""
    s = text or ""
    if not _has_digit(s):
        return False
    if any(t in s for t in _FX_SYM):
        return True
    toks = set(s.lower().replace(",", " ").replace(".", " ").split())
    return bool(toks & _FX_CODE)


def is_deposit(text: str) -> bool:
    """押金/定金请求?(带数字)→ 押金非普通费用·澄清不静默入账。"""
    low = (text or "").lower()
    return _has_digit(low) and any(t.lower() in low for t in _DEPOSIT)
