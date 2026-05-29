# -*- coding: utf-8 -*-
"""卖方智能分拣路由 DAL(REFACTOR-WA-B1 · 2026-05-29 从 workspace/store 抽出 · 纯搬家 0 逻辑改)

seller_workspace_routes 学习记忆表 + 按卖方税号/名 匹配账套(match_workspace_for_seller)+
归属后回写 ocr_history.workspace_client_id。组内自洽(只依赖 db + 组内 _norm_tax/_match)·
workspace/store 顶部 re-import 当 facade · db.X/store.X/本模块.X 单一对象不变。
"""

import logging
from typing import Optional, Dict, Any, List  # noqa: F401

logger = logging.getLogger(__name__)


def _norm_tax(tax: Optional[str]) -> str:
    """税号归一:去横杠/空格。"""
    return (tax or "").replace("-", "").replace(" ", "").strip()


def ensure_seller_route_table():
    """建 seller_workspace_routes 表 · 幂等。铁律 #2:DDL commit=True。"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS seller_workspace_routes (
                    id                  BIGSERIAL PRIMARY KEY,
                    tenant_id           UUID,
                    user_id             UUID NOT NULL,
                    seller_tax          TEXT,
                    seller_name         TEXT,
                    workspace_client_id BIGINT NOT NULL,
                    use_count           INTEGER NOT NULL DEFAULT 1,
                    last_used_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                -- 同 scope 下同 (税号, 名字归一) 唯一 → 支持 upsert
                CREATE UNIQUE INDEX IF NOT EXISTS seller_route_unique_scope
                    ON seller_workspace_routes
                    (COALESCE(tenant_id::text, user_id::text),
                     COALESCE(seller_tax, ''),
                     LOWER(COALESCE(seller_name, '')));
                CREATE INDEX IF NOT EXISTS seller_route_tax_idx
                    ON seller_workspace_routes (seller_tax)
                    WHERE seller_tax IS NOT NULL AND length(seller_tax) >= 10;
            """)
        logger.info("✅ seller_workspace_routes 表已就绪")
    except Exception as e:
        logger.warning(f"ensure_seller_route_table failed: {e}")


