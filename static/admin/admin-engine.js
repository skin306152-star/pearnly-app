/*
 * Pearnly · admin-engine.js · 超管「OCR 引擎」页(/admin/engine)的策略区
 *
 * 这页回答两个问题:每个档位到底什么能力(卡片区),以及哪个入口在烧钱(成本区,
 * 见 admin-engine-cost.js)。老板拿它定价 —— 所以卡片上的数字必须是实测值,
 * 没测过的档就写「—」,不许拿别的档的数字凑一个好看的平均。
 *
 * 依赖由 admin.js 注入(共用同一份 token/i18n/toast),本文件不碰全局状态。
 * 语言切换时 admin.js 会整页重渲染,故账号灰度的未保存编辑存在模块状态里、
 * 从状态重画,不从 DOM 反读 —— 否则切一次语言,刚填的邮箱就没了。
 */
(function () {
    'use strict';

    const TIERS = [
        { mode: 'direct35', code: 'A' },
        { mode: 'economy', code: 'B' },
        { mode: 'qwen', code: 'C' },
        { mode: 'selfhost', code: 'D' },
    ];
    // 接口读不到时的档位兜底 —— 从卡片表派生,加档只改 TIERS 一处,不会出现「新档在卡片上
    // 有、在下拉里没了」的半截状态。
    const MODE_FALLBACK = TIERS.map(function (t) {
        return t.mode;
    });
    const METRIC_KEYS = ['cost', 'quality', 'speed'];
    const PLANS = ['none', 'S', 'M', 'L', 'exempt'];
    const TASKS = ['invoice', 'id_card', 'bank_statement', 'gl_ledger', 'vat_report'];

    let D = null; // {fetch, t, esc, fmt, toast}
    let policy = null;
    let options = null;
    let accounts = []; // [{email, mode}] · 编辑中的灰度名单(含未保存改动)
    let bound = false;

    function _t(k) {
        return D.t(k);
    }

    /** 缺翻译时回落原值:入口/单据枚举随后端加,前端漏配也得照实显示,不能空着。 */
    function _label(prefix, value) {
        if (!value) return '—';
        const key = prefix + value;
        const text = D.t(key);
        return text === key ? value : text;
    }

    function _stateBox(kind, message, retry) {
        const btn = retry
            ? '<button type="button" class="btn btn-sm" data-eng-retry="' +
              retry +
              '">' +
              D.esc(_t('adm-eng-retry')) +
              '</button>'
            : '';
        return (
            '<div class="eng-state eng-state-' +
            kind +
            '" data-eng-state="' +
            kind +
            '"><span class="eng-state-msg">' +
            D.esc(message) +
            '</span>' +
            btn +
            '</div>'
        );
    }

    // 三件套单一 owner:成本区(admin-engine-cost.js)与这里各有一份逐字拷贝,收拢到本文件,
    // cost 侧只做薄委托。依赖的 D 是 admin.js 注入的同一份 deps,谁先调用都拿得到同一批函数。
    window.AdminEngineShared = {
        t: _t,
        label: _label,
        stateBox: _stateBox,
    };

    function _modeSelect(cls, modes, withEmpty, current) {
        let html = '<select class="adm-eng-select ' + cls + '">';
        if (withEmpty)
            html += '<option value="">' + D.esc(_t('adm-eng-follow-global')) + '</option>';
        const opts = modes.slice();
        // 后端存了本页不认识的档(新加档 / 前端没同步)也必须出现在列表里,否则 select 渲染
        // 成空白,一按保存就被当「跟全局」静默抹掉 —— 银行钉档真这样丢过。
        if (current && opts.indexOf(current) === -1) opts.push(current);
        opts.forEach(function (m) {
            html +=
                '<option value="' +
                D.esc(m) +
                '"' +
                (m === current ? ' selected' : '') +
                '>' +
                D.esc(_label('adm-eng-opt-', m)) +
                '</option>';
        });
        return html + '</select>';
    }

    /** 能力未齐的档(后端 PARTIAL_MODES):只能按账号灰度,全局/套餐位后端会 400 挡回。 */
    function _isPartial(mode) {
        return ((options && options.partial_modes) || []).indexOf(mode) !== -1;
    }

    function _tierCard(tier) {
        const on = policy.mode === tier.mode;
        const metrics = METRIC_KEYS.map(function (k) {
            return (
                '<span class="eng-tier-metric"><span class="eng-tier-metric-k">' +
                D.esc(_t('adm-eng-tier-lab-' + k)) +
                '</span><span class="eng-tier-metric-v">' +
                D.esc(_t('adm-eng-tier-' + tier.mode + '-' + k)) +
                '</span></span>'
            );
        }).join('');
        return (
            '<label class="eng-tier' +
            (on ? ' is-on' : '') +
            '" data-eng-tier="' +
            tier.mode +
            '"><input type="radio" name="adm-eng-mode" value="' +
            tier.mode +
            '"' +
            (on ? ' checked' : '') +
            ' /><span class="eng-tier-head"><span class="eng-tier-code">' +
            tier.code +
            '</span><span class="eng-tier-name">' +
            D.esc(_t('adm-eng-tier-' + tier.mode + '-name')) +
            '</span>' +
            (on
                ? '<span class="eng-tier-live">' + D.esc(_t('adm-eng-tier-live')) + '</span>'
                : '') +
            '</span><code class="eng-tier-models">' +
            D.esc(_t('adm-eng-tier-' + tier.mode + '-models')) +
            '</code><span class="eng-tier-metrics">' +
            metrics +
            '</span><span class="eng-tier-note">' +
            D.esc(_t('adm-eng-tier-' + tier.mode + '-note')) +
            '</span>' +
            (_isPartial(tier.mode)
                ? '<span class="eng-tier-partial" data-eng-partial="' +
                  tier.mode +
                  '">' +
                  D.esc(_t('adm-eng-partial-note')) +
                  '</span>'
                : '') +
            '</label>'
        );
    }

    function _autoRow() {
        const on = policy.mode === 'auto';
        return (
            '<label class="eng-tier eng-tier-auto' +
            (on ? ' is-on' : '') +
            '" data-eng-tier="auto"><input type="radio" name="adm-eng-mode" value="auto"' +
            (on ? ' checked' : '') +
            ' /><span class="eng-tier-name">' +
            D.esc(_t('adm-eng-tier-auto-name')) +
            '</span><span class="eng-tier-note">' +
            D.esc(_t('adm-eng-tier-auto-note')) +
            '</span></label>'
        );
    }

    function _rowSelects(host, keys, labelPrefix, cls, modes, withEmpty, current) {
        host.innerHTML = keys
            .map(function (k) {
                return (
                    '<label class="adm-eng-row"><span class="adm-set-row-label">' +
                    D.esc(_t(labelPrefix + k)) +
                    '</span>' +
                    _modeSelect(cls, modes, withEmpty, current(k)) +
                    '</label>'
                );
            })
            .join('');
        host.querySelectorAll('select').forEach(function (sel, i) {
            sel.dataset.engKey = keys[i];
        });
    }

    function _renderAccounts() {
        const host = document.getElementById('adm-eng-accounts');
        if (!host) return;
        if (!accounts.length) {
            host.innerHTML = _stateBox('empty', _t('adm-eng-acct-empty'), '');
            return;
        }
        const modes = (options && options.modes) || MODE_FALLBACK;
        host.innerHTML = accounts
            .map(function (a, i) {
                return (
                    '<div class="eng-acct-row" data-eng-acct="' +
                    i +
                    '"><input class="eng-acct-email" type="email" autocomplete="off" value="' +
                    D.esc(a.email) +
                    '" placeholder="' +
                    D.esc(_t('adm-eng-acct-ph')) +
                    '" />' +
                    _modeSelect('eng-acct-mode', modes, false, a.mode) +
                    '<button type="button" class="btn btn-ghost btn-sm eng-acct-del" data-eng-acct-del="' +
                    i +
                    '">' +
                    D.esc(_t('adm-eng-acct-del')) +
                    '</button></div>'
                );
            })
            .join('');
    }

    /** 档位/套餐/任务三块的可读区 HTML(不含账号灰度)。dirty 时只刷这段,保住未保存的输入。 */
    function _policyBodyHtml() {
        const planModes = (options && options.plan_modes) || MODE_FALLBACK;
        const taskModes = (options && options.modes) || planModes.concat(['auto']);
        return (
            '<div class="eng-tier-grid" id="adm-eng-tiers">' +
            TIERS.map(_tierCard).join('') +
            '</div>' +
            _autoRow() +
            '<div class="eng-tier-foot">' +
            D.esc(_t('adm-eng-tier-foot')) +
            '</div>' +
            '<div class="cost-section-head eng-sub-head"><h3>' +
            D.esc(_t('adm-eng-plan-title')) +
            '</h3></div><div id="adm-eng-plans"></div>' +
            '<div class="cost-section-head eng-sub-head"><h3>' +
            D.esc(_t('adm-eng-task-title')) +
            '</h3><span class="cost-section-hint">' +
            D.esc(_t('adm-eng-task-hint')) +
            '</span></div><div id="adm-eng-tasks"></div>'
        );
    }

    function _renderPolicyRows() {
        _rowSelects(
            document.getElementById('adm-eng-plans'),
            PLANS,
            'adm-eng-plan-',
            'eng-plan-sel',
            (options && options.plan_modes) || MODE_FALLBACK,
            false,
            function (p) {
                return (policy.defaults_by_plan || {})[p] || policy.mode;
            }
        );
        _rowSelects(
            document.getElementById('adm-eng-tasks'),
            TASKS,
            'adm-eng-task-',
            'eng-task-sel',
            (options && options.modes) || MODE_FALLBACK.concat(['auto']),
            true,
            function (k) {
                return (policy.overrides_by_task || {})[k] || '';
            }
        );
    }

    /** 全量重画(档位 + 套餐 + 任务 + 账号灰度)。 */
    function _renderPolicy() {
        const host = document.getElementById('adm-eng-policy-body');
        if (!host) return;
        host.innerHTML = _policyBodyHtml();
        _renderPolicyRows();
        _renderAccounts();
    }

    /** 只刷档位/套餐/任务,账号灰度容器原样保留(未保存编辑不能被服务器快照冲掉)。 */
    function _renderPolicyBody() {
        const host = document.getElementById('adm-eng-policy-body');
        if (!host) return;
        host.innerHTML = _policyBodyHtml();
        _renderPolicyRows();
    }

    function _collect() {
        const mode = document.querySelector('input[name="adm-eng-mode"]:checked');
        const body = {
            mode: (mode && mode.value) || policy.mode,
            defaults_by_plan: {},
            overrides_by_task: {},
            // 后端「缺键 = 保留现值」,所以删除一行必须靠回传完整对象来表达。
            overrides_by_account: {},
        };
        document.querySelectorAll('#adm-eng-plans select').forEach(function (sel) {
            body.defaults_by_plan[sel.dataset.engKey] = sel.value || body.mode;
        });
        document.querySelectorAll('#adm-eng-tasks select').forEach(function (sel) {
            if (sel.value) body.overrides_by_task[sel.dataset.engKey] = sel.value;
        });
        for (let i = 0; i < accounts.length; i++) {
            const email = (accounts[i].email || '').trim().toLowerCase();
            if (!email) continue;
            if (email.indexOf('@') === -1) return { error: email };
            body.overrides_by_account[email] = accounts[i].mode;
        }
        return { body: body };
    }

    async function _save() {
        if (!policy) return; // 策略没读出来就保存 = 拿一份空白覆盖线上配置
        const collected = _collect();
        if (collected.error) {
            D.toast(_t('adm-eng-acct-bad') + ' ' + collected.error, 'error');
            return;
        }
        try {
            const r = await D.fetch('/api/admin/ocr-engine', {
                method: 'POST',
                body: collected.body,
            });
            policy = r.policy || collected.body;
            accounts = _accountsFrom(policy);
            _renderPolicy();
            D.toast(_t('adm-eng-saved-toast'), 'success');
        } catch (e) {
            D.toast(_saveErrorText(e), 'error');
        }
    }

    /** 后端挡回来的理由要看得见:只报「保存失败」的话,超管不知道是哪一格被拒、为什么。
     *  认识的错误码走译文,不认识的把原码接在后面(比藏起来强)。 */
    function _saveErrorText(e) {
        const detail = (e && e.detail) || '';
        if (!detail) return _t('adm-eng-save-fail');
        const code = detail.split(':')[0];
        const key = 'adm-eng-err-' + code.split('.').pop();
        const text = D.t(key);
        return text === key ? _t('adm-eng-save-fail') + ' · ' + detail : text;
    }

    function _accountsFrom(p) {
        const raw = (p && p.overrides_by_account) || {};
        return Object.keys(raw).map(function (email) {
            return { email: email, mode: raw[email] };
        });
    }

    /** 档位区与账号灰度区读的是同一个接口,状态必须同进同退,不许一半是数据一半是旧壳。 */
    function _setBothStates(kind, message, retry) {
        ['adm-eng-policy-body', 'adm-eng-accounts'].forEach(function (id, i) {
            const el = document.getElementById(id);
            if (el) el.innerHTML = _stateBox(kind, message, i === 0 ? retry : '');
        });
    }

    /** 账号灰度编辑态与服务器态是否不一致(有未保存改动)。语言切换/整页重渲染会重拉策略,
     *  不一致时必须保住输入区,不能拿服务器快照把没保存的邮箱/档位冲掉。 */
    function _accountsDirty(p) {
        const saved = _accountsFrom(p);
        if (accounts.length !== saved.length) return true;
        for (let i = 0; i < accounts.length; i++) {
            const a = accounts[i];
            const s = saved[i];
            if (!s) return true;
            if ((a.email || '').trim().toLowerCase() !== s.email || a.mode !== s.mode) return true;
        }
        return false;
    }

    async function _loadPolicy() {
        const host = document.getElementById('adm-eng-policy-body');
        if (!host) return;
        // 有未保存编辑时,账号灰度容器在请求期间也原样保留(loading 一盖,输入框就没了)。
        const keepAccounts = _accountsDirty(policy);
        policy = null;
        if (keepAccounts) {
            host.innerHTML = _stateBox('loading', _t('adm-eng-loading'), '');
        } else {
            _setBothStates('loading', _t('adm-eng-loading'), '');
        }
        try {
            const d = await D.fetch('/api/admin/ocr-engine');
            policy = d.policy || {};
            options = d.options || {};
            if (keepAccounts && _accountsDirty(policy)) {
                // 编辑还没落库:账号输入区不动,只刷档位/套餐/任务(语言切换就是走这条)。
                _renderPolicyBody();
            } else {
                accounts = _accountsFrom(policy);
                _renderPolicy();
            }
            const saved = document.getElementById('adm-eng-saved');
            if (saved)
                saved.textContent = d.updated_at
                    ? _t('adm-set-saved-at') + ' ' + new Date(d.updated_at).toLocaleString()
                    : '';
        } catch (e) {
            if (keepAccounts && _accountsDirty(policy)) {
                host.innerHTML = _stateBox('error', _t('adm-eng-load-fail'), 'policy');
            } else {
                _setBothStates('error', _t('adm-eng-load-fail'), 'policy');
            }
        }
    }

    function _bind() {
        if (bound) return;
        bound = true;
        const root = document.getElementById('page-admin-engine');
        if (!root) return;
        root.addEventListener('click', function (e) {
            const retry = e.target.closest('[data-eng-retry]');
            if (retry && retry.dataset.engRetry === 'policy') {
                _loadPolicy();
                return;
            }
            const del = e.target.closest('[data-eng-acct-del]');
            if (del) {
                accounts.splice(Number(del.dataset.engAcctDel), 1);
                _renderAccounts();
                return;
            }
            if (e.target.closest('#adm-eng-acct-add')) {
                accounts.push({ email: '', mode: policy ? policy.mode : 'economy' });
                _renderAccounts();
                const rows = document.querySelectorAll('.eng-acct-row .eng-acct-email');
                if (rows.length) rows[rows.length - 1].focus();
                return;
            }
            if (e.target.closest('#adm-eng-save')) _save();
        });
        root.addEventListener('change', function (e) {
            const tier = e.target.closest('.eng-tier');
            if (tier) {
                root.querySelectorAll('.eng-tier').forEach(function (el) {
                    el.classList.toggle('is-on', el === tier);
                });
            }
            const row = e.target.closest('.eng-acct-row');
            // 邮箱不在这儿收:input 监听已逐键写回,change 再写一遍是同一个值。
            if (row && e.target.classList.contains('eng-acct-mode'))
                accounts[Number(row.dataset.engAcct)].mode = e.target.value;
        });
        root.addEventListener('input', function (e) {
            const row = e.target.closest('.eng-acct-row');
            if (row && e.target.classList.contains('eng-acct-email'))
                accounts[Number(row.dataset.engAcct)].email = e.target.value;
        });
    }

    async function render(deps) {
        D = deps;
        _bind();
        // 成本区先发车再等策略:两块数据互不依赖,先 await 策略等于让成本区白等一次往返。
        if (window.AdminEngineCost) window.AdminEngineCost.render(deps);
        await _loadPolicy();
    }

    window.AdminEngine = { render: render };
})();
