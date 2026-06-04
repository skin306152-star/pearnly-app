"""End-to-end: the OCR exception hook through the unified engine path.

Drives the real _async_run_exception_checks (not the bridge in isolation),
faking only the database and the LINE notify helper. The engine is the only rule
source now (no flag, no legacy path), so the invariants are: engine findings
land in the existing exception store, confidence_low still fires alongside them,
and a high-severity finding still triggers the exception_high LINE reminder. No
database, no network.
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


def _run_hook(*, confidence, fields, total_amount, duplicate=None):
    rec = _Recorder()
    notify_high = AsyncMock()
    with (
        patch.object(ec.db, "insert_exception", rec.insert_exception),
        patch.object(ec.db, "is_exception_whitelisted", lambda *a, **k: False),
        patch.object(ec, "_notify_exception_high", notify_high),
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
    return rec, notify_high


def test_engine_findings_coexist_with_confidence_low():
    rec, _ = _run_hook(
        confidence="low",
        fields={"seller_tax": _VALID_SELLER, "subtotal": "1000", "vat": "70"},
        total_amount=2000.0,  # != net + vat -> R-VAT-02
    )
    codes = rec.rule_codes()
    assert "confidence_low" in codes  # OCR-quality signal stays in the hook
    assert "R-VAT-02" in codes  # engine produced the arithmetic finding
    assert "math_mismatch" not in codes  # the retired legacy rule code is gone


def test_high_finding_triggers_line_reminder():
    _, notify_high = _run_hook(
        confidence="high",  # silence confidence_low to isolate the engine finding
        fields={"seller_tax": _VALID_SELLER, "subtotal": "1000", "vat": "70"},
        total_amount=2000.0,
    )
    fired = [call.kwargs.get("rule_code") for call in notify_high.call_args_list]
    assert "R-VAT-02" in fired


def test_clean_invoice_writes_nothing():
    rec, _ = _run_hook(
        confidence="high",
        fields={"seller_tax": _VALID_SELLER, "subtotal": "1000", "vat": "70"},
        total_amount=1070.0,
    )
    assert rec.inserted == []


from tests.unit.knowledge._pytest_adapter import build_case  # noqa: E402

TestExceptionHookIntegration = build_case(globals(), "TestExceptionHookIntegration")
