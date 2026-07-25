# -*- coding: utf-8 -*-
"""ERP 推送异常的错误码分类 + 自助修复派生(纯函数 · 无 DB · 无外部调用)。

从 erp_push_logs 的 error_msg / request_body 派生「这条异常是什么子类」(chip)+「能不能
用户自助补救、补什么」(待补科目卡 / 绑主体卡)。list_push_exceptions 消费,前端读结构化
字段渲染,不再解析裸错误串。push_log_queries re-import 当 facade(store.X is q.X 单一对象)。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services.erp.express_push.stock_acc_group import (
    REASON_ACC_GROUP_MISSING,
    REASON_ACC_GROUP_REQUIRED,
)
from services.erp.external_ref import _coerce_body

# 库存路的自助修失败码。前两个都是「账套零库存主档,建第一个库存品差一个存货科目组」,
# 差在缺的东西不同:required = 合格的组有好几个,没人拍板选哪个;missing = 一个合格的都没有,
# 会计得先去 Express 建。后两个是旧口径 —— 2026-07-25 起不再产出,历史日志还在,继续认得出来。
# 这两个码都要科目组下拉那张卡(而非补期初三格)。从产出方 import,不在这儿手打字面量:
# 各写一份就是两处对码名的假设,改名时 grep 常量找不全。此前用前缀 "stock_acc_group" 判,
# 将来出现 stock_acc_group_locked 之类的新码会被静默吞进这个分支。
_ACC_GROUP_REASONS = (REASON_ACC_GROUP_REQUIRED, REASON_ACC_GROUP_MISSING)
_STOCK_FIX_REASONS = (
    *_ACC_GROUP_REASONS,
    "stock_no_master_in_account_set",
    "STOCK_ITEM_NOT_FOUND",
)

# 小助手防重单闸的码(companion dbf_writer.ERR_PRIOR_DOC_EXISTS)。改了要两边一起改 ——
# 有 test_prior_docnum 的契约用例钉着。
PRIOR_DOC_CODE = "PRIOR_DOC_STILL_IN_ERP"


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
    # 防重单闸拦下:上一版单据还躺在 Express 里。会计得先去删那张,不删就重推必出重复单。
    # 须先于下面的通用分支 —— 这条有专属指引(要说清删哪一号),掉进 other 就只剩一句裸码。
    if PRIOR_DOC_CODE in msg:
        return "prior_doc_exists"
    # 库存路推不动(缺存货科目组 / 缺主档 / 库存零负)→ 会计自助可救(选科目组或补期初)。
    # 须先于 account_set,因 stock_no_master_in_account_set 串里含 "account_set" 会被下面误吞。
    if any(k in msg for k in _STOCK_FIX_REASONS):
        return "stock_opening_needed"
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
            "date_implausible",
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


def derive_prior_doc_fix(
    error_msg: Optional[str], request_body: Any = None
) -> Optional[Dict[str, Any]]:
    """防重单闸拦下时,告诉会计**要去 Express 删哪一号**。

    单据号取自载荷的 prior_docnum(我们自己发下去的、权威),不从错误串里正则抠 ——
    小助手那句提示是写死中文,泰国会计看不懂,也不该成为云端的数据来源。
    """
    if PRIOR_DOC_CODE not in (error_msg or ""):
        return None
    body = _coerce_body(request_body)
    payload = (body or {}).get("payload") if isinstance(body, dict) else None
    src = payload if isinstance(payload, dict) else (body if isinstance(body, dict) else {})
    return {"docnum": str((src or {}).get("prior_docnum") or "").strip()}


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


def derive_stock_fix(
    error_msg: Optional[str],
    request_body: Any = None,
    acc_groups: Optional[List[Dict[str, Any]]] = None,
    groups_reported: bool = False,
) -> Optional[Dict[str, Any]]:
    """从库存路失败推导补救卡要渲染什么(needs)+ 渲染它要的料。

    needs="acc_group":账套零库存主档且科目组定不下来 → 卡渲染科目组下拉,选完小助手就能
    从零建 STKTYP=0。候选(fit 过的)由调用方从端点 config 取来传进,本分类器是纯函数不查库。
    候选空(stock_acc_group_missing)时下拉退化成一句指引,靠 groups_reported 分「等小助手报」
    还是「去 Express 建」—— 同一张卡两种空态,不另开一条渲染路径。
    needs="opening" :旧口径缺主档/库存零负 → 卡渲染补期初三格(数量/成本/日期)。
    两者都带 items(票面商品行,取自 request_body.payload.items),让会计认出这张票涉及哪些
    商品;取不到明细则空列表(前端显示「无可补商品」而非崩)。

    groups_reported = 小助手到底上报过候选没有(端点 config 有 stock_acc_groups_seen_at)。
    候选为空有两种成因,混成一句会把人指错方向:没上报过是等小助手升级 + 下次目录上报,
    这时让会计去 Express 建组等于骗他白建一个多余的科目组。
    """
    msg = error_msg or ""
    if not any(k in msg for k in _STOCK_FIX_REASONS):
        return None
    body = _coerce_body(request_body)
    payload = (body or {}).get("payload") if isinstance(body, dict) else None
    src = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(src, list):
        src = (body or {}).get("items") if isinstance(body, dict) else None
    items = []
    seen = set()
    for it in src or []:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or it.get("description") or "").strip()
        stkcod = str(it.get("stkcod") or it.get("erp_item_code") or "").strip()
        key = stkcod or name
        if not key or key in seen:
            continue
        seen.add(key)
        items.append({"name": name, "stkcod": stkcod})
    needs = "acc_group" if any(r in msg for r in _ACC_GROUP_REASONS) else "opening"
    groups = [g for g in (acc_groups or []) if isinstance(g, dict)]
    return {
        "needs": needs,
        "items": items,
        "acc_groups": groups,
        "groups_reported": bool(groups_reported),
    }
