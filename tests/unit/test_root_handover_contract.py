# -*- coding: utf-8 -*-
"""根目录活交接( HANDOVER_TO_NEXT_WINDOW.md )机械契约(2026-08-27)。

根因:根目录交接虽早在正文标"已归档",但第 138 行仍写着
"always on master · push 用户授权后让用户自己 `! git push origin master`" —— 与 AGENTS.md
现行口径(施工窗口自验→commit→push origin master→盯本人 SHA 的 CI 全绿→精确 SHA 部署)直接冲突,
于是每个新窗口都重复问"要不要用户自己 push"。根治:历史正文挪进 docs/archive,根文件重写成
极短现行入口指针。

本闸锁两根桩(机械、防回退,不看人肉):
  ① 根目录活交接不许再出现"让用户自己 push / 不 push master"的反规则;
  ② 现行精确 SHA 部署闭环的关键锚点必须存在(git push origin master / rev-parse HEAD /
     github.sha / TARGET_SHA / ActiveEnterTimestamp / deploy),并指向唯一活地图(STATE + AGENTS)。
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOVER = REPO_ROOT / "HANDOVER_TO_NEXT_WINDOW.md"
ARCHIVED = REPO_ROOT / "docs" / "archive" / "HANDOFF-2026-05-23-银行对账M4-收尾.md"

# 反规则触发词:仅当"让用户自己 push / 不 push master"作为**指令**出现才算犯。
# 注意:权威口径的否定式"用户不需要自己 push"不含连续的"用户自己",不会被误伤。
_FORBIDDEN = [
    "用户授权后让用户",
    "让用户自己",
    "用户自己 push",
    "用户自己去 push",
    "! git push",
    "不 push master",
    "不要 push master",
    "不能 push master",
    "不可以 push master",
    "不让用户 push",
]

# 现行精确 SHA 部署闭环锚点。
_REQUIRED_MARKERS = [
    "docs/deployment/CLOUD_RUN.md",
    "docs/deployment/MIGRATION_STATUS.md",
    "SHA",
    "digest",
    "revision",
]


class RootHandoverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = HANDOVER.read_text(encoding="utf-8")

    def test_no_user_self_push_antirule(self):
        hits = [m for m in _FORBIDDEN if m in self.text]
        self.assertEqual(
            hits,
            [],
            f"根目录活交接仍含让用户自己 push / 不 push master 的旧规:{hits}",
        )

    def test_exact_sha_deploy_loop_anchors_present(self):
        missing = [m for m in _REQUIRED_MARKERS if m not in self.text]
        self.assertEqual(
            missing,
            [],
            f"根目录活交接缺现行精确 SHA 部署闭环锚点:{missing}",
        )

    def test_points_to_live_map_and_archive(self):
        # 活地图指向 + 历史正文挪档位置,新窗口不再拿旧正文当现状读。
        self.assertIn("docs/project/STATE_PEARNLY.md", self.text)
        self.assertIn("AGENTS.md", self.text)
        self.assertIn("docs/archive/HANDOFF-2026-05-23-银行对账M4-收尾.md", self.text)

    def test_historical_body_preserved_in_archive(self):
        # 历史正文确实挪进了 docs/archive(银行对账 M4 的关键内容还在,只是不再冒充现行)。
        archived_text = ARCHIVED.read_text(encoding="utf-8")
        for marker in ("银行对账", "KBank 8477", "_parse_stmt_text_coords"):
            self.assertIn(marker, archived_text, f"归档文件缺历史正文标记:{marker}")


if __name__ == "__main__":
    unittest.main()
