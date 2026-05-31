# -*- coding: utf-8 -*-
"""通用 ERP 外部单号派生层 (Zihao 2026-05-26 拍板 · 临时任务)

目标:推送成功后,用户能看到「外部 ERP 最终生成的单号」,并知道去 ERP 搜什么。

不在 erp_push_logs 表里新增列,也不动状态机 —— 纯粹在日志 API 读取时,
从已有的 response_body + adapter 派生出 3 个对用户友好的通用字段:

    external_doc_no   ERP 外部单号(给用户看 + 复制),没有则 ""
    external_doc_id   ERP 内部 ID,没有则 ""
    external_url      可打开的 ERP 链接,没有则 ""

外加一个给前端做"去哪搜"提示的 adapter 专属提示码:

    external_doc_hint adapter 专属提示码(前端做 i18n),没有则 ""

设计原则:
- 通用优先:default 派生器认 response_body 里的通用键(external_doc_no /
  doc_no / document_number / id / url 等),所以新 webhook 适配器零改动即可受益。
- adapter 专属覆盖:_DERIVERS 注册表按 adapter 名分发,MR.ERP 走专属逻辑
  (mrerp_bill_no -> external_doc_no)。Xero / QuickBooks / custom 在此预留位,
  接入时只需补一个派生器函数,日志 API / 前端都不用改。
- 永不抛异常:坏 JSON / None / failed log / 缺字段一律返回"全空"派生结果,
  调用方(日志列表 / 详情)绝不会因为派生失败而崩。
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 派生结果的固定形状 —— 调用方可以无条件读这 4 个键。
_EMPTY: Dict[str, str] = {
    "external_doc_no": "",
    "external_doc_id": "",
    "external_url": "",
    "external_doc_hint": "",
}


def _result(
    doc_no: str = "",
    doc_id: str = "",
    url: str = "",
    hint: str = "",
) -> Dict[str, str]:
    return {
        "external_doc_no": (doc_no or "").strip(),
        "external_doc_id": (doc_id or "").strip(),
        "external_url": (url or "").strip(),
        "external_doc_hint": (hint or "").strip(),
    }


def _coerce_body(response_body: Any) -> Dict[str, Any]:
    """把 response_body 统一转成 dict。

    response_body 可能是:已是 dict / JSON 字符串 / 非 JSON 文本 / None。
    任何无法解析成 dict 的情况都返回 {} —— 上层派生器据此返回全空,不崩。
    """
    if response_body is None:
        return {}
    if isinstance(response_body, dict):
        return response_body
    if isinstance(response_body, (bytes, bytearray)):
        try:
            response_body = response_body.decode("utf-8", "replace")
        except Exception:
            return {}
    if isinstance(response_body, str):
        s = response_body.strip()
        if not s or s[0] not in "{[":
            return {}
        try:
            parsed = json.loads(s)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


# ============================================================
# adapter 专属派生器
# ============================================================


def _derive_mrerp(body: Dict[str, Any], status: str) -> Dict[str, str]:
    """MR.ERP · 从 response_body.mrerp_bill_no 映射 external_doc_no。

    - external_doc_no = mrerp_bill_no
    - external_doc_id = 同 external_doc_no(MR.ERP 没有独立内部 ID)
    - external_url    = "" (MR.ERP 没有可直达的单据深链)
    - external_doc_hint = "mrerp_search" (前端提示去 销售赊账/ขายเชื่อ-ในประเทศ → List All 搜)
    """
    bill_no = body.get("mrerp_bill_no") or ""
    bill_no = str(bill_no).strip()
    if not bill_no:
        # 成功但 MR.ERP 没回单号 —— 返回全空,前端据 status=success 显示"未返回单号"。
        return _EMPTY.copy()
    return _result(
        doc_no=bill_no,
        doc_id=bill_no,
        url="",
        hint="mrerp_search",
    )


def _derive_mrerp_dms(body: Dict[str, Any], status: str) -> Dict[str, str]:
    """MR.ERP DMS · 从 response_body.booking_no 映射 external_doc_no(订车单号)。

    - external_doc_no = booking_no(订车单号 · 给用户看 + 复制)
    - external_doc_id = booking_id(DMS 内部订车单 ID)
    - external_url    = "" (DMS 没有可直达深链)
    - external_doc_hint = "mrerp_dms_search" (前端提示去 DMS 订车单/ใบจอง 搜该单号)
    """
    booking_no = str(body.get("booking_no") or "").strip()
    booking_id = str(body.get("booking_id") or "").strip()
    if not booking_no and not booking_id:
        return _EMPTY.copy()
    return _result(
        doc_no=booking_no,
        doc_id=booking_id or booking_no,
        url="",
        hint="mrerp_dms_search",
    )


def _derive_default(body: Dict[str, Any], status: str) -> Dict[str, str]:
    """通用派生器 · 认 response_body 里常见的单号/链接键。

    覆盖未注册的 adapter(含未来通用 webhook 对接的各种 ERP),让它们
    只要在响应里回标准键名就能零改动显示单号。
    """
    doc_no = (
        body.get("external_doc_no")
        or body.get("doc_no")
        or body.get("document_number")
        or body.get("number")
        or ""
    )
    doc_id = body.get("external_doc_id") or body.get("doc_id") or body.get("id") or ""
    url = body.get("external_url") or body.get("url") or ""
    return _result(doc_no=str(doc_no), doc_id=str(doc_id), url=str(url))


# adapter 名(小写) -> 派生器。预留 xero / quickbooks / custom 位:
# 接入新 ERP 时在这里加一行,日志 API 和前端都无需改动。
_DERIVERS = {
    "mrerp": _derive_mrerp,
    "mrerp_dms": _derive_mrerp_dms,
    # "xero": _derive_xero,
    # "quickbooks": _derive_quickbooks,
    # "custom": _derive_custom,
}


def derive_external_ref(
    adapter: Optional[str],
    response_body: Any,
    status: Optional[str] = None,
) -> Dict[str, str]:
    """日志 API 层调用入口。

    返回固定 4 键 dict(见模块 docstring)。永不抛异常。

    Args:
        adapter: erp_endpoints.adapter (mrerp/xero/webhook/...);端点已删时可能为 None。
        response_body: erp_push_logs.response_body(JSON 字符串 / dict / 文本 / None)。
        status: erp_push_logs.status('success'/'failed'/...);仅用于派生器内部判断,
                不改变状态机,也不参与"是否显示缺失提示"(那是前端职责)。
    """
    try:
        body = _coerce_body(response_body)
        key = (adapter or "").strip().lower()
        deriver = _DERIVERS.get(key, _derive_default)
        result = deriver(body, status or "")
        # 防御:派生器万一返回了缺键的 dict,补齐成固定形状。
        merged = _EMPTY.copy()
        if isinstance(result, dict):
            for k in merged:
                v = result.get(k)
                if v:
                    merged[k] = str(v)
        return merged
    except Exception:
        logger.exception("derive_external_ref failed · adapter=%s", adapter)
        return _EMPTY.copy()
