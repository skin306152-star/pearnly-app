# -*- coding: utf-8 -*-
"""DMS 建单恢复路径的纯函数单测(零网络零 DB):并发登录识别 → 可重试判定
→ 重试 Flex 卡 → BOOKING_ACTIONS 契约。

覆盖四件事:
  1. is_concurrent_login_dialog —— DMS 单账号重复登录的泰文弹窗识别。
  2. _retryable_result —— 什么失败结果可以安全重放:并发登录必可重试;
     银行主档未就绪仅在还没建出 booking_id 时可重试(已有 booking_id 重放
     会双建单);普通技术错误不可重试。
  3. booking_retry_card —— 失败后发给销售的重试卡:重试 postback 带 nonce、
     30 分钟提示、取消按钮。
  4. BOOKING_ACTIONS —— booking_flow 只认 confirm/cancel/retry 三个动作的
     契约(flow.py 的接线靠这个集合路由)。
"""

import os
import unittest
from urllib.parse import parse_qs
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-for-line-dms-qa-32bytes-long")

from services.erp.mrerp_dms_adapter import is_concurrent_login_dialog  # noqa: E402
from services.erp import erp_dms_intake  # noqa: E402
from services.line_dms import booking_flow as bf  # noqa: E402
from services.line_dms import cards, qa_cards  # noqa: E402

# DMS 单账号重复登录弹窗的泰文原文(服务端 detect 的标记者,见 mrerp_dms_adapter)。
_CONCURRENT_LOGIN_TH = "มีผู้เข้าใช้งานในระบบซ้ำ"


class ConcurrentLoginDialogTests(unittest.TestCase):
    def test_thai_duplicate_login_message_detected(self):
        msg = f"{_CONCURRENT_LOGIN_TH} กรุณาออกจากระบบ แล้วลองใหม่อีกครั้ง"
        self.assertTrue(is_concurrent_login_dialog(msg))

    def test_bare_marker_detected(self):
        self.assertTrue(is_concurrent_login_dialog(_CONCURRENT_LOGIN_TH))

    def test_normal_text_not_detected(self):
        self.assertFalse(is_concurrent_login_dialog("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"))
        self.assertFalse(is_concurrent_login_dialog("hello from dms"))

    def test_empty_and_none_not_detected(self):
        self.assertFalse(is_concurrent_login_dialog(""))
        self.assertFalse(is_concurrent_login_dialog(None))

    def test_logged_in_runner_maps_dialog_to_specific_error(self):
        class Adapter:
            concurrent_login_detected = True
            last_dialog = _CONCURRENT_LOGIN_TH

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def login(self):
                return None

            def _client(self):
                return object()

            def session_cookies(self):
                return []

        with mock.patch.object(
            erp_dms_intake,
            "_build_mrerp_dms_adapter",
            return_value=(Adapter(), None),
        ):
            result = erp_dms_intake._run_logged_in({"config": {}}, lambda client, adapter: {})

        self.assertEqual(result["error_code"], "ERR_DMS_CONCURRENT_LOGIN")
        self.assertIn(_CONCURRENT_LOGIN_TH, result["raw_error"])


