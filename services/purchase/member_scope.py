"""Creator ownership checks for restricted ERP purchase members."""

from core.pos_api import PosError


def _missing() -> None:
    raise PosError("purchase.unexpected", 404)


def assert_doc(cur, tenant_id: str, workspace_client_id: int, doc_id: str, creator) -> None:
    if creator is None:
        return
    cur.execute(
        "SELECT 1 FROM purchase_docs WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND id = %s AND created_by = %s",
        (tenant_id, workspace_client_id, doc_id, creator),
    )
    if cur.fetchone() is None:
        _missing()


def assert_line(cur, tenant_id: str, workspace_client_id: int, line_id: str, creator) -> None:
    if creator is None:
        return
    cur.execute(
        "SELECT 1 FROM purchase_lines l JOIN purchase_docs d "
        "ON d.id = l.purchase_doc_id AND d.tenant_id = l.tenant_id "
        "WHERE l.tenant_id = %s AND l.id = %s AND d.workspace_client_id = %s "
        "AND d.created_by = %s",
        (tenant_id, line_id, workspace_client_id, creator),
    )
    if cur.fetchone() is None:
        _missing()


def assert_attachment(
    cur, tenant_id: str, workspace_client_id: int, attachment_id: str, creator
) -> None:
    if creator is None:
        return
    cur.execute(
        "SELECT 1 FROM purchase_attachments a JOIN purchase_docs d "
        "ON d.id = a.purchase_doc_id AND d.tenant_id = a.tenant_id "
        "WHERE a.tenant_id = %s AND a.id = %s AND d.workspace_client_id = %s "
        "AND d.created_by = %s",
        (tenant_id, attachment_id, workspace_client_id, creator),
    )
    if cur.fetchone() is None:
        _missing()
