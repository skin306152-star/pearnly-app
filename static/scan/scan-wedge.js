/*
 * Pearnly · scan-wedge.js · 条码枪键盘楔子(keyboard wedge)
 *
 * 便宜的 USB/蓝牙条码枪对系统就是一个键盘:扫一次 = 极快地敲出一串字符,末尾通常带
 * Enter 或 Tab。所以「支持条码枪」不需要驱动,需要的是能把这串键盘输入从人手打字里分出来:
 *   - 人打字的字符间隔远大于 150ms,枪是几毫秒一个字符 → 间隔超 MAX_GAP_MS 即认为一串结束
 *   - Enter / Tab 立即收尾,不用等那 150ms
 *   - 少于 MIN_LENGTH 位的当误触丢掉(店员按一下键盘不该当成扫了一件货)
 *
 * 不抢焦点是硬要求:光标已经在某个输入框里时,店员是在打字(改数量、填备注),这时候把按键
 * 截走会让输入框吞字。要在某个框里也接枪,给那个元素加 data-enable-barcode 显式声明,两档:
 *   data-enable-barcode        这框里打什么都当条码送出去(入库数量框:扫完一件光标停在
 *                              那儿,下一枪照旧要收得到;落进框里的字符由使用方摘回去)
 *   data-enable-barcode="gun"  只有【枪打的那种串】才当条码,人手打的照旧归这个框。批号/
 *                              效期框走这一档:不声明就整发被吞 —— 条码 4901234567894 打进
 *                              type=date 会变成 49012-03-31,扫码零回调、屏上零提示,FEFO 与
 *                              近效期告警从此按四万九千年后算;而人手在同一个框里填日期必须
 *                              原样留下。判据见 looksLikeGun();认成枪扫时本层把框还原回扫
 *                              之前的内容(type=date 的 value 不是那串原文,使用方摘不回来)。
 *
 * 这层必须在首屏就挂上(枪可能在页面刚开就被扫),所以它进 dist/pos.js 与 dist/pre.js,
 * 而摄像头那套是懒加载的 —— 两者一起构成扫码地基,互不依赖。
 */
