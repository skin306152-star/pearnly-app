# -*- coding: utf-8 -*-
"""ERP 产品/货品映射 DAL(REFACTOR-WA-B1 · 2026-05-29 从 erp/mappings_store 抽出 · 纯搬家 0 逻辑改)

产品名归一(_product_name_norm_for_db)+ 产品映射 CRUD(list/upsert/delete)+ 批量查
(find_erp_product_mappings_batch · 推送时批量解析货品)。组内自洽(只依赖 db)·
mappings_store 顶部 re-import 当 facade · db.X/store.X/本模块.X 单一对象不变。
"""

import logging
from typing import Optional, Dict, Any, List  # noqa: F401

logger = logging.getLogger(__name__)


def _product_name_norm_for_db(s):
    """v27.8.1.17 · 商品名归一化(给数据库 unique key 用)· 小写 + 去空白标点
    跟 app.py 的 _normalize_buyer_name 同理 · 这里不调用避免循环引用
    """
    if not s:
        return ""
    import re as _re

    out = _re.sub(r"[\s\.,\-_/\\()&\"'`*]+", "", str(s))
    return out.lower().strip()[:256]


def list_erp_product_mappings(tenant_id, erp_type=None):
    """列商品映射(全部 / 单 ERP 类型)"""
    if not tenant_id:
        return []
    try:
        with db.get_cursor() as cur:
            if erp_type:
                cur.execute(
                    """
                    SELECT id, tenant_id, erp_type, item_name, erp_code, erp_name, notes,
                           created_by, created_at, updated_at
                    FROM erp_product_mappings
                    WHERE tenant_id = %s AND erp_type = %s
                    ORDER BY created_at DESC
                """,
                    (str(tenant_id), erp_type.strip().lower()),
                )
            else:
                cur.execute(
                    """
                    SELECT id, tenant_id, erp_type, item_name, erp_code, erp_name, notes,
                           created_by, created_at, updated_at
                    FROM erp_product_mappings
                    WHERE tenant_id = %s
                    ORDER BY erp_type, created_at DESC
                """,
                    (str(tenant_id),),
                )
            return cur.fetchall() or []
    except Exception as e:
        logger.error(f"list_erp_product_mappings failed: {e}")
        return []


def upsert_erp_product_mapping(tenant_id, erp_type, item_name, erp_code, erp_name, notes, user_id):
    """加/更新商品映射 · 同 (tenant, erp_type, item_name_norm) 覆盖"""
    if not tenant_id or not erp_type or not item_name or not erp_code:
        return None
    # 校验常量单一来源在 mappings_store(本模块由它 facade re-import · lazy 解循环)
    from services.erp.mappings_store import ERP_TYPES_VALID

    erp_type = (erp_type or "").strip().lower()
    if erp_type not in ERP_TYPES_VALID:
        return None
    item_name = (item_name or "").strip()[:512]
    item_name_norm = _product_name_norm_for_db(item_name)
    if not item_name_norm:
        return None
    erp_code_clean = (erp_code or "").strip()[:128]
    if not erp_code_clean:
        return None
    erp_name_clean = (erp_name or "").strip()[:256] if erp_name else None
    notes_clean = (notes or "").strip()[:500]
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO erp_product_mappings
                    (tenant_id, erp_type, item_name, item_name_norm, erp_code, erp_name, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, erp_type, item_name_norm)
                DO UPDATE SET
                    item_name = EXCLUDED.item_name,
                    erp_code = EXCLUDED.erp_code,
                    erp_name = EXCLUDED.erp_name,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id
            """,
                (
                    str(tenant_id),
                    erp_type,
                    item_name,
                    item_name_norm,
                    erp_code_clean,
                    erp_name_clean,
                    notes_clean,
                    str(user_id) if user_id else None,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_erp_product_mapping failed: {e}")
        return None


def delete_erp_product_mapping(tenant_id, mapping_id):
    if not tenant_id or not mapping_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_product_mappings WHERE id = %s AND tenant_id = %s",
                (str(mapping_id), str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_erp_product_mapping failed: {e}")
        return False


def find_erp_product_mappings_batch(tenant_id, erp_type, item_names):
    """v27.8.1.17 · 批量查多个 item_name 的映射状态(推送前预检 / 自动注入用)
    返回:dict[item_name_norm → {erp_code, erp_name, item_name}]
    """
    if not tenant_id or not erp_type or not item_names:
        return {}
    erp_type = (erp_type or "").strip().lower()
    norms = []
    for n in item_names:
        nm = _product_name_norm_for_db(n)
        if nm:
            norms.append(nm)
    if not norms:
        return {}
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT item_name, item_name_norm, erp_code, erp_name
                FROM erp_product_mappings
                WHERE tenant_id = %s AND erp_type = %s AND item_name_norm = ANY(%s)
            """,
                (str(tenant_id), erp_type, norms),
            )
            rows = cur.fetchall() or []
            out = {}
            for r in rows:
                out[r["item_name_norm"]] = {
                    "erp_code": r["erp_code"],
                    "erp_name": r["erp_name"] or "",
                    "item_name": r["item_name"],
                }
            return out
    except Exception as e:
        logger.error(f"find_erp_product_mappings_batch failed: {e}")
        return {}


from core import db  # noqa: E402
