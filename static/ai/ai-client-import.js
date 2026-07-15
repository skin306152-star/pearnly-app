/*
 * Pearnly AI · ai-client-import.js · 客户目录页「导入名录」模态(IN-0d)编排
 *
 * 事务所把 50-93 个客户的名录 Excel 一次导入建档,治"逐个手建档案"。上传 →
 * POST /api/workspace/clients/import/parse(dry_run 预览三态)→ 用户确认 →
 * POST /api/workspace/clients/import/commit(逐行落库)。两端点内部都调用与
 * 单建端点(POST /api/workspace/clients)同一段共享校验体(routes/workspace_routes.py::
 * _create_validated_client),M1 泰文名闸/税号查重/pos_only 一号一店闸对导入行同样生效
 * ——本文件只管状态机 + 网络 + 事件委托,HTML 拼装交给 AI.clientImportRender(纯函数)。
 *
 * 按钮显隐同 ai-client-new.js 先例:GET /api/workspace/clients/can-create 探针
 * (settings.workspace.manage 专属),没权限不给一个点了才 403 的假门。
 *
 * 依赖 window.AI.state/api/clientImportRender 与全局 at(),排在它们之后、ai.js 之前
 * 加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var MASK_ID = 'clientImportMask';

    var S = null;
    var wired = false;
    var fileInput = null; // 持久隐藏文件选择器(单例,不随 render 重建 → File 不丢,同 ai-vatcheck.js 先例)

    function esc(s) {
        return AI.state.esc(s);
    }

    function mask() {
        return document.getElementById(MASK_ID);
    }

    function bodyHtml() {
        var R = AI.clientImportRender;
        if (S.state === 'pick' || S.state === 'parsing') {
            var zone = R.fileZoneHtml({
                file: S.file,
                errKey: S.errKey,
                parsing: S.state === 'parsing',
            });
            return S.state === 'parsing' ? zone + AI.state.loadingHtml() : zone;
        }
        if (S.state === 'preview') return R.previewTableHtml(S.preview);
        if (S.state === 'committing') return AI.state.loadingHtml();
        return R.resultCardHtml(S.results);
    }

    function modalHtml() {
        return (
            '<div class="pkg-mask on" id="' +
            MASK_ID +
            '">' +
            '<div class="pkg-modal" role="dialog" aria-modal="true">' +
            '<div class="mh"><div><h3>' +
            esc(at('client_import_title')) +
            '</h3><p>' +
            esc(at('client_import_hint')) +
            '</p></div>' +
            '<button class="mclose" type="button" data-action="ci-close" aria-label="' +
            esc(at('pkg_evid_close')) +
            '">&times;</button></div>' +
            '<div class="mb" style="grid-template-columns: 1fr">' +
            bodyHtml() +
            '</div></div></div>'
        );
    }

    function render() {
        var existing = mask();
        var html = modalHtml();
        if (existing) existing.outerHTML = html;
        else document.body.insertAdjacentHTML('beforeend', html);
        var m = mask();
        if (!existing) m.classList.add('enter');
        m.addEventListener('click', function (e) {
            if (e.target === m) close();
        });
    }

    function pickFile() {
        fileInput.value = '';
        fileInput.click();
    }

    function setFile(list) {
        var file = (list || [])[0];
        if (!file) return;
        var check = AI.clientImportRender.validateFile(file);
        if (!check.ok) {
            S.file = null;
            S.errKey = check.errKey;
            render();
            return;
        }
        S.file = file;
        S.errKey = null;
        render();
        runParse();
    }

    function clearFile() {
        S.file = null;
        S.errKey = null;
        S.state = 'pick';
        render();
    }

    function runParse() {
        var session = S; // 快照——回调落地时若已切走(关闭又重开)一律不认。
        S.state = 'parsing';
        render();
        S.api
            .importClientsParse(S.file)
            .then(function (r) {
                if (S !== session) return;
                S.preview = r.preview || [];
                S.state = 'preview';
                render();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.state = 'pick';
                var key = AI.clientImportRender.errKeyFor(err && err.code);
                S.errKey = at(key) !== key ? key : 'err_generic';
                render();
            });
    }

    function confirmImport() {
        var session = S;
        var rows = S.preview.map(function (p) {
            return { row_index: p.row_index, name: p.name, tax_id: p.tax_id };
        });
        S.state = 'committing';
        render();
        S.api
            .importClientsCommit(rows)
            .then(function (r) {
                if (S !== session) return;
                S.results = r.results || [];
                S.createdCount = r.created || 0;
                S.state = 'result';
                render();
                if (S.createdCount > 0 && S.onImported) S.onImported();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.state = 'preview'; // 回预览,不丢用户已选的行
                var key = AI.clientImportRender.errKeyFor(err && err.code);
                S.errKey = at(key) !== key ? key : 'err_generic';
                render();
            });
    }

    function reset() {
        S.file = null;
        S.preview = [];
        S.results = [];
        S.errKey = null;
        S.state = 'pick';
        render();
    }

    function close() {
        S.open = false;
        var m = mask();
        if (m) m.remove();
        document.removeEventListener('keydown', onKeydown);
    }

    function onKeydown(e) {
        if (e.key === 'Escape') close();
    }

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'ci-close') close();
        else if (a === 'ci-pick' || a === 'ci-goto-upload') pickFile();
        else if (a === 'ci-clear-file') clearFile();
        else if (a === 'ci-confirm') confirmImport();
        else if (a === 'ci-cancel') close();
        else if (a === 'ci-reset') reset();
    }

    function onDragover(e) {
        var dz = e.target.closest && e.target.closest('#ciDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.add('over');
    }

    function onDragleave(e) {
        var dz = e.target.closest && e.target.closest('#ciDrop');
        if (dz) dz.classList.remove('over');
    }

    function onDrop(e) {
        var dz = e.target.closest && e.target.closest('#ciDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.remove('over');
        if (e.dataTransfer && e.dataTransfer.files) setFile(e.dataTransfer.files);
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'ciFileInput';
        fileInput.accept = '.xlsx,.xls,.csv';
        fileInput.style.display = 'none';
        fileInput.addEventListener('change', function () {
            setFile(fileInput.files);
        });
        document.body.appendChild(fileInput);
        document.body.addEventListener('click', onClick);
        document.body.addEventListener('dragover', onDragover);
        document.body.addEventListener('dragleave', onDragleave);
        document.body.addEventListener('drop', onDrop);
    }

    function open() {
        wireOnce();
        S.open = true;
        S.state = 'pick';
        S.file = null;
        S.preview = [];
        S.results = [];
        S.errKey = null;
        render();
        document.addEventListener('keydown', onKeydown);
    }

    // 按钮显隐探针:同 ai-client-new.js 先例,没有 settings.workspace.manage 的员工
    // 看不到「导入名录」——不是隐藏后靠前端拦截点击。
    function wireButton(api, onImported) {
        var btn = document.getElementById('clientsImportBtn');
        if (!btn) return;
        btn.style.display = 'none';
        api.canCreateWorkspaceClient()
            .then(function (r) {
                if (!r || !r.allowed) return;
                btn.style.display = '';
                btn.onclick = function () {
                    S = { api: api, onImported: onImported };
                    open();
                };
            })
            .catch(function () {
                /* 探针失败按钮保持隐藏(fail-closed,同 P0-1 拍板口径) */
            });
    }

    window.AI = window.AI || {};
    window.AI.clientImport = { wireButton: wireButton };
})();
