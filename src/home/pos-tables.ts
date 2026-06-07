// 餐厅 POS · 桌台管理(老板后台 · 主程序 · 照设计稿 05-桌台管理)· window.openPosTables。
// 区域 tabs + 桌台 grid CRUD,接 /api/pos/admin/restaurant/{areas,tables}(后端 PO-R1 已就绪)。
// owner 专属(收银员 nav 不显 + 后端 403)· 餐厅业态(module-nav 据 business_type 显隐 nav-pos-tables)。
// 按账套(workspace_client_id)隔离,数据喂收银员端「桌台总览」(view.py)。core-boot 满 500 → 做弹窗非路由。
// 智能省事:批量加桌(前缀+起始+数量 一次建 A1..A8)。四态(加载/空/错/非法输入)· 信封 body.ok→data · 失败 posErrMsg。
/* global t, token, showToast, escapeHtml */
import { activeWsId, posErrMsg } from './inventory-common';

interface Area {
    id: number;
    name: string;
    is_active: boolean;
    table_count: number | null;
}
interface Table {
    id: number;
    name: string;
    area_id: number | null;
    seats: number;
    is_active: boolean;
}

const PFX = '/api/pos/admin/restaurant';
let areas: Area[] = [];
let tables: Table[] = [];
let activeArea: number | null = null;
let ws = 0;

function hdr(): Record<string, string> {
    return {
        Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
        'Content-Type': 'application/json',
    };
}

async function call(method: string, path: string, body?: unknown): Promise<unknown> {
    let env: { ok?: boolean; data?: unknown; error?: { code?: string } };
    try {
        const r = await fetch(PFX + path, {
            method,
            headers: hdr(),
            body: body !== undefined ? JSON.stringify(body) : undefined,
        });
        env = await r.json();
    } catch (_) {
        throw new Error('pos.unexpected');
    }
    if (env && env.ok === true) return env.data;
    throw new Error((env && env.error && env.error.code) || 'pos.unexpected');
}

function errToast(e: unknown): void {
    const code = e instanceof Error ? e.message : 'pos.unexpected';
    // 桌上有人不能停用 → 专属人话(后端 pos.void_not_allowed · detail table_busy)。
    const key = code === 'pos.void_not_allowed' ? 'rtbl.busy' : code;
    showToast(posErrMsg(key, 'pos.unexpected'), 'error');
}

