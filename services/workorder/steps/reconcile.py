# -*- coding: utf-8 -*-
"""reconcile 步:勾稽四道闸(任务包 §5 步 4)。

纯编排:从事件流回放票面金额/人工裁决 → 调 reconcile_gates 的纯算法 → 按 R1→R2→R3→R4
顺序返回首个卡点或全绿。取数一律走事件流(item_classified 落的钱字段 / human_decision 裁决),
事件流既是证据链底座又是断点续跑恢复源——续跑时 classify 已跳过、ctx.data 为空,金额仍能从
事件回放,数字与一次跑完全一致。销项直读兼收 ctx.data 兜底(同进程单跑的 T4 契约)。

四道闸语义:
  R1 进项税=Σ票面   flagged 无裁决 → stuck(点名每张票),绝不默认吞进合计。
  R2 销项合计=POS直读 无可用直读源 → needs(["sales_summary"])。
  R3 银行           缺流水记备忘不 stuck;有流水时闸 pearnly_ai_bank_recon 开则逐笔真对平
                    (缺票/未达两清单进证据链,佐证层绝不阻断 package),闸关维持只判材料就绪。
  R4 试算平衡        进销派生内部分录,Σ借≠Σ贷(容差 0.01)→ stuck。纯函数,不落库、不碰
                    accounting 模块开关、不写任何真租户数据(真复式引擎接线留 M1)。
"""

from __future__ import annotations

from pathlib import Path

from core import feature_flags
from services.workorder import decisions, kinds
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import reconcile_gates as gates

_EVT_CLASSIFIED = "item_classified"
_EVT_DECISION = "human_decision"
_PURCHASE = kinds.PURCHASE_INVOICE
_SALES = kinds.SALES_SUMMARY
_BANK = kinds.BANK_STATEMENT

# gates.r5_shadow.reconcile_gl.gl_source 三态(T4a·勘察风险#6):无件 / 有件但解析失败 / 解析成功。
# parse_failed 绝不伪装成 no_gl_source——「读不出」和「没上传」必须分得开。
GL_SOURCE_NONE = "none"
GL_SOURCE_PARSE_FAILED = "parse_failed"
GL_SOURCE_OK = "ok"


def run(ctx: StepContext) -> StepResult:
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    classified = _replay_money(events)
    decisions_by_item = _replay(events, _EVT_DECISION)

    # R1 进项税。除已归堆的进项票外,还收编「方向不明」票:它们钱已 OCR 出来,只是进/销没判准,
    # 必须靠人工 assign_kind 裁决归位(裁进项才入 Σ),无裁决 → 与「flagged 无裁决」同等停机点名。
    purchases = [
        it for it in items if it["kind"] == _PURCHASE and it["status"] in ("ok", "flagged")
    ]
    ambiguous = [
        it
        for it in items
        if it["status"] == "flagged"
        and str(it.get("flag_reason") or "").startswith(decisions.DIRECTION_PREFIXES)
    ]
    r1 = gates.resolve_input_vat(purchases, classified, decisions_by_item, ambiguous=ambiguous)
    if r1["unresolved"]:
        return StepResult.stuck(r1["unresolved"])

    # R2 销项合计
    reads = _replay_sales_reads(events) or dict(ctx.data.get("sales_summary_reads") or {})
    if not reads:
        return StepResult.needs(["sales_summary"])
    r2 = gates.aggregate_sales(reads)
    if not r2["used"]:
        return StepResult.needs(["sales_summary"])

    # R3 银行材料存在性 + 逐笔真对平(pearnly_ai_bank_recon 闸)。闸关:逐字节维持存在性判定
    # 现状(only present/count/note)。闸开且有 bank_statement 件:把流水与工单事件流的票据
    # 逐笔打分对平,缺票/未达两张清单挂进 gate + 证据链(经 step_done 落库),绝不 stuck、绝不
    # 阻断 package——银行对账是佐证层,税额来自 R1/R2 不来自它。
    banks = [it for it in items if it["kind"] == _BANK]
    r3 = {"bank_statement_present": bool(banks), "bank_statement_count": len(banks)}
    if not banks:
        r3["note"] = "bank_statement_missing"
    elif _bank_recon_enabled(ctx):
        recon = _run_bank_recon(ctx, banks, events)
        if recon is not None:
            r3["recon"] = recon

    # R4 试算平衡(纯函数)
    tb = gates.trial_balance(r1["entries"], r2["sales_amount"], r2["output_vat"])
    if not tb["balanced"]:
        return StepResult.stuck(
            [f"trial_balance_unbalanced: 借={tb['debit']} 贷={tb['credit']} 差={tb['diff']}"]
        )

    purchase_amount = sum((e["net"] for e in r1["entries"]), gates.ZERO)
    result_gates = {
        "r1_input_vat": {"total": str(r1["total"]), "counted": len(r1["entries"])},
        "r2_sales": {
            "sales_amount": str(r2["sales_amount"]),
            "output_vat": str(r2["output_vat"]),
        },
        "r3_bank": r3,
        "r4_trial_balance": {
            "balanced": True,
            "debit": str(tb["debit"]),
            "credit": str(tb["credit"]),
        },
    }
    # R5 影子底稿(pearnly_ai_shadow_draft 闸)。闸关:_run_shadow_draft 返 None,gates 逐字节维持
    # 现状(无 r5_shadow 键)。闸开:把 R1 已裁分录 + R2 聚合销项过纯函数复式引擎产出三件套影子
    # 底稿,佐证层挂 r5_shadow——绝不 stuck、绝不阻断 package(影子只算不落法定表)。
    shadow = _run_shadow_draft(ctx, r1, r2)
    if shadow is not None:
        result_gates["r5_shadow"] = shadow
        # R6 月度报表(G1a):把 R5 影子科目余额过 books 注入式纯变换出 BS/PL/TB。闸复用
        # pearnly_ai_shadow_draft(影子在场才有科目余额可算)——影子跳过残影无 accounts →
        # _run_shadow_financials 返 None(无 r6_financials 键)。报表是佐证不改税额,佐证层隔离。
        financials = _run_shadow_financials(ctx, shadow)
        if financials is not None:
            result_gates["r6_financials"] = financials

    return StepResult.ok(
        input_vat_total=str(r1["total"]),
        purchase_amount_total=str(purchase_amount),
        sales_amount_total=str(r2["sales_amount"]),
        output_vat_total=str(r2["output_vat"]),
        gates=result_gates,
    )


