# -*- coding: utf-8 -*-
"""智能提醒(notification_rules + notification_logs)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
通知规则 CRUD + 发送日志 + 按模板查启用规则。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import json as _json
import logging
from typing import Optional, Dict, Any, List

from core import db

logger = logging.getLogger(__name__)


def ensure_notification_tables():
    """启动时建智能提醒 2 张表 · 幂等 + IF NOT EXISTS · 风格对齐异常栏"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notification_rules (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    name TEXT NOT NULL,
                    template_code TEXT NOT NULL,
                    params JSONB DEFAULT '{}'::jsonb,
                    enabled BOOLEAN DEFAULT true,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_notif_rules_user
                    ON notification_rules(user_id);
                CREATE INDEX IF NOT EXISTS idx_notif_rules_tenant
                    ON notification_rules(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_notif_rules_active
                    ON notification_rules(template_code) WHERE enabled = true;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    rule_id BIGINT,
                    template_code TEXT NOT NULL,
                    event_type TEXT,
                    event_ref TEXT,
                    line_user_id TEXT,
                    status TEXT NOT NULL,
                    error TEXT,
                    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_notif_logs_user
                    ON notification_logs(user_id, sent_at DESC);
                CREATE INDEX IF NOT EXISTS idx_notif_logs_rule
                    ON notification_logs(rule_id, sent_at DESC) WHERE rule_id IS NOT NULL;
            """)
            # B8 RLS wave3 3b:两表都含 tenant_id + user_id → tenant_or_user 隔离。
            # force=False(owner 仍绕过→外围未迁的裸 get_cursor 不破);业务连接 SET ROLE 后强制。
            from core.rls import apply_tenant_or_user_rls

            apply_tenant_or_user_rls(cur, "notification_rules", "notification_logs")
            logger.info("✅ notification_rules + notification_logs 表已就绪")
    except Exception as e:
        logger.error(f"ensure_notification_tables failed: {e}")


def list_notification_rules(user_id: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """列规则 · 同 tenant 共享视图(老板员工同租户共看共改)· 同异常栏隔离规则"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, name, template_code, params,
                           enabled, created_at, updated_at
                      FROM notification_rules
                     WHERE tenant_id = %s
                     ORDER BY created_at DESC
                """,
                    (tenant_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, name, template_code, params,
                           enabled, created_at, updated_at
                      FROM notification_rules
                     WHERE user_id = %s AND tenant_id IS NULL
                     ORDER BY created_at DESC
                """,
                    (str(user_id),),
                )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_notification_rules failed: {e}")
        return []


