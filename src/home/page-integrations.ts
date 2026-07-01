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

            <div class="sec-divider" data-firm-only="1"></div>

            <!-- 第 2 组 · 归档交付(Google · 事务所把结果交付客户/会计) -->
            <div class="integrations-info-bar" data-firm-only="1">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="8"/>
                    <line x1="10" y1="6" x2="10" y2="10"/>
                    <circle cx="10" cy="14" r="0.6" fill="currentColor"/>
                </svg>
                <span data-i18n="integrations-google-info">授权一次 Google 账号 · Drive 和 Sheets 均可使用 · 无需重复授权</span>
            </div>

            <div class="integrations-section-title" data-firm-only="1" data-i18n="integrations-section-archive">归档交付</div>

            <!-- Google 授权连接卡(外流归档 OAuth · purchase-google.ts 填状态/连接/断开)·
                 一次授权覆盖 Drive + Sheets · 凭据按套账隔离 · 未连点「连接 Google」走整页导航。 -->
            <div class="integration-row" id="int-google-card" data-firm-only="1">
                <div class="int-icon ic-g">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M7 18a4 4 0 01-.5-7.97 5 5 0 019.6-1.5A4 4 0 0117 18z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-google-name">Google Drive / Sheets</span><span class="int-gst off" id="int-google-st" data-i18n="int-google-st-off">未连接</span></div>
                    <div class="int-desc" id="int-google-desc" data-i18n="int-google-desc">把进项原图归档进 Drive(证据 + 交会计 PDF)· 并同步成可追溯的 Sheet 报表</div>
                </div>
                <div class="int-actions" id="int-google-act"></div>
            </div>

            <!-- 旧的 Google Drive / Google Sheets 两条描述行已删:被上方 OAuth 连接卡取代
                 (一次授权覆盖 Drive + Sheets)· 对齐原型⑥单卡 · 去 3 条 Google 冗余。 -->

            <!-- 第 3 组「ERP 系统」已移除(2026-07-01)· ERP 连接/推送改由「录入工作台」上下文卡承接:
                 发票任务→MR.ERP+Express·身份证任务→MR.ERP DMS(见 dms-intake-erp-cards)· 集成页只留采集/归档/通知。 -->

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
