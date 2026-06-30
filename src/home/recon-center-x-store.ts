// 对账中心重设计 · 共享状态 + 每类型配置(2026-06-14)
// 三类型共用一套外壳;切换=换配置(doc_type/端点/字段名)+清残留。

export type RxSide = 'left' | 'right';

export interface RxFile {
    file: File;
    method: 'standard' | 'table' | 'scan';
    ext: string;
    size: number;
}

export interface RxResult {
    rate: number; // 0..1
    matched: number;
    difference: number;
    unmatched: number;
    total: number;
    headers: string[];
    rows: Array<{ cells: string[]; status: 'matched' | 'difference' | 'unmatched' }>;
    issues: Array<{
        icon: string;
        title: string;
        sub: string;
        count: number;
        tone: 'warn' | 'none';
    }>;
    exportKind: 'bank' | 'income' | 'tax';
    exportTaskId: string;
}

export interface RxState {
    tab: 'bank' | 'tax' | 'income';
    left: RxFile | null;
    right: RxFile | null;
    running: boolean;
    jobId: string | null;
    result: RxResult | null;
    filter: 'all' | 'matched' | 'difference' | 'unmatched';
    page: number;
    pageSize: number;
}

export const RX: RxState = {
    tab: 'bank',
    left: null,
    right: null,
    running: false,
    jobId: null,
    result: null,
    filter: 'all',
    page: 1,
    pageSize: 50,
};

export interface RxTabConfig {
    // 左右上传卡的模板 doc_type(下载标准模板 + 模板中心)
    leftDoc: 'statement' | 'gl' | 'vat' | 'invoice';
    rightDoc: 'statement' | 'gl' | 'vat' | 'invoice';
    // submit 端点 + multipart 字段名(左→leftField,右→rightField)
    submit: string;
    leftField: string;
    rightField: string;
    // 银行对账才有余额预检(GL/账单 期初期末);其余类型隐藏
    balance: boolean;
    // 结果读取/导出的种类(决定 result 适配器与导出端点)
    kind: 'bank' | 'income' | 'tax';
}

// 模板/端点全部以后端为准(docs/reconciliation/00 §1.3);UI 稿的「收款流水/销售收入」作废。
export const RX_TABS: Record<RxState['tab'], RxTabConfig> = {
    bank: {
        leftDoc: 'statement',
        rightDoc: 'gl',
        submit: '/api/recon/bank-v2/submit',
        leftField: 'stmt_files',
        rightField: 'gl_files',
        balance: true,
        kind: 'bank',
    },
    income: {
        leftDoc: 'gl',
        rightDoc: 'vat',
        submit: '/api/recon/gl-vat/submit',
        leftField: 'gl_files',
        rightField: 'vat_files',
        balance: false,
        kind: 'income',
    },
    tax: {
        leftDoc: 'vat',
        rightDoc: 'invoice',
        submit: '/api/vat_excel/submit',
        leftField: 'reports',
        rightField: 'invoices',
        balance: false,
        kind: 'tax',
    },
};

export const RX_ACCEPT = '.pdf,.png,.jpg,.jpeg,.webp,.tiff,.xlsx,.xls,.csv,.doc,.docx';
const RX_SPREADSHEET = ['xlsx', 'xls', 'csv', 'tsv'];

// 读取方式判定(provisional · 真实标准/普通区分由 submit 的 needs_mapping 决定):
// 表格类按扩展名 → 普通表格读取;文件名带标准模板签名(Pearnly_<type> / 标准模板)→ 标准模板读取;
// 其余(PDF/图片/Word)→ 文件内容读取。卡片不展示任何行数/项数假数据。
export function rxClassify(name: string): RxFile['method'] {
    const lower = (name || '').toLowerCase();
    const ext = (lower.split('.').pop() || '').toLowerCase();
    if (RX_SPREADSHEET.includes(ext)) {
        const isTpl =
            lower.includes('pearnly') || lower.includes('标准模板') || lower.includes('template');
        return isTpl ? 'standard' : 'table';
    }
    return 'scan';
}

export function rxExt(name: string): string {
    const e = (name || '').split('.').pop() || '';
    return e.toUpperCase().slice(0, 4) || 'FILE';
}

export function rxCfg(): RxTabConfig {
    return RX_TABS[RX.tab];
}

export function rxLang(): string {
    return (window as any)._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
}

export function rxToken(): string {
    return localStorage.getItem('mrpilot_token') || '';
}

// 文案:走全局 window.t(i18n),缺失给中文兜底(开发期),正式 key 在 i18n-data.js 四语齐。
export function tt(key: string, fallback: string): string {
    const fn = (window as any).t;
    if (typeof fn === 'function') {
        const v = fn(key);
        if (v && v !== key) return v;
    }
    return fallback;
}

export function rxFmt(v: number | null | undefined): string {
    if (v === null || v === undefined || Number.isNaN(v)) return '—';
    return Number(v).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

export function rxEsc(s: unknown): string {
    if (s === null || s === undefined) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

export function rxFmtSize(bytes: number): string {
    if (!bytes) return '0 KB';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    let n = bytes;
    while (n >= 1024 && i < units.length - 1) {
        n /= 1024;
        i++;
    }
    return `${n.toFixed(i ? 1 : 0)} ${units[i]}`;
}

// 后端真实失败码 → 用户能懂的原因(不再笼统「对账未完成」)。纯映射,就近用 tt。
export function rxFailMsg(code: string | null | undefined): string {
    const map: Record<string, string> = {
        timeout: tt('rcx-err-timeout', '处理超时，请稍后重试'),
        poll_unreachable: tt('rcx-err-network', '网络错误'),
        gl_no_revenue_rows: tt(
            'rcx-fc-gl-no-rev',
            '总账中没有收入科目(科目代码以 4 开头),无法做收入对账'
        ),
        gl_parse_failed: tt('rcx-fc-gl-parse', '总账解析失败,请检查文件格式或换标准模板'),
        gl_headers_not_found: tt('rcx-fc-gl-head', '认不出总账表头(需含 科目/借方/贷方 列)'),
        vat_no_rows: tt('rcx-fc-vat-no-rows', '税表中没有可读取的数据行,请检查文件'),
        vat_parse_failed: tt('rcx-fc-vat-parse', '税表解析失败,请检查文件格式或换标准模板'),
        stmt_no_rows: tt('rcx-fc-stmt-no-rows', '银行账单中没有交易数据,请确认上传了正确的账单'),
        stmt_headers_not_found: tt(
            'rcx-fc-stmt-head',
            '认不出银行账单表头(需含 日期/金额/余额 列)'
        ),
        file_unreadable: tt('rcx-fc-unreadable', '文件无法读取,可能已损坏或被加密'),
        file_not_supported: tt(
            'rcx-fc-unsupported',
            '不支持此文件类型,请上传 PDF / 图片 / Excel / CSV'
        ),
        ocr_failed: tt('rcx-fc-ocr', '文件识别失败,请换更清晰的版本或转成 Excel / CSV 重传'),
    };
    return (code && map[code]) || tt('rcx-err-generic', '对账未能完成,请检查文件后重试');
}
