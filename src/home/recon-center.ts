// ============================================================
// REFACTOR-C1 (2026-05-27) · 对账中心首页(Reconcile Center 首页)从 home.js 抽出为 ES module
//
// 来源:home.js L17825-18151 的「对账中心顶级菜单首页加载」IIFE(v118.26.0)。
// 加载顺序:home.html <script src=home.js>(sync)先跑暴露公共全局 → 本 module
//   (Vite bundle · type=module defer)后跑。入口 window.loadReconcilePage 由 home.js 路由
//   (routeTo · L845)+ boot 补偿(setTimeout(0) · 晚于 defer module 执行)经 window 调,
//   执行时本 module 已注册,故安全。
// 依赖的全局(home.js 暴露 · bare 调 · 不 import):t / showToast / token / _userInfo /
//   currentRoute / window.{routeTo,navigateTo,subscribeI18n,_bankReconV2Init,_deleteBankSession,_openBankSession}。
// verbatim 搬迁 · 0 改逻辑(仅 prettier 重排格式)。
// ============================================================
/* global token */
// ============================================================
// v118.26.0 · 对账中心顶级菜单首页加载
// ============================================================
(function () {
    'use strict';

    const elNum = (key: string) => document.querySelector('[data-num-target="' + key + '"]');

    function _formatLastActivity(isoStr: string | null | undefined) {
        if (!isoStr) return t('reconcile-last-activity-none');
        try {
            const then = new Date(isoStr);
            const now = new Date();
            const diffMs = (now as unknown as number) - (then as unknown as number);
            const diffMin = diffMs / 60000;
            if (diffMin < 5) return t('reconcile-last-activity-just-now');
            // 同一日历日(BKK · 浏览器本地)算「今天」
            if (then.toDateString() === now.toDateString()) {
                return t('reconcile-last-activity-today');
            }
            const diffDays = Math.max(1, Math.floor(diffMs / (24 * 3600 * 1000)));
            return t('reconcile-last-activity-days-ago').replace(
                '{n}',
                diffDays as unknown as string
            );
        } catch (e) {
            return t('reconcile-last-activity-none');
        }
    }

    function _setNum(key: string, val: unknown, isEmpty: unknown) {
        const el = elNum(key);
        if (!el) return;
        el.textContent = isEmpty ? '-' : String(val);
        el.classList.toggle('is-empty', !!isEmpty);
    }

    function _showError(show: unknown) {
        const e = document.getElementById('reconcile-error');
        if (e) e.style.display = show ? 'flex' : 'none';
    }
    function _showEmpty(show: unknown) {
        const e = document.getElementById('reconcile-empty');
        if (e) e.style.display = show ? 'flex' : 'none';
    }
    function _setLastActivityText(text: string, hasData: unknown) {
        const el = document.getElementById('reconcile-last-activity');
        if (!el) return;
        el.textContent = text;
        el.classList.toggle('has-data', !!hasData);
    }

    function _renderStats(stats: any) {
        const isEmpty = !stats || (stats.total_sessions || 0) === 0;
        _setNum('pending', stats.pending || 0, isEmpty);
        _setNum('matched', stats.matched || 0, isEmpty);
        _setNum('unmatched', stats.unmatched || 0, isEmpty);
        _setLastActivityText(_formatLastActivity(stats.last_activity_at), !!stats.last_activity_at);
        _showError(false);
        // 有数据 → 隐藏空态(下面会显示最近对账列表 / 由 _renderRecent 控制)
        // 无数据 → 显示空态(下面 _renderRecent 会隐藏 recent 区块)
        _showEmpty(isEmpty);
    }

    // v118.26.1 · 最近对账列表渲染(有数据时显示 · 替代空态)
    function _bankChipClass(code: string | null | undefined) {
        const c = (code || '').toUpperCase();
        if (c === 'KBANK') return 'bank-chip-kbank';
        if (c === 'SCB') return 'bank-chip-scb';
        if (c === 'BBL') return 'bank-chip-bbl';
        if (c === 'KTB') return 'bank-chip-ktb';
        if (c === 'TTB') return 'bank-chip-ttb';
        return 'bank-chip-other';
    }

    function _fmtPeriodShort(start: unknown, end: unknown) {
        const fmt = (s: unknown) => (s ? String(s).slice(0, 10) : '?');
        if (!start && !end) return '';
        return fmt(start) + ' ~ ' + fmt(end);
    }

    function _esc(s: unknown) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function _renderRecent(sessions: any[]) {
        const wrap = document.getElementById('reconcile-recent');
        const list = document.getElementById('reconcile-recent-list');
        if (!wrap || !list) return;
        const items = (sessions || []).slice(0, 20);
        if (items.length === 0) {
            wrap.style.display = 'none';
            return;
        }
        wrap.style.display = '';
        // 有列表时空态隐藏
        _showEmpty(false);

        list.innerHTML = items
            .map((s: any) => {
                const failed = s.parse_status === 'parse_failed';
                const bankCode = s.bank_code || 'OTHER';
                const acct = s.account_last4 ? ' ···' + _esc(s.account_last4) : '';
                const period = _fmtPeriodShort(s.period_start, s.period_end);
                const fname = _esc(s.source_filename || '');
                const txN = Number(s.tx_count || 0);
                const status = failed
                    ? '<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">' +
                      t('reconcile-card-parse-failed') +
                      '</span>'
                    : '<span class="recon-card-tx">' +
                      t('reconcile-card-tx').replace('{n}', txN as unknown as string) +
                      '</span>';
                // v118.26.1.1 · hover 出垃圾桶 · 直接删该会话(共用 _deleteBankSession)
                return (
                    '<div class="recon-card" data-session-id="' +
                    _esc(s.id) +
                    '" data-session-name="' +
                    fname +
                    '">' +
                    '<span class="bank-chip ' +
                    _bankChipClass(bankCode) +
                    '">' +
                    _esc(bankCode) +
                    '</span>' +
                    '<div class="recon-card-main">' +
                    '<div class="recon-card-title">' +
                    fname +
                    acct +
                    '</div>' +
                    '<div class="recon-card-sub">' +
                    _esc(period) +
                    '</div>' +
                    '</div>' +
                    '<div class="recon-card-right">' +
                    status +
                    '</div>' +
                    '<button class="recon-card-trash" data-trash="' +
                    _esc(s.id) +
                    '" title="' +
                    _esc(t('bank-session-delete-tip') || '删除') +
                    '">' +
                    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' +
                    '<path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>' +
                    '</svg>' +
                    '</button>' +
                    '<svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>' +
                    '</div>'
                );
            })
            .join('');

        list.querySelectorAll('.recon-card').forEach((c) => {
            c.addEventListener('click', (e) => {
                if ((e.target as HTMLElement).closest('.recon-card-trash')) return; // 点的是垃圾桶
                const sid = (c as HTMLElement).dataset.sessionId;
                _gotoBankSession(sid);
            });
        });
        list.querySelectorAll('.recon-card-trash').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const sid = (btn as HTMLElement).dataset.trash;
                const card = btn.closest('.recon-card');
                const fname = card ? (card as HTMLElement).dataset.sessionName || '' : '';
                if (typeof window._deleteBankSession === 'function') {
                    window._deleteBankSession(sid, fname);
                }
            });
        });
    }

    function _gotoBankSession(_sessionId: unknown) {
        // v118.33.6 · redirect to reconcile center bank tab
        if (typeof window.routeTo === 'function') window.routeTo('reconcile');
        setTimeout(function () {
            const bankTab = document.querySelector('[data-recon-tab="bank"]') as HTMLElement | null;
            if (bankTab) bankTab.click();
        }, 150);
    }

    function _renderError() {
        _showError(true);
        _showEmpty(false);
    }

    function _gotoBankUpload() {
        // 导航到对账中心 → 银行对账 tab（不自动弹文件框，用户自己点区域）
        if (typeof window.routeTo === 'function') window.routeTo('reconcile');
        setTimeout(function () {
            const bankTab = document.querySelector('[data-recon-tab="bank"]') as HTMLElement | null;
            if (bankTab) bankTab.click();
        }, 150);
    }

    async function load() {
        // 进页面立即把数字重置成「-」(防止旧值闪现)
        _setNum('pending', 0, true);
        _setNum('matched', 0, true);
        _setNum('unmatched', 0, true);
        _setLastActivityText('', false);
        _showError(false);
        _showEmpty(false);
        // recent 列表先隐藏
        const recent = document.getElementById('reconcile-recent');
        if (recent) recent.style.display = 'none';

        const auth = { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
        // v118.26.1 · 并行拉 stats + sessions(单次往返成本最优)
        try {
            const [resStats, resSess] = await Promise.all([
                fetch('/api/bank-recon/stats', { headers: auth }),
                fetch('/api/bank-recon/sessions?limit=20', { headers: auth }),
            ]);
            if (!resStats.ok) throw new Error('http ' + resStats.status);
            const stats = await resStats.json();
            const sessions = resSess.ok ? await resSess.json() : [];
            _renderStats(stats || {});
            _renderRecent(sessions || []);
        } catch (e) {
            console.warn('[reconcile] load failed', e);
            _renderError();
        }
    }

    // 对账中心原地上传：选文件 → POST /api/bank-recon/upload → 刷新对账中心
    function _handleBankFileSelect(files: FileList | null | undefined) {
        if (!files || !files.length) return;
        const auth = 'Bearer ' + (localStorage.getItem('mrpilot_token') || '');
        let done = 0;
        const total = files.length;
        Array.from(files).forEach(function (file: File) {
            const fd = new FormData();
            fd.append('file', file, file.name);
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/bank-recon/upload');
            xhr.setRequestHeader('Authorization', auth);
            xhr.onload = function () {
                done++;
                try {
                    const body = JSON.parse(xhr.responseText);
                    if (xhr.status === 200 && body.tx_count !== undefined) {
                        showToast(
                            (t('bank-upload-ok') || '解析成功 · 共 {n} 条流水').replace(
                                '{n}',
                                body.tx_count
                            ),
                            'success'
                        );
                    } else {
                        showToast(file.name + ' ' + (t('upload-failed') || '上传失败'), 'error');
                    }
                } catch (e) {
                    showToast(file.name + ' ' + (t('upload-failed') || '上传失败'), 'error');
                }
                if (done === total) setTimeout(load, 600);
            };
            xhr.onerror = function () {
                done++;
                showToast(file.name + ' ' + (t('upload-failed') || '上传失败'), 'error');
                if (done === total) setTimeout(load, 600);
            };
            xhr.send(fd);
        });
        // toast 提示上传中
        showToast((t('bank-queue-status-uploading') || '上传中') + '…', 'info');
    }

    // 一次性绑定按钮(用事件委托 · 避免重复绑)
    function _bindOnce() {
        if (window.__reconcileBound) return;
        window.__reconcileBound = true;
        // 银行对账单文件选择器
        const bankFileInput = document.getElementById('reconcile-bank-file-input');
        if (bankFileInput) {
            bankFileInput.addEventListener('change', function (this: HTMLInputElement) {
                _handleBankFileSelect(this.files);
                this.value = ''; // 重置 · 允许重复选同一文件
            });
        }
        document.addEventListener('click', (e) => {
            if (
                (e.target as HTMLElement).closest('#btn-reconcile-upload-top') ||
                (e.target as HTMLElement).closest('#btn-reconcile-upload-empty')
            ) {
                _gotoBankUpload();
                return;
            }
            if ((e.target as HTMLElement).closest('#btn-reconcile-retry')) {
                load();
                return;
            }
            // v118.26.2 · 测试中心专用 · 插 mock 数据 · 仅 skin 白名单
            if ((e.target as HTMLElement).closest('#btn-reconcile-dev-seed')) {
                _devSeedMock();
                return;
            }
        });
    }

    // v118.26.2 · 检测 skin 测试账号 · 显示「插测试流水」按钮
    const _SKIN_USER_IDS = ['468b50c1-5593-4fd6-990d-515ce8085563'];
    function _maybeShowDevSeed() {
        const btn = document.getElementById('btn-reconcile-dev-seed');
        if (!btn) return;
        // v118.26.2.1 · _userInfo 在文件顶层 let · 不挂 window · 直接读
        const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
        const isSkin = u && u.id && _SKIN_USER_IDS.indexOf(String(u.id)) >= 0;
        btn.style.display = isSkin ? '' : 'none';
    }

    async function _devSeedMock() {
        try {
            const resp = await fetch('/api/bank-recon/_dev/seed', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) throw new Error('seed:' + resp.status);
            const data = await resp.json();
            const msg = (t('reconcile-dev-seed-ok') || '').replace('{n}', data.tx_count || 0);
            showToast(msg, 'success');
            // 跳到自动化模块的银行对账 tab + 直接打开新建的 session
            if (typeof window.navigateTo === 'function') {
                window.navigateTo('automation');
            } else {
                location.hash = '#/automation';
            }
            setTimeout(() => {
                const tab = document.querySelector('[data-auto-tab="bank"]') as HTMLElement | null;
                if (tab) tab.click();
                if (data.session_id && typeof window._openBankSession === 'function') {
                    window._openBankSession(data.session_id);
                }
            }, 300);
        } catch (e) {
            console.warn('[reconcile] dev seed failed', e);
            showToast(t('reconcile-dev-seed-fail') || 'Seed failed', 'error');
        }
    }

    window.loadReconcilePage = async function () {
        _bindOnce();
        _maybeShowDevSeed();
        // v118.33.6 · init bank recon v2 on reconcile page load
        if (typeof window._bankReconV2Init === 'function') {
            window._bankReconV2Init();
        }
        // Legacy stats load (harmless if DOM elements removed)
        try {
            await load();
        } catch (e) {}
    };

    // v118.26.1.2 · 对账中心首页注册 i18n 订阅总线
    //   切语言时刷新「最近对账时间」「最近对账列表」文案
    window._rerenderReconcile = function () {
        if (typeof currentRoute === 'string' && currentRoute === 'reconcile') {
            // 重新调 load · 简单稳定:数字 + 列表 + 文案一起刷
            load().catch(() => {});
        }
    };
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('reconcile', window._rerenderReconcile);
    }

    // 切账套重载已统一收口到 core-boot 全局 pearnly:workspace-changed → reloadCurrentRoute。
})();
