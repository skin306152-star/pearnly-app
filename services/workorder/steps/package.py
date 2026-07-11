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

from services.workorder import decisions, evidence, storage
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import conservation, financials_report, pnd_prep, pp30_form

_KIND_PP30 = "pp30_draft"
_KIND_LEDGER = "ledger_workpaper"
_KIND_BANK = "bank_workpaper"
_KIND_MEMO = "missing_doc_memo"
_KIND_EVIDENCE = "evidence_index"
_KIND_SHADOW = "shadow_workpaper"

_COMPUTE_KEYS = ("tax_due", "sales_amount", "output_vat", "purchase_amount", "input_vat", "period")


def run(ctx: StepContext) -> StepResult:
    base_dir = ctx.data.get("deliverables_dir")
    if not base_dir:
        return StepResult.needs(["deliverables_dir"])

    # 交付物版本化:未冻结重跑=新版本号,旧版本文件不动,读侧默认取最新版(C-2)。整批 5 件
    # 共用同一版本号(一次出包=一个版本),落盘走版本段目录 {base}/v{n}。
    version = ctx.store.next_deliverable_version(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    out_dir = storage.versioned_dir(base_dir, version)
    out_dir.mkdir(parents=True, exist_ok=True)

    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)

    # human_decision 回放一次(带 actor/at 完整 rec):守恒归堆取 payload、备忘留痕取 actor,
    # ledger 裁决列取 decision——三处共用同一份,不各 replay 一遍。
    decision_recs = evidence.replay_items_by_type(events, "human_decision")

    # 守恒闸(出包前置):每件必须有明确终态。待裁决>0 或 Σ桶≠N → stuck 逐件点名,绝不
    # 让无裁决/无豁免的件溜进交付包(G1R2 sales_direction_unhandled 黑洞根治的最后一道门)。
    cons = conservation.bucket_items(
        items, {iid: rec["payload"] for iid, rec in decision_recs.items()}
    )
    blocked = conservation.stuck_reasons(cons, len(items))
    if blocked:
        return StepResult.stuck(blocked)

    numbers = _resolve_numbers(ctx, events)

    # ภ.ง.ด.3/53 RD Prep(D1-3):当期有对应 payee 类型 WHT 才出,无则备忘录记一笔——
    # 装配/取数全归 pnd_prep(零重算钱),这里只负责把它并进整批出包。
    pnd_kinds, wht_memo_lines = pnd_prep.build(ctx, out_dir, numbers.get("period"))

    kinds = {
        _KIND_PP30: _write_pp30(out_dir, numbers),
        _KIND_LEDGER: _write_ledger(out_dir, items, events, decision_recs, numbers),
        _KIND_BANK: _write_bank(out_dir, items, numbers),
        _KIND_MEMO: _write_memo(out_dir, items, cons, decision_recs, numbers, wht_memo_lines),
        _KIND_EVIDENCE: _write_evidence_index(ctx, out_dir, items, events, numbers),
        **pnd_kinds,
        **financials_report.build(out_dir, numbers),  # G1a 月度报表:有 r6_financials 才出
    }
    # 影子底稿(F1):仅当 reconcile 挂了 r5_shadow(闸开且产出成功)才出这件交付物——闸关
    # 逐字节维持现状(不新增文件/交付物行)。从 gates.r5_shadow 取,只渲染不重算。
    shadow_gate = (numbers.get("gates") or {}).get("r5_shadow")
    if isinstance(shadow_gate, dict) and "trial_balance" in shadow_gate:
        kinds[_KIND_SHADOW] = _write_shadow(out_dir, shadow_gate)
    for kind, (artifact_path, snapshot) in kinds.items():
        ctx.store.upsert_deliverable(
            ctx.cur,
            tenant_id=ctx.tenant_id,
            work_order_id=ctx.work_order_id,
            kind=kind,
            version=version,
            artifact_path=artifact_path,
            numbers=snapshot,
        )

    return StepResult.ok(
        deliverables={k: v[0] for k, v in kinds.items()}, deliverable_version=version
    )