def _replay(events: list[dict], event_type: str) -> dict:
    """回放某类事件到 {item_id: payload}(同 item 多条时后者胜,反映最新裁决/识别)。"""
    out: dict = {}
    for e in events:
        if e["event_type"] != event_type:
            continue
        payload = e.get("payload") or {}
        iid = payload.get("item_id")
        if iid:
            out[iid] = payload
    return out


def _replay_money(events: list[dict]) -> dict:
    """票面钱字段:任何带 money 载荷的 item_classified 事件(进项票 + 方向不明票——后者
    钱已读出,待人工定向后按裁定 kind 决定是否进 R1)。按 item_id 回放,latest-wins。"""
    out: dict = {}
    for p in _replay(events, _EVT_CLASSIFIED).values():
        if p.get("money"):
            out[p["item_id"]] = p["money"]
    return out


def _replay_sales_reads(events: list[dict]) -> dict:
    """销项直读:item_classified(kind=sales_summary)的 sales_read 载荷(续跑安全的主源)。"""
    out: dict = {}
    for p in _replay(events, _EVT_CLASSIFIED).values():
        if p.get("kind") == _SALES and p.get("sales_read"):
            out[p["item_id"]] = p["sales_read"]
    return out


def _run_bank_recon(ctx: StepContext, banks: list[dict], events: list[dict]) -> dict | None:
    """闸开时的 R3 逐笔对平:银行流水行(注入解析)+ 工单事件流候选票 → 缺票/未达两张清单。

    对平结果作为纯 dict 挂在 r3["recon"],随 reconcile 的 StepResult.ok 经 step_done 落进证据链
    (E2 人审界面据此读)。任何异常都收进 note 不上抛——佐证层绝不拖垮出包。
    """
    from services.recon import workorder_recon_adapter as adapter

    try:
        rows = _bank_statement_rows(ctx, banks)
        statement_txs = [adapter.tx_from_statement_row(r) for r in rows]
        candidates = adapter.candidates_from_events(events)
        result = adapter.reconcile_workorder(statement_txs, candidates)
        return result.as_gate_payload()
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "bank_recon_skipped"}


