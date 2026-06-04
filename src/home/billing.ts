// ============================================================
// REFACTOR-A1.3 (2026-05-22) · 改 ES module · 不再 IIFE
//
// 原 v118.35.0.11 · 充值弹窗 · 3-step flow + 余额实时轮询
//
// 文件搬迁:
//   旧 static/home/billing.js(IIFE · script src 加载)
//   新 src/home/billing.js(ES module · Vite bundle 到 static/dist/main.js)
//
// 依赖 home.js 提供的全局:t / showToast / _userInfo / loadDashboard
//                       / _refreshBalanceAlerts / subscribeI18n
// 加载顺序:home.html <script src=home.js> 同步执行后,
//          <script type=module src=/static/dist/main.js> defer 自动后跑
// ============================================================

function _bt(k: string): string {
    return (typeof window.t === 'function' ? window.t(k) : null) || k;
}
function _tok() {
    return localStorage.getItem('mrpilot_token') || '';
}
function _g(id: string): HTMLElement | null {
    return document.getElementById(id);
}

// ── 余额实时轮询 ──
var _lastBal: number | null = null;
var _pollTimer: ReturnType<typeof setInterval> | null = null;

function _startPoll() {
    if (_pollTimer) return;
    _pollTimer = setInterval(function () {
        if (document.hidden) return;
        var tok = _tok();
        if (!tok) return;
        if (window._userInfo && window._userInfo.is_billing_exempt) return;
        fetch('/api/me/credits', { headers: { Authorization: 'Bearer ' + tok }, cache: 'no-store' })
            .then(function (r) {
                return r.ok ? r.json() : null;
            })
            .then(function (d) {
                if (!d) return;
                var bal = d.balance_thb != null ? Number(d.balance_thb) : 0;
                if (_lastBal !== null && bal > _lastBal) {
                    if (window.showToast) window.showToast(_bt('credits-updated'), 'success');
                    if (typeof window.loadDashboard === 'function') window.loadDashboard();
                    if (typeof window._refreshBalanceAlerts === 'function')
                        window._refreshBalanceAlerts();
                }
                _lastBal = bal;
            })
            .catch(function () {});
    }, 30000);
}

function _stopPoll() {
    if (_pollTimer) {
        clearInterval(_pollTimer);
        _pollTimer = null;
    }
    _lastBal = null;
}

window._startCreditsPoll = _startPoll;
window._stopCreditsPoll = _stopPoll;
_startPoll(); // 登录后页面已有 token,直接启动

// ── modal state ──
var _reqId: string | null = null;
var _amount = 0;

// ── 构建 DOM(懒创建,只建一次)──
function _render() {
    if (_g('topup-v2-ov')) return;
    var ov = document.createElement('div');
    ov.id = 'topup-v2-ov';
    ov.className = 'topup-v2-ov';
    ov.style.cssText =
        'display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px';
    ov.innerHTML = [
        '<div class="topup-v2-box">',
        '  <div class="topup-v2-head">',
        '    <div class="topup-v2-title" id="tv2-title"></div>',
        '    <button class="topup-v2-close" id="tv2-close" aria-label="close">',
        '      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',
        '    </button>',
        '  </div>',
        '  <div class="topup-v2-steps">',
        '    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>',
        '    <div class="topup-v2-line"></div>',
        '    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>',
        '    <div class="topup-v2-line"></div>',
        '    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',
        '  </div>',
        '  <div class="topup-v2-body">',
        // Step 1
        '    <div id="tv2-s1">',
        '      <label class="topup-v2-label" id="tv2-al"></label>',
        '      <div class="topup-v2-qamts">',
        '        <button class="topup-v2-qamt" data-val="100">฿100</button>',
        '        <button class="topup-v2-qamt" data-val="500">฿500</button>',
        '        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>',
        '        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',
        '      </div>',
        '      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">',
        '      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',
        '    </div>',
        // Step 2
        '    <div id="tv2-s2" style="display:none">',
        '      <p class="topup-v2-bank-label" id="tv2-bl"></p>',
        '      <div class="topup-v2-bank-card">',
        '        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>',
        '        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>',
        '        <div class="topup-v2-bank-acct">230-0-91368-4</div>',
        '        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>',
        '        <button class="topup-v2-copy" id="tv2-copy"></button>',
        '      </div>',
        '      <div class="topup-v2-warn" id="tv2-bn"></div>',
        '    </div>',
        // Step 3
        '    <div id="tv2-s3" style="display:none">',
        '      <div class="topup-v2-drop" id="tv2-drop">',
        '        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">',
        '        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
        '        <span class="topup-v2-drop-text" id="tv2-dt"></span>',
        '      </div>',
        '      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>',
        '      <label class="topup-v2-label" id="tv2-pl"></label>',
        '      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">',
        '      <label class="topup-v2-label" id="tv2-nl"></label>',
        '      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">',
        '      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',
        '    </div>',
        '  </div>',
        '  <div class="topup-v2-foot">',
        '    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>',
        '    <button class="btn btn-primary" id="tv2-next"></button>',
        '  </div>',
        '</div>',
    ].join('');
    document.body.appendChild(ov);
    _bindEvents();
}

