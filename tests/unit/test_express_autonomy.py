# -*- coding: utf-8 -*-
"""Express 自治级别单测(纯函数 · 无网络)。

钉死:manual 档把"本会入队(EXPRESS_QUEUED)"的 express 结果降级 autonomy_hold;
standard/auto 不改;非 express / 已人工 / 短路失败一律原样;默认 standard。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.autonomy import (  # noqa: E402
    AUTONOMY_HOLD,
    apply_autonomy_auto,
    autonomy_level,
)
from services.erp.express_push.enqueue import MANUAL_PREFIX, QUEUED_SENTINEL  # noqa: E402


def _ep(level=None, adapter="express"):
    cfg = {"account_set": "DATAT"}
    if level is not None:
        cfg["autonomy"] = level
    return {"id": "ep-1", "adapter": adapter, "config": cfg}


def _queued_result():
    return {
        "success": False,
        "error_msg": QUEUED_SENTINEL,
        "http_status": 202,
        "request_body": {"account_set": "DATAT", "lines": []},
        "response_body": json.dumps(
            {"queued": True, "preflight": [{"key": "feature", "status": "ok"}]}
        ),
        "adapter": "express",
    }


class LevelTests(unittest.TestCase):
    def test_default_standard(self):
        self.assertEqual(autonomy_level({}), "standard")
        self.assertEqual(autonomy_level({"autonomy": ""}), "standard")
        self.assertEqual(autonomy_level({"autonomy": "bogus"}), "standard")
        self.assertEqual(autonomy_level(None), "standard")

    def test_valid_levels(self):
        self.assertEqual(autonomy_level({"autonomy": "manual"}), "manual")
        self.assertEqual(autonomy_level({"autonomy": "AUTO"}), "auto")
        self.assertEqual(autonomy_level({"autonomy": " Standard "}), "standard")


class ApplyTests(unittest.TestCase):
    def test_manual_downgrades_queued_to_hold(self):
        out = apply_autonomy_auto(_queued_result(), _ep("manual"))
        self.assertFalse(out["success"])
        self.assertEqual(out["error_msg"], f"{MANUAL_PREFIX}: {AUTONOMY_HOLD}")
        body = json.loads(out["response_body"])
        self.assertEqual(body["queued"], False)
        self.assertEqual(body["manual_reason"], AUTONOMY_HOLD)
        # payload 留存 + 体检结果保留。
        self.assertEqual(out["request_body"]["account_set"], "DATAT")
        self.assertIn("preflight", body)

    def test_standard_unchanged(self):
        r = _queued_result()
        self.assertEqual(apply_autonomy_auto(r, _ep("standard")), r)

    def test_auto_unchanged_for_queue(self):
        r = _queued_result()
        self.assertEqual(apply_autonomy_auto(r, _ep("auto")), r)

    def test_default_level_unchanged(self):
        r = _queued_result()
        self.assertEqual(apply_autonomy_auto(r, _ep(None)), r)

    def test_non_express_untouched(self):
        r = _queued_result()
        self.assertEqual(apply_autonomy_auto(r, _ep("manual", adapter="mrerp")), r)

    def test_already_manual_untouched(self):
        r = {
            "success": False,
            "error_msg": f"{MANUAL_PREFIX}: low_confidence:x",
            "adapter": "express",
        }
        self.assertEqual(apply_autonomy_auto(r, _ep("manual")), r)

    def test_short_circuit_failed_untouched(self):
        r = {"success": False, "error_msg": "ERR_EXPRESS_DISABLED", "adapter": "express"}
        self.assertEqual(apply_autonomy_auto(r, _ep("manual")), r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
