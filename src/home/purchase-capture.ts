// 商户采购 · 采集屏(记一笔采购)· 列表主按钮 routeTo 进来 · 照搬草稿 s-capture。
// 桌面:拖拽区 + 上传文件 / 手工录入;手机:拍照(原生相机)/ 相册 / 文件 + 手工录入。
// 文件 → 统一智能入口 /api/purchase/intake 分流:draft→复核屏,否则落待归类。
// 识别阶段(可能 9~61s)有持久进度态:票据预览 + 转圈 + 文案 + 返回 · 失败可重试(不再 toast 一闪而过)。
/* global t, escapeHtml, showToast */
import { papi, activeWsId, purchaseErrMsg, injectPurBase, injectStyle } from './purchase-common.js';

const PAGE_CSS = `
.pur.cap .ph{display:flex;align-items:center;gap:10px;margin-bottom:16px;}
.pur.cap .back{cursor:pointer;color:var(--ink2);font-size:24px;line-height:1;flex:none;}
.pur.cap .ph .t{font-size:20px;font-weight:700;}
.pur.cap .panel{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);padding:16px;}
.pur.cap .note{background:var(--bg);border-radius:10px;padding:10px 12px;font-size:12.5px;color:var(--ink2);margin-bottom:14px;display:flex;gap:7px;align-items:flex-start;}
.pur.cap .note .ic{width:16px;height:16px;flex:none;margin-top:1px;}
.pur.cap .note b{color:var(--ink);}
.pur.cap .drop{border:2px dashed var(--accent);background:var(--accent-weak);border-radius:16px;padding:34px 16px;text-align:center;margin-bottom:14px;color:var(--accent-deep);cursor:pointer;}
.pur.cap .drop.over{background:var(--accent);color:var(--accent-ink);}
.pur.cap .drop .di{width:26px;height:26px;}
.pur.cap .drop .dt{font-weight:700;margin:8px 0 3px;color:var(--ink);}
.pur.cap .drop.over .dt{color:var(--accent-ink);}
.pur.cap .drop .dh{font-size:12px;color:var(--ink2);}
.pur.cap .row2{display:flex;gap:10px;}
.pur.cap .row2 .btn{flex:1;justify-content:center;}
.pur.cap .srcrow{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;}
.pur.cap .srcrow button{border:1px solid var(--line);background:var(--card);border-radius:12px;padding:15px 6px;display:flex;flex-direction:column;align-items:center;gap:7px;font-weight:700;font-size:12.5px;color:var(--ink);cursor:pointer;}
.pur.cap .srcrow button .si{width:26px;height:26px;}
.pur.cap .only-desk{display:block;} .pur.cap .only-mob{display:none;}
@media(max-width:600px){ .pur.cap .only-desk{display:none;} .pur.cap .only-mob{display:block;} }
/* 识别进度态 / 失败态 */
.pur.cap .recog{display:flex;flex-direction:column;align-items:center;text-align:center;padding:30px 20px;}
.pur.cap .preview{width:132px;height:172px;border-radius:12px;border:1px solid var(--line);background:var(--line2);overflow:hidden;display:flex;align-items:center;justify-content:center;margin-bottom:20px;color:var(--ink3);}
.pur.cap .preview img{width:100%;height:100%;object-fit:cover;}
.pur.cap .spin{width:30px;height:30px;border-radius:50%;border:3px solid var(--line);border-top-color:var(--accent);animation:pcapspin .8s linear infinite;margin-bottom:14px;}
@keyframes pcapspin{to{transform:rotate(360deg);}}
.pur.cap .rtitle{font-size:15px;font-weight:700;margin-bottom:6px;}
.pur.cap .rhint{font-size:12.5px;color:var(--ink2);max-width:320px;line-height:1.6;}
.pur.cap .recog.err .spin{display:none;}
.pur.cap .recog.err .rtitle{color:var(--red);}
.pur.cap .recog .acts{display:flex;gap:10px;margin-top:18px;}
`;

const IC_UP =
    '<svg class="di" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 16a4 4 0 01-.5-7.97 5 5 0 019.6-1.5A3.5 3.5 0 0117 16"/><path d="M12 12v7M9 15l3-3 3 3"/></svg>';
