// ============================================================
// MR.ERP DMS 身份证订车流程(两步流 · 2026-06-13)
//
// 单张身份证 → POST /api/dms/id-card/recognize(只 OCR + 查 DMS)→ 打开可编辑面板
// (dms-id-card-results.ts 的 openDmsIdCardPanel),用户核对/编辑后才推送。
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
        const resp = await fetch('/api/dms/id-card/recognize', {
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
            const k = 'dms-err-' + String(code).toLowerCase();
            const msg = t(k);
            showToast(msg && msg !== k ? msg : t('dic-recognize-fail'), 'error');
            return;
        }

        // OCR 字段不全(缺身份证号/姓名)→ 提示重拍 · 不开面板
        if (data.needs_review) {
            f.status = 'error';
            f.canRetry = true;
            if (typeof renderFileList === 'function') renderFileList();
            showToast(t('dic-needs-review'), 'warn');
            return;
        }

        f.status = 'success';
        if (typeof renderFileList === 'function') renderFileList();
        if (typeof updateStartButton === 'function') updateStartButton();
        if (typeof window.openDmsIdCardPanel === 'function') window.openDmsIdCardPanel(data);
    } catch (e) {
        f.status = 'error';
        f.canRetry = true;
        if (typeof renderFileList === 'function') renderFileList();
        showToast(t('dic-recognize-fail'), 'error');
    }
}

export { _runDmsIdCardFlow };
