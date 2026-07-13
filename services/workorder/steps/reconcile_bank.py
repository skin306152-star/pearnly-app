# -*- coding: utf-8 -*-
"""R3 银行流水逐笔对平 + OCR 解析逐件检查点(MC2-A2 ① · 件 4)。

从 reconcile.py 抽出银行段(单文件 <500 铁律),行为逐字节不变的基础上补上 C1 检查点:
银行流水解析(≈OCR,vertex 慢)原本整批压在 reconcile 单事务里,中断即整批重烧、进度假死。
照 classify 的 C1 范式 1:1 移植——每件独立事务提交 + 批前从已提交 item_bank_parsed 事件重建
已解析件表(防复件双计的血泪必须带上)+ 逐件心跳续约(checkpoint.item_scope 现成)。与
MC2-0 reaper 续跑天然衔接:杀进程→重启,已解析银行件零重烧,事件计数守恒。

佐证层纪律:对平结果只挂 R3 gate + 证据链,绝不 stuck、绝不阻断 package;任何异常收进 note
不上抛。税额来自 R1/R2 不来自银行对账。闸(pearnly_ai_bank_recon)关 → run_bank_recon 返 None,
R3 逐字节维持存在性判定现状(无 recon 键)。
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from core import feature_flags
from services.recon.bank_recon_types import StatementRow
from services.workorder.engine import StepContext
from services.workorder.steps import checkpoint

_STEP = "reconcile"
_EVT_BANK_PARSED = "item_bank_parsed"


def run_bank_recon(ctx: StepContext, banks: list[dict], events: list[dict]) -> Optional[dict]:
    """闸开时的 R3 逐笔对平:银行流水行(逐件检查点解析)+ 工单事件流候选票 → 缺票/未达两张
    清单。闸关返 None(调用方据此不挂 recon 键)。对平结果作为纯 dict 随 reconcile 的
    StepResult.ok 经 step_done 落进证据链(E2 人审界面据此读)。任何异常收进 note 不上抛。"""
    if not _bank_recon_enabled(ctx):
        return None
    from services.recon import workorder_recon_adapter as adapter

    try:
        rows = _checkpointed_rows(ctx, banks)
        statement_txs = [adapter.tx_from_statement_row(r) for r in rows]
        candidates = adapter.candidates_from_events(events)
        result = adapter.reconcile_workorder(statement_txs, candidates)
        return result.as_gate_payload()
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "bank_recon_skipped"}


def _checkpointed_rows(ctx: StepContext, banks: list[dict]) -> list:
    """R3 银行流水解析逐件检查点(件 4 · 照 C1 范式)。

    批前从已提交 item_bank_parsed 事件重建已解析件表:逐件提交后被杀,已落件不在内存里,从空
    建会让其重解析(= 重烧 OCR)且流水行被重放двойно计入对平 → 复件双计(C1 打回 R1 的静默
    钱洞同款)。重建保证中断续跑对每件的解析裁决与不中断跑逐字节一致。每件独立事务落
    item_bank_parsed(dedupe_key 锚件,重放不双落)+ 顺带续租(checkpoint.item_scope)。
    """
    parsed = _replay_parsed_banks(ctx)
    rows: list = []
    for it in banks:
        iid = it["id"]
        if iid in parsed:
            rows.extend(parsed[iid])
            continue
        fresh = _parse_bank_file(ctx, it)
        with checkpoint.item_scope(ctx):
            _emit_bank_parsed(ctx, it, fresh)
        rows.extend(fresh)
    return rows


def _replay_parsed_banks(ctx: StepContext) -> dict:
    """从已提交 item_bank_parsed 事件重建 {item_id: [StatementRow,...]}(首件在先,重放不覆写)。
    解析结果的流水行随事件持久化,续跑从此回放而非重解析——银行件的「断点续跑恢复源」。"""
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    out: dict = {}
    for e in events:
        if e.get("event_type") != _EVT_BANK_PARSED:
            continue
        payload = e.get("payload") or {}
        iid = payload.get("item_id")
        if iid and iid not in out:
            out[iid] = [_deserialize_row(d) for d in (payload.get("rows") or [])]
    return out


def _emit_bank_parsed(ctx: StepContext, item: dict, rows: list) -> None:
    """落一条 item_bank_parsed 检查点事件(dedupe_key 锚 item:并发接管/续跑重放同件只落一条,
    对平不被重放的流水行撑破)。rows 序列化进 payload,续跑从事件回放不重解析。"""
    ctx.store.append_event(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        step=_STEP,
        event_type=_EVT_BANK_PARSED,
        payload={"item_id": item["id"], "rows": [_serialize_row(r) for r in rows]},
        dedupe_key=f"bank_parse:{item['id']}",
    )


def _serialize_row(row: StatementRow) -> dict:
    """StatementRow → 可 JSON 序列化 dict(进 item_bank_parsed 事件)。date 转 iso;row_hash 原样
    带出,回放重建时不触发 __post_init__ 重算(指纹恒定)。"""
    d = row.date
    return {
        "date": d.isoformat() if hasattr(d, "isoformat") else None,
        "description": row.description,
        "withdrawal": row.withdrawal,
        "deposit": row.deposit,
        "balance": row.balance,
        "source_file": row.source_file,
        "account_no": row.account_no,
        "row_hash": row.row_hash,
        "confidence": row.confidence,
        "balance_ok": row.balance_ok,
        "direction_autocorrected": row.direction_autocorrected,
        "amount_autocorrected": row.amount_autocorrected,
    }


def _deserialize_row(d: dict) -> StatementRow:
    """item_bank_parsed 事件里的 dict → StatementRow(与原解析对象等价,喂 tx_from_statement_row)。"""
    raw = d.get("date")
    return StatementRow(
        date=date.fromisoformat(raw) if raw else None,
        description=d.get("description") or "",
        withdrawal=d.get("withdrawal") or 0.0,
        deposit=d.get("deposit") or 0.0,
        balance=d.get("balance") or 0.0,
        source_file=d.get("source_file") or "",
        account_no=d.get("account_no") or "",
        row_hash=d.get("row_hash") or "",
        confidence=d.get("confidence") or "high",
        balance_ok=d.get("balance_ok"),
        direction_autocorrected=bool(d.get("direction_autocorrected")),
        amount_autocorrected=bool(d.get("amount_autocorrected")),
    )


def _default_bank_recon_enabled(ctx: StepContext) -> bool:
    """R3 真对平放量闸(pearnly_ai_bank_recon)。工单线只有 tenant_id,按 tenant 判定;
    fail-closed 在 feature_flags 内部(基建抖动绝不误开真对平路)。"""
    return feature_flags.pearnly_ai_bank_recon_enabled_for(ctx.tenant_id)


def _default_parse_bank_file(ctx: StepContext, item: dict) -> list:
    """默认单件银行流水解析:读 file_ref 字节 → 生产 bank_recon 解析器 → StatementRow 列表。

    单测注入替身(reconcile_bank._parse_bank_file = fake),本函数不在测试里跑 → 不触真解析/
    付费。无 file_ref / 解析失败 → 空列表(佐证层不因单件坏料中断,该件如实解出零行)。
    """
    file_ref = item.get("file_ref")
    if not file_ref:
        return []
    from services.recon.bank_recon_v2 import _parse_bank_statement_impl

    data = Path(file_ref).read_bytes()
    parsed = _parse_bank_statement_impl(data, Path(file_ref).name, tenant_id=ctx.tenant_id)
    return list(parsed.get("rows") or []) if parsed.get("ok") else []


# 注入点:模块级绑定,测试用 reconcile_bank._xxx = fake 替换(同 classify/reconcile 惯例)。
_bank_recon_enabled = _default_bank_recon_enabled
_parse_bank_file = _default_parse_bank_file
