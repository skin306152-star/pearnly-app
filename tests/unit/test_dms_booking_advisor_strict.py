# -*- coding: utf-8 -*-
"""订车单顾问栏(销售提成归属)严格解析。

2026-08-11:顾问栏此前恒填名册首行(_ref_from_default 的首行兜底),而 payload 从没人写
advisor_id → 全公司的单都算到同一个人头上。改成只认调用方钉死的 id,认不出就报错;
只有名册取数失败(_bshsd 回 None)才按钉死标量降级,不因一次抖动拦生意 —— 名册真空
(回 [])一律拦,那种单 DMS 必拒,降级只会把失败拖到更晚。
"""

import json
import unittest

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_client_ops import DMSClientOpsMixin
from services.erp.mrerp_dms_models import BookingDefaults, ThaiIdCardPayload

_ADVISORS = [
    ["297", "sale01", "สมชาย", "0811111111"],
    ["335", "sale02", "sale02"],
]


_EMPLOYEE_LISTING = (
    'dt::<div data-val="297"><div><div><p>SALE01</p><p>sale01</p></div>'
    "<div><p>สมชาย</p></div></div></div>"
)


class _FakeClient(DMSClientOpsMixin):
    """桩 _bshsd(主档)+ _post_text(员工表):本测仅有的两个外部依赖,顺带记录调用参数。

    rows_by_elem 的值为 None 表示「取数失败」,与「名册真空([])」分开。
    """

    def __init__(self, rows_by_elem, employees_body=_EMPLOYEE_LISTING):
        self.rows_by_elem = rows_by_elem
        self.employees_body = employees_body
        self.calls = []
        self.posts = []

    def _bshsd(self, elemname, **extra):
        self.calls.append((elemname, extra))
        rows = self.rows_by_elem.get(elemname)
        if rows is None and elemname in self.rows_by_elem:
            return None
        return list(rows or [])

    def _post_text(self, path, data):
        self.posts.append(path)
        return self.employees_body


class _PagedMasters(DMSClientOpsMixin):
    """按 bshsdcurrpage 返回对应页的假客户端(验收普通主档翻页取全与跨页 pinned id)。"""

    def __init__(self, pages_by_elem, employees_body=_EMPLOYEE_LISTING):
        self.pages_by_elem = pages_by_elem
        self.employees_body = employees_body
        self.calls = []

    def _bshsd(self, elemname, **extra):
        self.calls.append((elemname, extra))
        pages = self.pages_by_elem.get(elemname)
        if pages is None:
            return None
        page = int(extra.get("bshsdcurrpage") or 1) - 1
        if page >= len(pages):
            return []
        rows = pages[page]
        return None if rows is None else list(rows)

    def _post_text(self, path, data):
        return self.employees_body


def _defaults(**over) -> BookingDefaults:
    return BookingDefaults(**{"advisor_id": "335", **over})


_CARD = ThaiIdCardPayload(people_id="1101700998118", first_name="ก", last_name="ข", birthday_be="")


