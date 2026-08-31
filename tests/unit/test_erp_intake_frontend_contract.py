from pathlib import Path

ROOT = Path(__file__).parents[2]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_erp_entry_reuses_dms_and_locks_direction():
    assert "sessionStorage" in read("src/home/erp-intake.ts")
    assert "erpIntakeDirection" in read("src/home/dms-intake-invoice.ts")
    assert "isErpEntry" in read("src/home/dms-intake.ts")


def test_erp_empty_ocr_line_does_not_guess_quantity_or_amount():
    recognize = read("src/home/dms-intake-invoice-recognize.ts")
    assert "{ name: '', qty: '', price: '', subtotal: '', posting_kind: '' }" in recognize
    assert "qty: '1', price: amount" not in recognize


def test_erp_review_has_per_line_type_and_discard_action():
    review = read("src/home/dms-intake-review.ts")
    assert "posting_kind" in review
    assert 'data-dx-action="discard"' in review
    assert "/api/erp/intake/discard" in review


def test_erp_nav_exposes_push_surfaces():
    assert "'integrations'" in read("src/home/nav-presets.ts")
    assert "'push-logs'" in read("src/home/route-table.ts")


def test_formal_purchase_and_sales_share_honest_push_contract():
    push = read("src/home/dms-intake-erp-push.ts")
    purchase = read("src/home/purchase-detail.ts")
    sales = read("src/home/sales-record-detail.ts")
    assert "operation_id: operationId()" in push
    assert "d.ok === true" in push
    assert "!r.ok" in push
    for state in ("waiting", "success", "failed", "needs_action"):
        assert state in push
    assert 'id="pur-erp-push"' in purchase
    assert 'id="srd-push"' in sales
    assert "pushStateLabel" in purchase
    assert "pushStateLabel" in sales


def test_push_toast_only_uses_success_tone_for_real_success():
    push = read("src/home/dms-intake-erp-push.ts")
    assert "if (state === 'success') return 'success'" in push
    assert "if (state === 'waiting') return 'info'" in push
    assert "if (state === 'needs_action') return 'warn'" in push
    assert "return 'error'" in push
    for name in (
        "src/home/purchase-detail.ts",
        "src/home/sales-record-detail.ts",
        "src/home/sales-records.ts",
    ):
        source = read(name)
        assert "pushToastKind(outcome)" in source
        assert "['failed', 'needs_action'].includes(outcome) ? 'error' : 'success'" not in source


def test_shared_express_card_uses_safe_projection_and_managed_lifecycle():
    card = read("src/home/dms-intake-erp-cards.ts")
    assert "connection_state" in card
    assert "account_set" in card
    assert "data-erp-toggle" in card
    assert "data-erp-config" in card
    assert "data-erp-enroll" not in card
    assert "data-erp-profile-confirm" not in card
    assert "expected_generation: generation" in card
    assert "operation_id: operationId()" in card


def test_express_pairing_reenables_a_disabled_legacy_endpoint_before_token_issue():
    wizard = read("src/home/erp-express-wizard.ts")
    helper = wizard.index("async function _enableLegacyEndpointForPairing")
    token_flow = wizard.index("async function _genToken")
    enable_call = wizard.index("await _enableLegacyEndpointForPairing", token_flow)
    token_issue = wizard.index("'/agent-token'", token_flow)
    assert helper < token_flow
    assert "binding_generation || 0" in wizard[helper:token_flow]
    assert "JSON.stringify({ enabled: true })" in wizard[helper:token_flow]
    assert enable_call < token_issue
