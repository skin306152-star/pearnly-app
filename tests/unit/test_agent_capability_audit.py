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
        for key, bucket in registry.items():
            if key.startswith("_"):
                continue
            self.assertIn(bucket, {"A", "B", "C", "D"}, f"{key} 的桶 {bucket!r} 非法(应 A/B/C/D)")


if __name__ == "__main__":
    unittest.main()
