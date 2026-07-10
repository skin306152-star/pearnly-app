# -*- coding: utf-8 -*-
"""classify 步:进项票过 OCR 归堆去重,销项汇总表直读(任务包 §5 步 3)。

纯编排:取 pending 料 → 调注入的 OCR/直读入口 → 用 sort.bin_ocr_fields 归堆、
totals.dedupe_key 算票面级指纹查重复票 → update_item 落堆/落状态。真 OCR/直读
入口通过模块级函数注入(_ocr_image / _read_sales_summary / _resolve_own_tax_id),
默认绑生产实现,单测全部 patch 掉——本文件测试不碰任何 API key,不触发真实
付费调用(硬约束)。

诚实三态:OCR 报警(_needs_review/_validation_warnings)或直读解不出表 → 该件
flagged + flag_reason,绝不静默吞;单件 OCR 异常只连坐该件(ocr_error),不拖垮
整步;全部处理完但存在 flagged → 步仍 ok(flagged 是 item 级状态,裁决交
reconcile/人审,金标 IMG_2647 必须落在这条路径而非被吃掉)。

幂等:只处理 status=pending 的件——已定堆(ok/flagged/excluded)的件不会再出现
在 pending 列表里,重跑天然跳过,不重复起 OCR。查重指纹只在本次调用内的批次
互相比对(work_order_items.dedupe_key 是 intake 的 file: 指纹,update_item 未开
写入口,不动 T1 的 store.py);M0 CLI 一次性喂全部语料、classify 单次跑完整批,
这个范围不影响金标——若 M1 要支持分批收料再分类,需要 T1 补 dedupe_key 更新口。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from services.purchase.totals import dedupe_key
from services.summary_import.parse import parse_table
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import sort as sort_step

# 校验警告文本命中这些关键词才归为「金额算不平」而非泛化的低置信——sanity.py 的
# 硬闸消息(小计/VAT/行和/折扣勾稽)都落在这个词表里,命中即 amount_math_fail。
_MATH_HINTS = ("小计", "总额", "行和", "vat", "折", "mismatch", "不平", "误读")


def run(ctx: StepContext) -> StepResult:
    """给 pending 的图片/PDF 过 OCR 归堆去重,给 pending 的销项 xlsx 直读。"""
    pending = ctx.store.list_items(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id, status="pending"
    )
    own_tax_id = _resolve_own_tax_id(ctx)
    own_name = _resolve_own_name(ctx)

    bins: dict[str, int] = {}
    flagged = 0
    seen_purchase_fp: dict[str, str] = {}

    for item in pending:
        if item["kind"] != "unknown":
            continue
        outcome = _classify_image(
            item, own_tax_id=own_tax_id, own_name=own_name, seen=seen_purchase_fp
        )
        upd = outcome["update"]
        ctx.store.update_item(ctx.cur, tenant_id=ctx.tenant_id, item_id=item["id"], **upd)
        # 归堆即落 item_classified 事件:进项票带票面钱字段。这条事件是 reconcile 回放金额的
        # 唯一持久源(证据链 + 断点续跑),classify 不算钱,只把票面原值落进证据流。
        _emit_classified(
            ctx, item, kind=upd["kind"], status=upd["status"], money=outcome.get("money")
        )
        bins[outcome["kind"]] = bins.get(outcome["kind"], 0) + 1
        if outcome["flagged"]:
            flagged += 1

    reads: dict[str, dict] = dict(ctx.data.get("sales_summary_reads") or {})
    for item in pending:
        if item["kind"] != "sales_summary":
            continue
        parsed, reason = _classify_summary(item)
        if reason:
            ctx.store.update_item(
                ctx.cur,
                tenant_id=ctx.tenant_id,
                item_id=item["id"],
                status="flagged",
                flag_reason=reason,
            )
            _emit_classified(ctx, item, kind="sales_summary", status="flagged", money=None)
            flagged += 1
        else:
            ctx.store.update_item(ctx.cur, tenant_id=ctx.tenant_id, item_id=item["id"], status="ok")
            reads[item["id"]] = parsed
            _emit_classified(
                ctx, item, kind="sales_summary", status="ok", money=None, sales_read=parsed
            )

    return StepResult.ok(bins=bins, flagged=flagged, sales_summary_reads=reads)


def _emit_classified(ctx, item, *, kind, status, money, sales_read=None):
    """落一条 item_classified 证据事件。payload 带 item_id/kind/status,进项另带票面 money,
    销项直读另带 sales_read——reconcile 据此回放,不依赖同进程 ctx.data(续跑不丢)。"""
    payload = {"item_id": item["id"], "kind": kind, "status": status}
    if money:
        payload["money"] = money
    if sales_read is not None:
        payload["sales_read"] = sales_read
    ctx.store.append_event(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        step="classify",
        event_type="item_classified",
        payload=payload,
    )


def _classify_image(
    item: dict, *, own_tax_id: Optional[str], own_name: Optional[str], seen: dict
) -> dict:
    """一张图/PDF:OCR → 归堆 → 购票查重 → 闸报警。异常只连坐这一件。"""
    try:
        fields = _ocr_image(item["file_ref"])
    except Exception as exc:  # noqa: BLE001 - 单件隔离,绝不拖垮整步
        upd = {"status": "flagged", "kind": None, "flag_reason": f"ocr_error:{type(exc).__name__}"}
        return {"kind": "unknown", "flagged": True, "update": upd, "money": None}

    kind, bin_reason = sort_step.bin_ocr_fields(fields, own_tax_id=own_tax_id, own_name=own_name)

    if kind == "purchase_invoice":
        fp = _purchase_fingerprint(fields)
        hit = seen.get(fp) if fp else None
        if hit:
            upd = {"status": "excluded", "kind": "duplicate", "flag_reason": f"duplicate_of:{hit}"}
            return {"kind": "duplicate", "flagged": False, "update": upd, "money": None}
        if fp:
            seen[fp] = Path(item["file_ref"] or "").name
        # 数学勾稽/OCR 置信闸只对进项票生效:进项要用票面钱字段算 VAT,才需盯净+税=总额。
        reason = _gate_reason(fields) or bin_reason
    else:
        # 销项小票/EDC 结算条/银行流水页没有「净+税=总额」结构,不进数学闸——维持各自方向/
        # 类型判据(sales_direction_unhandled / bank_statement / non_tax),不被误挂 amount_math_fail。
        reason = bin_reason

    # non_tax 是「确定无税务要素」的排除,不是留人工的疑点——与 sort.py 对
    # non_tax 的既有约定(status=excluded)同口径,不占 flagged 计数。
    if kind == "non_tax":
        status = "excluded"
    else:
        status = "flagged" if reason else "ok"
    upd = {"status": status, "kind": kind, "flag_reason": reason}
    # 方向不明的票也快照票面钱字段:该票 OCR 已读过,钱在手上,只是进/销方向没判准。人工
    # 裁定为进项后,reconcile 直接用这份读数进 R1,不必为定向重跑一遍付费 OCR。两类方向票
    # (direction_ambiguous / sales_direction_unhandled)同口径,后者裁进项时也要有钱可用。
    capture_money = kind == "purchase_invoice" or (reason or "").startswith(
        ("direction_ambiguous", "sales_direction_unhandled")
    )
    money = _money_fields(fields) if capture_money else None
    return {"kind": kind, "flagged": status == "flagged", "update": upd, "money": money}


def _money_fields(fields: dict) -> dict:
    """票面钱字段快照(进 item_classified 事件,供 reconcile 回放合计/试算)。Decimal 交给
    reconcile,这里只搬 OCR 原值不做换算——净额/税额/含税额 + 票号税号做证据溯源。"""
    return {
        "subtotal": fields.get("subtotal"),
        "vat": fields.get("vat"),
        "total_amount": fields.get("total_amount"),
        "invoice_number": fields.get("invoice_number"),
        "seller_tax": fields.get("seller_tax"),
    }


def _classify_summary(item: dict) -> tuple:
    """一份销项汇总表:直读拿 headers/rows,解不出留原因,不硬吃。"""
    try:
        parsed = _read_sales_summary(item["file_ref"])
    except Exception as exc:  # noqa: BLE001
        return None, f"summary_read_error:{type(exc).__name__}"
    if not parsed.get("rows"):
        return None, "summary_unparseable"
    return parsed, None


def _purchase_fingerprint(fields: dict) -> Optional[str]:
    """票面级查重指纹(任务包 §5:税号|票号|含税合计,复用 purchase.totals.dedupe_key)。"""
    digest = dedupe_key(
        supplier_tax=fields.get("seller_tax"),
        doc_no=fields.get("invoice_number"),
        grand_total=fields.get("total_amount") or fields.get("subtotal"),
    )
    return f"doc:{digest}" if digest else None


def _gate_reason(fields: dict) -> Optional[str]:
    """OCR 确定性闸/勾稽闸报警 → 具体原因,绝不静默放过(金标 IMG_2647 靠这条)。"""
    warnings = fields.get("_validation_warnings") or []
    if warnings:
        text = " ".join(str(w) for w in warnings).lower()
        if any(hint in text for hint in _MATH_HINTS):
            return "amount_math_fail"
        return "ocr_validation_warning"
    if fields.get("_needs_review"):
        band = fields.get("_confidence_band") or "needs_review"
        return f"ocr_low_confidence:{band}"
    return None


def _resolve_client_field(ctx: StepContext, column: str) -> Optional[str]:
    """工单 → workspace_client_id → workspace_clients.<column> 的单列查询。

    workspace_clients 不是工单域的表,不经 services/workorder/store(那是给工单 4 张表
    用的 DAL),这里直接用 ctx 的事务游标查。column 是调用方写死的字面量(tax_id/name),
    非外部输入,故内插进列位;WHERE 值仍走 %s 参数化,不拼字符串。单测全部 patch 掉。
    """
    wo = ctx.store.get_work_order(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    client_id = (wo or {}).get("workspace_client_id")
    if not client_id:
        return None
    ctx.cur.execute(
        f"SELECT {column} FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (client_id, ctx.tenant_id),
    )
    row = ctx.cur.fetchone()
    if not row:
        return None
    return row[column] if isinstance(row, dict) else row[0]


def _default_resolve_own_tax_id(ctx: StepContext) -> Optional[str]:
    """自家税号:锚点判方向的主判据(工单绑定客户账套的 tax_id)。"""
    return _resolve_client_field(ctx, "tax_id")


def _default_resolve_own_name(ctx: StepContext) -> Optional[str]:
    """自家公司名:税号锚失灵时的名称兜底(工单绑定客户账套的 name)。"""
    return _resolve_client_field(ctx, "name")


def _default_ocr_image(path: str) -> dict:
    """真实现:调生产 OCR 管线(services.ocr.entrypoints.run_pipeline_for_file)。

    单测全部 patch 掉这个函数,绝不触达真实付费调用。api_key=None 与
    tests/eval 的现成用法同口径(交由 ai_gateway 按调用环境解析),业务码本身
    不读取任何密钥文件。把 legacy 页字典的 fields 和闸报警字段(_needs_review/
    _validation_warnings/_confidence_band)拍平成一个 dict,供 bin_ocr_fields
    和 _gate_reason 共用同一份契约。
    """
    from services.ocr.entrypoints import run_pipeline_for_file
    from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

    data = Path(path).read_bytes()
    result = run_pipeline_for_file(data, Path(path).name, api_key=None, document_type="invoice")
    legacy = pipeline_result_to_legacy_dict(result)
    pages = legacy.get("pages") or []
    if not pages:
        return {}
    page = pages[0]
    fields = dict(page.get("fields") or {})
    fields["_needs_review"] = bool(page.get("_needs_manual_review") or legacy.get("_needs_review"))
    fields["_validation_warnings"] = list(page.get("_validation_warnings") or [])
    fields["_confidence_band"] = page.get("_confidence_band") or legacy.get("_confidence_band")
    return fields


def _default_read_sales_summary(path: str) -> dict:
    """真实现:xlsx 字节交给 summary_import.parse.parse_table 直读(纯函数,零成本)。"""
    data = Path(path).read_bytes()
    return parse_table(data, filename=Path(path).name)


# 注入点:模块级绑定,测试用 classify._xxx = fake 替换,不改调用方代码。
_resolve_own_tax_id = _default_resolve_own_tax_id
_resolve_own_name = _default_resolve_own_name
_ocr_image = _default_ocr_image
_read_sales_summary = _default_read_sales_summary
