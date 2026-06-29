# -*- coding: utf-8 -*-
"""客户实体(clients)+ 供应商分类记忆(supplier_categories)+ 买家→客户映射
(buyer_to_client_memory)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
会计/事务所给多家公司做账 · 把每张发票归属到客户(clients CRUD)·
供应商→科目分类记忆 · 买家名/税号→Pearnly 客户的学习与解析(try_resolve)。
全部按 tenant_id / user_id 隔离(tenant 隔离矩阵)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

from core import db

# facade re-export(REFACTOR-WA-B1 · 买家解析实现下沉 buyer_resolve · db.X/store.X 单一对象不变)
from services.clients.buyer_resolve import (  # noqa: F401,E402
    ensure_buyer_to_client_table,
    learn_buyer_to_client,
    try_resolve_buyer_to_client,
    _buyer_candidates_conflict,
    resolve_or_create_buyer_client,
    update_history_client_id,
)

logger = logging.getLogger(__name__)


def ensure_clients_table():
    """启动时建客户表 · 加 client_id 列到 ocr_history · 幂等"""
    try:
        with db.get_cursor(commit=True) as cur:
            # 1. 客户表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    name TEXT NOT NULL,
                    short_name TEXT,
                    tax_id TEXT,
                    address TEXT,
                    contact_person TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    notes TEXT,
                    color TEXT DEFAULT '#3b82f6',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_clients_user ON clients(user_id, is_active);
                CREATE INDEX IF NOT EXISTS idx_clients_tenant ON clients(tenant_id, is_active);
                CREATE INDEX IF NOT EXISTS idx_clients_tax_id ON clients(tax_id) WHERE tax_id IS NOT NULL;
            """)
            # 2. ocr_history 加 client_id 字段 + ai_raw 留底(反馈闭环 ②:首存基线·永不改·算用户修正 diff)
            #    + 官方名核验 ③(并存:保留 AI 名·另存税局 RD 官方抬头 + 已核验标·记账/推送优先用官方名)
            cur.execute("""
                ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS client_id BIGINT;
                CREATE INDEX IF NOT EXISTS idx_ocr_history_client ON ocr_history(client_id) WHERE client_id IS NOT NULL;
                ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS ai_raw JSONB;
                ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS seller_name_official TEXT;
                ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS seller_name_verified BOOLEAN NOT NULL DEFAULT FALSE;
            """)
            # B8 RLS wave3:两表都含 tenant_id + user_id → tenant_or_user 隔离。
            # force=False(owner 仍绕过→外围未迁的裸 get_cursor 不破);业务连接 SET ROLE 后强制。
            from core.rls import apply_tenant_or_user_rls

            apply_tenant_or_user_rls(cur, "clients", "ocr_history")
            logger.info("✅ clients 表 + ocr_history.client_id + RLS policy 已就绪")
    except Exception as e:
        logger.error(f"ensure_clients_table failed: {e}")


# ============================================================
# v118.18 · 推荐分类「学习」表 · 用户给某供应商打了分类后系统记忆 · 下次自动建议
# 唯一性:同 tenant(或孤立用户)下 · 同 seller_name 只有 1 条
# ============================================================


def ensure_supplier_categories_table():
    """启动时建表 · 幂等"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS supplier_categories (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id UUID,
                    user_id UUID NOT NULL,
                    seller_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    use_count INTEGER NOT NULL DEFAULT 1,
                    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_supcat_unique
                    ON supplier_categories (COALESCE(tenant_id::text, user_id::text), LOWER(seller_name));
                CREATE INDEX IF NOT EXISTS idx_supcat_tenant ON supplier_categories(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_supcat_user ON supplier_categories(user_id);
            """)
            from core.rls import apply_tenant_or_user_rls

            apply_tenant_or_user_rls(cur, "supplier_categories")
            logger.info("✅ supplier_categories 表 + tenant_or_user RLS policy 已就绪")
    except Exception as e:
        logger.error(f"ensure_supplier_categories_table failed: {e}")


