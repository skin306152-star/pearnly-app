# -*- coding: utf-8 -*-
"""图片上传存储(商品图 / logo / 印章 / 签名 共用 · docs/16 §L4)。

本地文件存储(无对象存储):租户隔离目录 + uuid 文件名,绝不用客户端文件名 → 杜绝路径穿越。
入图不设格式白名单:Pillow 解得开就收(含 iPhone 直拍的 HEIC,靠 pillow-heif),解不开才拒。
落盘前统一归一化 —— EXIF 转正、长边缩到 1600、重编码(顺带剥掉 EXIF/GPS 等元数据),所以
手机原图多大都行,落地永远是小图;25MB 之上才当可疑文件拒。磁盘余量守卫(铁律#24 防塞盘)。
读回时把存储 URL 反解成沙盒内的本地文件路径,供 PDF 直接读本地图(不 live-fetch 远程)。
纯叶子,不连库。
"""

from __future__ import annotations

import io
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

MAX_BYTES = 25 * 1024 * 1024  # 入图上限:手机原图 5~10MB 是常态,25MB 之上才可疑
MAX_EDGE = 1600  # 归一化长边:商品图/凭证打印用途足够,再大只是白占盘
MIN_FREE_BYTES = 200 * 1024 * 1024  # 磁盘余量 < 200MB 拒收,防塞盘
URL_PREFIX = "/api/uploads/image/"
_EXT_MEDIA = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}

# iPhone 相册原生是 HEIC。注册失败(依赖没装)不致命:HEIC 会按「解不开」走 not_an_image,
# 其他格式照常。注册统一走 heif 模块(幂等,已注册不重复)。
from services.imaging.heif import register_heif

register_heif()


class UploadError(ValueError):
    """上传校验失败:code 供路由映射 HTTP 状态。"""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def media_root() -> Path:
    return Path(os.environ.get("IMAGE_STORAGE_DIR", "/opt/mrpilot/storage/images"))


def media_type_for(ext: str) -> str:
    return _EXT_MEDIA.get(ext, "application/octet-stream")


def _normalize_image(content: bytes) -> tuple[bytes, str, int, int]:
    """Pillow 验真 + 归一化:返回 (落盘字节, ext, width, height);解不开抛 UploadError。

    格式规则:PNG/JPEG/WEBP 保持原格式(logo/印章的透明与体积特性各有道理);其他格式
    (HEIC/GIF/BMP/TIFF…)带透明转 PNG、不带转 JPEG —— 落地只有这三种,serve 与 PDF
    (reportlab ImageReader)都吃得下。重编码同时把 EXIF 方向落实成真像素、剥掉全部元数据
    (手机照片的 GPS 不该跟着商品图落盘)。
    """
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(content)) as probe:
            probe.verify()  # 校验完整性(校验后 probe 不可再用,需重开)
        with Image.open(io.BytesIO(content)) as im:
            fmt = (im.format or "").upper()
            im = ImageOps.exif_transpose(im)
            has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            if max(im.size) > MAX_EDGE:
                im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
            out = io.BytesIO()
            if fmt == "WEBP":
                ext = "webp"
                im.convert("RGBA" if has_alpha else "RGB").save(out, "WEBP", quality=85)
            elif fmt == "PNG" or (fmt != "JPEG" and has_alpha):
                ext = "png"
                im.convert("RGBA" if has_alpha else "RGB").save(out, "PNG", optimize=True)
            else:
                ext = "jpg"
                im.convert("RGB").save(out, "JPEG", quality=87, optimize=True)
            width, height = im.size
    # Pillow 对损坏图的异常不统一:坏 PNG(IDAT 校验和错)抛 SyntaxError、
    # 截断/非图抛 OSError/UnidentifiedImageError、个别解码器抛 ValueError。
    # 全部归为「不是有效图片」(422),绝不让它冒泡成 500。
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
    ):
        raise UploadError("not_an_image")
    return out.getvalue(), ext, int(width), int(height)


def save_image(tenant_id: str, content: bytes) -> dict:
    """校验 + 归一化 + 落地一张图,返回 {url, ext, width, height, bytes}。"""
    if not content:
        raise UploadError("empty_file")
    if len(content) > MAX_BYTES:
        raise UploadError("file_too_large")
    normalized, ext, width, height = _normalize_image(content)

    root = media_root()
    tenant_dir = root / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(tenant_dir).free < MIN_FREE_BYTES:
        raise UploadError("disk_full")

    name = f"{uuid.uuid4().hex}.{ext}"
    (tenant_dir / name).write_bytes(normalized)
    return {
        "url": f"{URL_PREFIX}{tenant_id}/{name}",
        "ext": ext,
        "width": width,
        "height": height,
        "bytes": len(normalized),
    }


def _safe_under_root(p: Path) -> Optional[Path]:
    """把路径锁死在 media_root 下(防 ../ 穿越);存在的普通文件才返回。"""
    root = media_root().resolve()
    rp = p.resolve()
    try:
        rp.relative_to(root)
    except ValueError:
        return None
    return rp if rp.is_file() else None


def local_path(tenant_id: str, name: str) -> Optional[Path]:
    """serve 路由用:tenant + 文件名 → 沙盒内本地路径(name 只取 basename 防穿越)。"""
    return _safe_under_root(media_root() / str(tenant_id) / os.path.basename(name))


def local_path_from_url(url: Optional[str]) -> Optional[Path]:
    """PDF 用:把存储 URL 反解成本地路径;外链/非本地 URL 返 None(绝不远程拉取)。"""
    if not url or not isinstance(url, str) or not url.startswith(URL_PREFIX):
        return None
    return _safe_under_root(media_root() / url[len(URL_PREFIX) :])


def delete_image(tenant_id: str, name: str) -> bool:
    """删一张已落盘图(路径沙盒同 local_path,name 只取 basename 防穿越)。

    幂等:文件本就不存在算成功(调用方常在"删了行才删文件"之后重试/并发场景遇到)。
    路径逃出 media_root 才是唯一真失败,返回 False 供调用方记日志。
    """
    root = media_root().resolve()
    target = (root / str(tenant_id) / os.path.basename(name)).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return False
    try:
        target.unlink(missing_ok=True)
    except OSError:
        return False
    return True
