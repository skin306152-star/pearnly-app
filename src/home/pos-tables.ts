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

// ── 注入式作用域样式(.ptbl · 逐令牌照搬桌面 05-桌台管理 v2 稿:左对齐 960 · :root 令牌原样)──
const STYLE = `
.ptbl{width:100%;margin:0;padding:26px 0 60px 28px;font-size:13.5px;color:var(--ink);}
.ptbl .ph{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:20px;}
.ptbl .ph .tt{font-size:21px;font-weight:700;}
.ptbl .ph .sub{color:var(--ink2);font-size:13px;margin-top:4px;}
.ptbl .btn{height:38px;padding:0 15px;border-radius:10px;font-size:13.5px;cursor:pointer;display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line);background:var(--card);color:var(--ink);font-weight:500;}
.ptbl .btn:hover{border-color:var(--accent-weak);}
.ptbl .btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600;}
.ptbl .btn.primary:hover{background:var(--accent-deep);}
.ptbl .zones{display:flex;align-items:center;gap:8px;margin-bottom:16px;flex-wrap:wrap;}
.ptbl .zone{height:36px;padding:0 6px 0 15px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink2);font-size:13.5px;cursor:pointer;display:inline-flex;align-items:center;gap:8px;}
.ptbl .zone .c{font-size:12px;color:var(--ink3);}
.ptbl .zone .mg{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;color:transparent;}
.ptbl .zone:hover .mg{color:var(--ink3);}
.ptbl .zone.on{background:var(--accent-weak);color:var(--accent-deep);border-color:var(--accent);}
.ptbl .zone.on .c{color:var(--accent-deep);}.ptbl .zone.on .mg{color:var(--accent-deep);}
.ptbl .zone.on:hover .mg{color:var(--accent-deep);}
.ptbl .card{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 1px 2px rgba(17,24,39,.04),0 4px 14px rgba(17,24,39,.05);overflow:hidden;}
.ptbl .ch{padding:14px 18px;border-bottom:1px solid var(--line2);display:flex;align-items:center;justify-content:space-between;}
.ptbl .ch .zt{font-weight:700;font-size:15px;display:flex;align-items:center;gap:10px;}
.ptbl .ch .zacts{display:flex;align-items:center;gap:8px;}
.ptbl .ch .zlink{font-size:12.5px;color:var(--ink2);cursor:pointer;display:inline-flex;align-items:center;gap:5px;padding:5px 8px;border-radius:7px;}
.ptbl .ch .zlink:hover{background:var(--line2);color:var(--ink);}
.ptbl .ch .zlink.del:hover{background:var(--red-weak);color:var(--red);}
.ptbl .grid{padding:16px 18px;display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));}
.ptbl .t{border:1px solid var(--line);border-radius:12px;padding:14px;background:var(--card);transition:box-shadow .12s;}
.ptbl .t:hover{box-shadow:0 1px 2px rgba(17,24,39,.04),0 4px 14px rgba(17,24,39,.05);}
.ptbl .t .top{display:flex;align-items:flex-start;justify-content:space-between;}
.ptbl .t .no{font-size:19px;font-weight:800;}
.ptbl .t .more{color:var(--ink3);line-height:1;}
.ptbl .t .seats{font-size:12.5px;color:var(--ink2);margin-top:6px;display:flex;align-items:center;gap:5px;}
.ptbl .t .ops{display:flex;gap:7px;margin-top:12px;}
.ptbl .t .op{flex:1;height:30px;border:1px solid var(--line);border-radius:7px;background:var(--card);color:var(--ink2);font-size:12px;cursor:pointer;}
.ptbl .t .op:hover{border-color:var(--accent-weak);color:var(--accent);}
.ptbl .t.off{opacity:.55;}.ptbl .t.off .no{color:var(--ink3);}
.ptbl .addt{border:1.5px dashed var(--line);border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;color:var(--ink3);cursor:pointer;min-height:104px;font-size:13px;}
.ptbl .addt:hover{border-color:var(--accent);color:var(--accent);background:var(--accent-weak);}
.ptbl .empty{padding:34px 18px;text-align:center;color:var(--ink3);}
.ptbl .empty svg{opacity:.4;margin-bottom:10px;}
.ptbl .empty .e-btn{margin-top:14px;}
.ptbl .state{padding:34px 18px;text-align:center;color:var(--ink3);}
.ptbl .note{margin-top:16px;font-size:12.5px;color:var(--ink2);background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px 16px;line-height:1.7;}
.ptbl .note b{color:var(--ink);}
.ptbl-sub{position:fixed;inset:0;background:rgba(17,24,39,.45);display:none;align-items:center;justify-content:center;z-index:1300;padding:16px;}
.ptbl-sub.show{display:flex;}
.ptbl-dlg{width:380px;max-width:92vw;background:var(--card);border-radius:16px;overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,.25);}
.ptbl-dlg .mh{padding:15px 20px;border-bottom:1px solid var(--line2);font-weight:700;font-size:16px;color:var(--ink);}
.ptbl-dlg .mb{padding:16px 20px;}
.ptbl-dlg label{display:block;font-size:12.5px;color:var(--ink2);margin:0 0 6px;}
.ptbl-dlg .fld{height:44px;border:1px solid var(--line);border-radius:10px;padding:0 13px;display:flex;align-items:center;background:var(--line2);margin-bottom:13px;}
.ptbl-dlg .fld input,.ptbl-dlg .fld select{border:0;outline:0;background:transparent;flex:1;font-size:15px;color:var(--ink);}
.ptbl-dlg .seg{display:flex;gap:8px;margin-bottom:13px;}
.ptbl-dlg .seg button{flex:1;height:36px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink2);font-size:13px;cursor:pointer;}
.ptbl-dlg .seg button.on{background:var(--accent-weak);border-color:var(--btn-blue,var(--accent));color:var(--btn-blue,var(--accent));font-weight:700;}
.ptbl-dlg .two{display:flex;gap:10px;}
.ptbl-dlg .two>div{flex:1;}
.ptbl-dlg .mf{padding:0 20px 18px;display:flex;gap:10px;}
.ptbl-dlg .g{height:44px;padding:0 16px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink2);cursor:pointer;}
.ptbl-dlg .ok{flex:1;height:44px;border:0;border-radius:10px;background:var(--btn-blue,var(--accent));color:var(--accent-ink);font-weight:700;font-size:15px;cursor:pointer;}
.ptbl-dlg .ok:disabled{background:var(--line);cursor:not-allowed;}
`;

