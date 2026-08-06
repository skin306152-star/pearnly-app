/*
 * Pearnly AI · ai-profile-card-render.js · 税务画像卡 HTML 拼装(依赖 at()/AI.state)
 *
 * 拆自 ai-profile-render.js(那份留纯字段模型/单字段校验,零 DOM,单文件<500 铁律撑不住
 * 两块一起放)。逐字段:值控件 + 来源徽章(官方接口/票据推断/手填/未知)+ 待确认圆点 +
 * 推断依据一句话(带置信度)+ 冲突并排二选一 + SBT 专属"让管家帮你确认"CTA。挂载/保存
 * 编排在 ai-profile.js。画像卡设计稿 v1 是唯一交互规格,逐块对照见交付报告。
 */
(function (root) {
    'use strict';
    if (!root) return;

    var PR = root.AI.profileRender;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    // 来源 → .st-badge 色族(复用 ai-states.css 现成词典,不新造一套色):
    // 官方接口=st-ok(绿)· 票据推断=st-ai(紫)· 手填=st-off(灰)· 未知=st-wait(黄)。
    var SOURCE_CLASS = {
        official: 'st-ok',
        inferred: 'st-ai',
        manual: 'st-off',
        unknown: 'st-wait',
    };
    var SOURCE_LABEL_KEY = {
        official: 'profile_source_official',
        inferred: 'profile_source_inferred',
        manual: 'profile_source_manual',
        unknown: 'profile_source_unknown',
    };

    // 依据文案是机器编码"field:hit|miss:count:period"(后端诚实边界:不写死中文一句话,
    // 4 语产品按当前语言 + 真实笔数/期间现拼——见 services/workorder/profile_inference.py)。
    function evidenceText(code) {
        if (!code) return '';
        var parts = String(code).split(':');
        var key = 'profile_evidence_' + parts[0] + '_' + parts[1];
        var text = at(key);
        if (text === key) return ''; // 未识别编码:不展示半句机器码给会计看
        return text.replace('{count}', parts[2] || '0').replace('{period}', parts[3] || '');
    }

    function enumValueLabel(field, value) {
        var labelMap = PR.GROUP_VALUE_LABEL_KEY[field.group] || {};
        return at(labelMap[value] || 'profile_val_unknown');
    }

    function fieldControlHtml(field, value) {
        var id = 'pf-' + field.key;
        if (field.kind === 'enum') {
            var optHtml = root.AI.state.optionsHtml(
                PR.GROUP_OPTIONS[field.group],
                value,
                function (v) {
                    return enumValueLabel(field, v);
                }
            );
            return (
                '<select class="pf-in" id="' +
                id +
                '" data-field="' +
                field.key +
                '">' +
                optHtml +
                '</select>'
            );
        }
        if (field.kind === 'bool') {
            return (
                '<label class="pf-tgl"><input type="checkbox" id="' +
                id +
                '" data-field="' +
                field.key +
                '" data-bool="1"' +
                (value ? ' checked' : '') +
                '>' +
                esc(at(value ? 'profile_val_yes' : 'profile_val_no')) +
                '</label>'
            );
        }
        if (field.kind === 'int') {
            return (
                '<input class="pf-in num" type="number" min="1" id="' +
                id +
                '" data-field="' +
                field.key +
                '" value="' +
                esc(value == null ? '' : value) +
                '">'
            );
        }
        if (field.kind === 'money') {
            return (
                '<input class="pf-in num" inputmode="decimal" id="' +
                id +
                '" data-field="' +
                field.key +
                '" value="' +
                esc(value == null ? '' : value) +
                '">'
            );
        }
        return (
            '<input class="pf-in" id="' +
            id +
            '" data-field="' +
            field.key +
            '" maxlength="200" value="' +
            esc(value == null ? '' : value) +
            '">'
        );
    }

    function badgeHtml(source) {
        return (
            '<span class="st-badge ' +
            (SOURCE_CLASS[source] || 'st-wait') +
            '">' +
            esc(at(SOURCE_LABEL_KEY[source] || 'profile_source_unknown')) +
            '</span>'
        );
    }

    function dotHtml(status) {
        if (status === 'confirmed')
            return (
                '<span class="pf-ok" title="' +
                esc(at('profile_status_confirmed')) +
                '">&#10003;</span>'
            );
        if (status === 'pending')
            return (
                '<span class="pf-dot pending" title="' +
                esc(at('profile_status_pending')) +
                '"></span>'
            );
        if (status === 'blocked')
            return (
                '<span class="pf-dot blocked" title="' +
                esc(at('profile_status_blocked')) +
                '"></span>'
            );
        return '';
    }

    function reasonHtml(status, meta) {
        var proposal = meta && meta.proposal;
        if ((status === 'pending' || status === 'conflict') && proposal) {
            var conf = proposal.confidence
                ? ' · ' +
                  esc(at('profile_confidence_label')) +
                  esc(at('profile_confidence_' + proposal.confidence))
                : '';
            return (
                '<div class="pf-reason"><b>' +
                esc(at('profile_reason_label')) +
                '</b>' +
                esc(evidenceText(proposal.evidence)) +
                conf +
                '</div>'
            );
        }
        if (meta && meta.source === 'inferred' && meta.evidence) {
            return (
                '<div class="pf-reason"><b>' +
                esc(at('profile_reason_label')) +
                '</b>' +
                esc(evidenceText(meta.evidence)) +
                '</div>'
            );
        }
        if (status === 'unknown') {
            return '<div class="pf-note">' + esc(at('profile_note_no_source')) + '</div>';
        }
        return '';
    }

    function conflictHtml(field, value, meta) {
        var proposal = meta.proposal;
        return (
            '<div class="pf-conflict"><div class="pf-conflict-ttl">' +
            esc(at('profile_conflict_title')) +
            '</div>' +
            '<div class="pf-conflict-opt" data-conflict-keep="' +
            field.key +
            '">' +
            '<div class="pf-conflict-desc">' +
            esc(at('profile_conflict_manual_label')) +
            '<b>' +
            esc(enumValueLabel(field, value)) +
            '</b></div>' +
            badgeHtml('manual') +
            '</div>' +
            '<div class="pf-conflict-opt" data-conflict-accept="' +
            field.key +
            '">' +
            '<div class="pf-conflict-desc">' +
            esc(at('profile_conflict_inferred_label')) +
            '<b>' +
            esc(enumValueLabel(field, proposal.value)) +
            '</b>' +
            '<small>' +
            esc(evidenceText(proposal.evidence)) +
            '</small></div>' +
            badgeHtml('inferred') +
            '</div></div>'
        );
    }

    // SBT 专属:没有官方数据源确认过 → 让管家帮你确认(要一张 ภ.พ.20),画像卡设计稿 v1
    // 唯一一处挂 AI.steward.openWith 的入口(挂载编排在 ai-profile.js)。
    function missingCtaHtml(status) {
        if (status !== 'blocked') return '';
        return (
            '<div class="pf-cta"><div class="pf-cta-txt">' +
            esc(at('profile_sbt_cta_txt')) +
            '</div>' +
            '<button type="button" class="btn sm" data-open-steward="1">' +
            esc(at('profile_sbt_cta_btn')) +
            '</button></div>'
        );
    }

    function fieldRowHtml(field, profile) {
        if (!PR.isApplicable(field, profile)) return '';
        var value = profile[field.key];
        var fieldMeta = profile.field_meta || {};
        var meta = fieldMeta[field.key] || null;
        var status = PR.deriveFieldStatus(field, value, meta);
        var source = PR.deriveSourceBadge(status, meta);
        var rowCls =
            'pf-row' +
            (status === 'blocked' ? ' blocked' : '') +
            (status === 'conflict' ? ' conflict' : '');
        var control =
            status === 'conflict'
                ? ''
                : '<div class="pf-control">' + fieldControlHtml(field, value) + '</div>';
        var actions =
            status === 'pending'
                ? '<div class="pf-actions"><button type="button" class="btn sm pri" data-confirm="' +
                  field.key +
                  '">' +
                  esc(at('profile_confirm_btn')) +
                  '</button></div>'
                : '';
        return (
            '<div class="' +
            rowCls +
            '">' +
            '<div class="pf-head"><span class="pf-label">' +
            esc(at(field.labelKey)) +
            '</span>' +
            '<span class="pf-badges">' +
            badgeHtml(source) +
            dotHtml(status) +
            '</span></div>' +
            control +
            reasonHtml(status, meta) +
            (status === 'conflict' ? conflictHtml(field, value, meta) : '') +
            missingCtaHtml(status) +
            actions +
            '</div>'
        );
    }

    function readonlyRowHtml(labelKey, valueText) {
        return (
            '<div class="pf-row readonly"><div class="pf-head"><span class="pf-label">' +
            esc(at(labelKey)) +
            '</span>' +
            '<span class="pf-badges">' +
            badgeHtml('official') +
            '</span></div>' +
            '<div class="pf-control"><span class="chip s">' +
            esc(valueText) +
            '</span></div></div>'
        );
    }

    function countPending(profile) {
        var n = 0;
        PR.FIELD_META.forEach(function (m) {
            if (!PR.isApplicable(m, profile)) return;
            var meta = (profile.field_meta || {})[m.key] || null;
            var status = PR.deriveFieldStatus(m, profile[m.key], meta);
            if (status === 'pending' || status === 'conflict') n++;
        });
        return n;
    }

    function summaryHtml(ctx) {
        var profile = ctx.profile || {};
        var pct = Math.round((ctx.completeness || 0) * 100);
        var pendingCount = countPending(profile);
        var actionHtml = pendingCount
            ? '<button type="button" class="btn pri" data-action="profile-confirm-all">' +
              esc(at('profile_confirm_all_btn').replace('{n}', String(pendingCount))) +
              '</button>'
            : '';
        var err = ctx.saveErrKey
            ? '<div class="intake-err">' + esc(at(ctx.saveErrKey)) + '</div>'
            : '';
        return (
            '<div class="pf-summary-row"><div><h3>' +
            esc(at('profile_title')) +
            '</h3>' +
            '<div class="pf-sub">' +
            esc(at('profile_sub')) +
            '</div></div>' +
            actionHtml +
            '</div>' +
            '<div class="pf-progress-line"><span class="st-bar ' +
            (pct >= 100 ? 'st-ok' : 'st-run') +
            '" style="--p:' +
            pct +
            '"><i></i></span>' +
            '<span class="pf-pct' +
            (pct >= 100 ? ' full' : '') +
            '">' +
            pct +
            '%</span></div>' +
            err
        );
    }

    function groupsHtml(profile) {
        var out = '';
        PR.GROUPS.forEach(function (g) {
            var rows = PR.FIELD_META.filter(function (m) {
                return m.groupKey === g.key;
            })
                .map(function (m) {
                    return fieldRowHtml(m, profile);
                })
                .join('');
            if (rows) out += '<div class="pf-grp-title">' + esc(at(g.titleKey)) + '</div>' + rows;
        });
        return out;
    }

    function cardHtml(ctx) {
        var profile = ctx.profile || {};
        var registered = profile.vat_status === 'registered';
        var body =
            readonlyRowHtml(
                'profile_field_vat_status',
                at(registered ? 'profile_val_vat_registered' : 'profile_val_vat_unregistered')
            ) +
            readonlyRowHtml('profile_field_branch', profile.branch || '') +
            groupsHtml(profile);
        return (
            '<div class="panel pf-card"><div class="hd">' +
            summaryHtml(ctx) +
            '</div><div class="bd">' +
            body +
            '</div></div>'
        );
    }

    root.AI.profileCardRender = { cardHtml: cardHtml, evidenceText: evidenceText };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
