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

# 小助手从这个版本起认 prior_docnum(见 companion/dbf_sales.ERR_PRIOR_DOC_EXISTS)。
# 比它旧的版本会把这个键当未知字段忽略 —— 闸静默不存在,而云端以为自己受保护了。
# 小助手是手动发版的,客户机上跑旧版是常态,故这里必须能看出来。
GUARD_MIN_COMPANION = (1, 1, 47)


def _version_tuple(raw: Any) -> tuple:
    try:
        return tuple(int(x) for x in str(raw or "").strip().split("."))
    except ValueError:
        return ()


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
    if not doc:
        return None
    # 上一版是哪个小助手写的 —— 同一台机器多半还是它。版本不够就明着喊,别让"闸不存在"
    # 静默发生:旧版忽略 prior_docnum 后照样建单,重复单要到对账时才暴露。
    ver = _version_tuple(meta.get("companion_version"))
    if ver and ver < GUARD_MIN_COMPANION:
        logger.warning(
            "防重单闸可能不生效:上一版 %s 由小助手 %s 写出,该版本不认 prior_docnum"
            "(需 >= %s)。重推若未先删旧单会产生重复单。",
            doc,
            meta.get("companion_version"),
            ".".join(str(x) for x in GUARD_MIN_COMPANION),
        )
    return doc


def attach_prior_docnum(
    payload: Dict[str, Any],
    history: Dict[str, Any],
    fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """原地给载荷补 prior_docnum(有才补)。两个 mapper 共用,逻辑不两处复制。

    钥匙优先用 fields.history_id ——【这条是闸能不能生效的关键】:会计改完表格回导时,
    收料口会为上传的工作簿新建一条 history 记录,拿新 id 去查上一版必然查不到,闸就正好
    在它该生效的场景下哑火。回导解析器从行键里带回的原 history_id 才指向真正的上一版。
    """
    key = str((fields or {}).get("history_id") or "").strip() or (history or {}).get("id")
    doc = prior_docnum(key)
    if doc:
        payload["prior_docnum"] = doc
    return payload
