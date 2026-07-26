# -*- coding: utf-8 -*-
"""管家工具注册表闭集(services/steward/registry.py + tools.py · B2-M1 + B4 首个写工具)。

锁:①注册表与执行器一一对应(不同步 = 大脑挑得到却调不了 / 或有后门能力没进闭集);
②写工具是点名白名单且个个要授权(冒出没点名的写工具即红);③表外名字物理调不到;④提示词工具表从注册表现生成
(加工具不改提示词也不会漏);⑤槽的接地来源全在 slots.py 认识的白名单里(不然接地闸会
静默把参数判成 unknown_source 丢掉)。
"""

from __future__ import annotations

import unittest

from services.agent.contracts import SlotSpec
from services.steward import registry, tools

_SLOT_SOURCES = {"user_text", "anchor", "endpoint_config", "prior_result", "model_freeform"}


class ClosedSetTests(unittest.TestCase):
    def test_registry_and_handlers_are_one_to_one(self):
        self.assertEqual(set(registry.TOOLS_BY_NAME), set(tools._HANDLERS))

    def test_handler_name_matches_declared_function(self):
        for tool in registry.TOOLS:
            self.assertEqual(tools._HANDLERS[tool.name].__name__, tool.handler)

    def test_write_tools_are_a_named_whitelist(self):
        """写工具是逐个点名进来的(B4 起只有 erp_push)。多出一个没被点名的 = 后门,红。"""
        writers = {t.name for t in registry.TOOLS if not t.readonly}
        self.assertEqual(writers, {registry.ERP_PUSH})

    def test_every_write_tool_requires_authorization(self):
        for tool in registry.TOOLS:
            self.assertEqual(registry.requires_authorization(tool), not tool.readonly, tool.name)

    def test_write_tools_declare_a_longer_timeout(self):
        """经桥写是分钟级:沿用只读工具的 5 分钟任务超时会在桥正常干活时把任务砍成 failed。"""
        for tool in registry.TOOLS:
            if not tool.readonly:
                self.assertTrue((tool.timeout_s or 0) >= 600, tool.name)

    def test_seven_tools_registered(self):
        self.assertEqual(len(registry.TOOLS), 7)
        self.assertEqual(len(registry.ALL_NAMES), len(set(registry.ALL_NAMES)))

    def test_unknown_names_rejected(self):
        for name in ("", None, "drop_tables", "push_to_erp", registry.OUT_OF_SCOPE):
            self.assertFalse(registry.is_known(name))
            self.assertIsNone(registry.get(name))

    def test_run_refuses_unregistered_tool(self):
        res = tools.run("push_to_erp", object(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools.ERR_UNKNOWN_TOOL)

    def test_run_swallows_tool_exception(self):
        """工具炸了是"这条查不出来",不是把异常抛进对话层(四态诚实)。"""
        original = tools._HANDLERS[registry.CLIENT_LOOKUP]

        def boom(_ctx, _args):
            raise RuntimeError("db down")

        tools._HANDLERS[registry.CLIENT_LOOKUP] = boom
        try:
            res = tools.run(registry.CLIENT_LOOKUP, object(), {})
        finally:
            tools._HANDLERS[registry.CLIENT_LOOKUP] = original
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools.ERR_TOOL_FAILED)


class SlotContractTests(unittest.TestCase):
    def test_slots_use_shared_contract_and_known_sources(self):
        for tool in registry.TOOLS:
            for slot in tool.slots:
                self.assertIsInstance(slot, SlotSpec)
                self.assertIn(slot.source, _SLOT_SOURCES)
                self.assertTrue(slot.desc_zh and slot.desc_th)

    def test_identity_slots_must_come_from_user_text(self):
        """客户名/关键词这类"指哪一个"的参数必须原话接地——模型编一个名字就会挂错账套。"""
        for tool in registry.TOOLS:
            for slot in tool.slots:
                if slot.name in ("client_name", "keyword"):
                    self.assertEqual(slot.source, "user_text", f"{tool.name}.{slot.name}")


class PromptCatalogTests(unittest.TestCase):
    def test_catalog_lists_every_tool(self):
        catalog = registry.catalog()
        for name in registry.ALL_NAMES:
            self.assertIn(name, catalog)

    def test_slot_hints_cover_every_slot(self):
        hints = registry.slot_hints()
        for tool in registry.TOOLS:
            for slot in tool.slots:
                self.assertIn(f"{tool.name}.{slot.name}", hints)

    def test_public_catalog_shape(self):
        rows = registry.public_catalog()
        self.assertEqual(len(rows), len(registry.TOOLS))
        self.assertTrue(all(set(r) == {"name", "desc", "readonly"} for r in rows))


if __name__ == "__main__":
    unittest.main()
