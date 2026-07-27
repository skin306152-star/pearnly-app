/*
 * Pearnly AI · ai-api-steward.js · 智能管家(B2-M1/B3/F1)十端点的后端调用薄层(拆自 ai-api.js)
 *
 * 单文件<500 行铁律:ai-api.js 已在预算线上,管家端点自成一族 —— 同 ai-api-desk.js/
 * ai-api-payroll.js 先例拆出去,调用方感知不到这层拆分。
 *
 * 契约(前缀 /api/ai/steward,Bearer 鉴权,权限比照 /ai):
 *   GET  /status                     → {enabled, attachments:{max_file_bytes,...}}
 *   POST /sessions                   → {session_id}
 *   GET  /sessions/{sid}             → {session_id, messages[], current_task_id?}
 *   POST /sessions/{sid}/attachments → {attachments[], count}(multipart · 见下)
 *   POST /sessions/{sid}/messages    → {message_id, user_message_id, reply, task_id?, ...}
 *   GET  /attachments/{aid}/download → 二进制原件(Content-Disposition 泰文名走 RFC 5987)
 *   GET  /tasks/{tid}                → 左窗任务数据(见 ai-steward-render.js 顶注)
 *   POST /tasks/{tid}/cancel         → 同左窗任务数据(幂等 · 已收尾的原样返回)
 *   POST /authorizations/approve     → {task_id, authorization}(body {token})
 *   POST /authorizations/reject      → 同上(token 走 body 不进 URL/访问日志)
 *
 * 上传单开一条 XHR 路:fetch 没有上传进度事件,只有 xhr.upload.onprogress 报得出字节级
 * 真进度(同 ai-api-upload.js 的理由);下载单开一条 fetch 路:这组端点只认 Authorization
 * 头,<a href> 发不了自定义头 —— 直接把后端给的 href 挂成链接就是一个点了 401 的假出口。
 */
(function (root) {
    'use strict';

    var BASE = '/api/ai/steward';

    function create(call, net, authHeaders, attachmentResponse) {
        return {
            // 闸探针(pearnly_ai_steward · tenant 级默认关):闸关也回 200 {enabled:false},
            // 不走 404 —— 照 getDeskStatus 先例,免得闸关用户每开一次 /ai 就吃一条 404。
            // attachments 是上传限额的单一事实源,前端不各硬编码一份(必漂)。
            getStewardStatus: function () {
                return call('GET', BASE + '/status');
            },
            createStewardSession: function () {
                return call('POST', BASE + '/sessions');
            },
            getStewardSession: function (sessionId) {
                return call('GET', BASE + '/sessions/' + encodeURIComponent(sessionId));
            },
            // body 三形态互斥(action > 纯文件 > 有话),形状由调用方拼好原样送:这层不替
            // 它判该带哪个键 —— 判据在 ai-steward-attach.js,两处各判一次必漂。
            sendStewardMessage: function (sessionId, body) {
                var payload = body || {};
                return call(
                    'POST',
                    BASE + '/sessions/' + encodeURIComponent(sessionId) + '/messages',
                    {
                        text: payload.text || '',
                        lang: (root.AII18N && root.AII18N.lang) || '',
                        attachment_ids: payload.attachment_ids || [],
                        action: payload.action || null,
                    }
                );
            },
            // 附上即传。password 仅当批里有加密 PDF 时带(只用于当场解开,不落盘)。
            // 非 2xx 走 parseUploadError —— 413 的 {code,limit,actual} 与 422 的四语
            // message 都要原样进 err.detail,调用方靠它逐件点名。
            uploadStewardAttachments: function (sessionId, files, password, onProgress) {
                var headers = authHeaders();
                var fd = new FormData();
                for (var i = 0; i < files.length; i++) fd.append('files', files[i]);
                if (password) fd.append('password', password);
                return new Promise(function (resolve, reject) {
                    var xhr = new XMLHttpRequest();
                    xhr.open(
                        'POST',
                        BASE + '/sessions/' + encodeURIComponent(sessionId) + '/attachments'
                    );
                    Object.keys(headers).forEach(function (k) {
                        xhr.setRequestHeader(k, headers[k]);
                    });
                    if (onProgress) {
                        xhr.upload.onprogress = function (e) {
                            if (e.lengthComputable) onProgress(e.loaded, e.total);
                        };
                    }
                    xhr.onload = function () {
                        if (xhr.status < 200 || xhr.status >= 300) {
                            reject(AI.apiUpload.parseUploadError(xhr.status, xhr.responseText));
                            return;
                        }
                        var j;
                        try {
                            j = JSON.parse(xhr.responseText);
                        } catch (e) {
                            j = {};
                        }
                        resolve(j);
                    };
                    xhr.onerror = xhr.ontimeout = function () {
                        reject(new TypeError('network request failed'));
                    };
                    xhr.send(fd);
                });
            },
            // 原件下载 → {blob, filename}(调用方交给 AI.api.saveBlob 存盘)。
            downloadStewardAttachment: function (attachmentId) {
                return net
                    .fetch(
                        BASE + '/attachments/' + encodeURIComponent(attachmentId) + '/download',
                        {
                            headers: authHeaders(),
                        }
                    )
                    .then(attachmentResponse('attachment'));
            },
            getStewardTask: function (taskId) {
                return call('GET', BASE + '/tasks/' + encodeURIComponent(taskId));
            },
            cancelStewardTask: function (taskId) {
                return call('POST', BASE + '/tasks/' + encodeURIComponent(taskId) + '/cancel');
            },
            // 决断二端点共形(body 只有 token):approve 要 tax.filing.approve,reject 只要
            // view —— 权限差异在后端判,这里不预判(403 由挂载层翻人话)。
            decideStewardAuthz: function (approve, token) {
                return call('POST', BASE + '/authorizations/' + (approve ? 'approve' : 'reject'), {
                    token: token,
                });
            },
        };
    }

    if (typeof module !== 'undefined' && module.exports) module.exports = { create: create };
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiSteward = { create: create };
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
