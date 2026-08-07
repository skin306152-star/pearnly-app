/*
 * Pearnly AI · ai-steward-view.js · 会话流页的分区渲染层(S1 · 拆自 ai-steward.js)
 *
 * 只管「把 S 画到屏上」:壳(一次)/ 侧栏 / 页头标题 / 消息流 / 输入条五个分区各自
 * 独立重画,绝不整页 innerHTML —— 输入框里打了一半的字是不可再生资源,重画输入条时
 * 先接住再放回。状态迁移与请求一概不在本层(编排在 ai-steward.js,单一事实源仍是 S)。
 *
 * hooks 契约:
 *   state()          → S(只读)
 *   getEl(id)        → element|null
 *   attachView()     → 附件盘视图(AI.stewardAttach.view())
 *   afterFeedRender()  消息流重画后的钩(编排层挂 actions.syncCountdown)
 */
(function (root) {
    'use strict';

    function create(hooks) {
        function S() {
            return hooks.state();
        }

        function renderShell() {
            var host = hooks.getEl('stwBody');
            host.innerHTML =
                AI.stewardChatRender.shellHtml() + AI.stewardAttachRender.dropOverlayHtml();
            renderSide();
            renderFeed({ force: true });
            renderComposer();
        }

        function renderSide() {
            var el = hooks.getEl('stwSide');
            if (!el) return;
            var s = S();
            el.classList.toggle('collapsed', !!s.sideCollapsed);
            el.innerHTML = AI.stewardSessionsRender.sidebarHtml({
                sessions: s.sessions,
                loading: s.sessionsLoading,
                error: s.sessionsErr,
                activeId: s.sessionId,
                renamingId: s.renamingId,
                deletingId: s.deletingId,
                busy: s.sessBusy,
                budget: s.budget,
                collapsed: s.sideCollapsed,
            });
            renderTitle();
        }

        function activeTitle() {
            var s = S();
            var entry = s.sessions.filter(function (x) {
                return x.session_id === s.sessionId;
            })[0];
            var title = AI.stewardSessionsRender.displayTitle(entry && entry.title);
            if (title) return title;
            var firstUser = s.messages.filter(function (m) {
                return m.role === 'user' && m.text;
            })[0];
            return (
                AI.stewardSessionsRender.displayTitle(firstUser && firstUser.text) ||
                at('stw_sess_untitled')
            );
        }

        function renderTitle() {
            var el = hooks.getEl('stwChatTitle');
            if (el) el.textContent = activeTitle();
        }

        function pinned() {
            var wrap = hooks.getEl('stwFeedWrap');
            return !wrap || wrap.scrollHeight - wrap.scrollTop - wrap.clientHeight < 140;
        }

        function scrollBottom(force) {
            var wrap = hooks.getEl('stwFeedWrap');
            if (wrap && (force || pinned())) wrap.scrollTop = wrap.scrollHeight;
        }

        // 消息流。opts.force:强制滚到底(送出/切会话);平时用户上翻时不抢滚。
        function renderFeed(opts) {
            var el = hooks.getEl('stwFeed');
            if (!el) return;
            var s = S();
            var keep = pinned();
            if (s.creating) {
                el.innerHTML = AI.state.loadingHtml();
                return;
            }
            if (s.createErr) {
                el.innerHTML = AI.state.errorHtml({
                    title: at('stw_session_err_t'),
                    sub: at('stw_session_err_s'),
                    retryLabel: at('stw_retry'),
                });
                return;
            }
            el.innerHTML = AI.stewardFlowRender.feedHtml(s.messages, {
                tasks: s.tasks,
                taskLoading: s.taskLoading,
                procOpen: s.procOpen,
                currentTaskId: s.taskId,
                busy: s.busy,
                stalled: s.stalled,
                authzBusy: s.authzBusy,
                actionErr: s.actionErr,
                hasMore: s.hasMore,
                loadingEarlier: s.loadingEarlier,
            });
            scrollBottom(opts && opts.force ? true : keep);
            hooks.afterFeedRender();
        }

        // live 任务态变化后的统一重画:任务别名回写缓存 + 消息流 + 输入条(停止键跟着变)。
        function renderTaskFace() {
            var s = S();
            if (s.task && s.taskId) s.tasks[s.taskId] = s.task;
            renderFeed();
            renderComposer();
        }

        // 发送键三形态:running 且可取消 = 停止;running 的写活 = 诚实置灰;其余 = 发送。
        function composerMode() {
            var s = S();
            var task = s.taskId && s.tasks[s.taskId];
            if (task && task.status === 'running') {
                return task.cancellable === false ? 'stop-locked' : 'stop';
            }
            return 'send';
        }

        // 输入条重画:先接住已打的字与光标,画完放回 —— 附件盘每变一次就重画一次,
        // 不能拿用户的半句话陪葬。
        function renderComposer() {
            var host = hooks.getEl('stwComposer');
            if (!host) return;
            var s = S();
            var input = hooks.getEl('stwInput');
            var value = input ? input.value : '';
            var hadFocus = input && root.document.activeElement === input;
            var selStart = hadFocus ? input.selectionStart : 0;
            var selEnd = hadFocus ? input.selectionEnd : 0;
            host.innerHTML = AI.stewardChatRender.composerHtml({
                busy: s.busy,
                errText: s.errText,
                attach: hooks.attachView(),
                mode: composerMode(),
                value: value,
            });
            autoGrow();
            var next = hooks.getEl('stwInput');
            if (next && hadFocus) {
                next.focus();
                try {
                    next.setSelectionRange(selStart, selEnd);
                } catch (e) {
                    // 旧引擎对空 textarea 设选区会抛,丢焦点位置无伤。
                }
            }
            syncSendGate();
        }

        function autoGrow() {
            var input = hooks.getEl('stwInput');
            if (!input) return;
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 176) + 'px';
        }

        function syncSendGate() {
            var btn = hooks.getEl('stwSendBtn');
            if (!btn) return;
            var s = S();
            var mode = composerMode();
            if (mode !== 'send') {
                btn.disabled = mode === 'stop-locked' || s.cancelBusy;
                return;
            }
            var input = hooks.getEl('stwInput');
            btn.disabled = !AI.stewardAttachRender.canSubmit({
                text: input ? input.value : '',
                chips: s.attChips,
                busy: s.busy,
            });
        }

        // ---------- 抽屉(≤800px 侧栏) ----------

        function openDrawer() {
            var side = hooks.getEl('stwSide');
            var scrim = hooks.getEl('stwScrim');
            if (side) side.classList.add('open');
            if (scrim) scrim.hidden = false;
        }

        function closeDrawer() {
            var side = hooks.getEl('stwSide');
            var scrim = hooks.getEl('stwScrim');
            if (side) side.classList.remove('open');
            if (scrim) scrim.hidden = true;
        }

        return {
            renderShell: renderShell,
            renderSide: renderSide,
            renderTitle: renderTitle,
            renderFeed: renderFeed,
            renderTaskFace: renderTaskFace,
            renderComposer: renderComposer,
            composerMode: composerMode,
            autoGrow: autoGrow,
            syncSendGate: syncSendGate,
            openDrawer: openDrawer,
            closeDrawer: closeDrawer,
        };
    }

    var api = { create: create };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.stewardView = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
