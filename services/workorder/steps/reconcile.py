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
from services.workorder import decisions, kinds, storage
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import reconcile_bank
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
    # 自动判本方销项票(MC1-c.1):默认销项不进 R1、无裁决不停机,人工改判进项才计入(拍错票兜底)。
    sales_docs = [it for it in items if it["kind"] == decisions.SALES_DOC]
    r1 = gates.resolve_input_vat(
        purchases, classified, decisions_by_item, ambiguous=ambiguous, sales_docs=sales_docs
    )
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
    else:
        recon = reconcile_bank.run_bank_recon(ctx, banks, events)
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
    # R2 销项佐证(MC1-c.1):逐票本方销项票聚合成「已开票销售」对账点,对比 R2 权威值给覆盖率/缺口。
    # 纯佐证层——R2 权威取值(上面 r2_sales)一行不改,聚合只读 sales_doc 件的票面钱、异常收 note
    # 不阻断出包。零 sales_doc 件返 None(不挂键,存量工单 payload 逐字节维持现状)。
    corroboration = _run_invoice_aggregate(items, classified, r2)
    if corroboration is not None:
        result_gates["r2_sales_corroboration"] = corroboration
    # R2 销项 EDC 聚合佐证(SA-2b):edc_settlement 件的结算快照 → SA-1 聚合(唯一算法,
    # 只 import 不重写)+ 对 R2 权威值覆盖率。同样纯佐证——不落申报数,零 EDC 件不挂键。
    edc = _run_edc_aggregate(events, r2)
    if edc is not None:
        result_gates["r2_edc_corroboration"] = edc
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


def _run_invoice_aggregate(items: list[dict], classified: dict, r2: dict) -> dict | None:
    """R2 销项佐证:sales_doc 件的逐票票面钱 → sales_aggregate 聚合(去重+守恒+求和)+ 对 R2 权威
    值算覆盖率/缺口。佐证层单点隔离——任何异常收进 note 不上抛,绝不拖垮出包。零 sales_doc 件 → None
    (调用方不挂 r2_sales_corroboration 键,存量工单 payload 逐字节维持改前现状)。"""
    money_list = [
        classified[it["id"]]
        for it in items
        if it["kind"] == decisions.SALES_DOC and classified.get(it["id"])
    ]
    if not money_list:
        return None
    from services.workorder.steps import sales_aggregate

    try:
        agg = sales_aggregate.aggregate_invoice_sales(money_list)
        return sales_aggregate.build_corroboration(
            agg, authoritative_net=r2["sales_amount"], authoritative_vat=r2["output_vat"]
        )
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "invoice_aggregate_skipped"}


def _run_edc_aggregate(events: list[dict], r2: dict) -> dict | None:
    """R2 销项 EDC 聚合佐证(SA-2b):事件流回放 edc 快照 → SA-1 聚合 → 覆盖率佐证。
    佐证层单点隔离——任何异常收进 note 不上抛,绝不拖垮出包。零 EDC 件 → None(调用方
    不挂 r2_edc_corroboration 键,存量工单 payload 逐字节维持改前现状)。"""
    from services.workorder.steps import edc_corroboration

    try:
        payloads = edc_corroboration.payloads_from_events(events)
        if not payloads:
            return None
        return edc_corroboration.build_corroboration(
            edc_corroboration.aggregate_report(payloads),
            authoritative_net=r2["sales_amount"],
            authoritative_vat=r2["output_vat"],
        )
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "edc_aggregate_skipped"}


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
        expected, report, matched_rows, matched_by = _shadow_push_report(ctx)
        push = recon.reconcile_push(expected, report)
        payload = gl.as_payload()
        payload["gl_source"] = src["source"]
        if src.get("note"):
            payload["gl_source_note"] = src["note"]
        push_payload = push.as_payload()
        # T4c 诚实标注(仅在真有回执可核对时挂,MC2-C):erp_push_logs.work_order_id 列已补
        # (老行 NULL),命中行全部按本工单精确匹配才标 "work_order_id";只要有一票落回租户+
        # 票号的旧口径,如实标 "invoice_no"(弱链接决定整体可信度,不由算法层假装精确)。
        # report is None(no_report)时不挂,存量工单(无 GL/无推送)payload 逐字节维持改前现状。
        if report is not None:
            push_payload["matched_by"] = matched_by
            push_payload["matched_rows"] = matched_rows
        payload["push"] = push_payload
        return payload
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"status": "reconcile_gl_skipped", "error": f"{type(exc).__name__}"}


def _default_shadow_draft_enabled(ctx: StepContext) -> bool:
    """R5 影子底稿放量闸(pearnly_ai_shadow_draft)。按 tenant 判定;fail-closed 在 feature_flags 内部
    (基建抖动绝不误开影子路)。"""
    return feature_flags.pearnly_ai_shadow_draft_enabled_for(ctx.tenant_id)


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
            parsed = gl_adapter.parse_gl_bytes(storage.read_bytes(it["file_ref"]), name)
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


_PUSH_TERMINAL_SUCCESS = ("success", "skipped_dup")


