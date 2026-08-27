import { authHeaders } from './dms-intake-core.js';

// ============================================================
// REFACTOR-WB-C3 (2026-05-29) · page-integrations 静态骨架从 home.html 抽出 · 运行期模板注入(R6 机制)
//
// home.html <section id="page-integrations"> 现为空壳 · 本模块注入骨架 innerHTML(含内嵌 erp-logs-section)。
// 集成页被 erp-integration / integration-config 等模块 + home.js int-top-tab
// IIFE(事件委托)渲染/绑定 → 本 import 置于 main.js 较前(随 page-reconcile)· eval 即注入 · 早于这些模块
// eval/DOMContentLoaded · 元素恒在场。int-drawer 抽屉(home.js _initDrawerEvents 绑定)是 section 外兄弟 · 留 home.html。
// home.js parse 期 0 处绑定 erp-logs-* 等 section 内元素(已核)。i18n 注入后子树补译(镜像 applyLang)· verbatim 0 改结构。
// ============================================================
(function () {
    'use strict';
    const sec = document.getElementById('page-integrations');
    if (!sec || sec.dataset.wbInjected === '1') return;
    if (window._entry === 'erp' || localStorage.getItem('pearnly_entry') === 'erp') {
        const lang = (localStorage.getItem('mrpilot_lang') || 'th').slice(0, 2);
        const tr = (th: string, en: string, zh: string, ja: string) =>
            ({ th, en, zh, ja })[lang] || th;
        sec.innerHTML = `
            <div class="page-head-clean"><div class="page-head-text">
                <div class="page-head-title">ERP</div><div class="page-head-sub">LINE ERP · ${window.t?.('nav-push-logs') || 'Push logs'}</div>
            </div></div>
            <div class="card"><div class="integrations-section-title">LINE ERP</div>
                <div id="erp-line-status" class="integration-row"><div class="int-info">
                    <div class="int-name">LINE ERP</div><div class="int-desc">${tr('สถานะการเชื่อมต่อ / สาขาปัจจุบัน', 'Connection status / current branch', '连接状态 / 当前分店', '接続状態 / 現在の支店')}</div>
                </div><div class="int-actions"><button class="int-btn-configure" id="erp-line-code">${tr('สร้างรหัสผูกบัญชี', 'Generate binding code', '生成绑定码', '連携コードを生成')}</button><button class="int-btn-configure" id="erp-line-unbind">${tr('ยกเลิกการผูก', 'Unbind', '解绑', '連携解除')}</button></div></div>
                <div id="erp-line-code-output" class="hint"></div>
            </div>
            <div class="card"><div class="integrations-section-title">${tr('ERP อื่น', 'Third-party ERP', '第三方 ERP', '外部 ERP')}</div>
                <div class="integration-row"><div class="int-info"><div class="int-name">MR.ERP / Express</div><div class="int-desc">${tr('การเชื่อมต่อและประวัติการส่ง', 'Connection and push history', '连接与推送记录', '接続と送信履歴')}</div></div>
                <div class="int-actions"><button class="int-btn-configure" id="erp-express-connect">${tr('เชื่อมต่อ', 'Configure connection', '配置连接', '接続を設定')}</button><button class="int-btn-configure" data-route="push-logs">${window.t?.('nav-push-logs') || 'Push logs'}</button></div></div>
            </div>`;
        sec.dataset.wbInjected = '1';
        const status = sec.querySelector('#erp-line-status .int-desc');
        const output = sec.querySelector('#erp-line-code-output');
        const statusText = (key: string) =>
            tr(
                key === 'bound' ? 'เชื่อมต่อแล้ว' : 'ยังไม่เชื่อมต่อ',
                key === 'bound' ? 'Bound' : 'Not bound',
                key === 'bound' ? '已绑定' : '未绑定',
                key === 'bound' ? '連携済み' : '未連携'
            );
        const headers = (json = false) => authHeaders(json) as HeadersInit;
        const refresh = () =>
            fetch('/api/line/erp/binding', { headers: headers() })
                .then((r) => r.json())
                .then((x) => {
                    const d = x.data || x;
                    if (status)
                        status.textContent = `${d.bound ? statusText('bound') : statusText('unbound')} · ${d.display_name || '-'} · ${d.workspace_client_id || '-'} · ${d.bound_at || '-'}`;
                    const unbind = sec.querySelector(
                        '#erp-line-unbind'
                    ) as HTMLButtonElement | null;
                    if (unbind) unbind.disabled = !d.bound;
                })
                .catch(() => {
                    if (status) status.textContent = statusText('failed');
                });
        sec.querySelector('#erp-line-code')?.addEventListener('click', () =>
            fetch('/api/line/erp/binding-code', {
                method: 'POST',
                headers: {
                    ...headers(true),
                    'X-Workspace-Client-Id': String(window.getActiveWorkspaceClientId?.() || ''),
                },
                body: '{}',
            })
                .then((r) => r.json())
                .then((x) => {
                    const d = x.data || x;
                    if (output)
                        output.textContent = `${d.code || statusText('failed')} · ${d.expires_at || ''}`;
                })
                .catch(() => {
                    if (output) output.textContent = statusText('failed');
                })
        );
        sec.querySelector('#erp-line-unbind')?.addEventListener('click', () => {
            if (
                !window.confirm(
                    tr(
                        'ยืนยันการยกเลิกการผูก?',
                        'Unbind LINE ERP?',
                        '确认解绑 LINE ERP？',
                        'LINE ERP の連携を解除しますか？'
                    )
                )
            )
                return;
            void fetch('/api/line/erp/binding', { method: 'DELETE', headers: headers() }).then(
                refresh
            );
        });
        sec.querySelector('#erp-express-connect')?.addEventListener('click', () => {
            const express = (window as Window & { ExpressWizard?: { open?: () => void } })
                .ExpressWizard;
            express?.open?.();
        });
        sec.querySelector('[data-route="push-logs"]')?.addEventListener('click', () =>
            window.routeTo?.('push-logs')
        );
        void refresh();
        return;
    }
    sec.innerHTML = `
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 16L4 21M15 8l5-5"/>
                    <path d="M11 5L6 10a3 3 0 000 4l4 4a3 3 0 004 0l5-5a3 3 0 000-4l-4-4a3 3 0 00-4 0z"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="integrations-title">集成</div>
                <div class="page-head-sub" data-i18n="integrations-sub">Google · LINE · 邮箱 · ERP · 文件夹 · 云盘 等第三方授权 · 让 Pearnly 自动同步数据</div>
            </div>
        </div>

        <!-- 推送日志已抽为左侧栏独立页(page-push-logs · 2026-07-01)· 集成页只留集成卡片 -->
        <div class="card">
            <!-- 2026-06-10 五-bis · 卡片按归属重排 + 业态显隐:
                 firm 全显;商户业态(retail/restaurant/…)只显 LINE Bot + 智能提醒(data-firm-only 由 module-nav 控)。
                 采集渠道(LINE 全业态 · Gmail/文件夹=事务所代收) / 归档交付(Drive/Sheets) / ERP / 通知。
                 隐藏≠删除:后端配置不动,切回 firm 即复现。 -->

            <!-- 第 1 组 · 采集渠道 -->
            <div class="integrations-section-title" data-i18n="integrations-section-channels">采集渠道</div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="line">
                <div class="int-icon ic-line">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 5.96 2 10.84c0 4.37 3.55 8.04 8.36 8.74.32.07.77.21.88.49.1.25.07.65.03.91l-.14.86c-.04.25-.2.99.87.54 1.07-.46 5.77-3.4 7.87-5.82C21.32 15.04 22 13.05 22 10.84 22 5.96 17.52 2 12 2z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-line">LINE Bot</span></div>
                    <div class="int-desc" data-i18n="int-desc-line">外勤拍照发 LINE · 自动入账 · 单聊群聊都支持</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="integration-row" data-firm-only="1" data-int-target="automation" data-int-anchor="gmail">
                <div class="int-icon ic-gm">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="5" width="18" height="14" rx="2"/>
                        <path d="M3 7l9 6 9-6"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-gmail">Gmail 抓取</span></div>
                    <div class="int-desc" data-i18n="int-desc-gmail">客户发来邮件附件自动抓 · 不用手动转发</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="integration-row" data-firm-only="1" data-int-target="automation" data-int-anchor="folder">
                <div class="int-icon ic-folder">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 7a2 2 0 012-2h4l2 3h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-folder">文件夹监听</span></div>
                    <div class="int-desc" data-i18n="int-desc-folder">指定本地/共享文件夹 · 扔进去就自动识别</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <!-- 归档交付(Google Drive/Sheets)连接卡已迁至采购导出页(purchase-export · purchase-export-google.ts):
                 连接就在用到它的地方 · 避免 per-套账 连接态在两处不一致。集成页只留采集/通知。
                 第 3 组「ERP 系统」亦已移除(2026-07-01)· ERP 连接/推送由「录入工作台」上下文卡承接。 -->

            <div class="sec-divider"></div>

            <!-- 第 4 组 · 通知提醒(全业态) -->
            <div class="integrations-section-title" data-i18n="int-section-automation">通知提醒</div>

            <div class="integration-row" data-int-target="drawer" data-int-anchor="alert">
                <div class="int-icon ic-alert">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                        <path d="M10 21a2 2 0 0 0 4 0"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="auto-alert-title">智能提醒</span></div>
                    <div class="int-desc" data-i18n="auto-alert-desc">异常 high 或大额发票发生时 · 自动推送到老板/会计的 LINE</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-i18n="btn-configure">配置</button>
                </div>
            </div>
        </div>
`;
    sec.dataset.wbInjected = '1';
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            sec.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n') as string;
                if (I[lang][k]) el.textContent = I[lang][k];
            });
            sec.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                const k = el.getAttribute('data-i18n-placeholder') as string;
                if (I[lang][k]) (el as HTMLInputElement).placeholder = I[lang][k];
            });
        }
    } catch (e) {
        /* silent · 初译失败不致命 · 切语言会补 */
    }
})();
