# -*- coding: utf-8 -*-
"""Bank-v2 对账路由组共享:bank_recon_v2 接入 + 错误/标签 i18n + 完整度/差异/锚点 helper。

recon_routes 拆分·verbatim 抽出(except 分支加 None 绑定保跨模块 import 降级)。"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
# v118.33.6 · Bank Statement vs GL Reconciliation v2
# ════════════════════════════════════════════════════════════════════
try:
    from services.recon.bank_recon_v2 import (
        parse_bank_statement_pdf,
        parse_gl as parse_gl_v2,
        merge_statements,
        merge_gl_files,
        reconcile as bank_reconcile,
        export_bank_recon_excel,
        rows_to_json,
        rows_from_json,
        summary_to_json as bank_summary_to_json,
        summary_from_json as bank_summary_from_json,
    )

    _BANK_V2_OK = True
except ImportError as _brv2_import_err:
    logger.warning(f"[bank-v2] bank_recon_v2 not available: {_brv2_import_err}")
    _BANK_V2_OK = False
    # 拆分后:import 失败时绑 None 让本模块仍可被 run/crud import(调用点均经 _BANK_V2_OK 守卫)
    parse_bank_statement_pdf = parse_gl_v2 = merge_statements = merge_gl_files = None
    bank_reconcile = export_bank_recon_excel = rows_to_json = rows_from_json = None
    bank_summary_to_json = bank_summary_from_json = None

_BRV2_ERR = {
    "auth_required": {
        "zh": "未登录",
        "en": "Not logged in",
        "th": "ยังไม่ได้เข้าสู่ระบบ",
        "ja": "未ログイン",
    },
    "no_stmt_files": {
        "zh": "请上传银行账单",
        "en": "Please upload bank statement files",
        "th": "กรุณาอัปโหลดไฟล์บัญชีธนาคาร",
        "ja": "銀行明細ファイルをアップロードしてください",
    },
    "no_gl_files": {
        "zh": "请上传GL文件",
        "en": "Please upload GL files",
        "th": "กรุณาอัปโหลดไฟล์ GL",
        "ja": "GLファイルをアップロードしてください",
    },
    "stmt_parse_fail": {
        "zh": "账单解析失败: {e}",
        "en": "Statement parse failed: {e}",
        "th": "อ่านไฟล์บัญชีไม่สำเร็จ: {e}",
        "ja": "明細解析失敗: {e}",
    },
    "gl_parse_fail": {
        "zh": "GL解析失败: {e}",
        "en": "GL parse failed: {e}",
        "th": "อ่านไฟล์ GL ไม่สำเร็จ: {e}",
        "ja": "GL解析失敗: {e}",
    },
    "stmt_no_rows": {
        "zh": "账单中未找到交易记录",
        "en": "No transactions found in bank statement",
        "th": "ไม่พบรายการในบัญชีธนาคาร",
        "ja": "銀行明細に取引が見つかりません",
    },
    "gl_no_rows": {
        "zh": "GL中未找到记录",
        "en": "No rows found in GL",
        "th": "ไม่พบรายการใน GL",
        "ja": "GLにデータが見つかりません",
    },
    "task_not_found": {
        "zh": "任务不存在",
        "en": "Task not found",
        "th": "ไม่พบงาน",
        "ja": "タスクが見つかりません",
    },
}


def _brv2_err(key: str, lang: str = "th", **fmt) -> str:
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    msg = (_BRV2_ERR.get(key) or {}).get(lang) or (_BRV2_ERR.get(key) or {}).get("en") or key
    return msg.format(**fmt) if fmt else msg


# v118.35.0.54 · 输入不匹配警告(GL 与对账单期间/科目对不上)· 防止系统闷头算出
# 让用户看不懂的差额、误以为系统坏了。返回 warnings 数组 · 前端显示提示条。
_BRV2_WARN = {
    "period_mismatch": {
        "zh": "⚠️ GL 与对账单的期间不重叠(GL:{g};对账单:{s})。很可能上传了不同期间的文件,请核对后重新上传同一期间的 GL 与对账单。",
        "en": "⚠️ The GL and bank statement periods do not overlap (GL: {g}; statement: {s}). You may have uploaded files from different periods — please re-upload the GL and statement for the same period.",
        "th": "⚠️ ช่วงเวลาของ GL กับใบแจ้งยอดไม่ตรงกัน (GL: {g}; ใบแจ้งยอด: {s}) อาจอัปโหลดไฟล์คนละช่วงเวลา กรุณาตรวจสอบและอัปโหลด GL กับใบแจ้งยอดของช่วงเวลาเดียวกัน",
        "ja": "⚠️ GL と明細の期間が重なっていません(GL:{g};明細:{s})。異なる期間のファイルをアップロードした可能性があります。同じ期間の GL と明細を再アップロードしてください。",
    },
    "gl_too_few": {
        "zh": "⚠️ GL 只有 {n} 行,而对账单有 {m} 行,差距过大。可能上传了不完整或不对应的 GL,对账结果可能无意义。",
        "en": "⚠️ The GL has only {n} row(s) but the statement has {m}. This large gap suggests an incomplete or mismatched GL — the reconciliation result may be meaningless.",
        "th": "⚠️ GL มีเพียง {n} รายการ แต่ใบแจ้งยอดมี {m} รายการ ความต่างมากเกินไป อาจเป็น GL ที่ไม่สมบูรณ์หรือไม่ตรงกัน ผลกระทบยอดอาจไม่มีความหมาย",
        "ja": "⚠️ GL は {n} 行のみですが明細は {m} 行あります。差が大きすぎるため、不完全または不一致の GL の可能性があり、照合結果が無意味になる場合があります。",
    },
    "no_match": {
        "zh": "⚠️ 没有任何记录匹配成功。请确认 GL 与对账单是否为同一账户、同一期间。",
        "en": "⚠️ No records matched at all. Please confirm the GL and statement are for the same account and period.",
        "th": "⚠️ ไม่มีรายการใดจับคู่สำเร็จ กรุณายืนยันว่า GL กับใบแจ้งยอดเป็นบัญชีและช่วงเวลาเดียวกัน",
        "ja": "⚠️ 一致したレコードがありません。GL と明細が同じ口座・同じ期間か確認してください。",
    },
    # v118.35.0.63 · 提取行与账单印刷合计/笔数/期末对不上 → 多半漏行或读错 · 主动提示核对
    "completeness": {
        "zh": "⚠️ 对账单完整性检查未通过:{detail}。这通常意味着有交易未被识别(漏行)或金额读错,请对照原始账单核对,必要时手动补充。",
        "en": "⚠️ Statement completeness check failed: {detail}. This usually means a transaction was missed or an amount misread — please check against the original statement and add any missing rows.",
        "th": "⚠️ การตรวจความครบถ้วนของใบแจ้งยอดไม่ผ่าน: {detail} มักหมายถึงมีรายการตกหล่นหรืออ่านยอดผิด กรุณาตรวจกับใบแจ้งยอดต้นฉบับและเพิ่มรายการที่ขาด",
        "ja": "⚠️ 明細の完全性チェックに失敗: {detail}。取引の取りこぼしや金額の誤読の可能性があります。元の明細と照合し、不足行を補ってください。",
    },
    # v118.35.0.61 · 一个文件含多个账户(每 sheet 一个)· 已分账户独立校验余额 · 提示用户
    "multi_account": {
        "zh": "⚠️ 此对账单文件含 {n} 个账户({codes})。系统已『分账户』独立核对各自余额,但银行对账需 GL 与单一账户对应。若 GL 只含其中某一个账户,请只看对应账户的结果。",
        "en": "⚠️ This statement file contains {n} accounts ({codes}). Each account's balance was verified separately, but reconciliation requires the GL to match a single account. If your GL covers only one of them, refer to that account's result only.",
        "th": "⚠️ ไฟล์ใบแจ้งยอดนี้มี {n} บัญชี ({codes}) ระบบตรวจยอดแต่ละบัญชีแยกกันแล้ว แต่การกระทบยอดต้องให้ GL ตรงกับบัญชีเดียว หาก GL มีเพียงบัญชีเดียว ให้ดูเฉพาะผลของบัญชีนั้น",
        "ja": "⚠️ この明細ファイルには {n} 口座（{codes}）が含まれます。各口座の残高は個別に検証済みですが、照合には GL が単一口座に対応している必要があります。GL が 1 口座のみの場合、その口座の結果のみを参照してください。",
    },
}


def _brv2_warn(key: str, lang: str = "th", **fmt) -> str:
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    msg = (_BRV2_WARN.get(key) or {}).get(lang) or (_BRV2_WARN.get(key) or {}).get("en") or key
    return msg.format(**fmt) if fmt else msg


_COMP_LBL = {
    "credit": {"zh": "存款", "en": "credits", "th": "ฝาก", "ja": "入金"},
    "debit": {"zh": "取款", "en": "debits", "th": "ถอน", "ja": "出金"},
    "cnt": {"zh": "笔数", "en": "count", "th": "จำนวน", "ja": "件数"},
    "sum": {"zh": "合计", "en": "sum", "th": "ยอดรวม", "ja": "合計"},
    "printed": {"zh": "账单印", "en": "stmt prints", "th": "ใบแจ้งยอด", "ja": "明細表記"},
    "got": {"zh": "识别", "en": "extracted", "th": "อ่านได้", "ja": "抽出"},
    "close": {"zh": "期末", "en": "closing", "th": "ยอดปิด", "ja": "期末"},
    "calc": {"zh": "算得", "en": "calculated", "th": "คำนวณ", "ja": "計算"},
}


# v118.35.0.66 · 笔数缺口巨大(读到的远少于页脚印的)→ 多半是『只上传了部分页』· 醒目提示缺页
_MISSPAGE_LBL = {
    "zh": "(疑似缺页 · 请确认上传了完整页数)",
    "en": "(likely missing pages — please upload all pages)",
    "th": "(อาจขาดหน้า — กรุณาอัปโหลดให้ครบทุกหน้า)",
    "ja": "(ページ欠落の可能性 — 全ページをアップロードしてください)",
}


def _completeness_details(issues, lang) -> list:
    """v118.35.0.63 · 把完整性 issue 列表转成简短可读的提示片段(跟 lang 走)。
    v118.35.0.66 · 笔数缺口巨大时追加『疑似缺页』提示(BBL 只上传末页那种)。"""

    def L(k):
        return (_COMP_LBL.get(k) or {}).get(lang) or (_COMP_LBL.get(k) or {}).get("en") or k

    def _misspage(printed, got):
        # 印的笔数 ≥ 读到的 2 倍、且缺口 ≥ 20 → 几乎肯定整页缺失,而非个别漏行
        return isinstance(printed, (int, float)) and printed >= max(got * 2, got + 20)

    out = []
    miss = False
    for it in issues or []:
        t = it.get("type", "")
        if t == "credit_count_mismatch":
            out.append(
                f"{L('credit')}{L('cnt')}({L('printed')}{it['printed']}/{L('got')}{it['count']})"
            )
            miss = miss or _misspage(it["printed"], it["count"])
        elif t == "debit_count_mismatch":
            out.append(
                f"{L('debit')}{L('cnt')}({L('printed')}{it['printed']}/{L('got')}{it['count']})"
            )
            miss = miss or _misspage(it["printed"], it["count"])
        elif t == "credit_sum_mismatch":
            out.append(
                f"{L('credit')}{L('sum')}({L('printed')}{it['printed']:,.0f}/{L('got')}{it['sum']:,.0f})"
            )
        elif t == "debit_sum_mismatch":
            out.append(
                f"{L('debit')}{L('sum')}({L('printed')}{it['printed']:,.0f}/{L('got')}{it['sum']:,.0f})"
            )
        elif t == "closing_mismatch":
            out.append(
                f"{L('close')}({L('printed')}{it['printed']:,.0f}/{L('calc')}{it['calc']:,.0f})"
            )
        elif t == "balance_break":
            # ADR-006 压测发现 · N 行余额对不上 · 摘要也提示(不止行级 ⚠)
            n = it.get("count", 0)
            _bb = {
                "zh": f"{n} 行余额对不上(已逐行标 ⚠ · 请核对)",
                "en": f"{n} row(s) fail the balance chain (flagged ⚠ — please review)",
                "th": f"{n} แถวยอดคงเหลือไม่ตรง (ทำเครื่องหมาย ⚠ แล้ว — โปรดตรวจสอบ)",
                "ja": f"{n} 行で残高が一致しません(⚠ 表示済み — ご確認ください)",
            }
            out.append(_bb.get(lang, _bb["en"]))
    if miss:
        out.append(_MISSPAGE_LBL.get(lang, _MISSPAGE_LBL["en"]))
    return out


def _detect_recon_mismatch(stmt_rows, gl_rows, matched_count, lang) -> list:
    """v118.35.0.54 · 检测 GL 与对账单是否明显不匹配 · 返回 4 语警告字符串列表(可空)。"""
    warnings = []
    try:
        s_dates = [r.date for r in stmt_rows if getattr(r, "date", None)]
        g_dates = [r.date for r in gl_rows if getattr(r, "date", None)]
        if s_dates and g_dates:
            smin, smax, gmin, gmax = min(s_dates), max(s_dates), min(g_dates), max(g_dates)
            if smax < gmin or gmax < smin:  # 完全不重叠
                warnings.append(
                    _brv2_warn("period_mismatch", lang, g=f"{gmin}~{gmax}", s=f"{smin}~{smax}")
                )
        # v118.35.0.61 · 改比例阈值:GL 行数 < 对账单 20% 且账单≥20 行 → 规模悬殊预警
        # (旧阈值 GL≤2 太严 · 12 行 GL 对 237 行账单这种明显不对应的情况漏报)
        if len(stmt_rows) >= 20 and len(gl_rows) * 5 < len(stmt_rows):
            warnings.append(_brv2_warn("gl_too_few", lang, n=len(gl_rows), m=len(stmt_rows)))
        if matched_count == 0 and (len(stmt_rows) + len(gl_rows)) >= 10:
            warnings.append(_brv2_warn("no_match", lang))
    except Exception:
        pass
    return warnings


def _apply_anchor_overrides(
    stmt_opening: float,
    gl_opening: float,
    gl_closing: float,
    stmt_closing: float,
    stmt_opening_override: Optional[float],
    gl_opening_override: Optional[float],
    gl_closing_override: Optional[float],
    stmt_closing_override: Optional[float] = None,
):
    """
    P0.1 BUG-B-T1 v118.35.0.37 · 把『OCR snapshot + override 替换』封装成纯函数 · 守门测试容易
    BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor stmt_closing(Statement 期末)· 客户反馈 OCR 95% 准
                                · 5% 抽不准时需要兜底框
    Always returns the OCR snapshot (even when no override) so the frontend can prefill
    the 4 anchor inputs next time (localStorage) and Excel/history can show OCR vs user.
    Returns: (final_stmt_open, final_gl_open, final_gl_close, final_stmt_close,
              anchor_ocr_dict, anchor_overrides_dict)
    """
    anchor_ocr = {
        "stmt_opening": stmt_opening,
        "gl_opening": gl_opening,
        "gl_closing": gl_closing,
        "stmt_closing": stmt_closing,
    }
    anchor_overrides = {}
    if stmt_opening_override is not None:
        anchor_overrides["stmt_opening"] = {
            "ocr": stmt_opening,
            "user": float(stmt_opening_override),
        }
        stmt_opening = float(stmt_opening_override)
    if gl_opening_override is not None:
        anchor_overrides["gl_opening"] = {"ocr": gl_opening, "user": float(gl_opening_override)}
        gl_opening = float(gl_opening_override)
    if gl_closing_override is not None:
        anchor_overrides["gl_closing"] = {"ocr": gl_closing, "user": float(gl_closing_override)}
        gl_closing = float(gl_closing_override)
    if stmt_closing_override is not None:
        anchor_overrides["stmt_closing"] = {
            "ocr": stmt_closing,
            "user": float(stmt_closing_override),
        }
        stmt_closing = float(stmt_closing_override)
    return stmt_opening, gl_opening, gl_closing, stmt_closing, anchor_ocr, anchor_overrides
