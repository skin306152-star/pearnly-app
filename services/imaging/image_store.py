# -*- coding: utf-8 -*-
"""图片上传存储(商品图 / logo / 印章 / 签名 共用 · docs/16 §L4)。

本地文件存储(无对象存储):租户隔离目录 + uuid 文件名,绝不用客户端文件名 → 杜绝路径穿越。
校验走 Pillow 真验图(不靠扩展名)+ 2MB 上限 + 磁盘余量守卫(铁律#24 防塞盘)。读回时把
存储 URL 反解成沙盒内的本地文件路径,供 PDF 直接读本地图(不 live-fetch 远程)。纯叶子,不连库。
"""

from __future__ import annotations

import io
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

MAX_BYTES = 2 * 1024 * 1024  # 2MB
MIN_FREE_BYTES = 200 * 1024 * 1024  # 磁盘余量 < 200MB 拒收,防塞盘
URL_PREFIX = "/api/uploads/image/"
# Pillow format → 落地扩展名(只收这三种)。
_FORMAT_EXT = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}
_EXT_MEDIA = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}


class UploadError(ValueError):
    """上传校验失败:code 供路由映射 HTTP 状态。"""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def media_root() -> Path:
    return Path(os.environ.get("IMAGE_STORAGE_DIR", "/opt/mrpilot/storage/images"))


def media_type_for(ext: str) -> str:
    return _EXT_MEDIA.get(ext, "application/octet-stream")


def _verify_image(content: bytes) -> tuple[str, int, int]:
    """Pillow 验真:返回 (ext, width, height);非图/不支持格式/坏图抛 UploadError。"""
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(content)) as im:
            im.verify()  # 校验完整性(校验后 im 不可再用,需重开取尺寸)
        with Image.open(io.BytesIO(content)) as im2:
            fmt, size = im2.format, im2.size
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
    ext = _FORMAT_EXT.get(fmt or "")
    if not ext:
        raise UploadError("unsupported_type")
    return ext, int(size[0]), int(size[1])


def save_image(tenant_id: str, content: bytes) -> dict:
    """校验 + 落地一张图,返回 {url, ext, width, height, bytes}。"""
    if not content:
        raise UploadError("empty_file")
    if len(content) > MAX_BYTES:
        raise UploadError("file_too_large")
    ext, width, height = _verify_image(content)

    root = media_root()
    tenant_dir = root / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(tenant_dir).free < MIN_FREE_BYTES:
        raise UploadError("disk_full")

    name = f"{uuid.uuid4().hex}.{ext}"
    (tenant_dir / name).write_bytes(content)
    return {
        "url": f"{URL_PREFIX}{tenant_id}/{name}",
        "ext": ext,
        "width": width,
        "height": height,
        "bytes": len(content),
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
