// 推送日志卡片(销项重做 · 对齐草稿)· 把单条 erp_push_log 渲染成卡片:
//   状态图标 + 标题(单据号 + 类型/触发标签) + 买方 + 目标系统 + 操作(详情/重试)
//   + 失败摘要条(失败时) + meta 页脚(时间/ERP单号/HTTP/耗时/重试)。
// 从 erp-integration.ts 的表格行重排抽出(腾行数 + 单一职责)· 数据装配逻辑搬运 0 改 ·
// data-log-* 属性原样保留 → 现有点击委托(详情/重试/勾选/复制单号)不变。
/* global t, escapeHtml, currentLang */

import {
    _erpExcAcctPanel,
    _erpExcAccGroupPanel,
    _erpExcBindPanel,
    _erpExcStockOpeningPanel,
} from './erp-exc-actions.js';
import { extractReasonCode, guideWhyLink } from './guide-links.js';

// Express 转人工/失败原因码 → 友好文案键(把「EXPRESS_MANUAL: no_revenue_account」这类
// 看不懂的英文码显成人话)。后端若已带 error_friendly 优先用它;否则这里按码翻译。
const _EXPRESS_REASON_I18N: Record<string, string> = {
    no_revenue_account: 'erp-reason-no-revenue',
    no_ar_account: 'erp-reason-no-ar',
    no_output_vat_account: 'erp-reason-no-output-vat',
    no_purchase_account: 'erp-reason-no-purchase',
    no_ap_account: 'erp-reason-no-ap',
    no_input_vat_account: 'erp-reason-no-input-vat',
    no_account_set: 'erp-reason-no-account-set',
    account_set_not_allowed: 'erp-reason-acct-not-allowed',
    direction_unknown: 'erp-reason-direction-unknown',
    direction_not_enabled: 'erp-reason-direction-not-enabled',
    // V2 明细对账(行合计与税前额对不上 / 缺品名金额)→ 退表头并转人工核对。
    items_mismatch: 'erp-reason-items-mismatch',
    items_incomplete: 'erp-reason-items-incomplete',
    // 本批选了「库存」但账套里一件真实库存品都没有 → 建库存主档没有模板可依,推了必炸。
    stock_no_master_in_account_set: 'erp-reason-stock-no-master',
    // 零主档账套建第一个库存品差存货科目组:required=合格的有好几个,没人选;missing=一个
    // 合格的都没有(或小助手还没报上来)。指引不同故分两句,别合成一条。
    stock_acc_group_required: 'erp-reason-stock-acc-group',
    stock_acc_group_missing: 'erp-reason-stock-acc-group-missing',
    low_confidence: 'erp-reason-low-confidence',
    enqueue_error: 'erp-reason-enqueue-error',
    amounts_not_consistent: 'erp-reason-amounts',
    bad_or_missing_date: 'erp-reason-bad-date',
    entry_not_balanced: 'erp-reason-unbalanced',
    account_not_in_chart: 'erp-reason-not-in-chart',
    // 单据防呆(doc_sanity · 须人工判断):外币/贷项/押金/未来日期/补开倒签/坏税号。
    currency_not_thb: 'erp-reason-currency',
    seller_buyer_same_tax: 'erp-reason-same-tax',
    credit_note: 'erp-reason-credit-note',
    deposit_receipt: 'erp-reason-deposit',
    date_implausible: 'erp-reason-date-implausible',
    date_future: 'erp-reason-date-future',
    date_reissued: 'erp-reason-date-reissued',
    tax_id_invalid: 'erp-reason-tax-invalid',
};

// 小助手(本地 Agent)ack 失败码 → 人话(error_msg 形如 "[SUPPLIER_DUP_SUSPECTED] dup")。
const _AGENT_REASON_I18N: Record<string, string> = {
    SUPPLIER_DUP_SUSPECTED: 'erp-reason-supplier-dup',
    CUSTOMER_DUP_SUSPECTED: 'erp-reason-customer-dup',
    CDX_REINDEX_FAILED: 'erp-reason-cdx-failed',
    ACCOUNT_BUSY_LOCKED: 'erp-reason-account-busy',
    // 防重单闸:改了票号回导重推,而上一版单据还在 Express 里。此前没接进来 → 前端翻译返空
    // → 原样显示小助手那句写死中文 + 方括号里的英文码,泰国会计看不懂也不知道要删哪张。
    PRIOR_DOC_STILL_IN_ERP: 'erp-reason-prior-doc',
};

