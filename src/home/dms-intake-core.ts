// ============================================================
// 录入工作台 · 共享状态 S + DOM/请求工具(发票 + 汇总表批量共用)
// 控制器 dms-intake.ts;发票流 dms-intake-invoice.ts;汇总表批量 dms-intake-batch.ts。
// ============================================================
/* global escapeHtml, token */
import { saveStep } from './step-resume.js';

export const S = {
    task: 'invoice' as 'invoice' | 'summary_batch',
    step: 1,
};

export function esc(s: unknown) {
    return typeof escapeHtml === 'function' ? escapeHtml(String(s ?? '')) : String(s ?? '');
}
export function sec(): HTMLElement | null {
    return document.getElementById('page-dms-intake');
}
export function $(id: string) {
    return document.getElementById(id);
}
export function authHeaders(json = false): Record<string, string> {
    const h: Record<string, string> = { Authorization: 'Bearer ' + token };
    if (json) h['Content-Type'] = 'application/json';
    return h;
}

export function showStep(step: number, stateId: string) {
    S.step = step;
    saveStep('dms-intake', step, S.task);
    sec()
        ?.querySelectorAll('.dx-state')
        .forEach((s) => s.classList.remove('active'));
    $(stateId)?.classList.add('active');
    // 手机端紧凑步骤条「第 N/4 步」· 桌面 ::after 隐藏
    sec()
        ?.querySelector('.dx-stepper')
        ?.setAttribute('data-frac', step + ' / 4');
    sec()
        ?.querySelectorAll('.dx-step')
        .forEach((el, i) => {
            const n = i + 1;
            el.classList.toggle('active', n === step);
            el.classList.toggle('done', n < step);
            const no = el.querySelector('.dx-step-no');
            if (no) no.textContent = n < step ? '✓' : String(n);
        });
}
