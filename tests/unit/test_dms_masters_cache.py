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
    **{key: [["1", "SCB", "SCB"]] for key in mc._COMPLETE_KEYS},
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

    def _fetch_masters(self, ep, **kwargs):
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

    def test_strict_force_refresh_is_forwarded_to_login_fetch(self):
        with mock.patch.object(mc, "_fetch_masters_via_login", return_value=_MASTERS) as fetch:
            mc.get_masters(_EP, force_refresh=True, require_complete=True)
        fetch.assert_called_once_with(_EP, require_complete=True)

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

    def test_strict_paint_fetch_failure_raises_and_is_not_cached(self):
        from services.erp.mrerp_dms_client_base import DMSClientError

        mc.get_masters(_EP)
        with mock.patch.object(mc, "_fetch_paints_via_login", return_value=None):
            with self.assertRaises(DMSClientError) as ctx:
                mc.get_paints(_EP, "c1", require_complete=True)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNAVAILABLE")
        self.assertNotIn("paints_by_car", self.mem.rows["E1"]["masters"])

    def test_full_refresh_preserves_paints(self):
        mc.get_masters(_EP)
        mc.get_paints(_EP, "c1")
        self.mem.rows["E1"]["age"] = 13 * 3600
        mc.get_masters(_EP)  # 全量刷主档
        mc.get_paints(_EP, "c1")  # paints_by_car 应仍在 → 不再抓
        self.assertEqual(self.paint_calls["c1"], 1)


class AuthoritativeSnapshotTests(unittest.TestCase):
    """write_authoritative_snapshot:权威空表 = 删除事实,不许被旧缓存合并回来。

    用户口径是「DMS 增删必须实时映射」:`[]` 与 `None` 必须分开 —— `_bshsd_all` 回 `[]`
    是权威读取成功的空表(该车型颜色/该类银行已在 DMS 删光),回 `None` 才是读取失败。
    """

    def setUp(self):
        self.mem = _Mem()
        self.es = contextlib.ExitStack()
        self.es.enter_context(mock.patch.object(mc, "_read", side_effect=self.mem.read))
        self.es.enter_context(mock.patch.object(mc, "_write", side_effect=self.mem.write))
        self.addCleanup(self.es.close)

    def _seed(self, masters):
        self.mem.write("E1", masters)
        return masters

    def _written(self):
        return self.mem.rows["E1"]["masters"]

    def test_authoritative_empty_paints_clear_the_selected_car(self):
        """选中车型权威回 [] → 旧颜色必须被清掉,不是「没拿到所以留旧色」。"""
        self._seed(
            {
                "cars": _MASTERS["cars"],
                "paints_by_car": {"c1": [["p1", "PC1", "Red"]], "c2": [["p2", "PC2", "Blue"]]},
            }
        )

        mc.write_authoritative_snapshot(
            _EP, {**_MASTERS, "paints_by_car": {}}, car_id="c1", paints=[]
        )

        written = self._written()
        self.assertEqual(written["paints_by_car"]["c1"], [])
        # 没读的其它车型旧色原样保留(安全合并)
        self.assertEqual(written["paints_by_car"]["c2"], [["p2", "PC2", "Blue"]])

    def test_authoritative_empty_paints_for_the_last_car_do_not_resurrect_on_next_write(self):
        """唯一一条颜色被清空后,下一次不带颜色读取的落库不许把旧色从那行缓存合并回来。"""
        self._seed({"cars": _MASTERS["cars"], "paints_by_car": {"c1": [["p1", "PC1", "Red"]]}})

        mc.write_authoritative_snapshot(_EP, _MASTERS, car_id="c1", paints=[])
        self.assertEqual(self._written()["paints_by_car"], {"c1": []})

        mc.write_authoritative_snapshot(_EP, _MASTERS)
        self.assertEqual(self._written()["paints_by_car"], {"c1": []})

    def test_none_paints_keep_the_old_row_for_that_car(self):
        """paints=None 是「这次没读到」→ 该车型旧条目原样保留(与 [] 明确分开)。"""
        old_paints = [["p1", "PC1", "Red"]]
        self._seed({"cars": _MASTERS["cars"], "paints_by_car": {"c1": old_paints}})

        mc.write_authoritative_snapshot(_EP, _MASTERS, car_id="c1", paints=None)

        self.assertEqual(self._written()["paints_by_car"]["c1"], old_paints)

    def test_authoritative_empty_bank_list_clears_the_old_row(self):
        """权威银行表回 [] = DMS 里这类银行已删光 → 不许用 falsy 判断恢复旧银行。"""
        self._seed(
            {
                "cars": _MASTERS["cars"],
                "company_banks": [["9", "OLD", "Old Bank"]],
                "source_banks": [["9", "OLD", "Old Bank"]],
            }
        )
        authoritative = {**_MASTERS, "company_banks": [], "source_banks": []}

        mc.write_authoritative_snapshot(_EP, authoritative)

        written = self._written()
        self.assertEqual(written["company_banks"], [])
        self.assertEqual(written["source_banks"], [])

    def test_bank_key_missing_from_the_snapshot_falls_back_to_the_old_row(self):
        """兼容边界:key 根本不在这次快照里(这次没读这类目录)→ 保留旧行,不误清。"""
        self._seed(
            {
                "cars": _MASTERS["cars"],
                "company_banks": [["9", "OLD", "Old Bank"]],
                "source_banks": [["9", "OLD", "Old Bank"]],
            }
        )
        authoritative = {k: v for k, v in _MASTERS.items() if k != "company_banks"}
        authoritative["source_banks"] = []

        mc.write_authoritative_snapshot(_EP, authoritative)

        written = self._written()
        self.assertEqual(written["company_banks"], [["9", "OLD", "Old Bank"]])  # 缺 key → 兼容旧值
        self.assertEqual(written["source_banks"], [])  # 有 key 且 [] → 权威删除


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

        def run(endpoint, fn, **kwargs):
            return fn(client, object())

        with (
            mock.patch.object(erp_dms_intake, "_run_logged_in", side_effect=run),
            mock.patch(
                "services.erp.mrerp_dms_company_banks.fetch_payment_bank_masters",
                return_value={"company_banks": [["1", "SCB", "SCB"]]},
            ),
        ):
            out = mc._fetch_masters_via_login(_EP)
        self.assertEqual(out["company_banks"], [["1", "SCB", "SCB"]])

    def test_strict_master_fetch_reaches_client(self):
        from services.erp import erp_dms_intake

        client = mock.Mock()
        client.fetch_masters.return_value = {"cars": []}

        def run(endpoint, fn, **kwargs):
            return fn(client, object())

        with (
            mock.patch.object(erp_dms_intake, "_run_logged_in", side_effect=run),
            mock.patch(
                "services.erp.mrerp_dms_company_banks.fetch_payment_bank_masters",
                return_value={},
            ),
        ):
            mc._fetch_masters_via_login(_EP, require_complete=True)
        client.fetch_masters.assert_called_once_with(strict=True)

    def test_paints_fetched_paged_with_car_id(self):
        """颜色主档走翻页取全(带 car_id):第 2 页起的颜色不静默丢失。"""
        from services.erp import erp_dms_intake

        client = mock.Mock()
        client._bshsd_all.return_value = [["p1", "PC1", "Red"]]

        def run(endpoint, fn, **kwargs):
            return fn(client, object())

        with mock.patch.object(erp_dms_intake, "_run_logged_in", side_effect=run):
            out = mc._fetch_paints_via_login(_EP, "c1")
        client._bshsd_all.assert_called_once_with("txtcarpaint", idcar="c1")
        self.assertEqual(out, [["p1", "PC1", "Red"]])


