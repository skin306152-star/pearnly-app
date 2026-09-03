from __future__ import annotations

from decimal import Decimal

VAT_RATE = Decimal("7")


def is_vat_registered(cur, *, tenant_id: str, workspace_client_id: int) -> bool:
    cur.execute(
        "SELECT vat_registered FROM workspace_clients WHERE tenant_id = %s AND id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    return bool(row and row["vat_registered"])


def resolve(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    price_includes_vat: bool,
) -> dict:
    registered = is_vat_registered(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    return {
        "vat_registered": registered,
        "vat_rate": VAT_RATE if registered else Decimal("0"),
        "price_includes_vat": registered and bool(price_includes_vat),
        "doc_kind": "abbrev_tax_invoice" if registered else "receipt",
    }


def receipt_doc_kind(cur, *, tenant_id: str, workspace_client_id: int) -> str:
    return resolve(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        price_includes_vat=False,
    )["doc_kind"]
