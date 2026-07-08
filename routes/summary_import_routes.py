# -*- coding: utf-8 -*-
"""汇总表 → 批量建单 路由(录入工作台第三卡 · 3 端点)。

parse    上传 xlsx/csv → 表头 + 行(供列映射)
validate 列映射 + 批次常量 → 逐行方向/落点判定 + 缺字段警告(前端预览据此,不前端假装判定)
commit   同一入参 + 已确认 → 逐行建账本草稿 + 写 ocr_history(可推 ERP)

薄层:auth → 套账解析(purchase_common 同款)→ 调 services/summary_import。判定/建单逻辑全在服务层。
统一 POS 信封(前缀已入 core.pos_api._POS_PREFIXES)。模块门控走 expense(与采购同域)。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Request, UploadFile
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, ok
from routes.purchase_common import auth_member, gate, resolve_ws, uid as _uid
from services.purchase.field_clean import clean_tax_id
from services.sales import seller_profile
from services.summary_import import commit as commit_svc
from services.summary_import import judge as judge_svc
from services.summary_import import mapping as mapping_svc
from services.summary_import import parse as parse_svc

router = APIRouter(prefix="/api/summary-import", tags=["summary-import"])

_MAX_BYTES = 8 * 1024 * 1024  # 汇总表远小于此;超限判异常输入,不吞内存


class MapConfig(BaseModel):
    parsed: Dict[str, Any] = Field(default_factory=dict)
    column_map: Dict[str, Any] = Field(default_factory=dict)
    constants: Dict[str, Any] = Field(default_factory=dict)
    include_summary: bool = False
    workspace_client_id: Optional[int] = None


def _workspace(cur, tenant_id: str, ws: int) -> Dict[str, Any]:
    """账套主体资料(判方向锚点 = 自家税号 · 销项落卖方抬头)。"""
    seller = seller_profile.get_seller(cur, tenant_id=tenant_id, workspace_client_id=ws) or {}
    return {
        "name": seller.get("name") or "",
        "tax_id": seller.get("tax_id") or "",
        "address": seller.get("address") or "",
    }


def _map_and_judge(cur, tenant_id: str, ws: int, cfg: MapConfig) -> Dict[str, Any]:
    """公共:映射 + 判定(validate/commit 同一套,保证预览与落库口径一致)。"""
    workspace = _workspace(cur, tenant_id, ws)
    mapped = mapping_svc.map_rows(
        cfg.parsed,
        column_map=cfg.column_map,
        constants=cfg.constants,
        workspace=workspace,
        include_summary=cfg.include_summary,
    )
    dup = mapping_svc.find_duplicate_doc_nos(mapped)
    judged = judge_svc.judge_rows(mapped, own_tax_id=workspace["tax_id"], dup_doc_nos=dup)
    return {
        "workspace": workspace,
        "mapped": mapped,
        "judged": judged,
        "dup_doc_nos": dup,
        "own_tax_present": bool(clean_tax_id(workspace["tax_id"])),
    }


@router.post("/parse")
async def api_parse(request: Request, file: UploadFile = File(...)):
    """上传汇总表 → 表头 + 行。纯解析,不落库。"""
    auth_member(request, "purchase.doc.create")
    raw = await file.read()
    if len(raw) > _MAX_BYTES:
        raise PosError("purchase.line_invalid", 413, detail="file_too_large")
    parsed = parse_svc.parse_table(raw, file.filename or "")
    if not parsed["headers"]:
        raise PosError("purchase.line_invalid", 422, detail="unparseable_table")
    return ok(parsed)


@router.post("/validate")
async def api_validate(cfg: MapConfig, request: Request):
    """列映射 + 常量 → 逐行预览(方向/现金落点/缺字段)。前端徽章直接用这里的真实判定。"""
    _, tid = auth_member(request, "purchase.doc.create")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, cfg.workspace_client_id)
        res = _map_and_judge(cur, tid, ws, cfg)
    # 预览只回判定 + 干净 fields(剥内部字段),不回整批原始 parsed(前端已持有)。
    preview: List[Dict[str, Any]] = []
    for m, j in zip(res["mapped"], res["judged"]):
        fields = {k: v for k, v in (m["fields"] or {}).items() if not k.startswith("_")}
        preview.append({**j, "fields": fields})
    return ok(
        {
            "preview": preview,
            "dup_doc_nos": res["dup_doc_nos"],
            "own_tax_present": res["own_tax_present"],
            "workspace_name": res["workspace"]["name"],
            "total": len(preview),
            "blocked_count": sum(1 for j in res["judged"] if j["blocked"]),
        }
    )


@router.post("/commit")
async def api_commit(cfg: MapConfig, request: Request):
    """确认后建单。硬阻断行(缺单号/日期/金额)自动跳过,其余逐行建账本草稿 + 写 ocr_history。"""
    user, tid = auth_member(request, "purchase.doc.create")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, cfg.workspace_client_id)
        res = _map_and_judge(cur, tid, ws, cfg)

    # 硬阻断行不建单(如实回 skipped);可建行才落库。
    to_commit: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for m, j in zip(res["mapped"], res["judged"]):
        if j["blocked"]:
            skipped.append(
                {"row_index": j["row_index"], "status": "skipped", "warnings": j["warnings"]}
            )
        else:
            to_commit.append(m)

    results = commit_svc.commit_rows(
        tenant_id=tid,
        workspace_client_id=ws,
        created_by=_uid(user),
        rows=to_commit,
        batch_ref=str(cfg.parsed.get("sheet_name") or "batch")[:24],
    )
    all_rows = results + skipped
    return ok(
        {
            "results": all_rows,
            "created": sum(1 for r in results if r["status"] == "created"),
            "booked_no_push": sum(1 for r in results if r["status"] == "booked_no_push"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "skipped": len(skipped),
            "total": len(all_rows),
        }
    )
