# -*- coding: utf-8 -*-
"""主体分拣路由 DAL(REFACTOR-WA-B1 · 2026-05-29 从 workspace/store 抽出)

seller_workspace_routes 学习记忆表 + 按票面一方税号/名 匹配账套主体 + 归属后回写
ocr_history.workspace_client_id。两个入口共用 _match_party_direct/_decide:
  · match_workspace_for_seller — 销项票卖方=账套主体(含学习路由记忆)
  · match_workspace_for_buyer  — 采购票买方=账套主体(2026-06-23 · 修 direction_unknown 根因)
组内自洽(只依赖 db + 组内 helper)· workspace/store 顶部 re-import 当 facade。
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
            # B8 RLS wave3 3b:含 tenant_id + user_id → tenant_or_user 隔离(带 user 兜底,
            # 孤立用户的学习路由仍自见)。force=False(owner 绕过→未迁裸 get_cursor 不破)。
            from core.rls import apply_tenant_or_user_rls

            apply_tenant_or_user_rls(cur, "seller_workspace_routes")
        logger.info("✅ seller_workspace_routes 表已就绪")
    except Exception as e:
        logger.warning(f"ensure_seller_route_table failed: {e}")
    # 税务画像 4 表挂 workspace 域 ensure 链自愈(alembic 0064 双跑)——方案 §5.3 首选
    # ensure_workspace_tables 尾部,但 store.py 已贴 500 行上限,挂本函数尾(startup 同链紧随调用)。
    try:
        from services.workspace.tax_profile_schema import ensure_tax_profile_schema

        ensure_tax_profile_schema()
    except Exception as e:
        logger.warning(f"ensure_tax_profile_schema failed: {e}")


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
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
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


def _scope_clause(user_id: str, tenant_id: Optional[str]) -> tuple:
    """tenant 隔离 scope(与 list_workspace_clients 一致)→ (scope_sql, scope_val)。"""
    if tenant_id:
        return "tenant_id = %s", tenant_id
    return "user_id = %s AND tenant_id IS NULL", str(user_id)


def _none_result(reason: str = "no_match") -> Dict[str, Any]:
    return {
        "action": "none",
        "workspace_client_id": None,
        "endpoint_id": None,
        "workspace_name": None,
        "match_source": "",
        "reason": reason,
    }


def _decide(rows: List[Dict[str, Any]], source: str) -> Optional[Dict[str, Any]]:
    """命中行 → 路由决策:空=None / 多=multi(需消歧)/ 单=assigned(有 endpoint)或 unbound。纯函数。"""
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


def _match_party_direct(
    cur,
    tax: Optional[str],
    name: Optional[str],
    scope_sql: str,
    scope_val: str,
    *,
    src_tax: str,
    src_name: str,
) -> Optional[Dict[str, Any]]:
    """按税号(13 位法定唯一 · 优先)→ 名字(精确)直配 active workspace_clients → _decide 或 None。
    卖方/买方分拣共用(只差 match_source 标签)· 在已开 cursor 上跑。"""
    tax_clean = _norm_tax(tax)
    if len(tax_clean) >= 10 and tax_clean.isdigit():
        cur.execute(
            f"""
            SELECT id, name, erp_endpoint_id FROM workspace_clients
            WHERE {scope_sql} AND is_active = TRUE
              AND REPLACE(REPLACE(COALESCE(tax_id,''),'-',''),' ','') = %s
            """,
            (scope_val, tax_clean),
        )
        d = _decide([dict(r) for r in (cur.fetchall() or [])], src_tax)
        if d:
            return d
    sname = (name or "").strip()
    if sname:
        cur.execute(
            f"""
            SELECT id, name, erp_endpoint_id FROM workspace_clients
            WHERE {scope_sql} AND is_active = TRUE
              AND LOWER(TRIM(name)) = LOWER(%s)
            """,
            (scope_val, sname),
        )
        d = _decide([dict(r) for r in (cur.fetchall() or [])], src_name)
        if d:
            return d
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
    税号优先(泰国 13 位法定唯一身份),名字兜底。采购票卖方=供应商≠自家 → 这里不命中,
    由 match_workspace_for_buyer 按买方兜底(见其 docstring)。

    返回 {action, workspace_client_id, endpoint_id, workspace_name, match_source, reason}:
      action:
        "assigned" — 唯一命中且该 workspace 已绑 endpoint → 可自动路由推送
        "unbound"  — 唯一命中但 workspace 未绑 ERP endpoint → 异常「未绑定 ERP 账套」
        "multi"    — 多个 workspace 命中(同税号/同名)→ 异常 · 需用户消歧
        "none"     — 没有任何匹配 → 异常 · 需绑定/新建账套
    纯只读 · 不写库(绑定/记忆由 caller 在用户操作后做)。
    """
    scope_sql, scope_val = _scope_clause(user_id, tenant_id)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            # 0) 学习路由记忆(用户绑过的 seller→workspace · 税号优先 → 名字)
            route_wcid = _match_seller_route_id(cur, seller_tax, seller_name, scope_sql, scope_val)
            if route_wcid:
                cur.execute(
                    f"""SELECT id, name, erp_endpoint_id FROM workspace_clients
                        WHERE id = %s AND {scope_sql} AND is_active = TRUE""",
                    (int(route_wcid), scope_val),
                )
                d = _decide([dict(r) for r in (cur.fetchall() or [])], "route_memory")
                if d:
                    return d
                # 记忆指向的 workspace 已删/停用 → 忽略记忆 · 继续按 tax/name 直配

            # 1+2) 税号精确(13 位法定唯一)→ 名字精确
            d = _match_party_direct(
                cur,
                seller_tax,
                seller_name,
                scope_sql,
                scope_val,
                src_tax="seller_tax",
                src_name="seller_name",
            )
            if d:
                return d
    except Exception as e:
        logger.warning(f"match_workspace_for_seller failed: {e}")
        return _none_result("lookup_error")

    return _none_result()


