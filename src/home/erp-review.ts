// ERP 推送复核台 · /home 接线控制器(M1 · 隐藏 dev 路由 erp-review · 读真 /api/history)
//
// 把纯渲染原型(console/verify/routing/data)接上真数据 + dev labels + 真原图查看器。
// 隐藏路由:route-table 有、侧栏无(手敲 #/erp-review 打开)。M2 才并入 dms-intake 步③
// 并换成全局 4 语 i18n;此处 dev labels 为中文常量,不引 i18n 键(免 check_i18n --strict)。
//
// 诚实约束:匹配(复用/新建/科目预填)是 M3,M1 未做 → 一律「待复核」、readyCount 由真数据派生
// (无匹配则 0,横幅不臆造「已就绪 N 张」)。原型 a1/a2 里写死的 128/96 等数字不搬进来。

import { renderReviewConsole, type ConsoleLabels } from './erp-review-console.js';
import { buildConsoleData, fmtAmount, type HistoryItem } from './erp-review-data.js';
import { createVerifyOverlay, type VerifyRow, type VerifyLabels } from './erp-review-verify.js';
import { mountImageViewer } from './image-viewer.js';

// 全局 token 由 core 登录后设(与 erp-integration 等同款取法)· 避免耦合 dms-intake-core。
function authHeaders(): Record<string, string> {
    const tk = (window as unknown as { token?: string }).token || '';
    return { Authorization: 'Bearer ' + tk };
}

// dev labels:数据驱动位({n}{done}{total})交渲染层填;静态位不写死伪造计数(状态诚实)。
const CONSOLE_LABELS: ConsoleLabels = {
    title: 'ERP 推送复核台',
    accountSet: '录入复核台 · 开发预览',
    agentOnline: '读取识别记录',
    stages: ['连接账套 · 读取现有资料', '识别 · 比对套账 · 预填', '人工复核(仅异常)', '写入 ERP'],
    stageDetails: ['读取客户 / 商品 / 科目', '识别并比对套账', '仅异常需人工确认', '确认后推送'],
    bannerHead: '{n} 张已就绪,无需逐张查看',
    bannerSub: '已就绪项已折叠,仅需处理下方异常',
    acceptAll: '采纳这 {n} 张',
    tabs: { need: '待处理', ready: '已就绪', unread: '识别失败', all: '全部' },
    colDir: '方向',
    colDoc: '单据 / 往来方',
    colAmount: '金额',
    colAccount: '科目',
    colDest: '记账去向',
    colState: '状态',
    dirIn: '进项',
    dirOut: '销项',
    stateReady: '就绪',
    stateConfirm: '待确认',
    stateNew: '新建待确认',
    stateUnread: '识别失败',
    destReuse: '{code}',
    destNew: '新建',
    destExp: '费用',
    collapseReady: '<b>+{n} 张</b>已就绪已折叠',
    collapseNeed: '其余 <b>{n} 张</b>已就绪,无需查看',
    hintOpen: '点任意一行 → 原图对照逐张核对',
    reviewStart: '开始逐张核对',
    push: '全部确认 → 推送',
    progress: '{done} / {total} 已就绪',
    remain: '还剩 {n} 张需确认',
};

const VERIFY_LABELS: VerifyLabels = {
    dirIn: '进项 · 采购',
    dirOut: '销项 · 销售',
    pos: '{i} / {n}',
    imgFrom: '原图',
    fieldsCap: '① 识别结果 · 可修正',
    balanceOk: '勾稽平衡:税前 + VAT = 合计',
    flagHint: '识别置信度低,请对照左侧原图核对',
    legEnter: '确认下一张',
    legNav: '翻页',
    legEdit: '改字段',
    legClose: '关闭',
    skip: '跳过',
    confirm: '确认并下一张',
    viewerHint: '滚轮缩放 · 拖拽平移',
    viewerNoimg: '无原图',
    viewerLoading: '加载中',
};

let items: HistoryItem[] = [];

function sec(): HTMLElement | null {
    return document.getElementById('page-erp-review');
}

function stateHtml(msg: string): string {
    return `<div class="rc-app"><div class="rc-devstate">${msg}</div></div>`;
}

// 单据 → 逐张核对行(M1:字段取列表已有项;routing/catalog 匹配是 M3 不做)。
function toVerifyRow(item: HistoryItem): VerifyRow {
    const fields = [
        { key: '单据号', value: item.invoice_no || item.filename || '' },
        { key: '往来方', value: item.seller_name || item.buyer_name || '' },
        { key: '金额', value: fmtAmount(item.total_amount) },
    ].filter((f) => f.value);
    return {
        id: item.id,
        docno: item.invoice_no || item.filename || String(item.id).slice(0, 8),
        dir: 'in',
        fields,
    };
}

// 点行 → 逐张遮罩(左真原图右识别读数)· 从点中那张起,←→ 翻遍整批。
function openRow(id: string): void {
    const root = sec();
    const mount = root && (root.querySelector('.erpr-overlay') as HTMLElement | null);
    if (!mount) return;
    const rows = items.map(toVerifyRow);
    const start = items.findIndex((x) => x.id === id);
    const ctrl = createVerifyOverlay(mount, {
        rows,
        labels: VERIFY_LABELS,
        mountImage: (pane, row) => mountImageViewer(pane, row.id),
    });
    ctrl.open(Math.max(0, start));
}

async function loadErpReview(): Promise<void> {
    const root = sec();
    if (!root) return;
    root.innerHTML = stateHtml('加载中…');
    try {
        const r = await fetch('/api/history?limit=50', { headers: authHeaders() });
        if (!r.ok) {
            root.innerHTML = stateHtml('读取识别记录失败(HTTP ' + r.status + ')');
            return;
        }
        const d = (await r.json()) as { items?: HistoryItem[] };
        items = d.items || [];
    } catch {
        root.innerHTML = stateHtml('读取识别记录失败 · 请重试');
        return;
    }
    if (!items.length) {
        root.innerHTML = stateHtml('暂无识别记录 · 先在录入工作台上传识别一批');
        return;
    }
    root.innerHTML = '<div class="erpr-console"></div><div class="erpr-overlay"></div>';
    renderReviewConsole(root.querySelector('.erpr-console') as HTMLElement, {
        data: buildConsoleData(items),
        labels: CONSOLE_LABELS,
        onOpenRow: openRow,
    });
}

(window as unknown as { loadErpReview: () => void }).loadErpReview = loadErpReview;
