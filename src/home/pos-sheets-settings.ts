// POS · Google Sheet 留档设置(老板后台 · 主程序)· window.loadPosSheets。
// 每笔售出自动追加一行到老板自己的 Google Sheet(留档用)。复用采购导出同一份 Google 凭据
// (export_google_credentials · 按套账隔离),只加"连去哪张表"配置。接 GET/PUT
// /api/pos/admin/sheets-settings + 复用 /api/integrations/google/connect|disconnect(return_to=pos)。
// owner 专属(收银员 403 + nav 不显)· 四态(加载/正常/保存中/错)· 信封 body.ok→data · 失败 posErrMsg。
/* global t, token, showToast, escapeHtml */
import { activeWsId, posErrMsg } from './inventory-common';

interface SheetsSettings {
    spreadsheet_id: string;
    tab_name: string;
    enabled: boolean;
    connected: boolean;
    email: string;
    sheet_url: string;
}

const URL = '/api/pos/admin/sheets-settings';
let ws = 0;

function hdr(): Record<string, string> {
    return {
        Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
        'Content-Type': 'application/json',
    };
}

async function callJson(path: string, method: string, body?: unknown): Promise<any> {
    let env: { ok?: boolean; data?: unknown; error?: { code?: string } };
    try {
        const r = await fetch(path, {
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

const call = (method: string, body?: unknown): Promise<SheetsSettings> =>
    callJson(URL + (method === 'GET' ? `?workspace_client_id=${ws}` : ''), method, body);

const STYLE = `
.rsheet{width:100%;margin:0;padding:26px 0 60px 28px;font-size:13.5px;color:var(--ink);}
.rsheet h1{font-size:21px;font-weight:700;color:var(--ink);margin:0 0 4px;}
.rsheet .sub{color:var(--ink2);font-size:13px;margin-bottom:18px;}
.rsheet .card{border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-bottom:16px;padding:16px;}
.rsheet .gst{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.rsheet .gst .badge{font-size:12px;padding:2px 9px;border-radius:999px;font-weight:600;}
.rsheet .gst .badge.on{background:var(--accent-weak);color:var(--btn-blue,var(--accent));}
.rsheet .gst .badge.off{background:var(--line2);color:var(--ink2);}
.rsheet .gst .em{color:var(--ink2);font-size:12.5px;}
.rsheet .ig-btn{height:36px;padding:0 16px;border-radius:9px;border:1px solid var(--line);background:var(--card);color:var(--ink);font-size:13px;font-weight:600;cursor:pointer;}
.rsheet .ig-btn.pri{background:var(--btn-blue,var(--accent));color:var(--accent-ink);border:0;}
.rsheet .hint{font-size:11.5px;color:var(--ink3);margin-top:6px;line-height:1.5;}
.rsheet .hint a{color:var(--btn-blue,var(--accent));font-weight:600;text-decoration:none;}
.rsheet .row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;}
.rsheet .row .n{font-size:14px;font-weight:600;color:var(--ink);}
.rsheet .sw{width:44px;height:25px;border-radius:999px;flex:0 0 44px;position:relative;cursor:pointer;transition:.15s;background:var(--line);}
.rsheet .sw::after{content:"";position:absolute;top:2px;left:2px;width:21px;height:21px;border-radius:50%;background:var(--card);transition:.15s;box-shadow:0 1px 3px rgba(0,0,0,.25);}
.rsheet .sw.on{background:var(--btn-blue,var(--accent));}.rsheet .sw.on::after{left:21px;}
.rsheet .save{position:sticky;bottom:16px;width:100%;height:50px;border:0;border-radius:11px;background:var(--btn-blue,var(--accent));color:var(--accent-ink);font-weight:700;font-size:16px;cursor:pointer;margin-top:18px;box-shadow:0 4px 16px rgba(0,0,0,.18);}
.rsheet .save:disabled{background:var(--line);cursor:not-allowed;}
.rsheet .state{padding:44px 0;text-align:center;color:var(--ink3);font-size:13.5px;}
`;

function ensureStyle(): void {
    if (document.getElementById('rsheet-style')) return;
    const s = document.createElement('style');
    s.id = 'rsheet-style';
    s.textContent = STYLE;
    document.head.appendChild(s);
}

function ensureShell(sec: HTMLElement): void {
    if (sec.dataset.rsheetInit === '1') return;
    ensureStyle();
    sec.innerHTML = `<div class="rsheet">
        <h1>${escapeHtml(t('psheet.title'))}</h1>
        <div class="sub">${escapeHtml(t('psheet.sub'))}</div>
        <div id="rsheet-body"><div class="state">${escapeHtml(t('rpay.loading'))}</div></div>
    </div>`;
    sec.dataset.rsheetInit = '1';
}

function render(s: SheetsSettings): void {
    const body = document.getElementById('rsheet-body');
    if (!body) return;
    const gst = s.connected
        ? `<span class="badge on">${escapeHtml(t('int-google-st-on'))}</span><span class="em">${escapeHtml(s.email ? t('int-google-connected-as', { email: s.email }) : '')}</span>`
        : `<span class="badge off">${escapeHtml(t('int-google-st-off'))}</span>`;
    const actBtn = s.connected
        ? `<button class="ig-btn" id="rsheet-disconnect">${escapeHtml(t('int-google-disconnect'))}</button>`
        : `<button class="ig-btn pri" id="rsheet-connect">${escapeHtml(t('int-google-connect'))}</button>`;
    const sheetLink = s.spreadsheet_id
        ? `<div class="hint">${escapeHtml(t('psheet.sheet_ready'))} <a href="${escapeHtml(s.sheet_url)}" target="_blank" rel="noopener">${escapeHtml(t('psheet.open_sheet'))}</a></div>`
        : `<div class="hint">${escapeHtml(t('psheet.auto_create_hint'))}</div>`;
    body.innerHTML = `<div class="card">
        <div class="gst">${gst}</div>
        <div class="hint">${escapeHtml(t('psheet.connect_hint'))}</div>
        ${actBtn}
        ${sheetLink}
        <div class="row"><div class="n">${escapeHtml(t('psheet.enabled'))}</div><div class="sw${s.enabled ? ' on' : ''}" id="rsheet-toggle"></div></div>
        </div>
        <button class="save" id="rsheet-save">${escapeHtml(t('rpay.save'))}</button>`;
    const toggle = document.getElementById('rsheet-toggle');
    if (toggle) toggle.addEventListener('click', () => toggle.classList.toggle('on'));
    const connectBtn = document.getElementById('rsheet-connect');
    if (connectBtn) connectBtn.addEventListener('click', gConnect);
    const disconnectBtn = document.getElementById('rsheet-disconnect');
    if (disconnectBtn) disconnectBtn.addEventListener('click', gDisconnect);
    const saveBtn = document.getElementById('rsheet-save');
    if (saveBtn) saveBtn.addEventListener('click', save);
}

async function gConnect(): Promise<void> {
    try {
        const data = (await callJson(
            `/api/integrations/google/connect/start?workspace_client_id=${ws}&return_to=pos`,
            'POST'
        )) as { url?: string };
        if (!data.url) throw new Error('missing_google_connect_url');
        window.location.href = data.url;
    } catch (e) {
        showToast(
            posErrMsg(e instanceof Error ? e.message : 'pos.unexpected', 'pos.unexpected'),
            'error'
        );
    }
}

async function gDisconnect(): Promise<void> {
    if (typeof window.showConfirm === 'function') {
        const okConfirm = await window.showConfirm(t('int-google-disconnect-confirm'));
        if (!okConfirm) return;
    }
    try {
        await callJson(`/api/integrations/google/disconnect?workspace_client_id=${ws}`, 'POST');
        showToast(t('int-google-disconnected'), 'success');
        load();
    } catch (e) {
        showToast(
            posErrMsg(e instanceof Error ? e.message : 'pos.unexpected', 'pos.unexpected'),
            'error'
        );
    }
}

async function save(): Promise<void> {
    const btn = document.getElementById('rsheet-save') as HTMLButtonElement;
    btn.disabled = true;
    const enabled = !!document.getElementById('rsheet-toggle')?.classList.contains('on');
    // 表头语言 = 当下老板后台界面语言(建表那一刻定死,后续追加沿用,不随收银员当下语言漂移)。
    const lang = window._currentLang || 'th';
    try {
        await call('PUT', { workspace_client_id: ws, enabled, lang });
        // PUT 只回业务字段(spreadsheet_id/tab_name/enabled)不带 connected/email → 重新拉一次取真连接态。
        await load();
        showToast(t('rpay.saved'), 'success');
    } catch (e) {
        btn.disabled = false;
        showToast(
            posErrMsg(e instanceof Error ? e.message : 'pos.unexpected', 'pos.unexpected'),
            'error'
        );
    }
}

async function load(): Promise<void> {
    const body = document.getElementById('rsheet-body');
    const id = activeWsId();
    if (id == null) {
        if (body) body.innerHTML = window.wsEmptyHtml ? window.wsEmptyHtml('rsheet-pick-ws') : '';
        const pick = document.getElementById('rsheet-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => load())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    ws = id;
    if (body) body.innerHTML = `<div class="state">${escapeHtml(t('rpay.loading'))}</div>`;
    try {
        render(await call('GET'));
    } catch (_) {
        if (body) body.innerHTML = `<div class="state">${escapeHtml(t('rpay.load_failed'))}</div>`;
    }
}

// 路由 'pos-sheets' 进入即调(core-boot ROUTE_LOADERS)· 渲染到 #page-pos-sheets 平铺 section。
// owner 门控由 nav(module-nav:pos+owner 才显 nav-pos-sheets)把守;此处只渲染。
window.loadPosSheets = function () {
    const sec = document.getElementById('page-pos-sheets');
    if (!sec) return;
    ensureShell(sec);
    load();
};