def _resolve_numbers(ctx: StepContext, events: list[dict]) -> dict:
    """取 compute 落下的六个数字 + reconcile 的 gates(供银行/进销底稿用)。同进程直接读
    ctx.data;续跑场景从事件流回放对应步的 step_done——与 compute.py 同一个范式。"""
    if all(ctx.data.get(k) for k in _COMPUTE_KEYS):
        base = {k: ctx.data[k] for k in _COMPUTE_KEYS}
        base["prior_period_check"] = ctx.data.get("prior_period_check")
        base["pp30_form"] = ctx.data.get("pp30_form")
    else:
        payload = evidence.replay_step_done(events, "compute") or {}
        base = {k: payload.get(k) for k in _COMPUTE_KEYS}
        base["prior_period_check"] = payload.get("prior_period_check")
        base["pp30_form"] = payload.get("pp30_form")

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


# 只有「本期无独立数据源诚实置 0」的字段需要脚注;derived/reconcile 是真数字不加注
# (map 命中即渲染,未命中的 source 自然无注)。
_SRC_NOTE_TH = {pp30_form.SRC_NO_SOURCE_M1: "本期无独立数据源 · M1 诚实置 0"}


def _pp30_form_rows(form: dict | None) -> list[str]:
    """把 compute 派生的 ภ.พ.30 全字段行渲染成 markdown 表(package 只渲染,不重算)。
    诚实置 0 的字段(0%/免税销售、上期留抵、加算金、罚金)带来源标注,不与真数字混同。"""
    if not form or not form.get("fields"):
        return ["| — | ยังไม่มีข้อมูลแบบเต็ม (无全字段数据) | — |"]
    rows = []
    for f in form["fields"]:
        note = _SRC_NOTE_TH.get(f["source"], "")
        rows.append(
            f"| {f['line']} | {f['label_th']} ({f['label_zh']}) | {_dec_str(f['amount'])}"
            f"{' · ' + note if note else ''} |"
        )
    return rows


def _write_pp30(out_dir: Path, numbers: dict) -> tuple[str, dict]:
    """ภ.พ.30 草稿:结构化 JSON(供程序/证据索引引用)+ markdown 底稿(供人读)。JSON 快照既留
    5 个关键基数(向后兼容既有引用)又留全字段 pp30_form(官方逐行契约)。"""
    form = numbers.get("pp30_form")
    snapshot = {k: numbers.get(k) for k in _COMPUTE_KEYS}
    snapshot["prior_period_check"] = numbers.get("prior_period_check")
    snapshot["sales_source"] = numbers.get("sales_source")
    snapshot["sales_source_note"] = numbers.get("sales_source_note")
    snapshot["pp30_form"] = form
    json_path = _write_md(
        out_dir, "pp30_draft.json", [json.dumps(snapshot, ensure_ascii=False, indent=2)]
    )
    snapshot["json_path"] = str(json_path)

    md_path = _write_md(
        out_dir,
        "pp30_draft.md",
        [
            "# แบบร่าง ภ.พ.30 (VAT 申报底稿 · 内部核对用,非官方申报表)",
            "",
            f"งวดที่ (期间): {numbers.get('period') or '-'}",
            "",
            "| ช่อง (行) | รายการ (项目) | จำนวนเงิน บาท (金额,THB) |",
            "|---|---|---|",
            *_pp30_form_rows(form),
            *_sales_source_note_lines(numbers),
            "",
            "หมายเหตุ: ฉบับทางการ (PDF) จัดทำใน M1 (官式 PDF 版式为 M1,本页仅内部核对底稿)",
        ],
    )
    return str(md_path), snapshot


def _write_ledger(
    out_dir: Path, items: list[dict], events: list[dict], decision_recs: dict, numbers: dict
) -> tuple[str, dict]:
    """进销明细底稿:每张进项票一行[文件名/票号/卖方税号/净额/税额/状态/裁决] + 销项汇总一段。"""
    classified = evidence.replay_items_by_type(events, "item_classified")
    purchases = sorted(
        (it for it in items if it["kind"] == "purchase_invoice"),
        key=lambda it: it.get("file_ref") or "",
    )

    def _row(it: dict) -> str:
        money = (classified.get(it["id"]) or {}).get("payload", {}).get("money") or {}
        decision = (decision_recs.get(it["id"]) or {}).get("payload", {}).get("decision") or "-"
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


