# -*- coding: utf-8 -*-
"""收料预处理:把真实"运输皮"(zip/HEIC/密码 PDF/损坏件)在登记前化成能进 intake 的普通件。

只作用于**新上传路径**(routes/workorder_routes.add_materials),存量已登记 item 零触碰。
产出是内存字节 + 元数据(NormalizedFile),由调用方经 storage.save_material 落盘(自动继承
file_crypto 加密)——本模块自己绝不落盘,故不在存储契约收口面内。

四种"进不来"的料各有出口:
  zip   → 服务端解包展开为叶子件逐件进料(嵌套 ≤2 层、总量/件数封顶防 zip bomb,超限整包拒);
  HEIC  → 转 JPEG 进管线,原件保留(转换产物走加密契约落盘,原件不进 OCR 只留证);
  密码 PDF → 检测到加密即拒并要密码;供钥后解开按普通 PDF 走(解开产物落盘走加密契约);
  0 字节/伪扩展名(magic 与扩展名不符)/坏 zip → 结构化 IntakePrepError 诚实拒绝,不静默。

不支持的归档(rar/7z)诚实拒绝(授权问题,提示转 zip);解包出的不支持格式**不在本层拦**,
原样登记交 sort 步按 unsupported_format 排除(分类语义单一事实源在 sort.py,本层不抢)。
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# 嵌套解包与体量护栏(防 zip bomb):总量/件数按解压后计,嵌套层数封顶。
_MAX_ZIP_DEPTH = 2  # outer.zip → inner.zip → 叶子(2 层 zip);再深一层拒
_MAX_ZIP_TOTAL_BYTES = 200 * 1024 * 1024
_MAX_ZIP_FILES = 200

# HEIC/HEIF:iPhone 默认相册格式,OCR 管线不吃,须转 JPEG。
_HEIC_EXTS = {".heic", ".heif"}
# 扩展名声称是媒体件(图片/PDF)却无对应 magic = 伪扩展名(如 .jpg 实为文本),诚实拒。
_MEDIA_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".tif",
    ".tiff",
    ".bmp",
    ".heic",
    ".heif",
    ".pdf",
}
_ARCHIVE_REJECT_EXTS = {".rar", ".7z", ".gz", ".tar", ".bz2"}

# HEIF 品牌码(ftyp box 第 9-12 字节):覆盖 iPhone 常见几种。
_HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"heim", b"heis", b"hevm", b"hevs", b"mif1", b"msf1"}

# 错误码 → 四语文案(th/en/zh/ja)。结构化错误的 message 直接内嵌四语,前端拿到即可呈现,
# 不依赖前端 i18n 包再映射一次(收料错误面自足)。context 另带 filename 等逐件点名信息。
_MESSAGES: dict[str, dict[str, str]] = {
    "workorder.intake.empty_file": {
        "th": "ไฟล์ว่างเปล่า (0 ไบต์) กรุณาอัปโหลดไฟล์ที่มีข้อมูล",
        "en": "File is empty (0 bytes). Please upload a file with content.",
        "zh": "文件为空(0 字节),请上传有内容的文件。",
        "ja": "ファイルが空です(0 バイト)。内容のあるファイルをアップロードしてください。",
    },
    "workorder.intake.fake_extension": {
        "th": "นามสกุลไฟล์ไม่ตรงกับเนื้อหาจริง (ไฟล์อาจเสียหายหรือไม่ใช่รูป/PDF)",
        "en": "File extension does not match its real content (corrupt or not an image/PDF).",
        "zh": "扩展名与真实内容不符(文件损坏或并非图片/PDF)。",
        "ja": "拡張子と実際の内容が一致しません(破損、または画像/PDF ではありません)。",
    },
    "workorder.intake.zip_limit": {
        "th": "ไฟล์ zip เกินขีดจำกัด (สูงสุด 200 ไฟล์ / 200MB / ซ้อนกัน 2 ชั้น) กรุณาแบ่งส่ง",
        "en": "Zip exceeds limits (max 200 files / 200MB / 2 nesting levels). Please split it.",
        "zh": "压缩包超限(最多 200 个文件 / 200MB / 嵌套 2 层),请拆分后再传。",
        "ja": "zip が上限を超えています(最大 200 ファイル / 200MB / ネスト 2 段)。分割してください。",
    },
    "workorder.intake.zip_corrupt": {
        "th": "ไฟล์ zip เสียหาย เปิดไม่ได้",
        "en": "Zip file is corrupt and cannot be opened.",
        "zh": "压缩包已损坏,无法打开。",
        "ja": "zip ファイルが破損しており開けません。",
    },
    "workorder.intake.unsupported_archive": {
        "th": "รองรับเฉพาะ zip เท่านั้น กรุณาแปลง rar/7z เป็น zip ก่อน",
        "en": "Only zip is supported. Please convert rar/7z to zip first.",
        "zh": "仅支持 zip,请先把 rar/7z 转成 zip。",
        "ja": "対応は zip のみです。rar/7z は zip に変換してください。",
    },
    "workorder.intake.pdf_password_required": {
        "th": "PDF นี้มีรหัสผ่าน กรุณากรอกรหัสผ่านเพื่อปลดล็อก",
        "en": "This PDF is password-protected. Please provide the password to unlock it.",
        "zh": "此 PDF 带密码,请提供密码以解锁。",
        "ja": "この PDF はパスワード保護されています。解除用のパスワードを入力してください。",
    },
    "workorder.intake.pdf_password_wrong": {
        "th": "รหัสผ่าน PDF ไม่ถูกต้อง กรุณาลองใหม่",
        "en": "Incorrect PDF password. Please try again.",
        "zh": "PDF 密码不正确,请重试。",
        "ja": "PDF のパスワードが正しくありません。もう一度お試しください。",
    },
    "workorder.intake.heic_conversion_failed": {
        "th": "แปลงรูป HEIC ไม่สำเร็จ ไฟล์อาจเสียหาย",
        "en": "Failed to convert HEIC image; the file may be corrupt.",
        "zh": "HEIC 图片转换失败,文件可能已损坏。",
        "ja": "HEIC 画像の変換に失敗しました。ファイルが破損している可能性があります。",
    },
}
_FALLBACK_CODE = "workorder.intake.fake_extension"


class IntakePrepError(Exception):
    """收料预处理拒绝:带错误码 + 四语文案 + 逐件点名 context(至少含 filename)。"""

    def __init__(self, code: str, *, filename: Optional[str] = None, **context):
        self.code = code
        self.filename = filename
        self.context = {"filename": filename, **context}
        super().__init__(code)

    def message_map(self) -> dict[str, str]:
        return _MESSAGES.get(self.code, _MESSAGES[_FALLBACK_CODE])


@dataclass
class NormalizedFile:
    """预处理产物:待落盘的一件料。register=False 的是留证原件(HEIC 源),落盘但不登记进
    work_order_items(不进 OCR、不进对账);register=True 的才是流水线要处理的正件。"""

    content: bytes
    suffix: str
    original_name: str
    register: bool = True


@dataclass
class _ZipBudget:
    """跨嵌套累计的 zip 解压预算(单一实例贯穿整包递归):件数/字节任一破限即整包拒。"""

    files: int = 0
    total_bytes: int = 0

    def charge(self, *, filename: str, add_bytes: int) -> None:
        self.files += 1
        self.total_bytes += max(0, add_bytes)
        if self.files > _MAX_ZIP_FILES or self.total_bytes > _MAX_ZIP_TOTAL_BYTES:
            raise IntakePrepError(
                "workorder.intake.zip_limit",
                filename=filename,
                files=self.files,
                total_bytes=self.total_bytes,
                max_files=_MAX_ZIP_FILES,
                max_bytes=_MAX_ZIP_TOTAL_BYTES,
            )


def _sniff(data: bytes) -> Optional[str]:
    """按 magic 认真实类型;认不出返 None(= 无已知二进制签名,疑似文本/损坏)。"""
    if data[:4] == b"%PDF":
        return "pdf"
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if data[:2] == b"BM":
        return "bmp"
    if data[:4] == b"PK\x03\x04":
        return "zip"
    if data[4:8] == b"ftyp" and data[8:12] in _HEIF_BRANDS:
        return "heic"
    return None


def _ext_of(name: Optional[str]) -> str:
    return Path(name or "").suffix.lower()


def _jpeg_name(name: str) -> str:
    """把源名的扩展名换成 .jpg(转换产物的展示名,如 photo.heic → photo.jpg)。"""
    stem = Path(name).stem or "image"
    return f"{stem}.jpg"


def _convert_heic(content: bytes, filename: str) -> bytes:
    """HEIC/HEIF → JPEG 字节。依赖 pillow-heif(懒加载:非 HEIC 路径不 import)。转换失败诚实报错。"""
    try:
        import pillow_heif
        from PIL import Image

        pillow_heif.register_heif_opener()
        img = Image.open(io.BytesIO(content)).convert("RGB")
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=90)
        return out.getvalue()
    except IntakePrepError:
        raise
    except Exception as e:  # noqa: BLE001 - 转换失败要 fail loud,不静默丢原件
        raise IntakePrepError(
            "workorder.intake.heic_conversion_failed", filename=filename, detail=str(e)
        ) from e


def _pdf_is_encrypted(content: bytes) -> bool:
    """PDF 是否带密码。读不开(非本层负责的深层损坏)返 False,交后续 OCR/sort 兜。"""
    try:
        from pypdf import PdfReader

        return bool(PdfReader(io.BytesIO(content)).is_encrypted)
    except Exception:  # noqa: BLE001 - 判"要不要密码"失败按"不要"处理,不误报密码墙
        return False


def _pdf_decrypt(content: bytes, password: str, filename: str) -> bytes:
    """用密码解开加密 PDF,返回去密的 PDF 字节(落盘再由 storage 层按开关加密)。密码错诚实拒。"""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(content))
    if reader.is_encrypted and not reader.decrypt(password):
        raise IntakePrepError("workorder.intake.pdf_password_wrong", filename=filename)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _zip_entry_name(info: zipfile.ZipInfo) -> str:
    """还原 zip 内条目文件名。UTF-8 flag(0x800)置位则 zipfile 已正确解码;未置位时 zipfile
    按 cp437 解成乱码——回编 cp437 再试 utf-8,救回泰文/emoji 名(多数打包器写 utf-8 不置 flag)。
    只取 basename,顺带挡 zip-slip(落盘位由 storage 生成 uuid 名,不用条目路径)。"""
    name = info.filename
    if not info.flag_bits & 0x800:
        try:
            name = name.encode("cp437").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return Path(name.replace("\\", "/")).name or "file"


def _normalize_zip_leaf(name: str, data: bytes) -> list[NormalizedFile]:
    """zip 内单个叶子件 → 待落盘件。宽松处理(空条目跳过、伪扩展名不拦):解包件的分类/排除
    交 sort 步单一裁决,本层只做 HEIC 转换这一件必须在登记前完成的事。"""
    if not data:
        return []
    ext = _ext_of(name)
    if ext in _HEIC_EXTS or _sniff(data) == "heic":
        return [
            NormalizedFile(data, ext or ".heic", name, register=False),
            NormalizedFile(_convert_heic(data, name), ".jpg", _jpeg_name(name), register=True),
        ]
    return [NormalizedFile(data, ext or ".bin", name)]


def _expand_zip(
    content: bytes, filename: str, *, budget: _ZipBudget, depth: int = 1
) -> list[NormalizedFile]:
    """解包一个 zip,递归展开嵌套 zip(≤_MAX_ZIP_DEPTH 层),累计计入 budget(超限整包拒)。"""
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as e:
        raise IntakePrepError("workorder.intake.zip_corrupt", filename=filename) from e

    results: list[NormalizedFile] = []
    with zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            leaf_name = _zip_entry_name(info)
            budget.charge(filename=leaf_name, add_bytes=info.file_size)
            if _ext_of(leaf_name) == ".zip":
                if depth + 1 > _MAX_ZIP_DEPTH:
                    raise IntakePrepError(
                        "workorder.intake.zip_limit",
                        filename=leaf_name,
                        depth=depth + 1,
                        max_depth=_MAX_ZIP_DEPTH,
                    )
                results.extend(
                    _expand_zip(zf.read(info), leaf_name, budget=budget, depth=depth + 1)
                )
            else:
                results.extend(_normalize_zip_leaf(leaf_name, zf.read(info)))
    return results


def normalize_upload(
    filename: Optional[str], content: bytes, *, password: Optional[str] = None
) -> list[NormalizedFile]:
    """单份上传 → 待落盘件清单(通常 1 件;zip 解出多件;HEIC 出原件+转换件两件)。

    不合规当场抛 IntakePrepError(0 字节/伪扩展名/超限或坏 zip/不支持归档/密码 PDF)——调用方
    在**任何落盘之前**统一转 422,故一批里任一件不合规都不会留半截孤儿在盘(413 孤儿修同理)。
    """
    if not content:
        raise IntakePrepError("workorder.intake.empty_file", filename=filename)

    ext = _ext_of(filename)
    kind = _sniff(content)

    if ext in _ARCHIVE_REJECT_EXTS:
        raise IntakePrepError("workorder.intake.unsupported_archive", filename=filename, ext=ext)
    if ext == ".zip" or (kind == "zip" and ext not in (".xlsx", ".xlsm", ".docx", ".pptx")):
        return _expand_zip(content, filename or "archive.zip", budget=_ZipBudget())

    # 伪扩展名:声称媒体件却无对应 magic(.jpg 实为文本等)= 损坏/伪装,诚实拒。zip 魔数的
    # xlsx/docx 上面已放行,故此处 kind is None 才是真伪装(不误伤合法 Office 件)。
    if ext in _MEDIA_EXTS and kind is None:
        raise IntakePrepError("workorder.intake.fake_extension", filename=filename, ext=ext)

    if ext in _HEIC_EXTS or kind == "heic":
        jpeg = _convert_heic(content, filename or "image.heic")
        return [
            NormalizedFile(content, ext or ".heic", filename or "image.heic", register=False),
            NormalizedFile(jpeg, ".jpg", _jpeg_name(filename or "image.heic"), register=True),
        ]

    if ext == ".pdf" or kind == "pdf":
        if _pdf_is_encrypted(content):
            if not password:
                raise IntakePrepError("workorder.intake.pdf_password_required", filename=filename)
            content = _pdf_decrypt(content, password, filename or "document.pdf")
        return [NormalizedFile(content, ".pdf", filename or "document.pdf")]

    return [NormalizedFile(content, ext or ".bin", filename or "file")]


def normalize_batch(pairs, *, password: Optional[str] = None) -> list[NormalizedFile]:
    """整批 (filename, content) 预处理:任一件不合规抛 IntakePrepError,调用方在**任何落盘之前**
    统一转 422,故整批零残留(413 孤儿修与乱料诚实拒的共因)。0 字节带名件诚实点名拒;框架侧
    无名空 part 视作"没选文件"跳过。"""
    out: list[NormalizedFile] = []
    for filename, content in pairs:
        if not content:
            if (filename or "").strip():
                raise IntakePrepError("workorder.intake.empty_file", filename=filename)
            continue
        out.extend(normalize_upload(filename, content, password=password))
    return out
