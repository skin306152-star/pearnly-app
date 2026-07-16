# -*- coding: utf-8 -*-
"""生成"乱料验收包"常设资产(tests/fixtures/messy_intake_pack/)。

一次性生成脚本:产物提交进仓库当永久测试资产(如同 pp30 金标),守门测试
test_messy_intake_pack.py 逐件断言进料口行为。今后进料口任何改动必过本包。

重跑:python tests/fixtures/messy_intake_pack/_build_fixtures.py
(HEIC 生成需 pillow-heif;PDF 需 PyMuPDF/pypdf;xlsx 需 openpyxl —— 均在 requirements.lock。)

单件保持 <2.5MB(check_blob_size 闸);全部内容确定性,不含真实客户数据。
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

_DIR = Path(__file__).resolve().parent
PDF_PASSWORD = "1234"  # password_protected.pdf 的解锁密码(守门测试引用)


def _jpeg(color=(200, 120, 60), size=(48, 32)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _heic(color=(60, 140, 200), size=(48, 32)) -> bytes:
    import pillow_heif
    from PIL import Image

    pillow_heif.register_heif_opener()
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="HEIF")
    return buf.getvalue()


def _pdf(pages=1, text="Receipt") -> bytes:
    import fitz

    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"{text} page {i + 1}")
    data = doc.tobytes()
    doc.close()
    return data


def _encrypted_pdf(password: str) -> bytes:
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for page in PdfReader(io.BytesIO(_pdf(1, "Bank statement"))).pages:
        writer.add_page(page)
    writer.encrypt(password)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _xlsx() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["วันที่", "รายการ", "ยอดขาย"])
    ws.append(["2569-05-01", "POS", 1234.50])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _nested_zip() -> bytes:
    """outer.zip → inner.zip(含两张收据)+ 一张顶层收据。解包应展开出 3 张叶子件。"""
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("receipt_a.jpg", _jpeg((10, 200, 10)))
        zf.writestr("receipt_b.jpg", _jpeg((10, 10, 200)))
    outer = io.BytesIO()
    with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("folder/inner.zip", inner.getvalue())
        zf.writestr("folder/top_receipt.pdf", _pdf(1, "Top receipt"))
    return outer.getvalue()


def _over_count_zip() -> bytes:
    """201 个微文件 → 触发 _MAX_ZIP_FILES=200 件数上限(整包拒),文件本身极小可入库。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for i in range(201):
            zf.writestr(f"f{i:03d}.txt", b"x")
    return buf.getvalue()


def _fake_rar() -> bytes:
    """RAR5 magic + 少量字节:扩展名 .rar 即被诚实拒(不解包),内容无关。"""
    return b"Rar!\x1a\x07\x01\x00" + b"\x00" * 32


_FILES = {
    "normal_receipt.jpg": _jpeg,
    "pos_summary.xlsx": _xlsx,
    "multipage_5.pdf": lambda: _pdf(5, "Scan"),
    "iphone_photo.heic": _heic,
    "empty.jpg": lambda: b"",
    "fake_image.jpg": lambda: "นี่คือข้อความ ไม่ใช่รูปภาพ\nthis is text not an image\n".encode(
        "utf-8"
    ),
    "ใบเสร็จ_🧾.pdf": lambda: _pdf(1, "Thai emoji named"),
    "password_protected.pdf": lambda: _encrypted_pdf(PDF_PASSWORD),
    "nested_2level.zip": _nested_zip,
    "over_count.zip": _over_count_zip,
    "archive.rar": _fake_rar,
}


def build() -> None:
    _DIR.mkdir(parents=True, exist_ok=True)
    for name, maker in _FILES.items():
        (_DIR / name).write_bytes(maker())
        print(f"  wrote {name} ({(_DIR / name).stat().st_size} B)")
    print(f"built {len(_FILES)} fixtures into {_DIR}")


if __name__ == "__main__":
    build()
