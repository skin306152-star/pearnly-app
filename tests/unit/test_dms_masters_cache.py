# -*- coding: utf-8 -*-
"""DMS 主档缓存(DL-4a · services/erp/dms_masters_cache.py)· TTL / 惰性 paints / 登录失败陈旧回退。

内存背板替 _read/_write,计数 _fetch_*_via_login 断言 DMS 登录次数(D1)。
"""

import contextlib
import unittest
from unittest import mock

from services.erp import dms_masters_cache as mc

_EP = {"id": "E1", "config": {}}
_MASTERS = {
    "cars": [["c1", "CODE1", "Car One"]],
    "advisors": [["a1", "A1", "Adv"]],
    "company_banks": [["1", "SCB", "SCB"]],
}
_PAINTS = [["p1", "PC1", "Red"]]


class _Mem:
    """endpoint_id → {masters, age};write 落地即 age=0(刚刷新)。"""

    def __init__(self):
        self.rows = {}

    def read(self, eid):
        r = self.rows.get(eid)
        return {"masters": r["masters"], "age_seconds": r["age"]} if r else None

    def write(self, eid, masters):
        self.rows[eid] = {"masters": masters, "age": 0.0}


class MastersCacheTests(unittest.TestCase):
    def setUp(self):
        self.mem = _Mem()
        self.masters_calls = 0
        self.paint_calls = {}
        self.es = contextlib.ExitStack()
        p = lambda *a, **k: self.es.enter_context(mock.patch.object(*a, **k))  # noqa: E731
        p(mc, "_read", side_effect=self.mem.read)
        p(mc, "_write", side_effect=self.mem.write)
        p(mc, "_fetch_masters_via_login", side_effect=self._fetch_masters)
        p(mc, "_fetch_paints_via_login", side_effect=self._fetch_paints)

    def tearDown(self):
        self.es.close()

    def _fetch_masters(self, ep):
        self.masters_calls += 1
        return {k: [list(r) for r in v] for k, v in _MASTERS.items()}

    def _fetch_paints(self, ep, car_id):
        self.paint_calls[car_id] = self.paint_calls.get(car_id, 0) + 1
        return [list(r) for r in _PAINTS]

    def test_d1_cold_fetch_then_cached(self):
        """D1:冷取 → fetch 一次 + 落缓存;12h 内二次取 → 零 DMS 调用。"""
        out = mc.get_masters(_EP)
        self.assertEqual(out["cars"], _MASTERS["cars"])
        self.assertEqual(self.masters_calls, 1)
        self.assertIn("E1", self.mem.rows)

        again = mc.get_masters(_EP)
        self.assertEqual(again["cars"], _MASTERS["cars"])
        self.assertEqual(self.masters_calls, 1)  # 命中缓存,不再登录

    def test_stale_refetches(self):
        mc.get_masters(_EP)
        self.mem.rows["E1"]["age"] = 13 * 3600  # 过期
        mc.get_masters(_EP)
        self.assertEqual(self.masters_calls, 2)

    def test_legacy_cache_without_company_banks_is_refreshed(self):
        self.mem.write("E1", {"cars": _MASTERS["cars"]})
        out = mc.get_masters(_EP)
        self.assertEqual(out["company_banks"], _MASTERS["company_banks"])
        self.assertEqual(self.masters_calls, 1)

    def test_force_refresh_bypasses_fresh_cache(self):
        """顾问认不出时要按现场名册重判 → force_refresh 必须真的重抓,不吃 12h 缓存。"""
        mc.get_masters(_EP)
        mc.get_masters(_EP, force_refresh=True)
        self.assertEqual(self.masters_calls, 2)

    def test_force_refresh_drops_stale_paints(self):
        """force_refresh 成功刷新按 DMS 现状落库:旧 paints_by_car 不合并回去,
        否则 DMS 新增/删除的颜色会被旧色遮住。"""
        mc.get_masters(_EP)
        mc.get_paints(_EP, "c1")
        out = mc.get_masters(_EP, force_refresh=True)
        self.assertEqual(self.masters_calls, 2)
        self.assertNotIn("paints_by_car", out)
        self.assertNotIn("paints_by_car", self.mem.rows["E1"]["masters"])
        # 旧色已作废 → 同一车型颜色要重新抓
        self.assertEqual(mc.get_paints(_EP, "c1"), _PAINTS)
        self.assertEqual(self.paint_calls["c1"], 2)

    def test_force_refresh_login_fail_fails_closed(self):
        """force_refresh 登录/抓取失败 → 空 dict(fail closed),绝不回退旧主档。"""
        mc.get_masters(_EP)
        with mock.patch.object(mc, "_fetch_masters_via_login", return_value=None):
            out = mc.get_masters(_EP, force_refresh=True)
        self.assertEqual(out, {})

    def test_login_fail_serves_stale(self):
        mc.get_masters(_EP)
        self.mem.rows["E1"]["age"] = 13 * 3600
        with mock.patch.object(mc, "_fetch_masters_via_login", return_value=None):
            out = mc.get_masters(_EP)
        self.assertEqual(out["cars"], _MASTERS["cars"])  # 登录失败 → 陈旧回退

    def test_paints_lazy_cached(self):
        mc.get_masters(_EP)
        self.assertEqual(mc.get_paints(_EP, "c1"), _PAINTS)
        self.assertEqual(self.paint_calls["c1"], 1)
        mc.get_paints(_EP, "c1")  # 同 car 再取 → 零调用
        self.assertEqual(self.paint_calls["c1"], 1)
        mc.get_paints(_EP, "c2")  # 异 car → 抓
        self.assertEqual(self.paint_calls["c2"], 1)

    def test_paint_fetch_failure_yields_empty_and_is_not_cached(self):
        """_bshsd 取数失败现在回 None(不再假装空表)—— 这条 None 路不许炸,也不许被当成
        「这个车型没有颜色」缓存下来。"""
        mc.get_masters(_EP)
        with mock.patch.object(mc, "_fetch_paints_via_login", return_value=None):
            self.assertEqual(mc.get_paints(_EP, "c1"), [])
        self.assertNotIn("paints_by_car", self.mem.rows["E1"]["masters"])
        self.assertEqual(mc.get_paints(_EP, "c1"), _PAINTS)  # 恢复后照常取到

    def test_full_refresh_preserves_paints(self):
        mc.get_masters(_EP)
        mc.get_paints(_EP, "c1")
        self.mem.rows["E1"]["age"] = 13 * 3600
        mc.get_masters(_EP)  # 全量刷主档
        mc.get_paints(_EP, "c1")  # paints_by_car 应仍在 → 不再抓
        self.assertEqual(self.paint_calls["c1"], 1)