// 过账去向留人工(raw 形如 "EXPRESS_MANUAL: posting_needs_review:perpetual")· 冒号后是这家
// 账套的客观库存用法,它决定该跟会计说哪一句,所以按后缀分文案,取不到后缀回落通用句。
const _POSTING_REVIEW_I18N: Record<string, string> = {
    perpetual: 'erp-reason-posting-review-perpetual',
    mixed: 'erp-reason-posting-review-mixed',
};

function _expressFriendlyReason(raw: string, log?: any): string {
    // raw 形如 "EXPRESS_MANUAL: no_revenue_account" 或 "account_set_not_allowed:DATAT"
    const code = extractReasonCode(raw);
    if (code === 'posting_needs_review') {
        const usage = raw.split(':').pop()!.trim();
        return t(_POSTING_REVIEW_I18N[usage] || 'erp-reason-posting-review');
    }
    if (_AGENT_REASON_I18N[code]) {
        const text = t(_AGENT_REASON_I18N[code]);
        // 单据号从后端派生的结构化字段取(载荷里的 prior_docnum),不从错误串抠。
        // 只说"有旧单挡着"而不说是哪一号,会计没法动手。
        const doc = (log && log.prior_doc_fix && log.prior_doc_fix.docnum) || '';
        return text.replace('{doc}', doc);
    }
    const key = _EXPRESS_REASON_I18N[code];
    return key ? t(key) : '';
}

