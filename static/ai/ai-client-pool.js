/*
 * Pearnly AI · ai-client-pool.js · D2-S8 客户池页(会计端)编排:拉取/推批/裁决
 *
 * 顶层「待我处理」导航位(id=v-pool,不挂在客户独立页四视图之下——待问池是跨客户的
 * 会计工作队列,不是某个客户的一个 tab)。四态由 AI.clientPoolRender.pageHtml 拼装,
 * 本文件只管状态机 + 网络 + 事件委托。依赖 window.AI.state/api/format/clientPoolRender
 * 与全局 at(),须排在它们之后、ai.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };
    var TOAST_MS = 3500;

    var S = null;
    var wired = false;

    function body() {
        return $('poolBody');
    }

    function freshState(api) {
        return {
            api: api,
            loading: true,
            error: false,
            groups: [],
            ctx: {}, // workspace_client_id -> {pushBusy, decide: {qid -> {busy, editing, editValue, editErr}}}
            toastTimer: null,
        };
    }

    function ctxFor(wsId) {
        if (!S.ctx[wsId]) S.ctx[wsId] = { pushBusy: false, decide: {} };
        return S.ctx[wsId];
    }

    function decideCtxFor(wsId, qid) {
        var c = ctxFor(wsId);
        if (!c.decide[qid]) c.decide[qid] = { busy: false, editing: false, editValue: '', editErr: false };
        return c.decide[qid];
    }

    function render() {
        var el = body();
        if (S.loading) {
            el.innerHTML = AI.state.loadingHtml();
            return;
        }
        if (S.error) {
            el.innerHTML = AI.state.errorHtml({
                title: at('error_t'),
                sub: at('error_s'),
                retryLabel: at('retry'),
            });
            var btn = el.querySelector('[data-action="retry"]');
            if (btn) btn.onclick = load;
            return;
        }
        el.innerHTML = AI.clientPoolRender.pageHtml(S.groups, S.ctx);
    }

    function load() {
        S.loading = true;
        S.error = false;
        render();
        S.api
            .listClientPool()
            .then(function (data) {
                if (!S) return; // 已卸载
                S.loading = false;
                S.groups = data.groups || [];
                render();
            })
            .catch(function () {
                if (!S) return;
                S.loading = false;
                S.error = true;
                render();
            });
    }

    // ============ toast(推批/裁决失败的一次性提示,同 ai-review.js showToast 精简版) ============

    function showToast(message) {
        hideToast();
        var div = document.createElement('div');
        div.innerHTML = '<div class="toast" id="cpToast">' + AI.state.esc(message) + '</div>';
        var el = div.firstChild;
        document.body.appendChild(el);
        requestAnimationFrame(function () {
            el.classList.add('on');
        });
        S.toastTimer = setTimeout(hideToast, TOAST_MS);
    }

    function hideToast() {
        if (S && S.toastTimer) {
            clearTimeout(S.toastTimer);
            S.toastTimer = null;
        }
        var el = $('cpToast');
        if (el) el.parentNode.removeChild(el);
    }

    function errText(err) {
        var key = AI.api.mapApiErrorKey(err && err.code);
        return at(key) !== key ? at(key) : at('err_generic');
    }

    // ============ 推批 ============

    function onPush(wsId) {
        var c = ctxFor(wsId);
        if (c.pushBusy) return;
        c.pushBusy = true;
        render();
        S.api
            .pushClientPoolBatch(wsId)
            .then(function (result) {
                c.pushBusy = false;
                if (!result || !result.ok) {
                    showToast(at('pool_push_reason_' + ((result && result.reason) || 'failed')));
                }
                load();
            })
            .catch(function (err) {
                c.pushBusy = false;
                showToast(errText(err));
                render();
            });
    }

    // ============ 裁决(manual_review) ============

    function findQuestion(qid) {
        for (var i = 0; i < S.groups.length; i++) {
            var g = S.groups[i];
            var rows = g.questions.manual_review || [];
            for (var j = 0; j < rows.length; j++) {
                if (rows[j].id === qid) return { group: g, question: rows[j] };
            }
        }
        return null;
    }

    var _ASSIGN_KIND = { purchase: 'purchase_invoice', sales: 'sales_doc', nontax: 'non_tax' };

    function submitDecision(wsId, qid, decision, kind, values) {
        var dc = decideCtxFor(wsId, qid);
        dc.busy = true;
        render();
        S.api
            .decideClientPoolQuestion(qid, {
                workspace_client_id: wsId,
                decision: decision,
                kind: kind || null,
                values: values || null,
            })
            .then(function () {
                dc.busy = false;
                load();
            })
            .catch(function (err) {
                dc.busy = false;
                showToast(errText(err));
                render();
            });
    }

    function onDecide(qid, kind) {
        var found = findQuestion(qid);
        if (!found) return;
        var wsId = found.group.workspace_client_id;
        var dc = decideCtxFor(wsId, qid);
        if (_ASSIGN_KIND[kind]) {
            submitDecision(wsId, qid, 'assign_kind', _ASSIGN_KIND[kind], null);
            return;
        }
        if (kind === 'exclude') {
            submitDecision(wsId, qid, 'exclude', null, null);
            return;
        }
        if (kind === 'accept') {
            submitDecision(wsId, qid, 'face_value', null, null);
            return;
        }
        if (kind === 'edit') {
            dc.editing = true;
            render();
            var input = body().querySelector('.cp-q-vat-input[data-qid="' + qid + '"]');
            if (input) input.focus();
            return;
        }
        if (kind === 'recalc') {
            var input2 = body().querySelector('.cp-q-vat-input[data-qid="' + qid + '"]');
            var vat = AI.format.parseAmount(input2 ? input2.value : '', true);
            if (!vat) {
                dc.editErr = true;
                render();
                return;
            }
            dc.editErr = false;
            submitDecision(wsId, qid, 'recalc', null, { vat: vat });
        }
    }

    function onContainerClick(e) {
        var pushEl = e.target.closest('[data-action="cp-push"]');
        if (pushEl) {
            onPush(Number(pushEl.getAttribute('data-ws')));
            return;
        }
        var decideEl = e.target.closest('[data-action="cp-decide"]');
        if (decideEl) {
            onDecide(Number(decideEl.getAttribute('data-qid')), decideEl.getAttribute('data-kind'));
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        body().addEventListener('click', onContainerClick);
    }

    function mount(api) {
        S = freshState(api);
        wireOnce();
        load();
    }

    function onLeave() {
        hideToast();
    }

    window.AI = window.AI || {};
    window.AI.pool = { mount: mount, onLeave: onLeave };
})();
