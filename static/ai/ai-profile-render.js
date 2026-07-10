/*
 * Pearnly AI · ai-profile-render.js · 税务画像表单(B2-e)的纯校验 + HTML 拼装
 *
 * 双导出(同 ai-intake-render.js UMD 先例):FIELD_DEFS/buildProfilePayload 零 DOM 依赖
 * (buildProfilePayload 借道 root.AI.format.parseAmount,node 测试须先 require ai-format.js,
 * 同 ai-intake-render.js 的 parseAmount 先例),node(tests/unit/test_ai_profile_pure.py)
 * 直接 require 断言;HTML 拼装依赖 at()/AI.state,只在浏览器根挂载。别名管理 + 义务清单两块
 * 拆在 ai-profile-panels-render.js(单文件<500 铁律,三块一个文件会破线);真正的挂载/保存
 * 编排在 ai-profile.js,三个 render 文件都排在它之前加载。
 *
 * 字段顺序 1:1 对齐税务画像-方案-B1.md §2.2 字段表(①VAT/SBT ②雇员 ③向个人/法人/境外/
 * 利息股息付款 ④分支 ⑤零申报 ⑥e-filing ⑦Tax Agent ⑧历史留抵)。unknown 值宁多问不静默
 * ——枚举字段当前值为 unknown 时,行上挂一个"未确认"warn 徽标(方案 §2.1 总则)。
 */
