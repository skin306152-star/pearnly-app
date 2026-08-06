/*
 * Pearnly AI · ai-profile-render.js · 税务画像卡(智能判断版)纯字段模型 + 单字段校验
 *
 * 画像卡设计稿 v1(唯一交互规格)落地:1:1 抄照 14 个字段键 + 分组/展露规则,每字段独立
 * 值控件+来源徽章+状态,不再是一张大表单一次性提交——手填即改即存,推断候选(来自
 * routes/tax_profile_routes.py 的 GET 响应 field_meta[key].proposal)要点"确认"才转正。
 * HTML 拼装(依赖 at()/AI.state)拆在 ai-profile-card-render.js(单文件<500 铁律,本文件
 * 只留零 DOM 依赖的纯函数,node 测试 tests/unit/test_ai_profile_pure.py 直接 require)。
 *
 * 字段顺序 1:1 对齐税务画像-方案-B1.md §2.2 字段表 ×(画像卡设计稿 v1 的分组:
 * employ 雇佣与代扣 / filing 申报方式 / special 特殊),不含只读派生字段 vat_status/branch
 * (那两行在卡片渲染层单独拼,见 ai-profile-card-render.js 的 readonlyRowHtml)。
 */
(function (root) {
    'use strict';

    // 三组三态枚举共享的取值集合 + 值→i18n key(§2.2 表:多数字段是 yes/no/unknown,
    // sbt_status 是 none/registered/unknown,filing_disposition 是 active/dormant/unknown)。
    var GROUP_OPTIONS = {
        yn: ['yes', 'no', 'unknown'],
        sbt: ['none', 'registered', 'unknown'],
        filing: ['active', 'dormant', 'unknown'],
    };
    var GROUP_VALUE_LABEL_KEY = {
        yn: { yes: 'profile_val_yes', no: 'profile_val_no', unknown: 'profile_val_unknown' },
        sbt: {
            none: 'profile_val_sbt_none',
            registered: 'profile_val_sbt_registered',
            unknown: 'profile_val_unknown',
        },
        filing: {
            active: 'profile_val_filing_active',
            dormant: 'profile_val_filing_dormant',
            unknown: 'profile_val_unknown',
        },
    };

    // 画像字段定义:14 键,不多不少(画像卡设计稿 v1 顶注已核实——不是任务口述的 13,
    // 交付报告已记)。showIf 按「当前画像草稿」判定是否展示(渐进展露),纯函数、零 DOM。
    var FIELD_META = [
        {
            key: 'sbt_status',
            kind: 'enum',
            group: 'sbt',
            groupKey: 'special',
            labelKey: 'profile_field_sbt_status',
        },
        {
            key: 'sbt_business_type',
            kind: 'text',
            groupKey: 'special',
            labelKey: 'profile_field_sbt_business_type',
            showIf: function (v) {
                return v.sbt_status !== 'none';
            },
        },
        {
            key: 'has_employees',
            kind: 'enum',
            group: 'yn',
            groupKey: 'employ',
            labelKey: 'profile_field_has_employees',
        },
        {
            key: 'pays_individuals',
            kind: 'enum',
            group: 'yn',
            groupKey: 'employ',
            labelKey: 'profile_field_pays_individuals',
            inferable: true,
        },
        {
            key: 'pays_juristic',
            kind: 'enum',
            group: 'yn',
            groupKey: 'employ',
            labelKey: 'profile_field_pays_juristic',
            inferable: true,
        },
        {
            key: 'pays_foreign',
            kind: 'enum',
            group: 'yn',
            groupKey: 'employ',
            labelKey: 'profile_field_pays_foreign',
        },
        {
            key: 'pays_interest_dividend',
            kind: 'enum',
            group: 'yn',
            groupKey: 'employ',
            labelKey: 'profile_field_pays_interest_dividend',
        },
        {
            key: 'has_multi_branch',
            kind: 'bool',
            groupKey: 'special',
            labelKey: 'profile_field_has_multi_branch',
        },
        {
            key: 'branch_count',
            kind: 'int',
            groupKey: 'special',
            labelKey: 'profile_field_branch_count',
            showIf: function (v) {
                return !!v.has_multi_branch;
            },
        },
        {
            key: 'filing_disposition',
            kind: 'enum',
            group: 'filing',
            groupKey: 'filing',
            labelKey: 'profile_field_filing_disposition',
        },
        {
            key: 'efiling_enrolled',
            kind: 'enum',
            group: 'yn',
            groupKey: 'filing',
            labelKey: 'profile_field_efiling_enrolled',
        },
        {
            key: 'tax_agent_authorized',
            kind: 'bool',
            groupKey: 'filing',
            labelKey: 'profile_field_tax_agent_authorized',
        },
        {
            key: 'tax_agent_ref',
            kind: 'text',
            groupKey: 'filing',
            labelKey: 'profile_field_tax_agent_ref',
            showIf: function (v) {
                return !!v.tax_agent_authorized;
            },
        },
        {
            key: 'vat_credit_carry',
            kind: 'money',
            groupKey: 'special',
            labelKey: 'profile_field_vat_credit_carry',
        },
    ];

    // 卡片四组分栏(画像卡设计稿 v1):基础登记(只读派生,渲染层单独拼)/ 雇佣与代扣 /
    // 申报方式 / 特殊。
    var GROUPS = [
        { key: 'employ', titleKey: 'profile_group_employ' },
        { key: 'filing', titleKey: 'profile_group_filing' },
        { key: 'special', titleKey: 'profile_group_special' },
    ];

    // 触发表单重绘(showIf 需要看最新值)的字段——其余字段改了不影响任何行的显隐。
    var VISIBILITY_FIELDS = ['sbt_status', 'has_multi_branch', 'tax_agent_authorized'];

    // 只有这两个字段有推断数据源(诚实边界,见 services/workorder/profile_inference.py 顶注)。
    var INFERABLE_FIELDS = FIELD_META.filter(function (f) {
        return f.inferable;
    }).map(function (f) {
        return f.key;
    });

    function fieldByKey(key) {
        for (var i = 0; i < FIELD_META.length; i++) {
            if (FIELD_META[i].key === key) return FIELD_META[i];
        }
        return null;
    }

    function isApplicable(meta, values) {
        return !meta.showIf || meta.showIf(values || {});
    }

    // 字段展示态派生(纯函数,镜像后端 field_meta 契约):
    //   confirmed  已确认过(手填或推断转正)
    //   conflict   有推断候选且与当前已确认值不同——需要人二选一
    //   pending    有推断候选、从未确认过——需要点一下"确认"
    //   unknown    枚举字段字面值就是 'unknown',没有候选可选——先手动选一下
    //   blocked    SBT 专属:没有官方数据源、也没人确认过(见下方特例注)
    //   confirmed(缺省兜底) bool/int/money/text 没有"未响应"哨兵值,或枚举字段有真实
    //              取值但没留痕(存量数据)——展示为已确认,不无端制造待办。
    function deriveFieldStatus(meta, value, fieldMetaEntry) {
        var entry = fieldMetaEntry || {};
        var hasProposal = !!entry.proposal;
        var confirmed = !!entry.confirmed_at;
        if (hasProposal && confirmed) return 'conflict';
        if (hasProposal && !confirmed) return 'pending';
        if (confirmed) return 'confirmed';
        if (meta.kind === 'enum') {
            // SBT 特例:表列默认落 'none'(不虚报"已确认无 SBT"),但从未有人确认过时,
            // 视觉上当"未确认"处理并挂 CTA——诚实边界:没有官方接口能查 SBT 登记状态,
            // 沉默默认不能算数(交付报告已记这条前端专属特例,后端真实值/义务判定不受影响)。
            if (meta.key === 'sbt_status' && value === 'none') return 'blocked';
            return value === 'unknown' ? 'unknown' : 'confirmed';
        }
        return 'confirmed';
    }

    // 来源徽章(官方接口 official / 票据推断 inferred / 手填 manual / 未知 unknown)。
    function deriveSourceBadge(status, fieldMetaEntry) {
        var entry = fieldMetaEntry || {};
        if (entry.source) return entry.source;
        // pending 只可能来自一条现算的推断候选(诚实边界:唯二可推断字段才会有 proposal),
        // 候选本身就是"票据推断"出处——徽章要照实说这条候选是哪来的,不能因为"还没确认"
        // 就退回手填(那会让人以为是自己填的,反而藏起了它其实是系统猜的这件事)。
        if (status === 'pending') return 'inferred';
        if (status === 'unknown' || status === 'blocked') return 'unknown';
        return 'manual'; // 有真实值但没有出处戳(存量数据)——按手填口径展示,不假装官方
    }

    // 单字段校验(替代旧版整表 buildProfilePayload——手填即存,一次只提交一个字段)。
    // 枚举/bool 字段走 select/checkbox,永远合法,不需要这里校验;int/money/text 才有
    // 校验空间。返回 { ok, value, errKey }。
    function validateFieldInput(field, raw) {
        if (field.kind === 'int') {
            var n = parseInt(raw, 10);
            if (!n || n < 1) return { ok: false, errKey: 'err_profile_branch_count_invalid' };
            return { ok: true, value: n };
        }
        if (field.kind === 'money') {
            if (raw == null || String(raw).trim() === '') return { ok: true, value: '0.00' };
            var amt = root.AI.format.parseAmount(raw, false);
            if (amt === null) return { ok: false, errKey: 'err_profile_vat_credit_invalid' };
            return { ok: true, value: amt };
        }
        if (field.kind === 'bool') return { ok: true, value: !!raw };
        if (field.kind === 'enum') return { ok: true, value: raw };
        // text:sbt_business_type/tax_agent_ref,留空合法(未填 = 空字符串)。
        return { ok: true, value: raw == null ? '' : String(raw) };
    }

    var pure = {
        GROUP_OPTIONS: GROUP_OPTIONS,
        GROUP_VALUE_LABEL_KEY: GROUP_VALUE_LABEL_KEY,
        FIELD_META: FIELD_META,
        GROUPS: GROUPS,
        VISIBILITY_FIELDS: VISIBILITY_FIELDS,
        INFERABLE_FIELDS: INFERABLE_FIELDS,
        fieldByKey: fieldByKey,
        isApplicable: isApplicable,
        deriveFieldStatus: deriveFieldStatus,
        deriveSourceBadge: deriveSourceBadge,
        validateFieldInput: validateFieldInput,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;
    if (root) {
        root.AI = root.AI || {};
        root.AI.profileRender = pure;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
