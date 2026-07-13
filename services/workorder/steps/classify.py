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

import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from itertools import islice
from pathlib import Path
from typing import Optional

from core import feature_flags
from services.ai_gateway import attribution
from services.purchase.totals import dedupe_key
from services.summary_import.parse import parse_table
from services.workorder import decisions, evidence, kinds
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import sort as sort_step
from services.workspace import client_alias_store

# 工单 OCR 成本归因 task(落 ai_usage,与主站散单 OCR 台账分得开,见 C-1 §5)。
_OCR_TASK = "workorder_classify"


def _ocr_concurrency() -> int:
    """classify 内并发喂 OCR 的上限(env PEARNLY_WORKORDER_OCR_CONCURRENCY,默认 5)。

    OCR 是纯网络 I/O(vertex asia-se1 ~1.7s/张),并发把 104 张串行 22-26 分钟压到几分钟;
    设 1 = 回退串行(feature flag 语义)。DB 写不并发——只并行取 OCR,结果按原序回主线程逐件
    落库,守恒(Σ桶=N)与查重确定性都不受并发影响。"""
    try:
        return max(1, int(os.environ.get("PEARNLY_WORKORDER_OCR_CONCURRENCY", "5")))
    except ValueError:
        return 5


# 校验警告文本命中这些关键词才归为「金额算不平」而非泛化的低置信——sanity.py 的
# 硬闸消息(小计/VAT/行和/折扣勾稽)都落在这个词表里,命中即 amount_math_fail。
_MATH_HINTS = ("小计", "总额", "行和", "vat", "折", "mismatch", "不平", "误读")


def run(ctx: StepContext) -> StepResult:
    """给 pending 的图片/PDF 过 OCR 归堆去重,给 pending 的销项 xlsx 直读。"""
    pending = ctx.store.list_items(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id, status="pending"
    )
    own_tax_id = _resolve_own_tax_id(ctx)
    # 别名闸 pearnly_ai_m1 开:走名集锚(法定名 + active human_confirmed 别名),补跨语种失锚。
    # 关:走单一法定名现状路,方向输出逐字节不变。fail-closed 于 feature_flags 内部。
    if _m1_enabled(ctx):
        own_name = None
        own_names = _resolve_own_names(ctx)
    else:
        own_name = _resolve_own_name(ctx)
        own_names = None

    bins: dict[str, int] = {}
    flagged = 0

    # 并发取 OCR、按原序回主线程逐件裁堆+落库。原序消费(非完成序)保证查重「先到先占」
    # 与串行逐字节一致;每件独立事务提交(有 cursor_factory 时),跑批中途被杀只丢在飞的
    # 那几件,已落库件不重烧(断点续跑从未处理件继续)。
    images = [it for it in pending if it["kind"] == kinds.UNKNOWN]
    # 查重表先从已提交事件重建再叠加本次批:逐件提交后 kill 中断,已落库原件不在 pending 里,
    # 内存从空建会让其复件漏判 duplicate → R1 双计(C1 打回单 R1 的静默钱洞)。重建保证
    # 中断续跑对查重的裁决与不中断跑逐字节一致。
    seen_purchase_fp: dict[str, str] = _replay_seen_fingerprints(ctx) if images else {}
    for item, ocr in _ocr_in_order(images, ctx.tenant_id):
        outcome = _classify_from_ocr(
            item,
            ocr,
            own_tax_id=own_tax_id,
            own_name=own_name,
            own_names=own_names,
            seen=seen_purchase_fp,
        )
        upd = outcome["update"]
        engine_ver = ocr.get("_ocr_engine") if isinstance(ocr, dict) else None
        with _item_scope(ctx):
            ctx.store.update_item(ctx.cur, tenant_id=ctx.tenant_id, item_id=item["id"], **upd)
            # 归堆即落 item_classified 事件:进项票带票面钱字段。这条事件是 reconcile 回放金额的
            # 唯一持久源(证据链 + 断点续跑),classify 不算钱,只把票面原值落进证据流。dedupe_key
            # 锚到 item:并发接管(过期租约被另一进程续跑)重放同件也只落一条,守恒不被撑破。
            # ocr_engine=OCR 管线版本(冻结 manifest 的模型版本自证据流取,不依赖 ai_usage 表)。
            _emit_classified(
                ctx,
                item,
                kind=upd["kind"],
                status=upd["status"],
                money=outcome.get("money"),
                ocr_engine=engine_ver,
            )
        bins[outcome["kind"]] = bins.get(outcome["kind"], 0) + 1
        if outcome["flagged"]:
            flagged += 1

    reads: dict[str, dict] = dict(ctx.data.get("sales_summary_reads") or {})
    for item in pending:
        if item["kind"] != kinds.SALES_SUMMARY:
            continue
        parsed, reason = _classify_summary(item)
        with _item_scope(ctx):
            if reason:
                ctx.store.update_item(
                    ctx.cur,
                    tenant_id=ctx.tenant_id,
                    item_id=item["id"],
                    status="flagged",
                    flag_reason=reason,
                )
                _emit_classified(ctx, item, kind=kinds.SALES_SUMMARY, status="flagged", money=None)
                flagged += 1
            else:
                ctx.store.update_item(
                    ctx.cur, tenant_id=ctx.tenant_id, item_id=item["id"], status="ok"
                )
                _emit_classified(
                    ctx, item, kind=kinds.SALES_SUMMARY, status="ok", money=None, sales_read=parsed
                )
                reads[item["id"]] = parsed

    return StepResult.ok(bins=bins, flagged=flagged, sales_summary_reads=reads)


