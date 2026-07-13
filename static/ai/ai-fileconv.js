/*
 * Pearnly AI · ai-fileconv.js · K1b/K2 财务文件转换(顶层独立视图)编排:上传
 * PDF/图片/Excel + 跑转换 + 下载 xlsx / pdf
 *
 * 顶层导航位(id=v-fileconv,同 /vatcheck 先例:转换一份文件本身不依赖任何客户/工单
 * 上下文)。上传走 POST /api/fileconv/convert(JSON 摘要),下载是同一份文件再 POST
 * 一次 `?format=xlsx|pdf`(K1b 派单书:无状态两段式,引擎幂等不落服务端状态)。K2:
 * Excel 底稿额外可下载规范排版 PDF,两个下载各自独立 in-flight(downloadKind),不共用
 * 一个全局布尔互相拖累。状态机 + 网络 + 事件委托在本文件,HTML 拼装交给
 * AI.fileconvRender(纯函数,零网络依赖)——同 ai-vatcheck.js 先例。
 *
 * 依赖 window.AI.state/api/format/fileconvRender 与全局 at()/AII18N,排在它们之后、
 * ai.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;
    var fileInput = null; // 持久隐藏文件选择器(单例,不随 render 重建 → File 不丢,同 ai-vatcheck.js 先例)

    function body() {
        return $('fcBody');
    }

    function freshState(api) {
        return {
            api: api,
            file: null,
            running: false,
            downloadKind: null, // null | 'xlsx' | 'pdf'——哪个下载在跑,两键各自独立禁用
            errKey: null,
            result: null,
        };
    }

    function render() {
        body().innerHTML = AI.fileconvRender.pageHtml({
            file: S.file,
            running: S.running,
            downloadKind: S.downloadKind,
            errKey: S.errKey,
            result: S.result,
        });
    }

    function pickFile() {
        fileInput.value = '';
        fileInput.click();
    }

    function setFile(list) {
        var file = (list || [])[0];
        if (!file) return;
        var check = AI.fileconvRender.validateFile(file);
        if (!check.ok) {
            S.file = null;
            S.errKey = check.errKey;
            render();
            return;
        }
        S.file = file;
        S.errKey = null;
        S.result = null;
        render();
    }

    function clearFile() {
        S.file = null;
        S.result = null;
        S.errKey = null;
        render();
    }

    function run() {
        if (S.running || !S.file) return;
        var session = S; // 快照——回调落地时若已切走(离开视图再回来重挂)一律不认。
        S.running = true;
        S.errKey = null;
        render();
        S.api
            .convertFile(S.file)
            .then(function (result) {
                if (S !== session) return;
                S.running = false;
                S.result = result;
                render();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.running = false;
                var key = AI.api.mapApiErrorKey(err && err.code);
                S.errKey = at(key) !== key ? key : 'err_generic';
                render();
            });
    }

    function triggerDownload(blob, filename) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    }

    // kind: 'xlsx' | 'pdf'——同一份已上传文件再跑一次 K1b/K2 转换直接回附件。
    function downloadAs(kind) {
        if (S.downloadKind || !S.file) return;
        var session = S;
        S.downloadKind = kind;
        render();
        var fetchPromise =
            kind === 'pdf'
                ? S.api.downloadConvertedPdf(S.file, (window.AII18N && window.AII18N.lang) || 'th')
                : S.api.downloadConvertedXlsx(S.file);
        fetchPromise
            .then(function (r) {
                if (S !== session) return;
                triggerDownload(r.blob, r.filename);
            })
            .catch(function (err) {
                if (S !== session) return;
                var key = AI.api.mapApiErrorKey(err && err.code);
                S.errKey = at(key) !== key ? key : 'err_generic';
            })
            .then(function () {
                if (S !== session) return;
                S.downloadKind = null;
                render();
            });
    }

    function reset() {
        S.file = null;
        S.result = null;
        S.errKey = null;
        render();
    }

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'fc-pick' || a === 'fc-goto-upload') pickFile();
        else if (a === 'fc-clear-file') clearFile();
        else if (a === 'fc-run') run();
        else if (a === 'fc-download-xlsx') downloadAs('xlsx');
        else if (a === 'fc-download-pdf') downloadAs('pdf');
        else if (a === 'fc-reset') reset();
    }

    function onDragover(e) {
        var dz = e.target.closest && e.target.closest('#fcDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.add('over');
    }

    function onDragleave(e) {
        var dz = e.target.closest && e.target.closest('#fcDrop');
        if (dz) dz.classList.remove('over');
    }

    function onDrop(e) {
        var dz = e.target.closest && e.target.closest('#fcDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.remove('over');
        if (e.dataTransfer && e.dataTransfer.files) setFile(e.dataTransfer.files);
    }

    // Enter/Space 在拖拽区聚焦时触发选择(Canon §7 键盘可达),同 ai-vatcheck.js 先例。
    function onKeydown(e) {
        if (e.target && e.target.id === 'fcDrop' && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            pickFile();
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'fcFileInput';
        fileInput.accept = '.pdf,.jpg,.jpeg,.png,.webp,.xlsx,.xlsm,.xls,.csv';
        fileInput.style.display = 'none';
        fileInput.addEventListener('change', function () {
            setFile(fileInput.files);
        });
        document.body.appendChild(fileInput);
        var host = body();
        host.addEventListener('click', onClick);
        host.addEventListener('dragover', onDragover);
        host.addEventListener('dragleave', onDragleave);
        host.addEventListener('drop', onDrop);
        host.addEventListener('keydown', onKeydown);
    }

    function mount(api) {
        S = freshState(api);
        wireOnce();
        render();
    }

    window.AI = window.AI || {};
    window.AI.fileconv = { mount: mount };
})();
