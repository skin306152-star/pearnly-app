# -*- coding: utf-8 -*-
"""套账切换防错上下文(switch_note · W3-3 事务所多账套)契约。

铁三条:① 未选过/切到同一个 → 空 dict 不加噪音;② 之前套账 + 30 分钟内落在
那边的最后一张单都带进观测(大脑照实告知"刚才那张在旧套账");③ 任何查询
故障 → 已取到的部分照返/空 dict,绝不抛(防错提示不许挡切换主路)。
"""

import unittest
from unittest.mock import MagicMock

from services.line_binding import line_workspace


def _cur(current_id=None, prev_name=None, recent_doc=None):
    cur = MagicMock()
    fetches = [{"current_workspace_client_id": current_id}]
    if current_id is not None:
        fetches.append({"name": prev_name} if prev_name else None)
        fetches.append(recent_doc)
    cur.fetchone.side_effect = fetches
    return cur


class TestSwitchNote(unittest.TestCase):
    def test_no_previous_selected_is_silent(self):
        out = line_workspace.switch_note(
            _cur(current_id=None), tenant_id="t1", line_user_id="U1", new_id=2
        )
        self.assertEqual(out, {})

    def test_same_workspace_is_silent(self):
        out = line_workspace.switch_note(
            _cur(current_id=2), tenant_id="t1", line_user_id="U1", new_id=2
        )
        self.assertEqual(out, {})

    def test_previous_and_recent_doc_included(self):
        doc = {"invoice_no": "IV001", "seller_name": "Makro", "total_amount": 185.0}
        out = line_workspace.switch_note(
            _cur(current_id=1, prev_name="บริษัท เอ", recent_doc=doc),
            tenant_id="t1",
            line_user_id="U1",
            new_id=2,
        )
        self.assertEqual(out["previous_workspace"], {"id": 1, "name": "บริษัท เอ"})
        self.assertEqual(out["recent_doc_in_previous"], doc)
        self.assertIn("previous workspace", out["note"])

    def test_previous_without_recent_doc(self):
        out = line_workspace.switch_note(
            _cur(current_id=1, prev_name="บริษัท เอ", recent_doc=None),
            tenant_id="t1",
            line_user_id="U1",
            new_id=2,
        )
        self.assertIn("previous_workspace", out)
        self.assertNotIn("recent_doc_in_previous", out)
        self.assertNotIn("note", out)

    def test_query_failure_never_raises(self):
        cur = MagicMock()
        cur.fetchone.side_effect = RuntimeError("db down")
        out = line_workspace.switch_note(cur, tenant_id="t1", line_user_id="U1", new_id=2)
        self.assertEqual(out, {})


if __name__ == "__main__":
    unittest.main()