# 2026-09-13 同会话只读原始响应勘查(租户 bshsd)记录的两个真实协议形态:
#   · 已登录、目录 0 行 → HTTP 200 + **空正文**(0 字节);
#   · 未登录/认证失效  → HTTP 200 + **65 字节非 JSON 正文**(strip 后 37 字符,非数组)。
# 下面第二条用等长占位正文表示「非 JSON 的认证失败壳」,断言的是协议分流本身(非 JSON → None),
# 不是逐字节复原那段正文。空正文 = 该目录 0 行,必须仍是合法空表。
_UNAUTHENTICATED_BODY = "0" * 65  # 非 JSON、非数组:模拟未登录壳(与真实响应同为非 JSON)


class BshsdBodyHonestyTests(unittest.TestCase):
    """bshsd 正文协议:空正文 = 合法 0 行目录;非 JSON 正文 = 取数失败(fail closed)。"""

    def test_blank_body_is_the_tenant_legitimate_empty_directory(self):
        """已登录、该目录 0 行 → 空正文 → []。空正文不是"没读到"。"""
        from services.erp.mrerp_dms_master_rows import parse_rows

        for body in ("", "   ", "\n\t \n"):
            with self.subTest(body=body):
                self.assertEqual(parse_rows("txtbanknametffrom", body), [])
        # 空数组 JSON 也是合法空表(不是唯一形态)。
        self.assertEqual(parse_rows("txtbanknametffrom", "[]"), [])
        self.assertEqual(parse_rows("txtbanknametffrom", '[["1","SCB","SCB"]]')[0][1], "SCB")

    def test_non_json_or_non_array_body_is_a_fetch_failure(self):
        """未登录壳(非 JSON)/HTML/对象/null/异常 JSON → None,不许被读成空目录。"""
        from services.erp.mrerp_dms_master_rows import parse_rows

        for body in (_UNAUTHENTICATED_BODY, "<html></html>", "{}", "[1,2", "null", '"x"'):
            with self.subTest(body=body):
                self.assertIsNone(parse_rows("txtbanknametffrom", body))

    def test_failed_login_never_writes_an_authoritative_empty_bank_row(self):
        """完整强制抓取里登录失败 → fail closed,不落任何权威缓存(含空表)。"""
        from services.erp import erp_dms_intake

        self.mem = _Mem()
        with (
            mock.patch.object(mc, "_read", side_effect=self.mem.read),
            mock.patch.object(mc, "_write", side_effect=self.mem.write),
            mock.patch.object(erp_dms_intake, "_run_logged_in", return_value=None),
            mock.patch.object(mc, "write_authoritative_snapshot") as write,
        ):
            out = mc.get_masters(_EP, force_refresh=True, require_complete=True)
        self.assertEqual(out, {})  # fail closed:不拿空表冒充实时主档
        write.assert_not_called()
        self.assertEqual(self.mem.rows, {})


if __name__ == "__main__":
    unittest.main()
