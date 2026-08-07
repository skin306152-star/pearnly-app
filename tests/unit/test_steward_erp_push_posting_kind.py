# -*- coding: utf-8 -*-
"""erp_push 过账去向可后补(services/steward/erp_push_tool.py · 治「转人工死胡同」)。

现状(改前):prepare() 只读票上已存的 posting_kind,_build_payload 硬编码
resolve_posting_kind(None, history)——会计在对话里明确说「按库存过账」也传不进去,永续客户
没声明过就卡死在 escalate,只能重传重扣费。本文件锁住修复的四个关键点:
  ① 铸卡时声明优先于票上已存值;
  ② 声明非法(不是 stock/service)当没给,回落票上已存值,不静默当 stock(错记库存不可逆);
  ③ 执行时批文里的声明真的传进 resolve_posting_kind(不是又焊死 None);
  ④ 声明与票上现值不同时先落档(posting_kind_store.update_history_posting_kind),
     回写失败当硬失败,不能装作这次推送已经用上了声明的去向;
  ⑤ 被拦文案只在「没声明过账去向」(posting_needs_review 族)时才教怎么解开,别的拦截
     原因加这句是瞎指路。

复用 test_steward_erp_push 的桥/端点/识别记录假世界(_World3rd),不重新拼一份。
"""

from __future__ import annotations

import unittest
from unittest import mock

from core import db as _core_db  # noqa: F401 —— 先落 core.db,避免撞 dal_reexports 循环导入
from services.steward import copy, erp_push_tool, registry, tools
from services.steward.registry import ToolContext
from tests.unit.test_steward_erp_push import _ACCOUNT_SET, _HISTORY_ID, _World3rd, _ctx, _history


class PrepareDeclarationTests(unittest.TestCase):
    """铸卡前:这次说了就以这次说的为准,没说才照旧读票上已存的声明。"""

    def setUp(self):
        self.world = _World3rd(self)

    def test_declared_value_overrides_the_stored_one(self):
        self.world.history = _history(posting_kind="service")
        out = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT", "posting_kind": "stock"})
        self.assertTrue(out.ok)
        self.assertEqual(out.args["posting_kind"], "stock")

    def test_no_declaration_falls_back_to_the_stored_one(self):
        self.world.history = _history(posting_kind="service")
        out = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT"})
        self.assertEqual(out.args["posting_kind"], "service")

    def test_invalid_declaration_is_ignored_not_treated_as_stock(self):
        """脏值当没声明,回落票存值 —— 绝不静默当 stock(错记库存扣客户存货不可逆)。"""
        self.world.history = _history(posting_kind="service")
        out = tools.prepare(
            registry.ERP_PUSH, _ctx(), {"keyword": "PTT", "posting_kind": "garbage"}
        )
        self.assertEqual(out.args["posting_kind"], "service")

    def test_neither_declared_nor_stored_stays_empty(self):
        self.world.history = _history()  # 无 posting_kind 键
        out = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT"})
        self.assertEqual(out.args["posting_kind"], "")


class ExecutionReconcileTests(unittest.TestCase):
    """执行侧:批文声明落回票上 + 真传进 resolve_posting_kind,不是焊死 None。"""

    def setUp(self):
        self.world = _World3rd(self)

    def _prepared_args(self, **over):
        args = dict(tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT"}).args)
        args.update(over)
        return args

    def test_declared_value_is_passed_into_resolve_posting_kind(self):
        """explicit 真的传进去(不是又焊死 None)—— 断言调用参数,不是断言副作用。"""
        from services.erp.express_push import posting_kind as posting_kind_mod

        self.world.history = _history(posting_kind="service")
        args = self._prepared_args(posting_kind="stock")
        with (
            mock.patch(
                "services.ocr_history.posting_kind_store.update_history_posting_kind",
                return_value=True,
            ) as upd,
            mock.patch.object(
                posting_kind_mod,
                "resolve_posting_kind",
                wraps=posting_kind_mod.resolve_posting_kind,
            ) as spy,
        ):
            res = erp_push_tool.erp_push(_ctx(), args)
        self.assertTrue(res.ok, res.error_code)
        spy.assert_called_with("stock", mock.ANY)
        upd.assert_called_once_with(_HISTORY_ID, "stock", _ctx().user_id, _ctx().tenant_id)

    def test_write_back_only_fires_when_declared_differs_from_stored(self):
        """声明跟票上现值一致就不必要地写一次库 —— 省一趟写,也省一条无意义的审计行。"""
        self.world.history = _history(posting_kind="stock")
        args = self._prepared_args(posting_kind="stock")
        with mock.patch(
            "services.ocr_history.posting_kind_store.update_history_posting_kind"
        ) as upd:
            res = erp_push_tool.erp_push(_ctx(), args)
        self.assertTrue(res.ok, res.error_code)
        upd.assert_not_called()

    def test_write_back_failure_is_a_hard_failure_not_silent(self):
        """回写失败 = 硬失败:不能假装这次推送已经用上了声明的去向,桥一次没碰。"""
        self.world.history = _history(posting_kind="service")
        args = self._prepared_args(posting_kind="stock")
        with mock.patch(
            "services.ocr_history.posting_kind_store.update_history_posting_kind",
            return_value=False,
        ):
            res = erp_push_tool.erp_push(_ctx(), args)
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, erp_push_tool.ERR_POSTING_KIND_WRITE_FAILED)
        self.assertEqual(self.world.submit.call_args_list, [])

    def test_write_back_uses_the_history_id_from_the_grant(self):
        self.world.history = _history(posting_kind="service")
        args = self._prepared_args(posting_kind="stock")
        with mock.patch(
            "services.ocr_history.posting_kind_store.update_history_posting_kind",
            return_value=True,
        ) as upd:
            erp_push_tool.erp_push(_ctx(), args)
        self.assertEqual(upd.call_args.args[0], _HISTORY_ID)


class BlockedCoachingCopyTests(unittest.TestCase):
    """被拦文案:只在「没声明过账去向」那一族追加教路句,别的拦截原因不给(误导)。"""

    def test_posting_needs_review_reason_gets_the_coaching_sentence(self):
        data = {"reason": "posting_needs_review:perpetual"}
        for lang in ("zh", "th"):
            text = copy.error("steward.erp_push_blocked", data, lang)
            self.assertIn("按库存过账" if lang == "zh" else "ลงแบบสต๊อก", text)
            self.assertIn("按服务过账" if lang == "zh" else "ลงแบบบริการ", text)

    def test_other_block_reasons_do_not_get_the_coaching_sentence(self):
        data = {"reason": "account_set_not_allowed"}
        text = copy.error("steward.erp_push_blocked", data, "zh")
        self.assertNotIn("按库存过账", text)

    def test_posting_kind_write_failure_has_both_languages(self):
        for lang in ("zh", "th"):
            text = copy.error(erp_push_tool.ERR_POSTING_KIND_WRITE_FAILED, {}, lang)
            self.assertTrue(text.strip())


if __name__ == "__main__":
    unittest.main()
