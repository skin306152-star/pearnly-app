/*
 * Pearnly POS · pos-scan.js · 扫码取件(摄像头连扫 + 条码枪 + 手输回落)
 *
 * 单独一个文件:pos-cashier.js 已经是屏1/3/4/5 一锅,再往里塞只会更难改;而扫码这条链
 * (三个入口 → 一次精确取件 → 加进购物车)本身就是一个能独立验的单元。
 *
 * 三个入口共用 submit(code) 一条取件路,差别只在反馈落在哪:
 *   摄像头层  连扫:加完一件不关层,件数实时涨(店员一手拿货一手举机,开一次关一次最费时间)
 *   条码枪    收银主屏零 UI:焦点不在输入框时扫一下就加货(楔子保证不抢输入框)
 *   手输      相机用不了 / 店员主动选 → pos-cashier 的数字键盘弹窗(原有能力保留,不删)
 *
 * 取件走 /api/pos/products/by-barcode 精确等值匹配,绝不退回模糊搜:搜到「差不多」的商品被
 * 当成扫中就是收错钱。命中尊重后端回的 matched_unit —— 扫箱码按箱加、瓶码按瓶加。
 */
(function () {
    const POS = window.POS;
    const CAM = window.PearnlyScanCamera;
    const WEDGE = window.PearnlyScanWedge;
    const $ = (id) => document.getElementById(id);

    // 首屏就能答的两档「这台机器为什么不能开相机」,各对应一句不同的话(见 scan-loader.js)。
    const UNSUPPORTED_KEY = {
        insecure_context: 'bscan.err.insecure',
        no_camera_api: 'bscan.err.unsupported',
    };

    let cam = null; // 摄像头 handle · 懒建:真的开相机那一刻才有
    let offWedge = null; // 摄像头层开着时的独占订阅(它在,页面级订阅者收不到 → 不会加两次)
    let scanned = 0; // 本轮连扫件数(每次开层归零)

    function isMainActive() {
        const el = $('view-main');
        return !!(el && el.classList.contains('is-active'));
    }
    // 收款/数量/折扣/成交/税票弹窗开着 → 枪扫到的码不许偷偷加进购物车(店员正在办别的事)。
    function modalOpen() {
        return !!document.querySelector('#view-main .mask.show');
    }
    // 这层现在只有取景层一种用法:每一件货的失败落在下面那份独立清单上,不再借这层暗底
    // 撑一张卡 —— 那张卡会被队列里下一件当场换掉。
    function cameraOpen() {
        return $('bscan-mask').classList.contains('show');
    }

    // ════════════════ 卡片(相机 / 解码器起不来)════════════════
    function clear(el) {
        while (el.firstChild) el.removeChild(el.firstChild);
    }

    // 扫到的码必须原样看得见 —— 店员靠它判断是货没建档还是码印错了。码嵌在译文中间,按 {code}
    // 切开拼节点:不拿 innerHTML 塞刚扫进来的字符串。
    function renderMsg(el, text, code) {
        const parts = String(text).split('{code}');
        clear(el);
        el.appendChild(document.createTextNode(parts[0]));
        if (parts.length > 1) {
            const b = document.createElement('b');
            b.className = 'bscan-code tnum';
            b.textContent = code;
            el.appendChild(b);
            el.appendChild(document.createTextNode(parts[1]));
        }
    }

    function renderActs(list) {
        const box = $('bscan-acts');
        clear(box);
        list.forEach((a) => {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'bscan-act' + (a.primary ? ' primary' : '');
            b.textContent = POS.t(a.labelKey);
            b.addEventListener('click', a.run);
            box.appendChild(b);
        });
    }

    // 卡片只剩「相机起不来 / 解码器拉不下来」两档:那时本来就没有画面可对,挡住取景区正合适,
    // 而且一轮扫码里只出一次 —— 不存在被下一件顶掉的问题。o = { msg(已译), actions }
    function showCard(o) {
        $('bscan-card-msg').textContent = o.msg;
        renderActs(o.actions);
        $('bscan-card').classList.add('show');
    }
    function hideCard() {
        $('bscan-card').classList.remove('show');
    }

    // note 跟着一起进手输弹窗:店员得知道自己为什么在手打(相机坏了?权限没给?),
    // 不然下次还会先去点扫码。
    function manualAct(primary, note) {
        return {
            labelKey: 'bscan.manual',
            primary: !!primary,
            run: function () {
                close();
                POS.cashier.openScanPad(note);
            },
        };
    }

    // ════════════════ 失败清单(累积 · 不被下一件抹掉)════════════════
    // 队列里第 N 件失败、第 N+1 件几个 microtask 之后就落地:单张卡会被下一件当场换掉,浏览器
    // 连重绘的机会都没有 —— 码是处理了,提示没了,对钱的效果跟「码被丢掉」一模一样(顾客那件
    // 货没进账、店员零提示)。失败因此落在一份只有店员点得掉的清单上:连扫 10 件里第 3 件失败,
    // 扫完回头仍看得见失败的是哪一件、哪个码。清单独立于取景层 —— 枪那条路上没有取景层。
    const fails = [];
    const FAILS_MAX = 20; // 只防无限长撑破布局;真实一轮不会有 20 件失败

    // o = { msgKey, vars, name(多语名对象), errCode, code, hintKey, searchable }
    // 存的是键不是译好的句子:清单会一直挂到店员点掉,期间切语言只会重画 —— 句子存死了就只有
    // 半张卡跟着换语言(标题泰文、正文中文,真截图上抓到过)。名字同理:POS.nm 也是按当时的
    // 语言取的,得留原始对象到画的时候再取。
    function pushFail(o) {
        fails.unshift(o); // 最新的排最上面:不滚动也看得见刚扫的那一件
        if (fails.length > FAILS_MAX) fails.length = FAILS_MAX;
        renderFails();
    }
    function clearFails() {
        fails.length = 0;
        renderFails();
    }

    function failMsg(f) {
        if (f.errCode) return POS.posErrMsg(f.errCode, 'pos.unexpected');
        if (!f.vars && !f.name) return POS.t(f.msgKey); // 不插值:{code} 留给 renderMsg 切
        const vars = Object.assign({}, f.vars);
        if (f.name) vars.name = POS.nm(f.name);
        return POS.tf(f.msgKey, vars);
    }

    function failRow(f) {
        const row = document.createElement('div');
        row.className = 'bscan-fail';
        const text = failMsg(f);
        const msg = document.createElement('div');
        msg.className = 'bscan-fail-msg';
        renderMsg(msg, text, f.code || '');
        row.appendChild(msg);
        // 话里没嵌码的那几档(单位不对 / 没设价)也得把码摆出来:店员拿它去后台核对这件货。
        if (f.code && text.indexOf('{code}') < 0) {
            const c = document.createElement('div');
            c.className = 'bscan-fail-code tnum';
            c.textContent = f.code;
            row.appendChild(c);
        }
        if (f.hintKey) {
            const h = document.createElement('div');
            h.className = 'bscan-fail-hint';
            h.textContent = POS.t(f.hintKey);
            row.appendChild(h);
        }
        // 已建档但没录条码的商品照这条救回来:拿这个码去商品名/编码里搜(原「扫码填搜索框」)。
        if (f.searchable) {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'bscan-fail-act';
            b.textContent = POS.t('posui.bscan.search_code');
            b.addEventListener('click', function () {
                close();
                clearFails();
                POS.cashier.searchFor(f.code);
            });
            row.appendChild(b);
        }
        return row;
    }

    function renderFails() {
        const box = $('bscan-fails');
        clear(box);
        box.classList.toggle('show', fails.length > 0);
        if (!fails.length) return;
        const head = document.createElement('div');
        head.className = 'bscan-fails-head';
        const n = document.createElement('div');
        n.className = 'bscan-fails-n';
        n.textContent = POS.tf('posui.bscan.fails_n', { n: fails.length });
        const ack = document.createElement('button');
        ack.type = 'button';
        ack.className = 'bscan-fails-ack';
        ack.textContent = POS.t('posui.bscan.fails_ack');
        ack.addEventListener('click', clearFails);
        head.appendChild(n);
        head.appendChild(ack);
        box.appendChild(head);
        fails.forEach((f) => box.appendChild(failRow(f)));
    }

    // ════════════════ 取件 ════════════════
    // 串行化走 promise 链,不是「在忙就把这一码丢掉」的布尔:枪连扫三件不同的货时,后两件
    // 都在第一件查回来之前进来 —— 丢掉就是零反馈地消失,顾客付一件的钱拿走三件。链保证
    // 码不丢、落地顺序等于扫的顺序(与 src/home/inventory-scan.ts 的 enqueue 同一招法)。
    let chain = Promise.resolve();
    let pending = 0; // 收下了但还没落地的码数(含正在查的那一件)

    function submit(raw) {
        const code = String(raw || '').trim();
        if (code.length < WEDGE.MIN_LENGTH) return chain;
        pending += 1;
        // 只有排在别人后面才提示:一件在飞是正常速度,提示反而会盖掉「已加入」。
        if (pending > 1) queuedNote(pending - 1);
        chain = chain.then(() => lookup(code)).then(release, release);
        return chain;
    }
    function release() {
        pending -= 1;
    }
    // 积压必须看得见:枪比后端快,店员看不到「还有 2 件在排队」就会当成没扫上,同一件再扫一遍。
    function queuedNote(n) {
        const msg = POS.tf('posui.bscan.queued', { n: n });
        if (cameraOpen()) $('bscan-last').textContent = msg;
        else POS.toast(msg);
    }

    async function lookup(code) {
        let item;
        try {
            // 缺货不拦:货已经在柜台上,拦下就是「看得见卖不出」;库存的最终裁决在建单那步。
            item = await POS.data.productByBarcode(code);
        } catch (e) {
            onMiss(code, e);
            return;
        }
        const refused = POS.cashier.addToCart(item);
        if (refused) {
            onRefused(code, item, refused);
            return;
        }
        scanned += 1;
        onHit(item);
    }

    function onHit(item) {
        const added = POS.tf('posui.bscan.added', { name: POS.nm(item.name) });
        if (!cameraOpen()) {
            POS.toast(added);
            return;
        }
        paintCount();
        $('bscan-last').textContent = added;
    }

    // 加不进购物车的两档都得停下来说清楚:这两档原先都是静默的 —— 一个把整箱按 ฿0 加进车,
    // 一个悄悄改按别的单位收钱,屏上、小票上、报表上都看不出异常。
    function onRefused(code, item, refused) {
        pushFail({
            msgKey: refused.key,
            vars: { unit: refused.unit },
            name: item.name,
            code: code,
            hintKey: 'posui.cart.fix_in_backoffice',
        });
    }

    // 未命中三种成因,话术必须分开:没建档(去建)/ 离线查不了(联网再扫)/ 别的失败(照实说)。
    // 混成一句「找不到商品」,店员就会对着一件本来能卖的货反复扫。
    function onMiss(code, e) {
        const notFound = !!e && e.code === 'pos.product_not_found';
        if (notFound && e.detail === 'no_catalog') {
            pushFail({ msgKey: 'posui.bscan.offline_nocatalog', code: code });
            return;
        }
        if (notFound && e.detail === 'snapshot_miss') {
            pushFail({ msgKey: 'posui.bscan.offline_miss', code: code, searchable: true });
            return;
        }
        if (notFound) {
            pushFail({
                msgKey: 'bscan.notfound',
                code: code,
                hintKey: 'posui.bscan.create_where',
                searchable: true,
            });
            return;
        }
        pushFail({ errCode: e && e.code, code: code });
    }

    // ════════════════ 摄像头层 ════════════════
    // 四态诚实:相机在开(loading)/ 在扫(normal)/ 出错(error 卡)/ 关了。
    // 「扫了但这个码没货」那一态由未命中卡承担。
    function paintState(s) {
        const hint = $('bscan-hint');
        if (s === 'starting') hint.textContent = POS.t('posui.bscan.starting');
        else if (s === 'scanning') hint.textContent = POS.t('posui.bscan.aim');
        else hint.textContent = '';
        $('bscan-frame').classList.toggle('live', s === 'scanning');
        if (s === 'scanning') sizeFrame(); // 出帧后才知道画面多大 → 框这时才画得准
    }
    function paintCount() {
        $('bscan-count').textContent = POS.tf('posui.bscan.count', { n: scanned });
    }

    function onCamError(err) {
        const acts = [];
        if (err.retryable) {
            acts.push({
                labelKey: 'posui.retry',
                primary: true,
                run: function () {
                    hideCard();
                    cam.retry();
                },
            });
        }
        // 没相机/非 HTTPS/权限被拒重试一万次也一样 → 那几档直接把手输摆成主按钮。
        acts.push(manualAct(!err.retryable, err.message));
        showCard({ msg: err.message, actions: acts });
    }

    // 画面在舞台里实际占的那块。预览是 object-fit: contain,画面按比例缩到舞台内再居中,
    // letterbox 之后画面盒子比舞台小 —— 参照系差这一层,框就画错地方。
    // 还没出帧(videoWidth=0)时先按舞台画个占位:那一刻还没有像素在被解。
    function videoBox() {
        const stage = $('bscan-stage');
        const sw = stage.clientWidth;
        const sh = stage.clientHeight;
        if (!sw || !sh) return null;
        const v = cam && cam.video;
        const vw = (v && v.videoWidth) || 0;
        const vh = (v && v.videoHeight) || 0;
        if (!vw || !vh) return { w: sw, h: sh };
        const scale = Math.min(sw / vw, sh / vh);
        return { w: vw * scale, h: vh * scale };
    }

    // 屏上的取景框 = 真正被解码的那块像素:比例从引擎反查(不在 CSS 里各写一份),参照系
    // 取画面盒子而不是舞台。三个参照系(舞台 / 画面 / 原生帧)一旦不重合,框外的另一件货
    // 也会被解出来直接进购物车 —— 底部条只显示最后一件的名字,店员看不出多收了钱。
    function sizeFrame() {
        const box = videoBox();
        if (!box || !cam) return;
        const ratio = cam.cropRatio();
        const f = $('bscan-frame');
        f.style.width = Math.round(box.w * ratio.width) + 'px';
        f.style.height = Math.round(box.h * ratio.height) + 'px';
    }

    function createCam(api) {
        cam = api.create({
            container: $('bscan-stage'),
            t: POS.t,
            onScan: submit,
            onError: onCamError,
            onState: paintState,
        });
        sizeFrame();
    }

    async function open() {
        const why = CAM.unsupportedReason();
        if (why) {
            // 扫码入口不静默消失(Odoo 的病):原因跟着手输弹窗一起摆出来。
            POS.cashier.openScanPad(POS.t(UNSUPPORTED_KEY[why]));
            return;
        }
        $('bscan-mask').classList.add('show');
        scanned = 0;
        paintCount();
        // 层里的文案都在开层这一刻按当前语言画(含「完成」按钮的字:HTML 里是空壳)。
        $('bscan-done').textContent = POS.t('posui.bscan.done');
        $('bscan-last').textContent = '';
        hideCard();
        paintState('starting');
        if (!offWedge) offWedge = WEDGE.register(submit, { exclusive: true });
        let api;
        try {
            api = await CAM.ensureLoaded();
        } catch {
            // 解码器(dist/scan.js)没拉下来:失败记录已被 loader 清掉,重试按钮直接再走一遍 open()。
            const why404 = POS.t('bscan.err.decoder');
            showCard({
                msg: why404,
                actions: [
                    { labelKey: 'posui.retry', primary: true, run: open },
                    manualAct(false, why404),
                ],
            });
            return;
        }
        if (!cameraOpen()) return; // 解码器还在下载时店员按了完成 → 别再去开相机
        if (!cam) createCam(api);
        cam.start();
    }

    // 失败清单不跟着关:那几件货还没建档 / 单位还没修好,店员关掉取景层正是要去处理它们。
    // 只有点「知道了」才清。
    function close() {
        $('bscan-mask').classList.remove('show');
        hideCard();
        if (offWedge) {
            offWedge();
            offWedge = null;
        }
        // 相机必须真放掉(漏了 = 指示灯一直亮、别的应用再打不开);连 video 元素一起扔,
        // 留着它下次开层会先闪一帧上一轮的画面。
        if (cam) {
            cam.destroy();
            cam = null;
        }
    }

    function wire() {
        $('bscan-done').addEventListener('click', close);
        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Escape') return;
            if (cameraOpen()) close();
            else clearFails();
        });
        // 框的尺寸是按当时的画面盒子算出来的 px:转屏/软键盘改了舞台大小就得重算。
        window.addEventListener('resize', function () {
            if (cameraOpen()) sizeFrame();
        });
        // 页面刚开就订阅条码枪,而不是「进主屏才订阅」:枪可能在任何时刻被扫,该不该收在回调里判。
        WEDGE.register(function (code) {
            if (!isMainActive() || modalOpen()) return;
            submit(code);
        });
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
    else wire();

    // relang:失败清单是常驻浮层,不属于任何一屏 → pos.js 的 rerenderActive() 覆不到它。
    // 清单会一直挂到店员点掉,期间切语言只重渲那一屏 = 清单永远停在旧语言。
    POS.scan = { open, close, submit, relang: renderFails };
})();
