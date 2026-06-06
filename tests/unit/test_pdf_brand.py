# -*- coding: utf-8 -*-
"""发票品牌图渲染守门:外链/缺图优雅跳过,本地图返 flowable。"""

import io
import os
import shutil
import tempfile
import unittest

from PIL import Image

from services.sales import pdf_brand
from services.imaging import image_store as st


class _Spacer:
    def __init__(self, *a):
        pass


class PdfBrandGracefulTests(unittest.TestCase):
    def test_external_url_returns_none(self):
        self.assertIsNone(pdf_brand.brand_image("https://x.com/y.png", 50, 20))

    def test_none_and_missing_return_none(self):
        self.assertIsNone(pdf_brand.brand_image(None, 50, 20))
        self.assertIsNone(pdf_brand.brand_image("/not/a/local/upload.png", 50, 20))

    def test_logo_flowables_empty_without_logo(self):
        self.assertEqual(pdf_brand.logo_flowables({"name": "X"}, 1, _Spacer), [])
        self.assertEqual(pdf_brand.logo_flowables(None, 1, _Spacer), [])


class PdfBrandLocalImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["IMAGE_STORAGE_DIR"] = self.tmp
        buf = io.BytesIO()
        Image.new("RGB", (80, 40), (16, 185, 129)).save(buf, "PNG")
        self.url = st.save_image("t1", buf.getvalue())["url"]

    def tearDown(self):
        os.environ.pop("IMAGE_STORAGE_DIR", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_local_image_returns_flowable(self):
        from reportlab.platypus import Image as RLImage

        img = pdf_brand.brand_image(self.url, 50, 20)
        self.assertIsInstance(img, RLImage)

    def test_logo_flowables_present_with_logo(self):
        from reportlab.lib.units import mm
        from reportlab.platypus import Spacer

        out = pdf_brand.logo_flowables({"logo_url": self.url}, mm, Spacer)
        self.assertEqual(len(out), 2)


if __name__ == "__main__":
    unittest.main()
