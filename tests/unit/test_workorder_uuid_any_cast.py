#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工单读模型的 uuid 数组查询必须 ::uuid[] 转型(回归守门)。

根因(2026-07-14 MC3 本地彩排抓到,与 POS catalog 2026-06-07 同类):psycopg2 把 Python str
列表适配成 text[],而 work_order_id / purchase_docs.id 是 uuid;`uuid = ANY(text[])` 无隐式
转换 → "operator does not exist: uuid = text" → review-queue 整个 500(收件箱打不开)。
review_feed 上线时队列为空 ANY 短路没炸,首个真 review 工单一到即炸。修法 = `ANY(%s::uuid[])`。
本测试静态钉死 review_feed / pnd_prep 两处,防复发。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_WORKORDER = Path(__file__).resolve().parents[2] / "services" / "workorder"
_UUID_FILES = (_WORKORDER / "review_feed.py", _WORKORDER / "steps" / "pnd_prep.py")


class WorkorderUuidCastTest(unittest.TestCase):
    def test_no_bare_any_on_uuid_columns(self):
        for path in _UUID_FILES:
            src = path.read_text(encoding="utf-8")
            bad = re.findall(r"ANY\(%s\)(?!::uuid)", src)
            self.assertEqual(
                bad,
                [],
                f"{path.name} 有未转型的 ANY(%s) → uuid 列需 ANY(%s::uuid[])(否则真数据一到整路 500)",
            )

    def test_uuid_casts_present(self):
        counts = {
            p.name: len(re.findall(r"ANY\(%s::uuid\[\]\)", p.read_text(encoding="utf-8")))
            for p in _UUID_FILES
        }
        self.assertGreaterEqual(counts["review_feed.py"], 2, f"实得 {counts}")
        self.assertGreaterEqual(counts["pnd_prep.py"], 1, f"实得 {counts}")


if __name__ == "__main__":
    unittest.main()
