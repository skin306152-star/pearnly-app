"""manifest 自洽 + 与 agent_registry.json 交叉核对(M1 验收)。

闭集保证:大脑只能从 TOOLS 选;每个工具其功能区在 registry 必为 A 档(只读),
否则 A 档工具挂到了写/系统区 = 越权,本测试红。
"""

import unittest

from services.agent import copy_map, manifest
from services.agent.contracts import ToolSpec

# CONVERSATION-SPEC §1.5 失败码表(键名锁定 · 两窗口对齐唯一源)。
_SPEC_FAILURE_CODES = {
    "insufficient_balance",
    "no_endpoint",
    "forbidden",
    "history_not_found",
    "no_tenant",
    "query_failed",
    "not_available_yet",
    "unknown",
}


class TestAgentManifest(unittest.TestCase):
    def test_tools_by_name_complete_and_unique(self):
        names = [t.name for t in manifest.TOOLS]
        self.assertEqual(len(names), len(set(names)), "工具名有重复")
        self.assertEqual(
            set(names), set(manifest.TOOLS_BY_NAME), "TOOLS_BY_NAME 索引与 TOOLS 不一致"
        )

    def test_buckets_valid_and_readonly_no_confirm(self):
        # M2:已含 A(只读)+ B(写:套账切换)。A 档只读一律不需确认。
        for t in manifest.TOOLS:
            self.assertIn(t.bucket, ("A", "B"), f"{t.name} 档非法:{t.bucket}")
            if t.bucket == "A":
                self.assertFalse(t.confirm, f"A 档只读不应要确认:{t.name}")

    def test_every_tool_has_registry_area(self):
        for t in manifest.TOOLS:
            self.assertIn(t.name, manifest.REGISTRY_AREA, f"{t.name} 没绑定功能区")

    def test_tool_bucket_matches_registry_area_bucket(self):
        # 工具档必须与其功能区在 registry 的档一致(A 工具挂 A 区,B 工具挂 B 区)。
        registry = manifest.load_registry()
        for t in manifest.TOOLS:
            area = manifest.REGISTRY_AREA[t.name]
            self.assertIn(area, registry, f"{t.name} 的功能区 {area} 不在 agent_registry.json")
            self.assertEqual(
                registry[area],
                t.bucket,
                f"{t.name}(档={t.bucket})挂在 {area}(档={registry[area]}),档必须一致",
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


class TestCopyMapKeyAlignment(unittest.TestCase):
    """键名锁定:失败 agent.failure.* / 成功回执 agent.ok.*(CONVERSATION-SPEC §1.3/§1.5)。"""

    def test_failure_keys_prefixed(self):
        for code, key in copy_map.ERROR_COPY.items():
            self.assertTrue(key.startswith("agent.failure."), f"{code}→{key} 应 agent.failure.*")

    def test_spec_failure_codes_covered(self):
        missing = _SPEC_FAILURE_CODES - set(copy_map.ERROR_COPY)
        self.assertFalse(missing, f"spec §1.5 失败码未映射:{missing}")

    def test_ok_keys_map_to_real_tools(self):
        # 换脑后回复由模型撰写(loop 用工具 data 成文),copy_map 模板退为兜底 · 非每工具必备;
        # 但 OK_COPY 里不许有指向不存在工具的孤儿 key。
        names = {t.name for t in manifest.TOOLS}
        self.assertTrue(set(copy_map.OK_COPY).issubset(names), "OK_COPY 有孤儿 key(非真实工具)")
        for key in copy_map.OK_COPY.values():
            self.assertTrue(key.startswith("agent.ok."), f"{key} 应 agent.ok.*")

    def test_failure_default_is_spec_default(self):
        self.assertEqual(copy_map.failure("never_seen_code"), "agent.failure._default")


if __name__ == "__main__":
    unittest.main()
