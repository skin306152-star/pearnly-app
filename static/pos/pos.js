/*
 * Pearnly POS · pos.js · 核心:启动 / i18n / 路由 / toast / 时钟 / 网络指示 / 屏6 开班登录
 * 独立 plain script,不依赖 home.js。屏1/3/4/5 渲染在 pos-cashier.js(window.POS.cashier)。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const $ = (id) => document.getElementById(id);

    // ── toast(跨屏)──
    let toastTimer = null;
    POS.toast = function (msg, type) {
        const el = $('pos-toast');
        const txt = $('pos-toast-txt');
        if (!el || !txt) return;
        txt.textContent = msg;
        el.classList.toggle('error', type === 'error');
        el.classList.add('show');
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
    };

    // ── i18n 应用(单语随当前语言)──
    POS.applyI18n = function (lang) {
        if (lang) state.lang = lang;
        const dict = (window.POS_I18N && window.POS_I18N[state.lang]) || {};
        document.querySelectorAll('[data-i18n]').forEach((el) => {
            const k = el.getAttribute('data-i18n');
            if (dict[k]) el.textContent = dict[k];
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
            const k = el.getAttribute('data-i18n-placeholder');
            if (dict[k]) el.setAttribute('placeholder', dict[k]);
        });
        document.documentElement.lang = state.lang;
    };

    // ── 路由 ──
    const VIEWS = ['login', 'main', 'hold', 'refund', 'shift'];
    POS.showView = function (name) {
        VIEWS.forEach((v) => {
            const el = $('view-' + v);
            if (el) el.classList.toggle('is-active', v === name);
        });
        const fatal = $('view-fatal');
        if (fatal) fatal.style.display = name === 'fatal' ? 'grid' : 'none';
        if (name === 'hold' && POS.cashier) POS.cashier.renderHold();
        if (name === 'refund' && POS.ops) POS.ops.resetRefund();
        if (name === 'shift' && POS.ops) POS.ops.renderShift();
    };

    // ── 时钟 ──
    function tick() {
        const c = $('main-clock');
        if (!c) return;
        c.textContent = POS.hm(new Date());
    }

    // ── 网络指示(真实探测 navigator.onLine + 手动模拟)──
    POS.setNet = function (online) {
        state.online = online;
        const pill = $('net-pill');
        const txt = $('net-txt');
        if (!pill) return;
        pill.classList.toggle('online', online);
        pill.classList.toggle('offline', !online);
        if (txt) txt.textContent = online ? POS.t('posui.net.online') : POS.t('posui.net.offline');
    };

    // ════════════════ 屏 6 · 开班登录 ════════════════
    let pin = '';
    let selectedCashier = null;

    function renderCashiers(list) {
        const box = $('login-cashiers');
        if (!box) return;
        if (!list || !list.length) {
            box.innerHTML = '<div class="empty">' + POS.t('posui.login.empty') + '</div>';
            return;
        }
        box.innerHTML = list
            .map((c, i) => {
                const color = c.color || '#2563EB';
                const initial = POS.initial(c.display_name);
                return (
                    '<div class="ca' +
                    (i === 0 ? ' on' : '') +
                    '" data-cid="' +
                    c.id +
                    '"><div class="av" style="background:' +
                    color +
                    '">' +
                    initial +
                    '</div><div class="nm">' +
                    (c.display_name || '') +
                    '</div></div>'
                );
            })
            .join('');
        selectedCashier = list[0];
        box.querySelectorAll('.ca').forEach((el) => {
            el.addEventListener('click', () => {
                box.querySelectorAll('.ca').forEach((x) => x.classList.remove('on'));
                el.classList.add('on');
                selectedCashier = list.find((c) => String(c.id) === el.dataset.cid) || null;
                resetPin();
            });
        });
    }

    function drawPins() {
        const dots = document.querySelectorAll('#login-pins .pd');
        dots.forEach((d, i) => d.classList.toggle('f', i < pin.length));
    }
    function resetPin() {
        pin = '';
        drawPins();
        $('login-pinerr').textContent = '';
    }

    function pinPress(v) {
        if (v === 'clear') return resetPin();
        if (v === 'back') {
            pin = pin.slice(0, -1);
            return drawPins();
        }
        if (pin.length >= 4) return;
        pin += v;
        drawPins();
        if (pin.length === 4) setTimeout(submitPin, 180);
    }

    async function submitPin() {
        if (!selectedCashier) return;
        const pad = document.querySelector('#view-login .pad');
        if (pad) pad.style.pointerEvents = 'none';
        try {
            const resp = await POS.data.pinLogin(selectedCashier.id, pin);
            if (resp.token) state.token = resp.token;
            state.cashier = resp.cashier || selectedCashier;
            POS.cashier.applyCashier();
            if (resp.shift) {
                state.shift = resp.shift;
                enterMain();
            } else {
                openShiftModal();
            }
        } catch (e) {
            const row = $('login-pins');
            if (row) {
                row.classList.add('shake');
                setTimeout(() => row.classList.remove('shake'), 420);
            }
            $('login-pinerr').textContent = POS.posErrMsg(e.code, 'pos.pin_invalid');
            resetPin();
        } finally {
            if (pad) pad.style.pointerEvents = '';
        }
    }

    function openShiftModal() {
        const sub = $('shift-open-sub');
        if (sub)
            sub.textContent =
                (state.cashier ? state.cashier.display_name : '') +
                ' · ' +
                POS.t('posui.shift.open.title');
        $('shift-open-float').value = '500';
        $('shift-mask').classList.add('show');
    }

    async function doOpenShift() {
        const btn = $('shift-open-go');
        const raw = ($('shift-open-float').value || '0').replace(/[^\d.]/g, '');
        btn.disabled = true;
        try {
            const shift = await POS.data.openShift(raw || '0');
            state.shift = shift;
            $('shift-mask').classList.remove('show');
            enterMain();
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        } finally {
            btn.disabled = false;
        }
    }

    function enterMain() {
        POS.showView('main');
        POS.cashier.enterMain();
    }

    async function loadLogin() {
        $('login-store').textContent = state.store || '';
        try {
            const list = await POS.data.listCashiers();
            renderCashiers(list);
        } catch (e) {
            renderCashiers([]);
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        }
        resetPin();
    }

    function bindLogin() {
        document.querySelectorAll('#view-login .pad .k').forEach((b) => {
            b.addEventListener('click', () => pinPress(b.dataset.pin));
        });
        $('shift-open-go').addEventListener('click', doOpenShift);
    }

    // ── 全局返回主屏(屏3/4/5 顶栏 back)──
    function bindNav() {
        document.querySelectorAll('[data-nav]').forEach((b) => {
            b.addEventListener('click', () => POS.showView(b.dataset.nav));
        });
        const fatalRetry = $('fatal-retry');
        if (fatalRetry) fatalRetry.addEventListener('click', () => location.reload());
    }

    // ════════════════ 启动 ════════════════
    function readEnv() {
        try {
            state.token = localStorage.getItem('mrpilot_token') || null;
            const lang = localStorage.getItem('mrpilot_lang');
            if (lang && window.POS_I18N[lang]) state.lang = lang;
            const wc = localStorage.getItem('pearnly_active_workspace_client_id');
            state.workspaceClientId = wc ? Number(wc) : null;
            state.store = localStorage.getItem('pearnly_active_workspace_name') || '';
        } catch (_) {}
    }

    function boot() {
        readEnv();
        POS.applyI18n(state.lang);
        bindLogin();
        bindNav();
        if (POS.cashier) POS.cashier.init();
        if (POS.ops) POS.ops.init();
        if (POS.offline) POS.offline.init();
        POS.setNet(navigator.onLine !== false);
        window.addEventListener('online', () => {
            POS.setNet(true);
            POS.toast(POS.t('posui.net.toast.online'));
            if (POS.offline) POS.offline.sync();
        });
        window.addEventListener('offline', () => {
            POS.setNet(false);
            POS.toast(POS.t('posui.net.toast.offline'));
        });
        // PWA 外壳 SW(08 ADR-1)· 失败不影响在线使用
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/pos/pos-sw.js?v=11850703').catch(() => {});
        }
        tick();
        setInterval(tick, 10000);
        POS.showView('login');
        loadLogin();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
