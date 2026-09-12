import contextlib
import copy
from unittest import IsolatedAsyncioTestCase, TestCase, mock

from services.line_dms import binding_guard, booking_edit, qa_cards

QA = {
    "endpoint_id": "E1",
    "customer": {"id": "C1", "name": "Old Name"},
    "advisor": {"id": "A1", "name": "sale02"},
    "draft": {
        "people_id": "1101700998118",
        "prefix_id": "17",
        "birthday_be": "15/05/2530",
        "phone": "0811111111",
        "house_no": "1",
        "province_id": "P1",
        "district_id": "D1",
        "subdistrict_id": "S1",
        "zipcode_id": "Z1",
    },
    "answers": {
        "place": {"id": "PL1", "name": "Showroom"},
        "car": {"id": "C1", "label": "DMAX"},
        "paint": {"id": "P1", "name": "Red"},
        "delivery_date_be": "22/08/2569",
        "term": {"id": "T1", "name": "Finance"},
        "regis": {"id": "R1", "name": "Person"},
        "regis_name": "Old Name",
    },
    "payments": [{"channel": "cash", "amount": "1000.00", "extra": {}}],
    "files": {"id_card_mid": "MID1", "slip_mid": "MID2"},
}

MASTERS = {
    "place_books": [["PL1", "P", "Showroom"]],
    "cars": [["C1", "DMAX", "X-Series"]],
    "term_sales": [["T1", "T", "Finance"]],
    "regis_behalfs": [["R1", "R", "Person"]],
    "company_banks": [["B1", "SCB", "SCB", "Rayong", "1234567890123"]],
    # 每个银行目录各自独立成项:不许再假设「五类目录都必有行」。
    "source_banks": [["S1", "KBANK", "KBANK"]],
    "cheque_banks": [["S1", "KBANK", "KBANK"]],
    "cashier_banks": [["S1", "KBANK", "KBANK"]],
    "card_banks": [["S1", "KBANK", "KBANK"]],
    "prefixes": [["17", "Mr", "Mr"]],
}

# 生产租户真形态(2026-09-13):收款账户 2 行,来源/支票/本票/银行卡目录都是 0 行。
MASTERS_PRODUCTION = {
    **MASTERS,
    "company_banks": [
        ["B1", "SCB", "SCB", "Rayong", "1234567890123"],
        ["B2", "BBL", "BBL", "Rayong", "9876543210"],
    ],
    "source_banks": [],
    "cheque_banks": [],
    "cashier_banks": [],
    "card_banks": [],
}


def form():
    customer = {
        "people_id": "1101700998118",
        "prefix_id": "17",
        "name": "New Name",
        "birthday_be": "15/05/2530",
        "phone": "0899999999",
        "house_no": "42",
        "building": "Tower",
        "floor": "5",
        "room": "501",
        "village": "Village",
        "moo": "2",
        "soi": "Soi 1",
        "road": "Road",
        "province_id": "P1",
        "province_name": "Bangkok",
        "district_id": "D1",
        "district_name": "District",
        "subdistrict_id": "S1",
        "subdistrict_name": "Subdistrict",
        "zipcode_id": "Z1",
        "zipcode": "10230",
    }
    return {
        "customer": customer,
        "answers": {
            "place_id": "PL1",
            "car_id": "C1",
            "paint_id": "PA1",
            "delivery_date_be": "23/08/2569",
            "term_id": "T1",
            "regis_id": "R1",
            "regis_name": "New Name",
        },
        "payments": [
            {
                "channel": "transfer",
                "amount": "12,000",
                "extra": {
                    "src_bank_id": "S1",
                    "dst_business_name": "Company",
                    "src_bank_name": "KBANK",
                    "src_account_no": "99",
                    "src_account_name": "Customer",
                    "src_branch_name": "Bangkok",
                    "src_time": "15:06",
                    "dst_id": "B1",
                },
            }
        ],
        "keep_files": {"id_card": True, "slip": True},
    }


