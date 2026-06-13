// 对账中心重设计 · 模板中心抽屉 + 引导横幅 + 导入说明弹窗 + 真后端模板下载(2026-06-14)
// 下载走 GET /api/recon/template/{doc_type}?lang=<UI语言>,真 .xlsx(后端含列头+示例+说明 sheet)。
// 严禁前端临时生成 CSV。
import { RX, rxCfg, rxLang, rxToken, rxEsc, tt } from './recon-center-x-store.js';

const $ = (id: string) => document.getElementById(id);

const TPL_INFO: Record<string, { name: [string, string]; desc: [string, string] }> = {
    statement: {
        name: ['rcx-tpl-statement', '银行账单标准模板'],
        desc: ['rcx-tpl-statement-d', '日期 · 摘要 · 提款 · 存款 · 余额'],
    },
    gl: {
        name: ['rcx-tpl-gl', '总账 GL 标准模板'],
        desc: ['rcx-tpl-gl-d', '日期 · 凭证号 · 科目代码 · 摘要 · 借方 · 贷方'],
    },
    vat: {
        name: ['rcx-tpl-vat', '销项税报告标准模板'],
        desc: ['rcx-tpl-vat-d', '日期 · 发票号 · 买方名 · 买方税号 · 分支 · 税前 · 税额 · 合计'],
    },
    invoice: {
        name: ['rcx-tpl-invoice', '销项发票明细标准模板'],
        desc: [
            'rcx-tpl-invoice-d',
            '日期 · 发票号 · 买方名 · 买方税号 · 分支 · 税前 · 税额 · 合计',
        ],
    },
};
const DRAWER_TITLE: Record<string, [string, string]> = {
    bank: ['rcx-tplpanel-bank', '银行对账模板'],
    income: ['rcx-tplpanel-income', '收入对账模板'],
    tax: ['rcx-tplpanel-tax', '销项税报告核查模板'],
};

let dlBusy = false;

// 真后端下载:fetch+blob 带鉴权(裸 <a href> 不带 Authorization)
export async function downloadTemplate(doc: string): Promise<boolean> {
    try {
        const resp = await fetch(
            '/api/recon/template/' + encodeURIComponent(doc) + '?lang=' + rxLang(),
            { headers: { Authorization: 'Bearer ' + rxToken() } }
        );
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            if (window.showToast)
                window.showToast((err as any).detail || tt('rcx-dl-fail', '模板下载失败'), 'error');
            return false;
        }
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') || '';
        const m = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fn = m ? m[1].replace(/['"]/g, '') : 'Pearnly_' + doc + '.xlsx';
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fn;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        return true;
    } catch (e) {
        if (window.showToast)
            window.showToast(
                tt('rcx-dl-fail', '模板下载失败') + ': ' + (e as Error).message,
                'error'
            );
        return false;
    }
}

// 下载当前对账两个模板(顺序真下载;防重复点击)
export async function downloadPageTemplates(btn?: HTMLButtonElement | null) {
    if (dlBusy) return;
    dlBusy = true;
    if (btn) btn.classList.add('rcx-loading');
    const cfg = rxCfg();
    const okL = await downloadTemplate(cfg.leftDoc);
    await new Promise((r) => setTimeout(r, 400));
    const okR = await downloadTemplate(cfg.rightDoc);
    if (btn) btn.classList.remove('rcx-loading');
    dlBusy = false;
    if (okL && okR && window.showToast)
        window.showToast(tt('rcx-dl-both-ok', '已下载本页两个模板'), 'success');
}

export function downloadSide(side: 'left' | 'right') {
    const cfg = rxCfg();
    return downloadTemplate(side === 'left' ? cfg.leftDoc : cfg.rightDoc);
}

// ── 模板中心抽屉:内容随当前对账类型 ─────────────────────────────
export function renderTemplates() {
    const cfg = rxCfg();
    const title = $('rcx-tplpanel-title');
    if (title) {
        const [k, zh] = DRAWER_TITLE[RX.tab] || DRAWER_TITLE.bank;
        title.textContent = tt(k, zh);
    }
    const list = $('rcx-template-list');
    if (!list) return;
    const docs = [cfg.leftDoc, cfg.rightDoc];
    list.innerHTML = docs
        .map((doc) => {
            const info = TPL_INFO[doc];
            return `
      <div class="rcx-template-card">
        <div class="rcx-template-top">
          <div class="rcx-template-icon">XLSX</div>
          <div class="rcx-template-meta">
            <b>${rxEsc(tt(info.name[0], info.name[1]))}</b>
            <p>${rxEsc(tt(info.desc[0], info.desc[1]))}</p>
          </div>
          <span class="rcx-reco-pill">${tt('rcx-recommend', '推荐')}</span>
        </div>
        <div class="rcx-template-actions">
          <button class="rcx-btn rcx-sm" data-rcx-dl-doc="${doc}" type="button">${tt('rcx-dl-template-btn', '下载模板')}</button>
        </div>
        <p class="rcx-tpl-hint">${tt('rcx-tpl-note', '模板内含列头、示例行与填写说明')}</p>
      </div>`;
        })
        .join('');
}

export function openDrawer() {
    renderTemplates();
    const ov = $('rcx-tplpanel-overlay');
    const dr = $('rcx-tplpanel');
    if (ov) ov.classList.add('rcx-show');
    if (dr) {
        dr.classList.add('rcx-show');
        dr.setAttribute('aria-hidden', 'false');
    }
}
export function closeDrawer() {
    const ov = $('rcx-tplpanel-overlay');
    const dr = $('rcx-tplpanel');
    if (ov) ov.classList.remove('rcx-show');
    if (dr) {
        dr.classList.remove('rcx-show');
        dr.setAttribute('aria-hidden', 'true');
    }
}

// ── 导入说明弹窗(纯说明,不改上传态)────────────────────────────
export function openGuide() {
    const ov = $('rcx-modal-overlay');
    const md = $('rcx-guide-modal');
    if (ov) ov.classList.add('rcx-show');
    if (md) md.classList.add('rcx-show');
}
export function closeModals() {
    const ov = $('rcx-modal-overlay');
    if (ov) ov.classList.remove('rcx-show');
    document.querySelectorAll('.rcx-modal.rcx-show').forEach((m) => m.classList.remove('rcx-show'));
}
