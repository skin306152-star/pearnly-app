/*
 * Pearnly AI · ai-api-upload.js · 收料上传 XHR 进度薄层(拆自 ai-api.js)
 *
 * 单文件<500 行铁律:同 ai-api-review.js 先例拆出·XHR 上传进度薄层。用 XHR 而非 fetch
 * ——fetch 没有上传进度事件,只有 xhr.upload.onprogress 能报字节级真进度(onProgress
 * 第 4 参可选,不传行为不变)。发 FormData 不手设 Content-Type(要让浏览器带 multipart
 * boundary)。password 可选(IN-0a 扩展的 Form 字段,整批同一密码,只用于解密不落盘)
 * ——不传则密码 PDF 422 pdf_password_required。
 *
 * 工厂函数 create(root, authHeaders) 由 ai-api.js 的 apiFactory() 调用(authHeaders 是
 * 它的内部闭包量,接线口径同 ai-api-review.js),返回的方法对象被 Object.assign 进
 * AI.api.create() 的结果里,调用方(ai-intake-queue.js)感知不到这层拆分。
 * parseUploadError 是纯函数,module.exports 双侧导出供 node 单测(同 ai-intake-manifest.js
 * 先例)。
 */
(function (root) {
    'use strict';

    // 非 2xx 响应体 → 与 ai-api.js handleResponse 同构的错误对象(code/status/detail):
    // 调用方依赖 err.detail 的 code/message/filename 走 422 隔离重试;JSON 解析失败
    // 兜底空对象 → code='generic',口径同 handleResponse 的 .catch(() => ({}))。
    function parseUploadError(status, responseText) {
        var j;
        try {
            j = JSON.parse(responseText);
        } catch (e) {
            j = {};
        }
        var detail = j.detail;
        var code =
            (detail && typeof detail === 'object' ? detail.code : detail) ||
            (j.error && j.error.code) ||
            'generic';
        var err = new Error(String(code));
        err.status = status;
        err.code = code;
        if (detail && typeof detail === 'object') err.detail = detail;
        return err;
    }

    function create(root, authHeaders) {
        return {
            // 补料上传(W4 + IN-0b 密码 PDF):multipart。非 2xx 走 parseUploadError(与
            // handleResponse 同一错误契约);网络级失败照 fetch 口径抛无 code 的 TypeError。
            addMaterials: function (orderId, files, password, onProgress) {
                var headers = authHeaders();
                var fd = new FormData();
                for (var i = 0; i < files.length; i++) fd.append('files', files[i]);
                if (password) fd.append('password', password);
                fd.append('defer_run', 'true');
                return new Promise(function (resolve, reject) {
                    var xhr = new XMLHttpRequest();
                    xhr.open(
                        'POST',
                        '/api/workorder/orders/' + encodeURIComponent(orderId) + '/materials'
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
                            reject(parseUploadError(xhr.status, xhr.responseText));
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
        };
    }

    var apiUpload = { create: create, parseUploadError: parseUploadError };
    if (typeof module !== 'undefined' && module.exports) module.exports = apiUpload;
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiUpload = apiUpload;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
