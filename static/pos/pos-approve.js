/*
 * Pearnly POS · pos-approve.js · 店长授权覆盖窗(PS-1 · 防内盗)
 *
 * 收银员无退货/作废权(后端授权闸开时返 pos.approval_required)→ 弹此窗:店长选本人 +
 * 输 PIN,凭据带回调用方重试(后端校验店长确有 pos.refund.approve)。校验失败留窗显错重试,
 * 成功则关窗走成功回调。授权闸关时后端永不返 pos.approval_required,此窗不触发,行为不变。
 * 复用登录同款 PIN 逻辑(4 位自研数字键盘,避开扩展吞键)。对外 window.POS.approve。
 */
(function () {
    const POS = window.POS;
    const $ = (id) => document.getElementById(id);

    let pin = '';
    let selected = null;
    let attemptFn = null; // (creds) => Promise(带凭据的真实重试)
    let onDone = null; // 重试成功回调
    let busy = false;

    function drawPins() {
        document
            .querySelectorAll('#mgr-pins .pd')
            .forEach((d, i) => d.classList.toggle('f', i < pin.length));
    }
    function resetPin() {
        pin = '';
        drawPins();
        $('mgr-pinerr').textContent = '';
    }

    function renderCashiers(list) {
        const box = $('mgr-cashiers');
        if (!box) return;
        if (!list || !list.length) {
            box.innerHTML = '<div class="mgr-empty">' + POS.t('posui.login.empty') + '</div>';
            selected = null;
            return;
        }
        box.innerHTML = list
            .map((c, i) => {
                // 未配色的收银员回退主色令牌(inline style 可解析 var();新代码禁写死旧蓝/裸hex)
                const color = POS.safeColor(c.color);
                const initial = POS.initial(c.display_name);
                return (
                    '<div class="mgr-ca' +
                    (i === 0 ? ' on' : '') +
                    '" data-cid="' +
                    POS.esc(c.id) +
                    '"><div class="av" style="background:' +
                    color +
                    '">' +
                    initial +
                    '</div><div class="nm">' +
                    POS.esc(c.display_name || '') +
                    '</div></div>'
                );
            })
            .join('');
        selected = list[0];
        box.querySelectorAll('.mgr-ca').forEach((el) => {
            el.addEventListener('click', () => {
                box.querySelectorAll('.mgr-ca').forEach((x) => x.classList.remove('on'));
                el.classList.add('on');
                selected = list.find((c) => String(c.id) === el.dataset.cid) || null;
                resetPin();
            });
        });
    }

    function press(v) {
        if (busy) return;
        if (v === 'clear') return resetPin();
        if (v === 'back') {
            pin = pin.slice(0, -1);
            return drawPins();
        }
        if (pin.length >= 4) return;
        pin += v;
        drawPins();
        if (pin.length === 4) setTimeout(submit, 160);
    }

    async function submit() {
        if (busy || !selected || pin.length < 4) return;
        busy = true;
        const pad = $('mgr-pad');
        if (pad) pad.style.pointerEvents = 'none';
        // close() 会清空 onDone,先抓引用再关窗,否则成功回调被吞(退货成功却不回主屏)。
        const done = onDone;
        try {
            // 重试结果回传给 done(建单场景要 res 渲染成交面板;退货/作废忽略此参,零影响)。
            const res = await attemptFn({ cashier_id: selected.id, pin: pin });
            close();
            if (done) done(res);
        } catch (e) {
            const row = $('mgr-pins');
            if (row) {
                row.classList.add('shake');
                setTimeout(() => row.classList.remove('shake'), 420);
            }
            $('mgr-pinerr').textContent = POS.posErrMsg(e && e.code, 'pos.approval_denied');
            resetPin();
        } finally {
            busy = false;
            if (pad) pad.style.pointerEvents = '';
        }
    }

    function close() {
        $('mgr-mask').classList.remove('show');
        attemptFn = null;
        onDone = null;
        selected = null;
        pin = '';
    }

    // open(attempt, done):attempt 收 {cashier_id,pin} 返 Promise(带凭据重试真实动作),
    // 成功则关窗调 done;失败(PosErr)留窗显错。
    async function open(attempt, done) {
        attemptFn = attempt;
        onDone = done;
        busy = false;
        $('mgr-mask').classList.add('show');
        resetPin();
        let list;
        try {
            list = await POS.data.listCashiers();
        } catch (_) {
            list = [];
        }
        renderCashiers(list);
    }

    function init() {
        const pad = $('mgr-pad');
        if (pad) {
            pad.querySelectorAll('.k').forEach((b) => {
                b.addEventListener('click', () => press(b.dataset.pin));
            });
        }
        const cancel = $('mgr-cancel');
        if (cancel) cancel.addEventListener('click', close);
    }

    POS.approve = { init, open, close };
})();
