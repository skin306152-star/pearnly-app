# -*- coding: utf-8 -*-
"""package 步:出交付包 + 落交付物快照(任务包 §5 步 6)。

纯编排:数字只从 ctx.data/事件流(compute 的 step_done、reconcile 的 gates、classify 的
item_classified/human_decision)取,本步绝不重算钱。五种交付物统一走"写文件到
deliverables_dir + store.upsert_deliverable 落 artifact_path/numbers 快照"——upsert 按
(work_order_id, kind) 覆盖,重跑天然幂等(不堆积、文件被覆盖为同样内容)。
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from services.workorder import evidence
from services.workorder.engine import StepContext, StepResult

_KIND_PP30 = "pp30_draft"
_KIND_LEDGER = "ledger_workpaper"
_KIND_BANK = "bank_workpaper"
_KIND_MEMO = "missing_doc_memo"
_KIND_EVIDENCE = "evidence_index"

_COMPUTE_KEYS = ("tax_due", "sales_amount", "output_vat", "purchase_amount", "input_vat", "period")


def run(ctx: StepContext) -> StepResult:
    out_dir = ctx.data.get("deliverables_dir")
    if not out_dir:
        return StepResult.needs(["deliverables_dir"])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    numbers = _resolve_numbers(ctx, events)

    kinds = {
        _KIND_PP30: _write_pp30(out_dir, numbers),
        _KIND_LEDGER: _write_ledger(out_dir, items, events, numbers),
        _KIND_BANK: _write_bank(out_dir, items, numbers),
        _KIND_MEMO: _write_memo(out_dir, items, events, numbers),
        _KIND_EVIDENCE: _write_evidence_index(ctx, out_dir, items, events, numbers),
    }
    for kind, (artifact_path, snapshot) in kinds.items():
        ctx.store.upsert_deliverable(
            ctx.cur,
            tenant_id=ctx.tenant_id,
            work_order_id=ctx.work_order_id,
            kind=kind,
            artifact_path=artifact_path,
            numbers=snapshot,
        )

    return StepResult.ok(deliverables={k: v[0] for k, v in kinds.items()})


def _resolve_numbers(ctx: StepContext, events: list[dict]) -> dict:
    """取 compute 落下的六个数字 + reconcile 的 gates(供银行/进销底稿用)。同进程直接读
    ctx.data;续跑场景从事件流回放对应步的 step_done——与 compute.py 同一个范式。"""
    if all(ctx.data.get(k) for k in _COMPUTE_KEYS):
        base = {k: ctx.data[k] for k in _COMPUTE_KEYS}
        base["prior_period_check"] = ctx.data.get("prior_period_check")
    else:
        payload = evidence.replay_step_done(events, "compute") or {}
        base = {k: payload.get(k) for k in _COMPUTE_KEYS}
        base["prior_period_check"] = payload.get("prior_period_check")

    gates = ctx.data.get("gates")
    if gates is None:
        gates = (evidence.replay_step_done(events, "reconcile") or {}).get("gates")
    base["gates"] = gates or {}

    # 销项来源标注(状态诚实条款):人工申报的销项数字必须与 POS 直读区分,不混同呈现——
    # 永远从事件流回放算(不吃 ctx.data 的同进程捷径),同一份判定给 pp30/ledger 底稿与
    # evidence_index 共用,不各拼一套。
    sales_source = evidence.sales_source_info_from_events(events)
    base["sales_source"] = sales_source.get("source")
    base["sales_source_note"] = sales_source.get("note")
    return base


def _dec_str(v) -> str:
    if v is None:
        return "-"
    try:
        return str(Decimal(str(v)))
    except InvalidOperation:
        return str(v)


def _write_md(out_dir: Path, name: str, lines: list[str]) -> Path:
    path = out_dir / name
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _bullets(title: str, rows: list[str]) -> list[str]:
    """一节列表:标题 + 逐行 bullet,空则显式写"(无)"(不许留白冒充"没查"）。"""
    return [f"## {title}", "", *(rows or ["- (无)"]), ""]


_SOURCE_LABEL_TH = {
    "manual_entry": "กรอกเอง (人工申报)",
    "direct_read": "อ่านตรงจากไฟล์ POS (POS 导出直读)",
    "mixed": "กรอกเอง + อ่านตรง (人工申报 + 直读混合)",
}

# 方向裁决(assign_kind)的裁定 kind → 备忘泰文人话(与既有 _SOURCE_LABEL_TH 同风格)。
# 备忘不该直出 "assign_kind" 这个内部裁决动作名——它只说"这是方向裁决",没说裁成了什么。
_ASSIGN_KIND_LABEL_TH = {
    "purchase_invoice": "ซื้อ (进项)",
    "sales_doc": "ขาย (销项)",
    "non_tax": "ไม่ใช่ใบกำกับ (非税)",
}


def _sales_source_visible(source: str | None) -> bool:
    """销项来源是否需要显著提示(状态诚实):direct_read 不提示(默认可信路径);
    manual_entry/mixed 才提示——pp30 脚注与 ledger 底稿共用同一份判定,不各拼一套。"""
    return bool(source) and source != "direct_read"


def _sales_source_note_lines(numbers: dict) -> list[str]:
    """销项来源脚注:与 evidence_index 的 sales_source_info 同一份判定,不重算。"""
    source = numbers.get("sales_source")
    if not _sales_source_visible(source):
        return []
    label = _SOURCE_LABEL_TH.get(source, source)
    line = f"หมายเหตุแหล่งที่มายอดขาย (销项来源标注): {label}"
    note = numbers.get("sales_source_note")
    if note:
        line += f" — {note}"
    return ["", line]


def _write_pp30(out_dir: Path, numbers: dict) -> tuple[str, dict]:
    """ภ.พ.30 关键行草稿:结构化 JSON(供程序/证据索引引用)+ markdown 底稿(供人读)。"""
    snapshot = {k: numbers.get(k) for k in _COMPUTE_KEYS}
    snapshot["prior_period_check"] = numbers.get("prior_period_check")
    snapshot["sales_source"] = numbers.get("sales_source")
    snapshot["sales_source_note"] = numbers.get("sales_source_note")
    json_path = _write_md(
        out_dir, "pp30_draft.json", [json.dumps(snapshot, ensure_ascii=False, indent=2)]
    )
    snapshot["json_path"] = str(json_path)

    due = Decimal(numbers["tax_due"])
    due_label = "ภาษีที่ต้องชำระ (应缴税额)" if due >= 0 else "ภาษีที่ขอคืน/ยกไป (留抵税额)"
    md_path = _write_md(
        out_dir,
        "pp30_draft.md",
        [
            "# แบบร่าง ภ.พ.30 (VAT 申报底稿 · 内部核对用,非官方申报表)",
            "",
            f"งวดที่ (期间): {numbers.get('period') or '-'}",
            "",
            "| รายการ (项目) | จำนวนเงิน บาท (金额,THB) |",
            "|---|---|",
            f"| ยอดขาย (销售额) | {_dec_str(numbers.get('sales_amount'))} |",
            f"| ภาษีขาย (销项税) | {_dec_str(numbers.get('output_vat'))} |",
            f"| มูลค่าซื้อที่นำมาหักได้ (可抵扣采购额) | {_dec_str(numbers.get('purchase_amount'))} |",
            f"| ภาษีซื้อ (进项税) | {_dec_str(numbers.get('input_vat'))} |",
            f"| {due_label} | {_dec_str(numbers.get('tax_due'))} |",
            *_sales_source_note_lines(numbers),
            "",
            "หมายเหตุ: ฉบับทางการ (PDF) จัดทำใน M1 (官式 PDF 版式为 M1,本页仅内部核对底稿)",
        ],
    )
    return str(md_path), snapshot


def _write_ledger(
    out_dir: Path, items: list[dict], events: list[dict], numbers: dict
) -> tuple[str, dict]:
    """进销明细底稿:每张进项票一行[文件名/票号/卖方税号/净额/税额/状态/裁决] + 销项汇总一段。"""
    classified = evidence.replay_items_by_type(events, "item_classified")
    decisions = evidence.replay_items_by_type(events, "human_decision")
    purchases = sorted(
        (it for it in items if it["kind"] == "purchase_invoice"),
        key=lambda it: it.get("file_ref") or "",
    )

    def _row(it: dict) -> str:
        money = (classified.get(it["id"]) or {}).get("payload", {}).get("money") or {}
        decision = (decisions.get(it["id"]) or {}).get("payload", {}).get("decision") or "-"
        return (
            f"| {Path(it.get('file_ref') or '').name} | {money.get('invoice_number') or '-'} "
            f"| {money.get('seller_tax') or '-'} | {_dec_str(money.get('subtotal'))} "
            f"| {_dec_str(money.get('vat'))} | {it['status']} | {decision} |"
        )

    header = [
        "| ไฟล์ (文件名) | เลขที่ใบกำกับ (票号) | เลขผู้ขาย (卖方税号) "
        "| มูลค่าสุทธิ (净额) | ภาษีซื้อ (税额) | สถานะ (状态) | คำวินิจฉัย (裁决) |",
        "|---|---|---|---|---|---|---|",
    ]
    sales_count = sum(1 for it in items if it["kind"] == "sales_summary" and it["status"] == "ok")
    source = numbers.get("sales_source")
    source_line = (
        f"แหล่งที่มา (来源): {_SOURCE_LABEL_TH.get(source, source)}"
        if _sales_source_visible(source)
        else None
    )
    path = _write_md(
        out_dir,
        "ledger_workpaper.md",
        [
            "# ใบงานประกอบบัญชีซื้อ-ขาย (进销明细底稿)",
            "",
            *_bullets("รายการซื้อ (进项明细)", header + [_row(it) for it in purchases]),
            *_bullets(
                "สรุปยอดขาย (销项汇总)",
                [
                    f"จากไฟล์สรุปยอดขาย {sales_count} รายการ (来自 {sales_count} 份销项汇总表): "
                    f"ยอดขาย {_dec_str(numbers.get('sales_amount'))} บาท / "
                    f"ภาษีขาย {_dec_str(numbers.get('output_vat'))} บาท",
                    *([source_line] if source_line else []),
                ],
            ),
        ],
    )
    snapshot = {
        "input_vat_total": numbers.get("input_vat"),
        "purchase_amount_total": numbers.get("purchase_amount"),
        "purchase_item_count": len(purchases),
        "sales_amount_total": numbers.get("sales_amount"),
        "output_vat_total": numbers.get("output_vat"),
        "sales_item_count": sales_count,
        "sales_source": source,
        "sales_source_note": numbers.get("sales_source_note"),
    }
    return str(path), snapshot


def _write_bank(out_dir: Path, items: list[dict], numbers: dict) -> tuple[str, dict]:
    """银行材料清单:M0 只判存在性,如实写 present/missing。"""
    banks = [it for it in items if it["kind"] == "bank_statement"]
    gate = (numbers.get("gates") or {}).get("r3_bank") or {}
    rows = [f"| {Path(it.get('file_ref') or '').name} | present |" for it in banks]
    header = ["| ไฟล์ (文件名) | สถานะ (状态) |", "|---|---|"] if banks else []
    body = (
        header + rows
        if banks
        else ["ไม่มีรายการเดินบัญชีธนาคารในชุดเอกสาร (材料中无银行流水,missing)"]
    )
    path = _write_md(
        out_dir, "bank_workpaper.md", ["# รายการเอกสารธนาคาร (银行材料清单)", "", *body]
    )
    snapshot = {
        "bank_statement_present": bool(banks),
        "bank_statement_count": len(banks),
        "note": gate.get("note"),
    }
    return str(path), snapshot


def _write_memo(
    out_dir: Path, items: list[dict], events: list[dict], numbers: dict
) -> tuple[str, dict]:
    """缺料备忘:银行单缺失、曾被标记复核的票及其裁决、non_tax/duplicate 排除清单——如实枚举。"""
    decisions = evidence.replay_items_by_type(events, "human_decision")
    gate = (numbers.get("gates") or {}).get("r3_bank") or {}
    bank_missing = gate.get("note") == "bank_statement_missing"
    flagged = [it for it in items if it.get("flag_reason") and it["status"] == "flagged"]
    non_tax = [it for it in items if it["kind"] == "non_tax" and it["status"] == "excluded"]
    duplicates = [it for it in items if it["kind"] == "duplicate" and it["status"] == "excluded"]

    def _tag(it: dict, extra: str = "") -> str:
        return f"- {Path(it.get('file_ref') or '').name}: {it.get('flag_reason')}{extra}"

    def _flag_row(it: dict) -> str:
        dec = (decisions.get(it["id"]) or {}).get("payload") or {}
        decision = dec.get("decision")
        if decision == "assign_kind":
            label = _ASSIGN_KIND_LABEL_TH.get(dec.get("kind"), dec.get("kind"))
            return _tag(it, f" → {label}")
        return _tag(it, f" → {decision or '无裁决'}")

    lines = [
        "# บันทึกเอกสารที่ขาด/ต้องทบทวน (缺料与待复核备忘)",
        "",
        *_bullets(
            "เอกสารธนาคาร (银行材料)",
            ["bank_statement_missing" if bank_missing else "ครบ (present)"],
        ),
        *_bullets(
            "รายการที่เคยถูกตั้งค่าสถานะ flagged (曾被标记复核)", [_flag_row(it) for it in flagged]
        ),
        *_bullets("รายการที่ไม่ใช่เอกสารภาษี (non_tax 排除清单)", [_tag(it) for it in non_tax]),
        *_bullets("เอกสารซ้ำ (duplicate 排除清单)", [_tag(it) for it in duplicates]),
    ]
    path = _write_md(out_dir, "missing_doc_memo.md", lines)
    snapshot = {
        "bank_statement_missing": bank_missing,
        "flagged_count": len(flagged),
        "non_tax_count": len(non_tax),
        "duplicate_count": len(duplicates),
    }
    return str(path), snapshot


def _write_evidence_index(
    ctx: StepContext, out_dir: Path, items: list[dict], events: list[dict], numbers: dict
) -> tuple[str, dict]:
    index = evidence.build_evidence_index(
        work_order_id=ctx.work_order_id,
        period=numbers.get("period"),
        items=items,
        events=events,
        numbers={
            k: numbers[k]
            for k in ("tax_due", "sales_amount", "output_vat", "purchase_amount", "input_vat")
            if numbers.get(k) is not None
        },
    )
    path = _write_md(
        out_dir, "evidence_index.json", [json.dumps(index, ensure_ascii=False, indent=2)]
    )
    return str(path), index["numbers"]
