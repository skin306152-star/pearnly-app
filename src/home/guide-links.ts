// ============================================================
// 教程深链 · 推送失败原因码 → 教程章节
//
// 会计最需要教程的一刻不是打开侧栏时,而是盯着一张推不进去的失败卡时。这里把两者接上:
// 失败卡与推送详情抽屉把原因码丢进本表,命中就在原因旁边挂一条「这是怎么回事」直达该章。
//
// 表里的值是「所属篇 + 章节 id」,ch 必须是正文里真实存在的章 —— scripts/check_guide.py
// 的深链闸逐条核。这里一度按「定稿清单」先填占位 id(stuck-no-revenue-account 之类),
// 正文写完是 exc-* 一套,35 条无一命中;openGuide 查不到章就退手册首页,不白屏不报错,
// 于是每条深链都成了「点了等于没点」而没人发现。要改指向只改这张表:
// 渲染侧三处(失败卡 / 详情抽屉失败框 / Express 体检行)共用它。
// ============================================================
import { esc, T } from './guide-content.js';

export interface ChapterRef {
    // 所属篇 —— 写表时就知道,带上它深链只拉这一篇,不必逐篇扫全书
    sec: string;
    ch: string;
}

const inSection = (sec: string, table: Record<string, string>): Record<string, ChapterRef> =>
    Object.fromEntries(Object.entries(table).map(([code, ch]) => [code, { sec, ch }]));

// 键 = 后端落到日志上的规范原因码:
//   EXPRESS_MANUAL 转人工码(services/erp/express_push/preflight.py 的 pf.reason)、
//   小助手 ack 的 [CODE] 码、体检 check 自己的 reason(subject_unbound / ambiguous)。
// 值 = 手册章节 id。故意不收的码见文件末尾说明。
const REASON_CHAPTER: Record<string, ChapterRef> = inSection('stuck', {
    // 六个缺科目走同一张「补科目」面板;科目越界(account_not_in_chart)是该章末尾那条提示的情形
    no_revenue_account: 'exc-fix-account-missing',
    no_ar_account: 'exc-fix-account-missing',
    no_output_vat_account: 'exc-fix-account-missing',
    no_purchase_account: 'exc-fix-account-missing',
    no_ap_account: 'exc-fix-account-missing',
    no_input_vat_account: 'exc-fix-account-missing',
    account_not_in_chart: 'exc-fix-account-missing',
    // 账套没选 / 选了但不在连接的允许范围 —— 都得回小助手改,网页上没有开关
    no_account_set: 'exc-account-set',
    account_set_not_allowed: 'exc-account-set',
    // 方向判不出的三个码是同一件事(subject_unbound / ambiguous 是体检行上的两种细分):
    // 该章正文讲绑主体,提示里讲「两方税号都读错时绑了也没用,回核对屏改」
    direction_unknown: 'exc-fix-bind-subject',
    subject_unbound: 'exc-fix-bind-subject',
    ambiguous: 'exc-fix-bind-subject',
    // 方向判出来了但本连接不收 —— 界面上无处可改,该章直接让人找支持,别反复重推
    direction_not_enabled: 'exc-direction-not-enabled',
    // 明细对账没过(行合计与税前额对不上 / 缺品名金额)
    items_mismatch: 'exc-items',
    items_incomplete: 'exc-items',
    // 库存路两支修法不同:缺存货科目组=选一次就能建主档;零库存主档=先推进货票或改服务模式
    stock_acc_group_required: 'exc-fix-stock-acc-group',
    stock_acc_group_missing: 'exc-fix-stock-acc-group',
    stock_no_master_in_account_set: 'exc-stock-lane-codes',
    // 票面数字本身有问题(置信度 / 三格金额 / 日期 / 借贷不平)
    low_confidence: 'exc-low-confidence',
    amounts_not_consistent: 'exc-amounts-date-balance',
    entry_not_balanced: 'exc-amounts-date-balance',
    bad_or_missing_date: 'exc-amounts-date-balance',
    // 单据防呆八种(外币 / 贷项 / 押金 / 日期 / 税号)· 该章逐条列了这八句摘要
    currency_not_thb: 'exc-doc-sanity',
    seller_buyer_same_tax: 'exc-doc-sanity',
    credit_note: 'exc-doc-sanity',
    deposit_receipt: 'exc-doc-sanity',
    date_implausible: 'exc-doc-sanity',
    date_future: 'exc-doc-sanity',
    date_reissued: 'exc-doc-sanity',
    tax_id_invalid: 'exc-doc-sanity',
    // 小助手在会计电脑上落库时报回来的
    SUPPLIER_DUP_SUSPECTED: 'exc-dup-suspected',
    CUSTOMER_DUP_SUSPECTED: 'exc-dup-suspected',
    CDX_REINDEX_FAILED: 'exc-write-rollback',
    ACCOUNT_BUSY_LOCKED: 'exc-waiting-lock',
    PRIOR_DOC_STILL_IN_ERP: 'exc-prior-doc',
});
// 不收 enqueue_error / payload_version_outdated:前者是系统异常(会计做不了任何事,该找我们),
// 后者是小助手版本落后(自更新解决)。给它们挂教程只会把人引去一篇帮不上忙的文章。

// 原因码在日志里有三种包装:「EXPRESS_MANUAL: code」「[AGENT_CODE] 中文」「code:细节」。
// 深链映射(本文件)与人话映射(erp-log-card)查的是同一个码,剥法只此一份 ——
// 分两处写迟早漂成「有文案没链接」。
export function extractReasonCode(raw: unknown): string {
    const stripped = String(raw ?? '')
        .replace(/^EXPRESS_MANUAL:?\s*/i, '')
        .trim();
    const agent = stripped.match(/^\[([A-Z0-9_]+)\]/);
    if (agent) return agent[1];
    return stripped.split(':')[0].trim();
}

export function guideChapterFor(raw: unknown): ChapterRef | null {
    return REASON_CHAPTER[extractReasonCode(raw)] || null;
}

// 无对应章节返回空串 —— 调用方直接拼进模板即可,不必自己判断要不要显示。
export function guideWhyLink(raw: unknown): string {
    const ref = guideChapterFor(raw);
    if (!ref) return '';
    return (
        `<button type="button" class="gd-why" data-gd-why="${esc(ref.ch)}" ` +
        `data-gd-why-sec="${esc(ref.sec)}" ` +
        `title="${esc(T('gd-why-tip'))}">${esc(T('gd-why-link'))}` +
        `<span class="gd-why-ar" aria-hidden="true">&#8594;</span></button>`
    );
}

// 捕获阶段接管:失败卡整张都是「打开详情抽屉」的热区,冒泡阶段再拦就已经弹出抽屉了。
document.addEventListener(
    'click',
    (e) => {
        const el = (e.target as HTMLElement | null)?.closest?.<HTMLElement>('[data-gd-why]');
        if (!el) return;
        e.preventDefault();
        e.stopPropagation();
        // 抽屉是挂在 body 上的浮层,跳走后会盖在教程页上 —— 跳前先收掉。
        document
            .querySelectorAll('.erp-detail-overlay, .erp-detail-drawer')
            .forEach((n) => n.remove());
        const open = (window as unknown as Record<string, unknown>).openGuide;
        if (typeof open === 'function')
            (open as (id: string, sec?: string) => unknown)(
                el.dataset.gdWhy || '',
                el.dataset.gdWhySec
            );
    },
    true
);

const api = window as unknown as Record<string, unknown>;
api.guideWhyLink = guideWhyLink;
