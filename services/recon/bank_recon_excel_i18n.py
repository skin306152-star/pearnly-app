# -*- coding: utf-8 -*-
"""bank_recon_excel 4 语标签 + 翻译 helper · bank_recon_excel 拆分 leaf。"""

from typing import Dict, Optional

_I18N_EXPORT: Dict[str, Dict[str, str]] = {
    # Sheet names
    "sh_summary": {"th": "สรุป", "en": "Summary", "zh": "汇总", "ja": "サマリー"},
    "sh_matched": {"th": "จับคู่แล้ว", "en": "Matched", "zh": "已匹配", "ja": "一致"},
    "sh_unmatched_gl": {
        "th": "GL ที่จับคู่ไม่ได้",
        "en": "Unmatched GL",
        "zh": "GL未匹配",
        "ja": "GL不一致",
    },
    "sh_unmatched_st": {
        "th": "Statement ที่จับคู่ไม่ได้",
        "en": "Unmatched Statement",
        "zh": "账单未匹配",
        "ja": "明細不一致",
    },
    # v118.34 · Consolidated Match Results sheet (matched + gl-only + stmt-only with Status col)
    "sh_match_results": {
        "th": "ผลการจับคู่",
        "en": "Match Results",
        "zh": "对账结果",
        "ja": "照合結果",
    },
    "status_matched": {"th": "✓ จับคู่แล้ว", "en": "✓ Matched", "zh": "✓ 已匹配", "ja": "✓ 一致"},
    # Column headers
    "col_date": {"th": "วันที่", "en": "Date", "zh": "日期", "ja": "日付"},
    "col_desc": {"th": "รายการ", "en": "Description", "zh": "摘要", "ja": "摘要"},
    "col_withdrawal": {"th": "ถอนเงิน", "en": "Withdrawal", "zh": "提款", "ja": "出金"},
    "col_deposit": {"th": "ฝากเงิน", "en": "Deposit", "zh": "存款", "ja": "入金"},
    "col_balance": {"th": "ยอดคงเหลือ", "en": "Balance", "zh": "余额", "ja": "残高"},
    "col_gl_date": {"th": "วันที่ GL", "en": "GL Date", "zh": "GL日期", "ja": "GL日付"},
    "col_gl_doc": {"th": "เลขที่ GL", "en": "GL Doc No", "zh": "GL凭证号", "ja": "GL伝票番号"},
    "col_gl_acct": {"th": "รหัสบัญชี", "en": "Account Code", "zh": "科目代码", "ja": "科目コード"},
    "col_gl_desc": {"th": "รายการ GL", "en": "GL Description", "zh": "GL摘要", "ja": "GL摘要"},
    "col_gl_debit": {"th": "เดบิต GL", "en": "GL Debit", "zh": "GL借方", "ja": "GL借方"},
    "col_gl_credit": {"th": "เครดิต GL", "en": "GL Credit", "zh": "GL贷方", "ja": "GL貸方"},
    "col_gl_balance": {"th": "ยอดคงเหลือ GL", "en": "GL Balance", "zh": "GL余额", "ja": "GL残高"},
    "col_match_layer": {"th": "ชั้นจับคู่", "en": "Match Layer", "zh": "匹配层", "ja": "マッチ層"},
    "col_date_diff": {"th": "ต่างวัน", "en": "Day Diff", "zh": "日期差", "ja": "日付差"},
    "col_status": {"th": "สถานะ", "en": "Status", "zh": "状态", "ja": "状態"},
    "col_source_stmt": {
        "th": "ไฟล์บัญชี",
        "en": "Statement File",
        "zh": "对账单文件",
        "ja": "明細ファイル",
    },
    "col_source_gl": {"th": "ไฟล์ GL", "en": "GL File", "zh": "GL文件", "ja": "GLファイル"},
    # Summary labels
    "lbl_bank": {"th": "ธนาคาร", "en": "Bank", "zh": "银行", "ja": "銀行"},
    "lbl_gl_acct": {"th": "รหัสบัญชี GL", "en": "GL Account", "zh": "GL科目", "ja": "GL科目"},
    "lbl_stmt_open": {
        "th": "ยอดยกมา (Statement)",
        "en": "Stmt Opening Balance",
        "zh": "对账单期初余额",
        "ja": "明細期首残高",
    },
    "lbl_stmt_close": {
        "th": "ยอดยกไป (Statement)",
        "en": "Stmt Closing Balance",
        "zh": "对账单期末余额",
        "ja": "明細期末残高",
    },
    "lbl_gl_open": {
        "th": "ยอดยกมา (GL)",
        "en": "GL Opening Balance",
        "zh": "GL期初余额",
        "ja": "GL期首残高",
    },
    "lbl_gl_close": {
        "th": "ยอดยกไป (GL)",
        "en": "GL Closing Balance",
        "zh": "GL期末余额",
        "ja": "GL期末残高",
    },
    "lbl_open_diff": {
        "th": "ผลต่างยอดยกมา",
        "en": "Opening Diff",
        "zh": "期初差异",
        "ja": "期首差異",
    },
    "lbl_matched": {
        "th": "รายการที่จับคู่ได้",
        "en": "Matched Items",
        "zh": "已匹配项目",
        "ja": "一致項目",
    },
    "lbl_gl_debit_only": {
        "th": "GL เดบิตเท่านั้น (ไม่มีในบัญชีธนาคาร)",
        "en": "GL Debit Only (not in Statement)",
        "zh": "仅 GL 有借方（对账单中缺失）",
        "ja": "GL の借方のみ（明細にない）",
    },
    "lbl_gl_credit_only": {
        "th": "GL เครดิตเท่านั้น (ไม่มีในบัญชีธนาคาร)",
        "en": "GL Credit Only (not in Statement)",
        "zh": "仅 GL 有贷方（对账单中缺失）",
        "ja": "GL の貸方のみ（明細にない）",
    },
    "lbl_stmt_wd_only": {
        "th": "รายการถอนใน Statement เท่านั้น (ไม่มีใน GL)",
        "en": "Stmt Withdrawal Only (not in GL)",
        "zh": "仅对账单有提款（GL 中缺失）",
        "ja": "明細の出金のみ（GL にない）",
    },
    "lbl_stmt_dep_only": {
        "th": "รายการฝากใน Statement เท่านั้น (ไม่มีใน GL)",
        "en": "Stmt Deposit Only (not in GL)",
        "zh": "仅对账单有存款（GL 中缺失）",
        "ja": "明細の入金のみ（GL にない）",
    },
    "lbl_formula_calc": {
        "th": "ยอดปิดคำนวณ (สูตร)",
        "en": "Calculated Closing (formula)",
        "zh": "公式计算期末余额",
        "ja": "計算期末残高（計算式）",
    },
    "lbl_formula_diff": {
        "th": "ผลต่าง (ควรเป็น 0)",
        "en": "Difference (should be 0)",
        "zh": "差异（应为0）",
        "ja": "差異（0が理想）",
    },
    "lbl_count": {"th": "จำนวน", "en": "Count", "zh": "数量", "ja": "件数"},
    "lbl_amount": {"th": "จำนวนเงิน", "en": "Amount", "zh": "金额", "ja": "金額"},
    "lbl_formula_title": {
        "th": "สูตรการกระทบยอด",
        "en": "Reconciliation Formula",
        "zh": "对账公式",
        "ja": "照合計算式",
    },
    "lbl_stats": {"th": "สถิติ", "en": "Statistics", "zh": "统计", "ja": "統計"},
    # Match layer labels
    "layer_1": {
        "th": "L1-ตรงวันที่",
        "en": "L1 - Exact Date",
        "zh": "L1-精确日期",
        "ja": "L1-日付一致",
    },
    "layer_2": {
        "th": "L2-ใกล้วันที่",
        "en": "L2 - Date Tolerance",
        "zh": "L2-日期容差",
        "ja": "L2-日付許容",
    },
    "layer_3": {
        "th": "L3-เฉพาะยอด",
        "en": "L3 - Amount Only",
        "zh": "L3-仅金额",
        "ja": "L3-金額のみ",
    },
    # Status labels
    "st_gl_debit_only": {
        "th": "GL เดบิตเท่านั้น",
        "en": "GL Debit Only",
        "zh": "仅 GL 借方",
        "ja": "GL の借方のみ",
    },
    "st_gl_credit_only": {
        "th": "GL เครดิตเท่านั้น",
        "en": "GL Credit Only",
        "zh": "仅 GL 贷方",
        "ja": "GL の貸方のみ",
    },
    "st_stmt_wd_only": {
        "th": "รายการถอนเท่านั้น",
        "en": "Stmt Withdrawal Only",
        "zh": "仅对账单提款",
        "ja": "明細の出金のみ",
    },
    "st_stmt_dep_only": {
        "th": "รายการฝากเท่านั้น",
        "en": "Stmt Deposit Only",
        "zh": "仅对账单存款",
        "ja": "明細の入金のみ",
    },
    # File-info diagnostics sheet
    "sh_fileinfo": {"th": "ข้อมูลไฟล์", "en": "File Info", "zh": "文件信息", "ja": "ファイル情報"},
    "fi_type": {"th": "ประเภท", "en": "Type", "zh": "类型", "ja": "種別"},
    "fi_file": {"th": "ชื่อไฟล์", "en": "File", "zh": "文件名", "ja": "ファイル"},
    "fi_rows": {"th": "แถวที่พบ", "en": "Rows Found", "zh": "解析行数", "ja": "解析行数"},
    "fi_bank_acct": {
        "th": "ธนาคาร/บัญชี",
        "en": "Bank/Account",
        "zh": "银行/科目",
        "ja": "銀行/科目",
    },
    "fi_status": {"th": "สถานะ", "en": "Status", "zh": "状态", "ja": "状態"},
    "fi_error": {"th": "ข้อผิดพลาด", "en": "Error", "zh": "错误", "ja": "エラー"},
    "fi_stmt_type": {
        "th": "Statement ธนาคาร",
        "en": "Bank Statement",
        "zh": "银行对账单",
        "ja": "銀行明細",
    },
    "fi_gl_type": {"th": "GL", "en": "GL", "zh": "总账（GL）", "ja": "GL"},
    "fi_ok": {"th": "✓ สำเร็จ", "en": "✓ OK", "zh": "✓ 成功", "ja": "✓ 成功"},
    "fi_warn": {"th": "⚠ 0 แถว", "en": "⚠ 0 Rows", "zh": "⚠ 0行", "ja": "⚠ 0行"},
    "fi_fail": {"th": "✗ ล้มเหลว", "en": "✗ Failed", "zh": "✗ 失败", "ja": "✗ 失敗"},
    # v118.35.0.61 · 匹配率诚实化 · 防『diff=0 恒等式假象』误导用户
    "lbl_match_section": {
        "th": "ผลการจับคู่ (กระทบยอด)",
        "en": "Matching Result",
        "zh": "勾稽匹配情况",
        "ja": "照合結果",
    },
    "lbl_matched_n": {"th": "จับคู่สำเร็จ", "en": "Matched", "zh": "已匹配笔数", "ja": "一致件数"},
    "lbl_match_rate": {"th": "อัตราจับคู่", "en": "Match Rate", "zh": "匹配率", "ja": "一致率"},
    "banner_no_match": {
        "th": "⚠ จับคู่สำเร็จ 0 รายการ · ค่า『ผลต่าง』ด้านล่างแม้แสดง 0 ก็เป็นเพียงผลของสมการบัญชี ไม่ได้กระทบยอดตรงกันจริง · GL กับใบแจ้งยอดอาจไม่ใช่บัญชี/ช่วงเวลาเดียวกัน กรุณาตรวจสอบ",
        "en": "⚠ 0 items matched. Even if the Difference below shows 0, that is only an accounting identity — NOT a true reconciliation. The GL and statement may not be the same account/period. Please verify.",
        "zh": "⚠ 本次 0 笔成功匹配。下方『差异』即便显示 0,也只是会计恒等式的结果,并非真正对平——很可能 GL 与对账单不是同一账户或同一期间,请核对。",
        "ja": "⚠ 一致 0 件。下の『差異』が 0 でも会計恒等式の結果にすぎず、真の照合ではありません。GL と明細が同一口座・同一期間か確認してください。",
    },
    "banner_low_match": {
        "th": "⚠ จับคู่ได้เพียง {n} รายการ ({r}%) ส่วนใหญ่ยังไม่ตรงกัน · กรุณายืนยันว่า GL กับใบแจ้งยอดเป็นบัญชี/ช่วงเวลาเดียวกัน",
        "en": "⚠ Only {n} item(s) matched ({r}%); most records did not correspond. Please confirm the GL and statement are the same account/period.",
        "zh": "⚠ 仅 {n} 笔匹配(匹配率 {r}%),绝大多数记录未能对应。请确认 GL 与对账单是否同一账户、同一期间。",
        "ja": "⚠ 一致は {n} 件のみ({r}%)。大半が対応していません。GL と明細が同一口座・同一期間か確認してください。",
    },
    "diff_identity_note": {
        "th": "(จับคู่ {n} รายการ · ผลต่าง≈0 ไม่ได้แปลว่ากระทบยอดตรง)",
        "en": "({n} matched · diff≈0 does NOT mean reconciled)",
        "zh": "(仅 {n} 笔匹配 · 差异≈0 不代表已对平)",
        "ja": "({n} 件一致 · 差異≈0 でも照合済みではない)",
    },
    # v118.33.13.0 · OCR verification labels
    "lbl_ocr_check": {
        "th": "ตรวจสอบความถูกต้องของ OCR",
        "en": "OCR Accuracy Check",
        "zh": "OCR 准确性核查",
        "ja": "OCR精度チェック",
    },
    "lbl_ocr_bal_warn": {
        "th": "ยอดคงเหลือไม่ตรง (โปรดตรวจสอบ)",
        "en": "Balance mismatch (review)",
        "zh": "余额验证未通过",
        "ja": "残高検証エラー",
    },
    "lbl_ocr_lowconf": {
        "th": "ความมั่นใจต่ำ (เลือนราง)",
        "en": "Low confidence (blurry)",
        "zh": "低置信度（模糊）",
        "ja": "信頼度低（不鮮明）",
    },
    "lbl_ocr_autofixed": {
        "th": "ระบบแก้ยอดอัตโนมัติตามยอดคงเหลือ (ควรตรวจ)",
        "en": "Auto-corrected by balance (review)",
        "zh": "系统按余额自动修正（建议复核）",
        "ja": "残高で自動修正（要確認）",
    },
    "col_confidence": {"th": "ความมั่นใจ", "en": "Confidence", "zh": "置信度", "ja": "信頼度"},
    "col_balance_ok": {"th": "ตรวจยอด", "en": "Balance Check", "zh": "余额校验", "ja": "残高検証"},
    # Statement detail sheet
    "sh_stmt_detail": {
        "th": "รายละเอียดSTATEMENT",
        "en": "Statement Detail",
        "zh": "银行对账单明细",
        "ja": "明細",
    },
    "sh_gl_detail": {
        "th": "รายละเอียดบัญชีแยกประเภท",
        "en": "GL Detail",
        "zh": "总账明细",
        "ja": "元帳明細",
    },
    # v118.34 · GL Detail Sheet column labels (no "GL" suffix · Sheet name already implies context)
    "col_doc_no": {"th": "เลขที่เอกสาร", "en": "Doc No", "zh": "凭证号", "ja": "伝票番号"},
    "col_account_code": {
        "th": "รหัสบัญชี",
        "en": "Account Code",
        "zh": "科目代码",
        "ja": "科目コード",
    },
    "col_debit": {"th": "เดบิต", "en": "Debit", "zh": "借方", "ja": "借方"},
    "col_credit": {"th": "เครดิต", "en": "Credit", "zh": "贷方", "ja": "貸方"},
    "sh_usage": {"th": "วิธีใช้งาน", "en": "How to Use", "zh": "使用说明", "ja": "使い方"},
    "col_source_file": {"th": "ไฟล์ต้นทาง", "en": "Source File", "zh": "原文件", "ja": "ファイル"},
    "conf_high": {"th": "✓ สูง", "en": "✓ High", "zh": "✓ 高", "ja": "✓ 高"},
    "conf_medium": {"th": "△ กลาง", "en": "△ Medium", "zh": "△ 中", "ja": "△ 中"},
    "conf_low": {"th": "◌ ต่ำ", "en": "◌ Low", "zh": "◌ 低", "ja": "◌ 低"},
    "bal_ok": {"th": "✓ ผ่าน", "en": "✓ Pass", "zh": "✓ 通过", "ja": "✓ 合格"},
    "bal_warn": {"th": "⚠ ตรวจ", "en": "⚠ Review", "zh": "⚠ 核对", "ja": "⚠ 要確認"},
    # v118.35.0.62 · 系统按余额反推自动修正了金额/方向 · 标『已修正』· 黄底 · 建议复核
    "bal_fixed": {
        "th": "✎ แก้อัตโนมัติ",
        "en": "✎ Auto-fixed",
        "zh": "✎ 已修正",
        "ja": "✎ 自動修正",
    },
    "bal_na": {"th": "—", "en": "—", "zh": "—", "ja": "—"},
    # v118.33.13.2 · Vertical itemized summary labels
    "col_summary_item": {"th": "รายการ", "en": "Item Description", "zh": "项目说明", "ja": "項目"},
    "col_summary_amount": {"th": "จำนวนเงิน", "en": "Amount", "zh": "金额", "ja": "金額"},
    "detail_no_items": {"th": "ไม่มี", "en": "(none)", "zh": "无", "ja": "なし"},
    "sec_open_diff_expand": {
        "th": "ผลต่างยอดยกมา (ยอดยกมา Statement − ยอดยกมา GL)",
        "en": "Opening Diff (Statement Open − GL Open)",
        "zh": "期初差异（对账单期初 − GL 期初）",
        "ja": "期首差異（明細期首 − GL 期首）",
    },
    "sec_gl_debit_only_full": {
        "th": "GL เดบิตเท่านั้น (ไม่มีใน Statement)",
        "en": "GL Debit Only (not in Statement)",
        "zh": "仅 GL 有借方（对账单中缺失）",
        "ja": "GL の借方のみ（明細にない）",
    },
    "sec_gl_credit_only_full": {
        "th": "GL เครดิตเท่านั้น (ไม่มีใน Statement)",
        "en": "GL Credit Only (not in Statement)",
        "zh": "仅 GL 有贷方（对账单中缺失）",
        "ja": "GL の貸方のみ（明細にない）",
    },
    "sec_stmt_wd_only_full": {
        "th": "รายการถอนใน Statement เท่านั้น (ไม่มีใน GL)",
        "en": "Statement Withdrawal Only (not in GL)",
        "zh": "仅对账单有提款（GL 中缺失）",
        "ja": "明細の出金のみ（GL にない）",
    },
    "sec_stmt_dep_only_full": {
        "th": "รายการฝากใน Statement เท่านั้น (ไม่มีใน GL)",
        "en": "Statement Deposit Only (not in GL)",
        "zh": "仅对账单有存款（GL 中缺失）",
        "ja": "明細の入金のみ（GL にない）",
    },
    # P0.2 BUG-B-T2 v118.35.0.38 · 手动录入痕迹 section · 标黄被覆盖的 anchor cell
    "sec_manual_entry": {
        "th": "ร่องรอยการกรอกยอดเอง (3 อันคอร์)",
        "en": "Manual Entry Audit Trail (3 anchors)",
        "zh": "手动录入痕迹（3 个 anchor）",
        "ja": "手入力履歴（3 アンカー）",
    },
    "lbl_manual_warn": {
        "th": "⚠ รายงานนี้มีการกรอกยอด anchor เอง · ดูตารางท้ายไฟล์",
        "en": "⚠ This report contains manually entered anchor values · see audit trail at bottom",
        "zh": "⚠ 本报告含手动录入 anchor · 看末尾对照表",
        "ja": "⚠ 本レポートは手入力アンカーを含む · ファイル末尾の照合表参照",
    },
    "col_manual_ocr": {
        "th": "ค่า OCR (อ้างอิง)",
        "en": "OCR Value (reference)",
        "zh": "OCR 抽到的（参考）",
        "ja": "OCR 値(参考)",
    },
    "col_manual_user": {
        "th": "ค่าที่คุณกรอก (ใช้จริง)",
        "en": "Your Value (used)",
        "zh": "你填的（实际用）",
        "ja": "入力値(実使用)",
    },
    "col_manual_diff": {"th": "ผลต่าง", "en": "Diff", "zh": "差额", "ja": "差額"},
    "lbl_anchor_stmt_open": {
        "th": "ยอดยกมา Statement",
        "en": "Statement Opening",
        "zh": "Statement 期初余额",
        "ja": "Statement 期首",
    },
    "lbl_anchor_gl_open": {
        "th": "ยอดยกมา GL",
        "en": "GL Opening",
        "zh": "GL 期初余额",
        "ja": "GL 期首",
    },
    "lbl_anchor_gl_close": {
        "th": "ยอดยกไป GL",
        "en": "GL Closing",
        "zh": "GL 期末余额",
        "ja": "GL 期末",
    },
    # BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor · Statement 期末(客户反馈缺这个录入框)
    "lbl_anchor_stmt_close": {
        "th": "ยอดยกไป STATEMENT",
        "en": "Statement Closing",
        "zh": "Statement 期末余额",
        "ja": "Statement 期末",
    },
}


def _t(key: str, lang: str) -> str:
    lang = lang if lang in ("th", "en", "zh", "ja") else "th"
    return (_I18N_EXPORT.get(key) or {}).get(lang) or (_I18N_EXPORT.get(key) or {}).get("en") or key


def _layer_label(layer: Optional[int], lang: str) -> str:
    if layer == 1:
        return _t("layer_1", lang)
    if layer == 2:
        return _t("layer_2", lang)
    if layer == 3:
        return _t("layer_3", lang)
    return ""


def _status_label(status: str, lang: str) -> str:
    mapping = {
        "gl_debit_only": "st_gl_debit_only",
        "gl_credit_only": "st_gl_credit_only",
        "stmt_withdrawal_only": "st_stmt_wd_only",
        "stmt_deposit_only": "st_stmt_dep_only",
    }
    key = mapping.get(status, status)
    return _t(key, lang)
