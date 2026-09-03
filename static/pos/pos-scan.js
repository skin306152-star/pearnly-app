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
    let controls = null; // 取景框右上角:补光灯 + 动画开关
    let offWedge = null; // 摄像头层开着时的独占订阅(它在,页面级订阅者收不到 → 不会加两次)
    let scanned = 0; // 本轮连扫件数(每次开层归零)

    function isMainActive() {
        const el = $('view-main');
        return !!(el && el.classList.contains('is-active'));
    }
    // 收款/数量/折扣/成交/税票弹窗开着 → 枪扫到的码不许偷偷加进购物车(店员正在办别的事),
    // 但也不许一声不吭地丢掉 —— 那一发的去向见 notAdded。
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
    // 「这一单还欠几件货」那本账在 pos-scan-fails.js —— 它的生死跟相机开不开、码从哪个入口进来
    // 无关(见该文件头)。这边只留下清单要往外做的那两件事:关取景层、把码交回取件那条路。
    const FAILS = window.PearnlyPosScanFails.create({
        // 已建档但没录条码的商品照这条救回来:拿这个码去商品名/编码里搜(原「扫码填搜索框」)。
        // 顺序照旧:先关层,再销这一条,最后才把码送进搜索框。
        onSearch: function (code) {
            close();
            FAILS.resolve(code);
            POS.cashier.searchFor(code);
        },
        // 「刚才那次重读是第二件」:走跟扫码完全同一条取件路(查码 → 加进车 → 成功销账),
        // 不在这里另写一遍加购。单位/缺价/离线那几档判定只该有一处,分叉出去就是两套收钱规则。
        // 这一行的账由店员这一下结掉(resolve 不再碰它)。先销后取件:取件是异步的,留着它等
        // 回包就等于同一颗按钮可以被连点两下,车里凭空多一件。取件真失败/被拒的话,那条路自己
        // 会挂一条说明白的,待办不会凭空消失。
        onAddOne: function (code) {
            FAILS.drop(code);
            submit(code);
        },
    });

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
    // 「当下这一句」说在哪:取景层开着时说在层里那条底栏 —— 那一轮的状态(件数 / 最后一件 /
    // 排队)全在那儿,这句落到别处店员就得在两个地方找。err 走红档:说的是「没加进车」,
    // 长得跟「已加入」一样就等于没说。
    function announce(msg, err) {
        if (cameraOpen()) $('bscan-last').textContent = msg;
        else POS.toast(msg, err ? 'error' : '');
    }
    // 积压必须看得见:枪比后端快,店员看不到「还有 2 件在排队」就会当成没扫上,同一件再扫一遍。
    function queuedNote(n) {
        announce(POS.tf('posui.bscan.queued', { n: n }));
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
        // 老板刚在后台把这个码补进商品资料,店员回头重扫 —— 这件货已经在车里了,清单上那笔欠账
        // 必须跟着销掉,否则屏上还写着「这件货没进车」,店员按它再补一件就是收两遍钱。
        FAILS.resolve(code);
        onHit(item);
    }

    function onHit(item) {
        const added = POS.tf('posui.bscan.added', { name: POS.nm(item.name) });
        const visual = window.PearnlyScanSuccessVisual;
        if (visual && typeof visual.show === 'function') {
            visual.show({
                label: POS.nm(item.name),
                imageUrl: item.image_url,
                target: [$('cart-peek'), $('cart')],
                loadImage: POS.data.loadProdImg,
            });
        }
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
        FAILS.push({
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
        if (notFound && cam && typeof cam.reject === 'function') cam.reject(code);
        if (notFound && e.detail === 'no_catalog') {
            FAILS.push({ msgKey: 'posui.bscan.offline_nocatalog', code: code });
            return;
        }
        if (notFound && e.detail === 'snapshot_miss') {
            FAILS.push({ msgKey: 'posui.bscan.offline_miss', code: code, searchable: true });
            return;
        }
        if (notFound) {
            FAILS.push({
                msgKey: 'bscan.notfound',
                code: code,
                hintKey: 'posui.bscan.create_where',
                searchable: true,
            });
            return;
        }
        FAILS.push({ errCode: e && e.code, code: code });
    }

    // 引擎说:这个码又读到了,但空档没够到「离开过取景框」的判据,于是当成同一件挡下了
    // (见 scan-camera.js 的 accept)。它分不出「举着不动被反光糊了一秒」和「拿开 A 换上同款
    // 的 B」—— 解码结果上是同一串「连着 N 次没解出」。分得出的只有店员,所以摆到他面前。
    // 落进失败清单而不是底部那行字:底部那行会被下一件当场换掉,而这一条正是「这件货可能
    // 没进车」。
    // 已经欠着一笔就什么都不做(不是照常 FAILS.push 顶掉它):那一笔要么是这条提示本身 ——
    // 举着不动会反复触发,重记只让它一直往清单顶上跳,把真正新失败的那件挤下去;要么是更该
    // 处理的失败 —— 码没建档时清单上写的是「去后台建品」,换成「按 +1 加进车」之后那颗 +1
    // 走同一条取件路,按下去只会再吃一次 404,而这件货要建档的线索没有第二个地方还记得。
    function onDuplicate(code) {
        if (FAILS.has(code)) return;
        FAILS.push({
            msgKey: 'posui.bscan.same_code',
            code: code,
            hintKey: 'posui.bscan.same_code_hint',
            addOne: true,
        });
    }

    // ════════════════ 收下了却没进车的那一发 ════════════════
    // 枪响了、灯闪了,屏上什么都没变 —— 店员没有任何办法知道这一件没算进去,那件货就跟着
    // 顾客出门了。两处都要说:toast 说当下(2.6 秒就走,而他那会儿正低头收钱),清单留到他
    // 处理掉(清单在弹窗后面,当场看不见)。少任何一处都还是「响过但没人知道」。
    // 一个键两处用:toast 拿插好码的整句,清单存键(切语言要重画),渲染时才把 {code} 切出来。
    function notAdded(code, msgKey, hintKey) {
        announce(POS.tf(msgKey, { code: code }), true);
        FAILS.push({ msgKey: msgKey, code: code, hintKey: hintKey });
    }

    // 楔子判成「人在打字」的那一发(scan-wedge.js 的 onTyped)。这里不第二次判它是不是枪 ——
    // 结论只有 looksLikeGun 那一份,这一路只负责让屏上有字;框里那串按人打的算,所以不还原。
    // 收银台今天没有框声明接枪,这一路因此不会响;备着是因为漏接的代价是静默丢掉一发输入,
    // 而那正是入库侧栽过的坑(慢枪扫的第二箱整箱从收货单消失)。
    function onTyped(code) {
        notAdded(code, 'posui.bscan.typed', 'posui.bscan.typed_hint');
    }

    // 枪那一发落在哪:没进收银主屏(登录 / 开班)时没有车可加,也没人在等结果;弹窗开着照旧
    // 不加进车(收款中改车会让金额跟已经报给顾客的应付对不上),但必须说一声 —— 收款窗开着
    // 正是最后一件货最容易被补扫的时刻,不说那件货就跟着顾客出门。
    function onGun(code) {
        if (!isMainActive()) return;
        if (modalOpen()) return notAdded(code, 'posui.bscan.modal_busy', 'posui.bscan.modal_hint');
        submit(code);
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
        if (s === 'scanning') {
            sizeFrame(); // 出帧后才知道画面多大 → 框这时才画得准
            if (controls) controls.refreshTorch();
        }
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
            onDuplicate: onDuplicate,
            onError: onCamError,
            onState: paintState,
        });
        const visual = window.PearnlyScanSuccessVisual;
        if (visual && typeof visual.mountControls === 'function') {
            controls = visual.mountControls({
                container: $('bscan-stage'),
                anchor: $('bscan-frame'),
                camera: cam,
                t: POS.t,
            });
        }
        sizeFrame();
    }

    async function open() {
        const why = CAM.unsupportedReason();
        if (why) {
            // 扫码入口不静默消失(Odoo 的病):原因跟着手输弹窗一起摆出来。
            POS.cashier.openScanPad(POS.t(UNSUPPORTED_KEY[why]));
            return;
        }
        if (CAM.armFeedback) CAM.armFeedback();
        $('bscan-mask').classList.add('show');
        scanned = 0;
        paintCount();
        // 层里的文案都在开层这一刻按当前语言画(含「完成」按钮的字:HTML 里是空壳)。
        $('bscan-done').textContent = POS.t('posui.bscan.done');
        $('bscan-last').textContent = '';
        hideCard();
        paintState('starting');
        if (!offWedge) offWedge = WEDGE.register(submit, { exclusive: true, onTyped: onTyped });
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
    // 清单只由三件事变小:那个码这次真进车了 / 那一条被带去搜索框了(FAILS.resolve)、店员点
    // 「知道了」、这一单结束了(saleEnded)。
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
        if (controls) {
            controls.destroy();
            controls = null;
        }
    }

    function wire() {
        $('bscan-done').addEventListener('click', close);
        // Esc 只关取景层。清单不跟着走:Esc 是「关掉眼前这层」的手势,顺手兼一份「这几件货我
        // 不管了」就是让店员在想关相机时静默抹掉几件没进车的货 —— 抹完没有任何地方还记得它们。
        // 清单自己头上有「知道了」那个显式出口,一份待办有一个出口就够。
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && cameraOpen()) close();
        });
        // 框的尺寸是按当时的画面盒子算出来的 px:转屏/软键盘改了舞台大小就得重算。
        window.addEventListener('resize', function () {
            if (cameraOpen()) sizeFrame();
        });
        // 页面刚开就订阅条码枪,而不是「进主屏才订阅」:枪可能在任何时刻被扫,该不该收在 onGun 里判。
        WEDGE.register(onGun, { onTyped: onTyped });
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
    else wire();

    // relang:失败清单挂在收银主屏里但由本文件渲染 → pos.js 的 rerenderActive() 覆不到它。
    // 清单会一直挂到店员点掉,期间切语言只重渲那一屏 = 清单永远停在旧语言。
    // saleEnded:清单是「这一单还欠几件货」的账本 —— 一单结束(收完 / 挂单 / 清空车)必须归零,
    // 否则上一位客人那件没进车的货顶在下一位客人的屏上,店员会照着它补一件不属于这单的货。
    POS.scan = { open, close, submit, saleEnded: FAILS.clear, relang: FAILS.render };
})();
