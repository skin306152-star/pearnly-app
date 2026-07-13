/*
 * Pearnly AI · ai-api-payroll.js · 工资表 ภ.ง.ด.1 工具卡的后端调用薄层(拆自 ai-api.js)
 *
 * 单文件<500 行铁律:ai-api.js 加满导航三门(N1)新增的建客户/报表下载方法后会破线,
 * 工资表 H1b 这五个方法(parse/commit/output 三产出 + ภ.ง.ด.1ก 年度聚合两个)体量独立、
 * 依赖面窄(只用 root/authHeaders/handleResponse 三个 apiFactory 内部闭包量),拆出去
 * 零行为改变——同 ai-payroll-annual-render.js 拆自 ai-payroll-render.js 的先例。
 *
 * 工厂函数 create(root, authHeaders, handleResponse, attachmentResponse) 由 ai-api.js 的
 * apiFactory() 调用(四个都是它的内部闭包量),返回的方法对象被 Object.assign 进
 * AI.api.create() 的结果里,调用方(ai-payroll.js)感知不到这层拆分。
 */
(function (root) {
    'use strict';

    function create(root, authHeaders, handleResponse, attachmentResponse) {
        return {
            // parse 纯读猜列/套模板,commit 落库 + 点亮义务,output 下载三产出——三者都是
            // multipart(parse/commit 带文件),不能走 ai-api.js 的 call()。
            parsePayroll: function (file, workspaceClientId, period) {
                var fd = new FormData();
                fd.append('file', file);
                fd.append('workspace_client_id', workspaceClientId);
                fd.append('period', period);
                return root
                    .fetch('/api/payroll/parse', {
                        method: 'POST',
                        headers: authHeaders(),
                        body: fd,
                    })
                    .then(handleResponse);
            },
            commitPayroll: function (file, opts) {
                var fd = new FormData();
                fd.append('file', file);
                fd.append('workspace_client_id', opts.workspaceClientId);
                fd.append('period', opts.period);
                fd.append('column_map', JSON.stringify(opts.columnMap || {}));
                fd.append('fixed_values', JSON.stringify(opts.fixedValues || {}));
                fd.append('income_code', opts.incomeCode || '40(1)');
                fd.append('manual_entries', JSON.stringify(opts.manualEntries || []));
                return root
                    .fetch('/api/payroll/commit', {
                        method: 'POST',
                        headers: authHeaders(),
                        body: fd,
                    })
                    .then(handleResponse);
            },
            // 三产出下载:GET 带鉴权头,<a href> 发不了自定义头,调用方拿 blob 自建
            // object URL(同 downloadDeliverable 先例)。文件名解析走共享 attachmentResponse。
            downloadPayrollOutput: function (workspaceClientId, period, kind) {
                var qs =
                    '?workspace_client_id=' +
                    encodeURIComponent(workspaceClientId) +
                    '&period=' +
                    encodeURIComponent(period) +
                    '&kind=' +
                    encodeURIComponent(kind);
                return root
                    .fetch('/api/payroll/output' + qs, { headers: authHeaders() })
                    .then(attachmentResponse(kind));
            },
            // ภ.ง.ด.1ก 年度聚合(批次 H 收尾件)——summary 纯读聚合预览(JSON),output 只接受
            // kind=keying(上传件格式未经官方样本核实,诚实降级见 routes/payroll_routes.py)。
            getPayrollAnnualSummary: function (workspaceClientId, taxYear) {
                var qs =
                    '?workspace_client_id=' +
                    encodeURIComponent(workspaceClientId) +
                    '&tax_year=' +
                    encodeURIComponent(taxYear);
                return root
                    .fetch('/api/payroll/annual/summary' + qs, { headers: authHeaders() })
                    .then(handleResponse);
            },
            downloadPayrollAnnualOutput: function (workspaceClientId, taxYear, kind) {
                var qs =
                    '?workspace_client_id=' +
                    encodeURIComponent(workspaceClientId) +
                    '&tax_year=' +
                    encodeURIComponent(taxYear) +
                    '&kind=' +
                    encodeURIComponent(kind);
                return root
                    .fetch('/api/payroll/annual/output' + qs, { headers: authHeaders() })
                    .then(attachmentResponse(kind));
            },
        };
    }

    if (typeof module !== 'undefined' && module.exports) module.exports = { create: create };
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiPayroll = { create: create };
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
