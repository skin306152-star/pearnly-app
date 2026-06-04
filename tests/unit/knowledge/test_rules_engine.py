"""Dead-rules engine: a clean invoice fires nothing; each rule fires on its case.

The clean invoice is the shared negative sample — every rule must leave it
alone. Each test then mutates one aspect (or supplies one client rule / dedup
hit) and asserts exactly that rule_id appears. No database, no network.
"""

from datetime import date, datetime

import pytest

from services.knowledge.rules.context import ClientRuleSet, Invoice, RuleContext
from services.knowledge.rules_engine import run_rules
from services.knowledge.schema import (
    RULE_ACCOUNTING_PERIOD,
    RULE_AMOUNT_LIMIT,
    RULE_FEATURE_TOGGLE,
    RULE_NO_AUTO_PUSH_CATEGORY,
    RULE_SUPPLIER_ALLOWLIST,
    RULE_SUPPLIER_FORCE_REVIEW,
    RULE_WHT_RATE,
    SUBJECT_CATEGORY,
    SUBJECT_GLOBAL,
    SUBJECT_SUPPLIER,
    ClientRule,
)

_TODAY = date(2026, 6, 4)
_SELLER = "1234567890121"  # valid checksum
_BUYER = "1111111111119"  # valid checksum


def _clean() -> Invoice:
    return Invoice(
        seller_tax_id=_SELLER,
        seller_name="ACME Co.",
        seller_address="123 Bangkok",
        seller_branch="00000",
        buyer_tax_id=_BUYER,
        buyer_name="Buyer Co.",
        buyer_address="456 Bangkok",
        invoice_no="INV-001",
        invoice_date="2026-06-01",
        line_items=[{"desc": "svc", "qty": 2, "unit_price": 500.0, "amount": 1000.0}],
        net_amount=1000.0,
        vat_amount=70.0,
        total_amount=1070.0,
        doc_type="full_tax_invoice",
        raw_text="ใบกำกับภาษี ...",
    )


def _ctx(**kw) -> RuleContext:
    kw.setdefault("tenant_id", "t")
    kw.setdefault("today", _TODAY)
    return RuleContext(**kw)


def _rule(rule_type, subject_type, subject_key, body, severity=None) -> ClientRule:
    return ClientRule(
        id=1,
        tenant_id="t",
        workspace_client_id=None,
        rule_type=rule_type,
        subject_type=subject_type,
        subject_key=subject_key,
        rule_body=body,
        severity=severity,
        is_active=True,
        effective_from=None,
        effective_to=None,
        origin="manual",
        created_at=datetime(2026, 6, 4),
    )


def _fired(invoice, ctx) -> set:
    return {f.rule_id for f in run_rules(invoice, ctx).findings}


def test_clean_invoice_fires_nothing():
    assert _fired(_clean(), _ctx()) == set()


def test_seller_tax_id_invalid():
    inv = _clean()
    inv.seller_tax_id = "1234567890120"
    assert "R-TAXID-01" in _fired(inv, _ctx())


def test_buyer_tax_id_invalid():
    inv = _clean()
    inv.buyer_tax_id = "1111111111118"
    assert "R-TAXID-02" in _fired(inv, _ctx())


def test_tax_id_placeholder():
    inv = _clean()
    inv.seller_tax_id = "2222222222222"
    fired = _fired(inv, _ctx())
    assert "R-TAXID-03" in fired


def test_date_unparseable_and_future():
    bad = _clean()
    bad.invoice_date = "not-a-date"
    assert "R-DATE-01" in _fired(bad, _ctx())
    future = _clean()
    future.invoice_date = "2027-01-01"
    assert "R-DATE-01" in _fired(future, _ctx())


def test_accounting_period():
    ruleset = ClientRuleSet.from_rules(
        [_rule(RULE_ACCOUNTING_PERIOD, SUBJECT_GLOBAL, None, {"mode": "current_month"})]
    )
    inv = _clean()
    inv.invoice_date = "2026-04-15"  # outside June
    assert "R-DATE-02" in _fired(inv, _ctx(rules=ruleset))


def test_branch_format():
    inv = _clean()
    inv.seller_branch = "12"
    assert "R-BRANCH-01" in _fired(inv, _ctx())


def test_vat_rate_mismatch():
    inv = _clean()
    inv.vat_amount = 50.0
    inv.total_amount = 1050.0
    assert "R-VAT-01" in _fired(inv, _ctx())


def test_exempt_skips_vat_rate():
    inv = _clean()
    inv.vat_amount = 0.0
    inv.total_amount = 1000.0
    inv.tax_exempt = True
    assert "R-VAT-01" not in _fired(inv, _ctx())


def test_total_mismatch():
    inv = _clean()
    inv.total_amount = 9999.0
    assert "R-VAT-02" in _fired(inv, _ctx())


