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

    def test_accepts_optional_target_sha_as_argv(self):
        # CI deploy job 传本次 push 的 40-hex SHA 作 $1 → TARGET_SHA(不传 = 旧语义)
        self.assertIn('TARGET_SHA="${1:-}"', GIT_DEPLOY_SH)

    def test_serializes_with_flock_bounded_wait(self):
        # flock 串行化并发部署 · 等锁上限拉足(≥ 一次完整部署最坏耗时)·
        # 队列里较新的请求不能因锁忙过早退出(否则那笔新 SHA 被静默丢弃)
        self.assertIn("LOCK=/var/lock/mrpilot-deploy.lock", GIT_DEPLOY_SH)
        self.assertIn('exec 9>"$LOCK"', GIT_DEPLOY_SH)
        self.assertIn('flock -w "$LOCK_WAIT" 9', GIT_DEPLOY_SH)
        self.assertIn("LOCK_WAIT=900", GIT_DEPLOY_SH)

    def test_exact_sha_guard_skips_superseded_deploy(self):
        # 请求精确 SHA 但 fetch 后 master 已领先 → 记 SUPERSEDED 并退出,绝不
        # 把未审查的更新 SHA 当目标部署(reset --hard 到别的 commit)。
        self.assertIn(
            'if [ -n "$TARGET_SHA" ] && [ "$NEW_HEAD" != "$TARGET_SHA" ]; then', GIT_DEPLOY_SH
        )
        self.assertIn("SUPERSEDED", GIT_DEPLOY_SH)
        self.assertIn("exit 0", GIT_DEPLOY_SH)

    def test_lock_acquired_before_fetch(self):
        # 锁必须在 fetch/reset 之前拿到:同一时刻只有一个 git-deploy 在跑,
        # 且拿到锁后的 fetch 才反映「锁内」的最新 master。
        lock_idx = GIT_DEPLOY_SH.index('flock -w "$LOCK_WAIT" 9')
        fetch_idx = GIT_DEPLOY_SH.index('git fetch "$REMOTE" "$BRANCH"')
        self.assertLess(lock_idx, fetch_idx)

    def test_startup_writes_this_exact_text(self):
        from services import startup

        self.assertIs(startup.GIT_DEPLOY_SH, GIT_DEPLOY_SH)


if __name__ == "__main__":
    unittest.main()
