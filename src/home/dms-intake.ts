// ============================================================
// 录入工作台 · 任务主控(发票/收据录入 + 汇总表→批量建单)
// 两张任务卡切换 + 事件委托 + 导航 + window.loadDmsIntake。
// 发票流程见 dms-intake-invoice.ts;汇总表批量见 dms-intake-batch.ts;
// 共享状态/工具见 dms-intake-core.ts;壳模板见 dms-intake-html.ts。
// ============================================================
import { dxShell } from './dms-intake-html.js';
import { S, sec, showStep } from './dms-intake-core.js';
import {
    IV,
    resetInvoice,
    renderInvoiceUpload,
    rerenderInvoice,
    onInvoiceClick,
    onInvoiceChange,
    onInvoiceDrop,
} from './dms-intake-invoice.js';
import { readStep } from './step-resume.js';
import { renderDxErpCards } from './dms-intake-erp-cards.js';
import {
    B,
    resetBatch,
    renderBatchUpload,
    rerenderBatch,
    onBatchClick,
    onBatchChange,
    onBatchDrop,
} from './dms-intake-batch.js';
import { onBatchReviewClick, rerenderBatchReview } from './dms-intake-batch-review.js';
import { onBatchSubmitClick } from './dms-intake-batch-submit.js';

// ── 导航 / 重置 ──────────────────────────────────────────────
function resetFlow() {
    if (S.task === 'summary_batch') {
        resetBatch();
        renderBatchUpload();
        showStep(1, 'dx-s-batch-up');
    } else {
        resetInvoice();
        renderInvoiceUpload();
        showStep(1, 'dx-s-upload');
    }
}

// 任务切换:重渲整壳(任务选择器高亮 + 标题/步骤条按任务)· 委托监听挂在 section 上,innerHTML 重写不丢
function selectTask(task: 'invoice' | 'summary_batch') {
    if (S.task === task) return;
    S.task = task;
    const el = sec();
    if (!el) return;
    el.innerHTML = dxShell(t, S.task);
    renderDxErpCards(S.task);
    resetFlow();
}

// 查看记录:两任务均进识别记录页
function openRecords() {
    if (typeof window.routeTo === 'function') window.routeTo('history');
}

// ── 事件委托 ──────────────────────────────────────────────────
function bind() {
    const el = sec();
    if (!el || (el as HTMLElement).dataset.dxBound) return;
    (el as HTMLElement).dataset.dxBound = '1';

    el.addEventListener('click', (ev) => {
        const tg = ev.target as HTMLElement;
        const taskCard = tg.closest('[data-task]') as HTMLElement | null;
        if (taskCard) return selectTask(taskCard.dataset.task as 'invoice' | 'summary_batch');
        if (tg.closest('#dx-records')) return openRecords();
        if (S.task === 'summary_batch') {
            if (tg.closest('#dxb-restart')) return resetFlow();
            if (onBatchReviewClick(tg)) return;
            if (onBatchSubmitClick(tg)) return;
            return onBatchClick(tg);
        }
        onInvoiceClick(tg);
    });

    el.addEventListener('change', (ev) => {
        const tg = ev.target as HTMLElement;
        if (S.task === 'summary_batch') return onBatchChange(tg);
        onInvoiceChange(tg);
    });

    el.addEventListener('dragover', (ev) => {
        if (S.step !== 1) return;
        ev.preventDefault();
        el.querySelector('.dx-drop')?.classList.add('drag-over');
    });
    el.addEventListener('dragleave', () =>
        el.querySelector('.dx-drop')?.classList.remove('drag-over')
    );
    el.addEventListener('drop', (ev) => {
        if (S.step !== 1) return;
        ev.preventDefault();
        el.querySelector('.dx-drop')?.classList.remove('drag-over');
        const files = (ev as DragEvent).dataTransfer?.files;
        if (S.task === 'summary_batch') return onBatchDrop(files);
        void onInvoiceDrop(files);
    });
}

// 续步:软导航回来时复原到离开的那一步。只在内存态够复原该步时才复原,否则回落第 1 步
// (硬刷新后内存态已空 → 守门不通过 → 干净从头)。成功页不复原。
function resumeFlow(): boolean {
    const memo = readStep('dms-intake', S.task);
    if (!memo) return false;
    if (S.task === 'summary_batch') {
        return rerenderBatch() || rerenderBatchReview();
    }
    if (IV.view !== 'review' && IV.view !== 'submit') return false;
    rerenderInvoice();
    return true;
}

window.loadDmsIntake = function () {
    const el = sec();
    if (!el) return;
    el.innerHTML = dxShell(t, S.task);
    renderDxErpCards(S.task);
    bind();
    if (!resumeFlow()) resetFlow();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('dms-intake', () => {
        if (!sec()?.querySelector('.dmsx')) return;
        sec()!.innerHTML = dxShell(t, S.task);
        renderDxErpCards(S.task);
        if (S.task === 'summary_batch') {
            if (B.view === 'map') return void rerenderBatch();
            if (B.view === 'review') return void rerenderBatchReview();
            renderBatchUpload();
            return showStep(1, 'dx-s-batch-up');
        }
        rerenderInvoice();
    });
}
