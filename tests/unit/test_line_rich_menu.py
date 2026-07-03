# -*- coding: utf-8 -*-
"""LINE Rich Menu(6 区接线)单测:payload 几何合法不重叠满覆盖 + rm_* 路由到现有功能 + setup 幂等。"""

from __future__ import annotations

import unittest
from unittest import mock

from services.line_binding import line_rich_menu as rm


class _Ctx:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _overlap(a, b):
    return not (
        a["x"] + a["width"] <= b["x"]
        or b["x"] + b["width"] <= a["x"]
        or a["y"] + a["height"] <= b["y"]
        or b["y"] + b["height"] <= a["y"]
    )


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.p = rm.build_payload()
        self.areas = self.p["areas"]

    def test_size_and_count(self):
        self.assertEqual(self.p["size"], {"width": 2500, "height": 1686})
        self.assertEqual(len(self.areas), 6)

    def test_default_collapsed(self):
        # 默认折叠:不每次强制展开盖聊天。LINE 无折叠 webhook → 无法逐用户记忆,
        # 只能定默认。改回 True 前先确认产品确实要每次弹开。
        self.assertFalse(self.p["selected"])

    def test_within_bounds(self):
        for a in self.areas:
            b = a["bounds"]
            self.assertGreaterEqual(b["x"], 0)
            self.assertGreaterEqual(b["y"], 0)
            self.assertLessEqual(b["x"] + b["width"], 2500)
            self.assertLessEqual(b["y"] + b["height"], 1686)

    def test_no_overlap(self):
        bs = [a["bounds"] for a in self.areas]
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                self.assertFalse(_overlap(bs[i], bs[j]), f"{i}-{j} overlap")

    def test_full_coverage(self):
        total = sum(a["bounds"]["width"] * a["bounds"]["height"] for a in self.areas)
        self.assertEqual(total, 2500 * 1686)  # 无重叠 + 满面积 = 恰好铺满

    def test_per_row_splits_match_illustration(self):
        # 点击区列边界贴 v7 插画按钮位置(非均分):底排比上排更靠左(中间被猫+咖啡占位)。
        # 换背景图若按钮位置变了,这里会挂 → 提醒同步复核 _TOP_X/_BOT_X。
        by = {}
        for a in self.areas:
            act = a["action"]
            key = act.get("data") or act.get("type")
            by[key] = a["bounds"]
        top_mid_x = by["a=rm_summary"]["x"]  # 上排中格左边界
        bot_mid_x = by["a=rm_help"]["x"]  # 下排中格左边界
        self.assertEqual(top_mid_x, 720)
        self.assertEqual(bot_mid_x, 670)
        self.assertLess(bot_mid_x, top_mid_x)  # 底排整体左移
        # 角上两格贴齐画布边(相机顶左、官网底右)
        self.assertEqual(by["camera"]["x"], 0)
        self.assertEqual(by["a=rm_detail"]["x"], 0)
        proof = by["a=rm_proof"]
        self.assertEqual(proof["x"] + proof["width"], 2500)

    def test_action_types(self):
        types = [a["action"]["type"] for a in self.areas]
        self.assertEqual(types.count("camera"), 1)  # 拍票
        self.assertEqual(types.count("postback"), 4)  # 汇总/PDF/明细/帮助
        self.assertEqual(types.count("uri"), 1)  # 官网

    def test_postback_data_actions(self):
        datas = [a["action"].get("data") for a in self.areas if a["action"]["type"] == "postback"]
        self.assertEqual(set(datas), {"a=rm_summary", "a=rm_proof", "a=rm_detail", "a=rm_help"})

    def test_uri_is_website(self):
        uri = next(a["action"]["uri"] for a in self.areas if a["action"]["type"] == "uri")
        # 官网按钮必须带 openExternalBrowser=1:LINE 内置浏览器里 Google 登录会被
        # disallowed_useragent 拦死 → 让 LINE 用系统浏览器直接打开。
        self.assertTrue(uri.startswith("https://pearnly.com"))
        self.assertIn("openExternalBrowser=1", uri)


