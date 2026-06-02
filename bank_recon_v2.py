# -*- coding: utf-8 -*-
"""
bank_recon_v2.py · Pearnly · v1.0.0
銀行対照 / Bank Statement vs GL Reconciliation Engine

Supported banks  : KBank · BBL · KKP · KTB · SCB · generic fallback
GL input formats : Excel (.xlsx / .xls) · PDF (pdfplumber → Gemini fallback)
Matching layers  : L1 exact date+amount  · L2 ±3-day tolerance · L3 amount only
Export           : 4-sheet openpyxl · i18n th/en/zh/ja
"""

import io
import re
import json
import logging
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

# v118.35.0.3 · 包装 pipeline 抛出的 pydantic ValidationError · 不再把
# "Input should be a valid string ... https://errors.pydantic.dev/2.13/v/..."
# 整串塞进对账中心红色 toast 给用户看
from services.ocr.error_format import short_error as _short_err

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DATE_TOL_DAYS = 3  # days tolerance for layer-2 matching


# DATA CLASSES · moved to services/recon/bank_recon_types.py
from services.recon.bank_recon_types import (
    StatementRow,
    GlRow,
    BankReconRow,
    BankReconSummary,
)

# CONSTANTS / OCR CACHE / UTILITIES · moved to services/recon/bank_recon_utils.py
from services.recon.bank_recon_utils import (  # noqa: F401  re-export + facade-internal
    AMOUNT_TOL,
    MIN_PLUMBER_ROWS,
    _GEMINI_STMT_CACHE,
    _GEMINI_GL_CACHE,
    _cache_get,
    _cache_put,
    _disk_cache_get,
    _disk_cache_put,
    _to_float,
    _parse_date,
    _amount_matches,
    _day_diff,
    _is_gl_skip_row,
    _detect_bank,
    _BANK_SIGNATURES,
)

# TABLE / PDF I/O · workbook+csv loaders, header match, summary-row, pdf text · moved to bank_table_io.py
from services.recon.bank_table_io import (  # noqa: F401  re-export + facade-internal (_hit/_is_summary_row tested)
    _is_summary_row,
    _hit,
    _load_excel_all_sheets,
    _load_csv_sheets,
    _pdf_extract_text_safe,
)

# ─────────────────────────────────────────────────────────────────────────────
# BANK STATEMENT PARSERS · extractors/text/gemini split to services/recon/bank_stmt_{extract,text,gemini}.py
from services.recon.bank_stmt_extract import (
    _parse_kbank_pages,
    _parse_bbl_pages,
    _parse_generic_pages,
    _parse_stmt_text_coords,
)
from services.recon.bank_stmt_text import (
    _parse_stmt_text_lines,
    _parse_kbank_text_columns,
)
from services.recon.bank_stmt_gemini import _gemini_parse_statement

# STATEMENT BALANCE VERIFY/REPAIR · moved to services/recon/bank_stmt_balance.py
from services.recon.bank_stmt_balance import (
    _stmt_bad_ratio,
    _correct_direction_from_balance,
    _verify_row_balances,
    _repair_amount_from_balance,
    _audit_completeness,
)

# LEGACY ParsedStatement pipeline · moved to services/recon/bank_stmt_legacy.py
from services.recon.bank_stmt_legacy import (  # noqa: F401  re-export (bank_recon_routes.br.*)
    BankTransaction,
    ParsedStatement,
    parsed_from_pipeline_legacy,
    gl_rows_from_pipeline_legacy,
    detect_bank,
    parse_statement_pdf,
)


