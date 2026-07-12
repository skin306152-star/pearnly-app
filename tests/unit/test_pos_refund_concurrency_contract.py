import inspect
import unittest

from services.pos import refund, sale, sales_store


class PosRefundConcurrencyContractTests(unittest.TestCase):
    def test_store_lock_primitives(self):
        self.assertIn('" FOR UPDATE" if for_update', inspect.getsource(sales_store.get_sale))
        self.assertIn('" FOR UPDATE" if for_update', inspect.getsource(sales_store.list_lines))
        self.assertIn("pg_advisory_xact_lock", inspect.getsource(sales_store.lock_client_uuid))

    def test_refund_locks_and_aggregates_duplicate_line_requests(self):
        source = inspect.getsource(refund.refund)
        self.assertLess(source.index("_current_refund_binding"), source.index("for_update=True"))
        self.assertIn("requested_qty.get(line_id", source)
        self.assertIn('existing["sale_type"] != "refund"', source)
        self.assertIn("refund_of_sale_id", source)

    def test_void_locks_shift_sale_and_lines_before_checks(self):
        source = inspect.getsource(sale.void_sale)
        shift_at = source.index("_shift_is_open")
        sale_at = source.index("for_update=True", source.index("sales_store.get_sale", shift_at))
        lines_at = source.index("sales_store.list_lines", sale_at)
        refunds_at = source.index("sales_store.has_refunds", sale_at)
        self.assertLess(shift_at, sale_at)
        self.assertLess(sale_at, lines_at)
        self.assertLess(lines_at, refunds_at)
        self.assertIn('expected_status="completed"', source)

    def test_status_update_is_compare_and_set(self):
        source = inspect.getsource(sales_store.set_status)
        self.assertIn("AND status = %s", source)
        self.assertIn("cur.rowcount == 1", source)


if __name__ == "__main__":
    unittest.main()
