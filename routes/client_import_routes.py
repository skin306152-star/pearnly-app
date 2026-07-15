# -*- coding: utf-8 -*-
"""IN-0d · 客户名录 Excel 批量导入路由(2 端点:parse 预览 + commit 落库)。

命门:commit 逐行走与单个建档(POST /api/workspace/clients)**同一段**校验/创建代码
——调用 routes.workspace_routes._create_validated_client(dry_run=...),不重造第二套
校验实现,M1 泰文名闸 / 税号查重 / pos_only 一号一店闸对导入行同样逐行如实生效。

解析 + 表头猜测在 services/workspace/client_import.py(纯函数,零 DB 依赖);本文件
只管上传 → 薄层编排(结构校验 → 共享校验体)→ 落库。上传内容全程内存,不落盘。

权限沿单建端点同款(settings.workspace.manage);RLS 天然隔离。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from core.route_helpers import _log_op, _tid
from routes.workspace_routes import WorkspaceClientCreate, _create_validated_client
from services.authz.deps import require_perm
from services.workspace import client_import as import_svc

router = APIRouter()


class ClientImportRow(BaseModel):
    row_index: int
    name: str = ""
    tax_id: Optional[str] = None
    branch: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class ClientImportCommitRequest(BaseModel):
    rows: List[ClientImportRow] = Field(default_factory=list)


def _judge_row(
    row: ClientImportRow, user: Dict[str, Any], tenant_id: Optional[str], *, dry_run: bool
) -> Dict[str, Any]:
    """单行判定:结构校验 → 共享校验体(dry_run 时只判不写)。

    三态:valid(预览将建)/created(已建)、skip(税号已存在)、error(缺 name/税号格式错/
    泰文名闸不过/pos_only 一号一店闸/其它)——逐行给 reason(前端映射四语文案)。结果
    始终回显 name/tax_id(前端预览表要展示这两列,报错行也要能看出是哪一行)。
    """
    name = (row.name or "").strip()
    tax_id = (row.tax_id or "").strip()
    base = {"row_index": row.row_index, "name": name, "tax_id": tax_id}

    err = import_svc.structural_error(name, tax_id)
    if err:
        return {**base, "status": "error", "reason": err}

    req = WorkspaceClientCreate(
        name=name,
        tax_id=tax_id or None,
        branch=(row.branch or "").strip() or None,
        phone=(row.phone or "").strip() or None,
        address=(row.address or "").strip() or None,
    )
    try:
        wid = _create_validated_client(req, user, tenant_id, dry_run=dry_run)
    except HTTPException as e:
        detail = e.detail
        code = detail if isinstance(detail, str) else (detail or {}).get("code")
        if code == "workspace.tax_id_duplicate":
            return {**base, "status": "skip", "reason": code}
        return {**base, "status": "error", "reason": code or "client_import.err_generic"}
    return {**base, "status": "valid" if dry_run else "created", "id": wid}


@router.post("/api/workspace/clients/import/parse")
async def api_client_import_parse(request: Request, file: UploadFile = File(...)):
    """上传名录 → 表头识别 + 逐行三态预览(dry_run,不落库)。"""
    user = require_perm(request, "settings.workspace.manage")
    tenant_id = _tid(user)
    raw = await file.read()
    if len(raw) > import_svc.MAX_BYTES:
        raise HTTPException(413, detail="client_import.file_too_large")
    parsed = import_svc.parse_client_rows(raw, file.filename or "")
    if not parsed["name_column_found"]:
        raise HTTPException(422, detail="client_import.header_not_recognized")

    preview = [
        _judge_row(ClientImportRow(**r), user, tenant_id, dry_run=True) for r in parsed["rows"]
    ]
    return {
        "preview": preview,
        "headers": parsed["headers"],
        "matched": parsed["matched"],
        "truncated": parsed["truncated"],
        "total": len(preview),
        "valid_count": sum(1 for p in preview if p["status"] == "valid"),
        "skip_count": sum(1 for p in preview if p["status"] == "skip"),
        "error_count": sum(1 for p in preview if p["status"] == "error"),
    }


@router.post("/api/workspace/clients/import/commit")
async def api_client_import_commit(cfg: ClientImportCommitRequest, request: Request):
    """确认后逐行落库。commit 幂等:同文件重导,已建的行(税号已在库)全落 skip。"""
    user = require_perm(request, "settings.workspace.manage")
    tenant_id = _tid(user)
    if len(cfg.rows) > import_svc.MAX_ROWS:
        raise HTTPException(422, detail="client_import.too_many_rows")

    results = [_judge_row(r, user, tenant_id, dry_run=False) for r in cfg.rows]
    for r in results:
        if r["status"] == "created":
            _log_op(
                request,
                user,
                "workspace.client.import_create",
                target_type="workspace_client",
                target_id=str(r.get("id")),
                target_name=r.get("name"),
            )
    return {
        "results": results,
        "created": sum(1 for r in results if r["status"] == "created"),
        "skipped": sum(1 for r in results if r["status"] == "skip"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "total": len(results),
    }
