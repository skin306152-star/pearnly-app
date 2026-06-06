# -*- coding: utf-8 -*-
"""图片上传存储守门:Pillow 验真 / 2MB 上限 / uuid 落地 / 沙盒路径(防穿越)/ 外链不解析。"""

import io
import os
import shutil
import tempfile
import unittest

from PIL import Image

from services.imaging import image_store as st


def _png(w=20, h=10, fmt="PNG") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (10, 20, 30)).save(buf, fmt)
    return buf.getvalue()


class ImageStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["IMAGE_STORAGE_DIR"] = self.tmp

    def tearDown(self):
        os.environ.pop("IMAGE_STORAGE_DIR", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_valid_png(self):
        res = st.save_image("t1", _png())
        self.assertTrue(res["url"].startswith("/api/uploads/image/t1/"))
        self.assertTrue(res["url"].endswith(".png"))
        self.assertEqual((res["width"], res["height"]), (20, 10))
        self.assertTrue(st.local_path_from_url(res["url"]).is_file())

    def test_uuid_filename_not_client_supplied(self):
        res = st.save_image("t1", _png())
        name = res["url"].rsplit("/", 1)[-1]
        self.assertEqual(len(name), 36)  # 32 hex + ".png"

    def test_reject_empty(self):
        self.assertRaisesRegex(st.UploadError, "empty_file", st.save_image, "t", b"")

    def test_reject_not_image(self):
        with self.assertRaises(st.UploadError) as c:
            st.save_image("t", b"definitely not an image")
        self.assertEqual(c.exception.code, "not_an_image")

    def test_reject_too_large(self):
        big = b"\x89PNG" + b"0" * (st.MAX_BYTES + 1)
        with self.assertRaises(st.UploadError) as c:
            st.save_image("t", big)
        self.assertEqual(c.exception.code, "file_too_large")

    def test_reject_unsupported_format(self):
        with self.assertRaises(st.UploadError) as c:
            st.save_image("t", _png(fmt="GIF"))
        self.assertEqual(c.exception.code, "unsupported_type")

    def test_jpeg_and_webp_ok(self):
        self.assertTrue(st.save_image("t", _png(fmt="JPEG"))["url"].endswith(".jpg"))
        self.assertTrue(st.save_image("t", _png(fmt="WEBP"))["url"].endswith(".webp"))

    def test_traversal_blocked(self):
        self.assertIsNone(st.local_path("t1", "../../../etc/passwd"))

    def test_local_path_basename_only(self):
        res = st.save_image("t1", _png())
        name = res["url"].rsplit("/", 1)[-1]
        # 带目录前缀也只取 basename,仍解析到同一文件。
        self.assertIsNotNone(st.local_path("t1", "sub/" + name))

    def test_external_url_not_resolved(self):
        self.assertIsNone(st.local_path_from_url("https://evil.example/x.png"))
        self.assertIsNone(st.local_path_from_url(None))
        self.assertIsNone(st.local_path_from_url("/other/path/x.png"))

    def test_media_type_mapping(self):
        self.assertEqual(st.media_type_for("png"), "image/png")
        self.assertEqual(st.media_type_for("jpg"), "image/jpeg")


if __name__ == "__main__":
    unittest.main()
