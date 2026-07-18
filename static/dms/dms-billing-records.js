/* Pearnly DMS · 记录明细(挂 window.DXBILLRECORDS · 照主站 billing-records.ts 复刻)。
 * 双 tab:扣费记录(usage)| 充值记录(topup)(Zihao 拍板:识别记录不要)。筛选(全部/日/月/年)+
 * 每页 10 条页码器 + 切 tab 竞态丢弃过期响应 + 充值行凭证下载 + 区间导出 xlsx。四态诚实。
 * 卡壳(tab/导出钮/#dms-bill-rec-body)由 dms-billing-html.recordsCard 渲染;本模块填 body + 委托事件。 */
(function (root) {
    'use strict';
    function t(k, v) {
        return typeof root.t === 'function' ? root.t(k, v) : k;
    }
    function esc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(s == null ? '' : s)
            : String(s);
    }
    function api() {
        return root.DXAPI.create();
    }
    function toast(m, k) {
        if (typeof root.showToast === 'function') root.showToast(m, k || 'info');
    }
    function H() {
        return root.DXBILLINGHTML;
    }
    var PAGE = 10;
    var DL =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"/></svg>';

    var R = {
        host: null,
        tab: 'usage',
        period: 'all',
        date: '',
        page: 1,
        total: 0,
        seq: 0,
        exporting: false,
    };

    function pad(n) {
        return (n < 10 ? '0' : '') + n;
    }
    function todayStr() {
        var d = new Date();
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
    }
    function monthAgoStr() {
        var d = new Date();
        d.setMonth(d.getMonth() - 1);
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
    }
    function body() {
        return R.host ? R.host.querySelector('#dms-bill-rec-body') : null;
    }

    // ── 筛选条 ──
    function dateControl() {
        if (R.period === 'day')
            return (
                '<input type="date" class="dms-bill-select" id="dms-bill-rec-date" value="' +
                esc(R.date || todayStr()) +
                '" max="' +
                todayStr() +
                '">'
            );
        if (R.period === 'month')
            return (
                '<input type="month" class="dms-bill-select" id="dms-bill-rec-date" value="' +
                esc((R.date || todayStr()).slice(0, 7)) +
                '">'
            );
        if (R.period === 'year') {
            var y = new Date().getFullYear();
            var opts = '';
            for (var i = 0; i < 7; i++) {
                var yy = y - i;
                opts +=
                    '<option value="' +
                    yy +
                    '"' +
                    ((R.date || todayStr()).slice(0, 4) === String(yy) ? ' selected' : '') +
                    '>' +
                    yy +
                    '</option>';
            }
            return '<select class="dms-bill-select" id="dms-bill-rec-date">' + opts + '</select>';
        }
        return '';
    }
    function filterBar() {
        function opt(v, key) {
            return (
                '<option value="' +
                v +
                '"' +
                (R.period === v ? ' selected' : '') +
                '>' +
                esc(t(key)) +
                '</option>'
            );
        }
        return (
            '<div class="dms-bill-rec-filter"><select class="dms-bill-select" id="dms-bill-rec-period">' +
            opt('all', 'dms-bill-rec-period-all') +
            opt('day', 'dms-bill-rec-period-day') +
            opt('month', 'dms-bill-rec-period-month') +
            opt('year', 'dms-bill-rec-period-year') +
            '</select>' +
            dateControl() +
            '</div>'
        );
    }

    // ── 行渲染 ──
    function badge(cls, key) {
        return '<span class="dms-bill-rec-badge ' + cls + '">' + esc(t(key)) + '</span>';
    }
    function usageRow(r) {
        var title = r.description || r.filename || t('dms-bill-rec-untitled');
        var meta = esc(r.date || '');
        if (r.pages) meta += ' · ' + t('dms-bill-used-fmt', { n: r.pages });
        var b, amt;
        if (r.type === 'subscription') {
            b = badge('neutral', 'dms-bill-rec-b-monthly');
            amt = r.cost_thb ? H().fmtBaht(r.cost_thb) : '';
        } else if (!r.cost_thb) {
            b = badge('free', 'dms-bill-rec-b-free');
            amt = '';
        } else {
            b = badge('bad', 'dms-bill-rec-b-charged');
            amt = '-' + H().fmtBaht(r.cost_thb);
        }
        return row(title, meta, b, amt, null);
    }
    function topupRow(r) {
        var title = r.payer_name || t('dms-bill-topup-title');
        var st =
            r.status === 'approved'
                ? badge('ok', 'dms-bill-hist-approved')
                : r.status === 'rejected'
                  ? badge('bad', 'dms-bill-hist-rejected')
                  : badge('warn', 'dms-bill-hist-pending');
        return row(title, esc(r.created_at || ''), st, '+ ' + H().fmtBaht(r.amount_thb), r.id);
    }
    function row(title, metaHtml, badgeHtml, amt, receiptId) {
        var dl = receiptId
            ? '<button type="button" class="btn dms-bill-rec-dl" data-receipt="' +
              esc(receiptId) +
              '" title="' +
              esc(t('dms-bill-rec-receipt')) +
              '">' +
              DL +
              '</button>'
            : '';
        return (
            '<div class="dms-bill-rec-row"><div class="dms-bill-rec-l"><div class="dms-bill-rec-title">' +
            esc(title) +
            '</div><div class="dms-bill-rec-meta">' +
            metaHtml +
            '</div></div><div class="dms-bill-rec-r">' +
            badgeHtml +
            (amt ? '<span class="dms-bill-rec-amt">' + esc(amt) + '</span>' : '') +
            dl +
            '</div></div>'
        );
    }
    function pager() {
        var tp = Math.max(1, Math.ceil(R.total / PAGE));
        if (tp <= 1)
            return (
                '<div class="dms-bill-pager">' +
                esc(t('dms-bill-rec-total', { n: R.total })) +
                '</div>'
            );
        return (
            '<div class="dms-bill-pager"><button type="button" class="btn dms-bill-page-btn" data-page="' +
            (R.page - 1) +
            '"' +
            (R.page <= 1 ? ' disabled' : '') +
            '>‹</button><span>' +
            R.page +
            ' / ' +
            tp +
            '</span><button type="button" class="btn dms-bill-page-btn" data-page="' +
            (R.page + 1) +
            '"' +
            (R.page >= tp ? ' disabled' : '') +
            '>›</button></div>'
        );
    }

    function load() {
        var bd = body();
        if (!bd) return;
        R.seq++;
        var mySeq = R.seq;
        bd.innerHTML =
            filterBar() +
            '<div class="dms-state loading"><p>' +
            esc(t('dms-bill-loading')) +
            '</p></div>';
        var params = { tab: R.tab, period: R.period, limit: PAGE, offset: (R.page - 1) * PAGE };
        if (R.period !== 'all') params.date = R.date || todayStr();
        api()
            .records(params)
            .then(function (data) {
                if (mySeq !== R.seq) return; // 切 tab/翻页竞态:过期响应丢弃
                if (typeof data.total === 'number' && data.total >= 0) R.total = data.total;
                var rows = data.rows || [];
                var mapper = R.tab === 'topup' ? topupRow : usageRow;
                var listHtml = rows.length
                    ? rows.map(mapper).join('')
                    : '<div class="dms-state empty"><p>' +
                      esc(t('dms-bill-rec-empty')) +
                      '</p></div>';
                bd.innerHTML = filterBar() + listHtml + (rows.length ? pager() : '');
            })
            .catch(function () {
                if (mySeq !== R.seq) return;
                bd.innerHTML =
                    filterBar() +
                    '<div class="dms-state error"><p>' +
                    esc(t('dms-bill-error')) +
                    '</p></div>';
            });
    }

    function switchTab(tab) {
        if (tab === R.tab) return;
        R.tab = tab;
        R.page = 1;
        R.total = 0;
        R.host.querySelectorAll('[data-bill-rectab]').forEach(function (b) {
            b.classList.toggle('on', b.getAttribute('data-bill-rectab') === tab);
        });
        load();
    }
    function gotoPage(p) {
        p = parseInt(p, 10);
        if (!p || p < 1) return;
        R.page = p;
        load();
    }
    function onPeriod(v) {
        R.period = v;
        R.date = v === 'all' ? '' : todayStr();
        R.page = 1;
        load();
    }
    function onDate(v) {
        if (R.period === 'month') R.date = v + '-01';
        else if (R.period === 'year') R.date = v + '-01-01';
        else R.date = v;
        R.page = 1;
        load();
    }

    // ── 凭证下载 / 导出 ──
    function downloadBlob(path, filename, btn) {
        if (btn) btn.disabled = true;
        fetch(path, { headers: root.DXAPI.authHeaders() })
            .then(function (r) {
                if (!r.ok) throw new Error('http_' + r.status);
                return r.blob();
            })
            .then(function (blob) {
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                setTimeout(function () {
                    URL.revokeObjectURL(url);
                }, 60000);
                if (btn) btn.disabled = false;
            })
            .catch(function () {
                if (btn) btn.disabled = false;
                toast(t('dms-bill-rec-receipt-fail'), 'error');
            });
    }
    function downloadReceipt(id, btn) {
        var lang = (root.DXI18N && root.DXI18N.lang) || 'zh';
        downloadBlob(
            '/api/credits/topup/' + encodeURIComponent(id) + '/receipt.pdf?lang=' + lang,
            'pearnly_topup_' + id + '.pdf',
            btn
        );
    }
    function openExport() {
        var ov = document.createElement('div');
        ov.className = 'modal-overlay';
        ov.innerHTML =
            '<div class="modal"><div class="modal-head">' +
            esc(t('dms-bill-rec-export')) +
            '</div><div class="modal-body"><p class="sub">' +
            esc(t('dms-bill-rec-range-hint')) +
            '</p><div class="dms-bill-field"><span>' +
            esc(t('dms-bill-rec-range-from')) +
            '</span><input type="date" class="dms-bill-input" id="xm-from" value="' +
            monthAgoStr() +
            '" max="' +
            todayStr() +
            '"></div><div class="dms-bill-field"><span>' +
            esc(t('dms-bill-rec-range-to')) +
            '</span><input type="date" class="dms-bill-input" id="xm-to" value="' +
            todayStr() +
            '" max="' +
            todayStr() +
            '"></div><div class="dms-bill-err" id="xm-err" style="display:none"></div></div><div class="dms-bill-modal-foot"><button type="button" class="btn" id="xm-cancel">' +
            esc(t('dms-op-modal-cancel')) +
            '</button><button type="button" class="btn primary" id="xm-do">' +
            esc(t('dms-bill-rec-export')) +
            '</button></div></div>';
        document.body.appendChild(ov);
        function close() {
            ov.remove();
        }
        ov.addEventListener('click', function (e) {
            if (e.target === ov) close();
        });
        ov.querySelector('#xm-cancel').addEventListener('click', close);
        ov.querySelector('#xm-do').addEventListener('click', function () {
            var from = ov.querySelector('#xm-from').value;
            var to = ov.querySelector('#xm-to').value;
            var err = ov.querySelector('#xm-err');
            if (!from || !to || from > to) {
                err.textContent = t('dms-bill-rec-range-invalid');
                err.style.display = '';
                return;
            }
            var lang = (root.DXI18N && root.DXI18N.lang) || 'zh';
            downloadBlob(
                '/api/credits/billing-export?lang=' +
                    lang +
                    '&date_from=' +
                    from +
                    '&date_to=' +
                    to,
                'pearnly_billing_' + todayStr().replace(/-/g, '') + '.xlsx',
                ov.querySelector('#xm-do')
            );
            setTimeout(close, 400);
        });
    }

    function onClick(e) {
        var tab = e.target.closest('[data-bill-rectab]');
        if (tab) return void switchTab(tab.getAttribute('data-bill-rectab'));
        if (e.target.closest('#dms-bill-rec-export')) return void openExport();
        var pg = e.target.closest('[data-page]');
        if (pg && !pg.disabled) return void gotoPage(pg.getAttribute('data-page'));
        var dl = e.target.closest('[data-receipt]');
        if (dl) return void downloadReceipt(dl.getAttribute('data-receipt'), dl);
    }
    function onChange(e) {
        if (e.target.id === 'dms-bill-rec-period') return void onPeriod(e.target.value);
        if (e.target.id === 'dms-bill-rec-date') return void onDate(e.target.value);
    }

    function mount(cardEl) {
        R.host = cardEl;
        if (!cardEl._recWired) {
            cardEl.addEventListener('click', onClick);
            cardEl.addEventListener('change', onChange);
            cardEl._recWired = true;
        }
        load();
    }

    root.DXBILLRECORDS = { mount: mount, reload: load };
})(typeof self !== 'undefined' ? self : this);
