# -*- coding: utf-8 -*-
"""git-deploy.sh 模板契约:内容抽成独立模块后不许悄悄变形。

这段文本会被 app 启动时写到生产磁盘当部署脚本跑,漂一个字都可能让 push 上不了线。
"""

import unittest

from services.deploy_script import GIT_DEPLOY_SH


class GitDeployScriptTest(unittest.TestCase):
    def test_is_bash_script(self):
        self.assertTrue(GIT_DEPLOY_SH.startswith("#!/bin/bash"))

    def test_keeps_rollback_and_health_check(self):
        # 回滚目标取远端追踪分支而非本地 HEAD;健康检查是回滚的触发判据。
        self.assertIn('PREV_HEAD=$(git rev-parse "$REMOTE/$BRANCH"', GIT_DEPLOY_SH)
        self.assertIn("HEALTH_URL=http://localhost:7860/api/health", GIT_DEPLOY_SH)

    def test_startup_writes_this_exact_text(self):
        from services import startup

        self.assertIs(startup.GIT_DEPLOY_SH, GIT_DEPLOY_SH)


if __name__ == "__main__":
    unittest.main()