# 客户四级地址 + 称谓的权威行:save 的标签解析吃本请求快照里的这一份(零额外登录)。
GEO_ROWS = {
    "provinces": [["P1", "Bangkok"]],
    "districts": [["D1", "District"]],
    "subdistricts": [["S1", "Subdistrict"]],
    "zipcodes": [["Z1", "10230"]],
}


def snapshot(masters=None, *, paints=None, geo=None, resolved_customer=None):
    """read_edit_snapshot 的返回形状:一次权威登录取回的主档/颜色/级联。"""
    use = masters or MASTERS
    return {
        "masters": use,
        "paints": {"C1": [["PA1", "RED", "Red"]]} if paints is None else paints,
        "prefixes": list(use.get("prefixes") or []),
        "geo": GEO_ROWS if geo is None else geo,
        "resolved_customer": resolved_customer or {},
    }


class BookingEditTests(TestCase):
    def setUp(self):
        self.user = {"id": "U1", "tenant_id": "T1"}
        self.binding = {"user_id": "U1", "tenant_id": "T1", "line_user_id": "L1"}
        self.payload = {"nonce": "N1", "qa": QA}

    def patches(self, masters=None, *, paints=None, snap=None):
        current = snap if snap is not None else snapshot(masters, paints=paints)
        return (
            mock.patch.object(booking_edit.store, "get_binding_by_user", return_value=self.binding),
            mock.patch.object(
                booking_edit.store,
                "get_session",
                return_value={"state": "booking_review", "payload": self.payload},
            ),
            mock.patch.object(
                booking_edit.dms_id_ocr,
                "resolve_dms_endpoint",
                return_value={"id": "E1"},
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                side_effect=lambda endpoint, **kwargs: copy.deepcopy(current),
            ),
        )

    def test_save_rotates_nonce_and_pushes_revised_preview(self):
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            send = es.enter_context(mock.patch.object(booking_edit, "_send"))
            next_nonce = booking_edit.save(self.user, "N1", form())

        saved = replace.call_args.args[3]
        qa = saved["qa"]
        self.assertNotEqual(next_nonce, "N1")
        self.assertEqual(saved["nonce"], next_nonce)
        self.assertEqual(qa["customer"]["name"], "New Name")
        self.assertEqual(qa["draft"]["zipcode"], "10230")
        self.assertEqual(qa["answers"]["car"]["label"], "DMAX X-Series")
        self.assertEqual(qa["payments"][0]["amount"], "12000.00")
        self.assertEqual(
            qa["payments"][0]["extra"],
            {
                "src_bank_id": "S1",
                "dst_business_name": "Company",
                "src_bank_name": "KBANK",
                "src_account_no": "99",
                "src_account_name": "Customer",
                "src_branch_name": "Bangkok",
                "dst_id": "B1",
                "dst": "SCB · 1234567890123 · Rayong",
                "dst_bank_id": "B1",
                "dst_bank_name": "SCB",
                "dst_branch_name": "Rayong",
                "dst_account_no": "1234567890123",
            },
        )
        self.assertIn("District", qa["summary"]["address"])
        self.assertIn("10230", qa["summary"]["address"])
        self.assertTrue(qa["customer_dirty"])
        self.assertEqual(qa["files"]["slip_mid"], "MID2")
        self.assertTrue(qa["master_snapshot"]["version"])
        self.assertEqual(qa["paint_snapshots"]["C1"]["rows"], [["PA1", "RED", "Red"]])
        self.assertEqual(send.call_args.args[0], "L1")
        self.assertIn(next_nonce, str(send.call_args.args[1]))

    def test_load_reads_one_fresh_snapshot_for_masters_and_car_colours(self):
        """load 一个请求只登录一次:主档 + 本次展示的车型颜色吃同一份新鲜快照。"""
        masters = {**MASTERS, "prefixes": [["17", "Mr"]]}
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                return_value=snapshot(masters, paints={"C1": [["PA1", "RED", "Red"]]}),
            ) as read,
        ):
            out = booking_edit.load(self.user, "N1")

        # 不拿 12h 缓存:唯一一次读取带上了本请求要展示的车型(颜色不再单独登第二次)。
        read.assert_called_once_with(
            {"id": "E1"},
            car_ids=("C1",),
            customer=out["form"]["customer"],
            customer_id="C1",
        )
        self.assertEqual(out["masters"]["prefixes"], [{"id": "17", "label": "Mr"}])
        self.assertEqual(out["masters"]["paints"], [{"id": "PA1", "label": "Red"}])

    def test_load_backfills_blank_title_and_postcode_from_current_dms_customer(self):
        qa = copy.deepcopy(QA)
        qa["draft"].update(prefix_id="", prefix_name="", zipcode_id="", zipcode="")
        payload = {"nonce": "N1", "qa": qa}
        resolved = {
            **booking_edit._form(qa)["customer"],
            "prefix_id": "17",
            "prefix_name": "นาย",
            "zipcode_id": "Z1",
            "zipcode": "10230",
        }
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, payload, {"id": "E1"}),
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                return_value=snapshot(resolved_customer=resolved),
            ),
        ):
            out = booking_edit.load(self.user, "N1")
        self.assertEqual(out["form"]["customer"]["prefix_id"], "17")
        self.assertEqual(out["form"]["customer"]["zipcode_id"], "Z1")
        self.assertEqual(out["form"]["customer"]["zipcode"], "10230")
        self.assertEqual(out["geo"]["zipcodes"], [{"id": "Z1", "label": "10230"}])
        self.assertEqual(
            out["masters"]["company_banks"],
            [
                {
                    "id": "B1",
                    "label": "SCB · 1234567890123 · Rayong",
                    "account_no": "1234567890123",
                    "branch_name": "Rayong",
                }
            ],
        )

    def test_generic_receiving_bank_requires_account_details_in_editor(self):
        from services.line_dms.booking_payments import (
            normalize_editor_payments,
            PaymentValidationError,
        )

        masters = {**MASTERS, "company_banks": [["B1", "SCB", "SCB", "", ""]]}
        payment = form()["payments"][0]
        with self.assertRaises(PaymentValidationError) as ctx:
            normalize_editor_payments([payment], masters)
        self.assertEqual(ctx.exception.code, "dms_booking.payment_detail_required")
        payment["extra"].update(dst_account_no="987654321", dst_branch_name="Rayong")
        clean = normalize_editor_payments([payment], masters)
        self.assertEqual(clean[0]["extra"]["dst_account_no"], "987654321")
        self.assertEqual(clean[0]["extra"]["dst_business_name"], "Company")

    def test_load_marks_manual_banks_only_where_the_directory_is_empty(self):
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                return_value=snapshot(MASTERS_PRODUCTION, paints={"C1": []}),
            ),
        ):
            out = booking_edit.load(self.user, "N1")
        self.assertEqual(
            out["manual_banks"],
            ["source_banks", "cheque_banks", "cashier_banks", "card_banks"],
        )
        self.assertEqual(out["masters"]["source_banks"], [])
        self.assertEqual(len(out["masters"]["company_banks"]), 2)

    def test_load_keeps_directory_selects_when_every_bank_directory_has_rows(self):
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                return_value=snapshot(MASTERS, paints={"C1": []}),
            ),
        ):
            out = booking_edit.load(self.user, "N1")
        # company_banks 永不手工 → 收款账户永远只出现在这里
        self.assertEqual(out["manual_banks"], [])

    def test_save_accepts_manual_source_bank_when_its_directory_is_empty(self):
        submitted = form()
        extra = submitted["payments"][0]["extra"]
        extra.pop("src_bank_id")
        extra["src_bank_name"] = "KBank สาขาระยอง"
        with contextlib.ExitStack() as es:
            for patcher in self.patches(masters=MASTERS_PRODUCTION):
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(mock.patch.object(booking_edit, "_send"))
            booking_edit.save(self.user, "N1", submitted)

        saved = replace.call_args.args[3]["qa"]
        payment = saved["payments"][0]["extra"]
        self.assertEqual(payment["src_bank_name"], "KBank สาขาระยอง")
        self.assertEqual(payment["src_bank_id"], "")
        self.assertEqual(payment["bank_manual"], "1")
        self.assertEqual(payment["dst_id"], "B1")  # 收款账户仍来自实时目录
        self.assertEqual(saved["master_snapshot"]["counts"]["source_banks"], 0)

    def test_save_rejects_a_source_bank_missing_from_a_non_empty_directory(self):
        submitted = form()
        submitted["payments"][0]["extra"]["src_bank_id"] = "S9"  # 目录里已删除的旧选项
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "invalid_bank"):
                booking_edit.save(self.user, "N1", submitted)
        replace.assert_not_called()

    def test_save_accepts_a_unique_exact_bank_name_from_a_non_empty_directory(self):
        submitted = form()
        extra = submitted["payments"][0]["extra"]
        extra.pop("src_bank_id")
        extra["src_bank_name"] = "KBank"
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(mock.patch.object(booking_edit, "_send"))
            booking_edit.save(self.user, "N1", submitted)
        payment = replace.call_args.args[3]["qa"]["payments"][0]["extra"]
        self.assertEqual(payment["src_bank_id"], "S1")
        self.assertEqual(payment["src_bank_name"], "KBANK")
        self.assertNotIn("bank_manual", payment)

    def test_save_accepts_manual_cheque_bank_when_its_directory_is_empty(self):
        submitted = form()
        submitted["payments"] = [
            {
                "channel": "cheque",
                "amount": "500.00",
                "extra": {
                    "cheque_no": "123456",
                    "cheque_book_no": "01",
                    "bank_name": "KBank สาขาระยอง",
                },
            }
        ]
        submitted["keep_files"]["slip"] = False
        with contextlib.ExitStack() as es:
            for patcher in self.patches(masters=MASTERS_PRODUCTION):
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(mock.patch.object(booking_edit, "_send"))
            booking_edit.save(self.user, "N1", submitted)
        self.assertEqual(
            replace.call_args.args[3]["qa"]["payments"][0]["extra"],
            {
                "bank_id": "",
                "bank_name": "KBank สาขาระยอง",
                "cheque_no": "123456",
                "cheque_book_no": "01",
                "bank_manual": "1",
            },
        )

    def test_save_rejects_a_manual_channel_bank_when_the_directory_has_rows(self):
        submitted = form()
        submitted["payments"] = [
            {
                "channel": "cheque",
                "amount": "500.00",
                "extra": {
                    "cheque_no": "123456",
                    "cheque_book_no": "01",
                    "bank_name": "ธนาคารที่ไม่มีในสารบบ",
                },
            }
        ]
        submitted["keep_files"]["slip"] = False
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "invalid_bank"):
                booking_edit.save(self.user, "N1", submitted)
        replace.assert_not_called()

    def test_receiving_account_cannot_be_entered_manually(self):
        from services.line_dms.booking_payments import (
            normalize_editor_payments,
            PaymentValidationError,
        )

        masters = {**MASTERS_PRODUCTION, "company_banks": []}
        payment = form()["payments"][0]
        payment["extra"]["dst_id"] = ""
        payment["extra"]["dst_bank_name"] = "SCB"
        with self.assertRaises(PaymentValidationError) as ctx:
            normalize_editor_payments([payment], masters)
        self.assertEqual(ctx.exception.code, "dms_booking.invalid_bank")

    def test_load_blocks_when_live_master_bundle_is_incomplete(self):
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                return_value=snapshot({"cars": MASTERS["cars"]}, paints={}),
            ),
        ):
            with self.assertRaisesRegex(
                booking_edit.BookingEditError, "dms_booking.master_unavailable"
            ) as ctx:
                booking_edit.load(self.user, "N1")
        self.assertEqual(ctx.exception.status, 503)

    def test_load_fails_closed_when_the_snapshot_cannot_be_read(self):
        """读取失败(登录/抓取)不留旧缓存兜底:如实 503,不拿 12h 快照冒充实时。"""
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(booking_edit, "read_edit_snapshot", return_value=None),
        ):
            with self.assertRaisesRegex(
                booking_edit.BookingEditError, "dms_booking.master_unavailable"
            ) as ctx:
                booking_edit.load(self.user, "N1")
        self.assertEqual(ctx.exception.status, 503)

    def test_payment_only_edit_does_not_mark_customer_for_master_overwrite(self):
        submitted = form()
        submitted["customer"] = booking_edit._form(QA)["customer"]
        submitted["customer"].update(
            {
                "province_name": "Bangkok",
                "district_name": "District",
                "subdistrict_name": "Subdistrict",
                "zipcode": "10230",
            }
        )
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(mock.patch.object(booking_edit, "_send"))
            booking_edit.save(self.user, "N1", submitted)
        self.assertFalse(replace.call_args.args[3]["qa"]["customer_dirty"])

    def test_duplicate_payment_channel_is_rejected(self):
        submitted = form()
        submitted["payments"].append(
            {
                "channel": "transfer",
                "amount": "1",
                "extra": {
                    "src_bank_name": "SCB",
                    "src_account_no": "1",
                    "dst_id": "B1",
                },
            }
        )
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            with self.assertRaisesRegex(booking_edit.BookingEditError, "duplicate_payment"):
                booking_edit.save(self.user, "N1", submitted)

    def test_paints_reads_one_fresh_snapshot_for_the_asked_car(self):
        """颜色下拉同 load:按当前 DMS 主档映射,不吃 12h 快照,一个请求只登录一次。"""
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                return_value=snapshot(MASTERS, paints={"C1": [["PA1", "RED", "Red"]]}),
            ) as read,
        ):
            out = booking_edit.paints(self.user, "N1", "C1")
        read.assert_called_once_with({"id": "E1"}, car_ids=("C1",), customer=None)
        self.assertEqual(out, [{"id": "PA1", "label": "Red"}])

    def test_unread_car_colours_fail_closed_instead_of_looking_empty(self):
        """快照里该车型是 None(这次没读到)≠ 空表(权威结论「没颜色」)→ 503,不冒充空目录。"""
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                return_value=snapshot(MASTERS, paints={"C1": None}),
            ),
        ):
            with self.assertRaisesRegex(
                booking_edit.BookingEditError, "dms_booking.master_unavailable"
            ) as ctx:
                booking_edit.paints(self.user, "N1", "C1")
        self.assertEqual(ctx.exception.status, 503)

    def test_save_reads_one_snapshot_for_masters_colours_and_customer_labels(self):
        """save 一次登录一份快照:主档/银行/选中车型颜色/客户四级地址标签全吃它,不再各登一次。"""
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            read = es.enter_context(
                mock.patch.object(
                    booking_edit,
                    "read_edit_snapshot",
                    side_effect=lambda endpoint, **kwargs: snapshot(),
                )
            )
            es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(mock.patch.object(booking_edit, "_send"))
            booking_edit.save(self.user, "N1", form())
        self.assertEqual(read.call_count, 1)
        args, kwargs = read.call_args
        self.assertEqual(args, ({"id": "E1"},))
        self.assertEqual(kwargs["car_ids"], ("C1",))
        # 客户四级地址标签的解析也吃同一份快照(不再为此单独登录、也不吃 12h 缓存)。
        self.assertEqual(kwargs["customer"]["province_id"], "P1")
        self.assertEqual(kwargs["customer"]["district_id"], "D1")

    def test_save_rejects_when_a_customer_label_is_missing_from_the_snapshot(self):
        """快照里查不到客户的府/区/街道/邮编 id → invalid_master,不写回预览。"""
        broken = form()
        broken["customer"]["province_id"] = "GONE"
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "invalid_master"):
                booking_edit.save(self.user, "N1", broken)
        replace.assert_not_called()

    def test_invalid_master_does_not_replace_review(self):
        broken = form()
        broken["answers"]["car_id"] = "NOT-A-CAR"
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "invalid_master"):
                booking_edit.save(self.user, "N1", broken)
        replace.assert_not_called()

    def test_transfer_cannot_remove_required_slip(self):
        submitted = form()
        submitted["keep_files"]["slip"] = False
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "slip_required"):
                booking_edit.save(self.user, "N1", submitted)
        replace.assert_not_called()

    def test_cash_cannot_keep_transfer_slip(self):
        submitted = form()
        submitted["payments"] = [{"channel": "cash", "amount": "12000", "extra": {}}]
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "slip_without_transfer"):
                booking_edit.save(self.user, "N1", submitted)
        replace.assert_not_called()

    def test_push_failure_restores_previous_nonce(self):
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(
                mock.patch.object(booking_edit, "_send", side_effect=RuntimeError("down"))
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "preview_send_failed"):
                booking_edit.save(self.user, "N1", form())
        self.assertEqual(replace.call_count, 2)
        self.assertEqual(replace.call_args.args[2], replace.call_args_list[0].args[3]["nonce"])
        self.assertEqual(replace.call_args.args[3]["nonce"], "N1")

    def test_preview_has_customer_contact_and_edit_deep_link(self):
        qa = {**QA, "draft": {**QA["draft"], "zipcode": "10230"}}
        with mock.patch.dict("os.environ", {"LINE_DMS_LIFF_ID": "DMS-LIFF"}):
            card = qa_cards.preview_card(qa, "N-EDIT")
        raw = str(card)
        self.assertIn("0811111111", raw)
        self.assertIn("10230", raw)
        self.assertIn("https://liff.line.me/DMS-LIFF?draft=N-EDIT", raw)

    def test_preview_legacy_qa_without_summary_falls_back_to_draft_address(self):
        """legacy qa 无 summary:预览卡从 draft 拼地址(府/区/街道/邮编),不丢可读性。"""
        qa = {
            **QA,
            "draft": {
                **QA["draft"],
                "province_name": "Bangkok",
                "district_name": "District",
                "subdistrict_name": "Subdistrict",
                "zipcode": "10230",
            },
        }
        card = qa_cards.preview_card(qa, "N-LEGACY")
        raw = str(card)
        self.assertIn("Subdistrict", raw)
        self.assertIn("District", raw)
        self.assertIn("Bangkok", raw)
        self.assertIn("10230", raw)
        self.assertIn("รหัสไปรษณีย์", raw)