def _write_shadow(out_dir: Path, shadow: dict) -> tuple[str, dict]:
    """影子底稿(F1):建议分录表 + 科目余额 + 试算平衡(Σ借=Σ贷 判平)。从 gates.r5_shadow 取,
    package 只渲染不重算(影子只算不落法定表——非第二账本,不写 journal_vouchers)。"""
    tb = shadow.get("trial_balance") or {}
    entry_rows = [
        f"| {e.get('source') or '-'} | {e.get('rule_key') or '-'} | {e.get('dr_cr') or '-'} "
        f"| {e.get('account_code') or '-'} {e.get('account_name') or ''} | {_dec_str(e.get('amount'))} |"
        for e in shadow.get("entries") or []
    ]
    account_rows = [
        f"| {a.get('code')} {a.get('name') or ''} | {_dec_str(a.get('debit'))} "
        f"| {_dec_str(a.get('credit'))} | {_dec_str(a.get('balance'))} |"
        for a in shadow.get("accounts") or []
    ]
    balanced = "✔ สมดุล (配平)" if tb.get("balanced") else "✘ ไม่สมดุล (不平)"
    lines = [
        "# ใบงานร่างบัญชีคู่ (影子底稿 · 内部校验用,非法定账本)",
        "",
        *_bullets(
            "รายการบัญชีที่แนะนำ (建议分录)",
            (
                [
                    "| ที่มา (来源) | กฎ (规则) | เดบิต/เครดิต (借/贷) | บัญชี (科目) | จำนวนเงิน (金额) |"
                ]
                + ["|---|---|---|---|---|"]
                + entry_rows
                if entry_rows
                else []
            ),
        ),
        *_bullets(
            "ยอดคงเหลือแต่ละบัญชี (科目余额)",
            (
                [
                    "| บัญชี (科目) | เดบิต (借方) | เครดิต (贷方) | คงเหลือ (净额) |",
                    "|---|---|---|---|",
                ]
                + account_rows
                if account_rows
                else []
            ),
        ),
        *_bullets(
            "งบทดลอง (试算平衡)",
            [
                f"Σ เดบิต (借方合计): {_dec_str(tb.get('debit'))}",
                f"Σ เครดิต (贷方合计): {_dec_str(tb.get('credit'))}",
                f"ผลต่าง (差额): {_dec_str(tb.get('diff'))}",
                f"สถานะ (状态): {balanced}",
            ],
        ),
        *_shadow_gl_section(shadow.get("reconcile_gl")),
    ]
    path = _write_md(out_dir, "shadow_workpaper.md", lines)
    snapshot = {
        "balanced": bool(tb.get("balanced")),
        "debit": tb.get("debit"),
        "credit": tb.get("credit"),
        "diff": tb.get("diff"),
        "entry_count": len(shadow.get("entries") or []),
        "account_count": len(shadow.get("accounts") or []),
        "uncertainties": shadow.get("uncertainties") or [],
        "gl_recon_status": (shadow.get("reconcile_gl") or {}).get("status"),
    }
    return str(path), snapshot


