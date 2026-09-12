"""订车单回读回归:短时不可见/模糊命中不得变成「订单不存在」假阴性。

生产事故(BK000002609000006):写入成功、管理员按单号确实查得到,系统却报
`ERR_DMS_BOOKING_OUTCOME_UNKNOWN`。这里锁住新契约:

* 回读只用只读入口(showdata 搜索 + form 详情),**绝不**再 POST `drfcbc/new.php`;
* 单号已知 → 有限次重查 + 必要分页,退避可控(单测 patch,一秒钟都不睡);
* 身份/关键字段必须精确匹配;纯展示镜像字段差异只留脱敏告警;
* 回读任何不确定都保持 submitted=true / retry_safe=false。
"""

import html
import unittest
from unittest.mock import patch

from services.erp.mrerp_dms_booking_readback import (
    READBACK_MAX_ATTEMPTS,
    STAGE_AMBIGUOUS,
    STAGE_CRITICAL_MISMATCH,
    STAGE_IDENTITY_MISMATCH,
    STAGE_SEARCH_EMPTY,
    max_readback_extra_seconds,
)
from services.erp.mrerp_dms_booking_submit import (
    DMSBookingOutcomeUnknown,
    submit_booking,
    verify_created_booking,
)
from services.erp.mrerp_dms_client import DMSClient
from services.erp.mrerp_dms_client_base import DMSClientError

_DOCNO = "PD26001100"
# 生产真实形态(2026-09-13):单号 BK000002609000007 在 DMS 表单里是两格 ——
# txtprefixautonum='BK' + txtdocno='000002609000007';提交的是一整串。
_BK_DOCNO = "BK000002609000007"
_BK_NUMBER = "000002609000007"
_BASE = {
    "stsel": "n",
    "idsel": "",
    # submit_booking 写库时把 txtdocno 拼进表单;回读的身份判据也用它。
    "txtdocno": _DOCNO,
    "cusval": "15024",
    "txtpeopleid": "1101700998118",
    "usersval": "89",
    "carval": "410",
    "carpaintval": "7",
    "branch_bookval": "1",
    "team_bookval": "30",
    "branch_sellval": "1",
    "team_sellval": "30",
    "usersposival2_book": "289",
    "usersposival3_book": "",
    "usersposival4_book": "41",
    "txtcardeliverydate": "19/09/2569",
    "txtearnestmoney": "1000.00",
    "txtmoneytfmon": "1000.00",
    "banktfmonval": "3",
    "txtbusinessnametfmon": "Company",
    "txtaccountnumtfmon": "1234567890",
    "txtbranchnametfmon": "Rayong",
}


def _stored(booking_id="15499", **overrides):
    return {**_BASE, "idsel": booking_id, "stsel": "e", **overrides}


def _submitted_bk(**overrides):
    """提交字典:整串单号(与 DMS 回读表单的两格形态不同)。"""
    return {**_BASE, "txtdocno": _BK_DOCNO, **overrides}


def _stored_native(booking_id="82", *, prefix="BK", number=_BK_NUMBER, **overrides):
    """真实回读表单:单号落成 prefix + 纯数字两格,绝不是提交字典原样。"""
    fields = {key: value for key, value in _BASE.items() if key != "txtdocno"}
    return {
        **fields,
        "stsel": "e",
        "idsel": booking_id,
        "txtprefixautonum": prefix,
        "txtdocno": number,
        **overrides,
    }


def _form(fields):
    return "".join(
        f'<input name="{html.escape(key)}" value="{html.escape(str(value), quote=True)}">'
        for key, value in fields.items()
    )


def _rows(keys):
    return "".join(f'<a data-val="{key}">row</a>' for key in keys)


class _Response:
    def __init__(self, body="", status=200):
        self.text, self.status_code = body, status