const IC_FILE =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/></svg>';
const IC_DOC =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M9 13h6M9 17h4"/></svg>';
const IC_DOC_LG =
    '<svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M9 13h6M9 17h4"/></svg>';
const IC_CAM =
    '<svg class="si" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h3l1.5-2h7L17 8h3v11H4z"/><circle cx="12" cy="13" r="3.2"/></svg>';
const IC_IMG =
    '<svg class="si" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 16l5-5 4 4 3-3 6 6"/><circle cx="8.5" cy="9" r="1.3"/></svg>';
const IC_FILE_LG =
    '<svg class="si" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/></svg>';
const IC_INFO =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 012-2h4l2 3h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>';

function sec(): HTMLElement | null {
    return document.getElementById('page-purchase-capture');
}

function headHtml(): string {
    return `<div class="ph"><span class="back" id="cap-back" title="${escapeHtml(t('pur-back'))}" aria-label="${escapeHtml(t('pur-back'))}">‹</span><div class="t">${escapeHtml(t('pur-record-purchase'))}</div></div>`;
}

function bindBack(): void {
    const back = document.getElementById('cap-back');
    if (back) back.onclick = () => window.routeTo?.('purchase');
}

// 识别中:持久进度态(票据预览 + 转圈 + 文案)· 破图回退图标。
function renderRecognizing(f: File): void {
    const s = sec();
    if (!s) return;
    const isImg = f.type.startsWith('image/');
    const preview = isImg ? `<img src="${URL.createObjectURL(f)}" alt="">` : IC_DOC_LG;
    s.innerHTML = `<div class="pur cap"><div class="wrap">${headHtml()}
        <div class="panel"><div class="recog">
            <div class="preview">${preview}</div>
            <div class="spin"></div>
            <div class="rtitle">${escapeHtml(t('pur-cap-recognizing'))}</div>
            <div class="rhint">${escapeHtml(t('pur-cap-recog-hint'))}</div>
        </div></div>
    </div></div>`;
    bindBack();
}

function renderError(f: File, msg: string): void {
    const s = sec();
    if (!s) return;
    s.innerHTML = `<div class="pur cap"><div class="wrap">${headHtml()}
        <div class="panel"><div class="recog err">
            <div class="preview">${IC_DOC_LG}</div>
            <div class="rtitle">${escapeHtml(t('pur-cap-recog-fail'))}</div>
            <div class="rhint">${escapeHtml(msg)}</div>
            <div class="acts"><button class="btn" id="cap-reselect">${escapeHtml(t('pur-cap-reselect'))}</button><button class="btn primary" id="cap-retry">${escapeHtml(t('pur-cap-retry'))}</button></div>
        </div></div>
    </div></div>`;
    bindBack();
    const re = document.getElementById('cap-retry');
    if (re) re.onclick = () => intakeFile(f);
    const rs = document.getElementById('cap-reselect');
    if (rs) rs.onclick = () => renderShell();
}

// 文件 → 统一智能入口分流(F12):draft→复核屏录入;sales/recon→提示后回采集屏;否则落待归类。
async function intakeFile(f: File): Promise<void> {
    renderRecognizing(f);
    const ws = activeWsId();
    const fd = new FormData();
    fd.append('image', f);
    if (ws != null) fd.append('workspace_client_id', String(ws));
    try {
        const res = (await papi('POST', '/api/purchase/intake', fd)) as {
            route?: string;
            draft?: Record<string, unknown> | null;
            dedupe_hit?: boolean;
            doc_id?: string;
        };
        // 自动入账(设置开):直接记账 → 开详情(可看/改/撤销),不进复核屏。
        if (res && res.route === 'booked' && res.doc_id) {
            showToast(t('pur-cap-booked'), 'success');
            window.openPurchaseDetail?.(res.doc_id);
            return;
        }
        const d = res && res.draft;
        if (d) {
            window.openPurchaseForm?.(null, {
                ...d,
                dedupe_hit: res.dedupe_hit,
                bill_image_local: URL.createObjectURL(f),
            });
            maybeAutobookHint();
            return;
        }
        const route = (res && res.route) || 'inbox';
        if (route === 'sales') {
            showToast(t('pur-intake-sales'), 'error');
            renderShell();
        } else if (route === 'recon') {
            showToast(t('pur-intake-recon'), 'error');
            renderShell();
        } else {
            showToast(t('pur-intake-inbox'), 'success');
            window.routeTo?.('purchase-inbox');
        }
    } catch (e) {
        renderError(f, purchaseErrMsg(e, 'purchase.unexpected'));
    }
}

