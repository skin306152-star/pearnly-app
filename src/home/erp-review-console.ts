// ERP 推送复核台 · 批量网格(按异常复核)
//
// 纯渲染 + 事件层:一批识别完的单据 → 批量表格,默认只摊开需人工处理的异常,
// 其余已就绪项折叠成一条汇总。数据与文案由调用方注入(不绑全局 i18n / token),
// 与 image-viewer.ts 同范式,便于独立验证与后续接 /api/history 真数据。
//
// A1 范围:主界面网格(横幅 + 筛选 tab + 表格 + 折叠条 + 底栏)。逐张核对遮罩(A2)、
// 推送闭环(D)另做。行操作经 onOpenRow 回调外抛,本模块不决定打开什么。

export type RowState = 'ready' | 'confirm' | 'new' | 'unread';
export type RowDir = 'in' | 'out';

export interface DestTag {
    kind: 'reuse' | 'new' | 'exp';
    code?: string;
}

export interface ReviewRow {
    id: string;
    dir: RowDir;
    docno: string;
    party: string;
    amount: string; // 已格式化;空串表示无金额(银行/识别失败)
    state: RowState;
    account?: string;
    dests?: DestTag[];
    bank?: boolean;
}

export type FilterKey = 'need' | 'ready' | 'unread' | 'all';

export interface ConsoleLabels {
    title: string;
    accountSet: string;
    agentOnline: string;
    // 流水线四段
    stages: [string, string, string, string];
    stageDetails: [string, string, string, string];
    bannerHead: string; // 含 {n}
    bannerSub: string;
    acceptAll: string; // 含 {n}
    tabs: Record<FilterKey, string>;
    colDir: string;
    colDoc: string;
    colAmount: string;
    colAccount: string;
    colDest: string;
    colState: string;
    dirIn: string;
    dirOut: string;
    stateReady: string;
    stateConfirm: string;
    stateNew: string;
    stateUnread: string;
    destReuse: string; // 含 {code}
    destNew: string;
    destExp: string;
    collapseReady: string; // 含 {n}
    collapseNeed: string; // 含 {n}
    hintOpen: string;
    reviewStart: string;
    push: string;
    progress: string; // 含 {done}{total}
    remain: string; // 含 {n}
}

export interface ConsoleData {
    rows: ReviewRow[];
    readyCount: number; // 已就绪总数(含未在 rows 里逐条列出的折叠项)
    total: number;
    unreadCount: number;
}

export interface ConsoleOptions {
    data: ConsoleData;
    labels: ConsoleLabels;
    onOpenRow?: (id: string) => void;
    onPush?: () => void;
    onAcceptAll?: () => void;
}

// 线性图标(描边 SVG · 与产品图标语言一致 · 无 emoji)
const IC = {
    check: '<path d="M20 6 9 17l-5-5"/>',
    spark: '<path d="M12 3l1.4 4L17.5 8.5 13.4 10 12 14l-1.4-4L6.5 8.5 10.6 7z"/>',
    alert: '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h16.9a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    bank: '<path d="M3 21h18M4 10v10M20 10v10M9 10v10M15 10v10M12 3 3.5 8h17z"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
};

function icon(name: keyof typeof IC, cls = ''): string {
    return `<svg class="rc-ic ${cls}" viewBox="0 0 24 24">${IC[name]}</svg>`;
}

