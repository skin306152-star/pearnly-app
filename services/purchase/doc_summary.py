"""Purchase document totals for list and dashboard cards."""

from typing import Optional


def summarize(cur, tenant_id, workspace_client_id, *, created_by: Optional[str] = None) -> dict:
    creator_sql = " AND created_by = %s" if created_by is not None else ""
    creator_params = (created_by,) if created_by is not None else ()
    cur.execute(
        """
        SELECT
          COALESCE(SUM(grand_total) FILTER (
            WHERE doc_kind IN ('purchase_invoice','purchase_order')
              AND doc_date >= date_trunc('month', CURRENT_DATE)), 0) AS goods_total,
          COALESCE(SUM(grand_total) FILTER (
            WHERE doc_kind = 'expense'
              AND doc_date >= date_trunc('month', CURRENT_DATE)), 0) AS expense_total,
          COALESCE(SUM(vat_amount) FILTER (
            WHERE doc_kind = 'purchase_invoice' AND has_vat
              AND doc_date >= date_trunc('month', CURRENT_DATE)), 0) AS vat_claimable,
          COALESCE(SUM(net_payable - paid_amount) FILTER (
            WHERE payment_status <> 'paid'), 0) AS unpaid_total
        FROM purchase_docs
        WHERE tenant_id = %s AND workspace_client_id = %s AND status = 'posted'
        """ + creator_sql,
        (tenant_id, workspace_client_id, *creator_params),
    )
    row = cur.fetchone()
    return {
        "goods_total": row["goods_total"],
        "expense_total": row["expense_total"],
        "vat_claimable": row["vat_claimable"],
        "unpaid_total": row["unpaid_total"],
    }
