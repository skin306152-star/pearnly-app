// REFACTOR-C1-home-batch9g1 · 从 home.js verbatim 抽出(0 逻辑改)
// 设置页 tab 点击绑定 + 保存按钮绑定(switchSettingsTab/saveProfile/saveCompany 经 window)
/* global switchSettingsTab, saveProfile, saveCompany */

// v118.10 · 设置页 · tab 点击绑定 + 持久化恢复
(function initSettingsTabs() {
    function bind() {
        const tabs = document.querySelectorAll<HTMLElement>('.settings-tab');
        if (!tabs.length) {
            setTimeout(bind, 200);
            return;
        }
        tabs.forEach((t) => {
            t.addEventListener('click', () => switchSettingsTab(t.dataset.tab!));
        });
        // 恢复上次 tab(若 tab 因权限隐藏 · 退回 profile)
        let saved = null;
        try {
            saved = localStorage.getItem('mrpilot_settings_tab');
        } catch (e) {}
        if (saved) {
            const target = document.querySelector<HTMLElement>(
                `.settings-tab[data-tab="${saved}"]`
            );
            if (target && target.style.display !== 'none') {
                switchSettingsTab(saved);
                return;
            }
        }
        switchSettingsTab('profile');
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else {
        bind();
    }
})();

// v118.10 · 绑定保存按钮
(function bindSettingsForms() {
    function bind() {
        const p = document.getElementById('btn-save-profile');
        const c = document.getElementById('btn-save-company');
        if (!p && !c) {
            setTimeout(bind, 200);
            return;
        }
        if (p) p.addEventListener('click', saveProfile);
        if (c) c.addEventListener('click', saveCompany);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else {
        bind();
    }
})();
