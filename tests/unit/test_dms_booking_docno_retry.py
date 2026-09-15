# -*- coding: utf-8 -*-
"""DMS 订车单原生取号协议 + 单号重复重试(create_booking_via_form)。

真因(2026-09-13 只读实测 · 见 services/erp/mrerp_dms_docno.py 顶注):

* 旧代码 ``_next_booking_docno`` 只留 ``autonumdetail.php`` 的 ``detail[2]`` 完整号,
  丢掉 ``detail[0]``(隐藏字段 ``idatndt``)、``detail[1]``(``natn``)与 ``cfg[2]`` 前缀,
  再拿整串号塞进原生表单的 ``txtdocno``(前缀栏留空)→ 原生保存/重复检查契约被破坏,
  计数器永不推进:当前实例 BK...000001~000007 已占用,取号仍回 ...000001。
* 修法:显式携带 native 取号状态(前缀 + 完整号 + 数字主体 + idatndt + natn),
  建单前只读扫列表选号并把 ``natn`` 同量前移,POST 完全模拟原生两栏表单。

这里覆盖解析、失败关闭、失步顺号、重复 bump 与「前缀与主体始终同步」。
"""

import json
import unittest
from dataclasses import replace
from unittest.mock import patch

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_client_ops import (
    DMSClientOpsMixin,
    _bump_docno,
    _is_duplicate_docno_error,
)
from services.erp.mrerp_dms_docno import (
    DMSBookingAutonumState,
    autonum_state,
    listing_docnos,
    parse_autonum_detail,
    scan_unoccupied_docno,
)

_DUP_BODY = 'err::"เลขที่ใบจอง" ซ้ำ'


class _Resp:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


def _cfg(prefix="BK", digits=6, enabled="1", autonum_id="16"):
    return json.dumps([autonum_id, enabled, prefix, digits, "1"])


def _detail(docno, *, idatndt="27", natn="1"):
    return json.dumps([idatndt, natn, docno])


class _RecordingTransport:
    """记录每次 new.php 提交的完整字段表;已占用号回 DMS 重复报错。"""

    def __init__(self, used):
        self.used = set(used)
        self.posts = []

    def post(self, url, data=None, files=None, timeout_ms=None):
        data = dict(data or {})
        self.posts.append(data)
        docno = f"{data.get('txtprefixautonum', '')}{data.get('txtdocno', '')}"
        if docno in self.used:
            return _Resp(200, _DUP_BODY)
        return _Resp(200, "ok")

    def docnos(self):
        return [f"{d.get('txtprefixautonum', '')}{d.get('txtdocno', '')}" for d in self.posts]


class _FakeDMSClient(DMSClientOpsMixin):
    """只保留取号/建单路径所需的依赖,其余桩掉;取号回原生三元组形态。"""

    def __init__(self, transport, *, cfg_body, detail_body, listing=()):
        self.transport = transport
        self._cfg_body = cfg_body
        self._detail_body = detail_body
        self.listing = tuple(listing)
        self.listing_unavailable = False
        self.listing_requests = []
        self.autonum_requests = []

    def _url(self, p):
        return "http://dms.test/" + p

    def _post_text(self, path, data=None):
        if path.endswith("autonum.php"):
            self.autonum_requests.append(dict(data or {}))
            return self._cfg_body
        if path.endswith("autonumdetail.php"):
            self.autonum_requests.append(dict(data or {}))
            return self._detail_body
        if path.endswith("showdata.php"):
            self.listing_requests.append(dict(data or {}))
            if self.listing_unavailable:
                raise TimeoutError("listing unavailable")
            return "".join(f"<p>{value}</p>" for value in self.listing)
        return "<form></form>"

    def _parse_form_defaults(self, html):
        return {}

    def _apply_booking_form_fields(self, data, *, customer_id, booking, card):
        pass

    def search_booking(self, docno):
        return "BID-" + docno


class _Branch:
    id = "42"


class _Booking:
    branch = _Branch()


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


class TestListingDocnos(unittest.TestCase):
    def test_only_accepts_same_prefix_and_digit_width(self):
        body = "<p>BK2608000001</p><p>BK2608000025</p><p>PN2608000099</p><p>BK260800123</p>"
        self.assertEqual(listing_docnos(body, "BK2608", 6), {"BK2608000001", "BK2608000025"})


