/*
 * Pearnly AI · ai-intake.js · 收料视图(W4 补料流)编排:上传 + 人工填销项 + 补料后续跑
 *
 * 契约:M1 §四 W4 行 + §五 状态诚实(客户「⌄」只读、LINE/邮箱收料显示未开通)。上传走
 * add_materials(前端先挡 50 张/20MB,后端 413 权威),按总体积/张数自动分批顺序调用(G1
 * 真机:一次 25 张 ~55MB 撞 prod nginx 50M 单请求挂死,splitBatches 见 ai-intake-render.js),
 * 人工填销项走新 /sales-summary 端点落事件解锁 R2;补料后引导「重新跑」——续跑判活/轮询
 * 范式照抄 ai-review.js(切走后续段不认)。银行流水倒推销项(SA-3b)的折叠/裁决/预判/
 * 采用建议值四个动作的网络编排拆到 ai-intake-bank-sales.js(单文件<500 行铁律),本文件
 * 只在 mount() 时用 bankSales.create(getS, render) 接上,onClick 里转发 data-action。
 *
 * 依赖 window.AI.state/api/router/intakeRender/bankSalesRender/intakeBankSales 与全局 at(),
 * 排在它们之后、ai-client.js 之前加载(见 scripts/build-home-js.mjs 的 bundle 顺序)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };
    var POLL_INTERVAL_MS = 2000;
    var POLL_MAX_TRIES = 30;

    var S = null;
    var wired = false;
    var fileInput = null; // 持久隐藏文件选择器(单例,不随 render 重建 → File 不丢)
    var bankSales = null; // AI.intakeBankSales 实例,mount() 时装配一次,取当前 S 靠 getS()

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
            uploadDone: 0, // 分批进度:已成功传的文件数(跨批累计,失败时留在原地不清)
            uploadTotal: 0, // 本次上传选中的文件总数(分批进度分母)
            uploadBatchIndex: 0, // 当前/失败批次序号(1-based)
            uploadBatchTotal: 0, // 本次上传切成的批数(>1 才需要拼进度文案)
            formOpen: false,
            formErr: false,
            submitting: false,
            dirty: false, // 本会话补过料(上传或人工填)→ 亮出「重新跑」
            rerunState: 'idle',
            rerunErrKey: null,
            // 银行流水倒推销项(SA-3b):折叠/行级裁决/预判 三区确认清单的纯 UI 态,
            // 建议本体不落在这里——始终读 S.order.bank_sales_suggestion(getOrder 回放)。
            bankSalesUi: AI.bankSalesRender.freshUiState(),
            bankSalesPrefill: null, // 「采用建议值」一次性预填 {sales, vat},render() 消费后清空
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
            uploadDone: S.uploadDone,
            uploadTotal: S.uploadTotal,
            uploadBatchIndex: S.uploadBatchIndex,
            uploadBatchTotal: S.uploadBatchTotal,
            formOpen: S.formOpen,
            formErr: S.formErr,
            submitting: S.submitting,
            dirty: S.dirty,
            rerunState: S.rerunState,
            rerunErrKey: S.rerunErrKey,
            bankSalesSuggestion: S.order && S.order.bank_sales_suggestion,
            bankSalesUi: S.bankSalesUi,
            salesCorrob: S.order && S.order.sales_corroboration,
            edcCorrob: S.order && S.order.edc_corroboration,
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
            // 「采用建议值」一次性预填(SA-3b):ctx() 在 innerHTML 替换前读的是旧 DOM(此时
            // 新表单还没有值可读),故预填改成替换后直接置 .value——同下面既有的
            // focus-after-replace 手法同一个道理,消费后立即清空防重复写。
            if (S.bankSalesPrefill) {
                var se = $('ikSales');
                var ve = $('ikVat');
                if (se) se.value = S.bankSalesPrefill.sales;
                if (ve) ve.value = S.bankSalesPrefill.vat;
                S.bankSalesPrefill = null;
            }
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

    // 分批选择累积(清单 #4):再次点选/拖拽追加进已选列表(去重按 name+size),不清空上一批
    // ——之前每次选择都整份替换,选完第一批再选第二批会把第一批悄悄丢掉。校验失败时保留原
    // 已选列表不动(只是这一次追加的批不并入),不因新增文件超限连累已经选好的那些。
    function setFiles(list) {
        var incoming = Array.prototype.slice.call(list || []);
        if (!incoming.length) return;
        var merged = AI.intakeRender.mergeFiles(S.files, incoming);
        var check = AI.intakeRender.validateFiles(merged);
        if (!check.ok) {
            S.uploadErrKey = check.errKey;
            render();
            return;
        }
        S.files = merged;
        S.uploadErrKey = null;
        render();
    }

    function clearFiles() {
        S.files = [];
        S.uploadErrKey = null;
        render();
    }

    // 一次选中可能撞 prod nginx client_max_body_size(G1 真机:25 张 ~55MB 单请求挂死)——
    // 按总体积/张数切成若干批(AI.intakeRender.splitBatches),顺序逐批调 addMaterials,
    // 复用同一份 session 判活;全批成功才算成功,某批失败即停,已传批次不重试不回滚。
    function upload() {
        if (S.uploading || !S.files.length) return;
        var session = S;
        var batches = AI.intakeRender.splitBatches(S.files);
        S.uploading = true;
        S.uploadErrKey = null;
        S.uploadDone = 0;
        S.uploadTotal = S.files.length;
        S.uploadBatchIndex = 0;
        S.uploadBatchTotal = batches.length;
        render();
        uploadNextBatch(session, batches, 0);
    }

    function uploadNextBatch(session, batches, index) {
        if (S !== session) return;
        S.uploadBatchIndex = index + 1;
        render();
        var batch = batches[index];
        S.api
            .addMaterials(S.orderId, batch)
            .then(function () {
                if (S !== session) return;
                S.uploadDone += batch.length;
                if (index + 1 < batches.length) {
                    uploadNextBatch(session, batches, index + 1);
                    return;
                }
                S.uploading = false;
                S.files = [];
                S.dirty = true;
                S.rerunErrKey = null;
                render();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.uploading = false;
                // 失败批 + 尚未发出的后续批留在 S.files 里(已成功批不放回)——重试/清空按
                // 剩下的来,不会把刚落库成功的那部分又送一遍(写操作幂等,拒绝重复登记材料)。
                S.files = batches.slice(index).reduce(function (acc, b) {
                    return acc.concat(b);
                }, []);
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
        // 进项队列口径与 W3 审核队列同一份判定(ai-review-queue.js):flagged 进项票 +
        // 方向不明票(kind=unknown/flag_reason=direction_ambiguous)都算未定,不能只认
        // kind===purchase_invoice 漏掉方向票,否则续跑卡在方向票时收料页无处可去。
        var purchaseQueue = AI.reviewQueue.filterPurchaseQueue(detail.flagged || []);
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
        else if (a === 'bxs-fold') bankSales.toggleFold(el.getAttribute('data-kind'));
        else if (a === 'bxs-decide') {
            bankSales.decideRow(el.getAttribute('data-fp'), el.getAttribute('data-verdict'));
        } else if (a === 'bxs-run') bankSales.run();
        else if (a === 'bxs-apply') bankSales.apply();
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
        if (!bankSales) {
            bankSales = AI.intakeBankSales.create(function () {
                return S;
            }, render);
        }
        wireOnce();
        loadDetail();
    }

    window.AI = window.AI || {};
    window.AI.intake = { mount: mount };
})();