function ensureStyle(): void {
    if (document.getElementById('ptbl-style')) return;
    const s = document.createElement('style');
    s.id = 'ptbl-style';
    s.textContent = STYLE;
    document.head.appendChild(s);
}

// 进路由即渲染页面骨架到 #page-pos-tables(只建一次 · routeTo 控 .page 显隐)。
function ensureShell(sec: HTMLElement): void {
    if (sec.dataset.ptblInit === '1') return;
    ensureStyle();
    const plus =
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';
    sec.innerHTML = `<div class="ptbl">
        <div class="ph">
            <div><div class="tt">${escapeHtml(t('rtbl.title'))}</div><div class="sub">${escapeHtml(t('rtbl.sub'))}</div></div>
            <button class="btn primary" id="ptbl-add-area">${plus}${escapeHtml(t('rtbl.add_area'))}</button>
        </div>
        <div id="ptbl-body"></div>
        <div class="note">${t('rtbl.note')}</div>
    </div>`;
    sec.dataset.ptblInit = '1';
    sec.querySelector('#ptbl-add-area')!.addEventListener('click', () => openAreaDialog());
    sec.querySelector('#ptbl-body')!.addEventListener('click', onBodyClick);
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
    const dots =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/><circle cx="5" cy="12" r="1.6"/></svg>';
    const plus13 =
        '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';
    const seatSvg =
        '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>';
    const zones = areas
        .map(
            (a) =>
                `<div class="zone${a.id === activeArea ? ' on' : ''}" data-area="${a.id}">${escapeHtml(
                    a.name
                )} <span class="c">${a.table_count ?? 0}</span><span class="mg">${dots}</span></div>`
        )
        .join('');
    const inZone = tables.filter((tb) => tb.area_id === activeArea);
    const cur = areas.find((a) => a.id === activeArea);
    const tcard = (tb: Table) =>
        `<div class="t${tb.is_active ? '' : ' off'}" data-table="${tb.id}">
            <div class="top"><div class="no">${escapeHtml(tb.name)}</div><span class="more">⋯</span></div>
            <div class="seats">${tb.is_active ? seatSvg + escapeHtml(t('rtbl.seats_n').replace('{n}', String(tb.seats))) : escapeHtml(t('rtbl.disabled'))}</div>
            <div class="ops">${
                tb.is_active
                    ? `<button class="op" data-act="edit">${escapeHtml(t('rtbl.edit'))}</button><button class="op" data-act="disable">${escapeHtml(t('rtbl.disable'))}</button>`
                    : `<button class="op" data-act="enable">${escapeHtml(t('rtbl.enable'))}</button><button class="op" data-act="delete">${escapeHtml(t('rtbl.delete'))}</button>`
            }</div>
        </div>`;
    const addt = `<div class="addt" data-act="add-table"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>${escapeHtml(t('rtbl.add_table'))}</div>`;
    const grid = inZone.length
        ? `<div class="grid">${inZone.map(tcard).join('')}${addt}</div>`
        : `<div class="empty"><svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
            <div>${escapeHtml(t('rtbl.empty_tables'))}</div>
            <button class="btn primary e-btn" data-act="add-table">${plus13}${escapeHtml(t('rtbl.add_table'))}</button></div>`;
    body.innerHTML = `<div class="zones">${zones}</div>
        <div class="card">
            <div class="ch">
                <div class="zt">${escapeHtml(cur ? cur.name : '')}</div>
                <div class="zacts">
                    <span class="zlink" data-act="rename-area"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>${escapeHtml(t('rtbl.rename'))}</span>
                    <span class="zlink del" data-act="delete-area"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>${escapeHtml(t('rtbl.del_area'))}</span>
                    <button class="btn primary" data-act="add-table">${plus13}${escapeHtml(t('rtbl.add_table'))}</button>
                </div>
            </div>
            ${grid}
        </div>`;
}