def parse_bank_statement_pdf(
    file_bytes: bytes, filename: str, api_key: str = "", tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse a bank statement.

    2026-05-21 multi-format refactor: name kept for back-compat but now
    accepts ANY format. .pdf goes through the existing pdfplumber + Gemini
    pipeline. Other formats (Excel / CSV / Word / image / TXT) go through
    services/ocr/pipeline with document_type='bank_statement' so the
    bank-statement prompt + validators block description-column digits
    from being assigned to deposit / withdrawal / balance.

    Strategy for PDF: (1) safe text extraction (2) pdfplumber tables (3) text-line fallback (4) Gemini
    """
    import os as _os

    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext != "pdf":
        return _parse_bank_stmt_via_pipeline(file_bytes, filename, tenant_id=tenant_id)

    # 2026-05-21: PDF bank statement defaults to new pipeline (document_type
    # =bank_statement + validators). Set OCR_PDF_STMT_LEGACY=true to opt back
    # into the existing pdfplumber+Gemini path.
    if _os.environ.get("OCR_PDF_STMT_LEGACY", "").strip().lower() != "true":
        pipeline_result = _parse_bank_stmt_via_pipeline(file_bytes, filename, tenant_id=tenant_id)
        if pipeline_result.get("ok") and pipeline_result.get("rows"):
            return pipeline_result
        logger.warning(
            f"[parse_bank_statement] pipeline yielded "
            f"{pipeline_result.get('row_count')} rows / "
            f"err={pipeline_result.get('error')!r} · falling back to legacy"
        )

    # ── Step 1: extract text safely (immune to pdfplumber KeyError crash) ──
    page_texts = _pdf_extract_text_safe(file_bytes)
    all_text = "\n".join(page_texts)
    bank_code = _detect_bank(all_text) if all_text.strip() else "generic"
    # DEBUG v118.33.11.1
    logger.info(
        f"[stmt_parse][{filename}] pages={len(page_texts)} chars={len(all_text)} bank={bank_code}"
    )
    if all_text.strip():
        logger.info(f"[stmt_parse][{filename}] first600: " + repr(all_text[:600]))
    if all_text.strip():
        try:
            import os

            os.makedirs("/tmp/stmt_debug", exist_ok=True)
            with open(f"/tmp/stmt_debug/{filename}.txt", "w") as _df:
                _df.write(all_text)
        except Exception:
            pass

    # ── Step 2: try pdfplumber table extraction ──
    all_tables: List = []
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not all_text.strip():
                all_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                bank_code = _detect_bank(all_text)
            for p in pdf.pages:
                try:
                    tbls = p.extract_tables() or []
                    all_tables.extend(tbls)
                except Exception:
                    pass  # 该页 extract_tables 失败 · 跳过(每页容错)
    except Exception as e:
        logger.warning(f"pdfplumber stmt [{filename}] skipped: {e}")

    # ── Step 3: table-based parsing ──
    rows: List[StatementRow] = []
    opening = 0.0
    closing = 0.0

    if all_tables:
        if bank_code == "kbank":
            rows, opening, closing = _parse_kbank_pages(all_tables)
        elif bank_code == "bbl":
            rows, opening, closing = _parse_bbl_pages(all_tables)
        else:
            rows, opening, closing = _parse_generic_pages(all_tables)

        if len(rows) < MIN_PLUMBER_ROWS and bank_code == "generic":
            rows2, op2, cl2 = _parse_kbank_pages(all_tables)
            if len(rows2) > len(rows):
                rows, opening, closing = rows2, op2, cl2

    # ── Step 4a: KBank column-stacked text (pdfminer-extracted) ──
    if len(rows) < MIN_PLUMBER_ROWS and all_text.strip() and bank_code == "kbank":
        col_rows, col_op, col_cl = _parse_kbank_text_columns(all_text)
        logger.info(f"[stmt_parse][{filename}] step4a kbank-columns: rows={len(col_rows)}")
        if len(col_rows) > len(rows):
            rows, opening, closing = col_rows, col_op, col_cl
    # ── Step 4b: generic text-line fallback ──
    if len(rows) < MIN_PLUMBER_ROWS and all_text.strip():
        text_rows, text_op, text_cl = _parse_stmt_text_lines(all_text, bank_code)
        logger.info(
            f"[stmt_parse][{filename}] step4b text-line: tbl_rows={len(rows)} text_rows={len(text_rows)} bank={bank_code}"
        )
        if len(text_rows) > len(rows):
            rows, opening, closing = text_rows, text_op, text_cl

    # ── Step 4c: 坐标感知文本解析(密集多页文本 PDF · BAY/SCB 等)v118.35.0.66 ──
    # 行级解析对存/取分立列的文本 PDF 易把列对错位(BAY 314 存全判成取 → 触发 Gemini
    # 再漏读)。坐标解析按表头列 x 归位 · 跨全部页 · 取『行数更多且余额链不更差』者。
    if all_text.strip():
        try:
            coord_rows, coord_op, coord_cl = _parse_stmt_text_coords(file_bytes)
        except Exception as e:
            coord_rows, coord_op, coord_cl = [], 0.0, 0.0
            logger.warning(f"[stmt_parse][{filename}] step4c coords skipped: {e}")
        if coord_rows:
            coord_bad = _stmt_bad_ratio(coord_rows, coord_op)
            cur_bad = _stmt_bad_ratio(rows, opening)
            logger.info(
                f"[stmt_parse][{filename}] step4c coords: rows={len(coord_rows)} "
                f"bad={coord_bad:.2f} vs cur rows={len(rows)} bad={cur_bad:.2f}"
            )
            # 坐标解析行数更多 · 且余额链不比现有更坏 → 采用(更全 + 列对位正确)
            if len(coord_rows) > len(rows) and coord_bad <= max(cur_bad, 0.05):
                rows, opening, closing = coord_rows, coord_op, coord_cl

    # ── Step 5: Gemini fallback ──
    # v118.35.0.52 · 触发条件升级:行数不足 OR 免费解析余额链大面积对不上(列错位 · 如
    # BAY/Krungsri 余额读成 0、KBank 把交易ID当金额)· 用余额链可信度做仲裁 · 取更优者。
    _free_rows, _free_op, _free_cl, _free_bank = rows, opening, closing, bank_code
    _free_bad = _stmt_bad_ratio(rows, opening)
    _need_gemini = (len(rows) < MIN_PLUMBER_ROWS) or (_free_bad > 0.30)
    if _need_gemini:
        logger.info(
            f"[stmt_parse][{filename}] step5 gemini: api_key_present={bool(api_key)} "
            f"text_chars={len(all_text)} free_rows={len(rows)} free_bad={_free_bad:.2f}"
        )
    printed_totals = None  # v118.35.0.63 · 账单印刷页脚汇总(仅 Gemini 路径有)· 完整性交叉校验用
    if _need_gemini and api_key:
        gemini_result = _gemini_parse_statement(file_bytes, filename, api_key)
        g_rows = gemini_result.get("rows") or []
        logger.info(
            f"[stmt_parse][{filename}] step5 gemini result: ok={gemini_result.get('ok')} rows={len(g_rows)}"
        )
        if gemini_result.get("ok") and g_rows:
            g_op = gemini_result.get("opening", opening)
            g_bad = _stmt_bad_ratio(g_rows, g_op)
            # 免费行数不足 → 直接用 Gemini;否则谁的余额链更可信用谁
            if len(_free_rows) < MIN_PLUMBER_ROWS or g_bad < _free_bad:
                logger.info(
                    f"[stmt_parse][{filename}] 采用 Gemini(free_bad={_free_bad:.2f} > gemini_bad={g_bad:.2f})"
                )
                rows = g_rows
                opening = g_op
                closing = gemini_result.get("closing", closing)
                bank_code = gemini_result.get("bank_code", bank_code)
                printed_totals = gemini_result.get("printed_totals")
            else:
                logger.info(
                    f"[stmt_parse][{filename}] 保留免费解析(更可信 · gemini_bad={g_bad:.2f})"
                )
                rows, opening, closing, bank_code = _free_rows, _free_op, _free_cl, _free_bank

    for r in rows:
        r.source_file = filename

    # v118.35.0.60 · 跳过底部汇总/合计行(Total/รวมรายการ/合计)· 不是交易 · 防被当交易误标 + 污染余额链
    #   汇合点统一过滤 · 覆盖 table/text/Gemini 全部解析路径
    rows = [r for r in rows if not _is_summary_row(r.description)]

    # v118.35.0.50 · 先用余额涨跌纠正 OCR 把借贷方向读反的行(必须在余额验证之前)
    _correct_direction_from_balance(rows, opening)

    # v118.33.13.0 · row-by-row balance arithmetic verification
    # For each row: prev_balance + deposit - withdrawal should equal current balance.
    # If it doesn't, set balance_ok=False so the UI can flag for human review.
    _verify_row_balances(rows, opening)
    # v118.35.0.62 · 余额链自动修复『数字读错的金额』· 把可证的 ⚠ 变成自动修正
    _repair_amount_from_balance(rows, opening)
    balance_warn_count = sum(1 for r in rows if r.balance_ok is False)
    low_conf_count = sum(1 for r in rows if r.confidence == "low")
    if balance_warn_count or low_conf_count:
        logger.info(
            f"[stmt_parse][{filename}] verification: "
            f"balance_warn={balance_warn_count} low_conf={low_conf_count} total={len(rows)}"
        )

    if not rows:
        hint = " (PDF has no extractable text)" if not all_text.strip() else ""
        return {
            "ok": False,
            "error": f"No statement rows found in PDF{hint}",
            "rows": [],
            "opening": 0.0,
            "closing": 0.0,
        }

    # v118.35.0.66 · 期初/期末兜底回填:Gemini 有时不回传 opening/closing 字段(实测 AM:
    # 4 笔交易全对、B/F 行也读到了,但 opening/closing 仍是 0 → 汇总区显示 0、期末交叉校验跳过)。
    # 行里已有 B/F 余额 + 末行余额时,数学补回(只在拿到 0/未知时补 · 不覆盖已知值)。
    _OPEN_KW = ("b/f", "brought forward", "ยอดยกมา", "ยกมา", "opening", "期初", "上期")
    if not opening:
        first = rows[0]
        fd = (first.description or "").lower()
        if (
            (first.deposit or 0) == 0
            and (first.withdrawal or 0) == 0
            and first.balance
            and any(k in fd for k in _OPEN_KW)
        ):
            opening = first.balance  # 显式 B/F 行余额
        else:
            fm = next((r for r in rows if (r.deposit or 0) or (r.withdrawal or 0)), None)
            if fm and fm.balance:  # 退路:首笔有动行『余额−净额』反推
                opening = round(fm.balance - ((fm.deposit or 0) - (fm.withdrawal or 0)), 2)
    if not closing:
        closing = next((r.balance for r in reversed(rows) if r.balance), closing)

    # v118.35.0.63 · 完整性交叉校验(印刷合计/笔数 + 期末平衡)· 主动发现漏行
    completeness = _audit_completeness(rows, opening, closing, printed_totals)
    if not completeness["ok"]:
        logger.info(f"[stmt_parse][{filename}] completeness issues: {completeness['issues']}")

    return {
        "ok": True,
        "rows": rows,
        "opening": opening,
        "closing": closing,
        "bank_code": bank_code,
        "row_count": len(rows),
        "balance_warn_count": balance_warn_count,
        "low_conf_count": low_conf_count,
        "completeness": completeness,  # v118.35.0.63
    }


# ─────────────────────────────────────────────────────────────────────────────
# GL PARSERS
# ─────────────────────────────────────────────────────────────────────────────
_GL_DATE_H = {"วันที่", "date", "วัน", "日期"}
_GL_DOC_H = {"ใบสำคัญ", "เลขที่เอกสาร", "doc", "voucher", "reference", "เอกสาร", "凭证", "ref"}
_GL_DESC_H = {"คำอธิบาย", "รายการ", "description", "detail", "รายละเอียด", "摘要"}
_GL_DEBIT_H = {"เดบิต", "เดบิท", "debit", "dr", "借方", "ถอน", "จ่าย"}
_GL_CRED_H = {"เครดิต", "credit", "cr", "贷方", "ฝาก", "รับ"}
_GL_ACCT_H = {"รหัสบัญชี", "account", "gl account", "เลขที่บัญชี", "รหัส", "账号", "科目"}
# BUG-FIX-T2 v118.35.0.43 · balance/余额 列识别 · 给 opening 检测读期初余额用
# (老逻辑只看 debit/credit · Row 2 期初 ยอดยกมา 余额列填 39749.85 没读到 → opening=0 → closing 全错)
_GL_BAL_H = {"คงเหลือ", "ยอดคงเหลือ", "balance", "running balance", "余额", "残高"}

_ACCT_RE = re.compile(r"(?<![\d.])([1-9]\d{3,6}(?:[-–]\d{2,3})?)(?![\d.])")

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


def _map_gl_cols(header_row: List) -> Dict[str, int]:
    col_map: Dict[str, int] = {}
    for i, cell in enumerate(header_row):
        h = str(cell or "").strip().lower()
        if not h:
            continue
        if "date" not in col_map and _hit(h, _GL_DATE_H):
            col_map["date"] = i
        elif "doc_no" not in col_map and _hit(h, _GL_DOC_H):
            col_map["doc_no"] = i
        elif "description" not in col_map and _hit(h, _GL_DESC_H):
            col_map["description"] = i
        elif "debit" not in col_map and _hit(h, _GL_DEBIT_H):
            col_map["debit"] = i
        elif "credit" not in col_map and _hit(h, _GL_CRED_H):
            col_map["credit"] = i
        elif "account" not in col_map and _hit(h, _GL_ACCT_H):
            col_map["account"] = i
        elif "balance" not in col_map and _hit(h, _GL_BAL_H):
            col_map["balance"] = i  # BUG-FIX-T2 v118.35.0.43 · 给 opening 检测读期初余额
    return col_map


def _extract_acct_code(text: str) -> str:
    m = _ACCT_RE.search(str(text or ""))
    return m.group(1) if m else ""


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
        if _is_gl_skip_row(row_list):
            # Check if this is an opening/closing balance row
            desc_idx = col_map.get("description", col_map.get("doc_no", -1))
            desc = row_list[desc_idx] if desc_idx >= 0 and desc_idx < len(row_list) else ""
            if any(kw in desc.lower() for kw in ["ยอดยกมา", "brought forward", "opening"]):
                # BUG-FIX-T2 v118.35.0.43 · 期初余额优先读 balance 列(如 Mr.erp 把期初放 คงเหลือ 列)
                # 老逻辑只读 debit/credit · Row 2 期初 ยอดยกมา 借贷列空 → opening=0 → closing 全错
                bal_idx = col_map.get("balance", -1)
                if bal_idx >= 0 and bal_idx < len(row_list) and row_list[bal_idx]:
                    opening = _to_float(row_list[bal_idx])
                    gl_opening_found = True
                else:
                    # fallback · credit - debit(老逻辑保留 · 兼容期初放借贷列的格式)
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


def _norm_thai(s: str) -> str:
    """v118.33.13.4 · Normalize Thai PUA characters that some PDF fonts emit
    instead of the standard Unicode codepoints. Thai PDFs encode combining
    tone marks in the Private Use Area (U+F70A..U+F712) rather than the
    standard U+0E47..U+0E4D range. The text renders identically but compares
    as a different string, breaking any keyword match against book types
    or other Thai tokens. Maps PUA glyphs back to standard combining marks."""
    if not s:
        return s
    return (
        s.replace("\uf70a", "\u0e48")  # mai-ek
        .replace("\uf70b", "\u0e49")  # mai-tho
        .replace("\uf70c", "\u0e4a")  # mai-tri
        .replace("\uf70d", "\u0e4b")  # mai-chattawa
        .replace("\uf70e", "\u0e4c")  # thantakhat
        .replace("\uf710", "\u0e4d")  # nikhahit
        .replace("\uf711", "\u0e31")  # mai-han-akat
        .replace("\uf712", "\u0e47")  # mai-taikhu
    )


def _is_numeric_tok(tok: str) -> bool:
    """v118.33.13.4 · Strict numeric-token test (unlike _to_float which returns 0.0
    for any garbage input). Accepts comma thousands, paren-negatives, Thai
    dot-thousands ('115.586.50' → 115586.50). Rejects dates, text, dashes, empty."""
    s = (tok or "").strip().replace(",", "")
    if not s or s in {"-", "–", "—"}:
        return False
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    if s.startswith("-"):
        s = s[1:]
    if not s:
        return False
    if s.count(".") > 1:
        last = s.rfind(".")
        s = s[:last].replace(".", "") + s[last:]
    try:
        float(s)
        return True
    except ValueError:
        return False


def _parse_gl_mrerp_table(
    table_rows, account_code: str = ""
) -> Tuple[List["GlRow"], List[str], float]:
    """
    v118.33.13.4 · Parse Mr.erp-style Thai GL PDFs where pdfplumber outputs
    each transaction as a SINGLE merged cell containing the whole row text.

    Row format:
        DD/MM/YY  สมุด  ใบสำคัญ  คำอธิบาย  เดบิท/เครดิต  ยอดคงเหลือ
        (date)    (book)(voucher) (desc...) (amount)      (balance)

    Book types: "รับ"=receipt→debit, "จ่าย"=payment→credit, "ทั่วไป"=general
    (general direction inferred from running-balance delta).

    Special rows:
        • Account header: "1112-01 CA K-BANK006-8-83962-9 ... 215,228.06" → opening
        • Totals/dividers/page-headers → skipped
        • Date is printed only when it changes — subsequent same-day rows omit it
    """
    rows: List[GlRow] = []
    accounts_seen: set = set()
    opening = 0.0
    last_date: Optional[date] = None
    last_balance: Optional[float] = None
    current_acct = ""

    DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
    BOOK_RECEIPT = "รับ"
    BOOK_PAYMENT = "จ่าย"
    BOOK_GENERAL = "ทั่วไป"
    BOOK_TYPES = {BOOK_RECEIPT, BOOK_PAYMENT, BOOK_GENERAL}
    # Header / footer / divider patterns to skip.
    # NB: keywords like "หน้า" (page) appear as a substring inside legitimate
    # transaction descriptions (e.g. "รับล่วงหน้า" = "advance receipt"), so we
    # only use phrase-level patterns that are unique to header/footer rows.
    SKIP_KEYWORDS = (
        "รายงานแยกประเภท",
        "(รวมแผนก)",
        "วันที่จาก",
        "เลขที่บัญชี",
        "รวมทั้งสิ้น",
        "หมายเหตุ ในช่อง",
        "ชื่อบัญชี",
        ">>>>",
        "<<<<",
    )
    # Page header pattern: "หน้า : 1" (always has the colon)
    SKIP_REGEX = re.compile(r"หน้า\s*[:：]\s*\d|^\s*Page\s+\d|^E\s+จะหมายถึง")

    for table_row in table_rows or []:
        # Each pdfplumber row is a list of cells. For Mr.erp PDFs the whole
        # transaction is in cell 0; cells 1+ are typically None or fragments.
        cells = [str(c).strip() for c in table_row if c is not None and str(c).strip()]
        if not cells:
            continue
        # v118.33.13.4 · Normalize Thai PUA tone-marks so book-type matches work
        line = _norm_thai(" ".join(cells).strip())
        if not line:
            continue

        # Skip pure dividers
        if re.match(r"^-+\s*-*$|^=+\s*=*$|^_+$", line):
            continue
        # Skip headers/footers/notes
        if any(kw in line for kw in SKIP_KEYWORDS):
            continue
        if SKIP_REGEX.search(line):
            continue
        # Skip the column-header row
        if ("วันที่" in line and "สมุด" in line) or (
            "เดบิท" in line and "เครดิต" in line and "ยอดคงเหลือ" in line
        ):
            continue
        # Skip pure totals rows: "รวม 1,689,872.00 1,780,000.00" or two numbers only
        if line.startswith("รวม") and len(line.split()) <= 6:
            continue
        if re.match(r"^[\d,]+\.\d+(\s+[\d,]+\.\d+)+\s*$", line):
            continue

        # Account header: "1112-01 CA K-BANK006-8-83962-9 ... 215,228.06"
        # Starts with N-N digits where N is 3-6 digits and a dash
        m_acct = re.match(r"^(\d{3,6}-\d+)\s+", line)
        if m_acct:
            current_acct = m_acct.group(1)
            accounts_seen.add(current_acct)
            nums = re.findall(r"[\d,]+\.\d+", line)
            if nums and not opening:
                opening = _to_float(nums[-1])
                last_balance = opening
            continue
        # Opening-balance keyword line
        if any(kw in line for kw in ("ยอดยกมา", "brought forward", "ยอดคงเหลือยกมา")):
            nums = re.findall(r"[\d,]+\.\d+", line)
            if nums:
                opening = _to_float(nums[-1])
                last_balance = opening
            continue

        # Tokenize on whitespace
        toks = line.split()
        if len(toks) < 4:
            continue

        # Collect contiguous numeric tokens at the RIGHT (strict check — NOT _to_float)
        num_vals: List[float] = []
        cut_idx = len(toks)
        for i in range(len(toks) - 1, -1, -1):
            if _is_numeric_tok(toks[i]):
                num_vals.insert(0, _to_float(toks[i]))
                cut_idx = i
            else:
                break
        if len(num_vals) < 2:
            continue

        balance = num_vals[-1]
        amount = num_vals[-2]
        # If 3 numerics: [debit, credit, balance] explicit format
        explicit_debit = None
        explicit_credit = None
        if len(num_vals) >= 3:
            explicit_debit = num_vals[-3]
            explicit_credit = num_vals[-2]

        # Parse front: DATE? BOOK VOUCHER DESC...
        front = toks[:cut_idx]
        if not front:
            continue

        d: Optional[date] = None
        d_idx = -1
        if DATE_RE.match(front[0]):
            d = _parse_date(front[0])
            if d:
                d_idx = 0
        if d is None:
            d = last_date
        else:
            last_date = d
        if d is None:
            continue

        after = front[d_idx + 1 :] if d_idx >= 0 else front
        if not after:
            continue

        # Book type (อาจมีหรือไม่มี)
        book = ""
        if after[0] in BOOK_TYPES:
            book = after[0]
            after = after[1:]
        if not after:
            continue

        # Voucher number + description (everything else)
        doc_no = after[0]
        desc = " ".join(after[1:]) if len(after) > 1 else ""

        # Determine direction
        if explicit_debit is not None and explicit_credit is not None:
            debit_v = explicit_debit
            credit_v = explicit_credit
        else:
            debit_v = 0.0
            credit_v = 0.0
            if book == BOOK_RECEIPT:
                debit_v = amount
            elif book == BOOK_PAYMENT:
                credit_v = amount
            else:
                # General/unknown: infer from balance delta
                if last_balance is not None:
                    delta = round(balance - last_balance, 2)
                    if abs(delta - amount) <= 0.05:
                        debit_v = amount
                    elif abs(delta + amount) <= 0.05:
                        credit_v = amount
                    else:
                        # Math doesn't pin down direction — default to debit
                        debit_v = amount
                else:
                    debit_v = amount  # default: cash-in

        last_balance = balance

        acct = current_acct or _extract_acct_code(doc_no) or _extract_acct_code(desc) or ""
        if account_code and acct and not acct.startswith(account_code):
            continue
        if debit_v == 0.0 and credit_v == 0.0:
            continue

        accounts_seen.add(acct or "?")
        rows.append(
            GlRow(
                date=d,
                doc_no=doc_no,
                account_code=acct,
                description=desc,
                debit=abs(debit_v),
                credit=abs(credit_v),
            )
        )

    return rows, sorted(accounts_seen - {"?"}), opening


def _gl_direction_sanity_check(rows: List["GlRow"]) -> Optional[str]:
    """v118.33.13.4 · Detect GL files that are clearly NOT a cash-account ledger.

    Bank-reconciliation requires the **cash/bank account** GL — where deposits
    appear as debits and withdrawals as credits. If the user uploads an
    expense-perspective ledger (everything in debit) or revenue-perspective
    (everything in credit), reconciliation will produce 0% match.

    Returns a warning message string if the GL looks one-sided, else None."""
    if not rows or len(rows) < 3:
        return None
    total_debit = sum(r.debit for r in rows)
    total_credit = sum(r.credit for r in rows)
    if total_debit + total_credit == 0:
        return None
    debit_ratio = total_debit / (total_debit + total_credit)
    n_debit = sum(1 for r in rows if r.debit > 0)
    n_credit = sum(1 for r in rows if r.credit > 0)

    # All on one side (no opposite transactions at all)
    if total_credit == 0 and n_debit >= 3:
        return (
            "GL appears to be debit-only (no credit entries). This is likely "
            "an expense or asset ledger, not the cash/bank account ledger. "
            "Bank reconciliation expects the BANK ACCOUNT ledger where "
            "withdrawals appear as credits."
        )
    if total_debit == 0 and n_credit >= 3:
        return (
            "GL appears to be credit-only (no debit entries). This is likely "
            "a revenue or liability ledger, not the cash/bank account ledger."
        )
    # Heavily imbalanced (>= 95% one side) — less certain but worth noting
    if debit_ratio >= 0.95 and total_credit > 0:
        return f"GL is {debit_ratio*100:.0f}% debit-side — verify this is the bank-account ledger."
    if debit_ratio <= 0.05 and total_debit > 0:
        return f"GL is {(1-debit_ratio)*100:.0f}% credit-side — verify this is the bank-account ledger."
    return None


def parse_gl_pdf(
    file_bytes: bytes, filename: str, account_code: str = "", api_key: str = ""
) -> Dict[str, Any]:
    """
    Parse GL from PDF.
    Strategy: (1) extract text safely via pdfminer/pypdf (immune to KeyError('date'))
              (2) try pdfplumber table extraction (may crash on some PDFs — fully isolated)
              (3) Mr.erp-format single-cell row parser (v118.33.13.4)
              (3b) Old column-mapping table parser (fallback)
              (4) Text-line parser fallback
              (5) Gemini fallback if api_key provided
    """
    # ── Step 1: extract raw text independently (never crashes the whole function) ──
    page_texts = _pdf_extract_text_safe(file_bytes)

    # ── Step 2: try pdfplumber table extraction (fully isolated) ──
    all_tables: List = []
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for p in pdf.pages:
                try:
                    tbls = p.extract_tables() or []
                    all_tables.extend(tbls)
                except Exception:
                    pass  # 该页 extract_tables 失败 · 跳过(每页容错)
                if not page_texts:
                    try:
                        page_texts.append(p.extract_text() or "")
                    except Exception:
                        pass  # 该页 extract_text 失败 · 跳过(每页容错)
    except Exception as e:
        logger.warning(f"pdfplumber [{filename}] skipped: {e}")

    # ── Step 3: parse table rows ──
    rows: List[GlRow] = []
    accounts_seen: set = set()
    opening = 0.0

    # v118.33.13.4 · Step 3a · Mr.erp single-cell-row parser (FIRST priority)
    # Many Thai GL PDFs come out of pdfplumber as one merged cell per row
    # containing the entire transaction text. The old per-column mapper can't
    # see headers because everything's in cell 0. We handle that here.
    if all_tables:
        flat_rows = []
        for tbl in all_tables:
            flat_rows.extend(tbl or [])
        mr_rows, mr_accts, mr_open = _parse_gl_mrerp_table(flat_rows, account_code)
        if mr_rows:
            rows = mr_rows
            accounts_seen = set(mr_accts)
            opening = mr_open
            logger.info(
                f"[gl_parse][{filename}] step3a mrerp: rows={len(rows)} accts={len(accounts_seen)}"
            )

    # Step 3b · Fall back to column-mapped table parser (other GL formats where
    # pdfplumber DOES split columns correctly)
    if not rows:
        for table in all_tables:
            if not table or len(table) < 2:
                continue
            col_map: Dict[str, int] = {}
            header_idx = 0
            for i, row in enumerate(table[:5]):
                cm = _map_gl_cols([str(c or "").strip() for c in row])
                if len(cm) >= 2:
                    col_map = cm
                    header_idx = i
                    break
            if not col_map:
                continue

            last_tbl_date = None
            for row in table[header_idx + 1 :]:
                if not row:
                    continue
                row_list = [str(c or "").strip() for c in row]
                if _is_gl_skip_row(row_list):
                    continue
                d_str = (
                    row_list[col_map["date"]]
                    if "date" in col_map and col_map["date"] < len(row_list)
                    else ""
                )
                d = _parse_date(d_str) if d_str else None
                if d is not None:
                    last_tbl_date = d
                elif last_tbl_date is not None:
                    d = last_tbl_date
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
                acct = ""
                if "account" in col_map and col_map["account"] < len(row_list):
                    acct = str(row_list[col_map["account"]]).strip()
                if not acct:
                    acct = _extract_acct_code(doc_no) or _extract_acct_code(desc)
                if debit == 0.0 and credit == 0.0:
                    continue
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
        if rows:
            logger.info(
                f"[gl_parse][{filename}] step3b col-map: rows={len(rows)} accts={len(accounts_seen)}"
            )

    # ── Step 4: text-line fallback (Mr.erp Thai GL format) ──
    if len(rows) < MIN_PLUMBER_ROWS and page_texts:
        full_text = "\n".join(page_texts)
        text_rows, text_accts, text_opening = _parse_gl_text_lines(full_text, account_code)
        if len(text_rows) >= len(rows):
            rows = text_rows
            accounts_seen = set(text_accts)
            opening = text_opening
            logger.info(f"[gl_parse][{filename}] step4 text-line: rows={len(rows)}")

    # ── Step 5: Gemini fallback ──
    if len(rows) < MIN_PLUMBER_ROWS and api_key:
        return _gemini_parse_gl(file_bytes, filename, account_code, api_key)

    if not rows:
        hint = " (PDF has no extractable text)" if not any(t.strip() for t in page_texts) else ""
        return {"ok": False, "error": f"No GL rows found in PDF{hint}", "rows": []}

    total_credit = sum(r.credit for r in rows)
    total_debit = sum(r.debit for r in rows)
    closing = round(opening + total_debit - total_credit, 2)

    # v118.33.13.4 · Direction sanity check — warn when GL is one-sided
    direction_warning = _gl_direction_sanity_check(rows)
    if direction_warning:
        logger.warning(f"[gl_parse][{filename}] {direction_warning}")
    result = {
        "ok": True,
        "rows": rows,
        "accounts": sorted(accounts_seen - {"?"}),
        "opening": opening,
        "closing": closing,
        "row_count": len(rows),
    }
    if direction_warning:
        result["warning"] = direction_warning
    return result


def _parse_gl_text_lines(text: str, account_code: str = "") -> Tuple[List[GlRow], List[str], float]:
    """
    Text-line fallback for Mr.erp Thai GL PDFs.
    Format: วันที่  สมุด  ใบสำคัญ  คำอธิบาย  เดบิต  เครดิต  สถานะ  ยอดคงเหลือ
    Date is printed once per day; subsequent same-day rows have blank date.
    Returns (rows, account_list, opening_balance).
    """
    rows: List[GlRow] = []
    accounts_seen: set = set()
    opening = 0.0
    last_date: Optional[date] = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Skip header/report title/total lines
        low = line.lower()
        if any(
            kw in low
            for kw in [
                "รายงาน",
                "account",
                "page",
                "หน้า",
                "บัญชี:",
                "ชื่อ",
                "รวม",
                "total",
                "สรุป",
                "หมายเหตุ",
                "note",
            ]
        ):
            continue

        # Account code header: "1112-01 CA K-BANK006-8-83962-9 215,228.06"
        # Starts with 3-6 digits then dash (NOT a date like "02/06/68")
        if re.match(r"^\d{3,6}-\d", line):
            nums = re.findall(r"[\d,]+\.\d+", line)
            if nums and not opening:
                opening = _to_float(nums[-1])
            continue

        # Opening balance line
        if any(kw in line for kw in ["ยอดยกมา", "brought forward", "ยอดคงเหลือยกมา"]):
            nums = re.findall(r"[\d,]+\.\d+", line)
            if nums:
                opening = _to_float(nums[-1])
            continue

        # Split on 2+ whitespace to get token columns
        parts = re.split(r"\s{2,}", line)
        if len(parts) < 3:
            continue

        # Try to identify date token (first or second part)
        d = None
        d_offset = 0
        for offset in range(min(2, len(parts))):
            d = _parse_date(parts[offset])
            if d is not None:
                d_offset = offset
                last_date = d
                break

        if d is None:
            if last_date is not None:
                d = last_date
                d_offset = -1  # no date token consumed
            else:
                continue

        # After date token, remaining parts: book, doc_no, description, amounts...
        rest = parts[d_offset + 1 :] if d_offset >= 0 else parts
        if len(rest) < 2:
            continue

        # Find numeric tokens from the right, skipping D/C/DR/CR status tokens
        num_vals: List[float] = []
        num_start = len(rest)
        status_tok = ""
        for i in range(len(rest) - 1, -1, -1):
            tok = rest[i].strip()
            tok_up = tok.upper()
            # Capture status token (D/C/DR/CR) but don't break
            if tok_up in ("D", "C", "DR", "CR") and not status_tok:
                status_tok = tok_up
                continue
            tok_clean = tok.replace(",", "")
            if re.match(r"^\d+(\.\d+)?$", tok_clean):
                num_vals.insert(0, float(tok_clean))
                num_start = i
            elif len(num_vals) > 0:
                break

        # Need at least 2 numerics (amount + balance, or debit + credit + balance)
        if len(num_vals) < 2:
            continue

        # Determine debit/credit using status token or positional heuristic
        debit = credit = 0.0
        if status_tok in ("D", "DR"):
            # Amount is debit; last numeric is balance, second-to-last is amount
            debit = num_vals[-2]
            credit = 0.0
        elif status_tok in ("C", "CR"):
            credit = num_vals[-2]
            debit = 0.0
        else:
            # No explicit status: 3 numerics → [debit, credit, balance]; 2 → [amount, balance]
            if len(num_vals) >= 3:
                debit = num_vals[-3]
                credit = num_vals[-2]
            else:
                # 2 numerics, no status — use first as debit (common for debit-only GL lines)
                debit = num_vals[-2]
                credit = 0.0

        if debit == 0.0 and credit == 0.0:
            continue

        desc_parts = rest[:num_start]
        doc_no = desc_parts[0] if desc_parts else ""
        desc = " ".join(desc_parts[1:]) if len(desc_parts) > 1 else doc_no

        acct = _extract_acct_code(doc_no) or _extract_acct_code(desc)
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

    return rows, sorted(accounts_seen - {"?"}), opening


def _gemini_parse_gl(
    file_bytes: bytes, filename: str, account_code: str, api_key: str
) -> Dict[str, Any]:
    """Gemini fallback for GL PDF parsing."""
    try:
        import google.generativeai as genai
        import base64

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        b64 = base64.b64encode(file_bytes).decode()
        acct_hint = (
            f" Filter to account code starting with '{account_code}'." if account_code else ""
        )
        prompt = (
            "This is a General Ledger (GL) document.{hint} "
            "Extract ALL transaction rows as JSON with keys:\n"
            '  "opening_balance": number,\n'
            '  "accounts": [list of account codes found],\n'
            '  "rows": [{{date:"YYYY-MM-DD", doc_no:string, account_code:string, '
            "description:string, debit:number, credit:number}}]\n"
            "Return ONLY valid JSON."
        ).format(hint=acct_hint)

        # v118.35.0.62 · temperature=0 · GL 抽取同样要确定性(同源 PDF 每次结果一致)
        resp = model.generate_content(
            [{"mime_type": "application/pdf", "data": b64}, prompt],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "candidate_count": 1,
                "max_output_tokens": 32768,
            },
        )
        text = (resp.text or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text).rstrip("`").strip()
        data = json.loads(text)

        raw_rows = data.get("rows") or []
        rows = []
        accounts_seen = set()
        for r in raw_rows:
            d = _parse_date(str(r.get("date", "")))
            if d is None:
                continue
            acct = str(r.get("account_code", "")).strip()
            if account_code and acct and not acct.startswith(account_code):
                continue
            accounts_seen.add(acct or "?")
            rows.append(
                GlRow(
                    date=d,
                    doc_no=str(r.get("doc_no", "")),
                    account_code=acct,
                    description=str(r.get("description", "")),
                    debit=float(r.get("debit", 0) or 0),
                    credit=float(r.get("credit", 0) or 0),
                )
            )

        opening = float(data.get("opening_balance", 0) or 0)
        closing = round(opening + sum(r.credit for r in rows) - sum(r.debit for r in rows), 2)
        return {
            "ok": True,
            "rows": rows,
            "accounts": sorted(accounts_seen - {"?"}),
            "opening": opening,
            "closing": closing,
            "row_count": len(rows),
        }

    except Exception as e:
        logger.warning(f"_gemini_parse_gl failed: {e}")
        return {"ok": False, "rows": [], "error": str(e)}


def parse_gl(
    file_bytes: bytes,
    filename: str,
    account_code: str = "",
    api_key: str = "",
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Route to Excel / PDF / pipeline GL parser based on file extension.

    2026-05-21 multi-format refactor:
    - .xlsx / .xls / .xlsm → parse_gl_excel (structural)
    - .pdf                 → parse_gl_pdf   (existing Gemini path)
    - .csv / .tsv / .docx / .doc / .txt / images → unified services/ocr/pipeline
      with document_type='general_ledger' so prompt + validators block
      description-column numbers (e.g. 6091) from being parsed as amounts.
    """
    import os as _os

    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext in ("xlsx", "xls", "xlsm"):
        result = parse_gl_excel(file_bytes, filename, account_code, tenant_id=tenant_id)
    elif ext in ("csv", "tsv"):
        # ADR-006 S6b · GL CSV 先走学习层(免费)· ok 或 needs_mapping 直接返回;
        # 只有真读不出(非 needs_mapping 失败)才降级 Gemini pipeline。
        result = parse_gl_excel(file_bytes, filename, account_code, tenant_id=tenant_id)
        if not result.get("ok") and not result.get("needs_mapping"):
            logger.info(f"[parse_gl] csv direct miss · falling back to pipeline: {filename}")
            result = _parse_gl_via_pipeline(file_bytes, filename, account_code)
    elif ext == "pdf":
        # 2026-05-21: PDF GL defaults to new pipeline (document_type=
        # general_ledger + validators). OCR_PDF_GL_LEGACY=true rolls back
        # to the previous Gemini Vision parse_gl_pdf path.
        if _os.environ.get("OCR_PDF_GL_LEGACY", "").strip().lower() == "true":
            result = parse_gl_pdf(file_bytes, filename, account_code, api_key)
        else:
            result = _parse_gl_via_pipeline(file_bytes, filename, account_code)
            if not (result.get("ok") and result.get("rows")):
                logger.warning(
                    f"[parse_gl] pipeline yielded {result.get('row_count')} rows / "
                    f"err={result.get('error')!r} · falling back to parse_gl_pdf"
                )
                result = parse_gl_pdf(file_bytes, filename, account_code, api_key)
    else:
        result = _parse_gl_via_pipeline(file_bytes, filename, account_code)

    if result.get("ok"):
        for r in result.get("rows", []):
            r.source_file = filename

    return result


def _parse_bank_stmt_via_pipeline(
    file_bytes: bytes, filename: str, tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """Bank-recon-v2 adapter: route non-PDF bank statements through the
    unified pipeline with document_type='bank_statement', then convert to
    List[StatementRow] so the rest of bank-v2/run consumes it unchanged.

    Validators guarantee deposit/withdrawal/balance came from their
    respective columns — description / reference / account-number digits
    are rejected and cleared before this adapter runs.
    """
    try:
        from services.ocr.pipeline import (
            run_on_image_bytes as _run_image,
            run_on_table_bytes as _run_table,
            IMAGE_EXTENSIONS,
            TABLE_EXTENSIONS,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
    except ImportError as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error": f"pipeline import failed: {e}",
        }

    ext_dot = "." + (filename or "").lower().rsplit(".", 1)[-1]

    # v118.35.0.19 · xlsx/xls 优先走直读 fallback(零成本 · 跳 Gemini)
    # 用户上传自家导出 / 银行下载 / 自己整理的 Excel · 表头清晰时直读即可
    # 直读不命中(表头识别不出) → 自动降级到 Gemini pipeline
    if ext_dot in (".xlsx", ".xls", ".xlsm", ".csv", ".tsv"):
        direct = parse_bank_stmt_xlsx_direct(file_bytes, filename, tenant_id=tenant_id)
        if direct.get("ok"):
            logger.info(
                f"[stmt_parse][{filename}] xlsx_direct OK · {direct['row_count']} rows · skip Gemini"
            )
            return direct
        # ADR-006 · 新模板拿不准 → 走"确认列对应"· 不烧 Gemini · 原样上抛
        if direct.get("needs_mapping"):
            logger.info(f"[stmt_parse][{filename}] xlsx_direct needs_mapping · skip Gemini")
            return direct
        logger.info(
            f"[stmt_parse][{filename}] xlsx_direct miss({direct.get('error_code')}) · falling back to Gemini"
        )

    try:
        if ext_dot in IMAGE_EXTENSIONS:
            pr = _run_image(file_bytes, document_type="bank_statement")
        elif ext_dot in TABLE_EXTENSIONS:
            pr = _run_table(file_bytes, filename=filename or "stmt", document_type="bank_statement")
        else:
            return {
                "ok": False,
                "rows": [],
                "row_count": 0,
                "bank_code": "generic",
                "error_code": "file_not_supported",
                "error": f"unsupported format {ext_dot}",
            }
    except Exception as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error_code": "ocr_failed",
            "error": _short_err(e),
        }

    legacy = pipeline_result_to_legacy_dict(pr)
    pages = legacy.get("pages") or []
    if not pages:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error": "no pages parsed",
        }
    doc = (pages[0] or {}).get("document") or {}
    bank_name_l = (doc.get("bank_name") or "").lower()
    bank_code = "generic"
    for code, sigs in _BANK_SIGNATURES.items():
        if any(s in bank_name_l or s in (doc.get("bank_name") or "") for s in sigs):
            bank_code = code
            break

    rows: List[StatementRow] = []
    for e in doc.get("entries") or []:
        deposit = _to_float(e.get("deposit"))
        withdrawal = _to_float(e.get("withdrawal"))
        balance = _to_float(e.get("balance"))
        if deposit == 0.0 and withdrawal == 0.0:
            continue
        tx_date = None
        if e.get("transaction_date"):
            try:
                yy, mm, dd = e["transaction_date"].split("-")
                tx_date = date(int(yy), int(mm), int(dd))
            except (ValueError, AttributeError):
                tx_date = _parse_date(e.get("transaction_date_raw") or "")
        rows.append(
            StatementRow(
                date=tx_date,
                description=e.get("description") or "",
                withdrawal=withdrawal,
                deposit=deposit,
                balance=balance,
                source_file=filename,
            )
        )
    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "bank_code": bank_code,
        "parser_version": "bank_recon_v2+pipeline_v1",
        "needs_review": legacy.get("_needs_review", False),
    }


