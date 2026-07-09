/*
 * Pearnly AI · ai-intake.js · 收料视图(W4 补料流)编排:上传 + 人工填销项 + 补料后续跑
 *
 * 契约:M1 §四 W4 行 + §五 状态诚实(客户「⌄」只读、LINE/邮箱收料显示未开通)。上传走
 * add_materials(前端先挡 50 张/20MB,后端 413 权威),人工填销项走新 /sales-summary 端点
 * 落事件解锁 R2;补料后引导「重新跑」——续跑判活/轮询范式照抄 ai-review.js(切走后续段不认)。
 *
 * 依赖 window.AI.state/api/router/intakeRender 与全局 at(),排在它们之后、ai-client.js 之前
 * 加载(见 scripts/build-home-js.mjs 的 bundle 顺序)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };
    var POLL_INTERVAL_MS = 2000;
    var POLL_MAX_TRIES = 30;
    var PURCHASE_KIND = 'purchase_invoice';

    var S = null;
    var wired = false;
    var fileInput = null; // 持久隐藏文件选择器(单例,不随 render 重建 → File 不丢)

    function body() {
        return $('cv-intake');
    }

    function freshState(api, order, clientId) {
        return {
            api: api,
            orderId: order.id,
            clientId: clientId,
            order: null, // getOrder 详情(needs/status/numbers)
            needsSales: false,
            files: [],
            uploading: false,
            uploadErrKey: null,
            formOpen: false,
            formErr: false,
            submitting: false,
            dirty: false, // 本会话补过料(上传或人工填)→ 亮出「重新跑」
            rerunState: 'idle',
            rerunErrKey: null,
        };
    }

    function ctx() {
        // 表单输入值在重渲染间保活:读当前 DOM(用户可能已敲了一半)回填。
        return {
            order: S.order,
            needsSales: S.needsSales,
            files: S.files,
            uploading: S.uploading,
            uploadErrKey: S.uploadErrKey,
            formOpen: S.formOpen,
            formErr: S.formErr,
            submitting: S.submitting,
            dirty: S.dirty,
            rerunState: S.rerunState,
            rerunErrKey: S.rerunErrKey,
            salesValue: readVal('ikSales'),
            vatValue: readVal('ikVat'),
            noteValue: readVal('ikNote'),
        };
    }

    function readVal(id) {
        var el = $(id);
        return el ? el.value : '';
    }

    function render() {
        body().innerHTML = AI.intakeRender.intakeHtml(ctx());
        if (S.formOpen) {
            var input = $('ikSales');
            if (input) input.focus();
        }
    }

    // ============ 拉详情(needs 判缺 sales_summary) ============

    function loadDetail() {
        body().innerHTML = AI.state.loadingHtml();
        var session = S;
        S.api
            .getOrder(S.orderId)
            .then(function (detail) {
                if (S !== session) return;
                S.order = detail;
                S.needsSales = (detail.needs || []).indexOf('sales_summary') >= 0;
                render();
            })
            .catch(function () {
                if (S !== session) return;
                body().innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body().querySelector('[data-action="retry"]');
                if (btn) btn.onclick = loadDetail;
            });
    }

    // ============ 上传补料 ============

    function pickFiles() {
        fileInput.value = '';
        fileInput.click();
    }

    function setFiles(list) {
        var files = Array.prototype.slice.call(list || []);
        if (!files.length) return;
        var check = AI.intakeRender.validateFiles(files);
        if (!check.ok) {
            S.files = [];
            S.uploadErrKey = check.errKey;
            render();
            return;
        }
        S.files = files;
        S.uploadErrKey = null;
        render();
    }

    function clearFiles() {
        S.files = [];
        S.uploadErrKey = null;
        render();
    }

    function upload() {
        if (S.uploading || !S.files.length) return;
        var session = S;
        var files = S.files;
        S.uploading = true;
        S.uploadErrKey = null;
        render();
        S.api
            .addMaterials(S.orderId, files)
            .then(function () {
                if (S !== session) return;
                S.uploading = false;
                S.files = [];
                S.dirty = true;
                S.rerunErrKey = null;
                render();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.uploading = false;
                var key = AI.api.mapApiErrorKey(err && err.code);
                S.uploadErrKey = at(key) !== key ? key : 'err_generic';
                render();
            });
    }

    // ============ 人工填销项 ============

    function openForm() {
        S.formOpen = true;
        S.formErr = false;
        render();
    }

    function cancelForm() {
        S.formOpen = false;
        S.formErr = false;
        render();
    }

    function submitForm() {
        if (S.submitting) return;
        var payload = AI.intakeRender.buildSalesPayload(
            readVal('ikSales'),
            readVal('ikVat'),
            readVal('ikNote')
        );
        if (!payload) {
            S.formErr = true;
            render();
            return;
        }
        var session = S;
        S.submitting = true;
        S.formErr = false;
        render();
        S.api
            .submitSalesSummary(S.orderId, payload)
            .then(function () {
                if (S !== session) return;
                S.submitting = false;
                S.formOpen = false;
                S.dirty = true;
                S.rerunErrKey = null;
                render();
            })
            .catch(function () {
                if (S !== session) return;
                S.submitting = false;
                S.formErr = true;
                render();
            });
    }

    // ============ 补料后重新跑 + 轮询(照 ai-review.js §4 判活范式) ============

    function startRerun() {
        if (S.rerunState === 'waiting') return;
        var session = S;
        S.rerunState = 'waiting';
        S.rerunErrKey = null;
        render();
        S.api
            .runOrder(S.orderId)
            .then(function () {
                if (S !== session) return;
                pollAfterRun(session, 0);
            })
            .catch(function () {
                if (S !== session) return;
                S.rerunState = 'idle';
                S.rerunErrKey = 'err_generic';
                render();
            });
    }

    function pollAfterRun(session, count) {
        if (count >= POLL_MAX_TRIES) {
            S.rerunState = 'idle';
            render();
            return;
        }
        setTimeout(function () {
            if (S !== session) return;
            S.api
                .getOrder(S.orderId)
                .then(function (detail) {
                    if (S !== session) return;
                    routeAfter(detail, session, count);
                })
                .catch(function () {
                    if (S !== session) return;
                    pollAfterRun(session, count + 1);
                });
        }, POLL_INTERVAL_MS);
    }

    function routeAfter(detail, session, count) {
        var hasNumbers = Object.keys(detail.numbers || {}).length > 0;
        var purchaseQueue = (detail.flagged || []).filter(function (it) {
            return it && it.kind === PURCHASE_KIND;
        });
        // 算到数(compute 出 tax_due)或已过 stuck → 去交付包看结果。
        if (hasNumbers || detail.status !== 'stuck') {
            window.location.hash = AI.router.buildClientHash(S.clientId, 'pkg');
            return;
        }
        // 仍 stuck 但改成缺进项裁决 → 去审核队列(补料把销项道打通了,卡点前移到进项)。
        if (purchaseQueue.length) {
            window.location.hash = AI.router.buildClientHash(S.clientId, 'review');
            return;
        }
        // 仍 stuck 且给了具体卡点/缺料原因 → 停下来诚实呈现,别空转。
        var reasons = [].concat(detail.blocked_reasons || [], detail.needs || []);
        if (reasons.length) {
            S.order = detail;
            S.needsSales = (detail.needs || []).indexOf('sales_summary') >= 0;
            S.rerunState = 'idle';
            S.rerunErrKey = null;
            render();
            return;
        }
        pollAfterRun(session, count + 1);
    }

    // ============ 事件接线(容器委托,只挂一次) ============

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'ik-pick' || a === 'ik-goto-upload') pickFiles();
        else if (a === 'ik-clear-files') clearFiles();
        else if (a === 'ik-upload') upload();
        else if (a === 'ik-open-form') openForm();
        else if (a === 'ik-form-cancel') cancelForm();
        else if (a === 'ik-rerun') startRerun();
    }

    function onSubmit(e) {
        if (e.target && e.target.id === 'ikSalesForm') {
            e.preventDefault();
            submitForm();
        }
    }

    // 表单内 Enter 提交 / Esc 取消(Canon §7 键盘可达)。dropzone 聚焦时 Enter/Space 触发选择。
    function onKeydown(e) {
        var view = body();
        if (!view || !view.classList.contains('on')) return;
        if (S.formOpen && view.contains(e.target)) {
            if (e.key === 'Escape') {
                e.preventDefault();
                cancelForm();
            } else if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
                e.preventDefault();
                submitForm();
            }
            return;
        }
        if (e.target && e.target.id === 'ikDrop' && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            pickFiles();
        }
    }

    function onDragover(e) {
        var dz = e.target.closest && e.target.closest('#ikDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.add('over');
    }

    function onDragleave(e) {
        var dz = e.target.closest && e.target.closest('#ikDrop');
        if (dz) dz.classList.remove('over');
    }

    function onDrop(e) {
        var dz = e.target.closest && e.target.closest('#ikDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.remove('over');
        if (e.dataTransfer && e.dataTransfer.files) setFiles(e.dataTransfer.files);
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'ikFileInput';
        fileInput.multiple = true;
        fileInput.accept = '.jpg,.jpeg,.png,.pdf,.xlsx,.xls';
        fileInput.style.display = 'none';
        fileInput.addEventListener('change', function () {
            setFiles(fileInput.files);
        });
        document.body.appendChild(fileInput);
        var host = body();
        host.addEventListener('click', onClick);
        host.addEventListener('submit', onSubmit);
        host.addEventListener('dragover', onDragover);
        host.addEventListener('dragleave', onDragleave);
        host.addEventListener('drop', onDrop);
        document.addEventListener('keydown', onKeydown);
    }

    function mount(api, order, clientId) {
        S = freshState(api, order, clientId);
        wireOnce();
        loadDetail();
    }

    window.AI = window.AI || {};
    window.AI.intake = { mount: mount };
})();
