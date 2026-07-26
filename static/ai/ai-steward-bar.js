/*
 * Pearnly AI · ai-steward-bar.js · 智能管家命令条(收起态 · 工作台矩阵上方常驻)
 *
 * 一行输入 + 四个高频问法 chips。点/回车 → 交给 AI.steward.openWith() 记下这句话并跳
 * #/steward(建会话与送出都在展开态那边收口,命令条不自己发请求)。
 *
 * 闸(pearnly_ai_steward)关时整条不渲染:#stwBar 在 ai.html 里默认 style="display:none"
 * 且内容为空 —— 闸关的 /ai 与今天逐字节一致,不是等探针回来再撤掉一个已经画上去的条
 * (同 navDesk 先例)。探针三态由 ai-steward.js 统一持有,本文件只吃它的结论。
 */
(function () {
    'use strict';

    var wired = false;

    function host() {
        return document.getElementById('stwBar');
    }

    function input() {
        return document.getElementById('stwBarInput');
    }

    function go(text) {
        var t = AI.stewardChatRender.normalizeText(text);
        if (!t) {
            // 空串不跳:光标留在原地,不开一个没话可说的空会话。
            if (input()) input().focus();
            return;
        }
        AI.steward.openWith(t);
    }

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'stw-bar-go') go(input() ? input().value : '');
        else if (a === 'stw-quick') go(el.getAttribute('data-text'));
    }

    function onKeydown(e) {
        if (e.target && e.target.id === 'stwBarInput' && e.key === 'Enter') {
            e.preventDefault();
            go(e.target.value);
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        var el = host();
        el.addEventListener('click', onClick);
        el.addEventListener('keydown', onKeydown);
    }

    // 只吃闸结论:命令条自身不发任何请求(建会话/送出都在展开态),所以不接 api。
    function applyGate(open) {
        var el = host();
        if (!el) return;
        if (!open) {
            el.style.display = 'none';
            el.innerHTML = '';
            return;
        }
        el.style.display = '';
        el.innerHTML = AI.stewardChatRender.barHtml();
        wireOnce();
    }

    window.AI = window.AI || {};
    window.AI.stewardBar = { applyGate: applyGate };
})();