class PostbackRouteTests(unittest.TestCase):
    def _run(self, data):
        calls = {}
        with (
            mock.patch("core.db.get_cursor_rls", return_value=_Ctx()),
            mock.patch("core.workspace_context.default_workspace_id", return_value=1),
            mock.patch(
                "services.line_binding.line_expense_qa.reply_summary",
                side_effect=lambda *a, **k: calls.setdefault("summary", 1),
            ),
            mock.patch(
                "services.line_binding.line_expense_qa.reply_detail",
                side_effect=lambda *a, **k: calls.setdefault("detail", 1),
            ),
            mock.patch(
                "services.line_binding.line_proof.start",
                side_effect=lambda *a, **k: calls.setdefault("proof", 1),
            ),
            mock.patch(
                "services.line_binding.line_reply.reply_text_context",
                side_effect=lambda *a, **k: calls.setdefault("reply", 1),
            ),
        ):
            handled = rm.handle_postback({"tenant_id": "t"}, "rt", data, "th", "U1")
        return handled, calls

    def test_summary(self):
        handled, calls = self._run("a=rm_summary")
        self.assertTrue(handled)
        self.assertIn("summary", calls)

    def test_proof(self):
        handled, calls = self._run("a=rm_proof")  # 等同发「ขอ PDF เดือนนี้」
        self.assertTrue(handled)
        self.assertIn("proof", calls)

    def test_detail(self):
        handled, calls = self._run("a=rm_detail")
        self.assertTrue(handled)
        self.assertIn("detail", calls)

    def test_help(self):
        handled, calls = self._run("a=rm_help")
        self.assertTrue(handled)
        self.assertIn("reply", calls)

    def test_non_rm_postback_not_handled(self):
        # 卡片动作 postback(confirm/undo…)→ 不被菜单拦截,交回卡片分发。
        handled, calls = self._run("a=confirm&doc=D1")
        self.assertFalse(handled)
        self.assertEqual(calls, {})


class SetupTests(unittest.TestCase):
    def test_setup_idempotent_delete_then_create_upload_default(self):
        seq = []
        with (
            mock.patch.object(
                rm, "_list_menus", return_value=[{"name": rm.MENU_NAME, "richMenuId": "OLD"}]
            ),
            mock.patch.object(
                rm, "_delete_menu", side_effect=lambda i: seq.append(("del", i)) or True
            ),
            mock.patch.object(
                rm.line_client,
                "create_rich_menu",
                side_effect=lambda p: seq.append(("create",)) or "NEW",
            ),
            mock.patch.object(
                rm, "_upload_image", side_effect=lambda *a, **k: seq.append(("up",)) or True
            ),
            mock.patch.object(
                rm, "_set_default", side_effect=lambda i: seq.append(("def", i)) or True
            ),
            mock.patch("builtins.open", mock.mock_open(read_data=b"PNGDATA")),
        ):
            rid = rm.setup_default_menu()
        self.assertEqual(rid, "NEW")
        self.assertIn(("del", "OLD"), seq)  # 幂等:先删旧同名
        self.assertLess(seq.index(("del", "OLD")), seq.index(("create",)))  # 删在建前
        self.assertIn(("up",), seq)
        self.assertIn(("def", "NEW"), seq)  # 设默认(全用户生效)

    def test_setup_missing_image_returns_none(self):
        with mock.patch("builtins.open", side_effect=OSError("no file")):
            self.assertIsNone(rm.setup_default_menu())

    def test_setup_jpeg_uploads_with_jpeg_mime(self):
        captured = {}
        with (
            mock.patch.object(rm, "_list_menus", return_value=[]),
            mock.patch.object(rm.line_client, "create_rich_menu", return_value="NEW"),
            mock.patch.object(
                rm,
                "_upload_image",
                side_effect=lambda rid, img, ct: captured.update(ct=ct) or True,
            ),
            mock.patch.object(rm, "_set_default", return_value=True),
            mock.patch("builtins.open", mock.mock_open(read_data=b"JPEGDATA")),
        ):
            rm.setup_default_menu(image_path="/x/menu.jpg")
        self.assertEqual(captured.get("ct"), "image/jpeg")


if __name__ == "__main__":
    unittest.main()
