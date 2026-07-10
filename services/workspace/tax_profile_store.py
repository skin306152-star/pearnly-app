# -*- coding: utf-8 -*-
"""客户税务画像 DAL(B2-b · client_tax_profiles · 每客户一行 · 套账隔离)。

方案:税务画像-方案-B1.md §2(字段表)/§5(schema)。表结构见
services/workspace/tax_profile_schema.py(与 alembic 0064 逐字对齐)。

隔离=每句 WHERE tenant_id;PK (tenant_id, workspace_client_id) 天然幂等 upsert。
vat_status/branch 派生自 workspace_clients(vat_registered/branch),画像表不重复存,
读时 JOIN——单一事实源(方案 §2.2 注)。金额字段(vat_credit_carry)全程 Decimal,
不经 float。枚举字段非法值一律拒绝(不吞不猜),抛 TaxProfileError。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Optional


class TaxProfileError(ValueError):
    """业务级校验错(枚举非法/必填缺失)。code 供调用方映射 4xx,不吞不猜。"""

    def __init__(self, code: str, *, field: Optional[str] = None):
        super().__init__(code)
        self.code = code
        self.field = field


# 字段表(方案 §2.2)枚举取值域。key 为 client_tax_profiles 列名。
ENUM_FIELDS = {
    "sbt_status": {"none", "registered", "unknown"},
    "has_employees": {"yes", "no", "unknown"},
    "pays_individuals": {"yes", "no", "unknown"},
    "pays_juristic": {"yes", "no", "unknown"},
    "pays_foreign": {"yes", "no", "unknown"},
    "pays_interest_dividend": {"yes", "no", "unknown"},
    "filing_disposition": {"active", "dormant", "unknown"},
    "efiling_enrolled": {"yes", "no", "unknown"},
    "source": {"onboarding", "data_inferred", "ai_suggested", "imported"},
}

_TEXT_FIELDS = {"sbt_business_type", "tax_agent_ref"}
_BOOL_FIELDS = {"has_multi_branch", "tax_agent_authorized"}
_INT_FIELDS = {"branch_count", "profile_version"}
_DECIMAL_FIELDS = {"vat_credit_carry"}
_NUMERIC_FIELDS = {"confidence"}

# 与 DDL DEFAULT 逐字对齐(services/workspace/tax_profile_schema.py)——
# 画像行不存在时,get_profile 回退这一份默认值,不再单独维护第二份常量。
_ROW_DEFAULTS: dict = {
    "sbt_status": "none",
    "sbt_business_type": "",
    "has_employees": "unknown",
    "pays_individuals": "unknown",
    "pays_juristic": "unknown",
    "pays_foreign": "unknown",
    "pays_interest_dividend": "unknown",
    "has_multi_branch": False,
    "branch_count": 1,
    "filing_disposition": "active",
    "efiling_enrolled": "unknown",
    "tax_agent_authorized": False,
    "tax_agent_ref": "",
    "vat_credit_carry": Decimal("0.00"),
    "source": "onboarding",
    "confidence": None,
    "profile_version": 1,
    "updated_by": "system",
    "updated_at": None,
    "created_at": None,
}

_MUTABLE_FIELDS = tuple(_ROW_DEFAULTS)  # 顺序固定,upsert/select 复用


def _to_decimal(value: Any, *, field: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise TaxProfileError("invalid_decimal", field=field) from None


def _validate_and_coerce(field: str, value: Any) -> Any:
    if field in ENUM_FIELDS and value not in ENUM_FIELDS[field]:
        raise TaxProfileError("invalid_enum_value", field=field)
    if field in _DECIMAL_FIELDS:
        return _to_decimal(value, field=field)
    if field in _NUMERIC_FIELDS:
        return None if value is None else _to_decimal(value, field=field)
    if field in _BOOL_FIELDS:
        return bool(value)
    if field in _INT_FIELDS:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise TaxProfileError("invalid_integer", field=field) from None
    if field in _TEXT_FIELDS or field in ENUM_FIELDS:
        return str(value)
    return value


_SELECT_COLUMNS = ", ".join(f"p.{f}" for f in _MUTABLE_FIELDS)


def get_profile(cur, *, tenant_id: str, workspace_client_id: int) -> Optional[dict]:
    """读画像(不存在则返回默认画像),跨租户/不存在的客户返回 None。

    LEFT JOIN 落在 workspace_clients 上(而非 client_tax_profiles),缺档时仍能派生
    vat_status/branch;JOIN 的 WHERE tenant_id 是隔离闸——别的租户的 workspace_client_id
    在这个 tenant_id 下查不到行,函数如实返回 None,不会把别家默认画像端出来。
    """
    cur.execute(
        f"""
        SELECT wc.vat_registered AS vat_registered, wc.branch AS ws_branch,
               {_SELECT_COLUMNS}
        FROM workspace_clients wc
        LEFT JOIN client_tax_profiles p
            ON p.tenant_id = wc.tenant_id AND p.workspace_client_id = wc.id
        WHERE wc.tenant_id = %s AND wc.id = %s
        """,
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    row = dict(row)

    profile: dict = {
        "tenant_id": tenant_id,
        "workspace_client_id": workspace_client_id,
        "vat_status": "registered" if row.get("vat_registered") else "unregistered",
        "branch": row.get("ws_branch") or "สำนักงานใหญ่",
    }
    for field, default in _ROW_DEFAULTS.items():
        value = row.get(field)
        if value is None:
            profile[field] = default
            continue
        if field in _DECIMAL_FIELDS or field in _NUMERIC_FIELDS:
            profile[field] = _to_decimal(value, field=field)
        else:
            profile[field] = value
    return profile


def upsert_profile(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    updated_by: str,
    sbt_status: Optional[str] = None,
    sbt_business_type: Optional[str] = None,
    has_employees: Optional[str] = None,
    pays_individuals: Optional[str] = None,
    pays_juristic: Optional[str] = None,
    pays_foreign: Optional[str] = None,
    pays_interest_dividend: Optional[str] = None,
    has_multi_branch: Optional[bool] = None,
    branch_count: Optional[int] = None,
    filing_disposition: Optional[str] = None,
    efiling_enrolled: Optional[str] = None,
    tax_agent_authorized: Optional[bool] = None,
    tax_agent_ref: Optional[str] = None,
    vat_credit_carry: Optional[Any] = None,
    source: Optional[str] = None,
    confidence: Optional[Any] = None,
    profile_version: Optional[int] = None,
) -> None:
    """部分字段更新(PK 幂等)。传 None 的字段保持既有值不动(首次建档落 DDL DEFAULT)。

    updated_by 必填(审计字段,方案 §2.2 元字段)——谁改的必须留痕,不许匿名写。
    枚举/Decimal/整数一律校验,非法值直接抛 TaxProfileError,不静默纠正/丢弃。
    """
    updated_by = str(updated_by or "").strip()
    if not updated_by:
        raise TaxProfileError("updated_by_required", field="updated_by")

    candidates = {
        "sbt_status": sbt_status,
        "sbt_business_type": sbt_business_type,
        "has_employees": has_employees,
        "pays_individuals": pays_individuals,
        "pays_juristic": pays_juristic,
        "pays_foreign": pays_foreign,
        "pays_interest_dividend": pays_interest_dividend,
        "has_multi_branch": has_multi_branch,
        "branch_count": branch_count,
        "filing_disposition": filing_disposition,
        "efiling_enrolled": efiling_enrolled,
        "tax_agent_authorized": tax_agent_authorized,
        "tax_agent_ref": tax_agent_ref,
        "vat_credit_carry": vat_credit_carry,
        "source": source,
        "confidence": confidence,
        "profile_version": profile_version,
    }
    provided = {
        field: _validate_and_coerce(field, value)
        for field, value in candidates.items()
        if value is not None
    }

    columns = ["tenant_id", "workspace_client_id", "updated_by"] + list(provided)
    values = [tenant_id, workspace_client_id, updated_by] + list(provided.values())
    placeholders = ", ".join(["%s"] * len(columns))
    update_sets = ["updated_by = EXCLUDED.updated_by", "updated_at = now()"]
    update_sets += [f"{field} = EXCLUDED.{field}" for field in provided]

    cur.execute(
        f"INSERT INTO client_tax_profiles ({', '.join(columns)}) "
        f"VALUES ({placeholders}) "
        "ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE SET "
        f"{', '.join(update_sets)}",
        tuple(values),
    )
