# -*- coding: utf-8 -*-
"""DMS 订车单单号重复重试(create_booking_via_form)。

真因(2026-06-14):DMS autonum 计数器按分店分段,跟全局唯一约束失步 → 回的
「下一个号」可能已被占用,提交即 err::"เลขที่ใบจอง" ซ้ำ → 每次推送都撞同一个号。
修法:撞重复就往后顺号重试,跳过所有已占用号。
"""

import unittest

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_client_ops import (
    DMSClientOpsMixin,
    _bump_docno,
    _is_duplicate_docno_error,
)

_DUP_BODY = 'err::"เลขที่ใบจอง" ซ้ำ'


class _Resp:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


class _FakeTransport:
    """已占用号回 DMS 重复报错,空闲号回成功。记录每次提交的 txtdocno。"""

    def __init__(self, used):
        self.used = set(used)
        self.posts = []

    def post(self, url, data=None, files=None, timeout_ms=None):
        docno = (data or {}).get("txtdocno")
        self.posts.append(docno)
        if docno in self.used:
            return _Resp(200, _DUP_BODY)
        return _Resp(200, "ok")


class _FakeClient(DMSClientOpsMixin):
    """只保留单号重试路径所需的依赖,其余桩掉。"""

    def __init__(self, transport, start_docno):
        self.transport = transport
        self._start = start_docno

    def _url(self, p):
        return "http://dms.test/" + p

    def _post_text(self, path, data=None):
        return "<form></form>"

    def _parse_form_defaults(self, html):
        return {}

    def _apply_booking_form_fields(self, data, *, customer_id, booking, card):
        pass

    def _next_booking_docno(self, branch_id):
        return self._start

    def search_booking(self, docno):
        return "BID-" + docno


class _Branch:
    id = "42"


class _Booking:
    branch = _Branch()
    booking_no = "BK2606000001"


class TestBumpDocno(unittest.TestCase):
    def test_keeps_width(self):
        self.assertEqual(_bump_docno("BK2606000001"), "BK2606000002")
        self.assertEqual(_bump_docno("BK2606000009"), "BK2606000010")
        self.assertEqual(_bump_docno("BK2606000099"), "BK2606000100")

    def test_no_digit_tail(self):
        self.assertEqual(_bump_docno("BK"), "BK1")


class TestDuplicateDetect(unittest.TestCase):
    def test_detect(self):
        self.assertTrue(_is_duplicate_docno_error(_DUP_BODY))

    def test_other_errors_not_duplicate(self):
        self.assertFalse(_is_duplicate_docno_error("ok"))
        self.assertFalse(_is_duplicate_docno_error('err::"something else" failed'))


class TestBookingDocnoRetry(unittest.TestCase):
    def test_skips_used_numbers(self):
        used = ["BK2606000001", "BK2606000002", "BK2606000003"]
        tr = _FakeTransport(used)
        cl = _FakeClient(tr, "BK2606000001")
        bid, bno = cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual(bno, "BK2606000004")
        self.assertEqual(bid, "BID-BK2606000004")
        self.assertEqual(tr.posts, used + ["BK2606000004"])

    def test_first_number_free_no_retry(self):
        tr = _FakeTransport([])
        cl = _FakeClient(tr, "BK2606000001")
        bid, bno = cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual(bno, "BK2606000001")
        self.assertEqual(tr.posts, ["BK2606000001"])

    def test_all_taken_raises_import_error(self):
        used = ["BK2606" + str(i).zfill(6) for i in range(1, 60)]
        tr = _FakeTransport(used)
        cl = _FakeClient(tr, "BK2606000001")
        with self.assertRaises(DMSClientError) as ctx:
            cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_IMPORT")

    def test_non_duplicate_error_does_not_retry(self):
        tr = _FakeTransport([])

        def _post(url, data=None, files=None, timeout_ms=None):
            tr.posts.append((data or {}).get("txtdocno"))
            return _Resp(200, 'err::"something broke"')

        tr.post = _post
        cl = _FakeClient(tr, "BK2606000001")
        with self.assertRaises(DMSClientError):
            cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual(len(tr.posts), 1)  # 非重复错误 → 不重试


if __name__ == "__main__":
    unittest.main()
