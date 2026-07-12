# -*- coding: utf-8 -*-
"""coa_erp_bridge 数据访问层(T4a · 科目桥专表 · 全参数化)。

语义钉死:coa_code = 影子 coa_preset 27 科目码(非法码拒收,fail loud 不静默丢);
erp_code = GL 上传件里的实际科目码(MR.ERP 扁平 1113-01 样式)。Express 四段码不进
join 键(T4b 建桥时只当辅助资料)。游标由调用方传入(与调用方同事务,RLS 上下文随
调用方连接),本层不开连接、不吞异常。
"""

from __future__ import annotations

from typing import Iterable

from services.accounting import coa_preset
from services.erp.mappings_store import ERP_TYPES_VALID

_COA_CODES = frozenset(code for code, *_ in coa_preset.PRESET_ACCOUNTS)


def _norm_erp_type(erp_type: str) -> str:
    et = (erp_type or "").strip().lower()
    if et not in ERP_TYPES_VALID:
        raise ValueError(f"erp_type 非法: {erp_type!r}")
    return et


def load_bridge(cur, *, tenant_id: str, workspace_client_id: int, erp_type: str) -> dict[str, str]:
    """{coa_code: erp_code} 桥。无行 → 空桥(调用方如实 unmapped 降级,不臆造)。"""
    cur.execute(
        "SELECT coa_code, erp_code FROM coa_erp_bridge "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND erp_type = %s",
        (str(tenant_id), int(workspace_client_id), _norm_erp_type(erp_type)),
    )
    rows = cur.fetchall() or []
    return {
        (r["coa_code"] if isinstance(r, dict) else r[0]): (
            r["erp_code"] if isinstance(r, dict) else r[1]
        )
        for r in rows
    }


def list_erp_types(cur, *, tenant_id: str, workspace_client_id: int) -> list[str]:
    """本账套已配桥的 erp_type 全集(去重有序)。工单不带 erp_type,消费方据此判归属。"""
    cur.execute(
        "SELECT DISTINCT erp_type FROM coa_erp_bridge "
        "WHERE tenant_id = %s AND workspace_client_id = %s ORDER BY erp_type",
        (str(tenant_id), int(workspace_client_id)),
    )
    return [(r["erp_type"] if isinstance(r, dict) else r[0]) for r in (cur.fetchall() or [])]


def upsert_rows(
    cur, *, tenant_id: str, workspace_client_id: int, erp_type: str, rows: Iterable[dict]
) -> int:
    """批量 upsert 桥行,返回写入行数。同 (tenant, 账套, erp_type, coa_code) 覆盖(幂等)。

    rows 元素:{coa_code, erp_code, erp_name?, match_source?}。coa_code 必须是 coa_preset
    科目码、erp_code 非空——违约抛 ValueError(建桥数据错在入口就炸,不落脏行)。
    """
    et = _norm_erp_type(erp_type)
    count = 0
    for row in rows:
        coa = str(row.get("coa_code") or "").strip()
        erp = str(row.get("erp_code") or "").strip()[:128]
        if coa not in _COA_CODES:
            raise ValueError(f"coa_code 非 coa_preset 科目码: {coa!r}")
        if not erp:
            raise ValueError(f"erp_code 为空: coa_code={coa}")
        cur.execute(
            "INSERT INTO coa_erp_bridge "
            "(tenant_id, workspace_client_id, erp_type, coa_code, erp_code, erp_name, "
            " match_source) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, workspace_client_id, erp_type, coa_code) DO UPDATE SET "
            "erp_code = EXCLUDED.erp_code, erp_name = EXCLUDED.erp_name, "
            "match_source = EXCLUDED.match_source, updated_at = NOW()",
            (
                str(tenant_id),
                int(workspace_client_id),
                et,
                coa,
                erp,
                str(row.get("erp_name") or "").strip()[:200],
                str(row.get("match_source") or "manual").strip()[:32],
            ),
        )
        count += 1
    return count


def delete_row(
    cur, *, tenant_id: str, workspace_client_id: int, erp_type: str, coa_code: str
) -> bool:
    """删一条桥行,返回是否真删到。"""
    cur.execute(
        "DELETE FROM coa_erp_bridge WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND erp_type = %s AND coa_code = %s",
        (str(tenant_id), int(workspace_client_id), _norm_erp_type(erp_type), str(coa_code)),
    )
    return cur.rowcount > 0
