// ============================================================
// 共享日期格式化 · 全站唯一出口(显示/表格/CSV/PDF 全走它)
// ------------------------------------------------------------
// 内部永远存公历 ISO(DB 不存佛历)· 此处只按用户偏好渲染:
//   历法 pearnly_calendar:'buddhist'(默认 พ.ศ. = 公历年 +543)| 'gregorian'
//   样式 pearnly_general_date_format:YYYY-MM-DD / DD/MM/YYYY / …(设置→通用)
// window.formatDate / getCalendar / setCalendar 供非模块代码裸调。
// ============================================================
/* eslint-disable no-undef */

const CAL_KEY = 'pearnly_calendar';
const FMT_KEY = 'pearnly_general_date_format';

type Calendar = 'buddhist' | 'gregorian';

export function getCalendar(): Calendar {
    try {
        return localStorage.getItem(CAL_KEY) === 'gregorian' ? 'gregorian' : 'buddhist';
    } catch (_) {
        return 'buddhist';
    }
}

export function setCalendar(v: string): void {
    try {
        localStorage.setItem(CAL_KEY, v === 'gregorian' ? 'gregorian' : 'buddhist');
    } catch (_) {
        /* silent · 私模/配额 */
    }
}

function getStyle(): string {
    try {
        return localStorage.getItem(FMT_KEY) || 'YYYY-MM-DD';
    } catch (_) {
        return 'YYYY-MM-DD';
    }
}

// 接受 ISO 串 / Date / 时间戳;纯日期串按本地构造避免 UTC 偏移差一天。
export function toDate(input: unknown): Date | null {
    if (input == null || input === '') return null;
    if (input instanceof Date) return isNaN(input.getTime()) ? null : input;
    if (typeof input === 'number') {
        const d = new Date(input);
        return isNaN(d.getTime()) ? null : d;
    }
    const s = String(input).trim();
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    const d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
}

export function formatDate(input: unknown, opts?: { style?: string; calendar?: Calendar }): string {
    const d = toDate(input);
    if (!d) return '';
    const style = (opts && opts.style) || getStyle();
    const cal = (opts && opts.calendar) || getCalendar();
    const year = cal === 'buddhist' ? d.getFullYear() + 543 : d.getFullYear();
    const yyyy = String(year);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    switch (style) {
        case 'DD/MM/YYYY':
            return `${dd}/${mm}/${yyyy}`;
        case 'MM/DD/YYYY':
            return `${mm}/${dd}/${yyyy}`;
        case 'DD-MM-YYYY':
            return `${dd}-${mm}-${yyyy}`;
        case 'YYYY/MM/DD':
            return `${yyyy}/${mm}/${dd}`;
        case 'YYYY-MM-DD':
        default:
            return `${yyyy}-${mm}-${dd}`;
    }
}

declare global {
    interface Window {
        formatDate: typeof formatDate;
        getCalendar: typeof getCalendar;
        setCalendar: typeof setCalendar;
    }
}

window.formatDate = formatDate;
window.getCalendar = getCalendar;
window.setCalendar = setCalendar;
