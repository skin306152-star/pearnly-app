# -*- coding: utf-8 -*-
"""订车单顾问栏(销售提成归属)严格解析。

2026-08-11:顾问栏此前恒填名册首行(_ref_from_default 的首行兜底),而 payload 从没人写
advisor_id → 全公司的单都算到同一个人头上。改成只认调用方钉死的 id,认不出就报错;
名册整份取不到(接口抖)时才按钉死标量降级,不因一次抖动拦生意。
"""

import unittest

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_client_ops import DMSClientOpsMixin
from services.erp.mrerp_dms_models import BookingDefaults, ThaiIdCardPayload

_ADVISORS = [
    ["297", "sale01", "สมชาย", "0811111111"],
    ["335", "sale02", "sale02"],
]


class _FakeClient(DMSClientOpsMixin):
    """只桩 _bshsd:主档取数是本测唯一外部依赖,顺带记录调用参数。"""

    def __init__(self, rows_by_elem):
        self.rows_by_elem = rows_by_elem
        self.calls = []

    def _bshsd(self, elemname, **extra):
        self.calls.append((elemname, extra))
        return list(self.rows_by_elem.get(elemname) or [])


def _defaults(**over) -> BookingDefaults:
    return BookingDefaults(**{"advisor_id": "335", **over})


_CARD = ThaiIdCardPayload(people_id="1101700998118", first_name="ก", last_name="ข", birthday_be="")


class AdvisorStrictTests(unittest.TestCase):
    def test_pinned_id_resolves_to_live_row_with_tel(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        ref = cl._advisor_ref_strict(_defaults(advisor_id="297"))
        self.assertEqual((ref.id, ref.code, ref.name), ("297", "sale01", "สมชาย"))
        self.assertEqual(ref.extra, ("0811111111",))  # txtuserstel 从这里取

    def test_master_is_fetched_unpaged(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        cl._advisor_ref_strict(_defaults())
        self.assertEqual(cl.calls, [("txtusers", {"bshsdamt": "200"})])

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

    def test_empty_master_falls_back_to_pinned_scalars(self):
        cl = _FakeClient({"txtusers": []})
        ref = cl._advisor_ref_strict(
            _defaults(advisor_id="335", advisor_code="sale02", advisor_name="sale02")
        )
        self.assertEqual((ref.id, ref.code, ref.name, ref.extra), ("335", "sale02", "sale02", ()))

    def test_empty_master_without_name_raises_unmatched(self):
        cl = _FakeClient({"txtusers": []})
        with self.assertRaises(DMSClientError) as ctx:
            cl._advisor_ref_strict(_defaults(advisor_id="335"))
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_ADVISOR_UNMATCHED")


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

    def test_unpinned_advisor_blocks_the_whole_booking(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        with self.assertRaises(DMSClientError) as ctx:
            cl.resolve_booking_payload(_defaults(advisor_id=""), _CARD)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_ADVISOR_REQUIRED")


class FetchMastersTests(unittest.TestCase):
    def test_advisors_pulled_unpaged_others_default(self):
        cl = _FakeClient({"txtusers": _ADVISORS})
        cl.fetch_masters()
        extras = dict(cl.calls)
        self.assertEqual(extras["txtusers"], {"bshsdamt": "200"})
        self.assertEqual(extras["txtcar"], {})


if __name__ == "__main__":
    unittest.main()
