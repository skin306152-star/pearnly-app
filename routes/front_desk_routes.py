# -*- coding: utf-8 -*-
"""Pearnly AI · 目标驱动前门(FD-0a)HTTP API:合同 + 盘点 + 路由骨架(不含大脑)。

四端点(施工总册 §3.1):
  POST /api/ai/front-desk/contracts   建草稿合同 + 暂存投料(出盘点摘要)
  POST /api/ai/front-desk/interpret   utterance → 大脑建议(FD-0a 桩:恒返 degraded)
  POST /api/ai/front-desk/confirm     人点确认:开工单 + 经 intake.register_file 入料
  GET  /api/ai/front-desk/feed        重建消息流(合同倒序)

全组挂 `pearnly_ai_front_desk`(tenant 级默认关 · fail-closed · 叠加 pearnly_ai_m1):闸关时
一律 404 —— 对存量用户等于不存在,/ai 与今天逐字节一致。编排薄:合同存储/状态机/入料在
services/front_desk 与 services/workorder,本层只做鉴权 + 取值 + 调用。执行永远开工单,前门
不第二套引擎。interpret 桩恒 degraded(大脑由 FD-0b 接),且与手动开单零共享故障面。
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from core import db, feature_flags
from core.route_helpers import assert_owns_workspace, authorize_pearnly_ai
from services.authz.deps import check_workspace_scope
from services.front_desk import contract_store, intents, interpret, inventory

router = APIRouter()
logger = logging.getLogger(__name__)

# 工单 = 月度申报工作:前门确认即开工单,沿用 tax.filing.* 细码(与 workorder_routes 同权点)。
_C_VIEW = "tax.filing.view"
_C_PREPARE = "tax.filing.create"

# 暂存上限照 workorder_routes 补料口径:单文件 20MB、单次 50 件(一个月原料分批以内传完)。
_MAX_FILE_BYTES = 20 * 1024 * 1024
_MAX_FILES = 50
_MAX_UTTERANCE = 2000  # §3.3:超长截断,单次解析预算 ~1-2k token
_NOT_FOUND = "front_desk.not_found"
# 工单账期全链是佛历 "YYYY-MM"(interpret 建议是公历,换算在前端接缝);这里 fail-fast
# 拦格式漂移,防止混纪年期间开出错税期的工单。
_PERIOD_BE_RE = re.compile(r"^25\d{2}-(0[1-9]|1[0-2])$")


def _require_period_be(period: str) -> None:
    if not _PERIOD_BE_RE.fullmatch(period):
        raise HTTPException(422, detail={"code": "front_desk.bad_period", "period": period})


class InterpretIn(BaseModel):
    contract_id: str = Field(..., description="草稿合同 id")
    utterance: str = Field("", max_length=8000, description="用户说的目标(截断到 2000 再解析)")


class ConfirmIn(BaseModel):
    contract_id: str = Field(..., description="草稿合同 id")
    workspace_client_id: int = Field(..., description="人点选定的客户账套 id(账套红线:必人点)")
    period: str = Field(..., min_length=1, max_length=20, description="申报期,如 2569-05")
    intent: str = Field(..., max_length=40, description="人确认的意图(须为已开放闭集)")


def _authorize(request: Request, perm: str) -> tuple:
    """登录 + 双闸(pearnly_ai_m1 叠加 pearnly_ai_front_desk · 关→404 fail-closed)+ 动作权限。

    authorize_pearnly_ai 先判 m1 + 权限;再叠 front_desk 闸(front_desk 组合闸内部也含 m1,
    双查冗余但零害,任一关或异常均 fail-closed 404)。"""
    user, tenant_id = authorize_pearnly_ai(request, perm, not_found=_NOT_FOUND)
    if not feature_flags.pearnly_ai_front_desk_enabled_for(tenant_id):
        raise HTTPException(404, detail=_NOT_FOUND)
    return user, tenant_id


def _raise_front_desk(e: "contract_store.FrontDeskError") -> None:
    """FrontDeskError → 4xx。归属/不存在类 404,其余校验错 422。"""
    if e.code == "front_desk.contract_not_found":
        raise HTTPException(404, detail=e.code)
    detail = {"code": e.code, **e.context} if e.context else e.code
    raise HTTPException(422, detail=detail)


@router.post("/api/ai/front-desk/contracts")
async def create_contract(
    request: Request,
    workspace_client_id: Optional[int] = Form(None),
    period: Optional[str] = Form(None),
    intent: Optional[str] = Form(None),
    files: list[UploadFile] = File(default=[]),
):
    """建草稿合同 + 暂存投料。客户/期间/意图可空(先投料出盘点卡,后说目标填合同卡)。
    附件先挂草稿(未确认不进工单),盘点摘要零成本按文件名分组返回。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    if len(files) > _MAX_FILES:
        raise HTTPException(413, detail="front_desk.too_many_files")
    if period is not None:
        _require_period_be(period)
    contract_store.ensure_once()  # 首用自愈建表(独立事务,先于下面的写事务)

    # 段一:读入 + 封顶(不落盘)。给了客户 id 则先验归属(不给未授权请求写盘的机会)。
    staged: list[tuple[str, bytes, str]] = []  # (original_name, content, sha256)
    for upload in files:
        content = await upload.read(_MAX_FILE_BYTES + 1)
        if len(content) > _MAX_FILE_BYTES:
            raise HTTPException(413, detail="front_desk.file_too_large")
        if not content:
            continue  # 空 part(没选文件)跳过
        staged.append((upload.filename or "", content, hashlib.sha256(content).hexdigest()))

    with db.get_cursor(commit=True) as cur:
        if workspace_client_id is not None:
            assert_owns_workspace(
                cur, request, user, tenant_id, workspace_client_id, not_found=_NOT_FOUND
            )
        contract = contract_store.create_draft(
            cur,
            tenant_id=tenant_id,
            created_by=f"user:{user['id']}",
            workspace_client_id=workspace_client_id,
            period=period,
            intent=intent,
        )
        # 段二:落盘暂存(加密)+ 登记附件。落盘失败不半提交:整块在同事务。
        files_out = []
        for original_name, content, sha in staged:
            suffix = Path(original_name).suffix
            path = contract_store.stage_file(tenant_id, contract["id"], content, suffix or ".bin")
            row = contract_store.add_file(
                cur,
                tenant_id=tenant_id,
                contract_id=contract["id"],
                file_ref=str(path),
                original_name=original_name or None,
                sha256=sha,
            )
            files_out.append(row)

    return {
        "contract": contract_store.public_view(contract, files_out),
        "inventory": inventory.summarize([n or "" for n, _c, _s in staged]),
    }


