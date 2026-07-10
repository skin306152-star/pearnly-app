# -*- coding: utf-8 -*-
"""冻结/归档服务编排(C-2 · 任务包设计 3/6)。

freeze.py 是纯 manifest 汇编;本模块做「取库 → 现算哈希 → 写盘 → 落事件 → 钉状态」的编排,
是 review→archive 这一步唯一入口。校验错抛 api.WorkOrderApiError(带 code/context),路由翻
4xx/409。冻结后工单只读:mutating 端点先过 assert_mutable(archive → 结构化拒)。

  - archive_order:原子冻结。六要素齐(逐 item sha256 现算 + 规则/模型版本 + 裁决回放 + 签批人
    + 时间)合成 freeze_manifest.json 交付物 + workorder_archived 事件 + status=archive。
    fail-closed:源文件缺失 → 拒绝并点名(freeze.FreezeError → 409)。幂等:已冻结 → 409。
  - verify_manifest:篡改校验(读侧)。逐 item 现算 sha256 与冻结 manifest 比对,点名不符。
  - attach_receipt:申报回执 append-only 补挂(冻结后唯一可写路径,不改 manifest 本体)。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from services.workorder import freeze, storage, store
from services.workorder.api import WorkOrderApiError

_STATUS_REVIEW = "review"  # engine.TERMINAL_STATUS:全 runnable 步绿停此,唯一可冻结起点
_STATUS_ARCHIVE = "archive"
_ARCHIVE_STEP = "archive"
_EVT_ARCHIVED = "workorder_archived"
_EVT_RECEIPT = "receipt_attached"


def assert_mutable(wo: dict) -> None:
    """冻结后拒绝一切结构化写(run/裁决/补料/upsert)。工单只读,唯回执可 append-only 补挂。"""
    if wo.get("status") == _STATUS_ARCHIVE:
        raise WorkOrderApiError("workorder.archived_readonly")


def _hash_source(file_ref: Optional[str]) -> Optional[str]:
    """现算源文件 sha256。file_ref 由 intake 登记(上传落工单目录 / CLI 操作者选定路径),
    非外部输入;读不到 → None 交冻结闸点名。"""
    return freeze.compute_source_hash(Path(file_ref)) if file_ref else None


def _manifest_summary(manifest: dict) -> dict:
    """交付物行 numbers 快照(概览):真 manifest 全文在 freeze_manifest.json。"""
    hashed = sum(1 for i in manifest["items"] if i["sha256"])
    return {
        "rules_version": manifest["rules_version"],
        "model_version": manifest["model_version"],
        "deliverable_version": manifest["deliverable_version"],
        "item_count": len(manifest["items"]),
        "hashed_source_count": hashed,
        "decision_count": len(manifest["decisions"]),
        "approved_by": manifest["approved_by"],
        "frozen_at": manifest["frozen_at"],
    }


def archive_order(cur, *, tenant_id: str, work_order_id: str, actor: str) -> dict:
    """review→archive 原子冻结。签批人=actor(触发归档的登录态),不做多角色审批(那是 C3)。"""
    wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not wo:
        raise WorkOrderApiError("workorder.not_found")
    if wo["status"] == _STATUS_ARCHIVE:
        raise WorkOrderApiError("workorder.already_archived")
    if wo["status"] != _STATUS_REVIEW:
        raise WorkOrderApiError("workorder.not_reviewable")

    version = store.current_deliverable_version(
        cur, tenant_id=tenant_id, work_order_id=work_order_id
    )
    if version < 1:
        raise WorkOrderApiError("workorder.no_deliverables")

    items = store.list_items(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    ocr_models = freeze.ocr_models_from_ai_usage(
        cur, tenant_id=tenant_id, item_ids=[it["id"] for it in items]
    )
    try:
        manifest = freeze.build_manifest(
            work_order=wo,
            items=items,
            events=events,
            deliverable_version=version,
            ocr_models=ocr_models,
            approver=actor,
            frozen_at=datetime.now(timezone.utc).isoformat(),
            sha256_of=_hash_source,
        )
    except freeze.FreezeError as exc:
        raise WorkOrderApiError(exc.code, context={"missing": exc.missing}) from exc

    out_dir = storage.versioned_dir(storage.deliverables_dir(tenant_id, work_order_id), version)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / freeze.MANIFEST_FILENAME
    # 唯一序列化出口(R1:真库事件行的 datetime 裁决时间戳直接 json.dumps 会 TypeError)。
    path.write_text(freeze.dumps_manifest(manifest), encoding="utf-8")

    summary = _manifest_summary(manifest)
    store.upsert_deliverable(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        kind=freeze.MANIFEST_KIND,
        version=version,
        artifact_path=str(path),
        numbers=summary,
    )
    store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=_ARCHIVE_STEP,
        event_type=_EVT_ARCHIVED,
        payload=summary,
        actor=actor,
        dedupe_key=f"archive:{work_order_id}",
    )
    store.set_status(cur, tenant_id=tenant_id, work_order_id=work_order_id, status=_STATUS_ARCHIVE)
    return {"status": _STATUS_ARCHIVE, "deliverable_version": version, "manifest": summary}


def _load_manifest(cur, *, tenant_id: str, work_order_id: str) -> Optional[dict]:
    for d in store.list_deliverables(cur, tenant_id=tenant_id, work_order_id=work_order_id):
        if d["kind"] == freeze.MANIFEST_KIND and d.get("artifact_path"):
            resolved = storage.resolve_within_order(tenant_id, work_order_id, d["artifact_path"])
            target = resolved or Path(d["artifact_path"])
            try:
                return json.loads(Path(target).read_text(encoding="utf-8"))
            except OSError:
                return None
    return None


def verify_manifest(cur, *, tenant_id: str, work_order_id: str) -> dict:
    """篡改校验:逐 item 现算 sha256 与冻结 manifest 比对(验收断言 4)。未冻结 → not_archived。
    返回 {ok, mismatches, missing}:mismatches=哈希不符(被改字节),missing=源文件已不在盘。"""
    manifest = _load_manifest(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if manifest is None:
        raise WorkOrderApiError("workorder.not_archived")
    mismatches, missing = [], []
    for rec in manifest.get("items", []):
        expected = rec.get("sha256")
        if not expected:
            continue  # 无源文件的件(人工填销项)本就无哈希,不校验
        actual = _hash_source(rec.get("file_ref"))
        if actual is None:
            missing.append({"item_id": rec["item_id"], "file_name": rec.get("file_name")})
        elif actual != expected:
            mismatches.append(
                {
                    "item_id": rec["item_id"],
                    "file_name": rec.get("file_name"),
                    "expected": expected,
                    "actual": actual,
                }
            )
    return {"ok": not mismatches and not missing, "mismatches": mismatches, "missing": missing}


def attach_receipt(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    content: bytes,
    original_name: Optional[str],
    actor: str,
) -> dict:
    """申报回执补挂(append-only):冻结后唯一可写路径。回执字节落工单目录 + 落 receipt_attached
    事件(带文件 sha256),不改已冻 manifest 本体。仅归档态可挂。"""
    wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not wo:
        raise WorkOrderApiError("workorder.not_found")
    if wo["status"] != _STATUS_ARCHIVE:
        raise WorkOrderApiError("workorder.not_archived")
    path = storage.save_material(
        tenant_id, work_order_id, content, ".pdf", original_name=original_name
    )
    digest = freeze.sha256_of_bytes(content)
    evt = store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=_ARCHIVE_STEP,
        event_type=_EVT_RECEIPT,
        payload={"file_ref": str(path), "original_name": original_name, "sha256": digest},
        actor=actor,
        dedupe_key=f"receipt:{digest}",
    )
    return {"sha256": digest, "file_ref": str(path), "event_id": evt["id"]}
