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
// F5 (2026-07-10) · 单别人工可选:doctype 单元格从只读改「自动/HP/RR」select + 保存。
// P3c (2026-07-10) · 单别裁决控件收口进共用组件 posting-editor.ts(window.PostingEditor)·
// 同一控件加了第二轴「货/费」(item_type)后 Express 卡与 MR.ERP 详情共用,不再各写一份
// select + 保存 + 徽标逻辑。本文件只负责算「初值该不该回填」这条业务判断(Express 专属)。
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

    // 单别/货费改判单元格:文案 + 徽标 + 共用组件 posting-editor.ts 的两轴 select + 保存按钮。
    // 现/赊 select 初值:仅当 doctype_src === 'manual' 才按 payload.doctype 选中对应项,否则
    // 「自动」——系统推定态(explicit/doc_type/profile/bank/config_default)不当成人工选择
    // 回填,避免误导「已经手动定过」。货/费 select 初值同理:仅 item_src === 'manual' 且
    // doc_lane 有值才回填对应项。两轴判据各自独立,互不影响对方的初值。
    function _doctypeCell(p: any, historyId: any): string {
        var isDoctype = p.doctype === 'HP' || p.doctype === 'RR';
        var isDocLane = p.doc_lane === 'goods' || p.doc_lane === 'expense';
        var docManual = p.doctype_src === 'manual' && isDoctype;
        var itemManual = p.item_src === 'manual' && isDocLane;
        return (window as any).PostingEditor.cell(historyId, {
            doctype: isDoctype ? p.doctype : null,
            doctypeSrc: p.doctype_src,
            doctypeSelVal: docManual ? p.doctype : 'auto',
            itemType: isDocLane ? p.doc_lane : null,
            itemSrc: p.item_src,
            itemSelVal: itemManual ? p.doc_lane : 'auto',
        });
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

    // 保存 + 委派 + 徽标渲染已收口进共用组件(posting-editor.ts · window.PostingEditor)·
    // 本文件只在 _doctypeCell 里算好两轴初值传过去,不再重复一份 fetch/委派逻辑。

    (window as any).ExpressDetail = { section: section };
})();
