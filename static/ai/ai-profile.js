/*
 * Pearnly AI · ai-profile.js · 税务画像/别名/义务清单视图(B2-e)编排
 *
 * 三块一次拉齐(getTaxProfile + listAliases + listObligations 并发),不像 intake/review/pkg
 * 那样要求先有工单——客户建档后、开第一张工单前也该能填画像、加别名(税务画像-方案-B1.md
 * §2.1"宁多问不静默"),order 可能是 null,义务清单请求就不带 period(后端默认当期)。
 *
 * 三个局部动作各自只重拉自己需要的那份数据,不做整页 reload:
 *   保存画像 → 刷新 profile + obligations(画像变了,当期义务后端会重物化,见
 *     routes/tax_profile_routes.py::put_tax_profile);
 *   加/停别名 → 只刷新 aliases。
 *
 * 依赖 window.AI.state/api/format/profileRender/profilePanelsRender 与全局 at(),排在它们
 * 之后、ai-client.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;

    function body() {
        return $('cv-profile');
    }

    function freshState(api, order, clientId) {
        return {
            api: api,
            clientId: clientId,
            orderPeriod: order ? order.period : null,
            profile: null,
            aliases: [],
            obligations: { period: null, rows: [] },
            saving: false,
            saveErrKey: null,
            savedFlash: false,
            aliasSubmitting: false,
            aliasErrKey: null,
            aliasRawValue: '',
            aliasKindValue: 'misc',
            aliasModeValue: 'exact',
            deactivatingId: null,
        };
    }

    function readVal(id, fallback) {
        var el = $(id);
        return el ? el.value : fallback;
    }

    function ctx() {
        return {
            profile: S.profile,
            aliases: S.aliases,
            obligations: S.obligations,
            saving: S.saving,
            saveErrKey: S.saveErrKey,
            savedFlash: S.savedFlash,
            aliasSubmitting: S.aliasSubmitting,
            aliasErrKey: S.aliasErrKey,
            aliasRawValue: readVal('aliasRaw', S.aliasRawValue),
            aliasKindValue: readVal('aliasKind', S.aliasKindValue),
            aliasModeValue: readVal('aliasMode', S.aliasModeValue),
            deactivatingId: S.deactivatingId,
        };
    }

    function render() {
        var c = ctx();
        body().innerHTML =
            AI.profileRender.formHtml(c) +
            AI.profilePanelsRender.aliasPanelHtml(c) +
            AI.profilePanelsRender.obligationsPanelHtml(c);
    }

    // ============ 拉数据 ============

    function loadAll() {
        body().innerHTML = AI.state.loadingHtml();
        var session = S;
        Promise.all([
            S.api.getTaxProfile(S.clientId),
            S.api.listAliases(S.clientId),
            S.api.listObligations(S.clientId, S.orderPeriod),
        ])
            .then(function (r) {
                if (S !== session) return;
                S.profile = r[0].profile;
                S.aliases = r[1].aliases || [];
                S.obligations = { period: r[2].period, rows: r[2].obligations || [] };
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

    // ============ 画像保存 ============

    function readProfileForm() {
        var raw = {};
        AI.profileRender.FIELD_DEFS.forEach(function (f) {
            var el = $('pf-' + f.key);
            if (!el) return; // showIf 隐藏时不在 DOM——不传,保留 draft 里的既有值
            raw[f.key] = f.kind === 'bool' ? el.checked : el.value;
        });
        return raw;
    }

    // 三个"影响其它行显隐"的字段一变(勾多分支/授权 Tax Agent/切 SBT 登记态),就把当前
    // 表单已敲的全部值合进草稿重渲染——不然 branch_count/tax_agent_ref/sbt_business_type
    // 永远不会在用户操作的这一刻冒出来(showIf 读的是草稿,不重渲染就看不到新增的行)。
    function onFormChange(e) {
        var id = e.target && e.target.id;
        var field = id && id.indexOf('pf-') === 0 ? id.slice(3) : null;
        if (!field || AI.profileRender.VISIBILITY_FIELDS.indexOf(field) < 0) return;
        S.profile = Object.assign({}, S.profile, readProfileForm());
        render();
    }

    function saveProfile(e) {
        if (e) e.preventDefault();
        if (S.saving) return;
        var built = AI.profileRender.buildProfilePayload(readProfileForm());
        if (!built.ok) {
            S.saveErrKey = built.errKey;
            S.savedFlash = false;
            render();
            return;
        }
        var session = S;
        S.saving = true;
        S.saveErrKey = null;
        S.savedFlash = false;
        render();
        S.api
            .putTaxProfile(S.clientId, built.payload)
            .then(function (res) {
                if (S !== session) return;
                S.profile = res.profile;
                S.saving = false;
                S.savedFlash = true;
                render();
                // 义务清单刷新是锦上添花(后端保存时已重物化当期义务),失败不额外报错——
                // 画像本身已经保存成功,不能让这一步的失败看起来像保存失败了。
                S.api
                    .listObligations(S.clientId, S.orderPeriod)
                    .then(function (obRes) {
                        if (S !== session) return;
                        S.obligations = { period: obRes.period, rows: obRes.obligations || [] };
                        render();
                    })
                    .catch(function () {});
            })
            .catch(function (err) {
                if (S !== session) return;
                S.saving = false;
                var key = AI.api.mapApiErrorKey(err && err.code);
                S.saveErrKey = at(key) !== key ? key : 'err_generic';
                render();
            });
    }

    // ============ 别名 ============

    function addAlias(e) {
        if (e) e.preventDefault();
        if (S.aliasSubmitting) return;
        var checked = AI.profilePanelsRender.validateAliasRaw(readVal('aliasRaw', ''));
        if (!checked.ok) {
            S.aliasErrKey = checked.errKey;
            render();
            return;
        }
        var kind = readVal('aliasKind', 'misc');
        var mode = readVal('aliasMode', 'exact');
        var session = S;
        S.aliasSubmitting = true;
        S.aliasErrKey = null;
        render();
        S.api
            .addAlias(S.clientId, { alias_raw: checked.value, alias_kind: kind, match_mode: mode })
            .then(function () {
                if (S !== session) return;
                S.aliasRawValue = '';
                return S.api.listAliases(S.clientId);
            })
            .then(function (r) {
                if (S !== session || !r) return;
                S.aliases = r.aliases || [];
                S.aliasSubmitting = false;
                render();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.aliasSubmitting = false;
                var key = AI.api.mapApiErrorKey(err && err.code);
                S.aliasErrKey = at(key) !== key ? key : 'err_generic';
                render();
            });
    }

    function deactivateAlias(aliasId) {
        if (S.deactivatingId) return;
        var session = S;
        S.deactivatingId = aliasId;
        render();
        S.api
            .deactivateAlias(S.clientId, aliasId)
            .then(function () {
                if (S !== session) return;
                return S.api.listAliases(S.clientId);
            })
            .then(function (r) {
                if (S !== session) return;
                S.aliases = (r && r.aliases) || [];
                S.deactivatingId = null;
                render();
            })
            .catch(function () {
                if (S !== session) return;
                S.deactivatingId = null;
                render();
            });
    }

    // ============ 事件接线(容器委托,只挂一次) ============

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'alias-deactivate') deactivateAlias(Number(el.getAttribute('data-id')));
    }

    function onSubmit(e) {
        if (e.target && e.target.id === 'profileForm') saveProfile(e);
        else if (e.target && e.target.id === 'aliasForm') addAlias(e);
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        var host = body();
        host.addEventListener('click', onClick);
        host.addEventListener('submit', onSubmit);
        host.addEventListener('change', onFormChange);
    }

    function mount(api, order, clientId) {
        S = freshState(api, order, clientId);
        wireOnce();
        loadAll();
    }

    window.AI = window.AI || {};
    window.AI.profile = { mount: mount };
})();
