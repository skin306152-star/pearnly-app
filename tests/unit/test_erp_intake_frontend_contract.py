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
