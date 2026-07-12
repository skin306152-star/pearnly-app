# -*- coding: utf-8 -*-
"""POS 销售、班次、终端和收银员对象绑定守门。"""

import unittest
from unittest import mock

from core.pos_api import PosError
from services.pos import refund, sale, shift


class _Cursor:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


def _shift_row(**overrides):
    row = {
        "id": "shift-1",
        "terminal_id": 3,
        "cashier_id": "cashier-opened",
        "terminal_active": True,
        "cashier_active": True,
    }
    row.update(overrides)
    return row


class SaleBindingTests(unittest.TestCase):
    def test_shift_lookup_is_workspace_scoped(self):
        cur = _Cursor([_shift_row()])
        bound = sale._resolve_sale_binding(
            cur,
            tenant_id="tenant-1",
            workspace_client_id=9,
            shift_id="shift-1",
            terminal_id=None,
            cashier_id="cashier-opened",
        )
        sql, params = cur.calls[0]
        self.assertIn("s.workspace_client_id = %s", sql)
        self.assertIn("FOR UPDATE OF s", sql)
        self.assertEqual(params, ("tenant-1", 9, "shift-1"))
        self.assertEqual(bound, {"terminal_id": 3, "cashier_id": "cashier-opened"})

    def test_cross_workspace_or_closed_shift_is_rejected(self):
        cur = _Cursor([None])
        with self.assertRaises(PosError) as ctx:
            sale._resolve_sale_binding(
                cur,
                tenant_id="tenant-1",
                workspace_client_id=9,
                shift_id="foreign-shift",
                terminal_id=3,
                cashier_id="cashier-1",
            )
        self.assertEqual(ctx.exception.code, "pos.shift_closed")

    def test_missing_operator_cashier_is_rejected_without_fallback(self):
        cur = _Cursor([_shift_row()])
        with self.assertRaises(PosError) as ctx:
            sale._resolve_sale_binding(
                cur,
                tenant_id="tenant-1",
                workspace_client_id=9,
                shift_id="shift-1",
                terminal_id=3,
                cashier_id=None,
            )
        self.assertEqual(ctx.exception.code, "pos.forbidden")
        self.assertEqual(cur.calls, [])

    def test_terminal_must_match_open_shift_and_be_active(self):
        for row, terminal_id, detail in (
            (_shift_row(), 4, "terminal_mismatch"),
            (_shift_row(terminal_active=False), 3, "terminal_inactive"),
        ):
            with self.subTest(detail=detail):
                cur = _Cursor([row])
                with self.assertRaises(PosError) as ctx:
                    sale._resolve_sale_binding(
                        cur,
                        tenant_id="tenant-1",
                        workspace_client_id=9,
                        shift_id="shift-1",
                        terminal_id=terminal_id,
                        cashier_id="cashier-1",
                    )
                self.assertEqual(ctx.exception.code, "pos.shift_closed")
                self.assertEqual(ctx.exception.detail, detail)

    def test_cashier_must_match_locked_shift(self):
        cur = _Cursor([_shift_row()])
        with self.assertRaises(PosError) as ctx:
            sale._resolve_sale_binding(
                cur,
                tenant_id="tenant-1",
                workspace_client_id=9,
                shift_id="shift-1",
                terminal_id=3,
                cashier_id="foreign-cashier",
            )
        self.assertEqual(ctx.exception.code, "pos.shift_closed")
        self.assertEqual(ctx.exception.detail, "cashier_mismatch")

    def test_locked_shift_cashier_must_still_be_active(self):
        cur = _Cursor([_shift_row(cashier_active=False)])
        with self.assertRaises(PosError) as ctx:
            sale._resolve_sale_binding(
                cur,
                tenant_id="tenant-1",
                workspace_client_id=9,
                shift_id="shift-1",
                terminal_id=3,
                cashier_id="cashier-opened",
            )
        self.assertEqual(ctx.exception.code, "pos.cashier_inactive")

    def test_binding_failure_precedes_warehouse_numbering_and_stock(self):
        with (
            mock.patch.object(
                sale,
                "_resolve_sale_binding",
                side_effect=PosError("pos.shift_closed", 409),
            ),
            mock.patch.object(sale.inv_store, "get_or_create_default_warehouse") as warehouse,
            mock.patch.object(sale.numbering, "next_number") as numbering,
            mock.patch.object(sale.stock, "deduct_for_sale") as deduct,
            self.assertRaises(PosError),
        ):
            sale.create_sale(
                _Cursor(),
                tenant_id="tenant-1",
                workspace_client_id=9,
                payload={"shift_id": "shift-1", "lines": []},
            )
        warehouse.assert_not_called()
        numbering.assert_not_called()
        deduct.assert_not_called()


