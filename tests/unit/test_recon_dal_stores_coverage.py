# -*- coding: utf-8 -*-
"""REFACTOR-D2 测试覆盖 · services/recon/ 对账任务 DAL 行为契约

既有 *_store_contract.py 只守门函数存在 + db re-export(防漂移),不测行为。
本文件补行为契约 · 用假游标拦 db.get_cursor:
  - tenant_id vs user_id 隔离矩阵(SQL 选了正确 WHERE 分支 + 正确 scope 参数)
  - 返回结构(dict / list / 分页字典 / None / bool / int)
  - 空值 / None / 异常分支 fail-safe(查询炸了返回安全默认 · 不抛)
  - 边界:batch 删除脏 id 过滤、分页 offset 计算、JSON 落库

只新建本测试文件 · 不碰任何源码 / 既有测试。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db
from services.recon import (
    vat_recon_tasks_store as vrt,
    gl_vat_store as glv,
    bank_recon_v2_store as brv2,
    bank_recon_v1_store as brv1,
    vat_recon_store as vrs,
    bank_recon_match as brm,  # REFACTOR-WA-B1 R11 · 匹配实现下沉 · patch 锚点
)


# ────────────────────────────────────────────────────────────
# 假游标:可编程 fetchone / fetchall / rowcount · 记录每次 execute(sql, params)
# ────────────────────────────────────────────────────────────
class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, rowcount=1, fetchone_seq=None):
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self._fetchone_seq = list(fetchone_seq) if fetchone_seq is not None else None
        self.rowcount = rowcount
        self.calls = []  # [(sql, params), ...]

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        if self._fetchone_seq is not None:
            return self._fetchone_seq.pop(0) if self._fetchone_seq else None
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    # 便捷断言辅助
    def all_sql(self):
        return "\n".join(c[0] for c in self.calls)

    def last_params(self):
        return self.calls[-1][1] if self.calls else None

    def all_params(self):
        return [c[1] for c in self.calls]


def patch_cursor(cur):
    """把 db.get_cursor 换成 yield 给定假游标的上下文管理器"""

    @contextmanager
    def _cm(*a, **k):
        yield cur

    return mock.patch("core.db.get_cursor", _cm)


def boom_cursor():
    """db.get_cursor 直接抛 → 验证各函数 except 分支的安全默认值"""

    @contextmanager
    def _cm(*a, **k):
        raise RuntimeError("db down")
        yield  # pragma: no cover

    return mock.patch("core.db.get_cursor", _cm)


TENANT = "11111111-1111-1111-1111-111111111111"
USER = "22222222-2222-2222-2222-222222222222"


# ════════════════════════════════════════════════════════════
# vat_recon_tasks_store
# ════════════════════════════════════════════════════════════
class VatReconTasksStoreTests(unittest.TestCase):
    def test_create_returns_str_id(self):
        cur = FakeCursor(fetchone={"id": "abc-123"})
        with patch_cursor(cur):
            rid = vrt.create_vat_recon_task(
                TENANT, USER, "ACME", "2026-05", 3, 3, 2, 1, 100.5, 4.2, "/x.xlsx", {"k": "v"}
            )
        self.assertEqual(rid, "abc-123")
        # tenant_id 序列化成 str · mismatch_amount 圆整到 2 位
        params = cur.last_params()
        self.assertEqual(params[0], TENANT)
        self.assertEqual(params[8], 100.5)

    def test_create_none_when_no_row(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(
                vrt.create_vat_recon_task(None, USER, "", "", 0, 0, 0, 0, 0, 0, None, None)
            )

    def test_create_exception_returns_none(self):
        with boom_cursor():
            self.assertIsNone(
                vrt.create_vat_recon_task(TENANT, USER, "A", "p", 0, 0, 0, 0, 0, 0, None, None)
            )

    def test_list_tenant_scope_branch(self):
        cur = FakeCursor(fetchone={"n": 5}, fetchall=[{"id": "x"}])
        with patch_cursor(cur):
            out = vrt.list_vat_recon_tasks(TENANT, USER, page=2, page_size=10)
        self.assertEqual(out["total"], 5)
        self.assertEqual(out["page"], 2)
        self.assertEqual(out["rows"], [{"id": "x"}])
        # tenant 分支:WHERE tenant_id · 不应出现 user_id 过滤
        self.assertIn("tenant_id = %s", cur.all_sql())
        self.assertNotIn("user_id = %s::uuid", cur.all_sql())
        # offset = (page-1)*page_size = 10
        self.assertEqual(cur.last_params()[-1], 10)

    def test_list_user_scope_branch(self):
        cur = FakeCursor(fetchone={"n": 0}, fetchall=[])
        with patch_cursor(cur):
            vrt.list_vat_recon_tasks(
                None, USER, page=1, page_size=20, status="done", period="2026-05"
            )
        sql = cur.all_sql()
        self.assertIn("user_id = %s::uuid", sql)
        self.assertIn("status = %s", sql)
        self.assertIn("period = %s", sql)

    def test_list_exception_returns_empty_shape(self):
        with boom_cursor():
            out = vrt.list_vat_recon_tasks(TENANT, USER, page=3, page_size=7)
        self.assertEqual(out, {"rows": [], "total": 0, "page": 3, "page_size": 7})

    def test_get_tenant_vs_user_branch(self):
        cur_t = FakeCursor(fetchone={"id": "t1"})
        with patch_cursor(cur_t):
            self.assertEqual(vrt.get_vat_recon_task("t1", TENANT, USER), {"id": "t1"})
        self.assertIn("tenant_id = %s", cur_t.all_sql())

        cur_u = FakeCursor(fetchone={"id": "u1"})
        with patch_cursor(cur_u):
            vrt.get_vat_recon_task("u1", None, USER)
        self.assertIn("user_id = %s::uuid", cur_u.all_sql())

    def test_get_none_and_exception(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(vrt.get_vat_recon_task("x", TENANT, USER))
        with boom_cursor():
            self.assertIsNone(vrt.get_vat_recon_task("x", TENANT, USER))

    def test_delete_returns_excel_path(self):
        cur = FakeCursor(fetchone={"excel_path": "/files/a.xlsx"})
        with patch_cursor(cur):
            self.assertEqual(vrt.delete_vat_recon_task("t1", TENANT, USER), "/files/a.xlsx")
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(vrt.delete_vat_recon_task("t1", None, USER))
        with boom_cursor():
            self.assertIsNone(vrt.delete_vat_recon_task("t1", TENANT, USER))

    def test_delete_older_than_returns_count_and_paths(self):
        cur = FakeCursor(
            fetchall=[{"excel_path": "/a.xlsx"}, {"excel_path": None}, {"excel_path": "/b.xlsx"}]
        )
        with patch_cursor(cur):
            n, paths = vrt.delete_vat_recon_tasks_older_than(30, TENANT, USER)
        self.assertEqual(n, 3)
        self.assertEqual(paths, ["/a.xlsx", "/b.xlsx"])  # None 被过滤
        with boom_cursor():
            self.assertEqual(vrt.delete_vat_recon_tasks_older_than(30, TENANT, USER), (0, []))

    def test_kpi_coerces_ints(self):
        cur = FakeCursor(fetchone={"this_month": "4", "running": None, "done": 2, "failed": "1"})
        with patch_cursor(cur):
            kpi = vrt.get_vat_recon_tasks_kpi(TENANT, USER)
        self.assertEqual(kpi, {"this_month": 4, "running": 0, "done": 2, "failed": 1})

    def test_kpi_user_branch_and_exception(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertEqual(
                vrt.get_vat_recon_tasks_kpi(None, USER),
                {"this_month": 0, "running": 0, "done": 0, "failed": 0},
            )
        self.assertIn("user_id = %s::uuid", cur.all_sql())
        with boom_cursor():
            self.assertEqual(
                vrt.get_vat_recon_tasks_kpi(TENANT, USER),
                {"this_month": 0, "running": 0, "done": 0, "failed": 0},
            )


# ════════════════════════════════════════════════════════════
# gl_vat_store
# ════════════════════════════════════════════════════════════
class GlVatStoreTests(unittest.TestCase):
    def test_create_returns_int_id(self):
        cur = FakeCursor(fetchone={"id": 77})
        with patch_cursor(cur):
            rid = glv.create_gl_vat_task(
                USER,
                TENANT,
                "gl.csv",
                "vat.pdf",
                10,
                8,
                [{"a": 1}],
                {"s": 1},
                matched_count=5,
                unmatched_count=3,
                diff_count=2,
            )
        self.assertEqual(rid, 77)
        self.assertIsInstance(rid, int)

    def test_create_none_and_exception(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(glv.create_gl_vat_task(USER, None, "g", "v", 0, 0, [], {}))
        with boom_cursor():
            self.assertIsNone(glv.create_gl_vat_task(USER, None, "g", "v", 0, 0, [], {}))

    def test_get_tenant_vs_user_branch(self):
        cur_t = FakeCursor(fetchone={"id": 1})
        with patch_cursor(cur_t):
            glv.get_gl_vat_task(1, USER, tenant_id=TENANT)
        self.assertIn("tenant_id = %s::uuid", cur_t.all_sql())

        cur_u = FakeCursor(fetchone={"id": 1})
        with patch_cursor(cur_u):
            glv.get_gl_vat_task(1, USER)
        self.assertIn("user_id = %s::uuid", cur_u.all_sql())

    def test_get_none_and_exception(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(glv.get_gl_vat_task(1, USER))
        with boom_cursor():
            self.assertIsNone(glv.get_gl_vat_task(1, USER))

    def test_list_returns_dicts_and_branches(self):
        cur = FakeCursor(fetchall=[{"id": 1}, {"id": 2}])
        with patch_cursor(cur):
            out = glv.list_gl_vat_tasks(USER, tenant_id=TENANT, limit=5)
        self.assertEqual(out, [{"id": 1}, {"id": 2}])
        self.assertIn("tenant_id = %s::uuid", cur.all_sql())
        # 不返回 detail_json/summary_json 减小数据量
        self.assertNotIn("detail_json", cur.all_sql())
        with boom_cursor():
            self.assertEqual(glv.list_gl_vat_tasks(USER), [])

    def test_delete_rowcount_to_bool(self):
        with patch_cursor(FakeCursor(rowcount=1)):
            self.assertTrue(glv.delete_gl_vat_task(1, USER))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(glv.delete_gl_vat_task(1, USER))
        with boom_cursor():
            self.assertFalse(glv.delete_gl_vat_task(1, USER))

    def test_batch_delete_filters_dirty_ids(self):
        # 空 → 0(不进 DB)
        self.assertEqual(glv.delete_gl_vat_tasks_batch([], USER), 0)
        # 全脏 → 0(clean_ids 空)
        self.assertEqual(glv.delete_gl_vat_tasks_batch(["abc", "x!"], USER), 0)
        # 混合:只有数字 id 进 ANY()
        cur = FakeCursor(rowcount=2)
        with patch_cursor(cur):
            n = glv.delete_gl_vat_tasks_batch(["1", 2, "bad"], USER)
        self.assertEqual(n, 2)
        self.assertEqual(cur.last_params()[0], [1, 2])  # 脏值剔除
        with boom_cursor():
            self.assertEqual(glv.delete_gl_vat_tasks_batch([1], USER), 0)


# ════════════════════════════════════════════════════════════
# bank_recon_v2_store
# ════════════════════════════════════════════════════════════
class BankReconV2StoreTests(unittest.TestCase):
    def _args(self):
        return dict(
            user_id=USER,
            tenant_id=TENANT,
            bank_code="KBANK",
            gl_account="1010",
            stmt_files="s.csv",
            gl_files="g.csv",
            stmt_row_count=10,
            gl_row_count=9,
            matched_count=8,
            unmatched_gl=1,
            unmatched_stmt=2,
            stmt_opening=100.0,
            stmt_closing=200.0,
            gl_opening=100.0,
            gl_closing=199.0,
            formula_diff=1.0,
            detail_json=[{"x": 1}],
            summary_json={"y": 2},
        )

    def test_create_returns_int(self):
        cur = FakeCursor(fetchone={"id": 5})
        with patch_cursor(cur):
            self.assertEqual(brv2.create_bank_recon_v2_task(**self._args()), 5)
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(brv2.create_bank_recon_v2_task(**self._args()))
        with boom_cursor():
            self.assertIsNone(brv2.create_bank_recon_v2_task(**self._args()))

    def test_get_branches(self):
        cur_t = FakeCursor(fetchone={"id": 1})
        with patch_cursor(cur_t):
            brv2.get_bank_recon_v2_task(1, USER, tenant_id=TENANT)
        self.assertIn("tenant_id = %s::uuid", cur_t.all_sql())
        cur_u = FakeCursor(fetchone={"id": 1})
        with patch_cursor(cur_u):
            brv2.get_bank_recon_v2_task(1, USER)
        self.assertIn("user_id = %s::uuid", cur_u.all_sql())
        with boom_cursor():
            self.assertIsNone(brv2.get_bank_recon_v2_task(1, USER))

    def test_list_branches_and_exception(self):
        cur = FakeCursor(fetchall=[{"id": 1}])
        with patch_cursor(cur):
            self.assertEqual(brv2.list_bank_recon_v2_tasks(USER, tenant_id=TENANT), [{"id": 1}])
        self.assertIn("tenant_id = %s::uuid", cur.all_sql())
        with boom_cursor():
            self.assertEqual(brv2.list_bank_recon_v2_tasks(USER), [])

    def test_delete_and_batch(self):
        with patch_cursor(FakeCursor(rowcount=1)):
            self.assertTrue(brv2.delete_bank_recon_v2_task(1, USER))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(brv2.delete_bank_recon_v2_task(1, USER))
        self.assertEqual(brv2.delete_bank_recon_v2_tasks_batch([], USER), 0)
        self.assertEqual(brv2.delete_bank_recon_v2_tasks_batch(["zzz"], USER), 0)
        cur = FakeCursor(rowcount=3)
        with patch_cursor(cur):
            self.assertEqual(brv2.delete_bank_recon_v2_tasks_batch([3, "4", "bad"], USER), 3)
        self.assertEqual(cur.last_params()[0], [3, 4])


# ════════════════════════════════════════════════════════════
# bank_recon_v1_store
# ════════════════════════════════════════════════════════════
class BankReconV1StoreTests(unittest.TestCase):
    def test_create_session_returns_id(self):
        cur = FakeCursor(fetchone={"id": "sess-1"})
        with patch_cursor(cur):
            self.assertEqual(brv1.create_bank_recon_session(USER, "KBANK", "f.pdf", 3), "sess-1")
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(brv1.create_bank_recon_session(USER, "K", "f", 1))
        with boom_cursor():
            self.assertIsNone(brv1.create_bank_recon_session(USER, "K", "f", 1))

    def test_save_parse_false_when_session_missing(self):
        # UPDATE ... RETURNING user_id 返回 None → 会话不存在 → False
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertFalse(brv1.save_bank_recon_parse("sess-x", {"transactions": []}))

    def test_save_parse_inserts_each_tx(self):
        cur = FakeCursor(fetchone={"user_id": USER})
        parsed = {
            "bank_code": "KBANK",
            "transactions": [
                {"row_no": 1, "tx_date": "2026-05-01", "direction": "IN", "amount": 100},
                {"row_no": 2, "tx_date": "2026-05-02", "direction": "OUT", "amount": 50},
            ],
        }
        with patch_cursor(cur):
            self.assertTrue(brv1.save_bank_recon_parse("sess-1", parsed))
        # 1 UPDATE session + 2 INSERT tx
        inserts = [c for c in cur.calls if "INSERT INTO bank_reconcile_transactions" in c[0]]
        self.assertEqual(len(inserts), 2)
        # tx_n=2 写进 tx_count 和 unmatched_count
        upd = cur.calls[0][1]
        self.assertIn(2, upd)

    def test_save_parse_exception(self):
        with boom_cursor():
            self.assertFalse(brv1.save_bank_recon_parse("s", {"transactions": []}))

    def test_mark_failed(self):
        with patch_cursor(FakeCursor(rowcount=1)):
            self.assertTrue(brv1.mark_recon_parse_failed("s", "boom"))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(brv1.mark_recon_parse_failed("s", "boom"))
        with boom_cursor():
            self.assertFalse(brv1.mark_recon_parse_failed("s", "boom"))

    def test_get_session_authz(self):
        cur = FakeCursor(fetchone={"id": "s1"})
        with patch_cursor(cur):
            self.assertEqual(brv1.get_bank_recon_session(USER, "s1"), {"id": "s1"})
        # WHERE id AND user_id(鉴权)
        self.assertIn("user_id = %s", cur.all_sql())
        self.assertEqual(cur.last_params(), ("s1", str(USER)))
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(brv1.get_bank_recon_session(USER, "s1"))

    def test_list_sessions_restrict_matrix(self):
        # None → 无 client filter
        cur_none = FakeCursor(fetchall=[{"id": "s"}])
        with patch_cursor(cur_none):
            brv1.list_bank_recon_sessions(USER, restrict_client_ids=None)
        self.assertNotIn("client_id", cur_none.all_sql().split("FROM")[1])

        # [] → client_id IS NULL(没分到客户只看自己未归属)
        cur_empty = FakeCursor(fetchall=[])
        with patch_cursor(cur_empty):
            brv1.list_bank_recon_sessions(USER, restrict_client_ids=[])
        self.assertIn("client_id IS NULL", cur_empty.all_sql())

        # [1,2] → ANY filter + 参数带 int 列表
        cur_some = FakeCursor(fetchall=[])
        with patch_cursor(cur_some):
            brv1.list_bank_recon_sessions(USER, limit=10, restrict_client_ids=[1, 2])
        self.assertIn("client_id = ANY(%s)", cur_some.all_sql())
        params = cur_some.last_params()
        self.assertIn([1, 2], params)

        with boom_cursor():
            self.assertEqual(brv1.list_bank_recon_sessions(USER), [])

    def test_update_session_client(self):
        with patch_cursor(FakeCursor(rowcount=1)):
            self.assertTrue(brv1.update_bank_recon_session_client(USER, "s1", 5))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(brv1.update_bank_recon_session_client(USER, "s1", None))
        with boom_cursor():
            self.assertFalse(brv1.update_bank_recon_session_client(USER, "s1", 5))

    def test_stats_default_on_no_row_and_exception(self):
        default = {
            "pending": 0,
            "matched": 0,
            "unmatched": 0,
            "total_sessions": 0,
            "last_activity_at": None,
        }
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertEqual(brv1.get_bank_recon_stats(USER), default)
        with boom_cursor():
            self.assertEqual(brv1.get_bank_recon_stats(USER), default)

    def test_stats_coerces_and_isoformats(self):
        from datetime import datetime

        ts = datetime(2026, 5, 20, 9, 30)
        cur = FakeCursor(
            fetchone={
                "pending": "3",
                "matched": 2,
                "unmatched": None,
                "total_sessions": "4",
                "last_activity_at": ts,
            }
        )
        with patch_cursor(cur):
            out = brv1.get_bank_recon_stats(USER)
        self.assertEqual(out["pending"], 3)
        self.assertEqual(out["unmatched"], 0)
        self.assertEqual(out["last_activity_at"], ts.isoformat())

    def test_list_transactions_filter(self):
        cur = FakeCursor(fetchall=[{"id": 1}])
        with patch_cursor(cur):
            brv1.list_bank_recon_transactions("s1", USER, match_filter="matched", limit=50)
        self.assertIn("match_status = %s", cur.all_sql())
        self.assertIn("matched", cur.last_params())
        # 非法 filter 不加条件
        cur2 = FakeCursor(fetchall=[])
        with patch_cursor(cur2):
            brv1.list_bank_recon_transactions("s1", USER, match_filter="garbage")
        self.assertNotIn("match_status = %s", cur2.all_sql())
        with boom_cursor():
            self.assertEqual(brv1.list_bank_recon_transactions("s1", USER), [])

    def test_delete_session(self):
        with patch_cursor(FakeCursor(rowcount=1)):
            self.assertTrue(brv1.delete_bank_recon_session(USER, "s1"))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(brv1.delete_bank_recon_session(USER, "s1"))

    def test_find_candidates_guard_clause(self):
        # amount 或 tx_date 为空 → 直接返回 [](不查 DB)
        self.assertEqual(brv1.find_invoice_candidates_for_tx(USER, 0, "2026-05-01"), [])
        self.assertEqual(brv1.find_invoice_candidates_for_tx(USER, 100, ""), [])

    def test_find_candidates_happy_path(self):
        cur = FakeCursor(fetchall=[{"id": "h1", "amount_total": 100}])
        with patch_cursor(cur):
            out = brv1.find_invoice_candidates_for_tx(USER, 100.0, "2026-05-01")
        self.assertEqual(out, [{"id": "h1", "amount_total": 100}])

    def test_find_candidates_falls_back_to_jsonb(self):
        # 主查询抛(模拟旧表无标量列)→ 降级到 _find_candidates_from_pages_jsonb
        with (
            patch_cursor(None),
            mock.patch.object(brv1.db, "get_cursor", side_effect=RuntimeError("no column")),
            # REFACTOR-WA-B1 R11:find_invoice_candidates_for_tx 与 _find_candidates_from_pages_jsonb
            # 同迁 bank_recon_match · 内部互调在该模块 resolve · patch 锚点改 brm
            mock.patch.object(
                brm, "_find_candidates_from_pages_jsonb", return_value=[{"id": "fallback"}]
            ) as m,
        ):
            out = brv1.find_invoice_candidates_for_tx(USER, 100.0, "2026-05-01")
        self.assertTrue(m.called)
        self.assertEqual(out, [{"id": "fallback"}])

    def test_save_match_result_unmatched_when_empty(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self.assertEqual(brv1.save_match_result("tx1", []), "unmatched")
        # 应清旧候选 + UPDATE unmatched
        self.assertIn("DELETE FROM bank_reconcile_candidates", cur.all_sql())
        self.assertIn("'unmatched'", cur.all_sql())

    def test_save_match_result_matched_suggested_unmatched_thresholds(self):
        # best >= thresh_auto → matched
        cur = FakeCursor()
        with patch_cursor(cur):
            st = brv1.save_match_result(
                "tx1",
                [{"history_id": "h1", "score": 90, "reason": "r"}],
                thresh_auto=85,
                thresh_suggest=60,
            )
        self.assertEqual(st, "matched")

        # suggest <= best < auto → suggested
        with patch_cursor(FakeCursor()):
            st = brv1.save_match_result(
                "tx1",
                [{"history_id": "h1", "score": 70, "reason": "r"}],
                thresh_auto=85,
                thresh_suggest=60,
            )
        self.assertEqual(st, "suggested")

        # best < suggest → unmatched
        with patch_cursor(FakeCursor()):
            st = brv1.save_match_result(
                "tx1",
                [{"history_id": "h1", "score": 40, "reason": "r"}],
                thresh_auto=85,
                thresh_suggest=60,
            )
        self.assertEqual(st, "unmatched")

        with boom_cursor():
            self.assertEqual(
                brv1.save_match_result("tx1", [{"history_id": "h", "score": 99, "reason": "r"}]),
                "unmatched",
            )

    def test_get_tx_candidates_isoformats_dates(self):
        from datetime import date

        cur = FakeCursor(
            fetchall=[
                {
                    "history_id": "h1",
                    "score": 90,
                    "invoice_date": date(2026, 5, 1),
                    "h_created_at": None,
                }
            ]
        )
        with patch_cursor(cur):
            out = brv1.get_tx_candidates("tx1", USER)
        self.assertEqual(out[0]["invoice_date"], "2026-05-01")
        self.assertIsNone(out[0]["h_created_at"])
        with boom_cursor():
            self.assertEqual(brv1.get_tx_candidates("tx1", USER), [])

    def test_update_session_match_stats(self):
        with patch_cursor(FakeCursor(rowcount=1)):
            self.assertTrue(brv1.update_session_match_stats("s1"))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(brv1.update_session_match_stats("s1"))
        with boom_cursor():
            self.assertFalse(brv1.update_session_match_stats("s1"))

    def test_override_tx_match_status_whitelist(self):
        # 非法 status → False · 不进 DB
        self.assertFalse(brv1.override_tx_match("tx", USER, None, "weird_status"))
        for st in ("matched", "unmatched", "ignored"):
            with patch_cursor(FakeCursor(rowcount=1)):
                self.assertTrue(brv1.override_tx_match("tx", USER, "h1", st))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(brv1.override_tx_match("tx", USER, "h1", "matched"))

    def test_clear_test_data_rowcount(self):
        with patch_cursor(FakeCursor(rowcount=2)):
            self.assertEqual(brv1.clear_bank_recon_test_data(USER), 2)
        with boom_cursor():
            self.assertEqual(brv1.clear_bank_recon_test_data(USER), 0)

    def test_seed_test_data_ok_and_exception(self):
        cur = FakeCursor(fetchone={"id": "seed-sess"})
        with patch_cursor(cur):
            res = brv1.seed_bank_recon_test_data(USER)
        self.assertTrue(res["ok"])
        self.assertEqual(res["tx_count"], 8)
        # 8 条流水 INSERT
        tx_inserts = [c for c in cur.calls if "INSERT INTO bank_reconcile_transactions" in c[0]]
        self.assertEqual(len(tx_inserts), 8)
        with boom_cursor():
            self.assertFalse(brv1.seed_bank_recon_test_data(USER)["ok"])


# ════════════════════════════════════════════════════════════
# vat_recon_store(销项税三表 + client helper)
# ════════════════════════════════════════════════════════════
class VatReconStoreTests(unittest.TestCase):
    def test_create_vat_report_returns_int(self):
        cur = FakeCursor(fetchone={"id": 9})
        with patch_cursor(cur):
            rid = vrs.create_vat_report(TENANT, 1, 2026, 5, [{"r": 1}], {"total_vat": 7})
        self.assertEqual(rid, 9)
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(vrs.create_vat_report(None, 1, 2026, 5, [], {}))
        with boom_cursor():
            self.assertIsNone(vrs.create_vat_report(TENANT, 1, 2026, 5, [], {}))

    def test_get_vat_report_decodes_json_string(self):
        cur = FakeCursor(fetchone={"id": 1, "parsed_rows": '[{"row_no": 1}]'})
        with patch_cursor(cur):
            r = vrs.get_vat_report(1)
        self.assertEqual(r["parsed_rows"], [{"row_no": 1}])  # str → list
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(vrs.get_vat_report(1))

    def test_create_recon_task(self):
        with patch_cursor(FakeCursor(fetchone={"id": 3})):
            self.assertEqual(vrs.create_recon_task(TENANT, USER, 1, 2026, 5, 9), 3)
        # 唯一约束冲突 → 异常 → None
        with boom_cursor():
            self.assertIsNone(vrs.create_recon_task(TENANT, USER, 1, 2026, 5, 9))

    def test_get_recon_task(self):
        with patch_cursor(FakeCursor(fetchone={"id": 1})):
            self.assertEqual(vrs.get_recon_task(1), {"id": 1})
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(vrs.get_recon_task(1))

    def test_list_recon_tasks_branches(self):
        cur_t = FakeCursor(fetchall=[{"id": 1}])
        with patch_cursor(cur_t):
            self.assertEqual(vrs.list_recon_tasks(tenant_id=TENANT), [{"id": 1}])
        self.assertIn("t.tenant_id = %s::uuid", cur_t.all_sql())
        cur_u = FakeCursor(fetchall=[])
        with patch_cursor(cur_u):
            vrs.list_recon_tasks(user_id=USER)
        self.assertIn("t.user_id = %s::uuid", cur_u.all_sql())
        with boom_cursor():
            self.assertEqual(vrs.list_recon_tasks(tenant_id=TENANT), [])

    def test_bulk_insert_recon_rows_noop_on_empty(self):
        # 空 list → 不进 DB(get_cursor 若被调用会炸,这里验证没调用)
        with boom_cursor():
            vrs.bulk_insert_recon_rows([])  # 不应抛

    def test_bulk_insert_recon_rows_inserts_each(self):
        cur = FakeCursor()
        rows = [
            {"task_id": 1, "invoice_id": None, "status": "matched"},
            {"task_id": 1, "invoice_id": "abc", "status": "mismatched", "diff_fields": {"x": 1}},
        ]
        with patch_cursor(cur):
            vrs.bulk_insert_recon_rows(rows)
        self.assertEqual(len(cur.calls), 2)

    def test_update_recon_row_action_whitelist(self):
        self.assertFalse(vrs.update_recon_row_action(1, "not_allowed"))
        for act in ("pending", "resolved", "customer_issue", "accepted_diff"):
            with patch_cursor(FakeCursor(rowcount=1)):
                self.assertTrue(vrs.update_recon_row_action(1, act))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(vrs.update_recon_row_action(1, "resolved"))

    def test_update_recon_row_ai_analysis(self):
        with patch_cursor(FakeCursor(rowcount=1)):
            self.assertTrue(vrs.update_recon_row_ai_analysis(1, {"verdict": "ok"}))
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(vrs.update_recon_row_ai_analysis(1, {}))
        with boom_cursor():
            self.assertFalse(vrs.update_recon_row_ai_analysis(1, {}))

    def test_find_client_by_tax_id(self):
        # 空 tax_id 直接 None
        self.assertIsNone(vrs.find_client_by_tax_id(TENANT, ""))
        cur_t = FakeCursor(fetchone={"id": 1})
        with patch_cursor(cur_t):
            self.assertEqual(vrs.find_client_by_tax_id(TENANT, "1234567890123"), {"id": 1})
        self.assertIn("tenant_id = %s::uuid", cur_t.all_sql())
        cur_u = FakeCursor(fetchone=None)
        with patch_cursor(cur_u):
            self.assertIsNone(vrs.find_client_by_tax_id(None, "1234567890123"))
        self.assertNotIn("tenant_id", cur_u.all_sql())

    def test_auto_create_client(self):
        with patch_cursor(FakeCursor(fetchone={"id": 42})):
            self.assertEqual(vrs.auto_create_client(USER, TENANT, "1234567890123", "ACME"), 42)
        with boom_cursor():
            self.assertIsNone(vrs.auto_create_client(USER, None, "123", "X"))

    def test_get_client_by_id(self):
        with patch_cursor(FakeCursor(fetchone={"id": 5})):
            self.assertEqual(vrs.get_client_by_id(5), {"id": 5})
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(vrs.get_client_by_id(5))

    def test_find_or_create_invalid_tax_id_length(self):
        # 非 13 位税号 → None(不查 DB)
        self.assertIsNone(vrs.find_or_create_client_by_tax_id(USER, None, "123", "X"))
        self.assertIsNone(vrs.find_or_create_client_by_tax_id(USER, None, "", "X"))

    def test_find_or_create_existing_client_short_circuits(self):
        cur = FakeCursor(fetchone={"id": 7})
        with (
            patch_cursor(cur),
            mock.patch.object(vrs.db, "create_client") as m_create,
        ):
            rid = vrs.find_or_create_client_by_tax_id(USER, TENANT, "1234567890123", "ACME")
        self.assertEqual(rid, 7)
        self.assertFalse(m_create.called)  # 找到就不建

    def test_find_or_create_creates_when_missing(self):
        cur = FakeCursor(fetchone=None)
        with (
            patch_cursor(cur),
            mock.patch.object(vrs.db, "create_client", return_value=88) as m_create,
        ):
            rid = vrs.find_or_create_client_by_tax_id(USER, None, "1234567890123", "ACME")
        self.assertEqual(rid, 88)
        self.assertTrue(m_create.called)

    def test_list_invoices_for_recon_numeric_coercion(self):
        cur = FakeCursor(
            fetchall=[
                {
                    "id": "h1",
                    "total_amount": "1,234.50",
                    "amount_pre_vat": None,
                    "vat_amount": "bad",
                }
            ]
        )
        with patch_cursor(cur):
            out = vrs.list_invoices_for_recon(
                tenant_id=TENANT, client_id=1, period_year=2026, period_month=5
            )
        self.assertEqual(out[0]["total_amount"], 1234.50)  # 逗号去掉后转 float
        self.assertIsNone(out[0]["amount_pre_vat"])
        self.assertIsNone(out[0]["vat_amount"])  # 无法转 → None
        with boom_cursor():
            self.assertEqual(vrs.list_invoices_for_recon(tenant_id=TENANT), [])


if __name__ == "__main__":
    unittest.main()
