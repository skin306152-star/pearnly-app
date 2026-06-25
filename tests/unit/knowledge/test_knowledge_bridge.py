"""The OCR-exception bridge: OCR fields -> engine -> exception store.

These exercise the unified path (KNOWLEDGE_RULES on) without a database: the
client_rules load, workspace lookup, and dedup queries are injected, and
insert_exception / is_exception_whitelisted are faked so each test asserts which
findings the bridge would write. Engine rule logic itself is covered in
test_rules_engine; here the concern is the OCR mapping and the write / whitelist
/ enabled-group gate. Per plan P2, each enabled rule gets a paired sample: one
invoice that must trigger it and a clean one that must not.
"""

from contextlib import contextmanager
from unittest.mock import patch

from services.exceptions import knowledge_bridge as kb
from services.knowledge.rules.context import ClientRuleSet
from services.knowledge.rules.validity import valid_thai_tax_id
from services.knowledge.schema import (
    RULE_AMOUNT_LIMIT,
    RULE_NO_AUTO_PUSH_CATEGORY,
    RULE_SUPPLIER_FORCE_REVIEW,
    SUBJECT_CATEGORY,
    SUBJECT_GLOBAL,
    SUBJECT_SUPPLIER,
    ClientRule,
)

_VALID_SELLER = "1234567890121"  # valid Thai tax-id checksum (shared with engine tests)


def _valid_tax_id(prefix="010553600002"):
    for digit in range(10):
        candidate = prefix + str(digit)
        if valid_thai_tax_id(candidate):
            return candidate
    raise AssertionError("no valid check digit found")


def _ruleset(rule_type, subject_type, subject_key, body, severity=None):
    rule = ClientRule(
        id=1,
        tenant_id="t1",
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
        created_at=None,
    )
    return ClientRuleSet.from_rules([rule])


class _Recorder:
    """Stands in for the exception store, recording what would be written."""

    def __init__(self, whitelisted=()):
        self.inserted = []
        self._whitelisted = set(whitelisted)
        self._next_id = 0

    def insert_exception(self, **kwargs):
        self.inserted.append(kwargs)
        self._next_id += 1
        return self._next_id

    def is_exception_whitelisted(self, user_id, tenant_id, seller_name, rule_code):
        return rule_code in self._whitelisted

    def rule_codes(self):
        return [row["rule_code"] for row in self.inserted]


@contextmanager
def _wired(recorder, *, exact=None, suspected=(), ruleset=None):
    """Isolate run_and_record from the database, injecting dedup + client rules."""
    loaded = ruleset if ruleset is not None else ClientRuleSet()

    def fake_lookups(**kwargs):
        return (lambda s, n: exact), (lambda s, t, d: list(suspected))

    with (
        patch.object(kb, "_load_ruleset", lambda *a, **k: loaded),
        patch.object(kb, "_resolve_workspace_client_id", lambda *a, **k: None),
        patch.object(kb, "make_dedup_lookups", fake_lookups),
        patch.object(kb.db, "insert_exception", recorder.insert_exception),
        patch.object(kb.db, "is_exception_whitelisted", recorder.is_exception_whitelisted),
    ):
        yield


def _run(
    fields,
    *,
    seller_name="ACME Co",
    invoice_no="INV-1",
    total_amount=None,
    recorder=None,
    exact=None,
    suspected=(),
    ruleset=None,
):
    rec = recorder or _Recorder()
    with _wired(rec, exact=exact, suspected=suspected, ruleset=ruleset):
        high = kb.run_and_record(
            history_id="11111111-1111-1111-1111-111111111111",
            user_id="u1",
            tenant_id="t1",
            seller_name=seller_name,
            invoice_no=invoice_no,
            total_amount=total_amount,
            fields=fields,
        )
    return rec, high


def test_build_invoice_maps_ocr_keys():
    inv = kb.build_invoice(
        {
            "seller_tax": "0105536000021",
            "buyer_tax": "0994000000010",
            "subtotal": "1,000.00",
            "vat": "70.00",
            "category": "rent",
            "items": [{"name": "x", "qty": "2", "price": "500", "subtotal": "1000"}],
        },
        invoice_no="INV-9",
        seller_name="ACME",
        total_amount=1070.0,
    )
    assert inv.seller_tax_id == "0105536000021"
    assert inv.buyer_tax_id == "0994000000010"
    assert inv.net_amount == 1000.0 and inv.vat_amount == 70.0
    assert inv.total_amount == 1070.0
    assert inv.invoice_no == "INV-9"
    assert inv.category == "rent"
    assert inv.line_items == [{"qty": 2.0, "unit_price": 500.0, "amount": 1000.0}]


