// 销售仪表盘图表件(手写 · 零依赖):柱/线趋势 + 环图 + 共用 hover 提示层。
// 规矩(dataviz):单轴(双轴是明令反模式,Odoo 那张收入柱+客单价线不抄)、细标记、
// 分类色绑实体不轮转(色号收在 home-43 的 --ch-* 令牌层,亮暗各自校验过)、
// 文字一律 ink 令牌不沾系列色、网格退后、hover 默认必配。
/* global escapeHtml */

export interface XyBucket {
    label: string;
    value: number;
}

export interface DonutSlice {
    label: string;
    value: number;
    colorVar: string; // CSS 令牌名(--ch-1 …)· 绑实体
}

// 轴上限取「好看的整数」:1/2/2.5/5 × 10^n 里第一个 ≥ max 的,刻度线才不会是 173 这种数。
export function niceMax(max: number): number {
    if (max <= 0) return 1;
    const pow = Math.pow(10, Math.floor(Math.log10(max)));
    for (const k of [1, 2, 2.5, 5, 10]) {
        if (k * pow >= max) return k * pow;
    }
    return 10 * pow;
}

function yGridHtml(top: number, fmt: (v: number) => string): string {
    // 三条水平网格(0 线由基线承担):75% / 50% / 25% + 顶线,标签在左,退后色。
    const lines = [1, 0.75, 0.5, 0.25]
        .map(
            (r) =>
                `<div class="ch-grid" style="bottom:${r * 100}%"><span class="ch-ylab">${escapeHtml(fmt(top * r))}</span></div>`
        )
        .join('');
    return lines;
}

// 柱状:HTML 列(继承旧 .chart 骨架的做法,文字不进 SVG 免缩放变形),每列带 hover 命中区。
export function barChartHtml(buckets: XyBucket[], fmt: (v: number) => string): string {
    const top = niceMax(buckets.reduce((m, b) => Math.max(m, b.value), 0));
    const cols = buckets
        .map((b, i) => {
            const h = Math.max(b.value > 0 ? 2 : 0, Math.round((b.value / top) * 100));
            return `<div class="ch-col" data-tip-i="${i}"><div class="ch-bar" style="height:${h}%"></div></div>`;
        })
        .join('');
    return `<div class="ch-plot" data-mode="bar">${yGridHtml(top, fmt)}<div class="ch-cols">${cols}</div></div>${xLabelsHtml(buckets)}`;
}

// 折线:SVG 只画几何(非缩放描边),hover 命中区仍是 HTML 列 → 柱/线共用一套提示逻辑。
export function lineChartHtml(buckets: XyBucket[], fmt: (v: number) => string): string {
    const top = niceMax(buckets.reduce((m, b) => Math.max(m, b.value), 0));
    const W = 1000;
    const H = 240;
    const n = buckets.length;
    const x = (i: number) => (n === 1 ? W / 2 : (i / (n - 1)) * W);
    const y = (v: number) => H - (v / top) * H;
    const pts = buckets.map((b, i) => `${x(i).toFixed(1)},${y(b.value).toFixed(1)}`);
    const area = `M0,${H} L${pts.join(' L')} L${W},${H} Z`;
    const dots = buckets
        .map(
            (b, i) =>
                `<circle class="ch-dot" data-dot-i="${i}" cx="${x(i).toFixed(1)}" cy="${y(b.value).toFixed(1)}" r="4" vector-effect="non-scaling-stroke"/>`
        )
        .join('');
    const cols = buckets
        .map((_, i) => `<div class="ch-col" data-tip-i="${i}"><i class="ch-cross"></i></div>`)
        .join('');
    return `<div class="ch-plot" data-mode="line">${yGridHtml(top, fmt)}
        <svg class="ch-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">
            <path class="ch-area" d="${area}"/>
            <polyline class="ch-line" points="${pts.join(' ')}" vector-effect="non-scaling-stroke"/>
            ${dots}
        </svg>
        <div class="ch-cols">${cols}</div></div>${xLabelsHtml(buckets)}`;
}

function xLabelsHtml(buckets: XyBucket[]): string {
    // 挤不下就抽稀:目标 ≤16 个可见标签(整月 31 天正好隔天一个,照定稿原型),首尾必留。
    const step = Math.max(1, Math.ceil(buckets.length / 16));
    const cells = buckets
        .map((b, i) => {
            const show = i % step === 0 || i === buckets.length - 1;
            return `<div class="ch-x">${show ? escapeHtml(b.label) : ''}</div>`;
        })
        .join('');
    return `<div class="ch-xrow">${cells}</div>`;
}

// 环图:stroke 圆弧 + 2px 面隙(间隙用底色描边盖出来),中心放合计。图例由调用方拼
//(图例必须带金额:sky 档对比 WARN 的「可见标签」救济就在这)。
export function donutHtml(slices: DonutSlice[], centerLabel: string, centerValue: string): string {
    const total = slices.reduce((s, x) => s + x.value, 0);
    if (total <= 0) return '';
    const R = 15.915; // 周长 100 的半径 → dasharray 直接用百分数
    let offset = 25; // 12 点方向起笔
    const segs = slices
        .map((s, i) => {
            const pct = (s.value / total) * 100;
            const el =
                `<circle class="dn-seg" data-tip-i="${i}" r="${R}" cx="21" cy="21" ` +
                `style="stroke:var(${s.colorVar})" stroke-dasharray="${pct.toFixed(3)} ${(100 - pct).toFixed(3)}" ` +
                `stroke-dashoffset="${offset.toFixed(3)}"/>`;
            offset -= pct;
            return el;
        })
        .join('');
    return `<div class="dn-wrap"><svg class="dn-svg" viewBox="0 0 42 42" role="img">${segs}</svg>
        <div class="dn-center"><div class="dn-cv tnum">${escapeHtml(centerValue)}</div><div class="dn-cl">${escapeHtml(centerLabel)}</div></div></div>`;
}

// 提示卡内容统一语法:标题 + 若干「标签 值」行。走势/环图/热力三处共用,改结构只动这里。
// title/label 这里转义;value 由调用方给成品(金额/数量已带货币符与千分位)。
export function tipCardHtml(title: string, rows: [string, string][]): string {
    return (
        `<b>${escapeHtml(title)}</b>` +
        rows.map(([l, v]) => `<span>${escapeHtml(l)} <em class="tnum">${v}</em></span>`).join('')
    );
}

// 共用提示卡:整页一张,fixed 跟指针走。触屏没有 hover,点按走同一套 pointer 事件天然可用。
// 调用方喂已转义的 HTML;各区自己在 pointerenter/move 里 tipShow、pointerleave 里 tipHide。
let tipEl: HTMLElement | null = null;

export function tipShow(ev: PointerEvent, html: string): void {
    if (!tipEl || !document.body.contains(tipEl)) {
        tipEl = document.createElement('div');
        tipEl.className = 'rep-tip';
        document.body.appendChild(tipEl);
    }
    tipEl.innerHTML = html;
    tipEl.classList.add('on');
    tipEl.style.left = Math.min(ev.clientX + 14, window.innerWidth - 190) + 'px';
    tipEl.style.top = Math.max(ev.clientY - 56, 6) + 'px';
}

export function tipHide(): void {
    if (tipEl) tipEl.classList.remove('on');
}
