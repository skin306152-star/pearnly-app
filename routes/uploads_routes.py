# -*- coding: utf-8 -*-
"""图片上传 + 公开取图(商品图 / logo / 印章 / 签名 共用 · docs/16 §L4)。

POST /api/uploads/image:登录 + 租户隔离,收文件 → 校验(Pillow 真验图 / 2MB 上限 / 磁盘守卫)
→ uuid 命名落租户目录 → 返 URL。GET /api/uploads/image/{tenant_id}/{name}:登录 + 租户匹配,
沙盒内本地文件回流。薄层:鉴权 + 整形 + 错误映射;存储/校验在 services/imaging/image_store.py。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from core.auth import get_current_user_from_request
from services.audit import file_access as audit_file_access
from services.imaging import image_store

logger = logging.getLogger("mr-pilot")
router = APIRouter(prefix="/api/uploads", tags=["uploads"])

_ERR_HTTP = {
    "empty_file": 400,
    "file_too_large": 413,
    "not_an_image": 422,
    "unsupported_type": 422,
    "disk_full": 507,
}


def _require_tenant(request: Request) -> str:
    user = get_current_user_from_request(request)
    tid = user.get("tenant_id") if user else None
    if not tid:
        raise HTTPException(400, detail="uploads.tenant_required")
    return str(tid)


@router.post("/image")
async def api_upload_image(request: Request, file: UploadFile = File(...)):
    """上传一张图(≤2MB · png/jpeg/webp)。返回可直接存进 image_url/logo_url 的 URL。"""
    tid = _require_tenant(request)
    # 只读到上限+1 字节:超限即拒,不把超大文件整个读进内存。
    content = await file.read(image_store.MAX_BYTES + 1)
    try:
        result = image_store.save_image(tid, content)
    except image_store.UploadError as exc:
        raise HTTPException(_ERR_HTTP.get(exc.code, 400), detail=f"uploads.{exc.code}")
    return {"ok": True, **result}


@router.get("/image/{tenant_id}/{name}")
async def api_get_image(tenant_id: str, name: str, request: Request):
    """取图:登录 + 只能取本租户的图(uuid 文件名 + 沙盒路径双保险)。"""
    user = get_current_user_from_request(request)
    tid = _require_tenant(request)
    if tid != tenant_id:
        raise HTTPException(404, detail="uploads.not_found")
    path = image_store.local_path(tenant_id, name)
    if not path:
        raise HTTPException(404, detail="uploads.not_found")
    ext = path.suffix.lstrip(".").lower()
    audit_file_access.log_user_file_access(
        request,
        user,
        audit_file_access.IMAGE_VIEWED,
        target_type="upload_image",
        target_id=name,
        details={"kind": "product_image"},
    )
    return FileResponse(
        str(path),
        media_type=image_store.media_type_for(ext),
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
