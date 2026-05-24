# -*- coding: utf-8 -*-
"""
通用模板学习层 · 列映射接口(ADR-006 · S4)。

- POST /api/recon/import/save-mapping  保存用户确认的列对应(下次同格式自动)
- GET  /api/recon/import/mappings      列出本租户已学的模板
- DELETE /api/recon/import/mappings/{id}  删除一个学过的模板(改错了重学)

映射作用域 = tenant_id 优先,没有租户的单用户退回 user_id(都是 UUID · 表 NOT NULL)。
铁律 #17/#23:独立 router · 不进 app.py。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from auth import get_current_user_from_request
from services.importer import template_store

logger = logging.getLogger("importer.routes")
router = APIRouter(tags=["importer"])

_VALID_DOC = ("statement", "gl")


def _scope(user) -> str:
    """映射作用域:有租户用租户,没有用 user_id。"""
    return str(user.get("tenant_id") or user.get("id"))


class SaveMappingBody(BaseModel):
    document_type: str
    template_signature: str
    mapping: Dict[str, int]
    sample_headers: Optional[List[str]] = None
    template_name: Optional[str] = ""
    sheet_hint: Optional[str] = ""


@router.post("/api/recon/import/save-mapping")
async def save_mapping(body: SaveMappingBody, request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    if body.document_type not in _VALID_DOC:
        raise HTTPException(422, "document_type 必须是 statement 或 gl")
    if not body.template_signature or not body.mapping:
        raise HTTPException(422, "缺少 template_signature 或 mapping")
    # statement 至少要 date;balance 强烈建议(便于余额校验)· date 必填
    if "date" not in body.mapping:
        raise HTTPException(422, "列映射至少需要指定『日期』列")
    ok = template_store.save_mapping(
        _scope(user),
        body.document_type,
        body.template_signature,
        body.mapping,
        source="user",
        template_name=body.template_name or "",
        sheet_hint=body.sheet_hint or "",
        sample_headers=body.sample_headers,
        created_by=str(user.get("id")),
    )
    if not ok:
        raise HTTPException(500, "保存失败,请稍后重试")
    return {"ok": True}


@router.get("/api/recon/import/mappings")
async def list_mappings(request: Request, document_type: Optional[str] = None):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    dt = document_type if document_type in _VALID_DOC else None
    return {"ok": True, "mappings": template_store.list_mappings(_scope(user), dt)}


@router.delete("/api/recon/import/mappings/{mapping_id}")
async def delete_mapping(mapping_id: str, request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    ok = template_store.delete_mapping(_scope(user), mapping_id)
    if not ok:
        raise HTTPException(404, "映射不存在或无权删除")
    return {"ok": True}
