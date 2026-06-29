# -*- coding: utf-8 -*-
"""发票字段级打分器:把"识别得对不对"按钱权重编码成确定性数字。

银行侧已有 run_eval 的行召回/期末核对;发票侧此前只能肉眼比对 before/after。
本模块给发票一个对等的尺子:同一份真值,任何一次抽取(线上 pipeline 或贴进来的
JSON)都能算出逐字段命中 + 加权分 + 钱字段精确率 + 关键字段漏判清单。

纯函数:不连 Gemini、不碰 pydantic、不读 IO。输入两个 dict(真值、抽取的 fields),
输出可序列化的打分结果 → 既进 CI 守门,也供运行器复用。

为什么按权重而非平均:总额读错 40 倍(pur05)和卖方名差一个空格,代价天差地别。
钱字段权重最高,名称类最低 —— 一个把总额读错却名称全对的抽取不该拿高分。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# 钱字段容差(泰铢):0.01 足够吸收浮点/四舍五入,又抓得住真错(pur05 差 1735 铢)。
MONEY_TOL = 0.01

# 字段 → (比对类型, 权重)。权重反映读错的业务代价,不是字段数量。
#   money  : 数值容差比对(总额>VAT/小计:总额是入账金额,错了直接错账)
#   id13   : 13 位泰国税号,只比数字(抵扣进项要真税号)
#   invno  : 发票号,去空格大小写归一后精确比
#   date   : YYYY-MM-DD 直比(年份消歧已在 schema 上游做掉)
#   currency: 币种,泰铢/บาท 归一为空(外币会被下游拦截不得当泰铢入账)
#   text   : 名称类,去空格小写折叠后比(版式噪声不算错)
#   exact  : 原样精确比(document_type 等枚举)
#   count  : 列表长度比(明细行数 → 多票/多行漏判信号)
_FIELD_SPEC: Dict[str, tuple] = {
    "total_amount": ("money", 5),
    "vat": ("money", 3),
    "subtotal": ("money", 3),
    "discount": ("money", 2),
    "seller_tax": ("id13", 3),
    "buyer_tax": ("id13", 2),
    "invoice_number": ("invno", 3),
    "date": ("date", 2),
    "currency": ("currency", 3),
    "document_type": ("exact", 1),
    "seller_name": ("text", 1),
    "buyer_name": ("text", 1),
    "items_count": ("count", 1),
}

# 权重 >= 此值的字段读错 → 计入 critical_misses(钱/税号/发票号级别)。
_CRITICAL_WEIGHT = 3

_THAI_BAHT_WORDS = ("บาท", "thb", "฿")


def normalize_money(v: Any) -> Optional[float]:
    """'฿1,780.00' / '1780' / 1780 → 1780.0;空/不可解 → None。

    剥掉除数字、小数点、负号外的一切(币种符、空格、บาท)。逗号当千分位去掉。
    """
    if v is None:
        return None
    s = re.sub(r"[^\d.\-]", "", str(v).replace(",", "").strip())
    if not s or s in ("-", ".", "-."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def normalize_id(v: Any) -> str:
    """税号只留数字(票面常带空格/连字符:0-7355-27000-28-9)。"""
    return re.sub(r"\D", "", str(v or ""))


def normalize_invoice_no(v: Any) -> str:
    """发票号去所有空白 + 大写(版式空格/大小写不算错;119/2560 vs 879/2566 仍判异)。"""
    return re.sub(r"\s+", "", str(v or "")).upper()


def normalize_text(v: Any) -> str:
    """名称类:折叠空白 + 小写 + 去首尾(NBSP 一并清,泰文渲染常掺)。"""
    return re.sub(r"\s+", " ", str(v or "").replace("\xa0", " ")).strip().lower()


def normalize_currency(v: Any) -> str:
    """币种归一:泰铢/บาท/฿/空 → ''(本币);外币留大写码(USD/EUR)。"""
    s = str(v or "").strip().lower()
    if not s or any(w in s for w in _THAI_BAHT_WORDS):
        return ""
    return re.sub(r"[^A-Za-z]", "", s).upper()


def normalize_date(v: Any) -> str:
    return str(v or "").strip()


def _both_blank(a: str, b: str) -> Optional[bool]:
    """两边都空 → True(都没这字段=一致);仅一边空 → False。都非空 → None(交给值比对)。"""
    if not a and not b:
        return True
    if not a or not b:
        return False
    return None


def _match_field(kind: str, expected: Any, actual: Any) -> bool:
    if kind == "money":
        e, a = normalize_money(expected), normalize_money(actual)
        if e is None and a is None:
            return True
        if e is None or a is None:
            return False
        return abs(e - a) <= MONEY_TOL
    if kind == "count":
        return _coerce_int(expected) == _coerce_int(actual)

    norm = {
        "id13": normalize_id,
        "invno": normalize_invoice_no,
        "text": normalize_text,
        "currency": normalize_currency,
        "date": normalize_date,
        "exact": lambda x: str(x or "").strip(),
    }[kind]
    e, a = norm(expected), norm(actual)
    blank = _both_blank(e, a)
    if blank is not None:
        return blank
    return e == a


def _coerce_int(v: Any) -> Optional[int]:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def _actual_value(kind: str, field: str, actual: Dict[str, Any]) -> Any:
    """从抽取 fields 里取该字段的值。items_count 是派生量(明细行数)。"""
    if field == "items_count":
        items = actual.get("items")
        return len(items) if isinstance(items, list) else None
    return actual.get(field)


def score_invoice(expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
    """对一张发票打分。

    Args:
        expected: 真值 dict。只比对其中**出现的**字段 → 最小真值(只填 total_amount
                  + 税号)也能用,不强求标全。items_count 显式给整数才比。
        actual:   抽取出的 fields dict(ThaiInvoice.model_dump 的形状)。

    Returns:
        {
          "fields": {name: {expected, actual, match, weight, kind}},
          "weighted_score": 0.0..1.0,   # sum(weight*match)/sum(weight)
          "money_exact": "k/n",          # 钱字段精确命中
          "critical_misses": [field],    # 权重>=3 且未命中
          "scored_fields": n,
        }
    """
    fields_out: Dict[str, Any] = {}
    w_total = w_hit = 0
    money_hit = money_n = 0
    critical_misses: List[str] = []

    for field, (kind, weight) in _FIELD_SPEC.items():
        if field not in expected:
            continue
        exp_val = expected[field]
        act_val = _actual_value(kind, field, actual)
        match = _match_field(kind, exp_val, act_val)

        fields_out[field] = {
            "expected": exp_val,
            "actual": act_val,
            "match": match,
            "weight": weight,
            "kind": kind,
        }
        w_total += weight
        if match:
            w_hit += weight
        elif weight >= _CRITICAL_WEIGHT:
            critical_misses.append(field)
        if kind == "money":
            money_n += 1
            money_hit += int(match)

    return {
        "fields": fields_out,
        "weighted_score": round(w_hit / w_total, 4) if w_total else None,
        "money_exact": f"{money_hit}/{money_n}" if money_n else None,
        "critical_misses": critical_misses,
        "scored_fields": len(fields_out),
    }


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """多张发票汇总:平均加权分 + 钱字段总精确率 + 全场关键漏判计数。"""
    scored = [r for r in results if r and r.get("weighted_score") is not None]
    if not scored:
        return {"n": 0, "avg_weighted_score": None, "money_exact": None, "critical_miss_total": 0}
    mh = mn = 0
    for r in scored:
        me = r.get("money_exact")
        if me:
            h, n = me.split("/")
            mh += int(h)
            mn += int(n)
    return {
        "n": len(scored),
        "avg_weighted_score": round(sum(r["weighted_score"] for r in scored) / len(scored), 4),
        "money_exact": f"{mh}/{mn}" if mn else None,
        "critical_miss_total": sum(len(r.get("critical_misses") or []) for r in scored),
    }
