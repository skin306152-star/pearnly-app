/*
 * Pearnly POS · pos-taxinv.js · 全式税票域(G2 凭小票号补开通路 + 结账完成页共用弹窗)
 *
 * 税票的弹窗 DOM、交互与 API 都收在这一个文件:
 * - #tax-mask 弹窗 JS 注入 document.body(与主站 pos-taxinv-modal 同范式):天然在
 *   .pos-view 作用域外,任何视图都能开;每次 openFor 重建,语言恒新鲜。
 * - POS.data.fullTaxInvoice / POS.data.taxLookup 定义在此、仍挂 data.*(餐厅紧凑弹窗
 *   等消费方挂载点不变,定义处随域走)。
 * - 税号 RD 带出(查不到诚实转手填)、Mod-11 前端镜像(与后端
 *   services/sales/buyer.th13_checksum_ok 同式)、买方档存回勾选、开出后自动开 A4 PDF。
 * - 已升级单在补开视图直接给「已开过 + 重打」卡,不进弹窗撞 409。对外 window.POS.taxinv。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const $ = (id) => document.getElementById(id);
    const fmt = POS.fmt;

    let taxSale = null; // 弹窗目标单 {id, receipt_no, grand_total, lines?}
    let taxOrigin = 'done'; // 'done'=结账完成页 · 'view'=补开视图(成功后回已开过卡)
    let taxBuyerType = 'company';
    let taxBranch = 'head';
    let todayItems = [];

    // ── 税票域 API(挂 POS.data · 定义随域走)──
    // 离线不可开税票(需联网连号 · 08 ADR v1 范围),仅纯本地预览回落 mock 演示。
    POS.data.fullTaxInvoice = async function (saleId, buyer, saveBuyer) {
        try {
            return await POS.apiFetch('POST', '/api/pos/sales/' + saleId + '/full-tax-invoice', {
                workspace_client_id: state.workspaceClientId,
                buyer,
                save_buyer: !!saveBuyer,
            });
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                return {
                    document: {
                        id: POS.uuid(),
                        doc_number: 'INV-LOCAL-' + Math.floor(Math.random() * 90000 + 10000),
                        doc_type: 'tax_invoice',
                    },
                };
            }
            throw e;
        }
    };
    // 税号 → RD 官方名称/地址(买方表单带出)。查不到/超时后端也回 found:false(不 4xx),
    // 不设 mock——查询失败诚实转手填。
    POS.data.taxLookup = function (taxId) {
        return POS.apiFetch(
            'GET',
            '/api/pos/tax-lookup?tax_id=' +
                encodeURIComponent(taxId) +
                (state.workspaceClientId ? '&workspace_client_id=' + state.workspaceClientId : '')
        );
    };

    // 泰国 13 位税号 Mod-11 校验位(后端同式;真号必过,打错一位即不过)。
    function th13Ok(v) {
        if (!/^\d{13}$/.test(v)) return false;
        let sum = 0;
        for (let i = 0; i < 12; i++) sum += Number(v[i]) * (13 - i);
        return Number(v[12]) === (11 - (sum % 11)) % 10;
    }

    // ════════════════ 弹窗 DOM(JS 注入 · 每次打开重建,语言恒新鲜)════════════════
    const SVG_X =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    const SVG_DOC =
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/></svg>';
    const SVG_OK =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>';
    const SVG_FIND =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
    const SVG_LOCK =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>';
    const SVG_PRINT =
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>';

    function modalHtml() {
        const t = POS.t;
        return (
            '<div class="modal tax-modal">' +
            '<div class="modal-head"><div class="t">' +
            t('posui.tax.title') +
            '</div>' +
            '<button class="icbtn" style="background: var(--line); color: var(--ink2)" id="tax-close">' +
            SVG_X +
            '</button></div>' +
            '<div class="tax-body">' +
            '<div class="tax-ref"><div class="ico">' +
            SVG_DOC +
            '</div>' +
            '<div class="info"><div class="a" id="tax-ref-no">—</div><div class="b" id="tax-ref-sub">—</div></div>' +
            '<div class="amt tnum" id="tax-ref-amt">฿0.00</div></div>' +
            '<div class="tax-seg" id="tax-seg">' +
            '<button class="active" data-bt="company"><span>' +
            t('posui.tax.buyer.company') +
            '</span></button>' +
            '<button data-bt="individual"><span>' +
            t('posui.tax.buyer.individual') +
            '</span></button></div>' +
            '<label id="tax-l-name">' +
            t('posui.tax.f.company') +
            '</label>' +
            '<div class="tax-fld"><input id="tax-name" placeholder="' +
            POS.esc(t('posui.tax.ph.company')) +
            '"></div>' +
            '<label>' +
            t('posui.tax.f.taxid') +
            '</label>' +
            '<div class="tax-fld" id="tax-taxid-fld">' +
            '<input class="tnum" id="tax-taxid" inputmode="numeric" placeholder="' +
            POS.esc(t('posui.tax.ph.taxid')) +
            '">' +
            '<span class="ok" id="tax-taxid-ok">' +
            SVG_OK +
            '<span>' +
            t('posui.tax.valid') +
            '</span></span>' +
            '<span class="bad" id="tax-taxid-bad">' +
            t('posui.tax.invalid') +
            '</span>' +
            '<button class="lookup" id="tax-lookup-btn" disabled>' +
            SVG_FIND +
            '<span>' +
            t('posui.tax.lookup') +
            '</span></button></div>' +
            '<div class="tax-lookup-hint" id="tax-lookup-hint"></div>' +
            '<div id="tax-company-fields"><label>' +
            t('posui.tax.branch') +
            '</label>' +
            '<div class="tax-branch">' +
            '<button class="active" data-branch="head">' +
            t('posui.tax.branch.head') +
            '</button>' +
            '<button data-branch="branch">' +
            t('posui.tax.branch.sub') +
            '</button>' +
            '<div class="tax-fld bno"><input class="tnum" id="tax-branchno" placeholder="' +
            POS.esc(t('posui.tax.ph.branchno')) +
            '"></div></div></div>' +
            '<label>' +
            t('posui.tax.address') +
            '</label>' +
            '<div class="tax-fld"><input id="tax-address" placeholder="' +
            POS.esc(t('posui.tax.ph.address')) +
            '"></div>' +
            '<label class="tax-save"><input type="checkbox" id="tax-save-buyer"><span>' +
            t('posui.tax.save_buyer') +
            '</span></label>' +
            '<div class="tax-lock">' +
            SVG_LOCK +
            '<div>' +
            t('posui.tax.lock') +
            '</div></div>' +
            '<div class="pm-err" id="tax-err"></div></div>' +
            '<div class="tax-foot">' +
            '<button class="ghost" id="tax-cancel">' +
            t('posui.tax.cancel') +
            '</button>' +
            '<button class="primary" id="tax-submit">' +
            SVG_PRINT +
            '<span>' +
            t('posui.tax.submit') +
            '</span></button></div></div>'
        );
    }

    function closeMask() {
        const m = $('tax-mask');
        if (m) m.classList.remove('show');
    }

    // 重建 + 绑事件(innerHTML 重建后旧监听全失效,必须每次重绑)。
    function buildModal() {
        let mask = $('tax-mask');
        if (!mask) {
            mask = document.createElement('div');
            mask.className = 'mask';
            mask.id = 'tax-mask';
            document.body.appendChild(mask);
        }
        mask.innerHTML = modalHtml();
        $('tax-close').addEventListener('click', closeMask);
        $('tax-cancel').addEventListener('click', closeMask);
        $('tax-submit').addEventListener('click', doIssueTax);
        document.querySelectorAll('#tax-seg button').forEach((b) =>
            b.addEventListener('click', () => {
                taxBuyerType = b.dataset.bt;
                applyTaxBuyerType();
                updateTaxSubmit();
            })
        );
        document.querySelectorAll('.tax-branch button[data-branch]').forEach((b) =>
            b.addEventListener('click', () => {
                taxBranch = b.dataset.branch;
                applyTaxBranch();
            })
        );
        $('tax-name').addEventListener('input', updateTaxSubmit);
        $('tax-taxid').addEventListener('input', validateTaxId);
        $('tax-lookup-btn').addEventListener('click', doLookup);
    }

    // ════════════════ 弹窗交互(结账完成页 / 补开视图共用)════════════════
    function openFor(sale, origin) {
        if (!sale || !sale.id) return;
        buildModal();
        taxSale = sale;
        taxOrigin = origin || 'done';
        taxBuyerType = 'company';
        taxBranch = 'head';
        $('tax-ref-no').textContent = POS.t('posui.tax.ref') + ' ' + (sale.receipt_no || '');
        const lines = sale.lines || [];
        const items = lines.reduce((s, l) => s + Number(l.qty || 0), 0);
        $('tax-ref-sub').textContent = POS.tf('posui.cart.items', { n: items, k: lines.length });
        $('tax-ref-amt').textContent = '฿' + fmt(sale.grand_total);
        applyTaxBuyerType();
        applyTaxBranch();
        validateTaxId();
        $('tax-mask').classList.add('show');
    }

    function applyTaxBuyerType() {
        document
            .querySelector('#tax-mask .tax-modal')
            .classList.toggle('buyer-individual', taxBuyerType === 'individual');
        document
            .querySelectorAll('#tax-seg button')
            .forEach((b) => b.classList.toggle('active', b.dataset.bt === taxBuyerType));
        const company = taxBuyerType === 'company';
        $('tax-l-name').textContent = POS.t(company ? 'posui.tax.f.company' : 'posui.tax.f.name');
        $('tax-name').setAttribute(
            'placeholder',
            POS.t(company ? 'posui.tax.ph.company' : 'posui.tax.ph.name')
        );
    }

    function applyTaxBranch() {
        document
            .querySelectorAll('.tax-branch button[data-branch]')
            .forEach((b) => b.classList.toggle('active', b.dataset.branch === taxBranch));
        const bno = $('tax-branchno').closest('.bno');
        if (bno) bno.style.display = taxBranch === 'branch' ? 'flex' : 'none';
    }

    // 13 位且校验位对 → 绿勾 + 可带出;13 位但校验位错 → 红提示(别等开票被 422)。
    function validateTaxId() {
        const v = ($('tax-taxid').value || '').replace(/\D/g, '');
        const ok = th13Ok(v);
        $('tax-taxid-fld').classList.toggle('ok-on', ok);
        $('tax-taxid-fld').classList.toggle('bad-on', v.length === 13 && !ok);
        $('tax-lookup-btn').disabled = !ok;
        updateTaxSubmit();
    }

    function updateTaxSubmit() {
        const name = ($('tax-name').value || '').trim();
        const tid = ($('tax-taxid').value || '').replace(/\D/g, '');
        // 公司:名 + 校验位合法的 13 位税号必填;个人:名必填,税号可选(填了必须合法)
        const tidOk = taxBuyerType === 'company' ? th13Ok(tid) : !tid || th13Ok(tid);
        $('tax-submit').disabled = !name || !tidOk;
    }

    // 税号 → RD 带出。四态:查询中(按钮忙)/查到(回填)/查不到(转手填)/网络失败(同前者)。
    async function doLookup() {
        const btn = $('tax-lookup-btn');
        const hint = $('tax-lookup-hint');
        const tid = ($('tax-taxid').value || '').replace(/\D/g, '');
        if (!th13Ok(tid) || btn.disabled) return;
        btn.disabled = true;
        btn.classList.add('busy');
        hint.textContent = POS.t('posui.tax.lookup.busy');
        try {
            const r = await POS.data.taxLookup(tid);
            if (r && r.found) {
                if (r.name) $('tax-name').value = r.name;
                if (r.address) $('tax-address').value = r.address;
                hint.textContent = '';
            } else {
                hint.textContent = POS.t('posui.tax.lookup.miss');
            }
        } catch (_) {
            hint.textContent = POS.t('posui.tax.lookup.miss');
        }
        btn.classList.remove('busy');
        btn.disabled = false;
        updateTaxSubmit();
    }

    async function doIssueTax() {
        if (!taxSale || !taxSale.id) return;
        const btn = $('tax-submit');
        const tid = ($('tax-taxid').value || '').replace(/\D/g, '');
        const buyer = {
            party_type: taxBuyerType,
            name: ($('tax-name').value || '').trim() || null,
            tax_id: tid || null,
            branch_type: taxBuyerType === 'company' ? taxBranch : null,
            branch_no:
                taxBuyerType === 'company' && taxBranch === 'branch'
                    ? ($('tax-branchno').value || '').trim() || null
                    : null,
            address: ($('tax-address').value || '').trim() || null,
        };
        const saleId = taxSale.id;
        btn.disabled = true;
        $('tax-err').textContent = '';
        try {
            await POS.data.fullTaxInvoice(saleId, buyer, $('tax-save-buyer').checked);
            closeMask();
            const dm = $('done-mask');
            if (dm) dm.classList.remove('show');
            POS.toast(POS.t('posui.tax.done'));
            openInvoicePdf(saleId);
            if (taxOrigin === 'view') openSaleById(saleId); // 回「已开过」卡,可再重打
        } catch (e) {
            // 已升级过:关弹窗 + toast(07 屏2);其余(税号无效等)弹窗内红字可改重试
            if (e.code === 'pos.already_upgraded') {
                closeMask();
                const dm = $('done-mask');
                if (dm) dm.classList.remove('show');
                POS.toast(POS.posErrMsg('pos.already_upgraded'), 'error');
            } else {
                $('tax-err').textContent = POS.posErrMsg(e.code, 'pos.tax_id_invalid');
                btn.disabled = false;
            }
        }
    }

    // A4 全式票 PDF(开出即打 / 已开过重打)。fetch 带 token 换 blob(同 pos-cashier 打印小票路)。
    async function openInvoicePdf(saleId) {
        try {
            const q = state.workspaceClientId
                ? '?workspace_client_id=' + state.workspaceClientId
                : '';
            const res = await fetch('/api/pos/sales/' + saleId + '/full-invoice-pdf' + q, {
                headers: state.token ? { Authorization: 'Bearer ' + state.token } : {},
            });
            if (!res.ok) throw new Error('pdf');
            const url = URL.createObjectURL(await res.blob());
            window.open(url, '_blank');
            setTimeout(() => URL.revokeObjectURL(url), 60000);
        } catch (_) {
            POS.toast(POS.posErrMsg('pos.unexpected'), 'error');
        }
    }

    // ════════════════ 补开视图(小票号召回 / 今日列表)════════════════
    function resetView() {
        $('taxinv-receipt').value = '';
        loadToday();
    }

    async function loadToday() {
        const body = $('taxinv-body');
        body.innerHTML = '<div class="state">' + POS.t('posui.loading') + '</div>';
        try {
            todayItems = await POS.data.salesToday();
        } catch (e) {
            body.innerHTML =
                '<div class="state">' + POS.posErrMsg(e.code, 'pos.unexpected') + '</div>';
            return;
        }
        renderToday();
    }

    function renderToday() {
        const body = $('taxinv-body');
        if (!todayItems.length) {
            body.innerHTML = '<div class="state">' + POS.t('posui.taxinv.hint') + '</div>';
            return;
        }
        const rows = todayItems
            .map(
                (it) =>
                    '<div class="titem" data-sale="' +
                    POS.esc(it.id) +
                    '"><div class="ti-main"><div class="ti-rc">' +
                    POS.esc(it.receipt_no || '') +
                    '</div><div class="ti-sub">' +
                    POS.esc(POS.hm(new Date(it.sold_at))) +
                    '</div></div><div class="ti-amt tnum">฿' +
                    fmt(it.grand_total) +
                    '</div></div>'
            )
            .join('');
        body.innerHTML =
            '<div class="tlist"><div class="tlist-h">' +
            POS.t('posui.taxinv.today') +
            '</div>' +
            rows +
            '</div>';
        body.querySelectorAll('.titem[data-sale]').forEach((el) => {
            el.onclick = () => openSaleById(el.dataset.sale);
        });
    }

    async function openSaleById(saleId) {
        const body = $('taxinv-body');
        body.innerHTML = '<div class="state">' + POS.t('posui.loading') + '</div>';
        try {
            handleDetail(await POS.data.saleDetail(saleId));
        } catch (e) {
            body.innerHTML =
                '<div class="state">' + POS.posErrMsg(e.code, 'pos.product_not_found') + '</div>';
        }
    }

    async function findByReceipt() {
        const no = ($('taxinv-receipt').value || '').trim();
        if (!no) return;
        const body = $('taxinv-body');
        body.innerHTML = '<div class="state">' + POS.t('posui.loading') + '</div>';
        try {
            handleDetail(await POS.data.findReceipt(no));
        } catch (e) {
            body.innerHTML =
                '<div class="state">' + POS.posErrMsg(e.code, 'pos.product_not_found') + '</div>';
        }
    }

    // 详情分流:已开过 → 「已开过 + 重打」卡(不进弹窗撞 409);正常完成单 → 买方弹窗;
    // 退货/作废单 → 诚实提示不可开。
    function handleDetail(det) {
        const head = det.sale || {};
        if (det.full_invoice) {
            renderIssued(det);
            return;
        }
        if (head.sale_type !== 'sale' || head.status !== 'completed') {
            $('taxinv-body').innerHTML =
                '<div class="state">' + POS.t('posui.taxinv.not_eligible') + '</div>';
            return;
        }
        renderToday(); // 弹窗背后留列表,取消后不落空屏
        openFor(
            {
                id: head.id,
                receipt_no: head.receipt_no,
                grand_total: head.grand_total,
                lines: det.lines,
            },
            'view'
        );
    }

    function renderIssued(det) {
        const head = det.sale || {};
        const inv = det.full_invoice;
        $('taxinv-body').innerHTML =
            '<div class="issued-card"><div class="ic-badge">' +
            SVG_OK +
            '</div><div class="ic-title">' +
            POS.t('posui.taxinv.issued.title') +
            '</div><div class="ic-row"><span>' +
            POS.t('posui.tax.ref') +
            '</span><span class="tnum">' +
            POS.esc(head.receipt_no || '') +
            '</span></div><div class="ic-row"><span>' +
            POS.t('posui.taxinv.issued.no') +
            '</span><span class="tnum b">' +
            POS.esc(inv.doc_number || '') +
            '</span></div><div class="ic-row"><span>' +
            POS.t('posui.taxinv.issued.date') +
            '</span><span class="tnum">' +
            POS.esc(inv.issue_date || '') +
            '</span></div><button class="ic-print" id="taxinv-reprint">' +
            POS.t('posui.taxinv.reprint') +
            '</button><button class="ic-back" id="taxinv-back">' +
            POS.t('posui.taxinv.back') +
            '</button></div>';
        $('taxinv-reprint').onclick = () => openInvoicePdf(String(head.id));
        $('taxinv-back').onclick = () => resetView();
    }

    function init() {
        $('cart-taxinv-btn').addEventListener('click', () => POS.showView('taxinv'));
        $('taxinv-find-btn').addEventListener('click', findByReceipt);
        $('taxinv-receipt').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') findByReceipt();
        });
    }

    POS.taxinv = { init, openFor, resetView };
})();