class TestAutonumProtocol(unittest.TestCase):
    """autonum.php + autonumdetail.php → 原生取号状态(不硬编码任何前缀)。"""

    def test_current_bk_shape_keeps_prefix_number_and_hidden_fields(self):
        state = autonum_state(_cfg("BK", 6), _detail("BK000002609000001", idatndt="27", natn="1"))
        self.assertEqual(state.prefix, "BK")
        self.assertEqual(state.docno, "BK000002609000001")
        self.assertEqual(state.body, "000002609000001")  # 数字主体 = 完整号去精确前缀
        self.assertEqual(state.tail_serial, "000001")
        self.assertEqual(state.idautonumdetail, "27")
        self.assertEqual(state.nextautonum, 1)

    def test_non_bk_and_non_ascci_prefix_needs_no_regex_shape(self):
        # 前缀来自配置:允许 1 位/多位、非 ASCII、含数字 —— 绝不能假定两位字母。
        for prefix, digits, docno in (
            ("PD", 4, "PD26000042"),
            ("จอง", 3, "จอง260009"),
            ("AB12", 5, "AB122600099"),
        ):
            with self.subTest(prefix=prefix):
                state = autonum_state(_cfg(prefix, digits), _detail(docno, natn="42"))
                self.assertEqual(state.prefix, prefix)
                self.assertEqual(state.docno, docno)
                self.assertEqual(state.body, docno[len(prefix) :])
                self.assertEqual(state.tail_serial, docno[-digits:])
                self.assertEqual(state.nextautonum, 42)
                self.assertEqual(state.body + state.prefix, docno[len(prefix) :] + prefix)

    def test_full_number_must_start_with_configured_prefix(self):
        with self.assertRaises(ValueError):
            autonum_state(_cfg("BK", 6), _detail("PD000002609000001"))

    def test_detail_missing_hidden_fields_fail_closed(self):
        for bad in (
            json.dumps(["27", "1"]),  # 缺 detail[2]
            json.dumps(["", "1", "BK000002609000001"]),  # 缺 idatndt
            json.dumps(["27", "x", "BK000002609000001"]),  # natn 非整数
            json.dumps(["27", "-1", "BK000002609000001"]),  # natn 负数
            json.dumps(["27", "1", ""]),  # 缺完整号
            json.dumps(["27", "1", "BK"]),  # 有前缀无主体
            "not json",
        ):
            with self.subTest(detail=bad):
                with self.assertRaises(ValueError):
                    autonum_state(_cfg("BK", 6), bad)

    def test_config_missing_fields_fail_closed(self):
        for bad in (
            json.dumps([None, "1", "BK", 6, "1"]),  # 缺编号器 id
            json.dumps(["16", "0", "BK", 6, "1"]),  # 未启用
            json.dumps(["16", "1", "", 6, "1"]),  # 空前缀
            json.dumps(["16", "1", "BK", 0, "1"]),  # 位宽非正
            json.dumps(["16", "1", "BK", "x", "1"]),  # 位宽非整数
            json.dumps(["16", "1"]),  # 形状不对
            "autonum off",
        ):
            with self.subTest(cfg=bad):
                with self.assertRaises(ValueError):
                    autonum_state(bad, _detail("BK000002609000001"))

    def test_parse_detail_keeps_raw_triple(self):
        detail = parse_autonum_detail(_detail("BK000002609000001", idatndt="27", natn="1"))
        self.assertEqual(detail.idautonumdetail, "27")
        self.assertEqual(detail.nextautonum, "1")
        self.assertEqual(detail.lastautonum, "BK000002609000001")

    def test_scan_reports_delta_against_candidate_serial(self):
        listing = [f"BK2606{index:06d}" for index in range(1, 8)]
        scan = scan_unoccupied_docno(
            "BK2606000001", 6, lambda path, data: "".join(f"<p>{v}</p>" for v in listing)
        )
        self.assertEqual(scan.docno, "BK2606000008")
        self.assertEqual(scan.numeric_tail, "000008")
        self.assertEqual(scan.delta, 7)

    def test_scan_falls_back_to_candidate_when_listing_unavailable(self):
        def boom(path, data):
            raise TimeoutError("listing unreachable")

        scan = scan_unoccupied_docno("BK2606000001", 6, boom)
        self.assertEqual((scan.docno, scan.numeric_tail, scan.delta), ("BK2606000001", "000001", 0))