class PreviewDispatchTests(TestCase):
    """save 必须拿到 LINE 成功回执；失败恢复旧 payload/nonce。"""

    def setUp(self):
        self.user = {"id": "U1", "tenant_id": "T1"}
        self.binding = {"id": "b1", "user_id": "U1", "tenant_id": "T1", "line_user_id": "L1"}
        self.payload = {"nonce": "N1", "qa": QA}
        self.patches = (
            mock.patch.object(booking_edit.store, "get_binding_by_user", return_value=self.binding),
            mock.patch.object(
                booking_edit.store,
                "get_session",
                return_value={"state": "booking_review", "payload": self.payload},
            ),
            mock.patch.object(
                booking_edit.dms_id_ocr, "resolve_dms_endpoint", return_value={"id": "E1"}
            ),
            mock.patch.object(
                booking_edit,
                "read_edit_snapshot",
                side_effect=lambda endpoint, **kwargs: snapshot(),
            ),
        )

    def test_production_save_waits_for_line_delivery_receipt(self):
        with contextlib.ExitStack() as es:
            for patcher in self.patches:
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            send = es.enter_context(mock.patch.object(booking_edit, "_send"))
            nonce = booking_edit.save(self.user, "N1", form())

        self.assertNotEqual(nonce, "N1")
        send.assert_called_once()
        self.assertEqual(send.call_args.args[0], "L1")
        self.assertIn(nonce, str(send.call_args.args[1]))
        saved = replace.call_args.args[3]
        self.assertEqual(saved["nonce"], nonce)

    def test_line_delivery_failure_restores_previous_payload_and_nonce(self):
        with contextlib.ExitStack() as es:
            for patcher in self.patches:
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(mock.patch.object(booking_edit, "_send", return_value=False))
            with self.assertRaisesRegex(booking_edit.BookingEditError, "preview_send_failed"):
                booking_edit.save(self.user, "N1", form())

        self.assertEqual(replace.call_count, 2)
        # 第二次 replace 把旧 payload/nonce 原样放回去(用户还能用同一个 nonce 重试)。
        self.assertEqual(replace.call_args.args[2], replace.call_args_list[0].args[3]["nonce"])
        self.assertEqual(replace.call_args.args[3]["nonce"], "N1")


