/*
 * Pearnly AI · ai-profile-panels-actions.js · 别名 + 供应商过账档案(Z3-b)增删编排
 *
 * 拆自 ai-profile.js(单文件<500 铁律——画像卡手填/确认/冲突/CTA 那一大块已经把原文件
 * 撑过线,别名+供应商这两块结构上自成一体,搬出来最省事)。共享状态仍是 ai-profile.js
 * 的单例 S(同一时刻只有一处调用 mount()),本文件不自己维护第二份状态,靠 AI.profile
 * 暴露的 _state()/_render() 两个访问器读写同一个对象——两次调用之间 S 可能被新的
 * mount() 换掉(客户独立页四视图切换),_state() 每次都取「当下这一个」,不缓存快照。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    function S() {
        return AI.profile._state();
    }
    function render() {
        AI.profile._render();
    }

    function readVal(id, fallback) {
        var el = $(id);
        return el ? el.value : fallback;
    }

    // ============ 别名 ============

    function addAlias(e) {
        if (e) e.preventDefault();
        var s = S();
        if (s.aliasSubmitting) return;
        var checked = AI.profilePanelsRender.validateAliasRaw(readVal('aliasRaw', ''));
        if (!checked.ok) {
            s.aliasErrKey = checked.errKey;
            render();
            return;
        }
        var kind = readVal('aliasKind', 'misc');
        var mode = readVal('aliasMode', 'exact');
        var session = s;
        s.aliasSubmitting = true;
        s.aliasErrKey = null;
        render();
        s.api
            .addAlias(s.clientId, { alias_raw: checked.value, alias_kind: kind, match_mode: mode })
            .then(function () {
                if (S() !== session) return;
                session.aliasRawValue = '';
                return session.api.listAliases(session.clientId);
            })
            .then(function (r) {
                if (S() !== session || !r) return;
                session.aliases = r.aliases || [];
                session.aliasSubmitting = false;
                render();
            })
            .catch(function (err) {
                if (S() !== session) return;
                session.aliasSubmitting = false;
                var key = AI.api.mapApiErrorKey(err && err.code);
                session.aliasErrKey = at(key) !== key ? key : 'err_generic';
                render();
            });
    }

    function deactivateAlias(aliasId) {
        var session = S();
        if (session.deactivatingId) return;
        session.deactivatingId = aliasId;
        render();
        session.api
            .deactivateAlias(session.clientId, aliasId)
            .then(function () {
                if (S() !== session) return;
                return session.api.listAliases(session.clientId);
            })
            .then(function (r) {
                if (S() !== session) return;
                session.aliases = (r && r.aliases) || [];
                session.deactivatingId = null;
                render();
            })
            .catch(function () {
                if (S() !== session) return;
                session.deactivatingId = null;
                render();
            });
    }

    // ============ 供应商过账档案(Z3-b) ============

    function addSupplierProfile(e) {
        if (e) e.preventDefault();
        var session = S();
        if (session.spSubmitting) return;
        var checked = AI.supplierProfilesRender.validateTaxIdRaw(readVal('spTaxId', ''));
        if (!checked.ok) {
            session.spErrKey = checked.errKey;
            render();
            return;
        }
        var UNSET = AI.supplierProfilesRender.UNSET;
        var payment = readVal('spPayment', UNSET);
        var itemType = readVal('spItemType', UNSET);
        if (payment === UNSET && itemType === UNSET) {
            session.spErrKey = 'err_sp_axis_required';
            render();
            return;
        }
        var body = {};
        if (payment !== UNSET) body.default_payment = payment;
        if (itemType !== UNSET) body.default_item_type = itemType;
        session.spSubmitting = true;
        session.spErrKey = null;
        render();
        session.api
            .putSupplierProfile(session.clientId, checked.value, body)
            .then(function () {
                if (S() !== session) return;
                session.spTaxIdValue = '';
                // readVal() 之后重渲染前优先读活 DOM 值(保留用户没提交那部分的在途输入),
                // 提交成功这条路必须连活元素一起清空,不然 ctx() 会把清空前的旧值读回来。
                var el = $('spTaxId');
                if (el) el.value = '';
                return session.api.listSupplierProfiles(session.clientId);
            })
            .then(function (r) {
                if (S() !== session || !r) return;
                session.supplierProfiles = r.profiles || [];
                session.spSubmitting = false;
                render();
            })
            .catch(function (err) {
                if (S() !== session) return;
                session.spSubmitting = false;
                var key = AI.api.mapApiErrorKey(err && err.code);
                session.spErrKey = at(key) !== key ? key : 'err_generic';
                render();
            });
    }

    function deleteSupplierProfile(taxId) {
        var session = S();
        if (session.spDeletingTaxId) return;
        if (!window.confirm(at('sp_delete_confirm'))) return;
        session.spDeletingTaxId = taxId;
        render();
        session.api
            .deleteSupplierProfile(session.clientId, taxId)
            .then(function () {
                if (S() !== session) return;
                return session.api.listSupplierProfiles(session.clientId);
            })
            .then(function (r) {
                if (S() !== session) return;
                session.supplierProfiles = (r && r.profiles) || [];
                session.spDeletingTaxId = null;
                render();
            })
            .catch(function () {
                if (S() !== session) return;
                session.spDeletingTaxId = null;
                render();
            });
    }

    window.AI = window.AI || {};
    window.AI.profilePanelsActions = {
        addAlias: addAlias,
        deactivateAlias: deactivateAlias,
        addSupplierProfile: addSupplierProfile,
        deleteSupplierProfile: deleteSupplierProfile,
    };
})();
