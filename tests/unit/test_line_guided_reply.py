# -*- coding: utf-8 -*-
"""引导框架(P2「听懂+对症引导」):没记账时按类别给贴身引导,不甩通用模板。

竞品标杆:发「ป้ายทะเบียน 103」→ 认出是车牌 + 给车相关示例。本测验确定性归类 + 池路由,
且通用 unknown/out_of_scope 会被替换成 guide_*(过 reply_pool 时贴身引导优先于语气层)。
"""

import unittest

from services.expense import replies


class GuidedKindTests(unittest.TestCase):
    def test_categories(self):
        cases = {
            "ป้ายทะเบียน 103": "guide_vehicle",
            "ทะเบียน กข 1234": "guide_vehicle",
            "โทรหาซัพ 0812345678": "guide_phone",
            "รอคิว 15 นาที": "guide_numnotmoney",
            "อายุ 25 ปี": "guide_numnotmoney",
            "เปิดร้าน 9 โมง": "guide_numnotmoney",
            "ซื้อทุเรียนที่ร้าน 711": "guide_store",
        }
        for text, kind in cases.items():
            self.assertEqual(replies.guided_kind(text), kind, text)

    def test_no_number_or_no_category_returns_none(self):
        for t in ["อากาศวันนี้เป็นไง", "เล่ามุกหน่อย", "ทะเบียนรถ", "สวัสดี"]:
            self.assertIsNone(replies.guided_kind(t), t)

    def test_pick_routes_unknown_to_guided(self):
        # pick 在 unknown/out_of_scope 时把通用替换成贴身引导。
        plate = replies.pick("unknown", "ป้ายทะเบียน 103", "th")
        self.assertIn("ทะเบียน", plate)
        self.assertIn("ค่าน้ำมัน", plate)  # 车相关示例
        # 中文车牌 → 中文贴身引导。
        self.assertIn("车牌", replies.pick("out_of_scope", "车牌 103", "zh"))

    def test_pick_generic_unknown_when_no_category(self):
        # 纯闲聊无类别 → 仍走通用 unknown(不强塞引导)。
        out = replies.pick("unknown", "อากาศวันนี้", "th")
        self.assertNotIn("ทะเบียน", out)


if __name__ == "__main__":
    unittest.main()
