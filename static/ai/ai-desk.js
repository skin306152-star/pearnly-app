/*
 * Pearnly AI · ai-desk.js · FD-0d 总台(#/desk)编排:上传 + 说目标 + 确认开工 + 手动兜底
 *
 * 顶层导航位(id=v-desk,同 /vatcheck /fileconv /payroll 先例)。状态机 + 网络 + 事件
 * 委托在本文件,HTML 拼装交给 AI.deskRender / AI.deskComposeRender(纯函数,零网络
 * 依赖)——同 ai-vatcheck.js/ai-payroll.js 先例。
 *
 * 一轮「送出」= 累积的待传文件(可能来自两次以上拖拽合批,AI.intakeRender.mergeFiles)
 * + 当前输入框文字,一次性建一份新草稿合同(POST contracts),若带了目标文字紧接着调
 * interpret。合同一旦建立不再二次追加文件(后端 create_contract 是纯建草稿,没有「追加
 * 到既有草稿」的端点)——同一目标要追加料,拿「修改」重新说一遍,新建一份合同。
 *
 * 依赖 window.AI.state/api/format/board/intakeRender/deskRender/deskComposeRender 与
 * 全局 at(),排在它们之后、ai-client.js 与 ai.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };
    var R = function () {
        return AI.deskRender;
    };
    var CR = function () {
        return AI.deskComposeRender;
    };

    var S = null;
    var wired = false;
    var fileInput = null; // 持久隐藏文件选择器(单例,不随 render 重建 → File 不丢,同 ai-intake.js 先例)

    function body() {
        return $('fdBody');
    }

    function freshState(api) {
        return {
            api: api,
            clients: [],
            contextClientId: '',
            turns: [], // 由 feed 重建,旧→新排(聊天式阅读顺序)
            liveExtra: {}, // contractId -> { inventory, suggestion, degraded, reason }(本次会话)
            contractCtx: {}, // contractId -> { selection:{clientId,period,intent}, confirming, errKey }
            lastDraftContractId: null, // 最近一次送出、尚未确认的草稿合同(手动兜底复用其暂存料)
            pendingFiles: [],
            utterance: '',
            sending: false,
            uploadErrKey: null,
            manual: {
                open: false,
                selection: {},
                submitting: false,
                errKey: null,
                reuseContractId: null,
            },
        };
    }

    // 合同卡的客户下拉/需料对照要用到客户名录 + 盘点分组——两者都是会话级状态
    // (S.clients/S.liveExtra),不属于 confirm 选择本身,渲染前统一并入每份 contractCtx,
    // 免得 ai-desk-render.js/ai-desk-compose-render.js 的纯函数签名要跟着传两份额外参数。
    function syncContractCtxDerived() {
        Object.keys(S.contractCtx).forEach(function (id) {
            var ctx = S.contractCtx[id];
            ctx.clients = S.clients;
            var extra = S.liveExtra[id];
            ctx.inventoryGroups = (extra && extra.inventory && extra.inventory.groups) || null;
        });
    }

    function render() {
        syncContractCtxDerived();
        body().innerHTML = CR().pageHtml(S);
    }

    function mapErrKey(err) {
        var key = AI.api.mapApiErrorKey(err && err.code);
        return at(key) !== key ? key : 'err_generic';
    }

    function scrollFeedToBottom() {
        var feed = $('fdFeed');
        if (feed) feed.scrollTop = feed.scrollHeight;
    }

    function loadClients() {
        S.api
            .listClients()
            .then(function (r) {
                if (!S) return;
                S.clients = (r && r.clients) || [];
                render();
            })
            .catch(function () {
                /* 客户列表加载失败不阻断总台其余功能,选择器留空由会计重试触发重拉 */
            });
    }

    function computeTurn(contract) {
        var turn = R().deriveCard(contract, S.liveExtra[contract.id]);
        turn.contract = contract;
        return turn;
    }

    function appendOrReplaceTurn(contract) {
        var turn = computeTurn(contract);
        for (var i = 0; i < S.turns.length; i++) {
            if (S.turns[i].contract.id === contract.id) {
                S.turns[i] = turn;
                return;
            }
        }
        S.turns.push(turn);
    }

    function loadFeed() {
        var session = S;
        S.api
            .getDeskFeed(S.contextClientId || null, 50)
            .then(function (r) {
                if (S !== session) return;
                var contracts = ((r && r.contracts) || []).slice().reverse(); // 倒序→旧到新
                S.turns = contracts.map(computeTurn);
                render();
                scrollFeedToBottom();
            })
            .catch(function () {
                /* feed 拉取失败不阻断本次上传/说目标的即时反馈(S.turns 已有的仍显示) */
            });
    }

    // ── 上传(累积多次拖拽/选择,复用 AI.intakeRender 的校验/合批纯函数)────────────────

    function pickFile() {
        fileInput.value = '';
        fileInput.click();
    }

    function setFiles(list) {
        var incoming = Array.prototype.slice.call(list || []);
        if (!incoming.length) return;
        var check = AI.intakeRender.validateFiles(incoming);
        if (!check.ok) {
            S.uploadErrKey = check.errKey;
            render();
            return;
        }
        S.pendingFiles = AI.intakeRender.mergeFiles(S.pendingFiles, incoming);
        S.uploadErrKey = null;
        render();
    }

    function clearFiles() {
        S.pendingFiles = [];
        S.uploadErrKey = null;
        render();
    }

    function useChip(text) {
        S.utterance = text;
        render();
    }

    // ── 送出:建草稿(带当前累积文件)→ 有文字则接着 interpret ──────────────────────

    function send() {
        if (S.sending) return;
        var utterance = (S.utterance || '').trim();
        var files = S.pendingFiles;
        if (!files.length && !utterance) return;
        var session = S;
        S.sending = true;
        S.uploadErrKey = null;
        render();
        S.api
            .createDeskContract({ files: files })
            .then(function (r) {
                if (S !== session) return;
                var contractId = r.contract.id;
                S.liveExtra[contractId] = { inventory: r.inventory };
                S.pendingFiles = [];
                S.lastDraftContractId = contractId;
                appendOrReplaceTurn(r.contract);
                if (!utterance) return null;
                return S.api.interpretDeskGoal(contractId, utterance).then(function (out) {
                    if (S !== session) return;
                    applySuggestion(contractId, out.suggestion);
                });
            })
            .catch(function (err) {
                if (S !== session) return;
                S.uploadErrKey = mapErrKey(err);
            })
            .then(function () {
                if (S !== session) return;
                S.utterance = '';
                S.sending = false;
                render();
                scrollFeedToBottom();
            });
    }

    function applySuggestion(contractId, suggestion) {
        var extra = S.liveExtra[contractId] || {};
        if (suggestion.degraded) {
            extra.degraded = true;
            extra.reason = suggestion.reason;
            extra.suggestion = null;
        } else {
            extra.degraded = false;
            extra.suggestion = suggestion;
            if (suggestion.intent && suggestion.intent !== 'unsupported') {
                var periods = AI.board.periodOptions();
                S.contractCtx[contractId] = {
                    selection: {
                        clientId:
                            suggestion.client_suggestion != null
                                ? String(suggestion.client_suggestion)
                                : S.contextClientId || '',
                        period: suggestion.period || periods[0],
                        intent: suggestion.intent,
                    },
                };
            }
        }
        S.liveExtra[contractId] = extra;
        // 补上盘点摘要(合同卡的需料对照要用):create 时已存,合并进同一份 liveExtra。
        appendOrReplaceTurn(findContract(contractId) || { id: contractId, status: 'draft' });
    }

    function findContract(contractId) {
        for (var i = 0; i < S.turns.length; i++) {
            if (S.turns[i].contract.id === contractId) return S.turns[i].contract;
        }
        return null;
    }

    // ── 合同卡:改客户/期间(必须人点下拉)→ 确认开工 / 修改(重新说一遍) ────────────

    function ensureCtx(contractId) {
        if (!S.contractCtx[contractId]) S.contractCtx[contractId] = { selection: {} };
        return S.contractCtx[contractId];
    }

    // 命名避开裸「confirm」调用形——ui_design_lint 的原生弹窗检查按不加限定的函数名
    // 正则抓,同名会被误判成浏览器原生确认框。
    function confirmContract(contractId) {
        var ctx = ensureCtx(contractId);
        var sel = ctx.selection || {};
        if (!R().confirmReady(sel) || ctx.confirming) return;
        var session = S;
        ctx.confirming = true;
        ctx.errKey = null;
        render();
        S.api
            .confirmDeskContract({
                contract_id: contractId,
                workspace_client_id: Number(sel.clientId),
                period: sel.period,
                intent: sel.intent,
            })
            .then(function (out) {
                if (S !== session) return;
                var c = findContract(contractId) || { id: contractId };
                appendOrReplaceTurn(
                    Object.assign({}, c, {
                        status: 'executing',
                        work_order_id: out.work_order_id,
                        workspace_client_id: Number(sel.clientId),
                        period: sel.period,
                        intent: sel.intent,
                    })
                );
                if (S.lastDraftContractId === contractId) S.lastDraftContractId = null;
            })
            .catch(function (err) {
                if (S !== session) return;
                ctx.errKey = mapErrKey(err);
            })
            .then(function () {
                if (S !== session) return;
                ctx.confirming = false;
                render();
            });
    }

    // 「修改」:不撤销合同(后端无 reject 端点可用),只清掉本次会话建议,回落成盘点/空卡,
    // 把输入框焦点还给用户重新说一遍——interpret 对同一 contract_id 可重复调用(update_draft
    // 幂等覆盖 brain_suggestion),不必新建合同。
    function modify(contractId) {
        var extra = S.liveExtra[contractId] || {};
        extra.suggestion = null;
        extra.degraded = false;
        S.liveExtra[contractId] = extra;
        delete S.contractCtx[contractId];
        var c = findContract(contractId);
        if (c) appendOrReplaceTurn(Object.assign({}, c, { brain_suggestion: {} }));
        render();
        var input = $('fdUtteranceInput');
        if (input) input.focus();
    }

    // ── 手动开单兜底(不经大脑,永远可用)───────────────────────────────────────
    //
    // 两条子路径:①刚送出过一轮还没被确认的草稿(常见于降级卡:料已经暂存在那份合同
    // 里)→ 手动表单直接对同一 contract_id 调 confirm,不必重新选文件重新传一遍;
    // ②没有可复用的草稿(手动面板主动点开,或从没送出过)→ 走建合同+确认两段,吃
    // composer 当前累积的 pendingFiles。

    function openManual() {
        var reuseId =
            S.lastDraftContractId && findContract(S.lastDraftContractId)
                ? S.lastDraftContractId
                : null;
        S.manual = {
            open: true,
            selection: {},
            submitting: false,
            errKey: null,
            reuseContractId: reuseId,
        };
        render();
    }

    function cancelManual() {
        S.manual = {
            open: false,
            selection: {},
            submitting: false,
            errKey: null,
            reuseContractId: null,
        };
        render();
    }

    function finishManualConfirm(contract, sel, out) {
        appendOrReplaceTurn(
            Object.assign({}, contract, {
                status: 'executing',
                work_order_id: out.work_order_id,
                workspace_client_id: Number(sel.clientId),
                period: sel.period,
                intent: sel.intent,
            })
        );
        if (S.lastDraftContractId === contract.id) S.lastDraftContractId = null;
        S.manual = {
            open: false,
            selection: {},
            submitting: false,
            errKey: null,
            reuseContractId: null,
        };
    }

    function manualSubmit() {
        var sel = S.manual.selection || {};
        if (!R().confirmReady(sel) || S.manual.submitting) return;
        var reuseId = S.manual.reuseContractId;
        if (!reuseId && !S.pendingFiles.length) return;
        var session = S;
        S.manual.submitting = true;
        S.manual.errKey = null;
        render();

        var chain = reuseId
            ? Promise.resolve({ contract: findContract(reuseId) || { id: reuseId } })
            : S.api.createDeskContract({
                  clientId: sel.clientId,
                  period: sel.period,
                  intent: sel.intent,
                  files: S.pendingFiles,
              });

        chain
            .then(function (r) {
                if (S !== session) return null;
                return S.api
                    .confirmDeskContract({
                        contract_id: r.contract.id,
                        workspace_client_id: Number(sel.clientId),
                        period: sel.period,
                        intent: sel.intent,
                    })
                    .then(function (out) {
                        if (S !== session) return;
                        finishManualConfirm(r.contract, sel, out);
                        if (!reuseId) S.pendingFiles = [];
                    });
            })
            .catch(function (err) {
                if (S !== session) return;
                S.manual.errKey = mapErrKey(err);
            })
            .then(function () {
                if (S !== session) return;
                S.manual.submitting = false;
                render();
                scrollFeedToBottom();
            });
    }

    // ── 事件委托 ──────────────────────────────────────────────────────────────

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        var cid = el.getAttribute('data-contract');
        if (a === 'desk-pick') pickFile();
        else if (a === 'desk-clear-files') clearFiles();
        else if (a === 'desk-send') send();
        else if (a === 'desk-confirm') confirmContract(cid);
        else if (a === 'desk-modify') modify(cid);
        else if (a === 'desk-chip') useChip(el.getAttribute('data-text') || '');
        else if (a === 'desk-open-manual') openManual();
        else if (a === 'desk-manual-cancel') cancelManual();
        else if (a === 'desk-manual-submit') manualSubmit();
    }

    function onInput(e) {
        if (e.target && e.target.id === 'fdUtteranceInput') {
            S.utterance = e.target.value;
            var btn = body().querySelector('[data-action="desk-send"]');
            if (btn) btn.disabled = S.sending || !(S.pendingFiles.length || S.utterance.trim());
        }
    }

    function onChange(e) {
        var t = e.target;
        if (t.classList && t.classList.contains('fd-client-sel')) {
            ensureCtx(t.getAttribute('data-contract')).selection.clientId = t.value;
            render();
        } else if (t.classList && t.classList.contains('fd-period-sel')) {
            ensureCtx(t.getAttribute('data-contract')).selection.period = t.value;
            render();
        } else if (t.id === 'fdCtxClientSel') {
            S.contextClientId = t.value;
            loadFeed();
        } else if (t.id === 'fdManualClientSel') {
            S.manual.selection.clientId = t.value;
            render();
        } else if (t.id === 'fdManualPeriodSel') {
            S.manual.selection.period = t.value;
            render();
        } else if (t.id === 'fdManualIntentSel') {
            S.manual.selection.intent = t.value;
            render();
        }
    }

    function onDragover(e) {
        var dz = e.target.closest && e.target.closest('#deskDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.add('over');
    }
    function onDragleave(e) {
        var dz = e.target.closest && e.target.closest('#deskDrop');
        if (dz) dz.classList.remove('over');
    }
    function onDrop(e) {
        var dz = e.target.closest && e.target.closest('#deskDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.remove('over');
        if (e.dataTransfer && e.dataTransfer.files) setFiles(e.dataTransfer.files);
    }
    function onKeydown(e) {
        if (e.target && e.target.id === 'deskDrop' && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            pickFile();
        }
        if (e.target && e.target.id === 'fdUtteranceInput' && e.key === 'Enter') {
            e.preventDefault();
            send();
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'fdFileInput';
        fileInput.multiple = true;
        fileInput.style.display = 'none';
        fileInput.addEventListener('change', function () {
            setFiles(fileInput.files);
        });
        document.body.appendChild(fileInput);
        var host = body();
        host.addEventListener('click', onClick);
        host.addEventListener('input', onInput);
        host.addEventListener('change', onChange);
        host.addEventListener('dragover', onDragover);
        host.addEventListener('dragleave', onDragleave);
        host.addEventListener('drop', onDrop);
        host.addEventListener('keydown', onKeydown);
    }

    function mount(api) {
        S = freshState(api);
        wireOnce();
        render();
        loadClients();
        loadFeed();
    }

    window.AI = window.AI || {};
    window.AI.desk = { mount: mount };
})();
