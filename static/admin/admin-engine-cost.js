/*
 * Pearnly · admin-engine-cost.js · 超管「OCR 引擎」页的逐入口成本区
 *
 * 存在的理由:定价按 ฿1.5/页 走,但银行对账单实际约 ฿2.2/页 —— 混合均值把这个差价藏了很久。
 * 所以这块只干一件事:把每个入口 × 单据的每页成本单独摊开,画上售价参考线,谁在亏一眼看见。
 *
 * 两条诚实约束,别为了图好看破掉:
 *   · 页数未知的行(如文件转换)cost_per_page 是 null,不是 0 —— 表里写「—」,柱图里不画。
 *   · 归因列上线前的历史行落在 unattributed,单独一行灰显,不许并进别的入口凑整。
 */
(function () {
    'use strict';

    // 老板当前对外售价(฿/页)。参考线用它,不是从后端算的 —— 它是定价决策的输入,不是观测值。
    const PRICE_THB = 1.5;
    const DAY_OPTIONS = [7, 30, 90];
    // 柱子超过这个数,横轴标签就挤成一团。按每页成本降序取前 N,并在图下说明截断了多少。
    const MAX_BARS = 12;

    let D = null;
    let days = 7;
    let bound = false;
    let unattributed = null;

    function _t(k) {
        return D.t(k);
    }

    /** 缺翻译回落原值:入口/单据枚举随后端加,前端漏配也要照实显示。 */
    function _label(prefix, value) {
        if (!value) return '—';
        const text = D.t(prefix + value);
        return text === prefix + value ? value : text;
    }

    function _baht(n) {
        if (n == null) return '—';
        // 四舍五入到 0.00 但其实花了钱的行,写 0.00 等于说它免费。
        if (n > 0 && n < 0.005) return '< ฿ 0.01';
        return '฿ ' + D.fmt(n, 2);
    }

    function _seconds(ms) {
        return ms == null ? '—' : D.fmt(ms / 1000, 1) + 's';
    }

    function _int(n) {
        return n ? D.fmt(n, 0) : '—';
    }

    function _stateBox(kind, message, retry) {
        return (
            '<div class="eng-state eng-state-' +
            kind +
            '" data-eng-state="' +
            kind +
            '"><span class="eng-state-msg">' +
            D.esc(message) +
            '</span>' +
            (retry
                ? '<button type="button" class="btn btn-sm" data-eng-retry="costs">' +
                  D.esc(_t('adm-eng-retry')) +
                  '</button>'
                : '') +
            '</div>'
        );
    }

    function _rowLabel(r) {
        const doc = r.doc_type ? ' · ' + _label('adm-eng-doc-', r.doc_type) : '';
        return _label('adm-eng-entry-', r.entry_point) + doc;
    }

    /** 横轴标签:入口一行、单据一行(柱子只有几十像素宽,一行排不下两个名字)。 */
    function _axisLabel(r) {
        const entry = _label('adm-eng-entry-', r.entry_point);
        return r.doc_type ? entry + '\n' + _label('adm-eng-doc-', r.doc_type) : entry;
    }

    function _tip(r) {
        return (
            '<b>' +
            D.esc(_rowLabel(r)) +
            '</b><br/>' +
            D.esc(_t('adm-eng-col-perpage')) +
            ' ' +
            _baht(r.cost_per_page) +
            '<br/>' +
            D.esc(_t('adm-eng-col-pages')) +
            ' ' +
            _int(r.pages) +
            ' · ' +
            D.esc(_t('adm-eng-col-calls')) +
            ' ' +
            _int(r.calls) +
            '<br/>' +
            D.esc(_t('adm-eng-col-cost')) +
            ' ' +
            _baht(r.cost_thb) +
            '<br/>' +
            D.esc((r.models || []).join(' · ') || '—')
        );
    }

    function _tableRow(r, muted) {
        const models = (r.models || []).join(' · ');
        return (
            '<tr' +
            (muted ? ' class="eng-row-muted"' : '') +
            '><td>' +
            D.esc(muted ? _t('adm-eng-unattributed') : _label('adm-eng-entry-', r.entry_point)) +
            '</td><td>' +
            D.esc(r.doc_type ? _label('adm-eng-doc-', r.doc_type) : '—') +
            '</td><td>' +
            _int(r.calls) +
            '</td><td>' +
            _int(r.pages) +
            '</td><td>' +
            _baht(r.cost_per_page) +
            '</td><td>' +
            _baht(r.cost_thb) +
            '</td><td>' +
            _seconds(r.p50_latency_ms) +
            '</td><td class="eng-cell-text">' +
            D.esc(models || '—') +
            '</td></tr>'
        );
    }

    function _table(rows, un) {
        const cols = [
            'adm-eng-col-entry',
            'adm-eng-col-doc',
            'adm-eng-col-calls',
            'adm-eng-col-pages',
            'adm-eng-col-perpage',
            'adm-eng-col-cost',
            'adm-eng-col-p50',
            'adm-eng-col-models',
        ];
        let body = rows.map(function (r) {
            return _tableRow(r, false);
        });
        if (un && un.calls) {
            body = body.concat(
                _tableRow(
                    {
                        entry_point: null,
                        doc_type: null,
                        calls: un.calls,
                        pages: 0,
                        cost_per_page: null,
                        cost_thb: un.cost_thb,
                        p50_latency_ms: null,
                        models: [],
                    },
                    true
                )
            );
        }
        return (
            '<div class="cost-table-wrap"><table class="cost-table eng-table"><thead><tr><th>' +
            cols
                .map(function (c) {
                    return D.esc(_t(c));
                })
                .join('</th><th>') +
            '</th></tr></thead><tbody>' +
            body.join('') +
            '</tbody></table></div>'
        );
    }

    function _donutSlices(rows, un) {
        const byEntry = {};
        rows.forEach(function (r) {
            byEntry[r.entry_point] = (byEntry[r.entry_point] || 0) + r.cost_thb;
        });
        const slices = Object.keys(byEntry).map(function (k) {
            return { name: _label('adm-eng-entry-', k), value: byEntry[k] };
        });
        if (un && un.cost_thb)
            slices.push({ name: _t('adm-eng-unattributed'), value: un.cost_thb, muted: true });
        return slices;
    }

    function _drawCharts(rows) {
        const barHost = document.getElementById('adm-eng-chart-bar');
        const pieHost = document.getElementById('adm-eng-chart-pie');
        if (!barHost || !pieHost) return;
        const priced = rows
            .filter(function (r) {
                return r.cost_per_page != null;
            })
            .sort(function (a, b) {
                return b.cost_per_page - a.cost_per_page;
            });
        window.AdminEngineCharts.ensure()
            .then(function () {
                window.AdminEngineCharts.disposeAll();
                window.AdminEngineCharts.renderBar(
                    barHost,
                    priced.slice(0, MAX_BARS).map(function (r) {
                        return {
                            label: _axisLabel(r),
                            tip: _tip(r),
                            cost_per_page: r.cost_per_page,
                        };
                    }),
                    PRICE_THB,
                    {
                        axisName: _t('adm-eng-axis-perpage'),
                        priceLabel: _t('adm-eng-price-line') + ' ' + _baht(PRICE_THB),
                    }
                );
                window.AdminEngineCharts.renderDonut(pieHost, _donutSlices(rows, unattributed), {
                    other: _t('adm-eng-slice-other'),
                });
            })
            .catch(function () {
                const wrap = document.getElementById('adm-eng-charts');
                if (wrap) wrap.innerHTML = _stateBox('error', _t('adm-eng-chart-fail'), 'costs');
            });
    }

    function _noteFor(rows) {
        const skipped = rows.filter(function (r) {
            return r.cost_per_page == null;
        }).length;
        const priced = rows.length - skipped;
        const notes = [];
        if (skipped) notes.push(_t('adm-eng-note-nopages').replace('{n}', skipped));
        if (priced > MAX_BARS) notes.push(_t('adm-eng-note-topn').replace('{n}', String(MAX_BARS)));
        return notes.length
            ? '<div class="eng-chart-note">' + D.esc(notes.join(' · ')) + '</div>'
            : '';
    }

    function _renderData(d) {
        const host = document.getElementById('adm-eng-cost-body');
        const rows = d.rows || [];
        const un = d.unattributed || { calls: 0, cost_thb: 0 };
        unattributed = un;
        if (!rows.length && !un.calls) {
            window.AdminEngineCharts.disposeAll();
            host.innerHTML = _stateBox('empty', _t('adm-eng-cost-empty'), '');
            return;
        }
        host.innerHTML =
            '<div class="eng-charts" id="adm-eng-charts">' +
            '<figure class="eng-chart eng-chart-main"><figcaption>' +
            D.esc(_t('adm-eng-chart-bar-title')) +
            '</figcaption><div class="eng-chart-canvas" id="adm-eng-chart-bar"></div></figure>' +
            '<figure class="eng-chart eng-chart-side"><figcaption>' +
            D.esc(_t('adm-eng-chart-pie-title')) +
            '</figcaption><div class="eng-chart-canvas" id="adm-eng-chart-pie"></div></figure>' +
            '</div>' +
            _noteFor(rows) +
            _table(rows, un) +
            (un.calls
                ? '<div class="eng-chart-note">' + D.esc(_t('adm-eng-unattributed-hint')) + '</div>'
                : '');
        _drawCharts(rows);
    }

    async function load() {
        const host = document.getElementById('adm-eng-cost-body');
        if (!host) return;
        window.AdminEngineCharts.disposeAll();
        host.innerHTML = _stateBox('loading', _t('adm-eng-loading'), '');
        try {
            const d = await D.fetch('/api/admin/ocr-engine/costs?days=' + days);
            _renderData(d || {});
        } catch (e) {
            host.innerHTML = _stateBox('error', _t('adm-eng-cost-fail'), 'costs');
        }
    }

    function _renderDays() {
        const host = document.getElementById('adm-eng-days');
        if (!host) return;
        host.innerHTML = DAY_OPTIONS.map(function (n) {
            return (
                '<button type="button" class="btn btn-sm eng-day' +
                (n === days ? ' is-on' : '') +
                '" data-eng-days="' +
                n +
                '" aria-pressed="' +
                (n === days) +
                '">' +
                D.esc(_t('adm-eng-days-' + n)) +
                '</button>'
            );
        }).join('');
    }

    function _bind() {
        if (bound) return;
        bound = true;
        const root = document.getElementById('page-admin-engine');
        if (!root) return;
        root.addEventListener('click', function (e) {
            const day = e.target.closest('[data-eng-days]');
            if (day) {
                days = Number(day.dataset.engDays);
                _renderDays();
                load();
                return;
            }
            const retry = e.target.closest('[data-eng-retry]');
            if (retry && retry.dataset.engRetry === 'costs') load();
        });
    }

    function render(deps) {
        D = deps;
        _bind();
        _renderDays();
        load();
    }

    window.AdminEngineCost = { render: render };
})();
