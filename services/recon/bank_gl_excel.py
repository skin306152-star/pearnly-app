# -*- coding: utf-8 -*-
"""
services/recon/bank_gl_excel.py · Pearnly

Structural GL parser for Excel/CSV: header detection (with ADR-006 template
learning fallback), debit/credit/amount column mapping, and row → GlRow. PDF
GL parsing lives in bank_gl_pdf; shared column recognition in bank_gl_common.
"""

import io
from typing import Dict, Any, Optional

from services.recon.bank_recon_types import GlRow
from services.recon.bank_recon_utils import _to_float, _parse_date, _is_gl_skip_row
from services.recon.bank_table_io import _load_csv_sheets
from services.recon.bank_gl_common import _map_gl_cols, _extract_acct_code

# 期初余额行关键词(4 语 · 仅"期初/承前",不含"期末/结转")· 我们的固定模板把标签放在
# 日期列(非描述列),故识别期初要扫该行前几格而非只看描述列。
_GL_OPENING_KW = (
    "ยอดยกมา",
    "ยกมา",
    "brought forward",
    "balance forward",
    "opening",
    "b/f",
    "期初",
    "繰越残高",
)


def parse_gl_excel(
    file_bytes: bytes,
    filename: str,
    account_code: str = "",
    tenant_id: Optional[str] = None,
    allow_ai: bool = False,
    api_key: str = "",
) -> Dict[str, Any]:
    """
    Parse GL from Excel file.
    Returns {ok, rows, accounts, opening, closing, row_count, error}

    ADR-006 S6b · 固定词典找不到表头时,接模板学习层:saved → 本地推断(GL 无余额链 · 靠表头词+
    形状 · 保守:借贷拿不准不自动套用)→ needs_mapping(交用户确认)。现有能认的 GL 走原路径零回归。
    """
    _ext = (filename or "").lower().rsplit(".", 1)[-1]
    all_rows_raw = None
    if _ext in ("csv", "tsv", "txt"):
        # ADR-006 S6b · GL CSV 也走学习层(此前 CSV GL 直接丢 Gemini)
        csv_sheets = _load_csv_sheets(file_bytes)
        if csv_sheets:
            all_rows_raw = csv_sheets[0][1]
    if all_rows_raw is None:
        try:
            import openpyxl

            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            ws = wb.active
            all_rows_raw = list(ws.values)
        except Exception:
            try:
                import xlrd

                wb = xlrd.open_workbook(file_contents=file_bytes)
                ws = wb.sheet_by_index(0)
                all_rows_raw = [ws.row_values(i) for i in range(ws.nrows)]
            except Exception as e:
                # 最后再试 CSV(扩展名没带对但内容是 CSV)
                csv_sheets = _load_csv_sheets(file_bytes)
                if csv_sheets:
                    all_rows_raw = csv_sheets[0][1]
                else:
                    return {"ok": False, "error": f"Cannot read Excel/CSV: {e}"}

    # Find header row (within first 10 rows)
    header_idx = 0
    col_map: Dict[str, int] = {}
    for i, row in enumerate(all_rows_raw[:10]):
        row_list = [str(c or "").strip() for c in row]
        cm = _map_gl_cols(row_list)
        # ADR-006 压测发现 · 必须有 date + 钱列(借/贷)才算真表头;只匹配到 date+科目+余额(无借贷)
        # 不算(否则解析出 0 行 · 如单列净额 GL)→ 交学习层(可识别单列净额 amount)。
        if "date" in cm and ("debit" in cm or "credit" in cm):
            col_map = cm
            header_idx = i
            break

    if not col_map:
        # ADR-006 S6b · 学习层(惰性 import · 失败退回原行为)
        try:
            from services.importer import template_learning as _tl, template_store as _ts
        except Exception:  # noqa: BLE001
            _tl = _ts = None
        if _tl is not None:
            try:
                l_idx, l_cm, conf, _r = _tl.infer_gl_col_map(all_rows_raw)
            except Exception:  # noqa: BLE001
                l_idx, l_cm, conf = -1, {}, "low"
            # parse_gl_excel 能用的键(S6b 起支持单列 amount · 按符号拆借贷);
            # 建议给前端时保留全部猜测 · 让用户在面板里改对。
            usable = {
                k: v
                for k, v in (l_cm or {}).items()
                if k
                in (
                    "date",
                    "doc_no",
                    "description",
                    "debit",
                    "credit",
                    "account",
                    "balance",
                    "amount",
                )
            }
            if l_idx >= 0:  # 找到了像 GL 的表格(date + 钱形状)· 不再死错
                sig = _tl.build_header_signature(all_rows_raw[l_idx])
                saved = _ts.find_mapping(tenant_id, "gl", sig) if (tenant_id and _ts) else None
                if saved:
                    col_map, header_idx = saved, l_idx
                elif (
                    conf == "high"
                    and "date" in usable
                    and ("debit" in usable or "credit" in usable or "amount" in usable)
                ):
                    col_map, header_idx = usable, l_idx
                    if tenant_id and _ts:
                        _ts.save_mapping(
                            tenant_id,
                            "gl",
                            sig,
                            usable,
                            source="local",
                            sample_headers=[str(c or "") for c in all_rows_raw[l_idx]],
                        )
                else:
                    # 拿不准(GL 无余额链可证 · 借贷/科目易判错)· ADR-006 S7:仅在 submit 预检
                    # (allow_ai)调一次 Gemini 要列映射 → 形状校验把关(GL 无链)→ 过才套用 + 存。
                    # 异步 worker 永不触发。失败/校验不过 → 交用户确认一次(不自动套用)。
                    ai_cm = (
                        _tl.suggest_mapping_with_ai(
                            "gl",
                            "",
                            all_rows_raw[l_idx],
                            _tl.preview_rows(all_rows_raw, l_idx, limit=20),
                            local_guess=l_cm,
                            api_key=api_key,
                            signature=sig,
                        )
                        if allow_ai
                        else None
                    )
                    if ai_cm and _tl.validate_gl_shape(all_rows_raw, l_idx, ai_cm)[0]:
                        col_map, header_idx = ai_cm, l_idx
                        if tenant_id and _ts:
                            _ts.save_mapping(
                                tenant_id,
                                "gl",
                                sig,
                                ai_cm,
                                source="ai",
                                sample_headers=[str(c or "") for c in all_rows_raw[l_idx]],
                            )
                    else:
                        return {
                            "ok": False,
                            "needs_mapping": True,
                            "error_code": "needs_mapping",
                            "error": "New GL template — please confirm column mapping",
                            "mapping_request": {
                                "document_type": "gl",
                                "template_signature": sig,
                                "sheet_name": "",
                                "headers": [str(c or "").strip() for c in all_rows_raw[l_idx]],
                                "preview_rows": _tl.preview_rows(all_rows_raw, l_idx, limit=20),
                                "suggested_mapping": l_cm,  # 全部猜测(含 amount)· UI 预填
                                "confidence": conf,
                            },
                        }
        if not col_map:
            # ADR-006 · 文件可读但认不出 GL 列(固定词典 + 学习层都没拿到可用表头 · 典型:
            # 无日期列的 A/B/C/D 表)· 不再静默返回 gl_headers_not_found —— 那会被对账流程当
            # "0 行 GL"一路跑到"完成",或在 CSV 路径降级 Gemini 把无表头数据硬读成空日期行参与匹配
            # (凭空造出 matched)。只要还是张表格(≥2 行 + ≥2 列)→ 返回 needs_mapping · 让
            # submit 预检弹"确认列对应"面板(用户手动指认 date/借/贷/科目)。CSV 因此也不再降级 Gemini。
            _tabular = [r for r in (all_rows_raw or []) if any(str(c or "").strip() for c in r)]
            _first_cols = max((len(r) for r in _tabular[:5]), default=0)
            if _tl is not None and len(_tabular) >= 2 and _first_cols >= 2:
                _hdr = 0
                try:
                    _guess = _tl._map_gl_by_header(all_rows_raw[_hdr])
                    _tl._fill_gl_by_shape(all_rows_raw, _hdr, _guess)
                except Exception:  # noqa: BLE001
                    _guess = {}
                try:
                    _sig = _tl.build_header_signature(all_rows_raw[_hdr])
                except Exception:  # noqa: BLE001
                    _sig = ""
                return {
                    "ok": False,
                    "needs_mapping": True,
                    "error_code": "needs_mapping",
                    "error": "New GL template — please confirm column mapping",
                    "mapping_request": {
                        "document_type": "gl",
                        "template_signature": _sig,
                        "sheet_name": "",
                        "headers": [str(c or "").strip() for c in all_rows_raw[_hdr]],
                        "preview_rows": _tl.preview_rows(all_rows_raw, _hdr, limit=20),
                        "suggested_mapping": _guess,
                        "confidence": "low",
                    },
                }
            # v118.35.0.19 · 加 error_code 让前端能翻译成友好文案
            return {
                "ok": False,
                "error_code": "gl_headers_not_found",
                "error": "Cannot detect GL column headers",
            }

    rows = []
    accounts_seen = set()
    opening = 0.0
    closing = 0.0
    gl_opening_found = False
    last_row_date = None  # carry-forward for blank date cells (Mr.erp style)
    last_balance_seen = None  # BUG-FIX-T2 v118.35.0.43 · 给 closing 兜底用最后一笔交易行的余额

    for row in all_rows_raw[header_idx + 1 :]:
        if not any(row):
            continue
        row_list = [str(c or "").strip() for c in row]
        # 期初余额行 · 我们的固定模板把『期初』标签放日期列(4 语:期初/Opening/ยอดยกมา/繰越),
        # 独立识别(不依赖 _GL_SKIP_KW 含各语 · zh/ja 不在该词典里 → 此前期初读 0 / closing 全错)。
        if any(kw in " ".join(row_list[:4]).lower() for kw in _GL_OPENING_KW):
            # BUG-FIX-T2 v118.35.0.43 · 期初优先读 balance 列(我们的模板/Mr.erp 把期初放 คงเหลือ 列)
            bal_idx = col_map.get("balance", -1)
            if bal_idx >= 0 and bal_idx < len(row_list) and row_list[bal_idx]:
                opening = _to_float(row_list[bal_idx])
                gl_opening_found = True
            else:
                # fallback · credit - debit(兼容期初放借贷列的格式)
                cr_idx = col_map.get("credit", -1)
                dr_idx = col_map.get("debit", -1)
                if cr_idx >= 0 and cr_idx < len(row_list):
                    cr = _to_float(row_list[cr_idx])
                    dr = _to_float(
                        row_list[dr_idx] if dr_idx >= 0 and dr_idx < len(row_list) else 0
                    )
                    opening = cr - dr  # net opening
                    gl_opening_found = True
            continue
        if _is_gl_skip_row(row_list):
            continue  # 其余汇总/结转行(ยอดยกไป/subtotal/总计)· 非交易 · 跳过

        # Extract fields
        d_str = (
            row_list[col_map["date"]]
            if "date" in col_map and col_map["date"] < len(row_list)
            else ""
        )
        d = _parse_date(d_str) if d_str else None
        if d is not None:
            last_row_date = d
        elif last_row_date is not None:
            d = last_row_date  # carry-forward blank date (Mr.erp prints date once per day)
        else:
            continue

        doc_no = (
            row_list[col_map["doc_no"]]
            if "doc_no" in col_map and col_map["doc_no"] < len(row_list)
            else ""
        )
        desc = (
            row_list[col_map["description"]]
            if "description" in col_map and col_map["description"] < len(row_list)
            else ""
        )
        debit = _to_float(
            row_list[col_map["debit"]]
            if "debit" in col_map and col_map["debit"] < len(row_list)
            else 0
        )
        credit = _to_float(
            row_list[col_map["credit"]]
            if "credit" in col_map and col_map["credit"] < len(row_list)
            else 0
        )
        # ADR-006 S6b · 单列净额(Net Movement)· 无独立借/贷列 → 按符号拆:正=借方 负=贷方
        # (GL "movement" 列正数=借方增加的通用约定 · 让单列净额 GL 也能解析而非读不到)
        if (
            debit == 0.0
            and credit == 0.0
            and "amount" in col_map
            and col_map["amount"] < len(row_list)
        ):
            _amt = _to_float(row_list[col_map["amount"]])
            if _amt > 0:
                debit = _amt
            elif _amt < 0:
                credit = abs(_amt)

        # Account code: from column or auto-extract from description
        acct = ""
        if "account" in col_map and col_map["account"] < len(row_list):
            acct = str(row_list[col_map["account"]]).strip()
        if not acct:
            acct = _extract_acct_code(doc_no) or _extract_acct_code(desc)

        if debit == 0.0 and credit == 0.0:
            continue

        # Filter by account_code if specified
        if account_code and acct and not acct.startswith(account_code):
            continue

        accounts_seen.add(acct or "?")
        rows.append(
            GlRow(
                date=d,
                doc_no=doc_no,
                account_code=acct,
                description=desc,
                debit=abs(debit),
                credit=abs(credit),
            )
        )
        # BUG-FIX-T2 v118.35.0.43 · 顺手记最后一笔的 balance(给下面 closing 兜底用)
        if (
            "balance" in col_map
            and col_map["balance"] < len(row_list)
            and row_list[col_map["balance"]]
        ):
            last_balance_seen = _to_float(row_list[col_map["balance"]])

    # Calculate opening/closing if not found
    if not gl_opening_found:
        opening = 0.0
    # 逐行运行余额(期初+累计借−贷)· 给导出"总账余额列"· 不参与匹配 · 银行账 GL debit=存入抬升
    _bal = opening
    for _r in rows:
        _bal = round(_bal + _r.debit - _r.credit, 2)
        _r.balance = _bal
    # BUG-FIX-T2 v118.35.0.43 · closing 优先用 balance 列最后一笔(防方向算反 · 资产 vs 收入科目)
    # 老公式 opening + credit - debit 对收入科目正确 · 对资产科目反 · balance 列直接读最稳
    # 没识别 balance 列(老文件无 คงเหลือ header)走老公式 · 0 regression
    if last_balance_seen is not None:
        closing = round(last_balance_seen, 2)
    else:
        total_credit = sum(r.credit for r in rows)
        total_debit = sum(r.debit for r in rows)
        closing = round(opening + total_credit - total_debit, 2)

    return {
        "ok": True,
        "rows": rows,
        "accounts": sorted(accounts_seen - {"?"}),
        "opening": opening,
        "closing": closing,
        "row_count": len(rows),
    }