class AdvisorStrictTests(unittest.TestCase):
    def test_pinned_id_resolves_to_live_row_with_tel(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        ref = cl._advisor_ref_strict(_defaults(advisor_id="297"))
        self.assertEqual((ref.id, ref.code, ref.name), ("297", "sale01", "สมชาย"))
        self.assertEqual(ref.extra, ("0811111111",))  # txtuserstel 从这里取

    def test_master_is_fetched_paged_from_page_one(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        cl._advisor_ref_strict(_defaults())
        self.assertEqual(cl.calls, [("txtusers", {"bshsdamt": 200, "bshsdcurrpage": 1})])

    def test_missing_pin_raises_required(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        with self.assertRaises(DMSClientError) as ctx:
            cl._advisor_ref_strict(_defaults(advisor_id=""))
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_ADVISOR_REQUIRED")
        self.assertEqual(cl.calls, [])  # 没 pin 就别浪费一次主档请求

    def test_pin_absent_from_master_raises_unmatched(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        with self.assertRaises(DMSClientError) as ctx:
            cl._advisor_ref_strict(_defaults(advisor_id="999", advisor_name="ผีน้อย"))
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_ADVISOR_UNMATCHED")

    def test_fetch_failure_falls_back_to_pinned_scalars(self):
        cl = _FakeClient({"txtusers": None})
        ref = cl._advisor_ref_strict(
            _defaults(advisor_id="335", advisor_code="sale02", advisor_name="sale02")
        )
        self.assertEqual((ref.id, ref.code, ref.name, ref.extra), ("335", "sale02", "sale02", ()))

    def test_fetch_failure_without_name_raises_unmatched(self):
        cl = _FakeClient({"txtusers": None})
        with self.assertRaises(DMSClientError) as ctx:
            cl._advisor_ref_strict(_defaults(advisor_id="335"))
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_ADVISOR_UNMATCHED")

    def test_empty_master_raises_even_with_pinned_name(self):
        # 名册真空 ≠ 取数失败:真空时 DMS 必拒这张单,降级放行只会把失败拖到更晚。
        cl = _FakeClient({"txtusers": []})
        with self.assertRaises(DMSClientError) as ctx:
            cl._advisor_ref_strict(
                _defaults(advisor_id="335", advisor_code="sale02", advisor_name="sale02")
            )
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_ADVISOR_UNMATCHED")


class RefFromDefaultStrictTests(unittest.TestCase):
    """普通主档 pinned id 一旦存在就走严格解析:主档读不到/找不到都不许回落首行或标量。

    _ref_from_default 的历史行为是「找不到 pinned 就悄悄取 rows[0]」——主档在第 2 页/被删
    时整单填错且当场无感。现在 pinned 只认 live rows 命中,失败按码上抛(见 2026-08-18 派单)。
    """

    def test_pinned_id_absent_raises_unmatched_not_first_row(self):
        # rows 有内容但找不到 pinned:绝不能回落 rows[0](会拿第一辆车顶替客户选的车)。
        cl = _FakeClient({"txtcar": [["c1", "DMX", "D-Max"], ["c2", "MX5", "MX-5"]]})
        with self.assertRaises(DMSClientError) as ctx:
            cl._ref_from_default("txtcar", "zz9", "", "")
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")

    def test_fetch_failure_with_pin_raises_unavailable(self):
        # 取数失败(rows None)≠ 真空:主档可能只是暂时读不到,重试有机会,但不许提交旧值。
        cl = _FakeClient({"txtcar": None})
        with self.assertRaises(DMSClientError) as ctx:
            cl._ref_from_default("txtcar", "c1", "", "")
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNAVAILABLE")

    def test_empty_master_with_pin_raises_unmatched(self):
        # 主档真空(rows [])是 DMS 的真实状态而非抖动:重试拿到的还是空,必须重选。
        cl = _FakeClient({"txtcar": []})
        with self.assertRaises(DMSClientError) as ctx:
            cl._ref_from_default("txtcar", "c1", "", "")
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")


class ResolveBookingPayloadTests(unittest.TestCase):
    def test_booking_payload_carries_matched_advisor(self):
        cl = _FakeClient({"txtusers": _ADVISORS, "txtcar": [["c1", "DMX", "D-Max"]]})
        booking = cl.resolve_booking_payload(_defaults(advisor_id="335"), _CARD)
        self.assertEqual(booking.advisor.id, "335")
        self.assertEqual(booking.advisor.name, "sale02")

    def test_other_masters_keep_first_row_fallback(self):
        # 顾问改严了,其余主档(车/场所/条件…)的首行兜底行为原样保留。
        cl = _FakeClient({"txtusers": _ADVISORS, "txtplacebook": [["pl1", "", "สาขาบางนา"]]})
        booking = cl.resolve_booking_payload(_defaults(), _CARD)
        self.assertEqual(booking.place_book.id, "pl1")

    def test_pinned_car_resolves_from_live_rows(self):
        # 普通主档 pinned id 有 live rows 时必须按该行解析(不落首行、不落标量)。
        cl = _FakeClient(
            {"txtusers": _ADVISORS, "txtcar": [["c1", "DMX", "D-Max"], ["c2", "MX5", "MX-5"]]}
        )
        booking = cl.resolve_booking_payload(
            _defaults(advisor_id="335", car_id="c2", car_code="MX5"), _CARD
        )
        self.assertEqual(
            (booking.car.id, booking.car.code, booking.car.name), ("c2", "MX5", "MX-5")
        )

    def test_resolve_raises_when_pinned_master_unavailable(self):
        # 全链路:主档取数失败时不再静默提交空/旧标量,而是按 UNAVAILABLE 上抛。
        cl = _FakeClient({"txtusers": _ADVISORS, "txtcar": None})
        with self.assertRaises(DMSClientError) as ctx:
            cl.resolve_booking_payload(_defaults(advisor_id="335", car_id="c1"), _CARD)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNAVAILABLE")

    def test_pinned_id_on_second_page_resolves(self):
        """pinned id 在第 2 页:全量翻页后仍能命中,不许回落第 1 页首行。"""
        page1 = [[f"pl{i}", "", f"สาขา {i}"] for i in range(200)]
        cl = _PagedMasters({"txtplacebook": [page1, [["pl200", "", "สาขา 200"]]]})
        ref = cl._ref_from_default("txtplacebook", "pl200", "", "")
        self.assertEqual((ref.id, ref.name), ("pl200", "สาขา 200"))
        self.assertEqual(
            [c[1]["bshsdcurrpage"] for c in cl.calls if c[0] == "txtplacebook"], [1, 2]
        )

    def test_unpinned_advisor_blocks_the_whole_booking(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        with self.assertRaises(DMSClientError) as ctx:
            cl.resolve_booking_payload(_defaults(advisor_id=""), _CARD)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_ADVISOR_REQUIRED")


class FetchMastersTests(unittest.TestCase):
    def test_advisors_pulled_paged_others_default(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        out = cl.fetch_masters()
        extras = dict(cl.calls)
        self.assertEqual(extras["txtusers"], {"bshsdamt": 200, "bshsdcurrpage": 1})
        # 普通主档与顾问名册一样翻页取全:第一页参数一致,第 2 页不满即止。
        self.assertEqual(extras["txtcar"], {"bshsdamt": 200, "bshsdcurrpage": 1})
        self.assertIn("prefixes", out)

    def test_fetch_masters_pulls_full_pages(self):
        """普通主档翻页取全:第 1 页满页继续拉第 2 页,选项一条不丢。"""
        page1 = [[f"c{i}", f"V{i}", f"Vios {i}"] for i in range(200)]
        cl = _PagedMasters({"txtcar": [page1, [["c200", "V200", "Vios 200"]]]})
        out = cl.fetch_masters()
        self.assertEqual(len(out["cars"]), 201)
        self.assertEqual(out["cars"][-1][0], "c200")
        pages = [c[1]["bshsdcurrpage"] for c in cl.calls if c[0] == "txtcar"]
        self.assertEqual(pages, [1, 2])

    def test_employees_pulled_for_the_exact_advisor_layer(self):
        # 顾问下拉的 code 列是员工编号,登录名只有员工表有 → 主档必须带上 employees。
        out = _FakeClient({"txtusers": _ADVISORS}).fetch_masters()
        self.assertEqual(
            out["employees"], [{"id": "297", "code": "SALE01", "login": "sale01", "name": "สมชาย"}]
        )

    def test_fetch_failure_degrades_to_empty_list(self):
        cl = _FakeClient({"txtusers": None, "txtcar": None}, employees_body="<html>login</html>")
        with self.assertLogs("services.erp.dms_employees", "WARNING"):
            out = cl.fetch_masters()
        self.assertEqual(out["advisors"], [])
        self.assertEqual(out["cars"], [])
        # 员工表拿不到不该拖垮整份主档:落 [],顾问匹配自己退化到启发层。
        self.assertEqual(out["employees"], [])


class BshsdPagingTests(unittest.TestCase):
    """_bshsd_all:翻页取全 + 失败传播 + 截断留痕(顾问名册靠它才拿得到第 11 个人)。"""

    class _Paged(DMSClientOpsMixin):
        def __init__(self, pages):
            self.pages = pages  # 第 n 页(1-based)的行;取不到 → 空页
            self.calls = []

        def _bshsd(self, elemname, **extra):
            self.calls.append((elemname, extra))
            page = int(extra.get("bshsdcurrpage") or 1)
            rows = self.pages[page - 1] if page <= len(self.pages) else []
            return None if rows is None else list(rows)

    def test_collects_every_full_page(self):
        pages = [[[str(i)] for i in range(3)], [["9"]]]
        cl = self._Paged(pages)
        rows = cl._bshsd_all("txtusers", page_size=3)
        self.assertEqual([r[0] for r in rows], ["0", "1", "2", "9"])
        self.assertEqual([c[1]["bshsdcurrpage"] for c in cl.calls], [1, 2])

    def test_exact_multiple_stops_on_empty_page(self):
        cl = self._Paged([[["0"], ["1"]], []])
        self.assertEqual(len(cl._bshsd_all("txtusers", page_size=2)), 2)
        self.assertEqual(len(cl.calls), 2)

    def test_any_failed_page_fails_the_whole_fetch(self):
        # 半份名册比取不到更危险:「不在名册」的判断会变成瞎话。
        cl = self._Paged([[["0"], ["1"]], None])
        self.assertIsNone(cl._bshsd_all("txtusers", page_size=2))

    def test_truncation_is_logged_not_silent(self):
        cl = self._Paged([[["a"], ["b"]]] * 4)
        with self.assertLogs("services.erp.mrerp_dms_client_ops", "WARNING") as logs:
            rows = cl._bshsd_all("txtusers", page_size=2, max_pages=3)
        self.assertEqual(len(rows), 6)
        self.assertIn("truncated", logs.output[0])


class SessionMemoTests(unittest.TestCase):
    """一次建单会话内同参主档只打一次(resolve + fetch_masters + 成功后刷缓存全共用)。"""

    class _Counting(DMSClientOpsMixin):
        def __init__(self, rows_by_elem, body_by_elem=None):
            self.rows_by_elem = rows_by_elem
            self.body_by_elem = body_by_elem or {}
            self.posts = []

        def _post_text(self, path, data):
            if "elemname" not in data:  # 员工表(users/…/showdata.php),不走 bshsd 备忘
                return _EMPLOYEE_LISTING
            self.posts.append((data["elemname"], data.get("bshsdcurrpage")))
            elem = data["elemname"]
            if elem in self.body_by_elem:
                return self.body_by_elem[elem]
            return json.dumps(self.rows_by_elem.get(elem) or [])

    def test_same_params_hit_the_wire_once(self):
        cl = self._Counting({"txtusers": _ADVISORS, "txtcar": [["c1", "DMX", "D-Max"]]})
        cl.resolve_booking_payload(_defaults(advisor_id="335"), _CARD)
        cl.fetch_masters()
        cl.fetch_masters()
        self.assertEqual(cl.posts.count(("txtusers", "1")), 1)
        self.assertEqual(cl.posts.count(("txtcar", "1")), 1)

    def test_failed_fetch_is_not_memoized(self):
        # 失败进备忘 = 一次抖动毒死整场会话;允许下次重试。
        cl = self._Counting({}, body_by_elem={"txtusers": "<html>session expired</html>"})
        with self.assertLogs("services.erp.mrerp_dms_client_ops", "WARNING"):
            self.assertIsNone(cl._bshsd("txtusers"))
        with self.assertLogs("services.erp.mrerp_dms_client_ops", "WARNING"):
            self.assertIsNone(cl._bshsd("txtusers"))
        self.assertEqual(len(cl.posts), 2)

    def test_empty_master_is_memoized(self):
        cl = self._Counting({"txtusers": []})
        self.assertEqual(cl._bshsd("txtusers"), [])
        self.assertEqual(cl._bshsd("txtusers"), [])
        self.assertEqual(len(cl.posts), 1)


if __name__ == "__main__":
    unittest.main()