@router.post("/api/ai/front-desk/interpret")
async def interpret_goal(req: InterpretIn, request: Request):
    """utterance → 大脑意图/客户/期间建议(taxops.intent 车道)。降级/闸关/异常 → degraded=True。

    大脑解析零写业务表——interpret 只只读客户名录做引用校验;这里把 utterance + 建议落**草稿**
    合同(合同卡刷新可服务端重建·消息流不建聊天表),执行永远等 confirm 端点人点确认。
    """
    user, tenant_id = _authorize(request, _C_PREPARE)
    contract_store.ensure_once()
    utterance = (req.utterance or "")[:_MAX_UTTERANCE]

    with db.get_cursor() as cur:
        contract = contract_store.get_contract(
            cur, tenant_id=tenant_id, contract_id=req.contract_id
        )
    if not contract:
        raise HTTPException(404, detail="front_desk.contract_not_found")

    # 解析(interpret 自取名录并全程 fail-closed;绝不上抛,故不与手动开单共享故障面)。
    suggestion = interpret.interpret(utterance, tenant_id=tenant_id, contract_id=req.contract_id)

    # 落草稿:utterance + 大脑建议(仅 draft 态可改·降级不覆盖既有建议)。
    if contract["status"] == contract_store.STATUS_DRAFT:
        with db.get_cursor(commit=True) as cur:
            contract_store.update_draft(
                cur,
                tenant_id=tenant_id,
                contract_id=req.contract_id,
                utterance_raw=utterance or None,
                brain_suggestion=None if suggestion["degraded"] else suggestion,
            )
    return {"contract_id": req.contract_id, "suggestion": suggestion}


@router.post("/api/ai/front-desk/confirm")
async def confirm_contract(req: ConfirmIn, request: Request):
    """人点确认:定客户/期间/意图 → 开工单(幂等)+ 暂存料经 intake.register_file 入料。

    意图未开放(闭集内但 enabled=False)→ 422 intent_not_enabled(诚实拒,不装懂)。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    _require_period_be(req.period)
    if not intents.is_enabled(req.intent):
        raise HTTPException(
            422, detail={"code": "front_desk.intent_not_enabled", "intent": req.intent}
        )
    contract_store.ensure_once()

    with db.get_cursor(commit=True) as cur:
        assert_owns_workspace(
            cur, request, user, tenant_id, req.workspace_client_id, not_found=_NOT_FOUND
        )
        contract = contract_store.get_contract(
            cur, tenant_id=tenant_id, contract_id=req.contract_id
        )
        if not contract:
            raise HTTPException(404, detail="front_desk.contract_not_found")
        # 人确认的最终值落草稿(合同卡「改客户」在此定案),再确认。
        if contract["status"] == contract_store.STATUS_DRAFT:
            contract_store.update_draft(
                cur,
                tenant_id=tenant_id,
                contract_id=req.contract_id,
                workspace_client_id=req.workspace_client_id,
                period=req.period,
                intent=req.intent,
            )
        try:
            out = contract_store.confirm(
                cur, tenant_id=tenant_id, contract_id=req.contract_id, actor=f"user:{user['id']}"
            )
        except contract_store.FrontDeskError as e:
            _raise_front_desk(e)
    return {"ok": True, **out}


@router.get("/api/ai/front-desk/feed")
async def get_feed(request: Request, client_id: Optional[int] = None, limit: int = 50):
    """重建消息流:该租户(可按客户筛)合同倒序。前端据 status 拼盘点/合同/进度卡。"""
    user, tenant_id = _authorize(request, _C_VIEW)
    contract_store.ensure_once()  # 首用自愈建表:feed 可能是首个被命中的端点(prod 无 alembic 升级路)
    limit = max(1, min(int(limit), 200))
    if client_id is not None:
        check_workspace_scope(request, user, client_id)
    with db.get_cursor() as cur:
        rows = contract_store.list_contracts(
            cur, tenant_id=tenant_id, workspace_client_id=client_id, limit=limit
        )
    return {"contracts": [contract_store.public_view(r) for r in rows]}
