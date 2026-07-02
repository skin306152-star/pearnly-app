# -*- coding: utf-8 -*-
"""ERP 推送异常的错误码分类 + 自助修复派生(纯函数 · 无 DB · 无外部调用)。

从 erp_push_logs 的 error_msg / request_body 派生「这条异常是什么子类」(chip)+「能不能
用户自助补救、补什么」(待补科目卡 / 绑主体卡)。list_push_exceptions 消费,前端读结构化
字段渲染,不再解析裸错误串。push_log_queries re-import 当 facade(store.X is q.X 单一对象)。
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from services.erp.external_ref import _coerce_body


def classify_push_exception(error_msg: Optional[str]) -> str:
    """把 ERP 推送失败错误码归到异常子类(前端 chip 用 · 通用 · 不写死 MR.ERP)。"""
    msg = error_msg or ""
    if "ERR_CUSTOMER_NAME_MISMATCH" in msg or "ERR_NO_CUSTOMER_MAPPING" in msg:
        return "customer_mismatch"
    if "ERR_PRODUCT_NAME_MISMATCH" in msg:
        return "product_mismatch"
    if "ERR_NO_CLIENT" in msg:
        return "no_client"
    if "VERIFY_UNAVAILABLE" in msg:
        return "verify_unavailable"
    # Express 留人工(EXPRESS_MANUAL:<reason>)· 按可补救路径分桶。
    # 账套配错(小助手连到不可写账套)先于科目判:account_set_not_allowed/no_account_set。
    if "account_set" in msg:
        return "account_set"
    # 缺 收入/应收/销项税/采购/应付/进项税 科目,或科目不在该账套科目表 → 待补科目卡可救。
    if "_account" in msg or "account_not_in_chart" in msg:
        return "account_missing"
    # 方向判不出:主体没绑 / 税号不齐 / 该方向未开。
    if "direction_unknown" in msg or "direction_not_enabled" in msg:
        return "direction_unknown"
    if "low_confidence" in msg:
        return "low_confidence"
    # 单据防呆(preflight doc_sanity)+ 套账匹配闸:须人工判断,无自助修。
    if any(
        k in msg
        for k in (
            "ERR_ACCOUNT_SET_MISMATCH",
            "currency_not_thb",
            "seller_buyer_same_tax",
            "credit_note",
            "deposit_receipt",
            "date_future",
            "date_reissued",
            "tax_id_invalid",
        )
    ):
        return "document_review"
    return "other"


# Express 缺科目失败码 → (方向, 该补的 config 槽位)· 待补科目卡据此只问相关槽位。
_SLOT_BY_ACCOUNT_REASON = {
    "no_revenue_account": ("sales", "revenue_acc"),
    "no_ar_account": ("sales", "ar_acc"),
    "no_output_vat_account": ("sales", "vat_output_acc"),
    "no_purchase_account": ("purchase", "fallback_acc"),
    "no_ap_account": ("purchase", "ap_acc"),
    "no_input_vat_account": ("purchase", "vat_input_acc"),
}
_SALES_SLOTS = ["revenue_acc", "ar_acc", "vat_output_acc"]
_PURCHASE_SLOTS = ["fallback_acc", "ap_acc", "vat_input_acc"]


def derive_account_fix(
    error_msg: Optional[str], request_body: Any = None
) -> Optional[Dict[str, Any]]:
    """从 Express 缺科目失败推导「待补科目卡」要问哪些科目槽(direction + slots)。

    单缺一科目(no_*_account)→ 只问那一槽;account_not_in_chart(某分录科目不在科目表)
    → 按 request_body.payload 的 direction 问该方向全部槽,带上越界码 bad_code。非缺科目错 → None。
    """
    msg = error_msg or ""
    for reason, (direction, slot) in _SLOT_BY_ACCOUNT_REASON.items():
        if reason in msg:
            return {"direction": direction, "slots": [slot]}
    if "account_not_in_chart" in msg:
        body = _coerce_body(request_body)
        direction = str((body or {}).get("direction") or "") if isinstance(body, dict) else ""
        m = re.search(r"account_not_in_chart:(\S+)", msg)
        bad = m.group(1) if m else ""
        if direction == "sales":
            slots = list(_SALES_SLOTS)
        elif direction == "purchase":
            slots = list(_PURCHASE_SLOTS)
        else:
            slots = _SALES_SLOTS + _PURCHASE_SLOTS
        return {"direction": direction, "slots": slots, "bad_code": bad}
    return None


def derive_bind_fix(error_msg: Optional[str]) -> Optional[Dict[str, Any]]:
    """direction_unknown 异常能否靠「绑主体」自助救(消前端 !/direction_not_enabled/ 正则)。

    主体没绑 / 税号没读到(direction_unknown)→ 选账套主体重推即可救 → {can_bind: True};
    direction_not_enabled(方向判出但该方向没在向导开)绑主体没用,得去向导开 → None。
    与前端旧口径逐字一致(classify 把两者并到 direction_unknown 子类,这里再细分能否绑)。
    """
    msg = error_msg or ""
    if "direction_unknown" not in msg or "direction_not_enabled" in msg:
        return None
    return {"can_bind": True}