class PaintFetchLayerTests(unittest.TestCase):
    """登录抓取层(不打桩本体):_bshsd 取数失败与登录失败在这里都必须落成 None。"""

    def test_none_and_error_dict_both_become_none(self):
        from services.erp import erp_dms_intake

        for outcome in (None, {"ok": False, "error_code": "ERR_DMS_AUTH"}):
            with mock.patch.object(erp_dms_intake, "_run_logged_in", return_value=outcome):
                self.assertIsNone(mc._fetch_paints_via_login(_EP, "c1"))

    def test_full_master_fetch_includes_company_banks(self):
        from services.erp import erp_dms_intake

        client = mock.Mock()
        client.fetch_masters.return_value = {"cars": []}

        def run(endpoint, fn):
            return fn(client, object())

        with (
            mock.patch.object(erp_dms_intake, "_run_logged_in", side_effect=run),
            mock.patch(
                "services.erp.mrerp_dms_company_banks.fetch_company_banks",
                return_value=[["1", "SCB", "SCB"]],
            ),
        ):
            out = mc._fetch_masters_via_login(_EP)
        self.assertEqual(out["company_banks"], [["1", "SCB", "SCB"]])

    def test_paints_fetched_paged_with_car_id(self):
        """颜色主档走翻页取全(带 car_id):第 2 页起的颜色不静默丢失。"""
        from services.erp import erp_dms_intake

        client = mock.Mock()
        client._bshsd_all.return_value = [["p1", "PC1", "Red"]]

        def run(endpoint, fn):
            return fn(client, object())

        with mock.patch.object(erp_dms_intake, "_run_logged_in", side_effect=run):
            out = mc._fetch_paints_via_login(_EP, "c1")
        client._bshsd_all.assert_called_once_with("txtcarpaint", idcar="c1")
        self.assertEqual(out, [["p1", "PC1", "Red"]])


if __name__ == "__main__":
    unittest.main()
