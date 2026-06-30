// 多步流程「续步记忆」(轻量版 · 只记步号)
// localStorage 记住用户停在第几步;每步数据仍由各模块自己的内存态承载。
// 软导航(不刷新)离开再回来 → 各模块用 readStep() + 「内存态是否够复原该步」自行守门复原;
// 硬刷新后内存态已空 → 守门不通过 → 自然回落第 1 步。各视图共用同一套键,行为统一。
const PREFIX = 'pearnly_step_';

export interface StepMemo {
    step: number;
    ctx?: string; // 同一视图多子流程区分(录入=task · 对账=tab)
}

// step<=1 视为「回到起点/已完成」→ 清掉记忆,避免下次误复原到空步。
export function saveStep(flow: string, step: number, ctx?: string): void {
    try {
        if (step > 1) localStorage.setItem(PREFIX + flow, JSON.stringify({ step, ctx }));
        else localStorage.removeItem(PREFIX + flow);
    } catch {
        // 隐私模式 localStorage 不可用 → 续步降级为不记忆,主流程不受影响
    }
}

export function readStep(flow: string): StepMemo | null {
    try {
        const raw = localStorage.getItem(PREFIX + flow);
        if (!raw) return null;
        const m = JSON.parse(raw) as StepMemo;
        return typeof m?.step === 'number' && m.step > 1 ? m : null;
    } catch {
        return null;
    }
}

export function clearStep(flow: string): void {
    try {
        localStorage.removeItem(PREFIX + flow);
    } catch {
        // noop
    }
}
