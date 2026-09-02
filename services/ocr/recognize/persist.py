"""
services/ocr/recognize/persist.py · OCR 识别·多发票入库持久化

从 app.py ocr_recognize 抽出(REFACTOR-WB-app · 2026-06-01 · 纯搬家 0 逻辑改)。
按发票分组逐张写 ocr_history:归档名/推荐分类学习/入库前查重/买方→client 闭环/
卖方智能分拣 workspace 归属/成功落库后 credits 扣费/异常栏 hook。
返回累计结果(history_ids / duplicate_warnings / primary_* / invoice_groups / invoice_count)。
"""

import logging

from fastapi import HTTPException

from core import db
from core.db import insert_ocr_history
from core.route_helpers import _tid
from services.erp.express_push.direction import apply_batch_direction as _apply_batch_direction
from services.erp.express_push.direction import normalize as _normalize_direction
from services.ocr.recognize import workspace_assignment as _workspace
from services.ocr.recognize import history_postprocess

logger = logging.getLogger("mr-pilot")


def persist_invoices(
    *,
    result,
    user,
    confidence,
    _billing,
    _chg_kind,
    _chg_units,
    file,
    content,
    file_hash,
    client_id,
    _ws_client_id,
    staged=False,
    posting_kind=None,
    direction=None,
    source="manual",
):
    # 8. 写入历史记录 · v0.8 改:所有 plan 都写(Free 也能看历史,只是保留 7 天)
    history_id = None
    # v0.11 · 多发票智能分组:把 PDF 拆成 N 张独立发票,每张一条历史
    import uuid as _uuid
    from services.ocr import invoice_grouper
    from services.archive import archive as _archive

    try:
        invoice_groups = invoice_grouper.group_pages_to_invoices(result["pages"])
        logger.info(f"📑 识别结果拆分为 {len(invoice_groups)} 张发票")
    except Exception as e:
        logger.warning(f"发票分组失败,回退为单张: {e}")
        invoice_groups = [
            {
                "invoice_fields": {},
                "source_pages": result["pages"],
                "page_indices": list(range(1, result["page_count"] + 1)),
            }
        ]

    invoice_count = len(invoice_groups)
    assignment_inputs = []
    for group in invoice_groups:
        fields = group["invoice_fields"]
        _apply_batch_direction(fields, direction)
        invoice_direction = _normalize_direction((fields or {}).get("direction") or direction)
        assignment_inputs.append((fields or {}, invoice_direction))
    try:
        workspace_decisions = _workspace.resolve_batch(
            assignment_inputs,
            user,
            source,
            fallback_workspace_id=_ws_client_id,
        )
    except _workspace.WorkspaceAssignmentError as exc:
        raise HTTPException(409, detail=f"ocr.{exc.code}") from exc
    source_pdf_id = str(_uuid.uuid4()) if invoice_count > 1 else None

    # 取用户归档模板(一次查询复用)
    try:
        template = db.get_archive_template(str(user["id"])) or _archive.DEFAULT_TEMPLATE
    except Exception:
        template = _archive.DEFAULT_TEMPLATE

    history_ids = []
    duplicate_warnings = []  # v0.13 · 收集所有发票的重复警告
    workspace_assignments = []  # 每张票的最终套账归属(路由结果透明给前端,治"扫完找不到")
    postprocess_entries = []
    primary_history_id = None  # 第一张发票的 history_id · 兼容老前端字段
    primary_archive_name = None
    primary_category_tag = None

    # v0.13 · 检查用户是否启用重复检测(默认开)
    dup_check_on = True
    try:
        dup_check_on = db.get_user_dup_check_enabled(str(user["id"]))
    except Exception as e:
        logger.warning(f"[dup_check] 读取用户设置失败 · 用默认值: {e}")

    # 每张票可能属于不同主体，分类树按最终账套缓存。
    from services.ocr.recognize import category_tag as _cat_tag

    _cat_trees = {}

    def _category_tree(workspace_id):
        if workspace_id in _cat_trees:
            return _cat_trees[workspace_id]
        tree = None
        try:
            if workspace_id:
                from services.purchase import categories as _cat_svc

                with db.get_cursor() as _cur:
                    tree = _cat_svc.get_tree(
                        _cur, tenant_id=_tid(user), workspace_client_id=int(workspace_id)
                    )
        except Exception as exc:
            logger.warning(f"[category] 载套账分类树失败(回落模型分类): {exc}")
        _cat_trees[workspace_id] = tree
        return tree

    # v114/v115 · PDF 留底(searchable PDF 生成 + save_pdf)·
    # REFACTOR-WA-OCRPERF Step1:挪出响应主路径 → 响应返回后后台生成 + 回填 pdf_storage_path
    #   (字段/响应不变 · 砍墙钟开销大头)。下方 insert 先存 None · 见函数尾部后台任务。

    for idx, group in enumerate(invoice_groups, start=1):
        g_pages = group["source_pages"]
        g_fields = group["invoice_fields"]
        workspace_decision = workspace_decisions[idx - 1]
        invoice_workspace_id = _ws_client_id
        if workspace_decision is not None:
            invoice_workspace_id = int(workspace_decision["workspace_client_id"])
        _cat_tree = _category_tree(invoice_workspace_id)

        # 给每张发票生成归档名(基于该张的合并字段)
        try:
            g_archive_name = _archive.preview_name(g_fields or {}, template)
        except Exception as e:
            logger.warning(f"归档名生成失败(发票 #{idx}): {e}")
            g_archive_name = None

        # 科目标签:归本套账分类(泰语)→ 命中用你的科目名并同步进 g_fields["category"]
        # (抽屉显示 f.category||category_tag,须一致);不中留空,不落模型自由文本/中文。
        # 载树失败/无套账(_cat_tree=None)→ 回落模型分类(不因基础设施问题全空)。
        if _cat_tree:
            try:
                g_category_tag = _cat_tag.resolve_tag(g_fields or {}, _cat_tree)
            except Exception as exc:
                logger.warning("category mapping failed (invoice=%s): %s", idx, exc)
                g_category_tag = None
            if g_fields is not None:
                g_fields["category"] = g_category_tag or ""
        else:
            g_category_tag = ((g_fields or {}).get("category") or "").strip() or None

        # v118.18 · 推荐分类「学习」· 同 seller 历史用过的 category 优先于 Gemini 的猜测
        try:
            g_seller = (g_fields.get("seller_name") or "").strip() if g_fields else None
            if g_seller:
                _learned = db.get_category_for_seller(
                    seller_name=g_seller,
                    user_id=str(user["id"]),
                    tenant_id=_tid(user),
                )
                # 学到的值也过树净化:旧的模型中文(非本套账分类)映射不上 → None → 不覆盖
                # (保留上面的树映射结果,既不回灌中文也不清空)。见 category_tag.sanitize_learned。
                _learned = _cat_tag.sanitize_learned(_learned, _cat_tree)
                if _learned:
                    g_category_tag = _learned
                    # 同步覆盖 g_fields["category"] · 让 pages 写入也带这个 · 抽屉打开就显示学到的科目
                    if g_fields is not None:
                        g_fields["category"] = _learned
        except Exception as _ce:
            logger.warning(f"category 学习查询失败(已忽略): {_ce}")

        # 为该张发票构造一份独立的 pages(只含该发票的页 + 合并后的主 fields)
        # pages 列表里:第一项放"主页"(含合并 fields)· 其他页按原顺序保留
        g_pages_for_save = []
        for pi, p in enumerate(g_pages):
            pc = dict(p)
            if pi == 0 and g_fields:
                # 主页的 fields 用合并后的 · 其他页保持原样
                pc["fields"] = g_fields
            g_pages_for_save.append(pc)

        # ─────────────────────────────────────────
        # v0.13 · 入库前重复检测
        # 检测到 · 仅记录警告 · 不阻断写入(让用户在前端选择如何处理)
        # ─────────────────────────────────────────
        if dup_check_on and g_fields:
            try:
                # 提取 summary 字段
                inv_no = (g_fields.get("invoice_number") or "").strip() or None
                seller = (g_fields.get("seller_name") or "").strip() or None
                # date 转 ISO 格式
                date_iso = None
                raw_date = g_fields.get("date")
                if raw_date:
                    try:
                        from datetime import datetime as _dt

                        s = str(raw_date).replace("/", "-")[:10]
                        _dt.strptime(s, "%Y-%m-%d")
                        date_iso = s
                    except Exception as e:
                        logger.warning(f"[ocr_post] invoice_date 解析失败: {e}")
                # 金额转 float
                total_f = None
                raw_amt = g_fields.get("total_amount")
                if raw_amt:
                    try:
                        total_f = float(str(raw_amt).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[ocr_post] total_amount 解析失败: {e}")

                dup = db.check_duplicate_invoice(
                    user_id=str(user["id"]),
                    invoice_no=inv_no,
                    invoice_date=date_iso,
                    seller_name=seller,
                    total_amount=total_f,
                    workspace_client_id=invoice_workspace_id,  # PO-4 · 重复检测限本套账
                    tenant_id=_tid(user),
                )
                if dup:
                    duplicate_warnings.append(
                        {
                            "invoice_index": idx,  # 第几张
                            "invoice_total": invoice_count,  # 共几张
                            "level": dup["level"],  # exact / likely
                            "matched_fields": dup["matched_fields"],
                            "match": dup["match"],
                            "current": {
                                "invoice_no": inv_no,
                                "invoice_date": date_iso,
                                "seller_name": seller,
                                "total_amount": total_f,
                            },
                        }
                    )
                    logger.info(
                        f"⚠️ 检测到重复发票 (idx={idx} · {dup['level']} · 匹配于历史 {dup['match']['id']})"
                    )
            except Exception as e:
                logger.warning(f"重复检测失败(已忽略): {e}")

        # v92 · Bug 1 第 1 层防御 · 识别成功才带 file_hash · 防止空结果污染缓存
        _gf = g_fields or {}
        _has_inv = bool(str(_gf.get("invoice_number") or "").strip())
        _has_amt = _gf.get("total_amount") is not None and bool(
            str(_gf.get("total_amount")).strip()
        )
        _has_seller = bool(str(_gf.get("seller_name") or "").strip())
        _recognized_ok = _has_inv or _has_amt or _has_seller
        _cache_hash = file_hash if (idx == 1 and _recognized_ok) else None
        if idx == 1 and not _recognized_ok:
            logger.warning(f"⚠️ 识别失败(关键字段全空) · file_hash 不入缓存 · file={file.filename}")

        try:
            hid = insert_ocr_history(
                user_id=str(user["id"]),
                tenant_id=_tid(user),  # 2026-05-24 · 多租户归属(原缺 → tenant_id 恒 NULL)
                filename=file.filename or "untitled",
                page_count=len(g_pages),
                pages=g_pages_for_save,
                confidence=confidence,
                elapsed_ms=result["elapsed_ms"] if idx == 1 else 0,  # 只在第一条记录总耗时
                file_size_kb=len(content) // 1024 if idx == 1 else None,
                file_hash=_cache_hash,  # v92 · 仅识别成功时带 hash
                archive_name=g_archive_name,
                category_tag=g_category_tag,
                source_pdf_id=source_pdf_id,
                source_page_indices=group["page_indices"] if invoice_count > 1 else None,
                source_index=idx if invoice_count > 1 else None,
                source_total=invoice_count if invoice_count > 1 else None,
                # v114 · PDF 留底 · REFACTOR-WA-OCRPERF Step1:先存 None · 响应返回后后台生成+回填
                pdf_storage_path=None,
                pdf_size_bytes=None,
                # v27.8.1.13a · 右上角客户切换器选中时自动归属(多发票同一 PDF 共享同一 client_id)
                client_id=(
                    int(client_id) if (client_id and str(client_id).strip().isdigit()) else None
                ),
                # B1 相 1 · workspace 账套归属(可选·校验在 insert_ocr_history 内·带不上 NULL)
                workspace_client_id=invoice_workspace_id,
                # 反馈闭环 ② · ai_raw 留底由 insert_ocr_history 缺省取 pages 自动写(全入口普适)
                # 草稿态:仅网页交互式上传传 True(第4步完成才落识别记录);后台/文件夹入口 False。
                staged=staged,
                # 同一 PDF 拆出的多张票共用同一声明(整批一个开关)· 已在 core 归一。
                posting_kind=posting_kind,
                source=source,
            )
        except Exception:
            _workspace.cleanup_failed_batch(user, history_ids, workspace_decisions)
            raise
        if not hid:
            _workspace.cleanup_failed_batch(user, history_ids, workspace_decisions)
            raise HTTPException(503, detail="ocr.history_write_failed")
        history_ids.append(hid)
        duplicate_warning = None
        if duplicate_warnings and duplicate_warnings[-1].get("invoice_index") == idx:
            duplicate_warnings[-1]["new_history_id"] = hid
            duplicate_warning = duplicate_warnings[-1]
        if idx == 1:
            primary_history_id = hid
            primary_archive_name = g_archive_name
            primary_category_tag = g_category_tag

        assignment = {
            "history_id": str(hid),
            "workspace_id": int(invoice_workspace_id) if invoice_workspace_id is not None else None,
        }
        if workspace_decision is not None:
            assignment.update(workspace_decision)
            assignment["workspace_id"] = assignment.pop("workspace_client_id")
        workspace_assignments.append(assignment)
        postprocess_entries.append(
            {
                "history_id": str(hid),
                "fields": g_fields or {},
                "pages": g_pages_for_save,
                "duplicate_warning": duplicate_warning,
            }
        )

    if primary_history_id:
        history_postprocess.charge_batch(
            user,
            _billing,
            _chg_kind,
            _chg_units,
            file.filename,
            primary_history_id,
        )
    for entry in postprocess_entries:
        history_postprocess.process_history(
            user=user,
            client_id=client_id,
            history_id=entry["history_id"],
            fields=entry["fields"],
            pages=entry["pages"],
            confidence=confidence,
            duplicate_warning=entry["duplicate_warning"],
        )

    return {
        "invoice_groups": invoice_groups,
        "invoice_count": invoice_count,
        "history_ids": history_ids,
        "duplicate_warnings": duplicate_warnings,
        "workspace_assignments": workspace_assignments,
        "primary_history_id": primary_history_id,
        "primary_archive_name": primary_archive_name,
        "primary_category_tag": primary_category_tag,
    }
