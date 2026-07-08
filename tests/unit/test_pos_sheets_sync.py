# -*- coding: utf-8 -*-
"""POS 售出留档到 Google Sheet(services/pos/sheets_sync)守门测试。

锁定:
  1. extract_spreadsheet_id:URL/纯 ID 两种输入都能抽出干净 ID
  2. get_settings/save_settings:无行回落默认 + upsert 往返
  3. sync_sale:未开/未配表/未连 Google 一律安静跳过(no-op·不报错)· 已配齐才真调
     SheetsClient.append_row · 任何环节抛异常都被吞掉(后台留档失败绝不影响收银)
"""

import unittest
from decimal import Decimal
from unittest.mock import patch

from services.pos import sheets_sync as svc


class FakeCursor:
    def __init__(self, fetch_queue=None, fetchall_queue=None):
        self.calls = []
        self._one = list(fetch_queue or [])
        self._all = list(fetchall_queue or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._one.pop(0) if self._one else None

    def fetchall(self):
        return self._all.pop(0) if self._all else []


class ExtractSpreadsheetIdTests(unittest.TestCase):
    def test_full_url(self):
        url = "https://docs.google.com/spreadsheets/d/1AbC-XyZ_123/edit#gid=0"
        self.assertEqual(svc.extract_spreadsheet_id(url), "1AbC-XyZ_123")

    def test_raw_id_passthrough(self):
        self.assertEqual(svc.extract_spreadsheet_id("1AbC-XyZ_123"), "1AbC-XyZ_123")

    def test_blank_input(self):
        self.assertEqual(svc.extract_spreadsheet_id(""), "")
        self.assertEqual(svc.extract_spreadsheet_id(None), "")


class GetSaveSettingsTests(unittest.TestCase):
    def test_defaults_when_no_row(self):
        cur = FakeCursor([None])
        out = svc.get_settings(cur, tenant_id="t-1", workspace_client_id=7)
        self.assertEqual(
            out, {"spreadsheet_id": "", "tab_name": "POS", "enabled": False, "header_lang": "th"}
        )

    def test_reads_explicit_row(self):
        cur = FakeCursor(
            [{"spreadsheet_id": "SS1", "tab_name": "Sales", "enabled": True, "header_lang": "en"}]
        )
        out = svc.get_settings(cur, tenant_id="t-1", workspace_client_id=7)
        self.assertEqual(
            out,
            {"spreadsheet_id": "SS1", "tab_name": "Sales", "enabled": True, "header_lang": "en"},
        )

    def test_save_extracts_id_and_upserts(self):
        # save_settings 末尾调 get_settings 回读 → 备第二次 fetchone
        cur = FakeCursor(
            [{"spreadsheet_id": "SS1", "tab_name": "POS", "enabled": True, "header_lang": "zh"}]
        )
        svc.save_settings(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            spreadsheet_id="https://docs.google.com/spreadsheets/d/SS1/edit",
            enabled=True,
            header_lang="zh",
        )
        upsert = cur.calls[0]
        self.assertIn("INSERT INTO pos_sheets_settings", upsert[0])
        self.assertEqual(upsert[1], ("t-1", 7, "SS1", True, "zh"))

    def test_save_blank_id_stores_null(self):
        cur = FakeCursor([None])
        svc.save_settings(
            cur, tenant_id="t-1", workspace_client_id=7, spreadsheet_id="", enabled=False
        )
        upsert = cur.calls[0]
        self.assertEqual(upsert[1], ("t-1", 7, None, False, "th"))


class SyncSaleTests(unittest.TestCase):
    def _cur(self, settings_row):
        return FakeCursor([settings_row])

    _SETTINGS_OFF = {
        "spreadsheet_id": "SS1",
        "tab_name": "POS",
        "enabled": False,
        "header_lang": "th",
    }
    _SETTINGS_NO_SHEET = {
        "spreadsheet_id": "",
        "tab_name": "POS",
        "enabled": True,
        "header_lang": "th",
    }
    _SETTINGS_ON = {
        "spreadsheet_id": "SS1",
        "tab_name": "POS",
        "enabled": True,
        "header_lang": "zh",
    }

    def test_disabled_is_noop(self):
        cur = self._cur(self._SETTINGS_OFF)
        with patch.object(svc, "get_settings", return_value=self._SETTINGS_OFF):
            with patch("services.export.google_oauth.valid_access_token") as tok:
                svc.sync_sale(cur, tenant_id="t-1", workspace_client_id=7, sale_id="s1")
                tok.assert_not_called()

    def test_no_spreadsheet_configured_is_noop(self):
        with patch.object(svc, "get_settings", return_value=self._SETTINGS_NO_SHEET):
            with patch("services.export.google_oauth.valid_access_token") as tok:
                svc.sync_sale(FakeCursor(), tenant_id="t-1", workspace_client_id=7, sale_id="s1")
                tok.assert_not_called()

    def test_no_google_token_is_noop_not_error(self):
        with patch.object(svc, "get_settings", return_value=self._SETTINGS_ON):
            with patch("services.export.google_oauth.valid_access_token", return_value=None):
                with patch("services.export.sheets.SheetsClient") as client_cls:
                    svc.sync_sale(
                        FakeCursor(), tenant_id="t-1", workspace_client_id=7, sale_id="s1"
                    )
                    client_cls.assert_not_called()

    def test_configured_and_connected_appends_row(self):
        # sync_sale 直查行项(cur.execute+fetchall) + 收银员姓名(cur.execute+fetchone);
        # sale 头/payments 走 sales_store(下方 mock)。
        sale_cur = FakeCursor(
            fetch_queue=[{"display_name": "Earn"}],
            fetchall_queue=[[{"qty": Decimal("1"), "name_th": "บลัชออน", "name_en": "Blush"}]],
        )
        with (
            patch.object(svc, "get_settings", return_value=self._SETTINGS_ON),
            patch("services.export.google_oauth.valid_access_token", return_value="TOKEN"),
            patch(
                "services.pos.sales_store.get_sale",
                return_value={
                    "id": "s1",
                    "receipt_no": "R001",
                    "cashier_id": "c1",
                    "subtotal": Decimal("271.03"),
                    "discount_total": Decimal("0"),
                    "vat_amount": Decimal("18.97"),
                    "grand_total": Decimal("290.00"),
                    "paid_total": Decimal("300.00"),
                    "change_amount": Decimal("10.00"),
                    "sold_at": None,
                },
            ),
            patch(
                "services.pos.sales_store.list_payments",
                return_value=[{"method": "transfer"}],
            ),
            patch("services.export.sheets.SheetsClient") as client_cls,
        ):
            svc.sync_sale(sale_cur, tenant_id="t-1", workspace_client_id=7, sale_id="s1")

        client_cls.assert_called_once_with("TOKEN")
        instance = client_cls.return_value
        instance.append_row.assert_called_once()
        args = instance.append_row.call_args[0]
        self.assertEqual(args[0], "SS1")
        self.assertEqual(args[1], "POS")
        row = args[2]
        self.assertEqual(row[0], "R001")
        self.assertEqual(row[3], "Earn")
        self.assertIn("บลัชออน x1", row[4])
        self.assertEqual(row[10], "银行转账")  # header_lang=zh → 中文付款方式标签

    def test_exception_anywhere_is_swallowed(self):
        with patch.object(svc, "get_settings", side_effect=RuntimeError("boom")):
            # 不抛异常 = 通过(后台留档失败绝不冒泡到收银主路径)
            svc.sync_sale(FakeCursor(), tenant_id="t-1", workspace_client_id=7, sale_id="s1")


if __name__ == "__main__":
    unittest.main()
