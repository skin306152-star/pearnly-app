# -*- coding: utf-8 -*-
"""目标合同存储 + 状态机(ai_goal_contracts / ai_contract_files · 见施工总册 §3.2)。

草稿合同是「用户投料 + 说目标」到「开工单执行」之间的中转站:附件先挂草稿(未确认不进
工单),人点确认后经**唯一入料口** services/workorder/steps/intake.register_file 落成
work_order_items。前门不建第二套上传存储、不第二套引擎:暂存字节走工单 storage 的加密写
helper(ENC 契约,禁裸 open),执行永远开工单。

状态机:draft → confirmed/executing(开工单回填 work_order_id)→ delivered → archived;
任何未开工前可 rejected。幂等:confirm 按 (tenant, client, period, work_order_intent) 撞
工单唯一键即挂靠既有工单不重建(open_work_order 的 ON CONFLICT);已 registered 的附件不
重复入料(intake 的 sha256 指纹天然去重,再叠一层 staged→registered 状态过滤,零重复件)。

建表:alembic/versions/0079_front_desk_contracts.py 逐字对齐留档 + ensure_table 首用自愈
(prod alembic 指针停 0020,靠 ensure 补建,照 brain_shadow.ensure_table 先例)。
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Optional

from services.front_desk import intents
from services.workorder import storage

logger = logging.getLogger(__name__)

# 合同状态机(单一词汇表:路由/前端读这里,不各打字符串)。
STATUS_DRAFT = "draft"
STATUS_CONFIRMED = "confirmed"
STATUS_EXECUTING = "executing"
STATUS_DELIVERED = "delivered"
STATUS_ARCHIVED = "archived"
STATUS_REJECTED = "rejected"

# 附件状态:暂存 → 已入料(经 register_file)→ 丢弃(确认前用户删)。
FILE_STAGED = "staged"
FILE_REGISTERED = "registered"
FILE_DISCARDED = "discarded"

# confirm 可从这些态发起(幂等:confirmed/executing 重按不重建工单、不重复入料)。
_CONFIRMABLE = (STATUS_DRAFT, STATUS_CONFIRMED, STATUS_EXECUTING)

_CONTRACT_COLUMNS = (
    "id, tenant_id, workspace_client_id, period, intent, deliverables, status, "
    "utterance_raw, brain_suggestion, work_order_id, created_by, confirmed_by, "
    "created_at, updated_at"
)
_FILE_COLUMNS = "id, contract_id, tenant_id, file_ref, original_name, sha256, status, created_at"

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS ai_goal_contracts (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint,
        period text,
        intent text,
        deliverables jsonb NOT NULL DEFAULT '[]'::jsonb,
        status text NOT NULL DEFAULT 'draft',
        utterance_raw text,
        brain_suggestion jsonb NOT NULL DEFAULT '{}'::jsonb,
        work_order_id uuid,
        created_by text,
        confirmed_by text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_contract_files (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        contract_id uuid NOT NULL REFERENCES ai_goal_contracts (id) ON DELETE CASCADE,
        tenant_id uuid NOT NULL,
        file_ref text NOT NULL,
        original_name text,
        sha256 text,
        status text NOT NULL DEFAULT 'staged',
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
)

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_ai_goal_contracts_tenant "
    "ON ai_goal_contracts (tenant_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_ai_goal_contracts_client "
    "ON ai_goal_contracts (tenant_id, workspace_client_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_ai_contract_files_contract "
    "ON ai_contract_files (tenant_id, contract_id)",
)

_RLS_TABLES = ("ai_goal_contracts", "ai_contract_files")

# 暂存目录:复用工单 storage 的加密写 helper 落盘,布局与工单料分开(未确认料不混进工单树)。
# 与工单 storage 同 BASE(同一磁盘卷/加密开关),确认时读回明文再经 save_material 促成工单料。
_STAGE_SUBDIR = "_fd_contracts"

_ensured = False


class FrontDeskError(ValueError):
    """前门业务校验错(路由映射成 4xx)。code 给前端错误契约。"""

    def __init__(self, code: str, *, context: Optional[dict] = None):
        super().__init__(code)
        self.code = code
        self.context = context or {}


def ensure_table() -> None:
    """幂等建两表 + 索引 + tenant RLS(首用自愈 · 照 brain_shadow.ensure_table 先例;
    alembic 0079 逐字对齐留档)。独立事务,入口点(startup / 路由写端点)在锁表前先调。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)


def ensure_once() -> None:
    """进程内幂等的 ensure_table 包装(路由写端点首用调,避免每请求 DDL)。"""
    global _ensured
    if _ensured:
        return
    ensure_table()
    _ensured = True


# ── 合同 CRUD ────────────────────────────────────────────────