def _parse_gl_via_pipeline(
    file_bytes: bytes, filename: str, account_code: str = ""
) -> Dict[str, Any]:
    """Bank-recon-v2 adapter: route GL through services/ocr/pipeline with
    document_type='general_ledger', then convert to List[GlRow]."""
    try:
        from services.ocr.pipeline import (
            run_on_image_bytes as _run_image,
            run_on_table_bytes as _run_table,
            IMAGE_EXTENSIONS,
            TABLE_EXTENSIONS,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
    except ImportError as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "accounts": [],
            "error": f"pipeline import failed: {e}",
        }
    ext_dot = "." + (filename or "").lower().rsplit(".", 1)[-1]
    try:
        if ext_dot in IMAGE_EXTENSIONS:
            pr = _run_image(file_bytes, document_type="general_ledger")
        elif ext_dot in TABLE_EXTENSIONS:
            pr = _run_table(file_bytes, filename=filename or "gl", document_type="general_ledger")
        else:
            return {
                "ok": False,
                "rows": [],
                "row_count": 0,
                "accounts": [],
                "error_code": "file_not_supported",
                "error": f"unsupported format {ext_dot}",
            }
    except Exception as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "accounts": [],
            "error_code": "ocr_failed",
            "error": _short_err(e),
        }

    legacy = pipeline_result_to_legacy_dict(pr)
    rows = gl_rows_from_pipeline_legacy(legacy)
    if account_code:
        rows = [r for r in rows if r.account_code == account_code]
    accounts = sorted({r.account_code for r in rows if r.account_code})
    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "accounts": accounts,
        "parser_version": "bank_recon_v2+pipeline_v1",
        "needs_review": legacy.get("_needs_review", False),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-FILE MERGE
