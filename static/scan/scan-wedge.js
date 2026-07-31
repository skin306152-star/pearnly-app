/*
 * Pearnly · scan-wedge.js · 条码枪键盘楔子(keyboard wedge)
 *
 * 便宜的 USB/蓝牙条码枪对系统就是一个键盘:扫一次 = 极快地敲出一串字符,末尾通常带
 * Enter 或 Tab。所以「支持条码枪」不需要驱动,需要的是能把这串键盘输入从人手打字里分出来。
 *
 * 不抢焦点是硬要求:光标已经在某个输入框里时,店员是在打字(改数量、填批号、填效期),这时候
 * 把按键截走会让输入框吞字。要在某个框里也接枪,给那个元素加 data-enable-barcode="gun" 显式
 * 声明 —— 声明了也只交出【枪打的那种串】,人手打的照旧归那个框(判据见 looksLikeGun)。
 * 不声明就整发被吞:条码 4901234567894 打进 type=date,真 Chromium 实测把它排成 49012-03-31
 * (取证同下方 dateResidue 用例),扫码零回调、屏上零提示,FEFO 与近效期告警从此按四万九千年
 * 后算。
 *
 * 判据只有一份,在这里。使用方拿到回调就是拿到结论,不许各自再按 gap 判一遍 —— 三个消费方
 * 各写各的尺子正是「换个屏就复发」的病根。第三个参数把这一串的实测事实一并交出去,给验收
 * 脚本当取证口(scripts/_gun_ruler_verify.cjs 就靠它在真页面上读出引擎量到的间隔)。
 * 判成「人在打字」的那一发也要说一声(register 的 onTyped),否则店员看不出这一发去哪了;
 * 说一声不等于多一个判据 —— 结论仍然只有 looksLikeGun 这一份,那一路只负责让屏上有字。
 *
 * 尺子量的是【事件产生的时刻】(KeyboardEvent.timeStamp),不是它在主线程被处理的时刻。
 * 这不是讲究,是判据成不成立的问题:主线程被一个长任务卡住时(这个 SPA 上是必然事件),
 * 排队的按键会在解封后挨个到达,Date.now() 量出来是一串 0ms 加一个 120ms 的坎 —— 那 120ms
 * 是页面自己卡的,不是枪打得慢。用墙钟量,自变量(主线程忙不忙)和因变量(判枪还是判人)
 * 就是同一个东西。真产品页实测(scripts/_gun_ruler_verify.cjs · ruler 用例:入库弹窗批号框、
 * 8ms/字符的枪中间插一次 120ms 长任务)—— 处理时刻最大间隔 135.1ms,事件戳最大间隔 22.3ms。
 * 拿前者当尺子,这一发就成了「人在打字」,批号被打成 LOT-B2403018850999320014 且零回调。
 *
 * 判据里没有「框里的残渣长得像不像日期」这一条,不是漏了 —— 是量过之后删掉的。同一个脚本
 * 的 dateResidue 用例在真效期框上量到:人手 120ms/字符打 20271231,控件留下 202712-03-01
 * (年份段一口气吃六位)—— 不是 yyyy-mm-dd。拿「像不像日期」当判据,店员填效期这个最日常的
 * 动作会被判成扫码,整框抹掉再发一次查码。代理判据在这个位置上是反的,速度这条尺子换准了
 * 就够,别再加回来(test_scan_wedge_ruler.py 有一条闸盯着 looksLikeGun 的入参)。
 *
 * 一串键中途会换框:查码应答一回来产品就把光标塞进数量框(inventory-scan.ts 命中后
 * qty.focus()),枪比网络快时同一发的后半串就落进那个框。所以「这一串碰过哪些框」按键逐个
 * 记,不在第一个键上定死 —— 定死过一次,框外开头、框里结尾的那一串两道保护同时落空(既不
 * 按 looksLikeGun 判,也不还原),而码照旧发出去查:数量框从 1 变成 1999320014 跟着整张收货
 * 单提交,手机端那列只有 72px 宽,屏上看得见的就是头几位。现在的规矩是:碰过任何一个框就
 * 按框里那套判,认成枪扫再把碰过的框逐个还原。焦点也跟着 focusin 记一次 —— 焦点在某一发的
 * 派发中途被挪走时,那一发的字符落进新框而 keydown 的 target 还是旧框,只认 keydown 会漏掉
 * 头一个字符(漏一个也是「写进框里没人管」)。
 *
 * 「按住一个键不放」这条与落在哪儿无关,所以框内框外同一条。框外原先根本不问:收银主屏的
 * 焦点常态就在 body 上,柜台上压住一个键实测 12 发 autoRepeat '0' 再蹭到 '5''7',楔子把
 * 00000000000057 当条码查了,屏上一张查无此货的失败卡。速度和长度那两条不搬过去 —— 框外
 * 没人在打字,慢枪照收(有些枪带 intercharacter delay),搬过去就把主路径掐了。
 *
 * 这层必须在首屏就挂上(枪可能在页面刚开就被扫),所以它进 dist/pos.js 与 dist/pre.js,
 * 而摄像头那套是懒加载的 —— 两者一起构成扫码地基,互不依赖。
 */
