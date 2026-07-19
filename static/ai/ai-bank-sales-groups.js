/* Pearnly AI · 银行待定行分组数据整形 + 分组确认 HTML(GC-C)。 */
(function (root) {
    'use strict';

    var LARGE_MIN = 10000;
    var GROUP_ORDER = ['qr_edc', 'transfer_in', 'cash_deposit', 'other_in'];
    var GROUP_TITLE_KEY = {
        qr_edc: 'bxs_group_qr_edc',
        transfer_in: 'bxs_group_transfer_in',
        cash_deposit: 'bxs_group_cash_deposit',
        other_in: 'bxs_group_other_in',
    };

    function pendingGroups(rows, summaries) {
        var byKey = {};
        var summaryByKey = {};
        (summaries || []).forEach(function (summary) {
            summaryByKey[summary.key] = summary;
        });
        (rows || []).forEach(function (row) {
            if (row.verdict !== 'pending') return;
            var key = GROUP_TITLE_KEY[row.group] ? row.group : 'other_in';
            (byKey[key] = byKey[key] || []).push(row);
        });
        return GROUP_ORDER.filter(function (key) {
            return byKey[key] && byKey[key].length;
        }).map(function (key) {
            var groupRows = byKey[key];
            var summary = summaryByKey[key] || {};
            return {
                key: key,
                titleKey: GROUP_TITLE_KEY[key],
                rows: groupRows,
                large: groupRows.filter(function (row) {
                    return Number(row.deposit) >= LARGE_MIN;
                }),
                small: groupRows.filter(function (row) {
                    return Number(row.deposit) < LARGE_MIN;
                }),
                count: Number(summary.count) || groupRows.length,
                sum: summary.sum == null ? null : summary.sum,
            };
        });
    }

    var pure = {
        LARGE_MIN: LARGE_MIN,
        GROUP_TITLE_KEY: GROUP_TITLE_KEY,
        pendingGroups: pendingGroups,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;
    if (!root) return;

    function esc(value) {
        return root.AI.state.esc(value);
    }

    function groupHtml(group, ui, rowHtml, readonlyRowHtml) {
        var busy = !!ui.batchBusy;
        var large = group.large.map(rowHtml).join('');
        var small = group.small.length
            ? '<details class="bxs-small"><summary>' +
              esc(at('bxs_small_rows', { n: group.small.length })) +
              '</summary>' +
              group.small.map(readonlyRowHtml).join('') +
              '</details>'
            : '';
        return (
            '<div class="bxs-group" data-bxs-group="' +
            group.key +
            '"><div class="bxs-group-h"><strong>' +
            esc(at(group.titleKey)) +
            '</strong><span>' +
            esc(at('bxs_group_meta', { n: group.count, sum: root.AI.format.money(group.sum) })) +
            '</span></div>' +
            large +
            small +
            '<div class="brx-actions"><button type="button" class="btn sm" data-action="bxs-batch-request" data-group="' +
            group.key +
            '" data-verdict="sales"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(at('bxs_group_all_sales')) +
            '</button><button type="button" class="btn sm" data-action="bxs-batch-request" data-group="' +
            group.key +
            '" data-verdict="non_sales"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(at('bxs_group_all_nonsales')) +
            '</button></div></div>'
        );
    }

    function sectionHtml(suggestion, ui, rowHtml, readonlyRowHtml) {
        var groups = pendingGroups(suggestion.rows, suggestion.pending_groups);
        var count = groups.reduce(function (sum, group) {
            return sum + group.count;
        }, 0);
        var body = groups.length
            ? groups
                  .map(function (group) {
                      return groupHtml(group, ui, rowHtml, readonlyRowHtml);
                  })
                  .join('')
            : '<p class="brx-empty">' + esc(at('bxs_pending_empty')) + '</p>';
        var err = ui.batchErrKey
            ? '<div class="bxs-err">' + esc(at(ui.batchErrKey)) + '</div>'
            : '';
        return (
            '<div class="brx-section' +
            (ui.open.pending ? ' on' : '') +
            '" data-bxs-kind="pending"><button type="button" class="brx-fold" data-action="bxs-fold" data-kind="pending"><span>' +
            esc(at('bxs_pending_title', { n: count })) +
            '</span><span class="chip ' +
            (count ? 'w' : 'n') +
            '">' +
            count +
            '</span><span class="brx-caret">' +
            esc(at(ui.open.pending ? 'brx_collapse' : 'brx_expand')) +
            '</span></button><div class="brx-body">' +
            body +
            err +
            '</div></div>'
        );
    }

    function confirmHtml(confirmGroup) {
        if (!confirmGroup) return '';
        var verdictKey =
            confirmGroup.verdict === 'sales' ? 'bxs_decide_sales' : 'bxs_decide_nonsales';
        var groupName = at(GROUP_TITLE_KEY[confirmGroup.key]);
        return (
            '<div class="pkg-mask on enter bxs-confirm-mask"><div class="pkg-modal rv-confirm-modal" role="dialog" aria-modal="true" aria-labelledby="bxsConfirmTitle"><div class="mh"><div><h3 id="bxsConfirmTitle">' +
            esc(at('bxs_batch_confirm_title')) +
            '</h3></div><button type="button" class="mclose" data-action="bxs-batch-cancel" aria-label="' +
            esc(at('intake_form_cancel')) +
            '">×</button></div><div class="mb"><p>' +
            esc(
                at('bxs_batch_confirm_msg', {
                    group: groupName,
                    n: confirmGroup.count,
                    sum: root.AI.format.money(confirmGroup.sum),
                    verdict: at(verdictKey),
                })
            ) +
            '</p><div class="rv-confirm-actions"><button type="button" class="btn" data-action="bxs-batch-cancel">' +
            esc(at('intake_form_cancel')) +
            '</button><button type="button" class="btn pri" data-action="bxs-batch-confirm">' +
            esc(at('bxs_batch_confirm_btn', { verdict: at(verdictKey) })) +
            '</button></div></div></div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.bankSalesGroups = Object.assign(
        { sectionHtml: sectionHtml, confirmHtml: confirmHtml },
        pure
    );
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