# ─────────────────────────────────────────────────────────────────────────────
def merge_statements(
    parsed_list: List[Dict[str, Any]],
) -> Tuple[List[StatementRow], float, float, str]:
    """Merge multiple parsed bank statements, deduplicate, sort by date."""
    seen_hashes = set()
    all_rows: List[StatementRow] = []
    opening = 0.0
    closing = 0.0
    bank_code = "generic"
    earliest_date = None
    latest_date = None

    for p in parsed_list:
        if not p.get("ok"):
            continue
        if p.get("bank_code") and p["bank_code"] != "generic":
            bank_code = p["bank_code"]
        for r in p.get("rows") or []:
            if r.row_hash in seen_hashes:
                continue
            seen_hashes.add(r.row_hash)
            all_rows.append(r)
            if r.date:
                if earliest_date is None or r.date < earliest_date:
                    earliest_date = r.date
                if latest_date is None or r.date > latest_date:
                    latest_date = r.date

    # v118.35.0.48 · 只按日期稳定排序 · 保留对账单原始打印顺序(同日多笔不重排)
    # 旧版按 (date, withdrawal, deposit) 排 · 把同一天的存/取款按金额重排 · 打乱了
    # 对账单的"上一行余额 ± 金额 = 本行余额"链条 · 导致余额验证误报 + 显示顺序错乱。
    # Python sort 稳定 → 同日行保持 append(= 解析 = PDF 顶到底)顺序。
    all_rows.sort(key=lambda r: (r.date or date.min,))

    # Opening: from first parsed file that has an opening balance
    for p in parsed_list:
        if p.get("ok") and p.get("opening", 0.0) != 0.0:
            opening = p["opening"]
            break

    # Closing: from last parsed file or recalculate
    for p in reversed(parsed_list):
        if p.get("ok") and p.get("closing", 0.0) != 0.0:
            closing = p["closing"]
            break

    if opening == 0.0 and all_rows:
        first = all_rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    if closing == 0.0 and all_rows:
        closing = all_rows[-1].balance

    return all_rows, opening, closing, bank_code


