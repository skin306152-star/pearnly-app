// ============================================================
// REFACTOR-WB (2026-06-02) · GL-VAT 对账 · 纯工具:DOM/i18n/格式化/KPI · 从 gl-vat-recon.js 抽出 · verbatim 0 改逻辑。
// ============================================================

const $ = (id) => document.getElementById(id);
const _token = () => localStorage.getItem('mrpilot_token') || '';
// v118.32.5.1 · 优先读 window.currentLang（实时切换不依赖 localStorage 刷新）
const _lang = () => {
    if (typeof window.currentLang === 'string' && window.currentLang) return window.currentLang;
    return localStorage.getItem('mrpilot_lang') || 'th';
};
const _authH = () => ({ Authorization: 'Bearer ' + _token() });

// ── 多语言文本（与后端 _I18N 字典同源） ──────────────────────────
const I18N = {
    th: {
        not_found: 'ไม่พบข้อมูล',
        running: 'กำลังกระทบยอด…',
        error: 'เกิดข้อผิดพลาด',
        need_files: 'กรุณาเลือกไฟล์ทั้งสอง',
        done: 'เสร็จสิ้น',
        hint_need_both: 'อัปโหลด ① รายงานภาษีขาย + ② GL',
        hint_need_one_more: 'อัปโหลดอีก 1 ไฟล์',
        hint_ready: 'พร้อมแล้ว · กดเริ่มกระทบยอด',
        hist_load: 'โหลด',
        hist_export: 'ส่งออก',
        hist_delete: 'ลบ',
        confirm_delete: 'ยืนยันการลบงานนี้?',
        s_gl_total: 'ยอดรวมตามบัญชีแยกประเภท',
        s_minus_gl_cr: 'หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย',
        s_plus_gl_dr: 'บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย',
        s_plus_vat_p: 'บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท',
        s_minus_vat_n: 'หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท',
        s_vat_total: 'ยอดรวมตามรายงานภาษีขาย',
    },
    zh: {
        not_found: '未找到数据',
        running: '正在对账中...',
        error: '出错了',
        need_files: '请先选择两个文件',
        done: '完成',
        hint_need_both: '请上传① 销项税报告 + ② 总账 GL',
        hint_need_one_more: '还需上传 1 份文件',
        hint_ready: '已就绪 · 点击开始对账',
        hist_load: '加载',
        hist_export: '导出',
        hist_delete: '删除',
        confirm_delete: '确认删除此任务？',
        s_gl_total: '总账金额合计',
        s_minus_gl_cr: '减：销项税报告中未列的贷方记录',
        s_plus_gl_dr: '加：销项税报告中未列的借方记录',
        s_plus_vat_p: '加：总账中未列的销售记录',
        s_minus_vat_n: '减：总账中未列的贷项凭单(credit note)记录',
        s_vat_total: '销项税报告金额合计',
    },
    en: {
        not_found: 'Not found',
        running: 'Reconciling...',
        error: 'Error',
        need_files: 'Please select both files',
        done: 'Done',
        hint_need_both: 'Upload ① Output VAT report + ② GL file',
        hint_need_one_more: '1 more file required',
        hint_ready: 'Ready · click Run to start',
        hist_load: 'Load',
        hist_export: 'Export',
        hist_delete: 'Delete',
        confirm_delete: 'Delete this task?',
        s_gl_total: 'Total per General Ledger',
        s_minus_gl_cr: 'Less: GL credits not in VAT Report',
        s_plus_gl_dr: 'Add: GL debits not in VAT Report',
        s_plus_vat_p: 'Add: Sales in VAT Report not in GL',
        s_minus_vat_n: 'Less: Credit notes in VAT Report not in GL',
        s_vat_total: 'Total per VAT Sales Report',
    },
    ja: {
        not_found: 'データなし',
        running: '照合中…',
        error: 'エラー',
        need_files: '両方のファイルを選択してください',
        done: '完了',
        hint_need_both: '① 売上税報告 + ② GL をアップロード',
        hint_need_one_more: 'あと 1 ファイル必要',
        hint_ready: '準備完了 · 「開始」をクリック',
        hist_load: '読込',
        hist_export: '出力',
        hist_delete: '削除',
        confirm_delete: 'このタスクを削除しますか?',
        s_gl_total: '総勘定元帳合計',
        s_minus_gl_cr: '減：売上税報告にないGL貸方記録',
        s_plus_gl_dr: '加：売上税報告にないGL借方記録',
        s_plus_vat_p: '加：GLにない売上記録',
        s_minus_vat_n: '減：GLにない赤伝記録',
        s_vat_total: '売上税報告合計',
    },
};
const _t = (key) => (I18N[_lang()] || I18N.th)[key] || key;

// M3-2:收入对账失败 error_code → 4 语可读原因 + 引导(取代泛化 "เกิดข้อผิดพลาด")
function _glvFailMsg(code) {
    const lang = _lang();
    const M = {
        gl_no_revenue_rows: {
            zh: 'GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。',
            th: 'ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่',
            en: 'No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.',
            ja: 'GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。',
        },
        gl_parse_failed: {
            zh: 'GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。',
            th: 'อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน',
            en: 'Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.',
            ja: 'GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。',
        },
        vat_no_rows: {
            zh: '销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。',
            th: 'ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง',
            en: 'No rows found in the sales-VAT report. Please check you uploaded the correct report.',
            ja: '売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。',
        },
        vat_parse_failed: {
            zh: '销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。',
            th: 'อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF',
            en: 'Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.',
            ja: '売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。',
        },
    };
    const m = M[code];
    return m ? m[lang] || m.th || m.en : _t('error') || 'Error';
}

const _fmt = (n) => {
    if (n === null || n === undefined || isNaN(n)) return '';
    return Number(n).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
};

function _renderKpi(stats) {
    if ($('glv-kpi-matched'))
        $('glv-kpi-matched').textContent = stats && stats.matched != null ? stats.matched : '—';
    if ($('glv-kpi-diff'))
        $('glv-kpi-diff').textContent = stats && stats.diff != null ? stats.diff : '—';
    if ($('glv-kpi-unmatched'))
        $('glv-kpi-unmatched').textContent =
            stats && stats.unmatched != null ? stats.unmatched : '—';
}

// ── 历史任务列表 ─────────────────────────────────────────────────
function _fmtTime(s) {
    if (!s) return '';
    try {
        const d = new Date(s);
        if (isNaN(d.getTime())) return s;
        const pad = (n) => String(n).padStart(2, '0');
        return (
            d.getFullYear() +
            '-' +
            pad(d.getMonth() + 1) +
            '-' +
            pad(d.getDate()) +
            ' ' +
            pad(d.getHours()) +
            ':' +
            pad(d.getMinutes())
        );
    } catch (_) {
        return s;
    }
}

export { $, _token, _lang, _authH, _t, _fmt, _glvFailMsg, _renderKpi, _fmtTime };
