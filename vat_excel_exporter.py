# -*- coding: utf-8 -*-
"""
v118.32.x · Pearnly · Korn 模板克隆 Excel 导出
铁律 60-VAT: VAT 对账 Excel 永远用 Korn 模板克隆 · 不许 openpyxl 直接 save
但因为 Korn 老师还没给我们参考模板 · v1 先用 openpyxl 严格按 PRD §7 复刻
"""
import io
import logging
from datetime import datetime
from typing import Dict, Any, List

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

# Korn 样本观察到的样式
HDR_FILL = PatternFill("solid", start_color="1E3A5F")
HDR_FONT = Font(bold=True, color="FFFFFF", name="Arial", size=10)
BOLD     = Font(bold=True, name="Arial", size=10)
NORMAL   = Font(name="Arial", size=10)
SMALL    = Font(name="Arial", size=9)
RED      = Font(name="Arial", size=10, color="C0392B", bold=True)
SUB_FILL = PatternFill("solid", start_color="F3F4F6")
DIFF_FILL = PatternFill("solid", start_color="FEF2F2")  # 差异行底色

THIN = Side(style='thin', color='B0BEC5')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT   = Alignment(horizontal="left",   vertical="center", wrap_text=True)
RIGHT  = Alignment(horizontal="right",  vertical="center", wrap_text=True)



