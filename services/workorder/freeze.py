# -*- coding: utf-8 -*-
"""冻结证据包 manifest 汇编(C-2 · 任务包设计 3/5)。

archive 动作把工单从 review 钉成不可变:逐 item 现算源文件 sha256 + 规则版本 + 模型版本 +
裁决/豁免回放 + 签批人 + 时间,六要素合成一份 freeze_manifest.json 交付物。本模块零副作用、
不碰 DB(除注入的 sha256_of/ai_usage 只读回调):输入是已查出的 items/events,输出是 manifest
或 FreezeError(点名)。回放复用 evidence(不另存副本);ocr_models 来自 C-1 的 ai_usage 归因
(单一事实源,不双写),ocr_engines 来自 item_classified 事件流(自证据流取,冻结自证明)。

fail-closed:任一 item 的源文件已不在盘(算不出 sha256)→ FreezeError 点名,绝不出残缺冻结包。
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Callable, Optional

from services.workorder import evidence, sod, storage

# 规则版本:裁决词汇(decisions.py)/守恒·勾稽闸逻辑变更时人工 bump,钉进每份冻结 manifest。
# 常量落此处而非 decisions.py(那是零依赖词汇叶子,契约零改动)——冻结包是它的唯一消费者。
RULES_VERSION = "wo-rules-2026.07"

MANIFEST_KIND = "freeze_manifest"
MANIFEST_FILENAME = "freeze_manifest.json"
SCHEMA = "workorder.freeze_manifest/v1"

_EVT_CLASSIFIED = "item_classified"
_EVT_DECISION = "human_decision"


class FreezeError(Exception):
    """冻结闸拒绝(fail-closed)。missing 点名算不出 sha256 的 item(源文件不在盘)。"""

    def __init__(self, code: str, *, missing: Optional[list] = None):
        super().__init__(code)
        self.code = code
        self.missing = missing or []


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _iso(v):
    """时间字段规整:真库事件行的 created_at 是 psycopg2 原生 datetime(R1 打回:直接进
    json.dumps 即 TypeError),统一转 ISO-8601 字符串;本就是字符串(测试替身/回读)原样过。"""
    return v.isoformat() if isinstance(v, (_dt.datetime, _dt.date)) else v


def _json_default(v):
    """manifest 序列化兜底:datetime/date → ISO 字符串,Decimal → 无损十进制字符串(禁 float)。
    其余未知类型 fail-loud——冻结包是审计原件,静默 str() 会把 bug 埋进不可变文件。"""
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return format(v, "f")
    raise TypeError(f"freeze manifest 不可序列化类型: {type(v).__name__}")


def dumps_manifest(manifest: dict) -> str:
    """冻结 manifest 的唯一序列化出口(archive 写盘用):已知非 JSON 原生类型确定性转换。"""
    return json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default)


def compute_source_hash(path: Optional[Path]) -> Optional[str]:
    """现算源文件 sha256;path 为 None(越界/已解析失败)或读不到 → None(交给闸点名)。"""
    if path is None:
        return None
    try:
        return sha256_of_bytes(Path(path).read_bytes())
    except OSError:
        return None


def _display_name(item: dict) -> Optional[str]:
    """展示用原始文件名:优先无损列 original_name,空回落落盘名反解(存量行不回填的兜底)。"""
    return item.get("original_name") or storage.original_name_of(item.get("file_ref"))


def _replay_decisions(events: list[dict]) -> dict:
    """裁决/豁免回放(复用 evidence,latest-wins)。每 item → 裁决动作 + 谁 + 何时 + 事件 id。"""
    replayed = evidence.replay_items_by_type(events, _EVT_DECISION)
    out: dict = {}
    for item_id, rec in replayed.items():
        payload = rec["payload"]
        out[item_id] = {
            "decision": payload.get("decision"),
            "kind": payload.get("kind"),
            "reason": payload.get("reason"),
            "values": payload.get("values") or {},
            "actor": rec.get("actor"),
            "at": _iso(rec.get("at")),  # 真库行是 datetime,源头规整成 ISO(R1)
            "event_id": rec.get("event_id"),
        }
    return out


def _ocr_engines(events: list[dict]) -> list:
    """从 item_classified 事件流取 distinct OCR 管线版本(冻结自证据流,不依赖外表)。"""
    replayed = evidence.replay_items_by_type(events, _EVT_CLASSIFIED)
    engines = {
        rec["payload"].get("ocr_engine")
        for rec in replayed.values()
        if rec["payload"].get("ocr_engine")
    }
    return sorted(engines)


def build_manifest(
    *,
    work_order: dict,
    items: list[dict],
    events: list[dict],
    deliverable_version: int,
    ocr_models: list,
    approver: str,
    frozen_at: str,
    sha256_of: Callable[[Optional[str]], Optional[str]],
) -> dict:
    """合成冻结 manifest(六要素齐)。sha256_of(file_ref)→现算哈希或 None;有 file_ref 却算不出
    (源文件不在盘)→ FreezeError 点名。无 file_ref 的件(人工填销项)源文件恒空,sha256=None
    非失败。"""
    item_records = []
    missing = []
    for it in items:
        file_ref = it.get("file_ref")
        digest = sha256_of(file_ref) if file_ref else None
        if file_ref and digest is None:
            missing.append(_display_name(it) or file_ref)
        item_records.append(
            {
                "item_id": it["id"],
                "kind": it.get("kind"),
                "status": it.get("status"),
                "file_name": _display_name(it),
                "file_ref": file_ref,
                "sha256": digest,
            }
        )
    if missing:
        raise FreezeError("workorder.freeze_source_missing", missing=sorted(missing))

    return {
        "schema": SCHEMA,
        "work_order_id": work_order["id"],
        "workspace_client_id": work_order.get("workspace_client_id"),
        "period": work_order.get("period"),
        "frozen_at": frozen_at,
        "approved_by": approver,
        "rules_version": RULES_VERSION,
        "model_version": {
            "ocr_engines": _ocr_engines(events),
            "ocr_models": sorted({m for m in (ocr_models or []) if m}),
        },
        "deliverable_version": int(deliverable_version),
        "items": item_records,
        "decisions": _replay_decisions(events),
        "signatures": _signatures(events, approver),
        "receipt": None,  # 申报回执 append-only 补挂(不改已冻 manifest 本体)
    }


def _signatures(events: list[dict], approver: str) -> dict:
    """签批四元组(additive · C3):制单集/复核签批人集合从事件流回放(与 sod.py 判定同一份
    事件流,不重算)。flag 关/开都如实回放——本块不受 SoD 强制闸门控,只是照实记「谁真的
    做了什么」,闸只管「允不允许」。approved_by 与顶层 approved_by 同值(冗余存一份供前端
    直接读 signatures 块不必再拼)。filed_by 冻结时恒空:回执 append-only 补挂不改已冻
    manifest 本体(与顶层 receipt 同语义),申报人查证走 receipt_attached 事件。"""
    return {
        "prepared_by": sorted(sod.preparer_actors(events)),
        "reviewed_by": sorted(sod.reviewer_actors(events)),
        "approved_by": approver,
        "filed_by": None,
    }


def ocr_models_from_ai_usage(cur, *, tenant_id: str, item_ids: list) -> list:
    """从 ai_usage 取本工单 classify 用过的模型名(C-1 归因单一事实源,只读不双写)。
    trace_id=item_id 由 classify._ocr_safe 打点;无行(无 OCR/被裁剪)返空。"""
    if not item_ids:
        return []
    cur.execute(
        "SELECT DISTINCT model FROM ai_usage "
        "WHERE tenant_id = %s AND task = 'workorder_classify' "
        "AND trace_id = ANY(%s) AND model IS NOT NULL",
        (tenant_id, list(item_ids)),
    )
    return [r["model"] if isinstance(r, dict) else r[0] for r in cur.fetchall()]
