# -*- coding: utf-8 -*-
"""workspace_clients(账套主体 / 工作台归属)数据访问层 · B0 地基(2026-05-25)

核心概念拆分(Zihao 2026-05-25 拍板):
  - workspace_client  = "在为哪家公司做账"(账套主体 / 权限范围 / 用哪个 ERP 账套)。
    登录时选;所有上传/对账/推送归属于它;员工权限按它分。← 本表
  - history.client_id = 发票买方(OCR 认 → MR.ERP 应收客户)。← 不动,另一回事

⚠️ 不复用 clients 表(那张语义已被"买方/对方"占用)· 新建独立表避免账错。
⚠️ Pearnly 不自动创建 ERP 账套主体:workspace 只**绑定已有** erp_endpoint;
   交易对象(买方/供应商/商品)才自动创建(见 mrerp_customer_sync)。

迁移机制:生产不跑 `alembic upgrade`(git-deploy 无钩子)· schema 靠启动 ensure_*
应用 → 本模块走"双跑"模式(alembic/versions/005 留档 + ensure_workspace_tables 真建)·
与 002_field_overrides 同范式。纯加法 · 幂等 · 零破坏现有表。

tenant 隔离:有 tenant_id 按 tenant 共享(老板+员工同租户可见)· 否则按 user_id。
"""

import logging
from typing import Optional, Dict, Any, List

import db

logger = logging.getLogger(__name__)


def ensure_workspace_tables():
    """建 workspace_clients 表 + 给 ocr_history 加 workspace_client_id 列 · 幂等。

    铁律 #2:DDL 必须 commit=True(get_cursor 默认不 commit · DDL 会回滚)。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workspace_clients (
                    id              BIGSERIAL PRIMARY KEY,
                    tenant_id       UUID,
                    user_id         UUID NOT NULL,
                    name            TEXT NOT NULL,
                    tax_id          TEXT,
                    erp_endpoint_id TEXT,
                    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_workspace_clients_tenant
                    ON workspace_clients(tenant_id, is_active);
                CREATE INDEX IF NOT EXISTS idx_workspace_clients_user
                    ON workspace_clients(user_id, is_active);
            """)
            # ocr_history 加 workspace 归属列(可空 · 不动现有 client_id=买方)
            cur.execute("""
                ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS workspace_client_id BIGINT;
                CREATE INDEX IF NOT EXISTS idx_ocr_history_workspace
                    ON ocr_history(workspace_client_id) WHERE workspace_client_id IS NOT NULL;
            """)
        logger.info("✅ workspace_clients 表 + ocr_history.workspace_client_id 已就绪")
    except Exception as e:
        logger.error(f"ensure_workspace_tables failed: {e}")


def create_workspace_client(
    user_id: str,
    tenant_id: Optional[str],
    name: str,
    tax_id: Optional[str] = None,
    erp_endpoint_id: Optional[str] = None,
) -> Optional[int]:
    """新建账套主体。返回新 id。name 必填。"""
    if not name or not name.strip():
        return None
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO workspace_clients
                    (user_id, tenant_id, name, tax_id, erp_endpoint_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    str(user_id),
                    tenant_id,
                    name.strip()[:200],
                    (tax_id or "").strip()[:30] or None,
                    (str(erp_endpoint_id).strip() if erp_endpoint_id else None),
                ),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_workspace_client failed: {e}")
        return None


def get_workspace_client(
    workspace_client_id: int,
    user_id: str,
    tenant_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """取单个账套主体(tenant 隔离:同租户共享 · 否则仅自己)。"""
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    "SELECT * FROM workspace_clients WHERE id = %s AND tenant_id = %s",
                    (int(workspace_client_id), tenant_id),
                )
            else:
                cur.execute(
                    "SELECT * FROM workspace_clients WHERE id = %s AND user_id = %s "
                    "AND tenant_id IS NULL",
                    (int(workspace_client_id), str(user_id)),
                )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.warning(f"get_workspace_client failed: {e}")
        return None