class _Transport:
    """脚本化只读传输:showdata 的第 N 次调用返回第 N 个脚本帧,耗尽即空页。

    帧形态:None=空页;list=第 1 页的 id;dict={页号: [id, …]}(缺页=空页)。
    `records` 是详情表单的 id→字段表;没有脚本帧时,第 1 页回落到 `records` 的键。
    """

    def __init__(self, records=None, *, script=None, write_response=None, write_error=None):
        self.records = records or {}
        self.script = list(script or [])
        self.write_response = write_response or _Response("ok")
        self.write_error = write_error
        self.posts = []
        self.search_calls = 0
        self.detail_reads = []
        self._frame = -1

    def post(self, url, data=None, files=None, timeout_ms=None):
        data = dict(data or {})
        self.posts.append((url, data))
        if url.endswith("drfcbc/new.php"):
            if self.write_error:
                raise self.write_error
            return self.write_response
        if url.endswith("drfcbc/component/showdata.php"):
            self.search_calls += 1
            return _Response(self._page_body(int(data.get("sdtpage") or 1)))
        if url.endswith("drfcbc/form.php"):
            booking_id = data.get("id")
            self.detail_reads.append(booking_id)
            fields = self.records.get(booking_id)
            if fields is None:
                return _Response("")
            # 原生详情表单的 idsel 恒等于被打开的那一行。
            return _Response(_form({**fields, "idsel": booking_id}))
        return _Response("")

    def _page_body(self, page):
        if page == 1 and self._frame + 1 < len(self.script):
            self._frame += 1
        if self._frame < 0:
            return _rows(self.records) if page == 1 else ""
        frame = self.script[self._frame]
        if frame is None:
            return ""
        if isinstance(frame, dict):
            return _rows(frame.get(page, ()))
        # 列表帧只有第 1 页有候选;第 2 页为空即终止分页。
        return _rows(frame) if page == 1 else ""

    def writes(self):
        return [data for path, data in self.posts if path.endswith("drfcbc/new.php")]


def _client(sales, admin=None):
    return DMSClient(sales, "https://same-company.test/dms/", admin_transport=admin)


class _NoSleepMixin:
    """回读退避必须可注入:单测里一秒钟都不许睡。"""

    def setUp(self):
        super().setUp()
        self.sleeps = []
        sleeper = patch(
            "services.erp.mrerp_dms_booking_submit.time.sleep",
            side_effect=self.sleeps.append,
        )
        sleeper.start()
        self.addCleanup(sleeper.stop)