def merge_gl_files(
    parsed_list: List[Dict[str, Any]], account_code: str = ""
) -> Tuple[List[GlRow], List[str], float, float]:
    """Merge multiple parsed GL files, deduplicate, sort by date."""
    seen_hashes = set()
    all_rows: List[GlRow] = []
    all_accounts: set = set()
    opening = 0.0

    for p in parsed_list:
        if not p.get("ok"):
            continue
        if p.get("opening", 0.0) != 0.0 and opening == 0.0:
            opening = p["opening"]
        for acct in p.get("accounts") or []:
            all_accounts.add(acct)
        for r in p.get("rows") or []:
            if account_code and r.account_code and not r.account_code.startswith(account_code):
                continue
            if r.row_hash in seen_hashes:
                continue
            seen_hashes.add(r.row_hash)
            all_rows.append(r)

    all_rows.sort(key=lambda r: (r.date or date.min, r.doc_no or ""))

    # v118.33.13.5 · Cash-ledger formula (matches parse_gl_pdf v118.33.13.4):
    # debit = cash IN (balance increase), credit = cash OUT (balance decrease)
    # The OLD formula `opening + credit - debit` was the expense/revenue
    # perspective and produced wrong closing balances for bank GLs.
    total_credit = sum(r.credit for r in all_rows)
    total_debit = sum(r.debit for r in all_rows)
    closing = round(opening + total_debit - total_credit, 2)

    return all_rows, sorted(all_accounts), opening, closing


