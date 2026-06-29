# -*- coding: utf-8 -*-
"""反馈闭环 ② · 真 ocr_correction_examples 表端到端隔离 + 捕获 round-trip(REFACTOR-B8 口径)。

用真 ensure_ocr_feedback_table()(建表 + enroll tenant_or_user)+ 真 store(record_corrections /
fetch_examples / record_correction_from_edit),在真 postgres 验:租户 A 的修正例租户 B 读不到;
编辑捕获按主体沉淀、重复修正累加 use_count。CI 默认 skip(无真 DB),本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_ocr_feedback_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"


class OcrFeedbackRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.ocr.feedback import schema, store

        cls.db, cls.store = db, store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS ocr_correction_examples CASCADE")

        schema.ensure_ocr_feedback_table()

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON ocr_correction_examples TO pearnly_app"
            )
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            cur.execute("ALTER TABLE ocr_correction_examples FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute("DROP TABLE IF EXISTS ocr_correction_examples CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE ocr_correction_examples RESTART IDENTITY")

    def _corr(self, field="invoice_number", ai="IV1", fixed="IV-001"):
        return [{"field_name": field, "ai_value": ai, "corrected_value": fixed}]

    def test_cross_tenant_blocked(self):
        self.store.record_corrections(UA, A, "0105556", "A Co", None, self._corr())
        self.store.record_corrections(UB, B, "0105556", "B Co", None, self._corr(fixed="IV-B"))
        # 同卖方税号,但 A 只看到自己的修正
        a = self.store.fetch_examples(UA, A, "0105556")
        self.assertEqual([e["corrected_value"] for e in a], ["IV-001"])
        b = self.store.fetch_examples(UB, B, "0105556")
        self.assertEqual([e["corrected_value"] for e in b], ["IV-B"])

    def test_repeat_correction_bumps_use_count(self):
        self.store.record_corrections(UA, A, "0105556", "A Co", None, self._corr())
        self.store.record_corrections(UA, A, "0105556", "A Co", None, self._corr())
        rows = self.store.fetch_examples(UA, A, "0105556")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["use_count"], 2)

    def test_record_from_edit_roundtrip(self):
        # seed 一条 ocr_history 带 ai_raw,再走捕获入口
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO ocr_history(user_id,tenant_id,filename,ai_raw) "
                "VALUES (%s,%s,'a.pdf',%s::jsonb) RETURNING id",
                (UA, A, '[{"fields":{"invoice_number":"IV1","seller_tax":"0105556"}}]'),
            )
            hid = str(cur.fetchone()["id"])
        corrected = [{"fields": {"invoice_number": "IV-001", "seller_tax": "0105556"}}]
        n = self.store.record_correction_from_edit(UA, A, hid, corrected)
        self.assertEqual(n, 1)
        rows = self.store.fetch_examples(UA, A, "0105556")
        self.assertEqual(rows[0]["corrected_value"], "IV-001")


if __name__ == "__main__":
    unittest.main()