function _applyText() {
    var setText = function (id: string, v: string) {
        var e = _g(id);
        if (e) e.textContent = v;
    };
    setText('tv2-title', _bt('topup-title'));
    setText('tv2-sl1', _bt('topup-step1'));
    setText('tv2-sl2', _bt('topup-step2'));
    setText('tv2-sl3', _bt('topup-step3'));
    setText('tv2-al', _bt('topup-amount-label'));
    setText('tv2-bl', _bt('topup-bank-label'));
    setText('tv2-copy', _bt('topup-copy-account'));
    setText('tv2-dt', _bt('topup-slip-drop'));
    setText('tv2-pl', _bt('topup-payer-label'));
    setText('tv2-nl', _bt('topup-note-label'));
}

function _setStep(n: number) {
    [1, 2, 3].forEach(function (i) {
        var s = _g('tv2-s' + i);
        if (s) s.style.display = i === n ? '' : 'none';
        var d = _g('tv2-d' + i);
        if (d) d.classList.toggle('active', i <= n);
    });
    var back = _g('tv2-back'),
        next = _g('tv2-next');
    if (n === 1) {
        if (back) {
            back.style.display = '';
            back.textContent = _bt('topup-btn-cancel');
        }
    } else {
        if (back) {
            back.style.display = '';
            back.textContent = _bt('topup-btn-back');
        }
    }
    if (next) next.textContent = n === 3 ? _bt('topup-btn-submit') : _bt('topup-btn-next');
    if (n === 2) {
        var bn = _g('tv2-bn');
        if (bn)
            bn.innerHTML = _bt('topup-bank-note').replace(
                '{amount}',
                '<strong>฿' + Number(_amount).toLocaleString() + '</strong>'
            );
    }
}

function _curStep() {
    for (var i = 1; i <= 3; i++) {
        var e = _g('tv2-s' + i);
        if (e && e.style.display !== 'none') return i;
    }
    return 1;
}

function _clrErr(id: string) {
    var e = _g(id);
    if (e) {
        e.textContent = '';
        e.style.display = 'none';
    }
}
function _showErr(id: string, msg: string) {
    var e = _g(id);
    if (e) {
        e.textContent = msg;
        e.style.display = '';
    }
}

function _setFile(f: File) {
    var dt = _g('tv2-dt');
    if (dt) dt.textContent = f.name;
    var drop = _g('tv2-drop');
    if (drop) drop.classList.add('has-file');
    _clrErr('tv2-se');
}

function _bindEvents() {
    var ov = _g('topup-v2-ov')!;
    _g('tv2-close')!.addEventListener('click', _close);
    ov.addEventListener('click', function (e) {
        if (e.target === ov) _close();
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && ov && ov.style.display !== 'none') _close();
    });
    // quick amount buttons
    ov.addEventListener('click', function (e) {
        var btn = (e.target as HTMLElement).closest('.topup-v2-qamt');
        if (!btn) return;
        ov.querySelectorAll('.topup-v2-qamt').forEach(function (b) {
            b.classList.remove('active');
        });
        btn.classList.add('active');
        var inp = _g('tv2-amt') as HTMLInputElement | null;
        if (inp) {
            inp.value = (btn as HTMLElement).dataset.val as string;
            _clrErr('tv2-ae');
        }
    });
    var amtInp = _g('tv2-amt');
    if (amtInp)
        amtInp.addEventListener('input', function () {
            ov.querySelectorAll('.topup-v2-qamt').forEach(function (b) {
                b.classList.remove('active');
            });
            _clrErr('tv2-ae');
        });
    // copy
    var copyBtn = _g('tv2-copy');
    if (copyBtn)
        copyBtn.addEventListener('click', function () {
            if (!navigator.clipboard) return;
            navigator.clipboard.writeText('2300913684').then(function () {
                var orig = copyBtn!.textContent;
                copyBtn!.textContent = _bt('topup-copied');
                setTimeout(function () {
                    copyBtn!.textContent = orig;
                }, 1500);
            });
        });
    // drop zone
    var drop = _g('tv2-drop'),
        fi = _g('tv2-file') as HTMLInputElement | null;
    if (drop) {
        drop.addEventListener('click', function () {
            if (fi) fi.click();
        });
        drop.addEventListener('dragover', function (e) {
            e.preventDefault();
            drop!.classList.add('drag-over');
        });
        drop.addEventListener('dragleave', function () {
            drop!.classList.remove('drag-over');
        });
        drop.addEventListener('drop', function (e) {
            e.preventDefault();
            drop!.classList.remove('drag-over');
            var f = e.dataTransfer && e.dataTransfer.files[0];
            if (f) _setFile(f);
        });
    }
    if (fi)
        fi.addEventListener('change', function () {
            if (fi!.files![0]) _setFile(fi!.files![0]);
        });
    // back / next
    _g('tv2-back')!.addEventListener('click', function () {
        var n = _curStep();
        if (n <= 1) {
            _close();
            return;
        }
        _setStep(n - 1);
    });
    _g('tv2-next')!.addEventListener('click', function () {
        var n = _curStep();
        if (n === 1) _step1Next();
        else if (n === 2) _setStep(3);
        else _step3Submit();
    });
}