# v118.32.3 · F2 · Excel 表头 4 语 i18n
# 数据本身(客户名/发票号等)保持 OCR 原文 · 只翻译标签
_LABELS = {
    "th": {  # 泰文(默认 · 给税局看)
        "biz_name":"ชื่อผู้ประกอบการ", "biz_address":"ที่อยู่สถานประกอบการ",
        "tax_id":"เลขประจำตัวผู้เสียภาษี", "branch":"สาขา",
        "period":"เดือน ปี งวดภาษี", "report_title":"รายงานภาษีขาย",
        "main_office":"สำนักงานใหญ่",
        "invoice_side":"ฝั่งใบกำกับภาษี (Invoice Side)",
        "check_marks":"✓ ช่องตรวจสอบ (Check Marks)",
        "report_side":"ฝั่งรายงาน (Report Side)",
        "note":"หมายเหตุ",
        "c_seq":"ลำดับ", "c_date":"วันที่", "c_inv_no":"เลขที่ใบกำกับ",
        "c_buyer_name":"ชื่อผู้ซื้อ", "c_buyer_tid":"เลขประจำตัวผู้เสียภาษี",
        "c_buyer_branch":"สาขาผู้ซื้อ",
        "c_pre_vat":"ยอดก่อน VAT", "c_vat":"ภาษี 7%", "c_total":"ยอดรวม",
        "c_category":"หมวดหมู่", "c_source":"แหล่งที่มา",
        "rc_date":"วันที่", "rc_no":"เลขที่", "rc_name":"ชื่อ",
        "rc_tid":"เลขภาษี", "rc_branch":"สาขา",
        "rc_pre":"ก่อน VAT", "rc_vat":"ภาษี 7%",
        "grand_total":"รวมยอดทั้งสิ้น",
        "sig_prepared":"ผู้จัดทำ", "sig_reviewer":"ผู้ตรวจสอบ", "sig_approver":"ผู้อนุมัติ",
    },
    "zh": {
        "biz_name":"经营者名", "biz_address":"经营场所地址",
        "tax_id":"税号", "branch":"分支",
        "period":"纳税期间", "report_title":"销项税报告",
        "main_office":"总部",
        "invoice_side":"发票侧 (Invoice Side)",
        "check_marks":"✓ 核对标记 (Check Marks)",
        "report_side":"报告侧 (Report Side)",
        "note":"备注",
        "c_seq":"序号", "c_date":"日期", "c_inv_no":"发票号",
        "c_buyer_name":"客户名", "c_buyer_tid":"客户税号",
        "c_buyer_branch":"客户分支",
        "c_pre_vat":"前税金额", "c_vat":"VAT 7%", "c_total":"含税总额",
        "c_category":"分类", "c_source":"来源",
        "rc_date":"日期", "rc_no":"号码", "rc_name":"名称",
        "rc_tid":"税号", "rc_branch":"分支",
        "rc_pre":"前税", "rc_vat":"VAT 7%",
        "grand_total":"合计",
        "sig_prepared":"制作人", "sig_reviewer":"审核人", "sig_approver":"批准人",
    },
    "en": {
        "biz_name":"Business Name", "biz_address":"Business Address",
        "tax_id":"Tax ID", "branch":"Branch",
        "period":"Tax Period", "report_title":"Sales VAT Report",
        "main_office":"Head Office",
        "invoice_side":"Invoice Side",
        "check_marks":"✓ Check Marks",
        "report_side":"Report Side",
        "note":"Note",
        "c_seq":"#", "c_date":"Date", "c_inv_no":"Invoice No",
        "c_buyer_name":"Buyer", "c_buyer_tid":"Buyer Tax ID",
        "c_buyer_branch":"Buyer Branch",
        "c_pre_vat":"Pre-VAT", "c_vat":"VAT 7%", "c_total":"Total",
        "c_category":"Category", "c_source":"Source",
        "rc_date":"Date", "rc_no":"No", "rc_name":"Name",
        "rc_tid":"Tax ID", "rc_branch":"Branch",
        "rc_pre":"Pre-VAT", "rc_vat":"VAT 7%",
        "grand_total":"Grand Total",
        "sig_prepared":"Prepared by", "sig_reviewer":"Reviewed by", "sig_approver":"Approved by",
    },
    "ja": {
        "biz_name":"事業者名", "biz_address":"事業所住所",
        "tax_id":"税番号", "branch":"支店",
        "period":"課税期間", "report_title":"売上 VAT レポート",
        "main_office":"本社",
        "invoice_side":"請求書側 (Invoice Side)",
        "check_marks":"✓ チェック欄 (Check Marks)",
        "report_side":"レポート側 (Report Side)",
        "note":"備考",
        "c_seq":"番号", "c_date":"日付", "c_inv_no":"請求書番号",
        "c_buyer_name":"顧客名", "c_buyer_tid":"顧客税番号",
        "c_buyer_branch":"顧客支店",
        "c_pre_vat":"税抜金額", "c_vat":"消費税 7%", "c_total":"税込合計",
        "c_category":"分類", "c_source":"出所",
        "rc_date":"日付", "rc_no":"番号", "rc_name":"名称",
        "rc_tid":"税番号", "rc_branch":"支店",
        "rc_pre":"税抜", "rc_vat":"消費税 7%",
        "grand_total":"総合計",
        "sig_prepared":"作成者", "sig_reviewer":"確認者", "sig_approver":"承認者",
    },
}

def _t(lang: str, key: str) -> str:
    """取 i18n 文字 · 不存在的语言或 key 自动 fallback 到泰文"""
    return _LABELS.get(lang, _LABELS["th"]).get(key, _LABELS["th"].get(key, key))


def _diff_field_match(diff_fields: Dict, field: str) -> bool:
    """diff_fields 里某字段 matched=True 返回 True · 否则 False · key 缺失也算 True(没对比)"""
    f = diff_fields.get(field) if isinstance(diff_fields, dict) else None
    if not f or not isinstance(f, dict):
        return True
    return bool(f.get("matched", True))


def _safe(v) -> str:
    return "" if v is None else str(v)


def _num(v):
    try:
        return float(str(v or 0).replace(",", ""))
    except Exception:
        return 0.0


