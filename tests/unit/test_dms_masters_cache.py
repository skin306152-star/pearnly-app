# -*- coding: utf-8 -*-
"""DMS 车辆选择面板主档缓存(DL-4a)· TTL / 惰性 paints / 登录失败陈旧回退。

内存背板替 _read/_write,计数 _fetch_*_via_login 断言 DMS 登录次数(D1)。
"""

import contextlib
import unittest
from unittest import mock

from services.line_dms import masters_cache as mc

_EP = {"id": "E1", "config": {}}
_MASTERS = {"cars": [["c1", "CODE1", "Car One"]], "advisors": [["a1", "A1", "Adv"]]}
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

    def test_full_refresh_preserves_paints(self):
        mc.get_masters(_EP)
        mc.get_paints(_EP, "c1")
        self.mem.rows["E1"]["age"] = 13 * 3600
        mc.get_masters(_EP)  # 全量刷主档
        mc.get_paints(_EP, "c1")  # paints_by_car 应仍在 → 不再抓
        self.assertEqual(self.paint_calls["c1"], 1)


if __name__ == "__main__":
    unittest.main()