(function (root) {
    'use strict';

    var doc = root && root.document;

    var MAX_GAP_MS = 150; // 有些枪带 intercharacter delay,实测 ≤50ms;150 留足余量又远小于人手
    var MIN_LENGTH = 3;
    // 「这一串是枪打的还是人打的」的判据,只在决定吃不吃 Enter/Tab 时用(见 endKeyFromGun)。
    // 实测枪 ≤50ms/字符;人手进不到这个区间 —— 键盘自动重复要按住 ~500ms 才起,那早就超过
    // MAX_GAP_MS 被收尾了,凑不出一串全 ≤50ms 的输入。
    var GUN_MAX_GAP_MS = 50;
    // data-enable-barcode="gun" 档的长度下限。零售码最短是 EAN-8 / UPC-E 的 8 位,而人手往
    // 批号/效期/数量里填的内容凑不出连续 8 个枪速字符 —— 长度和速度一起才有区分力:光看速度
    // 会把「31」这种两下快按当条码,光看长度会把慢慢打的一串批号抢走。
    var GUN_MIN_LENGTH = 8;

    var MODE_GUN = 'gun';
    var MODE_ALWAYS = 'always';

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

    // '' = 没声明;'always' = 打什么都当条码;'gun' = 只收枪打的那种串(见文件头两档说明)。
    function barcodeMode(el) {
        if (!el) return '';
        var raw = null;
        if (el.dataset && el.dataset.enableBarcode !== undefined) raw = el.dataset.enableBarcode;
        else if (typeof el.getAttribute === 'function')
            raw = el.getAttribute('data-enable-barcode');
        if (raw === null || raw === undefined) return '';
        return String(raw).trim().toLowerCase() === MODE_GUN ? MODE_GUN : MODE_ALWAYS;
    }

    // 落在可编辑元素上就让给人打字,除非该元素显式声明接枪。'gun' 档在这里也要收:是不是枪
    // 打的只有整串收完才判得出(速度要看字符间隔,长度要看攒了几个),收不到就无从判起。
    function shouldCapture(el) {
        if (!isEditable(el)) return true;
        return !!barcodeMode(el);
    }

    /**
     * 'gun' 档的框只交出「枪打的那种串」。三条判据缺一条就当人在打字:
     *  · 整串每个字符间隔 ≤ GUN_MAX_GAP_MS —— 人手进不到这个区间(见该常量);
     *  · 长度 ≥ GUN_MIN_LENGTH —— 日期「31/03/2027」按段打、批号一两位地打,都攒不到;
     *  · 至少两种不同字符 —— 按住一个键不放,系统自动重复约 30ms 一发,速度和长度两条都会
     *    过。那是人按的,把他的框清掉就是「填个效期字全没了」。
     */
    function looksLikeGun(code, gap) {
        if (code.length < GUN_MIN_LENGTH || gap > GUN_MAX_GAP_MS) return false;
        for (var i = 1; i < code.length; i++) {
            if (code.charAt(i) !== code.charAt(0)) return true;
        }
        return false;
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
    var lastKeyAt = 0;
    var maxGap = 0; // 本串里最大的字符间隔
    var captureMode = ''; // 本串落点的接枪声明('' / 'always' / 'gun')
    var restoreValue = null; // 'gun' 档的框在本串开始前的内容;认成枪扫就还原回去

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
        captureMode = '';
        restoreValue = null;
        if (sink) sink.value = '';
    }

    // 'gun' 档的框:这一串已经被浏览器打进去了(楔子不吃字符键 —— 吃了人手打字就没了),认成
    // 枪扫就把它还原到扫之前。无条件写回,不比对:枪把 type=date 打成半截时它的 value 仍是空
    // 串,只比对 value 会以为「没变过」,而格子里那截垃圾日期还在屏上。
    function restoreField(el, before) {
        if (before === null || !el || typeof el.value !== 'string') return;
        el.value = before;
    }

    // 枪打出来的 Enter/Tab 要吃掉:回车会把表单顺手提交,Tab 会把焦点顺手挪走。人手打的不能吃
    // —— 入库数量框(带 data-enable-barcode 显式接枪)里打「1000」再按 Tab,吞掉就是焦点纹丝
    // 不动,店员只看到「弹窗卡住了」。两者的区别只有速度,所以只在落点是可编辑元素时(那里
    // 才可能有人在打字)要求整串跑到枪速;落在按钮/页面上的一串本就不是打字,带 intercharacter
    // delay 的慢枪不该因此把回车漏给表单。水槽是我们自己塞的隐藏 input,没人往里打字。
    function endKeyFromGun(target, gap) {
        if (target === sink || !isEditable(target)) return true;
        return gap <= GUN_MAX_GAP_MS;
    }

    function finalize(ev) {
        // 安卓 Chrome 有时把枪的按键报成 key='Unidentified',缓冲区就收不全;水槽 input 的
        // value 在这种情况下比缓冲区长,取长的那份。正常情况两者一致。
        var raw = sink && sink.value.length > buffer.length ? sink.value : buffer;
        var code = clean(raw);
        var target = currentTarget;
        var gap = maxGap;
        var mode = captureMode;
        var before = restoreValue;
        reset();
        if (code.length < MIN_LENGTH) return;
        // 判不出是枪打的就当人在打字:不回调、不吃 Enter/Tab、不动那个框里的内容。
        if (mode === MODE_GUN && !looksLikeGun(code, gap)) return;
        if (ev && typeof ev.preventDefault === 'function' && endKeyFromGun(target, gap)) {
            ev.preventDefault();
        }
        if (mode === MODE_GUN) restoreField(target, before);
        receivers().forEach(function (s) {
            s.cb(code, target);
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
        // 快照要在本串第一个键上取:keydown 早于字符落进框,这时读到的才是「扫之前」的内容。
        if (!buffer) {
            captureMode = target === sink ? '' : barcodeMode(target);
            restoreValue =
                captureMode === MODE_GUN && target && typeof target.value === 'string'
                    ? target.value
                    : null;
        }
        currentTarget = target;
        if (sink && target !== sink && !isEditable(target)) sink.focus();

        var now = Date.now();
        if (buffer) maxGap = Math.max(maxGap, now - lastKeyAt);
        lastKeyAt = now;

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

    function attach() {
        if (attached || !doc) return;
        attached = true;
        if (touchLike() && doc.body && doc.createElement) sink = makeSink();
        // capture 阶段挂:等到冒泡阶段,页面上别的 keydown 处理器可能已经 stopPropagation。
        doc.addEventListener('keydown', onKeydown, true);
    }

    function detach() {
        if (!attached || !doc) return;
        attached = false;
        doc.removeEventListener('keydown', onKeydown, true);
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
        buffer = '';
        if (sink && sink.parentNode) sink.parentNode.removeChild(sink);
        sink = null;
    }

    /**
     * @param {function} cb (code, target) => void
     * @param {object} [opts] {exclusive:true} = 注册期间独占,别人收不到
     * @returns {function} 反注册(幂等)
     */
    function register(cb, opts) {
        if (typeof cb !== 'function') return function () {};
        var entry = { cb: cb, exclusive: !!(opts && opts.exclusive) };
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
        MAX_GAP_MS: MAX_GAP_MS,
        GUN_MAX_GAP_MS: GUN_MAX_GAP_MS,
        GUN_MIN_LENGTH: GUN_MIN_LENGTH,
        MIN_LENGTH: MIN_LENGTH,
        clean: clean,
        isEditable: isEditable,
        barcodeMode: barcodeMode,
        looksLikeGun: looksLikeGun,
        shouldCapture: shouldCapture,
        subscriberCount: function () {
            return subs.length;
        },
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.PearnlyScanWedge = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
