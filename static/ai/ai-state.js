/*
 * Pearnly AI · ai-state.js · 四态 UI 的纯 HTML 构造(loading/empty/error/ok 共用外壳)
 *
 * 不碰 DOM,只拼字符串——调用方 innerHTML 挂载。UMD 同 ai-format.js/ai-router.js 先例,
 * 供 tests/unit/test_ai_pure_modules.py 用真 node 跑本文件断言输出结构。
 */
(function (root) {
    'use strict';

    var SKELETON_ROWS = 3;

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }

    // loading:骨架条(无文案·避免闪烁式假状态)
    function loadingHtml() {
        var rows = '';
        for (var i = 0; i < SKELETON_ROWS; i++) {
            rows += '<div class="skel" style="height:56px;margin-bottom:10px"></div>';
        }
        return '<div data-state="loading">' + rows + '</div>';
    }

    // 空态/失败态的「出路」。两种出路各自独立可给:retryLabel 出重试按钮(调用方自己绑
    // data-action="retry" 的点击),actionLabel+actionHref 出一个直接跳过去的链接按钮——
    // 空态点名了去哪就得给按钮,不能让用户读完文案再自己找入口。retryName/actionName 可改写
    // 这两者的 data-action,供调用方挂到已有的点击委托上(如工单页的 wo-retry-stuck),
    // 不必为一个空态再绑一套监听。
    function actionsHtml(opts) {
        var out = opts.retryLabel
            ? '<button type="button" class="btn" data-action="' +
              esc(opts.retryName || 'retry') +
              '">' +
              esc(opts.retryLabel) +
              '</button>'
            : '';
        if (opts.actionLabel && opts.actionHref) {
            out +=
                '<a class="btn pri" href="' +
                esc(opts.actionHref) +
                '"' +
                (opts.actionName ? ' data-action="' + esc(opts.actionName) + '"' : '') +
                '>' +
                esc(opts.actionLabel) +
                '</a>';
        }
        return out;
    }

    // empty/error:图标 + 标题 + 副文案 + 可选出路。titleText/subText 是调用方已翻译好的文案
    // (本文件不依赖 window.at,保持纯 · i18n 由调用方在挂载前解出)。
    function blockHtml(mode, opts) {
        opts = opts || {};
        var cls = mode === 'error' ? 'state-block err' : 'state-block';
        var iconPath =
            mode === 'error'
                ? '<path d="M12 9v4m0 4h.01"/><circle cx="12" cy="12" r="10"/>'
                : '<path d="M3 3v18h18M7 14l4-4 4 4 5-5"/>';
        var retryBtn = actionsHtml(opts);
        return (
            '<div class="' +
            cls +
            '" data-state="' +
            mode +
            '"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke-width="2">' +
            iconPath +
            '</svg></div><div class="t">' +
            esc(opts.title) +
            '</div><div class="s">' +
            esc(opts.sub) +
            '</div>' +
            retryBtn +
            '</div>'
        );
    }

    // 页内小分区(分区标题下的那张清单)为空时的三态壳。与 blockHtml 分工:那个是整块面板
    // 没内容时的居中大方块,这个是面板里某张清单为空时的一行小块,所以不带图标。
    //
    // phase 必须由调用方按真实数据判,不许一律传 empty——「暂无 X」分不清是没跑、没料还是
    // 跑挂了,正是这里要根治的:
    //   idle  还没跑到 / 压根没料  → sub 说怎么开始,配去补料的入口
    //   empty 跑完了确实没有这一类 → sub 说为什么可能是空的(空得有理由,不是出错)
    //   error 这步没跑出来        → 配重试
    var SECTION_PHASES = ['idle', 'empty', 'error'];

    function sectionEmptyHtml(opts) {
        opts = opts || {};
        var phase = SECTION_PHASES.indexOf(opts.phase) >= 0 ? opts.phase : 'empty';
        var acts = actionsHtml(opts);
        return (
            '<div class="sec-empty sec-empty-' +
            phase +
            '" data-state="' +
            phase +
            '"><p class="sec-empty-t">' +
            esc(opts.title) +
            '</p>' +
            (opts.sub ? '<p class="sec-empty-s">' + esc(opts.sub) + '</p>' : '') +
            (acts ? '<p class="sec-empty-a">' + acts + '</p>' : '') +
            '</div>'
        );
    }

    // <option> 列表拼装:values 按传入顺序渲染,selected 命中打 selected,文案由调用方的
    // labelFn(v) 给(可读原始未转义文本,本函数负责 esc)。ai-profile-render.js(三态枚举
    // 字段)/ai-profile-panels-render.js(别名种类/匹配模式下拉)共用同一段循环体。
    function optionsHtml(values, selected, labelFn) {
        return values
            .map(function (v) {
                return (
                    '<option value="' +
                    v +
                    '"' +
                    (v === selected ? ' selected' : '') +
                    '>' +
                    esc(labelFn(v)) +
                    '</option>'
                );
            })
            .join('');
    }

    // 机器码那一行:码是会计转给我们排障用的那串东西,她自己看不懂也用不上 —— 所以它
    // 只以最低存在感出现,同排的复制按钮才是可点的那一半(10.5px 灰字在手机上既选不中
    // 也复制不走)。管家任务卡与异常裁决卡共用这一份,别各拼一套。
    // cls/action 由调用方给(两处各有自己的样式作用域与事件委托前缀),labels 已翻译好。
    function codeChipHtml(opts) {
        opts = opts || {};
        return (
            '<span class="' +
            esc(opts.cls) +
            '"><code>' +
            esc(opts.code) +
            '</code><button type="button" class="btn sm" data-action="' +
            esc(opts.action) +
            '" data-code="' +
            esc(opts.code) +
            '">' +
            esc(opts.copyLabel) +
            '</button></span>'
        );
    }

    var api = {
        loadingHtml: loadingHtml,
        emptyHtml: function (opts) {
            return blockHtml('empty', opts);
        },
        errorHtml: function (opts) {
            return blockHtml('error', opts);
        },
        SECTION_PHASES: SECTION_PHASES,
        sectionEmptyHtml: sectionEmptyHtml,
        esc: esc,
        optionsHtml: optionsHtml,
        codeChipHtml: codeChipHtml,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.state = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
