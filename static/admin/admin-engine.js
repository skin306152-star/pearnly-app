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
            '</span></label>'
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
        const modes = (options && options.modes) || ['direct35', 'economy', 'qwen', 'selfhost'];
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

    function _renderPolicy() {
        const host = document.getElementById('adm-eng-policy-body');
        if (!host) return;
        const planModes = (options && options.plan_modes) || ['direct35', 'economy'];
        const taskModes = (options && options.modes) || planModes.concat(['auto']);
        host.innerHTML =
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
            '</span></div><div id="adm-eng-tasks"></div>';
        _rowSelects(
            document.getElementById('adm-eng-plans'),
            PLANS,
            'adm-eng-plan-',
            'eng-plan-sel',
            planModes,
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
            taskModes,
            true,
            function (k) {
                return (policy.overrides_by_task || {})[k] || '';
            }
        );
        _renderAccounts();
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
            D.toast(_t('adm-eng-save-fail'), 'error');
        }
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

    async function _loadPolicy() {
        const host = document.getElementById('adm-eng-policy-body');
        if (!host) return;
        policy = null;
        _setBothStates('loading', _t('adm-eng-loading'), '');
        try {
            const d = await D.fetch('/api/admin/ocr-engine');
            policy = d.policy || {};
            options = d.options || {};
            accounts = _accountsFrom(policy);
            _renderPolicy();
            const saved = document.getElementById('adm-eng-saved');
            if (saved)
                saved.textContent = d.updated_at
                    ? _t('adm-set-saved-at') + ' ' + new Date(d.updated_at).toLocaleString()
                    : '';
        } catch (e) {
            _setBothStates('error', _t('adm-eng-load-fail'), 'policy');
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
            if (!row) return;
            const idx = Number(row.dataset.engAcct);
            if (e.target.classList.contains('eng-acct-email')) accounts[idx].email = e.target.value;
            else if (e.target.classList.contains('eng-acct-mode'))
                accounts[idx].mode = e.target.value;
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
        await _loadPolicy();
        if (window.AdminEngineCost) window.AdminEngineCost.render(deps);
    }

    window.AdminEngine = { render: render };
})();
