/*
 * Pearnly AI · ai-shadow-render.js · 影子底稿(F3)三件套 + GL 对平只读视图纯逻辑 + HTML 拼装
 *
 * 上半段(groupEntriesBySource/trialBalanceState/glReconState)零 DOM/零 i18n 依赖,node
 * (tests/unit/test_ai_shadow_pure.py)直接 require 断言;下半段依赖 at()/AI.state/AI.format,
 * 只在浏览器根挂载——同 ai-recon-render.js 的双段先例。
 *
 * 数据源:services/workorder/api.py::order_detail 的 shadow_draft 字段,原样透传
 * services/accounting/workorder_shadow_adapter.py::ShadowResult.as_gate_payload +
 * services/accounting/shadow_gl_recon.py::GlReconResult.as_payload(挂在 reconcile_gl 键)——
 * 本文件只读不改其形状,复式规则引擎(rules.py)一行不碰。
 */
(function (root) {
    'use strict';

    // 建议分录按来源(source,一次 rules.build 调用产出的一组配平分录)分组,配对
    // sources[] 里同 label 的 rule_key/human_note——entries 逐行只带 memo,不带 human_note,
    // 分组头一次性展示"这组为什么这样记",贴近真实记账凭证(一凭证多分录行)的心智模型。
    // sources 里没有对应分组(理论不该发生)时仍按 entry.source 兜底建组,不丢分录。
    function groupEntriesBySource(entries, sources) {
        var bySrc = {};
        var order = [];
        (sources || []).forEach(function (s) {
            bySrc[s.label] = {
                label: s.label,
                rule_key: s.rule_key,
                human_note: s.human_note,
                rows: [],
            };
            order.push(s.label);
        });
        (entries || []).forEach(function (e) {
            var g = bySrc[e.source];
            if (!g) {
                g = bySrc[e.source] = {
                    label: e.source,
                    rule_key: e.rule_key,
                    human_note: null,
                    rows: [],
                };
                order.push(e.source);
            }
            g.rows.push(e);
        });
        return order.map(function (label) {
            return bySrc[label];
        });
    }

    // 试算平衡 → 胶囊态(cls 沿用全局 .chip 色族:g=配平/w=有差异)。trial_balance 缺失
    // 理论不该发生(api.py::_shadow_draft 已把没有该键的残影过滤成 null)——仍不假装平。
    function trialBalanceState(tb) {
        tb = tb || {};
        return tb.balanced
            ? { cls: 'g', key: 'shadow_balanced_chip' }
            : { cls: 'w', key: 'shadow_unbalanced_chip' };
    }

    // GL 对平结果 → 胶囊态。四态诚实:no_gl_source 不冒充平/不平,用中性色 + 专属文案;
    // 未知 status(如 _run_shadow_gl_recon 自身异常落的 reconcile_gl_skipped)一律中性色,
    // 不替一个没见过的态编一句好听话(raw 原样带出,呈现层决定怎么兜底显示)。
    // no_gl_source 胶囊用短标签(shadow_gl_no_source_chip),完整诚实说明句留给正文
    // (glBodyHtml 的 shadow_gl_no_source)——两处文案不同字符串,避免同一句话在折叠头
    // 与正文重复出现两遍(also 撞 Playwright getByText 严格模式)。
    var _GL_STATE = {
        reconciled: { cls: 'g', key: 'shadow_gl_reconciled' },
        mismatch: { cls: 'w', key: 'shadow_gl_mismatch' },
        partial: { cls: 'n', key: 'shadow_gl_partial' },
        no_gl_source: { cls: 'n', key: 'shadow_gl_no_source_chip' },
    };
    function glReconState(reconcileGl) {
        var status = (reconcileGl || {}).status;
        return _GL_STATE[status] || { cls: 'n', key: null, raw: status };
    }

    var pure = {
        groupEntriesBySource: groupEntriesBySource,
        trialBalanceState: trialBalanceState,
        glReconState: glReconState,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.format,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }
    function money(v) {
        return v == null || v === '' ? '—' : root.AI.format.money(v);
    }
    function drCrLabel(dc) {
        return dc === 'credit' ? at('shadow_cr') : at('shadow_dr');
    }

    // ============ 折叠区壳(三分区共用:entries/accounts/gl)============

    function foldSectionHtml(kind, headerHtml, open, bodyHtml) {
        return (
            '<div class="sdw-section' +
            (open ? ' on' : '') +
            '" data-sdw-kind="' +
            kind +
            '">' +
            '<button type="button" class="sdw-fold" data-action="sdw-fold" data-kind="' +
            kind +
            '">' +
            headerHtml +
            '<span class="sdw-caret">' +
            (open ? esc(at('brx_collapse')) : esc(at('brx_expand'))) +
            '</span>' +
            '</button>' +
            '<div class="sdw-body">' +
            bodyHtml +
            '</div>' +
            '</div>'
        );
    }

    // ============ 建议分录(按凭证分组)============

    function voucherRowHtml(e) {
        return (
            '<tr><td>' +
            esc(drCrLabel(e.dr_cr)) +
            '</td><td>' +
            esc(e.account_code) +
            ' ' +
            esc(e.account_name) +
            '</td><td class="num">' +
            money(e.amount) +
            '</td><td>' +
            esc(e.memo || '—') +
            '</td></tr>'
        );
    }

    function voucherGroupHtml(g) {
        var rows = g.rows.map(voucherRowHtml).join('');
        return (
            '<div class="sdw-voucher">' +
            '<div class="sdw-vh"><b>' +
            esc(g.label) +
            '</b>' +
            (g.rule_key ? '<span class="chip s">' + esc(g.rule_key) + '</span>' : '') +
            '</div>' +
            (g.human_note ? '<p class="sdw-note">' + esc(g.human_note) + '</p>' : '') +
            '<div class="sdw-scroll"><table class="sdw-table"><thead><tr>' +
            '<th>' +
            esc(at('shadow_col_dircr')) +
            '</th><th>' +
            esc(at('shadow_col_account')) +
            '</th><th>' +
            esc(at('shadow_col_amount')) +
            '</th><th>' +
            esc(at('shadow_col_note')) +
            '</th></tr></thead><tbody>' +
            rows +
            '</tbody></table></div></div>'
        );
    }

    function entriesSectionHtml(entries, sources, open) {
        var n = (entries || []).length;
        var header = '<span>' + esc(at('shadow_entries_title', { n: n })) + '</span>';
        var body =
            n === 0
                ? '<p class="sdw-empty">' + esc(at('shadow_entries_empty')) + '</p>'
                : groupEntriesBySource(entries, sources).map(voucherGroupHtml).join('');
        return foldSectionHtml('entries', header, open, body);
    }

    // ============ 科目余额 ============

    function accountRowHtml(a) {
        return (
            '<tr><td>' +
            esc(a.code) +
            '</td><td>' +
            esc(a.name) +
            '</td><td class="num">' +
            money(a.debit) +
            '</td><td class="num">' +
            money(a.credit) +
            '</td><td class="num">' +
            money(a.balance) +
            '</td></tr>'
        );
    }

    function accountsSectionHtml(accounts, open) {
        accounts = accounts || [];
        var header =
            '<span>' + esc(at('shadow_accounts_title', { n: accounts.length })) + '</span>';
        var body =
            accounts.length === 0
                ? '<p class="sdw-empty">' + esc(at('shadow_accounts_empty')) + '</p>'
                : '<div class="mx-scroll"><table class="mx-table"><thead><tr>' +
                  '<th>' +
                  esc(at('shadow_col_code')) +
                  '</th><th>' +
                  esc(at('shadow_col_name')) +
                  '</th><th>' +
                  esc(at('shadow_col_debit')) +
                  '</th><th>' +
                  esc(at('shadow_col_credit')) +
                  '</th><th>' +
                  esc(at('shadow_col_balance')) +
                  '</th></tr></thead><tbody>' +
                  accounts.map(accountRowHtml).join('') +
                  '</tbody></table></div>';
        return foldSectionHtml('accounts', header, open, body);
    }

    // ============ GL 对平(F2)============

    function glMismatchRowHtml(r) {
        return (
            '<tr><td>' +
            esc(r.local_code) +
            (r.erp_code ? ' → ' + esc(r.erp_code) : '') +
            '</td><td class="num">' +
            money(r.shadow_debit) +
            '</td><td class="num">' +
            money(r.shadow_credit) +
            '</td><td class="num">' +
            money(r.gl_debit) +
            '</td><td class="num">' +
            money(r.gl_credit) +
            '</td><td class="num">' +
            money(r.debit_diff) +
            '</td><td class="num">' +
            money(r.credit_diff) +
            '</td></tr>'
        );
    }

    function glMismatchTableHtml(rows, titleKey) {
        if (!rows.length) return '';
        return (
            '<p class="sdw-subtitle">' +
            esc(at(titleKey, { n: rows.length })) +
            '</p>' +
            '<div class="sdw-scroll"><table class="sdw-table"><thead><tr>' +
            '<th>' +
            esc(at('shadow_col_account')) +
            '</th><th>' +
            esc(at('shadow_col_shadow_debit')) +
            '</th><th>' +
            esc(at('shadow_col_shadow_credit')) +
            '</th><th>' +
            esc(at('shadow_col_gl_debit')) +
            '</th><th>' +
            esc(at('shadow_col_gl_credit')) +
            '</th><th>' +
            esc(at('shadow_col_debit_diff')) +
            '</th><th>' +
            esc(at('shadow_col_credit_diff')) +
            '</th></tr></thead><tbody>' +
            rows.map(glMismatchRowHtml).join('') +
            '</tbody></table></div>'
        );
    }

    function glGapRowHtml(r) {
        return (
            '<tr><td>' +
            esc(r.local_code || r.erp_code) +
            '</td><td class="num">' +
            money(r.shadow_debit != null ? r.shadow_debit : r.gl_debit) +
            '</td><td class="num">' +
            money(r.shadow_credit != null ? r.shadow_credit : r.gl_credit) +
            '</td></tr>'
        );
    }

    function glGapTableHtml(rows, titleKey) {
        if (!rows.length) return '';
        return (
            '<p class="sdw-subtitle">' +
            esc(at(titleKey, { n: rows.length })) +
            '</p>' +
            '<div class="sdw-scroll"><table class="sdw-table"><thead><tr>' +
            '<th>' +
            esc(at('shadow_col_account')) +
            '</th><th>' +
            esc(at('shadow_col_shadow_debit')) +
            '</th><th>' +
            esc(at('shadow_col_shadow_credit')) +
            '</th></tr></thead><tbody>' +
            rows.map(glGapRowHtml).join('') +
            '</tbody></table></div>'
        );
    }

    // no_gl_source(未上传对账单)诚实降级:不拼假对平数字,只说明原因;其余状态按
    // 总额小计 + mismatch/unmapped/gl_only 三张子清单展开(mismatch 才是真报警,后两者
    // 是覆盖缺口不是报警,视觉上不用警示色堆叠)。未知 status 一律诚实兜底不臆造内容。
    function glBodyHtml(reconcileGl) {
        var g = reconcileGl || {};
        if (!g.status || g.status === 'no_gl_source') {
            return '<p class="sdw-note">' + esc(at('shadow_gl_no_source')) + '</p>';
        }
        var state = glReconState(g);
        if (!state.key) {
            return '<p class="sdw-note">' + esc(g.status) + '</p>';
        }
        var totals = g.totals || {};
        var totalsNote =
            '<p class="sdw-note">' +
            esc(
                at('shadow_gl_totals_note', {
                    sdebit: money(totals.shadow_debit),
                    scredit: money(totals.shadow_credit),
                    gdebit: money(totals.gl_debit),
                    gcredit: money(totals.gl_credit),
                })
            ) +
            '</p>';
        return (
            totalsNote +
            glMismatchTableHtml(g.mismatch || [], 'shadow_gl_mismatch_title') +
            glGapTableHtml(g.unmapped || [], 'shadow_gl_unmapped_title') +
            glGapTableHtml(g.gl_only || [], 'shadow_gl_only_title')
        );
    }

    function glSectionHtml(reconcileGl, open) {
        var g = reconcileGl || {};
        var state = glReconState(g);
        var chipLabel = state.key ? at(state.key) : g.status || '—';
        var header =
            '<span>' +
            esc(at('shadow_gl_title')) +
            '</span><span class="chip ' +
            state.cls +
            '">' +
            esc(chipLabel) +
            '</span>';
        return foldSectionHtml('gl', header, open, glBodyHtml(g));
    }

    // ============ 顶层组装 ============

    // ui: {open:{entries, accounts, gl}}(ai-shadow.js 持有的折叠态)。
    function pageHtml(shadowDraft, ui) {
        if (!shadowDraft) {
            return (
                '<div class="panel"><div class="hd"><h3>' +
                esc(at('shadow_title')) +
                '</h3></div><div class="bd">' +
                root.AI.state.emptyHtml({
                    title: at('shadow_disabled_t'),
                    sub: at('shadow_disabled_s'),
                }) +
                '</div></div>'
            );
        }
        var tb = shadowDraft.trial_balance || {};
        var tbState = trialBalanceState(tb);
        var uncertainties = shadowDraft.uncertainties || [];
        var hint =
            uncertainties.indexOf('category_unmapped') >= 0
                ? '<p class="sdw-hint">' + esc(at('shadow_uncertainty_category_unmapped')) + '</p>'
                : '';
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('shadow_title')) +
            ' <span class="chip ' +
            tbState.cls +
            '">' +
            esc(at(tbState.key)) +
            '</span>' +
            '<span class="note" style="margin-left:auto">' +
            esc(at('shadow_diff_note', { diff: money(tb.diff) })) +
            '</span></h3></div><div class="bd sdw-body-wrap">' +
            hint +
            entriesSectionHtml(
                shadowDraft.entries || [],
                shadowDraft.sources || [],
                ui.open.entries
            ) +
            accountsSectionHtml(shadowDraft.accounts || [], ui.open.accounts) +
            glSectionHtml(shadowDraft.reconcile_gl, ui.open.gl) +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.shadowRender = {
        groupEntriesBySource: groupEntriesBySource,
        trialBalanceState: trialBalanceState,
        glReconState: glReconState,
        pageHtml: pageHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
