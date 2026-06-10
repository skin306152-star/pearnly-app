// ============================================================
// 客户知识 · 功能介绍 + 费用弹窗(KNOWLEDGE feature · 阶段5)
//
// 页头「功能介绍 · 费用」按钮触发。讲清真实用处 + 费用构成。
// 费用金额为示意占位(标「待定」),最终定价由 Zihao 拍板后填真数。用 .modal 体系。
// ============================================================
import { KB_CAT, kbEsc, kbIcon, kbModalShell, kbT, type KbModal } from './knowledge-api.js';

let _shell: KbModal | null = null;

function ensureDom(): void {
    if (_shell) return;

    const st = document.createElement('style');
    st.id = 'kb-info-style';
    st.textContent = `
.kb-info-mask{position:fixed;inset:0;background:rgba(17,17,17,.42);z-index:1300;display:none;align-items:center;justify-content:center;padding:20px}
.kb-info-mask.open{display:flex}
.kb-info-modal{background:var(--card);border-radius:16px;width:560px;max-width:100%;max-height:88vh;overflow:auto;box-shadow:0 30px 80px rgba(17,17,17,.3)}
.kb-info-head{display:flex;align-items:flex-start;gap:14px;padding:22px 24px 0}
.kb-info-head .ic{width:52px;height:52px;border-radius:13px;background:var(--amber-weak);overflow:hidden;display:grid;place-items:center;flex-shrink:0}
.kb-info-head .ic img{width:48px;height:48px;object-fit:cover;object-position:center 14%}
.kb-info-head h2{font-size:18px;font-weight:800;margin:0}
.kb-info-head .lead{color:var(--ink-2,#555);font-size:12.5px;margin-top:3px;line-height:1.55}
.kb-info-head .x{margin-left:auto;color:var(--ink-3,#999);width:30px;height:30px;border-radius:8px;display:grid;place-items:center;cursor:pointer;border:none;background:none;flex-shrink:0}
.kb-info-head .x svg{width:16px;height:16px}
.kb-info-head .x:hover{background:var(--bg,var(--line2));color:var(--ink,var(--ink))}
.kb-info-body{padding:18px 24px 24px}
.kb-info-h{font-size:13px;font-weight:800;margin:18px 0 9px;display:flex;align-items:center;gap:8px}
.kb-info-h .l{width:4px;height:14px;border-radius:3px;background:var(--btn-blue,var(--accent))}
.kb-info-use{list-style:none;display:flex;flex-direction:column;gap:9px;padding:0;margin:0}
.kb-info-use li{display:flex;gap:10px;font-size:12.5px;color:var(--ink-2,#555);line-height:1.55}
.kb-info-use li .ck{width:20px;height:20px;border-radius:6px;background:var(--info-bg,var(--accent-weak));color:var(--info-ink,var(--accent-deep));display:grid;place-items:center;flex-shrink:0}
.kb-info-use li .ck svg{width:13px;height:13px;stroke-width:2.4}
.kb-info-price{border:1px solid var(--line,var(--line));border-radius:12px;overflow:hidden}
.kb-info-price .row{display:flex;align-items:center;gap:12px;padding:13px 15px;border-bottom:1px solid var(--line,var(--line))}
.kb-info-price .row:last-child{border-bottom:none}
.kb-info-price .pi{width:34px;height:34px;border-radius:9px;background:var(--bg,var(--line2));display:grid;place-items:center;color:var(--ink-2,#555);flex-shrink:0}
.kb-info-price .pi svg{width:17px;height:17px}
.kb-info-price .pm{flex:1}
.kb-info-price .pm b{font-weight:700;font-size:13px}
.kb-info-price .pm .d{font-size:11px;color:var(--ink-3,#999);margin-top:1px;line-height:1.4}
.kb-info-price .amt{font-size:11px;font-weight:700;color:var(--ink-3,#999);background:var(--bg,var(--line2));border-radius:7px;padding:4px 9px;white-space:nowrap}
.kb-info-tbd{display:flex;align-items:flex-start;gap:8px;background:var(--amber-weak);color:var(--amber);border:1px solid var(--amber-weak);border-radius:8px;padding:9px 12px;font-size:11.5px;font-weight:600;margin-top:12px;line-height:1.5}
.kb-info-foot{display:flex;justify-content:flex-end;padding:0 24px 22px}
`;
    document.head.appendChild(st);

    _shell = kbModalShell('info');
}