# ─────────────────────────────────────────────────────────────────────────────
# MATCHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def reconcile(
    stmt_rows: List[StatementRow],
    gl_rows: List[GlRow],
    stmt_opening: float = 0.0,
    gl_opening: float = 0.0,
    stmt_closing: float = 0.0,
    gl_closing: float = 0.0,
    bank_code: str = "",
    gl_account_code: str = "",
) -> Tuple[List[BankReconRow], BankReconSummary]:
    """
    3-layer matching: L1 exact date+amount, L2 ±3-day+amount, L3 amount only.
    Returns (recon_rows, summary).
    """
    recon_rows: List[BankReconRow] = []

    # Work with indices to track matched/unmatched
    gl_used = [False] * len(gl_rows)
    stmt_used = [False] * len(stmt_rows)

    def try_match_gl(stmt_row: StatementRow, layer: int) -> Optional[int]:
        """Find best GL match for a statement row. Returns GL index or None."""
        target_amount = stmt_row.withdrawal if stmt_row.withdrawal > 0 else stmt_row.deposit
        # Withdrawal from bank = company paid out = GL Credit; Deposit = GL Debit
        direction = "C" if stmt_row.withdrawal > 0 else "D"

        best_idx = None
        best_day_diff = 999

        for gi, gr in enumerate(gl_rows):
            if gl_used[gi]:
                continue
            gl_amount = gr.debit if direction == "D" else gr.credit
            if not _amount_matches(target_amount, gl_amount):
                continue
            if gl_amount == 0:
                continue

            dd = _day_diff(stmt_row.date, gr.date)
            if layer == 1:
                if dd is None or dd > 0:
                    continue
                best_idx = gi
                break
            elif layer == 2:
                if dd is None or dd > DATE_TOL_DAYS:
                    continue
                if dd < best_day_diff:
                    best_day_diff = dd
                    best_idx = gi
            elif layer == 3:
                if best_idx is None:
                    best_idx = gi

        return best_idx

    # Layer 1: exact date + exact amount
    for si, sr in enumerate(stmt_rows):
        gi = try_match_gl(sr, layer=1)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=1,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=0,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Layer 2: ±3-day tolerance
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        gi = try_match_gl(sr, layer=2)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            dd = _day_diff(sr.date, gr.date) or 0
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=2,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=dd,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Layer 3: amount only (no date constraint) — flagged
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        gi = try_match_gl(sr, layer=3)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            dd = _day_diff(sr.date, gr.date)
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=3,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=dd,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Remaining unmatched statement rows
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        status = "stmt_withdrawal_only" if sr.withdrawal > 0 else "stmt_deposit_only"
        recon_rows.append(
            BankReconRow(
                match_status=status,
                match_layer=None,
                stmt_date=sr.date,
                stmt_desc=sr.description,
                stmt_withdrawal=sr.withdrawal,
                stmt_deposit=sr.deposit,
                stmt_balance=sr.balance,
                stmt_confidence=sr.confidence,
                stmt_balance_ok=sr.balance_ok,
                stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                source_stmt_file=sr.source_file,
            )
        )

    # Remaining unmatched GL rows
    for gi, gr in enumerate(gl_rows):
        if gl_used[gi]:
            continue
        status = "gl_debit_only" if gr.debit > 0 else "gl_credit_only"
        recon_rows.append(
            BankReconRow(
                match_status=status,
                match_layer=None,
                gl_date=gr.date,
                gl_doc_no=gr.doc_no,
                gl_account_code=gr.account_code,
                gl_desc=gr.description,
                gl_debit=gr.debit,
                gl_credit=gr.credit,
                source_gl_file=gr.source_file,
            )
        )

    # Sort: matched first (by stmt_date), then unmatched
    def _sort_key(r: BankReconRow):
        order = 0 if r.match_status == "matched" else 1
        d = r.stmt_date or r.gl_date or date.min
        return (order, d)

    recon_rows.sort(key=_sort_key)

    # Build summary
    matched_rows = [r for r in recon_rows if r.match_status == "matched"]
    gl_debit_only = [r for r in recon_rows if r.match_status == "gl_debit_only"]
    gl_credit_only = [r for r in recon_rows if r.match_status == "gl_credit_only"]
    stmt_wd_only = [r for r in recon_rows if r.match_status == "stmt_withdrawal_only"]
    stmt_dep_only = [r for r in recon_rows if r.match_status == "stmt_deposit_only"]

    gl_debit_only_amt = round(sum(r.gl_debit for r in gl_debit_only), 2)
    gl_credit_only_amt = round(sum(r.gl_credit for r in gl_credit_only), 2)
    stmt_wd_only_amt = round(sum(r.stmt_withdrawal for r in stmt_wd_only), 2)
    stmt_dep_only_amt = round(sum(r.stmt_deposit for r in stmt_dep_only), 2)

    # Reconciliation formula:
    # stmt_closing ≈ gl_closing + opening_diff - gl_debit_only + gl_credit_only
    #                           - stmt_wd_only + stmt_dep_only
    opening_diff = round(stmt_opening - gl_opening, 2)
    formula_closing = round(
        gl_closing
        + opening_diff
        - gl_debit_only_amt
        + gl_credit_only_amt
        - stmt_wd_only_amt
        + stmt_dep_only_amt,
        2,
    )
    formula_diff = round(stmt_closing - formula_closing, 2)

    summary = BankReconSummary(
        bank_code=bank_code,
        gl_account_code=gl_account_code,
        stmt_opening=stmt_opening,
        stmt_closing=stmt_closing,
        gl_opening=gl_opening,
        gl_closing=gl_closing,
        stmt_total_deposit=round(sum(r.deposit for r in stmt_rows), 2),
        stmt_total_withdrawal=round(sum(r.withdrawal for r in stmt_rows), 2),
        gl_total_credit=round(sum(r.credit for r in gl_rows), 2),
        gl_total_debit=round(sum(r.debit for r in gl_rows), 2),
        matched_count=len(matched_rows),
        gl_debit_only_count=len(gl_debit_only),
        gl_credit_only_count=len(gl_credit_only),
        stmt_withdrawal_only_count=len(stmt_wd_only),
        stmt_deposit_only_count=len(stmt_dep_only),
        gl_debit_only_amount=gl_debit_only_amt,
        gl_credit_only_amount=gl_credit_only_amt,
        stmt_withdrawal_only_amount=stmt_wd_only_amt,
        stmt_deposit_only_amount=stmt_dep_only_amt,
        opening_diff=opening_diff,
        formula_stmt_closing=formula_closing,
        formula_diff=formula_diff,
    )

    return recon_rows, summary


