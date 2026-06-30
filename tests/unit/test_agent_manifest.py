"""manifest 自洽 + 与 agent_registry.json 交叉核对(M1 验收)。

闭集保证:大脑只能从 TOOLS 选;每个工具其功能区在 registry 必为 A 档(只读),
否则 A 档工具挂到了写/系统区 = 越权,本测试红。
"""

import unittest

from services.agent import manifest
from services.agent.contracts import ToolSpec


class TestAgentManifest(unittest.TestCase):
    def test_tools_by_name_complete_and_unique(self):
        names = [t.name for t in manifest.TOOLS]
        self.assertEqual(len(names), len(set(names)), "工具名有重复")
        self.assertEqual(
            set(names), set(manifest.TOOLS_BY_NAME), "TOOLS_BY_NAME 索引与 TOOLS 不一致"
        )

    def test_m1_registers_only_a_bucket(self):
        for t in manifest.TOOLS:
            self.assertEqual(t.bucket, "A", f"M1 只登记 A 档,{t.name} 是 {t.bucket}")
            self.assertFalse(t.confirm, f"A 档只读不应要确认:{t.name}")

    def test_every_tool_has_registry_area(self):
        for t in manifest.TOOLS:
            self.assertIn(t.name, manifest.REGISTRY_AREA, f"{t.name} 没绑定功能区")

    def test_tool_area_is_a_bucket_in_registry(self):
        registry = manifest.load_registry()
        for name, area in manifest.REGISTRY_AREA.items():
            self.assertIn(area, registry, f"{name} 的功能区 {area} 不在 agent_registry.json")
            self.assertEqual(
                registry[area],
                "A",
                f"{name} 挂在 {area}(档={registry[area]}),A 档工具必须挂 A 档功能区",
            )

    def test_handlers_resolve_on_toolset(self):
        from services.agent.executor import AgentToolset

        toolset = AgentToolset()
        for t in manifest.TOOLS:
            self.assertTrue(
                callable(getattr(toolset, t.handler, None)), f"{t.name} 的 handler 缺方法"
            )

    def test_specs_are_frozen(self):
        with self.assertRaises(Exception):
            manifest.TOOLS[0].name = "x"  # frozen dataclass 不可改
        self.assertIsInstance(manifest.TOOLS[0], ToolSpec)


if __name__ == "__main__":
    unittest.main()
