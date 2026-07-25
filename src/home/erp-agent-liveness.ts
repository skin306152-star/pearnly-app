// ============================================================
// 小助手(companion)活性判定 · 单一判据
// Express 靠会计电脑上的小助手写本地 DBF,小助手不在线时票只排队不落地 —— 界面必须
// 照实说。判据抽成模块是因为不止一处要用(录入工作台 ERP 卡、连接向导、日后的推送
// 就绪度体检),各写一份必漂。
// 心跳链路:小助手 POST /api/erp/agent/heartbeat → 服务端写 config.agent_last_seen_at;
// 小助手主动退出时上报 offline,服务端把时间戳写成 1970 让前端立刻转灰。
// ============================================================

export interface AgentEndpoint {
    adapter?: string;
    config?: Record<string, unknown>;
}

// 3 分钟内有心跳算在线 —— 与连接向导 erp-express-wizard 同一判据,别各调各的。
const ONLINE_MS = 180000;
// 小助手上下线只体现在心跳时间戳上,没有推事件;不轮询就冻结在开页那一刻的快照。
const POLL_MS = 30000;

// 拿不准一律判离线:缺字段、从未配对、时间戳损坏都不许显示「已连接」。
// MR.ERP 是云端直连,没有小助手这回事,恒不离线。
export function isAgentOffline(ep: AgentEndpoint): boolean {
    if (String(ep.adapter || '').toLowerCase() !== 'express') return false;
    const seen = ep.config?.agent_last_seen_at;
    const ts = seen ? new Date(String(seen)).getTime() : NaN;
    return isNaN(ts) || Date.now() - ts >= ONLINE_MS;
}

let timer = 0;

export function stopAgentPolling(): void {
    window.clearInterval(timer);
}

// anchor 脱离 DOM(壳重渲 / 切走页面)即自我了断,免得留野定时器并发打后端。
export function startAgentPolling(anchor: HTMLElement, tick: () => void): void {
    stopAgentPolling();
    timer = window.setInterval(() => {
        if (!anchor.isConnected) return stopAgentPolling();
        if (!document.hidden) tick();
    }, POLL_MS);
}
