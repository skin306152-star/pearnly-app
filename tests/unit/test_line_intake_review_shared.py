import json
import unittest
from pathlib import Path

from services.line_platform.draft_validation import batch_issues, document_issues
from services.line_platform.summary_review_card import build_summary_card, postback_action

ROOT = Path(__file__).resolve().parents[2]


def record(fields: dict, record_id: str = "history-1") -> dict:
    return {"id": record_id, "pages": [{"fields": fields}]}


class SharedSummaryCardTests(unittest.TestCase):
    def test_card_has_one_editor_action_and_no_direct_confirm(self):
        card = build_summary_card(
            title="Review",
            subtitle="Summary",
            alt_text="Review",
            accent="#16873E",
            summary=[],
            detail_label="Items",
            detail_count=12,
            detail_hint="Open details",
            edit_label="Edit details",
            edit_uri="https://pearnly.com/liff/erp?draft=h1",
            discard_action=postback_action("Discard", "discard", "h1"),
        )
        footer = card["contents"]["footer"]["contents"]
        self.assertEqual([item["action"]["type"] for item in footer], ["uri", "postback"])
        self.assertEqual(footer[0]["action"]["label"], "Edit details")
        self.assertNotIn("confirm", json.dumps(card).lower())


class SharedDraftValidationTests(unittest.TestCase):
    def test_batch_blocks_any_unresolved_document(self):
        ready = record(
            {
                "direction": "sales",
                "invoice_number": "INV-1",
                "date": "2026-09-01",
                "items": [{"name": "Lens", "qty": "1", "posting_kind": "stock"}],
            },
            "ready",
        )
        invalid = record(
            {
                "direction": "sales",
                "invoice_number": "INV-2",
                "date": "2026-09-01",
                "items": [{"name": "", "qty": "1", "posting_kind": "stock"}],
            },
            "invalid",
        )
        self.assertEqual(
            batch_issues([ready, invalid], "sales", require_posting_kind=True),
            {"invalid": ["item_name_required:0"]},
        )

    def test_purchase_requires_header_items_and_optional_per_item_kind(self):
        draft = record(
            {
                "seller_name": "Supplier",
                "date": "2026-09-01",
                "total_amount": "120.00",
                "items": [{"name": "Service", "qty": "1"}],
            }
        )
        self.assertEqual(document_issues(draft, "purchase", require_posting_kind=False), [])
        self.assertEqual(
            document_issues(draft, "purchase", require_posting_kind=True),
            ["posting_kind_required:0"],
        )


class SharedEditorSourceTests(unittest.TestCase):
    def test_both_editors_wrap_long_item_names_and_show_queue_state(self):
        cowork_fields = (ROOT / "static/cowork-line-intake/field-editor.js").read_text(
            encoding="utf-8"
        )
        cowork_css = (ROOT / "static/cowork-line-intake/intake.css").read_text(encoding="utf-8")
        erp_fields = (ROOT / "static/erp-line-intake/field-renderer.js").read_text(encoding="utf-8")
        erp_app = (ROOT / "static/erp-line-intake/erp-line-intake.js").read_text(encoding="utf-8")
        erp_css = (ROOT / "static/erp-line-intake/erp-line-intake.css").read_text(encoding="utf-8")
        self.assertIn(":items:", cowork_fields)
        self.assertIn(":item:", erp_fields)
        for source in (cowork_fields, erp_fields):
            self.assertIn("textarea", source)
            self.assertIn("item-field--", source)
        for css in (cowork_css, erp_css):
            self.assertIn(".item-field--name", css)
            self.assertIn("overflow-wrap: anywhere", css)
        self.assertIn("result.push_ok !== true", erp_app)
        self.assertIn("waiting ? 'waiting' : 'confirmed'", erp_app)

    def test_both_products_use_the_same_batch_runtime_and_old_runtime_is_removed(self):
        cowork = (ROOT / "static/cowork-line-intake/index.html").read_text(encoding="utf-8")
        erp = (ROOT / "static/erp-line-intake/index.html").read_text(encoding="utf-8")
        shared = (ROOT / "static/line-intake-review/batch-review.js").read_text(encoding="utf-8")
        source_page = (ROOT / "static/line-intake-review/source-page.js").read_text(
            encoding="utf-8"
        )
        for html in (cowork, erp):
            self.assertIn("/static/line-intake-review/batch-review.js?v=2", html)
            self.assertIn("/static/line-intake-review/source-page.js?v=1", html)
            self.assertIn("/static/line-intake-review/liff-runtime.js?v=1", html)
            self.assertIn("data-dialog-title", html)
        self.assertIn("IntersectionObserver", shared)
        self.assertIn("data-review-search", shared)
        self.assertIn("data-filter", shared)
        self.assertIn('data-review-action="confirm"', shared)
        self.assertIn("fieldPage", source_page)
        self.assertIn("data-review-page", source_page)
        self.assertIn("data-source-page", source_page)
        self.assertFalse((ROOT / "static/erp-line-intake/preview.js").exists())
        self.assertFalse((ROOT / "static/erp-line-intake/discard-dialog.js").exists())


if __name__ == "__main__":
    unittest.main()
