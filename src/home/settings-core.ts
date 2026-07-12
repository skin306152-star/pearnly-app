/* REFACTOR-C1-home-batch7 · 设置页 / 个人资料 / 公司信息
 * 从 home.js verbatim 抽出(0 逻辑改):switchSettingsTab / fillSettingsForms /
 * saveProfile / saveCompany / renderSettings(加载关于/首选项面板 + API Key 卡显隐)。
 *
 * 桥接说明:
 * - 5 个对外函数 window.X=X 挂出 —— home.js 的 initSettingsTabs/bindSettingsForms
 *   两个 IIFE(留在 home.js)在 DOMContentLoaded 裸调 switchSettingsTab/saveProfile/
 *   saveCompany;home.js 用户初始化裸调 fillSettingsForms;applyLang/routeTo 裸调
 *   renderSettings(三处已在 home.js 加 `typeof window.X==='function'` 引导期守卫)。
 * - saveProfile/saveCompany 重新赋值 _userInfo(home.js 顶层 let · 跨 realm 词法绑定可写)
 *   → eslint.config.mjs 已把 _userInfo 从 readonly 改 writable。
 * - renderSettings 内 `tt`(原 home.js 即如此)是历史遗留:唯一 `const tt` 在别的
 *   函数里,此处引用的是不存在的全局,但被 `if(apiKeyCard)` 守住(BYO API Key 已永久
 *   下线 · #api-key-card 不存在)→ 该分支永不执行。verbatim 保真 · 列入下方 global
 *   注释过 no-undef。
 */
/* global escapeHtml, apiGet, apiPut, shouldHideMoney, renderBrandWorkspace, tt */

// v118.10 · 设置页 · 二级 tab 切换
function switchSettingsTab(tabName: any) {
    if (!tabName) return;
    // v118.12.3 · 员工守卫:阻止切到隐藏的 tab(api/company · team/plan 已下线)
    // 防止 localStorage 恢复把员工带到隐藏 panel
    try {
        if (typeof shouldHideMoney === 'function' && shouldHideMoney(_userInfo)) {
            if (['api', 'company'].indexOf(tabName) >= 0) {
                tabName = 'profile';
                try {
                    localStorage.setItem('mrpilot_settings_tab', 'profile');
                } catch (e) {}
            }
        }
    } catch (e) {
        /* noop */
    }
    document.querySelectorAll('.settings-tab').forEach((t) => {
        t.classList.toggle('active', (t as HTMLElement).dataset.tab === tabName);
    });
    document.querySelectorAll('.settings-pane').forEach((p) => {
        p.classList.toggle('active', (p as HTMLElement).dataset.pane === tabName);
    });
    try {
        localStorage.setItem('mrpilot_settings_tab', tabName);
    } catch (e) {}
    // v118.10.1 · 切到 about / notifications 时调对应 load 函数(渲染联系方式 / 偏好开关)
    try {
        if (tabName === 'about' && typeof window.loadAboutPanel === 'function')
            window.loadAboutPanel();
        if (tabName === 'notifications' && typeof window.loadPrefsSettings === 'function')
            window.loadPrefsSettings();
        // v118.21.2 · 切到 learned tab 时加载学习规则
        if (tabName === 'learned' && typeof window.loadLearnedRules === 'function')
            window.loadLearnedRules();
    } catch (e) {
        console.warn('settings tab side effect failed:', e);
    }
}

// v118.10 · 设置页 · 预填充个人资料 + 公司信息表单
function fillSettingsForms(u: any) {
    if (!u) return;
    const set = (id: string, val: any) => {
        const el = document.getElementById(id);
        if (el) (el as HTMLInputElement).value = val || '';
    };
    set('profile-username', u.username || '');
    set('profile-email', u.username || ''); // 当前后端 email == username
    set('profile-fullname', u.full_name || '');
    set('profile-phone', u.phone || '');
    set('profile-country', u.country || 'TH');
    set('profile-line', u.line_id || '');
    set('company-name', u.company_name || '');
    set('company-volume', u.monthly_volume || '');
    set('company-role', u.user_role || u.role_self || '');
}

