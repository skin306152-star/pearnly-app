# -*- coding: utf-8 -*-
"""
services/recon/bank_stmt_xlsx.py · Pearnly

Direct Excel/CSV bank-statement parser: header detection, per-sheet account
and opening-balance scan, row mapping to StatementRow. Shared table I/O lives
in bank_table_io; template-learning fallback is imported lazily.
"""

from typing import List, Dict, Any, Optional

from services.recon.bank_recon_types import StatementRow
from services.recon.bank_recon_utils import _to_float, _parse_date
from services.recon.bank_table_io import (
    _hit,
    _is_summary_row,
    _load_excel_all_sheets,
    _load_csv_sheets,
)
from services.recon.bank_stmt_balance import (
    _correct_direction_from_balance,
    _verify_row_balances,
    _repair_amount_from_balance,
)

# v118.35.0.19 · 银行流水 xlsx 直读 fallback · 表头列名词典(4 语)
_STMT_DATE_H = {"วันที่", "วัน", "date", "trans date", "transaction date", "日期", "交易日", "ngày"}
_STMT_DESC_H = {
    "รายการ",
    "รายละเอียด",
    "description",
    "detail",
    "particulars",
    "narration",
    "memo",
    "摘要",
    "描述",
    "交易摘要",
    "diễn giải",
}
_STMT_WITHDRAW_H = {
    "ถอนเงิน",
    "ถอน",
    "withdrawal",
    "withdrawals",
    "debit",
    "dr",
    "out",
    "paid out",
    "取款",
    "出账",
    "支出",
    "借方",
    "rút",
}
_STMT_DEPOSIT_H = {
    "ฝากเงิน",
    "ฝาก",
    "deposit",
    "deposits",
    "credit",
    "cr",
    "in",
    "paid in",
    "存款",
    "入账",
    "收入",
    "贷方",
    "gửi",
}
_STMT_BALANCE_H = {"ยอดคงเหลือ", "คงเหลือ", "balance", "running balance", "余额", "结余", "số dư"}
# v118.35.0.55 · 单一带符号金额列(KTB 等:正=存款 负=取款)· 无独立存/取列时用它
_STMT_AMOUNT_H = {"amount", "จำนวนเงิน", "จำนวน", "金额", "金額", "số เงิน", "số tiền"}


def _map_bank_stmt_cols(header_row: List) -> Dict[str, int]:
    """v118.35.0.19 · 识别银行流水 Excel 表头列(zh/th/en/ja/vi)"""
    col_map: Dict[str, int] = {}
    for i, cell in enumerate(header_row):
        h = str(cell or "").strip().lower()
        if not h:
            continue
        if "date" not in col_map and _hit(h, _STMT_DATE_H):
            col_map["date"] = i
        elif "description" not in col_map and _hit(h, _STMT_DESC_H):
            col_map["description"] = i
        elif "withdrawal" not in col_map and _hit(h, _STMT_WITHDRAW_H):
            col_map["withdrawal"] = i
        elif "deposit" not in col_map and _hit(h, _STMT_DEPOSIT_H):
            col_map["deposit"] = i
        elif "balance" not in col_map and _hit(h, _STMT_BALANCE_H):
            col_map["balance"] = i
        elif "amount" not in col_map and _hit(h, _STMT_AMOUNT_H):
            col_map["amount"] = i
    return col_map


def _find_stmt_header(raw_rows):
    """v118.35.0.55 · 前 16 行找流水表头(KTB 等表头在第 11 行)· 返回 (idx, col_map)"""
    for i, row in enumerate(raw_rows[:16]):
        row_list = [str(c or "").strip() for c in row]
        cm = _map_bank_stmt_cols(row_list)
        if (
            "date" in cm
            and "balance" in cm
            and ("withdrawal" in cm or "deposit" in cm or "amount" in cm)
        ):
            return i, cm
    return -1, {}


_STMT_ACCT_LABEL = (
    "account no",
    "account number",
    "เลขที่บัญชี",
    "บัญชีเงินฝาก",
    "账号",
    "账户",
    "口座",
)