def _aggregate_matched_by(rows: list[dict]) -> str:
    """一批推送回执行的整体匹配口径(MC2-C):全部行都按本工单 work_order_id 精确命中才
    标 "work_order_id";只要有一行落回租户+票号的旧口径,如实标 "invoice_no"——弱链接
    决定整体可信度,不因部分精确命中就把有歧义风险的那部分也包装成精确。"""
    if rows and all(r.get("matched_by") == "work_order_id" for r in rows):
        return "work_order_id"
    return "invoice_no"


def _default_shadow_push_report(ctx: StepContext) -> tuple:
    """F2-辅 推送回执源(T4c · 纯读侧接入 · 零碰推送主路径)。

    expected:本工单已裁进项票号——kind=purchase_invoice 且 status=ok(已计入 R1 合计),
    或 status=flagged 且裁决非 exclude/waive(同样已计入 R1 合计,与 reconcile_gates.
    resolve_input_vat 同一份"采信"口径),从事件流回放 item_classified.money.invoice_number,
    空号丢弃、票号去重保序。方向不明票(assign_kind 裁进项)不在此列——本函数只认 sort/
    classify 阶段已直接定堆 purchase_invoice 的件,范围小于 R1 entries(有意收窄,不外推)。

    report:按 tenant_id(+ work_order_id 精确优先)查 erp_push_logs(services.erp.
    push_log_queries,SQL 参数化 + tenant_id 显式过滤做租户隔离),状态词映射到 ImportReport
    鸭子契约(见 _build_import_report)。查无任何匹配行 → (expected, None, 0, None),对数
    如实降级 no_report(没推过≠推失败)。

    matched_by(MC2-C · erp_push_logs.work_order_id 列已补):命中行按 ctx.work_order_id
    精确匹配的标 "work_order_id"(绝不跨工单串号);该列历史 NULL 或此票从未在本工单下推过的
    票号回落「租户 + 票号」旧口径,标 "invoice_no"(理论上可能跨工单同票号误命中)。整批的
    matched_by 汇总见 _aggregate_matched_by,挂进 payload 兜住口径差异,不由算法层假装精确。

    无 cur / 无 tenant_id(内存态单测、cursor_factory 续跑早期阶段等)→ ([], None, 0, None),
    不触真查询——同 _shadow_gl_rows/_shadow_account_bridge 的同款防御。
    """
    if ctx.cur is None or not ctx.tenant_id:
        return [], None, 0, None
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    classified = _replay_money(events)
    decisions_by_item = _replay(events, _EVT_DECISION)

    expected: list[str] = []
    seen: set[str] = set()
    for it in items:
        if it["kind"] != _PURCHASE or it["status"] not in ("ok", "flagged"):
            continue
        if it["status"] == "flagged":
            dec = decisions_by_item.get(it["id"]) or {}
            if dec.get("decision") in decisions.NON_COUNTING:
                continue  # 剔除/豁免——未采信,不进期望票号清单
        inv = str((classified.get(it["id"]) or {}).get("invoice_number") or "").strip()
        if inv and inv not in seen:
            seen.add(inv)
            expected.append(inv)
    if not expected:
        return [], None, 0, None

    from services.erp import push_log_queries

    rows = push_log_queries.list_push_logs_by_invoice_nos(
        ctx.cur, tenant_id=ctx.tenant_id, invoice_nos=expected, work_order_id=ctx.work_order_id
    )
    if not rows:
        return expected, None, 0, None
    return expected, _build_import_report(rows), len(rows), _aggregate_matched_by(rows)


def _build_import_report(rows: list[dict]):
    """erp_push_logs 状态词 → ImportReport 鸭子契约(T4c 状态词映射 · 复用 mrerp_report_parser
    的 dataclass,不新造平行类)。

    success / skipped_dup → success 侧(skipped_dup=判重跳过,语义是"之前已成功推过",归成功
    不归失败)。failed → failed 侧,reasons 取 error_msg(缺失兜底 "failed",不留空列表假装
    无原因)。pending / retrying / manual 是未终态——两侧都不进:如实反映"仍在途",让上层
    reconcile_push 把它落进 missing 桶,好过冒充任一终态。
    """
    from services.erp.mrerp_report_parser import ImportReport, ImportReportRow

    report = ImportReport()
    for row in rows:
        status = row.get("status")
        inv = row.get("invoice_no")
        if status in _PUSH_TERMINAL_SUCCESS:
            report.success.append(inv)
        elif status == "failed":
            report.failed.append(
                ImportReportRow(invoice_no=inv, reasons=[row.get("error_msg") or "failed"])
            )
    return report


# 注入点:模块级绑定,测试用 reconcile._xxx = fake 替换,不改调用方代码(同 classify 惯例)。
# R3 银行段的注入点(_bank_recon_enabled / _parse_bank_file)已随实现迁至 reconcile_bank。
_shadow_draft_enabled = _default_shadow_draft_enabled
_shadow_gl_rows = _default_shadow_gl_rows
_shadow_account_bridge = _default_shadow_account_bridge
_shadow_push_report = _default_shadow_push_report
_shadow_period = _default_shadow_period