async function load(): Promise<void> {
    // 按账套隔离 · 个人模式/未选账套 → 页内引导先选账套(不空请求)。
    const id = activeWsId();
    if (id == null) {
        const body = document.getElementById('ptbl-body');
        if (body) body.innerHTML = window.wsEmptyHtml ? window.wsEmptyHtml('ptbl-pick-ws') : '';
        const pick = document.getElementById('ptbl-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => load())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    ws = id;
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
    const zone = el.closest('.zone[data-area]') as HTMLElement | null;
    if (zone) {
        activeArea = Number(zone.dataset.area);
        renderBody('ok');
        return;
    }
    const act = (el.closest('[data-act]') as HTMLElement | null)?.dataset.act;
    if (act === 'add-table') return openTableDialog();
    if (act === 'rename-area') return openAreaDialog(curArea());
    if (act === 'delete-area') return deleteArea();
    const card = el.closest('.t[data-table]') as HTMLElement | null;
    if (!card || !act) return;
    const id = Number(card.dataset.table);
    const tb = tables.find((x) => x.id === id);
    if (act === 'edit' && tb) openTableDialog(tb);
    else if (act === 'disable') setTableActive(id, false);
    else if (act === 'enable') setTableActive(id, true);
    else if (act === 'delete' && tb) deleteTable(tb);
}

function curArea(): Area | undefined {
    return areas.find((a) => a.id === activeArea);
}

// 删区域(仅空区域;有桌台后端 409 → 专属人话)· 二次确认。
function deleteArea(): void {
    const a = curArea();
    if (!a) return;
    showDialog(
        t('rtbl.del_area'),
        `<div style="font-size:13.5px;color:var(--ink);line-height:1.6;">${escapeHtml(t('rtbl.del_area_confirm').replace('{name}', a.name))}</div>`,
        async () => {
            try {
                await call('DELETE', `/areas/${a.id}?workspace_client_id=${ws}`);
                activeArea = null;
                return true;
            } catch (err) {
                const code = err instanceof Error ? err.message : 'pos.unexpected';
                const key = code === 'pos.void_not_allowed' ? 'rtbl.area_has_tables' : code;
                showToast(posErrMsg(key, 'pos.unexpected'), 'error');
                return false;
            }
        }
    );
}

// 硬删:仅从没开过台的(后端校验)· 二次确认 · 开过台的 409 → 提示只能停用。
function deleteTable(tb: Table): void {
    showDialog(
        t('rtbl.delete'),
        `<div style="font-size:13.5px;color:var(--ink);line-height:1.6;">${escapeHtml(t('rtbl.del_confirm').replace('{name}', tb.name))}</div>`,
        async () => {
            try {
                await call('DELETE', `/tables/${tb.id}?workspace_client_id=${ws}`);
                return true;
            } catch (e) {
                // 开过台(有历史)→ 后端 409 pos.void_not_allowed:留账只能停用,给专属人话。
                const code = e instanceof Error ? e.message : 'pos.unexpected';
                const key = code === 'pos.void_not_allowed' ? 'rtbl.del_has_history' : code;
                showToast(posErrMsg(key, 'pos.unexpected'), 'error');
                return false;
            }
        }
    );
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

// ── 区域弹窗(新增 / 改名)──
function openAreaDialog(area?: Area): void {
    const isEdit = !!area;
    showDialog(
        isEdit ? t('rtbl.rename_area') : t('rtbl.add_area'),
        `<label>${escapeHtml(t('rtbl.area_name'))}</label><div class="fld"><input id="ptbl-an" maxlength="40" value="${area ? escapeHtml(area.name) : ''}" placeholder="${escapeHtml(t('rtbl.area_ph'))}"></div>`,
        async () => {
            const name = (document.getElementById('ptbl-an') as HTMLInputElement).value.trim();
            if (!name) return false;
            if (area) await call('PATCH', `/areas/${area.id}`, { workspace_client_id: ws, name });
            else {
                await call('POST', '/areas', { workspace_client_id: ws, name });
                activeArea = null; // 让 load 选回有效区
            }
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

// 路由 'pos-tables' 进入即调(core-boot ROUTE_LOADERS)· 渲染到 #page-pos-tables 平铺 section。
// owner 门控由 nav(module-nav:餐厅+pos+owner 才显 nav-pos-tables)把守;此处只渲染。页内动作仍弹窗。
window.loadPosTables = function () {
    const sec = document.getElementById('page-pos-tables');
    if (!sec) return;
    ensureShell(sec);
    load();
};
