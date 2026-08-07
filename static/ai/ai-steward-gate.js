/*
 * Pearnly AI · ai-steward-gate.js · 闸探针与路由收口(S1 · 拆自 ai-steward.js)
 *
 * B2-M1 语义原样保留:闸(pearnly_ai_steward · tenant 级默认关 · fail-closed)三态、
 * 闸关 = 侧栏项不显示 + #/steward 落回工作台、探针 401 走整站唯一的过期出口。
 * openWith(text) 供外部入口(画像卡 CTA · 见 ai-profile.js)记下第一句话再跳
 * #/steward,展开态建好会话立刻替用户送出。会话页满高靠 body 上的 stw-chat-mode 类,
 * 进出路由时在这里挂/摘(ai-steward-chat.css 消费)。
 *
 * hooks 契约:
 *   mount(api)        挂载会话页(编排层)
 *   stopWatchers()    离开本页时停 SSE/轮询/倒计时
 *   setPending(text)  记下 openWith 带来的第一句话(建好会话后由编排层送出)
 *   setLimits(raw)    探针带回的上传限额(单一事实源)
 *   getEl(id)         → element|null
 */
(function (root) {
    'use strict';

    function create(hooks) {
        var gateOpen = null; // null = 探针在途 / true / false

        function setChatMode(on) {
            root.document.body.classList.toggle('stw-chat-mode', !!on);
        }

        // 外部入口交棒(画像卡 CTA):记下第一句话再跳,展开态建好会话立刻替用户送出。
        function openWith(text) {
            hooks.setPending(AI.stewardChatRender.normalizeText(text) || null);
            root.location.hash = AI.router.buildStewardHash();
        }

        function applyGate(api, open) {
            gateOpen = open;
            hooks.getEl('navSteward').style.display = open ? '' : 'none';
            var current = AI.router.parseHash(root.location.hash);
            if (current.name !== 'steward') return;
            if (!open) {
                setChatMode(false);
                root.location.hash = AI.router.buildDashboardHash();
                return;
            }
            hooks.getEl('v-steward').classList.add('on');
            setChatMode(true);
            hooks.mount(api);
        }

        // 探针不阻塞首屏;失败 fail-closed(闸关待遇)。401 例外:会话过期不是"功能没开",
        // 走整站唯一的过期出口(ai.js 的 expireSession),文案沿用 intake_err_session。
        function probe(api) {
            gateOpen = null;
            api.getStewardStatus()
                .then(function (resp) {
                    hooks.setLimits(resp && resp.attachments);
                    applyGate(api, resp && resp.enabled === true);
                })
                .catch(function (err) {
                    if (err && err.status === 401) {
                        AI.expireSession('intake_err_session');
                        return;
                    }
                    applyGate(api, false);
                });
        }

        // 每条路由都调:不是管家页时关视图 + 停监听;是管家页则收口挂载/回落,
        // 返回 true 告诉 ai.js「这条路由归我了」。
        function onRoute(api, route) {
            var mine = route.name === 'steward';
            hooks.getEl('navSteward').classList.toggle('on', mine);
            hooks.getEl('v-steward').classList.toggle('on', mine && gateOpen !== false);
            if (!mine) {
                hooks.stopWatchers();
                setChatMode(false);
                return false;
            }
            if (gateOpen === false) {
                root.location.hash = AI.router.buildDashboardHash();
                return true;
            }
            // 探针在途先亮加载骨架 —— 深链/刷新落在本页时不能白屏。
            setChatMode(true);
            if (gateOpen === null) hooks.getEl('stwBody').innerHTML = AI.state.loadingHtml();
            else hooks.mount(api);
            return true;
        }

        return { probe: probe, onRoute: onRoute, openWith: openWith, applyGate: applyGate };
    }

    var api = { create: create };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.stewardGate = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
