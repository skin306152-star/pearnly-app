# -*- coding: utf-8 -*-
"""ERP 推送日志查询/明细/异常/统计 DAL(REFACTOR-WA-B1 · 2026-05-29 从 erp/push_store 抽出 · 纯搬家 0 逻辑改)

推送日志列表/明细(含 UI 友好化 friendly_for_ui + 外部引用 derive_external_ref)+ 推送异常清单 +
今日统计 + 批量删。组内自洽(只依赖 db + external_ref/business_friendly 叶子)·
push_store 顶部 re-import 当 facade · db.X/store.X/本模块.X 单一对象不变。
"""

import json
import re  # noqa: F401
import logging
from typing import Optional, Dict, Any, List  # noqa: F401

from services.erp.external_ref import _coerce_body, derive_external_ref  # noqa: F401
from services.erp.push_log_friendly import dms_push_friendly, friendly_any  # noqa: F401

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
                       l.next_retry_at, l.response_body,
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
                # DMS 推送可视化闭环(Zihao 2026-06-01)· 身份证→订车单 ≠ 发票推送:
                # 标 push_type 让前端按 DMS 字段(订车单号/客户/身份证)渲染该行,
                # 不再用发票字段框;并附 4 语友好错误(身份证订车码 friendly_for_ui 不覆盖)。
                # id_card_tail 已在 SELECT 用 request_body->>'people_id_tail' 取出(只取末4·不拉整个体)。
                it["push_type"] = _classify_push_type(it)
                it["error_friendly"] = friendly_any(it.get("error_msg"))
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


def classify_push_exception(error_msg: Optional[str]) -> str:
    """把 ERP 推送失败错误码归到异常子类(前端 chip 用 · 通用 · 不写死 MR.ERP)。"""
    msg = error_msg or ""
    if "ERR_CUSTOMER_NAME_MISMATCH" in msg or "ERR_NO_CUSTOMER_MAPPING" in msg:
        return "customer_mismatch"
    if "ERR_PRODUCT_NAME_MISMATCH" in msg:
        return "product_mismatch"
    if "ERR_NO_CLIENT" in msg:
        return "no_client"
    if "VERIFY_UNAVAILABLE" in msg:
        return "verify_unavailable"
    # Express 留人工(EXPRESS_MANUAL:<reason>)· 按可补救路径分桶。
    # 账套配错(小助手连到不可写账套)先于科目判:account_set_not_allowed/no_account_set。
    if "account_set" in msg:
        return "account_set"
    # 缺 收入/应收/销项税/采购/应付/进项税 科目,或科目不在该账套科目表 → 待补科目卡可救。
    if "_account" in msg or "account_not_in_chart" in msg:
        return "account_missing"
    # 方向判不出:主体没绑 / 税号不齐 / 该方向未开。
    if "direction_unknown" in msg or "direction_not_enabled" in msg:
        return "direction_unknown"
    if "low_confidence" in msg:
        return "low_confidence"
    return "other"


# Express 缺科目失败码 → (方向, 该补的 config 槽位)· 待补科目卡据此只问相关槽位。
_SLOT_BY_ACCOUNT_REASON = {
    "no_revenue_account": ("sales", "revenue_acc"),
    "no_ar_account": ("sales", "ar_acc"),
    "no_output_vat_account": ("sales", "vat_output_acc"),
    "no_purchase_account": ("purchase", "fallback_acc"),
    "no_ap_account": ("purchase", "ap_acc"),
    "no_input_vat_account": ("purchase", "vat_input_acc"),
}
_SALES_SLOTS = ["revenue_acc", "ar_acc", "vat_output_acc"]
_PURCHASE_SLOTS = ["fallback_acc", "ap_acc", "vat_input_acc"]


def derive_account_fix(
    error_msg: Optional[str], request_body: Any = None
) -> Optional[Dict[str, Any]]:
    """从 Express 缺科目失败推导「待补科目卡」要问哪些科目槽(direction + slots)。

    单缺一科目(no_*_account)→ 只问那一槽;account_not_in_chart(某分录科目不在科目表)
    → 按 request_body.payload 的 direction 问该方向全部槽,带上越界码 bad_code。非缺科目错 → None。
    """
    msg = error_msg or ""
    for reason, (direction, slot) in _SLOT_BY_ACCOUNT_REASON.items():
        if reason in msg:
            return {"direction": direction, "slots": [slot]}
    if "account_not_in_chart" in msg:
        body = _coerce_body(request_body)
        direction = str((body or {}).get("direction") or "") if isinstance(body, dict) else ""
        m = re.search(r"account_not_in_chart:(\S+)", msg)
        bad = m.group(1) if m else ""
        if direction == "sales":
            slots = list(_SALES_SLOTS)
        elif direction == "purchase":
            slots = list(_PURCHASE_SLOTS)
        else:
            slots = _SALES_SLOTS + _PURCHASE_SLOTS
        return {"direction": direction, "slots": slots, "bad_code": bad}
    return None


