"""Recovery must never replay an external write with an unresolved saved attempt."""

import unittest
from unittest import mock

from services.erp import erp_dms_intake
from services.erp.mrerp_dms_client_base import DMSClientError
from services.line_dms import booking_attempt, booking_flow


class AttemptTests(unittest.TestCase):
    def test_retry_arm_uses_consumed_nonce_guard(self):
        with mock.patch.object(
            booking_attempt.session_store, "replace_claimed_booking_payload", return_value=False
        ) as replace:
            self.assertFalse(booking_flow._arm_retry("T", "L", {"nonce": "OLD"}, "NEW"))
        replace.assert_called_once_with(
            "T", "L", "OLD", "booking_review", {"nonce": "NEW"}, ttl_minutes=30
        )

    def test_recorder_keeps_owner_and_advances_only_its_previous_number(self):
        payload = {"nonce": "N", "qa": {"customer": {"id": "C"}}}
        with mock.patch.object(
            booking_attempt.session_store, "record_booking_attempt", return_value=True
        ) as save:
            record = booking_attempt.recorder("T", "L", payload)
            record("PD0001")
            record("PD0002")
        first, second = [call.args for call in save.call_args_list]
        self.assertEqual(first[:4], ("T", "L", "N", "PD0001"))
        self.assertIsNone(first[5])
        self.assertEqual(second[5], "PD0001")
        self.assertEqual(first[4], second[4])

    def test_failed_marker_save_blocks_before_post(self):
        with mock.patch.object(
            booking_attempt.session_store, "record_booking_attempt", return_value=False
        ):
            with self.assertRaises(DMSClientError) as raised:
                booking_attempt.recorder("T", "L", {"nonce": "N"})("PD0001")
        self.assertEqual(raised.exception.error_code, "ERR_DMS_BOOKING_ATTEMPT_BLOCKED")

    def test_same_confirmation_is_blocked_by_saved_unknown_attempt(self):
        session = {"payload": {"booking_attempt": {"nonce": "N", "booking_no": "PD1"}}}
        with mock.patch.object(booking_attempt.store, "get_session", return_value=session):
            result = booking_attempt.pending("T", "L", {"nonce": "N"})
        self.assertEqual(result["booking_no"], "PD1")
        self.assertFalse(booking_flow._retryable_result(result))

    def test_completion_uses_nonce_guarded_clear(self):
        with mock.patch.object(
            booking_attempt.session_store, "clear_booking_attempt", return_value=True
        ) as clear:
            self.assertTrue(booking_attempt.clear_completed("T", "L", {"nonce": "N"}))
        clear.assert_called_once_with("T", "L", "N")

    def test_other_confirmation_does_not_reuse_previous_marker(self):
        session = {"payload": {"booking_attempt": {"nonce": "OLD", "booking_no": "PD1"}}}
        with mock.patch.object(booking_attempt.store, "get_session", return_value=session):
            self.assertIsNone(booking_attempt.pending("T", "L", {"nonce": "NEW"}))

    def test_post_submit_concurrent_login_never_becomes_safe_retry(self):
        adapter = mock.MagicMock()
        adapter.__enter__.return_value = adapter
        adapter.concurrent_login_detected = True
        error = DMSClientError("result unknown", booking_attempt.UNKNOWN)
        error.booking_no = "PD1"
        error.response_body = {"submitted": True, "retry_safe": False}
        with mock.patch.object(
            erp_dms_intake, "_build_mrerp_dms_adapter", return_value=(adapter, None)
        ):
            result = erp_dms_intake._run_logged_in({}, mock.Mock(side_effect=error))
        self.assertEqual(result["error_code"], booking_attempt.UNKNOWN)
        self.assertEqual(result["booking_no"], "PD1")
        self.assertFalse(booking_flow._retryable_result(result))

    def test_verified_booking_preserved_after_concurrent_login_flag(self):
        adapter = mock.MagicMock()
        adapter.__enter__.return_value = adapter
        adapter.concurrent_login_detected = True
        known = {"ok": True, "booking_id": "B1", "booking_no": "PD1"}
        with mock.patch.object(
            erp_dms_intake, "_build_mrerp_dms_adapter", return_value=(adapter, None)
        ):
            self.assertEqual(erp_dms_intake._run_logged_in({}, lambda *args: known), known)


class StalePreflightTests(unittest.IsolatedAsyncioTestCase):
    async def test_replaced_draft_neither_rearms_nor_receives_old_preflight_messages(self):
        for result in ({"preflight": "changed"}, {"preflight": "unmatched", "field": "advisor"}):
            with (
                self.subTest(result=result),
                mock.patch.object(
                    booking_attempt.session_store,
                    "replace_claimed_booking_payload",
                    return_value=False,
                ) as replace,
                mock.patch.object(booking_flow, "_send") as send,
            ):
                await booking_flow._resume_after_master_change(
                    {"tenant_id": "T"}, "L", {"nonce": "OLD", "qa": {}}, result
                )
            self.assertEqual(replace.call_args.args[2], "OLD")
            send.assert_not_called()
