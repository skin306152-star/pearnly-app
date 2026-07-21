// ERP 推送复核台 · 记账去向 + 商品去向面板(纯渲染)
//
// 遮罩右侧「② 记账去向」(方向/单据类型/写入账套/科目,均为系统预填 · 可改)+「③ 商品去向」
// (逐行:套账已有则复用、没有则新建到选定目录、拿不准则出裁决块)+ 系统提示/提问。
// 纯函数返回 HTML;交互(复用/新建裁决、下拉)由遮罩事件层处理(data-fz / data-pick)。
//
// 转义约定:文案模板(labels)= 开发者可信,不转义;动态值 = 传入前各自 esc(纯文本)或
// 包成可信 HTML 片段(mono/bold 里已 esc)。fmt 只做占位替换、不再二次转义。

export interface RoutingInfo {
    direction: string; // "进项 · 采购"
    directionSrc: string; // "依据账套主体税号"
    docType: string; // "赊购 RR"
    docTypeSrc: string;
    accountSet: string; // "68SINCER"(锁定 · 本连接授权)
    account: string; // "ซื้อสินค้า 5312-01"
    accountLooked?: string; // 有=套账核对到的依据(绿) · 无=用 accountSrc(系统预填)
    accountSrc?: string;
}

export interface ItemLine {
    name: string;
    qty: string;
    kind: 'reuse' | 'new' | 'fuzzy' | 'exp';
    code?: string; // reuse:套账已有码
    match?: string; // reuse:匹配说明
    dest?: string; // new/exp:目标目录
    guess?: string; // fuzzy:候选码
    sim?: string; // fuzzy:相似度
}

export interface RoutingNote {
    text: string;
    kind: 'sys' | 'q'; // sys=系统提示 · q=需人工回答的提问
}

export interface RoutingLabels {
    routeCap: string;
    routeChip: string;
    lblDir: string;
    lblDocType: string;
    lblAcctSet: string;
    lblAcct: string;
    itemsCap: string;
    reuseTpl: string; // 含 {code}{match}
    newTpl: string; // 含 {dest}
    lookedTpl: string; // 含 {note}
    fuzzyTpl: string; // 含 {name}{qty}{guess}{sim}
    fzReuse: string;
    fzNew: string;
}

const I = {
    check: '<svg class="rc-ic sm" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>',
    spark: '<svg class="rc-ic sm" viewBox="0 0 24 24"><path d="M12 3l1.4 4L17.5 8.5 13.4 10 12 14l-1.4-4L6.5 8.5 10.6 7z"/></svg>',
    lock: '<svg class="rc-ic sm" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
    alert: '<svg class="rc-ic sm" viewBox="0 0 24 24"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h16.9a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
};

function esc(s: string): string {
    return String(s == null ? '' : s).replace(
        /[&<>"']/g,
        (c) =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string
    );
}

// 占位替换 · 不转义(模板可信 · vars 由调用方保证安全)。
function fmt(tpl: string, vars: Record<string, string>): string {
    return tpl.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');
}

const mono = (s: string): string => `<span class="mono">${esc(s)}</span>`;

// pick:已是安全 HTML(调用方 esc 或可信片段)。src/looked 同,直接嵌;仅 lbl 在此 esc。
function pickRow(
    lbl: string,
    pick: string,
    opts: { locked?: boolean; src?: string; looked?: string }
): string {
    const cls = 'rcv-pick' + (opts.locked ? ' locked' : '');
    const tail = opts.looked
        ? `<span class="rcv-looked">${I.check}${opts.looked}</span>`
        : opts.src
          ? `<span class="rcv-src">${opts.src}</span>`
          : '';
    return `<div class="rcv-rrow"><span class="rcv-rlbl">${esc(lbl)}</span><div><span class="${cls}">${pick}</span>${tail}</div></div>`;
}

function lineHtml(ln: ItemLine, L: RoutingLabels): string {
    let chip: string;
    if (ln.kind === 'reuse')
        chip = `<span class="rcv-destchip reuse">${I.check}${fmt(L.reuseTpl, { code: mono(ln.code || ''), match: esc(ln.match || '') })}</span>`;
    else if (ln.kind === 'new')
        chip = `<span class="rcv-destchip new">${I.spark}${fmt(L.newTpl, { dest: esc(ln.dest || '') })}</span>`;
    else if (ln.kind === 'fuzzy') chip = `<span class="rcv-destchip pending">?</span>`;
    else chip = `<span class="rcv-destchip exp">${esc(ln.dest || '')}</span>`;
    const row = `<div class="rcv-line"><div><div class="rcv-lname">${esc(ln.name)}</div><div class="rcv-lqty">${esc(ln.qty)}</div></div><div>${chip}</div></div>`;
    if (ln.kind !== 'fuzzy') return row;
    // 拿不准:出裁决块(是否同一商品)· R/N 由遮罩键盘层处理
    const q = fmt(L.fuzzyTpl, {
        name: `<b>${esc(ln.name)}</b>`,
        qty: esc(ln.qty),
        guess: mono(ln.guess || ''),
        sim: esc(ln.sim || ''),
    });
    const fz =
        `<div class="rcv-fuzzy"><div class="rcv-fq">${I.alert}<span>${q}</span></div>` +
        `<div class="rcv-fa"><button class="rcv-mini pri" data-fz="reuse"><kbd>R</kbd> ${esc(L.fzReuse)}</button>` +
        `<button class="rcv-mini" data-fz="new"><kbd>N</kbd> ${esc(L.fzNew)}</button></div></div>`;
    return row + fz;
}

export function routingPanelHtml(
    routing: RoutingInfo,
    lines: ItemLine[] | undefined,
    note: RoutingNote | undefined,
    L: RoutingLabels
): string {
    let h = `<p class="rcv-cap rcv-cap2">${esc(L.routeCap)} <span class="rcv-chip sys">${I.spark}${esc(L.routeChip)}</span></p>`;
    h += '<div class="rcv-route">';
    h += pickRow(L.lblDir, esc(routing.direction), {
        locked: true,
        src: esc(routing.directionSrc),
    });
    h += pickRow(L.lblDocType, esc(routing.docType), { src: esc(routing.docTypeSrc) });
    h += pickRow(L.lblAcctSet, `${I.lock}${esc(routing.accountSet)}`, { locked: true });
    h += pickRow(L.lblAcct, esc(routing.account), {
        looked: routing.accountLooked
            ? fmt(L.lookedTpl, { note: esc(routing.accountLooked) })
            : undefined,
        src: routing.accountSrc ? esc(routing.accountSrc) : undefined,
    });
    h += '</div>';

    if (lines && lines.length) {
        h += `<p class="rcv-cap rcv-cap2">${esc(L.itemsCap)}</p>`;
        h += '<div class="rcv-lines">' + lines.map((ln) => lineHtml(ln, L)).join('') + '</div>';
    }
    if (note)
        h += `<div class="rcv-sysnote${note.kind === 'q' ? ' q' : ''}">${note.kind === 'q' ? I.alert : I.spark}<span>${esc(note.text)}</span></div>`;
    return h;
}