def get_notification_rule(
    rule_id: int, user_id: str, tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """取一条规则 · 鉴权:必须属于本人或本租户"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, name, template_code, params,
                           enabled, created_at, updated_at
                      FROM notification_rules
                     WHERE id = %s AND tenant_id = %s
                     LIMIT 1
                """,
                    (int(rule_id), tenant_id),
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, name, template_code, params,
                           enabled, created_at, updated_at
                      FROM notification_rules
                     WHERE id = %s AND user_id = %s AND tenant_id IS NULL
                     LIMIT 1
                """,
                    (int(rule_id), str(user_id)),
                )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_notification_rule failed: {e}")
        return None


def create_notification_rule(
    user_id: str,
    tenant_id: Optional[str],
    name: str,
    template_code: str,
    params: Optional[Dict[str, Any]] = None,
    enabled: bool = True,
) -> Optional[int]:
    """新建规则 · 返回新 id"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            cur.execute(
                """
                INSERT INTO notification_rules
                    (user_id, tenant_id, name, template_code, params, enabled)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                RETURNING id
            """,
                (
                    str(user_id),
                    tenant_id,
                    name.strip(),
                    template_code,
                    _json.dumps(params or {}, ensure_ascii=False),
                    bool(enabled),
                ),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_notification_rule failed: {e}")
        return None


def update_notification_rule(
    rule_id: int,
    user_id: str,
    tenant_id: Optional[str],
    name: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    enabled: Optional[bool] = None,
) -> bool:
    """改规则 · 任一字段非 None 即更新 · 鉴权同 get"""
    sets = []
    vals: list = []
    if name is not None:
        sets.append("name = %s")
        vals.append(name.strip())
    if params is not None:
        sets.append("params = %s::jsonb")
        vals.append(_json.dumps(params, ensure_ascii=False))
    if enabled is not None:
        sets.append("enabled = %s")
        vals.append(bool(enabled))
    if not sets:
        return True  # 没要改的 · 直接 OK
    sets.append("updated_at = NOW()")
    set_sql = ", ".join(sets)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            if tenant_id:
                cur.execute(
                    f"UPDATE notification_rules SET {set_sql} " f"WHERE id = %s AND tenant_id = %s",
                    (*vals, int(rule_id), tenant_id),
                )
            else:
                cur.execute(
                    f"UPDATE notification_rules SET {set_sql} "
                    f"WHERE id = %s AND user_id = %s AND tenant_id IS NULL",
                    (*vals, int(rule_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_notification_rule failed: {e}")
        return False


def delete_notification_rule(rule_id: int, user_id: str, tenant_id: Optional[str]) -> bool:
    """删规则 · 同 get 鉴权 · 同时删 logs 里的引用(SET NULL · 保留发送历史)"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            # 先把 logs 的 rule_id 置空(保留历史发送记录)· RLS 下只动本租户可见 logs
            cur.execute(
                "UPDATE notification_logs SET rule_id = NULL WHERE rule_id = %s",
                (int(rule_id),),
            )
            if tenant_id:
                cur.execute(
                    "DELETE FROM notification_rules WHERE id = %s AND tenant_id = %s",
                    (int(rule_id), tenant_id),
                )
            else:
                cur.execute(
                    "DELETE FROM notification_rules "
                    "WHERE id = %s AND user_id = %s AND tenant_id IS NULL",
                    (int(rule_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_notification_rule failed: {e}")
        return False


def log_notification(
    user_id: str,
    tenant_id: Optional[str],
    rule_id: Optional[int],
    template_code: str,
    event_type: Optional[str],
    event_ref: Optional[str],
    line_user_id: Optional[str],
    status: str,
    error: Optional[str] = None,
) -> Optional[int]:
    """写一条发送记录 · 失败也吞(不影响主流程)"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            cur.execute(
                """
                INSERT INTO notification_logs
                    (user_id, tenant_id, rule_id, template_code,
                     event_type, event_ref, line_user_id, status, error)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    str(user_id),
                    tenant_id,
                    int(rule_id) if rule_id is not None else None,
                    template_code,
                    event_type,
                    event_ref,
                    line_user_id,
                    status,
                    error,
                ),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.warning(f"log_notification failed: {e}")
        return None


def list_notification_logs(
    user_id: str, tenant_id: Optional[str] = None, limit: int = 50
) -> List[Dict[str, Any]]:
    """列发送日志 · 同 tenant 共享 · 默认最近 50 条"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, rule_id, template_code,
                           event_type, event_ref, line_user_id, status, error, sent_at
                      FROM notification_logs
                     WHERE tenant_id = %s
                     ORDER BY sent_at DESC LIMIT %s
                """,
                    (tenant_id, int(limit)),
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, rule_id, template_code,
                           event_type, event_ref, line_user_id, status, error, sent_at
                      FROM notification_logs
                     WHERE user_id = %s AND tenant_id IS NULL
                     ORDER BY sent_at DESC LIMIT %s
                """,
                    (str(user_id), int(limit)),
                )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_notification_logs failed: {e}")
        return []


def list_active_notification_rules_by_template(template_code: str) -> List[Dict[str, Any]]:
    """v118.22.1.1 hook 用 · 取所有启用的某模板规则(跨 user 全表 · 异步触发匹配)

    B8 RLS bypass(系统级):本函数是 _notify_exception_high 后台 hook 的唯一数据源,从 LINE
    webhook 等无 HTTP 单租户上下文的入口触发,故意跨租户取全表规则,再在 Python 端按
    (user, tenant) 过滤(_rule_belongs_to)。enroll 后若走单租户上下文会只返本租户规则 → hook
    漏推。因此显式 bypass=True。每条匹配规则的发送记录仍按该规则自带的 tenant/user 落库
    (log_notification 带上下文,非 bypass)。
    """
    try:
        with db.get_cursor_rls(bypass=True) as cur:
            cur.execute(
                """
                SELECT id, user_id, tenant_id, name, template_code, params, enabled
                  FROM notification_rules
                 WHERE template_code = %s AND enabled = true
            """,
                (template_code,),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_active_notification_rules_by_template failed: {e}")
        return []