@contextmanager
def _item_scope(ctx: StepContext):
    """单件写作用域。有 cursor_factory:每件开一个独立事务(update_item + item_classified 原子
    落库并提交),进程被杀只丢在飞件、已落件永久成立——逐件检查点。无 cursor_factory(内存
    测试 / CLI 单事务):复用 ctx.cur,由上层统一提交,行为逐字节不变。"""
    if ctx.cursor_factory is None:
        yield
        return
    prev = ctx.cur
    with ctx.cursor_factory() as cur:
        ctx.cur = cur
        try:
            yield
        finally:
            ctx.cur = prev


def _ocr_safe(item: dict, tenant_id: str):
    """取一件 OCR,单件隔离:异常原样返回(不抛,不拖垮整批)。成本按 _OCR_TASK + 本租户归因
    落 ai_usage(在本 worker 线程内设归因——ThreadPool 子线程起始上下文为空,主线程设了不算)。"""
    token = attribution.set_attribution(
        _OCR_TASK, tenant_id=str(tenant_id), trace_id=str(item.get("id") or "")
    )
    try:
        return _ocr_image(item["file_ref"])
    except Exception as exc:  # noqa: BLE001 - 单件隔离,绝不拖垮整步
        return exc
    finally:
        attribution.reset_attribution(token)


def _ocr_in_order(images: list[dict], tenant_id: str):
    """并发取 OCR、按输入原序 yield (item, ocr_or_exc)。并发上限见 _ocr_concurrency;
    ≤1 或单件走串行(免线程池开销,单测同步好断言)。原序消费保证下游查重/落库确定性。

    窗口式提交(2n)而非整批:消费方中途异常/生成器提前关闭时,排队未起跑的直接取消、
    在飞的不等(shutdown(wait=False)),失败立即上抛;白烧的 OCR 至多一个窗口,不是整批。"""
    n = _ocr_concurrency()
    if n <= 1 or len(images) <= 1:
        for it in images:
            yield it, _ocr_safe(it, tenant_id)
        return
    pool = ThreadPoolExecutor(max_workers=n, thread_name_prefix="wo-classify-ocr")
    window: deque = deque()
    rest = iter(images)
    try:
        for it in islice(rest, n * 2):
            window.append((it, pool.submit(_ocr_safe, it, tenant_id)))
        while window:
            item, fut = window.popleft()
            follow = next(rest, None)
            if follow is not None:
                window.append((follow, pool.submit(_ocr_safe, follow, tenant_id)))
            yield item, fut.result()
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _emit_classified(ctx, item, *, kind, status, money, sales_read=None, ocr_engine=None):
    """落一条 item_classified 证据事件。payload 带 item_id/kind/status,进项另带票面 money,
    销项直读另带 sales_read,OCR 件另带 ocr_engine(管线版本)——reconcile/冻结据此回放,不依赖
    同进程 ctx.data(续跑不丢)。

    dedupe_key 锚到 item:同件重放(并发接管/异常续跑)命中事件唯一约束不重记,守恒不被撑破。"""
    payload = {"item_id": item["id"], "kind": kind, "status": status}
    if money:
        payload["money"] = money
    if sales_read is not None:
        payload["sales_read"] = sales_read
    if ocr_engine:
        payload["ocr_engine"] = ocr_engine
    ctx.store.append_event(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        step="classify",
        event_type="item_classified",
        payload=payload,
        dedupe_key=f"classify:{item['id']}",
    )


def _classify_from_ocr(
    item: dict,
    ocr,
    *,
    own_tax_id: Optional[str],
    own_name: Optional[str],
    own_names=None,
    seen: dict,
) -> dict:
    """已取到 OCR(fields dict 或异常):归堆 → 购票查重 → 闸报警。异常只连坐这一件。

    OCR 调用本身在 _ocr_safe(可并发)完成,这里是纯裁决(主线程逐件、原序执行 → 查重确定性)。"""
    if isinstance(ocr, Exception):
        upd = {"status": "flagged", "kind": None, "flag_reason": f"ocr_error:{type(ocr).__name__}"}
        return {"kind": kinds.UNKNOWN, "flagged": True, "update": upd, "money": None}
    fields = ocr

    kind, bin_reason = sort_step.bin_ocr_fields(
        fields, own_tax_id=own_tax_id, own_name=own_name, own_names=own_names
    )

    if kind == kinds.PURCHASE_INVOICE:
        fp = _purchase_fingerprint(fields)
        hit = seen.get(fp) if fp else None
        if hit:
            upd = {
                "status": "excluded",
                "kind": kinds.DUPLICATE,
                "flag_reason": f"duplicate_of:{hit}",
            }
            return {"kind": kinds.DUPLICATE, "flagged": False, "update": upd, "money": None}
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
    if kind == kinds.NON_TAX:
        status = "excluded"
    else:
        status = "flagged" if reason else "ok"
    upd = {"status": status, "kind": kind, "flag_reason": reason}
    # 方向不明票 + 自动判本方销项票(sales_doc)都快照票面钱字段:方向票 OCR 已读过,人工裁进项
    # 后 reconcile 直接用这份读数进 R1,不必为定向重跑付费 OCR;sales_doc 的钱字段是 MC1-c.1 逐票
    # 销项聚合(r2_sales_corroboration 佐证层)的唯一料源,缺它聚合无从算起。
    capture_money = kind in (kinds.PURCHASE_INVOICE, decisions.SALES_DOC) or (
        reason or ""
    ).startswith(("direction_ambiguous", "sales_direction_unhandled"))
    money = _money_fields(fields) if capture_money else None
    return {"kind": kind, "flagged": status == "flagged", "update": upd, "money": money}


