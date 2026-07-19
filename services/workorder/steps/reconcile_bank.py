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
from services.ai_gateway import attribution
from services.recon.bank_recon_types import StatementRow
from services.workorder import storage
from services.workorder.engine import StepContext
from services.workorder.steps import checkpoint, stmt_totals

_STEP = "reconcile"
_EVT_BANK_PARSED = "item_bank_parsed"
EVT_BANK_PARSE_INVALIDATED = "bank_parse_invalidated"

# R3 银行流水解析走统一 OCR 管线(document_type=bank_statement),管线深处按内部标签
# (task=ocr.layer2·tenant 空)打点。归因到本 task 让这段成本记到客户账套头上,与主站散单
# 银行对账、classify 的进项 OCR 各自分账(名字诚实:银行件在 classify 已被 sort 归堆跳过,
# 到这里是首次也是唯一一次 OCR,非「复核升级」)。
_BANK_OCR_TASK = "workorder_bank_parse"


class BankStatementParseError(RuntimeError):
    """银行件未形成可核对流水行。失败件不落检查点，续跑时必须重新解析。"""

    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f"{filename}: bank_statement_parse_failed ({reason})")


def run_bank_recon(ctx: StepContext, banks: list[dict], events: list[dict]) -> Optional[dict]:
    """闸开时的 R3 逐笔对平:银行流水行(逐件检查点解析)+ 工单事件流候选票 → 缺票/未达两张
    清单。闸关返 None(调用方据此不挂 recon 键)。对平结果作为纯 dict 随 reconcile 的
    StepResult.ok 经 step_done 落进证据链(E2 人审界面据此读)。任何异常收进 note 不上抛。"""
    if not _bank_recon_enabled(ctx):
        return None
    from services.recon import workorder_recon_adapter as adapter

    try:
        rows = checkpoint_bank_statements(ctx, banks)
    except BankStatementParseError:
        raise
    try:
        emit_stmt_totals(ctx, banks, events)
        statement_txs = [adapter.tx_from_statement_row(r) for r in rows]
        candidates = adapter.candidates_from_events(events)
        result = adapter.reconcile_workorder(statement_txs, candidates)
        return result.as_gate_payload()
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "bank_recon_skipped"}


def checkpoint_bank_statements(ctx: StepContext, banks: list[dict]) -> Optional[list]:
    """仅把银行文件逐件解析并落断点，不执行页尾窄读和逐笔对账。"""
    if not _bank_recon_enabled(ctx):
        return None
    return _checkpointed_rows(ctx, banks)


def emit_stmt_totals(ctx: StepContext, banks: list[dict], events: list[dict]) -> None:
    """独立触发自报总数窄读；缺销项的 checkpoint-only 路径也必须执行。

    事件里已有自报总数即跳过——dedupe_key 只防事件重复落库,防不了重复付费 OCR 读:
    等销项期间 reconcile 每重跑一轮都会走到这里,无此守门每轮都白读一次锚页。"""
    if not banks or stmt_totals.totals_from_events(events) is not None:
        return
    if _bank_recon_enabled(ctx) and _stmt_totals_enabled(ctx):
        stmt_totals.emit_from_banks(ctx, banks)


def _checkpointed_rows(ctx: StepContext, banks: list[dict]) -> list:
    """R3 银行流水解析逐件检查点(件 4 · 照 C1 范式)。

    批前从已提交 item_bank_parsed 事件重建已解析件表:逐件提交后被杀,已落件不在内存里,从空
    建会让其重解析(= 重烧 OCR)且流水行被重放двойно计入对平 → 复件双计(C1 打回 R1 的静默
    钱洞同款)。重建保证中断续跑对每件的解析裁决与不中断跑逐字节一致。每件独立事务落
    item_bank_parsed(dedupe_key 锚件,重放不双落)+ 顺带续租(checkpoint.item_scope)。
    """
    parsed, generation = _replay_parsed_banks(ctx)
    rows: list = []
    for it in banks:
        iid = it["id"]
        if iid in parsed:
            rows.extend(parsed[iid])
            continue
        try:
            fresh = _parse_bank_file(ctx, it)
        except BankStatementParseError:
            raise
        except Exception as exc:
            name = it.get("original_name") or Path(it.get("file_ref") or "").name or iid
            raise BankStatementParseError(name, type(exc).__name__) from exc
        if not fresh:
            name = it.get("original_name") or Path(it.get("file_ref") or "").name or iid
            raise BankStatementParseError(name, "no_transaction_rows")
        with checkpoint.item_scope(ctx):
            _emit_bank_parsed(ctx, it, fresh, generation)
        rows.extend(fresh)
    return rows


