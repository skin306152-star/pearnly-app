# -*- coding: utf-8 -*-
"""Bank-v2 对账路由组共享:bank_recon_v2 接入 + 错误/标签 i18n + 完整度/差异/锚点 helper。

recon_routes 拆分·verbatim 抽出(except 分支加 None 绑定保跨模块 import 降级)。"""

import logging

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
