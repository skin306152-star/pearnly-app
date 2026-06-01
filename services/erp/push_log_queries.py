# -*- coding: utf-8 -*-
"""ERP 推送日志查询/明细/异常/统计 DAL(REFACTOR-WA-B1 · 2026-05-29 从 erp/push_store 抽出 · 纯搬家 0 逻辑改)

推送日志列表/明细(含 UI 友好化 friendly_for_ui + 外部引用 derive_external_ref)+ 推送异常清单 +
今日统计 + 批量删。组内自洽(只依赖 db + external_ref/business_friendly 叶子)·
push_store 顶部 re-import 当 facade · db.X/store.X/本模块.X 单一对象不变。
"""

import re  # noqa: F401
import logging
from typing import Optional, Dict, Any, List  # noqa: F401

from services.erp.external_ref import derive_external_ref  # noqa: F401
from services.erp.mrerp_business_friendly import friendly_for_ui  # noqa: F401

logger = logging.getLogger(__name__)


# 身份证→订车单(adapter=mrerp_dms)推送/识别错误码的 4 语友好文案(zh/th/en/ja)。
# 与 mrerp_business_friendly 的「发票推送」catalog 分开:这些码只在身份证订车流程产生,
# friendly_for_ui 不覆盖 → 不补就在日志/详情里裸露 ERR_*(Zihao 2026-06-01 指出问题)。
_DMS_PUSH_FRIENDLY: Dict[str, Dict[str, str]] = {
    "ERR_ID_CARD_REQUIRED_FIELDS": {
        "zh": "身份证关键字段未识别完整(身份证号或姓名)· 已暂停建单 · 请用清晰的正面照重新识别",
        "en": "Key ID-card fields (ID number or name) were not fully recognized; booking was paused. Please rescan a clear front image.",
        "th": "อ่านข้อมูลบัตรประชาชนหลัก (เลขบัตร/ชื่อ) ไม่ครบ จึงหยุดสร้างใบจอง กรุณาสแกนภาพด้านหน้าที่ชัดเจนอีกครั้ง",
        "ja": "身分証の主要項目(番号・氏名)を完全に読み取れず、予約作成を停止しました。鮮明な表面の画像で再読み取りしてください。",
    },
    "ERR_DMS_CUSTOMER_CREATE": {
        "zh": "在 DMS 建客户失败 · 请检查身份证上的地址信息后重试",
        "en": "Failed to create the customer in DMS. Please check the address on the ID card and retry.",
        "th": "สร้างลูกค้าใน DMS ไม่สำเร็จ กรุณาตรวจสอบที่อยู่บนบัตรประชาชนแล้วลองใหม่",
        "ja": "DMS での顧客作成に失敗しました。身分証の住所をご確認のうえ再試行してください。",
    },
    "ERR_DMS_IMPORT_REPORT": {
        "zh": "订车单导入 DMS 时被退回(数据校验未过)· 请核对身份证信息后重试",
        "en": "DMS rejected the booking import (data validation failed). Please verify the ID-card data and retry.",
        "th": "DMS ปฏิเสธการนำเข้าใบจอง (ตรวจสอบข้อมูลไม่ผ่าน) กรุณาตรวจสอบข้อมูลบัตรแล้วลองใหม่",
        "ja": "DMS が予約の取り込みを拒否しました(データ検証エラー)。身分証データをご確認のうえ再試行してください。",
    },
    "ERR_DMS_IMPORT": {
        "zh": "订车单导入 DMS 失败 · 请稍后重试",
        "en": "Failed to import the booking into DMS. Please retry shortly.",
        "th": "นำเข้าใบจองรถไปยัง DMS ไม่สำเร็จ กรุณาลองใหม่ภายหลัง",
        "ja": "予約データの DMS への取り込みに失敗しました。しばらくしてから再試行してください。",
    },
    "ERR_DMS_BOOKING_PATCH": {
        "zh": "订车单已建但补充资料失败 · 请到 DMS 后台核对该单",
        "en": "The booking was created but updating its details failed. Please verify it in the DMS console.",
        "th": "สร้างใบจองแล้วแต่บันทึกรายละเอียดเพิ่มเติมไม่สำเร็จ กรุณาตรวจสอบใบจองในระบบ DMS",
        "ja": "予約は作成されましたが詳細の更新に失敗しました。DMS 管理画面でご確認ください。",
    },
    "ERR_DMS_TEMPLATE": {
        "zh": "获取 DMS 订车单模板失败 · 请稍后重试",
        "en": "Failed to fetch the DMS booking template. Please retry shortly.",
        "th": "ดึงแม่แบบใบจองของ DMS ไม่สำเร็จ กรุณาลองใหม่ภายหลัง",
        "ja": "DMS の予約テンプレート取得に失敗しました。しばらくしてから再試行してください。",
    },
    "ERR_DMS_AUTH": {
        "zh": "DMS 登录失败 · 请到连接向导检查账号和密码",
        "en": "DMS login failed. Please check the username and password in the connection wizard.",
        "th": "เข้าสู่ระบบ DMS ไม่สำเร็จ กรุณาตรวจสอบชื่อผู้ใช้และรหัสผ่านในตัวช่วยเชื่อมต่อ",
        "ja": "DMS へのログインに失敗しました。連携ウィザードでユーザー名とパスワードをご確認ください。",
    },
    "ERR_DMS_NOT_INVOICE_ENDPOINT": {
        "zh": "该连接是身份证订车专用 · 不能用于推送发票",
        "en": "This connection is for ID-card vehicle booking only and cannot push invoices.",
        "th": "การเชื่อมต่อนี้ใช้สำหรับการจองรถด้วยบัตรประชาชนเท่านั้น ไม่สามารถส่งใบกำกับได้",
        "ja": "この連携は身分証による車両予約専用で、請求書の送信には使用できません。",
    },
    "ERR_DMS_TECHNICAL": {
        "zh": "连接 DMS 超时或网络异常 · 请稍后重试",
        "en": "DMS connection timed out or a network error occurred. Please retry shortly.",
        "th": "การเชื่อมต่อ DMS หมดเวลาหรือเครือข่ายขัดข้อง กรุณาลองใหม่ภายหลัง",
        "ja": "DMS への接続がタイムアウトまたはネットワーク異常です。しばらくしてから再試行してください。",
    },
    "ERR_DMS_UNEXPECTED": {
        "zh": "推送 DMS 时发生未知错误 · 请稍后重试或联系客服",
        "en": "An unexpected error occurred while pushing to DMS. Please retry or contact support.",
        "th": "เกิดข้อผิดพลาดที่ไม่คาดคิดขณะส่งไป DMS กรุณาลองใหม่หรือติดต่อฝ่ายสนับสนุน",
        "ja": "DMS への送信中に予期しないエラーが発生しました。再試行するかサポートにお問い合わせください。",
    },
}


