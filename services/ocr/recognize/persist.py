"""
services/ocr/recognize/persist.py · OCR 识别·多发票入库持久化

从 app.py ocr_recognize 抽出(REFACTOR-WB-app · 2026-06-01 · 纯搬家 0 逻辑改)。
按发票分组逐张写 ocr_history:归档名/推荐分类学习/入库前查重/买方→client 闭环/
卖方智能分拣 workspace 归属/成功落库后 credits 扣费/异常栏 hook。
返回累计结果(history_ids / duplicate_warnings / primary_* / invoice_groups / invoice_count)。
"""

import logging

from core import db
from core.db import insert_ocr_history
from core.route_helpers import _tid
from services.exceptions.exception_checks import _async_run_exception_checks

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
    source_pdf_id = str(_uuid.uuid4()) if invoice_count > 1 else None

    # 取用户归档模板(一次查询复用)
    try:
        template = db.get_archive_template(str(user["id"])) or _archive.DEFAULT_TEMPLATE
    except Exception:
        template = _archive.DEFAULT_TEMPLATE

    history_ids = []
    duplicate_warnings = []  # v0.13 · 收集所有发票的重复警告
    primary_history_id = None  # 第一张发票的 history_id · 兼容老前端字段
    primary_archive_name = None
    primary_category_tag = None

    # v0.13 · 检查用户是否启用重复检测(默认开)
    dup_check_on = True
    try:
        dup_check_on = db.get_user_dup_check_enabled(str(user["id"]))
    except Exception as e:
        logger.warning(f"[dup_check] 读取用户设置失败 · 用默认值: {e}")

    # v114/v115 · PDF 留底(searchable PDF 生成 + save_pdf)·
    # REFACTOR-WA-OCRPERF Step1:挪出响应主路径 → 响应返回后后台生成 + 回填 pdf_storage_path
    #   (字段/响应不变 · 砍墙钟开销大头)。下方 insert 先存 None · 见函数尾部后台任务。

    for idx, group in enumerate(invoice_groups, start=1):
        g_pages = group["source_pages"]
        g_fields = group["invoice_fields"]

        # 给每张发票生成归档名(基于该张的合并字段)
        try:
            g_archive_name = _archive.preview_name(g_fields or {}, template)
            g_category_tag = (g_fields.get("category") or "").strip() or None if g_fields else None
        except Exception as e:
            logger.warning(f"归档名生成失败(发票 #{idx}): {e}")
            g_archive_name = None
            g_category_tag = None

        # v118.18 · 推荐分类「学习」· 同 seller 历史用过的 category 优先于 Gemini 的猜测
        try:
            g_seller = (g_fields.get("seller_name") or "").strip() if g_fields else None
            if g_seller:
                _learned = db.get_category_for_seller(
                    seller_name=g_seller,
                    user_id=str(user["id"]),
                    tenant_id=_tid(user),
                )
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
                    workspace_client_id=_ws_client_id,  # PO-4 · 重复检测限本套账
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
            workspace_client_id=_ws_client_id,
            # 反馈闭环 ② · 首存基线留底(= 此刻写入的 pages)·永不改·供后续用户修正算 diff
            ai_raw=g_pages_for_save,
        )
        if hid:
            history_ids.append(hid)
            # 把 history_id 关联到对应的 dup warning(便于前端提供"删除"操作)
            _dup_for_idx = None
            if duplicate_warnings and duplicate_warnings[-1].get("invoice_index") == idx:
                duplicate_warnings[-1]["new_history_id"] = hid
                _dup_for_idx = duplicate_warnings[-1]
            if idx == 1:
                primary_history_id = hid
                primary_archive_name = g_archive_name
                primary_category_tag = g_category_tag
                # v118.46 · 扣费(成功识别 + 落库后 · 只扣一次 · 传 history_id 让 usage-history 显示文件名)
                #   描述结尾带 history_id 前 8 位 → usage-history 的 LIKE join 能命中(修 filename 空)
                if not _billing.get("is_exempt") and _chg_units > 0 and hid:
                    try:
                        import asyncio as _asyncio_chg

                        _asyncio_chg.create_task(
                            _asyncio_chg.to_thread(
                                db.charge_ocr_async,
                                str(user.get("id")),
                                _tid(user),
                                _chg_kind,
                                _chg_units,
                                str(hid),
                                f"OCR {_chg_kind} · {file.filename} · {str(hid)[:8]}",
                            )
                        )
                    except Exception as _ce:
                        logger.warning(f"💳 async charge dispatch skip: {_ce}")

            # 买方→Pearnly client 闭环(Zihao 2026-05-26 拍板 · 税号优先·混合)。
            # 右上角客户切换器没选 client_id(常态)时,把发票买方解析/创建成 client:
            #   决策逻辑全在 services/clients/store.resolve_or_create_buyer_client:
            #   assigned/created → 写回 history.client_id · 放行 auto-push(闭环)
            #   suggest          → 写 _suggested_client_* 到 history.pages · 等用户确认
            #   review/none      → 不绑/不建(防同名异主体错并 & qa_4 多页买方冲突)
            # 根因(替代旧「只匹配已存在客户」逻辑):新买方第一次出现匹配不到 →
            #   client_id=null → 推送必 ERR_NO_CLIENT。有合法 13 位税号即按税号建客户闭环。
            _auto_resolved_client = False
            try:
                history_existing_client = (
                    int(client_id) if (client_id and str(client_id).strip().isdigit()) else None
                )
                if not history_existing_client:
                    _buyer_name = (g_fields or {}).get("buyer_name")
                    _buyer_tax = (g_fields or {}).get("buyer_tax")
                    # 同一张发票多页的买方候选(给冲突检测 · qa_4)
                    _buyer_candidates = [
                        (p.get("fields") or {}).get("buyer_name") for p in (g_pages_for_save or [])
                    ]
                    decision = db.resolve_or_create_buyer_client(
                        buyer_name=_buyer_name,
                        buyer_tax=_buyer_tax,
                        user_id=str(user["id"]),
                        tenant_id=_tid(user),
                        buyer_candidates=_buyer_candidates,
                    )
                    _act = decision.get("action")
                    _rcid = decision.get("client_id")
                    if _act in ("assigned", "created") and _rcid:
                        db.update_history_client_id(
                            hid, _rcid, str(user["id"]), tenant_id=_tid(user)
                        )
                        _auto_resolved_client = True
                        logger.info(
                            "[buyer-resolve] %s history=%s client_id=%s name=%r "
                            "conf=%.2f source=%s",
                            _act,
                            hid[:8],
                            _rcid,
                            decision.get("client_name"),
                            decision.get("confidence", 0.0),
                            decision.get("match_source"),
                        )
                    elif _act == "suggest" and _rcid:
                        # 建议归属 · 不 auto-assign · stash 到 history.pages[0].fields
                        logger.info(
                            "[buyer-resolve] SUGGEST history=%s client_id=%s name=%r conf=%.2f",
                            hid[:8],
                            _rcid,
                            decision.get("client_name"),
                            decision.get("confidence", 0.0),
                        )
                        try:
                            _new_pages = [dict(p) for p in (g_pages_for_save or [])]
                            if _new_pages:
                                _f = dict(_new_pages[0].get("fields") or {})
                                _f["_suggested_client_id"] = _rcid
                                _f["_suggested_client_name"] = decision.get("client_name")
                                _f["_suggested_client_confidence"] = decision.get("confidence")
                                _new_pages[0] = {**_new_pages[0], "fields": _f}
                                db.update_ocr_history_pages(
                                    str(user["id"]), hid, _new_pages, tenant_id=_tid(user)
                                )
                        except Exception as _se:
                            logger.warning(f"stash suggestion failed: {_se}")
                    else:
                        logger.info(
                            "[buyer-resolve] %s history=%s buyer=%r reason=%s",
                            _act,
                            hid[:8],
                            (_buyer_name or "")[:40],
                            decision.get("reason"),
                        )
            except Exception as _are:
                logger.warning(f"buyer-resolve client_id failed (history={hid[:8]}): {_are}")

            # 卖方智能分拣 → workspace 归属(Phase 1 · Zihao 2026-05-26)。
            # 销项发票「卖方」= 账套主体 = workspace_client。归属**完全由 seller 决定**,
            # 右上角切换器只是查看过滤器、不再决定上传归属。
            #   匹配到(assigned/unbound)→ 写该 workspace_client_id(覆盖)
            #   未匹配/多候选(none/multi)→ 保留 insert 已写的归属(切换器/默认套账),不回写 NULL
            # 注:workspace_client_id 现已被 Express 推送方向判定(以 workspace 主体税号当锚点)
            #     消费 → none/multi 时清 NULL 会让采购票(卖方=供应商≠自家)失去自家锚点 →
            #     direction_unknown。故仅命中具体主体才覆盖,否则保留 insert 归属。
            _ws_assigned = None
            try:
                _seller_match = db.match_workspace_for_seller(
                    seller_tax=(g_fields or {}).get("seller_tax"),
                    seller_name=(g_fields or {}).get("seller_name"),
                    user_id=str(user["id"]),
                    tenant_id=_tid(user),
                )
                _ws_assigned = db.route_assigns_workspace(_seller_match)
                if _ws_assigned is not None:
                    db.update_history_workspace_client_id(
                        hid, _ws_assigned, str(user["id"]), tenant_id=_tid(user)
                    )
                logger.info(
                    "[seller-route] %s history=%s seller=%r workspace_client_id=%s",
                    _seller_match.get("action"),
                    hid[:8],
                    ((g_fields or {}).get("seller_name") or "")[:40],
                    _ws_assigned if _ws_assigned is not None else _ws_client_id,
                )
            except Exception as _sre:
                logger.warning(f"seller-route failed (history={hid[:8]}): {_sre}")

            # 采购票兜底:卖方=供应商(≠自家)→ 卖方分拣不命中 → 按【买方】=账套主体 分拣,
            # 否则采购票留在错误默认主体 → Express 方向判定失锚 → direction_unknown(本次根因)。
            # 不命中(none/multi)仍保留 insert 归属(同卖方口径,绝不回写 NULL)。
            if _ws_assigned is None:
                try:
                    _buyer_match = db.match_workspace_for_buyer(
                        buyer_tax=(g_fields or {}).get("buyer_tax"),
                        buyer_name=(g_fields or {}).get("buyer_name"),
                        user_id=str(user["id"]),
                        tenant_id=_tid(user),
                    )
                    _ws_buyer = db.route_assigns_workspace(_buyer_match)
                    if _ws_buyer is not None:
                        db.update_history_workspace_client_id(
                            hid, _ws_buyer, str(user["id"]), tenant_id=_tid(user)
                        )
                        logger.info(
                            "[buyer-route] %s history=%s buyer=%r workspace_client_id=%s",
                            _buyer_match.get("action"),
                            hid[:8],
                            ((g_fields or {}).get("buyer_name") or "")[:40],
                            _ws_buyer,
                        )
                except Exception as _bre:
                    logger.warning(f"buyer-route failed (history={hid[:8]}): {_bre}")

            # v118.20.1 · 异常栏 · 异步跑零成本规则(不阻塞 OCR 主流程)
            try:
                import asyncio as _asyncio_exc

                # 安全解析 total · 不依赖外层 try 块里的 total_f
                _exc_total = None
                _raw_t = (g_fields or {}).get("total_amount")
                if _raw_t:
                    try:
                        _exc_total = float(str(_raw_t).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[exc_check] total_amount 解析失败: {e}")
                _asyncio_exc.create_task(
                    _async_run_exception_checks(
                        history_id=str(hid),
                        user_id=str(user["id"]),
                        tenant_id=_tid(user),
                        seller_name=(g_fields or {}).get("seller_name"),
                        invoice_no=(g_fields or {}).get("invoice_number"),
                        total_amount=_exc_total,
                        confidence=confidence,
                        duplicate=_dup_for_idx,
                        fields=g_fields or {},  # v118.20.1.5 · 全字段 · 给自洽性规则用
                    )
                )
            except Exception as _exc_e:
                logger.warning(f"异常检测入队失败(不影响识别): {_exc_e}")

    return {
        "invoice_groups": invoice_groups,
        "invoice_count": invoice_count,
        "history_ids": history_ids,
        "duplicate_warnings": duplicate_warnings,
        "primary_history_id": primary_history_id,
        "primary_archive_name": primary_archive_name,
        "primary_category_tag": primary_category_tag,
    }
