# -*- coding: utf-8 -*-
"""L1/L2 超时常量 env 化守门:默认 60,OCR_L1/L2_TIMEOUT_SECONDS 可覆盖。

常量在 import 期读 env(与 layer3_fallback.OCR_L3_TIMEOUT_SECONDS 同款),测试用
importlib.reload 模拟进程启动时的 env;tearDown 重载复位,不污染其它测试。
"""

import importlib
import unittest
from unittest import mock

from services.ocr import layer1_base as l1
from services.ocr import layer2_structure as l2

# 测试期间常驻假 env 一律清掉,只留被测键
_ENV_KEYS = ("OCR_L1_TIMEOUT_SECONDS", "OCR_L2_TIMEOUT_SECONDS")


class LayerTimeoutEnvTests(unittest.TestCase):
    def tearDown(self):
        # 常量在 import 期读 env:重载恢复默认,避免带覆盖值跑进后续测试
        importlib.reload(l1)
        importlib.reload(l2)
        super().tearDown()

    def test_default_timeout_is_60(self):
        with mock.patch.dict("os.environ", {k: "" for k in _ENV_KEYS}):
            importlib.reload(l1)
            importlib.reload(l2)
        self.assertEqual(l1.DEFAULT_TIMEOUT_SECONDS, 60)
        self.assertEqual(l2.DEFAULT_TIMEOUT_SECONDS, 60)

    def test_env_override_wins(self):
        with mock.patch.dict(
            "os.environ", {"OCR_L1_TIMEOUT_SECONDS": "120", "OCR_L2_TIMEOUT_SECONDS": "90"}
        ):
            importlib.reload(l1)
            importlib.reload(l2)
            self.assertEqual(l1.DEFAULT_TIMEOUT_SECONDS, 120)
            self.assertEqual(l2.DEFAULT_TIMEOUT_SECONDS, 90)


if __name__ == "__main__":
    unittest.main()