def learn_seller_workspace_route(
    seller_tax: Optional[str],
    seller_name: Optional[str],
    workspace_client_id: int,
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """用户绑定卖方→账套时记忆。幂等 upsert(use_count++)。"""
    if not workspace_client_id:
        return False
    tax = _norm_tax(seller_tax) or None
    name = (seller_name or "").strip()[:200] or None
    if not tax and not name:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO seller_workspace_routes
                    (tenant_id, user_id, seller_tax, seller_name, workspace_client_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (COALESCE(tenant_id::text, user_id::text),
                             COALESCE(seller_tax, ''), LOWER(COALESCE(seller_name, '')))
                DO UPDATE SET workspace_client_id = EXCLUDED.workspace_client_id,
                              use_count = seller_workspace_routes.use_count + 1,
                              last_used_at = NOW()
                """,
                (tenant_id, str(user_id), tax, name, int(workspace_client_id)),
            )
        return True
    except Exception as e:
        logger.warning(f"learn_seller_workspace_route failed: {e}")
        return False


def _match_seller_route_id(cur, seller_tax, seller_name, scope_sql, scope_val) -> Optional[int]:
    """在已开 cursor 上查 seller 路由记忆 · 税号优先 → 名字 · 返 workspace_client_id 或 None。"""
    tax = _norm_tax(seller_tax)
    if len(tax) >= 10 and tax.isdigit():
        cur.execute(
            f"""SELECT workspace_client_id FROM seller_workspace_routes
                WHERE {scope_sql} AND seller_tax = %s
                ORDER BY last_used_at DESC LIMIT 1""",
            (scope_val, tax),
        )
        r = cur.fetchone()
        if r:
            return int(r["workspace_client_id"])
    name = (seller_name or "").strip()
    if name:
        cur.execute(
            f"""SELECT workspace_client_id FROM seller_workspace_routes
                WHERE {scope_sql} AND LOWER(TRIM(seller_name)) = LOWER(%s)
                ORDER BY last_used_at DESC LIMIT 1""",
            (scope_val, name),
        )
        r = cur.fetchone()
        if r:
            return int(r["workspace_client_id"])
    return None


def match_workspace_for_seller(
    seller_tax: Optional[str],
    seller_name: Optional[str],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """卖方智能分拣(Phase 1 · Zihao 2026-05-26):按发票**卖方**(=账套主体)的
    税号/名字匹配到 workspace_client + 其绑定的 ERP endpoint。

    销项发票上卖方 = 在为谁做账 = workspace_client = 绑定某 ERP 公司/年度账套。
    税号优先(泰国 13 位法定唯一身份),名字兜底。

    返回 {action, workspace_client_id, endpoint_id, workspace_name, match_source, reason}:
      action:
        "assigned" — 唯一命中且该 workspace 已绑 endpoint → 可自动路由推送
        "unbound"  — 唯一命中但 workspace 未绑 ERP endpoint → 异常「未绑定 ERP 账套」
        "multi"    — 多个 workspace 命中(同税号/同名)→ 异常 · 需用户消歧
        "none"     — 没有任何匹配 → 异常 · 需绑定/新建账套
    纯只读 · 不写库(绑定/记忆由 caller 在用户操作后做)。
    """
    out = {
        "action": "none",
        "workspace_client_id": None,
        "endpoint_id": None,
        "workspace_name": None,
        "match_source": "",
        "reason": "no_match",
    }

    # tenant 隔离(与 list_workspace_clients 一致)
    if tenant_id:
        scope_sql = "tenant_id = %s"
        scope_val = tenant_id
    else:
        scope_sql = "user_id = %s AND tenant_id IS NULL"
        scope_val = str(user_id)

    def _decide(rows: List[Dict[str, Any]], source: str) -> Optional[Dict[str, Any]]:
        if not rows:
            return None
        if len(rows) > 1:
            return {
                "action": "multi",
                "workspace_client_id": None,
                "endpoint_id": None,
                "workspace_name": None,
                "match_source": source,
                "reason": "multiple_workspace_candidates",
            }
        r = rows[0]
        ep = (r.get("erp_endpoint_id") or "").strip() or None
        return {
            "action": "assigned" if ep else "unbound",
            "workspace_client_id": int(r["id"]),
            "endpoint_id": ep,
            "workspace_name": r.get("name"),
            "match_source": source,
            "reason": "matched_with_endpoint" if ep else "workspace_has_no_endpoint",
        }

    def _load_decide(cur, wcid: int, source: str) -> Optional[Dict[str, Any]]:
        cur.execute(
            f"""SELECT id, name, erp_endpoint_id FROM workspace_clients
                WHERE id = %s AND {scope_sql} AND is_active = TRUE""",
            (int(wcid), scope_val),
        )
        return _decide([dict(r) for r in (cur.fetchall() or [])], source)

    try:
        with db.get_cursor() as cur:
            # 0) 学习路由记忆(用户绑过的 seller→workspace · 税号优先 → 名字)
            route_wcid = _match_seller_route_id(cur, seller_tax, seller_name, scope_sql, scope_val)
            if route_wcid:
                d = _load_decide(cur, route_wcid, "route_memory")
                if d:
                    return d
                # 记忆指向的 workspace 已删/停用 → 忽略记忆 · 继续按 tax/name 直配

            # 1) 税号精确(归一比对 · 13 位法定唯一)
            tax_clean = _norm_tax(seller_tax)
            if len(tax_clean) >= 10 and tax_clean.isdigit():
                cur.execute(
                    f"""
                    SELECT id, name, erp_endpoint_id FROM workspace_clients
                    WHERE {scope_sql} AND is_active = TRUE
                      AND REPLACE(REPLACE(COALESCE(tax_id,''),'-',''),' ','') = %s
                    """,
                    (scope_val, tax_clean),
                )
                d = _decide([dict(r) for r in (cur.fetchall() or [])], "seller_tax")
                if d:
                    return d

            # 2) 名字精确(忽略大小写 · 去首尾空格)
            sname = (seller_name or "").strip()
            if sname:
                cur.execute(
                    f"""
                    SELECT id, name, erp_endpoint_id FROM workspace_clients
                    WHERE {scope_sql} AND is_active = TRUE
                      AND LOWER(TRIM(name)) = LOWER(%s)
                    """,
                    (scope_val, sname),
                )
                d = _decide([dict(r) for r in (cur.fetchall() or [])], "seller_name")
                if d:
                    return d
    except Exception as e:
        logger.warning(f"match_workspace_for_seller failed: {e}")
        out["reason"] = "lookup_error"
        return out

    return out


def update_history_workspace_client_id(
    history_id: str,
    workspace_client_id: Optional[int],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """卖方分拣后把 workspace_client_id 写回 ocr_history(账套归属)。
    镜像 clients.update_history_client_id(买方),tenant 隔离,不碰 client_id(买方)。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    """
                    UPDATE ocr_history SET workspace_client_id = %s, updated_at = NOW()
                    WHERE id = %s
                      AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    """,
                    (workspace_client_id, str(history_id), tenant_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE ocr_history SET workspace_client_id = %s, updated_at = NOW()
                    WHERE id = %s AND user_id = %s
                    """,
                    (workspace_client_id, str(history_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.warning(f"update_history_workspace_client_id failed: {e}")
        return False


import db  # noqa: E402