function useItem(key: string, fb: string): string {
    return `<li><span class="ck">${kbIcon('check')}</span><span>${kbEsc(kbT(key, fb))}</span></li>`;
}

function priceRow(
    icon: string,
    nameK: string,
    nameFb: string,
    descK: string,
    descFb: string,
    amtK: string,
    amtFb: string
): string {
    return `<div class="row"><div class="pi">${icon}</div>
        <div class="pm"><b>${kbEsc(kbT(nameK, nameFb))}</b><div class="d">${kbEsc(kbT(descK, descFb))}</div></div>
        <span class="amt">${kbEsc(kbT(amtK, amtFb))}</span></div>`;
}

function render(): void {
    const modal = _shell?.modal;
    if (!modal) return;
    modal.innerHTML = `
        <div class="kb-info-head">
            <span class="ic"><img src="${KB_CAT}" alt=""></span>
            <div>
                <h2>${kbEsc(kbT('kb-info-title', '客户知识助手是什么'))}</h2>
                <div class="lead">${kbEsc(kbT('kb-info-lead', '把每家客户的合同与规矩，变成系统记得住、能自动执行、还能随时问的「活资料」。'))}</div>
            </div>
            <button class="x" data-kb-info-close aria-label="close">${kbIcon('x')}</button>
        </div>
        <div class="kb-info-body">
            <div class="kb-info-h"><span class="l"></span>${kbEsc(kbT('kb-info-use-h', '它真正帮你省什么'))}</div>
            <ul class="kb-info-use">
                ${useItem('kb-info-use1', '把客户的合同、采购政策、内部规矩上传一次，AI 读懂后建成可检索的资料库 —— 不用再翻文件夹找合同。')}
                ${useItem('kb-info-use2', '做账时 AI 自动按这家客户的规矩检查发票：金额超上限、供应商要不要人工复核、差旅超标…… 异常当场标出来。')}
                ${useItem('kb-info-use3', '任意页面右下角随手问「这家客户能不能这样报」，答案都带合同原文出处，点一下就能核对，AI 不瞎编。')}
                ${useItem('kb-info-use4', '把老会计脑子里记的客户规矩，变成系统记住、新人也能直接上手 —— 给多家公司做账的事务所尤其值。')}
            </ul>
            <div class="kb-info-h"><span class="l"></span>${kbEsc(kbT('kb-info-cost-h', '费用怎么算'))}</div>
            <p style="font-size:12.5px;color:var(--ink-2,#555);margin:0 0 11px;line-height:1.55">${kbEsc(kbT('kb-info-cost-lead', '从你的泰铢余额按用量扣，不用不花，跟 OCR 共用一个余额池：'))}</p>
            <div class="kb-info-price">
                ${priceRow(kbIcon('upload'), 'kb-info-c1-n', '上传建库', 'kb-info-c1-d', 'PDF / 图片按页、文档按字符 —— 跟现在 OCR 同价', 'kb-info-c1-amt', '฿1.50/页起')}
                ${priceRow(kbIcon('message'), 'kb-info-c2-n', 'AI 问答', 'kb-info-c2-d', '每次带合同原文出处的回答', 'kb-info-c2-amt', '฿0.50/次')}
                ${priceRow(kbIcon('shield-check'), 'kb-info-c3-n', '自动发票检查', 'kb-info-c3-d', '死规则:算术 / 税号 / 查重 / 客户规矩', 'kb-info-c3-amt', '免费')}
            </div>
            <div class="kb-info-tbd"><span>${kbEsc(kbT('kb-info-note', '充值与扣费跟现有 OCR 共用同一个泰铢余额；问答按真实成本加合理毛利定价（与 OCR 同档）。'))}</span></div>
        </div>
        <div class="kb-info-foot"><button class="btn btn-primary" data-kb-info-close>${kbEsc(kbT('kb-info-close', '知道了'))}</button></div>
    `;
}

function open(): void {
    ensureDom();
    render();
    _shell?.open();
}

window._kbOpenInfo = open;
