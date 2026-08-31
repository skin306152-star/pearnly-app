import { authHeaders } from './dms-intake-core.js';
import { initCoworkLineSummary } from './cowork-line/identity-panel.js';

type ErpTranslator = (th: string, en: string, zh: string, ja: string) => string;

function erpLineBindingMarkup(tr: ErpTranslator): string {
    return `
        <div class="page-head-clean"><div class="page-head-text">
            <div class="page-head-title">${tr('การเชื่อมต่อ LINE', 'LINE Integration', 'LINE 集成', 'LINE 連携')}</div>
            <div class="page-head-sub">${tr('ช่องทางเฉพาะสำหรับอัปโหลดเอกสารซื้อและขาย', 'Dedicated intake for purchase and sales documents', '采购与销售单据的专用上传入口', '仕入・売上書類専用のアップロード入口')}</div>
        </div></div>
        <div class="auto-panel-head">
            <div>
                <div class="auto-panel-title">Pearnly ERP LINE</div>
                <div class="auto-panel-desc">${tr('ส่งเอกสารซื้อหรือขายผ่าน LINE และตรวจสอบก่อนบันทึก', 'Send purchase or sales documents in LINE and review before saving', '在 LINE 上传采购或销售单据，确认后再入账', 'LINE で仕入・売上書類を送り、確認後に登録')}</div>
            </div>
            <span id="erp-linebot-status-summary" class="auto-status-pill">${tr('กำลังโหลด…', 'Loading…', '加载中…', '読み込み中…')}</span>
        </div>
        <div id="erp-linebot-unbound" style="display:none;">
            <div class="card linebot-card">
                <div class="linebot-bind-intro">${tr('เชื่อมต่อบัญชีนี้กับ Pearnly ERP LINE โดยทำตามขั้นตอนด้านล่าง', 'Connect this account to the dedicated Pearnly ERP LINE in the steps below.', '按下面步骤，把当前 ERP 账号绑定到专用 Pearnly ERP LINE。', '次の手順で、この ERP アカウントを専用 Pearnly ERP LINE に連携します。')}</div>
                <a id="erp-linebot-open-line" class="linebot-open-line" href="#" target="_blank" rel="noopener">${tr('เปิด Pearnly ERP ใน LINE', 'Open Pearnly ERP in LINE', '在 LINE 打开 Pearnly ERP', 'LINE で Pearnly ERP を開く')}</a>
                <div class="linebot-steps">
                    <div class="linebot-step">
                        <div class="linebot-step-no">1</div>
                        <div class="linebot-step-body">
                            <div class="linebot-step-title">${tr('เพิ่ม Pearnly ERP เป็นเพื่อน', 'Add Pearnly ERP as a friend', '添加 Pearnly ERP 为好友', 'Pearnly ERP を友だち追加')}</div>
                            <div class="linebot-step-desc">${tr('สแกน QR หรือค้นหาด้วย Bot ID', 'Scan the QR code or search by Bot ID.', '扫描二维码，或在 LINE 搜索下面的 Bot ID。', 'QR コードを読み取るか、Bot ID で検索します。')}</div>
                            <div class="linebot-qr-wrap">
                                <div id="erp-linebot-qr" class="linebot-qr-box empty"></div>
                                <div class="linebot-bot-id">Bot ID:
                                    <span id="erp-linebot-bot-id" class="linebot-bot-id-val">—</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="linebot-step">
                        <div class="linebot-step-no">2</div>
                        <div class="linebot-step-body">
                            <div class="linebot-step-title">${tr('ส่งรหัส 6 หลักนี้ให้ Bot', 'Send this 6-digit code to the Bot', '把这组 6 位数字发给 Bot', 'この6桁コードを Bot に送信')}</div>
                            <div class="linebot-step-desc">${tr('รหัสใช้ได้ 10 นาที', 'The code is valid for 10 minutes.', '绑定码 10 分钟内有效。', 'コードの有効期限は10分です。')}</div>
                            <div class="linebot-code-wrap">
                                <div id="erp-linebot-code" class="linebot-code">——————</div>
                                <button id="erp-linebot-code-refresh" class="btn btn-ghost btn-tiny" type="button" style="min-height:44px;">
                                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                                    <span>${tr('เปลี่ยนรหัส', 'New code', '换一个', '新しいコード')}</span>
                                </button>
                            </div>
                            <div id="erp-linebot-code-expires" class="linebot-code-expires"></div>
                        </div>
                    </div>
                    <div class="linebot-step">
                        <div class="linebot-step-no">3</div>
                        <div class="linebot-step-body">
                            <div class="linebot-step-title">${tr('รอให้การเชื่อมต่อเสร็จสิ้น', 'Wait for binding to finish', '等待绑定完成', '連携完了を待つ')}</div>
                            <div class="linebot-step-desc">${tr('หน้านี้จะอัปเดตอัตโนมัติ', 'This page updates automatically.', '发送成功后，本页会自动显示“已绑定”。', '送信後、この画面は自動的に更新されます。')}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div id="erp-linebot-bound" style="display:none;">
            <div class="card linebot-bound-card">
                <div class="linebot-bound-head">
                    <div class="linebot-bound-info">
                        <div class="linebot-bound-name" id="erp-linebot-bound-name">—</div>
                        <div class="linebot-bound-sub">
                            <span>${tr('เชื่อมต่อแล้ว', 'Bound', '已绑定', '連携済み')}</span>
                            <span id="erp-linebot-bound-since">—</span>
                        </div>
                    </div>
                    <div class="linebot-bound-badge">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8l4 4 8-8"/></svg>
                        <span>${tr('เชื่อมต่อแล้ว', 'Bound', '已绑定', '連携済み')}</span>
                    </div>
                </div>
                <div class="linebot-bound-tips">
                    <div class="linebot-tip-title">${tr('ใช้งานได้ทันที', 'Ready to use', '现在可以这样使用', '利用を開始できます')}</div>
                    <ul class="linebot-tip-list">
                        <li>${tr('เลือก ซื้อ หรือ ขาย ใน LINE ก่อนส่งเอกสาร', 'Choose purchase or sales in LINE before sending a document.', '先在 LINE 选择采购或销售，再上传单据。', 'LINE で仕入または売上を選んでから書類を送信します。')}</li>
                        <li>${tr('ตรวจสอบและแก้ไขข้อมูลก่อนยืนยัน', 'Review and edit the recognized fields before confirming.', '识别后先预览和编辑，确认后才会入账。', '認識結果を確認・編集し、確定後に登録します。')}</li>
                    </ul>
                </div>
                <div class="linebot-bound-actions">
                    <button id="erp-linebot-unbind" class="btn btn-ghost" type="button">${tr('ยกเลิกการเชื่อมต่อ LINE', 'Unbind LINE', '解绑 LINE', 'LINE 連携を解除')}</button>
                </div>
            </div>
        </div>
        <div id="erp-linebot-error" class="linebot-error" style="display:none;"></div>`;
}

