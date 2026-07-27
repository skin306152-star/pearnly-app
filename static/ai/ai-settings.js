/*
 * Pearnly AI · ai-settings.js · 设置(EN-clients · 侧栏「设置」转正)编排 + HTML 拼装
 *
 * 最薄版(主窗拍板:就三样,不镀金)——语言切换(复用既有 atSetLang/mrpilot_lang 机制,
 * 同 console.js 的 langSeg 先例,视觉复用 .view-toggle/.vt-btn 而非重画一套分段控件)
 * + 当前账号信息(GET /api/me 已有的 email/tenant_name,零新增后端)+ 退出登录
 * (复用 AI.api.logout() + 清 token,回调交给 ai.js,同 AI.gate.mountInvited 的
 * onLogout 先例)。B5 #16 起追加计费区(OCR 余额/三步充值/充值记录),整块下沉
 * AI.billing(ai-billing.js),本页只留一个挂载点。单文件小、编排与拼装未拆
 * (参照 ai-financials.js 同等体量的先例,
 * 未设独立 node 纯函数测试文件——本页无值得单测的业务逻辑,E2E 覆盖交互)。
 *
 * 语言切换后整页 reload(不做局部重渲染):侧栏/多层嵌套视图的文案分散在十余个模块,
 * 局部刷新容易漏掉某个未挂载视图的文案,reload 保证零遗漏——设置页低频操作,
 * reload 的成本可接受(同多数 SaaS 后台的语言切换取舍)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;

    function body() {
        return $('stBody');
    }

    function esc(s) {
        return AI.state.esc(s);
    }

    function langSegHtml() {
        return (
            '<div class="view-toggle" id="stLangSeg">' +
            (window.AII18N.supported || [])
                .map(function (lang) {
                    return (
                        '<button type="button" class="vt-btn' +
                        (lang === window.AII18N.lang ? ' on' : '') +
                        '" data-lang="' +
                        lang +
                        '">' +
                        esc(at('settings_lang_' + lang)) +
                        '</button>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function accountRowHtml(labelKey, value) {
        return (
            '<div class="cell"><div class="lb">' +
            esc(at(labelKey)) +
            '</div><div class="v">' +
            esc(value || '—') +
            '</div></div>'
        );
    }

    function render() {
        var me = S.me;
        body().innerHTML =
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('settings_lang_title')) +
            '</h3></div><div class="bd">' +
            langSegHtml() +
            '</div></div>' +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('settings_account_title')) +
            '</h3></div><div class="bd"><div class="wosum">' +
            accountRowHtml('settings_account_email', me && me.email) +
            accountRowHtml('settings_account_tenant', me && me.tenant_name) +
            '</div></div></div>' +
            '<div id="stBillingWrap"></div>' +
            '<button type="button" class="btn" data-action="settings-logout">' +
            esc(at('settings_logout_btn')) +
            '</button>';
        // 计费区(B5 #16):余额/充值/记录自带四态与轮询,数据编排全在 AI.billing。
        AI.billing.mount(S.api, $('stBillingWrap'));
        applyFocus();
    }

    // 计费区挂载时还是骨架、整页撑不出滚动条,那一刻 scrollIntoView 会被 clamp 成 no-op
    // (同 ai.js restoreScrollAfterPaint 踩过的坑);真数据落下来把页面撑高后没人补滚,
    // 手机上「去充值」就永远停在页顶、充值按钮被折线切掉。故有限重试到真滚到位为止。
    var FOCUS_RETRY_MS = [250, 700, 1500, 3000];

    // 滚到位的判据:block:'center' 成功后元素顶边必在视口中线以上(高元素为负)。
    // 页面不可滚时 top 停在原处(远大于中线)→ 判未到位 → 继续重试。
    function billingCentered(el) {
        return el.getBoundingClientRect().top < window.innerHeight / 2;
    }

    // #/settings?focus=billing:失败态「去充值」深链的落点。滚一次就把 focus 消费掉,
    // 免得之后切语言 reload 又莫名其妙往下跳。
    function applyFocus() {
        if (S.focus !== 'billing') return;
        S.focus = null;
        var session = S;
        var lastY = null;
        var i = 0;
        function attempt() {
            if (S !== session) return; // 已切走(重挂载/登出)
            var el = $('stBillingWrap');
            if (!el || !el.scrollIntoView) return;
            if (lastY !== null && window.scrollY !== lastY) return; // 用户自己滚了,不抢方向盘
            el.scrollIntoView({ block: 'center' });
            lastY = window.scrollY;
            if (billingCentered(el) || i >= FOCUS_RETRY_MS.length) return;
            window.setTimeout(attempt, FOCUS_RETRY_MS[i++]);
        }
        attempt();
    }

    function loadMe() {
        body().innerHTML = AI.state.loadingHtml();
        var session = S;
        S.api
            .getMe()
            .then(function (me) {
                if (S !== session) return;
                S.me = me;
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
                if (btn) btn.onclick = loadMe;
            });
    }

    function switchLang(lang) {
        window.atSetLang(lang);
        window.location.reload();
    }

    function doLogout() {
        S.api
            .logout()
            .catch(function () {
                /* 登出接口失败不阻断本地清态——token 反正要清,服务端会话过期也无妨 */
            })
            .then(function () {
                if (S.onLogout) S.onLogout();
            });
    }

    function onClick(e) {
        var langBtn = e.target.closest('[data-lang]');
        if (langBtn) {
            switchLang(langBtn.getAttribute('data-lang'));
            return;
        }
        if (e.target.closest('[data-action="settings-logout"]')) doLogout();
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        $('v-settings').addEventListener('click', onClick);
    }

    // opts.onLogout 由 ai.js 注入(清 token + 回到登录门面,同 AI.gate.mountInvited 先例)。
    // opts.focus 来自路由 ?focus=(目前只有 'billing')。
    function mount(api, opts) {
        S = {
            api: api,
            me: null,
            focus: (opts && opts.focus) || null,
            onLogout: (opts && opts.onLogout) || null,
        };
        wireOnce();
        loadMe();
    }

    window.AI = window.AI || {};
    window.AI.settings = { mount: mount };
})();
