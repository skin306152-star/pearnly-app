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
function openPicker(input: HTMLInputElement, trigger: HTMLButtonElement) {
    const iso = thaiDateIso(input.value);
    const date = new Date((iso || thaiToday()) + 'T12:00:00');
    let year = date.getFullYear(),
        month = date.getMonth();
    const dialog = document.createElement('dialog');
    dialog.className = 'thai-date-dialog';
    dialog.setAttribute('aria-label', 'เลือกวันที่ พ.ศ.');
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
        prev.setAttribute('aria-label', 'เดือนก่อน');
        const next = document.createElement('button');
        next.type = 'button';
        next.textContent = '›';
        next.setAttribute('aria-label', 'เดือนถัดไป');
        const months = document.createElement('select');
        months.setAttribute('aria-label', 'เดือน');
        for (let i = 0; i < 12; i++) {
            const option = new Option(
                new Intl.DateTimeFormat('th-TH', { month: 'long' }).format(new Date(2026, i, 1)),
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
        years.setAttribute('aria-label', 'ปี พ.ศ.');
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
        ['อา.', 'จ.', 'อ.', 'พ.', 'พฤ.', 'ศ.', 'ส.'].forEach((text) => {
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
                'วันนี้',
                () => {
                    choose(thaiToday());
                },
            ],
            ['ล้าง', () => choose('')],
            ['ปิด', close],
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
            text.textContent = thaiDateText(input.value) || 'วว/ดด/พ.ศ.';
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