class ShiftBindingTests(unittest.TestCase):
    def test_open_shift_rejects_foreign_terminal_before_insert(self):
        cur = _Cursor()
        with (
            mock.patch.object(shift.cashier_dal, "get_terminal", return_value=None),
            mock.patch.object(shift, "_insert_shift") as insert,
            self.assertRaises(PosError) as ctx,
        ):
            shift.open_shift(
                cur,
                tenant_id="tenant-1",
                workspace_client_id=9,
                terminal_id=3,
                cashier_id="cashier-1",
                opening_float=0,
            )
        self.assertEqual(ctx.exception.code, "pos.not_found")
        insert.assert_not_called()

    def test_open_shift_rejects_inactive_cashier_before_insert(self):
        cur = _Cursor()
        with (
            mock.patch.object(
                shift.cashier_dal,
                "get_terminal",
                return_value={"id": 3, "is_active": True},
            ),
            mock.patch.object(
                shift.cashier_dal,
                "get_cashier",
                return_value={"id": "cashier-1", "is_active": False},
            ),
            mock.patch.object(shift, "_insert_shift") as insert,
            self.assertRaises(PosError) as ctx,
        ):
            shift.open_shift(
                cur,
                tenant_id="tenant-1",
                workspace_client_id=9,
                terminal_id=3,
                cashier_id="cashier-1",
                opening_float=0,
            )
        self.assertEqual(ctx.exception.code, "pos.cashier_inactive")
        insert.assert_not_called()

    def test_close_shift_lookup_and_update_are_workspace_scoped(self):
        cur = _Cursor(
            [
                {"id": "shift-1", "opening_float": 0, "status": "open", "shift_seq": 1},
                {"n": 0, "gross": 0},
                {"chg": 0},
                {
                    "id": "shift-1",
                    "closed_at": None,
                    "expected_cash": 0,
                    "counted_cash": 0,
                    "cash_diff": 0,
                },
            ]
        )
        cur.fetchall = lambda: []
        shift.close_shift(
            cur,
            tenant_id="tenant-1",
            workspace_client_id=9,
            shift_id="shift-1",
            cashier_id="cashier-1",
            counted_cash=0,
        )
        lookup_sql, lookup_params = cur.calls[0]
        self.assertIn("workspace_client_id = %s", lookup_sql)
        self.assertEqual(lookup_params, ("tenant-1", 9, "shift-1", "cashier-1"))
        self.assertIn("FOR UPDATE", lookup_sql)
        update_sql, update_params = cur.calls[-1]
        self.assertIn("workspace_client_id = %s", update_sql)
        self.assertEqual(update_params[-4:], ("tenant-1", 9, "shift-1", "cashier-1"))
        self.assertIn("status = 'open'", update_sql)


class RefundBindingTests(unittest.TestCase):
    def test_refund_locks_current_cashier_shift(self):
        cur = _Cursor()
        open_shift = {"id": "shift-now", "terminal_id": 3}
        with (
            mock.patch.object(
                refund.cashier_dal,
                "get_open_shift_for_cashier",
                return_value=open_shift,
            ) as get_shift,
            mock.patch.object(
                refund.sale_binding,
                "resolve",
                return_value={"terminal_id": 3, "cashier_id": "cashier-1"},
            ) as resolve,
        ):
            bound = refund._current_refund_binding(
                cur,
                tenant_id="tenant-1",
                workspace_client_id=9,
                cashier_id="cashier-1",
            )
        self.assertEqual(
            bound,
            {"shift_id": "shift-now", "terminal_id": 3, "cashier_id": "cashier-1"},
        )
        self.assertTrue(get_shift.call_args.kwargs["for_update"])
        self.assertEqual(resolve.call_args.kwargs["shift_id"], "shift-now")


if __name__ == "__main__":
    unittest.main()
