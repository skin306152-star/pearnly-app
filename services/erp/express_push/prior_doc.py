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

# 小助手从这个版本起【销项和进项都】认 prior_docnum(1.1.47 只装了销项)。
# 比它旧的版本会把这个键当未知字段忽略 —— 闸静默不存在,而云端以为自己受保护了。
# 小助手是手动发版的,客户机上跑旧版是常态,故这里必须能看出来。
GUARD_MIN_COMPANION = (1, 1, 48)


def _version_tuple(raw: Any) -> tuple:
    try:
        return tuple(int(x) for x in str(raw or "").strip().split("."))
    except ValueError:
        return ()


def prior_docnum(history_id: Any, tenant_id: Any = None) -> Optional[str]:
    """该单据上一次成功推送写出的 ERP 凭证号;没有则 None。只读 · 查询失败降级为 None。

    降级不阻断推送:防重单是加固,不该因为一次查库抖动就把正常推送卡死。代价是
    那一次可能建出重复单 —— 相比"所有推送都推不出去",这是可接受的取舍。

    **必须带租户作用域**:钥匙可能来自 `fields.history_id`,而 fields 是客户端经
    `PUT /api/history` 可写的口袋 —— 任一租户能塞一个别家的 history UUID,不限定租户
    就等于把别家的 ERP 凭证号读进自己的载荷。拿不到 tenant_id 就不查(fail closed):
    宁可少一道加固,不可跨租户读。

    作用域**落在 ocr_history 上而不是 erp_push_logs 上**:生产实测 `insert_push_log`
    从来不写 `erp_push_logs.tenant_id`(109 行里只有 9 行有,全靠 user_id),按它过滤等于
    这道闸恒查不到、静默失效。而要回答的信任问题本来就是「这个 history_id 是不是我的」——
    `ocr_history.tenant_id` 才是那个事实(945/991),join 上去既安全又不误杀。
    """
    hid = str(history_id or "").strip()
    tid = str(tenant_id or "").strip()
    if not hid or not tid:
        return None
    try:
        from core import db

        with db.get_cursor_rls(tenant_id=tid) as cur:
            cur.execute(
                """
                SELECT l.response_body
                FROM erp_push_logs l
                JOIN ocr_history h ON h.id = l.history_id
                WHERE l.history_id = %s AND h.tenant_id = %s AND l.status = 'success'
                ORDER BY l.created_at DESC, l.id DESC
                LIMIT 1
                """,
                (hid, tid),
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

    租户来自 history(服务端查出来的记录),不从 fields 取 —— fields 里的东西客户端可写,
    让它自己指定要查哪个租户等于没有作用域。
    """
    key = str((fields or {}).get("history_id") or "").strip() or (history or {}).get("id")
    doc = prior_docnum(key, (history or {}).get("tenant_id"))
    if doc:
        payload["prior_docnum"] = doc
    return payload