def test_math_mismatch_writes_high_finding():
    rec, high = _run(
        {"seller_tax": _valid_tax_id(), "subtotal": "1000", "vat": "70"},
        total_amount=2000.0,  # != net + vat (1070)
    )
    assert "R-VAT-02" in rec.rule_codes()
    assert "R-VAT-02" in high


def test_clean_invoice_writes_nothing():
    rec, high = _run(
        {"seller_tax": _valid_tax_id(), "subtotal": "1000", "vat": "70"},
        total_amount=1070.0,
    )
    assert rec.inserted == []
    assert high == []


def test_invalid_seller_tax_id_writes_finding():
    rec, _ = _run({"seller_tax": "12345"})
    assert "R-TAXID-01" in rec.rule_codes()


def test_clean_seller_tax_id_does_not_fire():
    rec, _ = _run({"seller_tax": _valid_tax_id()})
    assert "R-TAXID-01" not in rec.rule_codes()


def test_whitelisted_rule_is_skipped():
    rec = _Recorder(whitelisted={"R-TAXID-01"})
    _run({"seller_tax": "12345"}, recorder=rec)
    assert "R-TAXID-01" not in rec.rule_codes()


def test_disabled_completeness_finding_not_written():
    # The engine produces R-FIELD-* for a bare invoice, but completeness is not in
    # the enabled set yet, so the bridge must not write it.
    assert kb._is_enabled("R-FIELD-02") is False
    rec, _ = _run({}, seller_name=None, invoice_no=None, total_amount=None)
    assert all(not code.startswith("R-FIELD") for code in rec.rule_codes())


def test_exact_duplicate_writes_high_finding():
    rec, high = _run(
        {"seller_tax": _valid_tax_id()},
        exact="99999999-9999-9999-9999-999999999999",
    )
    assert "R-DUP-01" in rec.rule_codes()
    assert "R-DUP-01" in high


def test_no_duplicate_when_lookup_empty():
    rec, _ = _run({"seller_tax": _valid_tax_id()})
    assert "R-DUP-01" not in rec.rule_codes()
    assert "R-DUP-02" not in rec.rule_codes()


def test_dedup_lookup_is_tenant_scoped_and_excludes_self():
    captured = {}

    class _Cur:
        def execute(self, sql, params):
            captured["sql"] = sql
            captured["params"] = list(params)

        def fetchone(self):
            return {"id": "abc"}

        def fetchall(self):
            return [{"id": "abc"}]

    @contextmanager
    def _cursor(*a, **k):
        yield _Cur()

    with patch.object(kb.db, "get_cursor_rls", _cursor):
        exact, _ = kb.make_dedup_lookups(
            user_id="u1", tenant_id="t1", exclude_history_id="self-id", seller_name="ACME"
        )
        result = exact("ignored", "INV-1")

    assert result == "abc"
    assert "tenant_id = %s" in captured["sql"]
    assert "id <> %s::uuid" in captured["sql"]
    assert "self-id" in captured["params"]
    assert "t1" in captured["params"]


def test_future_invoice_date_writes_finding():
    rec, _ = _run({"seller_tax": _VALID_SELLER, "invoice_date": "2999-01-01"})
    assert "R-DATE-01" in rec.rule_codes()


def test_unparseable_invoice_date_writes_finding():
    rec, _ = _run({"seller_tax": _VALID_SELLER, "invoice_date": "not a date"})
    assert "R-DATE-01" in rec.rule_codes()


def test_plausible_invoice_date_does_not_fire():
    rec, _ = _run({"seller_tax": _VALID_SELLER, "invoice_date": "2026-06-01"})
    assert "R-DATE-01" not in rec.rule_codes()


def test_force_review_supplier_writes_finding():
    ruleset = _ruleset(
        RULE_SUPPLIER_FORCE_REVIEW, SUBJECT_SUPPLIER, _VALID_SELLER, {"reason": "watch"}, "high"
    )
    rec, high = _run({"seller_tax": _VALID_SELLER}, ruleset=ruleset)
    assert "R-SUP-02" in rec.rule_codes()
    assert "R-SUP-02" in high


def test_force_review_does_not_fire_for_other_supplier():
    ruleset = _ruleset(
        RULE_SUPPLIER_FORCE_REVIEW, SUBJECT_SUPPLIER, "9999999999999", {"reason": "watch"}, "high"
    )
    rec, _ = _run({"seller_tax": _VALID_SELLER}, ruleset=ruleset)
    assert "R-SUP-02" not in rec.rule_codes()


