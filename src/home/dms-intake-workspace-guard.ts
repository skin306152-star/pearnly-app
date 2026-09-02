// ============================================================
// 录入工作台 · 复核屏「套账不符」非阻断横幅(检测 + 一键归入 + 保持)
//   真机场景(2026-08-08):美妆店销项票在冰块公司套账下上传,数据落错账本污染报表。
//   落库时 seller_routing 已按税号自动归对已存在套账;本模块只兜「无匹配/错配」——
//   复核屏检测票主税号 ≠ 当前套账税号 → 提示「切到已有套账并归入」或「建套账并归入」。
//   点「保持当前套账」会把草稿真实重绑到当前套账，不能只隐藏提示后继续。
//   错配未处理的文件不进「确认全部」(blockedIdxs 供 dms-intake-review.ts 过滤)。
// ============================================================
/* global t, showToast, withLoading */
import { esc, authHeaders } from './dms-intake-core.js';
import { IV } from './dms-intake-invoice.js';
import type { Dict } from './dms-intake-invoice.js';

type WsClient = { id: number; name?: string; tax_id?: string };

interface MismatchGroup {
    tax: string; // 归一后的 13 位税号(比对键)
    name: string; // 票主名(该税号第一张票)
    fileIdxs: number[]; // 本批内含该税号的文件下标(含已确认)
    historyIds: string[]; // 待归入的 history_ids(已确认文件排除)
    confirmedCount: number; // 其中已确认文件数(横幅注明不动)
    matchedWs: WsClient | null; // 命中我的其它套账(有 → 切换形态)
}

let _clients: WsClient[] = [];
let _clientsRequested = false;
let _groups: MismatchGroup[] = [];
let _settled = new Set<string>(); // 本批内已「保持/归入」的税号
let _batchKey = '';
let _rerender: (() => void) | null = null;

export function initGuard(rerender: () => void): void {
    _rerender = rerender;
}

// 拉我的账套列表(复用 workspace-switcher 既有桥)· 同步写回共享缓存,顶栏下拉与检测
// 同源。拉取失败保持旧缓存 —— 检测自然不打扰(无当前套账信息时宁可不拦)。
async function refreshClients(): Promise<void> {
    const w = window as unknown as { fetchWorkspaceClients?: () => Promise<unknown> };
    if (typeof w.fetchWorkspaceClients !== 'function') return;
    try {
        const l = await w.fetchWorkspaceClients();
        if (Array.isArray(l)) {
            _clients = l as WsClient[];
            window._workspaceClientsCache = _clients;
        }
    } catch {
        /* 网络失败:保持旧缓存,静默降级 */
    }
}

// 首次进入复核才拉一次账套列表;拉到后如仍在复核屏 → 补渲出横幅。
export async function ensureGuardData(): Promise<void> {
    if (_clientsRequested) return;
    _clientsRequested = true;
    await refreshClients();
    if (IV.view === 'review') _rerender?.();
}

function activeWsId(): number | null {
    const w = window as unknown as { getActiveWorkspaceClientId?: () => number | null };
    return typeof w.getActiveWorkspaceClientId === 'function'
        ? w.getActiveWorkspaceClientId()
        : null;
}

// 税号归一(去横杠/空格)· 与后端 services/workspace/seller_routing.py `_norm_tax` 同源。
function normTax(v: unknown): string {
    return String(v == null ? '' : v).replace(/[\s-]/g, '');
}

// 泰国 13 位税号 MOD-11 校验:前 12 位按权重 13..2 加权求和,
// check=(11-sum%11)%10,末位相等。
function validThaiTaxId(v: unknown): boolean {
    const s = normTax(v);
    if (!/^\d{13}$/.test(s)) return false;
    let sum = 0;
    for (let i = 0; i < 12; i++) sum += +s[i] * (13 - i);
    return +s[12] === (11 - (sum % 11)) % 10;
}

// 命中我的其它套账(排除当前活跃的)· 只认归一后相等的税号。
function findWsByTax(tax: string): WsClient | null {
    const activeId = activeWsId();
    return (
        _clients.find((c) => Number(c.id) !== Number(activeId) && normTax(c.tax_id) === tax) || null
    );
}

// 单张票的方向:识别结果自带 direction 优先(与复核屏 warnFields 同口径),否则回落本批
// 声明;两者都空 → 不检测(方向不明不知道该比卖方还是买方税号)。
function invoiceDirection(f: Dict): string {
    const d = String(f.direction || '');
    return d === 'sales' || d === 'purchase' ? d : IV.direction;
}

