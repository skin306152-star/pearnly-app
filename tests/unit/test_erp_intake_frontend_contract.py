from pathlib import Path

ROOT = Path(__file__).parents[2]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_erp_entry_reuses_dms_and_locks_direction():
    assert "sessionStorage" in read("src/home/erp-intake.ts")
    assert "erpIntakeDirection" in read("src/home/dms-intake-invoice.ts")
    assert "isErpEntry" in read("src/home/dms-intake.ts")


def test_legacy_main_entry_keeps_cowork_recognition_only_semantics():
    adapter = read("src/home/erp-intake.ts")
    conversion = read("src/home/dms-intake-review-convert.ts")
    assert "window._entry === 'main'" in adapter
    assert "localStorage.getItem('pearnly_entry') === 'main'" in adapter
    assert "else if (!isCoworkEntry())" in conversion


def test_dedicated_erp_line_uses_the_shared_scoped_catalog_refresh():
    app = read("static/erp-line-intake/erp-line-intake.js")
    i18n = read("static/erp-line-intake/i18n.js")
    assert "/api/line/erp/draft/" in app
    assert "'/target/'" in app
    assert "'/refresh'" in app
    assert "T.refreshTarget(api, path)" in app
    assert "catalog_refresh_request_id" in app
    assert "catalog_refresh_revision" in app
    assert i18n.count("loadingAccounts:") == 4
    assert i18n.count("loadingAccountsLong:") == 4
    assert i18n.count("loadAccountsFailed:") == 4


def test_erp_empty_ocr_line_does_not_guess_quantity_or_amount():
    recognize = read("src/home/dms-intake-invoice-recognize.ts")
    assert "{ name: '', qty: '', price: '', subtotal: '', posting_kind: '' }" in recognize
    assert "qty: '1', price: amount" not in recognize


def test_erp_review_has_batch_default_per_line_override_and_discard_action():
    review = read("src/home/dms-intake-review.ts")
    posting = read("src/home/dms-intake-review-posting.ts")
    assert "posting_kind" in review
    assert "data-iv-posting-default" in review
    assert "applyPostingDefault" in posting
    assert "confirmed.has(index)" in posting
    assert "missingPostingKind" in posting
    assert "item.name" not in posting
    assert "item.qty" not in posting
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


def test_erp_cards_do_not_turn_an_unknown_load_state_into_create_mode():
    card = read("src/home/dms-intake-erp-cards.ts")
    push = read("src/home/dms-intake-erp-push.ts")

    assert "card.dataset.erpLoaded = 'true'" in card
    assert "card.dataset.erpLoaded !== 'true'" in card
    assert "fetchErpEndpoints(false, [], true)" in card
    assert "if (!r.ok) throw new Error" in push
    assert "if (failOnError) throw error" in push


def test_erp_target_detection_uses_compact_cached_readiness_before_ocr_and_push():
    push = read("src/home/dms-intake-erp-push.ts")
    invoice = read("src/home/dms-intake-invoice.ts")
    invoice_erp = read("src/home/dms-intake-invoice-erp.ts")
    submit = read("src/home/dms-intake-invoice-submit.ts")
    batch = read("src/home/dms-intake-batch-submit.ts")
    assert "/test-connection" not in push
    assert "mrErpConfigured" in push
    assert "connection_state" in push
    assert "ready: state === 'online'" in push
    assert "ensureErpTargetReady" not in push
    assert "await preflightInvoiceErp(IV)" in invoice
    assert "state.endpoints = await fetchErpEndpoints(true)" in invoice_erp
    assert "await fetchErpEndpoints(true" in submit
    assert "await fetchErpEndpoints(true" in batch
    assert ".filter((e) => e.enabled !== false)" not in submit


