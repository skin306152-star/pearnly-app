# -*- coding: utf-8 -*-
"""回归守门:录入工作台复核"保存修改"必须真持久化,不能退回"只弹 toast"假保存。

血泪:dms-intake-review.ts 的 `.dx-save-one` 处理曾是 `showToast(...)` 一行,改了又
冒;用户改完字段以为存了,实际凭空蒸发(连导出/推 ERP 都用旧值)。此测试钉住:保存
分支必须调持久化函数,且该函数对 /api/history 发 PUT。结构级守门,防再回退。
"""

import re
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src" / "home" / "dms-intake-review.ts"


class SavePersistsRegressionTests(unittest.TestCase):
    def setUp(self):
        self.src = _SRC.read_text(encoding="utf-8")

    def test_save_button_calls_persist_not_just_toast(self):
        # 取 `.dx-save-one` 处理块,断言它调 saveOpenFileEdits(而非裸 showToast 假保存)
        m = re.search(r"closest\('\.dx-save-one'\)\)\s*\{(.+?)\}", self.src, re.S)
        self.assertIsNotNone(m, "找不到 .dx-save-one 处理块")
        block = m.group(1)
        self.assertIn("saveOpenFileEdits", block, "保存按钮未调持久化函数(疑回退假 toast)")
        self.assertNotRegex(
            block.replace("saveOpenFileEdits", ""),
            r"showToast\(",
            "保存按钮分支不应只弹 toast",
        )

    def test_persist_fn_puts_to_history_api(self):
        m = re.search(r"async function saveOpenFileEdits\b(.+?)\n\}", self.src, re.S)
        self.assertIsNotNone(m, "找不到 saveOpenFileEdits 定义")
        body = m.group(1)
        self.assertIn("/api/history/", body, "持久化未打到 /api/history")
        self.assertIn("'PUT'", body, "持久化应为 PUT")
        self.assertIn("history_id", body, "应按各张发票自己的 history_id 写")


if __name__ == "__main__":
    unittest.main()