// 首次记账(走了复核屏=没开自动入账)→ 一次性提示可去采购设置开自动入账(省去逐张复核)。
function maybeAutobookHint(): void {
    try {
        if (localStorage.getItem('pearnly_pur_autobook_hint')) return;
        localStorage.setItem('pearnly_pur_autobook_hint', '1');
        setTimeout(() => showToast(t('pur-cap-autobook-hint'), 'info'), 1400);
    } catch (_) {
        /* localStorage 不可用 → 跳过提示 */
    }
}

function pickFile(accept: string, capture?: string): void {
    const inp = document.createElement('input');
    inp.type = 'file';
    inp.accept = accept;
    if (capture) inp.setAttribute('capture', capture);
    inp.onchange = () => {
        const f = inp.files && inp.files[0];
        if (f) intakeFile(f);
    };
    inp.click();
}

function shell(wsName: string): string {
    return `<div class="pur cap"><div class="wrap">${headHtml()}
        <div class="panel">
            <div class="note">${IC_INFO}<span>${escapeHtml(t('pur-cap-booking-to'))} <b>${escapeHtml(wsName)}</b> · ${escapeHtml(t('pur-cap-switch-hint'))}</span></div>
            <div class="drop" id="cap-drop">${IC_UP}
                <div class="dt only-desk">${escapeHtml(t('pur-cap-drop-desk'))}</div>
                <div class="dt only-mob">${escapeHtml(t('pur-cap-drop-mob'))}</div>
                <div class="dh">${escapeHtml(t('pur-cap-formats'))}</div>
            </div>
            <div class="only-desk row2">
                <button class="btn primary" id="cap-upload">${IC_FILE}${escapeHtml(t('pur-cap-upload'))}</button>
                <button class="btn" id="cap-manual-d">${IC_DOC}${escapeHtml(t('pur-cap-manual'))}</button>
            </div>
            <div class="only-mob">
                <div class="srcrow">
                    <button id="cap-photo">${IC_CAM}${escapeHtml(t('pur-cap-photo'))}</button>
                    <button id="cap-album">${IC_IMG}${escapeHtml(t('pur-cap-album'))}</button>
                    <button id="cap-files">${IC_FILE_LG}${escapeHtml(t('pur-cap-file'))}</button>
                </div>
                <button class="btn" id="cap-manual-m" style="width:100%;justify-content:center;">${IC_DOC}${escapeHtml(t('pur-cap-manual-mob'))}</button>
            </div>
        </div>
    </div></div>`;
}

function renderShell(): void {
    const s = sec();
    if (!s) return;
    s.innerHTML = shell(wsName());
    bindBack();
    const manual = () => window.openPurchaseForm?.(null, { doc_kind: 'expense' });
    ['cap-manual-d', 'cap-manual-m'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.onclick = manual;
    });
    const up = document.getElementById('cap-upload');
    if (up) up.onclick = () => pickFile('image/*,application/pdf');
    const photo = document.getElementById('cap-photo');
    if (photo) photo.onclick = () => pickFile('image/*', 'environment');
    const album = document.getElementById('cap-album');
    if (album) album.onclick = () => pickFile('image/*');
    const files = document.getElementById('cap-files');
    if (files) files.onclick = () => pickFile('image/*,application/pdf');
    const drop = document.getElementById('cap-drop');
    if (drop) {
        drop.onclick = () => pickFile('image/*,application/pdf');
        drop.ondragover = (e) => {
            e.preventDefault();
            drop.classList.add('over');
        };
        drop.ondragleave = () => drop.classList.remove('over');
        drop.ondrop = (e) => {
            e.preventDefault();
            drop.classList.remove('over');
            const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
            if (f) intakeFile(f);
        };
    }
}

function wsName(): string {
    return (
        (window._userInfo && (window._userInfo as { company_name?: string }).company_name) ||
        t('pur-cap-current-ws')
    );
}

window.loadPurchaseCapture = function () {
    injectPurBase();
    injectStyle('pur-capture-css', PAGE_CSS);
    renderShell();
};
