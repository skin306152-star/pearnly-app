import json
import unittest
from unittest import mock

from services.erp import mrerp_dms_sales_readback as readback

ROW = """
dt::<div data-val="77" data-allo="g"><div class="detaildata"><div><div>
<p>-</p><p>แบบร่าง</p></div><div><p>BK-001</p><p>01/09/2569</p>
<p>15/09/2569</p></div><div><p>sale01</p><p>ลูกค้า ทดสอบ</p></div></div>
<div><div><p>Model X</p><p>RED</p></div><div><p>-</p><p>รออนุมัติ</p></div>
<div><p>SO-9</p><p>ENG-8</p></div></div></div><div class="statuscf"><p>ผู้จัดทำ</p></div></div>
"""


class ParseSalesRowsTests(unittest.TestCase):
    def test_parses_native_status_without_calling_draft_a_sale(self):
        rows = readback.parse_sales_rows(ROW)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["record_status"], "แบบร่าง")
        self.assertEqual(rows[0]["booking_no"], "BK-001")
        self.assertEqual(rows[0]["advisor"], "sale01")
        self.assertEqual(rows[0]["sales_doc_no"], "SO-9")
        self.assertEqual(rows[0]["engine_no"], "ENG-8")


class FetchSalesRowsTests(unittest.TestCase):
    def test_endpoint_lookup_failure_returns_a_stable_error(self):
        with mock.patch.object(readback, "_enabled_endpoint", side_effect=RuntimeError("db down")):
            result = readback.fetch_sales_records("u")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "ERR_UNEXPECTED")

    def test_each_call_starts_a_new_logged_in_read(self):
        endpoint = {"id": "ep", "config": {}}
        calls = []

        def run(ep, fn):
            calls.append(ep)
            client = mock.Mock()
            client._post_text.return_value = ROW
            return fn(client, mock.Mock())

        with (
            mock.patch.object(readback, "_enabled_endpoint", return_value=endpoint),
            mock.patch.object(readback, "_run_logged_in", side_effect=run),
        ):
            first = readback.fetch_sales_records("u", field="advisor", query="sale01")
            second = readback.fetch_sales_records("u", field="advisor", query="sale01")

        self.assertEqual(len(calls), 2)
        self.assertTrue(first["ok"] and second["ok"])
        self.assertEqual(first["source"], "mrerp_dms_live")

    def test_status_filter_uses_native_dms_code(self):
        seen = {}

        def run(_ep, fn):
            client = mock.Mock()

            def post(path, payload):
                seen.update(payload)
                return ROW

            client._post_text.side_effect = post
            return fn(client, mock.Mock())

        with (
            mock.patch.object(readback, "_enabled_endpoint", return_value={"id": "ep"}),
            mock.patch.object(readback, "_run_logged_in", side_effect=run),
        ):
            readback.fetch_sales_records("u", status="contract_opened")
        self.assertEqual(seen["ftd"], "13")


class FetchTopSalesTests(unittest.TestCase):
    HOME = """
    <input id="idusers" value="55">
    <select id="carmaxsellbranch"><option value="0">ทั้งหมด</option>
      <option value="42">BANGKOK</option></select>
    <select id="carmaxsellteam"><option value="36">BKK-A</option></select>
    """

    def test_uses_native_dashboard_count_and_page(self):
        posts = []

        class Transport:
            def get(self, _url):
                return mock.Mock(text=FetchTopSalesTests.HOME)

        adapter = mock.Mock(base_url="https://dms.example/")
        adapter._transport.return_value = Transport()
        client = mock.Mock()

        def post(path, payload):
            posts.append((path, dict(payload)))
            return "2" if payload["status"] == "all" else json.dumps([["Model X"], ["7"], [3]])

        client._post_text.side_effect = post

        def run(_ep, fn):
            return fn(client, adapter)

        with (
            mock.patch.object(readback, "_enabled_endpoint", return_value={"id": "ep"}),
            mock.patch.object(readback, "_run_logged_in", side_effect=run),
        ):
            result = readback.fetch_top_sales(
                "u",
                group="subtype",
                metric="amount",
                limit=30,
                date_from="01/08/2569",
                date_to="31/08/2569",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["rows"], [{"label": "Model X", "value": 3}])
        page_payload = posts[1][1]
        self.assertEqual(page_payload["carmaxselltypedata"], "3")
        self.assertEqual(page_payload["carmaxsellqnt"], "2")
        self.assertEqual(page_payload["carmaxsellshow"], "30")
        self.assertEqual(page_payload["carmaxsellbranch"], "42")


if __name__ == "__main__":
    unittest.main()