class RetryableResultTests(unittest.TestCase):
    def test_concurrent_login_always_retryable(self):
        self.assertTrue(bf._retryable_result({"error_code": "ERR_DMS_CONCURRENT_LOGIN"}))

    def test_concurrent_login_with_booking_id_not_retryable(self):
        # 已有外部单号时结果可能已写入,重放会双建单,不因错误码而放行。
        self.assertFalse(
            bf._retryable_result(
                {
                    "error_code": "ERR_DMS_CONCURRENT_LOGIN",
                    "booking_id": "BID1",
                }
            )
        )

    def test_bank_master_not_ready_without_booking_id_retryable(self):
        self.assertTrue(
            bf._retryable_result(
                {
                    "ok": False,
                    "error_code": "ERR_DMS_TECHNICAL",
                    "raw_error": "company bank master did not become ready; screenshot=1.png",
                    "response_body": {"raw_error": "company bank master did not become ready"},
                }
            )
        )

    def test_bank_master_not_ready_in_response_body_retryable(self):
        # _err 同时写 raw_error 与 response_body.raw_error;只落在 response_body 也要认。
        self.assertTrue(
            bf._retryable_result(
                {
                    "ok": False,
                    "error_code": "ERR_DMS_TECHNICAL",
                    "raw_error": "",
                    "response_body": {"raw_error": "company bank master did not become ready"},
                }
            )
        )

    def test_bank_master_not_ready_with_booking_id_not_retryable(self):
        # 主档读不到但 booking_id 已产出 → 重放会双建单,绝不重试。
        self.assertFalse(
            bf._retryable_result(
                {
                    "ok": False,
                    "error_code": "ERR_DMS_TECHNICAL",
                    "raw_error": "company bank master did not become ready; screenshot=1.png",
                    "booking_id": "BID1",
                }
            )
        )

    def test_plain_technical_error_not_retryable(self):
        self.assertFalse(
            bf._retryable_result(
                {
                    "ok": False,
                    "error_code": "ERR_DMS_TECHNICAL",
                    "raw_error": "timeout waiting for selector",
                }
            )
        )

    def test_empty_result_not_retryable(self):
        self.assertFalse(bf._retryable_result({}))


class BookingRetryCardTests(unittest.TestCase):
    def _card(self, nonce="abc123"):
        return qa_cards.booking_retry_card("สร้างใบจองรถไม่สำเร็จ", nonce)

    def test_returns_flex_bubble(self):
        card = self._card()
        self.assertEqual(card["type"], "flex")
        self.assertEqual(card["contents"]["type"], "bubble")
        self.assertTrue(card.get("altText"))

    def test_retry_postback_carries_action_and_nonce(self):
        nonce = "nonce-xyz-42"
        footer = self._card(nonce)["contents"]["footer"]["contents"]
        retry_btn = next(
            b for b in footer if b["action"]["data"].startswith("action=retry_booking")
        )
        self.assertEqual(retry_btn["action"]["type"], "postback")
        self.assertEqual(retry_btn["action"]["label"], cards.BTN_RETRY_BOOKING)
        params = parse_qs(retry_btn["action"]["data"])
        self.assertEqual(params["action"], ["retry_booking"])
        self.assertEqual(params["nonce"], [nonce])

    def test_body_shows_failure_message_and_30_minute_hint(self):
        message = "สร้างใบจองรถไม่สำเร็จ"
        body = self._card(message)["contents"]["body"]["contents"]
        texts = [row["text"] for row in body if row.get("type") == "text"]
        self.assertIn(message, texts)
        self.assertTrue(any("ภายใน 30 นาที" in t for t in texts))

    def test_cancel_button_present(self):
        footer = self._card()["contents"]["footer"]["contents"]
        cancel_btn = next(
            b for b in footer if b["action"]["data"].startswith("action=cancel_booking")
        )
        self.assertEqual(cancel_btn["action"]["label"], qa_cards.BTN_DISCARD)
        self.assertEqual(cancel_btn["action"]["type"], "postback")

    def test_fallback_message_when_empty(self):
        card = qa_cards.booking_retry_card("", "n1")
        texts = [
            row["text"] for row in card["contents"]["body"]["contents"] if row.get("type") == "text"
        ]
        self.assertTrue(any("สร้างใบจองไม่สำเร็จ" in t for t in texts))


class BookingActionsContractTests(unittest.TestCase):
    def test_retry_action_is_in_booking_actions(self):
        self.assertIn(cards.ACT_RETRY_BOOKING, bf.BOOKING_ACTIONS)

    def test_booking_actions_are_exactly_the_three_card_actions(self):
        self.assertEqual(
            bf.BOOKING_ACTIONS,
            frozenset(
                {
                    cards.ACT_CONFIRM_BOOKING,
                    cards.ACT_CANCEL_BOOKING,
                    cards.ACT_RETRY_BOOKING,
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()