def dms_push_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """命中身份证订车错误码 → 返回 {zh,th,en,ja} dict;否则 None。
    按码长度降序匹配(长码先于其前缀短码,如 ERR_DMS_IMPORT_REPORT 先于 ERR_DMS_IMPORT)
    防子串误命中 · 新增码进 _DMS_PUSH_FRIENDLY 即自动生效,无需再维护一份顺序列表。"""
    if not error_msg:
        return None
    for code in sorted(_DMS_PUSH_FRIENDLY, key=len, reverse=True):
        if code in error_msg:
            return _DMS_PUSH_FRIENDLY[code]
    return None


def friendly_any(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """发票推送 catalog 优先(friendly_for_ui)· 未命中再退身份证订车映射。
    给 push 日志/详情/异常统一用 · 任一命中即不裸露 ERR_*。"""
    return friendly_for_ui(error_msg) or dms_push_friendly(error_msg)


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


def list_push_logs(
    user_id: str,
    history_id: Optional[str] = None,
    endpoint_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    trigger_filter: Optional[str] = None,
    adapter_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """查询推送日志(P2-B 折叠版),支持按 history/endpoint/status/trigger/adapter 过滤.

    P2-B (Zihao 2026-05-27 · ERP 收尾) · 折叠到每对 (history×endpoint) 最新一条,
    清「混合手动+自动推」遗留重复行,与 list_push_exceptions 同口径(单一状态源·铁律 #12).
    NULL-safe:history_id/endpoint_id 任一为空(Xero/已删 endpoint 孤儿 log)→ 按行自身
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
                ref = derive_external_ref(
                    it.get("endpoint_adapter"), it.pop("response_body", None), it.get("status")
                )
                it.update(ref)
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
    return "other"


def list_push_exceptions(
    user_id: str,
    q: Optional[str] = None,
    category: Optional[str] = None,
    adapter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """ERP 推送异常队列(派生自 erp_push_logs · 铁律 #12 单一状态源,不另立异常表)。

    取每个 (history, endpoint) **最近一条** log · 仅保留 status='failed'(已被后续
    success/skipped_dup 解决的自动排除)。每条附:
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
                    l.retry_count, l.max_retries, l.next_retry_at,
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

    # 1) 仅留最近一条仍 failed 的(已解决的自动排除)+ 附 state/category/code
    base: List[Dict[str, Any]] = []
    for r in rows:
        if (r.get("status") or "") != "failed":
            continue
        # DMS 推送可视化闭环(Zihao 2026-06-01 · 修正:异常栏与推送日志【同理】· 保留身份证订车失败行,
        # 标 push_type 供前端按 DMS 字段(订车单号/客户)渲染 + ERP 下拉筛选 · 不再用发票字段框、不再误删)。
        # id_card_tail 已在 SELECT 用 request_body->>'people_id_tail' 取出(只取末4)。
        r["push_type"] = _classify_push_type(r)
        r["state"] = batch_view.classify_push_log(r)
        r["category"] = classify_push_exception(r.get("error_msg"))
        m = _re.search(r"ERR_[A-Z0-9_]+", r.get("error_msg") or "")
        r["error_code"] = m.group(0) if m else ""
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

    # 3) category 计数(搜索后 · 过滤前 → chip 显当前搜索范围内各子类数)
    categories: Dict[str, int] = {}
    for r in base:
        c = r.get("category") or "other"
        categories[c] = categories.get(c, 0) + 1

    # 4) category 过滤 + 按时间倒序 + 分页
    if category:
        base = [r for r in base if (r.get("category") or "other") == category]
    base.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    total = len(base)
    off = max(0, int(offset or 0))
    lim = max(1, min(int(limit or 50), 200))
    page = base[off : off + lim]
    return {"items": page, "total": total, "categories": categories}


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


import db  # noqa: E402
