# -*- coding: utf-8 -*-
"""做账 → 报税挂点(docs/tax-filing/04 seam):close-period 完成 → 本期税表草稿。

铁规矩同 accounting.hooks:结账主路径不能因报税生成失败而失败。SAVEPOINT 隔离 +
全异常吞(只告警);失败兜底 = 用户在报税中心手动「重算本月」。
"""

from __future__ import annotations

import logging

logger = logging.getLogger("mr-pilot")


def enqueue_generate(cur, *, tenant_id: str, workspace_client_id, period: str) -> None:
    """结账事务内调(与结账同 commit)。失败静默吞 + 告警,结账照常。"""
    if not tenant_id or not workspace_client_id:
        return
    try:
        cur.execute("SAVEPOINT tax_enqueue")
    except Exception as e:
        logger.warning(f"tax enqueue savepoint failed: {e}")
        return
    try:
        from services.tax import filings

        filings.generate_filings(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=int(workspace_client_id),
            period=period,
        )
        cur.execute("RELEASE SAVEPOINT tax_enqueue")
    except Exception as e:
        logger.warning(f"tax enqueue failed period={period}: {e}")
        try:
            cur.execute("ROLLBACK TO SAVEPOINT tax_enqueue")
        except Exception:
            pass
