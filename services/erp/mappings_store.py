# -*- coding: utf-8 -*-
"""ERP 映射底座(客户 / 科目 / 税码 / 商品 4 类映射)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
3+1 张映射表 CRUD + 校验常量(ERP_TYPES_VALID / PEARNLY_TAX_KINDS_VALID)+
商品名归一化私有 helper(_product_name_norm_for_db)。
db.py 文件尾 re-export 对外函数 · 所有 `db.xxx()` 调用点不变。
"""

import logging

from core import db

# facade re-export(REFACTOR-WA-B1 · 产品映射实现下沉 product_mappings_store · db.X/store.X 单一对象不变)
from services.erp.product_mappings_store import (  # noqa: F401,E402
    _product_name_norm_for_db,
    list_erp_product_mappings,
    upsert_erp_product_mapping,
    delete_erp_product_mapping,
    find_erp_product_mappings_batch,
)

logger = logging.getLogger(__name__)


ERP_TYPES_VALID = {"flowaccount", "peak", "xero", "quickbooks", "express", "mrerp"}
PEARNLY_TAX_KINDS_VALID = {
    "vat_7",
    "vat_0",
    "vat_exempt",
    "wht_1",
    "wht_3",
    "wht_5",
    "non_vat",
}


def ensure_erp_mapping_tables():
    """v118.27.0 · ERP 映射底座 3 张表 · 启动时幂等建"""
    try:
        with db.get_cursor(commit=True) as cur:
            # ── 客户映射(Pearnly client_id → ERP customer 编号 · 按 erp_type 区分)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_client_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    erp_code VARCHAR(128) NOT NULL,
                    notes TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, client_id, erp_type)
                );
                CREATE INDEX IF NOT EXISTS idx_erp_cli_map_tenant ON erp_client_mappings(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_erp_cli_map_client ON erp_client_mappings(client_id);
                CREATE INDEX IF NOT EXISTS idx_erp_cli_map_erp ON erp_client_mappings(erp_type);
            """)
            # ── 科目映射(Pearnly category → ERP GL code · tenant 共享)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_account_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    pearnly_category VARCHAR(64) NOT NULL,
                    erp_code VARCHAR(128) NOT NULL,
                    erp_name TEXT,
                    notes TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, erp_type, pearnly_category)
                );
                CREATE INDEX IF NOT EXISTS idx_erp_acc_map_tenant ON erp_account_mappings(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_erp_acc_map_erp ON erp_account_mappings(erp_type);
            """)
            # ── 税码映射(Pearnly tax_kind → ERP tax_code · tenant 共享)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_tax_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    pearnly_tax_kind VARCHAR(32) NOT NULL,
                    erp_code VARCHAR(64) NOT NULL,
                    notes TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, erp_type, pearnly_tax_kind)
                );
                CREATE INDEX IF NOT EXISTS idx_erp_tax_map_tenant ON erp_tax_mappings(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_erp_tax_map_erp ON erp_tax_mappings(erp_type);
            """)
            # ── v27.8.1.17 · 商品映射(OCR item_name → ERP product code · tenant 级)
            # key 是 OCR 抽到的明细行 name(归一化前)· 用 norm 字段建索引方便查
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_product_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    item_name_norm VARCHAR(256) NOT NULL,
                    erp_code VARCHAR(128) NOT NULL,
                    erp_name TEXT,
                    notes TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, erp_type, item_name_norm)
                );
                CREATE INDEX IF NOT EXISTS idx_erp_prod_map_tenant ON erp_product_mappings(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_erp_prod_map_erp ON erp_product_mappings(erp_type);
                CREATE INDEX IF NOT EXISTS idx_erp_prod_map_norm ON erp_product_mappings(tenant_id, erp_type, item_name_norm);
            """)
            # B8 RLS wave4:4 张映射表均 tenant_id NOT NULL(无 user_id 列)→ 纯 tenant 隔离。
            # force=False(owner 仍绕过→DDL/未迁裸 get_cursor 不破);业务连接 SET ROLE 后强制。
            from core.rls import apply_tenant_rls

            apply_tenant_rls(
                cur,
                "erp_client_mappings",
                "erp_account_mappings",
                "erp_tax_mappings",
                "erp_product_mappings",
            )
            logger.info("✅ v118.27.0 · erp 4 张映射表 + RLS policy 已就绪")
    except Exception as e:
        logger.error(f"ensure_erp_mapping_tables failed: {e}")


