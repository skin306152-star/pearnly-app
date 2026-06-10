// ============================================================
// REFACTOR-WB (2026-06-02) · GL-VAT 对账 · 历史列表 + 分页 · 从 gl-vat-recon.js 抽出 · verbatim 0 改逻辑。
// ============================================================
import { $, _t, _fmt, _fmtTime, _authH, _token, _lang } from './glv-helpers.js';
import { _loadTask } from './glv-results.js';
import { MORE_SVG } from './more-menu.js';

const GLV_PAGE_SIZE = 10;
var _glvAllTasks: any[] = [];
var _glvPage = 1;

function _applyGlvSearch() {
    _glvPage = 1;
    _renderGlvPage();
    var q = ((($('glv-hist-search') || {}) as HTMLInputElement).value || '').trim().toLowerCase();
    if (!q) return;
    var tbody = $('glv-history-tbody');
    if (!tbody) return;
    tbody.querySelectorAll('tr').forEach(function (tr) {
        if (!tr.dataset.taskId) return;
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
    });
}

function _renderGlvPage() {
    const tableEl = $('glv-history-table-wrap');
    const emptyEl = $('glv-history-empty');
    const tbody = $('glv-history-tbody');
    const pager = $('glv-history-pager');
    const info = $('glv-history-pager-info');
    const prev = $('glv-history-prev');
    const next = $('glv-history-next');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!_glvAllTasks.length) {
        if (tableEl) tableEl.style.display = 'none';
        if (emptyEl) emptyEl.style.display = '';
        if (pager) pager.style.display = 'none';
        return;
    }
    if (tableEl) tableEl.style.display = '';
    if (emptyEl) emptyEl.style.display = 'none';
    const totalPages = Math.ceil(_glvAllTasks.length / GLV_PAGE_SIZE);
    if (_glvPage > totalPages) _glvPage = totalPages;
    const start = (_glvPage - 1) * GLV_PAGE_SIZE;
    const pageTasks = _glvAllTasks.slice(start, start + GLV_PAGE_SIZE);
    if (pager) {
        pager.style.display = _glvAllTasks.length > GLV_PAGE_SIZE ? '' : 'none';
        if (info) info.textContent = _glvPage + ' / ' + totalPages;
        if (prev) (prev as HTMLButtonElement).disabled = _glvPage <= 1;
        if (next) (next as HTMLButtonElement).disabled = _glvPage >= totalPages;
    }
    const tasks = pageTasks;
    tasks.forEach((t) => {
        const tr = document.createElement('tr');
        tr.dataset.taskId = t.id; // v118.32.5.5.20 · 批量删多选用
        const cellTime = document.createElement('td');
        cellTime.textContent = _fmtTime(t.created_at);
        const cellFiles = document.createElement('td');
        cellFiles.className = 'glv-history-file';
        cellFiles.title = (t.vat_filename || '') + ' + ' + (t.gl_filename || '');
        cellFiles.textContent = (t.vat_filename || '?') + ' + ' + (t.gl_filename || '?');
        const cellRows = document.createElement('td');
        cellRows.className = 'glv-num';
        cellRows.textContent = (t.vat_row_count || 0) + ' / ' + (t.gl_row_count || 0);
        const cellMatched = document.createElement('td');
        cellMatched.className = 'glv-num';
        cellMatched.textContent = t.matched_count || 0;
        const cellDiff = document.createElement('td');
        cellDiff.className = 'glv-num';
        cellDiff.textContent = t.diff_count || 0;
        const cellMiss = document.createElement('td');
        cellMiss.className = 'glv-num';
        cellMiss.textContent = t.unmatched_count || 0;
        const cellAct = document.createElement('td');
        cellAct.className = 'glv-history-actions';
        // 三个图标按钮（hover 显示 tooltip · 同销项税对账风格）
        const mkBtn = (svg: string, title: string, cls: string, onClick: () => void) => {
            const b = document.createElement('button');
            b.type = 'button';
            if (cls) b.className = cls;
            b.title = title;
            b.setAttribute('aria-label', title);
            b.innerHTML = svg;
            b.onclick = onClick;
            return b;
        };
        const SVG_LOAD =
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>';
        const SVG_DL =
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>';
        const SVG_DEL =
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';
        cellAct.appendChild(mkBtn(SVG_LOAD, _t('hist_load'), '', () => _loadTask(t.id)));
        cellAct.appendChild(mkBtn(SVG_DL, _t('hist_export'), '', () => _exportTask(t.id)));
        // S9 4-bis:删除(危险)收行尾 ⋯ 菜单(开关/点外关由 more-menu 全局控制器管)
        // 二次确认在 _deleteTask
        const moreWrap = document.createElement('div');
        moreWrap.className = 'more-wrap';
        const menu = document.createElement('div');
        menu.className = 'more-menu right';
        menu.hidden = true;
        const delItem = document.createElement('button');
        delItem.type = 'button';
        delItem.className = 'mi dng';
        delItem.innerHTML = SVG_DEL;
        const delLabel = document.createElement('span');
        delLabel.textContent = _t('hist_delete');
        delItem.appendChild(delLabel);
        delItem.onclick = () => _deleteTask(t.id);
        menu.appendChild(delItem);
        moreWrap.appendChild(mkBtn(MORE_SVG, '⋯', '', () => {}));
        moreWrap.appendChild(menu);
        cellAct.appendChild(moreWrap);
        [cellTime, cellFiles, cellRows, cellMatched, cellDiff, cellMiss, cellAct].forEach((c) =>
            tr.appendChild(c)
        );
        tbody.appendChild(tr);
    });
}

