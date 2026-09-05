/*
 * Pearnly · admin-engine.js · 超管「OCR 引擎」页(/admin/engine)的策略区
 *
 * 这页回答两个问题:每个档位到底什么能力(卡片区),以及哪个入口在烧钱(成本区,
 * 见 admin-engine-cost.js)。老板拿它定价 —— 所以卡片上的数字必须是实测值,
 * 没测过的档就写「—」,不许拿别的档的数字凑一个好看的平均。
 *
 * 依赖由 admin.js 注入(共用同一份 token/i18n/toast),本文件不碰全局状态。
 */
(function () {
    'use strict';

    const TIERS = [
        { mode: 'enterprise', code: 'A' },
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
    const TASKS = [
        'invoice',
        'id_card',
        'bank_statement',
        'gl_ledger',
        'vat_report',
        'vat_report_csv',
        'salesvat',
        'fileconv_ocr',
    ];

    let D = null; // {fetch, t, esc, fmt, toast}
    let policy = null;
    let options = null;
    let runtime = null;
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
                (_isPartial(m) ? ' disabled' : '') +
                '>' +
                D.esc(_label('adm-eng-opt-', m)) +
                '</option>';
        });
        return html + '</select>';
    }

    /** 能力未齐的档(后端 PARTIAL_MODES):暂不可启用为任何档位,写侧后端会 400 挡回。 */
    function _isPartial(mode) {
        return ((options && options.partial_modes) || []).indexOf(mode) !== -1;
    }

    function _tierCard(tier) {
        const on = policy.mode === tier.mode;
        const facts = (runtime && runtime.tiers && runtime.tiers[tier.mode]) || {};
        const models = Object.entries(facts.models || {}).map(function (entry) {
            const m = entry[1];
            return (
                entry[0] +
                ': ' +
                m.model +
                ' / ' +
                m.backend +
                (m.location ? ' @' + m.location : '') +
                (m.thinking ? ' ' + m.thinking : '')
            );
        });
        if (facts.document_ocr) models.unshift('Document AI: ' + facts.document_ocr.version);
        const metrics = METRIC_KEYS.map(function (k) {
            return (
                '<span class="eng-tier-metric"><span class="eng-tier-metric-k">' +
                D.esc(_t('adm-eng-tier-lab-' + k)) +
                '</span><span class="eng-tier-metric-v">' +
                D.esc((facts.metrics && facts.metrics[k]) || '—') +
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
            (_isPartial(tier.mode) ? ' disabled' : '') +
            ' /><span class="eng-tier-head"><span class="eng-tier-code">' +
            tier.code +
            '</span><span class="eng-tier-name">' +
            D.esc(_t('adm-eng-tier-' + tier.mode + '-name')) +
            '</span>' +
            (on
                ? '<span class="eng-tier-live">' + D.esc(_t('adm-eng-tier-live')) + '</span>'
                : '') +
            '</span><code class="eng-tier-models">' +
            D.esc(models.join(' · ') || '—') +
            '</code><span class="eng-tier-metrics">' +
            metrics +
            '</span><span class="eng-tier-note">' +
            D.esc(_t('adm-eng-runtime-note')) +
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
                    (cls === 'eng-task-sel' && runtime && runtime.task_modes
                        ? '<small>' +
                          D.esc(
                              _t('adm-eng-effective') +
                                  ' ' +
                                  _label('adm-eng-opt-', runtime.task_modes[k])
                          ) +
                          '</small>'
                        : '') +
                    '</label>'
                );
            })
            .join('');
        host.querySelectorAll('select').forEach(function (sel, i) {
            sel.dataset.engKey = keys[i];
        });
    }

    /** 档位/套餐/任务三块的可读区 HTML。 */
    function _policyBodyHtml() {
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
            (options && options.tasks) || TASKS,
            'adm-eng-task-',
            'eng-task-sel',
            (options && options.modes) || MODE_FALLBACK.concat(['auto']),
            true,
            function (k) {
                return (policy.overrides_by_task || {})[k] || '';
            }
        );
    }

    function _renderPolicy() {
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
        };
        document.querySelectorAll('#adm-eng-plans select').forEach(function (sel) {
            body.defaults_by_plan[sel.dataset.engKey] = sel.value || body.mode;
        });
        document.querySelectorAll('#adm-eng-tasks select').forEach(function (sel) {
            if (sel.value) body.overrides_by_task[sel.dataset.engKey] = sel.value;
        });
        return body;
    }

    async function _save() {
        if (!policy) return; // 策略没读出来就保存 = 拿一份空白覆盖线上配置
        const body = _collect();
        try {
            const r = await D.fetch('/api/admin/ocr-engine', { method: 'POST', body: body });
            policy = r.policy || body;
            await _loadPolicy();
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

    async function _loadPolicy() {
        const host = document.getElementById('adm-eng-policy-body');
        if (!host) return;
        policy = null;
        host.innerHTML = _stateBox('loading', _t('adm-eng-loading'), '');
        try {
            const d = await D.fetch('/api/admin/ocr-engine');
            policy = d.policy || {};
            options = d.options || {};
            runtime = d.runtime || null;
            _renderPolicy();
            const saved = document.getElementById('adm-eng-saved');
            if (saved)
                saved.textContent = d.updated_at
                    ? _t('adm-set-saved-at') + ' ' + window._adminDate(d.updated_at, true)
                    : '';
        } catch {
            host.innerHTML = _stateBox('error', _t('adm-eng-load-fail'), 'policy');
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
            if (e.target.closest('#adm-eng-save')) _save();
        });
        root.addEventListener('change', function (e) {
            const tier = e.target.closest('.eng-tier');
            if (tier) {
                root.querySelectorAll('.eng-tier').forEach(function (el) {
                    el.classList.toggle('is-on', el === tier);
                });
            }
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
