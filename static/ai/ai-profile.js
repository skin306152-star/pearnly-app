/*
 * Pearnly AI · ai-profile.js · 税务画像卡/别名/义务清单/供应商过账档案视图编排
 *
 * 四块并发拉齐,只拉调用方要的那几块(见 opts.sections)——不像 intake/review/pkg 那样
 * 要求先有工单:客户建档后、开第一张工单前也该能填画像、加别名、挂供应商规则(税务画像
 * -方案-B1.md §2.1"宁多问不静默"),order 可能是 null,义务清单请求就不带 period(后端
 * 默认当期);供应商档案不挂工单,与 order 无关。
 *
 * 画像卡(画像卡设计稿 v1 · 智能判断版)手填即存,不再是一次性表单提交:每个字段独立
 * 触发 PUT(单字段 payload),推断候选(field_meta[key].proposal,GET 现算不落库)要点
 * "确认"才转正(POST .../tax-profile/confirm)。局部动作各自只重拉自己需要的那份数据:
 *   手填/确认某字段 → 刷新 profile + completeness,若响应带 added_obligations 再刷新
 *     obligations 并 toast「当期义务已重算」(routes/tax_profile_routes.py::put/confirm);
 *   加/停别名 → 只刷新 aliases;加/删供应商档案(Z3-b)→ 只刷新 supplierProfiles。
 *
 * container/sections(EN-clients · 2026-07-13 收口导航占位新增):原本硬绑
 * document.getElementById('cv-profile')——客户档案页(ai-client-archive.js)要把「画像+
 * 别名+义务」与「供应商过账档案」拆两个 tab 各自的容器复用同一份表单/面板 HTML + 保存/
 * 增删逻辑,不重抄一份,故把挂载点与要渲染的分区都改成调用方传参,不传时回落 ai-client.js
 * 的既有用法(cv-profile + 全四块)零改变。单例 S 假设同一时刻只有一处调用 mount()
 * (同 ai-pkg.js/ai-review.js 先例),客户独立页四视图切换与档案页 tab 切换都满足这一点。
 * 依赖 window.AI.state/api/format/profileRender/profileCardRender/profilePanelsRender/
 * supplierProfilesRender 与全局 at(),排在它们之后、ai-client.js 之前加载(见
 * scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var ALL_SECTIONS = ['form', 'alias', 'obligations', 'supplier'];

    var S = null;
    // 每个曾经挂载过的容器各记一次"已绑事件"(不是全局一次性锁)——客户独立页反复
    // 切回同一个 cv-profile 容器只绑一次,档案页的画像/供应商两个 tab 容器各自独立绑定。
    var wiredContainers = [];

    function body() {
        return S.container;
    }

    function has(section) {
        return S.sections.indexOf(section) >= 0;
    }

    function freshState(api, order, clientId, opts) {
        opts = opts || {};
        return {
            api: api,
            clientId: clientId,
            orderPeriod: order ? order.period : null,
            container: opts.container || $('cv-profile'),
            sections: opts.sections || ALL_SECTIONS,
            // 画像响应旁听钩子(EN-clients 档案页 0% CTA 用):收到 GET tax-profile 的完整
            // 响应(profile + completeness)时回调,免得调用方为同一份数据再发一次请求。
            onProfile: opts.onProfile || null,
            profile: null,
            completeness: 0,
            aliases: [],
            obligations: { period: null, rows: [] },
            savingField: null, // 正在保存的字段键(单字段 PUT 在途)
            confirmingFields: null, // 正在确认的字段键数组(POST confirm 在途)
            saveErrKey: null,
            aliasSubmitting: false,
            aliasErrKey: null,
            aliasRawValue: '',
            aliasKindValue: 'misc',
            aliasModeValue: 'exact',
            deactivatingId: null,
            supplierProfiles: [],
            spSubmitting: false,
            spErrKey: null,
            spTaxIdValue: '',
            spPaymentValue: '',
            spItemTypeValue: '',
            spDeletingTaxId: null,
        };
    }

    function readVal(id, fallback) {
        var el = $(id);
        return el ? el.value : fallback;
    }

    function ctx() {
        return {
            profile: S.profile,
            completeness: S.completeness,
            aliases: S.aliases,
            obligations: S.obligations,
            savingField: S.savingField,
            confirmingFields: S.confirmingFields,
            saveErrKey: S.saveErrKey,
            aliasSubmitting: S.aliasSubmitting,
            aliasErrKey: S.aliasErrKey,
            aliasRawValue: readVal('aliasRaw', S.aliasRawValue),
            aliasKindValue: readVal('aliasKind', S.aliasKindValue),
            aliasModeValue: readVal('aliasMode', S.aliasModeValue),
            deactivatingId: S.deactivatingId,
            supplierProfiles: S.supplierProfiles,
            spSubmitting: S.spSubmitting,
            spErrKey: S.spErrKey,
            spTaxIdValue: readVal('spTaxId', S.spTaxIdValue),
            spPaymentValue: readVal('spPayment', S.spPaymentValue),
            spItemTypeValue: readVal('spItemType', S.spItemTypeValue),
            spDeletingTaxId: S.spDeletingTaxId,
        };
    }

    function render() {
        var c = ctx();
        var html = '';
        if (has('form')) html += AI.profileCardRender.cardHtml(c);
        if (has('alias')) html += AI.profilePanelsRender.aliasPanelHtml(c);
        if (has('obligations')) html += AI.profilePanelsRender.obligationsPanelHtml(c);
        if (has('supplier')) html += AI.supplierProfilesRender.supplierProfilePanelHtml(c);
        body().innerHTML = html;
    }

    // ============ 拉数据 ============

    // 只发调用方要的那几块请求(archive 页画像 tab 不需要 supplierProfiles,供应商 tab
    // 不需要 profile/aliases/obligations)——不像客户独立页全量四块都要,避免多余往返。
    function loadAll() {
        body().innerHTML = AI.state.loadingHtml();
        var session = S;
        var tasks = [];
        if (has('form')) {
            tasks.push(
                S.api.getTaxProfile(S.clientId).then(function (r) {
                    if (S !== session) return;
                    S.profile = r.profile;
                    S.completeness = r.completeness;
                    if (S.onProfile) S.onProfile(r);
                })
            );
        }
        if (has('alias')) {
            tasks.push(
                S.api.listAliases(S.clientId).then(function (r) {
                    if (S === session) S.aliases = r.aliases || [];
                })
            );
        }
        if (has('obligations')) {
            tasks.push(
                S.api.listObligations(S.clientId, S.orderPeriod).then(function (r) {
                    if (S === session)
                        S.obligations = { period: r.period, rows: r.obligations || [] };
                })
            );
        }
        if (has('supplier')) {
            tasks.push(
                S.api.listSupplierProfiles(S.clientId).then(function (r) {
                    if (S === session) S.supplierProfiles = r.profiles || [];
                })
            );
        }
        Promise.all(tasks)
            .then(function () {
                if (S !== session) return;
                render();
            })
            .catch(function () {
                if (S !== session) return;
                body().innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body().querySelector('[data-action="retry"]');
                if (btn) btn.onclick = loadAll;
            });
    }

    // ============ 画像卡:手填即存 / 推断候选确认 / 冲突二选一 ============
    //
    // 不再是一次性表单提交——每个字段独立触发单字段 PUT,推断候选(field_meta[key]
    // .proposal,GET 现算不落库)要点"确认"才转正落库(POST .../tax-profile/confirm)。
    // 两条写路径(saveField/confirmFields)共用同一个"落库后刷新+提示"收尾
    // (afterProfileChange),不重复两遍收尾逻辑。

    var TOAST_MS = 3400;

    function showProfileToast(message) {
        var el = document.createElement('div');
        el.className = 'toast';
        el.id = 'pfToast';
        el.textContent = message;
        document.body.appendChild(el);
        requestAnimationFrame(function () {
            el.classList.add('on');
        });
        setTimeout(function () {
            if (el.parentNode) el.parentNode.removeChild(el);
        }, TOAST_MS);
    }

    // 把 added_obligations(纯义务码)配上刚刷新回来的义务清单行的 display_names 拼成
    // 一句提示——两处调用(手填/确认)都在 afterProfileChange 里收尾,不重复两遍。
    function announceAddedObligations(codes) {
        if (!codes || !codes.length) return;
        var byCode = {};
        (S.obligations.rows || []).forEach(function (r) {
            byCode[r.obligation_code] = r;
        });
        var lang = (window.AII18N && window.AII18N.lang) || 'zh';
        var names = codes
            .map(function (c) {
                var dn = byCode[c] && byCode[c].display_names;
                return (dn && (dn[lang] || dn.zh)) || c;
            })
            .join('、');
        showProfileToast(at('profile_toast_added').replace('{names}', names));
    }

    // 画像一变(手填/确认都走这里收尾):落库结果先渲染,义务清单刷新是锦上添花
    // (后端已重物化当期义务),失败不额外报错——画像本身已经保存成功,不能让这一步
    // 的失败看起来像保存失败了。
    function afterProfileChange(session, res) {
        if (S !== session) return;
        S.profile = res.profile;
        S.savingField = null;
        S.confirmingFields = null;
        render();
        var added = res.added_obligations || [];
        if (!has('obligations')) return;
        S.api
            .listObligations(S.clientId, S.orderPeriod)
            .then(function (obRes) {
                if (S !== session) return;
                S.obligations = { period: obRes.period, rows: obRes.obligations || [] };
                render();
                announceAddedObligations(added);
            })
            .catch(function () {});
    }

    function reportFieldError(err) {
        var key = AI.api.mapApiErrorKey(err && err.code);
        S.saveErrKey = at(key) !== key ? key : 'err_generic';
        render();
    }

    // 手填即存(select/checkbox 一选就发,int/money/text 失焦发)——单字段 PUT,source
    // 自动盖 'manual' 戳(services/workspace/tax_profile_store.py::upsert_profile)。
    function saveField(fieldKey, rawValue) {
        var field = AI.profileRender.fieldByKey(fieldKey);
        if (!field) return;
        var checked = AI.profileRender.validateFieldInput(field, rawValue);
        if (!checked.ok) {
            S.saveErrKey = checked.errKey;
            render();
            return;
        }
        var session = S;
        S.saveErrKey = null;
        S.savingField = fieldKey;
        render();
        var payload = {};
        payload[fieldKey] = checked.value;
        S.api
            .putTaxProfile(S.clientId, payload)
            .then(function (res) {
                afterProfileChange(session, res);
            })
            .catch(function (err) {
                if (S !== session) return;
                S.savingField = null;
                reportFieldError(err);
            });
    }

    // 推断候选转正(单个或"全部确认(N)")——后端用"这一刻重新现算"的候选核对,候选跟不上
    // 会诚实报 409(前端按通用错误提示处理,不专门拦这一种码)。
    function confirmFields(keys) {
        if (!keys || !keys.length) return;
        var session = S;
        S.saveErrKey = null;
        S.confirmingFields = keys;
        render();
        S.api
            .confirmTaxProfileFields(S.clientId, keys)
            .then(function (res) {
                afterProfileChange(session, res);
            })
            .catch(function (err) {
                if (S !== session) return;
                S.confirmingFields = null;
                reportFieldError(err);
            });
    }

    function confirmAll() {
        var pending = [];
        AI.profileRender.FIELD_META.forEach(function (m) {
            if (!AI.profileRender.isApplicable(m, S.profile)) return;
            var meta = (S.profile.field_meta || {})[m.key];
            var status = AI.profileRender.deriveFieldStatus(m, S.profile[m.key], meta);
            // 冲突字段需要人二选一,不进"全部确认"的批量转正(画像卡设计稿 v1 同款边界)。
            if (status === 'pending') pending.push(m.key);
        });
        confirmFields(pending);
    }

    // 冲突二选一:采纳推断走确认端点(source='inferred');保留手填 = 把当前已确认值
    // 原样再 PUT 一次(戳新的 confirmed_at)——若信号没变,下次刷新仍会诚实地再报一次
    // 冲突,不假装点一下就把真实分歧压下去了。
    function resolveConflictAccept(fieldKey) {
        confirmFields([fieldKey]);
    }
    function resolveConflictKeep(fieldKey) {
        saveField(fieldKey, S.profile[fieldKey]);
    }

    // SBT 无官方数据源确认过 → 交给管家(画像卡设计稿 v1 唯一一处 AI.steward.openWith
    // 入口)。客户名不在本模块状态里,预填句不带具体客户名(交付报告已记这条简化)。
    function openStewardCta() {
        if (window.AI && AI.steward && typeof AI.steward.openWith === 'function') {
            AI.steward.openWith(at('profile_sbt_cta_prefill'));
        }
    }

    // 别名(增/停)+ 供应商过账档案(Z3-b,增/删)编排拆在 ai-profile-panels-actions.js
    // (单文件<500 铁律——画像卡这一块已经把本文件撑过线);那份文件通过 _state()/_render()
    // 两个访问器读写这里的同一个 S/render,不是第二份状态。

    // ============ 事件接线(容器委托,只挂一次) ============

    function onClick(e) {
        var t = e.target;
        if (t.closest('[data-open-steward]')) return openStewardCta();
        var confirmBtn = t.closest('[data-confirm]');
        if (confirmBtn) return confirmFields([confirmBtn.getAttribute('data-confirm')]);
        var acceptBtn = t.closest('[data-conflict-accept]');
        if (acceptBtn) return resolveConflictAccept(acceptBtn.getAttribute('data-conflict-accept'));
        var keepBtn = t.closest('[data-conflict-keep]');
        if (keepBtn) return resolveConflictKeep(keepBtn.getAttribute('data-conflict-keep'));
        var el = t.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'profile-confirm-all') confirmAll();
        else if (a === 'alias-deactivate')
            AI.profilePanelsActions.deactivateAlias(Number(el.getAttribute('data-id')));
        else if (a === 'sp-delete')
            AI.profilePanelsActions.deleteSupplierProfile(el.getAttribute('data-tax'));
    }

    function onSubmit(e) {
        if (e.target && e.target.id === 'aliasForm') AI.profilePanelsActions.addAlias(e);
        else if (e.target && e.target.id === 'spForm')
            AI.profilePanelsActions.addSupplierProfile(e);
    }

    // 画像卡字段(id="pf-<key>")一变就单字段 PUT——native change 事件对 select/checkbox
    // 即时触发,对 text/number/money 输入框在失焦且值有变时触发,天然分了两种节奏,
    // 不需要额外挂 blur/focusout 监听。别的区(别名/供应商)控件 id 不带 pf- 前缀,原样忽略。
    function onFieldChange(e) {
        var id = e.target && e.target.id;
        var fieldKey = id && id.indexOf('pf-') === 0 ? id.slice(3) : null;
        if (!fieldKey) return;
        var field = AI.profileRender.fieldByKey(fieldKey);
        if (!field) return;
        saveField(fieldKey, field.kind === 'bool' ? e.target.checked : e.target.value);
    }

    function wireOnce(host) {
        if (wiredContainers.indexOf(host) >= 0) return;
        wiredContainers.push(host);
        host.addEventListener('click', onClick);
        host.addEventListener('submit', onSubmit);
        host.addEventListener('change', onFieldChange);
    }

    // opts.container(默认 cv-profile)/ opts.sections(默认四块全要)——见顶注。
    function mount(api, order, clientId, opts) {
        S = freshState(api, order, clientId, opts);
        wireOnce(S.container);
        loadAll();
    }

    window.AI = window.AI || {};
    window.AI.profile = {
        mount: mount,
        // 内部访问器,只给 ai-profile-panels-actions.js 读写同一个单例状态/触发重渲染——
        // 不是给别的模块用的公共 API(见该文件顶注)。
        _state: function () {
            return S;
        },
        _render: render,
    };
})();
