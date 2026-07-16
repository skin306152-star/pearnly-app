// ============================================================
// 录入工作台 · HTML 模板与纯构建函数(发票 + 汇总表批量)
// 作用域 .dmsx · 控制器在 dms-intake.ts。标签为 i18n 键 · 渲染时 t() · 跟随语言切换。
// ============================================================
/* global escapeHtml */

function dxEsc(s: unknown): string {
    return typeof escapeHtml === 'function'
        ? escapeHtml(s == null ? '' : String(s))
        : String(s == null ? '' : s);
}

// 步骤条标签键(按任务) · 纯数据。
export const STEP_KEYS: Record<string, Array<[string, string]>> = {
    invoice: [
        ['dxi-st1', 'dxi-st1s'],
        ['dxi-st2', 'dxi-st2s'],
        ['dxi-st3', 'dxi-st3s'],
        ['dxi-st4', 'dxi-st4s'],
    ],
    summary_batch: [
        ['dxb-st1', 'dxb-st1s'],
        ['dxb-st2', 'dxb-st2s'],
        ['dxb-st3', 'dxb-st3s'],
        ['dxb-st4', 'dxb-st4s'],
    ],
};

// 任务选择器卡(发票 / 汇总表批量)· data-task 切换由控制器接管
function taskPickerHtml(t: (k: string) => string, task: string): string {
    const opt = (key: string, titleK: string, descK: string, icon: string) =>
        `<div class="dx-opt${task === key ? ' active' : ''}" data-task="${key}">` +
        `<div class="dx-opt-ic">${icon}</div>` +
        `<div class="dx-opt-c"><b>${dxEsc(t(titleK))}</b><span>${dxEsc(t(descK))}</span></div>` +
        '<div class="dx-opt-sel"></div></div>';
    const icInv =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="22" height="22"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4"/><path d="M9 11h6M9 15h6"/></svg>';
    const icSum =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="22" height="22"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 4v16M3 14h18"/></svg>';
    return (
        '<div class="dx-card dx-task">' +
        '<div class="dx-task-h">' +
        `<b>${dxEsc(t('dxk-pick-h'))}</b><span>${dxEsc(t('dxk-pick-s'))}</span></div>` +
        '<div class="dx-task-grid">' +
        opt('invoice', 'dxk-inv-t', 'dxk-inv-d', icInv) +
        opt('summary_batch', 'dxk-sum-t', 'dxk-sum-d', icSum) +
        '</div></div>'
    );
}

const TITLE_KEYS: Record<string, [string, string]> = {
    invoice: ['dxi-title', 'dxi-sub'],
    summary_batch: ['dxb-title', 'dxb-sub'],
};

export function dxShell(t: (k: string) => string, task = 'invoice'): string {
    const [titleKey, subKey] = TITLE_KEYS[task] || TITLE_KEYS.invoice;
    const steps = STEP_KEYS[task] || STEP_KEYS.invoice;
    const step = (n: number, b: string, s: string) =>
        `<div class="dx-step" data-step="${n}"><div class="dx-step-no">${n}</div>` +
        `<div class="dx-step-c"><b>${dxEsc(t(b))}</b><span>${dxEsc(t(s))}</span></div></div>`;
    return (
        '<div class="dmsx"><div class="dx-wrap">' +
        taskPickerHtml(t, task) +
        // 流程卡
        '<div class="dx-card">' +
        '<div class="dx-flow-h"><div>' +
        `<b id="dx-flow-title">${dxEsc(t(titleKey))}</b>` +
        `<p id="dx-flow-sub">${dxEsc(t(subKey))}</p></div>` +
        `<button class="btn" id="dx-records">${dxEsc(t('dxk-records'))}</button></div>` +
        '<div class="dx-stepper">' +
        steps.map((s, i) => step(i + 1, s[0], s[1])).join('') +
        '</div>' +
        // state 容器(控制器注入内部)· 共享:上传/识别中/成功;发票:复核/导出
        '<div class="dx-state active" id="dx-s-upload"></div>' +
        '<div class="dx-state" id="dx-s-searching"></div>' +
        '<div class="dx-state" id="dx-s-inv-review"></div>' +
        '<div class="dx-state" id="dx-s-inv-submit"></div>' +
        // 汇总表批量建单:上传汇总表 / 列映射+常量 / 逐行预览 / 提交结果
        '<div class="dx-state" id="dx-s-batch-up"></div>' +
        '<div class="dx-state" id="dx-s-batch-map"></div>' +
        '<div class="dx-state" id="dx-s-batch-review"></div>' +
        '<div class="dx-state" id="dx-s-batch-submit"></div>' +
        '<div class="dx-state" id="dx-s-success"></div>' +
        '</div>' + // close .dx-card(流程卡)
        // 上下文 ERP 连接卡(控制器 renderDxErpCards 按任务填充:发票/汇总表 → MR.ERP+Express)
        '<div id="dx-erp-cards" class="dx-erp-cards-zone"></div>' +
        '</div></div>' + // close .dx-wrap / .dmsx
        // 确认弹窗(站内 .modal)
        '<div class="modal-overlay" id="dx-modal-mask" style="display:none;"></div>'
    );
}