(function (root) {
    'use strict';

    // 三组三态枚举共享的取值集合 + 值→i18n key(§2.2 表:多数字段是 yes/no/unknown,
    // sbt_status 是 none/registered/unknown,filing_disposition 是 active/dormant/unknown)。
    var GROUP_OPTIONS = {
        yn: ['yes', 'no', 'unknown'],
        sbt: ['none', 'registered', 'unknown'],
        filing: ['active', 'dormant', 'unknown'],
    };
    var GROUP_VALUE_LABEL_KEY = {
        yn: { yes: 'profile_val_yes', no: 'profile_val_no', unknown: 'profile_val_unknown' },
        sbt: {
            none: 'profile_val_sbt_none',
            registered: 'profile_val_sbt_registered',
            unknown: 'profile_val_unknown',
        },
        filing: {
            active: 'profile_val_filing_active',
            dormant: 'profile_val_filing_dormant',
            unknown: 'profile_val_unknown',
        },
    };

    // 画像字段定义(§2.2 表,不含只读派生字段 vat_status——那行单独渲染)。showIf 按
    // 「当前画像草稿」判定是否展示(渐进展露:分支数/Tax Agent 备案号/SBT 行业只在
    // 相关开关打开时才现身),纯函数、零 DOM。
    var FIELD_DEFS = [
        { key: 'sbt_status', kind: 'enum', group: 'sbt', labelKey: 'profile_field_sbt_status' },
        {
            key: 'sbt_business_type',
            kind: 'text',
            labelKey: 'profile_field_sbt_business_type',
            showIf: function (v) {
                return v.sbt_status !== 'none';
            },
        },
        {
            key: 'has_employees',
            kind: 'enum',
            group: 'yn',
            labelKey: 'profile_field_has_employees',
        },
        {
            key: 'pays_individuals',
            kind: 'enum',
            group: 'yn',
            labelKey: 'profile_field_pays_individuals',
        },
        {
            key: 'pays_juristic',
            kind: 'enum',
            group: 'yn',
            labelKey: 'profile_field_pays_juristic',
        },
        { key: 'pays_foreign', kind: 'enum', group: 'yn', labelKey: 'profile_field_pays_foreign' },
        {
            key: 'pays_interest_dividend',
            kind: 'enum',
            group: 'yn',
            labelKey: 'profile_field_pays_interest_dividend',
        },
        { key: 'has_multi_branch', kind: 'bool', labelKey: 'profile_field_has_multi_branch' },
        {
            key: 'branch_count',
            kind: 'int',
            labelKey: 'profile_field_branch_count',
            showIf: function (v) {
                return !!v.has_multi_branch;
            },
        },
        {
            key: 'filing_disposition',
            kind: 'enum',
            group: 'filing',
            labelKey: 'profile_field_filing_disposition',
        },
        {
            key: 'efiling_enrolled',
            kind: 'enum',
            group: 'yn',
            labelKey: 'profile_field_efiling_enrolled',
        },
        {
            key: 'tax_agent_authorized',
            kind: 'bool',
            labelKey: 'profile_field_tax_agent_authorized',
        },
        {
            key: 'tax_agent_ref',
            kind: 'text',
            labelKey: 'profile_field_tax_agent_ref',
            showIf: function (v) {
                return !!v.tax_agent_authorized;
            },
        },
        { key: 'vat_credit_carry', kind: 'money', labelKey: 'profile_field_vat_credit_carry' },
    ];

    // 触发表单重绘(showIf 需要看最新值)的字段——其余字段改了不影响任何行的显隐,
    // 交给提交时一次性读值即可,不必逐键都重渲染。
    var VISIBILITY_FIELDS = ['sbt_status', 'has_multi_branch', 'tax_agent_authorized'];

    // 画像表单读值(ai-profile.js 从 DOM 收集)→ 校验 + 建 PUT body。分支数/Tax Agent
    // 备案号只在对应开关打开时才校验/发送,历史留抵留空按 0 处理(表单默认就是加载回的
    // 既有画像值,留空视为用户主动清零,不是"从未填过"的 unknown 态)。
    function buildProfilePayload(raw) {
        raw = raw || {};
        var payload = {
            sbt_status: raw.sbt_status,
            sbt_business_type: raw.sbt_business_type || '',
            has_employees: raw.has_employees,
            pays_individuals: raw.pays_individuals,
            pays_juristic: raw.pays_juristic,
            pays_foreign: raw.pays_foreign,
            pays_interest_dividend: raw.pays_interest_dividend,
            has_multi_branch: !!raw.has_multi_branch,
            filing_disposition: raw.filing_disposition,
            efiling_enrolled: raw.efiling_enrolled,
            tax_agent_authorized: !!raw.tax_agent_authorized,
            tax_agent_ref: raw.tax_agent_authorized ? raw.tax_agent_ref || '' : '',
        };
        if (raw.has_multi_branch) {
            var bc = parseInt(raw.branch_count, 10);
            if (!bc || bc < 1) return { ok: false, errKey: 'err_profile_branch_count_invalid' };
            payload.branch_count = bc;
        } else {
            payload.branch_count = 1;
        }
        var vcRaw = raw.vat_credit_carry;
        if (vcRaw == null || String(vcRaw).trim() === '') {
            payload.vat_credit_carry = '0.00';
        } else {
            var vc = root.AI.format.parseAmount(vcRaw, false);
            if (vc === null) return { ok: false, errKey: 'err_profile_vat_credit_invalid' };
            payload.vat_credit_carry = vc;
        }
        return { ok: true, payload: payload };
    }

    var pure = {
        GROUP_OPTIONS: GROUP_OPTIONS,
        GROUP_VALUE_LABEL_KEY: GROUP_VALUE_LABEL_KEY,
        FIELD_DEFS: FIELD_DEFS,
        VISIBILITY_FIELDS: VISIBILITY_FIELDS,
        buildProfilePayload: buildProfilePayload,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    function selectHtml(field, value) {
        var opts = GROUP_OPTIONS[field.group];
        var labelMap = GROUP_VALUE_LABEL_KEY[field.group];
        var optHtml = opts
            .map(function (v) {
                return (
                    '<option value="' +
                    v +
                    '"' +
                    (v === value ? ' selected' : '') +
                    '>' +
                    esc(at(labelMap[v])) +
                    '</option>'
                );
            })
            .join('');
        return (
            '<select class="sf-in" id="pf-' +
            field.key +
            '" name="' +
            field.key +
            '">' +
            optHtml +
            '</select>'
        );
    }

    function fieldControlHtml(field, value) {
        var id = 'pf-' + field.key;
        if (field.kind === 'enum') return selectHtml(field, value);
        if (field.kind === 'bool') {
            return (
                '<input type="checkbox" id="' +
                id +
                '" name="' +
                field.key +
                '"' +
                (value ? ' checked' : '') +
                '>'
            );
        }
        if (field.kind === 'int') {
            return (
                '<input class="sf-in num" type="number" min="1" id="' +
                id +
                '" name="' +
                field.key +
                '" value="' +
                esc(value == null ? '' : value) +
                '">'
            );
        }
        if (field.kind === 'money') {
            return (
                '<input class="sf-in num" inputmode="decimal" id="' +
                id +
                '" name="' +
                field.key +
                '" value="' +
                esc(value == null ? '' : value) +
                '">'
            );
        }
        return (
            '<input class="sf-in" id="' +
            id +
            '" name="' +
            field.key +
            '" maxlength="200" value="' +
            esc(value == null ? '' : value) +
            '">'
        );
    }

    // unknown 值挂"未确认"warn 徽标(宁多问不静默,方案 §2.1)——只有 enum 字段才有
    // unknown 取值,bool/text/money 字段没有这个态。
    function fieldRowHtml(field, profile) {
        var value = profile[field.key];
        var unk = field.kind === 'enum' && value === 'unknown';
        var badge = unk
            ? ' <span class="chip w">' + esc(at('profile_unknown_badge')) + '</span>'
            : '';
        var rowCls = 'sf-row' + (field.kind === 'bool' ? ' sf-row-bool' : '') + (unk ? ' unk' : '');
        return (
            '<div class="' +
            rowCls +
            '"><label class="sf-lb" for="pf-' +
            field.key +
            '">' +
            esc(at(field.labelKey)) +
            badge +
            '</label>' +
            fieldControlHtml(field, value) +
            '</div>'
        );
    }

    // VAT 登记态是只读派生字段(join workspace_clients.vat_registered,画像表不重复存),
    // 展示成状态胶囊,不给可编辑控件——editable 会造出第二份事实源。
    function vatStatusRowHtml(profile) {
        var registered = profile.vat_status === 'registered';
        var key = registered ? 'profile_val_vat_registered' : 'profile_val_vat_unregistered';
        return (
            '<div class="sf-row sf-row-ro"><label class="sf-lb">' +
            esc(at('profile_field_vat_status')) +
            '</label><span class="chip ' +
            (registered ? 's' : 'n') +
            '">' +
            esc(at(key)) +
            '</span></div>'
        );
    }

    function formHtml(ctx) {
        var profile = ctx.profile || {};
        var rows =
            vatStatusRowHtml(profile) +
            FIELD_DEFS.filter(function (f) {
                return !f.showIf || f.showIf(profile);
            })
                .map(function (f) {
                    return fieldRowHtml(f, profile);
                })
                .join('');
        var err = ctx.saveErrKey
            ? '<div class="intake-err">' + esc(at(ctx.saveErrKey)) + '</div>'
            : '';
        var ok =
            !ctx.saveErrKey && ctx.savedFlash
                ? '<div class="profile-ok-note">' + esc(at('profile_saved_ok')) + '</div>'
                : '';
        var btnLabel = ctx.saving ? at('profile_saving') : at('profile_save');
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('profile_title')) +
            '</h3></div><div class="bd"><form id="profileForm" class="profile-form" novalidate>' +
            rows +
            err +
            ok +
            '<div class="sf-btns"><button type="submit" class="btn pri" data-action="profile-save"' +
            (ctx.saving ? ' disabled' : '') +
            '>' +
            esc(btnLabel) +
            '</button></div></form></div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.profileRender = {
        FIELD_DEFS: FIELD_DEFS,
        VISIBILITY_FIELDS: VISIBILITY_FIELDS,
        buildProfilePayload: buildProfilePayload,
        formHtml: formHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
