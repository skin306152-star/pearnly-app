// 对账中心重设计 · 主控制器(2026-06-14 · 落地 design-reference/pearnly_reconciliation_redesign_v2.html)
//
// 复用现有后端与组件:submit×3 / window._reconPollJob / window.ReconMapping / window.ReconReview /
// template 端点 / export 端点 / showToast / showConfirm。后端契约一字不改。
// 三类型共用一套外壳;切换=换配置+清残留。读取方式与「确认」由真实 submit→needs_mapping/needs_review
// 决定(不在卡片造假行数/项数)。进度无精确百分比 → 诚实进行中态(禁定时器假进度)。
import {
    RX,
    rxCfg,
    rxClassify,
    rxExt,
    rxLang,
    rxToken,
    tt,
    type RxSide,
    type RxState,
} from './recon-center-x-store.js';
import {
    renderCard,
    renderBalance,
    updateReady,
    collectOverrides,
    showView,
    setTaskTitle,
    type RxView,
} from './recon-center-x-render.js';
import {
    openDrawer,
    closeDrawer,
    openGuide,
    closeModals,
    renderTemplates,
    downloadTemplate,
    downloadSide,
    downloadPageTemplates,
} from './recon-center-x-tpl.js';
import {
    fetchResult,
    renderResult,
    renderDetail,
    setFilter,
    exportResult,
    handleDifferences,
} from './recon-center-x-results.js';
import { loadHistory, openHistory, deleteHistory } from './recon-center-x-history.js';
import { bindGridDrop } from './recon-center-x-drag.js';

const $ = (id: string) => document.getElementById(id);
const MAX_BYTES = 25 * 1024 * 1024; // 25MB 单文件上限
let bannerHidden = false;
let bound = false;

function view(v: RxView) {
    showView(v, bannerHidden);
}

// 清本次对账的临时数据(切换类型/清空/返回共用)
function resetRxData() {
    RX.left = null;
    RX.right = null;
    RX.result = null;
    RX.jobId = null;
    RX.filter = 'all';
    RX.page = 1;
}

