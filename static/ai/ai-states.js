/*
 * Pearnly AI · ai-states.js · 状态词典 #/states(B1)挂载层
 *
 * 词典页是给人「看状态长什么样」的,所以进度条/环不摆死数——一个演示计时器让百分比
 * 滚动起来,组件的过渡动画(width/conic 随 --p 变)才看得见。步进逻辑 nextDemoPct 是
 * 纯函数(node 单测),挂载层只管计时器的起停:离开路由(v-states 失去 .on)自动停,
 * 系统开了减弱动态(prefers-reduced-motion)则根本不起——与 CSS 层的动画降级同一态度。
 */
(function (root) {
    'use strict';

    // 演示步进:9 的步长走完 0→99 不整除,条/环的中间值更像真实进度;越界回 0 重来。
    function nextDemoPct(p) {
        var n = Number(p);
        if (!isFinite(n) || n < 0) n = 0;
        var next = n + 9;
        return next > 100 ? 0 : next;
    }

    var pure = { nextDemoPct: nextDemoPct };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;
    if (!root || typeof root.document === 'undefined') return;

    var $ = function (id) {
        return root.document.getElementById(id);
    };

    var wired = false;
    var timer = null;
    var demoPct = 64;

    function reducedMotion() {
        return (
            typeof root.matchMedia === 'function' &&
            root.matchMedia('(prefers-reduced-motion: reduce)').matches
        );
    }

    function tick() {
        // 路由已切走(视图失去 .on)就停表,回来时 mount() 重新起——不在后台空转。
        if (!$('v-states').classList.contains('on')) {
            stopTimer();
            return;
        }
        demoPct = nextDemoPct(demoPct);
        $('stsBody')
            .querySelectorAll('[data-demo="pct"]')
            .forEach(function (el) {
                el.style.setProperty('--p', demoPct);
                var num = el.querySelector('b');
                if (num) num.textContent = demoPct + '%';
            });
    }

    function stopTimer() {
        if (timer) {
            root.clearInterval(timer);
            timer = null;
        }
    }

    function onClick(e) {
        var toggle = e.target.closest('[data-action="sts-explain-toggle"]');
        if (toggle) toggle.closest('.st-explain').classList.toggle('on');
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        $('v-states').addEventListener('click', onClick);
    }

    function mount() {
        wireOnce();
        $('stsBody').innerHTML = root.AI.statesRender.pageHtml();
        stopTimer();
        if (!reducedMotion()) timer = root.setInterval(tick, 1800);
    }

    root.AI = root.AI || {};
    root.AI.states = { mount: mount, nextDemoPct: nextDemoPct };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
