"""守 Agent 能力防漏闸:每个 routes/*.py 都已在 agent_registry.json 分类。

新增路由文件忘了登记 → 闸脚本非零 → 本测试红,提醒"这条还没决定进不进 Agent"。
与 CI 的 lint-agent job 同闸,单测层再兜一道。
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "agent_capability_audit.py"
REGISTRY = ROOT / "docs" / "agent" / "agent_registry.json"


class TestAgentCapabilityAudit(unittest.TestCase):
    def test_audit_script_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertEqual(result.returncode, 0, f"防漏闸非零退出:\n{result.stdout}\n{result.stderr}")

    def test_buckets_are_valid(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for key, value in registry.items():
            if key.startswith("_"):
                continue
            bucket = value.get("bucket") if isinstance(value, dict) else value
            self.assertIn(bucket, {"A", "B", "C", "D"}, f"{key} 的桶 {bucket!r} 非法(应 A/B/C/D)")

    def test_a_bucket_tool_annotations_match_manifest(self):
        # A 档 tool: 声明的每个工具名必须真在 manifest 里(防登记表写不存在的名假装"已接")。
        from services.agent import manifest

        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for area, value in registry.items():
            if area.startswith("_") or not isinstance(value, dict):
                continue
            agent = value.get("agent") or ""
            if not agent.startswith("tool:"):
                continue
            for name in agent.split(":", 1)[1].split(","):
                name = name.strip()
                self.assertIn(name, manifest.TOOLS_BY_NAME, f"{area} 声明了不存在的工具 {name}")

    def test_every_a_tool_area_is_annotated(self):
        # 反向:manifest 挂在 A 档功能区的工具,该区 agent 声明必须点到它(防单向漂移)。
        from services.agent import manifest

        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for tool_name, area in manifest.REGISTRY_AREA.items():
            value = registry.get(area)
            bucket = value.get("bucket") if isinstance(value, dict) else value
            if bucket != "A":
                continue
            agent = (value.get("agent") or "") if isinstance(value, dict) else ""
            names = [n.strip() for n in agent.split(":", 1)[1].split(",")] if ":" in agent else []
            self.assertIn(tool_name, names, f"{area} 的 agent 声明没点到工具 {tool_name}")


if __name__ == "__main__":
    unittest.main()
