# -*- coding: utf-8 -*-
"""收料预处理守门(services/workorder/intake_prep.py · IN-0a)。

脱库脱盘纯字节验证:zip 解包/嵌套/限额、HEIC 真转、密码 PDF 检测+解开、0字节/伪扩展名/
坏 zip/不支持归档的诚实拒绝,以及错误四语文案齐全。HEIC 用真样本(fixtures)本地实转。"""

from __future__ import annotations

import io
import unittest
import zipfile
from pathlib import Path

from services.workorder import intake_prep as ip

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "messy_intake_pack"


def _jpeg(color=(1, 2, 3)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="JPEG")
    return buf.getvalue()


def _png() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (9, 9, 9)).save(buf, format="PNG")
    return buf.getvalue()


def _pdf(pages=1) -> bytes:
    import fitz

    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def _make_zip(entries: dict, compress=zipfile.ZIP_DEFLATED) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compress) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


class SniffTests(unittest.TestCase):
    def test_magic_recognized(self):
        self.assertEqual(ip._sniff(_jpeg()), "jpeg")
        self.assertEqual(ip._sniff(_png()), "png")
        self.assertEqual(ip._sniff(_pdf()), "pdf")
        self.assertEqual(ip._sniff(_make_zip({"a": b"x"})), "zip")
        self.assertIsNone(ip._sniff(b"just some text, no magic"))

    def test_heic_brand_sniffed(self):
        heic = (_FIXTURES / "iphone_photo.heic").read_bytes()
        self.assertEqual(ip._sniff(heic), "heic")


class RejectTests(unittest.TestCase):
    def test_empty_file_rejected(self):
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload("empty.jpg", b"")
        self.assertEqual(c.exception.code, "workorder.intake.empty_file")
        self.assertEqual(c.exception.context["filename"], "empty.jpg")

    def test_fake_extension_rejected(self):
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload("photo.jpg", b"this is plain text not an image")
        self.assertEqual(c.exception.code, "workorder.intake.fake_extension")

    def test_pdf_fake_extension_rejected(self):
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload("doc.pdf", b"not really a pdf")
        self.assertEqual(c.exception.code, "workorder.intake.fake_extension")

    def test_unsupported_archive_rejected(self):
        for name in ("a.rar", "a.7z"):
            with self.assertRaises(ip.IntakePrepError) as c:
                ip.normalize_upload(name, b"Rar!\x1a\x07\x00whatever")
            self.assertEqual(c.exception.code, "workorder.intake.unsupported_archive")

    def test_xlsx_zip_magic_not_flagged_fake(self):
        # xlsx 是 zip 容器(PK 魔数),不得被当伪扩展名拒,也不当归档解包。
        from openpyxl import Workbook

        buf = io.BytesIO()
        Workbook().save(buf)
        out = ip.normalize_upload("book.xlsx", buf.getvalue())
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].register)


class PassThroughTests(unittest.TestCase):
    def test_valid_jpeg_registers_as_is(self):
        out = ip.normalize_upload("r.jpg", _jpeg())
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].register)
        self.assertEqual(out[0].suffix, ".jpg")

    def test_png_bytes_under_jpg_ext_accepted(self):
        # 扩展名/内容都是已知媒体(png 内容、.jpg 名)→ 不算伪装,放行(宽松:交 OCR 按内容处理)。
        out = ip.normalize_upload("mis.jpg", _png())
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].register)

    def test_plain_pdf_registers(self):
        out = ip.normalize_upload("bill.pdf", _pdf())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].suffix, ".pdf")


class HeicTests(unittest.TestCase):
    def test_heic_real_sample_converts_and_keeps_original(self):
        heic = (_FIXTURES / "iphone_photo.heic").read_bytes()
        out = ip.normalize_upload("IMG_2647.HEIC", heic)
        self.assertEqual(len(out), 2)
        originals = [n for n in out if not n.register]
        converts = [n for n in out if n.register]
        self.assertEqual(len(originals), 1)  # 原件留证
        self.assertEqual(len(converts), 1)  # 转换件进管线
        self.assertEqual(originals[0].content, heic)
        # 转换产物是真 JPEG,PIL 可开。
        from PIL import Image

        jpeg = converts[0].content
        self.assertEqual(ip._sniff(jpeg), "jpeg")
        self.assertEqual(converts[0].suffix, ".jpg")
        self.assertEqual(Image.open(io.BytesIO(jpeg)).mode, "RGB")

    def test_heic_conversion_failure_is_honest(self):
        with self.assertRaises(ip.IntakePrepError) as c:
            # ftyp/heic 魔数骗过嗅探,但体不是合法 HEIC → 转换必败,诚实报错不静默。
            ip.normalize_upload("x.heic", b"\x00\x00\x00\x18ftypheic" + b"\x00" * 40)
        self.assertEqual(c.exception.code, "workorder.intake.heic_conversion_failed")


