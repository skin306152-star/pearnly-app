# -*- coding: utf-8 -*-
"""按账套清空数据 · 盘上文件那一半。

拆出来是因为它跟删表完全是另一回事:每类文件各有各的基准目录和拼法,把它们混在
purge.py 里既超行数又难读。

必须先收集再删:行没了就再也定位不到文件(同 services/purchase/attachment_files.py
的 collect→delete→purge 三段式)。删文件一律在事务提交之后 —— 先删文件再回滚就找不回来。

2026-07-26 事故补记:上一版只认 ocr_history.storage_path(生产上这列恒 NULL),又拿
storage 根目录去拼相对路径,基准全错 → 每次都报 files=0,一张图没删过。用户上传的原件
其实在 workorders/<租户8位>/<工单id>/ 底下,单这一个目录线上就 1.4G。
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 各基准目录跟写入方保持同一个 env 名,不另起一套(写在这儿的默认值只是兜底)。
_PDF_BASE = os.environ.get("PDF_STORAGE_DIR", "/opt/mrpilot/storage/pdfs")
_WORKORDER_BASE = os.environ.get("WORKORDER_STORAGE_DIR", "/opt/mrpilot/storage/workorders")
_IMAGE_BASE = os.environ.get("IMAGE_STORAGE_DIR", "/opt/mrpilot/storage/images")


def _rows(cur, sql: str, params) -> List[Dict[str, Any]]:
    cur.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def collect(cur, *, tenant_id: str, ws_id: int) -> Dict[str, List[str]]:
    """删表【之前】把该账套名下的盘上文件位置抠出来。

    返回 {"files": [绝对路径], "dirs": [绝对目录]}。取不到的类别静默跳过 —— 这些表
    未必在每套部署里都存在,少一类不该让整个清除失败。
    """
    files: List[str] = []
    dirs: List[str] = []

    # ① OCR 原件转出的 PDF:pdf_storage_path 相对 PDF_STORAGE_DIR(storage_path 生产恒 NULL,
    #    上一版只认它 → 一个都没收到)。
    try:
        for r in _rows(
            cur,
            "SELECT pdf_storage_path AS p FROM ocr_history "
            "WHERE workspace_client_id = %s AND pdf_storage_path IS NOT NULL "
            "AND pdf_storage_path <> ''",
            (ws_id,),
        ):
            files.append(str(Path(_PDF_BASE) / str(r["p"])))
    except Exception:  # noqa: BLE001
        logger.warning("[purge-files] ocr_history 收集失败", exc_info=True)

    # ② 知识库文档:相对 PDF_STORAGE_DIR/knowledge(见 services/knowledge/host_provider)
    try:
        for r in _rows(
            cur,
            "SELECT storage_path AS p FROM knowledge_documents "
            "WHERE workspace_client_id = %s AND storage_path IS NOT NULL AND storage_path <> ''",
            (ws_id,),
        ):
            files.append(str(Path(_PDF_BASE) / "knowledge" / str(r["p"])))
    except Exception:  # noqa: BLE001
        logger.warning("[purge-files] knowledge_documents 收集失败", exc_info=True)

    # ③ 工单目录(用户上传的原件与交付物都在这儿 · 线上最大的一块):
    #    workorders/<租户8位>/<工单id>/{materials,deliverables}
    try:
        from services.workorder import storage as wo_storage

        for r in _rows(
            cur,
            "SELECT id::text AS id FROM work_orders WHERE workspace_client_id = %s",
            (ws_id,),
        ):
            dirs.append(str(wo_storage.order_dir(tenant_id, r["id"])))
    except Exception:  # noqa: BLE001
        logger.warning("[purge-files] work_orders 目录收集失败", exc_info=True)

    # ④ 采购附件:generated=TRUE 是虚 URL(没有实体文件),不收。
    try:
        for r in _rows(
            cur,
            "SELECT url FROM purchase_attachments WHERE generated IS NOT TRUE "
            "AND purchase_doc_id IN "
            "(SELECT id FROM purchase_docs WHERE workspace_client_id = %s)",
            (ws_id,),
        ):
            name = Path(str(r["url"])).name
            if name:
                files.append(str(Path(_IMAGE_BASE) / str(tenant_id) / name))
    except Exception:  # noqa: BLE001
        logger.warning("[purge-files] purchase_attachments 收集失败", exc_info=True)

    return {"files": files, "dirs": dirs}


# 允许动的根:库里存的字符串不当可信输入,越出这几个根一律不碰。
_ALLOWED_ROOTS = (_PDF_BASE, _WORKORDER_BASE, _IMAGE_BASE)


def _inside_allowed_root(p: Path) -> bool:
    for root in _ALLOWED_ROOTS:
        try:
            r = Path(root).resolve()
        except OSError:
            continue
        if p == r or r in p.parents:
            return True
    return False


def purge(targets: Dict[str, List[str]]) -> int:
    """事务提交后 best-effort 删盘,返回真删掉的文件数(目录按其内文件数计)。

    失败只记日志不抛:表已经清了,留个孤儿文件不影响正确性,把整个清除报成失败更糟。
    """
    removed = 0
    for raw in targets.get("files") or []:
        try:
            p = Path(raw).resolve()
            if not _inside_allowed_root(p):
                logger.warning(f"[purge-files] 路径越界,跳过: {raw}")
                continue
            if p.is_file():
                p.unlink()
                removed += 1
        except Exception:  # noqa: BLE001
            logger.warning(f"[purge-files] 删文件失败: {raw}", exc_info=True)
    for raw in targets.get("dirs") or []:
        try:
            d = Path(raw).resolve()
            if not _inside_allowed_root(d):
                logger.warning(f"[purge-files] 目录越界,跳过: {raw}")
                continue
            if d.is_dir():
                removed += sum(1 for _ in d.rglob("*") if _.is_file())
                shutil.rmtree(d)
        except Exception:  # noqa: BLE001
            logger.warning(f"[purge-files] 删目录失败: {raw}", exc_info=True)
    return removed