function buildErpLogCard(log: any): string {
    const time = new Date(log.created_at);
    const p2 = (n: number) => String(n).padStart(2, '0');
    const timeStr = `${p2(time.getMonth() + 1)}-${p2(time.getDate())} ${p2(time.getHours())}:${p2(time.getMinutes())}`;

    const isRetrying =
        log.status === 'failed' &&
        log.next_retry_at &&
        new Date(log.next_retry_at).getTime() > Date.now() - 60000;
    const stage = log.push_stage || '';
    let statusClass: string, statusIcon: string, statusLabel: string;
    if (log.status === 'pending') {
        statusClass = 'retrying';
        statusIcon = '⟳';
        statusLabel = t('erp-status-pending');
    } else if (log.status === 'success') {
        statusClass = 'ok';
        statusIcon = '✓';
        statusLabel = t('erp-status-success');
    } else if (log.status === 'skipped_dup') {
        statusClass = 'skipped';
        statusIcon = '⏭';
        statusLabel = t('erp-status-skipped');
    } else if (isRetrying) {
        statusClass = 'retrying';
        statusIcon = '↻';
        statusLabel = t('erp-status-retrying');
    } else {
        statusClass = 'fail';
        statusIcon = '✗';
        statusLabel = t('erp-status-failed');
    }
    // V3 细粒度态(meta.stage 派生进 push_stage)只覆盖诚实标签 —— 复用既有图标,不新增 emoji:
    // waiting_lock 落 pending 分支(⟳ 等待中·非失败,不吓用户)· manual/needs_* 落 fail 分支(✗)。
    if (stage === 'waiting_lock') {
        statusLabel = t('erp-status-waiting-lock');
    } else if (stage === 'needs_mapping') {
        statusLabel = t('erp-status-needs-mapping');
    } else if (stage === 'needs_review' || log.status === 'manual') {
        statusLabel = t('erp-status-needs-review');
    }

    const isId = log.push_type === 'id_card';
    const typeBadge = isId
        ? `<span class="log-tag log-type-idcard">${escapeHtml(t('erp-log-type-idcard'))}</span>`
        : `<span class="log-tag log-type-invoice">${escapeHtml(t('erp-log-type-invoice'))}</span>`;
    const trig =
        log.trigger === 'auto'
            ? `<span class="log-tag auto">${escapeHtml(t('log-tag-auto'))}</span>`
            : log.trigger === 'retry'
              ? `<span class="log-tag retry">${escapeHtml(t('log-tag-retry'))}</span>`
              : `<span class="log-tag manual">${escapeHtml(t('log-tag-manual'))}</span>`;

    // 「系统替你做了主」类标记:徽章常驻,长解释挂在徽章的悬停提示里。
    //
    // 此前每条标记在卡片下方各占一条整宽横幅。真机一屏 8 张票,8 张全带「未结转成本」——
    // 同一段会计解释印 8 遍,提示就成了背景噪音,还把绿勾「成功」在视觉上否定掉。
    // 而这不是偶然:真账套 162 个库存品只有 2 个有标准成本,未结转成本在这个客户身上几乎每单必有。
    // 例外的展示方式承载不了常态 —— 故降到「扫一眼看得见、要细节才展开」。
    // 提示用真元素不用 ::after —— 伪元素在 CSSOM 里量不到尺寸,量不到就验不了「真的换行了没」,
    // 而这条正是本次改动的要点。真元素还能自然换行、能拿 rect 断言。
    const tipTag = (cls: string, label: string, tip: string) =>
        `<span class="log-tag ${cls}" tabindex="0">${escapeHtml(label)}` +
        `<span class="log-tip" role="tooltip">${escapeHtml(tip)}</span></span>`;

    // 未结转成本(小助手回执报了 no_cost_basis / new_item_no_cost_basis)· 后端 derive_uncosted 派生。
    // 推送本身是成功的,但账里欠着成本 —— 不标出来就是一条普通成功记录,会计要到毛利异常才发现。
    const uncostedN = Number(log.uncosted_lines) || 0;
    const uncostedTag = uncostedN
        ? tipTag(
              'uncosted',
              t('erp-uncosted-tag'),
              t('erp-uncosted-note', { n: String(uncostedN) }) +
                  (log.uncosted_created ? ' · ' + t('erp-uncosted-created') : '')
          )
        : '';

    // 单位是猜的(小助手建库存主档时票面没给单位,按本账套最常用的单位填的)· 后端 derive_guessed_unit
    // 派生。同「未结转成本」一样用琥珀:推送是成功的,但账里有一处是系统替会计做的主,得看得见。
    const unitGuessedN = Number(log.unit_guessed_lines) || 0;
    const unitCodes = (Array.isArray(log.unit_guessed_codes) ? log.unit_guessed_codes : [])
        .map((s: unknown) => String(s ?? '').trim())
        .filter(Boolean)
        .join(' · ');
    const unitTag = unitGuessedN
        ? tipTag(
              'unit-guessed',
              t('erp-unit-guessed-tag'),
              t('erp-unit-guessed-note', { n: String(unitGuessedN), u: unitCodes })
          )
        : '';

    // 本次在账套里新建了库存品 · 后端 derive_stock_acc_group 派生(回执 created + 载荷 stock_acccod)。
    // 账套只有一个合格存货科目组时那个组是系统替会计定的 —— 替人做主就得让他在日志上看见挂进了
    // 哪个存货科目,否则账里凭空多一件商品要等对科目余额才发现。
    const stockCreatedN = Number(log.stock_created) || 0;
    const stockGroup = stockCreatedN
        ? [log.stock_acccod, log.stock_acc, log.stock_acc_name]
              .map((s: unknown) => String(s ?? '').trim())
              .filter(Boolean)
              .join(' · ')
        : '';
    const stockTag = stockGroup
        ? tipTag(
              'stock-new',
              t('erp-stock-new-tag'),
              t('erp-stock-new-note', { n: String(stockCreatedN), g: stockGroup })
          )
        : '';

    const friendlyReason =
        (log.error_friendly && (log.error_friendly[currentLang] || log.error_friendly.en)) || '';

    const rc = log.retry_count || 0;
    const mr = log.max_retries || 3;
    let retryInfo = '';
    if (isRetrying) {
        const nextMin = Math.max(
            0,
            Math.round((new Date(log.next_retry_at).getTime() - Date.now()) / 60000)
        );
        retryInfo = `${t('erp-retry-attempt', { n: rc, max: mr })} · ${nextMin <= 0 ? t('erp-retry-next-soon') : t('erp-retry-next-min', { n: nextMin })}`;
    } else if (log.status === 'failed' && rc >= mr && !log.next_retry_at) {
        retryInfo = t('erp-retry-exhausted', { n: rc });
    }

    const canSelect = !isRetrying;
    const cb = canSelect
        ? `<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(log.id)}" ${window._erpSelected?.has(log.id) ? 'checked' : ''}>`
        : `<span class="erp-log-cb-spacer"></span>`;

    // 买方/客户(身份证订车显末4)· 卖方
    const buyerName = (log.ocr_buyer_name || '').trim() || (log.client_name || '').trim();
    const partyLabel = isId ? t('erp-log-col-idcard') : t('erp-log-col-buyer');
    const partyVal = isId
        ? log.id_card_tail
            ? '••••' + escapeHtml(log.id_card_tail)
            : '—'
        : buyerName
          ? escapeHtml(buyerName)
          : `<span class="log-client-empty">${escapeHtml(t('erp-log-client-unassigned'))}</span>`;
    const erpName = log.endpoint_name
        ? escapeHtml(log.endpoint_name)
        : `<span class="log-erp-deleted">${escapeHtml(t('erp-log-endpoint-deleted'))}</span>`;

    // ERP 单号(成功有则可复制 / 有链接则打开 / 成功但空则提示 / 否则不显)
    const extDocNo = (log.external_doc_no || '').trim();
    const extUrl = (log.external_url || '').trim();
    let docMeta = '';
    if (extUrl)
        docMeta = `<span><b>${escapeHtml(t('erp-log-col-doc'))}</b><a href="${escapeHtml(extUrl)}" target="_blank" rel="noopener" class="log-doc-open">${escapeHtml(t('erp-log-doc-open'))}</a></span>`;
    else if (extDocNo)
        docMeta = `<span><b>${escapeHtml(t('erp-log-col-doc'))}</b><span class="log-doc-copy" data-copy-doc="${escapeHtml(extDocNo)}" title="${escapeHtml(t('erp-log-doc-copy-tip'))}">${escapeHtml(extDocNo)}</span></span>`;
    else if (log.status === 'success')
        docMeta = `<span><b>${escapeHtml(t('erp-log-col-doc'))}</b><span class="log-doc-missing">${escapeHtml(t('erp-log-doc-missing'))}</span></span>`;

    // 科目 at-a-glance(Express 队列响应派生 push_accounts)· 列表不展开也看到记到哪几个科目。
    const acctMeta =
        Array.isArray(log.push_accounts) && log.push_accounts.length
            ? `<span class="log-accts"><b>${escapeHtml(t('erp-log-col-accounts'))}</b>${log.push_accounts
                  .map((a: any) => escapeHtml(a.acc))
                  .join(' · ')}</span>`
            : '';

    // 失败卡自助修复入口(原「推送异常」tab 并入此处 · 由后端 list_push_logs 在失败行附
    // category/account_fix/bind_fix)。补科目/绑主体卡用展开面板就地修复重推 → 不另给裸重试
    // (重试只会再失败);商品/客户不符走修复映射 picker + 保留重试。其余失败只给重试。
    const _cat = log.category || '';
    const isAcctFix = statusClass === 'fail' && _cat === 'account_missing' && !!log.account_fix;
    const isBindFix =
        statusClass === 'fail' &&
        _cat === 'direction_unknown' &&
        !!(log.bind_fix && log.bind_fix.can_bind);
    const canMapFix =
        statusClass === 'fail' &&
        (_cat === 'product_mismatch' || _cat === 'customer_mismatch' || _cat === 'no_client');
    // 库存路推不动的两支同归 category=stock_opening_needed,靠 stock_fix.needs 分卡:
    //   'acc_group' → 账套零库存主档且没选存货科目组,选一次就能建主档(候选可能为空,那时
    //                 面板显「先去 Express 建一个」,比不给入口诚实);
    //   缺省/其他   → 缺主档或零负库存,会计按真实单据补期初(B1·批次二 · 老日志无 needs)。
    const _sf = log.stock_fix || {};
    const isAccGrpFix =
        statusClass === 'fail' && _cat === 'stock_opening_needed' && _sf.needs === 'acc_group';
    const isStockFix =
        statusClass === 'fail' &&
        _cat === 'stock_opening_needed' &&
        !isAccGrpFix &&
        !!(_sf.items || []).length;
    let repairBtn = '';
    if (isAcctFix)
        repairBtn = `<button class="btn btn-sm btn-primary" type="button" data-erpexc-acctfix="${escapeHtml(log.id)}">${escapeHtml(t('erp-acctfix-open'))}</button>`;
    else if (isBindFix)
        repairBtn = `<button class="btn btn-sm btn-primary" type="button" data-erpexc-acctfix="${escapeHtml(log.id)}">${escapeHtml(t('erp-bind-open'))}</button>`;
    else if (isStockFix)
        repairBtn = `<button class="btn btn-sm btn-primary" type="button" data-erpexc-acctfix="${escapeHtml(log.id)}">${escapeHtml(t('erp-stockopen-open'))}</button>`;
    else if (isAccGrpFix)
        repairBtn = `<button class="btn btn-sm btn-primary" type="button" data-erpexc-acctfix="${escapeHtml(log.id)}">${escapeHtml(t('erp-accgrp-open'))}</button>`;
    else if (canMapFix)
        repairBtn = `<button class="btn btn-sm btn-secondary" type="button" data-erpexc-fix="${escapeHtml(log.id)}">${escapeHtml(_cat === 'product_mismatch' ? t('erp-exc-fix-product') : t('erp-exc-fix-customer'))}</button>`;
    const repairPanel = isAcctFix
        ? _erpExcAcctPanel(log)
        : isBindFix
          ? _erpExcBindPanel(log)
          : isStockFix
            ? _erpExcStockOpeningPanel(log)
            : isAccGrpFix
              ? _erpExcAccGroupPanel(log)
              : '';

    // 存货科目组卡不进这个排除表:选组只写端点配置、不重推,重试按钮得留着让会计选完自己点。
    const retryBtn =
        log.status === 'failed' && !isRetrying && !isAcctFix && !isBindFix && !isStockFix
            ? `<button class="btn btn-sm btn-secondary" data-log-retry="${escapeHtml(log.id)}">${escapeHtml(t('erp-exc-retry'))}</button>`
            : '';

    // 失败摘要:优先友好原因(catalog)· 回落到去掉 ERR_ 码的原始 error_msg(失败卡始终有摘要)
    const rawReason = (log.error_msg || '').replace(/^ERR_[A-Z0-9_]+:?\s*/, '').trim();
    const reasonText =
        friendlyReason || _expressFriendlyReason(log.error_msg || '', log) || rawReason;
    // 摘要读完接着就是「那我该怎么办」——原因码有对应章节时就地给一条深链,没有则不出现,
    // 免得点开一篇跟这张票无关的文章。
    const whyLink = statusClass === 'fail' ? guideWhyLink(log.error_msg || '') : '';
    const reasonStrip =
        statusClass === 'fail' && reasonText
            ? `<div class="erp-log-reason"><b>${escapeHtml(t('erp-log-fail-summary'))}</b><span>${escapeHtml(reasonText)}</span>${whyLink}</div>`
            : '';

    return `
        <div class="erp-log-card ${statusClass}${repairPanel ? ' has-acctfix' : ''}" data-log-detail="${escapeHtml(log.id)}">
            <div class="erp-log-card-main">
                <span class="erp-log-card-cb">${cb}</span>
                <span class="erp-log-state ${statusClass}" title="${escapeHtml(statusLabel)}">${statusIcon}</span>
                <div class="erp-log-titleblock">
                    <b title="${escapeHtml(log.invoice_no || '')}">${escapeHtml(log.invoice_no || '-')}</b>
                    <div class="erp-log-tags">${typeBadge}${trig}${uncostedTag}${unitTag}${stockTag}</div>
                </div>
                <div class="erp-log-party"><label>${escapeHtml(partyLabel)}</label><span>${partyVal}</span></div>
                <div class="erp-log-party"><label>${escapeHtml(t('erp-log-col-target'))}</label><span>${erpName}</span></div>
                <div class="erp-log-act">
                    ${repairBtn}
                    ${retryBtn}
                    <button class="btn btn-sm btn-ghost" data-log-detail="${escapeHtml(log.id)}">${escapeHtml(t('erp-log-detail-btn'))}</button>
                </div>
            </div>
            ${reasonStrip}
            <div class="erp-log-meta">
                <span><b>${escapeHtml(t('erp-log-col-time'))}</b>${escapeHtml(timeStr)}</span>
                ${docMeta}
                ${acctMeta}
                <span><b>HTTP</b>${log.http_status || '—'}</span>
                <span><b>${escapeHtml(t('erp-log-col-elapsed'))}</b>${log.elapsed_ms != null ? log.elapsed_ms + 'ms' : '—'}</span>
                ${retryInfo ? `<span><b>${escapeHtml(t('erp-log-col-retry'))}</b>${escapeHtml(retryInfo)}</span>` : ''}
            </div>
            ${repairPanel}
        </div>`;
}

window.buildErpLogCard = buildErpLogCard;
// 异常页待补科目卡复用同一套人话映射(单一源 · 不另写一份)。
(window as any)._expressFriendlyReason = _expressFriendlyReason;
