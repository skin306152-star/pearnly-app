# -*- coding: utf-8 -*-
"""智能管家 HTTP API:会话 + 消息 + 任务(B3 起消息异步:入队秒回,执行在 worker)。

十端点(前端契约,static/ai/ai-api-steward.js 逐条对齐):
  GET  /api/ai/steward/status                  闸态探针(闸关也回 200 {enabled:false})+ 上传限额
  POST /api/ai/steward/sessions                建会话
  GET  /api/ai/steward/sessions/{sid}          重建消息流 + 附件 + 当前任务 id
  POST /api/ai/steward/sessions/{sid}/attachments 附件上传(附上即传·零模型零扣费零业务写)
  POST /api/ai/steward/sessions/{sid}/messages 说一句话 → 立即应承(+ 入队的任务 id)
  GET  /api/ai/steward/attachments/{aid}/download 下载自己传的原件(鉴权 + 租户 + 防穿越 + 审计)
  GET  /api/ai/steward/tasks/{tid}             左窗任务数据(轮询;失联任务就地收口)
  POST /api/ai/steward/tasks/{tid}/cancel      取消还在跑的只读任务(幂等;写工具在跑时 409)
  POST /api/ai/steward/authorizations/approve  批准写授权卡(token 走 body 不进 URL/访问日志)
  POST /api/ai/steward/authorizations/reject   拒绝写授权卡(任务收 cancelled·一步没执行)

除 status 外全组挂 `pearnly_ai_steward`(tenant 级默认关 · fail-closed · 叠加 pearnly_ai_m1):
闸关一律 404 —— 对存量用户等于不存在。status 走 m1 鉴权但把 steward 闸态当数据返回,免得
闸关用户每开一次 /ai 就吃一条 404(照 front_desk /status 先例)。

权限:读端点统一 tax.filing.view(管家能看到的每一样都是「看申报工作」这一层的东西);
批准写授权卡要 tax.filing.approve(签批级动作,复用 C3 四权分立的现成码不另立),拒绝仍是
view —— 喊停永远是安全侧,谁看得见谁就能拦。权限判在 token 消费之前:无权点批准不烧卡。

编排薄:本层只做鉴权 + 作用域 + 取值,一句话怎么变成任务在 services/steward。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, Field

from core import db, feature_flags
from core.route_helpers import authorize_pearnly_ai, content_disposition
from routes.steward_common import NOT_FOUND as _NOT_FOUND
from routes.steward_common import authorize_steward as _authorize
from routes.steward_common import session_or_404 as _session_or_404
from services.audit import file_access as audit_file_access
from services.authz.deps import get_authz
from services.steward import (
    attach_intake,
    attachments,
    authz,
    brain_entry,
    copy as steward_copy,
    sessions_dal,
    store,
    worker,
)
from services.steward.registry import ToolContext
from services.workorder import intake_prep

router = APIRouter()
logger = logging.getLogger(__name__)

_C_VIEW = "tax.filing.view"
_C_APPROVE = "tax.filing.approve"
_CANCEL_LOCKED = "steward.cancel_locked"
_EMPTY_TURN = "steward.empty_turn"
_MAX_TEXT = 2000
_MAX_PAGE = 200


class ActionIn(BaseModel):
    """回执卡上的闭集按钮。歧义已被这一次点击解决,所以这一轮【不过 planner】——
    工具名与附件 id 都是按钮自己带的,再让模型猜一遍就是把解决掉的问题重新引进来。"""

    tool: str = Field(..., min_length=1, max_length=64)
    attachment_ids: list[str] = Field(default_factory=list, max_length=20)
    confirm_spend: bool = Field(False, description="true = 会计已同意为这份料调一次模型")


class MessageIn(BaseModel):
    # min_length=0:纯文件零文字是万能口的核心手势(拖进来就送出)。文字与附件与按钮
    # 三样全空才是「什么都没说」,在处理函数里 422 —— 那是形状对但内容空,不是格式错。
    text: str = Field("", max_length=8000, description="会计说的一句话(可为空:纯文件送出)")
    lang: str = Field("", max_length=8, description="回复语言(zh/th);不给则按这句话自判")
    attachment_ids: list[str] = Field(
        default_factory=list, max_length=20, description="这一轮带上的附件 id"
    )
    action: Optional[ActionIn] = Field(None, description="点了回执卡上的按钮时带")


class AuthzDecisionIn(BaseModel):
    token: str = Field(..., min_length=8, max_length=64, description="授权卡一次性令牌")


# 鉴权双闸与会话归属判定收口在 routes/steward_common.py(三个 steward 路由文件同一套门)。


def _context(request: Request, user: dict, tenant_id: str, lang: str = "") -> ToolContext:
    """工具执行身份:账套作用域与 /api/tax-profile/matrix 同源(被分派成员只看分到的)。"""
    authz = get_authz(request, user)
    allowed = None
    if not user.get("is_super_admin") and authz.scope_mode == "assigned":
        allowed = frozenset(int(i) for i in (authz.workspace_ids or frozenset()))
    return ToolContext(
        user=user,
        tenant_id=tenant_id,
        user_id=str(user["id"]),
        allowed_client_ids=allowed,
        lang=lang,
    )


@router.get("/api/ai/steward/status")
async def get_status(request: Request):
    """探针专用:闸态当数据返回,不走闸 404(前端据此挂三态,免 console 噪音)。

    上传限额一并带出去:前端在【选文件的当下】就要按同一份上限先拒一次(省一次无效上传),
    但这份上限的单一事实源在 services/steward/attachments —— 前端硬编码一份,两处必漂。"""
    _user, tenant_id = authorize_pearnly_ai(request, _C_VIEW, not_found=_NOT_FOUND)
    return {
        "enabled": bool(feature_flags.pearnly_ai_steward_enabled_for(tenant_id)),
        "attachments": attachments.limits(),
    }


@router.post("/api/ai/steward/sessions")
async def create_session(request: Request):
    """建会话。标题留空,第一句话落库时自动填(见 orchestrator)。"""
    user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        session = store.create_session(cur, tenant_id=tenant_id, user_id=str(user["id"]))
    return {"session_id": str(session["id"])}


@router.get("/api/ai/steward/sessions/{session_id}")
async def get_session(
    session_id: str,
    request: Request,
    before: Optional[str] = None,
    limit: int = 60,
):
    """重建消息流(刷新页面靠服务端重建,不在浏览器存对话)。附件按消息分组一并回:
    用户气泡下面那行附件是永久留痕,刷新后不该消失。

    游标分页(S1):默认回最近一页;before=已拿到的最早那条消息 id 时回更早一页。
    还有更早的才给 has_more=true(条件键,老前端与既有 E2E 桩不受影响)。"""
    user, tenant_id = _authorize(request)
    store.ensure_once()
    page = max(1, min(int(limit), _MAX_PAGE))
    with db.get_cursor() as cur:
        _session_or_404(cur, tenant_id=tenant_id, session_id=session_id, user_id=str(user["id"]))
        messages, has_more = sessions_dal.list_messages_page(
            cur, tenant_id=tenant_id, session_id=session_id, before_id=before, limit=page
        )
        current = store.latest_task_id(cur, tenant_id=tenant_id, session_id=session_id)
        files = attachments.list_for_message(cur, tenant_id=tenant_id, session_id=session_id)
    by_message = attachments.group_by_message(files)
    out = {
        "session_id": session_id,
        "messages": [
            {**store.public_message(m), **attachments.files_of(by_message, m["id"])}
            for m in messages
        ],
    }
    if has_more:
        out["has_more"] = True
    if current:
        out["current_task_id"] = current
    return out


@router.post("/api/ai/steward/sessions/{session_id}/attachments")
async def add_attachments(
    session_id: str,
    request: Request,
    files: list[UploadFile] = File(...),
    password: Optional[str] = Form(None),
):
    """附件上传(附上即传,与送出解耦)。这一步零模型、零扣费、零业务写 —— 只做:
    运输皮归一(zip/HEIC/密码 PDF/伪扩展名)→ 落盘 → 落行 → 逐件跑确定性识别 + 本地报价。

    封顶读法:最多读单件上限 +1 字节,超限即 413,不把超大文件整读进内存(同工单收料)。"""
    user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor() as cur:
        _session_or_404(cur, tenant_id=tenant_id, session_id=session_id, user_id=str(user["id"]))

    try:
        landed = attach_intake.accept(
            user=user,
            tenant_id=tenant_id,
            session_id=session_id,
            pairs=await _read_uploads(files),
            password=password,
        )
    except attach_intake.AttachmentLimitError as e:
        raise HTTPException(
            413, detail={"code": e.code, "limit": e.limit, "actual": e.actual}
        ) from e
    except intake_prep.IntakePrepError as e:
        # 结构化 422:{code, message(四语), ...逐件点名 context}。整批零残留由 accept 保证。
        raise HTTPException(
            422, detail={"code": e.code, "message": e.message_map(), **e.context}
        ) from e
    return {"attachments": landed, "count": len(landed)}


async def _read_uploads(files: list[UploadFile]) -> list[tuple[str, bytes]]:
    """读 part → [(文件名, 字节)]。三道闸判在读的过程中,不留到读完再一起判(照
    workorder_routes.add_materials 的先例):件数在【读第一件之前】判,单件与单批总量在
    【每读完一件】判。全交给 accept 里的 check_limits 等于先把整批攒进内存 —— 一个登录用户
    POST 1000 个 20MB 的 part,进程要先吃 ~20GB 才轮到那句「一次最多 20 件」;规规矩矩传
    20 件也要先吃 400MB 才发现单批 35MB 超了。单批上限本身就是「这批不该被读完」的声明。"""
    if len(files) > attachments.MAX_FILES_PER_MESSAGE:
        raise attach_intake.AttachmentLimitError(
            attach_intake.ERR_TOO_MANY, attachments.MAX_FILES_PER_MESSAGE, len(files)
        )
    pairs: list[tuple[str, bytes]] = []
    total = 0
    for upload in files:
        content = await upload.read(attachments.MAX_FILE_BYTES + 1)
        if len(content) > attachments.MAX_FILE_BYTES:
            raise attach_intake.AttachmentLimitError(
                attach_intake.ERR_TOO_LARGE, attachments.MAX_FILE_BYTES, len(content)
            )
        total += len(content)
        if total > attachments.MAX_BATCH_BYTES:
            raise attach_intake.AttachmentLimitError(
                attach_intake.ERR_BATCH_TOO_LARGE, attachments.MAX_BATCH_BYTES, total
            )
        pairs.append((upload.filename or "", content))
    return pairs


@router.post("/api/ai/steward/sessions/{session_id}/messages")
async def post_message(session_id: str, req: MessageIn, request: Request):
    """说一句话(或者只把料拖进来)→ 立即返回应承;派了活就给 task_id + task_status,
    前端轮询左窗看真进度。工具执行在后台 worker,追问/降级/超范围/回执卡仍当场回。"""
    user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor() as cur:
        _session_or_404(cur, tenant_id=tenant_id, session_id=session_id, user_id=str(user["id"]))
    text = req.text.strip()[:_MAX_TEXT]
    action = req.action.model_dump() if req.action else None
    ids = list(action["attachment_ids"]) if action else list(req.attachment_ids)
    if not text and not ids and not action:
        raise HTTPException(422, detail=_EMPTY_TURN)
    ctx = _context(request, user, tenant_id, lang=req.lang)
    # brain_entry 是分岔口(闸开 = 大脑循环 / 闸关、带附件、带按钮 = 原样交 orchestrator),
    # 不是新的一层编排:参数透传,闸关时行为与直调 orchestrator 逐字节相同。
    return brain_entry.handle_message(
        ctx, session_id=session_id, text=text, attachment_ids=tuple(ids), action=action
    )


@router.get("/api/ai/steward/attachments/{attachment_id}/download")
async def download_attachment(attachment_id: str, request: Request):
    """下载自己传进对话的原件。三道防线同 workorder 的 get_item_image:
    ①只放行库里登记过的 file_ref;②路径必须仍落在本会话目录之下(防穿越);③落库审计。
    取的是 (租户, id, 上传人) 三锚 —— 会话是私人工作记录,同租户别人也不给下。"""
    user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor() as cur:
        row = attachments.get_owned(
            cur, tenant_id=tenant_id, attachment_id=attachment_id, user_id=str(user["id"])
        )
    payload = attachments.download_payload(tenant_id, row) if row else None
    if not payload:
        raise HTTPException(404, detail=_NOT_FOUND)
    content, media_type, name = payload
    audit_file_access.log_user_file_access(
        request,
        user,
        audit_file_access.MATERIAL_VIEWED,
        target_type="steward_attachment",
        target_id=attachment_id,
        details={"kind": "steward_attachment", "session_id": str(row["session_id"])},
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition(name, "attachment")},
    )


@router.get("/api/ai/steward/tasks/{task_id}")
async def get_task(task_id: str, request: Request):
    """左窗任务数据(前端直接喂 B1 状态组件)。查询前先把失联任务就地收口 ——
    worker 死了/急停了,轮询的人也要在超时限后看到诚实的 failed,不是永远转圈。"""
    _user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        worker.heal_stale(cur, tenant_id=tenant_id, task_id=task_id)
        task = store.get_task(cur, tenant_id=tenant_id, task_id=task_id)
    if not task:
        raise HTTPException(404, detail=_NOT_FOUND)
    return store.public_task(task)


@router.post("/api/ai/steward/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, request: Request):
    """取消任务。只有还在跑的只读任务能取消;已收尾的原样返回(幂等,连点两下不报错)。
    与 worker 收尾赛跑时先落者赢:取消落定后,晚到的执行结果被 finish 守卫拒收。

    写工具在跑 = 已经批准、多半已经 submit_write:落 cancelled 等于告诉会计「后面的步骤没有
    跑」,而票可能已经写进账套;更糟的是作业号随之丢掉(worker 拿到 docnum 时任务已终态,
    finish 守卫拒收,只在日志里打一行),会计连去对账的钥匙都没有。故这条路直接 409 拒。"""
    _user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        task = store.get_task(cur, tenant_id=tenant_id, task_id=task_id)
        if not task:
            raise HTTPException(404, detail=_NOT_FOUND)
        if task["status"] == store.TASK_RUNNING:
            if not store.cancellable(task):
                raise HTTPException(409, detail=_CANCEL_LOCKED)
            tool = str((task.get("payload") or {}).get("tool") or "")
            lang = (task.get("payload") or {}).get("lang") or steward_copy.DEFAULT_LANG
            reason = steward_copy.fail_reason(worker.ERR_CANCELLED, lang, tool=tool)
            cancelled = store.cancel_task(
                cur,
                tenant_id=tenant_id,
                task_id=task_id,
                steps=store.fail_steps(task.get("steps") or [], reason),
            )
            task = cancelled or store.get_task(cur, tenant_id=tenant_id, task_id=task_id)
    return store.public_task(task)


@router.post("/api/ai/steward/authorizations/approve")
async def approve_authorization(req: AuthzDecisionIn, request: Request):
    """批准写授权卡:token 原子消费(单次单用)→ 参数指纹比对 → 任务复跑。
    权限(tax.filing.approve)判在消费之前 —— 无权点批准不烧卡,拿到权限后同一张卡仍可批。"""
    user, tenant_id = _authorize(request, perm=_C_APPROVE)
    return _decide_authorization(user, tenant_id, req.token, approve=True)


@router.post("/api/ai/steward/authorizations/reject")
async def reject_authorization(req: AuthzDecisionIn, request: Request):
    """拒绝写授权卡:任务收 cancelled,一步没执行。喊停是安全侧,view 权限即可。"""
    user, tenant_id = _authorize(request)
    return _decide_authorization(user, tenant_id, req.token, approve=False)


def _decide_authorization(user: dict, tenant_id: str, token: str, *, approve: bool) -> dict:
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        out = authz.decide(cur, tenant_id=tenant_id, token=token, actor=user, approve=approve)
    if not out["ok"]:
        raise HTTPException(out["http"], detail=out["code"])
    return {
        "task_id": out["task_id"],
        "authorization": authz.public_authorization_card(out["authorization"]),
    }