def test_step_four_uses_one_card_with_cascading_express_target_fields():
    accounts = read("src/home/dms-intake-erp-accounts.ts")
    refresh = read("src/home/dms-intake-erp-catalog-refresh.ts")
    cards = read("src/home/dms-intake-erp-push.ts")
    css = read("static/home-49-dms-intake.css")
    invoice = read("src/home/dms-intake-invoice.ts")
    batch = read("src/home/dms-intake-batch-submit.ts")
    submit = read("src/home/dms-intake-invoice-submit.ts")

    assert "root_key" in accounts
    assert "accountChoicesForSelectedRoot" in accounts
    assert "loadErpAccountChoices" in accounts
    assert "account_catalog_loaded" in accounts
    assert "account_catalog_error" in accounts
    assert "endpoint.selected_account_key = selectedAccount?.key || ''" in accounts
    assert "/target-projection`" in refresh
    assert "cache: 'no-store'" in refresh
    assert "AbortController" in refresh
    assert "Math.min(remaining, FETCH_TIMEOUT_MS)" in refresh
    assert "window.setTimeout(onSlow, SLOW_NOTICE_MS)" in refresh
    assert "TOTAL_TIMEOUT_MS = 930_000" in refresh
    assert "requestId: string; revision: number" in refresh
    assert "snapshotRevision !== revision" in refresh
    assert "catalogLoads.delete(endpoint)" in accounts
    assert "endpoint.account_catalog_refresh_request_id = undefined" in accounts
    assert "endpoint.account_catalog_projection_revision = undefined" in accounts
    assert "endpoint.account_catalog_refresh_request_id = fresh.requestId" in accounts
    assert "endpoint.account_catalog_projection_revision = fresh.revision" in accounts
    assert "selectedCatalogEvidence" in submit
    assert "selectedCatalogEvidence" in batch
    assert "body.target_refresh_request_id = catalogEvidence.requestId" in cards
    assert "body.target_projection_revision = catalogEvidence.revision" in cards
    assert "endpoint.account_catalog_loading || endpoint.account_catalog_error" in accounts
    assert "data-erp-root-select=" in cards
    assert "data-erp-account-select=" in cards
    assert "data-erp-catalog-refresh=" in cards
    assert "data-erp-catalog-armed=" in cards
    assert "data-erp-catalog-lazy=" not in cards
    assert 'class="dx-erp-fields-loading"' in cards
    assert 'aria-live="polite"' in cards
    assert "'dx-erp-catalog-loading'" in cards
    assert "'dx-erp-catalog-still-scanning'" in cards
    assert "dx-erp-fields-error" in cards
    assert "'/api/erp/endpoints?compact=true'" in cards
    assert "probed.map(enrichEndpointAccountChoices)" not in cards
    assert 'class="dx-erp-fields${' in cards
    assert 'class="dx-erp-fields single${' in cards
    assert 'class="dx-erp-head"' in cards
    assert 'class="dx-erp-account"' not in cards
    assert ".dx-erp-fields" in css
    assert ".dx-erp-fields-loading" in css
    assert "@keyframes dx-erp-spin" in css
    assert ".dx-erp-account{" not in css
    interaction = read("src/home/dms-intake-erp-catalog-interaction.ts")
    assert "preOpenErpCatalog" in invoice
    assert "preOpenErpCatalog" in batch
    assert "changeErpCatalogSelection" in invoice
    assert "changeErpCatalogSelection" in batch
    assert "selectErpRoot(endpoints" in interaction
    assert "selectErpAccount(endpoints" in interaction
    assert "consumeErpCatalogArm" in interaction
    assert "loadErpAccountChoices" in interaction
    assert "erpCatalogPointerOpen" in interaction
    assert "dx-erp-catalog-load-failed" in invoice
    assert "dx-erp-catalog-load-failed" in batch
    assert "isErpAccountSelectionComplete" in submit
    assert "isErpAccountSelectionComplete" in batch
    intake = read("src/home/dms-intake.ts")
    assert "addEventListener('pointerdown'" in intake
    assert "addEventListener('focusin'" in intake
    assert "ev.preventDefault()" in intake


def test_removed_posting_preview_is_not_registered_or_rendered():
    assert not (ROOT / "src/home/dms-intake-posting-preview.ts").exists()
    assert not (ROOT / "routes/erp_posting_preview_routes.py").exists()
    assert not (ROOT / "services/erp/express_push/posting_preview.py").exists()
    routes = read("routes/erp_routes.py")
    assert "posting-preview" not in routes
    assert "posting-profile" not in routes
    assert "postingPreview" not in read("src/home/dms-intake-invoice-submit.ts")
    assert "dxpp-" not in read("static/i18n-data.js")


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