# ─── 客户映射 CRUD(接 client_assignments filter)──────────────
def list_erp_client_mappings(tenant_id, restrict_client_ids=None):
    """列客户映射
    - restrict_client_ids=None → 不限制(老板/超管)
    - restrict_client_ids=[...] → 只看分配给员工的客户
    - restrict_client_ids=[]   → 没分配 → 空列表
    """
    if not tenant_id:
        return []
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id)) as cur:
            sql = """
                SELECT m.id, m.tenant_id, m.client_id, m.erp_type, m.erp_code,
                       m.notes, m.created_at, m.updated_at,
                       c.name AS client_name
                FROM erp_client_mappings m
                JOIN clients c ON c.id = m.client_id
                WHERE m.tenant_id = %s
            """
            params = [str(tenant_id)]
            if restrict_client_ids is not None:
                if not restrict_client_ids:
                    return []
                sql += " AND m.client_id = ANY(%s)"
                params.append([int(x) for x in restrict_client_ids])
            sql += " ORDER BY c.name ASC, m.erp_type ASC"
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_erp_client_mappings failed: {e}")
        return []


def upsert_erp_client_mapping(tenant_id, client_id, erp_type, erp_code, notes, user_id):
    """加/更新客户映射 · 校验 client_id 属于 tenant · 同 (tenant, client, erp_type) 覆盖"""
    if not tenant_id or not client_id or not erp_type or not erp_code:
        return None
    erp_type = (erp_type or "").strip().lower()
    if erp_type not in ERP_TYPES_VALID:
        return None
    erp_code = (erp_code or "").strip()[:128]
    if not erp_code:
        return None
    notes_clean = (notes or "").strip()[:500]
    try:
        with db.get_cursor_rls(
            tenant_id=str(tenant_id), user_id=str(user_id) if user_id else None, commit=True
        ) as cur:
            # 校验 client 属于 tenant
            cur.execute(
                """
                SELECT 1 FROM clients c
                JOIN users u ON u.id = c.user_id
                WHERE c.id = %s AND u.tenant_id = %s
            """,
                (int(client_id), str(tenant_id)),
            )
            if not cur.fetchone():
                return None
            cur.execute(
                """
                INSERT INTO erp_client_mappings
                    (tenant_id, client_id, erp_type, erp_code, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, client_id, erp_type)
                DO UPDATE SET
                    erp_code = EXCLUDED.erp_code,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id
            """,
                (
                    str(tenant_id),
                    int(client_id),
                    erp_type,
                    erp_code,
                    notes_clean,
                    str(user_id) if user_id else None,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_erp_client_mapping failed: {e}")
        return None


def delete_erp_client_mapping(tenant_id, mapping_id):
    if not tenant_id or not mapping_id:
        return False
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_client_mappings WHERE id = %s AND tenant_id = %s",
                (str(mapping_id), str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_client_mapping failed: {e}")
        return False


# ─── 科目映射 CRUD(tenant 共享 · 不接 client_assignments)─────
def list_erp_account_mappings(tenant_id):
    if not tenant_id:
        return []
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id)) as cur:
            cur.execute(
                """
                SELECT id, tenant_id, erp_type, pearnly_category, erp_code,
                       erp_name, notes, created_at, updated_at
                FROM erp_account_mappings
                WHERE tenant_id = %s
                ORDER BY erp_type ASC, pearnly_category ASC
            """,
                (str(tenant_id),),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_erp_account_mappings failed: {e}")
        return []


def upsert_erp_account_mapping(
    tenant_id, erp_type, pearnly_category, erp_code, erp_name, notes, user_id
):
    if not tenant_id or not erp_type or not pearnly_category or not erp_code:
        return None
    erp_type = (erp_type or "").strip().lower()
    if erp_type not in ERP_TYPES_VALID:
        return None
    cat = (pearnly_category or "").strip()[:64]
    code = (erp_code or "").strip()[:128]
    if not cat or not code:
        return None
    name_clean = (erp_name or "").strip()[:200]
    notes_clean = (notes or "").strip()[:500]
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                """
                INSERT INTO erp_account_mappings
                    (tenant_id, erp_type, pearnly_category, erp_code, erp_name, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, erp_type, pearnly_category)
                DO UPDATE SET
                    erp_code = EXCLUDED.erp_code,
                    erp_name = EXCLUDED.erp_name,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id
            """,
                (
                    str(tenant_id),
                    erp_type,
                    cat,
                    code,
                    name_clean,
                    notes_clean,
                    str(user_id) if user_id else None,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_erp_account_mapping failed: {e}")
        return None


def delete_erp_account_mapping(tenant_id, mapping_id):
    if not tenant_id or not mapping_id:
        return False
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_account_mappings WHERE id = %s AND tenant_id = %s",
                (str(mapping_id), str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_account_mapping failed: {e}")
        return False


# ─── 税码映射 CRUD(tenant 共享)──────────────────────────
def list_erp_tax_mappings(tenant_id):
    if not tenant_id:
        return []
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id)) as cur:
            cur.execute(
                """
                SELECT id, tenant_id, erp_type, pearnly_tax_kind, erp_code,
                       notes, created_at, updated_at
                FROM erp_tax_mappings
                WHERE tenant_id = %s
                ORDER BY erp_type ASC, pearnly_tax_kind ASC
            """,
                (str(tenant_id),),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_erp_tax_mappings failed: {e}")
        return []


def upsert_erp_tax_mapping(tenant_id, erp_type, pearnly_tax_kind, erp_code, notes, user_id):
    if not tenant_id or not erp_type or not pearnly_tax_kind or not erp_code:
        return None
    erp_type = (erp_type or "").strip().lower()
    if erp_type not in ERP_TYPES_VALID:
        return None
    kind = (pearnly_tax_kind or "").strip()
    if kind not in PEARNLY_TAX_KINDS_VALID:
        return None
    code = (erp_code or "").strip()[:64]
    if not code:
        return None
    notes_clean = (notes or "").strip()[:500]
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                """
                INSERT INTO erp_tax_mappings
                    (tenant_id, erp_type, pearnly_tax_kind, erp_code, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, erp_type, pearnly_tax_kind)
                DO UPDATE SET
                    erp_code = EXCLUDED.erp_code,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id
            """,
                (
                    str(tenant_id),
                    erp_type,
                    kind,
                    code,
                    notes_clean,
                    str(user_id) if user_id else None,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_erp_tax_mapping failed: {e}")
        return None


def delete_erp_tax_mapping(tenant_id, mapping_id):
    if not tenant_id or not mapping_id:
        return False
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_tax_mappings WHERE id = %s AND tenant_id = %s",
                (str(mapping_id), str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_tax_mapping failed: {e}")
        return False


# ─── 商品映射 CRUD(v27.8.1.17 · tenant 级 · key 是 OCR item_name 的归一化形式)─


def get_mrerp_mappings_bundle(tenant_id):
    """通用 ERP 映射束 · 一次拿 4 张映射表(clients / accounts / taxes / products)
    供推送引擎使用
    """
    if not tenant_id:
        return {"clients": [], "accounts": [], "taxes": [], "products": []}
    try:
        return {
            "clients": list_erp_client_mappings(tenant_id, restrict_client_ids=None),
            "accounts": list_erp_account_mappings(tenant_id),
            "taxes": list_erp_tax_mappings(tenant_id),
            "products": list_erp_product_mappings(tenant_id),
        }
    except Exception as e:
        logger.error(f"get_mrerp_mappings_bundle failed: {e}")
        return {"clients": [], "accounts": [], "taxes": [], "products": []}