def match_workspace_for_buyer(
    buyer_tax: Optional[str],
    buyer_name: Optional[str],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """采购票分拣(2026-06-23 · 修 direction_unknown 根因):票上【买方】= 账套主体 = 自家。

    采购发票卖方 = 供应商(≠自家)→ match_workspace_for_seller 不命中,采购票就落回错误的
    默认主体 → Express 方向判定失锚(自家税号空)→ direction_unknown。此时**买方**才是自家
    主体,按买方税号/名直配 workspace_client(不查 seller 路由记忆 —— 那是卖方语义)。

    仅当卖方分拣无果时由 caller 兜底调用(销项票卖方=自家先命中,不会走到这)。返回结构同
    match_workspace_for_seller,供 route_assigns_workspace 消费。纯只读 · 不写库。
    """
    scope_sql, scope_val = _scope_clause(user_id, tenant_id)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            d = _match_party_direct(
                cur,
                buyer_tax,
                buyer_name,
                scope_sql,
                scope_val,
                src_tax="buyer_tax",
                src_name="buyer_name",
            )
            if d:
                return d
    except Exception as e:
        logger.warning(f"match_workspace_for_buyer failed: {e}")
        return _none_result("lookup_error")

    return _none_result()


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
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
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


def route_assigns_workspace(seller_match: Optional[Dict[str, Any]]) -> Optional[int]:
    """卖方分拣结果 → 要【覆盖】账套归属用的 workspace_client_id;否则 None。

    命中具体主体(assigned/unbound)才返其 id;none/multi(没命中/多候选)返 None →
    调用方据此【保留】上传时已写的归属,**绝不用 None 回写清空**。否则采购票(卖方=
    供应商≠自家)归属被清成 NULL → 下游 Express 方向判定(以自家主体税号当锚点)失锚 →
    direction_unknown(2026-06-22 真机事故根因)。纯函数 · 无 DB。
    """
    m = seller_match or {}
    if m.get("action") in ("assigned", "unbound"):
        return m.get("workspace_client_id")
    return None


from core import db  # noqa: E402