def _money_fields(fields: dict) -> dict:
    """票面钱字段快照(进 item_classified 事件,供 reconcile 回放合计/试算)。Decimal 交给
    reconcile,这里只搬 OCR 原值不做换算——净额/税额/含税额 + 票号税号做证据溯源。

    date/seller_name 是 E1 银行对账候选的日期/供应商锚(佐证层),纯附加字段,不参与 R1/R2
    税额计算(reconcile_gates 只读 subtotal/vat/total_amount)——缺失即为 None,对已有金标零影响。
    """
    return {
        "subtotal": fields.get("subtotal"),
        "vat": fields.get("vat"),
        "total_amount": fields.get("total_amount"),
        "invoice_number": fields.get("invoice_number"),
        "seller_tax": fields.get("seller_tax"),
        "invoice_date": fields.get("date"),
        "vendor": fields.get("seller_name"),
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


def _replay_seen_fingerprints(ctx: StepContext) -> dict[str, str]:
    """从已提交 item_classified 事件重建进项查重表 {指纹: 原件文件名}。

    指纹三要素(seller_tax/invoice_number/total_amount)都在事件的 money 快照里,与在跑时
    对 OCR fields 算指纹同源同值;文件名从 items 表按 item_id 回查(duplicate_of:{name} 的
    展示口径不变)。只认 kind=purchase_invoice(方向票/复件事件无 money 或非该 kind,天然
    跳过——与在跑时只为进项票种表的语义一致)。首个持有者在先(事件按落库序,复件不覆写)。"""
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    classified = evidence.replay_items_by_type(events, "item_classified")
    if not classified:
        return {}
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    ref_by_id = {it["id"]: it.get("file_ref") for it in items}
    seen: dict[str, str] = {}
    for item_id, rec in classified.items():
        payload = rec["payload"]
        if payload.get("kind") != kinds.PURCHASE_INVOICE:
            continue
        fp = _purchase_fingerprint(payload.get("money") or {})
        if fp and fp not in seen:
            seen[fp] = Path(ref_by_id.get(item_id) or "").name
    return seen


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


def _default_resolve_own_names(ctx: StepContext) -> list:
    """名集锚(别名闸开时):法定名 + 该客户 active human_confirmed 别名 → [(name, mode)]。

    经 client_alias_store.resolve_names(单一事实源,含法定名并集)。工单未绑客户 → 空集
    → bin_ocr_fields 名集为空,退回 ambiguous(与无名兜底同口径)。查询走 ctx.cur 同事务。
    """
    wo = ctx.store.get_work_order(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    client_id = (wo or {}).get("workspace_client_id")
    if not client_id:
        return []
    return client_alias_store.resolve_names(
        ctx.cur, tenant_id=ctx.tenant_id, workspace_client_id=client_id
    )


def _default_m1_enabled(ctx: StepContext) -> bool:
    """别名/名集锚放量闸(pearnly_ai_m1)。工单线只有 tenant_id(work_orders.tenant_id NOT NULL),
    按 tenant 判定;fail-closed 在 feature_flags 内部(基建抖动绝不误开)。"""
    return feature_flags.pearnly_ai_m1_enabled_for(ctx.tenant_id, None)


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
    fields["_ocr_engine"] = legacy.get("engine")  # 管线版本 → item_classified 证据(冻结用)
    return fields


def _default_read_sales_summary(path: str) -> dict:
    """真实现:xlsx 字节交给 summary_import.parse.parse_table 直读(纯函数,零成本)。"""
    data = Path(path).read_bytes()
    return parse_table(data, filename=Path(path).name)


# 注入点:模块级绑定,测试用 classify._xxx = fake 替换,不改调用方代码。
_resolve_own_tax_id = _default_resolve_own_tax_id
_resolve_own_name = _default_resolve_own_name
_resolve_own_names = _default_resolve_own_names
_m1_enabled = _default_m1_enabled
_ocr_image = _default_ocr_image
_read_sales_summary = _default_read_sales_summary