class PasswordPdfTests(unittest.TestCase):
    def _encrypted(self, password="1234"):
        from pypdf import PdfReader, PdfWriter

        w = PdfWriter()
        for p in PdfReader(io.BytesIO(_pdf())).pages:
            w.add_page(p)
        w.encrypt(password)
        out = io.BytesIO()
        w.write(out)
        return out.getvalue()

    def test_password_required_when_no_password(self):
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload("bank.pdf", self._encrypted())
        self.assertEqual(c.exception.code, "workorder.intake.pdf_password_required")

    def test_correct_password_unlocks(self):
        out = ip.normalize_upload("bank.pdf", self._encrypted("1234"), password="1234")
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].register)
        # 解开产物是去密 PDF(可无密码再读)。
        from pypdf import PdfReader

        self.assertFalse(PdfReader(io.BytesIO(out[0].content)).is_encrypted)

    def test_wrong_password_rejected(self):
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload("bank.pdf", self._encrypted("1234"), password="0000")
        self.assertEqual(c.exception.code, "workorder.intake.pdf_password_wrong")


class ZipTests(unittest.TestCase):
    def test_flat_zip_expands_leaves(self):
        z = _make_zip({"a.jpg": _jpeg(), "b.pdf": _pdf()})
        out = ip.normalize_upload("pack.zip", z)
        self.assertEqual(len(out), 2)
        self.assertTrue(all(n.register for n in out))

    def test_nested_two_levels_ok(self):
        inner = _make_zip({"x.jpg": _jpeg(), "y.jpg": _jpeg()})
        outer = _make_zip({"inner.zip": inner, "top.pdf": _pdf()})
        out = ip.normalize_upload("outer.zip", outer)
        self.assertEqual(len(out), 3)  # x, y, top

    def test_three_levels_rejected(self):
        lvl3 = _make_zip({"leaf.jpg": _jpeg()})
        lvl2 = _make_zip({"lvl3.zip": lvl3})
        lvl1 = _make_zip({"lvl2.zip": lvl2})
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload("lvl1.zip", lvl1)
        self.assertEqual(c.exception.code, "workorder.intake.zip_limit")

    def test_over_file_count_rejected(self):
        z = _make_zip({f"f{i}.txt": b"x" for i in range(ip._MAX_ZIP_FILES + 1)})
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload("many.zip", z)
        self.assertIn("zip_limit", c.exception.code)

    def test_over_byte_budget_rejected(self):
        z = _make_zip({"a.jpg": b"y" * 5000})
        orig = ip._MAX_ZIP_TOTAL_BYTES
        ip._MAX_ZIP_TOTAL_BYTES = 100
        try:
            with self.assertRaises(ip.IntakePrepError) as c:
                ip.normalize_upload("big.zip", z)
            self.assertIn("zip_limit", c.exception.code)
        finally:
            ip._MAX_ZIP_TOTAL_BYTES = orig

    def test_corrupt_zip_rejected(self):
        with self.assertRaises(ip.IntakePrepError) as c:
            ip.normalize_upload("broken.zip", b"PK\x03\x04 not a real zip body")
        self.assertEqual(c.exception.code, "workorder.intake.zip_corrupt")

    def test_zip_heic_leaf_converted(self):
        heic = (_FIXTURES / "iphone_photo.heic").read_bytes()
        z = _make_zip({"photo.heic": heic})
        out = ip.normalize_upload("pack.zip", z)
        self.assertEqual(len(out), 2)  # 原件 + 转换件
        self.assertEqual(sum(1 for n in out if n.register), 1)

    def test_zip_skips_empty_entries(self):
        z = _make_zip({"empty.txt": b"", "real.jpg": _jpeg()})
        out = ip.normalize_upload("pack.zip", z)
        self.assertEqual(len(out), 1)


class ZipNameTests(unittest.TestCase):
    def test_recovers_cp437_thai_name(self):
        thai = "ใบเสร็จ.jpg"
        zi = zipfile.ZipInfo(thai.encode("utf-8").decode("cp437"))
        zi.flag_bits = 0  # 未置 UTF-8 flag → zipfile 会按 cp437 解成乱码
        self.assertEqual(ip._zip_entry_name(zi), thai)

    def test_keeps_utf8_flagged_name(self):
        zi = zipfile.ZipInfo("ใบเสร็จ.jpg")
        zi.flag_bits = 0x800
        self.assertEqual(ip._zip_entry_name(zi), "ใบเสร็จ.jpg")

    def test_strips_path_components(self):
        zi = zipfile.ZipInfo("../../etc/evil.jpg")
        zi.flag_bits = 0x800
        self.assertEqual(ip._zip_entry_name(zi), "evil.jpg")


class MessageCatalogTests(unittest.TestCase):
    def test_every_code_has_four_languages(self):
        for code, m in ip._MESSAGES.items():
            self.assertEqual(set(m), {"th", "en", "zh", "ja"}, code)
            for lang, text in m.items():
                self.assertTrue(text.strip(), f"{code}/{lang} 空文案")

    def test_error_message_map_returns_four_langs(self):
        e = ip.IntakePrepError("workorder.intake.pdf_password_required", filename="b.pdf")
        self.assertEqual(set(e.message_map()), {"th", "en", "zh", "ja"})


if __name__ == "__main__":
    unittest.main()
