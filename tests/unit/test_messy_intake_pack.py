# -*- coding: utf-8 -*-
"""乱料验收包守门(tests/fixtures/messy_intake_pack/ · IN-0a 常设制度)。

如同 pp30 金标:今后进料口任何改动必过本包。逐件断言预处理层(intake_prep.normalize_upload)
对真实"运输皮"的行为——解包/转换/诚实拒。产物由 _build_fixtures.py 生成并入库。"""

from __future__ import annotations

import io
import unittest
from pathlib import Path

from services.workorder import intake_prep as ip
from tests.fixtures.messy_intake_pack import _build_fixtures as build

_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "messy_intake_pack"


def _load(name: str) -> bytes:
    return (_DIR / name).read_bytes()


class PackPresentTests(unittest.TestCase):
    def test_pack_has_all_fixtures(self):
        for name in build._FILES:
            self.assertTrue((_DIR / name).exists(), f"缺乱料件: {name}")
        # ≥10 件的常设制度门槛。
        self.assertGreaterEqual(len(build._FILES), 10)

    def test_all_fixtures_under_blob_gate(self):
        for name in build._FILES:
            self.assertLess((_DIR / name).stat().st_size, 2_500_000, name)


class AcceptedTests(unittest.TestCase):
    """能进的料:登记件数符合预期。"""

    def test_normal_receipt(self):
        out = ip.normalize_upload("normal_receipt.jpg", _load("normal_receipt.jpg"))
        self.assertEqual([n.register for n in out], [True])

    def test_pos_summary_xlsx(self):
        out = ip.normalize_upload("pos_summary.xlsx", _load("pos_summary.xlsx"))
        self.assertEqual([n.register for n in out], [True])

    def test_multipage_pdf(self):
        out = ip.normalize_upload("multipage_5.pdf", _load("multipage_5.pdf"))
        self.assertEqual([n.register for n in out], [True])

    def test_thai_emoji_name_pdf(self):
        name = "ใบเสร็จ_🧾.pdf"
        out = ip.normalize_upload(name, _load(name))
        self.assertEqual([n.register for n in out], [True])

    def test_heic_converts_to_openable_jpeg(self):
        out = ip.normalize_upload("iphone_photo.heic", _load("iphone_photo.heic"))
        converts = [n for n in out if n.register]
        self.assertEqual(len(converts), 1)
        from PIL import Image

        self.assertEqual(Image.open(io.BytesIO(converts[0].content)).mode, "RGB")

    def test_nested_zip_expands_all_leaves(self):
        out = ip.normalize_upload("nested_2level.zip", _load("nested_2level.zip"))
        # inner(2 张收据) + 顶层 1 张 = 3 张叶子,全部登记。
        self.assertEqual(sum(1 for n in out if n.register), 3)


class RejectedTests(unittest.TestCase):
    """诚实拒的料:逐件点名 + 结构化码。"""

    def _reject(self, name, expect_code_substr, *, named=True, **kw):
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload(name, _load(name), **kw)
        self.assertIn(expect_code_substr, c.exception.code)
        # 逐件点名:context 必带 filename(zip 超限点到闯限的具体条目名,非包名)。
        self.assertTrue(c.exception.context.get("filename"))
        if named:
            self.assertEqual(c.exception.context.get("filename"), name)
        return c.exception

    def test_empty_file(self):
        self._reject("empty.jpg", "empty_file")

    def test_fake_extension(self):
        self._reject("fake_image.jpg", "fake_extension")

    def test_password_pdf_requires_password(self):
        e = self._reject("password_protected.pdf", "pdf_password_required")
        self.assertEqual(set(e.message_map()), {"th", "en", "zh", "ja"})

    def test_password_pdf_unlocks_with_password(self):
        out = ip.normalize_upload(
            "password_protected.pdf",
            _load("password_protected.pdf"),
            password=build.PDF_PASSWORD,
        )
        self.assertEqual([n.register for n in out], [True])

    def test_over_count_zip(self):
        self._reject("over_count.zip", "zip_limit", named=False)

    def test_unsupported_rar(self):
        self._reject("archive.rar", "unsupported_archive")


if __name__ == "__main__":
    unittest.main()
