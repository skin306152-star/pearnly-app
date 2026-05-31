// ============================================================
// src/home/dms-id-card-results.js · MR.ERP DMS 集成(2026-05-31)
//
// 身份证订车结果块:渲染在 OCR 上传卡下方(不另开页面)。
// 展示:姓名 / 身份证号(遮蔽)/ 地址 / DMS 客户号 / 订车单号 / 状态 / 失败重试。
// 不进普通发票 _results · 由 ocr-recognize.js 的身份证分流调用 window.renderDmsIdCardResult。
//
// 全局桥(bare):t / escapeHtml / showToast。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    function _esc(s) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }

    function _host() {
        var card = (function () {
            var dz = document.getElementById('drop-zone');
            return dz ? dz.closest('.card') : null;
        })();
        if (!card || !card.parentNode) return null;
        var el = document.getElementById('dms-id-card-result');
        if (el) return el;
        el = document.createElement('div');
        el.id = 'dms-id-card-result';
        el.className = 'card';
        el.style.cssText = 'display:none;margin-top:16px;';
        card.parentNode.insertBefore(el, card.nextSibling);
        return el;
    }

    function _row(labelKey, value) {
        return (
            '<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);">' +
            '<span style="color:var(--muted,#6b6b66);font-size:13px;">' +
            _esc(t(labelKey)) +
            '</span>' +
            '<span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">' +
            _esc(value || '—') +
            '</span>' +
            '</div>'
        );
    }

    function _addr(a) {
        if (!a) return '';
        var parts = [a.house_no, a.road, a.subdistrict, a.district, a.province, a.zipcode].filter(
            function (x) {
                return x;
            }
        );
        return parts.join(' ') || a.address_raw || '';
    }

    // status pill + headline message
    function _statusBlock(push) {
        var st = (push && push.status) || 'failed';
        var color, bg, key;
        if (st === 'success') {
            color = '#0a7a2c';
            bg = '#d6f5e0';
            key = 'dms-result-status-success';
        } else if (st === 'needs_review') {
            color = '#9a6b00';
            bg = '#fdf0d0';
            key = 'dms-result-status-needs-review';
        } else if (st === 'skipped') {
            color = '#5d5d57';
            bg = '#eee';
            key = 'dms-result-status-skipped';
        } else {
            color = '#b3261e';
            bg = '#fbe0de';
            key = 'dms-result-status-failed';
        }
        return (
            '<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:' +
            color +
            ';background:' +
            bg +
            ';">' +
            _esc(t(key)) +
            '</span>'
        );
    }

    // Public: render one ID-card → booking result. `data` is the
    // /api/dms/id-card-booking response (or {ok:false, dms_push:{...}} on error).
    window.renderDmsIdCardResult = function (data) {
        var el = _host();
        if (!el) return;
        data = data || {};
        var card = data.id_card || {};
        var addr = card.address || {};
        var push = data.dms_push || {};
        var st = push.status || (data.ok ? 'success' : 'failed');

        var bookingRows = '';
        if (st === 'success') {
            bookingRows =
                _row('dms-result-customer', push.customer_id) +
                _row('dms-result-booking', push.booking_no);
        }

        var retryBtn =
            st === 'failed' || st === 'needs_review'
                ? '<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">' +
                  _esc(t('dms-result-retry')) +
                  '</button>'
                : '';

        // failure reason line (friendly)
        var reasonLine = '';
        if (st === 'failed' && push.error_code) {
            // t() 缺键时回传 key 本身(truthy)· 不能用 `|| code` 兜底 · 否则露 raw key。
            // 显式判等:无对应文案 → 退回通用友好提示(ocr.*/dms.* 等也覆盖)。
            var _ecKey = 'dms-err-' + String(push.error_code).toLowerCase();
            var _ecMsg = t(_ecKey);
            if (!_ecMsg || _ecMsg === _ecKey) _ecMsg = t('dms-err-err_dms_unexpected');
            reasonLine =
                '<div style="margin-top:8px;color:#b3261e;font-size:12px;">' +
                _esc(_ecMsg) +
                '</div>';
        }

        el.style.display = '';
        el.innerHTML =
            '<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;">' +
            '<div class="section-title">' +
            _esc(t('dms-result-title')) +
            '</div>' +
            _statusBlock(push) +
            '</div>' +
            '<div style="margin-top:8px;">' +
            _row('dms-result-name', (card.first_name || '') + ' ' + (card.last_name || '')) +
            _row('dms-result-id', card.people_id_masked) +
            _row('dms-result-birthday', card.birthday_be) +
            _row('dms-result-address', _addr(addr)) +
            bookingRows +
            '</div>' +
            reasonLine +
            retryBtn;
    };

    window.clearDmsIdCardResult = function () {
        var el = document.getElementById('dms-id-card-result');
        if (el) {
            el.style.display = 'none';
            el.innerHTML = '';
        }
    };

    document.addEventListener('click', function (ev) {
        if (ev.target.closest('#dms-id-card-retry')) {
            ev.preventDefault();
            if (typeof window._dmsRetryIdCard === 'function') window._dmsRetryIdCard();
        }
    });
})();
