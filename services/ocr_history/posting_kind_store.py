# -*- coding: utf-8 -*-
"""票上的「过账去向」声明 · 窄写(ocr_history.posting_kind 一列)。

单开一叶而不是塞进 mutations.py:那个文件已顶到 500 行硬线,而这一列的写入语义也确实自成
一件事 —— **声明跟着票走,不跟着推送走**(见 express_push.posting_kind 顶注)。推送四条腿
(手动 / 识别后自动 / 失败重试 / 批量分拣)都读这一列,所以会计在失败卡上补选的那一次必须
落到票上;只当本次推送的入参传,这次点通了,轮到自动重试还会 escalate。

值的合法性由调用方用 express_push.posting_kind.normalize 归一(认不出的值一律拒,绝不静默
当成 stock —— 错记库存会真扣客户库存并结转 COGS,Express 里不可逆)。这里不再判一遍:两处
各判一份就是两套口径,迟早漂。
"""

from __future__ import annotations

import logging
from typing import Optional

from core import db

logger = logging.getLogger(__name__)


def update_history_posting_kind(
    record_id: str,
    posting_kind: str,
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """把补选的过账去向写回这张票。改不到(不存在 / 不是自己租户的)返 False。

    走窄更新不走 update_ocr_history_pages:后者会触发反馈捕获并 bump edit_count,等于拿系统
    的写冒充用户改了识别结果。租户谓词显式写进 SQL 而不只靠 RLS —— 这一列决定钱怎么记,
    多一道不吃亏(镜像 seller_routing.update_history_workspace_client_id)。
    """
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            if tenant_id:
                cur.execute(
                    """
                    UPDATE ocr_history SET posting_kind = %s, updated_at = NOW()
                    WHERE id = %s::uuid
                      AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)
                    """,
                    (posting_kind, str(record_id), tenant_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE ocr_history SET posting_kind = %s, updated_at = NOW()
                    WHERE id = %s::uuid AND user_id = %s::uuid
                    """,
                    (posting_kind, str(record_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.warning(f"update_history_posting_kind failed (id={record_id}): {e}")
        return False
