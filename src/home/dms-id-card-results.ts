// ============================================================
// DMS 身份证 → 可编辑面板(2026-06-13 · 取代旧只读结果块)
//
// 两步流第 2 屏:openDmsIdCardPanel(recognize 响应)渲染可编辑面板
//   → 用户核对/编辑(覆盖现有 / 另建新客户)+ 四级联动地址 + 订车单
//   → 推送 POST /api/dms/id-card/push → 成功态(客户号 + 订车单号)。
// 手机端 CSS(home-47)做底部全屏 sheet。全局桥:t / escapeHtml / showToast / token。
// ============================================================
/* global escapeHtml, token */
(function () {
    'use strict';

    const S: { mode: string; customerId: string | null } = { mode: 'create', customerId: null };

    function esc(s: unknown) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function lang() {
        return window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
    }
    function $(id: string) {
        return document.getElementById(id) as HTMLInputElement | HTMLSelectElement | null;
    }

    function host(): HTMLElement | null {
        const dz = document.getElementById('drop-zone');
        const card = dz ? (dz.closest('.panel') as HTMLElement | null) : null;
        if (!card || !card.parentNode) return null;
        let el = document.getElementById('dms-id-card-result');
        if (el) return el;
        el = document.createElement('div');
        el.id = 'dms-id-card-result';
        (el as HTMLElement).style.marginTop = '16px';
        card.parentNode.insertBefore(el, card.nextSibling);
        return el;
    }

    type Pair = [string, string];
    function pairOpts(pairs: Pair[], selId: unknown) {
        return (pairs || [])
            .map(
                (p) =>
                    `<option value="${esc(p[0])}"${String(p[0]) === String(selId) ? ' selected' : ''}>${esc(p[1])}</option>`
            )
            .join('');
    }
    function masterOpts(arr: Array<{ id: string; name?: string; code?: string }>) {
        return (arr || [])
            .map((m) => `<option value="${esc(m.id)}">${esc(m.name || m.code || m.id)}</option>`)
            .join('');
    }
    function field(label: string, id: string, val: unknown, req: boolean, ocr: boolean) {
        return (
            `<div class="dic-f"><label>${esc(t(label))}${req ? ' <span class="rq">*</span>' : ''}</label>` +
            `<input id="${id}" class="${ocr ? 'ocr' : ''}" value="${esc(val || '')}"></div>`
        );
    }
    function sel(label: string, id: string, opts: string, req: boolean, onchange: string) {
        return (
            `<div class="dic-f"><label>${esc(t(label))}${req ? ' <span class="rq">*</span>' : ''}</label>` +
            `<select id="${id}"${onchange ? ` data-geo="${onchange}"` : ''}>${opts}</select></div>`
        );
    }

    // recognize 响应 → 渲染可编辑面板
    window.openDmsIdCardPanel = function (data) {
        const el = host();
        if (!el) return;
        data = data || {};
        const ic = (data.id_card || {}) as Record<string, unknown>;
        const addr = (ic.address || {}) as Record<string, unknown>;
        const dms = (data.dms || {}) as Record<string, unknown>;
        if (!dms.ok) {
            const fr = (dms.error_friendly || {}) as Record<string, string>;
            showToast(fr[lang()] || fr.en || t('dic-dms-unreachable'), 'error');
            return;
        }
        const match = (dms.match || {}) as Record<string, unknown>;
        const geo = (dms.geo || {}) as Record<string, unknown>;
        const gsel = (geo.selected || {}) as Record<string, string>;
        const prefixes = (dms.prefixes || []) as Pair[];
        const masters = (dms.masters || {}) as Record<string, Array<{ id: string; name?: string }>>;

        S.mode = match.found ? 'overwrite' : 'create';
        S.customerId = match.found ? (match.customer_id as string) : null;
        const prefId = (prefixes.find((p) => p[1] === ic.prefix_name) || prefixes[0] || [''])[0];

        const banner = match.found
            ? bannerExist(match.current_fields as Record<string, unknown>, match.customer_id)
            : `<div class="dic-banner newc"><span class="dic-bt">${esc(t('dic-banner-new'))}</span></div>`;

        el.innerHTML =
            '<div class="dic-sheet"><div class="dic-head">' +
            `<span class="dic-ttl">${esc(t('dic-title'))}</span>` +
            `<span class="dic-badge">${esc(t('dic-ocr-badge'))}</span>` +
            `<button class="dic-x" id="dic-x">×</button></div>` +
            '<div class="dic-body">' +
            banner +
            // 客户资料
            `<div><div class="dic-sec-t">${esc(t('dic-sec-cust'))}</div><div class="dic-grid">` +
            sel('dic-l-prefix', 'dic-prefix', pairOpts(prefixes, prefId), true, '') +
            field('dic-l-name', 'dic-name', ic.name, true, true) +
            field('dic-l-pid', 'dic-pid', ic.people_id, true, true) +
            taxField(ic.people_id) +
            field('dic-l-bd', 'dic-bd', ic.birthday_be, false, true) +
            field('dic-l-tel', 'dic-tel', '', false, false) +
            '</div></div>' +
            // 户籍地址(四级联动)
            `<div><div class="dic-sec-t">${esc(t('dic-sec-addr'))}</div><div class="dic-grid">` +
            field('dic-l-house', 'dic-house', addr.house_no, false, true) +
            field('dic-l-moo', 'dic-moo', addr.moo, false, true) +
            field('dic-l-soi', 'dic-soi', addr.soi, false, false) +
            field('dic-l-road', 'dic-road', addr.road, false, false) +
            '</div><div class="dic-grid addr" style="margin-top:12px">' +
            sel(
                'dic-l-prov',
                'dic-prov',
                pairOpts(geo.provinces as Pair[], gsel.province_id),
                true,
                'prov'
            ) +
            sel(
                'dic-l-dist',
                'dic-dist',
                pairOpts(geo.districts as Pair[], gsel.district_id),
                true,
                'dist'
            ) +
            sel(
                'dic-l-sub',
                'dic-sub',
                pairOpts(geo.subdistricts as Pair[], gsel.subdistrict_id),
                true,
                'sub'
            ) +
            sel(
                'dic-l-zip',
                'dic-zip',
                pairOpts(geo.zipcodes as Pair[], gsel.zipcode_id),
                false,
                ''
            ) +
            '</div></div>' +
            // 订车单
            `<div><div class="dic-sec-t">${esc(t('dic-sec-book'))}</div><div class="dic-grid">` +
            sel('dic-l-advisor', 'dic-advisor', masterOpts(masters.advisors), true, '') +
            sel('dic-l-car', 'dic-car', masterOpts(masters.car_models), true, '') +
            sel('dic-l-place', 'dic-place', masterOpts(masters.place_books), false, '') +
            sel('dic-l-term', 'dic-term', masterOpts(masters.term_sales), false, '') +
            sel('dic-l-branch', 'dic-branch', masterOpts(masters.branches), false, '') +
            '</div></div>' +
            '</div>' + // body
            '<div class="dic-foot">' +
            `<span class="note">${esc(t('dic-foot-note'))}</span><span class="sp"></span>` +
            `<button class="btn btn-ghost" id="dic-cancel">${esc(t('dic-cancel'))}</button>` +
            `<button class="btn btn-primary" id="dic-push">${esc(t('dic-push'))}</button>` +
            '</div></div>';

        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    function bannerExist(cur: Record<string, unknown>, cid: unknown) {
        cur = cur || {};
        const r = (k: string, v: unknown) =>
            `<div class="r"><span class="k">${esc(t(k))}</span><span class="v">${esc(v || '—')}</span></div>`;
        return (
            '<div class="dic-banner exist">' +
            `<span class="dic-bt">${esc(t('dic-banner-exist'))} #${esc(cid)}</span>` +
            '<div class="dic-choice">' +
            `<label class="on" id="dic-ch-over"><input type="radio" name="dic-mode" checked> ${esc(t('dic-over'))}</label>` +
            `<label id="dic-ch-new"><input type="radio" name="dic-mode"> ${esc(t('dic-new'))}</label></div>` +
            `<details class="dic-hist"><summary>${esc(t('dic-hist'))}</summary><div class="g">` +
            r('dic-h-name', cur.name) +
            r('dic-h-phone', cur.phone) +
            r('dic-h-pid', cur.people_id) +
            r('dic-h-credit', cur.credit_day) +
            '</div></details></div>'
        );
    }

    function taxField(pid: unknown) {
        return (
            `<div class="dic-f"><label>${esc(t('dic-l-tax'))}</label>` +
            `<input id="dic-tax" value="${esc(pid || '')}" readonly>` +
            `<div class="dic-sw"><button class="dic-toggle on" id="dic-tax-sw"><span class="knob"></span></button>` +
            `<span>${esc(t('dic-tax-same'))}</span></div></div>`
        );
    }

    async function loadGeo(
        level: string,
        parent: string,
        selId: string,
        then?: (v: string) => void
    ) {
        const s = $(selId) as HTMLSelectElement | null;
        if (!s) return;
        const prev = s.innerHTML;
        s.disabled = true;
        try {
            const r = await fetch(
                `/api/dms/geo?level=${level}&parent_id=${encodeURIComponent(parent)}`,
                { headers: { Authorization: 'Bearer ' + token } }
            );
            const d = await r.json().catch(() => ({}));
            const opts = (d && d.options) || [];
            s.innerHTML = (opts as Pair[])
                .map((o) => `<option value="${esc(o[0])}">${esc(o[1])}</option>`)
                .join('');
            s.disabled = false;
            if (then) then(s.value);
        } catch (e) {
            s.innerHTML = prev;
            s.disabled = false;
        }
    }

    function onGeoChange(which: string, val: string) {
        if (which === 'prov')
            loadGeo('districts', val, 'dic-dist', (dv) =>
                loadGeo('subdistricts', dv, 'dic-sub', (sv) => loadGeo('zipcodes', sv, 'dic-zip'))
            );
        else if (which === 'dist')
            loadGeo('subdistricts', val, 'dic-sub', (sv) => loadGeo('zipcodes', sv, 'dic-zip'));
        else if (which === 'sub') loadGeo('zipcodes', val, 'dic-zip');
    }

    function gather() {
        const v = (id: string) => ($(id) ? ($(id) as HTMLInputElement).value.trim() : '');
        const lbl = (id: string) => {
            const s = $(id) as HTMLSelectElement | null;
            return s && s.selectedIndex >= 0 ? s.options[s.selectedIndex].text : '';
        };
        return {
            fields: {
                prefix_id: v('dic-prefix'),
                prefix_name: lbl('dic-prefix'),
                name: v('dic-name'),
                people_id: v('dic-pid').replace(/\s/g, ''),
                tax_id: v('dic-tax'),
                birthday_be: v('dic-bd'),
                phone: v('dic-tel'),
                house_no: v('dic-house'),
                moo: v('dic-moo'),
                soi: v('dic-soi'),
                road: v('dic-road'),
                province_id: v('dic-prov'),
                province_name: lbl('dic-prov'),
                district_id: v('dic-dist'),
                district_name: lbl('dic-dist'),
                subdistrict_id: v('dic-sub'),
                subdistrict_name: lbl('dic-sub'),
                zipcode_id: v('dic-zip'),
                zipcode: lbl('dic-zip'),
            },
            booking: {
                advisor_id: v('dic-advisor'),
                car_id: v('dic-car'),
                place_book_id: v('dic-place'),
                term_sale_id: v('dic-term'),
                branch_id: v('dic-branch'),
            },
        };
    }

    async function doPush() {
        const btn = $('dic-push') as HTMLButtonElement | null;
        const { fields, booking } = gather();
        if (!fields.people_id || !fields.name) {
            showToast(t('dic-need-fields'), 'error');
            return;
        }
        if (btn) {
            btn.disabled = true;
            btn.textContent = t('dic-pushing');
        }
        try {
            const r = await fetch('/api/dms/id-card/push', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
                body: JSON.stringify({
                    fields,
                    mode: S.mode,
                    customer_id: S.customerId,
                    booking,
                }),
            });
            const d = await r.json().catch(() => ({}));
            if (d && d.ok) {
                renderDone(d.dms_push || {});
                return;
            }
            const p = (d && d.dms_push) || {};
            const fr = (p.error_friendly || {}) as Record<string, string>;
            showToast(fr[lang()] || fr.en || t('dic-push-fail'), 'error');
        } catch (e) {
            showToast(t('dic-push-fail'), 'error');
        }
        if (btn) {
            btn.disabled = false;
            btn.textContent = t('dic-push');
        }
    }

    function renderDone(push: Record<string, unknown>) {
        const el = document.getElementById('dms-id-card-result');
        if (!el) return;
        const modeTxt = push.mode === 'overwrite' ? t('dic-mode-over') : t('dic-mode-new');
        el.innerHTML =
            '<div class="dic-done"><div class="ic">' +
            '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12l5 5 11-11"/></svg></div>' +
            `<div class="t">${esc(t('dic-done-t'))}</div>` +
            `<div class="m">${esc(t('dic-result-customer'))}: <b>#${esc(push.customer_id)}</b> · ${esc(modeTxt)}<br>` +
            `${esc(t('dic-result-booking'))}: <b>${esc(push.booking_no)}</b></div>` +
            `<button class="btn" id="dic-again">${esc(t('dic-again'))}</button></div>`;
        el.scrollIntoView({ behavior: 'smooth' });
    }

    window.clearDmsIdCardResult = function () {
        const el = document.getElementById('dms-id-card-result');
        if (el) {
            el.style.display = 'none';
            el.innerHTML = '';
        }
    };

    function close() {
        const el = document.getElementById('dms-id-card-result');
        if (el) el.innerHTML = '';
    }

    document.addEventListener('change', function (ev) {
        const tg = ev.target as HTMLElement;
        if (tg && tg.matches && tg.matches('select[data-geo]')) {
            onGeoChange(tg.getAttribute('data-geo')!, (tg as HTMLSelectElement).value);
        }
        if (tg && tg.matches && tg.matches('input[name="dic-mode"]')) {
            const over = (document.getElementById('dic-ch-over') as HTMLElement)?.contains(tg);
            S.mode = over ? 'overwrite' : 'create';
            document.getElementById('dic-ch-over')?.classList.toggle('on', !!over);
            document.getElementById('dic-ch-new')?.classList.toggle('on', !over);
        }
    });

    document.addEventListener('click', function (ev) {
        const tg = ev.target as HTMLElement;
        if (tg.closest('#dic-x') || tg.closest('#dic-cancel') || tg.closest('#dic-again')) {
            ev.preventDefault();
            close();
        } else if (tg.closest('#dic-push')) {
            ev.preventDefault();
            doPush();
        } else if (tg.closest('#dic-tax-sw')) {
            ev.preventDefault();
            const sw = tg.closest('#dic-tax-sw') as HTMLElement;
            const on = sw.classList.toggle('on');
            const tax = $('dic-tax') as HTMLInputElement;
            if (tax) {
                if (on) {
                    tax.value = ($('dic-pid') as HTMLInputElement).value.replace(/\s/g, '');
                    tax.readOnly = true;
                } else {
                    tax.readOnly = false;
                }
            }
        }
    });
})();
