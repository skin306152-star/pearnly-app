/* Pearnly DMS · 身份证向导 · 步骤3「全字段」表单渲染(4 分区:客户资料 + 三套地址)。
 * 拆自 dms-intake-confirm.js(单文件 <500 行铁律)· 移植自主站 dms-intake-confirm.ts 的
 * formView/section/field/select 一组纯渲染。footer 仍由 confirm 负责(比对/全字段两视图共用)。挂 window.DXFORM。 */
(function (root) {
    'use strict';
    var C = root.DXST;
    var S = C.S;
    var DX_SECTIONS = root.DXHTML.DX_SECTIONS;
    var esc = C.esc,
        existing = C.existing;
    function t(k) {
        return typeof root.t === 'function' ? root.t(k) : k;
    }

    // 四分区拼装(不含 footer)· confirm 的 renderConfirm 在其后接自己的 footerHtml。
    function sectionsHtml() {
        return DX_SECTIONS.map(sectionHtml).join('');
    }
    function sectionHtml(scn) {
        var open = S.openSec[scn.id] !== false;
        // 镜像开着 = 保存时本区被身份证地址整段覆盖。分区默认折叠,所以后果得写在恒可见的
        // 分区副标题上,不能只留一个开关(界面所见 = 实际所写)。
        var canMirror = !!(scn.addr && scn.sameAs);
        var mirrored = !!(canMirror && S.sameAs[scn.addr]);
        var tools = canMirror
            ? '<div class="dx-addr-tools"><span>' +
              esc(t('dx-same-addr')) +
              '</span><div class="dx-switch' +
              (S.sameAs[scn.addr] ? ' on' : '') +
              '" data-mirror="' +
              esc(scn.addr) +
              '"></div></div>'
            : '';
        var caret =
            '<div class="dx-fsec-caret"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg></div>';
        return (
            '<div class="dx-fsec' +
            (open ? ' open' : '') +
            '" data-sec="' +
            esc(scn.id) +
            '"><div class="dx-fsec-h"><div><b>' +
            esc(t(scn.title)) +
            '</b><div class="sub' +
            (mirrored ? ' mirror' : '') +
            '">' +
            esc(t(mirrored ? 'dx-same-addr-note' : scn.note)) +
            '</div></div><div class="dx-fsec-tools">' +
            tools +
            caret +
            '</div></div><div class="dx-fsec-body"><div class="dx-fgrid">' +
            scn.fields.map(fieldHtml).join('') +
            '</div></div></div>'
        );
    }
    function fieldHtml(f) {
        var v = S.form[f.key] != null ? S.form[f.key] : '';
        var full = f.key === 'name' ? ' full' : '';
        var control;
        if (f.type.indexOf('select-') === 0) {
            control = selectHtml(f, v);
        } else {
            var det = f.type === 'detected' ? ' detected' : '';
            var changed = existing() && C.isChanged(f.key) ? ' changed' : '';
            var ro = f.type === 'readonly' ? ' ro' : '';
            var roAttr = f.type === 'readonly' ? ' readonly' : '';
            control =
                '<input class="dx-in' +
                det +
                changed +
                ro +
                '" id="dx-f-' +
                esc(f.key) +
                '" data-fk="' +
                esc(f.key) +
                '" value="' +
                esc(v) +
                '"' +
                roAttr +
                '>';
        }
        return (
            '<div class="dx-field' +
            full +
            '"><label>' +
            esc(t(f.label)) +
            '</label>' +
            control +
            '</div>'
        );
    }
    function selectHtml(f, v) {
        var changed = existing() && C.isChanged(f.key) ? ' changed' : '';
        var opts;
        if (f.type === 'select-title') opts = S.prefixes;
        else if (f.type === 'select-province')
            opts = S.provinces.length ? S.provinces : C.currentOpt(f.key, v);
        else opts = C.currentOpt(f.key, v);
        var body = opts
            .map(function (o) {
                return (
                    '<option value="' +
                    esc(o[0]) +
                    '"' +
                    (String(o[0]) === String(v) ? ' selected' : '') +
                    '>' +
                    esc(o[1]) +
                    '</option>'
                );
            })
            .join('');
        return (
            '<select class="dx-sel' +
            changed +
            '" id="dx-f-' +
            esc(f.key) +
            '" data-fk="' +
            esc(f.key) +
            '" data-geo="' +
            esc(f.type) +
            '">' +
            body +
            '</select>'
        );
    }

    root.DXFORM = { sectionsHtml: sectionsHtml };
})(typeof self !== 'undefined' ? self : this);