// ── 注入式作用域样式(.ptbl · 主蓝 var(--btn-blue))──
const STYLE = `
.ptbl-mask{position:fixed;inset:0;background:rgba(17,24,39,.5);backdrop-filter:blur(3px);display:none;align-items:flex-start;justify-content:center;z-index:1200;padding:32px 16px;overflow:auto;}
.ptbl-mask.show{display:flex;}
.ptbl{width:760px;max-width:96vw;background:#fff;border-radius:18px;padding:24px 26px 22px;position:relative;box-shadow:0 24px 60px rgba(0,0,0,.25);}
.ptbl-x{position:absolute;top:16px;right:18px;border:0;background:#f0f0ec;color:#6b7280;width:30px;height:30px;border-radius:8px;font-size:18px;cursor:pointer;line-height:1;}
.ptbl .hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;}
.ptbl h1{font-size:20px;color:#111827;margin:0;}
.ptbl .sub{color:#6b7280;font-size:13px;margin-bottom:16px;}
.ptbl .zones{display:flex;gap:8px;margin-bottom:14px;align-items:center;flex-wrap:wrap;}
.ptbl .ztab{height:34px;padding:0 15px;border-radius:999px;border:1px solid #e8e8e3;background:#fff;color:#6b7280;font-size:13px;cursor:pointer;display:inline-flex;align-items:center;gap:7px;}
.ptbl .ztab.on{background:#111827;color:#fff;border-color:#111827;}
.ptbl .ztab .c{font-size:11px;opacity:.7;}
.ptbl .ztab.add{border-style:dashed;color:#2563EB;border-color:#c7d2fe;}
.ptbl .card{border:1px solid #e8e8e3;border-radius:14px;overflow:hidden;}
.ptbl .ch{padding:11px 16px;border-bottom:1px solid #f0f0ec;font-weight:700;font-size:13.5px;display:flex;justify-content:space-between;align-items:center;color:#111827;}
.ptbl .ch .btn{height:32px;padding:0 12px;border:0;border-radius:8px;background:var(--btn-blue,#2563EB);color:#fff;font-weight:700;font-size:12.5px;cursor:pointer;display:inline-flex;align-items:center;gap:5px;}
.ptbl .grid{padding:14px;display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));}
.ptbl .tcard{border:1px solid #e8e8e3;border-radius:12px;padding:13px;}
.ptbl .tcard.off{opacity:.55;}
.ptbl .tcard .no{font-size:18px;font-weight:800;color:#111827;}
.ptbl .tcard .seats{font-size:12px;color:#6b7280;margin-top:4px;display:flex;align-items:center;gap:5px;}
.ptbl .tcard .ops{display:flex;gap:6px;margin-top:11px;}
.ptbl .tcard .op{flex:1;height:30px;border:1px solid #e8e8e3;border-radius:7px;background:#fff;color:#6b7280;font-size:12px;cursor:pointer;}
.ptbl .tcard .op:hover{border-color:#c7d2fe;color:var(--btn-blue,#2563EB);}
.ptbl .addcard{border:1.5px dashed #e8e8e3;border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;color:#9ca3af;cursor:pointer;min-height:96px;}
.ptbl .addcard:hover{border-color:var(--btn-blue,#2563EB);color:var(--btn-blue,#2563EB);}
.ptbl .state{padding:40px 0;text-align:center;color:#9ca3af;font-size:13.5px;}
.ptbl .note{margin-top:14px;font-size:12.5px;color:#6b7280;background:#f8f8f5;border:1px solid #e8e8e3;border-radius:10px;padding:11px 13px;line-height:1.6;}
.ptbl-sub{position:fixed;inset:0;background:rgba(17,24,39,.45);display:none;align-items:center;justify-content:center;z-index:1300;padding:16px;}
.ptbl-sub.show{display:flex;}
.ptbl-dlg{width:380px;max-width:92vw;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,.25);}
.ptbl-dlg .mh{padding:15px 20px;border-bottom:1px solid #f0f0ec;font-weight:700;font-size:16px;color:#111827;}
.ptbl-dlg .mb{padding:16px 20px;}
.ptbl-dlg label{display:block;font-size:12.5px;color:#6b7280;margin:0 0 6px;}
.ptbl-dlg .fld{height:44px;border:1px solid #e8e8e3;border-radius:10px;padding:0 13px;display:flex;align-items:center;background:#fbfbf9;margin-bottom:13px;}
.ptbl-dlg .fld input,.ptbl-dlg .fld select{border:0;outline:0;background:transparent;flex:1;font-size:15px;color:#111827;}
.ptbl-dlg .seg{display:flex;gap:8px;margin-bottom:13px;}
.ptbl-dlg .seg button{flex:1;height:36px;border:1px solid #e8e8e3;border-radius:9px;background:#fff;color:#6b7280;font-size:13px;cursor:pointer;}
.ptbl-dlg .seg button.on{background:#DBEAFE;border-color:var(--btn-blue,#2563EB);color:var(--btn-blue,#2563EB);font-weight:700;}
.ptbl-dlg .two{display:flex;gap:10px;}
.ptbl-dlg .two>div{flex:1;}
.ptbl-dlg .mf{padding:0 20px 18px;display:flex;gap:10px;}
.ptbl-dlg .g{height:44px;padding:0 16px;border:1px solid #e8e8e3;border-radius:10px;background:#fff;color:#6b7280;cursor:pointer;}
.ptbl-dlg .ok{flex:1;height:44px;border:0;border-radius:10px;background:var(--btn-blue,#2563EB);color:#fff;font-weight:700;font-size:15px;cursor:pointer;}
.ptbl-dlg .ok:disabled{background:#c7cdd6;cursor:not-allowed;}
`;

function ensureStyle(): void {
    if (document.getElementById('ptbl-style')) return;
    const s = document.createElement('style');
    s.id = 'ptbl-style';
    s.textContent = STYLE;
    document.head.appendChild(s);
}