def _run_shadow_draft(ctx: StepContext, r1: dict, r2: dict) -> dict | None:
    """闸开时的 R5 影子底稿:已裁进项分录(r1["entries"] · {net,vat,grand})+ 聚合销项 →
    纯函数复式规则引擎 → 建议分录/科目余额/试算平衡。闸关返 None(gates 无 r5_shadow 键)。

    结果作为纯 dict 挂 r5_shadow,随 reconcile 的 StepResult.ok 经 step_done 落进证据链(F3 视图 /
    package 交付物据此渲染)。F2 在此基础上挂对数结果 reconcile_gl(影子科目 ↔ 上传 GL 文件对平 +
    推送逐行成败核对)。任何异常都收进 note 不上抛——佐证层绝不拖垮出包。
    """
    if not _shadow_draft_enabled(ctx):
        return None
    from services.accounting import workorder_shadow_adapter as adapter

    try:
        result = adapter.build_shadow(
            purchase_entries=r1["entries"],
            sales_amount=r2["sales_amount"],
            output_vat=r2["output_vat"],
        )
        payload = result.as_gate_payload()
        payload["reconcile_gl"] = _run_shadow_gl_recon(ctx, result)
        return payload
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "shadow_draft_skipped"}


def _run_shadow_financials(ctx: StepContext, shadow: dict) -> dict | None:
    """R6 月度报表(G1a):影子科目余额(shadow["accounts"])→ books 注入式纯变换 → BS/PL/TB。

    只 import books 变换层 + coa_preset,一行不写/不读 journal_vouchers(影子非第二账本护栏)。
    period 仅作报表标签,defensively 从 work_order 取(取不到=None,package 以 compute 权威期间
    渲染);取 period 单独 try 隔离,不带垮报表本体。任何异常收进 note 不上抛——佐证之佐证,
    层层不阻断出包。返 None(闸关/影子跳过残影无 accounts)= 调用方不挂 r6_financials 键。
    """
    from services.accounting import workorder_financials

    try:
        return workorder_financials.build_financials(shadow, period=_shadow_period(ctx))
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "financials_skipped"}


def _default_shadow_period(ctx: StepContext) -> str | None:
    """报表标签用期间:从 work_order 只读取一次(与 compute 同口径)。取不到 → None(不编造),
    package 以 compute 落的权威 period 渲染。单独隔离:store 无该口子/无 cur 也不带垮报表。"""
    if ctx.cur is None:
        return None
    try:
        wo = ctx.store.get_work_order(
            ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
        )
        return (wo or {}).get("period")
    except Exception:  # noqa: BLE001 - period 是标签,取不到不影响报表数字
        return None


def _run_shadow_gl_recon(ctx: StepContext, shadow) -> dict:
    """F2 对数:影子科目发生额 ↔ 上传 GL 文件(F2-主)+ 预期票 ↔ ERP 导入回执(F2-辅)。

    GL 行经注入点取(kind=gl_ledger 件逐件解析),payload 另带 gl_source 三态 + note,
    解析失败与没上传分得开;账户桥从 coa_erp_bridge 专表建,桥不全的科目标 unmapped。
    自身再 try/except 一层,对数失败不带垮上层影子底稿(佐证之佐证,层层不阻断出包)。
    """
    from services.accounting import shadow_gl_recon as recon

    try:
        src = _shadow_gl_rows(ctx)
        gl_rows = src["rows"]
        # 桥仅在有 GL 行时才被 reconcile_gl 读(无 GL → no_gl_source 前置返回),空跑时省掉一次 DB 查询。
        bridge = _shadow_account_bridge(ctx) if gl_rows else {}
        gl = recon.reconcile_gl(shadow.accounts, gl_rows, bridge)
        expected, report = _shadow_push_report(ctx)
        push = recon.reconcile_push(expected, report)
        payload = gl.as_payload()
        payload["gl_source"] = src["source"]
        if src.get("note"):
            payload["gl_source_note"] = src["note"]
        payload["push"] = push.as_payload()
        return payload
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"status": "reconcile_gl_skipped", "error": f"{type(exc).__name__}"}


def _default_shadow_draft_enabled(ctx: StepContext) -> bool:
    """R5 影子底稿放量闸(pearnly_ai_shadow_draft)。按 tenant 判定;fail-closed 在 feature_flags 内部
    (基建抖动绝不误开影子路)。"""
    return feature_flags.pearnly_ai_shadow_draft_enabled_for(ctx.tenant_id)


def _default_bank_recon_enabled(ctx: StepContext) -> bool:
    """R3 真对平放量闸(pearnly_ai_bank_recon)。工单线只有 tenant_id,按 tenant 判定;
    fail-closed 在 feature_flags 内部(基建抖动绝不误开真对平路)。"""
    return feature_flags.pearnly_ai_bank_recon_enabled_for(ctx.tenant_id)


