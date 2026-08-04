/*
 * Pearnly POS · pos-taxinv.js · 全式税票(G2 凭小票号补开通路 + 结账完成页共用弹窗)
 *
 * #tax-mask 弹窗从 pos-cashier 迁出成单一驱动点:结账完成页(lastSale)与补开视图
 * (今日列表 / 小票号召回)都经 POS.taxinv.openFor(sale, origin) 进来。新增:税号 RD
 * 带出(/api/pos/tax-lookup · 查不到诚实转手填)、Mod-11 前端镜像(与后端
 * services/sales/buyer.th13_checksum_ok 同式)、买方档存回勾选、开出后自动开 A4 PDF。
 * 已升级单在视图层直接给「已开过 + 重打」卡,不进弹窗撞 409。对外 window.POS.taxinv。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const $ = (id) => document.getElementById(id);
    const fmt = POS.fmt;

    let taxSale = null; // 弹窗目标单 {id, receipt_no, grand_total, lines?}
    let taxOrigin = 'done'; // 'done'=结账完成页 · 'view'=补开视图(成功后回列表)
    let taxBuyerType = 'company';
    let taxBranch = 'head';
    let todayItems = [];

    // 泰国 13 位税号 Mod-11 校验位(后端同式;真号必过,打错一位即不过)。
    function th13Ok(v) {
        if (!/^\d{13}$/.test(v)) return false;
        let sum = 0;
        for (let i = 0; i < 12; i++) sum += Number(v[i]) * (13 - i);
        return Number(v[12]) === (11 - (sum % 11)) % 10;
    }

    // ════════════════ 弹窗(结账完成页 / 补开视图共用)════════════════
    function openFor(sale, origin) {
        if (!sale || !sale.id) return;
        taxSale = sale;
        taxOrigin = origin || 'done';
        taxBuyerType = 'company';
        taxBranch = 'head';
        $('tax-ref-no').textContent = POS.t('posui.tax.ref') + ' ' + (sale.receipt_no || '');
        const lines = sale.lines || [];
        const items = lines.reduce((s, l) => s + Number(l.qty || 0), 0);
        $('tax-ref-sub').textContent = POS.tf('posui.cart.items', { n: items, k: lines.length });
        $('tax-ref-amt').textContent = '฿' + fmt(sale.grand_total);
        ['tax-name', 'tax-taxid', 'tax-branchno', 'tax-address'].forEach((id) => {
            const e = $(id);
            if (e) e.value = '';
        });
        $('tax-save-buyer').checked = false;
        $('tax-err').textContent = '';
        $('tax-lookup-hint').textContent = '';
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
        const lbl = $('tax-l-name');
        const lblKey = taxBuyerType === 'company' ? 'posui.tax.f.company' : 'posui.tax.f.name';
        lbl.setAttribute('data-i18n', lblKey);
        lbl.textContent = POS.t(lblKey);
        const nameInput = $('tax-name');
        const phKey = taxBuyerType === 'company' ? 'posui.tax.ph.company' : 'posui.tax.ph.name';
        nameInput.setAttribute('data-i18n-placeholder', phKey);
        nameInput.setAttribute('placeholder', POS.t(phKey));
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

    // 税号 → RD 官方名称/地址带出。四态:查询中(按钮转忙)/查到(回填)/查不到(转手填)/网络失败(同前者)。
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
            $('tax-mask').classList.remove('show');
            const dm = $('done-mask');
            if (dm) dm.classList.remove('show');
            POS.toast(POS.t('posui.tax.done'));
            openInvoicePdf(saleId);
            if (taxOrigin === 'view') openSaleById(saleId); // 回「已开过」卡,可再重打
        } catch (e) {
            // 已升级过:关弹窗 + toast(07 屏2);其余(税号无效等)弹窗内红字可改重试
            if (e.code === 'pos.already_upgraded') {
                $('tax-mask').classList.remove('show');
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
            '<div class="issued-card"><div class="ic-badge"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg></div><div class="ic-title">' +
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
        // 弹窗(原 pos-cashier 屏2 绑定迁入)
        $('tax-close').addEventListener('click', () => $('tax-mask').classList.remove('show'));
        $('tax-cancel').addEventListener('click', () => $('tax-mask').classList.remove('show'));
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
        // 补开视图
        $('cart-taxinv-btn').addEventListener('click', () => POS.showView('taxinv'));
        $('taxinv-find-btn').addEventListener('click', findByReceipt);
        $('taxinv-receipt').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') findByReceipt();
        });
    }

    POS.taxinv = { init, openFor, resetView };
})();
