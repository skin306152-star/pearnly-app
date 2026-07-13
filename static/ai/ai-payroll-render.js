/*
 * Pearnly AI · ai-payroll-render.js · H1b 工资表 ภ.ง.ด.1 工具卡纯逻辑 + HTML 拼装
 *
 * 引擎(services/payroll/、services/tax/pnd1_attach.py、services/tax/rdprep_pnd1.py)的
 * 产品化外壳:选客户 + 期间(佛历 YYYY-MM)→ 上传工资 Excel → 后端猜列/套模板 → 会计
 * 确认一次列映射(本卡核心交互:低置信/缺失字段留空强制人补,同表头第二次上传直接套
 * 模板不再要求确认)→ 提交校验落库 → 三产出下载 + issues 逐行点名(方案 §3 V1-V5)。
 *
 * 上半段(validateFile/issueKindKey/confidenceKey/defaultPeriod/isPeriodValid/
 * requiredFieldsSatisfied/manualEntryValid)零 DOM/零 i18n 依赖,node
 * (tests/unit/test_ai_pure_modules.py)直接 require 断言;下半段 HTML 拼装依赖
 * at()/AI.state/AI.format,只在浏览器根挂载——同 ai-fileconv-render.js 的双段先例。
 */
(function (root) {
    'use strict';

    var ALLOWED_EXT = /\.xlsx?$/i;

    function validateFile(file) {
        if (!file) return { ok: false, errKey: 'payroll_err_no_file' };
        if (!ALLOWED_EXT.test(file.name || '')) {
            return { ok: false, errKey: 'payroll_err_bad_type' };
        }
        return { ok: true };
    }

    // Issue.kind(services/payroll/model.py 七枚举)→ i18n key,逐行点名用。
    var ISSUE_KIND_KEYS = {
        invalid_employee_id: 'payroll_issue_invalid_employee_id',
        bad_paid_date: 'payroll_issue_bad_paid_date',
        paid_date_out_of_period: 'payroll_issue_paid_date_out_of_period',
        sum_mismatch: 'payroll_issue_sum_mismatch',
        wht_out_of_range: 'payroll_issue_wht_out_of_range',
        bad_amount: 'payroll_issue_bad_amount',
        missing_required_field: 'payroll_issue_missing_required_field',
    };

    function issueKindKey(kind) {
        return ISSUE_KIND_KEYS[kind] || kind;
    }

    var CONFIDENCE_KEYS = { high: 'payroll_conf_high', medium: 'payroll_conf_medium' };

    function confidenceKey(confidence) {
        return CONFIDENCE_KEYS[confidence] || confidence;
    }

    // 猜列目标字段的展示序(方案 §2.2):身份证/金额优先,姓名紧随称谓之后,收入码/条件
    // 类整表常量字段殿后——同 services/payroll/model.py::GUESSABLE_FIELDS 语义分组一致。
    var FIELD_ORDER = [
        'employee_id',
        'title',
        'first_name',
        'last_name',
        'paid_amount',
        'wht_amount',
        'paid_date',
        'income_code',
    ];

    var FIELD_LABEL_KEYS = {
        employee_id: 'payroll_field_employee_id',
        title: 'payroll_field_title',
        first_name: 'payroll_field_first_name',
        last_name: 'payroll_field_last_name',
        paid_amount: 'payroll_field_paid_amount',
        wht_amount: 'payroll_field_wht_amount',
        paid_date: 'payroll_field_paid_date',
        income_code: 'payroll_field_income_code',
    };

    // 整表可给固定值兜底的字段(方案 §2.2「整列=一个值」)——列映射留空时,前端另给
    // 一个固定值输入框,不强制每张表都得有一列。其余字段(身份证/姓名/金额)必须来自
    // 某一列,没有固定值兜底。
    var FIXABLE_FIELDS = { income_code: true, paid_date: true };

    // 佛历当月(YYYY-MM)——上传新客户工资表时的期间默认值,会计仍可手改。now 由调用方
    // 注入(纯函数可测,不读真时钟)。
    function defaultPeriod(now) {
        var d = now || new Date();
        var y = d.getFullYear() + 543;
        var m = String(d.getMonth() + 1).padStart(2, '0');
        return y + '-' + m;
    }

    function isPeriodValid(period) {
        return /^\d{4}-\d{2}$/.test(String(period || ''));
    }

    // 必填字段(model.REQUIRED_FIELDS 五枚举)全有映射列才准提交——低置信/缺失字段
    // 留空强制人补(方案 §2.2 校验前置到 UI,不等后端 V5 才点名)。
    function requiredFieldsSatisfied(columnMap, requiredFields) {
        return (requiredFields || []).every(function (f) {
            var v = (columnMap || {})[f];
            return v !== null && v !== undefined && v !== '';
        });
    }

    // 手工加行六字段(称谓/名/姓/身份证/实付/预扣)前端最小校验——真正的 mod-11/金额
    // 校验交后端 V1-V5 权威判定,这里只挡明显空值省一趟网络往返。
    function manualEntryValid(entry) {
        entry = entry || {};
        var required = ['employee_id', 'title', 'first_name', 'last_name', 'paid_amount'];
        return required.every(function (k) {
            return String(entry[k] || '').trim() !== '';
        });
    }

    var pure = {
        validateFile: validateFile,
        issueKindKey: issueKindKey,
        confidenceKey: confidenceKey,
        FIELD_ORDER: FIELD_ORDER,
        FIXABLE_FIELDS: FIXABLE_FIELDS,
        defaultPeriod: defaultPeriod,
        isPeriodValid: isPeriodValid,
        requiredFieldsSatisfied: requiredFieldsSatisfied,
        manualEntryValid: manualEntryValid,
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

    var UPLOAD_ICON =
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="2">' +
        '<path d="M12 3v12m0 0 4-4m-4 4-4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>';

    function clientPickerHtml(ctx) {
        var options =
            '<option value="">' +
            esc(at('payroll_pick_client')) +
            '</option>' +
            (ctx.clients || [])
                .map(function (c) {
                    return (
                        '<option value="' +
                        esc(c.id) +
                        '"' +
                        (String(c.id) === String(ctx.clientId) ? ' selected' : '') +
                        '>' +
                        esc(c.name) +
                        '</option>'
                    );
                })
                .join('');
        return (
            '<div class="pr-setup-row">' +
            '<label class="pr-lb">' +
            esc(at('payroll_client_label')) +
            '<select id="prClientSel">' +
            options +
            '</select></label>' +
            '<label class="pr-lb">' +
            esc(at('payroll_period_label')) +
            '<input id="prPeriodInput" type="text" placeholder="2569-05" value="' +
            esc(ctx.period) +
            '" maxlength="7" /></label>' +
            '</div>'
        );
    }

    function uploadZoneHtml(ctx) {
        var errHtml = ctx.errKey ? '<div class="intake-err">' + esc(at(ctx.errKey)) + '</div>' : '';
        var body;
        if (ctx.file) {
            body =
                '<div class="dz-filled"><div class="dz-count">' +
                esc(ctx.file.name) +
                '</div><div class="dz-btns">' +
                '<button type="button" class="btn" data-action="pr-clear-file">' +
                esc(at('intake_clear')) +
                '</button></div></div>';
        } else {
            body =
                '<div class="dz-inner" data-action="pr-goto-upload">' +
                '<div class="dz-ic">' +
                UPLOAD_ICON +
                '</div><div class="dz-t">' +
                esc(at('payroll_drop_t')) +
                '</div><div class="dz-s">' +
                esc(at('payroll_drop_s')) +
                '</div><button type="button" class="btn" data-action="pr-pick">' +
                esc(at('intake_pick')) +
                '</button></div>';
        }
        return '<div class="dropzone" id="prDrop" tabindex="0">' + body + '</div>' + errHtml;
    }

    function setupHtml(ctx) {
        return (
            '<div class="panel"><div class="bd">' +
            clientPickerHtml(ctx) +
            uploadZoneHtml(ctx) +
            '</div></div>'
        );
    }

    function confidenceBadgeHtml(confidence) {
        if (!confidence) return '';
        var cls = confidence === 'high' ? 'g' : 'w';
        return (
            '<span class="chip ' +
            cls +
            ' pr-conf">' +
            esc(at(confidenceKey(confidence))) +
            '</span>'
        );
    }

    function columnOptionsHtml(header, selected) {
        var opts = '<option value="">' + esc(at('payroll_unmapped')) + '</option>';
        (header || []).forEach(function (h, i) {
            opts +=
                '<option value="' +
                i +
                '"' +
                (Number(selected) === i ? ' selected' : '') +
                '>' +
                esc(at('payroll_col_n', { n: i + 1 })) +
                ': ' +
                esc(h == null ? '' : h) +
                '</option>';
        });
        return opts;
    }

    function mappingRowHtml(field, ctx) {
        var guessed = (ctx.parseResult.guessed || {})[field];
        var mapped = ctx.columnMap[field];
        var required = ctx.parseResult.required_fields.indexOf(field) >= 0;
        var missing = required && (mapped === null || mapped === undefined || mapped === '');
        var fixable = FIXABLE_FIELDS[field];
        var fixedInput = '';
        if (fixable && (mapped === null || mapped === undefined || mapped === '')) {
            var fv = field === 'income_code' ? ctx.incomeCodeFixed : ctx.paidDateFixed;
            var type = field === 'paid_date' ? 'date' : 'text';
            fixedInput =
                '<input class="pr-fixed" type="' +
                type +
                '" data-fixed="' +
                field +
                '" value="' +
                esc(fv || '') +
                '" placeholder="' +
                esc(at('payroll_fixed_ph')) +
                '" />';
        }
        return (
            '<div class="pr-map-row' +
            (missing ? ' pr-map-missing' : '') +
            '"><span class="pr-map-lb">' +
            esc(at(FIELD_LABEL_KEYS[field])) +
            (required ? ' *' : '') +
            '</span><select data-field="' +
            field +
            '">' +
            columnOptionsHtml(ctx.parseResult.header, mapped) +
            '</select>' +
            (guessed ? confidenceBadgeHtml(guessed.confidence) : '') +
            fixedInput +
            '</div>'
        );
    }

    function mappingHtml(ctx) {
        var payerNote = ctx.parseResult.payer_id_candidate
            ? '<div class="pr-payer-note">' +
              esc(at('payroll_payer_candidate', { id: ctx.parseResult.payer_id_candidate })) +
              '</div>'
            : '';
        var ok = requiredFieldsSatisfied(ctx.columnMap, ctx.parseResult.required_fields);
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('payroll_mapping_title')) +
            '</h3></div><div class="bd">' +
            payerNote +
            FIELD_ORDER.map(function (f) {
                return mappingRowHtml(f, ctx);
            }).join('') +
            '</div></div>' +
            '<div class="pr-actions">' +
            '<button type="button" class="btn pri" data-action="pr-confirm"' +
            (ok && !ctx.committing ? '' : ' disabled') +
            '>' +
            esc(ctx.committing ? at('payroll_committing') : at('payroll_confirm')) +
            '</button></div>'
        );
    }

    function issueRowHtml(issue) {
        return (
            '<div class="pr-issue"><span class="chip w">' +
            esc(at(issueKindKey(issue.kind))) +
            '</span><span class="pr-issue-body">' +
            (issue.row_no ? '<b>#' + esc(issue.row_no) + '</b> ' : '') +
            esc(issue.message) +
            (issue.value ? '<span class="pr-issue-v">' + esc(issue.value) + '</span>' : '') +
            '</span></div>'
        );
    }

    function totalsHtml(commitResult) {
        var t = commitResult.totals || {};
        return (
            '<div class="pr-stats">' +
            '<div class="fc-stat-row"><span class="fc-stat-lb">' +
            esc(at('payroll_stat_rows')) +
            '</span><span class="fc-stat-v">' +
            esc(commitResult.row_count) +
            '</span></div>' +
            '<div class="fc-stat-row"><span class="fc-stat-lb">' +
            esc(at('payroll_stat_paid')) +
            '</span><span class="fc-stat-v">' +
            money(t.paid_amount) +
            '</span></div>' +
            '<div class="fc-stat-row"><span class="fc-stat-lb">' +
            esc(at('payroll_stat_wht')) +
            '</span><span class="fc-stat-v">' +
            money(t.wht_amount) +
            '</span></div>' +
            '<div class="fc-stat-row"><span class="fc-stat-lb">' +
            esc(at('payroll_stat_declared')) +
            '</span><span class="fc-stat-v">' +
            (commitResult.declared_total == null ? '—' : money(commitResult.declared_total)) +
            '</span></div>' +
            '</div>'
        );
    }

    function downloadBtnHtml(kind, downloading) {
        var busy = !!(downloading || {})[kind];
        return (
            '<button type="button" class="btn" data-action="pr-download" data-kind="' +
            kind +
            '"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(busy ? at('payroll_downloading') : at('payroll_download_' + kind)) +
            '</button>'
        );
    }

    function manualFormHtml(form) {
        if (!form) {
            return (
                '<button type="button" class="btn sm" data-action="pr-manual-open">' +
                esc(at('payroll_manual_add')) +
                '</button>'
            );
        }
        var f = form;
        function field(key, label, type) {
            return (
                '<label class="pr-lb">' +
                esc(at(label)) +
                '<input data-manual="' +
                key +
                '" type="' +
                (type || 'text') +
                '" value="' +
                esc(f[key] || '') +
                '" /></label>'
            );
        }
        var ok = manualEntryValid(f);
        return (
            '<div class="pr-manual-form">' +
            field('title', 'payroll_field_title') +
            field('first_name', 'payroll_field_first_name') +
            field('last_name', 'payroll_field_last_name') +
            field('employee_id', 'payroll_field_employee_id') +
            field('paid_amount', 'payroll_field_paid_amount') +
            field('wht_amount', 'payroll_field_wht_amount') +
            '<div class="pr-manual-btns">' +
            '<button type="button" class="btn pri" data-action="pr-manual-submit"' +
            (ok ? '' : ' disabled') +
            '>' +
            esc(at('payroll_manual_submit')) +
            '</button>' +
            '<button type="button" class="btn" data-action="pr-manual-cancel">' +
            esc(at('intake_clear')) +
            '</button></div></div>'
        );
    }

    function resultsHtml(ctx) {
        var r = ctx.commitResult;
        var issues = r.issues || [];
        var issuesHtml = issues.map(issueRowHtml).join('');
        var banner = issues.length
            ? '<div class="fc-banner w"><span class="chip w">' +
              esc(at('payroll_has_issues_chip')) +
              '</span><span>' +
              esc(at('payroll_has_issues_s', { n: issues.length })) +
              '</span></div>'
            : '<div class="fc-banner g"><span class="chip g">' +
              esc(at('payroll_conserved_chip')) +
              '</span><span>' +
              esc(at('payroll_conserved_s')) +
              '</span></div>';
        return (
            '<div class="pr-done-bar"><span>' +
            esc(at('payroll_template_saved')) +
            '</span><button type="button" class="btn sm" data-action="pr-reset">' +
            esc(at('fileconv_reset')) +
            '</button></div>' +
            banner +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('payroll_totals_title')) +
            '</h3></div><div class="bd">' +
            totalsHtml(r) +
            '</div></div>' +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('fileconv_issues_title')) +
            '</h3></div><div class="bd">' +
            (issuesHtml || '<div class="fc-clean">' + esc(at('fileconv_no_issues')) + '</div>') +
            '</div></div>' +
            '<div class="pr-actions">' +
            downloadBtnHtml('keying', ctx.downloading) +
            downloadBtnHtml('attach', ctx.downloading) +
            downloadBtnHtml('central', ctx.downloading) +
            '</div>' +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('payroll_manual_title')) +
            '</h3></div><div class="bd">' +
            manualFormHtml(ctx.manualForm) +
            '</div></div>'
        );
    }

    // ctx 四态:未上传(无 file/无 result,setup 区)/ 识别或提交中(parsing||committing,
    // 骨架屏)/ 出错(errKey)/ 映射待确认(parseResult 有但 commitResult 无)/ 有结果
    // (commitResult)。骨架屏与已选文件名共存,不整块替换掉用户已选的文件——同
    // ai-fileconv-render.js 先例。
    function pageHtml(ctx) {
        ctx = ctx || {};
        if (ctx.parsing || ctx.committing) return setupHtml(ctx) + root.AI.state.loadingHtml();
        if (ctx.commitResult) return resultsHtml(ctx);
        if (ctx.parseResult) return setupHtml(ctx) + mappingHtml(ctx);
        return setupHtml(ctx);
    }

    root.AI = root.AI || {};
    root.AI.payrollRender = Object.assign({ pageHtml: pageHtml }, pure);
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
