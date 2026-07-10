# -*- coding: utf-8 -*-
"""F5 人工裁决窄写单测(services/ocr_history/posting_manual.py)。

钉死:UNSET(缺省 kwarg)不动该字段 · None(显式传)删键恢复自动 · 合法值写入;
只改主页 fields,不碰其余页;找不到记录 → False。SELECT 顺带带出 workspace_client_id +
主页卖方税号(seller_tax 缺省回落 seller_tax_id)供回流免整单重拉。回流(backflow_
supplier_profile)只在有 payment/item_type 值 + workspace_client_id + tenant_id + 卖方税号时
才调 upsert_profile,失败只 warning 不抛。
"""

from __future__ import annotations

import json
import unittest
from contextlib import contextmanager
from unittest import mock

from services.ocr_history import posting_manual as pm


class _FakeCur:
    """记录每次 execute 的 SQL/params;fetchone 按预置行答一次 SELECT。"""

    def __init__(self, select_row=None, rowcount=1):
        self.calls = []
        self._select_row = select_row
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self._select_row

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _patch_cursor_rls(cur):
    @contextmanager
    def _fake(**kw):
        yield cur

    return mock.patch.object(pm.db, "get_cursor_rls", lambda **kw: _fake(**kw))


class UpdateHistoryPostingManualTests(unittest.TestCase):
    def test_no_kwargs_at_all_is_noop(self):
        cur = _FakeCur()
        with _patch_cursor_rls(cur):
            result = pm.update_history_posting_manual("u1", "h1", "t1")
        self.assertFalse(result.ok)
        self.assertEqual(cur.calls, [])  # 没查也没写

    def test_record_not_found_returns_false(self):
        cur = _FakeCur(select_row=None)
        with _patch_cursor_rls(cur):
            result = pm.update_history_posting_manual("u1", "h1", "t1", payment="cash")
        self.assertFalse(result.ok)

    def test_writes_payment_leaves_item_type_untouched(self):
        pages = [{"fields": {"seller_name": "X", "posting_item_type_manual": "goods"}}]
        cur = _FakeCur(select_row={"pages": pages, "workspace_client_id": 7})
        with _patch_cursor_rls(cur):
            result = pm.update_history_posting_manual("u1", "h1", "t1", payment="cash")
        self.assertTrue(result.ok)
        self.assertEqual(result.workspace_client_id, 7)
        update_sql, update_params = cur.calls[-1]
        self.assertTrue(update_sql.startswith("UPDATE ocr_history SET pages"))
        written_pages = json.loads(update_params[0])
        self.assertEqual(written_pages[0]["fields"]["posting_payment_manual"], "cash")
        self.assertEqual(written_pages[0]["fields"]["posting_item_type_manual"], "goods")

    def test_explicit_none_deletes_key(self):
        pages = [{"fields": {"posting_payment_manual": "credit"}}]
        cur = _FakeCur(select_row={"pages": pages})
        with _patch_cursor_rls(cur):
            pm.update_history_posting_manual("u1", "h1", "t1", payment=None)
        written_pages = json.loads(cur.calls[-1][1][0])
        self.assertNotIn("posting_payment_manual", written_pages[0]["fields"])

    def test_invalid_value_treated_as_delete(self):
        pages = [{"fields": {"posting_item_type_manual": "expense"}}]
        cur = _FakeCur(select_row={"pages": pages})
        with _patch_cursor_rls(cur):
            pm.update_history_posting_manual("u1", "h1", "t1", item_type="garbage")
        written_pages = json.loads(cur.calls[-1][1][0])
        self.assertNotIn("posting_item_type_manual", written_pages[0]["fields"])

    def test_only_touches_primary_page(self):
        pages = [
            {"is_copy": True, "fields": {}},
            {"fields": {}},
        ]
        cur = _FakeCur(select_row={"pages": pages})
        with _patch_cursor_rls(cur):
            pm.update_history_posting_manual("u1", "h1", "t1", payment="cash")
        written_pages = json.loads(cur.calls[-1][1][0])
        self.assertNotIn("posting_payment_manual", written_pages[0]["fields"])
        self.assertEqual(written_pages[1]["fields"]["posting_payment_manual"], "cash")

    def test_update_carries_tenant_ownership_predicate(self):
        # 纵深防御:UPDATE 自带归属条件,不依赖同事务前置 SELECT 的验证。
        cur = _FakeCur(select_row={"pages": [{"fields": {}}]})
        with _patch_cursor_rls(cur):
            pm.update_history_posting_manual("u1", "h1", "t1", payment="cash")
        update_sql, update_params = cur.calls[-1]
        self.assertIn("user_id IN (SELECT id FROM users WHERE tenant_id", update_sql)
        self.assertEqual(update_params[1:], ("h1", "t1"))

    def test_seller_tax_falls_back_to_seller_tax_id(self):
        # 主页无 seller_tax 但有 seller_tax_id(仓库惯例回落)→ 结果带出该税号供回流用。
        pages = [{"fields": {"seller_tax_id": "0105546015062"}}]
        cur = _FakeCur(select_row={"pages": pages, "workspace_client_id": 3})
        with _patch_cursor_rls(cur):
            result = pm.update_history_posting_manual("u1", "h1", "t1", payment="cash")
        self.assertTrue(result.ok)
        self.assertEqual(result.seller_tax, "0105546015062")
        self.assertEqual(result.workspace_client_id, 3)

    def test_update_carries_user_ownership_predicate_without_tenant(self):
        cur = _FakeCur(select_row={"pages": [{"fields": {}}]})
        with _patch_cursor_rls(cur):
            pm.update_history_posting_manual("u1", "h1", None, payment="cash")
        update_sql, update_params = cur.calls[-1]
        self.assertIn("AND user_id = %s::uuid", update_sql)
        self.assertEqual(update_params[1:], ("h1", "u1"))