function detect(): void {
    _groups = [];
    const activeId = activeWsId();
    if (activeId == null) return;
    // 新一批(history_ids 指纹变了)→ 清掉上一批的「保持/归入」记忆(本批内记住语义)。
    const key = IV.results.map((r) => r.history_ids.slice().sort().join(',')).join('|');
    if (key !== _batchKey) {
        _batchKey = key;
        _settled.clear();
    }
    const current = _clients.find((c) => Number(c.id) === Number(activeId));
    if (!current) return; // 当前套账信息缺失 → 不猜,宁可不打扰
    const currentTax = normTax(current.tax_id);
    const byTax = new Map<string, MismatchGroup>();
    IV.results.forEach((r, fi) => {
        r.invoices.forEach((inv) => {
            const f = inv.fields;
            const dir = invoiceDirection(f);
            if (dir !== 'sales' && dir !== 'purchase') return;
            const tax = dir === 'sales' ? f.seller_tax : f.buyer_tax;
            // OCR 常把卖方税号幻觉复制进买方(2026-08-08 真机实锤)→ 进项票两号相同直接跳过
            if (dir === 'purchase' && String(f.seller_tax || '') === String(f.buyer_tax || '')) {
                return;
            }
            const n = normTax(tax);
            if (!validThaiTaxId(n)) return;
            // 错配判定:当前套账有税号 → 不等即错配;没税号 → 只认「命中我的其它套账」,
            // 不出「建档」形态(分不清是本套账没登记税号还是新客户,宁可不打扰)。
            const matched = findWsByTax(n);
            if (currentTax) {
                if (n === currentTax) return;
            } else if (!matched) {
                return;
            }
            let g = byTax.get(n);
            if (!g) {
                g = {
                    tax: n,
                    name:
                        dir === 'sales' ? String(f.seller_name || '') : String(f.buyer_name || ''),
                    fileIdxs: [],
                    historyIds: [],
                    confirmedCount: 0,
                    matchedWs: matched,
                };
                byTax.set(n, g);
            }
            if (!g.fileIdxs.includes(fi)) g.fileIdxs.push(fi);
            if (IV.confirmed.has(fi)) g.confirmedCount++;
            else
                r.history_ids.forEach((id) => {
                    if (!g.historyIds.includes(id)) g.historyIds.push(id);
                });
        });
    });
    _groups = Array.from(byTax.values())
        .filter((g) => !_settled.has(g.tax))
        .sort((a, b) => a.fileIdxs[0] - b.fileIdxs[0]);
}

// 错配且未处理(未归入/未保持/未确认)的文件下标 → confirm-all 过滤用。
export function blockedIdxs(): Set<number> {
    detect();
    const s = new Set<number>();
    _groups.forEach((g) =>
        g.fileIdxs.forEach((i) => {
            if (!IV.confirmed.has(i)) s.add(i);
        })
    );
    return s;
}

// ── 横幅(挂在复核屏 accordion 上方)────────────────────────────
// 多个不同错配税号 → 只展示第一组,尾注「另有 N 组」(v1 不做多组交互)。
export function guardBannerHtml(): string {
    detect();
    if (!_groups.length) return '';
    const g = _groups[0];
    const more = _groups.length - 1;
    const label = t('wsg-mismatch')
        .replace('{n}', String(g.fileIdxs.length))
        .replace('{name}', g.name || g.tax)
        .replace('{tax}', g.tax);
    // 全已确认 → 没有可归入的 id,只剩「保持」与说明
    const primary = g.historyIds.length
        ? g.matchedWs
            ? `<button class="btn small primary" data-wsg-switch>${esc(
                  t('wsg-switch-btn').replace(
                      '{name}',
                      g.matchedWs.name || g.matchedWs.tax_id || ''
                  )
              )}</button>`
            : `<button class="btn small primary" data-wsg-create>${esc(
                  t('wsg-create-btn')
              )}</button>`
        : '';
    const notes: string[] = [];
    if (g.confirmedCount > 0)
        notes.push(esc(t('wsg-confirmed-note').replace('{n}', String(g.confirmedCount))));
    if (more > 0) notes.push(esc(t('wsg-more-groups').replace('{n}', String(more))));
    return (
        `<div class="dx-wsguard">` +
        `<div class="dx-wsguard-t">${esc(label)}</div>` +
        `<div class="dx-wsguard-a">${primary}` +
        `<button class="btn small" data-wsg-keep>${esc(t('wsg-keep-btn'))}</button></div>` +
        (notes.length ? `<div class="dx-wsguard-notes">${notes.join(' · ')}</div>` : '') +
        '</div>'
    );
}