def create_draft(
    cur,
    *,
    tenant_id: str,
    created_by: str,
    workspace_client_id: Optional[int] = None,
    period: Optional[str] = None,
    intent: Optional[str] = None,
    utterance_raw: Optional[str] = None,
    deliverables: Optional[list] = None,
    brain_suggestion: Optional[dict] = None,
) -> dict:
    """建草稿合同。客户/期间/意图可空(先投料后说目标的流程:盘点卡先出,合同卡后填)。"""
    cur.execute(
        f"""
        INSERT INTO ai_goal_contracts
            (tenant_id, workspace_client_id, period, intent, deliverables,
             status, utterance_raw, brain_suggestion, created_by)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, %s)
        RETURNING {_CONTRACT_COLUMNS}
        """,
        (
            tenant_id,
            workspace_client_id,
            period,
            intent,
            json.dumps(deliverables or [], ensure_ascii=False),
            STATUS_DRAFT,
            utterance_raw,
            json.dumps(brain_suggestion or {}, ensure_ascii=False, default=str),
            created_by,
        ),
    )
    return dict(cur.fetchone())


def get_contract(cur, *, tenant_id: str, contract_id: str) -> Optional[dict]:
    cur.execute(
        f"SELECT {_CONTRACT_COLUMNS} FROM ai_goal_contracts " "WHERE tenant_id = %s AND id = %s",
        (tenant_id, contract_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_contracts(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """重建消息流用:该租户(可按客户筛)的合同倒序分页。前端据 status 拼盘点/合同/进度卡。"""
    cur.execute(
        f"SELECT {_CONTRACT_COLUMNS} FROM ai_goal_contracts "
        "WHERE tenant_id = %s "
        "AND (%s::bigint IS NULL OR workspace_client_id = %s::bigint) "
        "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s",
        (tenant_id, workspace_client_id, workspace_client_id, limit, offset),
    )
    return [dict(r) for r in cur.fetchall()]


def update_draft(
    cur,
    *,
    tenant_id: str,
    contract_id: str,
    workspace_client_id: Optional[int] = None,
    period: Optional[str] = None,
    intent: Optional[str] = None,
    utterance_raw: Optional[str] = None,
    brain_suggestion: Optional[dict] = None,
) -> None:
    """确认前改草稿的客户/期间/意图/utterance(合同卡「修改」+ 大脑建议回填)。只改传入的
    非 None 字段。仅 draft 态可改(已开工单的合同靠工单流程,不在此改)。"""
    set_clause, params = [], []
    for col, val in (
        ("workspace_client_id", workspace_client_id),
        ("period", period),
        ("intent", intent),
        ("utterance_raw", utterance_raw),
    ):
        if val is not None:
            set_clause.append(f"{col} = %s")
            params.append(val)
    if brain_suggestion is not None:
        set_clause.append("brain_suggestion = %s::jsonb")
        params.append(json.dumps(brain_suggestion, ensure_ascii=False, default=str))
    if not set_clause:
        return
    set_clause.append("updated_at = now()")
    params.extend([tenant_id, contract_id, STATUS_DRAFT])
    cur.execute(
        f"UPDATE ai_goal_contracts SET {', '.join(set_clause)} "
        "WHERE tenant_id = %s AND id = %s AND status = %s",
        tuple(params),
    )


def reject(cur, *, tenant_id: str, contract_id: str) -> None:
    """撤销草稿(合同卡撤回)。已开工单(有 work_order_id)不在此撤——那走工单作废流程。"""
    cur.execute(
        "UPDATE ai_goal_contracts SET status = %s, updated_at = now() "
        "WHERE tenant_id = %s AND id = %s AND work_order_id IS NULL",
        (STATUS_REJECTED, tenant_id, contract_id),
    )


# ── 附件(暂存 → 入料)────────────────────────────────────────


def stage_file(tenant_id: str, contract_id: str, content: bytes, suffix: str = ".bin") -> Path:
    """把上传字节加密落到合同暂存目录,返回绝对路径(禁裸 open:走 storage 的加密写 helper)。
    未确认前不进工单;确认时读回明文经 save_material 促成 work_order 料。"""
    base = os.environ.get("WORKORDER_STORAGE_DIR", "/opt/mrpilot/storage/workorders")
    tenant_short = str(tenant_id).replace("-", "")[:8] or "unknown"
    dest_dir = Path(base) / _STAGE_SUBDIR / tenant_short / str(contract_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = suffix if (suffix.startswith(".") and 2 <= len(suffix) <= 6) else ".bin"
    path = dest_dir / f"{uuid.uuid4().hex}{ext}"
    return storage.write_artifact_bytes(path, content)


def add_file(
    cur,
    *,
    tenant_id: str,
    contract_id: str,
    file_ref: str,
    original_name: Optional[str],
    sha256: str,
) -> dict:
    """登记一件暂存附件(sha256 = 明文字节指纹,与 intake 指纹同口径,确认入料时逐字节对齐)。"""
    cur.execute(
        f"""
        INSERT INTO ai_contract_files
            (contract_id, tenant_id, file_ref, original_name, sha256, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING {_FILE_COLUMNS}
        """,
        (contract_id, tenant_id, file_ref, original_name, sha256, FILE_STAGED),
    )
    return dict(cur.fetchone())


def list_files(
    cur, *, tenant_id: str, contract_id: str, status: Optional[str] = None
) -> list[dict]:
    if status is None:
        cur.execute(
            f"SELECT {_FILE_COLUMNS} FROM ai_contract_files "
            "WHERE tenant_id = %s AND contract_id = %s ORDER BY created_at",
            (tenant_id, contract_id),
        )
    else:
        cur.execute(
            f"SELECT {_FILE_COLUMNS} FROM ai_contract_files "
            "WHERE tenant_id = %s AND contract_id = %s AND status = %s ORDER BY created_at",
            (tenant_id, contract_id, status),
        )
    return [dict(r) for r in cur.fetchall()]


def _set_file_status(cur, *, tenant_id: str, file_id: str, status: str) -> None:
    cur.execute(
        "UPDATE ai_contract_files SET status = %s WHERE tenant_id = %s AND id = %s",
        (status, tenant_id, file_id),
    )


# ── confirm:开工单 + 唯一入料口 register_file ────────────────


def confirm(cur, *, tenant_id: str, contract_id: str, actor: str) -> dict:
    """人点确认 → 开工单(幂等)+ 逐个暂存附件经 intake.register_file 入料 → 回填 work_order_id。

    校验(fail-closed):合同须存在、可确认态、客户已点(账套红线:workspace_client_id 非空)、
    期间已定、意图为已开放闭集。任一不满足抛 FrontDeskError,零副作用。
    幂等:重按不重建工单(open_work_order ON CONFLICT)、已 registered 附件不重复入料。
    """
    from services.workorder import api as wo_api, engine
    from services.workorder.steps import intake

    contract = get_contract(cur, tenant_id=tenant_id, contract_id=contract_id)
    if not contract:
        raise FrontDeskError("front_desk.contract_not_found")
    if contract["status"] not in _CONFIRMABLE:
        raise FrontDeskError("front_desk.not_confirmable", context={"status": contract["status"]})
    ws_id = contract["workspace_client_id"]
    if not ws_id:
        raise FrontDeskError("front_desk.client_required")  # 账套红线:客户必须人点
    if not contract["period"]:
        raise FrontDeskError("front_desk.period_required")
    intent_def = intents.get(contract["intent"])
    if not (intent_def and intent_def.enabled):
        raise FrontDeskError(
            "front_desk.intent_not_enabled", context={"intent": contract["intent"]}
        )

    wo = wo_api.open_order(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=ws_id,
        period=contract["period"],
        intent=intent_def.work_order_intent,
    )
    ctx = engine.StepContext(cur=cur, tenant_id=tenant_id, work_order_id=wo["id"])

    registered = []
    for f in list_files(cur, tenant_id=tenant_id, contract_id=contract_id, status=FILE_STAGED):
        plaintext = storage.read_bytes(Path(f["file_ref"]))
        suffix = Path(f["original_name"] or f["file_ref"]).suffix
        material = storage.save_material(
            tenant_id, wo["id"], plaintext, suffix or ".bin", original_name=f["original_name"]
        )
        item = intake.register_file(ctx, material, "upload")
        _set_file_status(cur, tenant_id=tenant_id, file_id=f["id"], status=FILE_REGISTERED)
        registered.append({"item_id": item["id"], "sha256": f["sha256"]})

    cur.execute(
        "UPDATE ai_goal_contracts SET work_order_id = %s, status = %s, "
        "confirmed_by = %s, updated_at = now() WHERE tenant_id = %s AND id = %s",
        (wo["id"], STATUS_EXECUTING, actor, tenant_id, contract_id),
    )
    return {"work_order_id": wo["id"], "registered": registered, "count": len(registered)}


def public_view(contract: dict, files: Optional[list] = None) -> dict[str, Any]:
    """合同 → 前端安全视图(消息流/合同卡渲染用)。附件只暴露展示字段,不吐 file_ref 绝对路径。"""
    out = {
        "id": str(contract["id"]),
        "workspace_client_id": contract.get("workspace_client_id"),
        "period": contract.get("period"),
        "intent": contract.get("intent"),
        "status": contract.get("status"),
        "deliverables": contract.get("deliverables") or [],
        "work_order_id": contract.get("work_order_id") and str(contract["work_order_id"]),
    }
    if files is not None:
        out["files"] = [
            {"id": str(f["id"]), "name": f.get("original_name"), "status": f.get("status")}
            for f in files
        ]
    return out
