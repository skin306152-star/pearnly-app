# -*- coding: utf-8 -*-
"""ERP 推送日志查询/明细/异常/统计 DAL(REFACTOR-WA-B1 · 2026-05-29 从 erp/push_store 抽出 · 纯搬家 0 逻辑改)

推送日志列表/明细(含 UI 友好化 friendly_for_ui + 外部引用 derive_external_ref · 失败行附
异常子类 + 自助修复槽)+ 今日统计 + 批量删。组内自洽(只依赖 db + external_ref/business_friendly 叶子)·
push_store 顶部 re-import 当 facade · db.X/store.X/本模块.X 单一对象不变。
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List  # noqa: F401

from services.erp.external_ref import _coerce_body, derive_external_ref  # noqa: F401
from services.erp.push_log_friendly import dms_push_friendly, friendly_any  # noqa: F401

# 异常分类 + 自助修复派生抽到 push_exception_classify(纯函数)· 此处 re-import 保 facade
# (store.X is q.X 单一对象 · test_push_log_queries_contract 钉死)。
from services.erp.push_exception_classify import (  # noqa: F401
    classify_push_exception,
    derive_account_fix,
    derive_bind_fix,
)

logger = logging.getLogger(__name__)


def _classify_push_type(row: Dict[str, Any]) -> str:
    """从一行 push log 判 push_type:身份证订车(id_card)还是发票(invoice)。
    单一判定源 · list/detail/exceptions 三处共用 · 改判定规则只此一处。"""
    is_id_card = (row.get("trigger") or "") == "id_card" or (
        row.get("endpoint_adapter") or ""
    ).lower() == "mrerp_dms"
    return "id_card" if is_id_card else "invoice"


def delete_push_logs(user_id: str, log_ids: List[str]) -> int:
    """Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除推送日志.
    严格 user_id scope · 不许跨账号删除 · 返回真删除的行数."""
    if not log_ids:
        return 0
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_push_logs WHERE user_id = %s AND id = ANY(%s::uuid[])",
                (user_id, list(log_ids)),
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.error(f"delete_push_logs failed: {e}")
        return 0


def _derive_push_accounts(resp_raw: Any) -> Optional[List[Dict[str, str]]]:
    """从 response_body 取 Express 队列响应里的分录科目 → [{acc,side,desc}](列表卡科目列用)。

    response_body 可能是 jsonb dict 或 JSON 字符串;无 accounts → None(只在有时带,保列表轻量)。
    """
    if not resp_raw:
        return None
    try:
        body = resp_raw if isinstance(resp_raw, dict) else json.loads(resp_raw)
    except (ValueError, TypeError):
        return None
    accs = body.get("accounts") if isinstance(body, dict) else None
    if not isinstance(accs, list) or not accs:
        return None
    out: List[Dict[str, str]] = []
    for a in accs:
        if not isinstance(a, dict):
            continue
        code = str(a.get("acc") or "").strip()
        if code:
            out.append(
                {"acc": code, "side": str(a.get("side") or ""), "desc": str(a.get("desc") or "")}
            )
    return out or None


def _derive_v3_meta(body: Any) -> Dict[str, Any]:
    """从 response_body.meta 派生 V3 细粒度态标量进列表项(轻量·只取前端展示要的几个)。

    push_stage = waiting_lock/rolled_back/needs_review/... (status 列的细化·见 common.STAGE_*);
    rolled_back = 写了一半已恢复备份;fallback_count = 明细从非库存回落直接科目的行数。
    """
    out: Dict[str, Any] = {}
    meta = body.get("meta") if isinstance(body, dict) else None
    if isinstance(meta, dict):
        stage = str(meta.get("stage") or "").strip()
        if stage:
            out["push_stage"] = stage
        if meta.get("rolled_back"):
            out["rolled_back"] = True
    if isinstance(body, dict) and body.get("fallback_count"):
        out["fallback_count"] = body.get("fallback_count")
    return out


def list_push_logs(
    user_id: str,
    history_id: Optional[str] = None,
    endpoint_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    trigger_filter: Optional[str] = None,
    adapter_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    keyword: Optional[str] = None,
    push_type: Optional[str] = None,
) -> Dict[str, Any]:
    """查询推送日志(P2-B 折叠版),支持按 history/endpoint/status/trigger/adapter 过滤.

    P2-B (Zihao 2026-05-27 · ERP 收尾) · 折叠到每对 (history×endpoint) 最新一条,
    清「混合手动+自动推」遗留重复行,与 list_push_exceptions 同口径(单一状态源·铁律 #12).
    NULL-safe:history_id/endpoint_id 任一为空(已删 endpoint 孤儿 log)→ 按行自身
    id 独立分区,永不被误合并. 状态/trigger/adapter 过滤作用于折叠后的当前态.

    批 3 改动 6 (Zihao 2026-05-19 · v118.34.34) · adapter_filter 按 erp_endpoints.adapter
    过滤. 已删 endpoint join 不到 row (endpoint_adapter is NULL),自动不命中 adapter filter.
    """
    try:
        with db.get_cursor() as cur:
            # 折叠 CTE:每对 (history×endpoint) 取 created_at 最新一条(id 作 tie-break).
            # NULL-safe:任一 id 为空 → 'solo:'||id 独立分区 → _rn 恒为 1 → 全保留不合并.
            ranked_cte = """
                WITH ranked AS (
                    SELECT l.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY CASE
                                WHEN l.history_id IS NOT NULL AND l.endpoint_id IS NOT NULL
                                THEN l.history_id::text || '|' || l.endpoint_id::text
                                ELSE 'solo:' || l.id::text
                            END
                            ORDER BY l.created_at DESC, l.id DESC
                        ) AS _rn
                    FROM erp_push_logs l
                    WHERE l.user_id = %s
                )
            """
            # 过滤作用于「折叠后的当前态」(l._rn = 1) · 字段全 prefix 防 ambiguous.
            outer = ["l._rn = 1"]
            params: list = [user_id]
            if history_id:
                outer.append("l.history_id = %s")
                params.append(history_id)
            if endpoint_id:
                outer.append("l.endpoint_id = %s")
                params.append(endpoint_id)
            if status_filter == "success":
                outer.append("l.status = 'success'")
            elif status_filter == "retrying":
                # v118.25.1 · 重试中:failed + 仍在重试队列里(next_retry_at 未来/未清)
                outer.append("l.status = 'failed' AND l.next_retry_at IS NOT NULL")
            elif status_filter == "failed":
                # v118.25.1 · 失败终态:failed + 不在重试队列(已耗尽 / 端点删 / 手动停)
                outer.append("l.status = 'failed' AND l.next_retry_at IS NULL")
            if trigger_filter in ("manual", "auto"):
                outer.append("l.trigger = %s")
                params.append(trigger_filter)
            # 批 3 改动 6 · adapter filter · 走 JOIN 后 e.adapter · NULL-safe LOWER 滤孤儿.
            if adapter_filter:
                outer.append("LOWER(e.adapter) = LOWER(%s)")
                params.append(adapter_filter)
            # 业务类型(草稿「全部业务」下拉)· 身份证订车 = DMS endpoint 或 id_card trigger
            if push_type == "id_card":
                outer.append("(LOWER(e.adapter) = 'mrerp_dms' OR l.trigger = 'id_card')")
            elif push_type == "invoice":
                outer.append(
                    "(COALESCE(LOWER(e.adapter),'') <> 'mrerp_dms' AND COALESCE(l.trigger,'') <> 'id_card')"
                )
            # 关键字搜索(草稿「搜索单据号、客户或任务」)· 单据号 / 卖方
            if keyword:
                outer.append("(l.invoice_no ILIKE %s OR l.seller_name ILIKE %s)")
                _kw = f"%{keyword.strip()}%"
                params.extend([_kw, _kw])
            outer_sql = " AND ".join(outer)

            # COUNT(折叠后) · JOIN erp_endpoints 供 adapter filter(无 filter 时无害).
            cur.execute(
                ranked_cte + f"""
                    SELECT COUNT(*) AS n FROM ranked l
                    LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                    WHERE {outer_sql}
                """,
                tuple(params),
            )
            total = cur.fetchone()["n"]
            cur.execute(
                ranked_cte + f"""
                SELECT l.id, l.endpoint_id, l.history_id, l.invoice_no,
                       l.seller_name, l.total_amount, l.status, l.http_status,
                       l.error_msg, l.attempt, l.elapsed_ms, l.trigger,
                       l.created_at, l.retry_count, l.max_retries,
                       l.next_retry_at, l.response_body, l.request_body,
                       l.request_body->>'people_id_tail' AS id_card_tail,
                       h.client_id AS history_client_id,
                       c.name AS client_name,
                       COALESCE((
                           SELECT pg->'fields'->>'buyer_name'
                           FROM jsonb_array_elements(
                               CASE WHEN jsonb_typeof(h.pages)='array'
                                    THEN h.pages ELSE '[]'::jsonb END
                           ) pg
                           WHERE COALESCE(pg->'fields'->>'buyer_name','') <> ''
                           LIMIT 1
                       ), '') AS ocr_buyer_name,
                       e.name AS endpoint_name,
                       e.adapter AS endpoint_adapter,
                       w.name AS workspace_name
                FROM ranked l
                LEFT JOIN ocr_history h ON h.id = l.history_id
                LEFT JOIN clients c ON c.id = h.client_id
                LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                LEFT JOIN workspace_clients w ON w.id = h.workspace_client_id
                WHERE {outer_sql}
                ORDER BY l.created_at DESC
                LIMIT %s OFFSET %s
            """,
                tuple(params) + (limit, offset),
            )
            items = [dict(r) for r in cur.fetchall()]
            # 临时任务 (Zihao 2026-05-26) · 在日志 API 层派生通用 ERP 单号字段
            # (external_doc_no/external_doc_id/external_url + adapter 提示码)。
            # 不动状态机 · 不新增状态源 · 仅从已有 response_body+adapter 读出。
            # 派生后丢掉原始 response_body · 列表 payload 保持轻量(详情接口才回完整体)。
            for it in items:
                # response_body 只解析一次(_coerce_body),派生器都收已解析 dict,避免逐行双重 json.loads。
                body = _coerce_body(it.pop("response_body", None))
                ref = derive_external_ref(it.get("endpoint_adapter"), body, it.get("status"))
                it.update(ref)
                # Express 队列响应带的分录科目(at-a-glance·列表科目列)· 无则不带,保持轻量。
                it["push_accounts"] = _derive_push_accounts(body)
                it.update(_derive_v3_meta(body))  # V3 细粒度态(push_stage/rolled_back/fallback)
                # DMS 推送可视化闭环(Zihao 2026-06-01)· 身份证→订车单 ≠ 发票推送:
                # 标 push_type 让前端按 DMS 字段(订车单号/客户/身份证)渲染该行,
                # 不再用发票字段框;并附 4 语友好错误(身份证订车码 friendly_for_ui 不覆盖)。
                # id_card_tail 已在 SELECT 用 request_body->>'people_id_tail' 取出(只取末4·不拉整个体)。
                it["push_type"] = _classify_push_type(it)
                it["error_friendly"] = friendly_any(it.get("error_msg"))
                # 失败/留人工行附异常子类 + 自助修复槽(待补科目/绑主体)· 让推送日志失败卡
                # 直接展示修复入口(原「推送异常」tab 已并入此处 · 同一状态源不另查)。
                if (it.get("status") or "") in ("failed", "manual"):
                    it["category"] = classify_push_exception(it.get("error_msg"))
                    m = re.search(r"ERR_[A-Z0-9_]+", it.get("error_msg") or "")
                    it["error_code"] = m.group(0) if m else ""
                    if it["category"] == "account_missing":
                        it["account_fix"] = derive_account_fix(
                            it.get("error_msg"), it.get("request_body")
                        )
                    elif it["category"] == "direction_unknown":
                        it["bind_fix"] = derive_bind_fix(it.get("error_msg"))
                # request_body 仅用于派生 direction,用完丢弃,列表 payload 保持轻量。
                it.pop("request_body", None)
            return {"items": items, "total": total}
    except Exception as e:
        logger.error(f"list_push_logs failed: {e}")
        return {"items": [], "total": 0}


def get_push_log_detail(user_id: str, log_id: str) -> Optional[Dict[str, Any]]:
    """单条推送日志完整详情(含 request_body / response_body)

    临时任务 (Zihao 2026-05-26) · JOIN endpoints 拿 adapter + name,JOIN clients
    拿 Pearnly 客户/买方名,供凭证弹窗显示;并派生通用 ERP 单号字段
    (external_doc_no/external_doc_id/external_url + adapter 提示码)。
    response_body 在详情接口里保留(弹窗"技术详情"折叠区要看原始体)。
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT l.id, l.endpoint_id, l.history_id, l.invoice_no, l.seller_name,
                       l.total_amount, l.status, l.http_status,
                       l.request_body, l.response_body, l.error_msg,
                       l.attempt, l.elapsed_ms, l.trigger, l.created_at,
                       l.retry_count, l.max_retries, l.next_retry_at,
                       h.client_id AS history_client_id,
                       c.name AS client_name,
                       COALESCE((
                           SELECT pg->'fields'->>'buyer_name'
                           FROM jsonb_array_elements(
                               CASE WHEN jsonb_typeof(h.pages)='array'
                                    THEN h.pages ELSE '[]'::jsonb END
                           ) pg
                           WHERE COALESCE(pg->'fields'->>'buyer_name','') <> ''
                           LIMIT 1
                       ), '') AS ocr_buyer_name,
                       e.name AS endpoint_name,
                       e.adapter AS endpoint_adapter
                FROM erp_push_logs l
                LEFT JOIN ocr_history h ON h.id = l.history_id
                LEFT JOIN clients c ON c.id = h.client_id
                LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                WHERE l.id = %s AND l.user_id = %s
            """,
                (log_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            detail = dict(row)
            ref = derive_external_ref(
                detail.get("endpoint_adapter"), detail.get("response_body"), detail.get("status")
            )
            detail.update(ref)
            # P2-C (B7) · 附友好原因 4 语 dict(命中 catalog 才有 · 否则 None →
            # 前端回退 humanizeError)· 详情抽屉「失败原因」优先显本语言,不裸透泰文。
            detail["error_friendly"] = friendly_any(detail.get("error_msg"))
            detail["push_type"] = _classify_push_type(detail)
            return detail
    except Exception as e:
        logger.error(f"get_push_log_detail failed: {e}")
        return None


def get_push_stats_today(user_id: str) -> Dict[str, Any]:
    """今日推送统计(总数 · 成功 · 失败)"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status='success') AS success,
                    COUNT(*) FILTER (WHERE status='failed') AS failed,
                    COUNT(*) FILTER (WHERE trigger='auto') AS auto_cnt
                FROM erp_push_logs
                WHERE user_id = %s
                  AND created_at >= CURRENT_DATE
            """,
                (user_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0}
    except Exception as e:
        logger.error(f"get_push_stats_today failed: {e}")
        return {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0}


from core import db  # noqa: E402
