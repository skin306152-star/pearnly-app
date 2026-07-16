/* Pearnly DMS · 身份证向导 · 上下文 ERP 连接卡(MR.ERP DMS)。
 * 移植自主站 src/home/dms-intake-erp-cards.ts 的 identity 分支(独立壳只此一张卡)。
 * 卡片显示连接状态 + 启用/停用开关;点「配置」经 window._mrerpDmsOpenWizard 开向导
 * (dms-connect.js 提供)。启停是「同批不误投」闸:停用 → 后端按 enabled=TRUE 过滤。挂 window.DXERP。 */
(function (root) {
    'use strict';
    var esc = root.DXST.esc;
    var authHeaders = root.DXST.authHeaders;

    var DEF = { key: 'mrerp_dms', name: 'MR.ERP DMS', adapter: 'mrerp_dms' };
    var ICON =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="22" height="22"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2.1"/><path d="M6 16c.7-1.4 1.9-2.1 3-2.1s2.3.7 3 2.1M14 10h4M14 14h4"/></svg>';

    function T(k) {
        return typeof root.t === 'function' ? root.t(k) : k;
    }
    function isEnabled(ep) {
        return !!ep && ep.enabled !== false;
    }
    // DMS 的自动标志在 config.id_card_auto_push(adapter=mrerp_dms 的 auto_push 后端强制 false)。
    function isAutoPush(ep) {
        return (ep.config || {}).id_card_auto_push === true;
    }

    function cardHtml() {
        return (
            '<div class="dx-erp-card" data-erp="' +
            esc(DEF.adapter) +
            '"><div class="dx-erp-ic">' +
            ICON +
            '</div><div class="dx-erp-info"><b>' +
            esc(DEF.name) +
            '</b><span class="dx-erp-status" data-erp-status>' +
            esc(T('dx-erp-checking')) +
            '</span></div><div class="dx-erp-acts" data-erp-acts></div></div>'
        );
    }

    function fillCard(card, ep) {
        card._ep = ep;
        var st = card.querySelector('[data-erp-status]');
        var acts = card.querySelector('[data-erp-acts]');
        var enabled = isEnabled(ep);
        card.classList.toggle('is-connected', !!ep && enabled);
        card.classList.toggle('is-disabled', !!ep && !enabled);
        if (st) {
            if (!ep) st.textContent = T('dx-erp-not-connected');
            else if (!enabled) st.textContent = T('dx-erp-disabled');
            else
                st.textContent =
                    T('dx-erp-connected') +
                    ' · ' +
                    T(isAutoPush(ep) ? 'dx-erp-mode-auto' : 'dx-erp-mode-manual');
        }
        if (!acts) return;
        if (!ep) {
            acts.innerHTML =
                '<button type="button" class="dx-erp-cta" data-erp-config>' +
                esc(T('dx-erp-connect')) +
                '</button>';
            return;
        }
        acts.innerHTML =
            '<button type="button" class="dx-erp-toggle" data-erp-toggle>' +
            esc(T(enabled ? 'dx-erp-disable' : 'dx-erp-enable')) +
            '</button><button type="button" class="dx-erp-cta" data-erp-config>' +
            esc(T('dx-erp-config')) +
            '</button>';
    }

    function toggleEndpoint(card) {
        var ep = card._ep || null;
        if (!ep || !ep.id) return Promise.resolve();
        var enabling = !isEnabled(ep);
        var pre =
            !enabling && typeof root.pearnlyConfirm === 'function'
                ? root.pearnlyConfirm(T('dx-erp-confirm-disable'))
                : Promise.resolve(true);
        return pre.then(function (ok) {
            if (!ok) return;
            return fetch('/api/erp/endpoints/' + encodeURIComponent(ep.id), {
                method: 'PATCH',
                headers: authHeaders(true),
                body: JSON.stringify({ enabled: enabling }),
            })
                .then(function (r) {
                    if (!r.ok) throw new Error('http_' + r.status);
                    fillCard(card, Object.assign({}, ep, { enabled: enabling }));
                })
                .catch(function () {
                    /* 网络/权限失败:保持原状,不误显启停成功 */
                });
        });
    }

    function bindClicks(zone) {
        zone.addEventListener('click', function (e) {
            var target = e.target;
            var card = target.closest('.dx-erp-card');
            if (!card) return;
            if (target.closest('[data-erp-toggle]')) {
                e.preventDefault();
                void toggleEndpoint(card);
                return;
            }
            if (target.closest('[data-erp-config]')) {
                e.preventDefault();
                if (typeof root._mrerpDmsOpenWizard === 'function')
                    root._mrerpDmsOpenWizard(card._ep, function () {
                        loadStatus(zone);
                    });
            }
        });
    }

    function loadStatus(zone) {
        return fetch('/api/erp/endpoints', { headers: authHeaders() })
            .then(function (r) {
                return r.ok ? r.json() : { items: [] };
            })
            .then(function (data) {
                var items = (data && data.items) || [];
                var card = zone.querySelector('[data-erp="' + DEF.adapter + '"]');
                if (!card) return;
                var ep =
                    items.find(function (e) {
                        return String(e.adapter || '').toLowerCase() === DEF.adapter;
                    }) || null;
                fillCard(card, ep);
            })
            .catch(function () {
                var card = zone.querySelector('[data-erp="' + DEF.adapter + '"]');
                if (card) fillCard(card, null);
            });
    }

    function renderCards() {
        var zone = document.getElementById('dx-erp-cards');
        if (!zone) return;
        zone.innerHTML =
            '<div class="dx-erp-h">' +
            esc(T('dx-erp-h')) +
            '</div><div class="dx-erp-row">' +
            cardHtml() +
            '</div>';
        bindClicks(zone);
        void loadStatus(zone);
    }

    root.DXERP = { renderCards: renderCards };
})(typeof self !== 'undefined' ? self : this);
