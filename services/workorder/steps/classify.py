# -*- coding: utf-8 -*-
"""classify 步:进项票过 OCR 归堆去重,销项汇总表直读(任务包 §5 步 3)。

纯编排:取 pending 料 → 跨单去重复用(ocr_reuse)/ 调注入的 OCR/直读入口 → 用
sort.bin_ocr_fields 归堆、purchase_dedup 算票面级指纹查单内重复票 → update_item 落堆/落
状态 → 末尾 taxid_alert 守护税号错录。真 OCR/直读入口通过模块级函数注入(_ocr_image /
_read_sales_summary / _resolve_own_tax_id / _find_ocr_by_hashes),默认绑生产实现,单测全部
patch 掉——本文件测试不碰任何 API key,不触发真实付费调用(硬约束)。

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
from itertools import islice
from pathlib import Path
from typing import Optional

from core import feature_flags
from services.ai_gateway import attribution
from services.ocr import escalation_budget
from services.summary_import.parse import parse_table
from services.workorder import decisions, kinds, storage
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import checkpoint, ocr_cost_cap, ocr_ledger, ocr_quota, ocr_reuse
from services.workorder.steps import ocr_snapshots, purchase_dedup, taxid_alert
from services.workorder.steps import sort as sort_step
from services.workspace import client_alias_store

# quota 待补件的 flag_reason(续跑起手复位这些件回 pending 重试;单一事实源在此)。
_QUOTA_FLAG = "ocr_error:quota"

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
    _reset_quota_deferred(ctx)  # R1:先于取 pending,把上次 quota 待补件复位回 pending 一起重烧
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
    stmt_regroup = _stmt_regroup_enabled(ctx)  # SA3R-a 对账单续页回收闸,详见传入的 bin_ocr_fields

    bins: dict[str, int] = {}
    flagged = 0
    # OCR 识别台账双写归属(件 1):工单绑定客户账套的 owner user + workspace_client_id,
    # 整步解析一次(逐件复用,不 N 次查库)。解不出(未绑客户/无 owner)→ None,双写整体
    # 优雅跳过,item.ocr_history_id 如实留 NULL(只向前,不回填存量)。
    history_owner = _resolve_history_owner(ctx)

    # 并发取 OCR、按原序回主线程逐件裁堆+落库。原序消费(非完成序)保证查重「先到先占」
    # 与串行逐字节一致;每件独立事务提交(有 cursor_factory 时),跑批中途被杀只丢在飞的
    # 那几件,已落库件不重烧(断点续跑从未处理件继续)。
    images = [it for it in pending if it["kind"] == kinds.UNKNOWN]
    # R2B 跨单去重:调 OCR 前按文件哈希查同租户+同账套的既有识别读数,命中且带完整闸字段即复用
    # (零 OCR、零 ai_usage),item 照常归堆、事件标 ocr_reused_from——跨客户绝不串、老记录缺闸字段
    # 不复用照常烧(省钱绝不吞报警)。
    reused = ocr_reuse.resolve(images, history_owner, finder=_find_ocr_by_hashes) if images else {}
    # 查重表先从已提交事件重建再叠加本次批:逐件提交后 kill 中断,已落库原件不在 pending 里,内存
    # 从空建会让复件漏判 duplicate → R1 双计(C1 静默钱洞)。这是【循环前已提交】种子快照,与末尾
    # taxid_alert 的【循环后】快照是两个时点、不可合并(合用会漏本轮票面税号 → 守护闸失灵)。
    seen_purchase_fp: dict[str, str] = (
        purchase_dedup.replay_seen_fingerprints(ctx) if images else {}
    )
    # R1:配额退避+全局降速协调器 / 贵模型回落跑批级配额(用尽走诚实路径)/ 成本封顶(达 cap 停投料)。
    governor = ocr_quota.QuotaGovernor() if images else None
    budget = escalation_budget.new_budget(ocr_cost_cap.fallback_limit()) if images else None
    cost_cap = ocr_cost_cap.from_ctx(ctx, [it["id"] for it in images])
    quota_deferred = 0
    cost_capped = False
    # 复用件直接给缓存 fields(reused_from=源 history_id),其余走并发 OCR;原序消费保查重确定性。
    ocr_stream = ocr_reuse.stream(
        images,
        reused,
        lambda batch: _ocr_in_order(batch, ctx.tenant_id, governor=governor, budget=budget),
    )
    for item, ocr, reused_from in ocr_stream:
        # 撞配额且退避用尽:不落终局证据(留续跑重烧,免 dedupe 锁死错值),挂 quota 待补,整步 stuck 待续。
        if isinstance(ocr, Exception) and ocr_quota.is_quota_error(ocr):
            with checkpoint.item_scope(ctx):
                ctx.store.update_item(
                    ctx.cur,
                    tenant_id=ctx.tenant_id,
                    item_id=item["id"],
                    status="flagged",
                    flag_reason=_QUOTA_FLAG,
                )
            quota_deferred += 1
            continue
        outcome = _classify_from_ocr(
            item,
            ocr,
            own_tax_id=own_tax_id,
            own_name=own_name,
            own_names=own_names,
            seen=seen_purchase_fp,
            stmt_regroup=stmt_regroup,
        )
        upd = outcome["update"]
        engine_ver = ocr.get("_ocr_engine") if isinstance(ocr, dict) else None
        # 件 1:每件 OCR 落库时双写 ocr_history(识别台账),失败/无归属只留 NULL,绝不拖垮 classify。
        # 复用路同样双写一条本工单台账行(引用同 file_hash,不重复计费),主站看得见工单侧识别。
        history_id = (
            _record_ocr_history(item, ocr, history_owner) if isinstance(ocr, dict) else None
        )
        link = {"ocr_history_id": history_id} if history_id else {}
        with checkpoint.item_scope(ctx):
            ctx.store.update_item(
                ctx.cur, tenant_id=ctx.tenant_id, item_id=item["id"], **link, **upd
            )
            # 归堆即落 item_classified 事件(reconcile 回放金额的唯一持久源);dedupe_key 锚到 item,
            # 并发接管重放同件只落一条,守恒不被撑破。ocr_engine=管线版本(冻结 manifest 取);
            # reused_from=复用源 history_id(证据链可溯,标明本件读数复用而非新烧)。
            _emit_classified(
                ctx,
                item,
                kind=upd["kind"],
                status=upd["status"],
                money=outcome.get("money"),
                edc=outcome.get("edc"),
                ocr_engine=engine_ver,
                reused_from=reused_from,
            )
        bins[outcome["kind"]] = bins.get(outcome["kind"], 0) + 1
        if outcome["flagged"]:
            flagged += 1
        # 达成本封顶即停止投料:未处理件留 pending,生成器收尾取消在队未起的 OCR(白烧至多一窗)。
        # 复用件零成本不触发封顶回查;exceeded 内部走独立短事务读台账,读完即释放锁(绝不在步事务
        # 里攥 ai_usage 锁,见 ocr_cost_cap 死锁根因)。
        if reused_from is None and cost_cap is not None and cost_cap.exceeded():
            cost_capped = True
            break

    # 撞配额待补 / 成本封顶:整步 stuck 诚实待续(未处理件留 pending,人工 /run 重给预算)。
    if quota_deferred:
        return StepResult.stuck([f"ocr_quota_deferred:{quota_deferred}"])
    if cost_capped:
        return StepResult.stuck(["ocr_cost_cap_exceeded"])

    reads: dict[str, dict] = dict(ctx.data.get("sales_summary_reads") or {})
    for item in pending:
        if item["kind"] != kinds.SALES_SUMMARY:
            continue
        parsed, reason = _classify_summary(item)
        with checkpoint.item_scope(ctx):
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

    # R4 税号错录守护闸:分类跑完跨料聚合票面税号(内部【循环后】重取事件流,须含本轮新落的
    # item_classified,与上方 seen_purchase_fp 循环前种子分读)→ 疑似录错落工单级警示。纯读不碰钱/堆。
    taxid_alert.flag_if_suspected(ctx, own_tax_id)
    return StepResult.ok(bins=bins, flagged=flagged, sales_summary_reads=reads)


def _ocr_safe(item: dict, tenant_id: str, governor=None, budget=None):
    """取一件 OCR,单件隔离 + 配额退避。成本按 _OCR_TASK + 本租户归因落 ai_usage(在本 worker
    线程内设——ThreadPool 子线程起始上下文为空,主线程设了不算)。budget 同款 per-worker 播种:
    贵模型回落跑批级配额跨并发件全局递减(见 escalation_budget)。撞 quota 的退避在 ocr_quota。"""
    token = attribution.set_attribution(
        _OCR_TASK, tenant_id=str(tenant_id), trace_id=str(item.get("id") or "")
    )
    btoken = escalation_budget.set_budget(budget) if budget is not None else None
    try:
        return ocr_quota.fetch_with_retry(lambda: _ocr_image(item["file_ref"]), governor=governor)
    finally:
        if btoken is not None:
            escalation_budget.reset_budget(btoken)
        attribution.reset_attribution(token)


def _ocr_in_order(images: list[dict], tenant_id: str, *, governor=None, budget=None):
    """并发取 OCR、按输入原序 yield (item, ocr_or_exc)。并发上限见 _ocr_concurrency;
    ≤1 或单件走串行(免线程池开销,单测同步好断言)。原序消费保证下游查重/落库确定性。

    窗口式提交(2n)而非整批:消费方中途异常/生成器提前关闭时(如成本封顶 break),排队未起跑的
    直接取消、在飞的不等(shutdown(wait=False));白烧的 OCR 至多一个窗口,不是整批。"""
    n = _ocr_concurrency()
    if n <= 1 or len(images) <= 1:
        for it in images:
            yield it, _ocr_safe(it, tenant_id, governor, budget)
        return
    pool = ThreadPoolExecutor(max_workers=n, thread_name_prefix="wo-classify-ocr")
    window: deque = deque()
    rest = iter(images)
    try:
        for it in islice(rest, n * 2):
            window.append((it, pool.submit(_ocr_safe, it, tenant_id, governor, budget)))
        while window:
            item, fut = window.popleft()
            follow = next(rest, None)
            if follow is not None:
                window.append((follow, pool.submit(_ocr_safe, follow, tenant_id, governor, budget)))
            yield item, fut.result()
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _reset_quota_deferred(ctx: StepContext) -> None:
    """续跑起手把上次 quota 待补件(flagged, ocr_error:quota)复位回 pending 供重烧(它们当时未落
    终局证据事件,dedupe_key 不会锁死错值,重烧与不中断跑等价)。走独立提交事务(有 factory 时)
    释放行锁,免与后续 item_scope 逐件子事务互等自死锁。"""
    kw = dict(tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id, flag_reason=_QUOTA_FLAG)
    if ctx.cursor_factory is None:
        ctx.store.reset_quota_deferred_items(ctx.cur, **kw)
    else:
        with ctx.cursor_factory() as cur:
            ctx.store.reset_quota_deferred_items(cur, **kw)


def _emit_classified(
    ctx, item, *, kind, status, money, sales_read=None, edc=None, ocr_engine=None, reused_from=None
):
    """落一条 item_classified 证据事件。payload 带 item_id/kind/status,进项另带票面 money,
    销项直读另带 sales_read,EDC 结算票另带 edc 快照(SA-2b 聚合回放的唯一持久源),OCR 件
    另带 ocr_engine(管线版本)——reconcile/冻结据此回放,不依赖同进程 ctx.data(续跑不丢)。
    reused_from(R2B):本件读数复用自哪条 ocr_history(证据链可溯),新烧件为 None 不挂键。

    dedupe_key 锚到 item:同件重放(并发接管/异常续跑)命中事件唯一约束不重记,守恒不被撑破。"""
    payload = {"item_id": item["id"], "kind": kind, "status": status}
    if money:
        payload["money"] = money
    if sales_read is not None:
        payload["sales_read"] = sales_read
    if edc is not None:
        payload["edc"] = edc
    if ocr_engine:
        payload["ocr_engine"] = ocr_engine
    if reused_from:
        payload["ocr_reused_from"] = reused_from
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
    stmt_regroup: bool = False,
) -> dict:
    """已取到 OCR(fields dict 或异常):归堆 → 购票查重 → 闸报警。异常只连坐这一件。

    OCR 调用本身在 _ocr_safe(可并发)完成,这里是纯裁决(主线程逐件、原序执行 → 查重确定性)。"""
    if isinstance(ocr, Exception):
        # 撞配额(退避已在 _ocr_safe 用尽)归一到 ocr_error:quota,让 run() 走 quota 待补/续跑路;
        # 其余 OCR 异常按类型名如实点名,单件隔离不拖垮整步。
        detail = "quota" if ocr_quota.is_quota_error(ocr) else type(ocr).__name__
        upd = {"status": "flagged", "kind": None, "flag_reason": f"ocr_error:{detail}"}
        return {"kind": kinds.UNKNOWN, "flagged": True, "update": upd, "money": None}
    fields = ocr

    kind, bin_reason = sort_step.bin_ocr_fields(
        fields,
        own_tax_id=own_tax_id,
        own_name=own_name,
        own_names=own_names,
        stmt_regroup=stmt_regroup,
    )

    if kind == kinds.PURCHASE_INVOICE:
        fp = purchase_dedup.purchase_fingerprint(fields)
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
    money = ocr_snapshots.money_fields(fields) if capture_money else None
    # EDC 结算票快照走独立 payload 键(不进 money):money 是银行对账候选/R1 回放的料源,
    # 结算票混进去会被 E1 当票据候选双配(它已由 SA-1 的 EDC↔银行专线对账)。
    edc = ocr_snapshots.edc_fields(fields) if kind == kinds.EDC_SETTLEMENT else None
    return {"kind": kind, "flagged": status == "flagged", "update": upd, "money": money, "edc": edc}


def _classify_summary(item: dict) -> tuple:
    """一份销项汇总表:直读拿 headers/rows,解不出留原因,不硬吃。"""
    try:
        parsed = _read_sales_summary(item["file_ref"])
    except Exception as exc:  # noqa: BLE001
        return None, f"summary_read_error:{type(exc).__name__}"
    if not parsed.get("rows"):
        return None, "summary_unparseable"
    return parsed, None


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


def _default_stmt_regroup_enabled(ctx: StepContext) -> bool:
    """对账单续页回收闸(pearnly_ai_stmt_regroup · SA3R-a)。按 tenant 判定;fail-closed 内部。"""
    return feature_flags.pearnly_ai_stmt_regroup_enabled_for(ctx.tenant_id)


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

    data = storage.read_bytes(path)  # 落盘密文解回明文再喂 OCR(双轨读)
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
    data = storage.read_bytes(path)  # 落盘密文解回明文再解析(双轨读)
    return parse_table(data, filename=Path(path).name)


def _default_find_ocr_by_hashes(**kwargs) -> dict:
    """真实现:按整批文件哈希一次查回同租户+严格同账套的既有识别读数(R2B 跨单去重)。
    strict_workspace 钉死,跨客户绝不串(未归属 NULL 行不认)。单测 patch 掉,不触真库。"""
    from services.ocr_history import hash_dedup

    return hash_dedup.find_ocr_by_hashes(strict_workspace=True, **kwargs)


# 注入点:模块级绑定,测试用 classify._xxx = fake 替换,不改调用方代码。
_resolve_own_tax_id = _default_resolve_own_tax_id
_resolve_own_name = _default_resolve_own_name
_resolve_own_names = _default_resolve_own_names
_resolve_history_owner = ocr_ledger.resolve_owner
_record_ocr_history = ocr_ledger.record
_m1_enabled = _default_m1_enabled
_stmt_regroup_enabled = _default_stmt_regroup_enabled
_ocr_image = _default_ocr_image
_read_sales_summary = _default_read_sales_summary
_find_ocr_by_hashes = _default_find_ocr_by_hashes