class BookingSubmitReadbackTests(_NoSleepMixin, unittest.TestCase):
    def test_generated_vehicle_and_critical_fields_must_survive_readback(self):
        # 身份/关键字段被 DMS 存成别的值 → 绝不报成功(仍是 UNKNOWN)。
        for field in ("txtprice", "carbrandval", "carval", "txtcardeliverydate"):
            with self.subTest(field=field):
                submitted = {**_BASE, field: "123"}
                sales = _Transport({"15499": _stored(**{field: "999"})})
                with self.assertRaises(DMSBookingOutcomeUnknown):
                    submit_booking(_client(sales), submitted, _DOCNO)
                self.assertEqual(len(sales.writes()), 1)

    def test_display_only_fields_may_differ_with_warning(self):
        # 名称/格式化文本是展示镜像:不同仍确认存在,只在响应里留下字段名告警。
        submitted = {
            **_BASE,
            "txtcus": "นาย ทดสอบ ระบบ",
            "txtmanuyear": "2026",
            "txttel": "081-234-5678",
            "txtprovinces": "ระยอง",
        }
        stored = _stored(
            txtcus="นายทดสอบ ระบบ",
            txtmanuyear="2569",
            txttel="0812345678",
            txtprovinces="จังหวัดระยอง",
        )
        sales = _Transport({"15499": stored})
        self.assertEqual(submit_booking(_client(sales), submitted, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)

    def test_attempt_marker_is_persisted_before_post(self):
        sales = _Transport({"15499": _stored()})
        saved = []

        def save(docno):
            self.assertEqual(sales.writes(), [])
            saved.append(docno)

        submit_booking(_client(sales), _BASE, _DOCNO, on_attempt=save)
        self.assertEqual(saved, [_DOCNO])

    def test_failed_attempt_marker_blocks_the_write(self):
        sales = _Transport()

        def fail_save(docno):
            raise RuntimeError("draft store unavailable")

        with self.assertRaisesRegex(RuntimeError, "draft store unavailable"):
            submit_booking(_client(sales), _BASE, _DOCNO, on_attempt=fail_save)
        self.assertEqual(sales.posts, [])

    def test_hidden_sales_draft_is_verified_by_configured_admin_without_admin_write(self):
        sales = _Transport()
        admin = _Transport({"15499": _stored()})
        client = _client(sales, admin)
        client._bshsd_memo = {("irrelevant-sales-cache",): []}
        self.assertEqual(submit_booking(client, _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)
        self.assertEqual(admin.writes(), [])
        self.assertIs(client.transport, sales)
        self.assertTrue(all(url.startswith(client.base_url) for url, _ in admin.posts))
        self.assertEqual(
            [data["sd"] for url, data in admin.posts if url.endswith("showdata.php")], [_DOCNO]
        )

    def test_sales_exact_readback_does_not_login_admin(self):
        sales = _Transport({"15499": _stored(txtmoneytfmon="1,000.00")})
        client = _client(sales, lambda: self.fail("unneeded admin login"))
        self.assertEqual(submit_booking(client, _BASE, _DOCNO), ("15499", _DOCNO))

    def test_success_acknowledgement_without_readback_retains_attempt_and_blocks_retry(self):
        sales = _Transport()
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(_client(sales), _BASE, _DOCNO)
        error = raised.exception
        self.assertEqual(error.error_code, "ERR_DMS_BOOKING_OUTCOME_UNKNOWN")
        self.assertEqual(error.booking_no, _DOCNO)
        self.assertEqual(error.response_body["http_status"], 200)
        self.assertFalse(error.response_body["retry_safe"])
        self.assertTrue(error.response_body["submitted"])
        self.assertEqual(error.response_body["readback_stage"], STAGE_SEARCH_EMPTY)
        self.assertEqual(len(error.response_body["response_sha256"]), 64)
        self.assertEqual(len(sales.writes()), 1)

    def test_timeout_after_commit_is_recovered_without_resubmission(self):
        sales = _Transport(write_error=TimeoutError("response lost"))
        admin = _Transport({"15499": _stored()})
        self.assertEqual(submit_booking(_client(sales, admin), _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)

    def test_timeout_with_no_visible_record_is_unknown_not_safe_to_retry(self):
        sales = _Transport(write_error=TimeoutError("response lost"))
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(_client(sales), _BASE, _DOCNO)
        self.assertFalse(raised.exception.response_body["retry_safe"])
        self.assertEqual(len(sales.writes()), 1)

    def test_http_error_can_follow_commit_and_must_be_read_back(self):
        sales = _Transport({"15499": _stored()}, write_response=_Response("gateway", 502))
        self.assertEqual(submit_booking(_client(sales), _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)

    def test_explicit_rejection_stays_rejected_without_readback_or_retry(self):
        sales = _Transport(write_response=_Response("err::permission denied"))
        with self.assertRaises(DMSClientError) as raised:
            submit_booking(_client(sales), _BASE, _DOCNO)
        self.assertEqual(raised.exception.error_code, "ERR_DMS_IMPORT")
        self.assertEqual(len(sales.posts), 1)

    def test_admin_login_failure_after_submit_keeps_unknown_outcome(self):
        def fail_admin():
            raise RuntimeError("admin session unavailable")

        sales = _Transport()
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(_client(sales, fail_admin), _BASE, _DOCNO)
        self.assertEqual(raised.exception.response_body["readback_source"], "admin_unavailable")
        self.assertEqual(len(sales.writes()), 1)

    def test_fuzzy_first_row_is_skipped_and_exact_stored_form_is_verified(self):
        sales = _Transport({"900": _stored("900", txtdocno="PD260011001"), "15499": _stored()})
        client = _client(sales)
        self.assertEqual(
            verify_created_booking(client, _DOCNO, {**_BASE, "txtdocno": _DOCNO}), "15499"
        )

    def test_multiple_exact_records_are_ambiguous_not_success(self):
        sales = _Transport({"1": _stored("1"), "2": _stored("2")})
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(_client(sales), _BASE, _DOCNO)
        self.assertEqual(raised.exception.response_body["readback_stage"], STAGE_AMBIGUOUS)

    def test_identity_differences_stay_unknown(self):
        # (字段, 我们提交的值, DMS 实际储存的值) —— 身份不一致就不是我们那张单。
        for field, submitted, stored in (
            ("txtdocno", "PD26001100", "PD26001199"),
            ("cusval", "15024", "15025"),
            ("txtpeopleid", "1101700998118", "1101700207360"),
            ("usersval", "89", "90"),
            ("carval", "410", "411"),
            ("carpaintval", "7", "8"),
        ):
            with self.subTest(field=field):
                sales = _Transport({"15499": _stored(**{field: stored})})
                with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
                    submit_booking(_client(sales), {**_BASE, field: submitted}, _DOCNO)
                self.assertEqual(
                    raised.exception.response_body["readback_stage"], STAGE_IDENTITY_MISMATCH
                )
                self.assertFalse(raised.exception.response_body["retry_safe"])
                self.assertEqual(len(sales.writes()), 1)

    def test_critical_organization_payment_and_amount_differences_stay_unknown(self):
        # (字段, 我们提交的值, DMS 实际储存的值) —— 影响归属/金额/付款的关键差异,必须 UNKNOWN。
        for field, submitted, stored in (
            ("branch_bookval", "1", "2"),
            ("team_bookval", "30", "37"),
            ("branch_sellval", "1", "9"),
            ("usersposival2_book", "289", ""),
            ("txtprice", "850000.00", "999999.00"),
            ("txtmoneytfmon", "1000.00", "0"),
            ("txtaccountnumtfmon", "1234567890", ""),
            ("txtbusinessnametfmon", "Company", ""),
            ("banktfmonval", "3", "9"),
            ("txtcardeliverydate", "19/09/2569", "20/09/2569"),
        ):
            with self.subTest(field=field):
                sales = _Transport({"15499": _stored(**{field: stored})})
                with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
                    submit_booking(_client(sales), {**_BASE, field: submitted}, _DOCNO)
                self.assertEqual(
                    raised.exception.response_body["readback_stage"], STAGE_CRITICAL_MISMATCH
                )
                self.assertFalse(raised.exception.response_body["retry_safe"])
                self.assertEqual(len(sales.writes()), 1)


class BookingDocnoEquivalenceTests(unittest.TestCase):
    """单号等价:提交 BK+纯数字 与回读 prefix='BK' + txtdocno=纯数字 是同一张单。

    判据必须严格 —— 删字母、只比尾号、模糊前缀都会把别单认成我们刚提交的那张。
    """

    def test_prefix_plus_number_shape_matches_the_submitted_docno(self):
        from services.erp.mrerp_dms_booking_readback import docno_equal

        self.assertTrue(docno_equal(_BK_DOCNO, {"txtprefixautonum": "BK", "txtdocno": _BK_NUMBER}))
        # 旧形态/同形存储:回读的 txtdocno 就是我们提交的那一串。
        self.assertTrue(docno_equal(_BK_DOCNO, {"txtdocno": _BK_DOCNO}))
        self.assertTrue(docno_equal(_DOCNO, {"txtdocno": _DOCNO, "txtprefixautonum": _DOCNO[:2]}))

    def test_other_prefix_or_number_is_not_the_same_docno(self):
        from services.erp.mrerp_dms_booking_readback import docno_equal

        base = {"txtprefixautonum": "BK", "txtdocno": _BK_NUMBER}
        self.assertFalse(docno_equal(_BK_DOCNO, {**base, "txtprefixautonum": "PD"}))
        self.assertFalse(docno_equal(_BK_DOCNO, {**base, "txtprefixautonum": "bk"}))
        self.assertFalse(docno_equal(_BK_DOCNO, {**base, "txtdocno": "000002609000008"}))
        # 只比尾号/删字母就会误判的两种形态
        self.assertFalse(
            docno_equal(_BK_DOCNO, {"txtprefixautonum": "BKX", "txtdocno": _BK_NUMBER})
        )
        self.assertFalse(docno_equal(_BK_DOCNO, {"txtprefixautonum": "BK", "txtdocno": "09000007"}))

    def test_missing_cells_and_prefixless_submission_never_match(self):
        from services.erp.mrerp_dms_booking_readback import docno_equal

        # 缺前缀格(只剩纯数字)→ 不是这张单;缺编号格同理。
        self.assertFalse(docno_equal(_BK_DOCNO, {"txtdocno": _BK_NUMBER}))
        self.assertFalse(docno_equal(_BK_DOCNO, {"txtprefixautonum": "BK", "txtdocno": ""}))
        # 提交值本身没有前缀、回读的 txtdocno 又逐字相同 → 同形存储,按规则 1 通过;
        # 但只要编号不同就不再等价(前缀格凑不出一张单)。
        self.assertTrue(docno_equal(_BK_NUMBER, {"txtprefixautonum": "BK", "txtdocno": _BK_NUMBER}))
        self.assertFalse(
            docno_equal(_BK_NUMBER, {"txtprefixautonum": "BK", "txtdocno": "000002609000008"})
        )
        self.assertFalse(docno_equal(_BK_DOCNO, {}))


class BookingReadbackNativeDocnoTests(_NoSleepMixin, unittest.TestCase):
    """回读表单一律用真实形态(prefix + 纯数字),不再把提交字典原样当回读表单。"""

    def test_configured_prefix_shapes_need_no_regex(self):
        """前缀来自配置:非两位/non-ASCII/含数字都能精确拼接,不靠正则形状。"""
        for prefix, number in (("BK", _BK_NUMBER), ("PD", "26001100"), ("AB12", "2600099")):
            with self.subTest(prefix=prefix):
                full = prefix + number
                sales = _Transport(
                    {"82": _stored_native(prefix=prefix, number=number)},
                )
                submitted = {**_BASE, "txtprefixautonum": prefix, "txtdocno": full}
                self.assertEqual(submit_booking(_client(sales), submitted, full), ("82", full))
                self.assertEqual(len(sales.writes()), 1)

    def test_non_ascii_prefix_concatenates_exactly(self):
        # 非 ASCII 前缀照样要能精确拼接;正则形状([A-Za-z]+\\d+)在这里必然落空。
        sales = _Transport({"82": _stored_native(prefix="จอง", number="000042")})
        submitted = {**_BASE, "txtprefixautonum": "จอง", "txtdocno": "จอง000042"}
        self.assertEqual(
            submit_booking(_client(sales), submitted, "จอง000042"), ("82", "จอง000042")
        )

    def test_native_prefix_and_number_verifies_with_a_single_write(self):
        sales = _Transport({"82": _stored_native()})
        self.assertEqual(
            submit_booking(_client(sales), _submitted_bk(), _BK_DOCNO), ("82", _BK_DOCNO)
        )
        self.assertEqual(len(sales.writes()), 1)
        self.assertEqual(sales.writes()[0]["txtdocno"], _BK_DOCNO)  # 提交的仍是整串单号
        self.assertEqual(sales.detail_reads, ["82"])

    def test_other_prefix_stays_unknown_identity_mismatch(self):
        sales = _Transport({"82": _stored_native(prefix="PD")})
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(_client(sales), _submitted_bk(), _BK_DOCNO)
        self.assertEqual(raised.exception.response_body["readback_stage"], STAGE_IDENTITY_MISMATCH)
        self.assertFalse(raised.exception.response_body["retry_safe"])
        self.assertEqual(len(sales.writes()), 1)

    def test_other_number_stays_unknown_identity_mismatch(self):
        sales = _Transport({"82": _stored_native(number="000002609000008")})
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(_client(sales), _submitted_bk(), _BK_DOCNO)
        self.assertEqual(raised.exception.response_body["readback_stage"], STAGE_IDENTITY_MISMATCH)
        self.assertEqual(len(sales.writes()), 1)

    def test_missing_prefix_cell_stays_unknown_identity_mismatch(self):
        stored = _stored_native()
        stored.pop("txtprefixautonum")
        sales = _Transport({"82": stored})
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(_client(sales), _submitted_bk(), _BK_DOCNO)
        self.assertEqual(raised.exception.response_body["readback_stage"], STAGE_IDENTITY_MISMATCH)

    def test_fuzzy_candidate_is_skipped_and_the_real_booking_is_verified(self):
        # 900 是「同数字、别前缀」的模糊命中;82 才是刚建的那张。
        sales = _Transport(
            {
                "900": _stored_native("900", prefix="PD"),
                "82": _stored_native(),
            }
        )
        self.assertEqual(verify_created_booking(_client(sales), _BK_DOCNO, _submitted_bk()), "82")
        self.assertEqual(sales.detail_reads, ["900", "82"])  # 模糊候选被读过但没被认下
        self.assertEqual(len(sales.writes()), 0)

    def test_submit_finds_the_real_booking_after_a_fuzzy_candidate(self):
        sales = _Transport(
            {
                "900": _stored_native("900", number="000002609000006"),
                "82": _stored_native(),
            }
        )
        self.assertEqual(
            submit_booking(_client(sales), _submitted_bk(), _BK_DOCNO), ("82", _BK_DOCNO)
        )
        self.assertEqual(len(sales.writes()), 1)


class BookingReadbackRetryTests(_NoSleepMixin, unittest.TestCase):
    def test_first_search_empty_then_found_with_only_one_write(self):
        sales = _Transport({"15499": _stored()}, script=[None, ["15499"]])
        stage = {}
        self.assertEqual(
            verify_created_booking(_client(sales), _DOCNO, _BASE, stage_out=stage), "15499"
        )
        self.assertEqual(stage["stage"], "verified")
        self.assertEqual(sales.search_calls, 2)
        self.assertEqual(len(sales.writes()), 0)

    def test_submit_reads_back_after_empty_search_without_second_write(self):
        sales = _Transport({"15499": _stored()}, script=[None, ["15499"]])
        self.assertEqual(submit_booking(_client(sales), _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)
        self.assertEqual(
            [data["sd"] for url, data in sales.posts if url.endswith("showdata.php")],
            [_DOCNO, _DOCNO],
        )

    def test_admin_second_search_finds_order_after_sales_misses(self):
        sales = _Transport()
        admin = _Transport({"15499": _stored()}, script=[None, ["15499"]])
        stage = {}
        self.assertEqual(
            verify_created_booking(_client(sales, admin), _DOCNO, _BASE, stage_out=stage),
            "15499",
        )
        self.assertGreaterEqual(sales.search_calls, 1)
        self.assertEqual(admin.writes(), [])
        self.assertEqual(len(sales.writes()), 0)

    def test_submit_uses_admin_second_search_with_single_write(self):
        sales = _Transport()
        admin = _Transport({"15499": _stored()}, script=[None, ["15499"]])
        self.assertEqual(submit_booking(_client(sales, admin), _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)
        self.assertEqual(admin.writes(), [])

    def test_target_on_search_page_two_is_found(self):
        # 首页整页都是别单(模糊命中),目标只在第 2 页出现 —— 必须按需翻页找到。
        page_one = [f"90{index:03d}" for index in range(30)]
        sales = _Transport(
            {"15499": _stored()},
            script=[{1: page_one, 2: ["15499"]}],
        )
        stage = {}
        self.assertEqual(
            verify_created_booking(_client(sales), _DOCNO, _BASE, stage_out=stage), "15499"
        )
        self.assertEqual(stage["stage"], "verified")
        self.assertEqual(
            [int(data["sdtpage"]) for url, data in sales.posts if url.endswith("showdata.php")],
            [1, 2],
        )

    def test_submit_finds_page_two_target_without_second_write(self):
        page_one = [f"90{index:03d}" for index in range(30)]
        sales = _Transport(
            {"15499": _stored()},
            script=[{1: page_one, 2: ["15499"]}],
        )
        self.assertEqual(submit_booking(_client(sales), _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)

    def test_every_search_empty_stays_unknown_and_not_retry_safe(self):
        sales = _Transport()
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(_client(sales), _BASE, _DOCNO)
        body = raised.exception.response_body
        self.assertEqual(body["readback_stage"], STAGE_SEARCH_EMPTY)
        self.assertFalse(body["retry_safe"])
        self.assertTrue(body["submitted"])
        self.assertEqual(body["readback_attempts"], READBACK_MAX_ATTEMPTS)
        self.assertEqual(len(sales.writes()), 1)
        self.assertEqual(len(self.sleeps), READBACK_MAX_ATTEMPTS - 1)
        self.assertLessEqual(sum(self.sleeps), max_readback_extra_seconds())

    def test_timeout_after_commit_readback_success_has_no_second_write(self):
        sales = _Transport(
            {"15499": _stored()}, script=[None, ["15499"]], write_error=TimeoutError("lost")
        )
        self.assertEqual(submit_booking(_client(sales), _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)

    def test_transport_error_between_searches_does_not_write_again(self):
        sales = _Transport({"15499": _stored()})
        original = sales.post

        def flaky(url, data=None, files=None, timeout_ms=None):
            if url.endswith("form.php") and sales.search_calls <= 1:
                raise TimeoutError("detail read lost")
            return original(url, data, files, timeout_ms)

        sales.post = flaky
        self.assertEqual(submit_booking(_client(sales), _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)

    def test_backoff_is_bounded_and_never_repeats_the_write(self):
        sales = _Transport()
        with self.assertRaises(DMSBookingOutcomeUnknown):
            submit_booking(_client(sales), _BASE, _DOCNO)
        # 三页/三会话都只读:写入永远只有一次。
        self.assertEqual(len(sales.writes()), 1)
        self.assertEqual(sales.search_calls, READBACK_MAX_ATTEMPTS)


class ReadbackFieldClassificationTests(_NoSleepMixin, unittest.TestCase):
    """判据表不许随订车表单静默漂移:每个提交字段必须被显式分层。"""

    def test_every_submitted_booking_field_is_classified(self):
        from services.erp.mrerp_dms_booking_readback import field_spec
        from services.erp.mrerp_dms_client_ops import DMSClientOpsMixin
        from services.erp.mrerp_dms_models import DMSBookingPayload, DMSMasterRef
        from services.line_dms.booking_flow import _card_payload

        card = _card_payload(
            {
                "nonce": "N1",
                "qa": {"answers": {"people_id": "1101700998118"}},
            }
        )
        booking = DMSBookingPayload(
            doc_date_be="12/09/2569",
            advisor=DMSMasterRef(id="89", code="sale01", name="สมชาย", extra=("0812345678",)),
            place_book=DMSMasterRef(id="1", code="1", name="สำนักงานใหญ่"),
            car=DMSMasterRef(
                id="410",
                code="DMX",
                name="D-Max",
                extra=tuple(str(i) for i in range(14)),
            ),
            paint=DMSMasterRef(id="7", code="P7", name="White"),
            branch=DMSMasterRef(id="1", code="1", name="B1"),
            team=DMSMasterRef(id="30", code="30", name="T30"),
            term_sale=DMSMasterRef(id="3", code="3", name="Cash"),
            regis_behalf=DMSMasterRef(id="1", code="1", name="Self"),
            delivery_date_be="19/09/2569",
            organization_fields=(
                ("branch_bookval", "1"),
                ("txtbranch_book", "B1"),
                ("team_bookval", "30"),
                ("txtteam_book", "T30"),
                ("branch_sellval", "1"),
                ("txtbranch_sell", "B1"),
                ("team_sellval", "30"),
                ("txtteam_sell", "T30"),
                ("usersposival2_book", "289"),
                ("txtusersposi2_book", "Manager"),
            ),
            payments=(
                {
                    "channel": "transfer",
                    "amount": "1000",
                    "extra": {
                        "src_account_name": "Somchai",
                        "src_account_no": "1112223334",
                        "src_bank_name": "KBank",
                        "src_bank_id": "3",
                        "src_branch_name": "Rayong",
                        "src_time": "10:00",
                        "dst_business_name": "Company",
                        "dst_account_no": "1234567890",
                        "dst_bank_name": "KBank",
                        "dst_bank_id": "3",
                        "dst_branch_name": "Rayong",
                    },
                },
            ),
        )
        data = {}
        # 走真实 mixin 方法(不 stub 表单构造);transport 只有 get/post 契约,不会被调用。
        DMSClientOpsMixin._apply_booking_form_fields(
            object.__new__(DMSClient), data, customer_id="15024", booking=booking, card=card
        )
        unclassified = sorted(
            field for field in data if field != "idsel" and field_spec(field) is None
        )
        self.assertEqual(
            unclassified,
            [],
            "订车表单新增字段未分层:身份/关键字段必须比对,展示镜像只能记告警"
            f"(见 tests/unit/test_dms_booking_submit_readback.py)· 漏分层:{unclassified}",
        )


if __name__ == "__main__":
    unittest.main()
