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

    // empty/error:图标 + 标题 + 副文案 + 可选重试按钮。titleText/subText 是调用方已翻译好的文案
    // (本文件不依赖 window.at,保持纯 · i18n 由调用方在挂载前解出)。
    function blockHtml(mode, opts) {
        opts = opts || {};
        var cls = mode === 'error' ? 'state-block err' : 'state-block';
        var iconPath =
            mode === 'error'
                ? '<path d="M12 9v4m0 4h.01"/><circle cx="12" cy="12" r="10"/>'
                : '<path d="M3 3v18h18M7 14l4-4 4 4 5-5"/>';
        var retryBtn = opts.retryLabel
            ? '<button class="btn" data-action="retry">' + esc(opts.retryLabel) + '</button>'
            : '';
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

    var api = {
        loadingHtml: loadingHtml,
        emptyHtml: function (opts) {
            return blockHtml('empty', opts);
        },
        errorHtml: function (opts) {
            return blockHtml('error', opts);
        },
        esc: esc,
        optionsHtml: optionsHtml,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.state = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
