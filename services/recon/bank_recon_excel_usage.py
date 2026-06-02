# -*- coding: utf-8 -*-
"""bank_recon_excel 使用说明文案块(4 语)· bank_recon_excel 拆分 leaf。"""

from typing import Dict, List, Tuple

# v118.34 · Usage instructions block (4-sheet consolidated structure)
# Each (text, bold) tuple is one row. bold=True rows get a light-grey fill.
_USAGE_BLOCKS: Dict[str, List[Tuple[str, bool]]] = {
    "zh": [
        ("银行对账表 · 使用说明", True),
        ("", False),
        ("Sheet 结构(共 4 个):", True),
        ("• 「汇总」              本表 · 含文件信息、对账公式、统计数据、本说明", False),
        ("• 「对账结果」          已匹配 + 仅 GL 有 + 仅对账单有,以「状态」列区分", False),
        ("• 「银行对账单明细」    OCR 提取的全部对账单行 + 置信度 + 余额校验状态", False),
        ("• 「总账明细」          OCR 提取的全部 GL 总账行", False),
        ("", False),
        ("OCR 准确性图例:", True),
        ("• 置信度 ✓高: 数字清晰无歧义可直接信任", False),
        ("• 置信度 △中: 多数清晰但有少量疑点", False),
        ("• 置信度 ◌低: 数字模糊或难以辨认,请核对原 PDF", False),
        ("• 余额校验 ✓通过: 上一行余额 ± 金额 == 本行余额 (容差 0.05)", False),
        ("• 余额校验 ⚠核对: 不平衡 — 多半是 OCR 看错某个数字,请核对原 PDF", False),
        ("• 余额校验 —    : 无法校验 (首行或缺失余额)", False),
        ("", False),
        ("对账公式:", True),
        (
            "  GL 期末 + 期初差异 − 仅 GL 借方 + 仅 GL 贷方 − 仅对账单提款 + 仅对账单存款 = 计算期末",
            False,
        ),
        ("  计算期末 应等于 对账单期末; 差异 = 计算期末 − 对账单期末 (应为 0)", False),
        ("", False),
        (
            "重要提示: 扫描件 PDF 通过 AI OCR 识别 · 不可避免存在识别风险 · 凡是看到 ⚠ 或 ◌ 的行必须人工核对原 PDF 后才能采信。"
            "Pearnly 永远不会自行填充模糊的数字 — 看不清就标红,决不替你猜。",
            False,
        ),
    ],
    "en": [
        ("Bank Reconciliation · How to Use", True),
        ("", False),
        ("Sheet structure (4 total):", True),
        (
            "• 'Summary'              This sheet · file info, reconciliation formula, stats, these instructions",
            False,
        ),
        (
            "• 'Match Results'        Matched + Unmatched GL + Unmatched Statement, distinguished by Status column",
            False,
        ),
        (
            "• 'Statement Detail'     All OCR-extracted statement rows + confidence + balance check",
            False,
        ),
        ("• 'GL Detail'            All OCR-extracted GL ledger rows", False),
        ("", False),
        ("OCR Accuracy legend:", True),
        ("• Confidence ✓High: every digit is clear, can be trusted", False),
        ("• Confidence △Medium: mostly clear with minor doubts", False),
        (
            "• Confidence ◌Low: digit was blurry or hard to read — verify against the original PDF",
            False,
        ),
        (
            "• Balance check ✓Pass: prev_balance ± amount == this row balance (tolerance 0.05)",
            False,
        ),
        (
            "• Balance check ⚠Review: not balanced — likely a misread digit. Verify against the original PDF",
            False,
        ),
        ("• Balance check —      : cannot verify (first row or missing balance)", False),
        ("", False),
        ("Reconciliation formula:", True),
        (
            "  GL_close + Open_diff − GL_debit_only + GL_credit_only − Stmt_WD_only + Stmt_Dep_only = Calc_close",
            False,
        ),
        (
            "  Calc_close should equal Statement_close; Diff = Calc_close − Statement_close (should be 0)",
            False,
        ),
        ("", False),
        (
            "IMPORTANT: Scanned PDFs go through AI OCR. There is always residual OCR risk. "
            "Any row marked ⚠ or ◌ MUST be cross-checked against the original PDF before trusting it. "
            "Pearnly will NEVER auto-fill an unclear digit — if we can't read it, we flag it; we don't guess for you.",
            False,
        ),
    ],
    "th": [
        ("รายงานการกระทบยอด GL กับบัญชีธนาคาร · วิธีใช้งาน", True),
        ("", False),
        ("โครงสร้าง Sheet (รวม 4 แผ่น):", True),
        (
            "• 'สรุป'                          แผ่นนี้ · ข้อมูลไฟล์ สูตรกระทบยอด สถิติ และคำแนะนำการใช้งาน",
            False,
        ),
        (
            "• 'ผลการจับคู่'                   รายการจับคู่ + GL ที่จับคู่ไม่ได้ + Statement ที่จับคู่ไม่ได้ พร้อมคอลัมน์สถานะ",
            False,
        ),
        (
            "• 'รายละเอียดSTATEMENT'           รายการบัญชีที่ OCR อ่านได้ทั้งหมด + ความมั่นใจ + ผลตรวจยอด",
            False,
        ),
        (
            "• 'รายละเอียดบัญชีแยกประเภท'      รายการบัญชีแยกประเภท (GL) ที่ OCR อ่านได้ทั้งหมด",
            False,
        ),
        ("", False),
        ("คำอธิบายสัญลักษณ์ OCR:", True),
        ("• ความมั่นใจ ✓สูง: ตัวเลขชัดเจน ไว้ใจได้", False),
        ("• ความมั่นใจ △กลาง: ส่วนใหญ่ชัด แต่มีจุดน่าสงสัยเล็กน้อย", False),
        ("• ความมั่นใจ ◌ต่ำ: ตัวเลขเบลอหรืออ่านยาก — โปรดตรวจ PDF ต้นฉบับ", False),
        ("• ตรวจยอด ✓ผ่าน: ยอดก่อน ± จำนวน == ยอดบรรทัดนี้ (ค่าเผื่อ 0.05)", False),
        ("• ตรวจยอด ⚠ตรวจ: ไม่ตรง — น่าจะ OCR อ่านผิด โปรดตรวจ PDF ต้นฉบับ", False),
        ("• ตรวจยอด —    : ตรวจไม่ได้ (บรรทัดแรกหรือไม่มียอด)", False),
        ("", False),
        ("สูตรการกระทบยอด:", True),
        (
            "  ปิด GL + ผลต่างยอดยกมา − GL เดบิตเท่านั้น + GL เครดิตเท่านั้น − รายการถอนเท่านั้น + รายการฝากเท่านั้น = ปิดคำนวณ",
            False,
        ),
        (
            "  ปิดคำนวณ ควรเท่ากับ ยอดยกไป Statement; ผลต่าง = ปิดคำนวณ − ยอดยกไป Statement (ควรเป็น 0)",
            False,
        ),
        ("", False),
        (
            "สำคัญ: PDF ที่สแกนผ่าน AI OCR ย่อมมีความเสี่ยงในการอ่านผิดเสมอ "
            "แถวที่ติด ⚠ หรือ ◌ ต้องตรวจสอบกับ PDF ต้นฉบับก่อนเชื่อถือทุกครั้ง "
            "Pearnly จะไม่เติมตัวเลขที่ไม่ชัดเจนเอง — ถ้าอ่านไม่ออก เราติดสัญลักษณ์ ไม่เดาแทนคุณ",
            False,
        ),
    ],
    "ja": [
        ("銀行照合レポート · 使い方", True),
        ("", False),
        ("シート構成 (全 4 シート):", True),
        ("• 「サマリー」               本シート · ファイル情報、照合計算式、件数、使い方", False),
        ("• 「照合結果」               一致 + GL不一致 + 明細不一致 を状態列で区別", False),
        ("• 「明細」                  OCR抽出した全明細行 + 信頼度 + 残高検証結果", False),
        ("• 「元帳明細」               OCR抽出した全 GL 元帳行", False),
        ("", False),
        ("OCR精度凡例:", True),
        ("• 信頼度 ✓高: 数字明瞭、信頼可能", False),
        ("• 信頼度 △中: 概ね明瞭だが軽微な疑問あり", False),
        ("• 信頼度 ◌低: 数字がぼやけている — 元のPDFを照合してください", False),
        ("• 残高検証 ✓合格: 前残高 ± 金額 == この行残高 (誤差 0.05)", False),
        ("• 残高検証 ⚠要確認: 不一致 — OCR誤読の可能性。元のPDFを照合してください", False),
        ("• 残高検証 —      : 検証不可 (初行または残高欠落)", False),
        ("", False),
        ("照合計算式:", True),
        (
            "  GL 期末 + 期首差 − GL の借方のみ + GL の貸方のみ − 明細の出金のみ + 明細の入金のみ = 計算期末",
            False,
        ),
        ("  計算期末 は 明細期末 と等しいはず; 差異 = 計算期末 − 明細期末 (0 が理想)", False),
        ("", False),
        (
            "重要: スキャンPDFはAI OCRを使用 · OCR誤読リスクは常に存在します "
            "⚠ または ◌ が付いた行は必ず元のPDFと照合してから利用してください "
            "Pearnly は不明瞭な数字を自動で埋めません — 読めないものはマークし、推測しません",
            False,
        ),
    ],
}
