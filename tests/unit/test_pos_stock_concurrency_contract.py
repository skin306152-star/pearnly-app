import unittest
from decimal import Decimal
from unittest import mock

from core.pos_api import PosError
from services.inventory import ledger, store
from services.pos import stock


class PosStockConcurrencyContractTests(unittest.TestCase):
    def test_ledger_passes_negative_guard_to_store(self):
        with (
            mock.patch.object(store, "insert_txn", return_value={"id": "tx"}),
            mock.patch.object(store, "apply_stock_delta", return_value=Decimal("1")) as apply,
        ):
            ledger.apply_movement(
                object(),
                tenant_id="t",
                workspace_client_id=7,
                warehouse_id=1,
                product_id="p",
                batch_id="b",
                txn_type="sale_out",
                qty_delta=-4,
                reject_negative=True,
            )
        self.assertTrue(apply.call_args.kwargs["reject_negative"])

    def test_stock_maps_atomic_guard_to_out_of_stock(self):
        with mock.patch.object(
            stock.ledger, "apply_movement", side_effect=store.InsufficientStockError
        ):
            with self.assertRaises(PosError) as caught:
                stock._apply_sale_moves(
                    object(),
                    tenant_id="t",
                    workspace_client_id=7,
                    warehouse_id=1,
                    product_id="p",
                    moves=[("b", Decimal("4"))],
                    sale_id="s",
                )
        self.assertEqual(caught.exception.code, "pos.out_of_stock")

    def test_explicit_batch_from_other_workspace_rejected_before_stock_lookup(self):
        with (
            mock.patch.object(stock.inv_store, "get_batch", return_value=None),
            mock.patch.object(stock.inv_store, "get_stock_for_update") as get_stock,
        ):
            with self.assertRaises(PosError) as caught:
                stock._check_and_move(
                    object(),
                    tenant_id="t",
                    workspace_client_id=7,
                    warehouse_id=1,
                    product_id="p",
                    batch_id="foreign",
                    qty=Decimal("1"),
                    sale_id="s",
                )
        self.assertEqual(caught.exception.code, "pos.out_of_stock")
        get_stock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
