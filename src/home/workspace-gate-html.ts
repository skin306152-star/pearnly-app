// 套账硬门 + 顶栏富下拉切换器 · 样式 + 卡片/空态/orgPop 模板(从 workspace-gate 抽出控行数)。
// 复用 onboarding 的 stage 壳(.onb-root/.onb-top/.onb-body/.onb-pane/.onb-h1/.onb-sub/.onb-btn)。
// 交互基准:桌面 Pearnly_用户引导闭环_UI预览/01-交互原型.html(renderPick 全屏门 + orgPop 顶栏下拉)。
/* global t, escapeHtml */

const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));

const ICON: Record<string, string> = {
    building:
        '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    chev: '<path d="m9 18 6-6-6-6"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    box: '<path d="M21 8v8a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 2 16V8a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8z"/><path d="m3.3 7 8.7 5 8.7-5M12 22V12"/>',
};

export function wsgIcon(name: string, cls = ''): string {
    return (
        `<svg class="wsg-i ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
        `stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">` +
        (ICON[name] || '') +
        '</svg>'
    );
}

export function wsgInitials(name: string): string {
    const s = String(name || '').trim();
    return esc(s.slice(0, 2) || '#');
}

interface Subject {
    id: number;
    name?: string;
    tax_id?: string;
    subject_type?: string;
    invoice_count?: number;
}

function subtitle(c: Subject): string {
    if (String(c.subject_type) === 'personal') return esc(t('wsg-personal-sub'));
    const tax = c.tax_id ? esc(t('wsg-tax-prefix')) + ' ' + esc(c.tax_id) : esc(t('wsg-no-tax'));
    const n = Number(c.invoice_count || 0);
    return n > 0 ? tax + ' · ' + esc(t('wsg-invoice-count').replace('{n}', String(n))) : tax;
}

// 全屏门:主体卡列表 + 「新建主体」行(renderPick 逐屏搬)。
export function wsgListHtml(subjects: Subject[], activeId: number | null): string {
    const cards = subjects
        .map(
            (c) =>
                `<button class="wsg-card${activeId != null && Number(activeId) === Number(c.id) ? ' on' : ''}" data-wsg-pick="${c.id}">` +
                `<span class="wsg-co">${wsgInitials(c.name || '#' + c.id)}</span>` +
                `<span class="wsg-info"><span class="wsg-nm">${esc(c.name || '#' + c.id)}</span>` +
                `<span class="wsg-sub">${subtitle(c)}</span></span>` +
                wsgIcon('chev', 'wsg-chev') +
                '</button>'
        )
        .join('');
    const create = `<button class="wsg-new" data-wsg-new="1">${wsgIcon('plus')}<span>${esc(t('wsg-create'))}</span></button>`;
    return `<div class="wsg-list">${cards}${create}</div>`;
}

// 空态:owner(暂无套账·无法做业务·新建套账)/ 受邀成员(等管理员分配·无新建)。
export function wsgEmptyHtml(isOwner: boolean): string {
    if (isOwner) {
        return (
            '<div class="wsg-empty"><div class="wsg-empty-ic">' +
            wsgIcon('building') +
            `</div><div class="wsg-empty-t">${esc(t('wsg-empty-owner-t'))}</div>` +
            `<div class="wsg-empty-d">${esc(t('wsg-empty-owner-d'))}</div>` +
            `<button class="onb-btn pri" data-wsg-new="1">${wsgIcon('plus')}${esc(t('wsg-create'))}</button></div>`
        );
    }
    return (
        '<div class="wsg-empty"><div class="wsg-empty-ic">' +
        wsgIcon('users') +
        `</div><div class="wsg-empty-t">${esc(t('wsg-empty-member-t'))}</div>` +
        `<div class="wsg-empty-d">${esc(t('wsg-empty-member-d'))}</div></div>`
    );
}