class PreviewTaskHandlerTests(IsolatedAsyncioTestCase):
    """dms.booking_preview 任务:重新核对当前 booking_review 的 nonce,旧任务不发旧卡。"""

    BINDING = {"id": "b1", "user_id": "U1", "tenant_id": "T1", "line_user_id": "L1"}

    def _session(self, nonce: str) -> dict:
        return {"state": "booking_review", "payload": {"nonce": nonce, "qa": QA}}

    async def test_sends_only_the_current_booking_review_nonce(self):
        sess = self._session("N2")
        with (
            mock.patch.object(booking_edit.binding_guard, "current", return_value=True),
            mock.patch.object(booking_edit.store, "get_session", return_value=sess),
            mock.patch.object(booking_edit.store, "verify_nonce") as verify,
            mock.patch.object(booking_edit, "_send") as send,
        ):
            verify.return_value = True
            await booking_edit._send_review_preview(self.BINDING, "L1", "N2")
        verify.assert_called_once_with(sess, "N2", "booking_review")
        send.assert_called_once()
        self.assertEqual(send.call_args.args[0], "L1")
        self.assertIn("N2", str(send.call_args.args[1]))

    async def test_stale_nonce_is_dropped_without_sending(self):
        sess = self._session("N2")
        with (
            mock.patch.object(booking_edit.binding_guard, "current", return_value=True),
            mock.patch.object(booking_edit.store, "get_session", return_value=sess),
            mock.patch.object(booking_edit.store, "verify_nonce", return_value=False),
            mock.patch.object(booking_edit, "_send") as send,
        ):
            await booking_edit._send_review_preview(self.BINDING, "L1", "N1")
        send.assert_not_called()


