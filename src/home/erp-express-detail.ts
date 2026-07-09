// ============================================================
// src/home/erp-express-detail.js · Express 分录预览(信任关键屏 · P3b)
//
// 挂进现有「推送详情抽屉」(erp-log-detail)的 adapter=='express' 分支 · 渲染:
//   ① 识别字段(供应商/税号/票号/单别/佛历日期/税前·VAT·含税)
//   ② 将记入 Express 的复式分录卡(借采购/借进项税 ภาษีซื้อ = 贷应付 เจ้าหนี้)· 借贷不平显红警
//   ③ 已推送显 Express 单号 + 诚实状态时间线(识别→已入队→待推送/已推送/失败,不伪造)
// 数据全取 log.request_body(mapper 载荷)+ log.response_body(express_docnum)· 纯渲染无请求。
// 复用抽屉的 .erp-detail-sec / .erp-tl-row 视觉系统 · 新增只 .exp-je* 分录卡(令牌)。
// 暴露 (window).ExpressDetail.section(log) · 全局桥:t / escapeHtml / token。
//
// F5 (2026-07-10) · 单别人工可选:doctype 单元格从只读改「自动/HP/RR」select + 保存,
// 保存走 PATCH /api/history/{id}/posting(payment: cash|credit|null)。事件绑定不借宿主
// erp-log-detail 的 [data-receipt-action] 委派(那条链路末尾无条件 closeAll,会把抽屉关掉)·
// 改用模块自己的 document 级委派(drawer 每次重开都是新 DOM · 元素级绑定会失效)。
// 来源徽标读 request_body.doctype_src,复用 .log-tag 既有视觉(manual/auto 两色)。
// ============================================================
/* global escapeHtml, token */
(function () {
    'use strict';

    function _esc(s: any) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function _t(k: string, vars?: any) {
        try {
            var v = typeof t === 'function' ? t(k, vars) : k;
            return v || k;
        } catch (e) {
            return k;
        }
    }
    function _num(v: any): number {
        var n = parseFloat(String(v == null ? '' : v).replace(/,/g, ''));
        return isNaN(n) ? 0 : n;
    }
    function _amt(v: any): string {
        return _num(v).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }
    function _parseJson(v: any): any {
        // request_body / response_body 可能是 jsonb 对象或 JSON 字符串 · 统一解析,失败回 {}。
        if (!v) return {};
        if (typeof v === 'object') return v;
        try {
            return JSON.parse(v) || {};
        } catch (e) {
            return {};
        }
    }
    function _beDate(be: any): string {
        // 佛历 YYMMDD(末两位年)→ DD/MM/25YY 展示;非 6 位原样返回。
        var s = String(be || '');
        if (!/^\d{6}$/.test(s)) return s || '-';
        return s.slice(4, 6) + '/' + s.slice(2, 4) + '/25' + s.slice(0, 2);
    }

    function _sec(title: string, inner: string): string {
        return (
            '<section class="erp-detail-sec"><h3>' + _esc(title) + '</h3>' + inner + '</section>'
        );
    }
    function _cell(label: string, val: string): string {
        return (
            '<div class="erp-detail-cell"><label>' +
            _esc(label) +
            '</label><strong>' +
            _esc(val) +
            '</strong></div>'
        );
    }
    function _tl(cls: string, dot: string, title: string, sub: string): string {
        return (
            '<div class="erp-tl-row ' +
            cls +
            '"><div class="erp-tl-dot">' +
            dot +
            '</div><div class="erp-tl-copy"><b>' +
            _esc(title) +
            '</b><span>' +
            _esc(sub) +
            '</span></div></div>'
        );
    }

    // 来源徽标(doctype_src)· 复用 .log-tag 既有两色令牌:manual(人工)醒目 · 其余系统推定态柔和。
    // 值域外(未识别的 src)不显示 —— 不伪造徽标。
    var SRC_KEYS: Record<string, string> = {
        manual: 'expd-src-manual',
        explicit: 'expd-src-explicit',
        doc_type: 'expd-src-doc_type',
        profile: 'expd-src-profile',
        bank: 'expd-src-bank',
        config_default: 'expd-src-config_default',
    };
    function _srcBadge(src: any): string {
        var key = SRC_KEYS[String(src || '')];
        if (!key) return '';
        var cls = src === 'manual' ? 'manual' : 'auto';
        return '<span class="log-tag ' + cls + ' exp-doctype-src">' + _esc(_t(key)) + '</span>';
    }

    // 单别单元格:文案 + 三项 select(自动/HP/RR)+ 保存按钮。
    // select 初值:仅当 doctype_src === 'manual' 才按 payload.doctype 选中对应项,否则「自动」——
    // 系统推定态(explicit/doc_type/profile/bank/config_default)不当成人工选择回填,避免
    // 误导「已经手动定过」。无 history_id 时(理论不该发生 · 兜底)退回纯只读文案,不渲染控件。
    function _doctypeCell(p: any, historyId: any): string {
        var doctype = p.doctype === 'HP' ? _t('expd-doctype-hp') : _t('expd-doctype-rr');
        var isManual = p.doctype_src === 'manual' && (p.doctype === 'HP' || p.doctype === 'RR');
        var selVal = isManual ? p.doctype : 'auto';
        var opts = [
            ['auto', _t('expd-doctype-auto')],
            ['HP', _t('expd-doctype-hp')],
            ['RR', _t('expd-doctype-rr')],
        ]
            .map(function (o) {
                return (
                    '<option value="' +
                    o[0] +
                    '"' +
                    (o[0] === selVal ? ' selected' : '') +
                    '>' +
                    _esc(o[1]) +
                    '</option>'
                );
            })
            .join('');
        var editor = historyId
            ? '<div class="exp-doctype-edit">' +
              '<select class="exp-doctype-select">' +
              opts +
              '</select>' +
              '<button type="button" class="btn btn-ghost btn-tiny exp-doctype-save" data-history-id="' +
              _esc(String(historyId)) +
              '">' +
              _esc(_t('expd-doctype-save')) +
              '</button>' +
              '<span class="exp-doctype-msg"></span>' +
              '</div>'
            : '';
        return (
            '<div class="erp-detail-cell exp-doctype-cell"><label>' +
            _esc(_t('expd-f-doctype')) +
            '</label><strong>' +
            _esc(doctype) +
            _srcBadge(p.doctype_src) +
            '</strong>' +
            editor +
            '</div>'
        );
    }

    function _fields(p: any, historyId: any): string {
        var sup = p.supplier || {};
        var code = sup.code || (sup.supplier_new ? _t('expd-supplier-new') : '-');
        var grid =
            _cell(_t('expd-f-supplier'), sup.name || '-') +
            _cell(_t('expd-f-taxid'), sup.tax_id || '-') +
            _cell(_t('expd-f-code'), code) +
            _cell(_t('expd-f-refno'), p.ref_no || '-') +
            _doctypeCell(p, historyId) +
            _cell(_t('expd-f-date'), _beDate(p.docdate_be)) +
            _cell(_t('expd-f-vatrate'), (p.vat_rate != null ? p.vat_rate : '-') + '%') +
            _cell(_t('expd-f-base'), _amt(p.base_amount)) +
            _cell(_t('expd-f-vat'), _amt(p.vat_amount)) +
            _cell(_t('expd-f-total'), _amt(p.total_amount));
        return _sec(_t('expd-sec-fields'), '<div class="erp-detail-grid">' + grid + '</div>');
    }

    function _entry(p: any): string {
        var lines = p.lines || [];
        var dr = 0,
            cr = 0;
        var rows = lines
            .map(function (ln: any) {
                var isDr = ln.side === 'D';
                if (isDr) dr += _num(ln.amount);
                else cr += _num(ln.amount);
                return (
                    '<div class="exp-je-row"><span class="exp-je-side ' +
                    (isDr ? 'dr' : 'cr') +
                    '">' +
                    _esc(isDr ? _t('expd-dr') : _t('expd-cr')) +
                    '</span><span class="exp-je-acc">' +
                    _esc(ln.acc || '') +
                    '</span><span class="exp-je-desc">' +
                    _esc(ln.desc || '') +
                    '</span><span class="exp-je-amt">' +
                    _amt(ln.amount) +
                    '</span></div>'
                );
            })
            .join('');
        var balanced = Math.abs(dr - cr) < 0.01;
        var totalRow =
            '<div class="exp-je-row exp-je-total"><span class="exp-je-side"></span>' +
            '<span class="exp-je-desc">' +
            _esc(_t('expd-total-dr')) +
            ' / ' +
            _esc(_t('expd-total-cr')) +
            '</span><span class="exp-je-amt">' +
            _amt(dr) +
            ' / ' +
            _amt(cr) +
            '</span></div>';
        var badge =
            '<div class="exp-je-bal ' +
            (balanced ? 'ok' : 'bad') +
            '">' +
            _esc(balanced ? _t('expd-balanced') : _t('expd-unbalanced')) +
            '</div>';
        var warn = balanced
            ? ''
            : '<div class="exp-je-warn">' + _esc(_t('expd-unbalanced')) + '</div>';
        // 变动科目落账套默认(account_review)→ 柔和待核提示,提醒人核一眼(诚实状态)。
        var review = p.account_review
            ? '<div class="exp-je-note">' + _esc(_t('expd-acct-review')) + '</div>'
            : '';
        return _sec(
            _t('expd-sec-entry'),
            '<div class="exp-je">' + rows + totalRow + badge + '</div>' + review + warn
        );
    }

    function _timeline(log: any, docnum: string): string {
        var st = log.status || 'pending';
        var time = log.created_at ? new Date(log.created_at).toLocaleString() : '';
        var rows = [_tl('ok', '✓', _t('expd-tl-recognized'), time)];
        rows.push(_tl('ok', '✓', _t('expd-tl-queued'), _t('expd-tl-queued-sub')));
        if (st === 'success') rows.push(_tl('ok', '✓', _t('expd-tl-pushed'), docnum || ''));
        else if (st === 'failed')
            rows.push(_tl('fail', '✗', _t('expd-tl-failed'), 'HTTP ' + (log.http_status || '—')));
        else if (st === 'manual')
            rows.push(_tl('mid', '●', _t('expd-tl-manual'), _t('expd-tl-manual-sub')));
        else if (st === 'skipped_dup') rows.push(_tl('ok', '✓', _t('expd-tl-dup'), ''));
        else rows.push(_tl('mid', '●', _t('expd-tl-pending'), _t('expd-tl-pending-sub')));
        return _sec(
            _t('erp-detail-sec-timeline'),
            '<div class="erp-detail-timeline">' + rows.join('') + '</div>'
        );
    }

    function _preflightWhy(reason: string): string {
        if (reason === 'subject_unbound' || reason === 'ambiguous') {
            return _t('erp-preflight-reason-' + reason);
        }
        var fr = (window as any)._expressFriendlyReason;
        return (fr && fr(reason)) || '';
    }

    function _preflight(resp: any): string {
        var pf = resp && resp.preflight;
        if (!pf || !pf.length) return '';
        var rows = '';
        for (var i = 0; i < pf.length; i++) {
            var c = pf[i];
            var ok = c.status === 'ok';
            var bad = c.status === 'blocked';
            var cls = ok ? 'ok' : bad ? 'fail' : 'mid';
            var dot = ok ? '✓' : bad ? '✗' : '◦';
            var why = bad ? _preflightWhy(c.reason || '') : '';
            rows += _tl(cls, dot, _t('erp-preflight-key-' + c.key), why);
        }
        return _sec(
            _t('erp-preflight-title'),
            '<div class="erp-detail-timeline">' + rows + '</div>'
        );
    }

    function section(log: any): string {
        var p = _parseJson(log && log.request_body);
        var resp = _parseJson(log && log.response_body);
        var docnum = resp.express_docnum || '';
        var historyId = log && log.history_id;

        // 空态:无分录载荷(待人工复核 / 未过闸门)。
        if (!p.lines || !p.lines.length) {
            return (
                _preflight(resp) +
                _sec(
                    _t('expd-sec-entry'),
                    '<div class="exp-je-empty">' + _esc(_t('expd-empty')) + '</div>'
                ) +
                _timeline(log, docnum)
            );
        }

        var docSec =
            log.status === 'success' && docnum
                ? _sec(
                      _t('erp-receipt-doc-no'),
                      '<div class="erp-detail-docno"><strong>' +
                          _esc(docnum) +
                          '</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="' +
                          _esc(docnum) +
                          '">' +
                          _esc(_t('erp-receipt-copy-btn')) +
                          '</button></div>'
                  )
                : '';
        return (
            _fields(p, historyId) + _preflight(resp) + _entry(p) + docSec + _timeline(log, docnum)
        );
    }

    // 保存单别裁决 → PATCH /api/history/{id}/posting({payment: cash|credit|null})。
    // 三态文案(保存中/已保存/失败)就地更新触发按钮同格的 .exp-doctype-msg,不重渲整个抽屉——
    // 详情数据(log.request_body)留在闭包外,重渲要靠人手动重新打开详情,状态诚实不假装同步。
    async function _saveDoctype(btn: HTMLElement): Promise<void> {
        var cell = btn.closest('.exp-doctype-cell');
        var sel = cell
            ? (cell.querySelector('.exp-doctype-select') as HTMLSelectElement | null)
            : null;
        var msg = cell ? (cell.querySelector('.exp-doctype-msg') as HTMLElement | null) : null;
        var historyId = btn.getAttribute('data-history-id');
        if (!sel || !historyId) return;
        var val = sel.value;
        var payment = val === 'HP' ? 'cash' : val === 'RR' ? 'credit' : null;
        (btn as HTMLButtonElement).disabled = true;
        sel.disabled = true;
        if (msg) {
            msg.textContent = _t('expd-doctype-saving');
            msg.className = 'exp-doctype-msg mid';
        }
        try {
            var resp = await fetch('/api/history/' + encodeURIComponent(historyId) + '/posting', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: 'Bearer ' + token,
                },
                body: JSON.stringify({ payment: payment }),
            });
            var j: any = {};
            try {
                j = await resp.json();
            } catch (e) {
                /* 空体也可能是成功(理论不会 · 兜底不炸) */
            }
            if (!resp.ok || !j.ok) throw new Error('save failed');
            if (msg) {
                msg.textContent = _t('expd-doctype-saved');
                msg.className = 'exp-doctype-msg ok';
            }
        } catch (e) {
            if (msg) {
                msg.textContent = _t('expd-doctype-save-fail');
                msg.className = 'exp-doctype-msg fail';
            }
        } finally {
            (btn as HTMLButtonElement).disabled = false;
            sel.disabled = false;
        }
    }

    // document 级委派(一次性绑定)· 抽屉每次 showLogDetail() 都是新 DOM,元素级监听会失效;
    // 不借宿主 erp-log-detail 的 [data-receipt-action] 链路——那条链路末尾无条件 closeAll()。
    var _bound = false;
    function _bindOnce(): void {
        if (_bound) return;
        _bound = true;
        document.addEventListener('click', function (e: Event) {
            var tgt = e.target as HTMLElement;
            var btn = tgt.closest && (tgt.closest('.exp-doctype-save') as HTMLElement | null);
            if (!btn) return;
            _saveDoctype(btn);
        });
    }
    _bindOnce();

    (window as any).ExpressDetail = { section: section };
})();
