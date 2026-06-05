# -*- coding: utf-8 -*-
"""异常栏(exceptions + exception_whitelist)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
- exceptions:每条被规则拦截的单据(关联 ocr_history)
- exception_whitelist:用户「忽略此类」后写入 · 同供应商+同规则下次不再拦
设计:同 tenant 共享视图(老板员工看同一份异常池 + 同一份白名单)·
全部按 tenant_id / user_id 隔离(tenant 隔离矩阵)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import json as _json
import logging
from typing import Optional, Dict, Any, List

from core import db

# facade re-export(REFACTOR-WA-B1 · schema/whitelist 实现下沉 · db.X/store.X 单一对象不变)
from services.exceptions.exceptions_schema import ensure_exceptions_tables  # noqa: F401,E402
from services.exceptions.exceptions_whitelist import (  # noqa: F401,E402
    is_exception_whitelisted,
    add_exception_whitelist,
    list_exception_whitelist,
    delete_exception_whitelist,
    count_whitelist_rules,
)

logger = logging.getLogger(__name__)


def insert_exception(
    user_id: str,
    tenant_id: Optional[str],
    history_id: str,
    rule_code: str,
    severity: str = "medium",
    seller_name: Optional[str] = None,
    invoice_no: Optional[str] = None,
    total_amount: Optional[float] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """写入一条异常 · 同 history+rule 已有 pending 时直接 no-op(unique 索引保护)
    v118.20.1.6 · history_id 用 UUID 字符串(原 int 转换全失败)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO exceptions
                    (user_id, tenant_id, history_id, rule_code, severity,
                     seller_name, invoice_no, total_amount, detail_json, status)
                VALUES (%s, %s, %s::uuid, %s, %s, %s, %s, %s, %s::jsonb, 'pending')
                ON CONFLICT (history_id, rule_code) WHERE status = 'pending'
                DO NOTHING
                RETURNING id
            """,
                (
                    str(user_id),
                    tenant_id,
                    str(history_id),
                    rule_code,
                    severity,
                    seller_name,
                    invoice_no,
                    total_amount,
                    _json.dumps(detail or {}, ensure_ascii=False, default=str),
                ),
            )
            row = cur.fetchone()
            if row:
                ex_id = int(row["id"])
                logger.info(
                    f"[exception] +1 ex_id={ex_id} rule={rule_code} sev={severity} hid={history_id} seller={seller_name!r}"
                )
                return ex_id
            else:
                # ON CONFLICT 触发 · 同 history+rule 已存在 pending · 静默忽略
                return None
    except Exception as e:
        logger.warning(f"[exception] insert FAIL (rule={rule_code}, hid={history_id}): {e}")
        return None


def list_exceptions(
    user_id: str,
    tenant_id: Optional[str] = None,
    status: str = "pending",
    rule_code: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    client_id: Optional[int] = None,
    restrict_client_ids: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """列异常 · 同 tenant 共享视图 · 默认只看 pending
    v118.28.1 · restrict_client_ids = 员工只看分到的客户;None = 不限制
    """
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                where = ["e.tenant_id = %s"]
                params: list = [tenant_id]
            else:
                where = ["e.user_id = %s", "e.tenant_id IS NULL"]
                params = [user_id]
            if status and status != "all":
                where.append("e.status = %s")
                params.append(status)
            if rule_code:
                # 一个筛选 chip 可代表一组规则码(逗号分隔),按组过滤;单码保持原样
                codes = [c for c in rule_code.split(",") if c]
                if len(codes) == 1:
                    where.append("e.rule_code = %s")
                    params.append(codes[0])
                elif codes:
                    where.append("e.rule_code = ANY(%s)")
                    params.append(codes)
            # v118.21.0 · 客户筛选 · client_id 来自 ocr_history(JOIN 后字段)
            if client_id:
                where.append("h.client_id = %s")
                params.append(int(client_id))
            # v118.28.1 · 员工分配过滤
            if restrict_client_ids is not None:
                if len(restrict_client_ids) == 0:
                    where.append("(e.user_id = %s AND h.client_id IS NULL)")
                    params.append(user_id)
                else:
                    where.append(
                        "(h.client_id = ANY(%s::bigint[]) OR (e.user_id = %s AND h.client_id IS NULL))"
                    )
                    params.append([int(c) for c in restrict_client_ids])
                    params.append(user_id)
            where_sql = " AND ".join(where)
            cur.execute(
                f"""
                SELECT e.id, e.history_id, e.rule_code, e.severity,
                       e.seller_name, e.invoice_no, e.total_amount, e.detail_json,
                       e.status, e.created_at, e.resolved_at,
                       h.filename, h.invoice_date, h.confidence, h.client_id
                FROM exceptions e
                INNER JOIN ocr_history h ON h.id = e.history_id
                WHERE {where_sql}
                ORDER BY
                  CASE e.severity WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                  e.created_at DESC
                LIMIT %s OFFSET %s
            """,
                params + [int(limit), int(offset)],
            )
            items = []
            for r in cur.fetchall():
                items.append(
                    {
                        "id": int(r["id"]),
                        "history_id": str(r["history_id"]),
                        "rule_code": r["rule_code"],
                        "severity": r["severity"],
                        "seller_name": r["seller_name"],
                        "invoice_no": r["invoice_no"],
                        "total_amount": (
                            float(r["total_amount"]) if r["total_amount"] is not None else None
                        ),
                        "detail": r["detail_json"] or {},
                        "status": r["status"],
                        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                        "resolved_at": r["resolved_at"].isoformat() if r["resolved_at"] else None,
                        "filename": r.get("filename"),
                        "invoice_date": (
                            r["invoice_date"].isoformat() if r.get("invoice_date") else None
                        ),
                        "confidence": r.get("confidence"),
                        "client_id": int(r["client_id"]) if r.get("client_id") else None,
                    }
                )
            return items
    except Exception as e:
        logger.error(f"list_exceptions failed: {e}")
        return []


def get_exception(
    user_id: str, exception_id: int, tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """取单条异常详情"""
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT e.*, h.filename, h.invoice_date, h.confidence
                    FROM exceptions e
                    LEFT JOIN ocr_history h ON h.id = e.history_id
                    WHERE e.id = %s AND e.tenant_id = %s
                """,
                    (int(exception_id), tenant_id),
                )
            else:
                cur.execute(
                    """
                    SELECT e.*, h.filename, h.invoice_date, h.confidence
                    FROM exceptions e
                    LEFT JOIN ocr_history h ON h.id = e.history_id
                    WHERE e.id = %s AND e.user_id = %s
                """,
                    (int(exception_id), user_id),
                )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "id": int(r["id"]),
                "history_id": str(r["history_id"]),
                "rule_code": r["rule_code"],
                "severity": r["severity"],
                "seller_name": r["seller_name"],
                "invoice_no": r["invoice_no"],
                "total_amount": float(r["total_amount"]) if r["total_amount"] is not None else None,
                "detail": r["detail_json"] or {},
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "resolved_at": r["resolved_at"].isoformat() if r["resolved_at"] else None,
                "filename": r.get("filename"),
                "confidence": r.get("confidence"),
            }
    except Exception as e:
        logger.error(f"get_exception failed: {e}")
        return None


