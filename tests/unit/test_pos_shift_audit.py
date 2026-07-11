# -*- coding: utf-8 -*-
"""开/交班审计留痕守门(PC-3 · services/pos/shift_audit.py)。

锁定 FK 血泪:收银员令牌 id=cashier_id(非 users.id)→ actor_user_id 必须留 None(否则 FK
违约被静默吞);操作人身份走 actor_username + details。老板/绑主账号令牌(role≠cashier)才把
users.id 填进 actor_user_id。details 带 shift_seq 让台账与审计条对得上同一张班。
"""

import unittest
from unittest import mock

from services.pos import shift_audit

TID = "tenant-1"


class ShiftAuditTests(unittest.TestCase):
    def test_cashier_token_never_puts_cashier_id_in_actor_user_id(self):
        operator = {
            "id": "cashier-uuid",
            "cashier_id": "cashier-uuid",
            "display_name": "Aya",
            "role": "cashier",
        }
        shift = {"id": "shift-1", "shift_seq": 7, "opening_float": 500.0}
        with mock.patch("services.audit.store.insert_operation_log") as ins:
            shift_audit.log_shift_opened(tenant_id=TID, operator=operator, shift=shift)
        kw = ins.call_args.kwargs
        self.assertIsNone(kw["actor_user_id"])  # 绝不塞 cashier_id
        self.assertEqual(kw["action"], "pos.shift.opened")
        self.assertEqual(kw["actor_username"], "Aya")
        self.assertEqual(kw["target_type"], "pos_shift")
        self.assertEqual(kw["target_id"], "shift-1")
        self.assertEqual(kw["details"]["cashier_id"], "cashier-uuid")
        self.assertEqual(kw["details"]["shift_seq"], 7)
        self.assertEqual(kw["details"]["opening_float"], 500.0)

    def test_owner_token_fills_actor_user_id(self):
        operator = {"id": "user-uuid", "username": "boss", "role": "owner"}
        shift = {"id": "shift-2", "shift_seq": 8}
        with mock.patch("services.audit.store.insert_operation_log") as ins:
            shift_audit.log_shift_opened(tenant_id=TID, operator=operator, shift=shift)
        kw = ins.call_args.kwargs
        self.assertEqual(kw["actor_user_id"], "user-uuid")
        self.assertEqual(kw["actor_username"], "boss")

    def test_close_carries_cash_reconciliation_details(self):
        operator = {"id": "c", "cashier_id": "c", "display_name": "Ben", "role": "cashier"}
        shift = {
            "id": "shift-3",
            "shift_seq": 9,
            "expected_cash": 1450.0,
            "counted_cash": 1400.0,
            "cash_diff": -50.0,
        }
        with mock.patch("services.audit.store.insert_operation_log") as ins:
            shift_audit.log_shift_closed(tenant_id=TID, operator=operator, shift=shift)
        kw = ins.call_args.kwargs
        self.assertEqual(kw["action"], "pos.shift.closed")
        self.assertIsNone(kw["actor_user_id"])
        self.assertEqual(kw["details"]["cash_diff"], -50.0)
        self.assertEqual(kw["details"]["expected_cash"], 1450.0)
        self.assertEqual(kw["details"]["counted_cash"], 1400.0)
        self.assertEqual(kw["details"]["shift_seq"], 9)


if __name__ == "__main__":
    unittest.main()
