# -*- coding: utf-8 -*-
"""处理失败的 webhook 事件不再静默消失:落 failed + 回执请用户重发(老会计 OA 路由 + 回执模块)。

原缺陷:webhook 处理前就把 event_id 落表,handler 抛异常后行仍在表里 → LINE 重投永远
被拦 → 消息永久丢失且不可重投。修法不是机器重放(可能已部分写库,重放=重复入账),
而是让用户重发(新 webhookEventId)。这里守两件事:路由的 claim/ack 接线,以及回执的
reply→push 回落。
"""

import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import line_webhook_routes as w
from services.line_binding import line_webhook_dedup as dd
from services.line_binding import line_webhook_runner as nf


def _post(body: bytes) -> "TestClient":
    app = FastAPI()
    app.include_router(w.router)
    with mock.patch.object(w.line_client, "verify_signature", return_value=True):
        return TestClient(app).post("/api/line/webhook", content=body)


_EVENT = (
    b'{"events":[{"webhookEventId":"E1","type":"message","source":{"userId":"U1"},'
    b'"replyToken":"rt","message":{"type":"text","text":"\\u0e01\\u0e32\\u0e41\\u0e1f 50"}}]}'
)


class RouteClaimAckTests(unittest.TestCase):
    def test_success_marks_done(self):
        with (
            mock.patch.object(dd, "claim", return_value=dd.CLAIM_FRESH),
            mock.patch.object(dd, "mark_done") as done,
            mock.patch.object(dd, "mark_failed") as failed,
            mock.patch.object(w, "_handle_line_event") as handle,
        ):
            resp = _post(_EVENT)
        self.assertEqual(resp.status_code, 200)
        handle.assert_called_once()
        done.assert_called_once_with("E1")
        failed.assert_not_called()

    def test_skip_does_not_run_handler(self):
        with (
            mock.patch.object(dd, "claim", return_value=dd.CLAIM_SKIP),
            mock.patch.object(dd, "mark_done") as done,
            mock.patch.object(w, "_handle_line_event") as handle,
        ):
            resp = _post(_EVENT)
        self.assertEqual(resp.status_code, 200)
        handle.assert_not_called()
        done.assert_not_called()

    def test_reclaimed_stale_event_is_processed(self):
        """崩溃残留补跑:claim 判给了处理权就得真处理,不能当重投丢掉。"""
        with (
            mock.patch.object(dd, "claim", return_value=dd.CLAIM_RECLAIM),
            mock.patch.object(dd, "mark_done"),
            mock.patch.object(w, "_handle_line_event") as handle,
        ):
            _post(_EVENT)
        handle.assert_called_once()

    def test_failure_marks_failed_notifies_and_still_returns_200(self):
        with (
            mock.patch.object(dd, "claim", return_value=dd.CLAIM_FRESH),
            mock.patch.object(dd, "mark_done") as done,
            mock.patch.object(dd, "mark_failed") as failed,
            mock.patch.object(w, "_handle_line_event", side_effect=RuntimeError("boom")),
            mock.patch.object(nf, "notify_failed") as notify,
        ):
            resp = _post(_EVENT)
        # 恒 200:LINE 重投是控制台开关(不归我们控),回非 200 只会让 LINE 判 webhook 挂掉。
        self.assertEqual(resp.status_code, 200)
        done.assert_not_called()  # 失败的事件绝不能被钉成已处理
        self.assertEqual(failed.call_args.args[0], "E1")
        self.assertIn("boom", failed.call_args.args[1])
        self.assertEqual(failed.call_args.args[2]["webhookEventId"], "E1")  # 原始事件留库
        notify.assert_called_once()

    def test_one_bad_event_does_not_stop_the_batch(self):
        body = (
            b'{"events":['
            b'{"webhookEventId":"E1","type":"message","source":{"userId":"U1"}},'
            b'{"webhookEventId":"E2","type":"message","source":{"userId":"U1"}}]}'
        )
        with (
            mock.patch.object(dd, "claim", return_value=dd.CLAIM_FRESH),
            mock.patch.object(dd, "mark_done"),
            mock.patch.object(dd, "mark_failed"),
            mock.patch.object(w, "_handle_line_event", side_effect=[RuntimeError("boom"), None]),
            mock.patch.object(nf, "notify_failed"),
        ):
            resp = _post(body)
        self.assertEqual(resp.status_code, 200)


class NoticeDeliveryTests(unittest.TestCase):
    _EV = {"type": "message", "source": {"userId": "U1", "language": "th"}, "replyToken": "rt"}

    def test_reply_first_and_no_push_when_reply_lands(self):
        with (
            mock.patch.object(nf.line_reply, "reply_text_context", return_value=True) as reply,
            mock.patch.object(nf.line_reply, "push_text_context") as push,
        ):
            nf.notify_failed(self._EV)
        push.assert_not_called()
        self.assertIn("ส่งใหม่", reply.call_args.args[1])  # 泰语「请重发」

    def test_push_fallback_when_reply_token_already_consumed(self):
        """异常常发生在回复之后 → replyToken 已被吃掉/过期,必须回落 push,否则用户什么都收不到。"""
        with (
            mock.patch.object(nf.line_reply, "reply_text_context", return_value=False),
            mock.patch.object(nf.line_reply, "push_text_context") as push,
        ):
            nf.notify_failed(self._EV)
        push.assert_called_once()
        self.assertEqual(push.call_args.args[0], "U1")

    def test_push_fallback_when_reply_raises(self):
        with (
            mock.patch.object(nf.line_reply, "reply_text_context", side_effect=RuntimeError("x")),
            mock.patch.object(nf.line_reply, "push_text_context") as push,
        ):
            nf.notify_failed(self._EV)
        push.assert_called_once()

    def test_unfollow_is_never_answered(self):
        # LINE 明令不可回复 unfollow,且用户已删好友,push 必被拒。
        with (
            mock.patch.object(nf.line_reply, "reply_text_context") as reply,
            mock.patch.object(nf.line_reply, "push_text_context") as push,
        ):
            nf.notify_failed({"type": "unfollow", "source": {"userId": "U1"}})
        reply.assert_not_called()
        push.assert_not_called()

    def test_notice_failure_never_raises_into_route(self):
        # 事件已经在出错路径上,回执再失败也不该掀翻同一批里其余事件。
        with (
            mock.patch.object(nf.line_reply, "reply_text_context", side_effect=RuntimeError("x")),
            mock.patch.object(nf.line_reply, "push_text_context", side_effect=RuntimeError("y")),
        ):
            nf.notify_failed(self._EV)

    def test_dms_channel_uses_own_client_and_copy(self):
        with (
            mock.patch.object(nf.line_client, "reply_text", return_value=True) as reply,
            mock.patch.object(nf.line_reply, "reply_text_context") as default_reply,
        ):
            nf.notify_failed(self._EV, channel="dms", text="ลองใหม่")
        default_reply.assert_not_called()  # 通道隔离:DMS 不走老 OA 出口
        self.assertEqual(reply.call_args.args[1], "ลองใหม่")
        self.assertEqual(reply.call_args.kwargs["channel"], "dms")

    def test_copy_follows_event_language(self):
        for lang, needle in (("en", "send it again"), ("zh", "重新发送"), ("ja", "もう一度")):
            ev = dict(self._EV, source={"userId": "U1", "language": lang})
            with mock.patch.object(nf.line_reply, "reply_text_context", return_value=True) as r:
                nf.notify_failed(ev)
            self.assertIn(needle, r.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
