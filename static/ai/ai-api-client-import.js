/*
 * Pearnly AI · ai-api-client-import.js · 客户名录批量导入的后端调用薄层(拆自 ai-api.js)
 *
 * 单文件<500 行铁律:ai-api.js 已接近上限(同 ai-api-payroll.js/ai-api-review.js 拆分
 * 理由),这两个方法(parse 上传预览/commit 落库)体量独立、依赖面窄,拆出去零行为改变。
 *
 * parse 是 multipart(带文件),不能走 ai-api.js 的 call();commit 是纯 JSON body,
 * 走 call() 本可以,但两者同源(routes/client_import_routes.py 的 2 端点)放一起管理。
 *
 * 工厂函数 create(root, authHeaders, handleResponse, call) 由 ai-api.js 的 apiFactory()
 * 调用,返回的方法对象被 Object.assign 进 AI.api.create() 的结果里。
 */
(function (root) {
    'use strict';

    function create(root, authHeaders, handleResponse, call) {
        return {
            // 上传名录 → 表头识别 + 逐行三态预览(dry_run,不落库)。413/422 走
            // client_import.file_too_large / client_import.header_not_recognized,
            // 调用方 mapApiErrorKey 取四语文案。
            importClientsParse: function (file) {
                var fd = new FormData();
                fd.append('file', file);
                return root
                    .fetch('/api/workspace/clients/import/parse', {
                        method: 'POST',
                        headers: authHeaders(),
                        body: fd,
                    })
                    .then(handleResponse);
            },
            // 确认后逐行落库。rows 取自 parse 预览的行(用户可能已在预览表里逐行调整过)。
            importClientsCommit: function (rows) {
                return call('POST', '/api/workspace/clients/import/commit', { rows: rows });
            },
        };
    }

    if (typeof module !== 'undefined' && module.exports) module.exports = { create: create };
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiClientImport = { create: create };
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