def resolve_exception(
    user_id: str, exception_id: int, tenant_id: Optional[str] = None, new_status: str = "resolved"
) -> bool:
    """标记异常为已处理(resolved 或 ignored) · 同 tenant 内任意成员可处理"""
    if new_status not in ("resolved", "ignored", "pending"):
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    """
                    UPDATE exceptions
                    SET status = %s, resolved_by = %s, resolved_at = NOW()
                    WHERE id = %s AND tenant_id = %s
                """,
                    (new_status, str(user_id), int(exception_id), tenant_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE exceptions
                    SET status = %s, resolved_by = %s, resolved_at = NOW()
                    WHERE id = %s AND user_id = %s
                """,
                    (new_status, str(user_id), int(exception_id), user_id),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"resolve_exception failed: {e}")
        return False


# v118.21.2 · 学习规则面板 · 列表 + 删除(撤销学过的白名单)


# v118.21.3 · 字段编辑后清 pending 异常 · 让 hook 重跑写入新结果
def delete_pending_exceptions_by_history(
    history_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None
) -> int:
    """删除某 history 下的所有 pending 异常 · 保留 resolved/ignored
    返回:删除的条数
    """
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    """
                    DELETE FROM exceptions
                    WHERE history_id = %s::uuid AND tenant_id = %s AND status = 'pending'
                """,
                    (history_id, tenant_id),
                )
            else:
                cur.execute(
                    """
                    DELETE FROM exceptions
                    WHERE history_id = %s::uuid AND user_id = %s AND tenant_id IS NULL AND status = 'pending'
                """,
                    (history_id, str(user_id)),
                )
            return cur.rowcount
    except Exception as e:
        logger.error(f"delete_pending_exceptions_by_history failed: {e}")
        return 0


def count_exceptions_by_status_and_rule(
    user_id: str,
    tenant_id: Optional[str] = None,
    client_id: Optional[int] = None,
    by_rule_status: str = "pending",
) -> Dict[str, Any]:
    """统计 · 给前端筛选 chip 和顶部 KPI 用
    返回:{ pending: N, resolved: N, ignored: N,
           by_rule: { rule_code: count_at_by_rule_status } ,
           high_severity: N (pending 内的高危) }
    by_rule_status:控制 by_rule 字典统计哪个状态下的规则分布(默认 pending)
    """
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                where = "e.tenant_id = %s"
                params: list = [tenant_id]
            else:
                where = "e.user_id = %s AND e.tenant_id IS NULL"
                params = [user_id]
            # v118.21.0 · 客户筛选
            if client_id:
                where = where + " AND h.client_id = %s"
                params = list(params) + [int(client_id)]
            cur.execute(
                f"""
                SELECT e.status, e.rule_code, e.severity, COUNT(*) AS n
                FROM exceptions e
                INNER JOIN ocr_history h ON h.id = e.history_id
                WHERE {where}
                GROUP BY e.status, e.rule_code, e.severity
            """,
                params,
            )
            by_status = {"pending": 0, "resolved": 0, "ignored": 0}
            by_rule: Dict[str, int] = {}
            high = 0
            for r in cur.fetchall():
                st = r["status"]
                rc = r["rule_code"]
                sv = r["severity"]
                n = int(r["n"])
                by_status[st] = by_status.get(st, 0) + n
                # v118.21.1 · by_rule 跟随 by_rule_status(默认 pending)· high_severity 始终算 pending
                if st == by_rule_status:
                    by_rule[rc] = by_rule.get(rc, 0) + n
                if st == "pending" and sv == "high":
                    high += n
            return {
                "pending": by_status.get("pending", 0),
                "resolved": by_status.get("resolved", 0),
                "ignored": by_status.get("ignored", 0),
                "high_severity": high,
                "by_rule": by_rule,
            }
    except Exception as e:
        logger.error(f"count_exceptions_by_status_and_rule failed: {e}")
        return {"pending": 0, "resolved": 0, "ignored": 0, "high_severity": 0, "by_rule": {}}


# ============================================================
# v118.20.5 · 异常栏 P0-3 · 批量复核
# ============================================================
def batch_resolve_exceptions(
    user_id: str,
    exception_ids: List[int],
    tenant_id: Optional[str] = None,
    new_status: str = "resolved",
) -> Dict[str, Any]:
    """批量标记异常状态 · 一次性 UPDATE + 同时拿 (seller, rule) 给白名单调用方用
    返回 { processed: N, ids_done: [...], whitelist_pairs: [(seller, rule), ...] }
    whitelist_pairs 仅 new_status=='ignored' 且 seller_name 非空时返回 · 调用方自行去重写白名单
    """
    if new_status not in ("resolved", "ignored"):
        return {"processed": 0, "ids_done": [], "whitelist_pairs": []}
    if not exception_ids:
        return {"processed": 0, "ids_done": [], "whitelist_pairs": []}
    # 强制 int 类型 · 防注入
    safe_ids = [int(x) for x in exception_ids if x is not None]
    if not safe_ids:
        return {"processed": 0, "ids_done": [], "whitelist_pairs": []}
    try:
        with db.get_cursor(commit=True) as cur:
            # 先查满足条件的 (id, seller, rule) · 过滤掉跨 tenant 的(防越权)
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, seller_name, rule_code
                    FROM exceptions
                    WHERE id = ANY(%s) AND tenant_id = %s AND status = 'pending'
                """,
                    (safe_ids, tenant_id),
                )
            else:
                cur.execute(
                    """
                    SELECT id, seller_name, rule_code
                    FROM exceptions
                    WHERE id = ANY(%s) AND user_id = %s AND tenant_id IS NULL AND status = 'pending'
                """,
                    (safe_ids, user_id),
                )
            rows = cur.fetchall()
            ids_done = [int(r["id"]) for r in rows]
            if not ids_done:
                return {"processed": 0, "ids_done": [], "whitelist_pairs": []}
            # 批量 UPDATE
            if tenant_id:
                cur.execute(
                    """
                    UPDATE exceptions
                    SET status = %s, resolved_by = %s, resolved_at = NOW()
                    WHERE id = ANY(%s) AND tenant_id = %s AND status = 'pending'
                """,
                    (new_status, str(user_id), ids_done, tenant_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE exceptions
                    SET status = %s, resolved_by = %s, resolved_at = NOW()
                    WHERE id = ANY(%s) AND user_id = %s AND tenant_id IS NULL AND status = 'pending'
                """,
                    (new_status, str(user_id), ids_done, user_id),
                )
            # 收集 ignored 对应的 (seller, rule) · 缺 seller 的不进白名单
            wl_pairs: List[tuple] = []
            if new_status == "ignored":
                seen = set()
                for r in rows:
                    seller = (r.get("seller_name") or "").strip()
                    rc = r.get("rule_code")
                    if seller and rc:
                        key = (seller, rc)
                        if key not in seen:
                            seen.add(key)
                            wl_pairs.append(key)
            return {
                "processed": cur.rowcount,
                "ids_done": ids_done,
                "whitelist_pairs": wl_pairs,
            }
    except Exception as e:
        logger.error(f"batch_resolve_exceptions failed: {e}")
        return {"processed": 0, "ids_done": [], "whitelist_pairs": [], "error": str(e)}
