"""P5 — run the dead-rules engine over an OCR history and record the result.

This is the confluence point: it pulls one OCR history through the host
contract (so it never touches the main project's ocr_history directly), builds
an Invoice from its payload, loads the tenant's client_rules, runs the engine,
and persists an invoice_risk_checks row. Dedup lookups are left as no-ops in the
sandbox — exact/suspected duplicate detection queries the main project's
ocr_history, which is wired in at migration; the dedup rule logic itself is
already proven in the engine tests.
"""

from __future__ import annotations

import logging
from typing import Optional

from psycopg2.extras import Json

from services.knowledge import contract
from services.knowledge import rules_dal
from services.knowledge.access import AccessibleIds, workspace_filter
from services.knowledge.rules.context import Finding, Invoice, RuleContext
from services.knowledge.rules_engine import run_rules
from services.knowledge.schema import CHECK_SUCCESS, InvoiceRiskCheck

logger = logging.getLogger(__name__)

_RC_COLS = (
    "id, tenant_id, workspace_client_id, history_id, risk_level, "
    "needs_human_review, findings, status, human_status, created_at"
)


def _finding_dict(finding: Finding) -> dict:
    return {
        "rule_id": finding.rule_id,
        "severity": finding.severity,
        "message_key": finding.message_key,
        "evidence": finding.evidence,
        "client_rule_id": finding.client_rule_id,
    }


def _as_check(row: dict) -> InvoiceRiskCheck:
    return InvoiceRiskCheck(
        id=row["id"],
        tenant_id=str(row["tenant_id"]),
        workspace_client_id=row["workspace_client_id"],
        history_id=str(row["history_id"]),
        risk_level=row["risk_level"],
        needs_human_review=row["needs_human_review"],
        findings=row["findings"] or [],
        status=row["status"],
        human_status=row["human_status"],
        created_at=row["created_at"],
    )


def run_risk_check(
    cur, *, identity: contract.Identity, history_id: str
) -> Optional[InvoiceRiskCheck]:
    """Check one OCR history. Returns None if the history is not visible/found."""
    history = contract.get_ocr_history(history_id, identity)
    if history is None:
        return None

    invoice = Invoice.from_payload(history.payload)
    ruleset = rules_dal.load_client_rules(
        cur, tenant_id=identity.tenant_id, workspace_client_id=history.workspace_client_id
    )
    ctx = RuleContext(
        tenant_id=identity.tenant_id,
        workspace_client_id=history.workspace_client_id,
        workspace_client_tax_id=history.payload.get("workspace_client_tax_id"),
        rules=ruleset,
    )
    result = run_rules(invoice, ctx)

    check = _create_risk_check(
        cur,
        tenant_id=identity.tenant_id,
        workspace_client_id=history.workspace_client_id,
        history_id=history_id,
        risk_level=result.risk_level,
        needs_human_review=result.needs_human_review,
        findings=[_finding_dict(f) for f in result.findings],
        created_by=identity.user_id,
    )
    rules_dal.increment_hit_counts(
        cur,
        tenant_id=identity.tenant_id,
        rule_ids=[f.client_rule_id for f in result.findings if f.client_rule_id],
    )
    return check


def _create_risk_check(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int],
    history_id: str,
    risk_level: str,
    needs_human_review: bool,
    findings: list,
    created_by: Optional[str],
) -> InvoiceRiskCheck:
    cur.execute(
        "INSERT INTO invoice_risk_checks "
        "(tenant_id, workspace_client_id, history_id, risk_level, "
        " needs_human_review, findings, status, created_by) "
        f"VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_RC_COLS}",
        (
            tenant_id,
            workspace_client_id,
            history_id,
            risk_level,
            needs_human_review,
            Json(findings),
            CHECK_SUCCESS,
            created_by,
        ),
    )
    return _as_check(cur.fetchone())


def get_latest_risk_check(
    cur, *, tenant_id: str, history_id: str, accessible_ids: AccessibleIds
) -> Optional[InvoiceRiskCheck]:
    where, params = workspace_filter(accessible_ids)
    cur.execute(
        f"SELECT {_RC_COLS} FROM invoice_risk_checks "
        "WHERE tenant_id = %s AND history_id = %s" + where + " ORDER BY id DESC LIMIT 1",
        [tenant_id, history_id, *params],
    )
    row = cur.fetchone()
    return _as_check(row) if row is not None else None


def ensure_risk_check_rls() -> None:
    """B8 RLS:给 invoice_risk_checks 上 tenant policy(幂等 · 独立事务防牵连别的 ensure)。

    tenant_id NOT NULL;workspace_client_id 可空(NULL = firm-wide)。**纯 tenant 不能 tenant_ws**:
    get_latest_risk_check 经 workspace_filter 读 `workspace_client_id IS NULL OR = ANY(...)`(故意含
    firm-wide NULL 行),tenant_ws 的 _WS_MATCH 会隐藏 NULL 行 → 业务破(同 client_rules)。表只在
    alembic 0005 建、无 startup CREATE 钩子 → 独立 ensure_*_rls。force=False:风险引擎两访问点已全走
    get_cursor_rls(tenant)。先验存在防部分库整块失败。
    """
    from core import db
    from core.rls import apply_tenant_rls, existing_tables

    try:
        with db.get_cursor(commit=True) as cur:
            apply_tenant_rls(cur, *existing_tables(cur, ("invoice_risk_checks",)))
    except Exception as e:
        logger.warning(f"ensure_risk_check_rls skipped: {e}")