def get_category_for_seller(
    seller_name: Optional[str], user_id: str, tenant_id: Optional[str] = None
) -> Optional[str]:
    """识别时调:查同 seller 之前用过的 category(同 tenant 共享 · 否则查自己)"""
    if not seller_name or not seller_name.strip():
        return None
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user_id)) as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT category FROM supplier_categories
                    WHERE tenant_id = %s AND LOWER(seller_name) = LOWER(%s)
                    ORDER BY last_used_at DESC LIMIT 1
                """,
                    (tenant_id, seller_name.strip()),
                )
            else:
                cur.execute(
                    """
                    SELECT category FROM supplier_categories
                    WHERE user_id = %s AND tenant_id IS NULL AND LOWER(seller_name) = LOWER(%s)
                    ORDER BY last_used_at DESC LIMIT 1
                """,
                    (str(user_id), seller_name.strip()),
                )
            r = cur.fetchone()
            return r["category"] if r else None
    except Exception as e:
        logger.warning(f"get_category_for_seller failed: {e}")
        return None


def upsert_supplier_category(
    seller_name: Optional[str],
    category: Optional[str],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """保存编辑时调:记忆这个映射 · 已存在则更新 use_count 和 category"""
    if not seller_name or not seller_name.strip():
        return False
    if not category or not category.strip():
        return False
    s = seller_name.strip()[:200]
    c = category.strip()[:80]
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user_id), commit=True) as cur:
            # 用 ON CONFLICT 利用 unique index
            if tenant_id:
                cur.execute(
                    """
                    INSERT INTO supplier_categories (tenant_id, user_id, seller_name, category)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (COALESCE(tenant_id::text, user_id::text), LOWER(seller_name))
                    DO UPDATE SET category = EXCLUDED.category,
                                  use_count = supplier_categories.use_count + 1,
                                  last_used_at = NOW()
                """,
                    (tenant_id, str(user_id), s, c),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO supplier_categories (tenant_id, user_id, seller_name, category)
                    VALUES (NULL, %s, %s, %s)
                    ON CONFLICT (COALESCE(tenant_id::text, user_id::text), LOWER(seller_name))
                    DO UPDATE SET category = EXCLUDED.category,
                                  use_count = supplier_categories.use_count + 1,
                                  last_used_at = NOW()
                """,
                    (str(user_id), s, c),
                )
            return True
    except Exception as e:
        logger.warning(f"upsert_supplier_category failed: {e}")
        return False


def list_used_categories(
    user_id: str, tenant_id: Optional[str] = None, limit: int = 30
) -> List[str]:
    """列出用户/tenant 用过的所有 category(去重 · 按使用次数倒序)· 给前端 datalist 自动补全"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user_id)) as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT category, SUM(use_count) AS total FROM supplier_categories
                    WHERE tenant_id = %s
                    GROUP BY category ORDER BY total DESC LIMIT %s
                """,
                    (tenant_id, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT category, SUM(use_count) AS total FROM supplier_categories
                    WHERE user_id = %s AND tenant_id IS NULL
                    GROUP BY category ORDER BY total DESC LIMIT %s
                """,
                    (str(user_id), limit),
                )
            return [r["category"] for r in cur.fetchall()]
    except Exception as e:
        logger.warning(f"list_used_categories failed: {e}")
        return []


def count_supplier_mappings(user_id: str, tenant_id: Optional[str] = None) -> int:
    """统计已记忆的供应商→科目映射数量(给前端 '已记住 N 个供应商' 提示)"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user_id)) as cur:
            if tenant_id:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM supplier_categories WHERE tenant_id = %s",
                    (tenant_id,),
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM supplier_categories WHERE user_id = %s AND tenant_id IS NULL",
                    (str(user_id),),
                )
            r = cur.fetchone()
            return int(r["n"]) if r else 0
    except Exception:
        return 0


