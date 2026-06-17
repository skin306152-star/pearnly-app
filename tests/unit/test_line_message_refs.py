# -*- coding: utf-8 -*-
"""LINE 消息↔业务对象映射 + 改/删目标解析(引用底座 · Brain OS P1A)守门。

锁:record 逐条 id 入库;resolve_target 优先级 引用 > 第N笔 > 明确上一笔 > 不明确(不执行)。
真库隔离/RLS 由真账号 E2E 守;这里纯逻辑(FakeCursor + mock)。
"""

import unittest
from unittest import mock

from services.expense import conversation
from services.line_binding import line_message_refs as refs


class _RecCur:
    def __init__(self):
        self.params = []

    def execute(self, sql, params):
        self.params.append(params)


class RecordTests(unittest.TestCase):
    def test_batches_all_ids_in_one_insert(self):
        cur = _RecCur()
        refs.record(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            line_user_id="U",
            message_ids=["m1", "m2"],
            ref_id="D1",
            state="posted",
        )
        self.assertEqual(len(cur.params), 1)  # 单次多行 INSERT(非逐条往返)
        flat = cur.params[0]
        self.assertEqual(flat[0], "m1")  # 第 1 行的 line_message_id
        self.assertEqual(flat[9], "m2")  # 第 2 行的 line_message_id(每行 9 参数)

    def test_skips_empty_ids_or_ref(self):
        cur = _RecCur()
        refs.record(
            cur, tenant_id="t", workspace_client_id=1, line_user_id="U", message_ids=[], ref_id="D1"
        )
        refs.record(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            line_user_id="U",
            message_ids=["m"],
            ref_id="",
        )
        refs.record(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            line_user_id="U",
            message_ids=[None, ""],
            ref_id="D1",
        )
        self.assertEqual(cur.params, [])


class MentionsLastTests(unittest.TestCase):
    def test_detects(self):
        self.assertTrue(refs.mentions_last("撤销上一笔"))
        self.assertTrue(refs.mentions_last("ยกเลิกรายการล่าสุด"))
        self.assertTrue(refs.mentions_last("undo the last one"))

    def test_plain_action_is_not_last(self):
        self.assertFalse(refs.mentions_last("删除"))
        self.assertFalse(refs.mentions_last("ลบ"))
        self.assertFalse(refs.mentions_last("改成100"))


class ResolveTargetTests(unittest.TestCase):
    def _resolve(self, *, quoted=None, text="", pending=None, ref=None, last=None):
        with (
            mock.patch.object(refs, "lookup", return_value=ref),
            mock.patch.object(conversation, "peek_pending", return_value=pending),
            mock.patch.object(refs, "find_last_posted", return_value=last),
        ):
            return refs.resolve_target(
                object(),
                tenant_id="t",
                ws=1,
                line_user_id="U1",
                quoted_message_id=quoted,
                text=text,
            )

    def test_quoted_hits_carries_its_ws(self):
        r = self._resolve(
            quoted="m1",
            ref={"ref_type": "purchase_doc", "ref_id": "D5", "workspace_client_id": 3},
        )
        self.assertEqual((r["doc_id"], r["ws"], r["how"], r["error"]), ("D5", 3, "quoted", None))

    def test_quoted_but_missing_ref(self):
        self.assertEqual(self._resolve(quoted="m1", ref=None)["error"], "ref_not_found")

    def test_ordinal_from_detail_list(self):
        r = self._resolve(text="第2笔改成100", pending={"missing": "detail:A,B,C"})
        self.assertEqual((r["doc_id"], r["how"]), ("B", "ordinal"))

    def test_ordinal_out_of_range(self):
        r = self._resolve(text="第9笔改成100", pending={"missing": "detail:A,B"})
        self.assertEqual(r["error"], "ref_not_found")

    def test_ordinal_without_list(self):
        r = self._resolve(text="第2笔改成100", pending={"missing": "amount"})
        self.assertEqual(r["error"], "ref_not_found")

    def test_explicit_last(self):
        r = self._resolve(text="上一笔改成100", last={"id": "D1"})
        self.assertEqual((r["doc_id"], r["how"]), ("D1", "last"))

    def test_explicit_last_but_none(self):
        self.assertEqual(self._resolve(text="上一笔改成100", last=None)["error"], "none")

    def test_ambiguous_no_clear_object(self):
        # 「改成100」没引用/没序号/没明确上一笔 → 不执行,交调用方提示 reply。
        self.assertEqual(self._resolve(text="改成100")["error"], "ambiguous")

    def test_quoted_beats_everything(self):
        # 既引用又带「第2笔」→ 引用优先(最精确)。
        r = self._resolve(
            quoted="m1",
            text="第2笔改成100",
            ref={"ref_type": "purchase_doc", "ref_id": "Q", "workspace_client_id": 2},
        )
        self.assertEqual((r["doc_id"], r["how"]), ("Q", "quoted"))


if __name__ == "__main__":
    unittest.main()
