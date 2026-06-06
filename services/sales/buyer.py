# -*- coding: utf-8 -*-
"""买方信息动态模块:类型配置表 + 归一化 + 完整性校验(docs/sales-module/docs/15)。

泰国发票买方不是固定表单,而是随「买方类型」联动:公司 / 个人 / 外国个人 / 匿名散客。
一个 tax_id 字段三义(公司税号 / 身份证 / 护照),由 type 决定 label 与校验;分店标识只
对公司有意义。本模块是纯逻辑叶子(不连库):

- BUYER_CONFIG  声明式配置表,显隐/必填/校验器全从这里读(新增类型只改表)。
- normalize_buyer  §6 保险层:切类型后清掉不属于该类型的残值(防脏数据提交)。
- validate_buyer   §B 后端完整性闸:开出完整税票前按 doc_type 复跑校验,不信前端。

错误码(路由层映射 422):buyer_incomplete / buyer_tax_id_invalid /
buyer_branch_required / buyer_branch_no_invalid。
"""

from __future__ import annotations

import re
from typing import Optional

BUYER_TYPES = ("company", "individual", "foreigner", "anonymous")
DEFAULT_BUYER_TYPE = "company"

# 声明式配置(docs/15 §2)。tax_id 的值是校验器名(None = 该类型无税号);
# branch=True 表示「总公司/分店」标识只对此类型渲染并参与校验。
BUYER_CONFIG = {
    "company": {"name": "req", "address": "req", "tax_id": "th13", "branch": True},
    "individual": {"name": "req", "address": "req", "tax_id": "th13", "branch": False},
    "foreigner": {"name": "req", "address": "req", "tax_id": "passport", "branch": False},
    "anonymous": {"name": "opt", "address": "opt", "tax_id": None, "branch": False},
}

# 开出时必须买方齐全的单据类型(完整税票)。简易票(ABB)/收据/报价不在此列;
# 红冲/补开的买方继承自已开出原单(已校验过),不在这里复跑。
REQUIRE_FULL_BUYER = ("tax_invoice", "tax_invoice_receipt")

_TH13 = re.compile(r"^\d{13}$")
_PASSPORT = re.compile(r"^[A-Za-z0-9]{4,20}$")
_BRANCH_NO = re.compile(r"^\d{5}$")

# 买方块在 sales_documents 上的列名(canonical key → 列)。
_COLUMN = {
    "type": "buyer_type",
    "name": "buyer_name",
    "address": "buyer_address",
    "tax_id": "buyer_tax_id",
    "branch_type": "buyer_branch_type",
    "branch_no": "buyer_branch_no",
}


def _clean(v) -> str:
    return (str(v) if v is not None else "").strip()


def normalize_buyer(raw: Optional[dict]) -> dict:
    """把请求里的买方块归一化成 canonical dict(§6 保险层)。

    清空规则:tax_id 对匿名清空;branch_type/branch_no 对非公司清空,公司非分店态清空
    branch_no。返回键:type/name/address/tax_id/branch_type/branch_no。
    """
    raw = raw or {}
    btype = raw.get("type") or DEFAULT_BUYER_TYPE
    if btype not in BUYER_CONFIG:
        btype = DEFAULT_BUYER_TYPE
    cfg = BUYER_CONFIG[btype]

    tax_id = _clean(raw.get("tax_id"))
    if cfg["tax_id"] is None:  # 匿名:无税号字段
        tax_id = ""

    if cfg["branch"]:
        branch_type = raw.get("branch_type") or "hq"
        if branch_type not in ("hq", "branch"):
            branch_type = "hq"
        branch_no = _clean(raw.get("branch_no")) if branch_type == "branch" else ""
    else:  # 个人/外国/匿名:无分店概念
        branch_type = None
        branch_no = ""

    return {
        "type": btype,
        "name": _clean(raw.get("name")),
        "address": _clean(raw.get("address")),
        "tax_id": tax_id,
        "branch_type": branch_type,
        "branch_no": branch_no or None,
    }


def validate_buyer(buyer: Optional[dict], doc_type: str) -> Optional[str]:
    """开出前的完整性闸(§B)。返回错误码或 None(通过)。

    完整税票/合并单:买方须 name+address+税号齐全,公司还要分店标识;匿名不能背完整票。
    其余 doc_type 只跑「有值才校格式」的字段级校验。
    """
    buyer = buyer or {}
    btype = buyer.get("type") or DEFAULT_BUYER_TYPE
    cfg = BUYER_CONFIG.get(btype, BUYER_CONFIG[DEFAULT_BUYER_TYPE])
    requires_full = doc_type in REQUIRE_FULL_BUYER

    name = _clean(buyer.get("name"))
    address = _clean(buyer.get("address"))
    tax_id = _clean(buyer.get("tax_id"))

    if requires_full:
        if btype == "anonymous":
            return "buyer_incomplete"  # 匿名买方不能开完整税票(只能 ABB)
        if not name or not address:
            return "buyer_incomplete"

    validator = cfg["tax_id"]
    if validator is not None:
        if requires_full and not tax_id:
            return "buyer_incomplete"
        if tax_id and not _tax_id_ok(validator, tax_id):
            return "buyer_tax_id_invalid"

    if cfg["branch"] and requires_full:
        branch_type = buyer.get("branch_type")
        if branch_type not in ("hq", "branch"):
            return "buyer_branch_required"
        if branch_type == "branch" and not _BRANCH_NO.match(_clean(buyer.get("branch_no"))):
            return "buyer_branch_no_invalid"

    return None


def _tax_id_ok(validator: str, value: str) -> bool:
    if validator == "th13":
        return bool(_TH13.match(value))
    if validator == "passport":
        return bool(_PASSPORT.match(value))
    return True


def to_columns(buyer: dict) -> dict:
    """canonical buyer dict → {列名: 值},供 DAL 写 sales_documents 的买方列。"""
    return {col: buyer.get(key) for key, col in _COLUMN.items()}


def from_row(row: dict) -> dict:
    """sales_documents 行 → canonical buyer dict(供冻结快照 / PDF 渲染读取)。"""
    row = row or {}
    return {key: row.get(col) for key, col in _COLUMN.items()}