function ensureShell(): HTMLElement {
    let m = document.getElementById('ptbl-mask');
    if (m) return m;
    ensureStyle();
    m = document.createElement('div');
    m.id = 'ptbl-mask';
    m.className = 'ptbl-mask';
    m.innerHTML = `<div class="ptbl">
        <button class="ptbl-x" id="ptbl-close" aria-label="close">&times;</button>
        <div class="hd"><h1>${escapeHtml(t('rtbl.title'))}</h1>
            <button class="ztab add" id="ptbl-add-area">+ ${escapeHtml(t('rtbl.add_area'))}</button></div>
        <div class="sub">${escapeHtml(t('rtbl.sub'))}</div>
        <div id="ptbl-body"></div>
        <div class="note">${t('rtbl.note')}</div>
    </div>`;
    document.body.appendChild(m);
    m.addEventListener('click', (e) => {
        if (e.target === m) close();
    });
    m.querySelector('#ptbl-close')!.addEventListener('click', close);
    m.querySelector('#ptbl-add-area')!.addEventListener('click', () => openAreaDialog());
    m.querySelector('#ptbl-body')!.addEventListener('click', onBodyClick);
    return m;
}

function close(): void {
    document.getElementById('ptbl-mask')?.classList.remove('show');
}

function renderBody(state: 'loading' | 'error' | 'ok'): void {
    const body = document.getElementById('ptbl-body');
    if (!body) return;
    if (state === 'loading') {
        body.innerHTML = `<div class="state">${escapeHtml(t('rtbl.loading'))}</div>`;
        return;
    }
    if (state === 'error') {
        body.innerHTML = `<div class="state">${escapeHtml(t('rtbl.load_failed'))}</div>`;
        return;
    }
    if (!areas.length) {
        body.innerHTML = `<div class="state">${escapeHtml(t('rtbl.no_area'))}</div>`;
        return;
    }
    const zones = areas
        .map(
            (a) =>
                `<div class="ztab${a.id === activeArea ? ' on' : ''}" data-area="${a.id}">${escapeHtml(
                    a.name
                )}<span class="c">${a.table_count ?? 0}</span></div>`
        )
        .join('');
    const inZone = tables.filter((tb) => tb.area_id === activeArea);
    const cur = areas.find((a) => a.id === activeArea);
    const cards =
        inZone
            .map(
                (tb) =>
                    `<div class="tcard${tb.is_active ? '' : ' off'}" data-table="${tb.id}">
            <div class="no">${escapeHtml(tb.name)}</div>
            <div class="seats">${tb.is_active ? escapeHtml(t('rtbl.seats_n').replace('{n}', String(tb.seats))) : escapeHtml(t('rtbl.disabled'))}</div>
            <div class="ops">${
                tb.is_active
                    ? `<button class="op" data-act="edit">${escapeHtml(t('rtbl.edit'))}</button><button class="op" data-act="disable">${escapeHtml(t('rtbl.disable'))}</button>`
                    : `<button class="op" data-act="enable">${escapeHtml(t('rtbl.enable'))}</button>`
            }</div>
          </div>`
            )
            .join('') +
        `<div class="addcard" data-act="add-table"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>${escapeHtml(t('rtbl.add_table'))}</div>`;
    body.innerHTML = `<div class="zones">${zones}</div>
        <div class="card">
            <div class="ch"><span>${escapeHtml(cur ? cur.name : '')} · ${escapeHtml(t('rtbl.tables'))}</span>
                <button class="btn" data-act="add-table"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>${escapeHtml(t('rtbl.add_table'))}</button></div>
            <div class="grid">${cards}</div>
        </div>`;
}

async function load(): Promise<void> {
    renderBody('loading');
    try {
        const a = (await call('GET', `/areas?workspace_client_id=${ws}`)) as { areas: Area[] };
        areas = a.areas || [];
        if (activeArea === null || !areas.some((x) => x.id === activeArea)) {
            activeArea = areas.length ? areas[0].id : null;
        }
        const tb = (await call('GET', `/tables?workspace_client_id=${ws}`)) as { tables: Table[] };
        tables = tb.tables || [];
        renderBody('ok');
    } catch (_) {
        renderBody('error');
    }
}

