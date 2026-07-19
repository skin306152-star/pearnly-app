/*
 * Pearnly AI 收料编排：上传分批源于 G1 真机撞过 prod nginx 50M 单请求挂死。
 * 人工销项走 /sales-summary 解锁 R2；J-B 只在本轮全部收齐且真有新料时自动续跑一次。
 * bundle 顺序要求 state/api/router/render/manifest/bank-sales/queue/excluded 均先于本文件。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;
    var fileInput = null; // 持久隐藏文件选择器(单例,不随 render 重建 → File 不丢)
    var bankSales = null; // AI.intakeBankSales 实例,mount() 时装配一次,取当前 S 靠 getS()
    var intakeQueue = null; // AI.intakeQueue 实例(IN-0b 队列/密码/失败批),同上装配一次
    var excluded = null; // AI.intakeExcluded 实例,独立持有改判 busy/error 态
    var runPoll = null; // 当前重跑轮询的 AI.poll 句柄(mount()/换会话时先停旧的再起新的)

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
            rerunProgress: null, // classify 步逐件进度快照 {step,processed,total} · R2F-R3 #5
            rerunTimedOut: false, // 轮询次数用尽仍未收口(仍在后台跑)· R2F-R3 #5
            bankSalesUi: AI.bankSalesRender.freshUiState(),
            bankSalesPrefill: null, // 「采用建议值」一次性预填 {sales, vat},render() 消费后清空
            manifest: { accepted: 0, rejected: [], zipExpanded: 0 },
            passwordCard: null,
            failedBatches: [],
            resumeBanner: null,
            materialCount: 0,
        };
    }

    function ctx() {
        // 表单输入值在重渲染间保活:读当前 DOM(用户可能已敲了一半)回填。
        return Object.assign(
            {
                order: S.order,
                needsSales: S.needsSales,
                files: S.files,
                uploading: S.uploading,
                uploadErrKey: S.uploadErrKey,
                uploadDone: S.uploadDone,
                uploadTotal: S.uploadTotal,
                uploadBatchIndex: S.uploadBatchIndex,
                uploadBatchTotal: S.uploadBatchTotal,
                uploadBytesPct: S.uploadBytesPct,
                perFile: S.perFile,
                formOpen: S.formOpen,
                formErr: S.formErr,
                submitting: S.submitting,
                dirty: S.dirty,
                rerunState: S.rerunState,
                rerunErrKey: S.rerunErrKey,
                rerunProgress: S.rerunProgress,
                rerunTimedOut: S.rerunTimedOut,
                bankSalesSuggestion: S.order && S.order.bank_sales_suggestion,
                bankSalesUi: S.bankSalesUi,
                salesCorrob: S.order && S.order.sales_corroboration,
                edcCorrob: S.order && S.order.edc_corroboration,
                salesValue: readVal('ikSales'),
                vatValue: readVal('ikVat'),
                noteValue: readVal('ikNote'),
                manifest: S.manifest,
                passwordCard: S.passwordCard,
                failedBatches: S.failedBatches,
                resumeBanner: S.resumeBanner,
                materialCount: S.materialCount,
            },
            excluded.context()
        );
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
        if (S.passwordCard) {
            var pwInput = $('ikPwInput');
            if (pwInput) pwInput.focus();
        }
    }

    function renderUploadProgress() {
        var el = $('ikUploadProgress');
        if (!el) {
            render();
            return;
        }
        el.textContent = AI.intakeRender.uploadProgressText(ctx());
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
                S.materialCount = Number(detail.material_count) || 0;
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
    // 联网时序(按批切分/隔离重试/密码串行/失败批不拦后续批/队列态持久化,A10/A11)全在
    // ai-intake-queue.js 的 create(getS, render) 工厂里(同 bankSales 拆分先例),本文件
    // 只管 DOM 状态过户。
    function upload() {
        if (S.uploading || !S.files.length) return;
        var files = S.files;
        var session = S;
        var acceptedBefore = S.manifest.accepted;
        S.files = [];
        S.resumeBanner = null;
        intakeQueue.upload(files).then(function () {
            maybeAutoRun(session, acceptedBefore);
        });
    }

    // 收齐才开跑(J-B):intakeQueue.upload() 的 promise 要这一趟切出的全部批次(splitBatches)
    // 顺序落盘/拒收/失败都settle 才 resolve——不是每批各触发一次,是这一趟收尾才判一次。
    // 真有新料落盘(accepted 比这一趟开始前多)才自动续跑;一张没落盘(全部拒收/网络失败)
    // 不必空跑一次引擎。手动「重新跑」按钮仍在(rerunHtml),中途/事后用户自己点不受影响。
    function maybeAutoRun(session, acceptedBefore) {
        if (S !== session) return;
        if (session.rerunState === 'waiting') return; // 已经在跑(如失败批重试触发第二趟)
        if (session.manifest.accepted <= acceptedBefore) return;
        startRerun();
    }

    // ============ 续传横幅(A10/A11 · 刷新后接续) ============

    function resumePick() {
        S.resumeBanner = null;
        pickFiles();
    }

    // ============ 密码 PDF 供钥卡(IN-0b) ============

    function submitPassword() {
        intakeQueue.submitPassword(readVal('ikPwInput'));
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

    // ============ 补料后重新跑 + 轮询(共享 AI.poll,同 ai-review.js §4 判活范式) ========

    function startRerun() {
        if (S.rerunState === 'waiting') return;
        var session = S;
        S.rerunState = 'waiting';
        S.rerunErrKey = null;
        S.rerunProgress = null;
        S.rerunTimedOut = false;
        render();
        S.api
            .runOrder(S.orderId)
            .then(function () {
                if (S !== session) return;
                runPollFor(session);
            })
            .catch(function (err) {
                if (S !== session) return;
                var errKey = AI.api.mapApiErrorKey(err && err.code);
                // 409(工单已在跑,如另一标签页/收齐自动开跑触发):不是失败,是我们来晚了
                // ——仍然继续轮询进度,只是带上"正在跑"专属文案而不是让用户干等一个死按钮。
                if (errKey === 'err_workorder_run_in_progress') {
                    S.rerunErrKey = errKey;
                    render();
                    runPollFor(session);
                    return;
                }
                S.rerunState = 'idle';
                S.rerunErrKey = errKey;
                render();
            });
    }

    // 换会话/重复触发时先停旧轮询再起新的(runPoll 是模块作用域单例,同一时间只该有一份
    // 定时器在跑)。
    function runPollFor(session) {
        if (runPoll) runPoll.stop();
        runPoll = AI.poll.create({
            fetch: function () {
                return session.api.getOrder(session.orderId);
            },
            onTick: function (detail) {
                if (S !== session) return;
                // classify(逐张识别)与 reconcile(逐张读对账单)两步的真进度,谁在跑显谁,
                // 不空转省略号(J-1/J-9)。
                var progress = detail.progress || detail.bank_progress;
                if (progress) {
                    S.rerunProgress = progress;
                    render();
                }
            },
            isTerminal: function (detail) {
                if (S !== session) return true; // 已切走会话,静默收口,不做任何副作用
                return routeAfter(detail, session);
            },
            onTimeout: function () {
                if (S !== session) return;
                // 轮询次数用尽不等于跑完/跑失败——真实情况通常是引擎还在后台处理,只是
                // 比预算的时间窗慢。诚实说"仍在后台跑",给手动刷新钮,不假装已收口也
                // 不再无声空转(R2F-R3 #5)。
                S.rerunState = 'idle';
                S.rerunTimedOut = true;
                render();
            },
        });
        runPoll.start();
    }

    // 轮询超时后的手动"刷新查看"(R2F-R3 #5):重新从头计一轮轮询,不是单次探一下就撒手
    // ——用户点了就该看到跟原生重新跑一样的实时进度,不是又一次即时死按钮。
    function refreshAfterTimeout() {
        if (S.rerunState === 'waiting') return;
        S.rerunState = 'waiting';
        S.rerunTimedOut = false;
        render();
        runPollFor(S);
    }

    // 一次轮询拿到的 detail → 是否终态(true=停轮询,调用方已在这里做完全部导航/呈现副作用)。
    function routeAfter(detail, session) {
        var queueLen = AI.reviewQueue.filterPurchaseQueue(detail.flagged || []).length;
        var decision = AI.intakeManifest.routeAfterDecision(detail, queueLen);
        if (decision.kind === 'continue') return false;
        if (decision.kind === 'stay') {
            // 仍 stuck 且给了具体卡点/缺料原因 → 停下来诚实呈现,别空转。
            S.order = detail;
            S.needsSales = (detail.needs || []).indexOf('sales_summary') >= 0;
            S.rerunState = 'idle';
            S.rerunErrKey = null;
            render();
            return true;
        }
        // 走到这里 kind 只剩 review/pkg/wo,恰与 buildClientHash 的 view 值同名,直接用。
        window.location.hash = AI.router.buildClientHash(session.clientId, decision.kind);
        return true;
    }

    // 引导链①(J-B):自动/手动开跑落定后,收料页给「去工单页看进度」的出口——工单页
    // 是唯一能同时看到 classify/reconcile 两段进度 + stuck/review 引导条的地方。
    function gotoWorkorder() {
        window.location.hash = AI.router.buildClientHash(S.clientId, 'wo');
    }

    // 网络级失败批重试成功也算「真有新料落盘」,同 upload() 一样收编进收齐才开跑判断
    // ——不然用户点了重试、料确实传上去了,却还得再多点一次「重新跑」。
    function retryFailed() {
        var session = S;
        var acceptedBefore = S.manifest.accepted;
        intakeQueue.retryFailedBatches().then(function () {
            maybeAutoRun(session, acceptedBefore);
        });
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
        else if (a === 'ik-refresh-status') refreshAfterTimeout();
        else if (a === 'ik-goto-wo') gotoWorkorder();
        else if (a === 'ik-pw-skip') intakeQueue.skipPassword();
        else if (a === 'ik-resume-pick') resumePick();
        else if (a === 'ik-resume-dismiss') intakeQueue.resumeDismiss();
        else if (a === 'ik-retry-failed') retryFailed();
        else if (a.indexOf('bxs-') === 0) bankSales.onAction(a, el);
    }

    function onSubmit(e) {
        if (e.target && e.target.id === 'ikSalesForm') {
            e.preventDefault();
            submitForm();
        } else if (e.target && e.target.id === 'ikPwForm') {
            e.preventDefault();
            submitPassword();
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

    // 目录拖入递归展开；不支持件立即进入拒收盘点。
    function onDrop(e) {
        var dz = e.target.closest && e.target.closest('#ikDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.remove('over');
        var items = e.dataTransfer && e.dataTransfer.items;
        if (items && items.length && AI.intakeQueue.hasDirectoryEntry(items)) {
            AI.intakeQueue.walkDataTransferItems(items).then(function (result) {
                if (!result) return;
                if (result.rejected.length) {
                    S.manifest.rejected = S.manifest.rejected.concat(result.rejected);
                }
                // setFiles() 在空列表时早退不渲染(见其顶注)——全被拒收的文件夹仍要把
                // 盘点条的新拒收项画出来,不能因为没有一件合规就悄悄不吭声。
                if (result.files.length) setFiles(result.files);
                else render();
            });
            return;
        }
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
        host.addEventListener('change', function (event) {
            excluded.onChange(event);
        });
        host.addEventListener('dragover', onDragover);
        host.addEventListener('dragleave', onDragleave);
        host.addEventListener('drop', onDrop);
        document.addEventListener('keydown', onKeydown);
    }

    function mount(api, order, clientId) {
        S = freshState(api, order, clientId);
        // 续传横幅(A10/A11):上次投料若刷新前还有未完成/失败的文件名,读出来提示——
        // 只在真有残留时挂(hasResumableQueue 过滤掉早已全部完成、只是没被清干净的态)。
        var prior = AI.intakeQueue.loadQueueState(order.id);
        S.resumeBanner = AI.intakeManifest.hasResumableQueue(prior) ? prior : null;
        excluded = AI.intakeExcluded.create(
            function () {
                return S;
            },
            render,
            loadDetail
        );
        if (!bankSales) {
            bankSales = AI.intakeBankSales.create(function () {
                return S;
            }, render);
        }
        if (!intakeQueue) {
            intakeQueue = AI.intakeQueue.create(
                function () {
                    return S;
                },
                render,
                renderUploadProgress
            );
        }
        // 换单或换客户时立即停止旧轮询。
        if (runPoll) {
            runPoll.stop();
            runPoll = null;
        }
        wireOnce();
        loadDetail();
    }

    window.AI = window.AI || {};
    window.AI.intake = { mount: mount };
})();