export const WSG_CSS = `
.wsg-i{width:18px;height:18px;flex:none;}
.wsg-list{margin-top:26px;display:flex;flex-direction:column;gap:10px;}
.wsg-card{display:flex;align-items:center;gap:13px;border:1.5px solid var(--line);border-radius:14px;
  padding:14px 16px;background:var(--card);cursor:pointer;transition:.12s;text-align:left;width:100%;color:var(--ink);}
.wsg-card:hover{border-color:var(--accent);}
.wsg-card.on{border-color:var(--accent);background:var(--accent-weak);}
.wsg-co{width:42px;height:42px;border-radius:12px;background:var(--accent-weak);color:var(--accent);
  font-weight:700;font-size:15px;display:flex;align-items:center;justify-content:center;flex:none;}
.wsg-card.on .wsg-co{background:var(--card);}
.wsg-info{flex:1;min-width:0;display:flex;flex-direction:column;}
.wsg-nm{font-weight:650;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.wsg-sub{color:var(--ink3);font-size:11.5px;margin-top:2px;}
.wsg-chev{color:var(--ink3);}
.wsg-new{display:flex;align-items:center;justify-content:center;gap:8px;border:1.5px dashed var(--line);
  border-radius:14px;padding:15px;color:var(--accent);font-weight:650;font-size:13.5px;background:none;cursor:pointer;width:100%;}
.wsg-new:hover{border-color:var(--accent);background:var(--accent-weak);}
.wsg-empty{margin-top:24px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:6px;}
.wsg-empty-ic{width:60px;height:60px;border-radius:18px;background:var(--accent-weak);color:var(--accent);
  display:flex;align-items:center;justify-content:center;margin-bottom:8px;}
.wsg-empty-ic .wsg-i{width:28px;height:28px;}
.wsg-empty-t{font-size:17px;font-weight:700;}
.wsg-empty-d{color:var(--ink2);font-size:13px;line-height:1.7;max-width:min(380px,100%);margin-bottom:8px;}
.wsg-logout{margin-left:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;
  color:var(--ink2);font-size:13.5px;font-weight:600;padding:7px 14px;cursor:pointer;transition:.12s;}
.wsg-logout:hover{border-color:var(--ink3);color:var(--accent);}
.wsg-loading{width:30px;height:30px;margin:64px auto 0;border:3px solid var(--line);border-top-color:var(--accent);
  border-radius:50%;animation:wsg-spin .8s linear infinite;}
@keyframes wsg-spin{to{transform:rotate(360deg);}}
/* 顶栏富下拉切换器(orgPop · 照 01) */
.wsw{display:inline-flex;align-items:center;gap:10px;border:1px solid var(--line);border-radius:11px;
  height:36px;padding:0 8px 0 12px;background:var(--card);cursor:pointer;transition:.12s;color:var(--ink);}
.wsw:hover{border-color:var(--ink3);}
.wsw .wsw-co{width:24px;height:24px;border-radius:7px;background:var(--accent-weak);color:var(--accent);
  font-weight:700;font-size:11px;display:flex;align-items:center;justify-content:center;}
.wsw .wsw-nm{font-size:13px;font-weight:650;max-width:min(180px,100%);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.wsw .wsg-i{width:14px;height:14px;color:var(--ink3);}
.orgsw{position:relative;}
.orgsw-pop{position:absolute;top:44px;left:0;width:300px;background:var(--card);border:1px solid var(--line);
  border-radius:15px;box-shadow:var(--sh2);z-index:1100;overflow:hidden;}
.orgsw-srch{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid var(--line2);}
.orgsw-srch input{border:0;outline:0;background:none;color:var(--ink);font-size:12.5px;width:100%;}
.orgsw-srch .wsg-i{width:14px;height:14px;color:var(--ink3);}
.orgsw-cap{font-size:10.5px;color:var(--ink3);font-weight:700;letter-spacing:.3px;padding:9px 14px 3px;}
.orgsw-list{padding:2px 6px 6px;max-height:300px;overflow:auto;}
.orgsw-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:10px;cursor:pointer;width:100%;border:0;background:none;text-align:left;color:var(--ink);}
.orgsw-item:hover{background:var(--line2);}
.orgsw-item.on{background:var(--accent-weak);}
.orgsw-item .oco{width:30px;height:30px;border-radius:9px;background:var(--accent-weak);color:var(--accent);
  font-weight:700;font-size:12px;display:flex;align-items:center;justify-content:center;flex:none;}
.orgsw-item.on .oco{background:var(--card);}
.orgsw-item .oinfo{flex:1;min-width:0;}
.orgsw-item .onm{font-weight:600;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.orgsw-item .ocm{color:var(--ink3);font-size:11px;}
.orgsw-item .ochk{color:var(--accent);width:17px;height:17px;flex:none;}
.orgsw-foot{border-top:1px solid var(--line2);padding:6px;}
.orgsw-fa{display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;border:0;background:none;
  border-radius:10px;font-size:13px;color:var(--ink2);font-weight:550;cursor:pointer;}
.orgsw-fa:hover{background:var(--line2);color:var(--accent);}
.orgsw-fa .wsg-i{width:15px;height:15px;}
.orgsw-empty{padding:14px;color:var(--ink3);font-size:12px;text-align:center;}
`;
