# -*- coding: utf-8 -*-
"""ERP 推送失败重试调度(指数退避)+ 错误分类器(REFACTOR-WA-B2 · 2026-05-29 从 erp/push_store 抽出 · 纯搬家 0 逻辑改)

指数退避序列(60s/5min/30min · 共 3 次)+ 用户数据错判定(is_user_data_error · 不入 retry)+
「已推送过」中性态判定(is_already_pushed_error → skipped_dup)+ 单一权威 status 分类(classify_push_status)+
重试队列读写(schedule/clear/list_due/increment/update_log_status_after_retry)。组内自洽(只依赖 db)·
push_store 顶部 re-import 当 facade · db.X/store.X/本模块.X 单一对象不变。
"""

import logging
from typing import Optional, Dict, Any, List  # noqa: F401

logger = logging.getLogger(__name__)

# 指数退避序列(秒):60s · 5min · 30min · 共 3 次
_ERP_RETRY_DELAYS_SEC = [60, 300, 1800]
ERP_MAX_RETRIES = 3

# 批 1 改动 3 (Zihao 2026-05-19 拍板 · v118.34.33) · 用户数据错不 retry.
# 这些错 retry 没意义 · 用户数据没改之前再推还是失败 · 污染重试队列 +
# 用户看到一堆 "已重试 1/3 · 2 分钟后再试" 噪音.
# 区分:
#   - 用户数据错 → 不入 retry · status 留 'failed' · 用户看到时主动处理
#   - 技术错 (网络/timeout/session) → retry 3 次 (60s/5min/30min)
USER_DATA_ERROR_CODES = {
    "ERR_NO_CLIENT",
    "ERR_NO_CUSTOMER_MAPPING",
    "ERR_NO_INVOICE_NO",
    "ERR_NO_INVOICE_DATE",
    "ERR_NO_TOTAL_AMOUNT",
    "ERR_NEGATIVE_AMOUNT",
    "ERR_TAX_ID_INVALID",
    "ERR_DATE_FUTURE",
    "ERR_INVOICE_NO_TOO_LONG",
    "ERR_BILL_NO_TOO_LONG",
    "ERR_CUSTOMER_CODE_TOO_LONG",
    "ERR_NO_SEED_CUSTOMER",
    "ERR_NO_SEED_PRODUCT",
    # MR.ERP duplicate · 重推还是同一个 bill_no · 没意义
    "ERR_DUPLICATE_INVOICE",
    # Fail-safe 名字复核不匹配(Zihao 2026-05-26 拍板 · P1)· 用户得先改映射 ·
    # 重推同样不匹配 · 不入 retry。注:ERR_*_VERIFY_UNAVAILABLE(网络/超时无法确认)
    # 故意不在此 set · 属技术错 · 走 retry 队列(但永远不显示 success)。
    "ERR_CUSTOMER_NAME_MISMATCH",
    "ERR_PRODUCT_NAME_MISMATCH",
}

# Thai raw error patterns that map to user-data errors (报错可能直接是 raw 泰文)
USER_DATA_ERROR_THAI_PATTERNS = (
    "เลขที่ดังกล่าวมีอยู่ในระบบแล้ว",  # duplicate
    "เลขที่เอกสารซ้ำ",  # duplicate
    "ไม่พบข้อมูลรหัสลูกค้า",  # customer mapping missing
    "ลูกค้าไม่ระบุ",  # client missing
    "เลขที่ต้องไม่เกิน",  # length limit
)


# P2-D(Zihao 2026-05-27 拍板 · B8)· MR.ERP 返「发票号已存在/已推过」不是失败 ·
# 是「已推送过」中性态(skipped_dup)· 不红叉、不计失败、不入重试。
# 两种 MR.ERP 文案 + 我方 ERR_DUPLICATE_INVOICE 码都算。
_ALREADY_PUSHED_THAI_PATTERNS = (
    "เลขที่ดังกล่าวมีอยู่ในระบบแล้ว",  # 该号已存在系统
    "เลขที่เอกสารซ้ำ",  # 单据号重复
)


def is_already_pushed_error(error_msg: Optional[str]) -> bool:
    """这条「失败」其实是「发票号已存在/之前已推过」吗?是 → 应记为 skipped_dup 中性态。"""
    if not error_msg:
        return False
    s = str(error_msg)
    if "ERR_DUPLICATE_INVOICE" in s:
        return True
    for pat in _ALREADY_PUSHED_THAI_PATTERNS:
        if pat in s:
            return True
    return False


