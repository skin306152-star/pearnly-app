// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 v2 纯工具(无状态)· 从 bank-recon-v2.js 抽出
// verbatim 0 改逻辑。
// ============================================================

const $ = (id) => document.getElementById(id);
function fmtNum(v) {
    if (v === null || v === undefined) return '—';
    const n = Number(v);
    if (isNaN(n)) return '—';
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtDate(s) {
    if (!s) return '—';
    return String(s).slice(0, 10).split('-').reverse().join('/');
}
function esc2(s) {
    return String(s || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

// BUG-FIX-RECON-GLCSV · 后台整侧解析明确失败(无表格可现场修)→ 按 error_code 给 4 语友好原因 + 引导
function _brv2FailMsg(code, lang) {
    lang = window._currentLang || lang || 'th';
    const M = {
        stmt_headers_not_found: {
            zh: '认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传',
            th: 'หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่',
            en: 'Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV',
            ja: '銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください',
        },
        gl_headers_not_found: {
            zh: '认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传',
            th: 'หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่',
            en: 'Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV',
            ja: 'GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください',
        },
        stmt_no_rows: {
            zh: '文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传',
            th: 'ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า',
            en: 'No transaction rows found · please upload the correct statement, or try a clearer version',
            ja: '取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください',
        },
        no_rows: {
            zh: '解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传',
            th: 'ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่',
            en: 'No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version',
            ja: '解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください',
        },
        file_unreadable: {
            zh: '文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传',
            th: 'อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel',
            en: 'File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel',
            ja: 'ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください',
        },
        file_not_supported: {
            zh: '不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV',
            th: 'ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV',
            en: 'File type not supported · please upload PDF / image / Excel / CSV',
            ja: 'このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください',
        },
        ocr_failed: {
            zh: '文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传',
            th: 'อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV',
            en: 'Could not read the file · try a clearer version, or convert to PDF / Excel / CSV',
            ja: '読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください',
        },
    };
    const generic = {
        zh: '解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传',
        th: 'อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่',
        en: 'Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload',
        ja: '解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください',
    };
    const m = M[code] || generic;
    return m[lang] || m.th || m.en;
}

function _brv2FmtSize(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

function _brv2T(key, fallback) {
    return (window.t && window.t(key)) || fallback;
}
function _brv2EscHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
function _brv2FmtNum(v) {
    if (!Number.isFinite(+v)) return '—';
    return (+v).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

export { $, fmtNum, fmtDate, esc2, _brv2FailMsg, _brv2FmtSize, _brv2T, _brv2EscHtml, _brv2FmtNum };
