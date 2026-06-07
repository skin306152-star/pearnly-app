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
        return (
            '<div class="prod' +
            (out ? ' out' : '') +
            '" data-pid="' +
            p.id +
            '"><div class="thumb"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg><span class="stock' +
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
        renderCart();
    }

    function subtotalOf(list) {
        return list.reduce((s, c) => s + c.price * c.qty, 0);
    }

    function renderCart() {
        const lines = $('cart-lines');
        const empty = $('cart-empty');
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
            const items = cart.reduce((s, c) => s + c.qty, 0);
            $('cart-sub').textContent = POS.tf('posui.cart.items', { n: items, k: cart.length });
        }
        const sub = subtotalOf(cart);
        const disc = Math.min(discount, sub);
        $('cart-subtotal').textContent = fmt(sub);
        $('cart-disc-amt').textContent = fmt(disc);
        $('cart-grand').textContent = fmt(sub - disc);
        $('cart-pay-btn').disabled = cart.length === 0;
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
    function grandTotal() {
        const sub = subtotalOf(cart);
        return sub - Math.min(discount, sub);
    }
    function openPay() {
        if (!cart.length) return;
        const due = grandTotal();
        $('pay-due').textContent = fmt(due);
        $('pay-qr-amt').textContent = fmt(due);
        tendered = 0;
        renderQuickCash();
        updateCash();
        setPm('cash');
        ['pay-cash-err', 'pay-qr-err', 'pay-card-err'].forEach((id) => ($(id).textContent = ''));
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
            price_includes_vat: true,
            lines: cart.map((c) => ({
                product_id: c.id,
                sell_unit: c.sell_unit,
                qty: String(c.qty),
                unit_price: c.price.toFixed(2),
                line_discount: '0',
                batch_id: null,
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
        try {
            await POS.data.createSale(buildSalePayload(method));
            closePay();
            POS.toast(POS.t('posui.toast.paid'));
            clearCart();
        } catch (e) {
            // 07 屏1:收款失败弹窗内红字,不关弹窗,可改可重试
            $(errId).textContent = POS.posErrMsg(e.code, 'pos.unexpected');
        } finally {
            btn.disabled = false;
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
    }

    function enterMain() {
        applyCashier();
        renderCats();
        renderCart();
        loadGrid();
    }

    POS.cashier = {
        init,
        enterMain,
        applyCashier,
        renderHold,
    };
})();