function onBodyClick(e: Event): void {
    const el = e.target as HTMLElement;
    const zone = el.closest('.ztab[data-area]') as HTMLElement | null;
    if (zone) {
        activeArea = Number(zone.dataset.area);
        renderBody('ok');
        return;
    }
    const act = (el.closest('[data-act]') as HTMLElement | null)?.dataset.act;
    if (act === 'add-table') return openTableDialog();
    const card = el.closest('.tcard[data-table]') as HTMLElement | null;
    if (!card || !act) return;
    const id = Number(card.dataset.table);
    const tb = tables.find((x) => x.id === id);
    if (act === 'edit' && tb) openTableDialog(tb);
    else if (act === 'disable') setTableActive(id, false);
    else if (act === 'enable') setTableActive(id, true);
}

async function setTableActive(id: number, on: boolean): Promise<void> {
    try {
        await call('PATCH', `/tables/${id}`, { workspace_client_id: ws, is_active: on });
        showToast(t('rtbl.saved'), 'success');
        await load();
    } catch (e) {
        errToast(e);
    }
}

// ── 区域弹窗 ──
function openAreaDialog(): void {
    showDialog(
        t('rtbl.add_area'),
        `<label>${escapeHtml(t('rtbl.area_name'))}</label><div class="fld"><input id="ptbl-an" maxlength="40" placeholder="${escapeHtml(t('rtbl.area_ph'))}"></div>`,
        async () => {
            const name = (document.getElementById('ptbl-an') as HTMLInputElement).value.trim();
            if (!name) return false;
            await call('POST', '/areas', { workspace_client_id: ws, name });
            activeArea = null; // 让 load 选回有效区
            return true;
        }
    );
}

// ── 桌台弹窗(新增/编辑 · 新增含批量)──
function openTableDialog(tb?: Table): void {
    const isEdit = !!tb;
    const areaOpts = areas
        .map(
            (a) =>
                `<option value="${a.id}"${a.id === (tb ? tb.area_id : activeArea) ? ' selected' : ''}>${escapeHtml(a.name)}</option>`
        )
        .join('');
    const batchSeg = isEdit
        ? ''
        : `<div class="seg" id="ptbl-mode"><button data-m="one" class="on">${escapeHtml(t('rtbl.mode_one'))}</button><button data-m="batch">${escapeHtml(t('rtbl.mode_batch'))}</button></div>`;
    const single = `<div id="ptbl-one">
        <label>${escapeHtml(t('rtbl.table_no'))}</label><div class="fld"><input id="ptbl-tn" maxlength="20" value="${tb ? escapeHtml(tb.name) : ''}" placeholder="A9"></div></div>`;
    const batch = isEdit
        ? ''
        : `<div id="ptbl-batch" style="display:none;"><div class="two"><div><label>${escapeHtml(t('rtbl.prefix'))}</label><div class="fld"><input id="ptbl-pfx" maxlength="8" placeholder="A"></div></div><div><label>${escapeHtml(t('rtbl.start'))}</label><div class="fld"><input id="ptbl-start" type="number" value="1" min="1"></div></div><div><label>${escapeHtml(t('rtbl.count'))}</label><div class="fld"><input id="ptbl-cnt" type="number" value="4" min="1" max="50"></div></div></div></div>`;
    showDialog(
        isEdit ? t('rtbl.edit_table') : t('rtbl.add_table'),
        `${batchSeg}${single}${batch}
        <label>${escapeHtml(t('rtbl.area'))}</label><div class="fld"><select id="ptbl-ta">${areaOpts}</select></div>
        <label>${escapeHtml(t('rtbl.seats'))}</label><div class="fld"><input id="ptbl-ts" type="number" value="${tb ? tb.seats : 4}" min="1"></div>`,
        async () => submitTable(tb)
    );
    if (!isEdit) {
        const seg = document.getElementById('ptbl-mode');
        seg?.addEventListener('click', (e) => {
            const b = (e.target as HTMLElement).closest('button[data-m]') as HTMLElement | null;
            if (!b) return;
            seg.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
            const batchMode = b.dataset.m === 'batch';
            (document.getElementById('ptbl-one') as HTMLElement).style.display = batchMode
                ? 'none'
                : '';
            (document.getElementById('ptbl-batch') as HTMLElement).style.display = batchMode
                ? ''
                : 'none';
        });
    }
}

