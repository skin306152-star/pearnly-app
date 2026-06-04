// ============================================================
// src/home/ocr-document-mode.js · MR.ERP DMS 集成(2026-05-31)
//
// 在 OCR 上传卡注入轻量模式切换:发票 / 身份证订车。
// - 默认 invoice · 现有发票 OCR 路径完全不变。
// - 仅当存在【启用的 mrerp_dms endpoint】时才显示「身份证订车」段。
// - 用户选过身份证订车后记 localStorage · 重复用户保留上次选择。
// - 暴露 window.getOcrDocumentMode() → 'invoice' | 'thai_id_card'(供 ocr-recognize 分流)。
//
// 全局桥(bare):t / showToast。token 经 localStorage。i18n 经 window.subscribeI18n。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    var LS_KEY = 'pearnly_ocr_doc_mode';
    var _hasDms = false;
    var _dmsLoaded = false;

    function _esc(s: unknown) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }

    function _savedMode() {
        try {
            return localStorage.getItem(LS_KEY) === 'thai_id_card' ? 'thai_id_card' : 'invoice';
        } catch (e) {
            return 'invoice';
        }
    }

    // Public: current OCR document mode. Forced back to invoice when no DMS
    // endpoint is connected (so a stale localStorage can't route to DMS).
    window.getOcrDocumentMode = function () {
        if (!_hasDms) return 'invoice';
        return _savedMode();
    };

    function _uploadCard() {
        var dz = document.getElementById('drop-zone');
        return dz ? dz.closest('.card') : null;
    }

    function _ensureControl() {
        var card = _uploadCard();
        if (!card) return null;
        var el = card.querySelector('#ocr-doc-mode');
        if (el) return el;
        var head = card.querySelector('.section-head');
        el = document.createElement('div');
        el.id = 'ocr-doc-mode';
        el.className = 'ocr-doc-mode';
        el.setAttribute('role', 'tablist');
        (el as HTMLElement).style.cssText =
            'display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;' +
            'background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;';
        if (head && head.parentNode) {
            head.parentNode.insertBefore(el, head.nextSibling);
        } else {
            card.insertBefore(el, card.firstChild);
        }
        return el;
    }

    function _segBtn(mode: string, labelKey: string, active: boolean) {
        return (
            '<button type="button" class="ocr-doc-seg' +
            (active ? ' active' : '') +
            '" data-doc-mode="' +
            mode +
            '" role="tab" aria-selected="' +
            (active ? 'true' : 'false') +
            '" style="' +
            'border:none;background:' +
            (active ? 'var(--card,#fff)' : 'transparent') +
            ';color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:' +
            (active ? '600' : '500') +
            ';padding:6px 16px;border-radius:7px;cursor:pointer;' +
            'box-shadow:' +
            (active ? '0 1px 3px rgba(0,0,0,.08)' : 'none') +
            ';transition:background .15s;">' +
            _esc(t(labelKey)) +
            '</button>'
        );
    }

    function _render() {
        var el = _ensureControl();
        if (!el) return;
        // No DMS endpoint → keep the control hidden, mode stays invoice.
        if (!_hasDms) {
            (el as HTMLElement).style.display = 'none';
            return;
        }
        var mode = _savedMode();
        (el as HTMLElement).style.display = 'flex';
        el.innerHTML =
            _segBtn('invoice', 'ocr-mode-invoice', mode === 'invoice') +
            _segBtn('thai_id_card', 'ocr-mode-id-card', mode === 'thai_id_card');
    }

    function _setMode(mode: string) {
        try {
            localStorage.setItem(LS_KEY, mode === 'thai_id_card' ? 'thai_id_card' : 'invoice');
        } catch (e) {}
        _render();
        // Let other modules (dms-id-card-results) react to the switch.
        try {
            document.dispatchEvent(
                new CustomEvent('ocr-doc-mode-change', {
                    detail: { mode: window.getOcrDocumentMode!() },
                })
            );
        } catch (e) {}
    }

    async function _loadDmsEndpoints(force: boolean) {
        if (_dmsLoaded && !force) return;
        var tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        try {
            var r = await fetch('/api/erp/endpoints', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) return;
            var data = await r.json();
            var items = (data && data.items) || [];
            _hasDms = items.some(function (ep: { adapter?: string; enabled?: boolean }) {
                return (
                    ep && (ep.adapter || '').toLowerCase() === 'mrerp_dms' && ep.enabled !== false
                );
            });
            _dmsLoaded = true;
            // cache for ocr-recognize endpoint resolution / refresh hooks
            window._dmsHasEndpoint = _hasDms;
            _render();
        } catch (e) {
            /* silent · 拉取失败保持发票模式 */
        }
    }

    // Let the connect wizard force a refresh after saving a DMS endpoint.
    window._refreshOcrDocMode = function () {
        _loadDmsEndpoints(true);
    };

    document.addEventListener('click', function (ev) {
        var seg = (ev.target as HTMLElement).closest('.ocr-doc-seg');
        if (seg && seg.getAttribute('data-doc-mode')) {
            ev.preventDefault();
            _setMode(seg.getAttribute('data-doc-mode')!);
        }
    });

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('ocr-doc-mode', _render);
    }

    // Inject the control as soon as the upload card exists, then load DMS state.
    function _boot() {
        _ensureControl();
        _render();
        _loadDmsEndpoints(false);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _boot);
    } else {
        _boot();
    }
    // Re-check DMS endpoints when the user navigates to the OCR page.
    window.addEventListener('hashchange', function () {
        if (
            (location.hash || '').indexOf('ocr') >= 0 ||
            location.hash === '' ||
            location.hash === '#home'
        ) {
            setTimeout(function () {
                _ensureControl();
                _loadDmsEndpoints(false);
            }, 60);
        }
    });
})();