def list_push_exceptions(
    user_id: str,
    q: Optional[str] = None,
    category: Optional[str] = None,
    adapter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    push_type: Optional[str] = None,
) -> Dict[str, Any]:
    """ERP 推送异常队列(派生自 erp_push_logs · 铁律 #12 单一状态源,不另立异常表)。

    取每个 (history, endpoint) **最近一条** log · 仅保留 status='failed' 或 'manual'
    (Express 留人工)· 已被后续 success/skipped_dup 解决的自动排除。每条附:
      - state:batch_view 派生展示态(needs_action / retrying / failed)
      - category:错误码子类(customer_mismatch / product_mismatch / no_client /
        verify_unavailable / other)· 前端 chip 用
      - 发票号 / 发票卖方(seller_name)/ 发票买方(ocr_buyer_name)/ 已归属 Pearnly 客户
        / ERP 端点名 / 错误码 / 原始 error_msg(前端转友好文案)

    支持搜索(q:发票号/卖方/买方 模糊)+ category 过滤 + 分页(limit/offset)。
    返回 {items: 当前页, total: 过滤后总数, categories: 各子类计数(供 chip)}。
    通用层只认统一状态 + 错误码,不写 if adapter=='mrerp'。
    """
    from services.erp import batch_view
    import re as _re

    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (l.history_id, l.endpoint_id)
                    l.id, l.history_id, l.endpoint_id, l.invoice_no, l.seller_name,
                    l.total_amount, l.status, l.error_msg, l.trigger, l.created_at,
                    l.retry_count, l.max_retries, l.next_retry_at, l.request_body,
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
                    e.name AS endpoint_name, e.adapter AS endpoint_adapter
                FROM erp_push_logs l
                LEFT JOIN ocr_history h ON h.id = l.history_id
                LEFT JOIN clients c ON c.id = h.client_id
                LEFT JOIN erp_endpoints e ON e.id = l.endpoint_id
                WHERE l.user_id = %s
                ORDER BY l.history_id, l.endpoint_id, l.created_at DESC
                """,
                (str(user_id),),
            )
            rows = [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.error(f"list_push_exceptions failed: {e}")
        return {"items": [], "total": 0, "categories": {}}

    # 1) 仅留最近一条仍需人处理的(failed 或 Express manual=留人工)+ 附 state/category/code。
    #    manual(缺科目/低置信/账套拒)和 failed 一样要用户处理,绝不能从异常页消失(铁律 #3/#12)。
    #    success/skipped_dup/pending 不进异常。
    base: List[Dict[str, Any]] = []
    for r in rows:
        if (r.get("status") or "") not in ("failed", "manual"):
            continue
        # DMS 推送可视化闭环(Zihao 2026-06-01 · 修正:异常栏与推送日志【同理】· 保留身份证订车失败行,
        # 标 push_type 供前端按 DMS 字段(订车单号/客户)渲染 + ERP 下拉筛选 · 不再用发票字段框、不再误删)。
        # id_card_tail 已在 SELECT 用 request_body->>'people_id_tail' 取出(只取末4)。
        r["push_type"] = _classify_push_type(r)
        r["state"] = batch_view.classify_push_log(r)
        r["category"] = classify_push_exception(r.get("error_msg"))
        m = _re.search(r"ERR_[A-Z0-9_]+", r.get("error_msg") or "")
        r["error_code"] = m.group(0) if m else ""
        # 待补科目卡(account_missing)· 算出该问哪些科目槽(direction + slots)。
        # request_body 仅用于推 direction,用完丢弃,列表 payload 保持轻量。
        if r["category"] == "account_missing":
            r["account_fix"] = derive_account_fix(r.get("error_msg"), r.get("request_body"))
        r.pop("request_body", None)
        # P2-C (B7) · 附友好原因 4 语 dict(命中 catalog 才有 · 否则 None)·
        # 异常卡片优先显本语言,不裸透泰文。
        r["error_friendly"] = friendly_any(r.get("error_msg"))
        base.append(r)

    # 2) 搜索(发票号/卖方/买方 · 大小写不敏感)
    qq = (q or "").strip().lower()
    if qq:
        base = [
            r
            for r in base
            if qq in (r.get("invoice_no") or "").lower()
            or qq in (r.get("seller_name") or "").lower()
            or qq in (r.get("ocr_buyer_name") or "").lower()
        ]

    # 2.5) ERP 系统筛选(下拉 · 与推送日志同维度 · Zihao 2026-06-01 异常栏同理)·
    #      在 category 计数前应用 → chip 数反映所选 ERP 范围。
    ad = (adapter or "").strip().lower()
    if ad:
        base = [r for r in base if (r.get("endpoint_adapter") or "").lower() == ad]

    # 3) category 计数 + 身份证订车(push_type)计数(搜索后 · 过滤前 → 统计卡显当前范围各类数)
    categories: Dict[str, int] = {}
    for r in base:
        c = r.get("category") or "other"
        categories[c] = categories.get(c, 0) + 1
    id_card_count = sum(1 for r in base if r.get("push_type") == "id_card")

    # 4) category / push_type 过滤 + 按时间倒序 + 分页
    if category:
        base = [r for r in base if (r.get("category") or "other") == category]
    if push_type:
        base = [r for r in base if r.get("push_type") == push_type]
    base.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    total = len(base)
    off = max(0, int(offset or 0))
    lim = max(1, min(int(limit or 50), 200))
    page = base[off : off + lim]
    return {
        "items": page,
        "total": total,
        "categories": categories,
        "id_card_count": id_card_count,
    }


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
