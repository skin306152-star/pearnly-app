/* Pearnly DMS · 身份证向导 · 共享状态 S + 取值模型(单一数据源驱动比对/全字段/推送)。
 * 移植自主站 src/home/dms-intake-core.ts(identity 分支)· 控制器 dms-intake.js · 确认页
 * dms-intake-confirm.js。挂 window.DXST。 */
(function (root) {
    'use strict';
    var DX_COMPARE = root.DXHTML.DX_COMPARE;

    var S = {
        step: 1,
        file: null,
        ocr: null,
        scenario: 'none',
        candidates: [],
        selectedId: null,
        geo: {},
        prefixes: [],
        provinces: [],
        newVals: {},
        dmsVals: {},
        pick: {},
        prefixUnmappable: false,
        form: {},
        sameAs: { _ct: true, _sd: true },
        decision: 'update',
        tab: 'difference',
        busy: false,
        openSec: { cust: true, addr_id: true, addr_ct: false, addr_sd: false },
    };

    var ID_KEYS = ['prefix_id', 'name', 'people_id', 'tax_id', 'birthday_be'];
    // 地址全字段(含楼/层/室/村庄)· 表单可编辑的都进 payload,否则手改后发不出去。
    var ADDR_KEYS = [
        'house_no',
        'building',
        'floor',
        'room',
        'village',
        'moo',
        'soi',
        'road',
        'province_id',
        'district_id',
        'subdistrict_id',
        'zipcode_id',
    ];

    function esc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(String(s == null ? '' : s))
            : String(s == null ? '' : s);
    }
    function lang() {
        return (root.DXI18N && root.DXI18N.lang) || 'th';
    }
    function sec() {
        return document.getElementById('page-dms-intake');
    }
    function $(id) {
        return document.getElementById(id);
    }
    function authHeaders(json) {
        var tk = '';
        try {
            tk = localStorage.getItem('mrpilot_token') || '';
        } catch (e) {
            tk = '';
        }
        var h = { Authorization: 'Bearer ' + tk };
        if (json) h['Content-Type'] = 'application/json';
        return h;
    }
    function norm(s) {
        return (s || '').replace(/\s+/g, ' ').trim();
    }
    function existing() {
        return S.scenario !== 'none';
    }

    function showStep(step, stateId) {
        S.step = step;
        var el = sec();
        if (el)
            el.querySelectorAll('.dx-state').forEach(function (s) {
                s.classList.remove('active');
            });
        var target = $(stateId);
        if (target) target.classList.add('active');
        var stepper = el && el.querySelector('.dx-stepper');
        if (stepper) stepper.setAttribute('data-frac', step + ' / 4');
        if (el)
            el.querySelectorAll('.dx-step').forEach(function (node, i) {
                var n = i + 1;
                node.classList.toggle('active', n === step);
                node.classList.toggle('done', n < step);
                var no = node.querySelector('.dx-step-no');
                if (no) no.textContent = n < step ? '✓' : String(n);
            });
    }

    function geoLabel(list, id) {
        var hit = (list || []).find(function (o) {
            return String(o[0]) === String(id);
        });
        return (hit && hit[1]) || '';
    }

    // ── OCR → 新值 ──
    function buildNewVals() {
        var ic = S.ocr || {};
        var addr = (S.ocr || {}).address || {};
        var sel = S.geo.selected || {};
        var txt = S.geo.text || {};
        // 称谓:精确匹配 DMS 称谓主档,匹配不到留空(不回落第一项,否则称谓写错且永远显差异)。
        var hit = S.prefixes.find(function (p) {
            return p[1] === ic.prefix_name;
        });
        S.prefixUnmappable = !!ic.prefix_name && !hit;
        S.newVals = {
            prefix_id: hit ? hit[0] : '',
            prefix_name: ic.prefix_name || '',
            name: ic.name || '',
            people_id: ic.people_id || '',
            tax_id: ic.people_id || '',
            birthday_be: ic.birthday_be || '',
            phone: '',
            house_no: txt.house_no || addr.house_no || '',
            building: '',
            floor: '',
            room: '',
            village: '',
            moo: txt.moo || addr.moo || '',
            soi: txt.soi || addr.soi || '',
            road: txt.road || addr.road || '',
            province_id: sel.province_id || '',
            district_id: sel.district_id || '',
            subdistrict_id: sel.subdistrict_id || '',
            zipcode_id: sel.zipcode_id || '',
            province_name: geoLabel(S.geo.provinces, sel.province_id) || addr.province || '',
            district_name: geoLabel(S.geo.districts, sel.district_id) || addr.district || '',
            subdistrict_name:
                geoLabel(S.geo.subdistricts, sel.subdistrict_id) || addr.subdistrict || '',
            zipcode_name: geoLabel(S.geo.zipcodes, sel.zipcode_id) || addr.zipcode || '',
        };
    }

    // ── 取值模型 ──
    function initForm() {
        S.form = {};
        S.pick = {};
        DX_COMPARE.forEach(function (c) {
            var nv = S.newVals[c.key] || '';
            var dv = dmsCompareVal(c.key);
            var same = norm(nv) === norm(dv);
            S.pick[c.key] = !existing() ? 'new' : same || !nv ? 'dms' : 'new';
        });
        var base = existing() ? Object.assign({}, S.dmsVals) : {};
        if (!existing()) Object.assign(base, ocrFormDefaults());
        S.form = base;
        applyDecisionToForm();
        syncMirror();
    }
    function ocrFormDefaults() {
        var o = {};
        ID_KEYS.forEach(function (k) {
            o[k] = S.newVals[k] || '';
        });
        ADDR_KEYS.forEach(function (k) {
            o[k] = S.newVals[k] || '';
        });
        o.tax_id = S.newVals.tax_id || '';
        return o;
    }
    // 地址写库 id 字段 → 比对行 pick 键。house_no/moo/soi/road 自身即写库键;
    // building/floor/room/village 无身份证来源、无比对行 → 保留 DMS 原值。
    var ADDR_PICK = {
        house_no: 'house_no',
        moo: 'moo',
        soi: 'soi',
        road: 'road',
        province_id: 'province_name',
        district_id: 'district_name',
        subdistrict_id: 'subdistrict_name',
        zipcode_id: 'zipcode_name',
    };
    function applyDecisionToForm() {
        if (!existing()) return;
        var useNew = function (picked) {
            return S.decision === 'overwrite' || picked === 'new';
        };
        ID_KEYS.concat(['tax_id']).forEach(function (k) {
            var cmpKey = k === 'prefix_id' ? 'prefix_name' : k;
            var picked = S.pick[cmpKey] || 'dms';
            S.form[k] = useNew(picked) && S.newVals[k] ? S.newVals[k] : S.dmsVals[k] || '';
        });
        ADDR_KEYS.forEach(function (k) {
            var pk = ADDR_PICK[k];
            var picked = (pk && S.pick[pk]) || 'dms';
            S.form[k] = useNew(picked) && S.newVals[k] ? S.newVals[k] : S.dmsVals[k] || '';
        });
        ['province', 'district', 'subdistrict', 'zipcode'].forEach(function (b) {
            var nameKey = b + '_name';
            var picked = S.pick[nameKey] || 'dms';
            S.form[nameKey] =
                useNew(picked) && S.newVals[nameKey]
                    ? S.newVals[nameKey]
                    : S.dmsVals[nameKey] || '';
        });
    }
    function syncMirror() {
        ['_ct', '_sd'].forEach(function (sfx) {
            if (S.sameAs[sfx])
                ADDR_KEYS.forEach(function (k) {
                    S.form[k + sfx] = S.form[k] || '';
                });
        });
    }
    function dmsCompareVal(key) {
        if (key === 'prefix_name') return prefixLabel(S.dmsVals.prefix_id || '');
        return S.dmsVals[key] || '';
    }
    function newCompareVal(key) {
        return S.newVals[key] || '';
    }
    function prefixLabel(id) {
        return (
            (S.prefixes.find(function (p) {
                return p[0] === id;
            }) || ['', ''])[1] || ''
        );
    }
    function isChanged(key) {
        var dv = S.dmsVals[key] || '';
        return !!S.form[key] && norm(S.form[key]) !== norm(dv);
    }
    function diffNewCount() {
        return DX_COMPARE.filter(function (c) {
            return (
                norm(newCompareVal(c.key)) !== norm(dmsCompareVal(c.key)) &&
                S.pick[c.key] === 'new' &&
                newCompareVal(c.key)
            );
        }).length;
    }
    function currentOpt(key, v) {
        if (!v) return [];
        var labelKey = key
            .replace('province_id', 'province_name')
            .replace('district_id', 'district_name')
            .replace('subdistrict_id', 'subdistrict_name')
            .replace('zipcode_id', 'zipcode_name');
        var label = S.form[labelKey] || S.dmsVals[labelKey] || S.newVals[labelKey] || v;
        return [[v, label]];
    }
    function syncFormFromDom() {
        var el = sec();
        if (el)
            el.querySelectorAll('#dx-s-confirm [data-fk]').forEach(function (inp) {
                S.form[inp.dataset.fk] = inp.value;
            });
        syncMirror();
    }
    function buildPayload() {
        syncFormFromDom();
        var idKeys = [
            'prefix_id',
            'name',
            'people_id',
            'tax_id',
            'birthday_be',
            'phone',
            'tel_work',
            'tel_home',
            'email',
            'line_id',
            'facebook',
            'credit_day',
        ];
        var fields = {};
        idKeys.forEach(function (k) {
            if (S.form[k] != null) fields[k] = S.form[k];
        });
        fields.people_id = S.form.people_id || S.newVals.people_id || '';
        fields.name = S.form.name || S.newVals.name || '';
        var block = function (sfx) {
            var o = {};
            ADDR_KEYS.forEach(function (k) {
                o[k] = S.form[k + sfx] != null ? S.form[k + sfx] : '';
            });
            return o;
        };
        return {
            fields: fields,
            addresses: { '': block(''), _ct: block('_ct'), _sd: block('_sd') },
        };
    }

    root.DXST = {
        S: S,
        ID_KEYS: ID_KEYS,
        ADDR_KEYS: ADDR_KEYS,
        esc: esc,
        lang: lang,
        sec: sec,
        $: $,
        authHeaders: authHeaders,
        norm: norm,
        existing: existing,
        showStep: showStep,
        buildNewVals: buildNewVals,
        initForm: initForm,
        applyDecisionToForm: applyDecisionToForm,
        syncMirror: syncMirror,
        dmsCompareVal: dmsCompareVal,
        newCompareVal: newCompareVal,
        prefixLabel: prefixLabel,
        isChanged: isChanged,
        diffNewCount: diffNewCount,
        currentOpt: currentOpt,
        syncFormFromDom: syncFormFromDom,
        buildPayload: buildPayload,
    };
})(typeof self !== 'undefined' ? self : this);