function initErpLineBinding(sec: HTMLElement, tr: ErpTranslator): void {
    let codeTimer: ReturnType<typeof setInterval> | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let codeRequest: Promise<void> | null = null;
    let expiresAt = 0;
    const el = <T extends HTMLElement>(id: string) => sec.querySelector<T>(`#${id}`);
    const headers = (json = false) => authHeaders(json) as HeadersInit;
    const status = el('erp-linebot-status-summary');
    const error = el('erp-linebot-error');

    const label = (bound: boolean) =>
        bound
            ? tr('เชื่อมต่อแล้ว', 'Bound', '已绑定', '連携済み')
            : tr('ยังไม่เชื่อมต่อ', 'Not bound', '未绑定', '未連携');

    function stopTimers(): void {
        if (codeTimer) clearInterval(codeTimer);
        if (pollTimer) clearInterval(pollTimer);
        codeTimer = null;
        pollTimer = null;
    }

    function showError(message: string): void {
        if (error) {
            error.textContent = message;
            error.style.display = 'block';
        }
        if (status)
            status.textContent = tr(
                'เชื่อมต่อไม่สำเร็จ',
                'Connection failed',
                '连接失败',
                '接続に失敗'
            );
    }

    function hideError(): void {
        if (error) error.style.display = 'none';
    }

    function startCountdown(): void {
        if (codeTimer) clearInterval(codeTimer);
        const target = el('erp-linebot-code-expires');
        const tick = () => {
            const remaining = expiresAt - Date.now();
            if (remaining <= 0) {
                if (target)
                    target.textContent = tr(
                        'รหัสหมดอายุแล้ว',
                        'Code expired',
                        '绑定码已过期',
                        'コードの有効期限が切れました'
                    );
                if (codeTimer) clearInterval(codeTimer);
                codeTimer = null;
                return;
            }
            const total = Math.floor(remaining / 1000);
            const minutes = Math.floor(total / 60);
            const seconds = String(total % 60).padStart(2, '0');
            if (target) target.textContent = `${minutes}:${seconds}`;
        };
        tick();
        codeTimer = setInterval(tick, 1000);
    }

    async function fetchNewCode(): Promise<void> {
        if (codeRequest) return codeRequest;
        hideError();
        const request = (async () => {
            try {
                const response = await fetch('/api/line/erp/binding-code', {
                    method: 'POST',
                    headers: {
                        ...headers(true),
                        'X-Workspace-Client-Id': String(
                            window.getActiveWorkspaceClientId?.() || ''
                        ),
                    },
                    body: '{}',
                });
                if (!response.ok) throw new Error('binding-code');
                const payload = await response.json();
                const data = payload.data || payload;
                const code = el('erp-linebot-code');
                const botId = el('erp-linebot-bot-id');
                const openLine = el<HTMLAnchorElement>('erp-linebot-open-line');
                const qr = el('erp-linebot-qr');
                if (code) code.textContent = data.code || '——————';
                if (botId) botId.textContent = data.bot_basic_id || '—';
                if (openLine && data.bot_friend_url) openLine.href = data.bot_friend_url;
                if (qr && data.bot_friend_url) {
                    const qrUrl =
                        'https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data=' +
                        encodeURIComponent(data.bot_friend_url);
                    qr.classList.remove('empty');
                    qr.innerHTML = `<img src="${qrUrl}" alt="Pearnly ERP LINE QR">`;
                }
                expiresAt = new Date(data.expires_at).getTime();
                startCountdown();
            } catch {
                showError(
                    tr(
                        'สร้างรหัสเชื่อมต่อไม่สำเร็จ',
                        'Could not generate a binding code.',
                        '无法生成绑定码，请稍后重试。',
                        '連携コードを生成できませんでした。'
                    )
                );
            }
        })();
        codeRequest = request;
        try {
            await request;
        } finally {
            if (codeRequest === request) codeRequest = null;
        }
    }

    function renderBound(data: Record<string, unknown>): void {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = null;
        const unbound = el('erp-linebot-unbound');
        const bound = el('erp-linebot-bound');
        if (unbound) unbound.style.display = 'none';
        if (bound) bound.style.display = 'block';
        if (status) status.textContent = label(true);
        const name = el('erp-linebot-bound-name');
        const since = el('erp-linebot-bound-since');
        if (name) name.textContent = String(data.display_name || 'LINE User');
        if (since) {
            const value = data.bound_at ? new Date(String(data.bound_at)).toLocaleString() : '—';
            since.textContent = value;
        }
    }

    async function refreshStatus(): Promise<void> {
        try {
            const response = await fetch('/api/line/erp/binding', { headers: headers() });
            if (!response.ok) throw new Error('binding-status');
            const payload = await response.json();
            const data = payload.data || payload;
            if (data.bound) {
                renderBound(data);
                return;
            }
            const unbound = el('erp-linebot-unbound');
            const bound = el('erp-linebot-bound');
            if (unbound) unbound.style.display = 'block';
            if (bound) bound.style.display = 'none';
            if (status) status.textContent = label(false);
            if (!expiresAt || expiresAt <= Date.now()) await fetchNewCode();
            if (!pollTimer) pollTimer = setInterval(() => void refreshStatus(), 4000);
        } catch {
            showError(
                tr(
                    'โหลดสถานะ LINE ไม่สำเร็จ',
                    'Could not load LINE status.',
                    '无法读取 LINE 绑定状态。',
                    'LINE 連携状態を読み込めませんでした。'
                )
            );
        }
    }

    el('erp-linebot-code-refresh')?.addEventListener('click', () => void fetchNewCode());
    el('erp-linebot-unbind')?.addEventListener('click', async () => {
        const confirmed = await window.showConfirm?.(
            tr(
                'ยืนยันการยกเลิกการเชื่อมต่อ?',
                'Unbind Pearnly ERP LINE?',
                '确认解绑 Pearnly ERP LINE？',
                'Pearnly ERP LINE の連携を解除しますか？'
            ),
            { danger: true }
        );
        if (!confirmed) return;
        const response = await fetch('/api/line/erp/binding', {
            method: 'DELETE',
            headers: headers(),
        });
        if (!response.ok) {
            showError(
                tr(
                    'ยกเลิกการเชื่อมต่อไม่สำเร็จ',
                    'Could not unbind LINE.',
                    '解绑失败，请稍后重试。',
                    'LINE 連携を解除できませんでした。'
                )
            );
            return;
        }
        expiresAt = 0;
        await refreshStatus();
        window.showToast?.(
            tr('ยกเลิกการเชื่อมต่อแล้ว', 'LINE unbound', 'LINE 已解绑', 'LINE 連携を解除しました'),
            'success'
        );
    });
    window.addEventListener('hashchange', () => {
        if (location.hash.includes('integrations')) {
            void refreshStatus();
            return;
        }
        stopTimers();
    });
    void refreshStatus();
}

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
        sec.innerHTML = erpLineBindingMarkup(tr);
        sec.dataset.wbInjected = '1';
        initErpLineBinding(sec, tr);
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
            <!-- 第 1 组 · 采集渠道 -->
            <div class="integrations-section-title" data-i18n="integrations-section-channels">采集渠道</div>

            <div id="cowork-line-integration-row" class="integration-row" data-int-target="drawer" data-int-anchor="line">
                <div class="int-icon ic-line">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 5.96 2 10.84c0 4.37 3.55 8.04 8.36 8.74.32.07.77.21.88.49.1.25.07.65.03.91l-.14.86c-.04.25-.2.99.87.54 1.07-.46 5.77-3.4 7.87-5.82C21.32 15.04 22 13.05 22 10.84 22 5.96 17.52 2 12 2z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name">
                        <span data-cowork-line-copy="productName">Pearnly Cowork LINE</span>
                        <span id="cowork-line-status-summary" class="auto-status-pill cowork-line-status is-loading">加载中…</span>
                    </div>
                    <div class="int-desc" data-cowork-line-copy="productDescription">在 LINE 上传、识别、编辑，再选择推送目标</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" type="button" data-cowork-line-copy="manage">管理</button>
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
                 连接就在用到它的地方 · 避免 per-套账 连接态在两处不一致。集成页只留采集入口。
                 第 3 组「ERP 系统」亦已移除(2026-07-01)· ERP 连接/推送由「录入工作台」上下文卡承接。 -->
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
    initCoworkLineSummary(sec);
})();