# EXCEL EXPORT · moved to services/recon/bank_recon_excel.py
from services.recon.bank_recon_excel import export_bank_recon_excel  # noqa: F401 re-export


# ─────────────────────────────────────────────────────────────────────────────
# JSON SERIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def _date_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def _date_from_str(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def rows_to_json(rows: List[BankReconRow]) -> List[Dict[str, Any]]:
    result = []
    for r in rows:
        result.append(
            {
                "match_status": r.match_status,
                "match_layer": r.match_layer,
                "stmt_date": _date_str(r.stmt_date),
                "stmt_desc": r.stmt_desc,
                "stmt_withdrawal": r.stmt_withdrawal,
                "stmt_deposit": r.stmt_deposit,
                "stmt_balance": r.stmt_balance,
                "gl_date": _date_str(r.gl_date),
                "gl_doc_no": r.gl_doc_no,
                "gl_account_code": r.gl_account_code,
                "gl_desc": r.gl_desc,
                "gl_debit": r.gl_debit,
                "gl_credit": r.gl_credit,
                "date_diff_days": r.date_diff_days,
                "source_stmt_file": r.source_stmt_file,
                "source_gl_file": r.source_gl_file,
                # v118.33.13.0 · OCR accuracy verification
                "stmt_confidence": r.stmt_confidence,
                "stmt_balance_ok": r.stmt_balance_ok,
                "stmt_autocorrected": getattr(r, "stmt_autocorrected", False),
            }
        )
    return result


def rows_from_json(data: List[Dict[str, Any]]) -> List[BankReconRow]:
    rows = []
    for d in data or []:
        rows.append(
            BankReconRow(
                match_status=d.get("match_status", ""),
                match_layer=d.get("match_layer"),
                stmt_date=_date_from_str(d.get("stmt_date")),
                stmt_desc=d.get("stmt_desc", ""),
                stmt_withdrawal=float(d.get("stmt_withdrawal", 0) or 0),
                stmt_deposit=float(d.get("stmt_deposit", 0) or 0),
                stmt_balance=float(d.get("stmt_balance", 0) or 0),
                gl_date=_date_from_str(d.get("gl_date")),
                gl_doc_no=d.get("gl_doc_no", ""),
                gl_account_code=d.get("gl_account_code", ""),
                gl_desc=d.get("gl_desc", ""),
                gl_debit=float(d.get("gl_debit", 0) or 0),
                gl_credit=float(d.get("gl_credit", 0) or 0),
                date_diff_days=d.get("date_diff_days"),
                source_stmt_file=d.get("source_stmt_file", ""),
                source_gl_file=d.get("source_gl_file", ""),
                stmt_confidence=d.get("stmt_confidence", "high"),
                stmt_balance_ok=d.get("stmt_balance_ok"),
                stmt_autocorrected=bool(d.get("stmt_autocorrected", False)),
            )
        )
    return rows


def summary_to_json(s: BankReconSummary) -> Dict[str, Any]:
    return asdict(s)


def summary_from_json(d: Dict[str, Any]) -> BankReconSummary:
    if not d:
        return BankReconSummary()
    try:
        return BankReconSummary(
            **{k: v for k, v in d.items() if k in BankReconSummary.__dataclass_fields__}
        )
    except Exception:
        return BankReconSummary()


