/*
 * Pearnly POS · pos-scan-fails.js · 「这一单还欠几件货」那本账
 *
 * 从 pos-scan.js 分出来的一层。分界不是按行数切的:这本账的生死只由四件事决定 —— 那个码后来
 * 真进车了 / 被带去搜索框了 / 店员点了「知道了」 / 这一单结束了。相机开没开、码是从摄像头还是
 * 枪进来的,它一概不关心;反过来取件那条链也不该知道欠账怎么排版。
 *
 * 它为什么得是一份累积清单:队列里第 N 件失败、第 N+1 件几个 microtask 之后就落地,单张卡会被
 * 下一件当场换掉 —— 码是处理了,提示没了,对钱的效果跟「码被丢掉」一模一样(顾客那件货没进账、
 * 店员零提示)。清单只有店员点得掉:连扫 10 件里第 3 件失败,扫完回头仍看得见失败的是哪一件、
 * 哪个码。它挂在收银主屏里、独立于取景层 —— 枪那条路上根本没有取景层。
 *
 * 对外只认两个回调,别的动作一概交回去:凡「关取景层 / 把码送进搜索框 / 再走一遍取件」都发生在
 * 这本账之外 —— 在这里分叉出去就是第二套收钱规则。
 *   onSearch(code)  拿这个码去商品名/编码里搜(已建档但没录条码的照这条救回来)
 *   onAddOne(code)  「刚才那次重读是第二件」· 走跟扫码完全同一条取件路
 */
(function () {
    const POS = window.POS;
    const $ = (id) => document.getElementById(id);

    const FAILS_MAX = 20; // 只防无限长撑破布局;真实一轮不会有 20 件失败

    function empty(el) {
        while (el.firstChild) el.removeChild(el.firstChild);
    }

    // 扫到的码必须原样看得见 —— 店员靠它判断是货没建档还是码印错了。码嵌在译文中间,按 {code}
    // 切开拼节点:不拿 innerHTML 塞刚扫进来的字符串。
    function renderMsg(el, text, code) {
        const parts = String(text).split('{code}');
        empty(el);
        el.appendChild(document.createTextNode(parts[0]));
        if (parts.length > 1) {
            const b = document.createElement('b');
            b.className = 'bscan-code tnum';
            b.textContent = code;
            el.appendChild(b);
            el.appendChild(document.createTextNode(parts[1]));
        }
    }

    function failMsg(f) {
        if (f.errCode) return POS.posErrMsg(f.errCode, 'pos.unexpected');
        if (!f.vars && !f.name) return POS.t(f.msgKey); // 不插值:{code} 留给 renderMsg 切
        const vars = Object.assign({}, f.vars);
        if (f.name) vars.name = POS.nm(f.name);
        return POS.tf(f.msgKey, vars);
    }

    function actBtn(labelKey, run) {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'bscan-fail-act';
        b.textContent = POS.t(labelKey);
        b.addEventListener('click', run);
        return b;
    }

    // handlers = { onSearch, onAddOne }
    function create(handlers) {
        const fails = [];

        // 码是这本账的主键:同一件货只该欠一笔。
        function has(code) {
            return fails.some(function (f) {
                return f.code === code;
            });
        }
        function remove(code, onlyIf) {
            const at = fails.findIndex((f) => f.code === code && (!onlyIf || onlyIf(f)));
            if (at < 0) return false;
            fails.splice(at, 1);
            return true;
        }

        // item = { msgKey, vars, name(多语名对象), errCode, code, hintKey, searchable, addOne }
        // 存的是键不是译好的句子:清单会一直挂到店员点掉,期间切语言只会重画 —— 句子存死了就只有
        // 半张卡跟着换语言(标题泰文、正文中文,真截图上抓到过)。名字同理:POS.nm 也是按当时的
        // 语言取的,得留原始对象到画的时候再取。
        // 同码只留一条:店员以为没扫上就会再扫一下,同一件货记三笔会把「还有几件没进车」这个数
        // 说成三件 —— 而这个数正是他清点柜台的依据。新的那条顶掉旧的(失败原因可能已经变了)。
        function push(item) {
            remove(item.code);
            fails.unshift(item); // 最新的排最上面:不滚动也看得见刚扫的那一件
            if (fails.length > FAILS_MAX) fails.length = FAILS_MAX;
            render();
        }

        // 销账:这个码已经不欠了(真进车了 / 已经被带去搜索框处理)。不销 = 清单白纸黑字说这件货
        // 没进车,而车里明明有它,店员照着清单再补一次就是多收钱。入库侧同一招。
        // 「刚才那次重读被当成同一件」那一行(addOne)是唯一的例外:它说的是【那一件】可能没进车,
        // 而这个码后来又真记上一件,记的是【再一件】—— 拿后者销前者,等于把没进车的那件悄悄抹掉,
        // 屏上于是跟全都扫上了一模一样,顾客照样拿两件付一件的钱(这条提示本来就是来挡这个的)。
        // 真浏览器实测(1.2s 与 2.0s 空档交替、无人触碰):那一行被自动抹掉 2 次,车 3 件而柜台上
        // 是 6 件。所以这一行只有店员销得掉 —— 点「+1」补货(走 drop),或点「知道了」。
        function resolve(code) {
            if (remove(code, (f) => !f.addOne)) render();
        }
        // 店员亲手结掉这一条:不带 addOne 那层保护 —— 他结的正是那一行。
        function drop(code) {
            remove(code);
            render();
        }
        function clear() {
            fails.length = 0;
            render();
        }

        function row(f) {
            const el = document.createElement('div');
            el.className = 'bscan-fail';
            const text = failMsg(f);
            const msg = document.createElement('div');
            msg.className = 'bscan-fail-msg';
            renderMsg(msg, text, f.code || '');
            el.appendChild(msg);
            // 话里没嵌码的那几档(单位不对 / 没设价)也得把码摆出来:店员拿它去后台核对这件货。
            if (f.code && text.indexOf('{code}') < 0) {
                const c = document.createElement('div');
                c.className = 'bscan-fail-code tnum';
                c.textContent = f.code;
                el.appendChild(c);
            }
            if (f.hintKey) {
                const h = document.createElement('div');
                h.className = 'bscan-fail-hint';
                h.textContent = POS.t(f.hintKey);
                el.appendChild(h);
            }
            // 按钮上写的是「搜这个码」,就只能销掉这一条:整份清一遍等于替店员宣布另外那几件货
            // 他也不管了,而那几件的码此后没有任何地方还记得。销账由回调那头按顺序做。
            if (f.searchable) {
                el.appendChild(actBtn('posui.bscan.search_code', () => handlers.onSearch(f.code)));
            }
            if (f.addOne) {
                el.appendChild(actBtn('posui.bscan.add_one', () => handlers.onAddOne(f.code)));
            }
            return el;
        }

        function render() {
            const box = $('bscan-fails');
            empty(box);
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
            ack.addEventListener('click', clear);
            head.appendChild(n);
            head.appendChild(ack);
            box.appendChild(head);
            fails.forEach((f) => box.appendChild(row(f)));
        }

        return { push, has, resolve, drop, clear, render };
    }

    window.PearnlyPosScanFails = { create: create };
})();
