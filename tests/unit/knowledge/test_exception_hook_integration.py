"""End-to-end: the OCR exception hook through the unified engine path.

Drives the real _async_run_exception_checks (not the bridge in isolation) with
KNOWLEDGE_RULES on and off, faking only the database and the LINE notify helpers.
Asserts the three invariants of the switch: engine findings land in the existing
exception store, confidence_low still fires alongside them, the high-severity
LINE reminder still triggers off the new findings, and flag-off rolls back to the
legacy inline rules. No database, no network.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from services.exceptions import exception_checks as ec
from services.exceptions import knowledge_bridge as kb
from services.knowledge.rules.context import ClientRuleSet

_VALID_SELLER = "1234567890121"  # valid Thai tax-id checksum
_HISTORY_ID = "11111111-1111-1111-1111-111111111111"


class _Recorder:
    def __init__(self):
        self.inserted = []

    def insert_exception(self, **kwargs):
        self.inserted.append(kwargs)
        return len(self.inserted)

    def rule_codes(self):
        return [row["rule_code"] for row in self.inserted]


def _run_hook(*, flag_on, confidence, fields, total_amount, duplicate=None):
    rec = _Recorder()
    notify_high = AsyncMock()
    notify_large = AsyncMock()
    with (
        patch.object(ec, "KNOWLEDGE_RULES_ENABLED", flag_on),
        patch.object(ec.db, "insert_exception", rec.insert_exception),
        patch.object(ec.db, "is_exception_whitelisted", lambda *a, **k: False),
        patch.object(ec, "_notify_exception_high", notify_high),
        patch.object(ec, "_notify_large_invoice", notify_large),
        patch.object(kb, "_load_ruleset", lambda *a, **k: ClientRuleSet()),
        patch.object(kb, "_resolve_workspace_client_id", lambda *a, **k: None),
        patch.object(
            kb,
            "make_dedup_lookups",
            lambda **k: ((lambda s, n: None), (lambda s, t, d: [])),
        ),
    ):
        asyncio.run(
            ec._async_run_exception_checks(
                history_id=_HISTORY_ID,
                user_id="u1",
                tenant_id="t1",
                seller_name="ACME Co",
                invoice_no="INV-1",
                total_amount=total_amount,
                confidence=confidence,
                duplicate=duplicate,
                fields=fields,
            )
        )
    return rec, notify_high, notify_large


def test_flag_on_engine_findings_coexist_with_confidence_low():
    rec, _, _ = _run_hook(
        flag_on=True,
        confidence="low",
        fields={"seller_tax": _VALID_SELLER, "subtotal": "1000", "vat": "70"},
        total_amount=2000.0,  # != net + vat -> R-VAT-02
    )
    codes = rec.rule_codes()
    assert "confidence_low" in codes  # OCR-quality signal stays on the legacy path
    assert "R-VAT-02" in codes  # engine produced the arithmetic finding
    assert "math_mismatch" not in codes  # legacy inline rule did not run


def test_flag_on_high_finding_still_triggers_line_reminder():
    _, notify_high, notify_large = _run_hook(
        flag_on=True,
        confidence="high",  # silence confidence_low to isolate the engine finding
        fields={"seller_tax": _VALID_SELLER, "subtotal": "1000", "vat": "70"},
        total_amount=2000.0,
    )
    fired = [call.kwargs.get("rule_code") for call in notify_high.call_args_list]
    assert "R-VAT-02" in fired
    assert notify_large.called  # large-invoice reminder is independent of findings


def test_flag_off_falls_back_to_legacy_rules():
    rec, _, _ = _run_hook(
        flag_on=False,
        confidence="high",
        fields={"seller_tax": _VALID_SELLER, "subtotal": "1000", "vat": "70"},
        total_amount=2000.0,
    )
    codes = rec.rule_codes()
    assert "math_mismatch" in codes  # legacy inline rule ran
    assert "R-VAT-02" not in codes  # engine path did not


def test_flag_off_clean_invoice_writes_nothing():
    rec, _, _ = _run_hook(
        flag_on=False,
        confidence="high",
        fields={"seller_tax": _VALID_SELLER, "subtotal": "1000", "vat": "70"},
        total_amount=1070.0,
    )
    assert rec.inserted == []


from tests.unit.knowledge._pytest_adapter import build_case  # noqa: E402

TestExceptionHookIntegration = build_case(globals(), "TestExceptionHookIntegration")