async function submitTable(tb?: Table): Promise<boolean> {
    const area_id = Number((document.getElementById('ptbl-ta') as HTMLSelectElement).value) || null;
    const seats = Math.max(
        1,
        Number((document.getElementById('ptbl-ts') as HTMLInputElement).value) || 4
    );
    if (tb) {
        const name = (document.getElementById('ptbl-tn') as HTMLInputElement).value.trim();
        if (!name) return false;
        await call('PATCH', `/tables/${tb.id}`, { workspace_client_id: ws, name, area_id, seats });
        return true;
    }
    const batchMode =
        document.querySelector('#ptbl-mode button.on')?.getAttribute('data-m') === 'batch';
    if (batchMode) {
        const pfx = (document.getElementById('ptbl-pfx') as HTMLInputElement).value.trim();
        const start = Math.max(
            1,
            Number((document.getElementById('ptbl-start') as HTMLInputElement).value) || 1
        );
        const cnt = Math.min(
            50,
            Math.max(
                1,
                Number((document.getElementById('ptbl-cnt') as HTMLInputElement).value) || 1
            )
        );
        for (let i = 0; i < cnt; i++) {
            await call('POST', '/tables', {
                workspace_client_id: ws,
                name: pfx + (start + i),
                area_id,
                seats,
            });
        }
        return true;
    }
    const name = (document.getElementById('ptbl-tn') as HTMLInputElement).value.trim();
    if (!name) return false;
    await call('POST', '/tables', { workspace_client_id: ws, name, area_id, seats });
    return true;
}

// 通用子弹窗:body HTML + 提交回调(返回 true=成功关闭并 reload · false=校验不过不关)。
function showDialog(title: string, bodyHtml: string, onOk: () => Promise<boolean>): void {
    let d = document.getElementById('ptbl-sub');
    if (!d) {
        d = document.createElement('div');
        d.id = 'ptbl-sub';
        d.className = 'ptbl-sub';
        document.body.appendChild(d);
    }
    d.innerHTML = `<div class="ptbl-dlg"><div class="mh">${escapeHtml(title)}</div><div class="mb">${bodyHtml}</div>
        <div class="mf"><button class="g" id="ptbl-dcancel">${escapeHtml(t('rtbl.cancel'))}</button><button class="ok" id="ptbl-dok">${escapeHtml(t('rtbl.save'))}</button></div></div>`;
    d.classList.add('show');
    d.querySelector('#ptbl-dcancel')!.addEventListener('click', () => d!.classList.remove('show'));
    const okBtn = d.querySelector('#ptbl-dok') as HTMLButtonElement;
    okBtn.addEventListener('click', async () => {
        okBtn.disabled = true;
        try {
            const done = await onOk();
            if (done) {
                d!.classList.remove('show');
                showToast(t('rtbl.saved'), 'success');
                await load();
            } else {
                okBtn.disabled = false;
            }
        } catch (e) {
            okBtn.disabled = false;
            errToast(e);
        }
    });
}

window.openPosTables = function () {
    const isOwner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    if (!isOwner) {
        showToast(t('rtbl.owner_only'), 'error');
        return;
    }
    const id = activeWsId();
    if (!id) {
        showToast(t('rtbl.no_workspace'), 'error');
        return;
    }
    ws = id;
    ensureShell().classList.add('show');
    load();
};

// 侧栏「桌台管理」入口(owner · 餐厅 · module-nav 控显隐)→ 弹窗(core-boot 满 500 不加路由)。
document.addEventListener('click', (e) => {
    if (
        (e.target as HTMLElement).closest('#nav-pos-tables') &&
        typeof window.openPosTables === 'function'
    )
        window.openPosTables();
});