def _replay_parsed_banks(ctx: StepContext) -> tuple[dict, int]:
    """从已提交 item_bank_parsed 事件重建 {item_id: [StatementRow,...]}(首件在先,重放不覆写)。
    解析结果的流水行随事件持久化,续跑从此回放而非重解析——银行件的「断点续跑恢复源」。"""
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    out: dict = {}
    for e in active_bank_parse_events(events):
        payload = e.get("payload") or {}
        iid = payload.get("item_id")
        if iid and iid not in out:
            out[iid] = [_deserialize_row(d) for d in (payload.get("rows") or [])]
    return out, bank_parse_generation(events)


def active_bank_generation_events(events: list[dict]) -> list[dict]:
    """最后一次解析失效标记之后的银行代次事件流。

    检查点是追加证据，解析器修复后不能 DELETE 老结果，也不能继续回放错结果。运维落一条
    bank_parse_invalidated 即开启新代次：原事件永久留审计链，读侧只消费标记后的解析、
    大脑建议与行级人裁。没有标记的存量工单保持原行为。
    """
    start = 0
    for index, event in enumerate(events):
        if event.get("event_type") == EVT_BANK_PARSE_INVALIDATED:
            start = index + 1
    return events[start:]


def bank_parse_generation(events: list[dict]) -> int:
    """当前解析代次编号；仅用于检查点幂等键，失效标记每多一条就进入下一代。"""
    return sum(1 for event in events if event.get("event_type") == EVT_BANK_PARSE_INVALIDATED)


def active_bank_parse_events(events: list[dict]) -> list[dict]:
    """当前银行解析代次内的 item_bank_parsed 事件。"""
    return [
        event
        for event in active_bank_generation_events(events)
        if event.get("event_type") == _EVT_BANK_PARSED
    ]


def _emit_bank_parsed(ctx: StepContext, item: dict, rows: list, generation: int) -> None:
    """落一条 item_bank_parsed 检查点事件(dedupe_key 锚代次+item,同代重放只落一条)。
    rows 序列化进 payload；失效后新代次可重读，正常续跑仍从事件回放。"""
    ctx.store.append_event(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        step=_STEP,
        event_type=_EVT_BANK_PARSED,
        payload={"item_id": item["id"], "rows": [_serialize_row(r) for r in rows]},
        dedupe_key=f"bank_parse:g{generation}:{item['id']}",
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


def _default_stmt_totals_enabled(ctx: StepContext) -> bool:
    """自报总数窄读闸(SA3R-b)。复用 SA-3 建议闸(pearnly_ai_bank_sales_suggest)——只有它消费
    coverage 的缺料判据,别处开着白读白花钱。按 tenant 判定;fail-closed 在 feature_flags 内部。"""
    return feature_flags.pearnly_ai_bank_sales_suggest_enabled_for(ctx.tenant_id)


def _default_parse_bank_file(ctx: StepContext, item: dict) -> list:
    """默认单件银行流水解析:读 file_ref 字节 → 生产 bank_recon 解析器 → StatementRow 列表。

    单测注入替身(reconcile_bank._parse_bank_file = fake),本函数不在测试里跑 → 不触真解析/
    付费。无 file_ref、解析失败或零流水行都抛 BankStatementParseError；调用方停在 reconcile，
    且不写 item_bank_parsed，修复材料后续跑会重新解析该件。

    成本归因:解析深处走统一 OCR 管线,不设归因则落 ai_usage 的 task=ocr.layer2·tenant 空。
    在真正发起解析的本函数体内设归因(contextvars 线程本地——_checkpointed_rows 串行逐件调,
    此处即执行线程;管线内多页并发经 copy_context 承接),finally 清,照 classify._ocr_safe 先例。
    只改成本记给谁的标签,解析行为/返回数据一字不动。
    """
    file_ref = item.get("file_ref")
    name = item.get("original_name") or Path(file_ref or "").name or str(item.get("id") or "?")
    if not file_ref:
        raise BankStatementParseError(name, "file_missing")
    from services.recon.bank_recon_v2 import _parse_bank_statement_impl

    token = attribution.set_attribution(
        _BANK_OCR_TASK, tenant_id=str(ctx.tenant_id), trace_id=str(ctx.work_order_id)
    )
    try:
        data = storage.read_bytes(file_ref)  # 落盘密文解回明文再解析(双轨读)
        parsed = _parse_bank_statement_impl(data, Path(file_ref).name, tenant_id=ctx.tenant_id)
        if not parsed.get("ok"):
            reason = parsed.get("error_code") or parsed.get("error") or "parser_rejected"
            raise BankStatementParseError(name, str(reason)[:120])
        rows = list(parsed.get("rows") or [])
        if not rows:
            raise BankStatementParseError(name, "no_transaction_rows")
        return rows
    finally:
        attribution.reset_attribution(token)


# 注入点:模块级绑定,测试用 reconcile_bank._xxx = fake 替换(同 classify/reconcile 惯例)。
_bank_recon_enabled = _default_bank_recon_enabled
_stmt_totals_enabled = _default_stmt_totals_enabled
_parse_bank_file = _default_parse_bank_file
