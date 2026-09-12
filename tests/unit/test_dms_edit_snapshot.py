# -*- coding: utf-8 -*-
"""编辑器请求级权威快照(dms_edit_snapshot):一次登录取齐,读不到 fail closed。

生产实测编辑器 load/save 每个请求各登 2–3 次 DMS(6–10 秒 / 9.8 秒)。本模块把主档 +
银行目录 + 选中车型颜色 + 客户四级地址级联收进同一次会话;失败绝不回退 12h 缓存。
"""

import unittest
from unittest import mock

from services.erp import dms_edit_snapshot
from services.erp.mrerp_dms_client_base import DMSClientError

_MASTERS = {
    "cars": [["C1", "DMX", "D-Max"]],
    "place_books": [["PL1", "PL", "Showroom"]],
    "term_sales": [["T1", "T", "Cash"]],
    "branches": [["B1", "B", "Bangkok"]],
    "regis_behalfs": [["R1", "R", "Self"]],
    "advisors": [],
    "prefixes": [["17", "Mr", "Mr"]],
}
_BANKS = {
    key: [["1", "SCB", "SCB", "Rayong", "1234567890123"]]
    for key in ("company_banks", "source_banks", "cheque_banks", "cashier_banks", "card_banks")
}
_GEO_ROWS = {
    "provinces": [["P1", "Bangkok"]],
    "districts": [["D1", "District"]],
    "subdistricts": [["S1", "Subdistrict"]],
    "zipcodes": [["Z1", "10230"]],
}

_ENDPOINT = {"id": "E1", "config": {}}
_CUSTOMER = {
    "province_id": "P1",
    "district_id": "D1",
    "subdistrict_id": "S1",
    "zipcode_id": "Z1",
}


class _FakeClient:
    """记录这一次会话里到底读了哪些车型颜色、哪几级地址。"""

    def __init__(self, *, missing_paints=False):
        self.missing_paints = missing_paints
        self.paints = [["PA1", "RED", "Red"]]
        self.painted_cars = []
        self.geo_levels = []
        self.strict = None

    def fetch_masters(self, *, strict=False):
        self.strict = strict
        return dict(_MASTERS)

    def _bshsd_all(self, elemname, **kwargs):
        if elemname == "txtcarpaint":
            self.painted_cars.append(kwargs.get("idcar"))
            return None if self.missing_paints else self.paints
        return []

    def list_geo(self, level, parent_id=""):
        self.geo_levels.append((level, parent_id))
        return list(_GEO_ROWS.get(level) or [])


class _RunLoggedIn:
    """按 _run_logged_in 的真实契约跑 fn:计数 + 把 DMSClientError 映射成 _err dict。"""

    def __init__(self, client=None, *, error=""):
        self.client = client or _FakeClient()
        self.error = error
        self.calls = []

    def __call__(self, endpoint, fn, *, authoritative_read=False):
        self.calls.append({"endpoint": endpoint, "authoritative_read": authoritative_read})
        if self.error:
            return {"ok": False, "error_code": self.error}
        try:
            return fn(self.client, object())
        except DMSClientError as exc:
            return {"ok": False, "error_code": exc.error_code}


class EditSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.run = _RunLoggedIn()
        run = mock.patch("services.erp.erp_dms_intake._run_logged_in", side_effect=self.run)
        banks = mock.patch(
            "services.erp.mrerp_dms_company_banks.fetch_payment_bank_masters",
            return_value=dict(_BANKS),
        )
        store = mock.patch.object(dms_edit_snapshot, "_store")
        cached = mock.patch(
            "services.erp.dms_masters_cache.get_masters",
            side_effect=AssertionError("编辑器快照不得回退 12h 缓存"),
        )
        self.store = store.start()
        self.addCleanup(store.stop)
        for patcher in (run, banks, cached):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_one_authoritative_login_returns_masters_paints_prefixes_and_geo(self):
        snap = dms_edit_snapshot.read_edit_snapshot(
            _ENDPOINT, car_ids=("C1", "C1", ""), customer=_CUSTOMER
        )
        self.assertEqual(len(self.run.calls), 1)  # 一个请求一次登录
        self.assertTrue(self.run.calls[0]["authoritative_read"])
        self.assertEqual(self.run.client.painted_cars, ["C1"])  # 同车型只读一次颜色
        self.assertTrue(self.run.client.strict)  # 主档必须严格完整
        self.assertEqual(
            self.run.client.geo_levels,
            [
                ("provinces", ""),
                ("districts", "P1"),
                ("subdistricts", "D1"),
                ("zipcodes", "S1"),
            ],
        )
        self.assertEqual(snap["masters"]["cars"], _MASTERS["cars"])
        self.assertEqual(snap["masters"]["company_banks"], _BANKS["company_banks"])
        self.assertEqual(snap["paints"], {"C1": [["PA1", "RED", "Red"]]})
        self.assertEqual(snap["prefixes"], [["17", "Mr", "Mr"]])
        self.assertEqual(snap["geo"]["zipcodes"], [["Z1", "10230"]])
        self.store.assert_called_once()

    def test_load_snapshot_without_a_customer_reads_no_geo(self):
        snap = dms_edit_snapshot.read_edit_snapshot(_ENDPOINT, car_ids=("C1",))
        self.assertEqual(self.run.client.geo_levels, [])
        self.assertEqual(snap["geo"], {})

    def test_login_failure_is_none_and_never_falls_back_to_cache(self):
        self.run.error = "ERR_DMS_AUTH"
        self.assertIsNone(dms_edit_snapshot.read_edit_snapshot(_ENDPOINT, car_ids=("C1",)))
        self.store.assert_not_called()

    def test_unreadable_paint_master_is_marked_none_not_an_empty_car(self):
        """某车型颜色这次没读到 → 该车型落 None(读失败),绝不冒充「这车没颜色」。"""
        self.run.client = _FakeClient(missing_paints=True)
        snap = dms_edit_snapshot.read_edit_snapshot(_ENDPOINT, car_ids=("C1", "C2"))
        self.assertEqual(snap["paints"], {"C1": None, "C2": None})

    def test_an_authoritatively_empty_car_stays_an_empty_list(self):
        self.run.client = _FakeClient()
        self.run.client.paints = []  # DMS 权威结论:这个车型没有颜色
        snap = dms_edit_snapshot.read_edit_snapshot(_ENDPOINT, car_ids=("C1",))
        self.assertEqual(snap["paints"], {"C1": []})

    def test_geo_levels_skip_parents_that_are_not_known(self):
        self.assertEqual(
            dms_edit_snapshot.geo_levels({"province_id": "P1"}),
            (("provinces", ""), ("districts", "P1")),
        )
        self.assertEqual(dms_edit_snapshot.geo_levels(None), ())


if __name__ == "__main__":
    unittest.main()