// ── 动作 ──────────────────────────────────────────────────────
function switchWorkspace(id: number): void {
    // 复用 workspace-switcher 既有切套账函数(顶栏下拉选中走的就是它)—— 它负责发
    // pearnly:workspace-changed → 全站刷新联动,不绕过它裸写 localStorage。
    const w = window as unknown as { setActiveWorkspaceClientId?: (id: number) => void };
    if (typeof w.setActiveWorkspaceClientId === 'function') w.setActiveWorkspaceClientId(id);
}

async function rebindTo(
    historyIds: string[],
    workspaceClientId: number
): Promise<{ rebound?: number; skipped?: string[] }> {
    const r = await fetch('/api/workspace/rebind-history', {
        method: 'POST',
        headers: authHeaders(true),
        body: JSON.stringify({ history_ids: historyIds, workspace_client_id: workspaceClientId }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(String(r.status));
    return d as { rebound?: number; skipped?: string[] };
}

// 归入成功后的收尾(两形态共用):本批内记「已归入」→ 全局切套账 → 按 rebound/skipped
// 诚实 toast(不吞 skipped)→ 重渲复核屏。
function finishRebind(
    g: MismatchGroup,
    d: { rebound?: number; skipped?: string[] },
    targetId: number
): void {
    const skipped = Array.isArray(d.skipped) ? d.skipped : [];
    if (skipped.length) {
        showToast(
            t('wsg-partial')
                .replace('{n}', String(d.rebound || 0))
                .replace('{m}', String(skipped.length)),
            'warn'
        );
        _rerender?.();
        return;
    }
    _settled.add(g.tax);
    switchWorkspace(targetId);
    showToast(t('wsg-done').replace('{n}', String(d.rebound || 0)), 'success');
    _rerender?.();
}

// 形态2:建套账(名取票主名 + 税号)→ 刷新账套缓存 → 归入。
async function doCreateAndRebind(btn: HTMLElement): Promise<void> {
    const g = _groups[0];
    if (!g || !g.historyIds.length) return;
    try {
        await withLoading(btn, async () => {
            const c = await fetch('/api/workspace/clients', {
                method: 'POST',
                headers: authHeaders(true),
                body: JSON.stringify({ name: g.name || g.tax, tax_id: g.tax }),
            });
            const cd = (await c.json().catch(() => ({}))) as { id?: unknown };
            if (!c.ok) throw new Error(String(c.status));
            const newId = Number(cd.id);
            if (!newId) throw new Error('create-no-id');
            await refreshClients(); // 新套账进缓存,切换后检测/顶栏才认得它
            const d = await rebindTo(g.historyIds, newId);
            finishRebind(g, d, newId);
        });
    } catch {
        showToast(t('wsg-create-fail'), 'error');
    }
}

// 形态1:已有套账命中 → 直接归入 + 切过去。
async function doSwitchAndRebind(btn: HTMLElement): Promise<void> {
    const g = _groups[0];
    const target = g?.matchedWs ?? null;
    if (!g || !target || !g.historyIds.length) return;
    try {
        await withLoading(btn, async () => {
            const d = await rebindTo(g.historyIds, target.id);
            finishRebind(g, d, target.id);
        });
    } catch {
        showToast(t('wsg-create-fail'), 'error');
    }
}

// [保持当前套账]:真实重绑草稿归属；成功后横幅才消失。
async function handleKeep(btn: HTMLElement): Promise<void> {
    const g = _groups[0];
    if (!g) return;
    const current = activeWsId();
    if (current == null || !g.historyIds.length) return;
    try {
        await withLoading(btn, async () => {
            const d = await rebindTo(g.historyIds, current);
            finishRebind(g, d, current);
        });
    } catch {
        showToast(t('wsg-create-fail'), 'error');
    }
}

export function onGuardClick(tg: HTMLElement): boolean {
    const keep = tg.closest('[data-wsg-keep]') as HTMLElement | null;
    if (keep) {
        void handleKeep(keep);
        return true;
    }
    const sw = tg.closest('[data-wsg-switch]') as HTMLElement | null;
    if (sw) {
        void doSwitchAndRebind(sw);
        return true;
    }
    const cr = tg.closest('[data-wsg-create]') as HTMLElement | null;
    if (cr) {
        void doCreateAndRebind(cr);
        return true;
    }
    return false;
}