async function _step1Next() {
    var inp = _g('tv2-amt') as HTMLInputElement | null,
        amt = inp ? parseFloat(inp.value) : 0;
    if (!amt || amt < 10) {
        _showErr('tv2-ae', _bt('topup-amount-invalid'));
        return;
    }
    // v118.35.0.21 · 前端兜底:超过单次上限 ฿500,000 立即提示
    if (amt > 500000) {
        _showErr('tv2-ae', _bt('topup-amount-too-large'));
        return;
    }
    _amount = amt;
    var next = _g('tv2-next') as HTMLButtonElement | null;
    if (next) {
        next.disabled = true;
        next.textContent = '…';
    }
    try {
        var res = await fetch('/api/credits/topup/request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + _tok() },
            body: JSON.stringify({ amount_thb: amt }),
        });
        if (!res.ok) {
            // v118.35.0.21 · 422 raw pydantic ValidationError → 友好翻译
            var raw = await res.text();
            var msg = _bt('topup-submit-fail');
            try {
                var body = JSON.parse(raw);
                var d = body.detail;
                if (Array.isArray(d) && d.length) {
                    var typ = (d[0] && d[0].type) || '';
                    if (typ.indexOf('less_than') >= 0) msg = _bt('topup-amount-too-large');
                    else if (typ.indexOf('greater_than') >= 0) msg = _bt('topup-amount-invalid');
                    else if (typ.indexOf('parsing') >= 0) msg = _bt('topup-amount-invalid');
                } else if (typeof d === 'string') {
                    msg = d;
                }
            } catch (_) {}
            throw new Error(msg);
        }
        var data = await res.json();
        _reqId = data.request_id;
        _setStep(2);
    } catch (e) {
        _showErr('tv2-ae', (e as Error).message || _bt('topup-submit-fail'));
    } finally {
        if (next) {
            next.disabled = false;
            next.textContent = _bt('topup-btn-next');
        }
    }
}

async function _step3Submit() {
    var fi = _g('tv2-file') as HTMLInputElement | null;
    if (!fi || !fi.files || !fi.files[0]) {
        _showErr('tv2-se', _bt('topup-slip-required'));
        return;
    }
    var btn = _g('tv2-next') as HTMLButtonElement | null;
    if (btn) {
        btn.disabled = true;
        btn.textContent = '…';
    }
    try {
        var fd = new FormData();
        fd.append('file', fi.files![0]);
        var payer = _g('tv2-payer') as HTMLInputElement | null,
            note = _g('tv2-note') as HTMLInputElement | null;
        if (payer && payer.value.trim()) fd.append('payer_name', payer.value.trim());
        if (note && note.value.trim()) fd.append('note', note.value.trim());
        var res = await fetch('/api/credits/topup/upload-slip/' + _reqId, {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + _tok() },
            body: fd,
        });
        if (!res.ok) throw new Error(await res.text());
        var data = await res.json();
        if (data.auto_approved) {
            if (window.showToast) window.showToast(_bt('topup-auto-approved'), 'success');
            if (typeof window.loadDashboard === 'function') window.loadDashboard();
        } else {
            if (window.showToast) window.showToast(_bt('topup-pending'), 'info');
        }
        _close();
    } catch (e) {
        _showErr('tv2-ue', _bt('topup-upload-fail') + ' · ' + (e as Error).message);
        if (btn) {
            btn.disabled = false;
            btn.textContent = _bt('topup-btn-submit');
        }
    }
}

function _close() {
    var ov = _g('topup-v2-ov');
    if (ov) ov.style.display = 'none';
    if (typeof window.loadDashboard === 'function') window.loadDashboard();
}

window._openTopupModal = function () {
    _render();
    _reqId = null;
    _amount = 0;
    ['tv2-amt', 'tv2-payer', 'tv2-note'].forEach(function (id) {
        var e = _g(id) as HTMLInputElement | null;
        if (e) e.value = '';
    });
    var fi = _g('tv2-file') as HTMLInputElement | null;
    if (fi) fi.value = '';
    var drop = _g('tv2-drop');
    if (drop) drop.classList.remove('has-file', 'drag-over');
    _g('topup-v2-ov')!
        .querySelectorAll('.topup-v2-qamt')
        .forEach(function (b) {
            b.classList.remove('active');
        });
    ['tv2-ae', 'tv2-se', 'tv2-ue'].forEach(function (id) {
        _clrErr(id);
    });
    _applyText();
    _setStep(1);
    _g('topup-v2-ov')!.style.display = 'flex';
};

// 切语言时若 modal 开着,重新应用文字
if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('topup-v2', function () {
        var ov = _g('topup-v2-ov');
        if (ov && ov.style.display !== 'none' && ov.style.display !== '') {
            _applyText();
            _setStep(_curStep());
        }
    });
}
