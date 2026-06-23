# -*- coding: utf-8 -*-
"""守门测试 · 端点 success/failure 计数口径(铁律 #3/#12 单一状态源)。

回归:Express 留人工(status='manual')曾因 `final_status != "failed"` 被算成端点成功数,
掩盖缺科目/低置信/账套拒的真失败。counts_as_endpoint_success 把口径收成单一函数(push_retry)。
"""

import unittest

from core import db  # noqa: F401 · 先 import db 再 import push_store(避免 partial-init 循环)
from services.erp.push_store import counts_as_endpoint_success as ok


class EndpointSuccessCaliberTests(unittest.TestCase):
    def test_success_states_count_as_success(self):
        self.assertTrue(ok("success"))
        self.assertTrue(ok("skipped_dup"))

    def test_failed_and_manual_count_as_failure(self):
        self.assertFalse(ok("failed"))
        self.assertFalse(ok("manual"))

    def test_pending_is_not_failure(self):
        # 出站排队中,落定前不计失败(ack 时再计)。
        self.assertTrue(ok("pending"))

    def test_none_is_not_failure(self):
        self.assertTrue(ok(None))


if __name__ == "__main__":
    unittest.main()