def test_amount_over_limit_writes_finding():
    ruleset = _ruleset(
        RULE_AMOUNT_LIMIT,
        SUBJECT_SUPPLIER,
        _VALID_SELLER,
        {"limit": 1000, "basis": "total", "period": "per_invoice"},
        "high",
    )
    rec, _ = _run({"seller_tax": _VALID_SELLER}, total_amount=2000.0, ruleset=ruleset)
    assert "R-LIMIT-01" in rec.rule_codes()


def test_amount_within_limit_does_not_fire():
    ruleset = _ruleset(
        RULE_AMOUNT_LIMIT,
        SUBJECT_SUPPLIER,
        _VALID_SELLER,
        {"limit": 1000, "basis": "total", "period": "per_invoice"},
        "high",
    )
    rec, _ = _run({"seller_tax": _VALID_SELLER}, total_amount=500.0, ruleset=ruleset)
    assert "R-LIMIT-01" not in rec.rule_codes()


def test_no_auto_push_category_writes_finding():
    ruleset = _ruleset(RULE_NO_AUTO_PUSH_CATEGORY, SUBJECT_CATEGORY, "entertainment", {})
    rec, _ = _run({"seller_tax": _VALID_SELLER, "category": "entertainment"}, ruleset=ruleset)
    assert "R-CAT-01" in rec.rule_codes()


def test_other_category_does_not_fire_no_auto_push():
    ruleset = _ruleset(RULE_NO_AUTO_PUSH_CATEGORY, SUBJECT_CATEGORY, "entertainment", {})
    rec, _ = _run({"seller_tax": _VALID_SELLER, "category": "rent"}, ruleset=ruleset)
    assert "R-CAT-01" not in rec.rule_codes()


def test_global_amount_limit_fires_for_any_supplier():
    ruleset = _ruleset(
        RULE_AMOUNT_LIMIT,
        SUBJECT_GLOBAL,
        None,  # global: applies to every invoice, replacing the old large_invoice
        {"limit": 50000, "basis": "total", "period": "per_invoice"},
        "high",
    )
    rec, _ = _run({"seller_tax": _VALID_SELLER}, total_amount=60000.0, ruleset=ruleset)
    assert "R-LIMIT-01" in rec.rule_codes()


def test_global_amount_limit_silent_under_limit():
    ruleset = _ruleset(
        RULE_AMOUNT_LIMIT,
        SUBJECT_GLOBAL,
        None,
        {"limit": 50000, "basis": "total", "period": "per_invoice"},
        "high",
    )
    rec, _ = _run({"seller_tax": _VALID_SELLER}, total_amount=40000.0, ruleset=ruleset)
    assert "R-LIMIT-01" not in rec.rule_codes()


def test_amount_limit_notify_line_pushes_without_high_severity():
    ruleset = _ruleset(
        RULE_AMOUNT_LIMIT,
        SUBJECT_SUPPLIER,
        _VALID_SELLER,
        {"limit": 1000, "basis": "total", "period": "per_invoice", "notify_line": True},
        "medium",  # not high, but opted into the LINE push
    )
    rec, line = _run({"seller_tax": _VALID_SELLER}, total_amount=2000.0, ruleset=ruleset)
    assert "R-LIMIT-01" in rec.rule_codes()  # written to the exception store
    assert "R-LIMIT-01" in line  # and pushed to LINE despite being medium


def test_amount_limit_without_notify_line_does_not_push_when_medium():
    ruleset = _ruleset(
        RULE_AMOUNT_LIMIT,
        SUBJECT_SUPPLIER,
        _VALID_SELLER,
        {"limit": 1000, "basis": "total", "period": "per_invoice"},
        "medium",
    )
    rec, line = _run({"seller_tax": _VALID_SELLER}, total_amount=2000.0, ruleset=ruleset)
    assert "R-LIMIT-01" in rec.rule_codes()  # still a finding
    assert "R-LIMIT-01" not in line  # but no LINE push (medium, no opt-in)


def test_held_back_rules_are_not_enabled():
    # Inputs the OCR field dict does not carry yet — keep them off so they cannot
    # silently over-report once the engine runs live.
    for rule_id in ("R-WHT-01", "R-WS-01", "R-BRANCH-01", "R-FIELD-02"):
        assert kb._is_enabled(rule_id) is False


from tests.unit.knowledge._pytest_adapter import build_case  # noqa: E402

TestKnowledgeBridge = build_case(globals(), "TestKnowledgeBridge")
