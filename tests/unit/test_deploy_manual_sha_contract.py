# -*- coding: utf-8 -*-
"""/internal/deploy/manual?sha= 契约:校验 + argv 传递 + 无 shell 注入。

CI deploy job 拿 DEPLOY_TOKEN 调这个端点做精确部署。三件事不能漂:
  1. 非法 sha(非 40 位 hex)必须 422 —— 不让脏值进部署命令
  2. sha 经 bash -c 的位置参数($1)传给 git-deploy.sh —— 值不进命令字符串 → 注入面为零
  3. 不带 sha 的旧调用(webhook 时代的手动救援)语义不变 —— 部署当前 master
"""

import unittest
from unittest import mock

from fastapi import HTTPException

from routes.admin_diagnostics_routes import _launch_deploy, _validate_target_sha

HEX40 = "c635a5bfb9a807c504162a416c1a09d07745bb46"


class ValidateTargetShaTest(unittest.TestCase):
    def test_none_passes_through(self):
        self.assertIsNone(_validate_target_sha(None))

    def test_valid_40_hex_passes(self):
        self.assertEqual(_validate_target_sha(HEX40), HEX40)

    def test_uppercase_hex_normalized(self):
        self.assertEqual(_validate_target_sha(HEX40.upper()), HEX40)

    def test_short_sha_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            _validate_target_sha(HEX40[:7])
        self.assertEqual(ctx.exception.status_code, 422)

    def test_non_hex_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            _validate_target_sha("g" * 40)
        self.assertEqual(ctx.exception.status_code, 422)

    def test_empty_string_rejected(self):
        with self.assertRaises(HTTPException):
            _validate_target_sha("")


class LaunchDeployArgvPropagationTest(unittest.TestCase):
    def _popen(self):
        patcher = mock.patch("subprocess.Popen")
        popen = patcher.start()
        self.addCleanup(patcher.stop)
        return popen

    def test_no_target_keeps_legacy_argv_shape(self):
        popen = self._popen()
        _launch_deploy(1)
        argv = popen.call_args[0][0]
        self.assertEqual(argv[0], "bash")
        self.assertEqual(argv[1], "-c")
        self.assertIn("bash /opt/mrpilot/git-deploy.sh >>", argv[2])
        self.assertEqual(len(argv), 3)  # 无 sha → 无 $0/$1 位置参数

    def test_target_passed_as_positional_argv_not_in_string(self):
        popen = self._popen()
        _launch_deploy(1, target_sha=HEX40)
        argv = popen.call_args[0][0]
        cmd = argv[2]
        # 命令字符串里只有 "$1" 引用 · sha 本身绝不出现在字符串里(注入面 = 0)
        self.assertNotIn(HEX40, cmd)
        self.assertIn('"$1"', cmd)
        # sha 经 exec argv 传递 · bash -c 的 $0=_,$1=<sha>
        self.assertEqual(argv[3:], ["_", HEX40])

    def test_webhook_and_manual_preserve_sleep_deltas(self):
        popen = self._popen()
        _launch_deploy(3)  # webhook: sleep 3
        self.assertIn("sleep 3 &&", popen.call_args[0][0][2])
        popen.reset_mock()
        _launch_deploy(1)  # manual: sleep 1
        self.assertIn("sleep 1 &&", popen.call_args[0][0][2])

    def test_detached_session_flags_preserved(self):
        popen = self._popen()
        _launch_deploy(1, target_sha=HEX40)
        kwargs = popen.call_args[1]
        self.assertTrue(kwargs["close_fds"])
        self.assertTrue(kwargs["start_new_session"])


if __name__ == "__main__":
    unittest.main()