def test_line_sum_mismatch():
    inv = _clean()
    inv.line_items = [{"qty": 1, "unit_price": 1.0, "amount": 1.0}]
    assert "R-SUM-01" in _fired(inv, _ctx())


def test_line_amount_mismatch():
    inv = _clean()
    inv.line_items = [{"qty": 2, "unit_price": 500.0, "amount": 999.0}]
    # the bad line also breaks the net sum; assert the per-line rule specifically
    assert "R-LINE-01" in _fired(inv, _ctx())


def test_multipage_mismatch():
    inv = _clean()
    inv.is_multipage = True
    inv.pages = [{"net_amount": 400.0, "vat_amount": 28.0, "total_amount": 428.0}]
    assert "R-MULTIPAGE-01" in _fired(inv, _ctx())


def test_wht_rate_mismatch():
    ruleset = ClientRuleSet.from_rules(
        [_rule(RULE_WHT_RATE, SUBJECT_CATEGORY, "service", {"expected_rate": 3.0})]
    )
    inv = _clean()
    inv.category = "service"
    inv.declared_wht_rate = 5.0
    assert "R-WHT-01" in _fired(inv, _ctx(rules=ruleset))


def test_duplicate_exact():
    ctx = _ctx(find_exact_duplicate=lambda s, n: "hist-9")
    assert "R-DUP-01" in _fired(_clean(), ctx)


def test_duplicate_suspected():
    ctx = _ctx(find_suspected_duplicates=lambda s, t, d: ["hist-7"])
    assert "R-DUP-02" in _fired(_clean(), ctx)


def test_missing_tax_invoice_marker():
    inv = _clean()
    inv.raw_text = "ใบเสร็จ"
    assert "R-FIELD-01" in _fired(inv, _ctx())


def test_seller_incomplete():
    inv = _clean()
    inv.seller_address = None
    assert "R-FIELD-02" in _fired(inv, _ctx())


def test_buyer_incomplete():
    inv = _clean()
    inv.buyer_name = None
    assert "R-FIELD-03" in _fired(inv, _ctx())


def test_invoice_identity_incomplete():
    inv = _clean()
    inv.invoice_no = None
    assert "R-FIELD-04" in _fired(inv, _ctx())


def test_amounts_incomplete():
    inv = _clean()
    inv.net_amount = None
    inv.vat_amount = None
    assert "R-FIELD-05" in _fired(inv, _ctx())


def test_supplier_not_allowlisted():
    ruleset = ClientRuleSet.from_rules(
        [
            _rule(RULE_FEATURE_TOGGLE, SUBJECT_GLOBAL, "supplier_allowlist", {"enabled": True}),
            _rule(RULE_SUPPLIER_ALLOWLIST, SUBJECT_SUPPLIER, "9999999999999", {}),
        ]
    )
    assert "R-SUP-01" in _fired(_clean(), _ctx(rules=ruleset))


def test_supplier_allowlist_off_by_default():
    ruleset = ClientRuleSet.from_rules(
        [_rule(RULE_SUPPLIER_ALLOWLIST, SUBJECT_SUPPLIER, "9999999999999", {})]
    )
    assert "R-SUP-01" not in _fired(_clean(), _ctx(rules=ruleset))


def test_supplier_force_review():
    ruleset = ClientRuleSet.from_rules(
        [_rule(RULE_SUPPLIER_FORCE_REVIEW, SUBJECT_SUPPLIER, _SELLER, {"reason": "new"})]
    )
    result = run_rules(_clean(), _ctx(rules=ruleset))
    assert "R-SUP-02" in {f.rule_id for f in result.findings}
    assert result.needs_human_review is True


def test_wrong_workspace():
    inv = _clean()
    assert "R-WS-01" in _fired(inv, _ctx(workspace_client_tax_id="2222222222229"))


def test_amount_over_limit():
    ruleset = ClientRuleSet.from_rules(
        [
            _rule(
                RULE_AMOUNT_LIMIT,
                SUBJECT_SUPPLIER,
                _SELLER,
                {"limit": 500.0, "basis": "total", "period": "per_invoice"},
            )
        ]
    )
    assert "R-LIMIT-01" in _fired(_clean(), _ctx(rules=ruleset))


def test_category_no_auto_push():
    ruleset = ClientRuleSet.from_rules(
        [_rule(RULE_NO_AUTO_PUSH_CATEGORY, SUBJECT_CATEGORY, "entertainment", {})]
    )
    inv = _clean()
    inv.category = "entertainment"
    assert "R-CAT-01" in _fired(inv, _ctx(rules=ruleset))


def test_no_llm_imported_by_engine():
    import sys

    import services.knowledge.rules_engine  # noqa: F401

    assert "openai" not in sys.modules
    assert "anthropic" not in sys.modules


from tests.unit.knowledge._pytest_adapter import build_case  # noqa: E402

TestRulesEngine = build_case(globals(), "TestRulesEngine")
