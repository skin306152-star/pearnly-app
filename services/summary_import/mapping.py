# -*- coding: utf-8 -*-
"""列映射 + 批次常量 → 每行规范化 fields(OCR 同形 · 供下游判方向/建单/写 ocr_history)。

「多场景适配」核心:表里有的字段按列取,表里没有的(客户/税号/商品/付款/单号)整批填一次。
甲乙方按批次方向落位——销项则账套=卖方、对方=买方;采购反之。散客开关命中则对方归一到现金
客户「เงินสด」(同时满足 MR.ERP 结构判定与 Express 文本判定,见 [[mrerp-cash-counterparty-fallback]])。
纯函数:不连库、不判方向(判方向在 judge)、不建单(建单在 commit)。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from services.purchase.field_clean import clean_tax_id

CASH_COUNTERPARTY = "เงินสด"  # 与 MRERP_CASH_CUSTOMER / Express CASH_CUSTOMER_NAME 同串
_SEQ_RE = re.compile(r"\{(?:seq|n|序号|日期序号)\}")


def _col_value(row_cells: List[str], column_map: Dict[str, Any], key: str) -> str:
    """按列映射取值。映射值可为列下标(int)或表头名已在上游解析成下标。缺映射 → ''。"""
    idx = column_map.get(key)
    if idx is None:
        return ""
    try:
        return str(row_cells[int(idx)]).strip()
    except (IndexError, ValueError, TypeError):
        return ""


def _gen_doc_no(pattern: str, index: int, width: int) -> str:
    """单号规则 → 本行单号。{seq}/{序号} 占位替换为补零序号;无占位符原样返回(整批同号→查重会警告)。"""
    p = (pattern or "").strip()
    if not p:
        return ""
    seq = str(index + 1).zfill(max(width, 3))
    return _SEQ_RE.sub(seq, p)


def _own_party(workspace: Dict[str, Any]) -> Dict[str, str]:
    return {
        "name": str((workspace or {}).get("name") or "").strip(),
        "tax": clean_tax_id((workspace or {}).get("tax_id")),
        "addr": str((workspace or {}).get("address") or "").strip(),
    }


def _counterparty(constants: Dict[str, Any], *, walkin: bool) -> Dict[str, str]:
    """对方(客户/供应商)身份。散客开关命中 → 归一现金客户,清空税号(走两个 ERP 的现金兜底)。"""
    if walkin:
        return {"name": CASH_COUNTERPARTY, "tax": "", "addr": ""}
    return {
        "name": str(constants.get("counterparty_name") or "").strip(),
        "tax": clean_tax_id(constants.get("counterparty_tax")),
        "addr": str(constants.get("counterparty_address") or "").strip(),
    }


def _assign_parties(
    fields: Dict[str, Any], direction: str, own: Dict[str, str], other: Dict[str, str]
) -> None:
    """按方向把账套主体/对方落到 seller/buyer 槽(下游 detect_by_tax 据此用税号复核方向)。"""
    if direction == "sales":
        seller, buyer = own, other
    else:
        seller, buyer = other, own
    fields["seller_name"] = seller["name"]
    fields["seller_tax"] = seller["tax"]
    fields["seller_addr"] = seller["addr"]
    fields["buyer_name"] = buyer["name"]
    fields["buyer_tax"] = buyer["tax"]
    fields["buyer_addr"] = buyer["addr"]
    # sales_mapper 另读 customer_name/customer_tax → 镜像买方,避免销项侧漏字段。
    fields["customer_name"] = buyer["name"]
    fields["customer_tax"] = buyer["tax"]


def _line_item(
    constants: Dict[str, Any], cells: List[str], column_map: Dict[str, Any]
) -> Dict[str, str]:
    """单行商品明细。商品名整批常量优先,否则取映射列;编码整批常量(空→ERP 自建)。"""
    name = str(constants.get("product_name") or "").strip() or _col_value(
        cells, column_map, "item_name"
    )
    return {
        "name": name,
        "code": str(constants.get("product_code") or "").strip(),
        "qty": _col_value(cells, column_map, "qty"),
        "price": _col_value(cells, column_map, "unit_price"),
        "subtotal": _col_value(cells, column_map, "subtotal"),
    }


def build_row_fields(
    cells: List[str],
    index: int,
    *,
    column_map: Dict[str, Any],
    constants: Dict[str, Any],
    workspace: Dict[str, Any],
    row_count: int,
) -> Dict[str, Any]:
    """一行 → OCR 同形 fields dict(未判方向的中间态,方向/现金落点交给 judge)。"""
    direction = (
        "sales" if str(constants.get("direction") or "sales").lower() == "sales" else "purchase"
    )
    walkin = bool(constants.get("cash_walkin"))
    has_vat = constants.get("has_vat")
    payment_method = str(constants.get("payment_method") or "").strip()

    item = _line_item(constants, cells, column_map)
    fields: Dict[str, Any] = {
        "document_type": "tax_invoice" if has_vat is not False else "receipt",
        "invoice_number": _gen_doc_no(
            str(constants.get("doc_no_pattern") or ""), index, len(str(row_count))
        ),
        "date": _col_value(cells, column_map, "date"),
        "subtotal": _col_value(cells, column_map, "subtotal"),
        "vat": _col_value(cells, column_map, "vat"),
        "total_amount": _col_value(cells, column_map, "total_amount"),
        "payment_method": payment_method,
        "items": (
            [{k: item[k] for k in ("name", "qty", "price", "subtotal")}] if item["name"] else []
        ),
    }
    _assign_parties(
        fields, direction, _own_party(workspace), _counterparty(constants, walkin=walkin)
    )
    fields["_product_code"] = item[
        "code"
    ]  # commit 建商品/写行用;下划线前缀=内部字段,ERP mapper 不读
    fields["_direction"] = direction
    fields["_walkin"] = walkin
    return fields


def map_rows(
    parsed: Dict[str, Any],
    *,
    column_map: Dict[str, Any],
    constants: Dict[str, Any],
    workspace: Dict[str, Any],
    include_summary: bool = False,
) -> List[Dict[str, Any]]:
    """整批映射。默认跳过底部合计行(is_summary);include_summary=True 时也建(用户显式勾选)。

    返回 [{row_index, fields}]。方向判定/缺字段警告由 judge 接手,这里只做确定性落位。
    """
    rows = parsed.get("rows") or []
    row_count = len([r for r in rows if include_summary or not r.get("is_summary")])
    out: List[Dict[str, Any]] = []
    seq = 0
    for r in rows:
        if r.get("is_summary") and not include_summary:
            continue
        fields = build_row_fields(
            r.get("cells") or [],
            seq,
            column_map=column_map,
            constants=constants,
            workspace=workspace,
            row_count=row_count,
        )
        out.append({"row_index": r.get("index", seq), "fields": fields})
        seq += 1
    return out


def find_duplicate_doc_nos(mapped: List[Dict[str, Any]]) -> List[str]:
    """批次内重复单号(ERP 拒收重复)→ 去重后的重复号列表,供上游告警。"""
    seen: Dict[str, int] = {}
    for m in mapped:
        no = str((m.get("fields") or {}).get("invoice_number") or "").strip()
        if no:
            seen[no] = seen.get(no, 0) + 1
    return [no for no, n in seen.items() if n > 1]