// v118.10 · 保存个人资料
async function saveProfile() {
    const btn = document.getElementById('btn-save-profile') as HTMLButtonElement;
    const msg = document.getElementById('profile-save-msg');
    if (!btn) return;
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span>${t('msg-saving') || '保存中...'}</span>`;
    if (msg) {
        msg.textContent = '';
        msg.classList.remove('error');
    }
    try {
        const payload = {
            full_name:
                ((document.getElementById('profile-fullname') || {}) as HTMLInputElement).value ||
                '',
            phone:
                ((document.getElementById('profile-phone') || {}) as HTMLInputElement).value || '',
            country:
                ((document.getElementById('profile-country') || {}) as HTMLInputElement).value ||
                'TH',
            line_id:
                ((document.getElementById('profile-line') || {}) as HTMLInputElement).value || '',
        };
        const r = await apiPut('/api/me/profile', payload);
        if (r && r.ok) {
            if (msg) msg.textContent = t('msg-saved') || '已保存';
            // 刷新用户信息(让顶栏公司名 / 姓名同步)
            try {
                const fresh = await apiGet('/api/me');
                _userInfo = fresh;
                try {
                    window._userInfo = fresh;
                } catch (_) {
                    /* silent · workspace-switcher 读它判 owner */
                }
                renderBrandWorkspace();
            } catch (e) {}
        } else {
            throw new Error('save failed');
        }
    } catch (e) {
        if (msg) {
            msg.textContent = t('msg-save-failed') || '保存失败';
            msg.classList.add('error');
        }
    } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
        setTimeout(() => {
            if (msg) msg.textContent = '';
        }, 3000);
    }
}

// v118.10 · 保存公司信息
async function saveCompany() {
    const btn = document.getElementById('btn-save-company') as HTMLButtonElement;
    const msg = document.getElementById('company-save-msg');
    if (!btn) return;
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span>${t('msg-saving') || '保存中...'}</span>`;
    if (msg) {
        msg.textContent = '';
        msg.classList.remove('error');
    }
    try {
        const payload = {
            company_name:
                ((document.getElementById('company-name') || {}) as HTMLInputElement).value || '',
            monthly_volume:
                ((document.getElementById('company-volume') || {}) as HTMLInputElement).value || '',
            role: ((document.getElementById('company-role') || {}) as HTMLInputElement).value || '',
        };
        const r = await apiPut('/api/me/profile', payload);
        if (r && r.ok) {
            if (msg) msg.textContent = t('msg-saved') || '已保存';
            // 刷新顶栏公司名(关键体验)
            try {
                const fresh = await apiGet('/api/me');
                _userInfo = fresh;
                try {
                    window._userInfo = fresh;
                } catch (_) {
                    /* silent · workspace-switcher 读它判 owner */
                }
                renderBrandWorkspace();
            } catch (e) {}
        } else {
            throw new Error('save failed');
        }
    } catch (e) {
        if (msg) {
            msg.textContent = t('msg-save-failed') || '保存失败';
            msg.classList.add('error');
        }
    } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
        setTimeout(() => {
            if (msg) msg.textContent = '';
        }, 3000);
    }
}

// 设置页 · 进入时加载联系我们 + 首选项面板,并按账号类型显隐 API Key 卡片。
// (原「用量」面板已删 · 计费说明移到充值弹窗 · 此处不再渲染 #settings-info)
function renderSettings() {
    if (!_userInfo) return;
    if (typeof window.loadAboutPanel === 'function') window.loadAboutPanel();
    if (typeof window.loadPrefsSettings === 'function') window.loadPrefsSettings();

    // API Key 卡片:买断账号(tenant_type=byo_api)或超管可见(测试 + 管理需要)。
    const apiKeyCard = document.getElementById('api-key-card');
    if (apiKeyCard) {
        const showCard =
            (tt as unknown as string) === 'byo_api' || (_userInfo && _userInfo.is_super_admin);
        apiKeyCard.style.display = showCard ? '' : 'none';
    }
}

// ── window 桥(home.js 的 IIFE / 用户初始化 / applyLang / routeTo + 其它模块裸调解析)──
window.switchSettingsTab = switchSettingsTab;
window.fillSettingsForms = fillSettingsForms;
window.saveProfile = saveProfile;
window.saveCompany = saveCompany;
window.renderSettings = renderSettings;
