// ============================================================
// REFACTOR-WB-modularize · MR.ERP DMS 身份证订车流程 从 ocr-recognize.js 拆出
//
// 与发票热路径隔离:单张身份证 → POST /api/dms/id-card-booking → renderDmsIdCardResult。
// btn-start(ocr-recognize.js)thai_id_card 模式经 ESM import 调 _runDmsIdCardFlow。
// ============================================================
/* global _selectedFiles, token, renderFileList, updateStartButton */
async function _runDmsIdCardFlow(forceFile?: File) {
    let f: SelectedFile;
    if (forceFile) {
        f = _selectedFiles.find((x) => x.file === forceFile) || {
            file: forceFile,
            name: forceFile.name,
            status: 'waiting',
        };
    } else {
        const pending = _selectedFiles.filter((x) => x.status === 'waiting');
        if (!pending.length) return;
        f = pending[0]; // 身份证订车按单张处理
    }
    window._dmsLastFile = f.file;
    f.status = 'processing';
    if (typeof renderFileList === 'function') renderFileList();

    try {
        const form = new FormData();
        form.append('file', f.file, f.name);
        form.append('push', 'true');
        const resp = await fetch('/api/dms/id-card-booking', {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token },
            body: form,
        });

        if (resp.status === 401 || resp.status === 403) {
            const body = await resp
                .clone()
                .json()
                .catch(() => ({}));
            const _det = body && body.detail;
            const code = typeof _det === 'string' ? _det : (_det && _det.code) || '';
            if (!code || code.startsWith('auth.')) {
                localStorage.removeItem('mrpilot_token');
                showToast(t('alert-session'), 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1200);
                return;
            }
        }

        const data = await resp.json().catch(() => ({}));
        if (!resp.ok) {
            f.status = 'error';
            const code = (data && data.detail && (data.detail.code || data.detail)) || 'unknown';
            f.errorKey = 'err.' + code;
            f.canRetry = true;
            if (typeof renderFileList === 'function') renderFileList();
            if (typeof window.renderDmsIdCardResult === 'function') {
                window.renderDmsIdCardResult({
                    ok: false,
                    dms_push: { status: 'failed', error_code: String(code) },
                });
            }
            return;
        }

        // OCR 成功(后端 ok 反映 DMS 推送是否成功 · needs_review 也是 ok:true)
        f.status =
            data.ok || (data.dms_push && data.dms_push.status === 'needs_review')
                ? 'success'
                : 'error';
        if (typeof renderFileList === 'function') renderFileList();
        if (typeof window.renderDmsIdCardResult === 'function') window.renderDmsIdCardResult(data);
        if (typeof updateStartButton === 'function') updateStartButton();
    } catch (e) {
        f.status = 'error';
        f.canRetry = true;
        if (typeof renderFileList === 'function') renderFileList();
        if (typeof window.renderDmsIdCardResult === 'function') {
            window.renderDmsIdCardResult({
                ok: false,
                dms_push: { status: 'failed', error_code: 'network' },
            });
        }
    }
}

// 结果块「重试」按钮回调(dms-id-card-results.js 触发)· 复跑上一张身份证。
window._dmsRetryIdCard = function () {
    if (window._dmsLastFile) _runDmsIdCardFlow(window._dmsLastFile);
};

export { _runDmsIdCardFlow };
