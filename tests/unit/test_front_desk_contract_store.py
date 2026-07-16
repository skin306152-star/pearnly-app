# -*- coding: utf-8 -*-
"""前门合同存储 · 状态机校验 + 暂存往返 + DDL 面(services/front_desk/contract_store.py)。

confirm 的 fail-closed 校验(合同不存在/态不可确认/客户未点/期间缺/意图未开放)用假游标验,
不碰真库;真库全链(开工单 + register_file + sha256)在 tests/integration。暂存往返验加密写
helper 复用(禁裸 open)+ read_bytes 明文回读一致。
"""

import os
import tempfile
import unittest

from services.front_desk import contract_store
from services.workorder import storage
from tests.unit._route_contract_fakes import FakeCur


def _contract(**over):
    base = {
        "id": "c-1",
        "status": contract_store.STATUS_DRAFT,
        "workspace_client_id": 7,
        "period": "2569-05",
        "intent": "monthly_vat",
        "work_order_id": None,
    }
    base.update(over)
    return base


class ConfirmValidationTests(unittest.TestCase):
    def _confirm(self, fetch):
        return contract_store.confirm(
            FakeCur(fetch=fetch), tenant_id="t-1", contract_id="c-1", actor="user:1"
        )

    def test_contract_not_found(self):
        with self.assertRaises(contract_store.FrontDeskError) as ctx:
            self._confirm(None)
        self.assertEqual(ctx.exception.code, "front_desk.contract_not_found")

    def test_not_confirmable_status(self):
        with self.assertRaises(contract_store.FrontDeskError) as ctx:
            self._confirm(_contract(status=contract_store.STATUS_DELIVERED))
        self.assertEqual(ctx.exception.code, "front_desk.not_confirmable")

    def test_client_required_is_account_redline(self):
        with self.assertRaises(contract_store.FrontDeskError) as ctx:
            self._confirm(_contract(workspace_client_id=None))
        self.assertEqual(ctx.exception.code, "front_desk.client_required")

    def test_period_required(self):
        with self.assertRaises(contract_store.FrontDeskError) as ctx:
            self._confirm(_contract(period=None))
        self.assertEqual(ctx.exception.code, "front_desk.period_required")

    def test_disabled_intent_rejected(self):
        with self.assertRaises(contract_store.FrontDeskError) as ctx:
            self._confirm(_contract(intent="digitize"))
        self.assertEqual(ctx.exception.code, "front_desk.intent_not_enabled")

    def test_unknown_intent_rejected(self):
        with self.assertRaises(contract_store.FrontDeskError) as ctx:
            self._confirm(_contract(intent="pnd50"))
        self.assertEqual(ctx.exception.code, "front_desk.intent_not_enabled")


class PublicViewTests(unittest.TestCase):
    def test_hides_file_ref_exposes_display_fields(self):
        view = contract_store.public_view(
            _contract(work_order_id="wo-9"),
            files=[
                {
                    "id": "f1",
                    "original_name": "IMG.jpg",
                    "status": "staged",
                    "file_ref": "/secret/path.enc",
                }
            ],
        )
        self.assertEqual(view["intent"], "monthly_vat")
        self.assertEqual(view["work_order_id"], "wo-9")
        self.assertEqual(view["files"][0]["name"], "IMG.jpg")
        self.assertNotIn("file_ref", view["files"][0])  # 绝对路径不外泄

    def test_files_omitted_when_not_passed(self):
        view = contract_store.public_view(_contract())
        self.assertNotIn("files", view)


class StageRoundTripTests(unittest.TestCase):
    def test_stage_writes_via_crypto_helper_and_reads_back_plaintext(self):
        with tempfile.TemporaryDirectory() as d:
            old = os.environ.get("WORKORDER_STORAGE_DIR")
            os.environ["WORKORDER_STORAGE_DIR"] = d
            try:
                content = b"hello front desk \xf0\x9f\x93\x8e"
                path = contract_store.stage_file("t-1-aaaa", "c-42", content, ".pdf")
                self.assertTrue(path.is_file())
                self.assertEqual(storage.read_bytes(path), content)  # 明文往返一致
            finally:
                if old is None:
                    os.environ.pop("WORKORDER_STORAGE_DIR", None)
                else:
                    os.environ["WORKORDER_STORAGE_DIR"] = old


class SchemaFaceTests(unittest.TestCase):
    def test_two_tables_and_rls_targets_aligned(self):
        joined = " ".join(contract_store._TABLES)
        self.assertIn("ai_goal_contracts", joined)
        self.assertIn("ai_contract_files", joined)
        self.assertEqual(
            set(contract_store._RLS_TABLES), {"ai_goal_contracts", "ai_contract_files"}
        )


if __name__ == "__main__":
    unittest.main()
