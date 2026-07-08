/*
 * Pearnly POS · pos-cashier.js · 屏1 收银主屏 + 屏3 挂单 + 屏4 退货 + 屏5 交班
 * 视觉照搬概念稿(01/03/04/05);数据走 window.POS.data(B2 前 mock 兜底);失败统一 posErrMsg。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const $ = (id) => document.getElementById(id);
    const fmt = POS.fmt;

    let cart = []; // { id, name, sell_unit, qty, price }
    let activeCat = null;
    let tendered = 0;
    let discount = 0;
    let lastSale = null; // 刚成交的单(成功面板 + 升级税票用)
    let taxBuyerType = 'company';
    let taxBranch = 'head';
    const HELD_KEY = 'pos_held_orders';

    // ── topbar ──
    function applyCashier() {
        const c = state.cashier;
        if (!c) return;
        $('main-avatar').textContent = POS.initial(c.display_name);
        $('main-avatar').style.background = c.color || '#2563EB';
        $('main-cashier-name').textContent = c.display_name || '';
        $('main-store').textContent = state.store ? '· ' + state.store : '';
        if (state.shift) {
            $('main-shift-info').textContent =
                POS.t('posui.shift.opened') + ' ' + POS.hm(new Date(state.shift.opened_at));
        }
    }

    // ════════════════ 商品网格 ════════════════
    function renderCats() {
        const box = $('main-cats');
        const cats = POS.data.categories();
        const all =
            '<div class="cat' +
            (activeCat === null ? ' active' : '') +
            '" data-cat="">' +
            POS.t('posui.main.cat.all') +
            '</div>';
        box.innerHTML =
            all +
            cats
                .map(
                    (c) =>
                        '<div class="cat' +
                        (activeCat === c.id ? ' active' : '') +
                        '" data-cat="' +
                        c.id +
                        '">' +
                        POS.nm(c.name) +
                        '</div>'
                )
                .join('');
        box.querySelectorAll('.cat').forEach((el) => {
            el.addEventListener('click', () => {
                activeCat = el.dataset.cat ? Number(el.dataset.cat) : null;
                renderCats();
                loadGrid();
            });
        });
    }

    function gridSkeleton() {
        $('main-grid').innerHTML = Array.from({ length: 8 }, () => '<div class="skel"></div>').join(
            ''
        );
    }
    function gridState(msg, withRetry) {
        $('main-grid').innerHTML =
            '<div class="grid-state"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg><div>' +
            msg +
            '</div>' +
            (withRetry ? '<button id="grid-retry">' + POS.t('posui.retry') + '</button>' : '') +
            '</div>';
        if (withRetry) $('grid-retry').addEventListener('click', loadGrid);
    }

    async function loadGrid() {
        const q = ($('main-search').value || '').trim();
        gridSkeleton();
        let items;
        try {
            items = await POS.data.products(q, activeCat);
        } catch (e) {
            gridState(POS.posErrMsg(e.code, 'pos.unexpected'), true);
            return;
        }
        if (!items.length) {
            gridState(
                q ? POS.t('posui.main.empty.search') : POS.t('posui.main.empty.store'),
                false
            );
            return;
        }
        items.forEach((p) => (POS.nameCache[p.id] = p.name)); // 供历史小票退货回查商品名
        $('main-grid').innerHTML = items.map(renderProd).join('');
        $('main-grid')
            .querySelectorAll('img[data-pimg]')
            .forEach((im) => POS.data.loadProdImg(im, im.dataset.pimg));
        $('main-grid')
            .querySelectorAll('.prod')
            .forEach((el) => {
                el.addEventListener('click', () => {
                    if (el.classList.contains('out')) return;
                    addToCart(items.find((p) => p.id === el.dataset.pid));
                });
            });
    }

    function renderProd(p) {
        const qty = Number((p.stock && p.stock.qty_base) || 0);
        const low = qty <= 10;
        const out = qty <= 0;
        const unit = (p.units || []).find((u) => u.default_sell) ||
            (p.units || [])[0] || { price: '0' };
        const thumbInner = p.image_url
            ? '<img class="pimg" alt="" data-pimg="' +
              String(p.image_url).replace(/"/g, '&quot;').replace(/</g, '&lt;') +
              '">'
            : '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>';
        return (
            '<div class="prod' +
            (out ? ' out' : '') +
            '" data-pid="' +
            p.id +
            '"><div class="thumb">' +
            thumbInner +
            '<span class="stock' +
            (low ? ' low' : '') +
            '">' +
            qty +
            '</span></div><div class="meta"><div class="nm">' +
            POS.nm(p.name) +
            '</div><div class="pr tnum">฿' +
            fmt(unit.price) +
            '</div></div></div>'
        );
    }

    // ════════════════ 购物车 ════════════════
    function addToCart(p) {
        if (!p) return;
        const unit = (p.units || []).find((u) => u.default_sell) ||
            (p.units || [])[0] || { unit_name: '', price: '0' };
        const ex = cart.find((c) => c.id === p.id && c.sell_unit === unit.unit_name);
        if (ex) ex.qty++;
        else
            cart.push({
                id: p.id,
                name: p.name,
                sell_unit: unit.unit_name,
                qty: 1,
                price: Number(unit.price),
                vat_applicable: p.vat_applicable !== false,
            });
        renderCart();
    }
    function changeQty(i, d) {
        cart[i].qty += d;
        if (cart[i].qty <= 0) cart.splice(i, 1);
        renderCart();
    }
    function clearCart() {
        cart = [];
        discount = 0;
        closeSheet();
        renderCart();
    }

    // 移动端底部购物车 sheet(桌面 .cart-peek/.cart-scrim 为 display:none,这些类无副作用)
    function openSheet() {
        $('cart').classList.add('sheet-open');
        $('cart-scrim').classList.add('show');
    }
    function closeSheet() {
        $('cart').classList.remove('sheet-open');
        $('cart-scrim').classList.remove('show');
    }
    function toggleSheet() {
        if ($('cart').classList.contains('sheet-open')) closeSheet();
        else openSheet();
    }

    function subtotalOf(list) {
        return list.reduce((s, c) => s + c.price * c.qty, 0);
    }

    function renderCart() {
        const lines = $('cart-lines');
        const empty = $('cart-empty');
        const itemCount = cart.reduce((s, c) => s + c.qty, 0);
        if (!cart.length) {
            lines.innerHTML = '';
            empty.style.display = 'flex';
            $('cart-sub').textContent = POS.t('posui.cart.empty.sub');
        } else {
            empty.style.display = 'none';
            lines.innerHTML = cart
                .map(
                    (c, i) =>
                        '<div class="line"><div class="li-nm"><div class="n">' +
                        POS.nm(c.name) +
                        '</div><div class="u tnum">฿' +
                        fmt(c.price) +
                        ' ' +
                        POS.t('posui.cart.unit') +
                        '</div></div><div class="stepper"><button data-dec="' +
                        i +
                        '">−</button><span class="q tnum">' +
                        c.qty +
                        '</span><button data-inc="' +
                        i +
                        '">+</button></div><div class="li-amt tnum">฿' +
                        fmt(c.price * c.qty) +
                        '</div></div>'
                )
                .join('');
            lines
                .querySelectorAll('[data-dec]')
                .forEach((b) => (b.onclick = () => changeQty(Number(b.dataset.dec), -1)));
            lines
                .querySelectorAll('[data-inc]')
                .forEach((b) => (b.onclick = () => changeQty(Number(b.dataset.inc), 1)));
            $('cart-sub').textContent = POS.tf('posui.cart.items', {
                n: itemCount,
                k: cart.length,
            });
        }
        const sub = subtotalOf(cart);
        const disc = Math.min(discount, sub);
        const grand = sub - disc;
        $('cart-subtotal').textContent = fmt(sub);
        $('cart-disc-amt').textContent = fmt(disc);
        $('cart-grand').textContent = fmt(grand);
        $('cart-pay-btn').disabled = cart.length === 0;
        $('cart-peek-count').textContent = itemCount;
        $('cart-peek-grand').textContent = fmt(grand);
    }

    function setDiscount() {
        const sub = subtotalOf(cart);
        const raw = window.prompt(POS.t('posui.discount.prompt'), String(discount || ''));
        if (raw === null) return;
        const v = Number(String(raw).replace(/[^\d.]/g, '')) || 0;
        discount = Math.max(0, Math.min(v, sub));
        renderCart();
    }

    // ════════════════ 收款弹窗 ════════════════
    // 收款设置访问器/显隐/拉取统一在 POS.pay(与餐厅埋单共用)。

    function grandTotal() {
        const sub = subtotalOf(cart);
        return sub - Math.min(discount, sub);
    }
    function openPay() {
        if (!cart.length) return;
        closeSheet();
        const due = grandTotal();
        $('pay-due').textContent = fmt(due);
        $('pay-qr-amt').textContent = fmt(due);
        tendered = 0;
        renderQuickCash();
        updateCash();
        POS.pay.applyMethods('#pay-mask .pm'); // 按收款设置显隐 PromptPay/刷卡
        setPm('cash');
        ['pay-cash-err', 'pay-qr-err', 'pay-card-err', 'pay-transfer-err'].forEach(
            (id) => ($(id).textContent = '')
        );
        $('pay-mask').classList.add('show');
    }
    function closePay() {
        $('pay-mask').classList.remove('show');
    }
    function setPm(m) {
        document
            .querySelectorAll('#pay-mask .pm')
            .forEach((e) => e.classList.toggle('active', e.dataset.pm === m));
        $('pm-cash').style.display = m === 'cash' ? 'block' : 'none';
        $('pm-qr').style.display = m === 'qr' ? 'block' : 'none';
        $('pm-card').style.display = m === 'card' ? 'block' : 'none';
        $('pm-transfer').style.display = m === 'transfer' ? 'block' : 'none';
        if (m === 'qr') loadQr();
        if (m === 'transfer') loadBankInfo();
    }
    // 切到银行转账 → 显示老板配的银行名/账号/户名;没配就提示去收款设置填(参照 loadQr 的 no_id 提示)。
    function loadBankInfo() {
        const s = POS.pay.settings();
        const has = !!(s.bank_name || s.bank_account_no);
        $('pay-bank-card').style.display = has ? 'block' : 'none';
        $('pay-bank-name').textContent = s.bank_name || '';
        $('pay-bank-no').textContent = s.bank_account_no || '';
        $('pay-bank-acc-name').textContent = s.bank_account_name || '';
        $('pay-transfer-err').textContent = has ? '' : POS.t('posui.pay.transfer.no_bank');
    }
    // 切到 PromptPay → 用账套配的 ID + 待收金额出码;未配 ID 提示去收款设置填。
    async function loadQr() {
        const box = $('pay-qr-box');
        if (!box) return;
        box.innerHTML = '<div class="qr-loading">' + POS.t('posui.loading') + '</div>';
        $('pay-qr-err').textContent = '';
        try {
            const r = await POS.data.promptpayQr(grandTotal());
            box.innerHTML =
                '<img alt="PromptPay QR" style="width:200px;height:200px;" src="data:image/png;base64,' +
                r.png_base64 +
                '">';
        } catch (e) {
            box.innerHTML = '';
            // 未配 PromptPay ID(后端 422 detail no_promptpay_id)→ 引导去「收款设置」填。
            $('pay-qr-err').textContent =
                e && e.detail === 'no_promptpay_id'
                    ? POS.t('posui.pay.qr.no_id')
                    : POS.posErrMsg(e && e.code, 'posui.pay.qr.fail');
        }
    }
    function renderQuickCash() {
        const box = $('pay-quick');
        box.innerHTML = [50, 100, 500, 1000]
            .map((v) => '<button data-cash="' + v + '">฿' + v + '</button>')
            .join('');
        box.querySelectorAll('button').forEach(
            (b) =>
                (b.onclick = () => {
                    tendered = Number(b.dataset.cash);
                    updateCash();
                })
        );
    }
    function keyPress(k) {
        let s = String(tendered);
        if (k === 'back') s = s.slice(0, -1) || '0';
        else s = (s === '0' ? '' : s) + k;
        tendered = parseInt(s || '0', 10);
        updateCash();
    }
    function updateCash() {
        const due = grandTotal();
        $('pay-tendered').textContent = tendered.toLocaleString('en-US');
        const ch = tendered - due;
        $('pay-change').textContent = fmt(ch > 0 ? ch : 0);
        $('pay-cash-err').textContent = '';
    }

    function buildSalePayload(method) {
        const due = grandTotal();
        const sub = subtotalOf(cart);
        const paid = method === 'cash' ? Math.max(tendered, due) : due;
        return {
            client_uuid: POS.uuid(),
            workspace_client_id: state.workspaceClientId,
            shift_id: state.shift ? state.shift.id : null,
            terminal_id: state.terminalId,
            doc_kind: 'receipt',
            sale_type: 'sale',
            member_client_id: null,
            price_includes_vat: POS.pay.inclVat(),
            lines: cart.map((c) => ({
                product_id: c.id,
                sell_unit: c.sell_unit,
                qty: String(c.qty),
                unit_price: c.price.toFixed(2),
                line_discount: '0',
                batch_id: null,
                vat_applicable: c.vat_applicable !== false, // 离线本地算价用(服务端忽略,以商品为准)
            })),
            header_discount:
                discount > 0
                    ? { type: 'amount', value: Math.min(discount, sub).toFixed(2) }
                    : { type: 'none', value: '0' },
            payments: [{ method, amount: paid.toFixed(2) }],
            sold_at: new Date().toISOString(),
        };
    }

    async function confirmPay(method, errId, btn) {
        if (method === 'cash' && tendered < grandTotal()) {
            $(errId).textContent = POS.t('posui.pay.short');
            return;
        }
        btn.disabled = true;
        const snapshot = {
            lines: cart.map((c) => ({
                name: c.name,
                qty: c.qty,
                price: c.price,
                sell_unit: c.sell_unit,
            })),
            method,
            grand: grandTotal(),
            tendered: method === 'cash' ? tendered : grandTotal(),
        };
        try {
            const res = await POS.data.createSale(buildSalePayload(method));
            closePay();
            POS.toast(POS.t('posui.toast.paid'));
            clearCart();
            showDone(res, snapshot);
        } catch (e) {
            // 07 屏1:收款失败弹窗内红字,不关弹窗,可改可重试
            $(errId).textContent = POS.posErrMsg(e.code, 'pos.unexpected');
        } finally {
            btn.disabled = false;
        }
    }

    // ════════════════ 成交成功面板 + 屏2 升级税票 ════════════════
    function showDone(res, snap) {
        const sale = (res && res.sale) || {};
        lastSale = {
            id: sale.id || null,
            receipt_no: sale.receipt_no || '',
            grand_total: sale.grand_total != null ? sale.grand_total : snap.grand.toFixed(2),
            change_amount: sale.change_amount,
            offline: !!(res && res.offline), // 离线补单(Part B5)→ 不可即时开税票
            lines: snap.lines,
            method: snap.method,
            sold_at: new Date(),
        };
        const cash = snap.method === 'cash';
        const change =
            lastSale.change_amount != null
                ? lastSale.change_amount
                : cash
                  ? Math.max(0, snap.tendered - snap.grand).toFixed(2)
                  : '0.00';
        $('done-change-row').style.display = cash ? 'flex' : 'none';
        $('done-change').textContent = fmt(change);
        $('done-receipt').textContent = lastSale.receipt_no || '—';
        // 离线单 / 纯本地预览均不可开正式税票(税票需联网连号)→ 隐税票钮 + 显提示
        const taxable = !lastSale.offline && !!lastSale.id;
        document.querySelector('#done-mask .done-modal').classList.toggle('is-offline', !taxable);
        $('done-mask').classList.add('show');
    }

    function openReceipt() {
        if (!lastSale) return;
        if (!lastSale.offline && lastSale.id && !POS.allowMock()) {
            printServerReceipt(lastSale.id);
        } else {
            printLocalReceipt(lastSale);
        }
    }

    // 在线真单:取后端热敏 PDF(带 Bearer)新窗打印;取不到回落本地小票
    async function printServerReceipt(saleId) {
        try {
            const res = await fetch('/api/pos/sales/' + saleId + '/receipt-pdf', {
                headers: state.token ? { Authorization: 'Bearer ' + state.token } : {},
            });
            if (!res.ok) throw new Error('pdf');
            const url = URL.createObjectURL(await res.blob());
            window.open(url, '_blank');
            setTimeout(() => URL.revokeObjectURL(url), 60000);
        } catch (_) {
            printLocalReceipt(lastSale);
        }
    }

    // 本地热敏小票(离线 / 取不到服务端 PDF 时)· 弹窗即打印
    function printLocalReceipt(sale) {
        const rows = (sale.lines || [])
            .map(
                (l) =>
                    '<tr><td>' +
                    POS.nm(l.name) +
                    ' ×' +
                    l.qty +
                    '</td><td class="r">฿' +
                    fmt(l.price * l.qty) +
                    '</td></tr>'
            )
            .join('');
        const addrLine = state.storeAddress
            ? '<div class="meta">' + POS.esc(state.storeAddress) + '</div>'
            : '';
        const methodLine = sale.method
            ? '<tr class="tot"><td>' +
              POS.t('posui.pay.method') +
              '</td><td class="r">' +
              POS.t('posui.pay.' + sale.method) +
              '</td></tr>'
            : '';
        const html =
            '<!doctype html><html><head><meta charset="utf-8"><title>' +
            (sale.receipt_no || '') +
            '</title><style>body{font:12px monospace;width:280px;margin:0 auto;padding:12px;color:#111}' +
            'h3{text-align:center;margin:0 0 8px}table{width:100%;border-collapse:collapse}' +
            'td{padding:2px 0}.r{text-align:right}.tot td{border-top:1px dashed #000;padding-top:6px;font-weight:700}' +
            '.meta{color:#555;margin-bottom:8px}</style></head><body><h3>' +
            (state.store || 'Pearnly POS') +
            '</h3>' +
            addrLine +
            '<div class="meta">' +
            (sale.receipt_no || '') +
            ' · ' +
            POS.hm(sale.sold_at || new Date()) +
            '</div><table>' +
            rows +
            '<tr class="tot"><td>' +
            POS.t('posui.done.total') +
            '</td><td class="r">฿' +
            fmt(sale.grand_total) +
            '</td></tr>' +
            methodLine +
            '</table>' +
            '<scr' +
            'ipt>window.onload=function(){window.print()}</scr' +
            'ipt></body></html>';
        const w = window.open('', '_blank', 'width=320,height=620');
        if (!w) {
            POS.toast(POS.t('posui.done.print'));
            return;
        }
        w.document.write(html);
        w.document.close();
    }

    function openTaxModal() {
        if (!lastSale || lastSale.offline || !lastSale.id) return;
        taxBuyerType = 'company';
        taxBranch = 'head';
        $('tax-ref-no').textContent = POS.t('posui.tax.ref') + ' ' + (lastSale.receipt_no || '');
        const items = (lastSale.lines || []).reduce((s, l) => s + l.qty, 0);
        $('tax-ref-sub').textContent = POS.tf('posui.cart.items', {
            n: items,
            k: (lastSale.lines || []).length,
        });
        $('tax-ref-amt').textContent = '฿' + fmt(lastSale.grand_total);
        ['tax-name', 'tax-taxid', 'tax-branchno', 'tax-address'].forEach((id) => {
            const e = $(id);
            if (e) e.value = '';
        });
        $('tax-err').textContent = '';
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

    function validateTaxId() {
        const v = ($('tax-taxid').value || '').replace(/\D/g, '');
        $('tax-taxid-fld').classList.toggle('ok-on', v.length === 13);
        updateTaxSubmit();
    }

    function updateTaxSubmit() {
        const name = ($('tax-name').value || '').trim();
        const tid = ($('tax-taxid').value || '').replace(/\D/g, '');
        // 公司:名 + 13 位税号必填;个人:仅名必填(税号可选)
        const ok = taxBuyerType === 'company' ? !!name && tid.length === 13 : !!name;
        $('tax-submit').disabled = !ok;
    }

    async function doIssueTax() {
        if (!lastSale || !lastSale.id) return;
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
        btn.disabled = true;
        $('tax-err').textContent = '';
        try {
            await POS.data.fullTaxInvoice(lastSale.id, buyer);
            $('tax-mask').classList.remove('show');
            $('done-mask').classList.remove('show');
            POS.toast(POS.t('posui.tax.done'));
        } catch (e) {
            // 已升级过:关弹窗 + toast(07 屏2);其余(税号无效等)弹窗内红字可改重试
            if (e.code === 'pos.already_upgraded') {
                $('tax-mask').classList.remove('show');
                $('done-mask').classList.remove('show');
                POS.toast(POS.posErrMsg('pos.already_upgraded'), 'error');
            } else {
                $('tax-err').textContent = POS.posErrMsg(e.code, 'pos.tax_id_invalid');
                btn.disabled = false;
            }
        }
    }

    // ════════════════ 屏 3 · 挂单 / 取单 ════════════════
    function loadHeld() {
        try {
            return JSON.parse(localStorage.getItem(HELD_KEY) || '[]');
        } catch (_) {
            return [];
        }
    }
    function saveHeld(list) {
        try {
            localStorage.setItem(HELD_KEY, JSON.stringify(list));
        } catch (_) {}
    }
    function holdCurrent() {
        if (!cart.length) return;
        const list = loadHeld();
        list.push({
            id: POS.uuid(),
            no: 'H-' + String(list.length + 1).padStart(2, '0'),
            time: POS.hm(new Date()),
            cart: cart.slice(),
            discount,
        });
        saveHeld(list);
        clearCart();
        POS.toast(POS.t('posui.toast.held'));
    }
    function renderHold() {
        const list = loadHeld();
        $('hold-count').textContent = POS.tf('posui.hold.count', { n: list.length });
        const grid = $('hold-grid');
        const empty = $('hold-empty');
        if (!list.length) {
            grid.innerHTML = '';
            empty.style.display = 'block';
            return;
        }
        empty.style.display = 'none';
        grid.innerHTML = list
            .map((h) => {
                const items = h.cart.reduce((s, c) => s + c.qty, 0);
                const sub = subtotalOf(h.cart);
                const total = sub - Math.min(h.discount || 0, sub);
                const names = h.cart.map((c) => POS.nm(c.name) + ' ×' + c.qty).join(' · ');
                return (
                    '<div class="held"><div class="h"><span class="no">' +
                    h.no +
                    '</span><span class="tm">' +
                    h.time +
                    '</span></div><div class="items">' +
                    names +
                    '</div><div class="ft"><span class="sum">' +
                    POS.tf('posui.cart.items', { n: items, k: h.cart.length }) +
                    '</span><span class="amt tnum">฿' +
                    fmt(total) +
                    '</span></div><div class="ft2"><button class="resume" data-resume="' +
                    h.id +
                    '"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>' +
                    POS.t('posui.hold.resume') +
                    '</button><button class="del" data-del="' +
                    h.id +
                    '"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg></button></div></div>'
                );
            })
            .join('');
        grid.querySelectorAll('[data-resume]').forEach(
            (b) => (b.onclick = () => resumeHeld(b.dataset.resume))
        );
        grid.querySelectorAll('[data-del]').forEach(
            (b) => (b.onclick = () => deleteHeld(b.dataset.del))
        );
    }
    function resumeHeld(id) {
        const list = loadHeld();
        const h = list.find((x) => x.id === id);
        if (!h) return;
        cart = h.cart.slice();
        discount = h.discount || 0;
        saveHeld(list.filter((x) => x.id !== id));
        renderCart();
        POS.showView('main');
        POS.toast(POS.t('posui.toast.resumed'));
    }
    function deleteHeld(id) {
        saveHeld(loadHeld().filter((x) => x.id !== id));
        renderHold();
        POS.toast(POS.t('posui.hold.deleted'));
    }

    // ════════════════ 绑定 + 对外 ════════════════
    function init() {
        let searchTimer = null;
        $('main-search').addEventListener('input', () => {
            if (searchTimer) clearTimeout(searchTimer);
            searchTimer = setTimeout(loadGrid, 220);
        });
        $('main-scan-btn').addEventListener('click', () => {
            const code = window.prompt(POS.t('posui.scan.prompt'));
            if (code) {
                $('main-search').value = code;
                loadGrid();
            }
        });
        $('cart-peek').addEventListener('click', toggleSheet);
        $('cart-scrim').addEventListener('click', closeSheet);
        $('cart-hold-btn').addEventListener('click', holdCurrent);
        $('cart-clear-btn').addEventListener('click', clearCart);
        $('cart-resume-btn').addEventListener('click', () => POS.showView('hold'));
        $('cart-refund-btn').addEventListener('click', () => POS.showView('refund'));
        $('cart-disc-btn').addEventListener('click', setDiscount);
        $('cart-pay-btn').addEventListener('click', openPay);
        $('main-menu-btn').addEventListener('click', () => POS.showView('shift'));
        $('net-pill').addEventListener('click', () => {
            POS.setNet(!state.online);
            POS.toast(
                state.online ? POS.t('posui.net.toast.online') : POS.t('posui.net.toast.offline')
            );
            if (state.online && POS.offline) POS.offline.sync();
        });
        $('pay-close-btn').addEventListener('click', closePay);
        document
            .querySelectorAll('#pay-mask .pm')
            .forEach((el) => el.addEventListener('click', () => setPm(el.dataset.pm)));
        $('pay-keypad')
            .querySelectorAll('.key')
            .forEach((b) => b.addEventListener('click', () => keyPress(b.dataset.key)));
        $('pay-cash-confirm').addEventListener('click', (e) =>
            confirmPay('cash', 'pay-cash-err', e.currentTarget)
        );
        $('pay-qr-confirm').addEventListener('click', (e) =>
            confirmPay('qr', 'pay-qr-err', e.currentTarget)
        );
        $('pay-card-confirm').addEventListener('click', (e) =>
            confirmPay('card', 'pay-card-err', e.currentTarget)
        );
        $('pay-transfer-confirm').addEventListener('click', (e) =>
            confirmPay('transfer', 'pay-transfer-err', e.currentTarget)
        );
        // 成交成功面板
        $('done-print').addEventListener('click', openReceipt);
        $('done-tax').addEventListener('click', () => {
            $('done-mask').classList.remove('show');
            openTaxModal();
        });
        $('done-next').addEventListener('click', () => $('done-mask').classList.remove('show'));
        // 屏2 升级税票
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
    }

    function enterMain() {
        applyCashier();
        renderCats();
        renderCart();
        loadGrid();
        POS.pay.ensure(); // 拉收款设置(显隐方式 / 价内VAT / PromptPay 出码)
    }

    POS.cashier = {
        init,
        enterMain,
        applyCashier,
        renderHold,
    };
})();