def _shadow_gl_section(recon: dict | None) -> list[str]:
    """影子 ↔ GL 对平结果(F2)。仅在 reconcile.py 挂了 reconcile_gl(F2 对数已跑)时渲染;
    只呈现不重算。无 GL 上传(no_gl_source)也如实标,不假装对平过。"""
    if not isinstance(recon, dict) or not recon.get("status"):
        return []
    t = recon.get("totals") or {}
    push = recon.get("push") or {}
    lines = [
        f"สถานะการกระทบยอด GL (对平状态): {recon.get('status')}"
        + ("  ⚠ พบผลต่าง (有差额报警)" if recon.get("alert") else "")
    ]
    if t:
        lines.append(
            f"合计 借 影子/GL: {_dec_str(t.get('shadow_debit'))} / {_dec_str(t.get('gl_debit'))}"
            f" · 贷: {_dec_str(t.get('shadow_credit'))} / {_dec_str(t.get('gl_credit'))}"
        )
    lines += [
        f"✘ {m.get('local_code')}→{m.get('erp_code')} 借差 {_dec_str(m.get('debit_diff'))}"
        f" 贷差 {_dec_str(m.get('credit_diff'))}"
        for m in recon.get("mismatch") or []
    ]
    if recon.get("unmapped"):
        lines.append(
            "unmapped (桥不全,未对): " + ", ".join(u.get("local_code") for u in recon["unmapped"])
        )
    if push.get("status"):
        miss = " · 漏推 " + ", ".join(push["missing"]) if push.get("missing") else ""
        rej = " · 被拒 " + ", ".join(r.get("invoice_no") for r in push.get("rejected") or [])
        lines.append(
            f"推送核对 (F2-辅): {push.get('status')}{miss}{rej if push.get('rejected') else ''}"
        )
    return _bullets("กระทบยอดกับ GL (与 GL 对平 · F2)", lines)


def _write_memo(
    out_dir: Path,
    items: list[dict],
    cons: conservation.Conservation,
    decision_recs: dict,
    numbers: dict,
    wht_lines: list[str],
) -> tuple[str, dict]:
    """缺料备忘:银行单缺失、曾被标记复核的票及其裁决、non_tax/duplicate 排除清单、人工豁免
    留痕——如实枚举。豁免件虽出包,但谁豁免·为何·哪张必须显著在案(状态诚实,不悄悄放行)。
    豁免成员资格取自守恒桶(cons.buckets[WAIVED]),与出包闸同一事实源,不另判一套。
    wht_lines 是 pnd_prep 算出的 ภ.ง.ด.3/53 附加事项(本期无 WHT / 缺税号 / 个人缺地址),
    与其余"缺料"类别同一份文件、同一种直白列法,不另起一个交付物面。"""
    gate = (numbers.get("gates") or {}).get("r3_bank") or {}
    bank_missing = gate.get("note") == "bank_statement_missing"
    flagged = [it for it in items if it.get("flag_reason") and it["status"] == "flagged"]
    non_tax = [it for it in items if it["kind"] == "non_tax" and it["status"] == "excluded"]
    duplicates = [it for it in items if it["kind"] == "duplicate" and it["status"] == "excluded"]
    waived = cons.buckets[conservation.WAIVED]

    def _tag(it: dict, extra: str = "") -> str:
        return f"- {Path(it.get('file_ref') or '').name}: {it.get('flag_reason')}{extra}"

    def _flag_row(it: dict) -> str:
        dec = (decision_recs.get(it["id"]) or {}).get("payload") or {}
        decision = dec.get("decision")
        if decision == decisions.ASSIGN_KIND:
            label = _ASSIGN_KIND_LABEL_TH.get(dec.get("kind"), dec.get("kind"))
            return _tag(it, f" → {label}")
        return _tag(it, f" → {decision or '无裁决'}")

    def _waive_row(it: dict) -> str:
        rec = decision_recs.get(it["id"]) or {}
        dec = rec.get("payload") or {}
        actor = rec.get("actor") or "?"
        reason = dec.get("reason") or "-"
        return f"- {Path(it.get('file_ref') or '').name}: ยกเว้นโดย (豁免人) {actor} · เหตุผล (理由) {reason}"

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
        *_bullets(
            "รายการที่ยกเว้นโดยมนุษย์ (人工豁免出包 · 谁豁免·为何·哪张)",
            [_waive_row(it) for it in waived],
        ),
        *_bullets("หัก ณ ที่จ่าย (WHT · ภ.ง.ด.3/53)", wht_lines),
    ]
    path = _write_md(out_dir, "missing_doc_memo.md", lines)
    snapshot = {
        "bank_statement_missing": bank_missing,
        "flagged_count": len(flagged),
        "non_tax_count": len(non_tax),
        "duplicate_count": len(duplicates),
        "waived_count": len(waived),
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
