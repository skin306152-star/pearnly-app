# -*- coding: utf-8 -*-
"""回归守门:录入工作台复核改字段必须真持久化,不能凭空蒸发(连导出/推 ERP 都用旧值)。

血泪:旧手风琴 dms-intake-review.ts 的保存曾退回"只弹 toast"假保存。M2 步③换成复核台
console(dms-intake-review-console.ts)后,契约不变但机制变了:遮罩改字段经 onFieldEdit
实时写回 IV.results[fi].invoices[ii].fields,步④ persistAllEdits 再把 IV 的改值 PUT
到 /api/history 落库。此测试钉住这条链,防再退回假保存。
"""

import re
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src" / "home"
_CONSOLE = _SRC / "dms-intake-review-console.ts"
_SUBMIT = _SRC / "dms-intake-invoice-submit.ts"


class SavePersistsRegressionTests(unittest.TestCase):
    def test_edit_writes_back_to_iv(self):
        # 步③遮罩改字段 → onFieldEdit 实时写回 IV.results[..].invoices[..].fields。
        src = _CONSOLE.read_text(encoding="utf-8")
        self.assertIn("onFieldEdit", src, "步③应接 onFieldEdit 写回口")
        self.assertRegex(
            src, r"\.fields\[[^\]]+\]\s*=", "改字段应实时写回 IV.results[..].fields(非假保存)"
        )

    def test_persist_fn_puts_to_history_api(self):
        # 步④ persistAllEdits 把 IV 改值 PUT 落库(按各张发票自己的 history_id)。
        src = _SUBMIT.read_text(encoding="utf-8")
        self.assertIn("persistAllEdits", src, "步④应有 persistAllEdits 落库")
        self.assertIn("/api/history/", src, "持久化未打到 /api/history")
        self.assertRegex(src, r"method:\s*'PUT'", "持久化应为 PUT")
        self.assertIn("history_id", src, "应按各张发票自己的 history_id 写")


if __name__ == "__main__":
    unittest.main()
