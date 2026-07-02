# -*- coding: utf-8 -*-
"""LINE 拍身份证 → 建 DMS 客户(services/agent/dms_push)· 设计红线。

铁三条:① 必填(证号+姓名)读不出绝不出确认——直说缺哪个;② 复述必存检查点
(tool/fields/endpoint_id/mode)且尾4 上卡;③ 执行走网页同一函数 + 写
erp_push_logs(trigger=line_dms),失败人话不裸码。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.agent import dms_push as d
from services.erp.dms_id_ocr import DmsOcrError

_USER = {"id": "u-1", "tenant_id": "t-1"}
_EP = {"id": "e1", "adapter": "mrerp_dms", "name": "DMS TEST"}
_OCR = {
    "needs_review": False,
    "missing_fields": [],
    "id_card": {
        "prefix_name": "นาย",
        "first_name": "สมชาย",
        "last_name": "ใจดี",
        "people_id": "1103700123456",
        "birthday_be": "2530-01-01",
        "address": {},
    },
}


class TestWantsDms(unittest.TestCase):
    def test_only_dms_goal_counts(self):
        self.assertTrue(d.wants_dms({"goals": ["dms"]}))
        self.assertFalse(d.wants_dms({"goals": ["push"]}))
        self.assertFalse(d.wants_dms(None))
        self.assertFalse(d.wants_dms({}))


class TestHandleIdCard(unittest.TestCase):
    def _run(self, *, ocr=None, err=None):
        sent = []
        with (
            patch.object(d.dms_id_ocr, "recognize_id_card") as rec,
            patch("services.line_binding.line_pending_actions.set_action") as sa,
            patch.object(d, "_notify", side_effect=lambda u, t, m, q=None: sent.append(m)),
            patch.object(d, "_note"),
        ):
            if err:
                rec.side_effect = err
            else:
                rec.return_value = (_EP, ocr or _OCR, 900)
            out = d.handle_id_card(_USER, "t-1", "Uabc", "zh", b"img", "id.jpg", "qt")
        return out, sent, sa

    def test_happy_path_stores_checkpoint_and_restates(self):
        out, sent, sa = self._run()
        self.assertTrue(out)
        action = sa.call_args.args[2]
        self.assertEqual(action["tool"], "dms_push")
        self.assertEqual(action["endpoint_id"], "e1")
        self.assertEqual(action["mode"], "create")
        self.assertEqual(action["fields"]["people_id"], "1103700123456")
        self.assertIn("3456", sent[0])  # 复述带证号尾4
        self.assertIn("สมชาย ใจดี", sent[0])

    def test_missing_required_never_creates_checkpoint(self):
        ocr = {**_OCR, "id_card": {**_OCR["id_card"], "people_id": ""}}
        out, sent, sa = self._run(ocr=ocr)
        self.assertTrue(out)
        sa.assert_not_called()
        self.assertIn("证号", sent[0])  # 直说缺哪个字段

    def test_no_endpoint_guides_to_web(self):
        out, sent, sa = self._run(err=DmsOcrError("dms.no_endpoint", 400, "dms.no_endpoint"))
        self.assertTrue(out)
        sa.assert_not_called()
        self.assertIn("集成", sent[0])

    def test_unreadable_asks_for_retake(self):
        out, sent, sa = self._run(
            err=DmsOcrError("ocr.id_card_unreadable", 422, {"code": "ocr.id_card_unreadable"})
        )
        self.assertTrue(out)
        sa.assert_not_called()
        self.assertIn("正面照", sent[0])


class TestExecuteConfirmed(unittest.TestCase):
    _ACTION = {
        "tool": "dms_push",
        "endpoint_id": "e1",
        "mode": "create",
        "fields": {"name": "สมชาย ใจดี", "people_id": "1103700123456"},
    }

    def _run(self, result):
        sent = []
        with (
            patch.object(d.dms_id_ocr, "resolve_dms_endpoint", return_value=_EP),
            patch(
                "services.erp.erp_dms_intake.push_idcard_fields_mrerp_dms", return_value=result
            ) as push,
            patch.object(d.db, "insert_push_log") as log,
            patch.object(d, "_notify", side_effect=lambda u, t, m, q=None: sent.append(m)),
            patch.object(d, "_note"),
        ):
            d.execute_confirmed(_USER, "t-1", "Uabc", "zh", self._ACTION)
        return sent, push, log

    def test_success_pushes_and_logs_line_dms(self):
        sent, push, log = self._run(
            {"success": True, "customer_id": "c9", "response_body": {}, "elapsed_ms": 5}
        )
        self.assertEqual(push.call_args.kwargs["mode"], "create")
        self.assertEqual(log.call_args.args[-1], "line_dms")  # trigger 口径
        self.assertEqual(log.call_args.args[8]["trigger"], "line_dms")
        self.assertTrue(any("✅" in m for m in sent))

    def test_failure_speaks_human_reason(self):
        sent, _push, log = self._run(
            {"success": False, "error_code": "ERR_DMS_X", "error_friendly": "证号已存在"}
        )
        self.assertEqual(log.call_args.args[6], "failed")
        self.assertTrue(any("❌" in m and "证号已存在" in m for m in sent))

    def test_endpoint_gone_is_honest(self):
        sent = []
        with (
            patch.object(d.dms_id_ocr, "resolve_dms_endpoint", return_value=None),
            patch("services.erp.erp_dms_intake.push_idcard_fields_mrerp_dms") as push,
            patch.object(d, "_notify", side_effect=lambda u, t, m, q=None: sent.append(m)),
        ):
            d.execute_confirmed(_USER, "t-1", "Uabc", "zh", self._ACTION)
        push.assert_not_called()
        self.assertTrue(any("集成" in m for m in sent))


if __name__ == "__main__":
    unittest.main()
