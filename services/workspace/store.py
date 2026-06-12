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

from core import db

# facade re-export(REFACTOR-WA-B1 · 卖方分拣实现下沉 seller_routing · db.X/store.X 单一对象不变)
from services.workspace.seller_routing import (  # noqa: F401,E402
    _norm_tax,
    ensure_seller_route_table,
    learn_seller_workspace_route,
    _match_seller_route_id,
    match_workspace_for_seller,
    update_history_workspace_client_id,
)

logger = logging.getLogger(__name__)

SUBJECT_TYPES = ("company", "personal")


def _norm_subject_type(value: Optional[str]) -> str:
    """归一主体类型。未知/空 → company(保守默认 · 不误判为个人零税号)。"""
    v = (value or "").strip().lower()
    return v if v in SUBJECT_TYPES else "company"


def _find_active_personal(cur, user_id: str, tenant_id: Optional[str]) -> Optional[int]:
    """查同 scope 在用的 personal 主体 id(幂等建主体用)。tenant 隔离同其余读路径。"""
    if tenant_id:
        cur.execute(
            "SELECT id FROM workspace_clients WHERE tenant_id = %s "
            "AND subject_type = 'personal' AND is_active = TRUE ORDER BY id LIMIT 1",
            (tenant_id,),
        )
    else:
        cur.execute(
            "SELECT id FROM workspace_clients WHERE user_id = %s AND tenant_id IS NULL "
            "AND subject_type = 'personal' AND is_active = TRUE ORDER BY id LIMIT 1",
            (str(user_id),),
        )
    row = cur.fetchone()
    return int(row["id"]) if row else None


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
            # 用户引导闭环(2026-06-11):主体类型 company|personal。个人/freelancer/未
            # 注册小店走 personal(零税号 · 仅开收据)。存量行默认 company。
            cur.execute(
                "ALTER TABLE workspace_clients "
                "ADD COLUMN IF NOT EXISTS subject_type TEXT NOT NULL DEFAULT 'company'"
            )
            # 每 scope 至多一个在用 personal 主体 → 建主体并发幂等 + 迁移可重入的 DB 兜底。
            # subject_type 为新列,无存量 personal 行,索引创建必成功。
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_workspace_clients_personal_tenant "
                "ON workspace_clients(tenant_id) "
                "WHERE subject_type = 'personal' AND is_active AND tenant_id IS NOT NULL"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_workspace_clients_personal_user "
                "ON workspace_clients(user_id) "
                "WHERE subject_type = 'personal' AND is_active AND tenant_id IS NULL"
            )
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
    address: Optional[str] = None,
    branch: Optional[str] = None,
    phone: Optional[str] = None,
    vat_registered: bool = True,
    subject_type: Optional[str] = None,
) -> Optional[int]:
    """新建账套主体(= 发票卖方)。返回新 id。name 必填,其余开票字段可空。

    subject_type=personal 时幂等:同 scope 已有在用个人主体 → 返回既有 id 不重复建
    (并发双提交 / 迁移重入安全 · DB 部分唯一索引兜底)。
    """
    if not name or not name.strip():
        return None
    stype = _norm_subject_type(subject_type)
    try:
        with db.get_cursor(commit=True) as cur:
            if stype == "personal":
                existing = _find_active_personal(cur, str(user_id), tenant_id)
                if existing:
                    return existing
            cur.execute(
                """
                INSERT INTO workspace_clients
                    (user_id, tenant_id, name, tax_id, erp_endpoint_id,
                     address, branch, phone, vat_registered, subject_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    str(user_id),
                    tenant_id,
                    name.strip()[:200],
                    (tax_id or "").strip()[:30] or None,
                    (str(erp_endpoint_id).strip() if erp_endpoint_id else None),
                    (address or "").strip()[:500] or None,
                    (branch or "").strip()[:120] or "สำนักงานใหญ่",
                    (phone or "").strip()[:50] or None,
                    bool(vat_registered),
                    stype,
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
    address: Optional[str] = None,
    branch: Optional[str] = None,
    phone: Optional[str] = None,
    vat_registered: Optional[bool] = None,
    subject_type: Optional[str] = None,
) -> bool:
    """改账套主体的开票字段(P3-客户管理页编辑用)。tenant 隔离。

    只更新传入的字段(None=不动)。name 给空串视为不改(账套主体名不能清空)。
    subject_type 留作个人→企业升级入口(传入即归一后更新)。
    """
    sets: list = []
    params: list = []
    if name is not None and name.strip():
        sets.append("name = %s")
        params.append(name.strip()[:200])
    if subject_type is not None:
        sets.append("subject_type = %s")
        params.append(_norm_subject_type(subject_type))
    if tax_id is not None:
        sets.append("tax_id = %s")
        params.append((tax_id or "").strip()[:30] or None)
    if address is not None:
        sets.append("address = %s")
        params.append((address or "").strip()[:500] or None)
    if branch is not None:
        sets.append("branch = %s")
        params.append((branch or "").strip()[:120] or "สำนักงานใหญ่")
    if phone is not None:
        sets.append("phone = %s")
        params.append((phone or "").strip()[:50] or None)
    if vat_registered is not None:
        sets.append("vat_registered = %s")
        params.append(bool(vat_registered))
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


# ============================================================
# P1a · seller 路由记忆(seller_tax/seller_name → workspace_client)
# 用户给未匹配卖方绑定一次 → 记住 → 下次自动命中(Zihao 2026-05-26)。
# 独立表 · 不污染 workspace_clients.tax_id(一个 workspace 可多卖方抬头/名字变体)。
# ============================================================
