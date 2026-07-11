/*
 * Pearnly AI · ai-vatcheck.js · N1 销项税报告三查(顶层独立视图)编排:上传单份报告 + 运行三查
 *
 * 顶层导航位(id=v-vatcheck,不挂在客户独立页四视图之下——报告三查是拿到手的一份报告文件
 * 本身的静态自查,不依赖任何客户/工单上下文,同「待我处理」客户池页的顶层路由先例)。
 * 上传走 POST /api/vat_report_checks/run(N1-a 已上线),响应即三查结果,本文件只管状态机 +
 * 网络 + 事件委托,HTML 拼装交给 AI.vatcheckRender(纯函数,零网络依赖)。
 *
 * 依赖 window.AI.state/api/format/vatcheckRender 与全局 at(),排在它们之后、ai.js 之前
 * 加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;
    var fileInput = null; // 持久隐藏文件选择器(单例,不随 render 重建 → File 不丢,同 ai-intake.js 先例)

    function body() {
        return $('vcBody');
    }

    function freshState(api) {
        return { api: api, file: null, running: false, errKey: null, result: null };
    }

    function render() {
        body().innerHTML = AI.vatcheckRender.pageHtml({
            file: S.file,
            running: S.running,
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
        var check = AI.vatcheckRender.validateFile(file);
        if (!check.ok) {
            S.file = null;
            S.errKey = check.errKey;
            render();
            return;
        }
        S.file = file;
        S.errKey = null;
        render();
    }

    function clearFile() {
        S.file = null;
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
            .runVatReportChecks(S.file)
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
        if (a === 'vc-pick' || a === 'vc-goto-upload') pickFile();
        else if (a === 'vc-clear-file') clearFile();
        else if (a === 'vc-run') run();
        else if (a === 'vc-reset') reset();
    }

    function onDragover(e) {
        var dz = e.target.closest && e.target.closest('#vcDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.add('over');
    }

    function onDragleave(e) {
        var dz = e.target.closest && e.target.closest('#vcDrop');
        if (dz) dz.classList.remove('over');
    }

    function onDrop(e) {
        var dz = e.target.closest && e.target.closest('#vcDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.remove('over');
        if (e.dataTransfer && e.dataTransfer.files) setFile(e.dataTransfer.files);
    }

    // Enter/Space 在拖拽区聚焦时触发选择(Canon §7 键盘可达),同 ai-intake.js 先例。
    function onKeydown(e) {
        if (e.target && e.target.id === 'vcDrop' && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            pickFile();
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'vcFileInput';
        fileInput.accept = '.pdf,.xlsx,.xls,.jpg,.jpeg,.png';
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
    window.AI.vatcheck = { mount: mount };
})();
