# -*- coding: utf-8 -*-
"""ERP 桥出站接口(hello / lease / ack)+ 管理端铸密钥 · 列桥。

拓扑:桥装在客户内网能读 ERP 数据共享的机器上,**桥主动外拨连云端**,云端永远不主动
连桥(内网不开洞)。桥侧三个动作:注册+心跳(hello)、领任务(lease,长轮询)、回结果
(ack)。与小助手 companion 零共享通道:独立密钥前缀 brg_、独立表、独立路由前缀。

鉴权:桥侧走 Authorization: Bearer brg_<bridge_id>_<secret>(库里只存 sha256);管理端
两条走网页会话 + settings.org.* 权限码。密钥所级 —— 一个租户配一次全所会计继承。

长轮询取舍(为什么敢在同步栈里挂 20 秒):本仓是 FastAPI + uvicorn --workers 2,每个
worker 是一个事件循环,挂起的 async 请求占的是一个 Task + 一条 socket,不是线程也不是
worker;真正稀缺的是 psycopg2 连接池(每 worker maxconn=15),所以每一拍都开-查-关,
绝不把游标跨 await 拿着。窗口默认 20s(见 bridge.poll_hold_seconds:Nginx 未设
proxy_read_timeout = 默认 60s,留两倍余量)。DB 每拍一查而不是 LISTEN/NOTIFY:桥按所计
数量是个位数,20s 窗口 = 20 次主键查询,不值得为它引入连接常驻的通知通道。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.auth.entrance import require_erp_portal
from services.authz.deps import require_perm
from services.erp.bridge import bridge_enabled, poll_hold_seconds
from services.erp.bridge import store

logger = logging.getLogger("mr-pilot")

router = APIRouter()

# 长轮询每拍间隔:没任务时的空转成本 = 每秒一次主键查询 × 在线桥数(个位数)。
_TICK_SECONDS = 1.0


def _require_enabled() -> None:
    if not bridge_enabled():
        raise HTTPException(404, detail="erp.bridge_disabled")


def _auth_bridge(request: Request) -> Dict[str, Any]:
    """Bearer 密钥 → 桥行;失败 401(不区分"没这座桥"与"密钥错",不给枚举面)。"""
    header = request.headers.get("authorization") or ""
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    bridge = store.authenticate(token)
    if not bridge:
        raise HTTPException(401, detail="erp.bridge_unauthorized")
    return bridge


def _assert_self(bridge: Dict[str, Any], claimed: Optional[str]) -> None:
    """请求体里的 bridge_id 只是自述 —— 与密钥解出的身份不符即拒,身份只认密钥。"""
    if claimed and str(claimed) != str(bridge["id"]):
        raise HTTPException(403, detail="erp.bridge_id_mismatch")


def _tenant_of(user: dict) -> str:
    tenant_id = (user or {}).get("tenant_id")
    if not tenant_id:
        raise HTTPException(403, detail="erp.bridge_no_tenant")
    return str(tenant_id)


class BookRef(BaseModel):
    book_id: str = Field(..., min_length=1, max_length=64)
    dir: Optional[str] = None
    company: Optional[str] = None
    taxid: Optional[str] = None


class HelloRequest(BaseModel):
    bridge_id: Optional[str] = None
    bridge_version: Optional[str] = None
    role: str = "read"
    books: List[BookRef] = Field(default_factory=list)
    host: Optional[str] = None


class LeaseRequest(BaseModel):
    bridge_id: Optional[str] = None
    max: int = Field(1, ge=1, le=10)


class AckRequest(BaseModel):
    job_id: str
    bridge_id: Optional[str] = None
    ok: bool = True
    result: Optional[dict] = None
    error: Optional[dict] = None


class MintRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)
    role: str = "read"


# ── 桥侧(Bearer)─────────────────────────────────────────────────────────
@router.post("/api/erp/bridge/hello")
async def erp_bridge_hello(req: HelloRequest, request: Request):
    """注册 + 心跳(60s 一拍)· 上报本桥看得见的账套清单,拿回生效角色与轮询窗口。

    写桥唯一闸:同一账套已有在线写桥时,后来者 effective_role 降为 read 并在 note 里说明,
    桥必须遵守 —— P1 只做 read,字段与闸现在就落地,免得开写那天才发现双写没人拦。
    """
    _require_enabled()
    bridge = _auth_bridge(request)
    _assert_self(bridge, req.bridge_id)
    res = await asyncio.to_thread(
        store.register_hello,
        bridge,
        role=req.role,
        books=[b.model_dump() for b in req.books],
        bridge_version=req.bridge_version,
        host=req.host,
    )
    holder = res.get("held_by")
    body = {
        "ok": True,
        "bridge_id": str(bridge["id"]),
        "effective_role": res["effective_role"],
        "poll_hold_seconds": poll_hold_seconds(),
        "books_registered": res["books"],
    }
    if holder:
        body["note"] = f"该账套已有在线写桥({holder.get('name') or holder.get('id')})· 本桥降为只读"
    return body


@router.post("/api/erp/bridge/lease")
async def erp_bridge_lease(req: LeaseRequest, request: Request):
    """领任务 · 长轮询:有活立刻返回,没活挂到 poll_hold_seconds 再返空数组。

    桥拿到空数组会立刻发起下一次,形成准实时通道。每一拍单独开关游标(见文件头取舍),
    客户端断开时 asyncio.CancelledError 会顺着 await 冒出去,不留悬挂 Task。
    """
    _require_enabled()
    bridge = _auth_bridge(request)
    _assert_self(bridge, req.bridge_id)
    deadline = asyncio.get_running_loop().time() + poll_hold_seconds()
    while True:
        jobs = await asyncio.to_thread(store.lease_jobs, bridge, req.max)
        if jobs:
            return {"ok": True, "lease_seconds": store.LEASE_SECONDS, "jobs": _shape(jobs)}
        if asyncio.get_running_loop().time() >= deadline:
            return {"ok": True, "lease_seconds": store.LEASE_SECONDS, "jobs": []}
        await asyncio.sleep(_TICK_SECONDS)


def _shape(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "job_id": str(j["id"]),
            "kind": j.get("kind"),
            "book_id": j.get("book_id"),
            "payload": j.get("payload") or {},
        }
        for j in jobs
    ]


@router.post("/api/erp/bridge/ack")
async def erp_bridge_ack(req: AckRequest, request: Request):
    """回结果 · 落 done/failed 唤醒等待方。超 2MB 的结果截断并标 truncated。"""
    _require_enabled()
    bridge = _auth_bridge(request)
    _assert_self(bridge, req.bridge_id)
    res = await asyncio.to_thread(
        store.finish_job, bridge, req.job_id, req.ok, req.result, req.error
    )
    if not res.get("ok"):
        raise HTTPException(409, detail=f"erp.bridge_{res.get('reason', 'ack_failed')}")
    return res


# ── 管理端(网页会话)─────────────────────────────────────────────────────
@router.post("/api/erp/bridges")
async def erp_bridge_mint(req: MintRequest, request: Request):
    """铸所级密钥 · 明文只返一次(库里只存 sha256)· 全所会计继承同一把。"""
    _require_enabled()
    user = require_perm(request, "settings.org.edit")
    require_erp_portal(user)
    tenant_id = _tenant_of(user)
    res = await asyncio.to_thread(store.mint_bridge, tenant_id, req.name, req.role)
    logger.info(
        "[erp-bridge] 铸密钥 tenant=%s bridge=%s role=%s", tenant_id, res["bridge_id"], res["role"]
    )
    return {"ok": True, "note": "shown once; store securely", **res}


@router.get("/api/erp/bridges")
async def erp_bridge_list(request: Request):
    """列本租户的桥与在线状态(永不返密钥)。"""
    _require_enabled()
    user = require_perm(request, "settings.org.view")
    require_erp_portal(user)
    from services.erp.bridge import client as bridge_client

    status = await asyncio.to_thread(bridge_client.bridge_status, _tenant_of(user))
    return {"ok": True, **status}
