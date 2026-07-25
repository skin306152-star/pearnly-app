# -*- coding: utf-8 -*-
"""「未结转成本」判据(services/erp/push_log_meta · 无 DB/网络)。

新规则下 no_cost_basis / new_item_no_cost_basis 两类行只记收入不结 COGS,当期毛利虚高。
这里钉死三段:
1. 派生认得出这两个码,并数得出行数、认得出本次新建了库存品;
2. 筛选器的 SQL 谓词与派生共用同一份名单(分叉了「筛出来的」和「标出来的」就不是同一批单);
3. 谓词把 reason 名单走参数,不拼进 SQL(response_body 是 text 列,拼串既注入又会炸类型)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import push_log_meta as meta  # noqa: E402
from services.erp import push_log_queries as q  # noqa: E402


def _body(*reasons, created=False):
    return {
        "ok": True,
        "line_modes": [
            {"seq": i + 1, "mode": "stock_sale", "reason": r, "created": created}
            for i, r in enumerate(reasons)
        ],
    }


class DeriveUncostedTests(unittest.TestCase):
    def test_counts_lines_and_flags_created(self):
        out = meta.derive_uncosted(_body("no_cost_basis", "no_cost_basis"))
        self.assertEqual(out["uncosted_lines"], 2)
        self.assertFalse(out["uncosted_created"])

    def test_new_item_reason_implies_created(self):
        # 该码本身就是「本次新建了库存品」· 行没自报 created 也得说出来。
        out = meta.derive_uncosted(_body("new_item_no_cost_basis"))
        self.assertEqual(out["uncosted_lines"], 1)
        self.assertTrue(out["uncosted_created"])

    def test_created_flag_from_line(self):
        self.assertTrue(
            meta.derive_uncosted(_body("no_cost_basis", created=True))["uncosted_created"]
        )

    def test_empty_when_nothing_to_say(self):
        # 正常结转的成功单不带任何键 —— 列表 payload 保持轻量,前端也不会误标。
        self.assertEqual(meta.derive_uncosted({"ok": True, "line_modes": [{"seq": 1}]}), {})
        self.assertEqual(meta.derive_uncosted(_body("items_mismatch")), {})
        self.assertEqual(meta.derive_uncosted({"ok": True}), {})
        self.assertEqual(meta.derive_uncosted(None), {})
        self.assertEqual(meta.derive_uncosted("not a dict"), {})

    def test_bad_line_modes_shape_does_not_raise(self):
        self.assertEqual(meta.uncosted_lines({"line_modes": "nope"}), [])
        self.assertEqual(meta.uncosted_lines({"line_modes": ["str", None]}), [])

    def test_v3_meta_carries_uncosted(self):
        out = meta._derive_v3_meta({"meta": {"stage": "success"}, **_body("no_cost_basis")})
        self.assertEqual(out["push_stage"], "success")
        self.assertEqual(out["uncosted_lines"], 1)


class UncostedPredicateTests(unittest.TestCase):
    def test_reasons_are_not_inlined_into_sql(self):
        for reason in meta.NO_COST_REASONS:
            self.assertNotIn(reason, meta.UNCOSTED_SQL)
        self.assertIn("= ANY(%s)", meta.UNCOSTED_SQL)

    def test_guards_non_json_response_bodies(self):
        # 生产 erp_push_logs.response_body 是 text 列且混着 HTML / 裸错误串,
        # 裸 ::jsonb 会让整条列表查询报错 —— 守卫掉了就是全页 500。
        self.assertIn("pg_input_is_valid", meta.UNCOSTED_SQL)
        self.assertIn("jsonb_typeof", meta.UNCOSTED_SQL)

    def test_facade_single_source(self):
        # 前后端只认一份判据:DAL 用的常量必须就是派生用的那个对象。
        self.assertIs(q.UNCOSTED_SQL, meta.UNCOSTED_SQL)
        self.assertIs(q.NO_COST_REASONS, meta.NO_COST_REASONS)
        self.assertIs(q._derive_v3_meta, meta._derive_v3_meta)
        self.assertIs(q._derive_push_accounts, meta._derive_push_accounts)


if __name__ == "__main__":
    unittest.main()
