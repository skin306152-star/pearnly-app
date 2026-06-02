// ============================================================
// REFACTOR-C1 (2026-05-27) · 银行对账模块(M10)bank-recon 从 home.js 抽出为 ES module
// REFACTOR-WB (2026-06-02) · store 中心化 + 拆 6 子模块(store/helpers/queue/sessions/detail/drawer/picker)。
// currentRoute / t 为 eslint 内建全局(不重声明);load/bindEvents 不用 token/showConfirm。
// ============================================================
import { S } from './bank-recon-store.js';
import {
    refreshSessions,
    refreshSummary,
    renderSessionList,
    showListMode,
    handleDeleteSessionFromList,
} from './bank-recon-sessions.js';
import {
    loadSessionDetail,
    renderDetailMeta,
    renderTxTable,
    handleDeleteSession,
    handleRunMatch,
    handleIgnoreTx,
} from './bank-recon-detail.js';
import { closeCandDrawer } from './bank-recon-drawer.js';
import {
    _renderClientBadge,
    _openClientPicker,
    _closeClientPicker,
    _saveClientPicker,
} from './bank-recon-picker.js';
import { handleFilePick, _clearDone, renderQueue } from './bank-recon-queue.js';

async function load() {
    if (S.loaded) {
        refreshSummary();
        return;
    }
    S.loaded = true;
    bindEvents();
    await refreshSessions();
    refreshSummary();
}

function bindEvents() {
    // 上传(v118.26.1 · 批量)
    const input = document.getElementById('bank-file-input');
    if (input && !input._bound) {
        input._bound = true;
        input.addEventListener('change', handleFilePick);
    }
    // 清除已完成队列
    const btnClear = document.getElementById('btn-bank-queue-clear-done');
    if (btnClear && !btnClear._bound) {
        btnClear._bound = true;
        btnClear.addEventListener('click', _clearDone);
    }
    // 返回列表
    const btnBack = document.getElementById('btn-bank-back');
    if (btnBack && !btnBack._bound) {
        btnBack._bound = true;
        btnBack.addEventListener('click', () => {
            S.currentSession = null;
            S.currentTxs = [];
            showListMode();
        });
    }
    // 删除会话
    const btnDel = document.getElementById('btn-bank-delete');
    if (btnDel && !btnDel._bound) {
        btnDel._bound = true;
        btnDel.addEventListener('click', handleDeleteSession);
    }
    // 触发匹配
    const btnMatch = document.getElementById('btn-bank-run-match');
    if (btnMatch && !btnMatch._bound) {
        btnMatch._bound = true;
        btnMatch.addEventListener('click', handleRunMatch);
    }
    // 过滤按钮组(委托到容器)
    document.querySelectorAll('.bank-filter-btn').forEach((b) => {
        if (b._bound) return;
        b._bound = true;
        b.addEventListener('click', () => {
            S.currentFilter = b.dataset.bankFilter || 'all';
            document.querySelectorAll('.bank-filter-btn').forEach((x) => {
                x.classList.toggle('active', x === b);
            });
            renderTxTable();
        });
    });
    // 抽屉关闭(旧 fixed drawer · 保留兼容)
    document.querySelectorAll('[data-bank-cand-close]').forEach((e) => {
        if (e._bound) return;
        e._bound = true;
        e.addEventListener('click', closeCandDrawer);
    });
    // v118.26.2 · 新右半屏 pane 的 close 按钮(移动端 drawer 模式才显示)
    const btnPaneClose = document.getElementById('btn-bank-cand-pane-close');
    if (btnPaneClose && !btnPaneClose._bound) {
        btnPaneClose._bound = true;
        btnPaneClose.addEventListener('click', closeCandDrawer);
    }
    // 抽屉的忽略按钮(旧 + 新 pane)
    const btnIgn = document.getElementById('btn-bank-cand-ignore');
    if (btnIgn && !btnIgn._bound) {
        btnIgn._bound = true;
        btnIgn.addEventListener('click', handleIgnoreTx);
    }
    const btnIgnPane = document.getElementById('btn-bank-cand-ignore-pane');
    if (btnIgnPane && !btnIgnPane._bound) {
        btnIgnPane._bound = true;
        btnIgnPane.addEventListener('click', handleIgnoreTx);
    }
    // v118.26.2 · 客户徽章点击 · 老板可改 / 员工只读
    const badge = document.getElementById('bank-client-badge');
    if (badge && !badge._bound) {
        badge._bound = true;
        badge.addEventListener('click', _openClientPicker);
    }
    // v118.26.2 · 客户绑定 modal · close 按钮
    document.querySelectorAll('[data-bank-client-picker-close]').forEach((e) => {
        if (e._bound) return;
        e._bound = true;
        e.addEventListener('click', _closeClientPicker);
    });
    // v118.26.2 · 客户绑定 modal · 保存按钮
    const btnSave = document.getElementById('btn-bank-client-picker-save');
    if (btnSave && !btnSave._bound) {
        btnSave._bound = true;
        btnSave.addEventListener('click', _saveClientPicker);
    }
    // v118.26.1.1 · session list 顶部筛选 chip
    document.querySelectorAll('.bank-sessions-chip').forEach((b) => {
        if (b._bound) return;
        b._bound = true;
        b.addEventListener('click', () => {
            S.sessionFilter = b.dataset.sessFilter || 'all';
            document.querySelectorAll('.bank-sessions-chip').forEach((x) => {
                x.classList.toggle('active', x === b);
            });
            renderSessionList();
        });
    });
}

// 暴露给对账中心首页用
window._deleteBankSession = handleDeleteSessionFromList;

// 暴露
window._loadBankReconPanel = load;
window._rerenderBankRecon = function () {
    // v118.26.1.2 · 改成只渲染当前路由 · 防止其他页面无谓 DOM 操作
    if (currentRoute !== 'automation') return;
    renderSessionList();
    if (S.currentSession) {
        renderDetailMeta();
        renderTxTable();
        // v118.26.2 · 客户徽章文案随 t() 切换
        _renderClientBadge();
        // 候选 pane 空态文案随 t() 切换(只在没选流水时刷)
        if (!S.currentTxForDrawer) {
            const titleEl = document.getElementById('bank-cand-pane-title');
            const subEl = document.getElementById('bank-cand-pane-sub');
            if (titleEl) titleEl.textContent = t('bank-cand-pane-empty-title');
            if (subEl) subEl.textContent = t('bank-cand-pane-empty-sub');
        }
    }
    renderQueue();
};
// v118.26.1.2 · 注册到 i18n 订阅总线 · 切语言自动重渲(不再依赖 applyLang 散调用)
if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('bank-recon', window._rerenderBankRecon);
}

// v118.26.1 · 对账中心点最近会话卡 → 跳过来打开会话
window._openBankSession = async function (sessionId) {
    if (!sessionId) return;
    // 确保面板已 load · 否则 refreshSessions 没跑 · 顺序点击会跳空
    if (!S.loaded) {
        await load();
    }
    await loadSessionDetail(sessionId);
};