def classify_push_status(success: bool, error_msg: Optional[str]) -> str:
    """推送结果 → 单一权威 status(铁律 #12)。
    success → 'success';「发票号已存在」→ 'skipped_dup'(中性·已推送过);其余 → 'failed'。

    Express 出站拉取:它的"推送"= 写待领取队列,不是即时成败。enqueue_express 在
    error_msg 里带哨兵让这一行落成队列态(单一状态源 · 不另立队列表):
      EXPRESS_QUEUED   → 'pending'(进队列等本地 Agent lease)
      EXPRESS_MANUAL:* → 'manual' (低置信/判脏/账套拒 · 留人工)
    其它 adapter 永不产生这两个哨兵,行为零变化。
    """
    if not success and error_msg:
        if "EXPRESS_QUEUED" in error_msg:
            return "pending"
        if "EXPRESS_MANUAL" in error_msg:
            return "manual"
    if success:
        return "success"
    if is_already_pushed_error(error_msg):
        return "skipped_dup"
    return "failed"


def is_user_data_error(error_msg: Optional[str]) -> bool:
    """判断这条错误是不是"用户数据错"(不应该 retry).
    匹配 ERR_* code 前缀 OR 已知泰文 raw 模式.
    """
    if not error_msg:
        return False
    s = str(error_msg)
    # 任一 ERR_* code 命中
    for code in USER_DATA_ERROR_CODES:
        if code in s:
            return True
    # 任一已知泰文模式命中
    for pat in USER_DATA_ERROR_THAI_PATTERNS:
        if pat in s:
            return True
    return False


def get_erp_retry_delay_sec(retry_count: int) -> Optional[int]:
    """根据已重试次数返回下次重试延迟(秒)· 超过最大次数返回 None"""
    if retry_count < 0 or retry_count >= ERP_MAX_RETRIES:
        return None
    if retry_count >= len(_ERP_RETRY_DELAYS_SEC):
        return _ERP_RETRY_DELAYS_SEC[-1]
    return _ERP_RETRY_DELAYS_SEC[retry_count]


def schedule_log_retry(log_id: str, delay_sec: int) -> bool:
    """把一条失败日志加入重试队列 · next_retry_at = NOW + delay"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_push_logs
                SET next_retry_at = NOW() + (%s * INTERVAL '1 second')
                WHERE id = %s AND status = 'failed'
            """,
                (int(delay_sec), log_id),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"schedule_log_retry failed: {e}")
        return False


def clear_retry_schedule(log_id: str):
    """重试成功 / 达到上限后调用 · 清空 next_retry_at(从队列里摘出来)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_push_logs
                SET next_retry_at = NULL
                WHERE id = %s
            """,
                (log_id,),
            )
    except Exception as e:
        logger.error(f"clear_retry_schedule failed: {e}")


def list_logs_due_for_retry(limit: int = 20) -> List[Dict[str, Any]]:
    """找到当下到期需要重试的失败日志 · 按到期时间正序"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT l.id, l.user_id, l.endpoint_id, l.history_id,
                       l.invoice_no, l.seller_name, l.total_amount,
                       l.retry_count, l.max_retries, l.next_retry_at
                FROM erp_push_logs l
                WHERE l.status = 'failed'
                  AND l.next_retry_at IS NOT NULL
                  AND l.next_retry_at <= NOW()
                  AND l.retry_count < l.max_retries
                ORDER BY l.next_retry_at ASC
                LIMIT %s
            """,
                (int(limit),),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_logs_due_for_retry failed: {e}")
        return []


def increment_retry_count(log_id: str) -> int:
    """重试一次后自增 retry_count · 返回新值"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_push_logs
                SET retry_count = retry_count + 1
                WHERE id = %s
                RETURNING retry_count
            """,
                (log_id,),
            )
            row = cur.fetchone()
            return int(row["retry_count"]) if row else 0
    except Exception as e:
        logger.error(f"increment_retry_count failed: {e}")
        return 0


def update_log_status_after_retry(
    log_id: str,
    success: bool,
    http_status: Optional[int],
    response_body: Optional[str],
    error_msg: Optional[str],
    elapsed_ms: int,
    request_body: Optional[Any] = None,
    final_status: Optional[str] = None,
):
    """更新原 log 的 status / http_status / response(不写新行)。
    重试完成调用;也用于把识别后立刻写的「pending(推送中)」行落定成
    success/failed(2026-05-26)。request_body 仅在传入时覆盖(retry 不传 → 保留原值)。
    P2-D(2026-05-27):final_status 传入时直接用它(支持 'skipped_dup' 中性态);
    不传则沿用 success→'success'/'failed' 老映射(向后兼容所有现有调用)。"""
    import json as _json

    status = final_status if final_status else ("success" if success else "failed")
    try:
        rb = None
        if request_body is not None:
            rb = (
                request_body
                if isinstance(request_body, str)
                else _json.dumps(request_body, ensure_ascii=False)
            )
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_push_logs
                SET status = %s,
                    http_status = %s,
                    response_body = %s,
                    error_msg = %s,
                    elapsed_ms = %s,
                    request_body = COALESCE(%s::jsonb, request_body)
                WHERE id = %s
            """,
                (
                    status,
                    http_status,
                    response_body,
                    error_msg,
                    int(elapsed_ms),
                    rb,
                    log_id,
                ),
            )
    except Exception as e:
        logger.error(f"update_log_status_after_retry failed: {e}")


from core import db  # noqa: E402
