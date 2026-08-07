/*
 * Pearnly AI · ai-side-toggle.js · 左侧主菜单折叠(2026-08-07,拆自 ai.js · 单文件<500 铁律)
 *
 * #sideToggle 是 ai.html 里的静态元素,不随登录/门面切换重画(同 sidebar-nav.ts 先例:
 * bundle 走 <script defer>,执行时 DOM 已解析完)——持久化态与点击接线都在脚本加载期
 * 一次性做完,不必像 navSteward 那批按钮一样等 chromeWired 在 enterApp() 里再接。
 */
(function (root) {
    'use strict';

    var KEY = 'mrpilot_ai_side_collapsed';
    var btn = root.document.getElementById('sideToggle');

    if (root.localStorage && root.localStorage.getItem(KEY) === '1') {
        root.document.body.classList.add('side-collapsed');
    }

    // aria-label 现取(i18n 词典是同步 <script> 先于本 bundle 加载,at() 此刻已就绪),
    // 没走 ai.js 的通用 data-at-* 机制——全站独一份 aria-label 消费者,不值得为它
    // 开一条新的通用约定。
    if (btn) {
        btn.setAttribute('aria-label', at('side_toggle_aria'));
        btn.addEventListener('click', function () {
            var collapsed = root.document.body.classList.toggle('side-collapsed');
            try {
                root.localStorage.setItem(KEY, collapsed ? '1' : '0');
            } catch (e) {
                // 隐私模式等 localStorage 不可用:折叠本身仍生效,只是不跨次记住。
            }
        });
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
