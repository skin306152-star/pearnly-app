/*
 * Pearnly AI · ai-profile-panels-render.js · 别名管理 + 当期义务清单(B2-e)纯校验 + HTML 拼装
 *
 * 拆自 ai-profile-render.js(三块——画像表单/别名/义务清单——挤一个文件会破单文件<500 铁律,
 * 画像表单留在原文件,这里收别名 + 义务两块结构较简的列表面板)。双导出同 ai-profile-render.js
 * 先例:validateAliasRaw 零 DOM 依赖,node(tests/unit/test_ai_profile_pure.py)直接 require;
 * HTML 拼装依赖 at()/AI.state,只在浏览器根挂载。编排在 ai-profile.js。
 *
 * 别名污染五闸(唯一/长度/泛词/来源分级/冲突)全在后端 client_alias_store,这里不重抄一份
 * 校验——前端只挡"非空",真正拒绝原因走 AliasError.code → mapApiErrorKey 四语透传。
 * 义务状态口径见 obligation_engine.py(due/tentative/data_triggered/nil/conflict),
 * 不做矩阵(B2-e 拍板范围·矩阵归批次 C4),只列当期这一份。
 */
(function (root) {
    'use strict';

    var ALIAS_KINDS = [
        'trade_en',
        'trade_th',
        'brand',
        'storefront',
        'romanized',
        'abbrev',
        'misc',
    ];
    var MATCH_MODES = ['exact', 'substring'];

    var OB_STATUS_CHIP = { due: 'w', tentative: 'n', data_triggered: 'a', nil: 's', conflict: 'b' };
    var OB_STATUS_KEY = {
        due: 'ob_status_due',
        tentative: 'ob_status_tentative',
        data_triggered: 'ob_status_data_triggered',
        nil: 'ob_status_nil',
        conflict: 'ob_status_conflict',
    };

    // 别名输入的最小前端校验(非空)。真正的长度/泛词/唯一性闸在后端(client_alias_store
    // 五道污染闸),前端不重抄一份泰文归一逻辑。
    function validateAliasRaw(raw) {
        var v = String(raw == null ? '' : raw).trim();
        if (!v) return { ok: false, errKey: 'err_alias_required' };
        return { ok: true, value: v };
    }

    var pure = {
        ALIAS_KINDS: ALIAS_KINDS,
        MATCH_MODES: MATCH_MODES,
        OB_STATUS_CHIP: OB_STATUS_CHIP,
        OB_STATUS_KEY: OB_STATUS_KEY,
        validateAliasRaw: validateAliasRaw,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    function aliasKindLabel(kind) {
        return at('alias_kind_' + (ALIAS_KINDS.indexOf(kind) >= 0 ? kind : 'misc'));
    }
    function aliasModeLabel(mode) {
        return at('alias_mode_' + (mode === 'substring' ? 'substring' : 'exact'));
    }

    function aliasRowHtml(alias, deactivatingId) {
        var busy = deactivatingId === alias.id;
        // ai_suggested/data_inferred 别名走影子(方案 §4.6 闸3):列出但标"尚未确认",
        // 不假装它已经在锚方向——只有 human_confirmed 才真正被 sort._direction_by_name 消费。
        var shadow =
            alias.source !== 'human_confirmed'
                ? ' <span class="chip w">' + esc(at('alias_source_shadow')) + '</span>'
                : '';
        return (
            '<div class="alias-row"><div class="alias-main"><b>' +
            esc(alias.alias_raw) +
            '</b>' +
            shadow +
            '<small>' +
            esc(aliasKindLabel(alias.alias_kind)) +
            ' · ' +
            esc(aliasModeLabel(alias.match_mode)) +
            '</small></div>' +
            '<button type="button" class="btn sm" data-action="alias-deactivate" data-id="' +
            alias.id +
            '"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(busy ? at('alias_deactivate_busy') : at('alias_deactivate_btn')) +
            '</button></div>'
        );
    }

    function aliasListHtml(aliases, deactivatingId) {
        if (!aliases || !aliases.length) {
            return '<div class="alias-empty">' + esc(at('alias_empty_s')) + '</div>';
        }
        return (
            '<div class="alias-list">' +
            aliases
                .map(function (a) {
                    return aliasRowHtml(a, deactivatingId);
                })
                .join('') +
            '</div>'
        );
    }

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

    function aliasFormHtml(ctx) {
        var err = ctx.aliasErrKey
            ? '<div class="intake-err">' + esc(at(ctx.aliasErrKey)) + '</div>'
            : '';
        var btnLabel = ctx.aliasSubmitting ? at('alias_add_btn_busy') : at('alias_add_btn');
        return (
            '<form id="aliasForm" class="alias-form" novalidate>' +
            '<input class="sf-in" id="aliasRaw" name="alias_raw" maxlength="200" placeholder="' +
            esc(at('alias_add_ph')) +
            '" value="' +
            esc(ctx.aliasRawValue || '') +
            '">' +
            '<select class="sf-in" id="aliasKind" name="alias_kind">' +
            optionsHtml(ALIAS_KINDS, ctx.aliasKindValue || 'misc', aliasKindLabel) +
            '</select>' +
            '<select class="sf-in" id="aliasMode" name="match_mode">' +
            optionsHtml(MATCH_MODES, ctx.aliasModeValue || 'exact', aliasModeLabel) +
            '</select>' +
            '<button type="submit" class="btn pri" data-action="alias-add"' +
            (ctx.aliasSubmitting ? ' disabled' : '') +
            '>' +
            esc(btnLabel) +
            '</button>' +
            err +
            '</form>'
        );
    }

    function aliasPanelHtml(ctx) {
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('alias_title')) +
            '</h3></div><div class="bd">' +
            aliasListHtml(ctx.aliases, ctx.deactivatingId) +
            aliasFormHtml(ctx) +
            '</div></div>'
        );
    }

    function obligationNameHtml(row) {
        var names = row.display_names || {};
        var lang = (root.AII18N && root.AII18N.lang) || 'zh';
        return esc(names[lang] || names.zh || row.obligation_code);
    }

    function obligationRowHtml(row) {
        var cls = OB_STATUS_CHIP[row.status] || 'n';
        var key = OB_STATUS_KEY[row.status];
        var chip = '<span class="chip ' + cls + '">' + esc(key ? at(key) : row.status) + '</span>';
        var due = row.due_efiling || row.due_paper;
        return (
            '<div class="ob-row"><div class="ob-name">' +
            obligationNameHtml(row) +
            '</div>' +
            chip +
            '<div class="ob-due">' +
            (due ? esc(due) : '—') +
            '</div></div>'
        );
    }

    function obligationsPanelHtml(ctx) {
        var rows = (ctx.obligations && ctx.obligations.rows) || [];
        var body = rows.length
            ? rows.map(obligationRowHtml).join('')
            : '<div class="alias-empty">' + esc(at('obligations_empty_s')) + '</div>';
        var period = (ctx.obligations && ctx.obligations.period) || '';
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('obligations_title')) +
            ' <span class="note">' +
            esc(at('obligations_period_label')) +
            ' ' +
            esc(period) +
            '</span></h3></div><div class="bd">' +
            body +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.profilePanelsRender = {
        ALIAS_KINDS: ALIAS_KINDS,
        MATCH_MODES: MATCH_MODES,
        validateAliasRaw: validateAliasRaw,
        aliasPanelHtml: aliasPanelHtml,
        obligationsPanelHtml: obligationsPanelHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
