# -*- coding: utf-8 -*-
"""收料口编排:一批上传 → 运输皮归一 → 落盘 → 落行 → 逐件确定性识别(万能口 F1)。

这一步【零模型、零扣费、零业务写】—— 它只是把料接住、认一认、如实登记。真正花钱/写数据的
动作要等人在回执卡上点一下(见 attach_turn),或者会计自己把动词说出口。

整批先读齐再落盘:任一件不合规 → IntakePrepError 上抛,调用方统一转 422,盘上零孤儿
(照 routes/workorder_routes.add_materials 的两段式,同一条 413 孤儿修的理由)。

HEIC 的留证原件不收:workorder 那边收是因为工单是档案面;对话附件是临时件,收一个没有行的
文件进来,到期清理(靠行定位文件)就永远扫不到它 —— 那才是真漏。转出来的 JPEG 照收。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from services.steward import attach_kinds, attachments
from services.workorder import intake_prep

logger = logging.getLogger(__name__)

ERR_TOO_MANY = "steward.attachment_too_many"
ERR_TOO_LARGE = "steward.attachment_too_large"
ERR_BATCH_TOO_LARGE = "steward.attachment_batch_too_large"
# 解包后才发现超限的那两条要单出码:她手上只有一个压缩包,「先送出一批再传下一批」这句话
# 她没法执行 —— 得告诉她拆的是 zip。intake_prep 的 zip 预算(200 件/200MB)按工单档案面
# 定,收窄它会连坐收料口,故在这一层用自己的口径说话。
ERR_ZIP_TOO_MANY = "steward.attachment_zip_too_many"
ERR_ZIP_TOO_LARGE = "steward.attachment_zip_too_large"

_PLAIN_CODES = (ERR_TOO_MANY, ERR_TOO_LARGE, ERR_BATCH_TOO_LARGE)
_ZIP_CODES = (ERR_ZIP_TOO_MANY, ERR_TOO_LARGE, ERR_ZIP_TOO_LARGE)


class AttachmentLimitError(Exception):
    """超限:code + 上限值(路由转 413,前端在【选文件的当下】就按同一份上限先拒一次)。"""

    def __init__(self, code: str, limit: int, actual: int):
        self.code = code
        self.limit = limit
        self.actual = actual
        super().__init__(code)


def check_limits(pairs: list[tuple[str, bytes]], *, codes: tuple = _PLAIN_CODES) -> None:
    """件数 / 单件 / 单批总量三道闸。上限单一事实源在 attachments,前端从 /status 读同一份。
    codes 只换说法不换上限:同一道闸,料是拖进来的还是从 zip 里解出来的,人要做的事不一样。"""
    too_many, too_large, batch_too_large = codes
    if len(pairs) > attachments.MAX_FILES_PER_MESSAGE:
        raise AttachmentLimitError(too_many, attachments.MAX_FILES_PER_MESSAGE, len(pairs))
    total = 0
    for _name, content in pairs:
        size = len(content or b"")
        if size > attachments.MAX_FILE_BYTES:
            raise AttachmentLimitError(too_large, attachments.MAX_FILE_BYTES, size)
        total += size
    if total > attachments.MAX_BATCH_BYTES:
        raise AttachmentLimitError(batch_too_large, attachments.MAX_BATCH_BYTES, total)


def accept(
    *,
    user: dict,
    tenant_id: str,
    session_id: str,
    pairs: list[tuple[str, bytes]],
    password: Optional[str] = None,
) -> list[dict[str, Any]]:
    """一批上传 → 已登记的附件视图(前端 chips 直接喂)。抛 AttachmentLimitError /
    IntakePrepError 由路由转码;落盘之后才开事务,一件失败清掉自己刚落的盘再上抛。"""
    from core import db

    check_limits(pairs)
    prepared = [nf for nf in intake_prep.normalize_batch(pairs, password=password) if nf.register]
    # 解包后件数可能暴涨(一个 zip 里 200 张),再过一次同一道闸 —— 换成 zip 口径的码,
    # 因为这时候要人去拆的是压缩包,不是「先送出一批」。
    check_limits(
        [(nf.original_name, nf.content) for nf in prepared],
        codes=_ZIP_CODES if len(prepared) > len(pairs) else _PLAIN_CODES,
    )

    landed: list[str] = []
    out: list[dict[str, Any]] = []
    try:
        for nf in prepared:
            detected = attach_kinds.detect(nf.content, nf.original_name, user=user)
            path = attachments.save(
                nf.content,
                tenant_id=tenant_id,
                session_id=session_id,
                original_name=nf.original_name,
            )
            landed.append(str(path))
            with db.get_cursor(commit=True) as cur:
                row = attachments.insert(
                    cur,
                    tenant_id=tenant_id,
                    session_id=session_id,
                    user_id=str(user["id"]),
                    original_name=nf.original_name,
                    file_ref=str(path),
                    size_bytes=len(nf.content),
                    sha256=attachments.sha256_of(nf.content),
                    mime=attachments.guess_mime(nf.original_name),
                    kind=detected.kind,
                    kind_source=detected.kind_source,
                    kind_reason=detected.kind_reason,
                    detect=detected.to_detect(),
                )
            out.append(attachments.public_attachment(row))
    except Exception:
        for ref in landed[len(out) :]:
            attachments.remove_file(ref)  # 登记没落成的那件清掉,不留无主文件
        raise
    return out