def _extract_sheet_account(raw_rows, header_idx, sheet_name=""):
    """v118.35.0.61 · 从表头之前的行里找『Account No. : xxx』· 找不到退回 sheet 名。
    多账户 .xls 每个 sheet 一个账户 · 账户号在表头上方的 label 行。"""
    for raw in raw_rows[: max(header_idx, 0)]:
        cells = [str(c or "").strip() for c in raw]
        for i, cell in enumerate(cells):
            cl = cell.lower()
            if any(lbl in cl for lbl in _STMT_ACCT_LABEL):
                # 同行右侧第一个非空值即账户号
                for v in cells[i + 1 :]:
                    if v:
                        return v
    # 退回 sheet 名(KTB 把账户号当 sheet 名:984-2-99825-8)
    sn = str(sheet_name or "").strip()
    return sn if any(ch.isdigit() for ch in sn) else ""


_STMT_OPEN_KW = (
    "ยอดยกมา",
    "ยกยอด",
    "ยกมา",
    "brought forward",
    "balance b/f",
    "b/f",
    "opening",
    "期初",
    "上期",
)


def _scan_preheader_opening(raw_rows, header_idx):
    """v118.35.0.61 · 表头上方找带标签的期初余额(ยกมา / opening / b/f)。
    KTB 多账户 .xls 把期初放在表头上方汇总区(ยกมา -7,409,714.58)· 返回 float 或 None。"""
    for raw in raw_rows[: max(header_idx, 0)]:
        cells = [str(c or "").strip() for c in raw]
        line = " ".join(cells).lower()
        if any(kw in line for kw in _STMT_OPEN_KW):
            for c in cells:
                v = _to_float(c)
                if v != 0.0 or c.strip() in ("0", "0.00", "0.0"):
                    return v
    return None


def _parse_stmt_sheet(raw_rows, header_idx, col_map, filename, account_no=""):
    """v118.35.0.55 · 解析单个 sheet 的流水行 · 返回 (rows, opening or None, closing or None)
    支持单一带符号 amount 列(正=存 负=取)· v118.35.0.61 每行打 account_no 标签 +
    表头上方期初 + 末期取最后一个『有余额』的行(末行常是无余额的 Sweep 行)"""
    rows: List[StatementRow] = []
    # v118.35.0.61 · 先看表头上方有没有带标签的期初(KTB 等汇总区)
    opening_balance = _scan_preheader_opening(raw_rows, header_idx)
    opening_found = opening_balance is not None
    last_valid_closing = None
    last_date = None
    d_idx = col_map["date"]
    bal_idx = col_map.get("balance", -1)  # ADR-006 · 学习层映射可能无余额列 · 缺则按 0(不崩)
    wd_idx = col_map.get("withdrawal", -1)
    dp_idx = col_map.get("deposit", -1)
    amt_idx = col_map.get("amount", -1)
    desc_idx = col_map.get("description", -1)

    def _cell(row_list, idx):
        return row_list[idx] if 0 <= idx < len(row_list) else ""

    for raw in raw_rows[header_idx + 1 :]:
        if not any(raw):
            continue
        row_list = [str(c or "").strip() for c in raw]
        d_str = _cell(row_list, d_idx)
        d = _parse_date(d_str) if d_str else None
        if d is not None:
            last_date = d
        bal_raw = _cell(row_list, bal_idx)
        balance = _to_float(bal_raw)
        withdrawal = _to_float(_cell(row_list, wd_idx)) if wd_idx >= 0 else 0.0
        deposit = _to_float(_cell(row_list, dp_idx)) if dp_idx >= 0 else 0.0
        # 单一带符号 amount 列(无独立存/取列)· 正=存款 负=取款
        if amt_idx >= 0 and wd_idx < 0 and dp_idx < 0:
            amt = _to_float(_cell(row_list, amt_idx))
            if amt > 0:
                deposit = amt
            elif amt < 0:
                withdrawal = abs(amt)
        desc = _cell(row_list, desc_idx)

        # ADR-006 · 合计/汇总行(รวมยอด/Total/合计)整行跳过 —— 否则其余额(常是大额合计,
        # 如 รวมยอด 余额=1,651,950)会被当成期末污染余额链(真实小现金件 เงินสดย่อย 实测)。
        # 此前 summary 过滤在 parse_bank_stmt_xlsx_direct 里事后做 · last_valid_closing 已被污染。
        if desc and _is_summary_row(desc):
            continue

        is_opening = (
            not opening_found
            and d is None
            and withdrawal == 0.0
            and deposit == 0.0
            and balance != 0.0
        ) or (
            not opening_found
            and desc
            and any(
                # ยกยอด:泰文"承前结转/上期结转"另一常见写法(ยกยอดมา)· 之前漏 → 被当存款计入
                kw in desc.lower()
                for kw in ["ยอดยกมา", "ยกยอด", "ยกมา", "brought forward", "opening", "期初"]
            )
        )
        if is_opening:
            opening_balance = balance
            opening_found = True
            continue
        if d is None and last_date is None:
            continue
        if withdrawal == 0.0 and deposit == 0.0:
            continue
        rows.append(
            StatementRow(
                date=d if d is not None else last_date,
                description=desc,
                withdrawal=withdrawal,
                deposit=deposit,
                balance=balance,
                source_file=filename,
                account_no=account_no,
            )
        )
        # v118.35.0.66 · 区分『余额真的是 0』(Sweep 归零户合法期末)和『余额单元格空着』。
        # row_list 用 str(c or "") 会把数值 0.0 变成 ""(0.0 为假值)→ 此前把归零户那一行
        # 的期末 0 当成空 · 误退回上一行余额(KTB 8258 期末被报成 3845.3 而非真值 0)。
        # 这里直接看『原始单元格』判空 · 而非被 or 改写过的字符串。
        raw_bal_cell = raw[bal_idx] if 0 <= bal_idx < len(raw) else None
        if raw_bal_cell is not None and str(raw_bal_cell).strip() != "":
            last_valid_closing = balance
    return rows, opening_balance, last_valid_closing


