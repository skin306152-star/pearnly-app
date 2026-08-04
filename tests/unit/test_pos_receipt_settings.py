# -*- coding: utf-8 -*-
"""POS 小票合规字段 ensure + 二维码载荷守门(G1/G4)。

ensure 与 alembic 0094 必须同源(prod 不跑 alembic,漂了 = 生产缺列);qr_payload 是
G2 通路码内容的单一定义处,URL 形态在此钉住。
"""

import inspect
import os
import unittest
from pathlib import Path
from unittest import mock

from services.pos import receipt_settings

_MIGRATION = Path("alembic/versions/0094_pos_receipt_compliance.py")


class EnsureSchemaSyncTests(unittest.TestCase):
    def test_ensure_and_migration_add_the_same_columns(self):
        ensure_src = inspect.getsource(receipt_settings.ensure_receipt_schema)
        mig_src = _MIGRATION.read_text(encoding="utf-8")
        for src in (ensure_src, mig_src):
            self.assertIn("pos_register_no text", src)
            self.assertIn("pos_receipt_qr_enabled", src)
            self.assertIn("DEFAULT FALSE", src)  # 二维码开关默认关(G2 未施工 · 不给死链)

    def test_ensure_runs_ddl_with_commit(self):
        # db.get_cursor 默认不 commit,DDL 不带 commit=True 就是静默没生效。
        executed = []

        class _Cur:
            def execute(self, sql, params=None):
                executed.append(sql)

        class _Ctx:
            def __enter__(self):
                return _Cur()

            def __exit__(self, *a):
                return False

        from core import db

        with mock.patch.object(db, "get_cursor", return_value=_Ctx()) as gc:
            receipt_settings.ensure_receipt_schema()
        self.assertEqual(gc.call_args.kwargs.get("commit"), True)
        self.assertEqual(len(executed), 2)
        self.assertTrue(all("ADD COLUMN IF NOT EXISTS" in sql for sql in executed))

    def test_registered_in_pos_schema_bootstrap(self):
        from services import pos_schema

        src = inspect.getsource(pos_schema.bootstrap_pos_schema)
        self.assertIn("ensure_receipt_schema", src)


class QrPayloadTests(unittest.TestCase):
    def test_default_base_points_to_g2_route(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PEARNLY_BASE_URL", None)
            url = receipt_settings.qr_payload(workspace_client_id=9, receipt_no="ABB-T1-2026-00187")
        self.assertEqual(url, "https://pearnly.com/pos/full-tax-invoice?ws=9&no=ABB-T1-2026-00187")

    def test_base_env_override(self):
        with mock.patch.dict(os.environ, {"PEARNLY_BASE_URL": "https://staging.pearnly.com/"}):
            url = receipt_settings.qr_payload(workspace_client_id=1, receipt_no="X")
        self.assertTrue(url.startswith("https://staging.pearnly.com/pos/full-tax-invoice?"))

    def test_receipt_no_is_url_encoded(self):
        url = receipt_settings.qr_payload(workspace_client_id=1, receipt_no="A B/1#x")
        self.assertIn("no=A%20B/1%23x", url)


if __name__ == "__main__":
    unittest.main()