class BackflowSupplierProfileTests(unittest.TestCase):
    def test_no_values_is_noop(self):
        with mock.patch("services.purchase.supplier_posting.upsert_profile") as mocked_upsert:
            pm.backflow_supplier_profile(
                record_id="h1",
                tenant_id="t1",
                payment=None,
                item_type=None,
                workspace_client_id=7,
                seller_tax="0105546015062",
            )
        mocked_upsert.assert_not_called()

    def test_missing_tenant_id_skips(self):
        with mock.patch("services.purchase.supplier_posting.upsert_profile") as mocked_upsert:
            pm.backflow_supplier_profile(
                record_id="h1",
                tenant_id=None,
                payment="cash",
                item_type=None,
                workspace_client_id=7,
                seller_tax="0105546015062",
            )
        mocked_upsert.assert_not_called()

    def test_missing_workspace_client_id_skips(self):
        with mock.patch("services.purchase.supplier_posting.upsert_profile") as mocked_upsert:
            pm.backflow_supplier_profile(
                record_id="h1",
                tenant_id="t1",
                payment="cash",
                item_type=None,
                workspace_client_id=None,
                seller_tax="0105546015062",
            )
        mocked_upsert.assert_not_called()

    def test_missing_seller_tax_skips(self):
        with mock.patch("services.purchase.supplier_posting.upsert_profile") as mocked_upsert:
            pm.backflow_supplier_profile(
                record_id="h1",
                tenant_id="t1",
                payment="cash",
                item_type=None,
                workspace_client_id=7,
                seller_tax="",
            )
        mocked_upsert.assert_not_called()

    def test_writes_profile_when_all_present(self):
        with mock.patch("services.purchase.supplier_posting.upsert_profile") as mocked_upsert:
            with mock.patch.object(pm.db, "get_cursor", lambda **kw: _NullCtx()):
                pm.backflow_supplier_profile(
                    record_id="h1",
                    tenant_id="t1",
                    payment="cash",
                    item_type="goods",
                    workspace_client_id=7,
                    seller_tax="0105546015062",
                )
        mocked_upsert.assert_called_once()
        kwargs = mocked_upsert.call_args.kwargs
        self.assertEqual(kwargs["tenant_id"], "t1")
        self.assertEqual(kwargs["workspace_client_id"], 7)
        self.assertEqual(kwargs["seller_tax_id"], "0105546015062")
        self.assertEqual(kwargs["default_payment"], "cash")
        self.assertEqual(kwargs["default_item_type"], "goods")
        self.assertEqual(kwargs["source"], "correction")

    def test_own_tax_id_matches_workspace_skips_upsert(self):
        # 销项票 seller_tax = 账套自家税号 → 没有"供应商"这维度,不落死档案。
        own_cur = _FakeCur(select_row={"tax_id": "0105546015062"})
        with mock.patch("services.purchase.supplier_posting.upsert_profile") as mocked_upsert:
            with mock.patch.object(pm.db, "get_cursor", lambda **kw: _CtxOf(own_cur)):
                pm.backflow_supplier_profile(
                    record_id="h1",
                    tenant_id="t1",
                    payment="cash",
                    item_type=None,
                    workspace_client_id=7,
                    seller_tax="0105546015062",
                )
        mocked_upsert.assert_not_called()

    def test_workspace_tax_id_lookup_empty_still_backflows(self):
        # 查不到账套税号(表无数据/字段空)→ 保守照旧回流,别把正常采购误杀。
        own_cur = _FakeCur(select_row=None)
        with mock.patch("services.purchase.supplier_posting.upsert_profile") as mocked_upsert:
            with mock.patch.object(pm.db, "get_cursor", lambda **kw: _CtxOf(own_cur)):
                pm.backflow_supplier_profile(
                    record_id="h1",
                    tenant_id="t1",
                    payment="cash",
                    item_type=None,
                    workspace_client_id=7,
                    seller_tax="0105546015062",
                )
        mocked_upsert.assert_called_once()
        self.assertEqual(mocked_upsert.call_args.kwargs["seller_tax_id"], "0105546015062")

    def test_upsert_failure_swallowed(self):
        with mock.patch(
            "services.purchase.supplier_posting.upsert_profile",
            side_effect=RuntimeError("db down"),
        ):
            with mock.patch.object(pm.db, "get_cursor", lambda **kw: _NullCtx()):
                # 不抛 · 只 warning
                pm.backflow_supplier_profile(
                    record_id="h1",
                    tenant_id="t1",
                    payment="cash",
                    item_type=None,
                    workspace_client_id=7,
                    seller_tax="0105546015062",
                )


class _NullCtx:
    def __enter__(self):
        return _FakeCur()

    def __exit__(self, *a):
        return False


class _CtxOf:
    """回流一个 with 块里先查账套税号再 upsert · 两次 execute 共用同一个 cur。"""

    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


if __name__ == "__main__":
    unittest.main(verbosity=2)
