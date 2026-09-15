# -*- coding: utf-8 -*-
"""Native payment field questions shared by the booking conversation.

渠道银行目录有两副面孔:目录有行 → 选按钮(LINE quick reply);目录**权威为空** → 回到改前的
可填写文本流程(银行名称 + 原生必要资料),不再报「读取失败」。读取失败另有路径
(master_contract.snapshot_rows 抛 MasterSyncError → master_problem 卡),不许在这里冒充空目录。
"""

# 一行资料里的字段分隔符提示:与 services/line_dms/text_fields.py 支持的规则同一套
# (半/全角竖线、英文/中文逗号、顿号、斜杠、居中点、留白点号)。文案只列最常用的四种,
# 不再声称「只能用 |」—— 用户怎么写都能收,只在真的拆不出来时才重问。
TXT_SEP_HINT = "คั่นช่องด้วย | , / หรือ ·"

# 该渠道银行目录权威为空时的兼容问法:多问一项银行名称(hidden bank id 允许为空)。
TXT_ASK_CHEQUE_REF_MANUAL = (
    "พิมพ์ เลขที่เช็ค | เล่มที่เช็ค | ชื่อธนาคาร เช่น 123456 | 01 | KBank\n" + TXT_SEP_HINT
)
TXT_ASK_CARD_REF_MANUAL = "พิมพ์ ชื่อธนาคาร | ประเภทบัตร เช่น KBank | VISA\n" + TXT_SEP_HINT


def ask_pay_ref(channel: str, manual_bank: bool = False) -> dict:
    """渠道补充信息文案:分类查 CHANNEL_EXTRA_SHAPE 单表,不再各处硬编码渠道子集。

    manual_bank 是该渠道银行目录权威为空(手工填名称)时的问法。"""
    from services.line_dms.qa_cards import (
        _msg,
        TXT_ASK_CARD_REF,
        TXT_ASK_CHEQUE_REF,
        TXT_ASK_OTHER_REF,
    )
    from services.line_dms.qa_util import CHANNEL_EXTRA_SHAPE

    if CHANNEL_EXTRA_SHAPE.get(channel) != "ref":
        return _msg(TXT_ASK_OTHER_REF)
    if manual_bank:
        return _msg(TXT_ASK_CARD_REF_MANUAL if channel == "card" else TXT_ASK_CHEQUE_REF_MANUAL)
    return _msg(TXT_ASK_CARD_REF if channel == "card" else TXT_ASK_CHEQUE_REF)


def ask_payment_bank(banks: list, page: int = 0, channel: str = "") -> dict:
    from services.line_dms.qa_cards import _msg, _option_text, _pick_rows, ask_pay_ref
    from services.erp.mrerp_dms_company_banks import company_bank_label, sort_bank_rows

    banks = sort_bank_rows(banks)
    if not banks:
        return ask_pay_ref(channel, manual_bank=True)
    return _msg(
        _option_text("เลือกธนาคาร", banks, company_bank_label, page),
        _pick_rows(banks, "paybank", company_bank_label, page),
    )