def list_clients(
    user_id: str, include_inactive: bool = False, tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """列出某用户的所有客户(按名字排序)
    v118.15 · tenant_id 给了 → 同 tenant 共享(老板员工看到同一份客户档案)
    """
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            if tenant_id:
                where = "user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
                params = [tenant_id]
            else:
                where = "user_id = %s"
                params = [user_id]
            if not include_inactive:
                where += " AND is_active = TRUE"
            cur.execute(
                f"""
                SELECT c.*,
                    (SELECT COUNT(*) FROM ocr_history WHERE client_id = c.id) AS invoice_count,
                    (SELECT COALESCE(SUM(total_amount), 0) FROM ocr_history 
                     WHERE client_id = c.id AND total_amount IS NOT NULL) AS total_amount,
                    (SELECT MAX(created_at) FROM ocr_history WHERE client_id = c.id) AS last_invoice_at
                FROM clients c
                WHERE {where}
                ORDER BY c.is_active DESC, c.name ASC
            """,
                params,
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_clients failed: {e}")
        return []


def get_client(
    user_id: str, client_id: int, tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """获取单个客户
    v118.15 · tenant_id 给了 → 同 tenant 任意成员可查
    """
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT * FROM clients WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                """,
                    (client_id, tenant_id),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM clients WHERE id = %s AND user_id = %s
                """,
                    (client_id, user_id),
                )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_client failed: {e}")
        return None


def create_client(user_id: str, tenant_id: Optional[str], name: str, **kwargs) -> Optional[int]:
    """创建客户 · 返回新 ID"""
    if not name or not name.strip():
        return None
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            cur.execute(
                """
                INSERT INTO clients (user_id, tenant_id, name, short_name, tax_id,
                    address, contact_person, contact_phone, contact_email, notes, color,
                    party_type, branch, promptpay_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    user_id,
                    tenant_id,
                    name.strip()[:200],
                    (kwargs.get("short_name") or "").strip()[:80] or None,
                    (kwargs.get("tax_id") or "").strip()[:20] or None,
                    (kwargs.get("address") or "").strip()[:500] or None,
                    (kwargs.get("contact_person") or "").strip()[:100] or None,
                    (kwargs.get("contact_phone") or "").strip()[:50] or None,
                    (kwargs.get("contact_email") or "").strip()[:200] or None,
                    (kwargs.get("notes") or "").strip()[:1000] or None,
                    kwargs.get("color") or "#3b82f6",
                    # 买方目录字段(docs/16 §N · 向导预填买方块):类型/分店/PromptPay。
                    (kwargs.get("party_type") or "").strip()[:20] or None,
                    (kwargs.get("branch") or "").strip()[:120] or None,
                    (kwargs.get("promptpay_id") or "").strip()[:40] or None,
                ),
            )
            return cur.fetchone()["id"]
    except Exception as e:
        import traceback

        logger.error(f"create_client failed: {e}\n{traceback.format_exc()}")
        return None


def update_client(user_id: str, client_id: int, tenant_id: Optional[str] = None, **kwargs) -> bool:
    """更新客户信息 · 部分字段更新
    v118.15 · tenant_id 给了 → 同 tenant 任意成员可改
    """
    allowed_fields = [
        "name",
        "short_name",
        "tax_id",
        "address",
        "contact_person",
        "contact_phone",
        "contact_email",
        "notes",
        "color",
        "is_active",
        # 买方目录字段(docs/16 §N)。
        "party_type",
        "branch",
        "promptpay_id",
    ]
    updates = []
    params = []
    for k in allowed_fields:
        if k in kwargs and kwargs[k] is not None:
            updates.append(f"{k} = %s")
            v = kwargs[k]
            if isinstance(v, str):
                v = v.strip()
                # 字段长度限制
                limits = {
                    "name": 200,
                    "short_name": 80,
                    "tax_id": 20,
                    "address": 500,
                    "contact_person": 100,
                    "contact_phone": 50,
                    "contact_email": 200,
                    "notes": 1000,
                    "color": 20,
                    "party_type": 20,
                    "branch": 120,
                    "promptpay_id": 40,
                }
                if k in limits:
                    v = v[: limits[k]] or None
            params.append(v)
    if not updates:
        return False
    updates.append("updated_at = NOW()")
    if tenant_id:
        where_sql = "id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
        params.extend([client_id, tenant_id])
    else:
        where_sql = "id = %s AND user_id = %s"
        params.extend([client_id, user_id])
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            cur.execute(
                f"""
                UPDATE clients SET {', '.join(updates)}
                WHERE {where_sql}
            """,
                params,
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_client failed: {e}")
        return False


def delete_client(
    user_id: str, client_id: int, cascade_unlink: bool = True, tenant_id: Optional[str] = None
) -> bool:
    """删除客户 · 默认级联解绑发票(把发票的 client_id 置 NULL · 不删发票)
    v118.15 · tenant_id 给了 → 同 tenant 任意成员可删
    """
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            # 先解绑发票(RLS 下只解绑本租户可见的 ocr_history 行)
            if cascade_unlink:
                cur.execute(
                    """
                    UPDATE ocr_history SET client_id = NULL
                    WHERE client_id = %s
                """,
                    (client_id,),
                )
            # 再删客户
            if tenant_id:
                cur.execute(
                    """
                    DELETE FROM clients WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                """,
                    (client_id, tenant_id),
                )
            else:
                cur.execute(
                    """
                    DELETE FROM clients WHERE id = %s AND user_id = %s
                """,
                    (client_id, user_id),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_client failed: {e}")
        return False


def assign_invoice_to_client(
    user_id: str, history_id: str, client_id: Optional[int], tenant_id: Optional[str] = None
) -> bool:
    """把发票归属到客户(client_id=None 表示移除归属)
    v108.2 · history_id 是 UUID 字符串(ocr_history 主键是 UUID)
    v118.15 · tenant_id 给了 → 同 tenant 任意成员可标 · 客户和发票都按 tenant 过滤
    """
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            # 验证客户属于该用户/tenant(防越权)
            if client_id is not None:
                if tenant_id:
                    cur.execute(
                        "SELECT id FROM clients WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)",
                        (client_id, tenant_id),
                    )
                else:
                    cur.execute(
                        "SELECT id FROM clients WHERE id = %s AND user_id = %s",
                        (client_id, user_id),
                    )
                if not cur.fetchone():
                    return False
            # 更新发票归属(同样按 tenant 过滤)
            if tenant_id:
                cur.execute(
                    """
                    UPDATE ocr_history SET client_id = %s
                    WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                """,
                    (client_id, str(history_id), tenant_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE ocr_history SET client_id = %s
                    WHERE id = %s AND user_id = %s
                """,
                    (client_id, str(history_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        import traceback

        logger.error(f"assign_invoice_to_client failed: {e}\n{traceback.format_exc()}")
        return False