class TestBookingDocnoRetry(unittest.TestCase):
    """transport 级:原生两栏 payload、失步顺号、重复 bump 都看真实字段。"""

    def setUp(self):
        # 本套只锁编号。落库表单的精确回读(含空可见面与管理员兜底)另有 transport 级套件。
        probe = patch(
            "services.erp.mrerp_dms_booking_submit.verify_created_booking",
            side_effect=lambda client, docno, submitted, **kwargs: client.search_booking(docno),
        )
        probe.start()
        self.addCleanup(probe.stop)

    def _client(self, transport, *, cfg_body, detail_body, listing=()):
        return _FakeDMSClient(
            transport, cfg_body=cfg_body, detail_body=detail_body, listing=listing
        )

    def test_posts_native_two_cell_payload_not_the_full_number(self):
        tr = _RecordingTransport([])
        cl = self._client(tr, cfg_body=_cfg("BK", 6), detail_body=_detail("BK000002609000001"))
        bid, bno = cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual((bid, bno), ("BID-BK000002609000001", "BK000002609000001"))
        self.assertEqual(len(tr.posts), 1)
        sent = tr.posts[0]
        self.assertEqual(sent["txtprefixautonum"], "BK")
        self.assertEqual(sent["txtdocno"], "000002609000001")  # 纯数字主体,不是整串
        self.assertNotIn("BK", sent["txtdocno"])
        self.assertEqual(sent["idatndt"], "27")
        self.assertEqual(sent["natn"], "1")
        self.assertEqual(sent["txtprefixautonum"] + sent["txtdocno"], "BK000002609000001")

    def test_out_of_sync_listing_selects_next_serial_and_moves_natn(self):
        # 真实失步场景:detail 回 ...000001/natn=1,列表已有 1~7 → 必须只 POST 一次 ...000008
        # 且 natn=8(计数器与所选号同步),绝不重写真实 1~7。
        used = [f"BK000002609{index:06d}" for index in range(1, 8)]
        tr = _RecordingTransport(used)
        cl = self._client(
            tr,
            cfg_body=_cfg("BK", 6),
            detail_body=_detail("BK000002609000001", idatndt="27", natn="1"),
            listing=used,
        )
        bid, bno = cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual((bid, bno), ("BID-BK000002609000008", "BK000002609000008"))
        self.assertEqual(len(tr.posts), 1)
        sent = tr.posts[0]
        self.assertEqual(sent["txtprefixautonum"], "BK")
        self.assertEqual(sent["txtdocno"], "000002609000008")
        self.assertEqual(sent["idatndt"], "27")
        self.assertEqual(sent["natn"], "8")  # detail[1]=1 + delta 7
        # 只读扫描按「配置前缀 + 号段」搜(不是写死的两位前缀/纯流水)。
        self.assertEqual(cl.listing_requests[0]["sd"], "BK000002609")

    def test_out_of_sync_listing_keeps_a_counter_base_above_the_tail(self):
        # natn 是 DMS 计数器基数,不必等于单号尾号:detail 回 natn=101 而尾号=1 时,
        # 选到尾号 8 只能发 natn=108。写成「natn = 新尾号 8」会把基数抹掉,
        # 下一次取号直接倒回 2~8 这段已占用的号。
        used = [f"BK000002609{index:06d}" for index in range(1, 8)]
        tr = _RecordingTransport(used)
        cl = self._client(
            tr,
            cfg_body=_cfg("BK", 6),
            detail_body=_detail("BK000002609000001", idatndt="27", natn="101"),
            listing=used,
        )
        bid, bno = cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual((bid, bno), ("BID-BK000002609000008", "BK000002609000008"))
        self.assertEqual(len(tr.posts), 1)  # delta 只推一次,409/重复都不该出现
        sent = tr.posts[0]
        self.assertEqual(sent["txtprefixautonum"], "BK")
        self.assertEqual(sent["txtdocno"], "000002609000008")  # 选号与计数器基数无关
        self.assertEqual(sent["natn"], "108")  # 101 + delta 7,不是 8

    def test_duplicate_bump_moves_body_and_natn_together(self):
        used = ["BK2606000001", "BK2606000002"]
        tr = _RecordingTransport(used)
        cl = self._client(tr, cfg_body=_cfg("BK2606", 6), detail_body=_detail("BK2606000001"))
        bid, bno = cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual((bid, bno), ("BID-BK2606000003", "BK2606000003"))
        self.assertEqual(tr.docnos(), used + ["BK2606000003"])  # 每次 bump 都真发过
        bodies = [d["txtdocno"] for d in tr.posts]
        natns = [d["natn"] for d in tr.posts]
        self.assertEqual(bodies, ["000001", "000002", "000003"])
        self.assertEqual(natns, ["1", "2", "3"])  # 数字主体与 natn 一起递增
        self.assertTrue(all(d["txtprefixautonum"] == "BK2606" for d in tr.posts))

    def test_duplicate_bump_keeps_a_counter_base_above_the_tail(self):
        # 扫描拿不到号段时的兜底路径:原生候选是基数 107 / 尾号 7,而 7~9 都被占
        # → 两次重复 bump 每次只 +1,尾号 8/9 配 natn 108/109,最后落到尾号 10/natn 110。
        taken = [f"BK2606{index:06d}" for index in range(1, 10)]
        tr = _RecordingTransport(taken)
        cl = self._client(
            tr,
            cfg_body=_cfg("BK2606", 6),
            detail_body=_detail("BK2606000007", natn="107"),
        )
        cl.listing_unavailable = True  # 扫描拿不到号段 → 只能靠重复 bump 往后走
        bid, bno = cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual((bid, bno), ("BID-BK2606000010", "BK2606000010"))
        self.assertEqual(
            tr.docnos(), ["BK2606000007", "BK2606000008", "BK2606000009", "BK2606000010"]
        )
        self.assertEqual(
            [d["txtdocno"] for d in tr.posts], ["000007", "000008", "000009", "000010"]
        )
        self.assertEqual([d["natn"] for d in tr.posts], ["107", "108", "109", "110"])  # delta-only

    def test_out_of_sync_then_duplicate_keeps_natn_in_step_with_body(self):
        # 顺号选到 ...008(natn=8)又撞重复:DMS 计数器停在 1,重试必须自己把 8→9 一起推。
        used = [f"BK2606{index:06d}" for index in range(1, 10)]
        tr = _RecordingTransport(used)
        cl = self._client(
            tr,
            cfg_body=_cfg("BK2606", 6),
            detail_body=_detail("BK2606000001", natn="1"),
            listing=used[:8],
        )
        bid, bno = cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual((bid, bno), ("BID-BK2606000010", "BK2606000010"))
        self.assertEqual([d["txtdocno"] for d in tr.posts], ["000009", "000010"])
        self.assertEqual([d["natn"] for d in tr.posts], ["9", "10"])

    def test_on_attempt_sees_the_full_canonical_number(self):
        used = [f"BK2606{index:06d}" for index in range(1, 4)]
        tr = _RecordingTransport(used)
        cl = self._client(tr, cfg_body=_cfg("BK2606", 6), detail_body=_detail("BK2606000001"))
        seen = []
        cl.create_booking_via_form(
            customer_id="100", booking=_Booking(), card=object(), on_attempt=seen.append
        )
        # 台账 marker 每次都必须给完整号(不是纯数字主体),否则草稿与 DMS 单号对不上。
        self.assertEqual(seen, ["BK2606000001", "BK2606000002", "BK2606000003", "BK2606000004"])
        self.assertEqual(seen[-1], "BK2606000004")

    def test_autonum_protocol_unavailable_fails_closed_without_write(self):
        tr = _RecordingTransport([])
        for cfg_body, detail_body in (
            ("", ""),
            (_cfg("BK", 6), json.dumps(["27", "1"])),  # 缺完整号
            (_cfg("BK", 6), json.dumps(["", "1", "BK000002609000001"])),  # 缺 idatndt
            (_cfg("BK", 6), json.dumps(["27", "x", "BK000002609000001"])),  # natn 无效
            (json.dumps(["16", "0", "BK", 6, "1"]), _detail("BK000002609000001")),  # 未启用
        ):
            with self.subTest(detail=detail_body):
                tr.posts.clear()
                cl = self._client(tr, cfg_body=cfg_body, detail_body=detail_body)
                with self.assertRaises(DMSClientError) as ctx:
                    cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
                self.assertEqual(ctx.exception.error_code, "ERR_DMS_IMPORT")
                self.assertEqual(tr.posts, [])  # 协议不兼容绝不写、也绝不造号

    def test_all_taken_raises_import_error(self):
        used = [f"BK2606{index:06d}" for index in range(1, 60)]
        tr = _RecordingTransport(used)
        cl = self._client(tr, cfg_body=_cfg("BK2606", 6), detail_body=_detail("BK2606000001"))
        with self.assertRaises(DMSClientError) as ctx:
            cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_IMPORT")

    def test_non_duplicate_error_does_not_retry(self):
        tr = _RecordingTransport([])
        tr.post = lambda url, data=None, files=None, timeout_ms=None: (
            tr.posts.append(dict(data or {})) or _Resp(200, 'err::"something broke"')
        )
        cl = self._client(tr, cfg_body=_cfg("BK2606", 6), detail_body=_detail("BK2606000001"))
        with self.assertRaises(DMSClientError):
            cl.create_booking_via_form(customer_id="100", booking=_Booking(), card=object())
        self.assertEqual(len(tr.posts), 1)  # 非重复错误 → 不重试

    def test_with_docno_adds_the_serial_delta_only_once(self):
        """换号 = 只加「新尾号 - 旧尾号」;natn 是计数器基数,绝不能被尾号绝对值覆盖。"""
        state = DMSBookingAutonumState(
            prefix="BK2606",
            docno="BK2606000001",
            digits=6,
            idautonumdetail="27",
            nextautonum=1,
        )
        bumped = state.with_docno("BK2606000008")
        self.assertEqual(
            (bumped.docno, bumped.body, bumped.tail_serial), ("BK2606000008", "000008", "000008")
        )
        self.assertEqual(bumped.nextautonum, 8)
        self.assertEqual(bumped.prefix, "BK2606")  # 前缀不因 bump 改变
        # 同一状态再换一次号也只看这一对新旧尾号 +1,不是在已有 natn 上累加尾号。
        self.assertEqual(bumped.with_docno("BK2606000009").nextautonum, 9)

    def test_with_docno_keeps_a_counter_base_that_differs_from_the_tail(self):
        """natn=101/尾号=1 是合法原生状态:换到尾号 8 必须发 natn=108,不是 8。"""
        state = DMSBookingAutonumState(
            prefix="BK",
            docno="BK000002609000001",
            digits=6,
            idautonumdetail="27",
            nextautonum=101,
        )
        moved = state.with_docno("BK000002609000008")
        self.assertEqual((moved.docno, moved.tail_serial), ("BK000002609000008", "000008"))
        self.assertEqual(moved.nextautonum, 108)  # 101 + (8 - 1),保留基数
        # 反向换号不允许把计数器写成负数(状态不自洽就该炸,不是静默写坏)。
        floor = replace(state, nextautonum=0)
        with self.assertRaises(ValueError):
            floor.with_docno("BK000002609000000")  # 0 + (0 - 1)

    def test_with_docno_uses_the_configured_width_for_the_delta(self):
        """基数与尾号各走各的:计数器基数 7、单号尾号 0042(两月不同流水段)也只看差值。"""
        state = DMSBookingAutonumState(
            prefix="BK2606",
            docno="BK2606000042",
            digits=6,
            idautonumdetail="27",
            nextautonum=7,
        )
        moved = state.with_docno("BK2606000050")
        self.assertEqual((moved.tail_serial, moved.nextautonum), ("000050", 15))  # 7 + 8


if __name__ == "__main__":
    unittest.main()
