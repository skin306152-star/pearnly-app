/*
 * Pearnly AI · ai-payroll.js · H1b 工资表 ภ.ง.ด.1 工具卡(顶层独立视图)编排:选客户/
 * 期间 → 上传 Excel → 猜列/确认映射 → 提交校验落库 → 三产出下载 + 手工加行
 *
 * 顶层导航位(id=v-payroll,同 /fileconv /vatcheck 先例)。parse 无状态纯读(POST
 * /api/payroll/parse);commit 落库 + 点亮义务(POST /api/payroll/commit,column_map/
 * fixed_values/manual_entries 随 file 一起重传——后端整体替换,不依赖上一次请求的
 * 服务端状态,同 K1b 两段式先例)。同表头第二次上传命中模板(template_hit)→ 跳过
 * 映射确认直接提交(方案验收断言 #3)。状态机 + 网络 + 事件委托在本文件,HTML 拼装
 * 交给 AI.payrollRender(纯函数,零网络依赖)——同 ai-fileconv.js 先例。
 *
 * 依赖 window.AI.state/api/format/payrollRender 与全局 at(),排在它们之后、ai.js
 * 之前加载(见 scripts/build-home-js.mjs)。
 *
 * ภ.ง.ด.1ก 年度聚合(批次 H 收尾件)——独立于上面月度状态机的小面板(loadAnnualSummary/
 * downloadAnnual),渲染委托 AI.payrollAnnualRender(ai-payroll-annual-render.js),
 * render() 里常驻拼在页面末尾。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };
    var R = function () {
        return AI.payrollRender;
    };

    var S = null;
    var wired = false;
    var fileInput = null; // 持久隐藏文件选择器(单例,不随 render 重建 → File 不丢,同 ai-fileconv.js 先例)

    function body() {
        return $('prBody');
    }

    function freshState(api) {
        return {
            api: api,
            clients: [],
            clientId: '',
            period: R().defaultPeriod(),
            file: null,
            parsing: false,
            committing: false,
            parseResult: null,
            columnMap: {},
            incomeCodeFixed: '',
            paidDateFixed: '',
            commitResult: null,
            manualEntries: [],
            manualForm: null,
            downloading: {},
            errKey: null,
            // ภ.ง.ด.1ก 年度聚合(批次 H 收尾件)——独立于上面月度进料状态机的小面板状态。
            annualYear: AI.payrollAnnualRender.defaultTaxYear(),
            annualSummary: null,
            annualLoading: false,
            annualDownloading: false,
            annualErrKey: null,
        };
    }

    function render() {
        body().innerHTML = R().pageHtml(S) + AI.payrollAnnualRender.panelHtml(S);
    }

    function loadClients() {
        S.api
            .listClients()
            .then(function (r) {
                if (!S) return;
                S.clients = (r && r.clients) || [];
                render();
            })
            .catch(function () {
                /* 客户列表加载失败不阻断本卡其余功能,选择器留空由会计重试上传触发重拉 */
            });
    }

    function pickFile() {
        fileInput.value = '';
        fileInput.click();
    }

    function setFile(list) {
        var file = (list || [])[0];
        if (!file) return;
        var check = R().validateFile(file);
        if (!check.ok) {
            S.file = null;
            S.errKey = check.errKey;
            render();
            return;
        }
        S.file = file;
        S.errKey = null;
        S.parseResult = null;
        S.commitResult = null;
        render();
        runParse();
    }

    function clearFile() {
        S.file = null;
        S.parseResult = null;
        S.commitResult = null;
        S.errKey = null;
        render();
    }

    function readyToParse() {
        return S.clientId && R().isPeriodValid(S.period) && S.file && !S.parsing;
    }

    function runParse() {
        if (!readyToParse()) return;
        var session = S;
        S.parsing = true;
        S.errKey = null;
        render();
        S.api
            .parsePayroll(S.file, S.clientId, S.period)
            .then(function (result) {
                if (S !== session) return;
                S.parsing = false;
                S.parseResult = result;
                S.columnMap = {};
                Object.keys(result.guessed || {}).forEach(function (f) {
                    S.columnMap[f] = result.guessed[f].column;
                });
                S.incomeCodeFixed = result.income_code || '';
                S.paidDateFixed = (result.fixed_values || {}).paid_date || '';
                render();
                if (result.template_hit) runCommit([]);
            })
            .catch(function (err) {
                if (S !== session) return;
                S.parsing = false;
                S.errKey = mapErrKey(err);
                render();
            });
    }

    function mapErrKey(err) {
        var key = AI.api.mapApiErrorKey(err && err.code);
        return at(key) !== key ? key : 'err_generic';
    }

    function buildColumnMap() {
        var out = {};
        R().FIELD_ORDER.forEach(function (f) {
            var v = S.columnMap[f];
            if (v !== null && v !== undefined && v !== '') out[f] = Number(v);
        });
        return out;
    }

    function buildFixedValues() {
        var out = Object.assign({}, (S.parseResult && S.parseResult.fixed_values) || {});
        if (
            (S.columnMap.income_code === '' || S.columnMap.income_code == null) &&
            S.incomeCodeFixed
        ) {
            out.income_code = S.incomeCodeFixed;
        } else {
            delete out.income_code;
        }
        if ((S.columnMap.paid_date === '' || S.columnMap.paid_date == null) && S.paidDateFixed) {
            out.paid_date = S.paidDateFixed;
        } else {
            delete out.paid_date;
        }
        return out;
    }

    function runCommit(manualEntriesOverride) {
        if (S.committing || !S.file) return;
        var session = S;
        S.committing = true;
        S.errKey = null;
        render();
        var manual = manualEntriesOverride !== undefined ? manualEntriesOverride : S.manualEntries;
        S.api
            .commitPayroll(S.file, {
                workspaceClientId: S.clientId,
                period: S.period,
                columnMap: buildColumnMap(),
                fixedValues: buildFixedValues(),
                incomeCode: S.incomeCodeFixed || (S.parseResult && S.parseResult.income_code),
                manualEntries: manual,
            })
            .then(function (result) {
                if (S !== session) return;
                S.committing = false;
                S.commitResult = result;
                S.manualEntries = manual;
                S.manualForm = null;
                render();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.committing = false;
                S.errKey = mapErrKey(err);
                render();
            });
    }

    function download(kind) {
        if (S.downloading[kind]) return;
        var session = S;
        S.downloading[kind] = true;
        render();
        S.api
            .downloadPayrollOutput(S.clientId, S.period, kind)
            .then(function (r) {
                if (S !== session) return;
                var url = URL.createObjectURL(r.blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = r.filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
            })
            .catch(function (err) {
                if (S !== session) return;
                S.errKey = mapErrKey(err);
            })
            .then(function () {
                if (S !== session) return;
                S.downloading[kind] = false;
                render();
            });
    }

    // ภ.ง.ด.1ก 年度聚合(批次 H 收尾件)——先拉 JSON 汇总(Σ支付/Σ预扣 + issues)看清楚
    // 再下载,同月报 parse→commit 两段式先例,不闷头吐文件。
    function loadAnnualSummary() {
        var ready = S.clientId && AI.payrollAnnualRender.isTaxYearValid(S.annualYear);
        if (!ready || S.annualLoading) return;
        var session = S;
        S.annualLoading = true;
        S.annualErrKey = null;
        S.annualSummary = null;
        render();
        S.api
            .getPayrollAnnualSummary(S.clientId, S.annualYear)
            .then(function (result) {
                if (S !== session) return;
                S.annualLoading = false;
                S.annualSummary = result;
                render();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.annualLoading = false;
                S.annualErrKey = mapErrKey(err);
                render();
            });
    }

    function downloadAnnual() {
        if (S.annualDownloading) return;
        var session = S;
        S.annualDownloading = true;
        render();
        S.api
            .downloadPayrollAnnualOutput(S.clientId, S.annualYear, 'keying')
            .then(function (r) {
                if (S !== session) return;
                var url = URL.createObjectURL(r.blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = r.filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
            })
            .catch(function (err) {
                if (S !== session) return;
                S.annualErrKey = mapErrKey(err);
            })
            .then(function () {
                if (S !== session) return;
                S.annualDownloading = false;
                render();
            });
    }

    function reset() {
        S.file = null;
        S.parseResult = null;
        S.commitResult = null;
        S.columnMap = {};
        S.manualEntries = [];
        S.manualForm = null;
        S.errKey = null;
        render();
    }

    function manualFieldsFromForm() {
        var out = {};
        body()
            .querySelectorAll('[data-manual]')
            .forEach(function (el) {
                out[el.getAttribute('data-manual')] = el.value;
            });
        return out;
    }

    function submitManual() {
        var entry = manualFieldsFromForm();
        if (!R().manualEntryValid(entry)) return;
        runCommit(S.manualEntries.concat([entry]));
    }

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'pr-pick' || a === 'pr-goto-upload') pickFile();
        else if (a === 'pr-clear-file') clearFile();
        else if (a === 'pr-confirm') runCommit([]);
        else if (a === 'pr-download') download(el.getAttribute('data-kind'));
        else if (a === 'pr-reset') reset();
        else if (a === 'pr-manual-open') {
            S.manualForm = {};
            render();
        } else if (a === 'pr-manual-cancel') {
            S.manualForm = null;
            render();
        } else if (a === 'pr-manual-submit') submitManual();
        else if (a === 'pr-annual-summary') loadAnnualSummary();
        else if (a === 'pr-annual-download') downloadAnnual();
    }

    function onChange(e) {
        var t = e.target;
        if (t.id === 'prAnnualYearInput') {
            S.annualYear = t.value.trim();
            S.annualSummary = null;
            S.annualErrKey = null;
            render();
            return;
        }
        if (t.id === 'prClientSel' || t.id === 'prPeriodInput') {
            if (t.id === 'prClientSel') S.clientId = t.value;
            else S.period = t.value.trim();
            // 换客户/改期间作废已拿到的映射结果(防误把 A 客户的映射套去 B 客户提交),
            // 文件仍在的话直接重新识别,免得会计还得重新拖一次文件。
            S.parseResult = null;
            S.commitResult = null;
            if (S.file) runParse();
            else render();
            return;
        }
        if (t.hasAttribute('data-field')) {
            S.columnMap[t.getAttribute('data-field')] = t.value;
            render();
            return;
        }
        if (t.hasAttribute('data-fixed')) {
            if (t.getAttribute('data-fixed') === 'income_code') S.incomeCodeFixed = t.value;
            else S.paidDateFixed = t.value;
            return;
        }
        if (t.hasAttribute('data-manual')) {
            if (S.manualForm) S.manualForm[t.getAttribute('data-manual')] = t.value;
            render();
        }
    }

    function onDragover(e) {
        var dz = e.target.closest && e.target.closest('#prDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.add('over');
    }

    function onDragleave(e) {
        var dz = e.target.closest && e.target.closest('#prDrop');
        if (dz) dz.classList.remove('over');
    }

    function onDrop(e) {
        var dz = e.target.closest && e.target.closest('#prDrop');
        if (!dz) return;
        e.preventDefault();
        dz.classList.remove('over');
        if (e.dataTransfer && e.dataTransfer.files) setFile(e.dataTransfer.files);
    }

    function onKeydown(e) {
        if (e.target && e.target.id === 'prDrop' && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            pickFile();
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'prFileInput';
        fileInput.accept = '.xlsx,.xls';
        fileInput.style.display = 'none';
        fileInput.addEventListener('change', function () {
            setFile(fileInput.files);
        });
        document.body.appendChild(fileInput);
        var host = body();
        host.addEventListener('click', onClick);
        host.addEventListener('change', onChange);
        host.addEventListener('dragover', onDragover);
        host.addEventListener('dragleave', onDragleave);
        host.addEventListener('drop', onDrop);
        host.addEventListener('keydown', onKeydown);
    }

    function mount(api) {
        S = freshState(api);
        wireOnce();
        render();
        loadClients();
    }

    window.AI = window.AI || {};
    window.AI.payroll = { mount: mount };
})();
