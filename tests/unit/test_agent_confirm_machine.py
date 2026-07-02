# -*- coding: utf-8 -*-
"""M3 确认握手 resume 闸(services/agent/confirm_machine)· 设计 §2/§5 红线。

铁三条:① 词表全等匹配不猜("不确认"/"确认一下再说"/长句一律 None);
② 无语境卡(15 分钟窗)绝不执行——"确认"两字交正常轮;③ 任何故障 fail-open 回 False。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.agent import confirm_machine as m

_USER = {"id": "u-1", "tenant_id": "t-1"}


def _cm(cur):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cur)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class TestClassify(unittest.TestCase):
    def test_yes_words(self):
        for w in ("确认", "ยืนยัน", "confirm", "確認", "ยืนยันเลย", "确认推送"):
            self.assertEqual(m.classify(w), "yes", w)

    def test_no_words(self):
        for w in ("取消", "ยกเลิก", "cancel", "キャンセル", "不推"):
            self.assertEqual(m.classify(w), "no", w)

    def test_trailing_politeness_stripped(self):
        self.assertEqual(m.classify("ยืนยันค่ะ"), "yes")
        self.assertEqual(m.classify("确认!"), "yes")
        self.assertEqual(m.classify("ยกเลิกนะครับ"), "no")

    def test_ambiguous_never_guessed(self):
        # 陷阱词:含确认字样但语义存疑 / 万能应答词 / 长句 → 一律 None(走正常轮)。
        for w in (
            "不确认",
            "确认一下再说",
            "好",
            "ok",
            "ใช่",
            "确认吗?",
            "帮我确认下这张对不对",
            "",
        ):
            self.assertIsNone(m.classify(w), w)


class TestResume(unittest.TestCase):
    def _run(self, text, *, flag=True, token="tok1"):
        cur = MagicMock()
        with (
            patch("core.feature_flags.agent_confirm_enabled_for", return_value=flag),
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
            patch(
                "services.line_binding.line_action_nonce.latest_pending", return_value=token
            ) as lp,
            patch("services.agent.push_confirm.handle_postback") as hp,
        ):
            out = m.try_resume(_USER, "rtok", text, "zh", tenant_id="t-1", line_user_id="Uabc")
        return out, lp, hp

    def test_yes_consumes_same_nonce_as_button(self):
        out, _lp, hp = self._run("确认")
        self.assertTrue(out)
        hp.assert_called_once()
        self.assertEqual(hp.call_args.args[2], "agent_push_ok")
        self.assertEqual(hp.call_args.args[3], "tok1")
        self.assertEqual(hp.call_args.args[0].get("line_user_id"), "Uabc")

    def test_no_cancels(self):
        out, _lp, hp = self._run("取消")
        self.assertTrue(out)
        self.assertEqual(hp.call_args.args[2], "agent_push_no")

    def test_no_pending_card_falls_to_normal_turn(self):
        out, _lp, hp = self._run("确认", token=None)
        self.assertFalse(out)
        hp.assert_not_called()

    def test_flag_off_never_touches_store(self):
        cur = MagicMock()
        with (
            patch("core.feature_flags.agent_confirm_enabled_for", return_value=False),
            patch("core.db.get_cursor_rls", return_value=_cm(cur)) as g,
        ):
            self.assertFalse(
                m.try_resume(_USER, "r", "确认", "zh", tenant_id="t-1", line_user_id="U")
            )
        g.assert_not_called()

    def test_non_confirm_text_short_circuits_before_db(self):
        # 普通聊天不摸库:resume 闸挡在所有文本最前,热路开销必须为零。
        with (
            patch("core.feature_flags.agent_confirm_enabled_for", return_value=True),
            patch("core.db.get_cursor_rls") as g,
        ):
            self.assertFalse(
                m.try_resume(_USER, "r", "今天吃什么", "zh", tenant_id="t-1", line_user_id="U")
            )
        g.assert_not_called()

    def test_any_crash_fails_open(self):
        with (
            patch("core.feature_flags.agent_confirm_enabled_for", return_value=True),
            patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")),
        ):
            self.assertFalse(
                m.try_resume(_USER, "r", "确认", "zh", tenant_id="t-1", line_user_id="U")
            )


class TestNonceQueryContract(unittest.TestCase):
    def test_latest_pending_sql_shape(self):
        from services.line_binding import line_action_nonce as nonce

        cur = MagicMock()
        cur.fetchone.return_value = {"token": "t9"}
        out = nonce.latest_pending(
            cur, tenant_id="t-1", user_id="u-1", kind="agent_push", within_minutes=15
        )
        self.assertEqual(out, "t9")
        sql = cur.execute.call_args.args[0]
        self.assertIn("consumed_at IS NULL", sql)
        self.assertIn("expires_at > now()", sql)
        self.assertIn("make_interval", sql)  # 会话语境窗,非 72h 防重放窗
        self.assertIn('"kind": "agent_push"', cur.execute.call_args.args[1][-1])


if __name__ == "__main__":
    unittest.main()
