// ============================================================
// REFACTOR-WB (2026-06-02) · GL-VAT 对账 · 运行对账 + 导出 · 从 gl-vat-recon.js 抽出 · verbatim 0 改逻辑。
// ============================================================
/* global showConfirm */
import { STATE } from './glv-store.js';
import { $, _t, _fmt, _glvFailMsg, _renderKpi, _authH, _token, _lang } from './glv-helpers.js';
import { _glvFiles, _updateRunButton } from './glv-upload.js';
import { _renderTable, _renderSummary, _expandResults } from './glv-results.js';
import { _loadHistory } from './glv-history.js';

// ── 跑对账 ──────────────────────────────────────────────────────
async function _run() {
    if (!STATE.glFile || !STATE.vatFile) {
        if (typeof showToast === 'function') showToast(_t('need_files'), 'warn');
        return;
    }
    STATE.running = true;
    _updateRunButton();
    const status = $('glv-status');
    const progress = $('glv-progress');
    const progressSub = $('glv-progress-sub');
    if (status) {
        status.className = 'vex-action-info muted';
        status.style.color = '';
        status.innerHTML = '<span>' + _t('running') + '</span>';
    }
    if (progress) progress.style.display = '';
    if (progressSub)
        progressSub.textContent =
            ((STATE.vatFile as unknown as File).name || 'VAT') +
            ' + ' +
            ((STATE.glFile as unknown as File).name || 'GL');

    const fd = new FormData();
    // v118.35.0.3 · multi-file · 同 key 多次 append → 后端 List[UploadFile]
    const _vats = _glvFiles('vatFile');
    const _gls = _glvFiles('glFile');
    for (const f of _vats) fd.append('vat_files', f, f.name);
    for (const f of _gls) fd.append('gl_files', f, f.name);
    const prefix =
        (($('glv-prefix') && ($('glv-prefix') as HTMLInputElement).value) || '4').trim() || '4';
    fd.append('revenue_prefix', prefix);
    fd.append('lang', _lang()); // v118.32.5 · 后端按 lang 返回错误消息

    try {
        // BUG-FIX-RECON-ASYNC #16 · 改异步:submit 秒回 job_id → 轮询 → 用 result_id 取结果
        const submitRes = await fetch('/api/recon/gl-vat/submit', {
            method: 'POST',
            headers: _authH(),
            body: fd,
        });
        // 兜底:网关非 JSON 错误页不再抛 "Unexpected token '<'"
        let sub = null;
        try {
            sub = await submitRes.json();
        } catch (_) {
            sub = null;
        }
        if (!submitRes.ok || !sub || !sub.ok || !sub.job_id) {
            throw new Error(
                (sub && sub.detail) || (sub && sub.error) || 'HTTP ' + submitRes.status
            );
        }
        // 轮询 · 转圈旁实时显示「共 X/Y 个文件」
        const _glvSub = $('glv-progress-sub');
        const job = (await window._reconPollJob(sub.job_id, _token(), {
            onProgress: (p: unknown) => {
                if (_glvSub)
                    _glvSub.textContent = window._reconProgressText(
                        p as { stage?: string; stage_total?: number; stage_done?: number },
                        _lang()
                    );
            },
        })) as { status?: string; result_id?: string; error_code?: string } | null;
        if (!job || job.status !== 'done' || !job.result_id) {
            // M3-2 修(2026-05-25):失败时用后端 error_code 映射成可读文案 · 不再泛化 "เกิดข้อผิดพลาด"
            if (job && job.status === 'failed' && job.error_code) {
                throw new Error(_glvFailMsg(job.error_code));
            }
            throw new Error(_t('error') || 'Error');
        }
        // 用 result_id 调现有结果接口(GET 形状与 run 一致)
        const res = await fetch('/api/recon/gl-vat/' + encodeURIComponent(job.result_id), {
            headers: _authH(),
        });
        let data = null;
        try {
            data = await res.json();
        } catch (_) {
            data = null;
        }
        if (!res.ok || !data || !data.ok) {
            throw new Error((data && data.detail) || (data && data.error) || 'HTTP ' + res.status);
        }
        STATE.currentTaskId = data.task_id;
        STATE.lastDetail = data.detail || [];
        STATE.lastSummary = data.summary || {};
        _renderKpi(data.stats || {});
        _renderTable(STATE.lastDetail);
        _renderSummary(STATE.lastSummary);
        const rs = $('glv-result');
        if (rs) rs.style.display = '';
        _expandResults();
        // 识别完成 → 自动下载对账报告一次(复用导出按钮逻辑 · 用户仍可手动再下)
        void _export();
        if (status) {
            status.className = 'vex-action-info ok';
            status.style.color = '';
            status.innerHTML =
                '<span>' +
                _t('done') +
                ' · GL ' +
                (data.gl_row_count || 0) +
                ' · VAT ' +
                (data.vat_row_count || 0) +
                '</span>';
        }
        // M3-1 修(2026-05-25):成功后刷新「近期对账任务」· 此前只渲染结果区 · 历史表不更新
        _loadHistory();
    } catch (e) {
        console.error('[gl-vat] run failed:', e);
        if (status) {
            status.className = 'vex-action-info';
            status.style.color = '#ef4444';
            status.innerHTML =
                '<span>' + _t('error') + ': ' + ((e as Error).message || e) + '</span>';
        }
    } finally {
        STATE.running = false;
        if (progress) progress.style.display = 'none';
        _updateRunButton();
    }
}

// ── 导出 Excel ──────────────────────────────────────────────────
async function _export() {
    if (!STATE.currentTaskId) return;
    try {
        const url =
            '/api/recon/gl-vat/' +
            STATE.currentTaskId +
            '/export?lang=' +
            encodeURIComponent(_lang());
        const res = await fetch(url, { headers: _authH() });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'GL_VAT_recon_' + STATE.currentTaskId + '.xlsx';
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            URL.revokeObjectURL(a.href);
            a.remove();
        }, 200);
    } catch (e) {
        console.error('[gl-vat] export failed:', e);
        if (typeof showToast === 'function')
            showToast(_t('error') + ': ' + ((e as Error).message || e), 'error');
    }
}

export { _run, _export };
