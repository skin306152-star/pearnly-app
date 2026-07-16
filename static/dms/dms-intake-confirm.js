/* Pearnly DMS · 身份证向导 · 步骤3 资料确认(比对/全字段)+ 步骤4 推送/成功 + 确认弹窗。
 * 移植自主站 src/home/dms-intake-confirm.ts。取值模型在 dms-intake-core.js(DXST)。挂 window.DXCONFIRM。 */
(function (root) {
    'use strict';
    var C = root.DXST;
    var S = C.S;
    var DX_COMPARE = root.DXHTML.DX_COMPARE;
    var esc = C.esc,
        $ = C.$,
        norm = C.norm,
        existing = C.existing;
    function t(k) {
        return typeof root.t === 'function' ? root.t(k) : k;
    }

    function enterConfirm() {
        var p = Promise.resolve();
        if (S.scenario === 'similar') {
            if (!S.selectedId) return root.showToast(t('dx-pick-cand'), 'warn');
            p = loadCustomerFields(S.selectedId);
        }
        return p.then(function () {
            C.initForm();
            S.tab = 'difference';
            renderConfirm();
            C.showStep(3, 'dx-s-confirm');
        });
    }
    function loadCustomerFields(cid) {
        return fetch('/api/dms/customer-fields', {
            method: 'POST',
            headers: C.authHeaders(true),
            body: JSON.stringify({ customer_id: cid }),
        })
            .then(function (r) {
                return r.json().catch(function () {
                    return {};
                });
            })
            .then(function (d) {
                if (d && d.ok) {
                    S.dmsVals = d.current_fields || {};
                    if (d.prefixes) S.prefixes = d.prefixes;
                    if (d.provinces) S.provinces = d.provinces;
                }
            })
            .catch(function () {
                /* dmsVals 留空 → 走新值 */
            });
    }

    function renderConfirm() {
        var el = $('dx-s-confirm');
        if (!el) return;
        el.innerHTML =
            '<div class="dx-tabs">' +
            '<button class="dx-tab' +
            (S.tab === 'difference' ? ' active' : '') +
            '" data-tab="difference">' +
            esc(t('dx-tab-diff')) +
            '</button>' +
            '<button class="dx-tab' +
            (S.tab === 'allfields' ? ' active' : '') +
            '" data-tab="allfields">' +
            esc(t('dx-tab-all')) +
            '</button></div>' +
            '<div class="dx-tabview' +
            (S.tab === 'difference' ? ' active' : '') +
            '">' +
            (existing() ? diffViewHtml() : noMatchHtml()) +
            '</div>' +
            '<div class="dx-tabview' +
            (S.tab === 'allfields' ? ' active' : '') +
            '">' +
            formViewHtml() +
            '</div>';
    }
    function diffViewHtml() {
        return (
            '<div class="dx-cmp-top"><b>' +
            esc(t('dx-cmp-h')) +
            '</b><div class="dx-cmp-act">' +
            '<button class="btn small" id="dx-all-new">' +
            esc(t('dx-all-new')) +
            '</button><button class="btn small" id="dx-all-dms">' +
            esc(t('dx-all-dms')) +
            '</button></div></div>' +
            '<div class="dx-cmp">' +
            cmpHeadHtml() +
            DX_COMPARE.map(cmpRowHtml).join('') +
            '</div>' +
            '<div class="dx-cmp-cards">' +
            cmpCardsHtml() +
            '</div>' +
            decisionHtml() +
            footerHtml(false)
        );
    }
    function cmpCardsHtml() {
        var basic = DX_COMPARE.filter(function (c) {
            return !c.addr;
        })
            .map(cmpCardHtml)
            .join('');
        var addr = DX_COMPARE.filter(function (c) {
            return c.addr;
        })
            .map(cmpCardHtml)
            .join('');
        return basic + '<div class="dx-cmp-sub">' + esc(t('dxs-addr-id')) + '</div>' + addr;
    }
    function cmpCardHtml(c) {
        var nv = C.newCompareVal(c.key);
        var dv = C.dmsCompareVal(c.key);
        var same = norm(nv) === norm(dv);
        var pick = S.pick[c.key] || 'dms';
        var blocked = c.key === 'prefix_name' && S.prefixUnmappable;
        var res = same
            ? '<span class="dx-sbadge">' + esc(t('dx-same')) + '</span>'
            : '<span class="dx-dbadge">' +
              esc(blocked ? t('dx-no-dms-opt') : t('dx-diff')) +
              '</span>';
        var picker =
            same || blocked
                ? ''
                : '<div class="dx-pick" data-key="' +
                  esc(c.key) +
                  '"><button data-src="new" class="' +
                  (pick === 'new' ? 'active' : '') +
                  '">' +
                  esc(t('dx-use-new')) +
                  '</button><button data-src="dms" class="' +
                  (pick === 'dms' ? 'active' : '') +
                  '">DMS</button></div>';
        return (
            '<div class="dx-ccard' +
            (same || blocked ? '' : ' diff') +
            '"><div class="dx-ccard-h"><b>' +
            esc(t(c.label)) +
            '</b>' +
            res +
            '</div><div class="dx-ccard-v"><div><label>' +
            esc(t('dx-col-new')) +
            '</label><strong>' +
            esc(nv || '—') +
            '</strong></div><div><label>' +
            esc(t('dx-col-dms')) +
            '</label><strong>' +
            esc(dv || '—') +
            '</strong></div></div>' +
            picker +
            '</div>'
        );
    }
    function cmpHeadHtml() {
        return (
            '<div class="dx-row head">' +
            ['dx-col-field', 'dx-col-new', 'dx-col-dms', 'dx-col-res', 'dx-col-keep']
                .map(function (k) {
                    return '<div class="dx-cell">' + esc(t(k)) + '</div>';
                })
                .join('') +
            '</div>'
        );
    }
    function cmpRowHtml(c) {
        var nv = C.newCompareVal(c.key);
        var dv = C.dmsCompareVal(c.key);
        var same = norm(nv) === norm(dv);
        var pick = S.pick[c.key] || 'dms';
        var blocked = c.key === 'prefix_name' && S.prefixUnmappable;
        var result = same
            ? '<span class="dx-sbadge">' + esc(t('dx-same')) + '</span>'
            : blocked
              ? '<span class="dx-dbadge" title="' +
                esc(t('dx-no-dms-opt')) +
                '">' +
                esc(t('dx-no-dms-opt')) +
                '</span>'
              : '<span class="dx-dbadge">' + esc(t('dx-diff')) + '</span>';
        var picker = blocked
            ? '<span style="font-size:9px;color:#9a93a6">DMS</span>'
            : '<div class="dx-pick" data-key="' +
              esc(c.key) +
              '"><button data-src="new" class="' +
              (pick === 'new' ? 'active' : '') +
              '">' +
              esc(t('dx-use-new')) +
              '</button><button data-src="dms" class="' +
              (pick === 'dms' ? 'active' : '') +
              '">DMS</button></div>';
        return (
            '<div class="dx-row' +
            (same || blocked ? '' : ' diff') +
            '"><div class="dx-cell"><b>' +
            esc(t(c.label)) +
            '</b></div><div class="dx-cell val">' +
            esc(nv || '—') +
            '</div><div class="dx-cell val">' +
            esc(dv || '—') +
            '</div><div class="dx-cell">' +
            result +
            '</div><div class="dx-cell">' +
            picker +
            '</div></div>'
        );
    }
    function decisionHtml() {
        var upd = S.decision === 'update' ? ' active' : '';
        var ovr = S.decision === 'overwrite' ? ' active' : '';
        return (
            '<div class="dx-decision"><h3>' +
            esc(t('dx-save-way')) +
            '</h3><div class="dx-dgrid"><div class="dx-dcard rec' +
            upd +
            '" data-rec="' +
            esc(t('dx-recommended')) +
            '" data-decision="update"><div class="dx-dic">↻</div><b>' +
            esc(t('dx-dec-update')) +
            '</b><p>' +
            esc(t('dx-dec-update-x')) +
            '</p></div><div class="dx-dcard danger' +
            ovr +
            '" data-decision="overwrite"><div class="dx-dic">!</div><b>' +
            esc(t('dx-dec-over')) +
            '</b><p>' +
            esc(t('dx-dec-over-x')) +
            '</p></div></div><div class="dx-warn' +
            (S.decision === 'overwrite' ? ' show' : '') +
            '">' +
            esc(t('dx-over-warn')) +
            '</div></div>'
        );
    }
    function footerHtml(create) {
        var note = create
            ? esc(t('dx-foot-create'))
            : esc(
                  t(S.decision === 'update' ? 'dx-foot-update' : 'dx-foot-over')
                      .replace('{id}', S.selectedId || '')
                      .replace('{n}', String(C.diffNewCount()))
              );
        var btn = create
            ? t('dx-btn-create')
            : S.decision === 'update'
              ? t('dx-btn-update')
              : t('dx-btn-over');
        return (
            '<div class="dx-foot"><div class="dx-note">' +
            note +
            '</div><button class="btn primary dx-save-btn">' +
            esc(btn) +
            '</button></div>'
        );
    }
    function noMatchHtml() {
        return (
            '<div class="dx-nomatch"><div class="dx-nomatch-ic">+</div><h3>' +
            esc(t('dx-none-t')) +
            '</h3><p>' +
            esc(t('dx-none-create')) +
            '</p></div>' +
            footerHtml(true)
        );
    }

    // 全字段表单:四分区(DXFORM · 拆分模块)+ 本模块 footer(比对/全字段两视图共用)。
    function formViewHtml() {
        return root.DXFORM.sectionsHtml() + footerHtml(!existing());
    }

    // ── 确认弹窗 + 推送 + 成功 ──
    function openModal() {
        C.syncFormFromDom();
        var create = !existing();
        var items = create
            ? [t('dx-m-c1'), t('dx-m-c2'), t('dx-m-c3')]
            : S.decision === 'overwrite'
              ? [t('dx-m-o1'), t('dx-m-o2'), t('dx-m-o3')]
              : [
                    t('dx-m-u1').replace('{id}', S.selectedId || ''),
                    t('dx-m-u2').replace('{n}', String(C.diffNewCount())),
                    t('dx-m-u3'),
                ];
        var title = create
            ? t('dx-m-create-t')
            : S.decision === 'overwrite'
              ? t('dx-m-over-t')
              : t('dx-m-update-t');
        var text = create
            ? t('dx-m-create-x')
            : S.decision === 'overwrite'
              ? t('dx-m-over-x')
              : t('dx-m-update-x');
        var mask = $('dx-modal-mask');
        if (!mask) return;
        mask.innerHTML =
            '<div class="modal dmsx" style="max-width:480px"><div class="modal-head"><b>' +
            esc(title) +
            '</b></div><div class="modal-body"><p style="font-size:12px;color:#6f687d;line-height:1.6;margin:0">' +
            esc(text) +
            '</p><ul class="dx-mlist">' +
            items
                .map(function (x) {
                    return '<li>' + esc(x) + '</li>';
                })
                .join('') +
            '</ul></div><div class="modal-foot" style="display:flex;justify-content:flex-end;gap:8px;padding:13px 18px">' +
            '<button class="btn" id="dx-m-cancel">' +
            esc(t('dx-cancel')) +
            '</button><button class="btn primary" id="dx-m-ok">' +
            esc(t('dx-confirm-save')) +
            '</button></div></div>';
        mask.style.display = 'flex';
    }
    function closeModal() {
        var mask = $('dx-modal-mask');
        if (mask) {
            mask.style.display = 'none';
            mask.innerHTML = '';
        }
    }
    function doSave() {
        if (S.busy) return Promise.resolve();
        var payload = C.buildPayload();
        var fields = payload.fields,
            addresses = payload.addresses;
        if (!fields.people_id || !fields.name) return root.showToast(t('dic-need-fields'), 'error');
        var mode = !existing() ? 'create' : S.decision;
        if (mode === 'create' && !String(fields.phone || '').trim()) {
            S.tab = 'allfields';
            renderConfirm();
            return root.showToast(t('dx-need-phone'), 'error');
        }
        S.busy = true;
        var okBtn = $('dx-m-ok');
        if (okBtn) okBtn.disabled = true;
        return fetch('/api/dms/id-card/push', {
            method: 'POST',
            headers: C.authHeaders(true),
            body: JSON.stringify({
                fields: fields,
                addresses: addresses,
                mode: mode,
                customer_id: S.selectedId,
            }),
        })
            .then(function (r) {
                return r.json().catch(function () {
                    return {};
                });
            })
            .then(function (d) {
                closeModal();
                if (d && d.ok) {
                    renderSuccess(d.dms_push || {}, mode);
                    C.showStep(4, 'dx-s-success');
                    return;
                }
                var fr = (d && d.dms_push && d.dms_push.error_friendly) || {};
                root.showToast(fr[C.lang()] || fr.en || t('dic-push-fail'), 'error');
            })
            .catch(function () {
                closeModal();
                root.showToast(t('dic-push-fail'), 'error');
            })
            .then(function () {
                S.busy = false;
            });
    }
    function renderSuccess(push, mode) {
        var el = $('dx-s-success');
        if (!el) return;
        var create = mode === 'create';
        var cid = push.customer_id || S.selectedId || '';
        var modeTxt = create
            ? t('dx-mode-new')
            : mode === 'overwrite'
              ? t('dx-mode-over')
              : t('dx-mode-update');
        el.innerHTML =
            '<div class="dx-success"><div class="dx-suc-ic">✓</div><h3>' +
            esc(create ? t('dx-suc-create') : t('dx-suc-save')) +
            '</h3><p>' +
            esc(t('dx-suc-sub')) +
            '</p><div class="dx-sgrid"><div class="dx-sitem"><label>' +
            esc(t('dx-result-customer')) +
            '</label><strong>#' +
            esc(cid) +
            ' · ' +
            esc(S.form.name || '') +
            '</strong></div><div class="dx-sitem"><label>' +
            esc(t('dx-result-mode')) +
            '</label><strong>' +
            esc(modeTxt) +
            '</strong></div><div class="dx-sitem"><label>' +
            esc(t('dx-result-res')) +
            '</label><strong>' +
            esc(create ? t('dx-res-created') : t('dx-res-saved')) +
            '</strong></div></div><div class="dx-sact"><button class="btn primary" id="dx-restart">' +
            esc(t('dx-next-id')) +
            '</button></div></div>';
    }

    // 地址级联(府→县→区→邮编)· ID 块/联系/寄送各自联动。
    function onGeoChange(selEl) {
        var fk = selEl.dataset.fk;
        S.form[fk] = selEl.value;
        var chain = {
            province_id: ['districts', 'district_id'],
            district_id: ['subdistricts', 'subdistrict_id'],
            subdistrict_id: ['zipcodes', 'zipcode_id'],
        };
        var base = fk.replace(/_ct$|_sd$/, '');
        var sfx = fk.slice(base.length);
        var next = chain[base];
        if (!next) return C.syncMirror();
        return fetch(
            '/api/dms/geo?level=' + next[0] + '&parent_id=' + encodeURIComponent(selEl.value),
            { headers: C.authHeaders() }
        )
            .then(function (r) {
                return r.json().catch(function () {
                    return {};
                });
            })
            .then(function (d) {
                var opts = (d && d.options) || [];
                var tgt = $('dx-f-' + next[1] + sfx);
                if (tgt && opts.length) {
                    tgt.innerHTML = opts
                        .map(function (o) {
                            return '<option value="' + esc(o[0]) + '">' + esc(o[1]) + '</option>';
                        })
                        .join('');
                    S.form[next[1] + sfx] = tgt.value;
                    tgt.dispatchEvent(new Event('change', { bubbles: true }));
                }
            })
            .catch(function () {
                /* 忽略级联失败 */
            })
            .then(function () {
                C.syncMirror();
            });
    }

    root.DXCONFIRM = {
        enterConfirm: enterConfirm,
        renderConfirm: renderConfirm,
        openModal: openModal,
        closeModal: closeModal,
        doSave: doSave,
        onGeoChange: onGeoChange,
    };
})(typeof self !== 'undefined' ? self : this);
