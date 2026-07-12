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
    let taken = []; // 本单已收明细(混合支付):{ method, amount:Number, ref? }·每次开收款窗重置
    let discount = 0; // 折后金额(购物车渲染用·金额/百分比两种模式都归一到此)
    let discountMode = 'none'; // 'none' | 'amount' | 'pct' · 建单走哪个 header_discount 分支
    let discountPctValue = 0; // discountMode='pct' 时的原始百分比,建单传给后端按下单时小计复算
    let discountReason = ''; // 折扣理由 · 随 payload 携带(后端暂无落点,extra 字段忽略即可)
    let lastSale = null; // 刚成交的单(成功面板 + 升级税票用)
    window.addEventListener('pos:sale-synced', (event) => {
        const synced = event.detail || {};
        if (!lastSale || lastSale.client_uuid !== synced.client_uuid) return;
        lastSale.id = synced.sale_id;
        lastSale.receipt_no = synced.receipt_no;
        lastSale.offline = false;
        lastSale.temporary_receipt = false;
        if ($('done-receipt')) $('done-receipt').textContent = synced.receipt_no || '—';
    });
    let taxBuyerType = 'company';
    let taxBranch = 'head';
    const HELD_KEY = 'pos_held_orders';

    // ── topbar ──
    function applyCashier() {
        const c = state.cashier;
        if (!c) return;
        $('main-avatar').textContent = POS.initial(c.display_name);
        $('main-avatar').style.background = POS.safeColor(c.color);
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
                        POS.esc(c.id) +
                        '">' +
                        POS.esc(POS.nm(c.name)) +
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
            POS.esc(p.id) +
            '"><div class="thumb">' +
            thumbInner +
            '<span class="stock' +
            (low ? ' low' : '') +
            '">' +
            qty +
            '</span></div><div class="meta"><div class="nm">' +
            POS.esc(POS.nm(p.name)) +
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
    // 点数量 → 键盘弹窗输入(便利店大批量免狂点 +)。用点击而非原生 input 焦点:触屏友好,
    // 且不受浏览器扩展/焦点抢占干扰(实测 inline input 在真机被环境吞键)。qtyBuf='' = 未输入
    // (显示原数量);首键从头输;确定时 >0 覆盖 · =0/清空则删行。物理键盘作桌面加成(见 init)。
    let qtyIdx = -1;
    let qtyBuf = '';
    function openQtyPad(i) {
        qtyIdx = i;
        qtyBuf = '';
        $('qty-item-name').textContent = POS.nm(cart[i].name);
        updateQtyDisp();
        $('qty-mask').classList.add('show');
    }
    function closeQtyPad() {
        $('qty-mask').classList.remove('show');
        qtyIdx = -1;
    }
    function updateQtyDisp() {
        if (qtyIdx < 0) return;
        $('qty-disp').textContent = qtyBuf === '' ? String(cart[qtyIdx].qty) : qtyBuf;
    }
    function qtyKey(k) {
        if (qtyIdx < 0) return;
        if (k === 'clear') qtyBuf = '0';
        else if (k === 'back') qtyBuf = (qtyBuf || String(cart[qtyIdx].qty)).slice(0, -1);
        else qtyBuf = (qtyBuf === '0' ? '' : qtyBuf) + k;
        if (qtyBuf.length > 4) qtyBuf = qtyBuf.slice(0, 4); // 防离谱数量撑破布局
        updateQtyDisp();
    }
    function confirmQtyPad() {
        if (qtyIdx < 0) return;
        const v = qtyBuf === '' ? cart[qtyIdx].qty : parseInt(qtyBuf, 10);
        if (!Number.isFinite(v) || v <= 0) cart.splice(qtyIdx, 1);
        else cart[qtyIdx].qty = v;
        closeQtyPad();
        renderCart();
    }

    // 折扣/扫码共用键盘弹窗:同一个 #pad-mask DOM(第 2/3 例复用 qty pad 骨架),
    // 按 opts 显隐 %/฿ 切换与理由框。buf 存原始字符串(扫码码可能带前导 0,不当数字解析)。
    let padCtx = null;
    function openPad(opts) {
        padCtx = {
            kind: opts.kind,
            mode: opts.mode || 'amount',
            buf: '',
            prefill: opts.prefill || '',
            maxLen: opts.maxLen || 7,
        };
        $('pad-title').textContent = opts.title;
        $('pad-label').textContent = opts.label || '';
        $('pad-seg').style.display = opts.showToggle ? 'flex' : 'none';
        $('pad-reason-row').style.display = opts.showReason ? 'flex' : 'none';
        if (opts.showReason) $('pad-reason').value = opts.reasonValue || '';
        if (opts.showToggle) {
            document
                .querySelectorAll('#pad-seg button')
                .forEach((b) => b.classList.toggle('active', b.dataset.mode === padCtx.mode));
        }
        updatePadDisp();
        $('pad-mask').classList.add('show');
    }
    function closePad() {
        $('pad-mask').classList.remove('show');
        padCtx = null;
    }
    function setPadMode(mode) {
        if (!padCtx) return;
        padCtx.mode = mode;
        padCtx.buf = '';
        padCtx.prefill = '';
        document
            .querySelectorAll('#pad-seg button')
            .forEach((b) => b.classList.toggle('active', b.dataset.mode === mode));
        updatePadDisp();
    }
    function updatePadDisp() {
        if (!padCtx) return;
        $('pad-disp').textContent =
            padCtx.buf || padCtx.prefill || (padCtx.kind === 'scan' ? '' : '0');
    }
    function padKey(k) {
        if (!padCtx) return;
        if (k === 'clear') padCtx.buf = '';
        else if (k === 'back') padCtx.buf = padCtx.buf.slice(0, -1);
        else if (padCtx.buf.length < padCtx.maxLen) padCtx.buf += k;
        updatePadDisp();
    }
    // 折扣:百分比模式只存原始百分比(单一事实源),不折成固定金额——预览按当前小计实时复算
    // (见 discountFor),购物车加减商品后总计才不漂移、与后端 pct 复算口径一致。金额模式存绝对额。
    // 扫码:命中即回填搜索框触发同款商品查找,空码不动作。
    function confirmPad() {
        if (!padCtx) return;
        if (padCtx.kind === 'discount') {
            const sub = subtotalOf(cart);
            const raw = padCtx.buf === '' ? Number(padCtx.prefill) || 0 : parseInt(padCtx.buf, 10);
            if (padCtx.mode === 'pct') {
                discountPctValue = Math.max(0, Math.min(raw, 100));
                discount = 0;
                discountMode = discountPctValue > 0 ? 'pct' : 'none';
            } else {
                discount = Math.max(0, Math.min(raw, sub));
                discountPctValue = 0;
                discountMode = discount > 0 ? 'amount' : 'none';
            }
            discountReason = ($('pad-reason').value || '').trim();
            renderCart();
        } else if (padCtx.kind === 'scan') {
            const code = padCtx.buf;
            if (code) {
                $('main-search').value = code;
                loadGrid();
            }
        }
        closePad();
    }

    function clearCart() {
        cart = [];
        discount = 0;
        discountMode = 'none';
        discountPctValue = 0;
        discountReason = '';
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

    // 当前生效折扣额:pct 模式按当前小计实时复算(quantize 到分,对齐后端 Decimal 口径),
    // amount 模式取绝对额;两者都夹在 [0, 小计]。购物车渲染/应收/建单全走这一条,避免预览漂移。
    function discountFor(sub) {
        if (discountMode === 'pct') {
            return Math.max(0, Math.min(Math.round(sub * discountPctValue) / 100, sub));
        }
        return Math.max(0, Math.min(discount, sub));
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
                        POS.esc(POS.nm(c.name)) +
                        '</div><div class="u tnum">฿' +
                        fmt(c.price) +
                        ' ' +
                        POS.t('posui.cart.unit') +
                        '</div></div><div class="stepper"><button data-dec="' +
                        i +
                        '">−</button><span class="q tnum" data-qi="' +
                        i +
                        '" role="button" tabindex="0">' +
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
            lines
                .querySelectorAll('.q[data-qi]')
                .forEach((el) => (el.onclick = () => openQtyPad(Number(el.dataset.qi))));
            $('cart-sub').textContent = POS.tf('posui.cart.items', {
                n: itemCount,
                k: cart.length,
            });
        }
        const sub = subtotalOf(cart);
        const disc = discountFor(sub);
        const grand = sub - disc;
        $('cart-subtotal').textContent = fmt(sub);
        $('cart-disc-amt').textContent = fmt(disc);
        $('cart-grand').textContent = fmt(grand);
        $('cart-pay-btn').disabled = cart.length === 0;
        $('cart-peek-count').textContent = itemCount;
        $('cart-peek-grand').textContent = fmt(grand);
    }

    function openDiscountPad() {
        openPad({
            kind: 'discount',
            title: POS.t('posui.discount.title'),
            label: POS.t('posui.cart.subtotal') + ' ฿' + fmt(subtotalOf(cart)),
            showToggle: true,
            mode: discountMode === 'pct' ? 'pct' : 'amount',
            prefill:
                discountMode === 'pct'
                    ? String(discountPctValue || '')
                    : discount
                      ? String(discount)
                      : '',
            showReason: true,
            reasonValue: discountReason,
        });
    }
    function openScanPad() {
        openPad({ kind: 'scan', title: POS.t('posui.scan.title'), maxLen: 24 });
    }

    // ════════════════ 收款弹窗 ════════════════
    // 收款设置访问器/显隐/拉取统一在 POS.pay(与餐厅埋单共用)。

    function grandTotal() {
        const sub = subtotalOf(cart);
        return sub - discountFor(sub);
    }

    // ── 混合支付 running-tender ──
    // 每方式确认按钮映射,+ 该方式默认「已付满」文案(用于按钮在成交/记一笔间活变时还原)。
    const PM_CONFIRM_BTN = {
        cash: 'pay-cash-confirm',
        qr: 'pay-qr-confirm',
        card: 'pay-card-confirm',
        transfer: 'pay-transfer-confirm',
    };
    const PM_CONFIRM_KEY = {
        cash: 'posui.pay.confirm.cash',
        qr: 'posui.pay.confirm.qr',
        card: 'posui.pay.confirm.card',
        transfer: 'posui.pay.confirm.transfer',
    };
    const EPS = 0.005; // 金额到分,半分容差:防浮点让「刚好付满」误判成还差一点

    function takenSum() {
        return taken.reduce((s, p) => s + p.amount, 0);
    }
    // 尚差 = 应收 − 已收累加。四舍五入到分,防 0.1+0.2 类浮点尾巴。
    function remaining() {
        return Math.round((grandTotal() - takenSum()) * 100) / 100;
    }
    function pmAmtInput(method) {
        if (method === 'qr') return $('pay-qr-amt-in');
        if (method === 'card') return $('pay-card-amt');
        if (method === 'transfer') return $('pay-transfer-amt');
        return null;
    }
    // 本笔待收金额:现金取 tendered(实收现钞),非现金取该方式输入框(空=0)。
    function tenderAmount(method) {
        if (method === 'cash') return tendered;
        const el = pmAmtInput(method);
        const v = parseFloat((el && el.value ? el.value : '').replace(/[^\d.]/g, ''));
        return Number.isFinite(v) ? v : 0;
    }
    function pmLabel(method) {
        return POS.t('posui.pay.' + (method === 'qr' ? 'promptpay' : method));
    }

    // 收下一笔前重置本方式输入 → 默认填新尚差(非现金)/清空现钞(现金)。
    function resetTenderInputs(method) {
        if (method === 'cash') {
            tendered = 0;
            updateCash();
            return;
        }
        const el = pmAmtInput(method);
        if (el) el.value = remaining().toFixed(2);
        if (method === 'card') $('pay-card-ref').value = '';
        if (method === 'qr') loadQr();
    }

    function renderTaken() {
        const box = $('pay-taken');
        const remRow = $('pay-remaining');
        if (!taken.length) {
            box.style.display = 'none';
            box.innerHTML = '';
            remRow.style.display = 'none';
            return;
        }
        box.style.display = 'flex';
        box.innerHTML = taken
            .map((p, i) => {
                const ref = p.ref ? '<span class="tk-ref">· ' + POS.esc(p.ref) + '</span>' : '';
                // 只有最后一笔可撤(倒序撤单),避免中间撤单让尚差链错位
                const x =
                    i === taken.length - 1
                        ? '<button class="tk-x" aria-label="undo">✕</button>'
                        : '';
                return (
                    '<span class="taken-chip"><span class="tk-m">' +
                    pmLabel(p.method) +
                    '</span><span class="tk-a tnum">฿' +
                    fmt(p.amount) +
                    '</span>' +
                    ref +
                    x +
                    '</span>'
                );
            })
            .join('');
        const x = box.querySelector('.tk-x');
        if (x) x.onclick = undoLastTaken;
        remRow.style.display = 'flex';
        $('pay-remaining-amt').textContent = fmt(remaining());
    }

    function undoLastTaken() {
        taken.pop();
        renderTaken();
        const active = document.querySelector('#pay-mask .pm.active');
        resetTenderInputs(active ? active.dataset.pm : 'cash');
        updatePayButtons();
    }

    // 智能确认按钮:本笔 ≥ 尚差 → 成交文案(还原方式原文);0 < 本笔 < 尚差 → 记一笔并显剩余;本笔=0 → 禁用。
    function updatePayButtons() {
        const rem = remaining();
        Object.keys(PM_CONFIRM_BTN).forEach((m) => {
            const btn = $(PM_CONFIRM_BTN[m]);
            if (!btn) return;
            const amt = tenderAmount(m);
            if (amt <= 0) {
                btn.disabled = true;
                btn.textContent = POS.t(PM_CONFIRM_KEY[m]);
                return;
            }
            btn.disabled = false;
            if (amt < rem - EPS) {
                const record = m === 'cash' ? amt : Math.min(amt, rem);
                btn.textContent = POS.tf('posui.pay.confirm.part', { y: fmt(rem - record) });
            } else {
                btn.textContent = POS.t(PM_CONFIRM_KEY[m]);
            }
        });
    }

    function openPay() {
        if (!cart.length) return;
        closeSheet();
        const due = grandTotal();
        $('pay-due').textContent = fmt(due);
        $('pay-qr-amt').textContent = fmt(due);
        tendered = 0;
        taken = [];
        $('pay-card-ref').value = '';
        renderTaken();
        renderQuickCash();
        updateCash();
        POS.pay.applyMethods('#pay-mask .pm'); // 先按已缓存的设置显隐(瞬时,不阻塞开窗)
        setPm('cash');
        ['pay-cash-err', 'pay-qr-err', 'pay-card-err', 'pay-transfer-err'].forEach(
            (id) => ($(id).textContent = '')
        );
        $('pay-mask').classList.add('show');
        // 开窗即强制重拉最新收款设置:老板刚在后台开的方式(如转账)靠这步立刻显出,
        // 不再依赖切标签的 visibilitychange(真机操作流里常不触发 → 此前"开了不显")。
        POS.pay.refresh(true);
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
        // 非现金默认整付尚差(最常见);loadQr 读该值出码,故先填后出码。
        const amtEl = pmAmtInput(m);
        if (amtEl) amtEl.value = remaining().toFixed(2);
        if (m === 'qr') loadQr();
        if (m === 'transfer') loadBankInfo();
        updatePayButtons();
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
        // 出码金额 = 本笔待收(默认尚差,可下调拆单),而非整单应收——拆单时码要对得上真收的这笔。
        const amt = tenderAmount('qr') || remaining();
        $('pay-qr-amt').textContent = fmt(amt);
        box.innerHTML = '<div class="qr-loading">' + POS.t('posui.loading') + '</div>';
        $('pay-qr-err').textContent = '';
        try {
            const r = await POS.data.promptpayQr(amt);
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
    // 绑定 3×4 数字键盘(收款/数量共用):点键 → fn(data-key)。两处键盘同一 data-key 约定,免属性名分叉。
    function bindKeypad(id, fn) {
        $(id)
            .querySelectorAll('.key')
            .forEach((b) => b.addEventListener('click', () => fn(b.dataset.key)));
    }
    function keyPress(k) {
        let s = String(tendered);
        if (k === 'back') s = s.slice(0, -1) || '0';
        else s = (s === '0' ? '' : s) + k;
        tendered = parseInt(s || '0', 10);
        updateCash();
    }
    function updateCash() {
        $('pay-tendered').textContent = tendered.toLocaleString('en-US');
        const ch = tendered - remaining(); // 找零对尚差算(单笔时尚差=应收,结果与旧版一致)
        $('pay-change').textContent = fmt(ch > 0 ? ch : 0);
        $('pay-cash-err').textContent = '';
        updatePayButtons();
    }

    function buildSalePayload(payments) {
        const sub = subtotalOf(cart);
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
                discountFor(sub) > 0
                    ? {
                          type: discountMode === 'pct' ? 'pct' : 'amount',
                          value:
                              discountMode === 'pct'
                                  ? discountPctValue.toFixed(2)
                                  : Math.min(discount, sub).toFixed(2),
                          reason: discountReason || undefined,
                      }
                    : { type: 'none', value: '0' },
            payments: payments.map((p) => ({
                method: p.method,
                amount: p.amount.toFixed(2),
                ref: p.ref || null,
            })),
            sold_at: new Date().toISOString(),
        };
    }

    // 一个方式的确认:本笔 ≥ 尚差 → 连同已收各笔一并出票成交;本笔 < 尚差 → 记一笔、更新尚差、留窗继续。
    // 现金按实收现钞入账(可溢出,后端据 paid_total−grand 算找零);非现金封顶到尚差(卡/转账不产生找零)。
    async function confirmPay(method, errId, btn) {
        const rem = remaining();
        const amt = tenderAmount(method);
        if (amt <= 0) return; // 按钮此时已禁用,双保险
        const ref = method === 'card' ? ($('pay-card-ref').value || '').trim() || null : null;
        const record = method === 'cash' ? amt : Math.min(amt, rem);
        const tender = { method, amount: record, ref };
        if (amt < rem - EPS) {
            taken.push(tender);
            renderTaken();
            resetTenderInputs(method);
            updatePayButtons();
            POS.toast(POS.tf('posui.pay.part_toast', { x: fmt(record), y: fmt(remaining()) }));
            return;
        }
        await submitSale(taken.concat([tender]), errId, btn);
    }

    async function submitSale(payments, errId, btn) {
        btn.disabled = true;
        const grand = grandTotal();
        const paidTotal = payments.reduce((s, p) => s + p.amount, 0);
        const snapshot = {
            lines: cart.map((c) => ({
                name: c.name,
                qty: c.qty,
                price: c.price,
                sell_unit: c.sell_unit,
            })),
            payments: payments.map((p) => ({ method: p.method, amount: p.amount, ref: p.ref })),
            grand,
            change: Math.max(0, paidTotal - grand),
        };
        const payload = buildSalePayload(payments);
        const onOk = (res) => {
            taken = [];
            closePay();
            POS.toast(POS.t('posui.toast.paid'));
            clearCart();
            showDone(res, snapshot);
        };
        try {
            onOk(await POS.data.createSale(payload));
        } catch (e) {
            // caps 闸开 + 折扣超上限/手工改价越权 → 弹店长授权窗,带 approval(含全部已收笔)重发建单;
            // 授权成功走同一成交流程,失败留窗显错(同退货/作废 PS-1 流程)。
            if (e.code === 'pos.approval_required' && POS.approve) {
                POS.approve.open(
                    (creds) => POS.data.createSale(Object.assign({}, payload, { approval: creds })),
                    onOk
                );
                return;
            }
            // 07 屏1:收款失败弹窗内红字,不关弹窗,可改可重试(taken 未变,不会重复记笔)
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
            client_uuid: snap.client_uuid || sale.id || null,
            receipt_no: sale.receipt_no || '',
            grand_total: sale.grand_total != null ? sale.grand_total : snap.grand.toFixed(2),
            change_amount: sale.change_amount,
            offline: !!(res && res.offline), // 离线补单(Part B5)→ 不可即时开税票
            temporary_receipt: !!sale.temporary_receipt,
            lines: snap.lines,
            payments: snap.payments,
            sold_at: new Date(),
        };
        // 后端据 paid_total 算的找零优先;离线本地兜底用快照。找零>0 才显(只在含现金溢出时发生)。
        const change =
            lastSale.change_amount != null ? lastSale.change_amount : snap.change.toFixed(2);
        $('done-change-row').style.display = Number(change) > 0 ? 'flex' : 'none';
        $('done-change').textContent = fmt(change);
        renderDoneMethods(lastSale.payments);
        $('done-receipt').textContent = lastSale.temporary_receipt
            ? (lastSale.receipt_no || '—') + ' · ' + POS.t('posui.sync.receipt_pending')
            : lastSale.receipt_no || '—';
        // 离线单 / 纯本地预览均不可开正式税票(税票需联网连号)→ 隐税票钮 + 显提示
        const taxable = !lastSale.offline && !!lastSale.id;
        document.querySelector('#done-mask .done-modal').classList.toggle('is-offline', !taxable);
        $('done-mask').classList.add('show');
    }

    // 成交面板按方式分列每笔收款(单笔时也就一行,与原单方式展示等价)。
    function renderDoneMethods(payments) {
        $('done-methods').innerHTML = (payments || [])
            .map(
                (p) =>
                    '<div class="dm-row"><span>' +
                    pmLabel(p.method) +
                    (p.ref ? ' · ' + POS.esc(p.ref) : '') +
                    '</span><span class="tnum">฿' +
                    fmt(p.amount) +
                    '</span></div>'
            )
            .join('');
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
                    POS.esc(POS.nm(l.name)) +
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
        const methodLine = (sale.payments || [])
            .map(
                (p) =>
                    '<tr><td>' +
                    POS.t('posui.pay.' + (p.method === 'qr' ? 'promptpay' : p.method)) +
                    (p.ref ? ' · ' + POS.esc(p.ref) : '') +
                    '</td><td class="r">฿' +
                    fmt(p.amount) +
                    '</td></tr>'
            )
            .join('');
        const changeLine =
            sale.change_amount != null && Number(sale.change_amount) > 0
                ? '<tr><td>' +
                  POS.t('posui.done.change') +
                  '</td><td class="r">฿' +
                  fmt(sale.change_amount) +
                  '</td></tr>'
                : '';
        const html =
            '<!doctype html><html><head><meta charset="utf-8"><title>' +
            POS.esc(sale.receipt_no || '') +
            '</title><style>body{font:12px monospace;width:280px;margin:0 auto;padding:12px;color:#111}' +
            'h3{text-align:center;margin:0 0 8px}table{width:100%;border-collapse:collapse}' +
            'td{padding:2px 0}.r{text-align:right}.tot td{border-top:1px dashed #000;padding-top:6px;font-weight:700}' +
            '.meta{color:#555;margin-bottom:8px}</style></head><body><h3>' +
            POS.esc(state.store || 'Pearnly POS') +
            '</h3>' +
            addrLine +
            '<div class="meta">' +
            POS.esc(sale.receipt_no || '') +
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
            changeLine +
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
            discount: discountFor(subtotalOf(cart)), // 挂单快照存生效额(pct 也折成当时金额,取单按金额续)
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
                const names = h.cart.map((c) => POS.esc(POS.nm(c.name)) + ' ×' + c.qty).join(' · ');
                return (
                    '<div class="held"><div class="h"><span class="no">' +
                    POS.esc(h.no) +
                    '</span><span class="tm">' +
                    POS.esc(h.time) +
                    '</span></div><div class="items">' +
                    names +
                    '</div><div class="ft"><span class="sum">' +
                    POS.tf('posui.cart.items', { n: items, k: h.cart.length }) +
                    '</span><span class="amt tnum">฿' +
                    fmt(total) +
                    '</span></div><div class="ft2"><button class="resume" data-resume="' +
                    POS.esc(h.id) +
                    '"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>' +
                    POS.t('posui.hold.resume') +
                    '</button><button class="del" data-del="' +
                    POS.esc(h.id) +
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
        discountMode = discount > 0 ? 'amount' : 'none'; // 挂单只存了金额,取单按金额模式续
        discountPctValue = 0;
        discountReason = '';
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
        $('main-scan-btn').addEventListener('click', openScanPad);
        $('cart-peek').addEventListener('click', toggleSheet);
        $('cart-scrim').addEventListener('click', closeSheet);
        $('cart-hold-btn').addEventListener('click', holdCurrent);
        $('cart-clear-btn').addEventListener('click', clearCart);
        $('cart-resume-btn').addEventListener('click', () => POS.showView('hold'));
        $('cart-refund-btn').addEventListener('click', () => POS.showView('refund'));
        $('cart-disc-btn').addEventListener('click', openDiscountPad);
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
        bindKeypad('pay-keypad', keyPress);
        // 数量键盘弹窗:点键累加(主路径·不靠物理键盘)+ 关闭/确定 + 背景点击关。
        bindKeypad('qty-keypad', qtyKey);
        $('qty-close-btn').addEventListener('click', closeQtyPad);
        $('qty-confirm').addEventListener('click', confirmQtyPad);
        $('qty-mask').addEventListener('click', (e) => {
            if (e.target === $('qty-mask')) closeQtyPad();
        });
        // 折扣/扫码共用键盘弹窗:同款点击键盘 + 关闭/确定/背景关 + %/฿ 切换。
        bindKeypad('pad-keypad', padKey);
        $('pad-close-btn').addEventListener('click', closePad);
        $('pad-confirm').addEventListener('click', confirmPad);
        $('pad-mask').addEventListener('click', (e) => {
            if (e.target === $('pad-mask')) closePad();
        });
        document
            .querySelectorAll('#pad-seg button')
            .forEach((b) => b.addEventListener('click', () => setPadMode(b.dataset.mode)));
        // 桌面加成:弹窗开着时物理键盘也能输(数字/退格/回车/Esc);靠上面的点击兜底,吞键也不影响。
        // 数量弹窗与折扣/扫码弹窗互斥(同时只开一个),按谁在开路由到对应 handler。
        document.addEventListener('keydown', (e) => {
            const target =
                qtyIdx >= 0
                    ? { key: qtyKey, ok: confirmQtyPad, esc: closeQtyPad }
                    : padCtx
                      ? { key: padKey, ok: confirmPad, esc: closePad }
                      : null;
            if (!target) return;
            if (e.key >= '0' && e.key <= '9') target.key(e.key);
            else if (e.key === 'Backspace') target.key('back');
            else if (e.key === 'Enter') target.ok();
            else if (e.key === 'Escape') target.esc();
            else return;
            e.preventDefault();
        });
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
        // 非现金本笔金额:改额即刷新智能按钮;QR 还需按新额重新出码(用 change 避免逐键打 API)。
        $('pay-card-amt').addEventListener('input', updatePayButtons);
        $('pay-transfer-amt').addEventListener('input', updatePayButtons);
        $('pay-qr-amt-in').addEventListener('input', updatePayButtons);
        $('pay-qr-amt-in').addEventListener('change', loadQr);
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
