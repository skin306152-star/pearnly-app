from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class CoworkLineIntakeFrontendContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = ROOT / "static" / "cowork-line-intake"
        cls.html = (folder / "index.html").read_text(encoding="utf-8")
        cls.app = (folder / "app.js").read_text(encoding="utf-8")
        cls.app_compact = " ".join(cls.app.split())
        cls.i18n = (folder / "i18n.js").read_text(encoding="utf-8")
        cls.fields = (folder / "field-editor.js").read_text(encoding="utf-8")
        shared = ROOT / "static" / "line-intake-review"
        cls.runtime = (shared / "liff-runtime.js").read_text(encoding="utf-8")
        cls.review = (shared / "batch-review.js").read_text(encoding="utf-8")
        cls.target_select = (shared / "target-select.js").read_text(encoding="utf-8")
        cls.target_select_compact = " ".join(cls.target_select.split())

    def test_upload_stays_in_line_chat(self):
        combined = self.html + self.app
        self.assertNotIn('type="file"', combined)
        self.assertNotIn("/api/ocr/recognize", combined)
        self.assertIn("liff.getIDToken()", self.runtime)
        self.assertIn("window.lineIntakeLiff", self.app)

    def test_editor_has_independent_scoped_paths_and_full_actions(self):
        self.assertIn("/api/cowork-line/intake/draft/", self.app)
        self.assertNotIn("/api/line/erp/draft/", self.app)
        for action in ("save", "confirm", "discard"):
            self.assertIn("'" + action + "'", self.app)
        for field in ("seller_tax", "buyer_tax", "wht_amount", "total_amount", "items"):
            self.assertIn("'" + field + "'", self.fields)

    def test_target_projection_and_modes_are_rendered_honestly(self):
        for key in (
            "selectable",
            "connection_state",
            "configured",
            "ready_checks",
            "missing",
            "block_reason",
            "setup_action",
        ):
            self.assertIn(key, self.target_select)
        for mode in ("stock", "service", "cash", "credit"):
            self.assertIn("'" + mode + "'", self.target_select)
        self.assertIn("target.workspace_name", self.target_select)

    def test_line_primary_redirect_restores_scoped_draft(self):
        self.assertIn("direct.get('liff.state')", self.runtime)
        self.assertIn("draftFromLocation", self.runtime)
        self.assertLess(
            self.runtime.index("window.liff.init"),
            self.runtime.index("draftFromLocation(options.flow)"),
        )

    def test_confirm_and_recoverable_errors_are_not_reported_as_complete(self):
        self.assertIn("result.saved !== true", self.app)
        self.assertIn("action === 'confirm' && !review.canConfirm()", self.app)
        self.assertIn("result.push_ok !== true", self.app)
        self.assertIn("show('pushFailed', 'error')", self.app)
        self.assertIn("error.status === 409 ? 'recoverable' : 'failed'", self.app)
        self.assertIn("draft_(expired|forbidden)", self.app)
        self.assertIn('data-review-action="confirm"', self.review)
        self.assertIn("confirm.disabled = busy || !report.canConfirm", self.review)

    def test_mrerp_purchase_only_offers_credit(self):
        self.assertIn("purchase ? ''", self.target_select_compact)
        self.assertIn("selection().payment === 'credit'", self.target_select)
        self.assertIn("/^(cash|credit)$/.test", self.target_select)

    def test_four_languages_are_present(self):
        for language in ("th:", "en:", "zh:", "ja:"):
            self.assertIn(language, self.i18n)
        self.assertEqual(self.i18n.count("pushFailed:"), 4)
        self.assertEqual(self.i18n.count("recoverable:"), 4)


if __name__ == "__main__":
    unittest.main()