function _glvInitPager() {
    var prev = $('glv-history-prev') as any;
    var next = $('glv-history-next') as any;
    if (prev && !prev._glvBound) {
        prev._glvBound = true;
        prev.addEventListener('click', function () {
            if (_glvPage > 1) {
                _glvPage--;
                _renderGlvPage();
            }
        });
    }
    if (next && !next._glvBound) {
        next._glvBound = true;
        next.addEventListener('click', function () {
            var totalPages = Math.ceil(_glvAllTasks.length / GLV_PAGE_SIZE);
            if (_glvPage < totalPages) {
                _glvPage++;
                _renderGlvPage();
            }
        });
    }
}

async function _loadHistory() {
    try {
        const res = await fetch('/api/recon/gl-vat/tasks', { headers: _authH() });
        const data = await res.json();
        _glvAllTasks = (data && data.tasks) || [];
        _glvPage = 1;
        _renderGlvPage();
        _glvInitPager();
    } catch (e) {
        console.error('[gl-vat] history load failed:', e);
    }
}

async function _exportTask(taskId: any) {
    try {
        const url = '/api/recon/gl-vat/' + taskId + '/export?lang=' + encodeURIComponent(_lang());
        const res = await fetch(url, { headers: _authH() });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'GL_VAT_recon_' + taskId + '.xlsx';
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            URL.revokeObjectURL(a.href);
            a.remove();
        }, 200);
    } catch (e) {
        console.error('[gl-vat] exportTask failed:', e);
        if (typeof showToast === 'function')
            showToast(_t('error') + ': ' + ((e as Error).message || e), 'error');
    }
}

async function _deleteTask(taskId: any) {
    // v118.32.5.4 · 用产品自带 showConfirm 替换原生 confirm()
    let ok;
    if (typeof window.showConfirm === 'function') {
        ok = await window.showConfirm(_t('confirm_delete'), { danger: true });
    } else {
        ok = confirm(_t('confirm_delete')); // 兜底
    }
    if (!ok) return;
    try {
        const res = await fetch('/api/recon/gl-vat/' + taskId, {
            method: 'DELETE',
            headers: _authH(),
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        _loadHistory();
    } catch (e) {
        console.error('[gl-vat] delete failed:', e);
        if (typeof showToast === 'function')
            showToast(_t('error') + ': ' + ((e as Error).message || e), 'error');
    }
}

export { _loadHistory, _glvInitPager, _applyGlvSearch, _renderGlvPage, _exportTask, _deleteTask };
