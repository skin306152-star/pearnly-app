/* Pearnly DMS · 身份证 → DMS 客户 · 4 步向导主控(上传 / 识别匹配 / 事件委托 / 挂载)。
 * 移植自主站 src/home/dms-intake.ts 的 identity 分支——独立壳无发票/汇总任务,去任务切换。
 * 步骤3-4(资料确认/推送)在 dms-intake-confirm.js;状态/取值在 dms-intake-core.js。挂 window.DX。 */
(function (root) {
    'use strict';
    var C = root.DXST;
    var S = C.S;
    var DX_COMPARE = root.DXHTML.DX_COMPARE;
    var CF = root.DXCONFIRM;
    var esc = C.esc,
        sec = C.sec,
        $ = C.$,
        norm = C.norm,
        showStep = C.showStep;
    function t(k) {
        return typeof root.t === 'function' ? root.t(k) : k;
    }
    function toast(m, k) {
        if (typeof root.showToast === 'function') root.showToast(m, k);
    }

    // ── 步骤 1:上传 ──
    function renderUpload() {
        var el = $('dx-s-upload');
        if (!el) return;
        el.innerHTML =
            '<div class="dx-two"><div class="dx-panel"><div class="dx-panel-h"><b>' +
            esc(t('dx-up-title')) +
            '</b><span>' +
            esc(t('dx-up-formats')) +
            '</span></div>' +
            (S.file ? uploadedHtml() : dropHtml()) +
            '</div>' +
            sideHtml(
                [t('dx-side-flow1'), t('dx-side-flow2'), t('dx-side-flow3')],
                t('dx-side-tip')
            ) +
            '</div><input type="file" id="dx-file" accept="image/*,application/pdf" style="display:none">';
    }
    function dropHtml() {
        return (
            '<div class="dx-drop up-dz" id="dx-drop"><div><div class="dx-drop-g">↑</div><h3>' +
            esc(t('dx-up-title')) +
            '</h3><p>' +
            esc(t('dx-up-hint')) +
            '</p><button class="btn primary" id="dx-pick">' +
            esc(t('dx-up-pick')) +
            '</button><div class="dx-hint" style="margin-top:10px">' +
            esc(t('dx-up-drag')) +
            '</div></div></div>'
        );
    }
    function uploadedHtml() {
        var f = S.file;
        return (
            '<div class="dx-file"><div class="dx-file-ic">📄</div><div class="dx-file-c"><b>' +
            esc(f.name) +
            '</b><span>' +
            (f.size / 1048576).toFixed(1) +
            ' MB</span></div><span class="dx-badge green">' +
            esc(t('dx-up-ready')) +
            '</span></div><div class="dx-bar"><div class="dx-note">' +
            esc(t('dx-up-next')) +
            '</div><div style="display:flex;gap:8px"><button class="btn" id="dx-replace">' +
            esc(t('dx-up-replace')) +
            '</button><button class="btn primary" id="dx-start">' +
            esc(t('dx-up-start')) +
            '</button></div></div>'
        );
    }
    function sideHtml(items, tip) {
        return (
            '<div class="dx-side"><div class="dx-side-box"><b>' +
            esc(t('dx-side-cur')) +
            '</b><ul>' +
            items
                .map(function (i) {
                    return '<li>' + esc(i) + '</li>';
                })
                .join('') +
            '</ul></div><div class="dx-side-box"><b>' +
            esc(t('dx-side-rule')) +
            '</b><p>' +
            esc(tip) +
            '</p></div></div>'
        );
    }
    function pickFile() {
        var el = $('dx-file');
        if (el) el.click();
    }
    function onFile(f) {
        if (!f) return;
        S.file = f;
        renderUpload();
    }

    // ── 步骤 2:识别 + 匹配 ──
    function startRecognize() {
        if (!S.file || S.busy) return Promise.resolve();
        S.busy = true;
        renderSearching();
        showStep(2, 'dx-s-searching');
        var form = new FormData();
        form.append('file', S.file, S.file.name);
        return fetch('/api/dms/id-card/recognize', {
            method: 'POST',
            headers: C.authHeaders(),
            body: form,
        })
            .then(function (r) {
                return r
                    .json()
                    .catch(function () {
                        return {};
                    })
                    .then(function (d) {
                        return { r: r, d: d };
                    });
            })
            .then(function (res) {
                var r = res.r,
                    d = res.d;
                if (!r.ok) {
                    var code = (d && d.detail && (d.detail.code || d.detail)) || 'unknown';
                    var k = 'dms-err-' + String(code).toLowerCase();
                    var m = t(k);
                    toast(m && m !== k ? m : t('dic-recognize-fail'), 'error');
                    return backToUpload();
                }
                if (d.needs_review) {
                    toast(t('dic-needs-review'), 'warn');
                    return backToUpload();
                }
                ingestRecognize(d);
                renderMatch();
                showStep(2, 'dx-s-match');
            })
            .catch(function () {
                toast(t('dic-recognize-fail'), 'error');
                backToUpload();
            })
            .then(function () {
                S.busy = false;
            });
    }
    function ingestRecognize(d) {
        S.ocr = d.id_card || {};
        var dms = d.dms || {};
        S.scenario = dms.scenario || 'none';
        S.candidates = dms.candidates || [];
        S.geo = dms.geo || {};
        S.prefixes = dms.prefixes || [];
        S.provinces = (S.geo.provinces || []).slice();
        S.selectedId =
            S.scenario === 'exact'
                ? (S.candidates[0] && S.candidates[0].customer_id) || null
                : null;
        var match = dms.match || {};
        S.dmsVals = S.scenario === 'exact' ? match.current_fields || {} : {};
        C.buildNewVals();
    }
    function renderSearching() {
        var el = $('dx-s-searching');
        if (!el) return;
        var ic = S.ocr || {};
        el.innerHTML =
            '<div class="dx-searching"><div class="dx-spin"></div><h3>' +
            esc(t('dx-searching')) +
            '</h3><p>' +
            esc(t('dx-searching-sub')) +
            '</p><div class="dx-schips">' +
            (ic.people_id ? '<span class="dx-schip">' + esc(ic.people_id) + '</span>' : '') +
            (ic.name ? '<span class="dx-schip">' + esc(ic.name) + '</span>' : '') +
            '<span class="dx-schip">MR.ERP DMS</span></div></div>';
    }
    function renderMatch() {
        var el = $('dx-s-match');
        if (!el) return;
        el.innerHTML =
            '<div class="dx-two"><div>' +
            bannerHtml() +
            '<div class="dx-cands">' +
            candsHtml() +
            '</div><div class="dx-panel"><div class="dx-panel-h"><b>' +
            esc(t('dx-next-h')) +
            '</b><span>' +
            esc(t('dx-next-s')) +
            '</span></div><div style="font-size:11px;color:#7d768e;line-height:1.65">' +
            esc(matchHint()) +
            '</div><div class="dx-actions"><button class="btn" id="dx-back-up">' +
            esc(t('dx-back')) +
            '</button><button class="btn primary" id="dx-go-confirm">' +
            esc(t('dx-go-confirm')) +
            '</button></div></div></div>' +
            sideHtml([t('dx-mrule1'), t('dx-mrule2'), t('dx-mrule3')], t('dx-mrule-why')) +
            '</div>';
    }
    function bannerHtml() {
        var sc = S.scenario;
        var cls = sc === 'exact' ? '' : sc === 'similar' ? ' similar' : ' none';
        var sym = sc === 'exact' ? '✓' : sc === 'similar' ? '!' : '0';
        var badge =
            sc === 'exact'
                ? '<span class="dx-badge green">' + esc(t('dx-b-exact')) + '</span>'
                : sc === 'similar'
                  ? '<span class="dx-badge amber">' + esc(t('dx-b-similar')) + '</span>'
                  : '<span class="dx-badge blue">' + esc(t('dx-b-none')) + '</span>';
        var title =
            sc === 'exact'
                ? t('dx-exact-t').replace('{id}', S.selectedId || '')
                : sc === 'similar'
                  ? t('dx-similar-t').replace('{n}', String(S.candidates.length))
                  : t('dx-none-t');
        var text =
            sc === 'exact'
                ? t('dx-exact-x')
                : sc === 'similar'
                  ? t('dx-similar-x')
                  : t('dx-none-x');
        return (
            '<div class="dx-rbanner' +
            cls +
            '"><div class="dx-rsym">' +
            sym +
            '</div><div class="dx-rc"><b>' +
            esc(title) +
            '</b><p>' +
            esc(text) +
            '</p></div>' +
            badge +
            '</div>'
        );
    }
    function candsHtml() {
        return S.candidates
            .map(function (c) {
                var on = S.selectedId === c.customer_id ? ' active' : '';
                return (
                    '<div class="dx-cand' +
                    on +
                    '" data-cid="' +
                    esc(c.customer_id) +
                    '"><div class="dx-cand-av">C</div><div class="dx-cand-c"><b>DMS #' +
                    esc(c.customer_id) +
                    ' · ' +
                    esc(c.name || '') +
                    '</b><span>' +
                    esc(t('dx-c-id')) +
                    ' ' +
                    esc(c.people_id || '—') +
                    ' · ' +
                    esc(t('dx-c-score')) +
                    ' ' +
                    esc(c.score != null ? c.score : '') +
                    '%</span></div><div class="dx-radio"></div></div>'
                );
            })
            .join('');
    }
    function matchHint() {
        return S.scenario === 'exact'
            ? t('dx-hint-exact')
            : S.scenario === 'similar'
              ? t('dx-hint-similar')
              : t('dx-hint-none');
    }

    // ── 导航 / 重置 ──
    function backToUpload() {
        renderUpload();
        showStep(1, 'dx-s-upload');
    }
    function resetFlow() {
        S.file = null;
        S.ocr = null;
        S.selectedId = null;
        S.decision = 'update';
        S.tab = 'difference';
        renderUpload();
        showStep(1, 'dx-s-upload');
    }
    // 查看记录:切壳导航到「推送记录」页(恒按 mrerp_dms 筛,见 dms-records.js)。
    function openRecords() {
        if (typeof root._dmsGoRecords === 'function') root._dmsGoRecords();
    }

    // ── 事件委托 ──
    function bind() {
        var el = sec();
        if (!el || el.dataset.dxBound) return;
        el.dataset.dxBound = '1';

        el.addEventListener('click', function (ev) {
            var tg = ev.target;
            var hit = function (id) {
                return tg.closest('#' + id);
            };
            if (hit('dx-records')) return openRecords();
            if (hit('dx-pick') || (tg.closest('#dx-drop') && !S.file)) return pickFile();
            if (hit('dx-replace')) {
                S.file = null;
                return renderUpload();
            }
            if (hit('dx-start')) return void startRecognize();
            if (hit('dx-back-up')) return backToUpload();
            if (hit('dx-go-confirm')) return void CF.enterConfirm();
            if (hit('dx-restart')) return resetFlow();
            if (tg.closest('.dx-save-btn')) return CF.openModal();
            if (hit('dx-m-cancel')) return CF.closeModal();
            if (hit('dx-m-ok')) return void CF.doSave();
            if (hit('dx-all-new')) {
                DX_COMPARE.filter(function (c) {
                    return norm(C.newCompareVal(c.key)) !== norm(C.dmsCompareVal(c.key));
                }).forEach(function (c) {
                    S.pick[c.key] = C.newCompareVal(c.key) ? 'new' : 'dms';
                });
                C.applyDecisionToForm();
                C.syncMirror();
                return CF.renderConfirm();
            }
            if (hit('dx-all-dms')) {
                DX_COMPARE.forEach(function (c) {
                    S.pick[c.key] = 'dms';
                });
                C.applyDecisionToForm();
                C.syncMirror();
                return CF.renderConfirm();
            }
            var cand = tg.closest('[data-cid]');
            if (cand) {
                S.selectedId = cand.dataset.cid;
                el.querySelectorAll('.dx-cand').forEach(function (x) {
                    x.classList.toggle('active', x === cand);
                });
                return;
            }
            var tab = tg.closest('[data-tab]');
            if (tab) {
                S.tab = tab.dataset.tab;
                C.syncFormFromDom();
                return CF.renderConfirm();
            }
            var dec = tg.closest('[data-decision]');
            if (dec) {
                S.decision = dec.dataset.decision;
                C.applyDecisionToForm();
                C.syncMirror();
                return CF.renderConfirm();
            }
            var pickBtn = tg.closest('.dx-pick [data-src]');
            if (pickBtn) {
                var key = pickBtn.closest('[data-key]').dataset.key;
                S.pick[key] = pickBtn.dataset.src;
                C.applyDecisionToForm();
                C.syncMirror();
                return CF.renderConfirm();
            }
            var mir = tg.closest('[data-mirror]');
            if (mir) {
                var sfx = mir.dataset.mirror;
                S.sameAs[sfx] = !S.sameAs[sfx];
                C.syncFormFromDom();
                return CF.renderConfirm();
            }
            var fsecH = tg.closest('.dx-fsec-h');
            if (fsecH) {
                var secEl = fsecH.closest('[data-sec]');
                if (secEl) {
                    C.syncFormFromDom();
                    var id = secEl.dataset.sec;
                    S.openSec[id] = !S.openSec[id];
                    return CF.renderConfirm();
                }
            }
        });

        el.addEventListener('change', function (ev) {
            var tg = ev.target;
            if (tg.id === 'dx-file') return onFile((tg.files && tg.files[0]) || null);
            if (tg.matches('select[data-geo]')) return void CF.onGeoChange(tg);
            var fk = tg.dataset && tg.dataset.fk;
            if (fk) S.form[fk] = tg.value;
        });

        el.addEventListener('dragover', function (ev) {
            if (S.step !== 1) return;
            ev.preventDefault();
            var dz = el.querySelector('.dx-drop');
            if (dz) dz.classList.add('drag-over');
        });
        el.addEventListener('dragleave', function () {
            var dz = el.querySelector('.dx-drop');
            if (dz) dz.classList.remove('drag-over');
        });
        el.addEventListener('drop', function (ev) {
            if (S.step !== 1) return;
            ev.preventDefault();
            var dz = el.querySelector('.dx-drop');
            if (dz) dz.classList.remove('drag-over');
            var files = ev.dataTransfer && ev.dataTransfer.files;
            onFile((files && files[0]) || null);
        });
    }

    // 复原当前步(壳内软导航回来 → 保留向导进度;硬刷新后内存态空 → 干净从头)。
    function renderCurrentStep() {
        if (S.ocr && S.step === 2) {
            renderMatch();
            return showStep(2, 'dx-s-match');
        }
        if (S.ocr && S.step === 3) {
            CF.renderConfirm();
            return showStep(3, 'dx-s-confirm');
        }
        renderUpload();
        showStep(1, 'dx-s-upload');
    }

    function mountIntake() {
        var el = sec();
        if (!el) return;
        el.innerHTML = root.DXHTML.dxShell(t);
        root.DXERP.renderCards();
        root.DXLINE.mount('#dx-line-card');
        bind();
        if (!S.ocr) S.step = 1;
        renderCurrentStep();
    }

    // 语言切换:整壳重渲 + 复原当前步(仅当录入视图在场)。
    if (typeof root.subscribeI18n === 'function') {
        root.subscribeI18n('dms-intake', function () {
            var el = sec();
            if (!el || !el.querySelector('.dmsx')) return;
            el.innerHTML = root.DXHTML.dxShell(t);
            root.DXERP.renderCards();
            if (S.step === 1) renderUpload();
            else if (S.ocr && S.step === 2) renderMatch();
            else if (S.ocr && S.step === 3) CF.renderConfirm();
            var map = { 1: 'dx-s-upload', 2: 'dx-s-match', 3: 'dx-s-confirm', 4: 'dx-s-success' };
            showStep(S.step, map[S.step] || 'dx-s-upload');
        });
    }

    root.DX = { mountIntake: mountIntake, resetFlow: resetFlow };
})(typeof self !== 'undefined' ? self : this);
