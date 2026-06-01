import { ONBOARDING_HTML } from './welcome-wizard-html.js'; // REFACTOR-WB-C3 · onboarding 4 步骨架 HTML(home.html #onboarding-modal 抽出 · showOnboarding 懒注入)
// ============================================================
// REFACTOR-C1 (2026-05-27) · 登录后欢迎向导 welcome-wizard 从 home.js 抽出为 ES module
//
// 来源:home.js L15713-15907 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* eslint-disable no-unreachable -- verbatim home.js · wizard 暂下架(maybeShowOnboarding 内 early return)· return 后旧逻辑刻意保留 · 非 bug */
// ============================================================
// v110.7 · 登录后欢迎向导(B 方案 · 4 步渐进收集)
// 触发条件:用户首次进系统 · _userInfo.role 为空 · localStorage 未标记完成 / 24h 内跳过
// 提交接口:PUT /api/me/profile { role, monthly_volume, country, line_id }
// 后端 endpoint 由 Zihao 自己加到 app.py(本对话末尾给出代码片段)
// ============================================================
(function () {
    let _obData = { role: '', monthly_volume: '', country: '', line_id: '' };
    let _obStep = 1;
    const OB_TOTAL = 4;
    const OB_DISMISS_KEY = 'pilot_ob_dismiss';
    const OB_DONE_KEY = 'pilot_ob_done';
    const OB_DISMISS_HOURS = 24;

    // 暴露给 loadAll 调用
    window.maybeShowOnboarding = function (user) {
        // v118.12.6 · onboarding wizard 暂时下架(无个性化推荐 · 弹了反而干扰)
        // 触发机制:本来基于 localStorage(OB_DONE_KEY / OB_DISMISS_KEY)+ 后端 profile_filled
        // 但无痕模式 localStorage 空 · 后端字段又不能保证总 true · 干脆直接关
        // 要恢复:删除下面这行 return · 旧逻辑完整保留在下方
        return;
        try {
            // 已永久关闭(填完 / 主动跳过)→ 不再弹
            if (localStorage.getItem(OB_DONE_KEY) === '1') return;
            // 24h 内暂时关闭 → 不弹
            const dismissTs = parseInt(localStorage.getItem(OB_DISMISS_KEY) || '0', 10);
            if (dismissTs && Date.now() - dismissTs < OB_DISMISS_HOURS * 3600 * 1000) return;
            // v110.7 · 用 profile_filled 判断(后端会保护性默认 role="owner" · 不能直接看 role)
            // profile_filled = role / monthly_volume / country / line_id 任一非空
            if (user && user.profile_filled === true) {
                localStorage.setItem(OB_DONE_KEY, '1');
                return;
            }
            // 满足条件 · 弹向导(延迟 800ms 让页面先渲染完)
            setTimeout(showOnboarding, 800);
        } catch (e) {
            console.error('maybeShowOnboarding', e);
        }
    };

    function showOnboarding() {
        const modal = document.getElementById('onboarding-modal');
        if (!modal) return;
        // REFACTOR-WB-C3 · 骨架抽到 welcome-wizard-html.js · 首次显示时懒注入(空壳 → 完整向导)+ 子树初译
        if (modal.dataset.wbInjected !== '1') {
            modal.innerHTML = ONBOARDING_HTML;
            modal.dataset.wbInjected = '1';
            try {
                const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
                const I = window.I18N;
                if (I && I[lang]) {
                    modal.querySelectorAll('[data-i18n]').forEach((el) => {
                        const k = el.getAttribute('data-i18n');
                        if (I[lang][k]) el.textContent = I[lang][k];
                    });
                    modal.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                        const k = el.getAttribute('data-i18n-placeholder');
                        if (I[lang][k]) el.placeholder = I[lang][k];
                    });
                }
            } catch (e) {
                /* silent · 初译失败不致命 · 切语言会补 */
            }
        }
        _obStep = 1;
        _obData = { role: '', monthly_volume: '', country: '', line_id: '' };
        // 预填用户已有的字段(如果有)
        if (window._userInfo) {
            _obData.role = window._userInfo.role || '';
            _obData.monthly_volume = window._userInfo.monthly_volume || '';
            _obData.country = window._userInfo.country || '';
            _obData.line_id = window._userInfo.line_id || '';
        }
        gotoStep(1);
        modal.style.display = 'flex';
    }

    function gotoStep(n) {
        _obStep = n;
        for (let i = 1; i <= OB_TOTAL; i++) {
            const el = document.getElementById('ob-step-' + i);
            if (el) el.style.display = i === n ? 'block' : 'none';
        }
        // 进度圆点
        document.querySelectorAll('.ob-dot').forEach((dot) => {
            const s = parseInt(dot.dataset.step, 10);
            dot.classList.toggle('active', s === n);
            dot.classList.toggle('done', s < n);
        });
        const lbl = document.getElementById('ob-step-label');
        if (lbl) lbl.textContent = n + ' / ' + OB_TOTAL;
        // 按钮文案 · 最后一步是「完成」
        const nextBtn = document.getElementById('ob-next');
        if (nextBtn) {
            nextBtn.textContent = n === OB_TOTAL ? t('ob-finish') : t('ob-next');
        }
        // 第 4 步预填 LINE input
        if (n === 4) {
            const inp = document.getElementById('ob-line-input');
            if (inp) inp.value = _obData.line_id || '';
        }
    }

    function showFeedback(msg) {
        const modal = document.querySelector('.onboarding-modal');
        if (!modal) return;
        let fb = modal.querySelector('.ob-feedback');
        if (!fb) {
            fb = document.createElement('div');
            fb.className = 'ob-feedback';
            modal.appendChild(fb);
        }
        fb.textContent = msg;
        fb.classList.add('show');
        setTimeout(() => fb.classList.remove('show'), 1800);
    }

    // 选项点击(所有 .ob-option 共用)
    document.addEventListener('click', (e) => {
        const opt = e.target.closest('.ob-option');
        if (!opt) return;
        const wrap = opt.parentElement;
        if (!wrap || !wrap.classList.contains('ob-options')) return;
        // 选中视觉 + 记录
        wrap.querySelectorAll('.ob-option').forEach((o) => o.classList.remove('selected'));
        opt.classList.add('selected');
        const value = opt.dataset.value;
        if (wrap.id === 'ob-role-options') _obData.role = value;
        else if (wrap.id === 'ob-volume-options') _obData.monthly_volume = value;
        else if (wrap.id === 'ob-country-options') _obData.country = value;
    });

    // 跳过当前步
    document.addEventListener('click', (e) => {
        if (e.target.id !== 'ob-skip') return;
        // 当前步骤的字段不填 · 直接进下一步
        nextStepOrFinish();
    });

    // 下一步 / 完成
    document.addEventListener('click', (e) => {
        if (e.target.id !== 'ob-next') return;
        // 第 4 步收集 LINE input
        if (_obStep === 4) {
            const inp = document.getElementById('ob-line-input');
            _obData.line_id = ((inp && inp.value) || '').trim().replace(/^@+/, '');
        }
        nextStepOrFinish();
    });

    // 关闭按钮(右上 X)· 24h 不再弹
    document.addEventListener('click', (e) => {
        if (e.target.closest('#ob-close')) {
            localStorage.setItem(OB_DISMISS_KEY, String(Date.now()));
            const m = document.getElementById('onboarding-modal');
            if (m) m.style.display = 'none';
        }
    });

    function nextStepOrFinish() {
        // 价值反馈(填了才反馈 · 跳过不反馈)
        if (_obStep === 1 && _obData.role) showFeedback(t('ob-fb-role'));
        else if (_obStep === 2 && _obData.monthly_volume) showFeedback(t('ob-fb-volume'));
        else if (_obStep === 3 && _obData.country) showFeedback(t('ob-fb-country'));
        else if (_obStep === 4 && _obData.line_id) showFeedback(t('ob-fb-line'));

        if (_obStep < OB_TOTAL) {
            setTimeout(
                () => gotoStep(_obStep + 1),
                _obData[Object.keys(_obData)[_obStep - 1]] ? 350 : 0
            );
        } else {
            finishOnboarding();
        }
    }

    async function finishOnboarding() {
        const modal = document.getElementById('onboarding-modal');
        // 标记完成(无论后端成功失败都不再弹)
        localStorage.setItem(OB_DONE_KEY, '1');
        // 清理 dismiss 标记
        localStorage.removeItem(OB_DISMISS_KEY);

        // 提交到后端
        const payload = {};
        if (_obData.role) payload.role = _obData.role;
        if (_obData.monthly_volume) payload.monthly_volume = _obData.monthly_volume;
        if (_obData.country) payload.country = _obData.country;
        if (_obData.line_id) payload.line_id = _obData.line_id;

        if (Object.keys(payload).length === 0) {
            // 全部跳过 · 不需要请求
            if (modal) modal.style.display = 'none';
            return;
        }

        try {
            const resp = await fetch('/api/me/profile', {
                method: 'PUT',
                headers: {
                    Authorization:
                        'Bearer ' + (window.token || localStorage.getItem('mrpilot_token')),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });
            if (resp.ok) {
                showFeedback(t('ob-fb-done'));
                // 更新本地 _userInfo
                if (window._userInfo) Object.assign(window._userInfo, payload);
                setTimeout(() => {
                    if (modal) modal.style.display = 'none';
                }, 1200);
            } else {
                // 后端没接口 / 失败 · 数据保留在 localStorage 备份
                localStorage.setItem('pilot_ob_pending', JSON.stringify(payload));
                console.warn('onboarding profile save failed', resp.status);
                showFeedback(t('ob-fb-saved-local'));
                setTimeout(() => {
                    if (modal) modal.style.display = 'none';
                }, 1500);
            }
        } catch (err) {
            console.error('onboarding submit', err);
            localStorage.setItem('pilot_ob_pending', JSON.stringify(payload));
            if (modal) modal.style.display = 'none';
        }
    }
})();