(function (root) {
    'use strict';

    var doc = root && root.document;

    var MAX_GAP_MS = 150; // 有些枪带 intercharacter delay,实测 ≤50ms;150 留足余量又远小于人手
    var MIN_LENGTH = 3;
    // 枪速上限。人手在同一个框里连打 8 个字符、发发 ≤50ms 是打不出来的(≈20 字符/秒持续)。
    // 键盘自动重复能进这个区间(真 Chromium 实测 40.1~47.9ms 一发),那一路由 repeat 标志挡,
    // 不靠速度。这个上限抬不得:人手填日期实测 100~260ms/字符,而「慢枪」这一档(50~100ms)
    // 与它是叠着的 —— 没有哪个阈值分得开,只能宁可把慢枪当人打的(代价见 register 的 gap)。
    var GUN_MAX_GAP_MS = 50;
    // 声明接枪的框里还要够长才算条码。零售码最短是 EAN-8 / UPC-E 的 8 位,而人手往批号/效期/
    // 数量里填的内容凑不出连续 8 个枪速字符 —— 长度和速度一起才有区分力:光看速度会把「31」
    // 这种两下快按当条码,光看长度会把慢慢打的一串批号抢走。
    var GUN_MIN_LENGTH = 8;

    var ATTR = 'data-enable-barcode';
    var MODE_GUN = 'gun';

    // 枪在传 GS1 分隔符时会发 Alt/Control 组合键,那些键得放进缓冲区(不能在 keydown 就丢,
    // 否则组合键的字符部分也跟着没了),但键名本身不是条码内容,收尾时清掉。
    var NOISE = /Alt|Shift|Control/g;

    function clean(raw) {
        return String(raw || '').replace(NOISE, '');
    }

    // 用 tagName / isContentEditable 判断,不用 el.matches:node 单测里喂的是普通对象桩,
    // 判据必须在没有真 DOM 时也成立(否则这条最容易出错的规则永远没被测过)。
    function isEditable(el) {
        if (!el) return false;
        if (el.isContentEditable) return true;
        var tag = String(el.tagName || '').toLowerCase();
        return tag === 'input' || tag === 'textarea';
    }

    /**
     * 这个可编辑元素声明了接枪吗。
     *
     * 只有一档(gun),但属性值仍然要求写全 —— 判据在 scripts/check_scan_optin.py 那道闸上,
     * 不在这里:运行期一律按最安全的那档走(声明了就走 gun),漏写值退化成「保护人手打字」
     * 而不是「把框吞掉」。裸声明曾经等于「打什么都当条码」,那正是三轮里把人手填的效期
     * 整框换掉的那一档,已经删掉。
     */
    function declaresGun(el) {
        if (!el) return false;
        if (el.dataset && el.dataset.enableBarcode !== undefined) return true;
        return typeof el.getAttribute === 'function' && el.getAttribute(ATTR) !== null;
    }

    // 落在可编辑元素上就让给人打字,除非该元素显式声明接枪。声明了的在这里也要收:是不是枪
    // 打的只有整串收完才判得出(速度要看字符间隔,长度要看攒了几个),收不到就无从判起。
    function shouldCapture(el) {
        if (!isEditable(el)) return true;
        return declaresGun(el);
    }

    /**
     * 事件【产生】的时刻(DOMHighResTimeStamp · 浏览器在事件生成时打的戳)。
     * 见文件头:主线程被长任务卡住时,这个戳纹丝不动,而 Date.now()/performance.now() 在
     * 处理器里读到的是解封之后的时刻。0 / 非数字 = 拿不到(合成事件、老浏览器),回落墙钟。
     */
    function eventTime(ev) {
        var t = ev && ev.timeStamp;
        return typeof t === 'number' && isFinite(t) && t > 0 ? t : null;
    }

    // 整串同一个字符 = 按住一个键不放。repeat 拿不到的浏览器上靠这条兜底。
    function hasTwoDistinct(code) {
        for (var i = 1; i < code.length; i++) {
            if (code.charAt(i) !== code.charAt(0)) return true;
        }
        return false;
    }

    /**
     * 按住一个键不放。两条都是物理事实,不看内容长成什么样:
     *  · repeat —— 浏览器给自动重复的 keydown 打的标志。实测 40~48ms 一发,长度和速度两条
     *    判据全过,只有这个答得了;
     *  · 整串就一种字符 —— 给拿不到 repeat 的环境兜底(见 hasTwoDistinct)。
     *
     * 这条与「落在哪个框里」无关,所以是 finalize 的第一道,框内框外都过它(见文件头)。
     */
    function heldKey(code, info) {
        return !!info.repeat || !hasTwoDistinct(code);
    }

    /**
     * 声明接枪的框只交出「枪打的那种串」。三条判据缺一条就当人在打字:
     *  · 长度 ≥ GUN_MIN_LENGTH —— 日期按段打、批号一两位地打,都攒不到;
     *  · 不是按住一个键不放(见 heldKey)—— 把他的框清掉就是「填个效期字全没了」;
     *  · 每个字符间隔 ≤ GUN_MAX_GAP_MS(按事件产生时刻算,见 eventTime)。
     *
     * 三条全是物理事实,没有一条是「内容长得像什么」的代理判据 —— 代理判据在这个位置上被
     * 验证过是反的(见文件头第三段)。判不准时一律偏向「人在打字」:那一半的错是可见的
     * (码没落地,店员看得见没反应会再扫一次),反过来那一半是静默改效期。
     */
    function looksLikeGun(code, info) {
        if (code.length < GUN_MIN_LENGTH) return false;
        if (heldKey(code, info)) return false;
        return info.gap <= GUN_MAX_GAP_MS;
    }

    /**
     * 「除了慢,其余都像条码」—— 够长、不是按住一个键不放、不是同一个字符反复。
     * 只决定要不要跟使用方说一声(见 finalize 里那条 return),不参与判定。
     *
     * 条件不在这里重抄一遍,而是把速度那一条按满分喂给 looksLikeGun 自己算:两处各写一份
     * 必然漂,而这里漂了就是「该说的时候不说」—— 慢枪扫的那箱货又变回没人知道。
     */
    function shapedLikeCode(code, info) {
        return looksLikeGun(code, { gap: 0, repeat: info.repeat });
    }

    // 非打印键一律放过(Escape/Backspace/方向键/F1…),否则缓冲区会被塞进 'ArrowLeft' 之类。
    // shiftKey 不排除:有些枪用 Shift 打数字。metaKey 组合是快捷键,不是条码。
    function isTypingKey(ev) {
        if (!ev.key || ev.key === 'Unidentified') return false;
        if (ev.key === 'Control' || ev.key === 'Alt') return true;
        return ev.key.length === 1 && !ev.metaKey;
    }

    function isEndKey(ev) {
        return ev.key === 'Enter' || ev.key === 'Tab';
    }

    var subs = [];
    var buffer = '';
    var currentTarget = null;
    var timer = null;
    var attached = false;
    var sink = null;
    var lastStamp = null; // 上一个按键的事件戳(拿不到就是 null)
    var lastWall = 0; // 上一个按键的墙钟时刻 · 只在拿不到事件戳时当尺子
    var maxGap = 0; // 本串里最大的字符间隔
    var sawRepeat = false; // 本串里出现过自动重复的 keydown(按住一个键不放)
    var marks = []; // 本串碰过的每个声明接枪的框 + 它被碰到之前的内容;认成枪扫就逐个还原

    // 安卓上蓝牙条码枪一被当键盘,系统就弹软键盘把收银界面挡掉半屏。把焦点塞进一个
    // inputmode="none" 的隐藏 input,系统就认为「这个框不需要键盘」而不弹 —— 枪的按键照旧
    // 到达 document。这个框只当键盘水槽,内容不作为事实源(见 finalize 里的兜底注释)。
    function makeSink() {
        var el = doc.createElement('input');
        el.setAttribute('inputmode', 'none');
        el.setAttribute('autocomplete', 'off');
        el.setAttribute('aria-hidden', 'true');
        el.setAttribute('tabindex', '-1');
        el.className = 'bscan-sink';
        el.style.cssText =
            'position:fixed;top:50%;left:0;width:1px;height:1px;opacity:0;z-index:-1';
        doc.body.appendChild(el);
        return el;
    }

    function touchLike() {
        if (!root) return false;
        if ('ontouchstart' in root) return true;
        var nav = root.navigator;
        return !!(nav && nav.maxTouchPoints > 0);
    }

    // exclusive 订阅者存在时,只有最后注册的那个收 —— 对应「某个 modal 打开时独占扫码」,
    // 底下页面的订阅者不该在 modal 开着时偷偷把货加进购物车。
    function receivers() {
        var last = null;
        for (var i = 0; i < subs.length; i++) {
            if (subs[i].exclusive) last = subs[i];
        }
        return last ? [last] : subs.slice();
    }

    function reset() {
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
        buffer = '';
        currentTarget = null;
        maxGap = 0;
        sawRepeat = false;
        marks = [];
        if (sink) sink.value = '';
    }

    // 同一个框在一串里只记第一次:后面几个键读到的 value 已经带上这一串的前半截了。
    function mark(el) {
        if (!el || el === sink || !isEditable(el)) return;
        for (var i = 0; i < marks.length; i++) {
            if (marks[i].el === el) return;
        }
        marks.push({ el: el, before: typeof el.value === 'string' ? el.value : null });
    }

    // info.before 配的是 info 里那个 target(这一串最后落在哪个框)—— 使用方拿它还原,
    // 给错了框就是把另一个框的内容写过去。这一串没碰过框(或最后落在框外)就是 null。
    function snapshotOf(list, el) {
        for (var i = 0; i < list.length; i++) {
            if (list[i].el === el) return list[i].before;
        }
        return null;
    }

    // 声明接枪的框:这一串已经被浏览器打进去了(楔子不吃字符键 —— 吃了人手打字就没了),认成
    // 枪扫就把它还原到扫之前。无条件写回,不比对:枪把 type=date 打成半截时它的 value 仍是空
    // 串,只比对 value 会以为「没变过」,而格子里那截垃圾日期还在屏上。
    function restoreField(el, before) {
        if (before === null || !el || typeof el.value !== 'string') return;
        el.value = before;
    }

    function finalize(ev) {
        // 安卓 Chrome 有时把枪的按键报成 key='Unidentified',缓冲区就收不全;水槽 input 的
        // value 在这种情况下比缓冲区长,取长的那份。正常情况两者一致。
        var raw = sink && sink.value.length > buffer.length ? sink.value : buffer;
        var code = clean(raw);
        var target = currentTarget;
        var touched = marks;
        var info = {
            gap: maxGap,
            repeat: sawRepeat,
            field: touched.length > 0,
            before: snapshotOf(touched, target),
        };
        reset();
        if (code.length < MIN_LENGTH) return;
        // 按住一个键不放:框内框外同一条。放在最前面而不是塞进下面那个 if —— 下面那条只在
        // 落进框里时问,而收银主屏的焦点常态在 body 上,压住一个键的那一串就那样发出去查了。
        if (heldKey(code, info)) return;
        // 判不出是枪打的就当人在打字:不回调、不吃 Enter/Tab、不动那个框里的内容。
        // 但「这一发我没当成扫码」也是一种状态,一声不吭 return 掉就是三轮实测的那一幕:
        // 慢枪扫的第二箱整箱从收货单消失,消息还停在上一件的「已加入」,店员以为枪没响。
        // 所以除了速度之外都像条码的那一串,给使用方一声(onTyped)—— 它不是第二个判据出口,
        // 结论仍然只有一个,这一路只负责让屏上有字。数量框里打个 240 不在此列,不打扰。
        if (info.field && !looksLikeGun(code, info)) {
            if (shapedLikeCode(code, info)) {
                receivers().forEach(function (s) {
                    if (s.onTyped) s.onTyped(code, target, info);
                });
            }
            return;
        }
        // 枪打出来的 Enter/Tab 要吃掉:回车会把表单顺手提交,Tab 会把焦点顺手挪走。人手打的
        // 到不了这一行 —— 落在框里的上一句已经拦掉了,落在按钮/页面上的一串本就不是打字。
        if (ev && typeof ev.preventDefault === 'function') ev.preventDefault();
        // 碰过的框逐个还原,不是只还原最后那个:一串枪可以从框外开头、被 focus() 塞进框里
        // 结尾,也可以横跨两个框(上一件的数量框 → 下一行的批号框)。
        for (var i = 0; i < touched.length; i++) restoreField(touched[i].el, touched[i].before);
        receivers().forEach(function (s) {
            s.cb(code, target, info);
        });
    }

    function onKeydown(ev) {
        if (!ev || !ev.key) return; // Chrome 自动填充会发不带 key 的 keydown
        var ending = isEndKey(ev);
        if (!ending && !isTypingKey(ev)) return;

        var target = ev.target;
        if (target !== sink && !shouldCapture(target)) {
            reset();
            return;
        }

        var stamp = eventTime(ev);
        var wall = Date.now();
        var gap = Infinity;
        if (buffer) {
            gap = stamp !== null && lastStamp !== null ? stamp - lastStamp : wall - lastWall;
            if (!(gap >= 0)) gap = wall - lastWall; // 戳不可比(换了时间源)→ 退回墙钟
        }
        // 物理上真隔开了 = 另起一串。不只靠底下那只 150ms 计时器:主线程卡住时它跟按键一起
        // 晚点,而这里读的是按键自己带的时刻,卡不卡都分得开。
        if (buffer && gap > MAX_GAP_MS) {
            finalize(null);
            gap = Infinity;
        }
        // 快照跟着焦点走,不是只取第一个键那一次(见文件头)。keydown 早于字符落进框,所以
        // 每个框第一次被碰到时读到的仍是「它被碰之前」的内容。
        mark(target);
        currentTarget = target;
        if (sink && target !== sink && !isEditable(target)) sink.focus();

        if (buffer) maxGap = Math.max(maxGap, gap);
        if (ev.repeat) sawRepeat = true;
        lastStamp = stamp;
        lastWall = wall;

        if (timer) clearTimeout(timer);
        if (ending) {
            finalize(ev);
            return;
        }
        buffer += ev.key;
        timer = setTimeout(function () {
            finalize(null);
        }, MAX_GAP_MS);
    }

    /**
     * 攒串期间焦点被挪走。字符落进框是在整个 keydown 派发【之后】,所以在某一发的派发中途
     * 调 focus()(产品在 keydown 处理器里挪光标就是这样)时,那一发的字符落进新框,而
     * keydown 拿到的 target 还是旧框 —— 只认 keydown 会把新框的头一个字符漏在外面。focusin
     * 是同步发的,这时新框还干净,拿到的才是真正的「扫之前」。
     */
    function onFocusIn(ev) {
        if (!buffer) return; // 没在攒串,焦点怎么动都与楔子无关
        mark(ev && ev.target);
    }

    function attach() {
        if (attached || !doc) return;
        attached = true;
        if (touchLike() && doc.body && doc.createElement) sink = makeSink();
        // capture 阶段挂:等到冒泡阶段,页面上别的 keydown 处理器可能已经 stopPropagation。
        doc.addEventListener('keydown', onKeydown, true);
        doc.addEventListener('focusin', onFocusIn, true);
    }

    function detach() {
        if (!attached || !doc) return;
        attached = false;
        doc.removeEventListener('keydown', onKeydown, true);
        doc.removeEventListener('focusin', onFocusIn, true);
        // 半截缓冲、计时器、快照一起清:快照拿着 DOM 引用,留着会拖住已经卸掉的弹窗。
        reset();
        if (sink && sink.parentNode) sink.parentNode.removeChild(sink);
        sink = null;
    }

    /**
     * @param {function} cb (code, target, info) => void
     *   info = { gap, repeat, field, before } —— 这一串的实测事实,不是给使用方再判一遍用的
     *   (判据在 looksLikeGun,只此一份),是给验收脚本取证 + 排障看的:
     *     gap     最大字符间隔(ms · 按事件产生时刻算)。> GUN_MAX_GAP_MS 而又发到了这里,
     *             说明这一串一个框都没碰过(框外没人在打字,慢也照收)—— 碰过框的慢串到不了。
     *     repeat  这一串里出现过自动重复的 keydown
     *     field   这一串碰过至少一个声明接枪的框(字符已落进 DOM,楔子已把碰过的框逐个还原)
     *     before  target 那个框在被这一串碰到之前的内容(没碰过框、或最后落在框外时为 null)
     * @param {object} [opts]
     *   exclusive:true  注册期间独占,别人收不到
     *   onTyped(code, target, info)  这一串落在声明接枪的框里、判据说是人在打字时叫一声
     *     (只在「除了慢其余都像条码」时叫)。它不是第二个判据出口 —— cb 收到的仍然只有枪打
     *     的那种串;这一路是给「屏上得有字」用的:静默丢掉一发输入,慢枪扫的那箱货没人知道。
     *     info.before 是那个框扫之前的内容,使用方要把它当条码用时得自己还原(楔子没动过框)。
     * @returns {function} 反注册(幂等)
     */
    function register(cb, opts) {
        if (typeof cb !== 'function') return function () {};
        var entry = { cb: cb, exclusive: !!(opts && opts.exclusive) };
        if (opts && typeof opts.onTyped === 'function') entry.onTyped = opts.onTyped;
        subs.push(entry);
        attach();
        return function () {
            var i = subs.indexOf(entry);
            if (i < 0) return;
            subs.splice(i, 1);
            // 没人订阅就把监听器和隐藏 input 撤掉:不扫码的页面不该白挂一个全局 keydown。
            if (!subs.length) detach();
        };
    }

    var api = {
        register: register,
        ATTR: ATTR,
        MODE_GUN: MODE_GUN,
        MAX_GAP_MS: MAX_GAP_MS,
        GUN_MAX_GAP_MS: GUN_MAX_GAP_MS,
        GUN_MIN_LENGTH: GUN_MIN_LENGTH,
        MIN_LENGTH: MIN_LENGTH,
        clean: clean,
        isEditable: isEditable,
        declaresGun: declaresGun,
        looksLikeGun: looksLikeGun,
        shouldCapture: shouldCapture,
        subscriberCount: function () {
            return subs.length;
        },
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.PearnlyScanWedge = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
