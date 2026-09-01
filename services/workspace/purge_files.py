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
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# 各基准目录跟写入方保持同一个 env 名,不另起一套(写在这儿的默认值只是兜底)。
_PDF_BASE = os.environ.get("PDF_STORAGE_DIR", "/opt/mrpilot/storage/pdfs")
_WORKORDER_BASE = os.environ.get("WORKORDER_STORAGE_DIR", "/opt/mrpilot/storage/workorders")
_IMAGE_BASE = os.environ.get("IMAGE_STORAGE_DIR", "/opt/mrpilot/storage/images")
# VAT 对账上传的 Excel 落在 uploads 下(不在 storage 里),见 routes/vat_excel_routes.EXCEL_STORE_DIR
_VAT_EXCEL_BASE = "/opt/mrpilot/uploads/vat_recon"


def _rows(cur, sql: str, params) -> List[Dict[str, Any]]:
    cur.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def collect(
    cur, *, tenant_id: str, ws_id: int, scope: Dict[str, List[str]] | None = None
) -> Dict[str, List[str]]:
    """删表【之前】把该账套名下的盘上文件位置抠出来。

    scope 给值 = 只清这一期(purge.period_scope 的产物:该期工单 id 与挂上去的票据 id),
    别期的文件一个不碰。scope=None = 整个账套。

    返回 {"files": [绝对路径], "dirs": [绝对目录]}。取不到的类别静默跳过 —— 这些表
    未必在每套部署里都存在,少一类不该让整个清除失败。
    """
    files: List[str] = []
    dirs: List[str] = []

    # ① OCR 原件转出的 PDF:pdf_storage_path 相对 PDF_STORAGE_DIR(storage_path 生产恒 NULL,
    #    上一版只认它 → 一个都没收到)。
    try:
        if scope is None:
            rows = _rows(
                cur,
                "SELECT pdf_storage_path AS p FROM ocr_history "
                "WHERE workspace_client_id = %s AND pdf_storage_path IS NOT NULL "
                "AND pdf_storage_path <> ''",
                (ws_id,),
            )
        elif scope.get("ocr_history_ids"):
            rows = _rows(
                cur,
                "SELECT pdf_storage_path AS p FROM ocr_history "
                "WHERE id::text = ANY(%s) AND pdf_storage_path IS NOT NULL "
                "AND pdf_storage_path <> ''",
                (scope["ocr_history_ids"],),
            )
        else:
            rows = []
        for r in rows:
            files.append(str(Path(_PDF_BASE) / str(r["p"])))
    except Exception:  # noqa: BLE001
        logger.warning("[purge-files] ocr_history 收集失败", exc_info=True)

    # 历史已下线文档与采购附件都不带账期,只在整套账清除时收 —— 按期清不该动它们。
    if scope is None:
        # 保留退役数据的文件回收,避免删除账套后遗留用户文件。
        try:
            for r in _rows(
                cur,
                "SELECT storage_path AS p FROM knowledge_documents WHERE workspace_client_id = %s "
                "AND storage_path IS NOT NULL AND storage_path <> ''",
                (ws_id,),
            ):
                files.append(str(Path(_PDF_BASE) / "knowledge" / str(r["p"])))
        except Exception:  # noqa: BLE001
            logger.warning("[purge-files] knowledge_documents 收集失败", exc_info=True)
        # VAT 对账上传的 Excel:excel_path 是绝对路径。
        try:
            for r in _rows(
                cur,
                "SELECT excel_path AS p FROM vat_recon_tasks WHERE workspace_client_id = %s "
                "AND excel_path IS NOT NULL AND excel_path <> ''",
                (ws_id,),
            ):
                files.append(str(r["p"]))
        except Exception:  # noqa: BLE001
            logger.warning("[purge-files] vat_recon_tasks 收集失败", exc_info=True)
        # 采购附件:generated=TRUE 是虚 URL(没有实体文件),不收。
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

    # ③ 工单目录(用户上传的原件与交付物都在这儿 · 线上最大的一块):
    #    workorders/<租户8位>/<工单id>/{materials,deliverables}
    try:
        from services.workorder import storage as wo_storage

        if scope is None:
            ids = [
                r["id"]
                for r in _rows(
                    cur,
                    "SELECT id::text AS id FROM work_orders WHERE workspace_client_id = %s",
                    (ws_id,),
                )
            ]
        else:
            ids = list(scope.get("work_order_ids") or [])
        for wid in ids:
            dirs.append(str(wo_storage.order_dir(tenant_id, wid)))
    except Exception:  # noqa: BLE001
        logger.warning("[purge-files] work_orders 目录收集失败", exc_info=True)

    return {"files": files, "dirs": dirs}


# 允许动的根:库里存的字符串不当可信输入,越出这几个根一律不碰。
# 模块加载时解析一次 —— 原来每判一个路径就把三个根重解析一遍(N 个文件 = 3N 次 syscall)。
_ALLOWED_ROOTS = (_PDF_BASE, _WORKORDER_BASE, _IMAGE_BASE, _VAT_EXCEL_BASE)


def _resolved_roots() -> Tuple[Path, ...]:
    out = []
    for root in _ALLOWED_ROOTS:
        try:
            out.append(Path(root).resolve())
        except OSError:
            continue
    return tuple(out)


_ROOTS = _resolved_roots()


def _inside_allowed_root(p: Path) -> bool:
    return any(p == r or r in p.parents for r in _ROOTS)


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
                # 一次 os.walk 边数边删:原来 rglob 数一遍(每项一次 stat)再 rmtree 走一遍,
                # 同一棵树遍历两次;线上工单目录曾有 1.4G,不值当。
                for root, _dirs, names in os.walk(d, topdown=False):
                    removed += len(names)
                shutil.rmtree(d)
        except Exception:  # noqa: BLE001
            logger.warning(f"[purge-files] 删目录失败: {raw}", exc_info=True)
    return removed
