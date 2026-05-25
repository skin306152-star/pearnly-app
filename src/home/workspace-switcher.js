// ============================================================
// B4 (2026-05-25) · Workspace 切换器(账套主体 = "在为哪家公司做账")
//
// 非破坏 · 并行能力:
//   - 与旧 ClientSwitcher(localStorage 'pearnly_current_client_id' = 发票买方维度)
//     **完全分离**:本模块用独立键 'pearnly_active_workspace_client_id'。
//   - 不强制(B1)、不弹登录窗(B2)—— 那两步等 Zihao 确认后再做。
//   - 数据源:GET /api/workspace/clients(workspace_routes.py · B4 后端)。
//
// ⚠️ 尚未接入 bundle 入口(src/home/index 之类)与 home UI —— 故意如此:
//   接入需动构建/home.js,留到 Codex 验收 + Zihao 确认上线后再做(见文末 INTEGRATION)。
//   本文件先作为 reviewable 的并行能力落库。
//
// 依赖 home.js 暴露的全局:apiGet / showToast / t / subscribeI18n(运行时已就绪)。
// 入口:window.loadWorkspaceSwitcher(el) 渲染;window.getActiveWorkspaceClientId()。
// 事件:选中后派发 CustomEvent('pearnly:workspace-changed', {detail:{id}})。
// ============================================================
(function () {
    'use strict';

    const LS_KEY = 'pearnly_active_workspace_client_id';

    // ---------- 状态 API(供其它模块/上传请求读取) ----------
    function getActiveWorkspaceClientId() {
        const v = localStorage.getItem(LS_KEY);
        if (!v || v === 'null' || v === '0' || v === '') return null;
        const n = parseInt(v, 10);
        return isNaN(n) ? null : n;
    }

    function setActiveWorkspaceClientId(id) {
        const old = getActiveWorkspaceClientId();
        if (id == null || id === 0) {
            localStorage.removeItem(LS_KEY);
        } else {
            localStorage.setItem(LS_KEY, String(id));
        }
        if (String(old) !== String(id)) {
            try {
                window.dispatchEvent(
                    new CustomEvent('pearnly:workspace-changed', { detail: { id: id } })
                );
            } catch {
                /* no-op */
            }
        }
    }

    // ---------- 数据 ----------
    async function fetchWorkspaceClients() {
        try {
            const fn = window.apiGet;
            if (typeof fn !== 'function') return [];
            const res = await fn('/api/workspace/clients');
            return (res && (res.clients || res.items)) || [];
        } catch {
            return [];
        }
    }

    // ---------- 渲染(并行 UI · 不替换顶栏旧切换器) ----------
    async function loadWorkspaceSwitcher(targetEl) {
        const el = targetEl || document.getElementById('workspace-switcher-root') || null;
        if (!el) return;
        const list = await fetchWorkspaceClients();
        const active = getActiveWorkspaceClientId();
        const _t = typeof window.t === 'function' ? window.t : (k) => k;

        if (!list.length) {
            // 0 个:不弹窗(B2 才弹)· 仅提示
            el.innerHTML = '<div class="ws-empty">' + _t('ws-none-hint') + '</div>';
            return;
        }

        const opts = list
            .map(function (c) {
                const sel = String(c.id) === String(active) ? ' selected' : '';
                const name = (c.name || '').replace(/</g, '&lt;');
                return '<option value="' + c.id + '"' + sel + '>' + name + '</option>';
            })
            .join('');
        el.innerHTML =
            '<label class="ws-label">' +
            _t('ws-current-label') +
            '</label>' +
            '<select class="ws-select" id="ws-select">' +
            opts +
            '</select>';

        const sel = el.querySelector('#ws-select');
        if (sel) {
            sel.addEventListener('change', function () {
                const id = parseInt(sel.value, 10);
                setActiveWorkspaceClientId(isNaN(id) ? null : id);
                if (typeof window.showToast === 'function') {
                    window.showToast(_t('ws-switched'), 'info');
                }
            });
        }
    }

    // ---------- 暴露 ----------
    window.getActiveWorkspaceClientId = getActiveWorkspaceClientId;
    window.setActiveWorkspaceClientId = setActiveWorkspaceClientId;
    window.loadWorkspaceSwitcher = loadWorkspaceSwitcher;
    window.fetchWorkspaceClients = fetchWorkspaceClients;

    // 切语言重渲(若已渲染过)
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('workspace-switcher', function () {
            const el = document.getElementById('workspace-switcher-root');
            if (el && el.childElementCount) loadWorkspaceSwitcher(el);
        });
    }

    // ============================================================
    // INTEGRATION(待 Zihao 确认上线后做 · 本期不做):
    //  1. 在 bundle 入口 import 本模块;home 顶栏加 <div id="workspace-switcher-root">。
    //  2. 上传/对账/推送请求带 header 'X-Workspace-Client-Id': getActiveWorkspaceClientId()
    //     (后端 B1 相 1 先"可写不强制",相 2 再强制)。
    //  3. i18n 4 语补:ws-none-hint / ws-current-label / ws-switched。
    //  4. B2 登录弹窗:0 个→引导建/空状态;1 个→自动选;>1→弹窗(红线·先过方案)。
    // ============================================================
})();