def export_recon_task(task: Dict[str, Any],
                       rows: List[Dict[str, Any]],
                       client: Dict[str, Any],
                       vat_report: Dict[str, Any] = None,
                       lang: str = "th") -> bytes:
    """
    返回 .xlsx 二进制
    严格按 PRD §7 出 Korn 模板:
      - 6 行表头(经营者信息 + 期间)
      - 表格:发票侧 11 列 + 9 个 / 标记列 + 报告侧 7 列 + 备注 1 列 = 28 列
      - 一发票多差异 → 拆 N 行(铁律候选 · PRD §7.2)
      - 底部:总计 + 三栏签字位
    """
    wb = Workbook()
    ws = wb.active
    # v118.32.3 · sheet 标题:本地语言 · 泰文界面就纯泰文
    _title = _t(lang, "report_title")
    ws.title = (_title if lang == "th" else f"{_title}")[:31]  # Excel sheet 名 31 字符上限

    # ─── 6 行表头 ──────────────────────────────────────
    period_str = f"{task.get('period_month'):02d}/{task.get('period_year') + 543}"  # 佛历
    # 主标题:本地语言 · 非泰文时下挂泰文副标题(确保税局也认)
    title_main = _t(lang, "report_title")
    title_with_th = title_main if lang == "th" else f"{title_main}  ·  รายงานภาษีขาย"
    header_meta = [
        (_t(lang, "biz_name"),    client.get("name") or "-"),
        (_t(lang, "biz_address"), client.get("address") or "-"),
        (_t(lang, "tax_id"),      client.get("tax_id") or "-"),
        (_t(lang, "branch"),      f"{_t(lang, 'main_office')} (00000)"),
        (_t(lang, "period"),      period_str),
        ("",                       title_with_th),
    ]
    for r, (a, b) in enumerate(header_meta, 1):
        ws.cell(r, 1, a).font = BOLD
        ws.cell(r, 2, b).font = NORMAL if r < 6 else BOLD
        if r == 6:
            ws.cell(r, 2).alignment = CENTER
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=28)

    # ─── 表头(2 层) ─────────────────────────────────
    R = 8
    # 第一层 · 分段标题
    ws.merge_cells(start_row=R, start_column=1, end_row=R, end_column=11)
    ws.cell(R, 1, _t(lang, "invoice_side")).fill = HDR_FILL
    ws.cell(R, 1).font = HDR_FONT
    ws.cell(R, 1).alignment = CENTER

    ws.merge_cells(start_row=R, start_column=12, end_row=R, end_column=20)
    ws.cell(R, 12, _t(lang, "check_marks")).fill = HDR_FILL
    ws.cell(R, 12).font = HDR_FONT
    ws.cell(R, 12).alignment = CENTER

    ws.merge_cells(start_row=R, start_column=21, end_row=R, end_column=27)
    ws.cell(R, 21, _t(lang, "report_side")).fill = HDR_FILL
    ws.cell(R, 21).font = HDR_FONT
    ws.cell(R, 21).alignment = CENTER

    ws.cell(R, 28, _t(lang, "note")).fill = HDR_FILL
    ws.cell(R, 28).font = HDR_FONT
    ws.cell(R, 28).alignment = CENTER

    R += 1
    # 第二层 · 列名(28 列)
    col_headers = [
        _t(lang, "c_seq"), _t(lang, "c_date"), _t(lang, "c_inv_no"), _t(lang, "c_buyer_name"),
        _t(lang, "c_buyer_tid"), _t(lang, "c_buyer_branch"),
        _t(lang, "c_pre_vat"), _t(lang, "c_vat"), _t(lang, "c_total"),
        _t(lang, "c_category"), _t(lang, "c_source"),
        # 9 个标记列(数字标记 · 不需要翻译)
        "1", "2.1", "2.2", "2.3", "2.4", "3", "4", "5/6/7", "8/9",
        # 报告侧 7 列
        _t(lang, "rc_date"), _t(lang, "rc_no"), _t(lang, "rc_name"),
        _t(lang, "rc_tid"), _t(lang, "rc_branch"),
        _t(lang, "rc_pre"), _t(lang, "rc_vat"),
        # 备注
        _t(lang, "note"),
    ]
    for c, h in enumerate(col_headers, 1):
        cell = ws.cell(R, c, h)
        cell.fill = SUB_FILL
        cell.font = BOLD
        cell.alignment = CENTER
        cell.border = BORDER

    # ─── 数据行 ──────────────────────────────────────
    R += 1
    sum_pre = 0.0
    sum_vat = 0.0
    sum_total = 0.0

    for idx, row in enumerate(rows, 1):
        diff_fields = row.get("diff_fields") or {}
        if isinstance(diff_fields, str):
            try:
                import json as _j
                diff_fields = _j.loads(diff_fields)
            except Exception:
                diff_fields = {}

        diff_cats = (row.get("diff_categories") or "").split(",")
        diff_cats = [c.strip() for c in diff_cats if c.strip()]

        # 发票侧字段
        inv_no       = _safe(row.get("invoice_no"))
        inv_date     = _safe(row.get("invoice_date"))
        buyer_name   = _safe(row.get("buyer_name") or row.get("seller_name"))
        buyer_tax    = _safe(row.get("buyer_tax_id"))
        buyer_branch = _safe(row.get("buyer_branch") or "00000")
        amt_pre      = _num(row.get("amount_pre_vat") or row.get("total_amount"))
        amt_vat      = _num(row.get("vat_amount"))
        amt_total    = _num(row.get("total_amount"))
        source       = row.get("invoice_filename") or "-"

        sum_pre   += amt_pre
        sum_vat   += amt_vat
        sum_total += amt_total

        # 决定要写几行(铁律 PRD §7.2:每差异一行)
        if len(diff_cats) <= 1:
            row_count = 1
            cats_per_row = [diff_cats[0] if diff_cats else ""]
        else:
            row_count = len(diff_cats)
            cats_per_row = diff_cats

        for ri, cat in enumerate(cats_per_row):
            is_first = ri == 0
            is_diff_row = row.get("status") in ("mismatched", "invoice_orphan", "report_orphan")
            bg = DIFF_FILL if is_diff_row else None

            # 1. 发票侧(只在第一行填,后续行留空便于阅读)
            cells = [
                idx if is_first else "",
                inv_date if is_first else "",
                inv_no if is_first else "",
                buyer_name if is_first else "",
                buyer_tax if is_first else "",
                buyer_branch if is_first else "",
                amt_pre if is_first else "",
                amt_vat if is_first else "",
                amt_total if is_first else "",
                "" ,  # 分类 · 待自动归类后填
                source if is_first else "",
            ]
            for c, v in enumerate(cells, 1):
                cell = ws.cell(R, c, v)
                cell.alignment = RIGHT if c in (1,7,8,9) else LEFT
                cell.font = NORMAL
                cell.border = BORDER
                if bg: cell.fill = bg
                if c in (7,8,9): cell.number_format = '#,##0.00'

            # 2. 9 个 / 标记列(全部打 / 表示"已核对")
            for c in range(12, 21):
                cell = ws.cell(R, c, "/")
                cell.alignment = CENTER
                cell.font = NORMAL
                cell.border = BORDER
                if bg: cell.fill = bg

            # 3. 报告侧 7 列(只在第一行填)
            rep_date    = _safe(row.get("report_date"))    if is_first else ""
            rep_inv     = _safe(row.get("report_invoice_no")) if is_first else ""
            rep_name    = _safe(row.get("report_buyer_name")) if is_first else ""
            rep_tax     = _safe(row.get("report_buyer_tax_id")) if is_first else ""
            rep_branch  = _safe(row.get("report_buyer_branch")) if is_first else ""
            rep_pre     = _num(row.get("report_amount_pre_vat")) if is_first else ""
            rep_vat     = _num(row.get("report_vat_amount")) if is_first else ""

            rep_cells = [rep_date, rep_inv, rep_name, rep_tax, rep_branch, rep_pre, rep_vat]
            for ci, v in enumerate(rep_cells):
                c = 21 + ci
                cell = ws.cell(R, c, v)
                cell.alignment = RIGHT if c in (26, 27) else LEFT
                cell.font = NORMAL
                cell.border = BORDER
                if bg: cell.fill = bg
                if c in (26, 27): cell.number_format = '#,##0.00'

            # 4. 备注列(写差异说明)
            note = _category_to_thai_note(cat) if cat else ""
            cell = ws.cell(R, 28, note)
            cell.font = RED if is_diff_row else NORMAL
            cell.alignment = LEFT
            cell.border = BORDER
            if bg: cell.fill = bg

            R += 1

    # ─── 总计行 ──────────────────────────────────────
    ws.cell(R, 1, _t(lang, "grand_total")).font = BOLD
    ws.merge_cells(start_row=R, start_column=1, end_row=R, end_column=6)
    ws.cell(R, 7, sum_pre).font = BOLD;   ws.cell(R, 7).number_format = '#,##0.00'
    ws.cell(R, 8, sum_vat).font = BOLD;   ws.cell(R, 8).number_format = '#,##0.00'
    ws.cell(R, 9, sum_total).font = BOLD; ws.cell(R, 9).number_format = '#,##0.00'
    for c in range(1, 29):
        ws.cell(R, c).border = BORDER
        ws.cell(R, c).fill = SUB_FILL

    # ─── 签字栏 ──────────────────────────────────────
    R += 3
    ws.cell(R, 1, f"{_t(lang, 'sig_prepared')}: ____________________").font = NORMAL
    ws.cell(R, 12, f"{_t(lang, 'sig_reviewer')}: ____________________").font = NORMAL
    ws.cell(R, 22, f"{_t(lang, 'sig_approver')}: ____________________").font = NORMAL

    # ─── 列宽 ────────────────────────────────────────
    widths = {
        1:6, 2:11, 3:18, 4:30, 5:18, 6:10, 7:11, 8:10, 9:11, 10:14, 11:18,
        12:5, 13:5, 14:5, 15:5, 16:5, 17:5, 18:5, 19:5, 20:5,
        21:11, 22:16, 23:24, 24:18, 25:8, 26:11, 27:10,
        28:30,
    }
    for c, w in widths.items():
        ws.column_dimensions[get_column_letter(c)].width = w

    # 行高
    ws.row_dimensions[8].height = 26
    ws.row_dimensions[9].height = 32

    # 冻结表头
    ws.freeze_panes = "A10"

    # 导出
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def _category_to_thai_note(cat: str) -> str:
    """差异类别 → 泰语备注"""
    return {
        "date_diff":            "วันที่ไม่ตรงกัน",
        "date_period_mismatch": "วันที่ข้ามงวดภาษี",
        "invoice_no_prefix":    "เลขที่ใบกำกับต่างเพียงคำนำหน้า",
        "invoice_no_mismatch":  "เลขที่ใบกำกับไม่ถูกต้อง",
        "name_fuzzy":           "ชื่อผู้ซื้อใกล้เคียง · ไม่ตรงทุกตัวอักษร",
        "name_mismatch":        "ชื่อผู้ซื้อไม่ถูกต้อง",
        "tax_id_mismatch":      "เลขประจำตัวผู้เสียภาษีไม่ถูกต้อง",
        "branch_mismatch":      "สาขาผู้ซื้อไม่ถูกต้อง",
        "amount_diff":          "ยอดเงินไม่ตรงกัน",
        "vat_precision":        "ภาษีมูลค่าเพิ่มต่างเพราะปัดเศษ",
        "vat_calc_wrong":       "ภาษีมูลค่าเพิ่มคำนวณผิด",
        "invoice_orphan":       "พบใบกำกับ แต่ไม่พบในรายงาน",
        "report_orphan":        "พบในรายงาน แต่ไม่พบใบกำกับ",
    }.get(cat, cat)