class EditLinkChannelTests(TestCase):
    """编辑入口带绑定所属 OA；同 Provider 的 DMS OA 共用登录 LIFF。"""

    _BINDING = {
        "id": "b1",
        "line_user_id": "L1",
        "tenant_id": "t1",
        "user_id": "u1",
        "channel_key": "dms_a",
    }

    def test_legacy_channel_uses_legacy_liff(self):
        with mock.patch.dict("os.environ", {"LINE_DMS_LIFF_ID": "DMS-LIFF"}, clear=False):
            self.assertEqual(
                qa_cards._edit_url("N1", "dms"),
                "https://liff.line.me/DMS-LIFF?draft=N1&channel=dms",
            )

    def test_non_legacy_channel_uses_its_own_liff(self):
        with mock.patch.dict("os.environ", {"LINE_DMS_A_LIFF_ID": "A-LIFF"}, clear=False):
            self.assertEqual(
                qa_cards._edit_url("N1", "dms_a"),
                "https://liff.line.me/A-LIFF?draft=N1&channel=dms_a",
            )

    def test_non_legacy_without_override_uses_provider_liff(self):
        with mock.patch.dict(
            "os.environ", {"LINE_DMS_LIFF_ID": "DMS-LIFF", "LINE_LIFF_ID": "SHARED"}, clear=True
        ):
            self.assertEqual(
                qa_cards._edit_url("N1", "dms_b"),
                "https://liff.line.me/SHARED?draft=N1&channel=dms_b",
            )

    def test_binding_scope_selects_channel(self):
        with mock.patch.dict("os.environ", {"LINE_DMS_A_LIFF_ID": "A-LIFF"}, clear=True):
            with binding_guard.scope(self._BINDING):
                self.assertEqual(
                    qa_cards._edit_url("N1"),
                    "https://liff.line.me/A-LIFF?draft=N1&channel=dms_a",
                )

    def test_preview_keeps_edit_button_on_provider_liff(self):
        with mock.patch.dict("os.environ", {"LINE_LIFF_ID": "SHARED"}, clear=True):
            with binding_guard.scope({**self._BINDING, "channel_key": "dms_b"}):
                card = qa_cards.preview_card(QA, "N-NO-LIFF")
        self.assertIn(qa_cards.BTN_EDIT, str(card))
