# -*- coding: utf-8 -*-
"""采购附件行 ↔ 落盘文件生命周期边界(补「删附件行不删文件」的磁盘泄漏)。

只删本系统 uploads 落盘图(经 /api/uploads/image 上传、url 形如
/api/uploads/image/{tenant_id}/{name})。其余一律跳过:
  - generated=TRUE:替代收据/扣缴凭证是按需渲染的虚 URL(/api/purchase/docs/.../document.pdf),
    不落盘,没有文件可删。
  - kind='bill':url 存的是 OCR 落盘 ref(services/ocr/pdf_storage 的相对路径,不是本模块管的
    uploads URL)。这份 ref 与识别记录共生命周期,且 services/purchase/correct.py 的
    clone_as_draft 会把同一 ref 复制到更正后的新草稿——物理删了会打穿仍在世的另一份单据/
    识别记录,绝不能删。

物理删除必须在 DB 事务提交后做(行没删成、文件先没了 = 悬空引用),调用方(路由层)负责在
`with get_cursor(...)` 块结束后调 purge_files;这里只判断"该不该删"+ 真删。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.imaging import image_store

logger = logging.getLogger("mr-pilot")

# kind='bill' 的 url 不是本模块管的 uploads 文件,见模块 docstring。
_SKIP_KINDS = ("bill",)


def resolve_upload_ref(
    *, tenant_id: str, kind: str, url: Optional[str], generated: bool
) -> Optional[tuple[str, str]]:
    """附件行 → (tenant_id, 文件名);非本租户经 /api/uploads/image 落盘的图一律 None。"""
    if generated or kind in _SKIP_KINDS:
        return None
    if not url or not url.startswith(image_store.URL_PREFIX):
        return None
    rest = url[len(image_store.URL_PREFIX) :]
    # 合法上传 url 恰好两段({tenant}/{uuid文件名});更深路径不是本模块落的盘,拒。
    parts = rest.split("/")
    if len(parts) != 2 or not parts[1]:
        return None
    url_tenant, name = parts
    if url_tenant != str(tenant_id):
        return None
    return str(tenant_id), name


def collect_doc_refs(cur, *, tenant_id: str, workspace_client_id, doc_id) -> list[tuple[str, str]]:
    """一个单据(限本套账内)的全部附件行 → 过滤出该物理删的 uploads 文件 ref 列表。

    调用方须在 docs.delete_doc 级联删单**之前**查(行被 FK CASCADE 删掉就查不到了),
    拿到 ref 后自己等事务提交、docs.delete_doc 确认真删成功了,才能物理清文件。
    """
    cur.execute(
        "SELECT a.kind, a.url, a.generated FROM purchase_attachments a "
        "JOIN purchase_docs d ON d.id = a.purchase_doc_id AND d.tenant_id = a.tenant_id "
        "WHERE a.tenant_id = %s AND d.workspace_client_id = %s AND a.purchase_doc_id = %s",
        (tenant_id, workspace_client_id, doc_id),
    )
    refs = []
    for row in cur.fetchall():
        ref = resolve_upload_ref(
            tenant_id=tenant_id, kind=row["kind"], url=row["url"], generated=row["generated"]
        )
        if ref is not None:
            refs.append(ref)
    return refs


def purge_files(refs: list[tuple[str, str]]) -> None:
    """事务提交后 best-effort 落盘清理。失败只记日志不抛——附件行已经删了,
    孤儿文件不影响业务正确性,历史存量清理是另一个任务。"""
    for tid, name in refs:
        try:
            ok = image_store.delete_image(tid, name)
        except Exception:
            logger.warning(
                "purchase.attachment_file_purge_error tenant=%s name=%s", tid, name, exc_info=True
            )
            continue
        if not ok:
            logger.warning("purchase.attachment_file_purge_failed tenant=%s name=%s", tid, name)
