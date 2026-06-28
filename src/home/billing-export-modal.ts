// ============================================================
// 首页 · 账单导出区间选择弹窗 · 2026-06-28
//
// 点「导出明细」先弹此窗:起始 / 结束两个年月日选择器(默认近一个月 ~ 今天,
// 上限今天,结束不得早于起始)。确定 → resolve {from,to};取消/关闭/ESC → null。
// billing-records.ts 经 window._pickExportRange 调用,选定后再请求 billing-export。
// 独立成文件以守 <500 行闸;_t/_esc 与同域模块同款轻桥(window.t/escapeHtml)。
// ============================================================

function _t(k: string, fb?: string): string {
    try {
        return (typeof window.t === 'function' ? window.t(k) : fb) || fb || k;
    } catch (_) {
        return fb || k;
    }
}
function _esc(s: unknown): string {
    return typeof window.escapeHtml === 'function'
        ? window.escapeHtml(s)
        : String(s == null ? '' : s).replace(
              /[&<>"']/g,
              (c) =>
                  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[
                      c as '&' | '<' | '>' | '"' | "'"
                  ]
          );
}
function _pad(n: number): string {
    return String(n).padStart(2, '0');
}
function _todayStr(): string {
    const d = new Date();
    return d.getFullYear() + '-' + _pad(d.getMonth() + 1) + '-' + _pad(d.getDate());
}
function _oneMonthAgoStr(): string {
    const d = new Date();
    d.setMonth(d.getMonth() - 1); // JS 自动处理短月/跨年回退
    return d.getFullYear() + '-' + _pad(d.getMonth() + 1) + '-' + _pad(d.getDate());
}

function pickExportRange(): Promise<{ from: string; to: string } | null> {
    return new Promise((resolve) => {
        const today = _todayStr();
        const ov = document.createElement('div');
        ov.className = 'modal-overlay ui rec-xm-overlay';
        ov.innerHTML =
            '<div class="modal rec-xm-card">' +
            '<div class="modal-head"><div class="modal-title">' +
            _esc(_t('rec-export', '导出明细')) +
            '</div><button class="rec-xm-x" id="rec-xm-x" aria-label="' +
            _esc(_t('confirm-cancel', '取消')) +
            '">×</button></div>' +
            '<div class="rec-xm-body"><div class="rec-xm-hint">' +
            _esc(_t('rec-range-hint', '选择导出区间(年月日 ~ 年月日)')) +
            '</div><div class="rec-xm-fields">' +
            '<label class="rec-xm-field"><span>' +
            _esc(_t('rec-range-from', '起始日期')) +
            '</span><input type="date" class="fin rec-xm-date" id="rec-xm-from" max="' +
            _esc(today) +
            '" value="' +
            _esc(_oneMonthAgoStr()) +
            '"></label>' +
            '<label class="rec-xm-field"><span>' +
            _esc(_t('rec-range-to', '结束日期')) +
            '</span><input type="date" class="fin rec-xm-date" id="rec-xm-to" max="' +
            _esc(today) +
            '" value="' +
            _esc(today) +
            '"></label></div>' +
            '<div class="rec-xm-err" id="rec-xm-err"></div></div>' +
            '<div class="rec-xm-foot"><button class="btn sec" id="rec-xm-cancel">' +
            _esc(_t('confirm-cancel', '取消')) +
            '</button><button class="btn pri" id="rec-xm-ok">' +
            _esc(_t('rec-do-export', '导出')) +
            '</button></div></div>';
        document.body.appendChild(ov);

        const fromEl = ov.querySelector('#rec-xm-from') as HTMLInputElement;
        const toEl = ov.querySelector('#rec-xm-to') as HTMLInputElement;
        const errEl = ov.querySelector('#rec-xm-err') as HTMLElement;
        const done = (val: { from: string; to: string } | null) => {
            document.removeEventListener('keydown', onKey);
            ov.remove();
            resolve(val);
        };
        const onKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') done(null);
        };
        const confirm = () => {
            const from = fromEl.value;
            const to = toEl.value;
            if (!from || !to) {
                errEl.textContent = _t('rec-range-need', '请选择起始与结束日期');
                return;
            }
            if (from > to) {
                errEl.textContent = _t('rec-range-invalid', '结束日期不能早于起始日期');
                return;
            }
            done({ from, to });
        };
        (ov.querySelector('#rec-xm-ok') as HTMLElement).onclick = confirm;
        (ov.querySelector('#rec-xm-cancel') as HTMLElement).onclick = () => done(null);
        (ov.querySelector('#rec-xm-x') as HTMLElement).onclick = () => done(null);
        ov.onclick = (e) => {
            if (e.target === ov) done(null);
        };
        document.addEventListener('keydown', onKey);
        setTimeout(() => fromEl.focus(), 50);
    });
}

window._pickExportRange = pickExportRange;
