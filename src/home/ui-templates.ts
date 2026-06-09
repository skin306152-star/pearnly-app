// ============================================================
// 6 页面模板骨架 · 实物源 scripts/_mock/templates.html(DESIGN_SYSTEM §3)
// ------------------------------------------------------------
// 全站新屏/迁移屏对号入座套这 6 个之一,内容由各屏以 HTML 串填 slot。
// 结构 = .ui 作用域 + kit 组件(home-45-kit.css)+ 模板原语(.pagehead/.panel/
// .cols/.tool/.foot/.setrow/.steps…)。布局令牌化,改一处全站随。
// window.uiTpl 供非模块代码裸调。
// ============================================================
/* eslint-disable no-undef */

interface HeadOpts {
    title: string;
    sub?: string;
    actions?: string; // 头部带右上动作区 HTML(按钮等)
}

function head(o: HeadOpts): string {
    const sub = o.sub ? `<div class="sub">${o.sub}</div>` : '';
    const actions = o.actions ? `<div class="head-actions">${o.actions}</div>` : '';
    return `<div class="pagehead"><div><div class="h1">${o.title}</div>${sub}</div>${actions}</div>`;
}

// ① 概览:信息带 → 快捷 + 最近动态
export function tplOverview(o: {
    title: string;
    sub?: string;
    band?: string;
    quick?: string;
    recent?: string;
}): string {
    const band = o.band ? `<div class="panel band">${o.band}</div>` : '';
    return `<div class="ui"><div class="wrap">${head({ title: o.title, sub: o.sub })}${band}
        <div class="cols" style="grid-template-columns:360px 1fr;margin-top:var(--s4)">
            <div class="panel box">${o.quick || ''}</div>
            <div class="panel box">${o.recent || ''}</div>
        </div></div></div>`;
}

// ② 列表:头部带 → 控件带 → 表格 → 分页
export function tplList(o: {
    title: string;
    sub?: string;
    actions?: string;
    band?: string;
    tools?: string;
    table?: string;
    pager?: string;
}): string {
    const band = o.band
        ? `<div class="panel band" style="margin-bottom:var(--s4)">${o.band}</div>`
        : '';
    const tools = o.tools ? `<div class="tool">${o.tools}</div>` : '';
    const pager = o.pager
        ? `<div class="foot" style="justify-content:space-between">${o.pager}</div>`
        : '';
    return `<div class="ui"><div class="wrap">${head({ title: o.title, sub: o.sub, actions: o.actions })}${band}
        <div class="panel">${tools}<div style="padding:0 var(--s4) var(--s4)">${o.table || ''}</div>${pager}</div></div></div>`;
}

// ③ 详情:标题带(状态+动作)→ 两栏(主信息 | 侧)
export function tplDetail(o: {
    title: string;
    status?: string;
    actions?: string;
    main?: string;
    side?: string;
}): string {
    const status = o.status ? ` ${o.status}` : '';
    return `<div class="ui"><div class="wrap">${head({ title: o.title + status, actions: o.actions })}
        <div class="cols detail">
            <div class="panel box">${o.main || ''}</div>
            <div class="panel box">${o.side || ''}</div>
        </div></div></div>`;
}

// ④ 录入:分屏(票图 | 表单)
export function tplEntry(o: {
    title: string;
    sub?: string;
    image?: string;
    form?: string;
}): string {
    return `<div class="ui"><div class="wrap">${head({ title: o.title, sub: o.sub })}
        <div class="cols entry">
            <div class="panel box">${o.image || ''}</div>
            <div class="panel box">${o.form || ''}</div>
        </div></div></div>`;
}

// ⑤ 设置:分节(标签|控件)→ 保存条
export function tplSettings(o: {
    title: string;
    sub?: string;
    sections?: string;
    footer?: string;
}): string {
    const footer = o.footer ? `<div class="foot">${o.footer}</div>` : '';
    return `<div class="ui"><div class="wrap">${head({ title: o.title, sub: o.sub })}
        <div class="panel">${o.sections || ''}${footer}</div></div></div>`;
}

// ⑥ 向导:步骤条 → 当前步内容 → 上一步/下一步
export function tplWizard(o: {
    title: string;
    step: number;
    total: number;
    body?: string;
    prev?: string;
    next?: string;
}): string {
    let steps = '';
    for (let i = 1; i <= o.total; i++) {
        steps += `<span class="dot${i <= o.step ? ' on' : ''}">${i}</span>`;
        if (i < o.total) steps += `<span class="seg${i < o.step ? ' on' : ''}"></span>`;
    }
    const foot =
        o.prev || o.next
            ? `<div class="foot" style="justify-content:space-between">${o.prev || '<span></span>'}${o.next || ''}</div>`
            : '';
    return `<div class="ui"><div class="wrap">${head({ title: o.title })}
        <div class="panel"><div class="steps">${steps}</div>
            <div class="box" style="border:none">${o.body || ''}</div>${foot}</div></div></div>`;
}

export const uiTpl = {
    overview: tplOverview,
    list: tplList,
    detail: tplDetail,
    entry: tplEntry,
    settings: tplSettings,
    wizard: tplWizard,
};

declare global {
    interface Window {
        uiTpl: typeof uiTpl;
    }
}

window.uiTpl = uiTpl;
