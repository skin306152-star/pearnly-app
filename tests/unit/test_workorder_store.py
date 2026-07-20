# -*- coding: utf-8 -*-
"""工单制 DAL 守门测试(services/workorder/store.py · 照 test_pos_payment_settings.py 配方)。

FakeCursor 只录 execute 调用 + 回放 fetchone/fetchall 队列,不连真库(CI 无 DB)。
锁定:① 各函数发的 SQL 形状(ON CONFLICT 幂等键对不对)② jsonb 载荷走参数化而非拼接
③ work_order_events 只追加 —— 模块公开 API 没有改/删事件的函数。
"""

import json
import unittest

from services.workorder import store


class FakeCursor:
    def __init__(self, fetch_queue=None, fetchall_queue=None):
        self.calls = []
        self._one = list(fetch_queue or [])
        self._all = list(fetchall_queue or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._one.pop(0) if self._one else None

    def fetchall(self):
        return self._all.pop(0) if self._all else []


class OpenWorkOrderTests(unittest.TestCase):
    def test_idempotent_upsert_shape_and_params(self):
        row = {
            "id": "wo-1",
            "tenant_id": "t-1",
            "workspace_client_id": 7,
            "period": "2569-05",
            "intent": "monthly_vat",
            "status": "collecting",
            "current_step": None,
            "created_at": "now",
            "updated_at": "now",
        }
        cur = FakeCursor([row])
        out = store.open_work_order(cur, tenant_id="t-1", workspace_client_id=7, period="2569-05")
        sql, params = cur.calls[0]
        self.assertIn("ON CONFLICT (tenant_id, workspace_client_id, period, intent)", sql)
        self.assertIn("DO UPDATE SET updated_at = work_orders.updated_at", sql)
        self.assertEqual(params, ("t-1", 7, "2569-05", "monthly_vat"))
        self.assertEqual(out["id"], "wo-1")

    def test_default_intent_is_monthly_vat(self):
        cur = FakeCursor([{"id": "wo-1"}])
        store.open_work_order(cur, tenant_id="t-1", workspace_client_id=7, period="2569-05")
        self.assertEqual(cur.calls[0][1][3], "monthly_vat")


class WorkOrderReadWriteTests(unittest.TestCase):
    def test_get_work_order_none_when_missing(self):
        cur = FakeCursor([None])
        self.assertIsNone(store.get_work_order(cur, tenant_id="t-1", work_order_id="wo-x"))
        self.assertIn("WHERE tenant_id = %s AND id = %s", cur.calls[0][0])

    def test_set_status_without_step_leaves_current_step_untouched(self):
        cur = FakeCursor()
        store.set_status(cur, tenant_id="t-1", work_order_id="wo-1", status="stuck")
        sql, params = cur.calls[0]
        self.assertNotIn("current_step", sql)
        self.assertEqual(params, ("stuck", "t-1", "wo-1"))

    def test_set_status_with_step_updates_both(self):
        cur = FakeCursor()
        store.set_status(
            cur, tenant_id="t-1", work_order_id="wo-1", status="running", current_step="classify"
        )
        sql, params = cur.calls[0]
        self.assertIn("current_step = %s", sql)
        self.assertEqual(params, ("running", "classify", "t-1", "wo-1"))


class EventsAppendOnlyTests(unittest.TestCase):
    def test_append_event_serializes_payload_as_json_param(self):
        cur = FakeCursor([{"id": 1, "event_type": "step_started"}])
        store.append_event(
            cur,
            tenant_id="t-1",
            work_order_id="wo-1",
            step="intake",
            event_type="step_started",
            payload={"n": 3},
        )
        sql, params = cur.calls[0]
        self.assertIn("INSERT INTO work_order_events", sql)
        self.assertEqual(json.loads(params[4]), {"n": 3})
        self.assertEqual(params[5], "system")  # actor 默认

    def test_append_event_defaults_payload_to_empty_object(self):
        cur = FakeCursor([{"id": 1}])
        store.append_event(
            cur, tenant_id="t-1", work_order_id="wo-1", step="sort", event_type="step_done"
        )
        self.assertEqual(json.loads(cur.calls[0][1][4]), {})

    def test_list_events_orders_by_insertion_id(self):
        cur = FakeCursor(fetchall_queue=[[{"id": 1}, {"id": 2}]])
        out = store.list_events(cur, tenant_id="t-1", work_order_id="wo-1")
        self.assertIn("ORDER BY id", cur.calls[0][0])
        self.assertEqual([r["id"] for r in out], [1, 2])

    def test_dal_exposes_no_mutation_functions_for_events(self):
        # 只追加铁律的直接证据:store 模块公开 API 里没有改/删事件的函数
        # (append 与两个只读查询是全部合法出口)。
        public = {n for n in dir(store) if not n.startswith("_")}
        event_mutators = {
            n
            for n in public
            if "event" in n and n not in ("append_event", "list_events", "list_event_actors")
        }
        self.assertEqual(event_mutators, set())


class ItemsTests(unittest.TestCase):
    def test_add_item_upsert_targets_dedupe_partial_index(self):
        cur = FakeCursor([{"id": "item-1", "dedupe_key": "abc"}])
        store.add_item(
            cur,
            tenant_id="t-1",
            work_order_id="wo-1",
            source="upload",
            dedupe_key="abc",
        )
        sql, params = cur.calls[0]
        self.assertIn(
            "ON CONFLICT (tenant_id, work_order_id, dedupe_key) WHERE dedupe_key IS NOT NULL", sql
        )
        self.assertEqual(params[:3], ("t-1", "wo-1", "upload"))
        self.assertEqual(params[3], "unknown")  # kind 默认

    def test_list_items_filters_by_status_when_given(self):
        cur = FakeCursor(fetchall_queue=[[]])
        store.list_items(cur, tenant_id="t-1", work_order_id="wo-1", status="flagged")
        sql, params = cur.calls[0]
        self.assertIn("AND status = %s", sql)
        self.assertEqual(params, ("t-1", "wo-1", "flagged"))

    def test_update_item_only_sets_given_fields(self):
        cur = FakeCursor()
        store.update_item(cur, tenant_id="t-1", item_id="item-1", status="flagged")
        sql, params = cur.calls[0]
        self.assertIn("status = %s", sql)
        self.assertNotIn("kind = %s", sql)
        self.assertEqual(params, ("flagged", "t-1", "item-1"))

    def test_update_item_noop_when_nothing_given(self):
        cur = FakeCursor()
        store.update_item(cur, tenant_id="t-1", item_id="item-1")
        self.assertEqual(cur.calls, [])

    def test_update_item_backfills_ocr_history_id(self):
        # 件 1:ocr_history_id 回填(给了才写,缺省不动存量 NULL)。
        cur = FakeCursor()
        store.update_item(cur, tenant_id="t-1", item_id="item-1", status="ok", ocr_history_id="h-9")
        sql, params = cur.calls[0]
        self.assertIn("ocr_history_id = %s", sql)
        self.assertEqual(params, ("ok", "h-9", "t-1", "item-1"))


class LastStepDonePayloadTests(unittest.TestCase):
    """效率5:窄取某步最后一条 step_done payload(银行对账裁决校验免全量事件流回放)。"""

    def test_narrow_query_shape_and_params(self):
        cur = FakeCursor([{"payload": {"gates": {"r3_bank": {"recon": {"auto_matched": []}}}}}])
        out = store.last_step_done_payload(
            cur, tenant_id="t-1", work_order_id="wo-1", step="reconcile"
        )
        sql, params = cur.calls[0]
        self.assertIn("event_type = 'step_done'", sql)
        self.assertIn("ORDER BY id DESC LIMIT 1", sql)
        self.assertEqual(params, ("t-1", "wo-1", "reconcile"))
        self.assertEqual(out["gates"]["r3_bank"]["recon"], {"auto_matched": []})

    def test_none_when_no_step_done(self):
        cur = FakeCursor([])
        self.assertIsNone(
            store.last_step_done_payload(
                cur, tenant_id="t-1", work_order_id="wo-1", step="reconcile"
            )
        )


class DeliverablesTests(unittest.TestCase):
    def test_upsert_deliverable_targets_kind_version_unique_key(self):
        cur = FakeCursor([{"id": "d-1", "kind": "pp30_draft", "version": 2}])
        store.upsert_deliverable(
            cur,
            tenant_id="t-1",
            work_order_id="wo-1",
            kind="pp30_draft",
            version=2,
            numbers={"tax_due": "30851.33"},
        )
        sql, params = cur.calls[0]
        self.assertIn("ON CONFLICT (tenant_id, work_order_id, kind, version)", sql)
        self.assertIn("DO UPDATE SET artifact_path = EXCLUDED.artifact_path", sql)
        self.assertEqual(params[3], 2)  # version
        self.assertEqual(json.loads(params[5]), {"tax_due": "30851.33"})

    def test_list_deliverables_takes_latest_version_per_kind(self):
        cur = FakeCursor(fetchall_queue=[[]])
        store.list_deliverables(cur, tenant_id="t-1", work_order_id="wo-1")
        sql = cur.calls[0][0]
        self.assertIn("DISTINCT ON (kind)", sql)
        self.assertIn("ORDER BY kind, version DESC", sql)

    def test_next_deliverable_version_is_max_plus_one(self):
        cur = FakeCursor([{"v": 3}])
        self.assertEqual(
            store.next_deliverable_version(cur, tenant_id="t-1", work_order_id="wo-1"), 3
        )
        self.assertIn("COALESCE(MAX(version), 0) + 1", cur.calls[0][0])


class NarrowEventReadTests(unittest.TestCase):
    def test_list_event_actors_is_narrow_read_in_insertion_order(self):
        # 效率4(MC2-A1):熔断预算只要 run/run_requested 的 actor 序列,不整流搬回。
        cur = FakeCursor(fetchall_queue=[[{"actor": "system:reaper"}, {"actor": "user:a"}]])
        out = store.list_event_actors(
            cur, tenant_id="t-1", work_order_id="wo-1", step="run", event_type="run_requested"
        )
        sql, params = cur.calls[0]
        self.assertIn("SELECT actor FROM work_order_events", sql)
        self.assertIn("ORDER BY id", sql)
        self.assertEqual(params, ("t-1", "wo-1", "run", "run_requested"))
        self.assertEqual(out, ["system:reaper", "user:a"])


class AppendEventDedupeTests(unittest.TestCase):
    """C-1 §4 事件幂等键:无 dedupe_key = 老路径逐字节;带 key = ON CONFLICT DO NOTHING。"""

    def test_no_dedupe_key_keeps_legacy_insert(self):
        cur = FakeCursor([{"id": 1}])
        store.append_event(
            cur, tenant_id="t-1", work_order_id="wo-1", step="classify", event_type="x"
        )
        sql, _ = cur.calls[0]
        self.assertNotIn("ON CONFLICT", sql)
        self.assertNotIn("dedupe_key", sql)

    def test_dedupe_key_uses_on_conflict_do_nothing(self):
        cur = FakeCursor([{"id": 2}])
        store.append_event(
            cur,
            tenant_id="t-1",
            work_order_id="wo-1",
            step="classify",
            event_type="item_classified",
            payload={"item_id": "i1"},
            dedupe_key="classify:i1",
        )
        sql, params = cur.calls[0]
        self.assertIn("ON CONFLICT (tenant_id, work_order_id, step, event_type, dedupe_key)", sql)
        self.assertIn("DO NOTHING", sql)
        self.assertEqual(params[-1], "classify:i1")

    def test_dedupe_conflict_returns_existing_row(self):
        # INSERT ON CONFLICT DO NOTHING → 无 RETURNING 行(None);回读既有那条返回,不重记。
        cur = FakeCursor([None, {"id": 7, "event_type": "item_classified"}])
        out = store.append_event(
            cur,
            tenant_id="t-1",
            work_order_id="wo-1",
            step="classify",
            event_type="item_classified",
            dedupe_key="classify:i1",
        )
        self.assertEqual(out["id"], 7)
        self.assertEqual(len(cur.calls), 2)  # INSERT + 回读 SELECT
        self.assertIn("SELECT", cur.calls[1][0])


if __name__ == "__main__":
    unittest.main()


class UpdateItemFlagReasonTests(unittest.TestCase):
    """None 是「省略此字段」不是「置空」——两者混淆过一次(statement_regroup 以为传
    flag_reason=None 就清掉了,脏值留在库里)。这里把语义钉死在 DAL 层。"""

    def test_none_flag_reason_is_omitted_not_cleared(self):
        cur = FakeCursor()
        store.update_item(cur, tenant_id="t-1", item_id="i-1", status="ok", flag_reason=None)
        sql, params = cur.calls[0]
        self.assertNotIn("flag_reason", sql)
        self.assertEqual(params, ("ok", "t-1", "i-1"))

    def test_clear_flag_reason_writes_sql_null(self):
        cur = FakeCursor()
        store.update_item(cur, tenant_id="t-1", item_id="i-1", status="ok", clear_flag_reason=True)
        sql, params = cur.calls[0]
        self.assertIn("flag_reason = NULL", sql)
        # NULL 直接进 SQL 文本,不占参数位——多塞一个占位符会让参数错位。
        self.assertEqual(params, ("ok", "t-1", "i-1"))

    def test_explicit_value_wins_over_clear_flag(self):
        cur = FakeCursor()
        store.update_item(
            cur, tenant_id="t-1", item_id="i-1", flag_reason="ocr_error:x", clear_flag_reason=True
        )
        sql, params = cur.calls[0]
        self.assertIn("flag_reason = %s", sql)
        self.assertNotIn("flag_reason = NULL", sql)
        self.assertEqual(params, ("ocr_error:x", "t-1", "i-1"))

    def test_clear_flag_alone_still_issues_update(self):
        cur = FakeCursor()
        store.update_item(cur, tenant_id="t-1", item_id="i-1", clear_flag_reason=True)
        self.assertEqual(len(cur.calls), 1)
        self.assertIn("flag_reason = NULL", cur.calls[0][0])