function esc(s: string): string {
    return String(s == null ? '' : s).replace(
        /[&<>"']/g,
        (c) =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string
    );
}

function fill(tpl: string, vars: Record<string, string | number>): string {
    return tpl.replace(/\{(\w+)\}/g, (_, k) => esc(String(vars[k] ?? '')));
}

const STATE_CLS: Record<RowState, string> = {
    ready: 'ready',
    confirm: 'confirm',
    new: 'new',
    unread: 'unread',
};

function destPill(d: DestTag, L: ConsoleLabels): string {
    if (d.kind === 'reuse')
        return `<span class="rc-dpill reuse">${icon('check', 'sm')}${esc(fill(L.destReuse, { code: d.code || '' }))}</span>`;
    if (d.kind === 'new')
        return `<span class="rc-dpill new">${icon('spark', 'sm')}${esc(L.destNew)}</span>`;
    return `<span class="rc-dpill exp">${esc(L.destExp)}</span>`;
}

function stateCell(row: ReviewRow, L: ConsoleLabels): string {
    const map: Record<RowState, [string, keyof typeof IC]> = {
        ready: [L.stateReady, 'check'],
        confirm: [L.stateConfirm, 'alert'],
        new: [L.stateNew, 'spark'],
        unread: [L.stateUnread, 'alert'],
    };
    const [txt, ic] = map[row.state];
    return `<span class="rc-need ${STATE_CLS[row.state]}">${icon(ic, 'sm')}${esc(txt)}</span>`;
}

function rowHtml(row: ReviewRow, L: ConsoleLabels): string {
    const dir =
        row.dir === 'in'
            ? `<span class="rc-dir in">${esc(L.dirIn)}</span>`
            : `<span class="rc-dir out">${esc(L.dirOut)}</span>`;
    let dests: string;
    if (row.bank) dests = `<span class="rc-dpill exp">${icon('bank', 'sm')}</span>`;
    else if (row.dests && row.dests.length) dests = row.dests.map((d) => destPill(d, L)).join('');
    else dests = '—';
    const amt = row.amount ? `฿${esc(row.amount)}` : '';
    return (
        `<tr class="rc-row${row.state === 'ready' ? ' done' : ''}" data-id="${esc(row.id)}" tabindex="0">` +
        `<td><span class="rc-dot ${STATE_CLS[row.state]}"></span></td>` +
        `<td>${dir}</td>` +
        `<td><div class="rc-party" title="${esc(row.party)}">${esc(row.party)}</div><div class="rc-docno">${esc(row.docno)}</div></td>` +
        `<td class="rc-amt">${amt}</td>` +
        `<td class="rc-hidecol rc-acctcell">${esc(row.account || '—')}</td>` +
        `<td class="rc-hidecol"><div class="rc-dests">${dests}</div></td>` +
        `<td>${stateCell(row, L)}</td></tr>`
    );
}

function filterRows(rows: ReviewRow[], f: FilterKey): ReviewRow[] {
    if (f === 'need') return rows.filter((r) => r.state === 'confirm' || r.state === 'new');
    if (f === 'unread') return rows.filter((r) => r.state === 'unread');
    if (f === 'ready') return rows.filter((r) => r.state === 'ready');
    return rows;
}

export function renderReviewConsole(root: HTMLElement, opts: ConsoleOptions): void {
    const { data, labels: L } = opts;
    let filter: FilterKey = 'need';

    const needCount = data.rows.filter((r) => r.state === 'confirm' || r.state === 'new').length;

    root.innerHTML =
        '<div class="rc-app">' +
        // 顶部账套条
        '<div class="rc-top">' +
        `<div class="rc-title">${esc(L.title)}</div><div class="rc-sp"></div>` +
        `<div class="rc-acct"><span class="rc-live"></span><b>${esc(L.accountSet)}</b>` +
        `<span class="rc-muted">· ${esc(L.agentOnline)}</span></div></div>` +
        // 流水线
        '<div class="rc-pipe"></div>' +
        // 复核横幅
        '<div class="rc-banner"></div>' +
        // 筛选
        '<div class="rc-tabs"></div>' +
        // 表格
        '<div class="rc-grid"><table class="rc-table"><thead><tr>' +
        `<th class="rc-col-dot"></th><th class="rc-col-dir">${esc(L.colDir)}</th><th>${esc(L.colDoc)}</th>` +
        `<th class="rc-tr rc-col-amt">${esc(L.colAmount)}</th><th class="rc-hidecol rc-col-acct">${esc(L.colAccount)}</th>` +
        `<th class="rc-hidecol rc-col-dest">${esc(L.colDest)}</th><th class="rc-col-state">${esc(L.colState)}</th>` +
        '</tr></thead><tbody class="rc-body"></tbody></table><div class="rc-collapse"></div></div>' +
        // 底栏
        '<div class="rc-actionbar"></div>' +
        '</div>';

    const pipe = root.querySelector('.rc-pipe') as HTMLElement;
    pipe.innerHTML = L.stages
        .map((t, i) => {
            const cls = i < 2 ? 'done' : i === 2 ? 'active' : '';
            const mark = i < 2 ? icon('check', 'sm') : String(i + 1);
            return (
                `<div class="rc-stage ${cls}"><div class="rc-icn">${mark}</div>` +
                `<div><div class="rc-st-t">${esc(t)}</div><div class="rc-st-d">${esc(L.stageDetails[i])}</div></div></div>`
            );
        })
        .join('');

    const banner = root.querySelector('.rc-banner') as HTMLElement;
    // 「已完成 N 张」横幅仅在有已就绪项时出现(匹配前 readyCount=0 → 不显示空横幅)。
    if (data.readyCount > 0) {
        banner.innerHTML =
            `<div><div class="rc-b-head">${fill(L.bannerHead, { n: data.readyCount })}</div>` +
            `<div class="rc-b-sub">${esc(L.bannerSub)}</div></div><div class="rc-sp"></div>` +
            `<button class="rc-btn ok" data-act="accept-all">${icon('check', 'sm')}${esc(fill(L.acceptAll, { n: data.readyCount }))}</button>`;
    } else {
        banner.style.display = 'none';
    }

    const tabsEl = root.querySelector('.rc-tabs') as HTMLElement;
    const tabCounts: Record<FilterKey, number> = {
        need: needCount,
        ready: data.readyCount,
        unread: data.unreadCount,
        all: data.total,
    };
    const tabKeys: FilterKey[] = ['need', 'ready', 'unread', 'all'];
    tabsEl.innerHTML =
        tabKeys
            .map(
                (k) =>
                    `<button class="rc-tab${k === 'need' ? ' warn' : ''}" data-f="${k}">` +
                    `${esc(L.tabs[k])} <span class="rc-cnt">${tabCounts[k]}</span></button>`
            )
            .join('') +
        '<div class="rc-sp"></div>' +
        `<span class="rc-hint">${icon('search', 'sm')}${esc(L.hintOpen)}</span>`;

    const bodyEl = root.querySelector('.rc-body') as HTMLElement;
    const collapseEl = root.querySelector('.rc-collapse') as HTMLElement;

    function paint(): void {
        bodyEl.innerHTML = filterRows(data.rows, filter)
            .map((r) => rowHtml(r, L))
            .join('');
        if (filter === 'ready' || filter === 'all')
            collapseEl.innerHTML = `${icon('folder')} ${fill(L.collapseReady, { n: data.readyCount })}`;
        else if (filter === 'need')
            collapseEl.innerHTML = `${icon('check')} ${fill(L.collapseNeed, { n: data.readyCount })}`;
        else collapseEl.innerHTML = '';
        collapseEl.style.display = filter === 'unread' ? 'none' : 'flex';
        tabsEl.querySelectorAll('.rc-tab').forEach((t) => {
            t.classList.toggle('on', (t as HTMLElement).dataset.f === filter);
        });
    }

    tabsEl.addEventListener('click', (e) => {
        const t = (e.target as HTMLElement).closest('.rc-tab') as HTMLElement | null;
        if (!t) return;
        filter = t.dataset.f as FilterKey;
        paint();
    });

    bodyEl.addEventListener('click', (e) => {
        const tr = (e.target as HTMLElement).closest('.rc-row') as HTMLElement | null;
        if (tr && opts.onOpenRow) opts.onOpenRow(tr.dataset.id || '');
    });

    banner.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).closest('[data-act="accept-all"]') && opts.onAcceptAll)
            opts.onAcceptAll();
    });

    const actionbar = root.querySelector('.rc-actionbar') as HTMLElement;
    const pct = data.total ? Math.round((data.readyCount / data.total) * 100) : 0;
    actionbar.innerHTML =
        `<div class="rc-prog"><div class="rc-pbar"><i style="width:${pct}%"></i></div>` +
        `<span class="rc-muted">${fill(L.progress, { done: data.readyCount, total: data.total })}</span></div>` +
        `<span class="rc-remain">${fill(L.remain, { n: needCount })}</span><div class="rc-sp"></div>` +
        `<button class="rc-btn" data-act="review">${esc(L.reviewStart)}</button>` +
        `<button class="rc-btn pri" data-act="push">${esc(L.push)}</button>`;
    actionbar.addEventListener('click', (e) => {
        const t = e.target as HTMLElement;
        if (t.closest('[data-act="push"]') && opts.onPush) opts.onPush();
        else if (t.closest('[data-act="review"]') && opts.onOpenRow) {
            const first = filterRows(data.rows, 'need')[0];
            if (first) opts.onOpenRow(first.id);
        }
    });

    paint();
}
