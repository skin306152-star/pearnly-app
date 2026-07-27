# -*- coding: utf-8 -*-
"""现场算账工具的文案(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因同 copy_close:体积闸(单文件 <500 行),不是语义分家 —— copy.py
仍是唯一入口,tool_title / reply / error 按工具委派到这里。

一句话答复要把「按什么算的」一并说出来:税率、基准(把哪个数当成含税/未含税)都印在答复里。
只报三个数会让会计无从判断我是不是把方向搞反了 —— 方向反了答案照样是漂亮的两位小数。
"""

from __future__ import annotations

from services.steward import registry, tools_calc

DEFAULT_LANG = "zh"

TITLES = {registry.VAT_CALC: {"zh": "算 VAT", "th": "คำนวณ VAT"}}

_BASIS_LABEL = {
    tools_calc.BASIS_INCLUSIVE: {"zh": "按含税价算", "th": "คิดจากราคารวม VAT"},
    tools_calc.BASIS_EXCLUSIVE: {"zh": "按税前价算", "th": "คิดจากราคาก่อน VAT"},
}

_REPLY = {
    "zh": "{basis}:税前 ฿{base} + VAT {rate}% ฿{vat} = 含税 ฿{total}。{wht}",
    "th": "{basis}: ก่อนภาษี ฿{base} + VAT {rate}% ฿{vat} = รวม ฿{total} {wht}",
}
_WHT = {
    "zh": "预扣 {rate}% ฿{wht},实付 ฿{net}。",
    "th": "หัก ณ ที่จ่าย {rate}% ฿{wht} จ่ายจริง ฿{net}",
}

# 表格行名(左窗产物)。行名与答复用同一套词,两处对不上会让人以为是两笔账。
ROW_LABEL = {
    "base": {"zh": "税前", "th": "ก่อนภาษี"},
    "vat": {"zh": "VAT {rate}%", "th": "VAT {rate}%"},
    "total": {"zh": "含税合计", "th": "รวมทั้งสิ้น"},
    "wht": {"zh": "预扣 {rate}%", "th": "หัก ณ ที่จ่าย {rate}%"},
    "net_payable": {"zh": "实付", "th": "จ่ายจริง"},
}
_ROW_RATE_KEY = {"vat": "vat_rate", "wht": "wht_rate"}  # 行名里要印「几个点」的那两行

ERRORS = {
    tools_calc.ERR_AMOUNT_UNREADABLE: {
        "zh": "「{raw}」读不出金额,填数字,例如「10700 含税」。",
        "th": 'อ่านจำนวนเงิน "{raw}" ไม่ออก กรอกเป็นตัวเลข เช่น「10700 รวม VAT」',
    },
    tools_calc.ERR_BASIS_UNCLEAR: {
        "zh": "฿{amount} 含税了吗?",
        "th": "฿{amount} รวม VAT แล้วหรือยัง",
    },
    # 该扣几个点是税务判断不是算账(见 registry 的 wht_rate 槽),所以只请她填数字、
    # 不给缺省值 —— 但这条设计不必写进文案里表功。
    tools_calc.ERR_RATE_UNREADABLE: {
        "zh": "预扣税率「{raw}」读不出,填数字,例如 3%。",
        "th": 'อัตราหัก ณ ที่จ่าย "{raw}" อ่านไม่ออก กรอกเป็นตัวเลข เช่น 3%',
    },
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def vat_calc(data: dict, lang: str) -> str:
    """一句话答复。数字全部取自 data,模板只填空(模型不碰任何一位)。"""
    wht = ""
    if data.get("wht") is not None:
        wht = _t(_WHT, lang).format(
            rate=data.get("wht_rate", ""),
            wht=data.get("wht", "0.00"),
            net=data.get("net_payable", "0.00"),
        )
    return _t(_REPLY, lang).format(
        basis=_t(_BASIS_LABEL.get(data.get("basis") or "", {}), lang),
        base=data.get("base", "0.00"),
        rate=data.get("vat_rate", ""),
        vat=data.get("vat", "0.00"),
        total=data.get("total", "0.00"),
        wht=wht,
    )


def breakdown_rows(data: dict, lang: str) -> list[dict]:
    """左窗表格的行(item/amount 两列 · 与既有 columns+dict 行契约同形)。

    没有的数整行不出现:会计没报税率时印一行「预扣 0.00」等于替她定了率是 0。
    """
    rows = []
    for key in ("base", "vat", "total", "wht", "net_payable"):
        amount = data.get(key)
        if amount is None:
            continue
        rate_key = _ROW_RATE_KEY.get(key)
        rate = data.get(rate_key, "") if rate_key else ""
        rows.append({"item": _t(ROW_LABEL[key], lang).format(rate=rate), "amount": amount})
    return rows


def error(code: str, data: dict, lang: str) -> str:
    return _t(ERRORS[code], lang).format(
        raw=(data or {}).get("raw", ""), amount=(data or {}).get("amount", "")
    )


# 工具名 → 答复渲染器(copy.reply 按本表委派)。
REPLIES = {registry.VAT_CALC: vat_calc}
