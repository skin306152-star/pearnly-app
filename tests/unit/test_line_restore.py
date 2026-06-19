# -*- coding: utf-8 -*-
"""引用已撤单「恢复」闭环(line_restore · 05 Slice 2)守门。

detect_restore 反例(带金额无引用不算恢复);maybe_restore 各状态诚实分流;correct.restore_doc
控制流(原非 void→not_voided / 幂等→already / 成功克隆+过账)。真库写由真账号 E2E 守。
"""

import unittest
from unittest import mock

from services.expense import line_classify
from services.expense import line_restore as lr
from services.line_binding import line_message_refs as refs
from services.purchase import correct as correct_svc


class _Ctx:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


class DetectRestoreTests(unittest.TestCase):
    def test_bare_restore_words_are_restore(self):
        for w in ("恢复", "还原", "กู้คืน", "ฟื้นฟู", "restore"):
            self.assertTrue(line_classify.detect_restore(w), w)

    def test_restore_word_with_amount_no_quote_is_not_restore(self):
        # 「ฟื้นฟูเครื่อง 500 / 恢复机器花了500」带金额无引用 = 记账,不是恢复(防误伤新支出)。
        self.assertFalse(line_classify.detect_restore("ฟื้นฟูเครื่อง 500"))
        self.assertFalse(line_classify.detect_restore("恢复机器 500"))

    def test_restore_word_with_amount_but_quoted_is_restore(self):
        # 明确引用了卡片 → 即便句里有数字也按恢复(用户在对那张卡操作)。
        self.assertTrue(line_classify.detect_restore("恢复 500", has_quote=True))

    def test_non_restore_text(self):
        self.assertFalse(line_classify.detect_restore("金额改为300", has_quote=True))
        self.assertFalse(line_classify.detect_restore("ยกเลิก"))


