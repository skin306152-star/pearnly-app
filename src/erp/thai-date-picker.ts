import './thai-date-picker.css';
const pad = (n: number) => String(n).padStart(2, '0');
export function thaiToday(): string {
    const parts = new Intl.DateTimeFormat('en', {
        timeZone: 'Asia/Bangkok',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).formatToParts(new Date());
    const part = (key: string) => parts.find((p) => p.type === key)!.value;
    return `${part('year')}-${part('month')}-${part('day')}`;
}
export function thaiDateIso(value: string): string {
    const m =
        value.trim().match(/^(\d{4})-(\d{1,2})-(\d{1,2})/) ||
        value.trim().match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})/);
    if (!m) return '';
    const yearFirst = m[1].length === 4;
    let y = Number(yearFirst ? m[1] : m[3]);
    if (y >= 2400) y -= 543;
    const month = Number(m[2]),
        day = Number(yearFirst ? m[3] : m[1]);
    const date = new Date(y, month - 1, day);
    return date.getFullYear() === y && date.getMonth() === month - 1 && date.getDate() === day
        ? `${y}-${pad(month)}-${pad(day)}`
        : '';
}
export function thaiDateText(value: string): string {
    const iso = thaiDateIso(value);
    if (!iso) return value;
    const [y, m, d] = iso.split('-');
    return `${d}/${m}/${Number(y) + 543}`;
}
function calendarText() {
    const lang = (document.documentElement.lang || 'th').split('-')[0];
    const words: Record<string, string[]> = {
        th: [
            'เลือกวันที่ พ.ศ.',
            'เดือนก่อน',
            'เดือนถัดไป',
            'เดือน',
            'ปี พ.ศ.',
            'วันนี้',
            'ล้าง',
            'ปิด',
            'วว/ดด/พ.ศ.',
        ],
        zh: [
            '选择佛历日期',
            '上个月',
            '下个月',
            '月份',
            '佛历年份',
            '今天',
            '清空',
            '关闭',
            '日/月/佛历年',
        ],
        en: [
            'Choose date (BE)',
            'Previous month',
            'Next month',
            'Month',
            'Year (BE)',
            'Today',
            'Clear',
            'Close',
            'DD/MM/BE',
        ],
        ja: [
            '仏暦の日付を選択',
            '前月',
            '翌月',
            '月',
            '仏暦年',
            '今日',
            'クリア',
            '閉じる',
            '日/月/仏暦年',
        ],
    };
    return {
        locale:
            ({ zh: 'zh-CN', en: 'en-GB', ja: 'ja-JP', th: 'th-TH' } as Record<string, string>)[
                lang
            ] || 'th-TH',
        words: words[lang] || words.th,
    };
}
function openPicker(input: HTMLInputElement, trigger: HTMLButtonElement) {
    const { locale, words } = calendarText();
    const iso = thaiDateIso(input.value);
    const date = new Date((iso || thaiToday()) + 'T12:00:00');
    let year = date.getFullYear(),
        month = date.getMonth();
    const dialog = document.createElement('dialog');
    dialog.className = 'thai-date-dialog';
    dialog.setAttribute('aria-label', words[0]);
    const close = () => {
        dialog.close();
        dialog.remove();
        trigger.focus();
    };
    const choose = (value: string) => {
        const raw = (
            input.dataset.gridField ||
            input.dataset.ivField ||
            input.dataset.k ||
            input.dataset.field ||
            input.name
        ).includes('date_raw');
        input.value = raw || input.dataset.businessDate === 'true' ? thaiDateText(value) : value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        close();
    };
    const render = () => {
        dialog.replaceChildren();
        const header = document.createElement('div');
        header.className = 'td-head';
        const prev = document.createElement('button');
        prev.type = 'button';
        prev.textContent = '‹';
        prev.setAttribute('aria-label', words[1]);
        const next = document.createElement('button');
        next.type = 'button';
        next.textContent = '›';
        next.setAttribute('aria-label', words[2]);
        const months = document.createElement('select');
        months.setAttribute('aria-label', words[3]);
        for (let i = 0; i < 12; i++) {
            const option = new Option(
                new Intl.DateTimeFormat(locale, { month: 'long' }).format(new Date(2026, i, 1)),
                String(i)
            );
            months.add(option);
        }
        months.value = String(month);
        const years = document.createElement('input');
        years.type = 'number';
        years.min = '2443';
        years.max = '2743';
        years.value = String(year + 543);
        years.setAttribute('aria-label', words[4]);
        months.onchange = () => {
            month = Number(months.value);
            render();
        };
        years.onchange = () => {
            if (years.checkValidity() && years.value) {
                year = Number(years.value) - 543;
                render();
            }
        };
        prev.onclick = () => {
            if (--month < 0) {
                month = 11;
                year--;
            }
            render();
        };
        next.onclick = () => {
            if (++month > 11) {
                month = 0;
                year++;
            }
            render();
        };
        header.append(prev, months, years, next);
        const grid = document.createElement('div');
        grid.className = 'td-grid';
        Array.from({ length: 7 }, (_, day) =>
            new Intl.DateTimeFormat(locale, { weekday: 'short' }).format(new Date(2026, 0, 4 + day))
        ).forEach((text) => {
            const el = document.createElement('span');
            el.textContent = text;
            grid.append(el);
        });
        for (let i = 0; i < new Date(year, month, 1).getDay(); i++)
            grid.append(document.createElement('span'));
        for (let day = 1; day <= new Date(year, month + 1, 0).getDate(); day++) {
            const value = `${year}-${pad(month + 1)}-${pad(day)}`;
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = String(day);
            button.setAttribute('aria-label', thaiDateText(value));
            button.classList.toggle('selected', value === iso);
            button.disabled = !!(
                (input.min && value < input.min) ||
                (input.max && value > input.max)
            );
            button.onclick = () => choose(value);
            grid.append(button);
        }
        const footer = document.createElement('div');
        footer.className = 'td-footer';
        for (const [label, action] of [
            [
                words[5],
                () => {
                    choose(thaiToday());
                },
            ],
            [words[6], () => choose('')],
            [words[7], close],
        ] as const) {
            const b = document.createElement('button');
            b.type = 'button';
            b.textContent = label;
            b.onclick = action;
            footer.append(b);
        }
        dialog.append(header, grid, footer);
    };
    dialog.addEventListener('cancel', (event) => {
        event.preventDefault();
        close();
    });
    document.body.append(dialog);
    render();
    dialog.showModal();
}
export function installThaiDates(root: ParentNode = document) {
    root.querySelectorAll<HTMLInputElement>('input').forEach((input) => {
        const key =
            input.name ||
            input.dataset.gridField ||
            input.dataset.ivField ||
            input.dataset.k ||
            input.dataset.field ||
            input.dataset.fld ||
            '';
        const isDate =
            input.type === 'date' ||
            /^(date|due_date|delivery_date|bill_date|date_raw)$/.test(key) ||
            /:(date|date_raw)$/.test(key);
        if (!isDate || input.dataset.thaiDate) return;
        input.dataset.thaiDate = 'true';
        if (input.type !== 'date') input.dataset.businessDate = 'true';
        const wrapper = document.createElement('span');
        wrapper.className = 'thai-date-field';
        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'thai-date-trigger';
        trigger.setAttribute('aria-haspopup', 'dialog');
        const text = document.createElement('span');
        const icon = document.createElement('span');
        icon.innerHTML =
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18M8 15h2M14 15h2M8 18h2"/></svg>';
        icon.setAttribute('aria-hidden', 'true');
        const sync = () => {
            text.textContent = thaiDateText(input.value) || calendarText().words[8];
            trigger.disabled = input.disabled;
        };
        trigger.append(text, icon);
        input.before(wrapper);
        wrapper.append(input, trigger);
        input.type = 'hidden';
        if (input.readOnly) {
            trigger.disabled = true;
            icon.hidden = true;
        } else trigger.onclick = () => openPicker(input, trigger);
        input.addEventListener('input', sync);
        input.addEventListener('change', sync);
        sync();
        if (input.readOnly) trigger.disabled = true;
    });
}
if (/^\/erp(?:\/|$)|^\/liff\/erp(?:\/|$)/.test(location.pathname)) {
    const observer = new MutationObserver(() => installThaiDates());
    observer.observe(document.documentElement, { childList: true, subtree: true });
    installThaiDates();
}
