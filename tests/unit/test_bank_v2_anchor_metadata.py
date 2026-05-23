# -*- coding: utf-8 -*-
"""
P0.1 BUG-B-T1 v118.35.0.37 · 守门测试 · recon_routes._apply_anchor_overrides

锁定 3 个契约:
  1. OCR snapshot 总是返回(无论是否有 override) → 前端 localStorage 预填用
  2. override 替换 final 值 · 但 anchor_overrides[].ocr 保留原 OCR 值(P0.3 历史详情对照用)
  3. 不传 override 时 · anchor_overrides 必须为空 dict(不污染 summary._anchor_overrides)
"""
import unittest

from recon_routes import _apply_anchor_overrides


class ApplyAnchorOverridesContractTests(unittest.TestCase):

    def test_no_override_returns_ocr_snapshot_and_empty_overrides(self):
        """P0.1 契约 · 不传 override 时 · OCR snapshot 仍返 · overrides dict 必须空"""
        final_stmt, final_gl_open, final_gl_close, final_stmt_close, ocr_snap, overrides = _apply_anchor_overrides(
            stmt_opening=1000.0, gl_opening=1010.0, gl_closing=2000.0, stmt_closing=2050.0,
            stmt_opening_override=None,
            gl_opening_override=None,
            gl_closing_override=None,
        )
        # 4 个 final 值跟 OCR 一致
        self.assertEqual(final_stmt, 1000.0)
        self.assertEqual(final_gl_open, 1010.0)
        self.assertEqual(final_gl_close, 2000.0)
        self.assertEqual(final_stmt_close, 2050.0)
        # OCR snapshot 总是返 4 个 anchor(BUG-FIX-T3 v118.35.0.44 加 stmt_closing)
        self.assertEqual(ocr_snap, {
            "stmt_opening": 1000.0,
            "gl_opening": 1010.0,
            "gl_closing": 2000.0,
            "stmt_closing": 2050.0,
        })
        # 不传 override → overrides 必须空(防污染 summary._anchor_overrides)
        self.assertEqual(overrides, {})

    def test_partial_override_only_replaces_specified_anchors(self):
        """P0.1 契约 · 只 override stmt_opening · 其它 3 个仍走 OCR · overrides 只记 stmt"""
        final_stmt, final_gl_open, final_gl_close, final_stmt_close, ocr_snap, overrides = _apply_anchor_overrides(
            stmt_opening=1000.0, gl_opening=1010.0, gl_closing=2000.0, stmt_closing=2050.0,
            stmt_opening_override=1500.0,
            gl_opening_override=None,
            gl_closing_override=None,
        )
        # 只 stmt 被替换 · 其它 3 个保留 OCR
        self.assertEqual(final_stmt, 1500.0)
        self.assertEqual(final_gl_open, 1010.0)
        self.assertEqual(final_gl_close, 2000.0)
        self.assertEqual(final_stmt_close, 2050.0)
        # OCR snapshot 仍保留所有 4 个 OCR 原值(给 P0.3 历史对照)
        self.assertEqual(ocr_snap, {
            "stmt_opening": 1000.0,
            "gl_opening": 1010.0,
            "gl_closing": 2000.0,
            "stmt_closing": 2050.0,
        })
        # overrides 只记 stmt · 含 ocr 原值 + user 输入值
        self.assertEqual(overrides, {
            "stmt_opening": {"ocr": 1000.0, "user": 1500.0},
        })

    def test_all_three_overrides_preserve_ocr_in_snapshot_and_overrides(self):
        """P0.1 契约 · 3 个全 override · OCR snapshot 仍是原 OCR · overrides 3 个全记 ocr+user 对照"""
        final_stmt, final_gl_open, final_gl_close, final_stmt_close, ocr_snap, overrides = _apply_anchor_overrides(
            stmt_opening=1000.0, gl_opening=1010.0, gl_closing=2000.0, stmt_closing=2050.0,
            stmt_opening_override=1500.5,
            gl_opening_override=1515.5,
            gl_closing_override=2500.5,
        )
        # 3 个 final 都被替换 · stmt_closing 没传 override 保留 OCR 原值
        self.assertEqual(final_stmt, 1500.5)
        self.assertEqual(final_gl_open, 1515.5)
        self.assertEqual(final_gl_close, 2500.5)
        self.assertEqual(final_stmt_close, 2050.0)
        # OCR snapshot 含全 4 个 anchor · 不能被 override 污染
        self.assertEqual(ocr_snap, {
            "stmt_opening": 1000.0,
            "gl_opening": 1010.0,
            "gl_closing": 2000.0,
            "stmt_closing": 2050.0,
        })
        self.assertEqual(overrides, {
            "stmt_opening": {"ocr": 1000.0, "user": 1500.5},
            "gl_opening": {"ocr": 1010.0, "user": 1515.5},
            "gl_closing": {"ocr": 2000.0, "user": 2500.5},
        })

    def test_all_four_overrides_including_stmt_closing(self):
        """BUG-FIX-T3 v118.35.0.44 契约 · 加第 4 个 anchor stmt_closing(客户反馈缺这个)
        4 个全 override 时 · OCR snapshot + overrides dict 都含 4 个 key
        """
        final_stmt, final_gl_open, final_gl_close, final_stmt_close, ocr_snap, overrides = _apply_anchor_overrides(
            stmt_opening=1000.0, gl_opening=1010.0, gl_closing=2000.0, stmt_closing=2050.0,
            stmt_opening_override=1500.5,
            gl_opening_override=1515.5,
            gl_closing_override=2500.5,
            stmt_closing_override=2555.5,
        )
        # 4 个 final 都被替换
        self.assertEqual(final_stmt, 1500.5)
        self.assertEqual(final_gl_open, 1515.5)
        self.assertEqual(final_gl_close, 2500.5)
        self.assertEqual(final_stmt_close, 2555.5)
        # OCR snapshot 必须含 4 个 anchor 原值
        self.assertEqual(ocr_snap, {
            "stmt_opening": 1000.0,
            "gl_opening": 1010.0,
            "gl_closing": 2000.0,
            "stmt_closing": 2050.0,
        })
        # overrides 4 个全记
        self.assertEqual(overrides, {
            "stmt_opening": {"ocr": 1000.0, "user": 1500.5},
            "gl_opening": {"ocr": 1010.0, "user": 1515.5},
            "gl_closing": {"ocr": 2000.0, "user": 2500.5},
            "stmt_closing": {"ocr": 2050.0, "user": 2555.5},
        })

    def test_stmt_closing_override_alone_does_not_touch_others(self):
        """BUG-FIX-T3 契约 · 只 override stmt_closing · 其它 3 个保留 OCR · overrides 只记 stmt_closing"""
        final_stmt, final_gl_open, final_gl_close, final_stmt_close, ocr_snap, overrides = _apply_anchor_overrides(
            stmt_opening=1000.0, gl_opening=1010.0, gl_closing=2000.0, stmt_closing=2050.0,
            stmt_opening_override=None, gl_opening_override=None, gl_closing_override=None,
            stmt_closing_override=2999.0,
        )
        self.assertEqual(final_stmt, 1000.0)
        self.assertEqual(final_gl_open, 1010.0)
        self.assertEqual(final_gl_close, 2000.0)
        self.assertEqual(final_stmt_close, 2999.0)
        self.assertEqual(overrides, {"stmt_closing": {"ocr": 2050.0, "user": 2999.0}})


if __name__ == "__main__":
    unittest.main()
