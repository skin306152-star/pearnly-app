# -*- coding: utf-8 -*-
"""REFACTOR-D2 覆盖补强 · services/erp/push_store.py 数据层行为契约

只新增测试 · 不碰源码。用假游标 (FakeCursor) 截 SQL/params,验证:
  - 端点 CRUD(list/get/create/update/delete)的 SQL 形态、user_id scope、
    is_default 互斥、字段白名单、jsonb 序列化。
  - push log 写入/去重/统计的返回结构与 None 边界。
  - 重试调度纯函数(get_erp_retry_delay_sec / is_user_data_error /
    classify_push_status / classify_push_exception)的真行为契约。
  - 异常分支(get_cursor 抛错)被吞 → 返回安全默认值(不冒泡)。

不依赖真实 DB · 不触发计费/推送。
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import db  # noqa: E402,F401  · 先 import db 避免 partial-init 循环
from services.erp import push_store as store  # noqa: E402


# ─────────────────────────── 假游标基建 ───────────────────────────
class FakeCursor:
    """记录每次 execute 的 (sql, params);可预设 fetchone/fetchall 结果与 rowcount。"""

    def __init__(self, fetchone=None, fetchall=None, rowcount=0, fetchone_seq=None):
        self.calls = []  # [(sql, params), ...]
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self.rowcount = rowcount
        self._fetchone_seq = list(fetchone_seq) if fetchone_seq is not None else None

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        if self._fetchone_seq is not None:
            return self._fetchone_seq.pop(0) if self._fetchone_seq else None
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    # 便捷断言辅助
    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class FakeCM:
    """get_cursor(...) 上下文管理器替身。记录是否传了 commit=True。"""

    def __init__(self, cur, commit_flag_box):
        self.cur = cur
        self._box = commit_flag_box

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def patch_cursor(cur):
    """返回一个 patch 对象:把 store.db.get_cursor 换成产出 cur 的工厂。
    同时把每次调用的 kwargs 收集到 cur.cm_kwargs。"""
    cur.cm_kwargs = []

    def factory(*a, **k):
        cur.cm_kwargs.append(k)
        return FakeCM(cur, None)

    return mock.patch.object(store.db, "get_cursor", factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(store.db, "get_cursor", factory)


# ─────────────────────── 纯函数:重试延迟序列 ───────────────────────
class RetryDelayTests(unittest.TestCase):
    def test_delay_sequence_matches_backoff(self):
        # 0/1/2 次 → 60/300/1800;到上限返回 None
        self.assertEqual(store.get_erp_retry_delay_sec(0), 60)
        self.assertEqual(store.get_erp_retry_delay_sec(1), 300)
        self.assertEqual(store.get_erp_retry_delay_sec(2), 1800)

    def test_at_or_over_max_returns_none(self):
        self.assertIsNone(store.get_erp_retry_delay_sec(store.ERP_MAX_RETRIES))
        self.assertIsNone(store.get_erp_retry_delay_sec(99))

    def test_negative_returns_none(self):
        self.assertIsNone(store.get_erp_retry_delay_sec(-1))

    def test_max_retries_const(self):
        self.assertEqual(store.ERP_MAX_RETRIES, len(store._ERP_RETRY_DELAYS_SEC))


# ─────────────────── 纯函数:用户数据错误分类器 ───────────────────
class UserDataErrorTests(unittest.TestCase):
    def test_each_err_code_matches(self):
        for code in store.USER_DATA_ERROR_CODES:
            self.assertTrue(store.is_user_data_error(f"prefix {code} suffix"), code)

    def test_thai_patterns_match(self):
        for pat in store.USER_DATA_ERROR_THAI_PATTERNS:
            self.assertTrue(store.is_user_data_error(f"...{pat}..."), pat)

    def test_technical_errors_not_user_data(self):
        self.assertFalse(store.is_user_data_error("ETIMEDOUT after 30s"))
        self.assertFalse(store.is_user_data_error("Connection refused"))
        # VERIFY_UNAVAILABLE 故意属技术错 · 不在 USER_DATA set
        self.assertFalse(store.is_user_data_error("ERR_CUSTOMER_VERIFY_UNAVAILABLE"))

    def test_empty_and_none(self):
        self.assertFalse(store.is_user_data_error(None))
        self.assertFalse(store.is_user_data_error(""))


class ClassifyPushExceptionTests(unittest.TestCase):
    def test_buckets(self):
        c = store.classify_push_exception
        self.assertEqual(c("ERR_CUSTOMER_NAME_MISMATCH"), "customer_mismatch")
        self.assertEqual(c("ERR_NO_CUSTOMER_MAPPING"), "customer_mismatch")
        self.assertEqual(c("ERR_PRODUCT_NAME_MISMATCH"), "product_mismatch")
        self.assertEqual(c("ERR_NO_CLIENT"), "no_client")
        self.assertEqual(c("xx VERIFY_UNAVAILABLE yy"), "verify_unavailable")
        self.assertEqual(c("ERR_RANDOM"), "other")
        self.assertEqual(c(None), "other")

    def test_customer_mismatch_priority_over_no_client(self):
        # 同时含 customer + client 关键词 → customer 分支先命中(顺序契约)
        self.assertEqual(
            store.classify_push_exception("ERR_NO_CUSTOMER_MAPPING ERR_NO_CLIENT"),
            "customer_mismatch",
        )


# ─────────────────────── 端点 CRUD 行为 ───────────────────────
class ListEndpointsTests(unittest.TestCase):
    def test_returns_dict_list_and_scopes_user(self):
        cur = FakeCursor(fetchall=[{"id": "e1", "name": "x"}])
        with patch_cursor(cur):
            out = store.list_erp_endpoints("u1")
        self.assertEqual(out, [{"id": "e1", "name": "x"}])
        self.assertEqual(cur.last_params, ("u1",))
        self.assertIn("WHERE user_id = %s", cur.last_sql)
        # 默认不加 auto_push 过滤
        self.assertNotIn("auto_push = TRUE", cur.last_sql)

    def test_auto_push_only_adds_filter(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            store.list_erp_endpoints("u1", auto_push_only=True)
        self.assertIn("auto_push = TRUE AND enabled = TRUE", cur.last_sql)

    def test_select_includes_user_id_column_erp1_fix(self):
        # ERP-1 修:SELECT 必须含 user_id(否则自动推 tenant_id None)
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            store.list_erp_endpoints("u1")
        self.assertIn("user_id", cur.last_sql)

    def test_exception_returns_empty(self):
        with patch_cursor_raises():
            self.assertEqual(store.list_erp_endpoints("u1"), [])


class GetEndpointTests(unittest.TestCase):
    def test_returns_dict(self):
        cur = FakeCursor(fetchone={"id": "e1"})
        with patch_cursor(cur):
            out = store.get_erp_endpoint("u1", "e1")
        self.assertEqual(out, {"id": "e1"})
        self.assertEqual(cur.last_params, ("u1", "e1"))

    def test_missing_returns_none(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(store.get_erp_endpoint("u1", "nope"))

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.get_erp_endpoint("u1", "e1"))


class GetDefaultEndpointTests(unittest.TestCase):
    def test_only_enabled_and_default_first(self):
        cur = FakeCursor(fetchone={"id": "e1", "is_default": True})
        with patch_cursor(cur):
            out = store.get_default_erp_endpoint("u1")
        self.assertEqual(out["id"], "e1")
        self.assertIn("enabled = true", cur.last_sql)
        self.assertIn("is_default DESC", cur.last_sql)

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.get_default_erp_endpoint("u1"))


class CreateEndpointTests(unittest.TestCase):
    def test_returns_new_id_and_serializes_config(self):
        cur = FakeCursor(fetchone={"id": "new-1"})
        with patch_cursor(cur):
            out = store.create_erp_endpoint("u1", "n", "webhook", {"url": "x"})
        self.assertEqual(out, "new-1")
        # config 被 json.dumps · INSERT 的 params 里应有 '{"url": "x"}'
        insert_call = [c for c in cur.calls if "INSERT INTO erp_endpoints" in c[0]][0]
        self.assertIn('"url": "x"', insert_call[1][3])
        # 成功后清空 module-global error
        self.assertIsNone(store._last_create_endpoint_error)

    def test_is_default_unsets_others_first(self):
        cur = FakeCursor(fetchone={"id": "new-1"})
        with patch_cursor(cur):
            store.create_erp_endpoint("u1", "n", "webhook", {}, is_default=True)
        # 第一条应是把别的 is_default 取消
        self.assertIn("SET is_default = false", cur.calls[0][0])

    def test_no_unset_when_not_default(self):
        cur = FakeCursor(fetchone={"id": "new-1"})
        with patch_cursor(cur):
            store.create_erp_endpoint("u1", "n", "webhook", {}, is_default=False)
        self.assertNotIn("SET is_default = false", cur.all_sql())

    def test_exception_records_global_error_and_returns_none(self):
        with patch_cursor_raises(ValueError("dberr")):
            out = store.create_erp_endpoint("u1", "n", "webhook", {})
        self.assertIsNone(out)
        self.assertIsNotNone(store._last_create_endpoint_error)
        self.assertIn("ValueError", store._last_create_endpoint_error)


class UpdateEndpointTests(unittest.TestCase):
    def test_no_allowed_fields_returns_false_without_db(self):
        # 全是非白名单字段 → 不触 DB · 直接 False
        called = {"hit": False}

        def factory(*a, **k):
            called["hit"] = True
            raise AssertionError("should not open cursor")

        with mock.patch.object(store.db, "get_cursor", factory):
            self.assertFalse(store.update_erp_endpoint("u1", "e1", bogus=1, secret=2))
        self.assertFalse(called["hit"])

    def test_config_serialized_as_jsonb(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = store.update_erp_endpoint("u1", "e1", config={"a": 1})
        self.assertTrue(ok)
        self.assertIn("config = %s::jsonb", cur.last_sql)
        self.assertIn('"a": 1', cur.last_params[0])

    def test_is_default_unsets_other_rows(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            store.update_erp_endpoint("u1", "e1", is_default=True)
        self.assertIn("id <> %s", cur.calls[0][0])

    def test_rowcount_zero_returns_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(store.update_erp_endpoint("u1", "e1", name="z"))

    def test_exception_returns_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.update_erp_endpoint("u1", "e1", name="z"))


class DeleteEndpointTests(unittest.TestCase):
    def test_stops_retries_then_deletes(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = store.delete_erp_endpoint("u1", "e1")
        self.assertTrue(ok)
        # 第一条:停挂起重试(next_retry_at = NULL);第二条:DELETE
        self.assertIn("next_retry_at = NULL", cur.calls[0][0])
        self.assertIn("DELETE FROM erp_endpoints", cur.calls[1][0])

    def test_rowcount_zero_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(store.delete_erp_endpoint("u1", "e1"))

    def test_exception_returns_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.delete_erp_endpoint("u1", "e1"))


# ─────────────────────── push log 写/查/去重/统计 ───────────────────────
class InsertPushLogTests(unittest.TestCase):
    def test_returns_id_and_jsonb_request_body(self):
        cur = FakeCursor(fetchone={"id": "log-1"})
        with patch_cursor(cur):
            out = store.insert_push_log(
                "u1",
                "e1",
                "h1",
                "INV1",
                "seller",
                100.0,
                "success",
                200,
                {"k": "v"},
                "resp",
                None,
                1,
                50,
                "manual",
            )
        self.assertEqual(out, "log-1")
        # request_body json 序列化进 params(第 9 个值,index 8)
        self.assertIn('"k": "v"', cur.last_params[8])

    def test_none_request_body_passes_none(self):
        cur = FakeCursor(fetchone={"id": "log-1"})
        with patch_cursor(cur):
            store.insert_push_log(
                "u1",
                None,
                None,
                None,
                None,
                None,
                "failed",
                None,
                None,
                None,
                "err",
                0,
                0,
            )
        self.assertIsNone(cur.last_params[8])

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            out = store.insert_push_log(
                "u1",
                "e1",
                "h1",
                "INV1",
                "s",
                1.0,
                "success",
                200,
                None,
                None,
                None,
                1,
                1,
            )
        self.assertIsNone(out)


class HasRecentSuccessfulPushTests(unittest.TestCase):
    def test_missing_args_short_circuit(self):
        # history_id 或 endpoint_id 缺 → 不查 DB 直接 None
        with patch_cursor_raises(AssertionError("should not query")):
            self.assertIsNone(store.has_recent_successful_push("", "e1", "u1"))
            self.assertIsNone(store.has_recent_successful_push("h1", "", "u1"))

    def test_scopes_user_and_success_only(self):
        cur = FakeCursor(fetchone={"id": "log-9", "invoice_no": "INV"})
        with patch_cursor(cur):
            out = store.has_recent_successful_push("h1", "e1", "u1")
        self.assertEqual(out["id"], "log-9")
        self.assertIn("status = 'success'", cur.last_sql)
        self.assertEqual(cur.last_params, ("h1", "e1", "u1"))

    def test_none_when_no_row(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(store.has_recent_successful_push("h1", "e1", "u1"))

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.has_recent_successful_push("h1", "e1", "u1"))


class UpdateEndpointStatsTests(unittest.TestCase):
    def test_success_increments_success_count(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.update_endpoint_stats("e1", True)
        self.assertIn("success_count = success_count + 1", cur.last_sql)
        self.assertIn("'success'", cur.last_sql)

    def test_failure_increments_failure_count(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.update_endpoint_stats("e1", False)
        self.assertIn("failure_count = failure_count + 1", cur.last_sql)
        self.assertIn("'failed'", cur.last_sql)

    def test_exception_swallowed(self):
        with patch_cursor_raises():
            store.update_endpoint_stats("e1", True)  # 不抛即通过


class UpdateHistoryPushStatusTests(unittest.TestCase):
    def test_updates_ocr_history(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.update_history_push_status("h1", "success")
        self.assertIn("UPDATE ocr_history", cur.last_sql)
        self.assertEqual(cur.last_params, ("success", "h1"))

    def test_exception_swallowed(self):
        with patch_cursor_raises():
            store.update_history_push_status("h1", "success")


class RetrySchedulingTests(unittest.TestCase):
    def test_schedule_log_retry_uses_interval_and_failed_guard(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = store.schedule_log_retry("log-1", 300)
        self.assertTrue(ok)
        self.assertIn("INTERVAL '1 second'", cur.last_sql)
        self.assertIn("status = 'failed'", cur.last_sql)
        self.assertEqual(cur.last_params, (300, "log-1"))

    def test_schedule_rowcount_zero_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(store.schedule_log_retry("log-1", 60))

    def test_schedule_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.schedule_log_retry("log-1", 60))

    def test_clear_retry_schedule_nulls_next_retry(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.clear_retry_schedule("log-1")
        self.assertIn("next_retry_at = NULL", cur.last_sql)
        self.assertEqual(cur.last_params, ("log-1",))

    def test_clear_exception_swallowed(self):
        with patch_cursor_raises():
            store.clear_retry_schedule("log-1")


class ListLogsDueForRetryTests(unittest.TestCase):
    def test_returns_dict_rows_with_failed_and_due_guards(self):
        cur = FakeCursor(fetchall=[{"id": "l1"}, {"id": "l2"}])
        with patch_cursor(cur):
            out = store.list_logs_due_for_retry(limit=5)
        self.assertEqual([r["id"] for r in out], ["l1", "l2"])
        self.assertIn("status = 'failed'", cur.last_sql)
        self.assertIn("next_retry_at <= NOW()", cur.last_sql)
        self.assertIn("retry_count < l.max_retries", cur.last_sql)
        self.assertEqual(cur.last_params, (5,))

    def test_exception_returns_empty(self):
        with patch_cursor_raises():
            self.assertEqual(store.list_logs_due_for_retry(), [])


class IncrementRetryCountTests(unittest.TestCase):
    def test_returns_new_count(self):
        cur = FakeCursor(fetchone={"retry_count": 3})
        with patch_cursor(cur):
            self.assertEqual(store.increment_retry_count("l1"), 3)
        self.assertIn("retry_count = retry_count + 1", cur.last_sql)

    def test_no_row_returns_zero(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertEqual(store.increment_retry_count("l1"), 0)

    def test_exception_returns_zero(self):
        with patch_cursor_raises():
            self.assertEqual(store.increment_retry_count("l1"), 0)


class UpdateLogStatusAfterRetryTests(unittest.TestCase):
    def test_default_maps_success_bool(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.update_log_status_after_retry("l1", True, 200, "resp", None, 10)
        # status 是 params 第一个
        self.assertEqual(cur.last_params[0], "success")

    def test_default_maps_failure_bool(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.update_log_status_after_retry("l1", False, 500, "r", "err", 10)
        self.assertEqual(cur.last_params[0], "failed")

    def test_final_status_overrides(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.update_log_status_after_retry(
                "l1", False, 200, "r", "e", 10, final_status="skipped_dup"
            )
        self.assertEqual(cur.last_params[0], "skipped_dup")

    def test_request_body_none_keeps_original_via_coalesce(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.update_log_status_after_retry("l1", True, 200, "r", None, 10)
        self.assertIn("COALESCE(%s::jsonb, request_body)", cur.last_sql)
        # rb 参数(倒数第二)应为 None → 保留原值
        self.assertIsNone(cur.last_params[-2])

    def test_request_body_dict_serialized(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.update_log_status_after_retry(
                "l1", True, 200, "r", None, 10, request_body={"x": 1}
            )
        self.assertIn('"x": 1', cur.last_params[-2])

    def test_exception_swallowed(self):
        with patch_cursor_raises():
            store.update_log_status_after_retry("l1", True, 200, "r", None, 10)


class DeletePushLogsTests(unittest.TestCase):
    def test_empty_ids_short_circuit_zero(self):
        with patch_cursor_raises(AssertionError("should not query")):
            self.assertEqual(store.delete_push_logs("u1", []), 0)

    def test_scopes_user_and_returns_rowcount(self):
        cur = FakeCursor(rowcount=2)
        with patch_cursor(cur):
            n = store.delete_push_logs("u1", ["l1", "l2"])
        self.assertEqual(n, 2)
        self.assertIn("user_id = %s", cur.last_sql)
        self.assertEqual(cur.last_params, ("u1", ["l1", "l2"]))

    def test_exception_returns_zero(self):
        with patch_cursor_raises():
            self.assertEqual(store.delete_push_logs("u1", ["l1"]), 0)


class GetPushStatsTodayTests(unittest.TestCase):
    def test_returns_row_dict(self):
        cur = FakeCursor(fetchone={"total": 5, "success": 3, "failed": 2, "auto_cnt": 1})
        with patch_cursor(cur):
            out = store.get_push_stats_today("u1")
        self.assertEqual(out["total"], 5)
        self.assertIn("CURRENT_DATE", cur.last_sql)

    def test_no_row_returns_zeros(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            out = store.get_push_stats_today("u1")
        self.assertEqual(out, {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0})

    def test_exception_returns_zeros(self):
        with patch_cursor_raises():
            out = store.get_push_stats_today("u1")
        self.assertEqual(out, {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0})


class GetPushLogDetailTests(unittest.TestCase):
    def test_none_when_no_row(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(store.get_push_log_detail("u1", "l1"))

    def test_returns_detail_with_derived_and_friendly(self):
        row = {
            "id": "l1",
            "endpoint_adapter": "webhook",
            "response_body": None,
            "status": "failed",
            "error_msg": "ERR_NO_CLIENT",
        }
        cur = FakeCursor(fetchone=row)
        with patch_cursor(cur):
            out = store.get_push_log_detail("u1", "l1")
        self.assertEqual(out["id"], "l1")
        # derive_external_ref + friendly_for_ui 已 update 进去
        self.assertIn("error_friendly", out)
        self.assertEqual(cur.last_params, ("l1", "u1"))

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.get_push_log_detail("u1", "l1"))


class ListPushLogsTests(unittest.TestCase):
    """折叠版 list_push_logs:COUNT + 数据两次查询 · 派生 external_ref。"""

    def _run(self, **kw):
        # 两次 execute:第一次 COUNT(fetchone),第二次数据(fetchall)
        cur = FakeCursor(
            fetchone={"n": 1},
            fetchall=[
                {
                    "id": "l1",
                    "endpoint_adapter": "webhook",
                    "response_body": None,
                    "status": "success",
                    "error_msg": None,
                }
            ],
        )
        with patch_cursor(cur):
            return store.list_push_logs("u1", **kw), cur

    def test_returns_items_and_total(self):
        res, cur = self._run()
        self.assertEqual(res["total"], 1)
        self.assertEqual(len(res["items"]), 1)
        # response_body 被 pop 掉(列表轻量)
        self.assertNotIn("response_body", res["items"][0])

    def test_status_filter_retrying_builds_retry_predicate(self):
        res, cur = self._run(status_filter="retrying")
        self.assertIn("next_retry_at IS NOT NULL", cur.all_sql())

    def test_status_filter_failed_builds_terminal_predicate(self):
        res, cur = self._run(status_filter="failed")
        self.assertIn("next_retry_at IS NULL", cur.all_sql())

    def test_exception_returns_empty_shape(self):
        with patch_cursor_raises():
            res = store.list_push_logs("u1")
        self.assertEqual(res, {"items": [], "total": 0})


if __name__ == "__main__":
    unittest.main()