// ── tab 切换:换配置 + 清残留(文件/结果/余额/筛选)──────────────
function switchTab(tab: RxState['tab']) {
    if (tab === RX.tab) return;
    // 仅「有未保存的上传文件」才提醒;已完成/载入的结果已存历史可找回 → 不拦。
    const hasStaged = !!(RX.left || RX.right);
    const apply = () => {
        resetRxData();
        RX.tab = tab;
        document.querySelectorAll('#rcx-tabs .rcx-seg').forEach((b) => {
            const on = (b as HTMLElement).dataset.rcxTab === tab;
            b.classList.toggle('active', on);
            b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        setTaskTitle();
        renderCard('left');
        renderCard('right');
        renderBalance();
        renderTemplates();
        updateReady();
        view('workspace');
        loadHistory();
    };
    if (hasStaged && typeof window.showConfirm === 'function') {
        window
            .showConfirm(tt('rcx-switch-msg', '切换后将清空当前已上传的文件和结果，确定继续吗？'), {
                title: tt('rcx-switch-title', '切换对账类型'),
            })
            .then((ok) => {
                if (ok) apply();
            });
    } else {
        apply();
    }
}

// ── 上传:选择/拖拽同一处理函数 ───────────────────────────────────
function handleFiles(side: RxSide, files: FileList | File[] | null | undefined) {
    if (!files || !files.length) return;
    if (files.length > 1 && window.showToast)
        window.showToast(tt('rcx-multi-one', '每个区域一次只读取一个文件，已取第一个'), 'info');
    const file = files[0];
    if (!/\.(pdf|png|jpe?g|webp|tiff|xlsx|xls|csv|docx?)$/i.test(file.name)) {
        if (window.showToast) window.showToast(tt('rcx-bad-format', '不支持的文件格式'), 'error');
        return;
    }
    if (file.size > MAX_BYTES) {
        if (window.showToast) window.showToast(tt('rcx-too-big', '文件过大（上限 25MB）'), 'error');
        return;
    }
    RX[side] = { file, method: rxClassify(file.name), ext: rxExt(file.name), size: file.size };
    renderCard(side);
    updateReady();
}

function removeFile(side: RxSide) {
    RX[side] = null;
    renderCard(side);
    updateReady();
    if (window.showToast) window.showToast(tt('rcx-removed', '已移除文件'), 'info');
}

function previewFile(side: RxSide) {
    const d = RX[side];
    if (!d) return;
    // 真实预览:打开用户自己的文件 blob(PDF/图片浏览器内置预览;表格/Word 由浏览器处理)
    const url = URL.createObjectURL(d.file);
    window.open(url, '_blank');
    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

function clearAll() {
    const hasStaged = !!(RX.left || RX.right);
    const apply = () => {
        resetRxData();
        renderCard('left');
        renderCard('right');
        renderBalance();
        updateReady();
        view('workspace');
    };
    if (hasStaged && typeof window.showConfirm === 'function') {
        window
            .showConfirm(tt('rcx-clear-msg', '确定清空本次对账内容吗？未保存的修改将丢失。'), {
                title: tt('rcx-clear-title', '清空本次对账'),
                danger: true,
            })
            .then((ok) => {
                if (ok) apply();
            });
    } else {
        apply();
    }
}

// ── 开始对账:submit → 轮询 → 诚实进度 → 结果 ────────────────────
function setProcessingSub(text: string) {
    const el = $('rcx-processing-sub');
    if (el) el.textContent = text || '';
}

async function start() {
    if (RX.running || !RX.left || !RX.right) return;
    const cfg = rxCfg();
    RX.running = true;
    updateReady();
    view('processing');
    setProcessingSub('');
    const token = rxToken();
    const lang = rxLang();
    try {
        const fd = new FormData();
        fd.append(cfg.leftField, RX.left.file, RX.left.file.name);
        fd.append(cfg.rightField, RX.right.file, RX.right.file.name);
        fd.append('lang', lang);
        collectOverrides(fd);

        const submitRes = await fetch(cfg.submit, {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token },
            body: fd,
        });
        let sub: any = null;
        try {
            sub = await submitRes.json();
        } catch {
            sub = null;
        }
        // 提交即需『确认字段对应』(普通表格)→ 复用现有面板,确认保存后重跑
        if (sub && sub.needs_mapping) {
            RX.running = false;
            if (window.ReconMapping) {
                view('workspace');
                window.ReconMapping.show(sub, { token, lang, onConfirmed: () => start() });
            } else {
                fail(tt('rcx-err-server', '服务器繁忙，请稍后重试'));
            }
            return;
        }
        if (!submitRes.ok || !sub || !sub.ok || !sub.job_id) {
            RX.running = false;
            const msg =
                sub && (sub.detail || sub.error)
                    ? String(sub.detail || sub.error)
                    : tt('rcx-err-server', '服务器繁忙，请稍后重试');
            fail(msg);
            return;
        }

        RX.jobId = sub.job_id;
        const job: any = await window._reconPollJob(sub.job_id, token, {
            onProgress: (p: unknown) => setProcessingSub(window._reconProgressText(p as any, lang)),
        });
        await afterPoll(job, token, lang);
    } catch (e) {
        RX.running = false;
        fail((e as Error).message || tt('rcx-err-network', '网络错误'));
    }
}

async function afterPoll(job: any, token: string, lang: string) {
    // 后台解析认不出列 → 弹『确认字段对应』(防御纵深)
    if (job && job.status === 'needs_mapping' && job.mapping) {
        RX.running = false;
        view('workspace');
        if (window.ReconMapping)
            window.ReconMapping.show(job.mapping, { token, lang, onConfirmed: () => start() });
        else fail(tt('rcx-err-server', '服务器繁忙，请稍后重试'));
        return;
    }
    // 读取结果需确认 → 弹『确认需要关注的内容』,确认后用修正行重对账
    if (job && job.status === 'needs_review' && job.review) {
        RX.running = false;
        view('workspace');
        if (window.ReconReview) {
            window.ReconReview.show(job.review, {
                token,
                lang,
                jobId: RX.jobId,
                onConfirmed: async (newJobId: string) => {
                    RX.running = true;
                    view('processing');
                    const j2: any = await window._reconPollJob(newJobId, token, {
                        onProgress: (p: unknown) =>
                            setProcessingSub(window._reconProgressText(p as any, lang)),
                    });
                    await afterPoll(j2, token, lang);
                },
            });
        } else {
            fail(tt('rcx-err-server', '服务器繁忙，请稍后重试'));
        }
        return;
    }
    if (!job || job.status === 'failed' || job.status === 'timeout' || job.status !== 'done') {
        RX.running = false;
        fail(failMsg(job && job.error_code));
        return;
    }
    // done → 取结果 + 适配 + 渲染
    const resultId = job.result_id || RX.jobId;
    const res = await fetchResult(rxCfg().kind, resultId);
    RX.running = false;
    if (!res) {
        fail(tt('rcx-err-result', '结果读取失败，请重试'));
        return;
    }
    RX.result = res;
    // 结果已落库(可在历史找回)→ 清掉已消费的上传文件,使其后切换不再误提示「清空」。
    RX.left = null;
    RX.right = null;
    renderCard('left');
    renderCard('right');
    updateReady();
    loadHistory();
    view('results');
    renderResult();
}

// 结果视图「返回」:回工作区(结果已存历史 · 无数据丢失)
function backToWorkspace() {
    RX.result = null;
    RX.filter = 'all';
    view('workspace');
}

function failMsg(code: string | null | undefined): string {
    const map: Record<string, string> = {
        timeout: tt('rcx-err-timeout', '处理超时，请稍后重试'),
        poll_unreachable: tt('rcx-err-network', '网络错误'),
    };
    return (code && map[code]) || tt('rcx-err-generic', '对账未能完成，请检查文件后重试');
}

function fail(msg: string) {
    const el = $('rcx-fail-text');
    if (el) el.textContent = msg;
    view('fail');
    updateReady();
}

// ── 事件绑定(委托)+ 初始化 ────────────────────────────────────
function bindOnce() {
    if (bound) return;
    bound = true;
    const root = document;

    // tab
    document
        .querySelectorAll('#rcx-tabs .rcx-seg')
        .forEach((b) =>
            b.addEventListener('click', () =>
                switchTab((b as HTMLElement).dataset.rcxTab as RxState['tab'])
            )
        );

    // 顶部 / 横幅 / 抽屉 / 弹窗 按钮
    const on = (id: string, fn: (e: Event) => void) => {
        const el = $(id);
        if (el) el.addEventListener('click', fn);
    };
    on('rcx-guide-btn', openGuide);
    on('rcx-template-btn', openDrawer);
    on('rcx-tplpanel-close', closeDrawer);
    on('rcx-tplpanel-overlay', closeDrawer);
    on('rcx-modal-overlay', closeModals);
    on('rcx-banner-download', (e) => downloadPageTemplates(e.currentTarget as HTMLButtonElement));
    on('rcx-tplpanel-download-all', (e) =>
        downloadPageTemplates(e.currentTarget as HTMLButtonElement)
    );
    on('rcx-banner-hide', () => {
        bannerHidden = true;
        const b = $('rcx-banner');
        if (b) b.classList.add('rcx-hidden');
        if (window.showToast)
            window.showToast(
                tt('rcx-banner-hidden', '已关闭本次提示，可在模板中心重新查看'),
                'info'
            );
    });
    on('rcx-clear-btn', clearAll);
    on('rcx-start-btn', start);
    on('rcx-export-btn', (e) => exportResult(e.currentTarget as HTMLButtonElement));
    on('rcx-handle-btn', handleDifferences);
    on('rcx-fail-retry', () => {
        if (RX.left && RX.right) start();
        else view('workspace');
    });
    on('rcx-fail-back', () => view('workspace'));
    on('rcx-back-btn', backToWorkspace);

    // 弹窗关闭按钮(X / 知道了 · 静态在 RCX_HTML 中)
    document
        .querySelectorAll('.rcx-modal-close')
        .forEach((b) => b.addEventListener('click', closeModals));

    // KPI 点击筛选
    document
        .querySelectorAll('#rcx-kpis .rcx-kpi')
        .forEach((k) =>
            k.addEventListener('click', () =>
                setFilter((k as HTMLElement).dataset.filter as RxState['filter'])
            )
        );

    // 委托:卡片内按钮(choose/remove/preview/下载侧模板)、模板抽屉下载、分页
    root.addEventListener('click', (e) => {
        const tgt = e.target as HTMLElement;
        const choose = tgt.closest('[data-rcx-choose]') as HTMLElement | null;
        if (choose) {
            const side = choose.dataset.rcxChoose as RxSide;
            const input = document.querySelector(
                `[data-rcx-input="${side}"]`
            ) as HTMLInputElement | null;
            if (input) input.click();
            return;
        }
        const rm = tgt.closest('[data-rcx-remove]') as HTMLElement | null;
        if (rm) return removeFile(rm.dataset.rcxRemove as RxSide);
        const pv = tgt.closest('[data-rcx-preview]') as HTMLElement | null;
        if (pv) return previewFile(pv.dataset.rcxPreview as RxSide);
        const dlS = tgt.closest('[data-rcx-dl-side]') as HTMLElement | null;
        if (dlS) {
            void downloadSide(dlS.dataset.rcxDlSide as RxSide);
            return;
        }
        const dlD = tgt.closest('[data-rcx-dl-doc]') as HTMLElement | null;
        if (dlD) {
            void downloadTemplate(dlD.dataset.rcxDlDoc as string);
            return;
        }
        const pg = tgt.closest('[data-rcx-page]') as HTMLElement | null;
        if (pg) {
            RX.page += pg.dataset.rcxPage === 'next' ? 1 : -1;
            if (RX.page < 1) RX.page = 1;
            renderDetail();
            return;
        }
        // 历史:删除按钮优先,否则点整行 → 载入该记录结果
        const histDel = tgt.closest('[data-rcx-hist-del]') as HTMLElement | null;
        if (histDel) {
            void deleteHistory(histDel.dataset.rcxHistDel as string);
            return;
        }
        const histRow = tgt.closest('[data-rcx-hist]') as HTMLElement | null;
        if (histRow) {
            void openHistory(histRow.dataset.rcxHist as string, () => view('results'));
            return;
        }
    });

    // 委托:卡片 file input change + 拖拽(选择/拖拽走同一 handleFiles)
    root.addEventListener('change', (e) => {
        const inp = e.target as HTMLElement;
        if (inp && inp.matches('[data-rcx-input]')) {
            const side = (inp as HTMLElement).dataset.rcxInput as RxSide;
            handleFiles(side, (inp as HTMLInputElement).files);
            (inp as HTMLInputElement).value = '';
        }
    });
    // 拖拽:容器级委托(卡片 innerHTML 重渲后仍生效)· 与「选择文件」走同一 handleFiles
    bindGridDrop(handleFiles);

    // 键盘:Esc 关弹窗/抽屉
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        const drawer = $('rcx-tplpanel');
        if (drawer && drawer.classList.contains('rcx-show')) {
            closeDrawer();
            return;
        }
        if (document.querySelector('.rcx-modal.rcx-show')) closeModals();
    });

    // 切语言重渲动态部分
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('rcx', () => {
            setTaskTitle();
            renderCard('left');
            renderCard('right');
            renderBalance();
            renderTemplates();
            updateReady();
            loadHistory();
            if (RX.result) {
                renderResult();
            }
        });
    }
}

function init() {
    const root = $('rcx-root');
    if (!root) return;
    bindOnce();
    setTaskTitle();
    renderCard('left');
    renderCard('right');
    renderBalance();
    renderTemplates();
    updateReady();
    view('workspace');
    loadHistory();
}

// 路由进对账页时初始化(覆盖旧 loadReconcilePage:旧统计首页 DOM 已被重设计替换)
window.loadReconcilePage = async function () {
    init();
};
document.addEventListener('DOMContentLoaded', () => {
    if ($('rcx-root')) init();
});