# ============================================================
# v0.18 · 匹配算法
# ============================================================

# 权重配置(总和 100)
_W_AMOUNT = 50
_W_DATE = 30
_W_DIRECTION = 15
_W_KEYWORD = 5

# 阈值
THRESH_AUTO = 85  # 自动选中
THRESH_SUGGEST = 60  # 可显示为疑似

# 发票金额/日期误差容忍
AMOUNT_TOL_EQUAL = 0.01  # 小于这个差值 = 金额精确一致
AMOUNT_TOL_SMALL = 1.00  # 1 泰铢内
AMOUNT_TOL_MEDIUM = 10.00  # 10 泰铢内(手续费差 / 汇率小差)
DATE_TOL_DAYS = 7  # 超过 7 天不计候选


def score_amount(bank_amount: float, invoice_amount: float) -> float:
    """金额接近度 → 0..50"""
    if not bank_amount or not invoice_amount:
        return 0.0
    diff = abs(float(bank_amount) - float(invoice_amount))
    if diff <= AMOUNT_TOL_EQUAL:
        return float(_W_AMOUNT)  # 完全一致
    if diff <= AMOUNT_TOL_SMALL:
        return float(_W_AMOUNT) - 5  # 1 泰铢内:45
    if diff <= AMOUNT_TOL_MEDIUM:
        return float(_W_AMOUNT) - 15  # 10 泰铢内:35
    # 更大差距:按比例打分(误差 ≤ 1% 给 20 分,≤ 5% 给 10 分)
    pct = diff / max(float(invoice_amount), 0.01)
    if pct <= 0.01:
        return 20.0
    if pct <= 0.05:
        return 10.0
    return 0.0


def score_date(bank_date: Optional[str], invoice_date: Optional[str]) -> float:
    """日期接近度 → 0..30"""
    if not bank_date or not invoice_date:
        return 0.0
    try:
        d1 = date.fromisoformat(bank_date)
        d2 = date.fromisoformat(invoice_date)
    except (ValueError, TypeError):
        return 0.0
    days = abs((d1 - d2).days)
    if days == 0:
        return float(_W_DATE)  # 同日:30
    if days <= 1:
        return 25.0
    if days <= 3:
        return 20.0
    if days <= 7:
        return 10.0
    return 0.0


def score_direction(bank_direction: str, invoice_meta: Dict[str, Any]) -> float:
    """方向一致性 → 0 或 15
    银行 OUT = 付出去钱 = 对应 采购/费用 发票(应付)
    银行 IN  = 收到钱    = 对应 销售/收入 发票(应收)
    判断依据:ocr_history 里的 category_tag / vendor 字段
    """
    if not bank_direction:
        return 0.0
    cat = (invoice_meta.get("category_tag") or "").lower()
    # 简单分类:销售/收入类 vs 采购/费用类
    income_words = ["sale", "sales", "revenue", "income", "销售", "收入"]
    expense_words = ["purchase", "expense", "cost", "fee", "采购", "费用", "开支"]
    is_income = any(w in cat for w in income_words)
    is_expense = any(w in cat for w in expense_words)

    if bank_direction == "IN" and is_income:
        return float(_W_DIRECTION)
    if bank_direction == "OUT" and is_expense:
        return float(_W_DIRECTION)
    if bank_direction == "OUT" and not is_income:
        # 大多数 OCR 历史是采购发票(默认场景)
        return float(_W_DIRECTION) * 0.7  # 约 10 分
    # 其他情况:不扣分但不加分
    return float(_W_DIRECTION) * 0.3  # 约 4.5 分


def score_keyword(bank_desc: str, invoice_meta: Dict[str, Any]) -> float:
    """描述关键词相似 → 0..5 · 软加分"""
    if not bank_desc:
        return 0.0
    desc_lower = bank_desc.lower()
    vendor = (invoice_meta.get("vendor") or "").lower()
    ref = (invoice_meta.get("invoice_no") or "").lower()

    score = 0.0
    # 供应商名在描述里出现(取前 6 字符以上的片段)
    if vendor and len(vendor) >= 3:
        # 拆 vendor 单词 · 任一个在 desc 中出现就给分
        for w in re.findall(r"[A-Za-z\u0E00-\u0E7F\u4e00-\u9fff]{3,}", vendor):
            if w in desc_lower:
                score += 3.0
                break
    # 发票号在描述里
    if ref and ref in desc_lower:
        score += 2.0
    return min(score, float(_W_KEYWORD))


def match_one_tx(bank_tx: Dict[str, Any], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """对一条银行流水 · 在候选发票集合中打分排序 · 返回 [{history_id, score, reason, breakdown}, ...]"""
    scored: List[Dict[str, Any]] = []
    for inv in candidates:
        s_amt = score_amount(
            bank_tx.get("amount") or 0, inv.get("amount_total") or inv.get("total") or 0
        )
        if s_amt <= 0:
            continue  # 金额差太大 · 直接跳过
        s_date = score_date(bank_tx.get("tx_date"), inv.get("invoice_date"))
        s_dir = score_direction(bank_tx.get("direction") or "", inv)
        s_kw = score_keyword(bank_tx.get("description") or "", inv)
        total = round(s_amt + s_date + s_dir + s_kw, 2)

        # 生成人类可读原因
        parts = []
        if s_amt >= _W_AMOUNT - 0.5:
            parts.append("金额精确")
        elif s_amt >= _W_AMOUNT - 5.5:
            parts.append("金额接近")
        if s_date >= _W_DATE - 0.5:
            parts.append("同日")
        elif s_date >= 25:
            parts.append("日期差 1 天")
        elif s_date >= 20:
            parts.append("日期差 3 天内")
        elif s_date >= 10:
            parts.append("日期差 7 天内")
        if s_kw > 0:
            parts.append("描述匹配")
        reason = " + ".join(parts) if parts else "低置信"

        scored.append(
            {
                "history_id": inv["id"],
                "score": total,
                "reason": reason,
                "breakdown": {
                    "amount": s_amt,
                    "date": s_date,
                    "direction": s_dir,
                    "keyword": s_kw,
                },
            }
        )
    # 按分降序
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:5]  # 最多留 5 个候选


# ============================================================
# Session 级匹配:遍历所有流水 · 查候选 · 写结果
# ============================================================
def run_matching_for_session(session_id: str, user_id: str) -> Dict[str, Any]:
    """
    对一个对账会话下的所有流水跑匹配
    返回统计:{tx_total, matched, suggested, unmatched, elapsed_ms}
    """
    import time
    import db

    t0 = time.time()
    txs = db.list_bank_recon_transactions(session_id, user_id, limit=2000)
    if not txs:
        return {
            "tx_total": 0,
            "matched": 0,
            "suggested": 0,
            "unmatched": 0,
            "elapsed_ms": 0,
            "error": "no_transactions",
        }

    stat = {"matched": 0, "suggested": 0, "unmatched": 0}

    for tx in txs:
        # 只处理 unmatched / suggested(已被用户确认的 matched 跳过)
        if tx.get("match_status") == "matched":
            stat["matched"] += 1
            continue

        amt = tx.get("amount")
        tx_date = tx.get("tx_date")
        if not amt or not tx_date:
            stat["unmatched"] += 1
            continue

        # 预筛选候选
        if hasattr(tx_date, "isoformat"):
            tx_date_str = tx_date.isoformat()
        else:
            tx_date_str = str(tx_date)

        candidates = db.find_invoice_candidates_for_tx(
            user_id=user_id,
            amount=float(amt),
            tx_date=tx_date_str,
            amount_tol=AMOUNT_TOL_MEDIUM,
            date_tol_days=DATE_TOL_DAYS,
        )

        if not candidates:
            db.save_match_result(tx["id"], [], THRESH_AUTO, THRESH_SUGGEST)
            stat["unmatched"] += 1
            continue

        # 打分
        tx_for_score = {
            "amount": float(amt),
            "tx_date": tx_date_str,
            "direction": tx.get("direction") or "",
            "description": tx.get("description") or "",
        }
        scored = match_one_tx(tx_for_score, candidates)

        # 写结果(算法内只保留 ≥ THRESH_SUGGEST 的)
        scored_kept = [s for s in scored if s["score"] >= THRESH_SUGGEST]
        final_status = db.save_match_result(tx["id"], scored_kept, THRESH_AUTO, THRESH_SUGGEST)
        stat[final_status] = stat.get(final_status, 0) + 1

    # 更新 session 头统计
    db.update_session_match_stats(session_id)

    elapsed = int((time.time() - t0) * 1000)
    return {
        "tx_total": len(txs),
        "matched": stat.get("matched", 0),
        "suggested": stat.get("suggested", 0),
        "unmatched": stat.get("unmatched", 0),
        "elapsed_ms": elapsed,
    }
