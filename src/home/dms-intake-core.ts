// ============================================================
// 录入工作台 · 共享状态 S + 取值模型(单一数据源驱动比对/全字段/推送)
// 控制器 dms-intake.ts(步骤1-2+事件)· 资料确认 dms-intake-confirm.ts(步骤3-4)。
// ============================================================
/* global escapeHtml, token */
import { DX_COMPARE } from './dms-intake-html.js';

export type Dict = Record<string, string>;
export interface Cand {
    customer_id: string;
    cuscode?: string;
    name?: string;
    people_id?: string;
    score?: number;
}

export const S = {
    step: 1,
    file: null as File | null,
    ocr: null as Dict | null,
    scenario: 'none' as 'exact' | 'similar' | 'none',
    candidates: [] as Cand[],
    selectedId: null as string | null,
    geo: {} as Record<string, unknown>,
    prefixes: [] as Array<[string, string]>,
    provinces: [] as Array<[string, string]>,
    newVals: {} as Dict,
    dmsVals: {} as Dict,
    pick: {} as Record<string, 'new' | 'dms'>,
    prefixUnmappable: false,
    form: {} as Dict,
    sameAs: { _ct: true, _sd: true } as Record<string, boolean>,
    decision: 'update' as 'update' | 'overwrite',
    tab: 'difference' as 'difference' | 'allfields',
    busy: false,
};

