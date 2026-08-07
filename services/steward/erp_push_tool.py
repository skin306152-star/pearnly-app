# -*- coding: utf-8 -*-
"""管家第一个写工具 erp_push:把一张已识别的票经桥真写进 Express(B4)。

两段式,与授权闸的「批的就是执行的」对齐:
  ① prepare(请求侧 · 铸卡前):把用户嘴里的「那张 7-11 的票」落成一条真实 history —— 命中
     0 条/多条都不猜,退回可追问的错误;顺带把目标账套(端点配置)与票面快照(票号/卖方/
     含税额)钉进参数。授权卡因此能说清「对哪个账套做什么、影响几条」,而不是摆一串 uuid。
  ② erp_push(执行侧 · worker 持批文调):重新读票 → 与快照比对(铸卡后被改过就不写)→
     preflight_express 组装 express payload v1(复用既有 mapper,不自己拼)→ 经桥门面
     submit_write 投单 → 轮询 write_status 到终态。

不复用 enqueue_express 的原因:那条路是「写进 erp_push_logs 等小助手来领」(pending),
本工具走的是 P2-A 的桥直写(submit_write),两者只共用 preflight 这一段体检 + 载荷装配。
推送日志照旧落一行(erp_push_logs 是推送状态唯一事实源),否则管家推完自己的
push_log_query 会答「近 7 天 0 条」;投单没投出去的两条路(桥不在线/桥拒收)同样落 ——
「会计说推了但账套里没有」最需要的就是这两条的痕迹。

超时不等于没写进去(见 bridge/client.write 顶注):桥领走后的写活迟到 ack 照样落库,
所以等不到终态时报 pending 并把 job_id 交出去对账,文案明确「别重推」——重推 = 双写。
在途那一行还要钉一个远期占位租约:Express 旧队列就是「本表 status='pending' 且没被租约
占住的行」,不占住的话小助手会把同一份载荷再领走写一遍。

双写的另外两个口子一并堵在本模块:①同 history × endpoint 已 success 过就不再推
(别家推送腿都有这道闸);②大脑给的 direction 只当复核 —— 它是 model_freeform 槽,认它
就等于让一个词盖过税号锚点的确定性判定。

过账去向(posting_kind)可在对话里后补:这次会计明确说了「按库存/服务过账」就以这次说的为
准,没说才照旧读票上已存的声明(prepare 里 resolve_posting_kind 定优先级)。执行前先把声明
回写进 ocr_history.posting_kind(_reconcile_posting_kind)——四条推送腿共用这一列,聊天里
的声明不落档,下一条腿(重试/其它入口)读到的还是旧值,照样把票 escalate 给会计。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from services.agent.contracts import ToolResult
from services.erp.bridge import BridgeError, BridgeUnavailable
from services.steward import erp_push_trail as trail, tool_scope
from services.steward.registry import ToolContext
from services.steward.tool_scope import ERR_INVOICE_AMBIGUOUS, ERR_INVOICE_NOT_FOUND  # noqa: F401

logger = logging.getLogger(__name__)

ERR_ENDPOINT_MISSING = "steward.erp_endpoint_missing"
ERR_ACCOUNT_SET_MISMATCH = "steward.account_set_mismatch"
ERR_INVOICE_CHANGED = "steward.invoice_changed"
ERR_ALREADY_PUSHED = "steward.erp_already_pushed"
ERR_DIRECTION_CONFLICT = "steward.erp_direction_conflict"
ERR_PUSH_BLOCKED = "steward.erp_push_blocked"
ERR_BRIDGE_OFFLINE = "steward.bridge_offline"
ERR_PUSH_REJECTED = "steward.erp_push_rejected"
ERR_PUSH_FAILED = "steward.erp_push_failed"
ERR_PUSH_EXPIRED = "steward.erp_push_expired"
ERR_PUSH_PENDING = "steward.erp_push_pending"
# 确认放行的写单被领走后没回结果:与 ERR_PUSH_EXPIRED 同一个 job 状态(expired),但事实相反
# —— 那条是"没人来领,肯定没写",这条是"领了,写没写不知道"。共用一句文案就等于替她断定
# 没写,而她照着再说一次就是账上两张。
ERR_PUSH_UNCERTAIN = "steward.erp_push_uncertain"
# 声明跟着票走(见 _reconcile_posting_kind 顶注):回写 ocr_history.posting_kind 失败当硬
# 失败,绝不装作这次推送已经用上了声明的过账去向。
ERR_POSTING_KIND_WRITE_FAILED = "steward.posting_kind_write_failed"
# Express 正开着这个账套 → 桥连备份都没做就快拒。旧队列(小助手来领)撞上它会自己重领,
# 桥直写这条路不会 —— 共用 ERR_PUSH_FAILED 的"查清原因后再说一次"等于让会计去查一件
# 她一眼就能解决的事(把 Express 关掉),而她无从知道那才是原因。
ERR_PUSH_ACCOUNT_BUSY = "steward.erp_push_account_busy"
# 桥端占用码(companion bridge/writepath/orchestrator.ERR_WAITING_LOCK)。云端不产它,只认。
BRIDGE_ACCOUNT_BUSY_CODE = "ACCOUNT_BUSY_LOCKED"


# 快照字段:铸卡时定格、执行前重比。票面变了(会计改了金额/票号/过账去向)旧批文就不作数
# —— posting_kind 在列里是因为它决定这张票按库存还是按服务记账,批的是哪一种就得写哪一种。
SNAPSHOT_KEYS = ("invoice_no", "seller_name", "total_amount", "posting_kind")
# 授权卡上的参数行顺序(前端按键序摆行)。
ARG_KEYS = (
    "account_set",
    "direction",
    "posting_kind",
    "invoice_no",
    "seller_name",
    "total_amount",
    "history_id",
)

# 轮询:桥端一次写活是分钟级(备份→写 DBF→重建 CDX),2 秒一拍够密。deadline 留在任务
# 超时(registry.ERP_PUSH_TIMEOUT_S)之内,好让「还在写」由本函数如实报出来并带上 job_id
# ——被 worker 的 wait_for 硬砍掉的话,job_id 就丢了,会计没有东西可以对账。
_POLL_INTERVAL_S = 2.0
_POLL_DEADLINE_S = 840.0


@dataclass
class PrepareResult:
    """铸卡前的接地结果:成功给可执行参数 + 卡面事实;失败给可追问的 ToolResult。"""

    args: dict = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    workspace_client_id: int = 0  # 目标账套主体(nonce 表的目标位 · 令牌因此绑死这个账套)
    error: Optional[ToolResult] = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _fail(code: str, **data) -> PrepareResult:
    return PrepareResult(error=ToolResult(ok=False, error_code=code, data=data))


_money = tool_scope.money  # 钱不过 float:卡上印的、比对的、审计的必须同一个值


def express_endpoint(user_id: str) -> Optional[dict]:
    """本用户的 Express 连接(单例 · push_store 建连接时就保 express 唯一)。"""
    from core import db

    for endpoint in db.list_erp_endpoints(user_id):
        if (endpoint.get("adapter") or "").lower() == "express" and endpoint.get("enabled", True):
            return endpoint
    return None


def prepare(ctx: ToolContext, args: dict) -> PrepareResult:
    """用户级参数 → 可执行参数 + 卡面事实。任何一步接不了地都不铸卡(绝不批一张空头卡)。"""
    from services.erp.express_push.direction import normalize as normalize_direction
    from services.erp.express_push.posting_kind import resolve_posting_kind

    endpoint = express_endpoint(ctx.user_id)
    if not endpoint:
        return _fail(ERR_ENDPOINT_MISSING)
    account_set = str((endpoint.get("config") or {}).get("account_set") or "").strip()
    if not account_set:
        return _fail(ERR_ENDPOINT_MISSING)

    asked = str(args.get("account_set") or "").strip()
    if asked and asked.upper() != account_set.upper():
        # 会计说 A、连接配的是 B:账套写错是账务事故,宁可停下问,绝不"就近"推进 B。
        return _fail(ERR_ACCOUNT_SET_MISMATCH, asked=asked, account_set=account_set)

    keyword = str(args.get("keyword") or "")
    row, err = tool_scope.resolve_invoice(ctx, keyword)
    if err:
        return PrepareResult(error=err)
    workspace_client_id = int(row.get("workspace_client_id") or 0)
    if workspace_client_id and not tool_scope.in_scope(ctx, workspace_client_id):
        # 接地闸与执行闸(erp_push 里那道)同口径:作用域外的票一律当查无 —— 否则卡面会把
        # 被分派成员根本看不到的那个账套的票号/金额印出来,批准后才在执行层撞成死胡同。
        return _fail(ERR_INVOICE_NOT_FOUND, keyword=keyword)

    history_id = str(row.get("id") or "")
    prior = _prior_success(ctx, endpoint, history_id)
    if prior:
        # 别家推送腿投单前都查这一条(手动推/自动推/重试/Agent),写工具此前没有:批准一张
        # 已经推成功的票 = 同一张发票在客户账套里记两遍(进项税、应付、库存全部翻倍)。
        return _fail(
            ERR_ALREADY_PUSHED,
            invoice_no=str(row.get("invoice_no") or ""),
            account_set=account_set,
            pushed_at=_stamp(prior.get("created_at")),
        )

    # 过账去向只有详情查得到(列表 SQL 不带这一列),而它决定按库存还是按服务记账 —— 卡上
    # 不印出来,批准的人看不出这张卡把「库存」办成了「服务」。
    detail = _load_history(ctx, history_id) or {}
    resolved = {
        "history_id": history_id,
        "account_set": account_set,
        "direction": normalize_direction(args.get("direction")) or "",
        # 这次说了「按库存/服务过账」就以这次说的为准,没说才照旧读票上已存的声明 ——
        # resolve_posting_kind 是这道优先级的单一权威(explicit 非法值当没给,自动回落)。
        "posting_kind": resolve_posting_kind(args.get("posting_kind"), detail) or "",
        "invoice_no": str(row.get("invoice_no") or ""),
        "seller_name": str(row.get("seller_name") or ""),
        "total_amount": _money(row.get("total_amount")),
    }
    return PrepareResult(
        args={k: resolved[k] for k in ARG_KEYS},
        facts={**resolved, "doc_count": 1},
        workspace_client_id=workspace_client_id,
    )


def _prior_success(ctx: ToolContext, endpoint: dict, history_id: str) -> Optional[dict]:
    """同 history × endpoint 是否已经推成功过(命中即最近那条 success 日志)。

    与别家推送腿共用 db.has_recent_successful_push 的口径,不另起一份判据。查询本身出错时
    返 None 放行 —— 桥端幂等是最后一道墙,宁可让那道墙拦,也不因为一次读库抖动就把会计
    合法的推送永久堵死。
    """
    from core import db

    if not history_id:
        return None
    try:
        return db.has_recent_successful_push(history_id, str(endpoint.get("id") or ""), ctx.user_id)
    except Exception:  # noqa: BLE001 — 防重推查询挂了不该反过来阻断推送
        logger.warning("[steward.erp_push] dedup lookup failed history=%s", history_id[:8])
        return None


def _stamp(value) -> str:
    """时间戳 → 「2026-07-26 14:03」这样能念出来的字符串(答复层直接印)。"""
    text = value.isoformat() if hasattr(value, "isoformat") else str(value or "")
    return text[:16].replace("T", " ")


def _load_history(ctx: ToolContext, history_id: str) -> Optional[dict]:
    from core import db

    return db.get_ocr_history_detail(ctx.user_id, history_id, tenant_id=ctx.tenant_id)


def _snapshot_drift(history: dict, args: dict) -> Optional[str]:
    """票面与批文快照的差异键(None = 一致)。会计在等批准的空档改了票,这张批文就作废。"""
    current = {
        "invoice_no": str(history.get("invoice_no") or ""),
        "seller_name": str(history.get("seller_name") or ""),
        "total_amount": _money(history.get("total_amount")),
        "posting_kind": str(history.get("posting_kind") or ""),
    }
    for key in SNAPSHOT_KEYS:
        if current[key] != str(args.get(key) or ""):
            return key
    return None


def _reconcile_posting_kind(ctx: ToolContext, history: dict, args: dict) -> Optional[ToolResult]:
    """批文里声明的过账去向落回票上(声明跟着票走 · 铁律)。

    四条推送腿(手动 / 识别后自动 / 失败重试 / 批量分拣)共用 ocr_history.posting_kind 这一
    列 —— 这次在对话里说的「按库存/服务过账」只落在这次调用的参数里不落档的话,下一条腿读到
    的还是旧值,照样 escalate 交会计。写在 _snapshot_drift 之前跑:批文声明与票上旧值本来
    就会不同(声明就是为了改它),先落档同步,票面对比才不会把这次声明误判成"等批的空档被
    人偷改过"。

    只在真声明了(合法值)且与票上现值不同才写库,没声明 / 声明和现值一致都不必要地写一次。
    回写失败当硬失败:不能假装这次推送已经用上了声明的去向,推送继续走下去只会把票记到会计
    没说过的那一侧。
    """
    from services.erp.express_push.posting_kind import normalize as normalize_posting_kind
    from services.ocr_history.posting_kind_store import update_history_posting_kind

    declared = normalize_posting_kind(args.get("posting_kind"))
    if not declared or declared == str(history.get("posting_kind") or ""):
        return None
    history_id = str(args.get("history_id") or "")
    if not update_history_posting_kind(history_id, declared, ctx.user_id, ctx.tenant_id):
        return ToolResult(
            ok=False, error_code=ERR_POSTING_KIND_WRITE_FAILED, data={"history_id": history_id}
        )
    history["posting_kind"] = declared
    return None


def _build_payload(
    endpoint: dict, history: dict, direction: str, declared_posting_kind: Optional[str] = None
) -> tuple[Optional[dict], str, str]:
    """走 preflight 的全套体检 + mapper 装配,返回 (express payload v1, 错误码, 细节)。

    过账去向必须显式解析后传进去:preflight 自己不读票上的声明(那是 enqueue 那条腿干的),
    漏传 = 上传向导里明确选了「库存」的票被按服务记账 —— 采购不建库存品不入库、销售不扣
    库存不结转 COGS,或者画像判 blocks_auto_posting 的账套直接 escalate、这张票永远推不动。

    declared_posting_kind 是这次批文里的声明(经 _reconcile_posting_kind 落档、与 history
    已同步)—— 传给 resolve_posting_kind 让它优先于票上的值,聊天里刚说的这次和上传向导选的
    上次同等权威,不因为走的是对话这条腿就矮一头。

    大脑给的方向只当复核:direction 是 model_freeform 槽,接地闸不要求它出现在用户原话里,
    认它就等于让一个词盖过税号锚点的确定性判定(进项票走 sales_mapper → 记成收入 + 销项税,
    ภ.พ.30 两侧同时错)。与体检判出来的方向不一致 → 停手问人,绝不按「谁更晚说」定。
    """
    from services.erp.express_push.posting_kind import resolve_posting_kind
    from services.erp.express_push.preflight import preflight_express

    kind = resolve_posting_kind(declared_posting_kind, history)
    pf = preflight_express(endpoint, history, posting_kind=kind)
    if pf.disabled:
        return None, ERR_PUSH_BLOCKED, "express_disabled"
    if pf.blocked:
        return None, ERR_PUSH_BLOCKED, pf.reason or "blocked"
    if direction and pf.direction and direction != pf.direction:
        return None, ERR_DIRECTION_CONFLICT, pf.direction
    return pf.payload, "", ""


def _await_write(tenant_id: str, job_id: str) -> dict:
    """轮询桥的写活到终态。返回 {status, result, error};等不到终态 → status='pending'。"""
    from services.erp.bridge import client as bridge_client

    deadline = time.monotonic() + _POLL_DEADLINE_S
    while True:
        job = bridge_client.write_status(tenant_id, job_id) or {}
        status = str(job.get("status") or "")
        if status in ("done", "failed", "expired"):
            return {"status": status, "result": job.get("result") or {}, "error": job.get("error")}
        if time.monotonic() >= deadline:
            return {"status": "pending", "result": {}, "error": None}
        time.sleep(_POLL_INTERVAL_S)


def erp_push(ctx: ToolContext, args: dict) -> ToolResult:
    """把一张已识别的票经桥真写进 Express。只在持批文时进得来(闸在 tools.run)。"""
    endpoint = express_endpoint(ctx.user_id)
    if not endpoint:
        return ToolResult(ok=False, error_code=ERR_ENDPOINT_MISSING)
    account_set = str(args.get("account_set") or "").strip()
    configured = str((endpoint.get("config") or {}).get("account_set") or "").strip()
    if not account_set or account_set != configured:
        # 铸卡后连接被改成别的账套 → 批的那个账套已不是现在会写进去的那个,停手。
        return ToolResult(
            ok=False,
            error_code=ERR_ACCOUNT_SET_MISMATCH,
            data={"asked": account_set, "account_set": configured},
        )

    history = _load_history(ctx, str(args.get("history_id") or ""))
    if not history:
        return ToolResult(ok=False, error_code=ERR_INVOICE_NOT_FOUND, data={"keyword": ""})
    wcid = history.get("workspace_client_id")
    if wcid and ctx.allowed_client_ids is not None and int(wcid) not in ctx.allowed_client_ids:
        return ToolResult(ok=False, error_code=ERR_INVOICE_NOT_FOUND, data={"keyword": ""})

    kind_err = _reconcile_posting_kind(ctx, history, args)
    if kind_err:
        return kind_err
    drift = _snapshot_drift(history, args)
    if drift:
        return ToolResult(ok=False, error_code=ERR_INVOICE_CHANGED, data={"field": drift})

    # 铸卡时查过一次,这里再查一次:等批准的空档里,会计完全可能已经在集成页手动推过。
    prior = _prior_success(ctx, endpoint, str(history.get("id") or ""))
    if prior:
        return ToolResult(
            ok=False,
            error_code=ERR_ALREADY_PUSHED,
            data={
                "invoice_no": str(history.get("invoice_no") or ""),
                "account_set": account_set,
                "pushed_at": _stamp(prior.get("created_at")),
            },
        )

    direction = str(args.get("direction") or "")
    payload, code, detail = _build_payload(endpoint, history, direction, args.get("posting_kind"))
    if not payload:
        data = (
            {"asked": direction, "detected": detail}
            if code == ERR_DIRECTION_CONFLICT
            else {"reason": detail}
        )
        return ToolResult(ok=False, error_code=code, data=data)

    return _submit(ctx, endpoint, history, payload, account_set)


def _submit(
    ctx: ToolContext, endpoint: dict, history: dict, payload: dict, account_set: str
) -> ToolResult:
    """投单 + 等终态 + 落推送日志/审计。桥层异常一律翻成人话错误码,不上抛。"""
    from services.erp.bridge import client as bridge_client
    from services.erp.bridge import write_gate as bridge_write_gate

    try:
        job_id = bridge_client.submit_write(ctx.tenant_id, account_set, payload)
    except BridgeUnavailable:
        logger.warning("[steward.erp_push] no write bridge for %s", account_set)
        return _refused(ctx, endpoint, history, payload, account_set, ERR_BRIDGE_OFFLINE, "offline")
    except BridgeError as e:
        # 形状被拒(BridgeRejected)与其它桥层异常同归一路:都是"没写进去",指路文案一致。
        return _refused(ctx, endpoint, history, payload, account_set, ERR_PUSH_REJECTED, str(e))

    trail.audit(ctx, history, payload, job_id)
    outcome = _await_write(ctx.tenant_id, job_id)
    data = {
        "job_id": job_id,
        "account_set": account_set,
        "doctype": payload.get("doctype"),
        "direction": payload.get("direction"),
        "ref_no": payload.get("ref_no"),
        "total_amount": payload.get("total_amount"),
        "docnum": (outcome["result"] or {}).get("docnum") or "",
    }
    status = outcome["status"]
    result = outcome["result"] or {}
    if status == "done" and result.get("ok") is not False:
        trail.log_push(ctx, endpoint, history, payload, "success", data)
        return ToolResult(ok=True, data=data)
    if status == "pending":
        # 桥还在写:不是失败也不是成功,如实报"在途"并交出 job_id(重推 = 双写)。
        trail.log_push(ctx, endpoint, history, payload, "pending", data, leased=True)
        return ToolResult(ok=False, error_code=ERR_PUSH_PENDING, data=data)
    err = outcome["error"] or _business_error(result)
    bridge_code = str(err.get("code") or "")
    data["reason"] = str(err.get("message") or bridge_code or "")
    if bridge_code == bridge_write_gate.CONFIRMED_UNACKED_CODE:
        # 领了没回执:结果未知,不能落"失败"(她会重推,那就是两张)。这一行的真相是"投出去了,
        # 收不到回音",与上面在途那条同形 —— 同样占住远期租约,否则小助手会把同一份载荷领走
        # 再写一遍,而这份载荷带着确认位、写侧幂等闸是关的。
        trail.log_push(
            ctx, endpoint, history, payload, "pending", data, leased=True, code=bridge_code
        )
        return ToolResult(ok=False, error_code=ERR_PUSH_UNCERTAIN, data=data)
    if bridge_code == BRIDGE_ACCOUNT_BUSY_CODE and not _bridge_wrote(result):
        # 账套被占是唯一「会计自己一步就能解开、且解完重推确定安全」的失败:桥在备份之前就
        # 快拒(write_jobs 的占用预探测),或写到一半拿不到锁并已回滚,两条都一个字节没写。
        # 只在桥自己说没写时才敢这么讲 —— 它说写了就照旧走通用失败,别拿"放心重推"赌一张重单。
        trail.log_push(ctx, endpoint, history, payload, "failed", data, code=bridge_code)
        return ToolResult(ok=False, error_code=ERR_PUSH_ACCOUNT_BUSY, data=data)
    code = ERR_PUSH_EXPIRED if status == "expired" else ERR_PUSH_FAILED
    trail.log_push(ctx, endpoint, history, payload, "failed", data, code=bridge_code)
    return ToolResult(ok=False, error_code=code, data=data)


def _bridge_wrote(result: dict) -> bool:
    """桥是否自报「往账套写了字节」(meta.written)。缺这个键 = 桥没表态,按没写算。

    只有桥知道真相,云端无从判断;这个判据单独拎出来,是因为它决定敢不敢跟会计说「放心重推」。
    """
    meta = result.get("meta")
    return bool(isinstance(meta, dict) and meta.get("written") is True)


def _business_error(result: dict) -> dict:
    """桥自报的业务失败 → 与 job.error 同形的 {code,message}。

    job 落 done 只说明「桥执行完并回了话」:业务成败在结果体的 ok 位上(桥一律 ack
    transport-ok,见 bridge/cloud_jobs 文件头)。拿 done 当成功,会把桥辛苦区分出来的
    每一种诚实失败 —— 同钥匙内容不同、账套被占用、读回校验没过、回滚 —— 一律报成
    「推成功了」,而账套里一个字节都没有。docnum 也拿不到(失败结果体不带这个键),
    于是会计连去 Express 核对哪一张都无从下手。
    """
    return {
        "code": str(result.get("error_code") or "bridge.failed"),
        "message": str(result.get("error") or ""),
    }


def _refused(
    ctx: ToolContext,
    endpoint: dict,
    history: dict,
    payload: dict,
    account_set: str,
    code: str,
    reason: str,
) -> ToolResult:
    """投单没投出去(桥不在线 / 桥拒收):照样落推送日志 + 审计,再翻成人话错误码。

    这两条是最常见的失败,而它们恰恰是排查「会计说他推了、账套里却没有」时唯一的痕迹;
    桥拒收尤其要留 request_body —— 载荷形状被拒说明 mapper 产物有问题,不留就无从查起。
    """
    data = {"account_set": account_set, "reason": reason, "job_id": ""}
    trail.log_push(ctx, endpoint, history, payload, "failed", data, http_status=0)
    trail.audit(ctx, history, payload, "", action=trail.AUDIT_REFUSED, reason=reason)
    return ToolResult(ok=False, error_code=code, data=data)
