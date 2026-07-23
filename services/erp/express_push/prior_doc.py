# -*- coding: utf-8 -*-
"""重推时把「上一版写进 ERP 的凭证号」带给小助手,供其防重单。

小助手既有的幂等按 YOUREF(票面号)+ 客户码 认。但复核流程的主要目的之一就是
**纠正错票号** —— 号一改,幂等就认不出来:旧单还躺在 Express 里,新单再建一张,
一张票记两遍账。

故这里按 history_id 回查该记录上一次成功推送写出的 DOCNUM,随载荷带下去;小助手
查它还在不在账里,还在就拒绝并说清要先删哪一张(见 dbf_sales.ERR_PRIOR_DOC_EXISTS)。

查不到就不带这个键 —— 首次推送本就没有上一版,带个空串反而会让老版本小助手困惑。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def prior_docnum(history_id: Any) -> Optional[str]:
    """该单据上一次成功推送写出的 ERP 凭证号;没有则 None。只读 · 查询失败降级为 None。

    降级不阻断推送:防重单是加固,不该因为一次查库抖动就把正常推送卡死。代价是
    那一次可能建出重复单 —— 相比"所有推送都推不出去",这是可接受的取舍。
    """
    hid = str(history_id or "").strip()
    if not hid:
        return None
    try:
        from core import db

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT response_body
                FROM erp_push_logs
                WHERE history_id = %s AND status = 'success'
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (hid,),
            )
            row = cur.fetchone()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"prior_docnum lookup failed (hid={hid}): {e}")
        return None
    if not row:
        return None

    from services.erp.external_ref import _coerce_body

    body = _coerce_body(dict(row).get("response_body"))
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    doc = str(body.get("express_docnum") or meta.get("docnum") or "").strip()
    return doc or None


def attach_prior_docnum(payload: Dict[str, Any], history: Dict[str, Any]) -> Dict[str, Any]:
    """原地给载荷补 prior_docnum(有才补)。两个 mapper 共用,逻辑不两处复制。"""
    doc = prior_docnum((history or {}).get("id"))
    if doc:
        payload["prior_docnum"] = doc
    return payload