class MaybeRestoreTests(unittest.TestCase):
    def _run(self, text, *, quoted="MID", state=None, live=None, restore_res=None, raise_err=None):
        sent, set_active, restore_calls = [], [], []

        def _restore(*a, **k):
            restore_calls.append(k.get("doc_id"))
            if raise_err:
                raise raise_err
            return restore_res

        with (
            mock.patch.object(lr.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(
                refs, "resolve_target", return_value={"doc_id": "DEAD", "ws": 1, "error": None}
            ),
            mock.patch.object(refs, "resolve_card_state", return_value=(state, live)),
            mock.patch.object(correct_svc, "restore_doc", side_effect=_restore),
            mock.patch.object(
                lr.line_correct, "_set_active", side_effect=lambda *a, **k: set_active.append(a)
            ),
            mock.patch.object(
                lr.line_reply,
                "reply_text_context",
                side_effect=lambda tok, body, **k: sent.append(body),
            ),
        ):
            ctx = {"line_user_id": "U1", "tenant_id": "t", "quote_token": "q"}
            res = lr.maybe_restore({"id": "u1"}, "tok", "U1", text, "zh", "t", 1, quoted, ctx)
        return res, (sent[0] if sent else ""), set_active, restore_calls

    def test_not_restore_returns_false(self):
        res, _, _, calls = self._run("金额改为300", state=refs.LIVE)
        self.assertFalse(res)
        self.assertEqual(calls, [])

    def test_bare_restore_needs_quote(self):
        res, body, _, calls = self._run("恢复", quoted=None)
        self.assertTrue(res)
        self.assertIn("长按", body)
        self.assertEqual(calls, [])  # 不定位、不建单

    def test_quoted_live_not_voided(self):
        res, body, set_active, calls = self._run("恢复", state=refs.LIVE, live={"doc": {}})
        self.assertTrue(res)
        self.assertIn("没有被撤销", body)
        self.assertEqual(calls, [])  # ★ 活单不重建
        self.assertEqual(set_active, [])

    def test_quoted_superseded_already(self):
        live = {"doc": {"id": "D9", "grand_total": "50.00"}}
        res, body, _, calls = self._run("恢复", state=refs.SUPERSEDED, live=live)
        self.assertTrue(res)
        self.assertIn("最新版本", body)
        self.assertEqual(calls, [])  # ★ 已有活版本,不重建

    def test_quoted_voided_restores_and_sets_active(self):
        restored = {"restored": {"doc": {"id": "D2", "grand_total": "300.00"}}}
        res, body, set_active, calls = self._run(
            "恢复", state=refs.VOIDED, live=None, restore_res=restored
        )
        self.assertTrue(res)
        self.assertIn("已恢复", body)
        self.assertEqual(calls, ["DEAD"])  # 对引用的死单恢复
        self.assertEqual(set_active[0][2], "D2")  # 续接到新活单

    def test_quoted_voided_already_restored_idempotent(self):
        res, body, set_active, calls = self._run(
            "恢复", state=refs.VOIDED, restore_res={"already": {"id": "D9", "grand_total": "50.00"}}
        )
        self.assertTrue(res)
        self.assertIn("最新版本", body)
        self.assertEqual(set_active, [])  # 幂等:不重建、不重设

    def test_closed_period_honest(self):
        from core.pos_api import PosError

        res, body, _, _ = self._run(
            "恢复", state=refs.VOIDED, raise_err=PosError("acct.period_closed", 409)
        )
        self.assertTrue(res)
        self.assertIn("结账", body)

    def test_discarded_soft_delete_restored(self):
        # Slice 2b:引用软删草稿说「恢复」→ restore_doc 翻回 draft → RESTORE_DONE。
        restored = {"restored": {"doc": {"id": "DEAD", "grand_total": "50.00"}}}
        res, body, set_active, calls = self._run("恢复", state=refs.DISCARDED, restore_res=restored)
        self.assertTrue(res)
        self.assertIn("已恢复", body)
        self.assertEqual(calls, ["DEAD"])
        self.assertEqual(set_active[0][2], "DEAD")  # 续接同一张(翻回的草稿)

    def test_discarded_physically_gone_says_gone(self):
        # 旧物理删(数据没了)→ restore_doc 返 gone → 诚实「数据已不在」。
        res, body, set_active, _ = self._run(
            "恢复", state=refs.DISCARDED, restore_res={"gone": True}
        )
        self.assertTrue(res)
        self.assertIn("不在", body)
        self.assertEqual(set_active, [])  # 不重建、不续接


class _FakeCur:
    """restore_doc 幂等查询用:execute 记 SQL,fetchone 吐预设。"""

    def __init__(self, existing=None):
        self._existing = existing
        self.sql = []

    def execute(self, sql, params=None):
        self.sql.append(sql)

    def fetchone(self):
        return self._existing


class RestoreDocTests(unittest.TestCase):
    def _run(self, *, orig_status, existing=None):
        from services.purchase import docs as docs_svc
        from services.purchase import posting as posting_svc

        cur = _FakeCur(existing=existing)
        orig = {"doc": {"status": orig_status, "id": "O"}} if orig_status else None
        # 恢复后回查:void→新 posted 克隆 / discarded→同一单翻回 draft
        after = {
            "doc": {
                "id": "O" if orig_status == "discarded" else "O_r",
                "status": "draft" if orig_status == "discarded" else "posted",
                "grand_total": "70.00",
            }
        }
        clone = {"doc": {"id": "O_r", "grand_total": "70.00"}}
        get_calls = iter([orig, after])  # 1) 原单状态 2) 恢复后回查
        with (
            mock.patch.object(docs_svc, "get_doc", side_effect=lambda *a, **k: next(get_calls)),
            mock.patch.object(correct_svc, "clone_as_draft", return_value=clone) as cl,
            mock.patch.object(posting_svc, "post_doc", return_value=after) as pd,
        ):
            res = correct_svc.restore_doc(
                cur, tenant_id="t", workspace_client_id=1, doc_id="O", created_by="u"
            )
        return res, cl, pd

    def test_not_deleted_when_original_live(self):
        res, cl, pd = self._run(orig_status="posted")
        self.assertEqual(res, {"not_deleted": True})
        cl.assert_not_called()
        pd.assert_not_called()

    def test_gone_when_missing(self):
        res, cl, pd = self._run(orig_status=None)
        self.assertEqual(res, {"gone": True})
        cl.assert_not_called()

    def test_discarded_flips_to_draft_no_clone(self):
        # 草稿软删 → 原地翻回 draft(不克隆·不过账·数据原样)。
        res, cl, pd = self._run(orig_status="discarded")
        self.assertEqual(res["restored"]["doc"]["status"], "draft")
        cl.assert_not_called()
        pd.assert_not_called()

    def test_idempotent_when_already_restored(self):
        res, cl, pd = self._run(orig_status="void", existing={"id": "O_r", "grand_total": "70"})
        self.assertEqual(res["already"]["id"], "O_r")
        cl.assert_not_called()  # 已有活子单 → 不重建

    def test_void_restores_clone_then_posts(self):
        res, cl, pd = self._run(orig_status="void", existing=None)
        self.assertEqual(res["restored"]["doc"]["status"], "posted")
        # 克隆走 restored_from 审计键(非 corrected_from)
        self.assertEqual(cl.call_args.kwargs.get("audit_key"), "restored_from")
        pd.assert_called_once()


if __name__ == "__main__":
    unittest.main()