def _default_bank_statement_rows(ctx: StepContext, banks: list[dict]) -> list:
    """默认银行流水解析:逐件读 file_ref 字节 → 生产 bank_recon 解析器 → StatementRow 列表。

    单测全部注入替身(reconcile._bank_statement_rows = fake),本函数不在测试里跑 → 不触真解析
    /付费。解析失败的件跳过(佐证层不因单件坏料中断);多件流水行顺序拼接。
    """
    from services.recon.bank_recon_v2 import _parse_bank_statement_impl

    rows: list = []
    for it in banks:
        file_ref = it.get("file_ref")
        if not file_ref:
            continue
        data = Path(file_ref).read_bytes()
        parsed = _parse_bank_statement_impl(data, Path(file_ref).name, tenant_id=ctx.tenant_id)
        if parsed.get("ok"):
            rows.extend(parsed.get("rows") or [])
    return rows


def _default_shadow_gl_rows(ctx: StepContext) -> dict:
    """F2-主 GL 佐证源:本工单 kind=gl_ledger 件逐件读字节解析成 GlRow。

    返回 {"rows", "source", "note"} 三态诚实(勘察风险#6 根治):无件 → none;有件但任一
    整件解析失败 → parse_failed + note 逐件摘要(其余成功件的行仍参与对平);全部成功 → ok,
    行级定向丢弃(单金额行方向定不了)如实进 note。单件失败只连坐该件,不拖垮整批。
    """
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    gl_items = [it for it in items if it["kind"] == kinds.GL_LEDGER]
    if not gl_items:
        return {"rows": [], "source": GL_SOURCE_NONE, "note": None}
    from services.accounting import gl_upload_adapter as gl_adapter

    rows: list = []
    failures: list[str] = []
    row_notes: list[str] = []
    for it in gl_items:
        name = Path(it.get("file_ref") or "").name or str(it.get("id"))
        try:
            parsed = gl_adapter.parse_gl_bytes(Path(it["file_ref"]).read_bytes(), name)
        except gl_adapter.GlUploadParseError as exc:
            failures.append(f"{name}: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001 - 读盘/解析库炸也如实记 parse_failed,不上抛
            failures.append(f"{name}: {type(exc).__name__}")
            continue
        rows.extend(parsed["rows"])
        row_notes.extend(parsed["row_issues"])
    if failures:
        return {"rows": rows, "source": GL_SOURCE_PARSE_FAILED, "note": "; ".join(failures)}
    return {"rows": rows, "source": GL_SOURCE_OK, "note": "; ".join(row_notes) or None}


def _default_shadow_account_bridge(ctx: StepContext) -> dict:
    """F2 账户桥:coa_erp_bridge 专表(T4a,替换 erp_account_mappings 过渡启发式)。

    无 cur / 工单未绑账套 / 表空 → 空桥(全科目 unmapped,如实反映桥未配,不臆造对应)。
    工单不带 erp_type:该账套桥行恰属单一 erp_type 时即用之;多 ERP 桥并存时无法归属
    GL 件属谁 → 空桥不猜(T4b 若要多 ERP 需带件级 erp_type 信号)。
    """
    if ctx.cur is None or not ctx.tenant_id:
        return {}
    from services.accounting import bridge_store

    wo = ctx.store.get_work_order(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    client_id = (wo or {}).get("workspace_client_id")
    if not client_id:
        return {}
    erp_types = bridge_store.list_erp_types(
        ctx.cur, tenant_id=ctx.tenant_id, workspace_client_id=client_id
    )
    if len(erp_types) != 1:
        return {}
    return bridge_store.load_bridge(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        workspace_client_id=client_id,
        erp_type=erp_types[0],
    )


def _default_shadow_push_report(ctx: StepContext) -> tuple:
    """F2-辅 推送回执源。当前工单管线不含 ERP 推送步(推送在集成页独立流)→ (无预期票, 无回执),
    对数如实降级 no_report。推送接入工单后本函数改为回放推送清单 + parse_import_report(注入点已就位)。"""
    return [], None


# 注入点:模块级绑定,测试用 reconcile._xxx = fake 替换,不改调用方代码(同 classify 惯例)。
_bank_recon_enabled = _default_bank_recon_enabled
_bank_statement_rows = _default_bank_statement_rows
_shadow_draft_enabled = _default_shadow_draft_enabled
_shadow_gl_rows = _default_shadow_gl_rows
_shadow_account_bridge = _default_shadow_account_bridge
_shadow_push_report = _default_shadow_push_report
_shadow_period = _default_shadow_period
