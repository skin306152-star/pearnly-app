# -*- coding: utf-8 -*-
"""图片上传存储守门:Pillow 验真 / 归一化(EXIF 转正·长边 1600·剥元数据)/ 25MB 上限 /
uuid 落地 / 沙盒路径(防穿越)/ 外链不解析。"""

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

    def test_reject_corrupt_png_as_upload_error(self):
        # 回归(prod 500):合法 PNG 头但 IDAT 数据损坏 → Pillow verify() 抛 SyntaxError。
        # 必须归为 UploadError(→422),绝不能冒泡成未处理异常(→500)。
        raw = bytearray(_png(40, 40))
        idat = raw.find(b"IDAT")
        raw[idat + 6] ^= 0xFF  # 篡改 IDAT 数据 → CRC 不匹配
        with self.assertRaises(st.UploadError) as c:
            st.save_image("t", bytes(raw))
        self.assertEqual(c.exception.code, "not_an_image")

    def test_reject_too_large(self):
        big = b"\x89PNG" + b"0" * (st.MAX_BYTES + 1)
        with self.assertRaises(st.UploadError) as c:
            st.save_image("t", big)
        self.assertEqual(c.exception.code, "file_too_large")

    def test_other_formats_normalized_not_rejected(self):
        # 2026-08-04 拍板:不设格式白名单(手机相册什么都有)。非核心格式落 JPEG/PNG。
        res = st.save_image("t", _png(fmt="GIF"))
        self.assertTrue(res["url"].endswith(".jpg"))
        self.assertEqual((res["width"], res["height"]), (20, 10))

    def test_jpeg_and_webp_ok(self):
        self.assertTrue(st.save_image("t", _png(fmt="JPEG"))["url"].endswith(".jpg"))
        self.assertTrue(st.save_image("t", _png(fmt="WEBP"))["url"].endswith(".webp"))

    def test_huge_photo_downscaled_to_max_edge(self):
        res = st.save_image("t", _png(4000, 3000, fmt="JPEG"))
        self.assertEqual((res["width"], res["height"]), (1600, 1200))
        with Image.open(st.local_path_from_url(res["url"])) as im:
            self.assertEqual(im.size, (1600, 1200))

    def test_alpha_preserved_as_png(self):
        buf = io.BytesIO()
        Image.new("RGBA", (20, 10), (10, 20, 30, 0)).save(buf, "PNG")
        res = st.save_image("t", buf.getvalue())
        self.assertTrue(res["url"].endswith(".png"))
        with Image.open(st.local_path_from_url(res["url"])) as im:
            self.assertEqual(im.convert("RGBA").getpixel((0, 0))[3], 0)

    def test_exif_orientation_applied_and_stripped(self):
        # 手机竖拍常见:像素横放 + EXIF Orientation=6(顺时针转 90°)。归一化必须把方向
        # 落实成真像素(缩略图/PDF 不吃 EXIF),并且不把整包 EXIF(含 GPS)带到落盘文件。
        buf = io.BytesIO()
        im = Image.new("RGB", (40, 20), (10, 20, 30))
        exif = Image.Exif()
        exif[274] = 6  # Orientation
        im.save(buf, "JPEG", exif=exif)
        res = st.save_image("t", buf.getvalue())
        self.assertEqual((res["width"], res["height"]), (20, 40))
        with Image.open(st.local_path_from_url(res["url"])) as out:
            self.assertEqual(dict(out.getexif()), {})

    def test_heic_accepted_when_plugin_available(self):
        try:
            import pillow_heif  # noqa: F401
        except ImportError:
            self.skipTest("pillow-heif not installed")
        from services.imaging.heif import register_heif

        buf = io.BytesIO()
        register_heif()
        Image.new("RGB", (30, 20), (10, 20, 30)).save(buf, "HEIF")
        res = st.save_image("t", buf.getvalue())
        self.assertTrue(res["url"].endswith(".jpg"))
        self.assertEqual((res["width"], res["height"]), (30, 20))

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

    def test_delete_image_removes_file(self):
        res = st.save_image("t1", _png())
        name = res["url"].rsplit("/", 1)[-1]
        path = st.local_path("t1", name)
        self.assertTrue(path.is_file())
        self.assertTrue(st.delete_image("t1", name))
        self.assertFalse(path.exists())

    def test_delete_image_missing_file_is_idempotent(self):
        self.assertTrue(st.delete_image("t1", "does-not-exist.png"))

    def test_delete_image_traversal_blocked(self):
        # 沙盒逃逸(basename 剥掉 ../ 后仍在 root 下就正常删;真逃逸场景是 tenant_id 本身
        # 带 ../ —— basename 只清洗 name,tenant_id 段必须自己撑住)。
        self.assertFalse(st.delete_image("../../etc", "passwd"))

    def test_delete_image_does_not_touch_other_tenant(self):
        res = st.save_image("t1", _png())
        name = res["url"].rsplit("/", 1)[-1]
        st.delete_image("t2", name)  # 别的租户同名文件不存在 → 幂等成功但不该删到 t1 的
        self.assertTrue(st.local_path("t1", name).is_file())


class HeifRegisterTests(unittest.TestCase):
    """register_heif 幂等:重复调用不炸、不重复挂 opener,HEIC 解不开的语义由上层兜。"""

    def test_register_is_idempotent(self):
        from services.imaging.heif import register_heif

        register_heif()
        register_heif()  # 第二次:扩展表已带 .heic → 幂等短路,不该抛
        self.assertIn(".heic", Image.registered_extensions())

    def test_already_registered_does_not_reopen(self):
        from services.imaging.heif import register_heif

        before = Image.registered_extensions().get(".heic")
        register_heif()
        self.assertEqual(Image.registered_extensions().get(".heic"), before)


if __name__ == "__main__":
    unittest.main()