export const ID_KEYS = ['prefix_id', 'name', 'people_id', 'tax_id', 'birthday_be'];
// 地址全字段(含楼/层/室/村庄)· 表单可编辑的都要进 payload,否则手动改了发不出去
export const ADDR_KEYS = [
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

export function esc(s: unknown) {
    return typeof escapeHtml === 'function' ? escapeHtml(String(s ?? '')) : String(s ?? '');
}
export function lang() {
    return window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
}
export function sec(): HTMLElement | null {
    return document.getElementById('page-dms-intake');
}
export function $(id: string) {
    return document.getElementById(id);
}
export function authHeaders(json = false): Record<string, string> {
    const h: Record<string, string> = { Authorization: 'Bearer ' + token };
    if (json) h['Content-Type'] = 'application/json';
    return h;
}
export function norm(s: string) {
    return (s || '').replace(/\s+/g, ' ').trim();
}
export function existing() {
    return S.scenario !== 'none';
}

export function showStep(step: number, stateId: string) {
    S.step = step;
    sec()
        ?.querySelectorAll('.dx-state')
        .forEach((s) => s.classList.remove('active'));
    $(stateId)?.classList.add('active');
    sec()
        ?.querySelectorAll('.dx-step')
        .forEach((el, i) => {
            const n = i + 1;
            el.classList.toggle('active', n === step);
            el.classList.toggle('done', n < step);
            const no = el.querySelector('.dx-step-no');
            if (no) no.textContent = n < step ? '✓' : String(n);
        });
}

// 从级联选项 [[id,label]] 里按选中 id 取 label
function geoLabel(list: unknown, id: string): string {
    return (
        ((list as Array<[string, string]>) || []).find((o) => String(o[0]) === String(id))?.[1] ||
        ''
    );
}

// ── OCR → 新值 ────────────────────────────────────────────────
export function buildNewVals() {
    const ic = (S.ocr || {}) as Dict;
    const addr = ((S.ocr || {}).address || {}) as unknown as Dict;
    const sel = ((S.geo.selected as Dict) || {}) as Dict;
    const txt = ((S.geo.text as Dict) || {}) as Dict;
    // 称谓:身份证已归一全称(后端)· 在 DMS 称谓主档里精确匹配;匹配不到 → 留空,
    // 决不回落到第一项(否则把 น.ส. 客户写成 นาย 且永远显差异)。prefixUnmappable 透出给比对标注。
    const hit = S.prefixes.find((p) => p[1] === ic.prefix_name);
    S.prefixUnmappable = !!ic.prefix_name && !hit;
    // 地址下拉标签优先取级联结果(与 DMS 写库口径一致)· 回落 OCR 文本。
    // 邮编身份证常缺印 → 必须从级联补,否则地址串缺邮编恒显差异。
    S.newVals = {
        prefix_id: hit ? hit[0] : '',
        prefix_name: ic.prefix_name || '',
        name: ic.name || '',
        people_id: ic.people_id || '',
        tax_id: ic.people_id || '',
        birthday_be: ic.birthday_be || '',
        phone: '',
        house_no: txt.house_no || addr.house_no || '',
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

// ── 取值模型 ──────────────────────────────────────────────────
export function initForm() {
    S.form = {};
    S.pick = {};
    DX_COMPARE.forEach((c) => {
        const nv = S.newVals[c.key] || '';
        const dv = dmsCompareVal(c.key);
        const same = norm(nv) === norm(dv);
        S.pick[c.key] = !existing() ? 'new' : same || !nv ? 'dms' : 'new';
    });
    const base: Dict = existing() ? { ...S.dmsVals } : {};
    if (!existing()) Object.assign(base, ocrFormDefaults());
    S.form = base;
    applyDecisionToForm();
    syncMirror();
}
function ocrFormDefaults(): Dict {
    const o: Dict = {};
    ID_KEYS.forEach((k) => (o[k] = S.newVals[k] || ''));
    ADDR_KEYS.forEach((k) => (o[k] = S.newVals[k] || ''));
    o.tax_id = S.newVals.tax_id || '';
    return o;
}
export function applyDecisionToForm() {
    if (!existing()) return;
    const useNew = (picked: 'new' | 'dms') => S.decision === 'overwrite' || picked === 'new';
    ID_KEYS.concat(['tax_id']).forEach((k) => {
        const cmpKey = k === 'prefix_id' ? 'prefix_name' : k;
        const picked = S.pick[cmpKey] || 'dms';
        S.form[k] = useNew(picked) && S.newVals[k] ? S.newVals[k] : S.dmsVals[k] || '';
    });
    const addrNew = S.decision === 'overwrite' || S.pick['address'] === 'new';
    ADDR_KEYS.forEach((k) => {
        S.form[k] = addrNew && S.newVals[k] ? S.newVals[k] : S.dmsVals[k] || '';
    });
}
export function syncMirror() {
    (['_ct', '_sd'] as const).forEach((sfx) => {
        if (S.sameAs[sfx]) ADDR_KEYS.forEach((k) => (S.form[k + sfx] = S.form[k] || ''));
    });
}
export function dmsCompareVal(key: string): string {
    if (key === 'address') return addrStr(S.dmsVals, '');
    if (key === 'prefix_name') return prefixLabel(S.dmsVals.prefix_id || '');
    return S.dmsVals[key] || '';
}
export function newCompareVal(key: string): string {
    if (key === 'address') return addrStr(S.newVals, '');
    return S.newVals[key] || '';
}
function addrStr(v: Dict, sfx: string): string {
    return [
        v['house_no' + sfx],
        v['moo' + sfx] ? 'ม.' + v['moo' + sfx] : '',
        v['soi' + sfx],
        v['road' + sfx],
        v['subdistrict_name' + sfx],
        v['district_name' + sfx],
        v['province_name' + sfx],
        v['zipcode_name' + sfx] || v['zipcode' + sfx],
    ]
        .filter(Boolean)
        .join(' ')
        .trim();
}
export function prefixLabel(id: string): string {
    return (S.prefixes.find((p) => p[0] === id) || ['', ''])[1] || '';
}
export function isChanged(key: string): boolean {
    const dv = S.dmsVals[key] || '';
    return !!S.form[key] && norm(S.form[key]) !== norm(dv);
}
export function diffNewCount() {
    return DX_COMPARE.filter(
        (c) =>
            norm(newCompareVal(c.key)) !== norm(dmsCompareVal(c.key)) &&
            S.pick[c.key] === 'new' &&
            newCompareVal(c.key)
    ).length;
}
export function currentOpt(key: string, v: string): Array<[string, string]> {
    if (!v) return [];
    const labelKey = key
        .replace('province_id', 'province_name')
        .replace('district_id', 'district_name')
        .replace('subdistrict_id', 'subdistrict_name')
        .replace('zipcode_id', 'zipcode_name');
    const label = S.form[labelKey] || S.dmsVals[labelKey] || S.newVals[labelKey] || v;
    return [[v, label]];
}

export function syncFormFromDom() {
    sec()
        ?.querySelectorAll<HTMLInputElement>('#dx-s-confirm [data-fk]')
        .forEach((inp) => {
            S.form[inp.dataset.fk!] = inp.value;
        });
    syncMirror();
}
export function buildPayload() {
    syncFormFromDom();
    const idKeys = [
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
    const fields: Dict = {};
    idKeys.forEach((k) => {
        if (S.form[k] != null) fields[k] = S.form[k];
    });
    fields.people_id = S.form.people_id || S.newVals.people_id || '';
    fields.name = S.form.name || S.newVals.name || '';
    const block = (sfx: string): Dict => {
        const o: Dict = {};
        ADDR_KEYS.forEach((k) => (o[k] = S.form[k + sfx] ?? ''));
        return o;
    };
    return { fields, addresses: { '': block(''), _ct: block('_ct'), _sd: block('_sd') } };
}