def list_workspace_clients(
    user_id: str,
    tenant_id: Optional[str] = None,
    restrict_ids: Optional[List[int]] = None,
    active_only: bool = True,
) -> List[Dict[str, Any]]:
    """列出账套主体。

    restrict_ids(B3 员工分配用):None=不限(老板)· []=没分配→空 · [...]=只看这些。
    """
    if restrict_ids is not None and len(restrict_ids) == 0:
        return []
    try:
        params: list = []
        if tenant_id:
            where = "tenant_id = %s"
            params.append(tenant_id)
        else:
            where = "user_id = %s AND tenant_id IS NULL"
            params.append(str(user_id))
        if active_only:
            where += " AND is_active = TRUE"
        if restrict_ids is not None:
            where += " AND id = ANY(%s)"
            params.append([int(x) for x in restrict_ids])
        with db.get_cursor() as cur:
            cur.execute(
                f"SELECT * FROM workspace_clients WHERE {where} ORDER BY name",
                tuple(params),
            )
            return [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.warning(f"list_workspace_clients failed: {e}")
        return []


def update_workspace_client(
    workspace_client_id: int,
    user_id: str,
    tenant_id: Optional[str] = None,
    name: Optional[str] = None,
    tax_id: Optional[str] = None,
) -> bool:
    """改账套主体的名称/税号(P3-客户管理页编辑用)。tenant 隔离。

    只更新传入的字段(None=不动)。name 给空串视为不改(账套主体名不能清空)。
    """
    sets: list = []
    params: list = []
    if name is not None and name.strip():
        sets.append("name = %s")
        params.append(name.strip()[:200])
    if tax_id is not None:
        sets.append("tax_id = %s")
        params.append((tax_id or "").strip()[:30] or None)
    if not sets:
        return False
    sets.append("updated_at = NOW()")
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                where = "id = %s AND tenant_id = %s"
                params += [int(workspace_client_id), tenant_id]
            else:
                where = "id = %s AND user_id = %s AND tenant_id IS NULL"
                params += [int(workspace_client_id), str(user_id)]
            cur.execute(
                f"UPDATE workspace_clients SET {', '.join(sets)} WHERE {where}",
                tuple(params),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_workspace_client failed: {e}")
        return False


def archive_workspace_client(
    workspace_client_id: int,
    user_id: str,
    tenant_id: Optional[str] = None,
    active: bool = False,
) -> bool:
    """归档/恢复账套主体(软删 · is_active 切换)。

    软删而非硬删:历史发票的 workspace_client_id 归属、seller 路由记忆都还指向它,
    硬删会留下悬空引用。归档后默认列表(active_only)看不到,但归属链完整。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    "UPDATE workspace_clients SET is_active = %s, updated_at = NOW() "
                    "WHERE id = %s AND tenant_id = %s",
                    (bool(active), int(workspace_client_id), tenant_id),
                )
            else:
                cur.execute(
                    "UPDATE workspace_clients SET is_active = %s, updated_at = NOW() "
                    "WHERE id = %s AND user_id = %s AND tenant_id IS NULL",
                    (bool(active), int(workspace_client_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"archive_workspace_client failed: {e}")
        return False


def list_workspace_clients_enriched(
    user_id: str,
    tenant_id: Optional[str] = None,
    active_only: bool = True,
) -> List[Dict[str, Any]]:
    """列账套主体 + 关联发票统计(发票数 / 金额合计)· 客户管理页「账套主体」tab 用。

    与 list_workspace_clients 同 scope/隔离规则,额外 LEFT JOIN ocr_history 聚合。
    归属 = ocr_history.workspace_client_id。tenant 模式下统计同租户全部成员的发票。
    """
    try:
        params: list = []
        if tenant_id:
            where = "wc.tenant_id = %s"
            params.append(tenant_id)
            join_user = ""  # tenant 共享:不再按 user 限制发票
        else:
            where = "wc.user_id = %s AND wc.tenant_id IS NULL"
            params.append(str(user_id))
            join_user = ""
        if active_only:
            where += " AND wc.is_active = TRUE"
        with db.get_cursor() as cur:
            cur.execute(
                f"""
                SELECT wc.*,
                       COALESCE(agg.invoice_count, 0)  AS invoice_count,
                       COALESCE(agg.total_amount, 0)   AS total_amount,
                       agg.last_invoice_at             AS last_invoice_at
                FROM workspace_clients wc
                LEFT JOIN (
                    SELECT workspace_client_id,
                           COUNT(*)               AS invoice_count,
                           SUM(total_amount)      AS total_amount,
                           MAX(created_at)        AS last_invoice_at
                    FROM ocr_history
                    WHERE workspace_client_id IS NOT NULL
                    GROUP BY workspace_client_id
                ) agg ON agg.workspace_client_id = wc.id
                WHERE {where} {join_user}
                ORDER BY wc.name
                """,
                tuple(params),
            )
            return [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.warning(f"list_workspace_clients_enriched failed: {e}")
        # 兜底:退回不带统计的基础列表(不让管理页白屏)
        return list_workspace_clients(user_id, tenant_id=tenant_id, active_only=active_only)


def bind_workspace_endpoint(
    workspace_client_id: int,
    erp_endpoint_id: Optional[str],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """把账套主体绑到一个**已有** ERP endpoint(erp_endpoint_id=None 解绑)。

    只绑定 · 绝不创建 ERP 账套(Pearnly 不自动建账套主体)。tenant 隔离。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    "UPDATE workspace_clients SET erp_endpoint_id = %s, updated_at = NOW() "
                    "WHERE id = %s AND tenant_id = %s",
                    (
                        (str(erp_endpoint_id).strip() if erp_endpoint_id else None),
                        int(workspace_client_id),
                        tenant_id,
                    ),
                )
            else:
                cur.execute(
                    "UPDATE workspace_clients SET erp_endpoint_id = %s, updated_at = NOW() "
                    "WHERE id = %s AND user_id = %s AND tenant_id IS NULL",
                    (
                        (str(erp_endpoint_id).strip() if erp_endpoint_id else None),
                        int(workspace_client_id),
                        str(user_id),
                    ),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"bind_workspace_endpoint failed: {e}")
        return False


def get_workspace_endpoint_id(
    workspace_client_id: int,
    user_id: str,
    tenant_id: Optional[str] = None,
) -> Optional[str]:
    """取账套主体绑定的 ERP endpoint id(没绑返 None → 上层提示"未配置 ERP 连接")。"""
    wc = get_workspace_client(workspace_client_id, user_id, tenant_id)
    if not wc:
        return None
    return wc.get("erp_endpoint_id") or None


def _norm_tax(tax: Optional[str]) -> str:
    """税号归一:去横杠/空格。"""
    return (tax or "").replace("-", "").replace(" ", "").strip()


# ============================================================
# P1a · seller 路由记忆(seller_tax/seller_name → workspace_client)
# 用户给未匹配卖方绑定一次 → 记住 → 下次自动命中(Zihao 2026-05-26)。
# 独立表 · 不污染 workspace_clients.tax_id(一个 workspace 可多卖方抬头/名字变体)。
# ============================================================


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