def parse_bank_stmt_xlsx_direct(
    file_bytes: bytes,
    filename: str,
    tenant_id: Optional[str] = None,
    allow_ai: bool = False,
    api_key: str = "",
) -> Dict[str, Any]:
    """v118.35.0.55 · 银行流水 Excel 直读(零成本 · 跳过 Gemini)· 多 sheet 版

    遍历『所有』sheet(用户可能把多个账户塞一个文件 · 每 sheet 一个账户)·
    每个 sheet 独立找表头 + 解析 · 合并所有行。
    支持:.xlsx + 旧 .xls(xlrd)· 表头在前 16 行任意位置 · 单一带符号 amount 列。

    ADR-006 模板学习层:固定词典 _find_stmt_header 找不到表头时,不再直接放弃,而是
      ① 查已存映射(tenant + signature 命中)→ 直接套
      ② 本地推断(同义词更全 + 数据形状 + 余额链校验)· 高信心 → 套 + 自动存
      ③ 仍不行 → 返回 needs_mapping(带预览 + 系统猜测)· 交上层弹"确认列对应"
    现有能识别的文件走原 _find_stmt_header · 一行不变 = 零回归。
    """
    sheets = _load_excel_all_sheets(file_bytes)
    if not sheets:
        # ADR-006 S6a · Excel 读不出且是 CSV/TSV → 用 CSV 加载器(编码+分隔符)· 同一套三层识别
        _ext = (filename or "").lower().rsplit(".", 1)[-1]
        if _ext in ("csv", "tsv", "txt"):
            sheets = _load_csv_sheets(file_bytes)
    if not sheets:
        return {
            "ok": False,
            "error_code": "file_unreadable",
            "error": "Cannot read Excel/CSV (legacy .xls / corrupt / unsupported format)",
        }
    # ADR-006 · 学习层惰性 import(防循环 · 失败不致命退回原行为)
    try:
        from services.importer import template_learning as _tl, template_store as _ts
    except Exception:  # noqa: BLE001
        _tl = _ts = None
    needs_mapping_candidate: Optional[Dict[str, Any]] = None

    # v118.35.0.61 · 分账户解析 + 逐账户独立余额校验。
    # 一个文件可能含多个账户(每 sheet 一个)· 各账户期初/余额链互不相干 ——
    # 此前合并成一条链 + 用首账户期初校验全部 · 真实案例 KTB(8258 期初 -39 /
    # 8606 期初 -740万)余额从几万跳到 -737万整链作废。现在每账户独立 verify。
    accounts: List[Dict[str, Any]] = []  # [{account_no, rows, opening, closing}]
    sheets_with_data = 0
    for _sheet_name, raw_rows in sheets:
        header_idx, col_map = _find_stmt_header(raw_rows)
        if not col_map and _tl is not None:
            # ADR-006 学习层:固定词典没找到 → saved → 本地高信心推断 → 否则记 needs_mapping
            try:
                l_idx, l_cm, conf, _rate, _reasons = _tl.infer_stmt_col_map(raw_rows)
            except Exception:  # noqa: BLE001
                l_idx, l_cm, conf = -1, {}, "low"
            if l_idx >= 0 and l_cm:
                sig = _tl.build_header_signature(raw_rows[l_idx])
                saved = (
                    _ts.find_mapping(tenant_id, "statement", sig) if (tenant_id and _ts) else None
                )
                if saved:
                    header_idx, col_map = l_idx, saved
                elif conf == "high":
                    header_idx, col_map = l_idx, l_cm
                    if tenant_id and _ts:
                        _ts.save_mapping(
                            tenant_id,
                            "statement",
                            sig,
                            l_cm,
                            source="local",
                            sample_headers=[str(c or "") for c in raw_rows[l_idx]],
                        )
                else:
                    # ADR-006 S7 · 本地拿不准(low/medium)· 仅在 submit 预检阶段(allow_ai)
                    # 调一次 Gemini 要列映射 → 余额链把关 → 过才套用 + 存(source="ai")· 同步阻塞
                    # + 要钱,异步 worker 永不触发(allow_ai 默认 False)。失败/校验不过 → needs_mapping。
                    ai_cm = (
                        _tl.suggest_mapping_with_ai(
                            "statement",
                            _sheet_name,
                            raw_rows[l_idx],
                            _tl.preview_rows(raw_rows, l_idx, limit=20),
                            local_guess=l_cm,
                            api_key=api_key,
                            signature=sig,
                        )
                        if allow_ai
                        else None
                    )
                    if ai_cm and _tl.validate_by_balance(raw_rows, l_idx, ai_cm)[0]:
                        header_idx, col_map = l_idx, ai_cm
                        if tenant_id and _ts:
                            _ts.save_mapping(
                                tenant_id,
                                "statement",
                                sig,
                                ai_cm,
                                source="ai",
                                sample_headers=[str(c or "") for c in raw_rows[l_idx]],
                            )
                    elif needs_mapping_candidate is None:
                        needs_mapping_candidate = {
                            "document_type": "statement",
                            "template_signature": sig,
                            "sheet_name": _sheet_name,
                            "headers": [str(c or "").strip() for c in raw_rows[l_idx]],
                            "preview_rows": _tl.preview_rows(raw_rows, l_idx, limit=20),
                            "suggested_mapping": l_cm,
                            "confidence": conf,
                        }
        if not col_map:
            continue  # 该 sheet 无流水表头(汇总页/空页)· 跳过
        acct = _extract_sheet_account(raw_rows, header_idx, _sheet_name)
        s_rows, s_opening, s_closing = _parse_stmt_sheet(
            raw_rows, header_idx, col_map, filename, acct
        )
        # v118.35.0.60 · 跳过底部汇总/合计行(同 PDF 路径)
        s_rows = [r for r in s_rows if not _is_summary_row(r.description)]
        if not s_rows:
            continue
        # v118.35.0.66 · 期初汇总区被银行清空(KTB 8258 那种 ยกมา/คงเหลือ 整块留白 ·
        # 只剩净额 -39.15)时,用首笔交易『余额 − 净额』数学反推期初余额 ——
        # 这是唯一可证的算术(非猜测),给余额链一个正确锚点;否则期初默认 0 会让
        # 第一行无从核对、且期末交叉校验失真,错误悄悄溜过去。
        opening_known = s_opening is not None
        if not opening_known and s_rows[0].balance is not None:
            fr = s_rows[0]
            s_open = round(fr.balance - ((fr.deposit or 0) - (fr.withdrawal or 0)), 2)
            opening_known = True
        else:
            s_open = s_opening if s_opening is not None else 0.0
        closing_known = s_closing is not None
        # 末期:优先用最后一个『有余额』行;退回末行余额
        s_close = s_closing if s_closing is not None else s_rows[-1].balance
        # 关键:每账户用自己的期初做方向纠正 + 余额校验 + 自动修复 · 不跨账户
        _correct_direction_from_balance(s_rows, s_open)
        _verify_row_balances(s_rows, s_open)
        _repair_amount_from_balance(s_rows, s_open)
        accounts.append(
            {
                "account_no": acct,
                "rows": s_rows,
                "opening": s_open,
                "closing": s_close,
                "opening_known": opening_known,
                "closing_known": closing_known,
            }
        )
        sheets_with_data += 1

    if not accounts:
        # ADR-006 · 有"像表格但拿不准"的 sheet → 不报死错 · 交上层弹"确认列对应"
        if needs_mapping_candidate is not None:
            return {
                "ok": False,
                "needs_mapping": True,
                "error_code": "needs_mapping",
                "error": "New template — please confirm column mapping",
                "mapping_request": needs_mapping_candidate,
            }
        return {
            "ok": False,
            "error_code": "stmt_headers_not_found",
            "error": "No bank-statement table found in any sheet",
        }

    all_rows: List[StatementRow] = [r for a in accounts for r in a["rows"]]
    multi_account = len([a for a in accounts if a["account_no"]]) > 1 or len(accounts) > 1
    # 单账户:opening/closing 照旧。多账户:期初/期末取各账户合计(聚合口径 · 配合警告)
    opening_balance = sum(a["opening"] for a in accounts)
    closing_balance = sum(a["closing"] for a in accounts)

    # v118.35.0.66 · .xls 直读路径过去『没有』完整性交叉校验(_audit_completeness 只跑 PDF),
    # 多账户余额链对不上时悄无声息 —— 违背『0 静默错误』铁律。这里逐账户做期末平衡校验:
    #   期初 + Σ存 − Σ取 ?= 期末。对不上 = 可能漏行/读错金额 → 产出 closing_mismatch issue,
    #   路由(recon_routes)会据此自动弹『请核对原件』警告条(已支持 closing_mismatch 类型)。
    comp_issues: List[Dict[str, Any]] = []
    for a in accounts:
        if not (a.get("opening_known") and a.get("closing_known")):
            continue  # 期初/期末有一头没拿到真值 · 无从交叉校验 · 不误报
        sdep = round(sum(r.deposit or 0 for r in a["rows"]), 2)
        swd = round(sum(r.withdrawal or 0 for r in a["rows"]), 2)
        calc = round(a["opening"] + sdep - swd, 2)
        tol = max(1.0, abs(a["closing"]) * 0.001)
        if abs(calc - a["closing"]) > tol:
            comp_issues.append(
                {
                    "type": "closing_mismatch",
                    "calc": calc,
                    "printed": a["closing"],
                    "diff": round(calc - a["closing"], 2),
                    "account": a["account_no"],
                }
            )

    # ADR-006 压测发现 · 行级余额对不上(balance_ok=False)此前只在明细行标 ⚠,摘要不提示 →
    # 用户得逐行翻才发现。这里汇总:有 N 行余额链断 → 产出 balance_break issue,弹显眼警告条。
    _bad_balance = sum(1 for r in all_rows if getattr(r, "balance_ok", None) is False)
    if _bad_balance > 0:
        comp_issues.append({"type": "balance_break", "count": _bad_balance})

    return {
        "ok": True,
        "rows": all_rows,
        "row_count": len(all_rows),
        "opening": opening_balance,
        "closing": closing_balance,
        "bank_code": "generic",
        "parser_version": "bank_recon_v2+xlsx_direct_v3",
        "sheets_parsed": sheets_with_data,
        "accounts": accounts,  # v118.35.0.61 · 分账户明细
        "account_codes": [a["account_no"] for a in accounts if a["account_no"]],
        "multi_account": multi_account,  # v118.35.0.61 · 多账户标志
        "completeness": {
            "ok": len(comp_issues) == 0,  # v118.35.0.66 · 期末交叉校验
            "issues": comp_issues,
        },
        "needs_review": False,
    }
