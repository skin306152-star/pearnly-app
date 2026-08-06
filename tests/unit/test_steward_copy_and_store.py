# -*- coding: utf-8 -*-
"""管家文案层 + 任务视图(services/steward/copy.py · store.py · B2-M1)。

锁三件:①答复里的每个数字都来自工具返回的 data(模板不算账,给什么显什么——喂 0 就说 0,
不许"贴心地"补一个);②状态/步骤机器词与前端 static/ai/ai-i18n-steward.js 的 stw_status_* /
stw_step_* 键一一对应(跨文件引用必须配闸:前端渲染时按机器词拼 key,后端多吐一个词就落空);
③深链只指 static/ai/ai-router.js 真认识的路由(编一个不存在的 hash = 用户点了什么都不发生)。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from services.steward import (
    copy,
    copy_artifacts,
    copy_brief,
    copy_calc,
    copy_close,
    copy_erp_push,
    copy_file,
    copy_lang,
    copy_loop,
    copy_period,
    registry,
    store,
)
from services.workorder import engine

_ROOT = Path(__file__).resolve().parents[2]
_I18N = _ROOT / "static" / "ai" / "ai-i18n-steward.js"
_ROUTER = _ROOT / "static" / "ai" / "ai-router.js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class NumbersComeFromToolsTests(unittest.TestCase):
    def test_matrix_reply_prints_exactly_what_tool_returned(self):
        data = {
            "period": "2569-06",
            "client_count": 12,
            "missing_order": 3,
            "badges": {"missing_materials": 5, "pending_review": 2, "in_progress": 1},
        }
        line = copy.reply(registry.MATRIX_OVERVIEW, data, "zh")
        for value in ("2569-06", "12", "5", "2", "1", "3"):
            self.assertIn(value, line)

    def test_zero_stays_zero(self):
        """空数据不许被润色成"一切正常"——四态诚实,0 就是 0。"""
        line = copy.reply(registry.MATRIX_OVERVIEW, {"period": "2569-06"}, "zh")
        self.assertIn("0", line)

    def test_workorder_reply_states_the_filter_it_used(self):
        """答复要自证口径:只说「0 张工单」时,同屏矩阵写「待审 2」就无从判断谁错。"""
        data = {"period": "2569-07", "status_filter": "pending_review", "total": 2, "counts": {}}
        line = copy.reply(registry.WORKORDER_LIST, data, "zh")
        self.assertIn("2569-07", line)
        self.assertIn("待审", line)
        self.assertIn("2", line)
        self.assertIn("รอตรวจ", copy.reply(registry.WORKORDER_LIST, data, "th"))

    def test_workorder_reply_without_filter_says_nothing_extra(self):
        data = {"period": "2569-07", "status_filter": None, "total": 5, "counts": {}}
        self.assertEqual(copy.reply(registry.WORKORDER_LIST, data, "zh"), "2569-07:5 张工单。")

    def test_unknown_filter_group_is_not_dressed_up(self):
        self.assertEqual(copy.status_filter("some_future_group", "zh"), " · some_future_group")

    def test_every_status_group_has_copy_in_both_languages(self):
        """反证:engine 加一个语义组而这里忘了配人话,答复会把机器词吐给会计。"""
        for group, _statuses in engine.STATUS_GROUPS:
            for lang in ("zh", "th"):
                self.assertNotIn(group, copy.status_filter(group, lang), f"{group}/{lang}")

    def test_client_status_reply_uses_returned_status_and_counts(self):
        data = {
            "client_name": "Sister Makeup",
            "period": "2569-06",
            "has_order": True,
            "status": "collecting",
            "current_step": "intake",
            "material_count": 4,
            "needs": [{"kind": "a"}, {"kind": "b"}],
        }
        line = copy.reply(registry.CLIENT_STATUS, data, "zh")
        self.assertIn("Sister Makeup", line)
        self.assertIn("收料中", line)
        self.assertIn("4", line)
        self.assertIn("2", line)

    def test_no_order_is_said_plainly(self):
        line = copy.reply(
            registry.CLIENT_STATUS,
            {"client_name": "A", "period": "2569-06", "has_order": False},
            "zh",
        )
        self.assertIn("还没开工单", line)

    def test_unknown_future_order_status_is_not_dressed_up(self):
        self.assertEqual(copy.order_status("some_future_status", "zh"), "some_future_status")

    def test_every_tool_has_a_reply_template(self):
        for name in registry.ALL_NAMES:
            self.assertTrue(copy.tool_title(name, "zh"))
            self.assertTrue(copy.tool_title(name, "th"))


class LanguageTests(unittest.TestCase):
    def test_thai_text_answers_in_thai(self):
        self.assertEqual(copy.pick_lang("งวดนี้ใครส่งเอกสารไม่ครบ"), "th")

    def test_chinese_default(self):
        self.assertEqual(copy.pick_lang("本期谁缺料"), "zh")

    def test_explicit_hint_wins(self):
        self.assertEqual(copy.pick_lang("本期谁缺料", "th"), "th")
        self.assertEqual(copy.pick_lang("x", "fr"), "zh")  # 白名单外回落

    def test_missing_thai_falls_back_to_default_not_to_the_key(self):
        """回落只往 DEFAULT_LANG 走,取不到就给空串。

        九个 copy_* 模块共用 copy_lang.t —— 这条锁的是「泰文没写全时会计看到的是中文,
        不是一串 stw_xxx」。任何一处改回落口径,这里先红。
        """
        self.assertEqual(copy_lang.t({"zh": "缺料"}, "th"), "缺料")
        self.assertEqual(copy_lang.t({}, "th"), "")

    def test_every_copy_module_shares_one_language_base(self):
        """反证:这条闸报绿得是因为真收成了一份,而不是各模块又各写了一个同名函数。"""
        mods = (
            copy,
            copy_artifacts,
            copy_brief,
            copy_calc,
            copy_close,
            copy_erp_push,
            copy_file,
            copy_loop,
            copy_period,
        )
        for mod in mods:
            self.assertIs(mod._t, copy_lang.t, mod.__name__)


class ErrorCopyTests(unittest.TestCase):
    def test_ambiguous_client_lists_candidates(self):
        line = copy.error(
            "steward.client_ambiguous",
            {"keyword": "siam", "candidates": [{"name": "Siam A"}, {"name": "Siam B"}]},
            "zh",
        )
        self.assertIn("Siam A", line)
        self.assertIn("2", line)

    def test_unknown_error_code_still_says_something_useful(self):
        line = copy.error("steward.weird", None, "zh")
        self.assertIn("steward.weird", line)


class DeepLinkTests(unittest.TestCase):
    """深链落点必须是 ai-router.js 真认识的路由(memory:35 条深链全落空的教训)。"""

    def test_matrix_link_is_the_dashboard_route(self):
        arts = copy.artifacts(registry.MATRIX_OVERVIEW, {"attention": []}, "zh")
        self.assertEqual([a["href"] for a in arts], ["/ai#/"])
        self.assertIn("buildDashboardHash", _read(_ROUTER))

    def test_client_link_matches_router_client_view_shape(self):
        arts = copy.artifacts(registry.CLIENT_STATUS, {"client_id": 7, "period": "2569-06"}, "zh")
        href = arts[0]["href"]
        self.assertEqual(href, "/ai#/client/7/wo?period=2569-06")
        # ai-router.js 的 VIEWS 必须真含 'wo',否则 parseHash 会把它落回默认视图
        views = re.search(r"var VIEWS = \[(.*?)\]", _read(_ROUTER)).group(1)
        self.assertIn("'wo'", views)

    def test_table_artifacts_carry_columns_and_rows(self):
        arts = copy.artifacts(
            registry.CLIENT_LOOKUP, {"clients": [{"id": 1, "name": "A", "tax_id": "0105"}]}, "zh"
        )
        self.assertEqual(arts[0]["kind"], "table")
        self.assertEqual([c["key"] for c in arts[0]["columns"]], ["name", "tax_id"])
        self.assertEqual(arts[0]["rows"], [{"name": "A", "tax_id": "0105"}])

    def test_no_artifacts_when_nothing_found(self):
        self.assertEqual(copy.artifacts(registry.HISTORY_QUERY, {"rows": []}, "zh"), [])


class StateVocabularyTests(unittest.TestCase):
    """后端吐的 status/step 机器词,前端每一个都得有对应词条 —— 反证:多吐一个就红。"""

    def _i18n_keys(self) -> set:
        return set(re.findall(r"^\s{4}(\w+):", _read(_I18N), flags=re.M))

    def test_task_statuses_have_frontend_keys(self):
        keys = self._i18n_keys()
        for status in (
            store.TASK_RUNNING,
            store.TASK_DONE,
            store.TASK_FAILED,
            store.TASK_WAITING_USER,
        ):
            self.assertIn(f"stw_status_{status}", keys)

    def test_step_states_have_frontend_keys(self):
        keys = self._i18n_keys()
        for state in (
            store.STEP_DONE,
            store.STEP_RUNNING,
            store.STEP_QUEUED,
            store.STEP_WAITING_AUTH,
            store.STEP_FAILED,
        ):
            self.assertIn(f"stw_step_{state}", keys)

    def test_guard_catches_a_vocabulary_that_frontend_never_heard_of(self):
        """反证:闸不是摆设 —— 一个前端没有词条的态,断言必须失败。"""
        self.assertNotIn("stw_status_almost_done", self._i18n_keys())


class PublicViewTests(unittest.TestCase):
    def test_public_task_shape_matches_left_pane_contract(self):
        from datetime import datetime, timezone

        row = {
            "id": "task-1",
            "title": "查本期矩阵",
            "status": store.TASK_DONE,
            "created_at": datetime(2026, 7, 26, 3, 0, tzinfo=timezone.utc),
            "finished_at": None,
            "steps": [{"id": "understand", "state": "done"}],
            "artifacts": [],
        }
        out = store.public_task(row)
        self.assertEqual(out["task_id"], "task-1")
        self.assertEqual(out["status"], "done")
        self.assertEqual(out["agent_count"], 1)  # M1 一轮一个工具,诚实报 1
        self.assertTrue(out["started_at"].startswith("2026-07-26"))
        self.assertEqual(out["steps"][0]["id"], "understand")

    def test_public_message_hides_tool_trace(self):
        from datetime import datetime, timezone

        row = {
            "id": "m1",
            "role": store.ROLE_STEWARD,
            "text": "好的",
            "tool_trace": [{"tool": "matrix_overview", "ok": True}],
            "task_id": "task-1",
            "created_at": datetime(2026, 7, 26, tzinfo=timezone.utc),
        }
        out = store.public_message(row)
        self.assertNotIn("tool_trace", out)
        self.assertEqual(out["task_id"], "task-1")
        self.assertEqual(out["role"], "steward")


class _StubMessageCur:
    """message_text 的假游标:只认自己那一条 SQL,不解析真实 SQL 文本(同 FakeCur 先例,
    但按 message_id 分流返回值,而不是恒定返回一个预置行)。"""

    def __init__(self, rows: dict):
        self._rows = rows
        self.executed = False

    def execute(self, sql, params):
        self.executed = True
        self._last_id = params[-1]

    def fetchone(self):
        row = self._rows.get(self._last_id)
        return {"text": row} if row is not None else None


class MessageTextTests(unittest.TestCase):
    """doc_read_qa/table_generate 找「随文件一起说的那句话」的取值路(见 tools_doc_qa/
    tools_table 顶注):附件不经模型 slot,问题/整理指令从挂着这份附件的那条用户消息
    (attachment.message_id)原样取回。"""

    def test_returns_the_message_text(self):
        cur = _StubMessageCur({"m-1": "这份合同的付款期限是多久"})
        text = store.message_text(cur, tenant_id="t-1", session_id="s-1", message_id="m-1")
        self.assertEqual(text, "这份合同的付款期限是多久")

    def test_missing_message_id_short_circuits_without_a_query(self):
        cur = _StubMessageCur({})
        text = store.message_text(cur, tenant_id="t-1", session_id="s-1", message_id=None)
        self.assertEqual(text, "")
        self.assertFalse(cur.executed)

    def test_message_not_found_returns_empty_string_not_none(self):
        cur = _StubMessageCur({})
        text = store.message_text(cur, tenant_id="t-1", session_id="s-1", message_id="m-x")
        self.assertEqual(text, "")


if __name__ == "__main__":
    unittest.main()
