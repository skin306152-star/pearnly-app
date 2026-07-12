/*
 * Pearnly POS · pos-data.js · 状态 + i18n 取词 + 信封 fetch + 错误码本地化 + B2 前 mock 兜底
 *
 * 信封铁律(docs/pos/04 §0.1):先看 body.ok → true 读 body.data,false 读 body.error.code;
 * 绝不靠 HTTP 码判业务成败。失败码经 posErrMsg 映射 06 字典,绝不裸露 code/英文/HTTP。
 *
 * 接口就绪度:收银员鉴权/开通(B1)已上线 → 走真接口;商品/小票/班次/退货(B2/B6)未上线 →
 * 路由缺失(无信封的 404 / 网络失败)时回落本地 mock,让前台整条可本地预览;接口一上线自动接真。
 * 业务级失败(带信封 ok:false)一律照抛,UI 显友好文案,绝不被 mock 吞掉。
 */
(function () {
    const POS = (window.POS = window.POS || {});

    const state = (POS.state = {
        token: null,
        storeToken: null, // 设备店铺令牌(绑定后 · PIN 登录前的鉴权)
        lang: 'th', // 泰国市场默认泰语;有 mrpilot_lang 时随之(readEnv);页内可切

        workspaceClientId: null,
        terminalId: null,
        store: '',
        cashier: null, // { id, display_name, color }
        shift: null, // { id, opened_at, opening_float }
        online: true,
    });

    // ── i18n ──
    POS.t = function (key) {
        const dict =
            (window.POS_I18N && window.POS_I18N[state.lang]) ||
            (window.POS_I18N && window.POS_I18N.en) ||
            {};
        return dict[key] || key;
    };
    // 模板插值:POS.tf('posui.cart.items', {n: 3, k: 2})
    POS.tf = function (key, vars) {
        let s = POS.t(key);
        if (vars) {
            for (const k in vars) s = s.replace('{' + k + '}', vars[k]);
        }
        return s;
    };
    // 多语言名字段(商品名是 {th,en,zh,ja} 对象)→ 当前语言单值
    POS.nm = function (obj) {
        if (!obj) return '';
        if (typeof obj === 'string') return obj;
        return obj[state.lang] || obj.en || obj.th || obj.zh || Object.values(obj)[0] || '';
    };
    // HTML 转义(本地小票拼字符串塞进 document.write 前用 · 防店铺资料含尖括号破版式)
    POS.esc = function (s) {
        return String(s == null ? '' : s).replace(
            /[&<>"']/g,
            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
        );
    };
    // 商品名缓存(product_id → name 对象)· 选品时填充 · 历史小票退货(详情行不带 name)按 id 回查
    POS.nameCache = {};
    POS.productName = function (productId) {
        const n = POS.nameCache[productId];
        return n ? POS.nm(n) : '';
    };

    // ── 错误码本地化(09 §A.3)──
    // posErrText:查得到返当前语言文案,查不到返 null(绝不抛原始码)。
    POS.posErrText = function (code) {
        if (!code) return null;
        const dict = (window.POS_I18N && window.POS_I18N[state.lang]) || {};
        return dict[code] || null;
    };
    // posErrMsg:查不到回退一句本地化兜底,保证用户永远看到人话。
    POS.posErrMsg = function (code, fallbackKey) {
        return POS.posErrText(code) || POS.t(fallbackKey || 'pos.unexpected');
    };

    // ── 格式化 ──
    POS.fmt = function (n) {
        return Number(n || 0).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    };
    POS.uuid = function () {
        if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = (Math.random() * 16) | 0;
            return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
        });
    };
    // HH:MM(本地时分 · 顶栏时钟/班次开班/挂单/交班共用)
    POS.hm = function (d) {
        return (
            String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
        );
    };
    // 头像首字母(收银员名 · 登录选人 + 主屏顶栏共用)
    POS.initial = function (name) {
        return String(name || '?')
            .trim()
            .charAt(0)
            .toUpperCase();
    };
    // mock 兜底总开关:仅无 workspace 的纯本地预览才允许 mock;真租户绑定后端缺路由一律走诚实失败,
    // 绝不在真店渲染假成功/假财务数(单一策略 · 治"假功能":跨小票/退货/交班/班次汇总统一生效)。
    POS.allowMock = function () {
        return !state.workspaceClientId;
    };

    // ── 收款设置访问器(老板配 · bootstrap 拉到 state.payment;未拉到用默认全开)──
    // 收银台与餐厅埋单共用。支付方式显隐数据驱动:data-pm 值同时是发后端的 method 字符串
    // (收银台 qr / 餐厅 promptpay 指同一 PromptPay),不归一以免改动报表分组,经 PM_FLAG 映射到开关。
    const PAY_DEFAULTS = {
        promptpay_enabled: true,
        card_enabled: true,
        bank_transfer_enabled: false,
        price_includes_vat: true,
    };
    const PM_FLAG = {
        qr: 'promptpay_enabled',
        promptpay: 'promptpay_enabled',
        card: 'card_enabled',
        transfer: 'bank_transfer_enabled',
        // cash 无开关 → 恒显
    };
    const pay = (POS.pay = {});
    pay.settings = function () {
        return state.payment || PAY_DEFAULTS;
    };
    pay.inclVat = function () {
        return pay.settings().price_includes_vat !== false;
    };
    pay.svcRate = function () {
        const r = pay.settings().service_charge_rate;
        return r != null ? String(r) : '10';
    };
    // bootstrap 拉收款设置到 state.payment(已拉过则跳过;失败静默用默认,不阻塞卖货)。
    // 顺带回写店铺名/地址缓存(小票抬头用,见 pos.js POS.cacheStoreInfo)。
    pay.ensure = async function () {
        if (state.payment) return;
        try {
            const b = await POS.data.bootstrap();
            if (b && b.payment) state.payment = b.payment;
            if (b && b.store && POS.cacheStoreInfo) POS.cacheStoreInfo(b.store);
        } catch (_) {}
    };
    // 强制重拉收款设置(老板在别处改了开关 → 收银台回前台时同步 · 走轻量口不重拉整包 bootstrap)。
    // 与 ensure 区别:无视已缓存必拉;失败静默保留旧值(离线/路由缺失不误清已配的方式)。
    // 节流 60s:回前台事件在手机上很频繁(切去银行 App 核对转账/锁屏/切窗都触发),而收款设置
    // 极少变,不必每次切窗都打网络(retail flaky wifi)。force=true 时无视节流——开收款弹窗那刻
    // 收银员正要选方式,必须拿到最新开关(否则老板刚开的转账在 60s 节流窗内看不到,正是此前的坑)。
    let lastPayRefresh = 0;
    pay.refresh = async function (force) {
        const now = Date.now();
        if (!force && now - lastPayRefresh < 60000) return;
        lastPayRefresh = now;
        try {
            const p = await POS.data.paymentMethods();
            if (!p) return;
            state.payment = p;
            const mask = document.getElementById('pay-mask');
            if (mask && mask.classList.contains('show')) pay.applyMethods('#pay-mask .pm');
        } catch (_) {}
    };
    // 按收款设置显隐支付方式元素(现金恒显;关掉的方式不显)。sel 命中容器内带 data-pm 的元素。
    pay.applyMethods = function (sel) {
        const s = pay.settings();
        document.querySelectorAll(sel).forEach((el) => {
            const flag = PM_FLAG[el.dataset.pm];
            if (flag) el.style.display = s[flag] !== false ? '' : 'none';
        });
    };

    // ── 信封 fetch ──
    // enveloped=true 表示服务端返了 {ok:...} 信封(业务级成败);false 表示路由缺失/网络失败。
    function PosErr(code, status, detail, enveloped) {
        this.code = code;
        this.status = status;
        this.detail = detail || null;
        this.enveloped = !!enveloped;
    }
    POS.PosErr = PosErr;

    async function apiFetch(method, path, body) {
        const headers = { 'Content-Type': 'application/json' };
        // PIN 登录前用设备店铺令牌鉴权(列收银员/验PIN);登录后收银员 token 覆盖。
        const bearer = state.token || state.storeToken;
        if (bearer) headers.Authorization = 'Bearer ' + bearer;
        let res;
        try {
            res = await fetch(path, {
                method,
                headers,
                body: body ? JSON.stringify(body) : undefined,
            });
        } catch (e) {
            throw new PosErr('pos.unexpected', 0, 'network', false);
        }
        let json = null;
        try {
            json = await res.json();
        } catch (_) {
            json = null;
        }
        if (json && json.ok === true) return json.data;
        if (json && json.ok === false && json.error) {
            throw new PosErr(json.error.code, res.status, json.error.detail, true);
        }
        // 无信封 → POS 路由尚未注册(B2 前)/ 非 POS 错误
        throw new PosErr('pos.unexpected', res.status, null, false);
    }
    POS.apiFetch = apiFetch;
    // 路由缺失(非业务失败)→ 回落 mock 的判定
    POS.isRouteMissing = function (e) {
        return e instanceof PosErr && !e.enveloped;
    };

    // ════════════════ 本地 mock(B2/B6 上线前)════════════════
    const CATS = [
        { id: 1, name: { th: 'เครื่องดื่ม', en: 'Drinks', zh: '饮料', ja: '飲料' } },
        { id: 2, name: { th: 'ขนม', en: 'Snacks', zh: '零食', ja: 'スナック' } },
        { id: 3, name: { th: 'ของใช้', en: 'Daily', zh: '日用', ja: '日用品' } },
        { id: 4, name: { th: 'เหล้า/บุหรี่', en: 'Liquor', zh: '烟酒', ja: '酒・煙草' } },
        { id: 5, name: { th: 'พร้อมทาน', en: 'Ready', zh: '即食', ja: '惣菜' } },
    ];
    function mkProduct(id, name, cat, price, stock, barcode) {
        return {
            id: 'mock-' + id,
            name,
            category_id: cat,
            base_unit: name.zh,
            image_url: null,
            vat_applicable: true,
            units: [
                {
                    unit_name: name.zh,
                    factor: '1.000',
                    barcode,
                    price: String(price),
                    default_sell: true,
                },
            ],
            track_batch: false,
            is_weighed: false,
            stock: { qty_base: String(stock), near_expiry: false },
        };
    }
    const MOCK_PRODUCTS = [
        mkProduct(
            1,
            { th: 'โค้ก 325ml', en: 'Coke 325ml', zh: '可乐 325ml', ja: 'コーラ 325ml' },
            1,
            15,
            48,
            '8851959131013'
        ),
        mkProduct(
            2,
            { th: 'น้ำเปล่า 600ml', en: 'Water 600ml', zh: '矿泉水 600ml', ja: '水 600ml' },
            1,
            10,
            120,
            '8850999320013'
        ),
        mkProduct(
            3,
            { th: 'ขนมปัง', en: 'Bread', zh: '面包', ja: 'パン' },
            5,
            25,
            9,
            '8853474091201'
        ),
        mkProduct(
            4,
            { th: 'มันฝรั่งทอด', en: 'Potato chips', zh: '薯片', ja: 'ポテトチップス' },
            2,
            20,
            32,
            '8852017300014'
        ),
        mkProduct(
            5,
            { th: 'นมกล่อง', en: 'Milk box', zh: '盒装牛奶', ja: '紙パック牛乳' },
            1,
            18,
            54,
            '8850088200015'
        ),
        mkProduct(
            6,
            { th: 'กาแฟกระป๋อง', en: 'Canned coffee', zh: '罐装咖啡', ja: '缶コーヒー' },
            1,
            22,
            27,
            '8851019120016'
        ),
        mkProduct(
            7,
            { th: 'บะหมี่กึ่งสำเร็จรูป', en: 'Instant noodles', zh: '方便面', ja: 'カップ麺' },
            5,
            6,
            200,
            '8850987100017'
        ),
        mkProduct(
            8,
            { th: 'ไข่ไก่ แผง', en: 'Eggs (tray)', zh: '鸡蛋(板)', ja: '卵(パック)' },
            3,
            120,
            14,
            '8859000180018'
        ),
        mkProduct(
            9,
            { th: 'น้ำอัดลม สไปรท์', en: 'Sprite', zh: '雪碧', ja: 'スプライト' },
            1,
            15,
            40,
            '8851959131099'
        ),
        mkProduct(
            10,
            { th: 'ช็อกโกแลต', en: 'Chocolate', zh: '巧克力', ja: 'チョコ' },
            2,
            35,
            18,
            '8851234560020'
        ),
        mkProduct(
            11,
            { th: 'หมากฝรั่ง', en: 'Gum', zh: '口香糖', ja: 'ガム' },
            2,
            12,
            60,
            '8851234560021'
        ),
        mkProduct(
            12,
            { th: 'ทิชชู่', en: 'Tissue', zh: '纸巾', ja: 'ティッシュ' },
            3,
            28,
            22,
            '8858888100022'
        ),
    ];
    const MOCK_CASHIERS = [
        { id: 'mock-c1', display_name: 'Nok', color: '#2563EB' },
        { id: 'mock-c2', display_name: 'Ploy', color: '#0891b2' },
        { id: 'mock-c3', display_name: 'Aek', color: '#7c3aed' },
    ];
    POS.mock = { CATS, PRODUCTS: MOCK_PRODUCTS, CASHIERS: MOCK_CASHIERS };

    // 通用本地选品过滤(mock 预览 + 离线快照共用)
    POS.filterCatalog = function (list, q, cat) {
        let items = (list || []).slice();
        if (cat) items = items.filter((p) => p.category_id === cat);
        if (q) {
            const s = q.toLowerCase();
            items = items.filter((p) => {
                const hit = Object.values(p.name).join(' ').toLowerCase().includes(s);
                const code = (p.units || []).some((u) => (u.barcode || '').includes(q));
                return hit || code;
            });
        }
        return items;
    };
    function filterProducts(q, cat) {
        return POS.filterCatalog(MOCK_PRODUCTS, q, cat);
    }

    // ════════════════ 高层数据方法 ════════════════
    const data = (POS.data = {});

    data.categories = function () {
        return CATS;
    };

    // 商品图鉴权取图:收银员 token 不能放进 <img src>(浏览器不带 Authorization 头),
    // 故 fetch 成 blob 再塞 objectURL。image_url 形如 /api/uploads/image/{tenant}/{name}
    // (那条只认登录用户)→ POS 改走 /api/pos/products/image/{name}(认收银员 token)。
    data.loadProdImg = async function (img, imageUrl) {
        if (!img || !imageUrl) return;
        const m = String(imageUrl).match(/\/api\/uploads\/image\/[^/]+\/([^/?#]+)/);
        if (!m) {
            img.src = imageUrl; // 外链:直接用
            return;
        }
        const bearer = state.token || state.storeToken;
        try {
            const res = await fetch('/api/pos/products/image/' + encodeURIComponent(m[1]), {
                headers: bearer ? { Authorization: 'Bearer ' + bearer } : {},
            });
            if (!res.ok) return;
            const obj = URL.createObjectURL(await res.blob());
            img.addEventListener('load', () => URL.revokeObjectURL(obj), { once: true });
            img.src = obj;
        } catch (_) {
            /* 取图失败:留占位,不抛 */
        }
    };

    // 设备绑定:店铺码 → 店铺令牌(04 §1b)。无 mock 兜底:绑定必须真后端(隔离关键)。
    data.bind = async function (code) {
        return apiFetch('POST', '/api/pos/bind', { code: code });
    };

    data.listCashiers = async function () {
        try {
            const d = await apiFetch(
                'GET',
                '/api/pos/cashiers?workspace_client_id=' + state.workspaceClientId
            );
            return d.cashiers || [];
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) return MOCK_CASHIERS; // 纯本地预览
            throw e;
        }
    };

    data.pinLogin = async function (cashierId, pin) {
        try {
            return await apiFetch('POST', '/api/pos/auth/pin', {
                workspace_client_id: state.workspaceClientId,
                cashier_id: cashierId,
                pin,
            });
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                // 本地预览(无后端):任意非空 PIN 视为通过,返 mock token
                const c = MOCK_CASHIERS.find((x) => x.id === cashierId) || MOCK_CASHIERS[0];
                return { token: 'mock-token', cashier: c, shift: null, offline_ttl_hours: 12 };
            }
            throw e;
        }
    };

    data.openShift = async function (openingFloat) {
        try {
            const d = await apiFetch('POST', '/api/pos/shifts/open', {
                workspace_client_id: state.workspaceClientId,
                terminal_id: state.terminalId,
                opening_float: openingFloat,
            });
            return d.shift;
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                return {
                    id: 'mock-shift',
                    opened_at: new Date().toISOString(),
                    opening_float: openingFloat,
                };
            }
            throw e;
        }
    };

    // 前台启动包(04 §1)· 取业态(modules.pos.config.business_type)分流零售/餐厅。
    data.bootstrap = async function () {
        try {
            return await apiFetch(
                'GET',
                '/api/pos/bootstrap?workspace_client_id=' + (state.workspaceClientId || '')
            );
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock())
                return { modules: { pos: { config: { business_type: 'retail' } } } };
            throw e;
        }
    };

    // 轻量拉收款设置(pay.refresh 用 · 只回显隐开关+银行/PromptPay 信息,不含商品)。
    data.paymentMethods = async function () {
        return await apiFetch(
            'GET',
            '/api/pos/payment-methods?workspace_client_id=' + (state.workspaceClientId || '')
        );
    };

    // 收款前出码:按账套配的 PromptPay ID + 待收金额生成二维码(无需先建单)。
    data.promptpayQr = async function (amount) {
        const qs = new URLSearchParams({
            workspace_client_id: state.workspaceClientId || '',
            amount: Number(amount || 0).toFixed(2),
        });
        return await apiFetch('GET', '/api/pos/promptpay-qr?' + qs.toString());
    };

    data.products = async function (q, cat) {
        try {
            const qs = new URLSearchParams({ workspace_client_id: state.workspaceClientId || '' });
            if (q) qs.set('q', q);
            if (cat) qs.set('category', cat);
            const d = await apiFetch('GET', '/api/pos/products?' + qs.toString());
            const items = d.items || [];
            if (!q && !cat && POS.offline) POS.offline.cacheCatalog(items); // 全量快照供离线选品
            return items;
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) return filterProducts(q, cat);
            // 离线真租户:回落本地商品快照(联网时已缓存)
            if (POS.isRouteMissing(e) && POS.offline && POS.offline.hasSnapshot())
                return POS.offline.filterCached(q, cat);
            throw e;
        }
    };

    // 收款建小票。离线(navigator/手动)→ 走 outbox 本地出单;在线 → 真 POST;纯本地预览回落 mock。
    data.createSale = async function (payload) {
        if (!state.online && POS.offline) return POS.offline.enqueueSale(payload);
        try {
            return await apiFetch('POST', '/api/pos/sales', payload);
        } catch (e) {
            // 在线请求却网络失败(信封缺失 = isRouteMissing)且引擎在 → 落 outbox 不丢单
            if (POS.isRouteMissing(e) && POS.offline && !POS.allowMock())
                return POS.offline.enqueueSale(payload);
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                const grand = payload.lines.reduce(
                    (s, l) => s + Number(l.unit_price) * Number(l.qty),
                    0
                );
                const paid = payload.payments.reduce((s, p) => s + Number(p.amount), 0);
                return {
                    sale: {
                        id: POS.uuid(),
                        receipt_no: 'RCP-LOCAL-' + Math.floor(Math.random() * 90000 + 10000),
                        grand_total: grand.toFixed(2),
                        paid_total: paid.toFixed(2),
                        change_amount: Math.max(0, paid - grand).toFixed(2),
                        status: 'completed',
                    },
                    stock_applied: true,
                    deduped: false,
                };
            }
            throw e;
        }
    };

    data.findReceipt = async function (no) {
        if (String(no).startsWith('OFF-') && POS.offline) {
            const local = await POS.offline.findReceipt(no);
            if (!local || local.status !== 'synced') {
                const code =
                    local && local.status === 'blocked'
                        ? 'pos.offline_blocked'
                        : 'pos.offline_pending';
                throw new PosErr(code, 409, local && local.last_error, true);
            }
            no = local.receipt_no;
        }
        try {
            return await apiFetch('GET', '/api/pos/sales/by-receipt?no=' + encodeURIComponent(no));
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                // mock 原单:固定一张可演示退货流程
                return {
                    sale: {
                        id: 'mock-sale',
                        receipt_no: no,
                        sold_at: new Date().toISOString(),
                        method: 'cash',
                        cashier: state.cashier ? state.cashier.display_name : 'Nok',
                    },
                    lines: [
                        {
                            sale_line_id: 'L1',
                            name: MOCK_PRODUCTS[0].name,
                            unit_price: '15.00',
                            qty: '2',
                        },
                        {
                            sale_line_id: 'L2',
                            name: MOCK_PRODUCTS[2].name,
                            unit_price: '25.00',
                            qty: '1',
                        },
                        {
                            sale_line_id: 'L3',
                            name: MOCK_PRODUCTS[3].name,
                            unit_price: '20.00',
                            qty: '1',
                        },
                    ],
                    payments: [{ method: 'cash', amount: '75.00' }],
                };
            }
            throw e;
        }
    };

    // 今日已完成交易(退货/作废入口 · 收银员 token 可读)。每项带 method/mixed/voidable。
    data.salesToday = async function () {
        try {
            const d = await apiFetch(
                'GET',
                '/api/pos/sales/today' +
                    (state.workspaceClientId
                        ? '?workspace_client_id=' + state.workspaceClientId
                        : '')
            );
            return (d && d.items) || [];
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                // 纯本地预览:一张现金单(可作废)+ 一张混合单(已交班不可作废,演示退货)
                return [
                    {
                        id: 'mock-sale',
                        receipt_no: 'RCP-3012',
                        sold_at: new Date().toISOString(),
                        grand_total: '75.00',
                        method: 'cash',
                        mixed: false,
                        voidable: true,
                    },
                    {
                        id: 'mock-sale-2',
                        receipt_no: 'RCP-3009',
                        sold_at: new Date(Date.now() - 5400000).toISOString(),
                        grand_total: '120.00',
                        method: 'card',
                        mixed: true,
                        voidable: false,
                    },
                ];
            }
            throw e;
        }
    };

    // 单笔详情(退货详情 · 与 findReceipt 同信封 {sale, lines, payments})。
    data.saleDetail = async function (saleId) {
        try {
            return await apiFetch('GET', '/api/pos/sales/' + saleId);
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) return data.findReceipt(saleId);
            throw e;
        }
    };

    // 当班作废(错单干净回滚)。approval 同退货:授权闸开且收银员无权时带店长凭据重试。
    data.void = async function (saleId, approval) {
        const body = {};
        if (state.workspaceClientId) body.workspace_client_id = state.workspaceClientId;
        if (approval) body.approval = approval;
        try {
            return await apiFetch('POST', '/api/pos/sales/' + saleId + '/void', body);
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock())
                return { sale_id: saleId, status: 'void', stock_returned: true };
            throw e;
        }
    };

    // approval(可选):店长授权覆盖凭据 { cashier_id, pin }。仅在授权闸开且收银员无权时,
    // 前台弹窗收集后带上重试;闸关时永不出现(后端不返 pos.approval_required)。
    // refundPayments(可选):混合支付原路拆退 [{method, amount正额}],Σ 须等于退款额;
    // 只给 refund_method 单笔时走后端兼容路。符号约定:前台传正额,后端统一取负存。
    data.refund = async function (saleId, lines, method, approval, refundPayments) {
        const body = {
            client_uuid: POS.uuid(),
            lines,
            refund_method: method,
        };
        if (refundPayments && refundPayments.length) body.refund_payments = refundPayments;
        if (approval) body.approval = approval;
        try {
            return await apiFetch('POST', '/api/pos/sales/' + saleId + '/refund', body);
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                const total = lines.reduce((s, l) => s + Number(l._amt || 0), 0);
                return {
                    refund_sale: {
                        id: POS.uuid(),
                        receipt_no: 'RFD-LOCAL',
                        grand_total: '-' + total.toFixed(2),
                    },
                    stock_returned: true,
                };
            }
            throw e;
        }
    };

    // 班次汇总(交班屏)。按收银台查当前未结班次(不依赖前端内存 → 刷新/换人仍可交班)。
    // B2 前回落 mock(对齐概念稿 05 数字)。
    data.shiftSummary = async function () {
        try {
            const d = await apiFetch(
                'GET',
                '/api/pos/shifts/current' +
                    (state.workspaceClientId
                        ? '?workspace_client_id=' + state.workspaceClientId
                        : '')
            );
            if (d && d.shift) state.shift = d.shift; // 同步内存:交班 close 取 state.shift.id
            return d;
        } catch (e) {
            // 真租户绑定后端却缺 summary 端点时返 null(屏5 显诚实空态),绝不在真店渲染假财务数。
            // 班次汇总 GET 待后端补(close 才返 summary)· mock 仅纯本地预览(POS.allowMock 单一策略)。
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                if (!state.shift) return null;
                return {
                    shift: {
                        id: state.shift.id,
                        opened_at: state.shift.opened_at,
                        opening_float: state.shift.opening_float,
                    },
                    summary: {
                        sales_count: 86,
                        gross: '12480.00',
                        by_method: { cash: '7230.00', promptpay: '4650.00', card: '600.00' },
                        expected_cash: '7730.00',
                    },
                };
            }
            if (POS.isRouteMissing(e)) return null;
            throw e;
        }
    };

    // 小票升级正式税票(04 §6 · B4)。买方公司/个人字段集见屏2。
    // 离线不可开税票(税票需联网连号 · 08 ADR v1 范围),仅纯本地预览回落 mock 演示。
    data.fullTaxInvoice = async function (saleId, buyer) {
        try {
            return await apiFetch('POST', '/api/pos/sales/' + saleId + '/full-tax-invoice', {
                workspace_client_id: state.workspaceClientId,
                buyer,
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

    // 离线批量补传(04 §6 · B5)。逐张幂等,部分失败不卡其余;失败项端上保留重试。
    data.syncSales = function (items) {
        return apiFetch('POST', '/api/pos/sales/sync', {
            workspace_client_id: state.workspaceClientId,
            sales: items,
        });
    };

    data.closeShift = async function (countedCash) {
        try {
            return await apiFetch('POST', '/api/pos/shifts/' + state.shift.id + '/close', {
                counted_cash: countedCash,
            });
        } catch (e) {
            if (POS.isRouteMissing(e) && POS.allowMock()) {
                return {
                    shift: {
                        id: state.shift.id,
                        closed_at: new Date().toISOString(),
                        counted_cash: countedCash,
                    },
                };
            }
            throw e;
        }
    };
})();
