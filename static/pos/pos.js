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

    // ── 语言切换(店员可在登录页/主屏自选 · 持久化到 mrpilot_lang · 与主程序共享)──
    function updateLangButtons() {
        document.querySelectorAll('[data-lang]').forEach((b) => {
            b.classList.toggle('on', b.dataset.lang === state.lang);
        });
    }
    POS.setLang = function (lang) {
        if (!window.POS_I18N || !window.POS_I18N[lang]) return;
        state.lang = lang;
        try {
            localStorage.setItem('mrpilot_lang', lang);
        } catch (_) {}
        POS.applyI18n(lang);
        updateLangButtons();
        rerenderActive(); // 重渲当前屏的 JS 动态内容(静态 data-i18n 已由 applyI18n 处理)
    };
    function rerenderActive() {
        const active = VIEWS.find((v) => {
            const el = $('view-' + v);
            return el && el.classList.contains('is-active');
        });
        if (active === 'login') loadLogin();
        else if (active === 'main' && POS.cashier) POS.cashier.enterMain();
        else if (active === 'hold' && POS.cashier) POS.cashier.renderHold();
        else if (active === 'refund' && POS.ops) POS.ops.resetRefund();
        else if (active === 'shift' && POS.shift) POS.shift.renderShift();
        else if (active === 'rtables' && POS.restaurant) POS.restaurant.renderTables();
        else if (active === 'rkitchen' && POS.restaurant) POS.restaurant.renderKitchen();
        else if (active === 'rorder' && POS.restaurant && POS.restaurant.curSession())
            POS.restaurant.reloadOrder();
    }

    // ── 路由 ──
    const VIEWS = [
        'bind',
        'login',
        'main',
        'hold',
        'refund',
        'shift',
        'rtables',
        'rorder',
        'rkitchen',
    ];
    POS.showView = function (name) {
        VIEWS.forEach((v) => {
            const el = $('view-' + v);
            if (el) el.classList.toggle('is-active', v === name);
        });
        const fatal = $('view-fatal');
        if (fatal) fatal.style.display = name === 'fatal' ? 'grid' : 'none';
        if (name === 'hold' && POS.cashier) POS.cashier.renderHold();
        if (name === 'refund' && POS.ops) POS.ops.resetRefund();
        if (name === 'shift' && POS.shift) POS.shift.renderShift();
        if (name === 'rkitchen' && POS.restaurant) POS.restaurant.renderKitchen();
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
                if (resp.shift.terminal_id != null) state.terminalId = resp.shift.terminal_id;
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
            if (shift && shift.terminal_id != null) state.terminalId = shift.terminal_id;
            $('shift-mask').classList.remove('show');
            enterMain();
        } catch (e) {
            // 本收银台已有进行中班次(别人/上一班开的)→ 共享钱箱:接续该班进主屏,绝不卡死。
            if (e.code === 'pos.shift_already_open' && (await resumeOpenShift())) return;
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        } finally {
            btn.disabled = false;
        }
    }

    // 取本收银台当前未结班次并接续(共享);成功进主屏返回 true。
    async function resumeOpenShift() {
        try {
            const d = await POS.data.shiftSummary(); // 内部同步 state.shift
            if (d && d.shift) {
                state.shift = d.shift;
                if (d.shift.terminal_id != null) state.terminalId = d.shift.terminal_id;
                $('shift-mask').classList.remove('show');
                await enterMain();
                return true;
            }
        } catch (_) {
            /* 取不到 → 回退通用提示 */
        }
        return false;
    }

    function cancelShiftModal() {
        $('shift-mask').classList.remove('show');
        resetPin(); // 回到 PIN 输入(可换收银员)
    }

    async function enterMain() {
        // 业态=restaurant 进桌台流;零售/药房走收银主屏(pos-cashier)。
        if (POS.restaurant && (await POS.restaurant.ensureBusinessType())) {
            POS.restaurant.enter();
            return;
        }
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
        $('shift-open-cancel').addEventListener('click', cancelShiftModal);
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
    const STORE_TOKEN_KEY = 'pos_store_token';
    const STORE_WS_KEY = 'pos_store_ws';
    const STORE_NAME_KEY = 'pos_store_name';
    const STORE_ADDR_KEY = 'pos_store_addr';

    function readEnv() {
        try {
            state.token = localStorage.getItem('mrpilot_token') || null;
            const lang = localStorage.getItem('mrpilot_lang');
            if (lang && window.POS_I18N[lang]) state.lang = lang;
            // 设备店铺绑定(收银员任意设备路径)优先;否则老板「切到收银台」旧路径(选的账套)
            state.storeToken = localStorage.getItem(STORE_TOKEN_KEY) || null;
            if (state.storeToken) {
                const sw = localStorage.getItem(STORE_WS_KEY);
                state.workspaceClientId = sw ? Number(sw) : null;
                state.store = localStorage.getItem(STORE_NAME_KEY) || '';
            } else {
                const wc = localStorage.getItem('pearnly_active_workspace_client_id');
                state.workspaceClientId = wc ? Number(wc) : null;
                state.store = localStorage.getItem('pearnly_active_workspace_name') || '';
            }
            // 小票抬头地址:离线打印用,来源见 pos-data.js pay.ensure() 拉到 bootstrap.store 后回写缓存。
            state.storeAddress = localStorage.getItem(STORE_ADDR_KEY) || '';
        } catch (_) {}
    }

    function saveBinding(d) {
        state.storeToken = d.store_token;
        state.workspaceClientId = d.workspace_client_id;
        state.store = d.store_name || '';
        try {
            localStorage.setItem(STORE_TOKEN_KEY, d.store_token);
            localStorage.setItem(STORE_WS_KEY, String(d.workspace_client_id));
            localStorage.setItem(STORE_NAME_KEY, state.store);
        } catch (_) {}
    }

    // bootstrap 拉到账套主体资料后回写店名/地址缓存(供离线打印小票用)· pos-data.js pay.ensure() 调。
    POS.cacheStoreInfo = function (store) {
        if (!store) return;
        state.store = store.name || state.store;
        state.storeAddress = store.address || '';
        try {
            if (store.name) localStorage.setItem(STORE_NAME_KEY, store.name);
            localStorage.setItem(STORE_ADDR_KEY, state.storeAddress);
        } catch (_) {}
    };

    // 已绑定(店铺令牌)或老板旧路径(选了账套)→ 进登录;否则进设备绑定屏。
    function isProvisioned() {
        return !!(state.storeToken || state.workspaceClientId);
    }

    async function bindDevice(code) {
        const go = $('bind-go');
        const err = $('bind-err');
        const c = (code || '').trim().toUpperCase();
        err.textContent = '';
        if (c.length < 4) {
            err.textContent = POS.posErrMsg('pos.store_code_invalid');
            return;
        }
        go.disabled = true;
        try {
            const d = await POS.data.bind(c);
            saveBinding(d);
            POS.showView('login');
            loadLogin();
        } catch (e) {
            err.textContent = POS.posErrMsg(e.code, 'pos.store_code_invalid');
        } finally {
            go.disabled = false;
        }
    }

    // ── 摄像头扫码(BarcodeDetector · 安卓 Chrome 等支持;iOS Safari 无此 API → 回落手输)──
    let scanStream = null;
    let scanTimer = null;
    function parseStoreCode(raw) {
        if (!raw) return null;
        const m = String(raw).match(/[?&]store=([^&\s]+)/i);
        return m ? decodeURIComponent(m[1]) : String(raw).trim();
    }
    function closeScan() {
        if (scanTimer) {
            clearTimeout(scanTimer);
            scanTimer = null;
        }
        if (scanStream) {
            scanStream.getTracks().forEach((t) => t.stop());
            scanStream = null;
        }
        const mask = $('bind-scan-mask');
        if (mask) mask.classList.remove('show');
    }
    async function openScan() {
        const inp = $('bind-code');
        const ok =
            'BarcodeDetector' in window &&
            navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia;
        if (!ok) {
            POS.toast(POS.t('posui.bind.scan_unsupported'));
            if (inp) inp.focus();
            return;
        }
        const video = $('bind-scan-video');
        try {
            scanStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' },
            });
            video.srcObject = scanStream;
            await video.play();
        } catch (_) {
            POS.toast(POS.t('posui.bind.scan_denied'));
            if (inp) inp.focus();
            return;
        }
        $('bind-scan-mask').classList.add('show');
        let detector;
        try {
            detector = new window.BarcodeDetector({ formats: ['qr_code'] });
        } catch (_) {
            detector = new window.BarcodeDetector();
        }
        const tick = async () => {
            if (!scanStream) return;
            try {
                const codes = await detector.detect(video);
                if (codes && codes.length) {
                    const code = parseStoreCode(codes[0].rawValue);
                    if (code) {
                        closeScan();
                        $('bind-code').value = code;
                        bindDevice(code);
                        return;
                    }
                }
            } catch (_) {}
            scanTimer = setTimeout(tick, 350);
        };
        tick();
    }

    function bindBindScreen() {
        const go = $('bind-go');
        if (go) go.addEventListener('click', () => bindDevice($('bind-code').value));
        const inp = $('bind-code');
        if (inp)
            inp.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') bindDevice(inp.value);
            });
        const scanBtn = $('bind-scan-btn');
        if (scanBtn) scanBtn.addEventListener('click', openScan);
        const scanCancel = $('bind-scan-cancel');
        if (scanCancel) scanCancel.addEventListener('click', closeScan);
    }

    // 入口决策:URL ?store= 自动绑定 → 已绑/旧路径进登录 → 否则绑定屏。
    async function startEntry() {
        let code = null;
        try {
            code = new URLSearchParams(location.search).get('store');
        } catch (_) {}
        if (code && !state.storeToken) {
            await bindDevice(code);
            return;
        }
        if (isProvisioned()) {
            POS.showView('login');
            loadLogin();
        } else {
            POS.showView('bind');
            const inp = $('bind-code');
            if (inp) inp.focus();
        }
    }

    function boot() {
        readEnv();
        POS.applyI18n(state.lang);
        bindLogin();
        bindNav();
        bindBindScreen();
        document.querySelectorAll('[data-lang]').forEach((b) => {
            b.addEventListener('click', () => POS.setLang(b.dataset.lang));
        });
        updateLangButtons();
        if (POS.cashier) POS.cashier.init();
        if (POS.ops) POS.ops.init();
        if (POS.approve) POS.approve.init();
        if (POS.restaurant) POS.restaurant.init();
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
        // 收银台回到前台 → 同步收款设置(老板可能在另一设备/标签页改了收款方式;不刷新看不到)。
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && POS.pay) POS.pay.refresh();
        });
        // PWA 外壳 SW(08 ADR-1 · PS-5 迁址)· 失败不影响在线使用。收银台新家在 /cashier,从根路径
        // /cashier-sw.js 注册 + scope:/cashier → SW 能控 /cashier 导航(断网重开外壳)。只注销更旧的
        // /static/pos/ 作用域残留;老 /pos 作用域 SW 故意保留 —— 迁移中的老设备靠它离线兜底老壳,
        // 落到 /cashier 后各管各的作用域,互不抢导航。
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker
                .getRegistrations()
                .then((regs) => {
                    regs.forEach((r) => {
                        if (r.scope.indexOf('/static/pos/') >= 0) r.unregister();
                    });
                })
                .catch(() => {});
            navigator.serviceWorker
                .register('/cashier-sw.js?v=11911101', { scope: '/cashier' })
                .catch(() => {});
        }
        tick();
        setInterval(tick, 10000);
        startEntry();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
