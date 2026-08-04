/*
 * Pearnly AI · ai-steward-sessions.js · 会话侧栏动作层(S1):列表 / 切换 / 改名 / 删除 / 余额
 *
 * 工厂注入钩子,零模块级状态 —— 状态全落在 ai-steward.js 的 S 上(单一事实源)。
 * node(tests/unit/test_ai_steward_sessions.py)用假钩子 + 假 api 直接 create() 断言
 * 状态迁移,不需要浏览器。
 *
 * hooks 契约:
 *   state()            → S(读写 sessions/sessionsLoading/sessionsErr/renamingId/
 *                        deletingId/sessBusy/budget;读 api/sessionId)
 *   getEl(id)          → element|null(改名输入框取值)
 *   renderSide()       重画侧栏
 *   switchSession(sid) 切到另一个会话(消息流重建归编排层)
 *   newSession()       开新会话(删掉当前会话后的落点)
 */
(function (root) {
    'use strict';

    function create(hooks) {
        function load() {
            var S = hooks.state();
            if (!S) return;
            S.sessionsLoading = !S.sessions.length; // 已有列表时静默刷新,不闪骨架
            S.sessionsErr = false;
            hooks.renderSide();
            var session = S;
            S.api
                .listStewardSessions()
                .then(function (resp) {
                    if (hooks.state() !== session) return;
                    S.sessionsLoading = false;
                    S.sessions = (resp && resp.sessions) || [];
                    hooks.renderSide();
                })
                .catch(function () {
                    if (hooks.state() !== session) return;
                    S.sessionsLoading = false;
                    // 已有列表时刷新失败不翻错脸:旧列表仍是真的,静默留着下次再刷。
                    S.sessionsErr = !S.sessions.length;
                    hooks.renderSide();
                });
        }

        // 余额是给人看的参考数:拿不到就整行不显示(budget=null),不编数字、不翻错脸。
        function refreshBudget() {
            var S = hooks.state();
            if (!S || !S.sessionId) return;
            var session = S;
            var sid = S.sessionId;
            S.api
                .getStewardBudget(sid)
                .then(function (resp) {
                    if (hooks.state() !== session || S.sessionId !== sid) return;
                    S.budget = resp && resp.available ? resp : null;
                    hooks.renderSide();
                })
                .catch(function () {
                    if (hooks.state() !== session) return;
                    S.budget = null;
                    hooks.renderSide();
                });
        }

        function startRename(sid) {
            var S = hooks.state();
            if (!S || S.sessBusy) return;
            S.renamingId = sid;
            S.deletingId = null;
            hooks.renderSide();
            var input = hooks.getEl('stwSessRename');
            if (input) {
                input.focus();
                input.select();
            }
        }

        function commitRename(sid) {
            var S = hooks.state();
            var input = hooks.getEl('stwSessRename');
            if (!S || !input || S.sessBusy) return;
            var title = String(input.value || '').trim();
            var old = S.sessions.filter(function (s) {
                return s.session_id === sid;
            })[0];
            // 没改/清空 = 撤销,不打请求(空标题后端 422,这里直接不送)。
            if (!title || (old && title === old.title)) {
                S.renamingId = null;
                hooks.renderSide();
                return;
            }
            S.sessBusy = true;
            hooks.renderSide();
            var session = S;
            S.api
                .renameStewardSession(sid, title)
                .then(function (resp) {
                    if (hooks.state() !== session) return;
                    S.sessBusy = false;
                    S.renamingId = null;
                    if (old) old.title = (resp && resp.title) || title;
                    hooks.renderSide();
                })
                .catch(function () {
                    if (hooks.state() !== session) return;
                    // 改名失败保持编辑态,填的字还在 —— 吞掉输入再让人重打一遍是双重惩罚。
                    S.sessBusy = false;
                    hooks.renderSide();
                });
        }

        function cancelRename() {
            var S = hooks.state();
            if (!S) return;
            S.renamingId = null;
            hooks.renderSide();
        }

        function askDelete(sid) {
            var S = hooks.state();
            if (!S || S.sessBusy) return;
            S.deletingId = sid;
            S.renamingId = null;
            hooks.renderSide();
        }

        function confirmDelete(sid) {
            var S = hooks.state();
            if (!S || S.sessBusy) return;
            S.sessBusy = true;
            hooks.renderSide();
            var session = S;
            S.api
                .deleteStewardSession(sid)
                .then(function () {
                    if (hooks.state() !== session) return;
                    S.sessBusy = false;
                    S.deletingId = null;
                    S.sessions = S.sessions.filter(function (s) {
                        return s.session_id !== sid;
                    });
                    if (S.sessionId === sid) {
                        // 删的是正开着的会话:落到最近的另一个,一个不剩就开新对话。
                        var next = S.sessions[0];
                        if (next) hooks.switchSession(next.session_id);
                        else hooks.newSession();
                        return;
                    }
                    hooks.renderSide();
                })
                .catch(function () {
                    if (hooks.state() !== session) return;
                    S.sessBusy = false;
                    S.deletingId = null;
                    hooks.renderSide();
                });
        }

        function cancelDelete() {
            var S = hooks.state();
            if (!S) return;
            S.deletingId = null;
            hooks.renderSide();
        }

        // 侧栏的点击动作自己认(编排层 onClick 只转一次手)。
        function onClick(action, el) {
            var sid = el.getAttribute('data-sid');
            if (action === 'stw-sess-open') hooks.switchSession(sid);
            else if (action === 'stw-sess-rename') startRename(sid);
            else if (action === 'stw-sess-del') askDelete(sid);
            else if (action === 'stw-sess-del-yes') confirmDelete(sid);
            else if (action === 'stw-sess-del-no') cancelDelete();
            else if (action === 'stw-sess-reload') load();
            else return false;
            return true;
        }

        // 改名输入框:Enter 存,Esc 撤。blur 也当撤 —— 误触别处不该把半截标题写上去。
        function onKeydown(e) {
            var S = hooks.state();
            if (!S || !e.target || e.target.id !== 'stwSessRename') return false;
            if (e.key === 'Enter') {
                e.preventDefault();
                commitRename(S.renamingId);
                return true;
            }
            if (e.key === 'Escape') {
                e.preventDefault();
                cancelRename();
                return true;
            }
            return false;
        }

        return {
            load: load,
            refreshBudget: refreshBudget,
            onClick: onClick,
            onKeydown: onKeydown,
            cancelRename: cancelRename,
        };
    }

    var api = { create: create };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.stewardSessions = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
