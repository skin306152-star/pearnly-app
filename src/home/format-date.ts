// ============================================================
// 共享日期格式化 · 全站唯一出口(显示/表格/CSV/PDF 全走它)
// ------------------------------------------------------------
// 内部永远存公历 ISO(DB 不存佛历)· 用户可见日期统一按佛历渲染(公历年 +543)。
//   样式 pearnly_general_date_format:YYYY-MM-DD / DD/MM/YYYY / …(设置→通用)
// formatDate 纯日期 · formatDateTime = formatDate + 本地 HH:mm(带时间显示用)。
// window.formatDate / formatDateTime / getCalendar / setCalendar 供非模块代码裸调。
// ============================================================
/* eslint-disable no-undef */

const CAL_KEY = 'pearnly_calendar';
const FMT_KEY = 'pearnly_general_date_format';

type Calendar = 'buddhist' | 'gregorian';

export function getCalendar(): Calendar {
    return 'buddhist';
}

export function setCalendar(_v: string): void {
    try {
        localStorage.setItem(CAL_KEY, 'buddhist');
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

// 机读 ISO(YYYY-MM-DD · 本地时区):API 参数/字典键用,永远公历 —— 跟 formatDate
// (用户偏好渲染 · 可佛历)是两种用途,别混:参数走它,屏上显示走 formatDate。
export function ymdIso(d: Date): string {
    const p2 = (n: number) => String(n).padStart(2, '0');
    return d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate());
}

export function formatDate(input: unknown, opts?: { style?: string; calendar?: Calendar }): string {
    const d = toDate(input);
    if (!d) return '';
    const style = (opts && opts.style) || getStyle();
    const cal: Calendar = 'buddhist';
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

export function formatDateTime(
    input: unknown,
    opts?: { style?: string; calendar?: Calendar }
): string {
    const d = toDate(input);
    if (!d) return '';
    const p2 = (n: number) => String(n).padStart(2, '0');
    return formatDate(d, opts) + ' ' + p2(d.getHours()) + ':' + p2(d.getMinutes());
}

declare global {
    interface Window {
        formatDate: typeof formatDate;
        formatDateTime: typeof formatDateTime;
        getCalendar: typeof getCalendar;
        setCalendar: typeof setCalendar;
    }
}

window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.getCalendar = getCalendar;
window.setCalendar = setCalendar;
