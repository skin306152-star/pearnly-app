import { authHeaders } from '../dms-intake-core.js';

type Language = 'th' | 'en' | 'zh' | 'ja';
type Phase = 'loading' | 'ready' | 'pendingFriend' | 'disconnected' | 'error';

type Copy = {
    productName: string;
    productDescription: string;
    manage: string;
    loading: string;
    ready: string;
    pendingFriend: string;
    disconnected: string;
    loadError: string;
    retry: string;
    intro: string;
    setupDescription: string;
    stepAdd: string;
    stepAddDescription: string;
    stepCode: string;
    stepCodeDescription: string;
    stepWait: string;
    stepWaitDescription: string;
    scanQr: string;
    openLine: string;
    botId: string;
    codeLoading: string;
    codeExpires: string;
    codeExpired: string;
    refreshCode: string;
    codeError: string;
    connectedAs: string;
    connectedAt: string;
    readyTitle: string;
    readyDescription: string;
    disconnect: string;
    disconnecting: string;
    disconnectConfirm: string;
    disconnectedToast: string;
    actionError: string;
};

const COPY: Record<Language, Copy> = {
    th: {
        productName: 'Pearnly Cowork LINE',
        productDescription: 'อัปโหลด ตรวจเอกสาร แก้ไข และเลือกปลายทางส่งต่อใน LINE',
        manage: 'จัดการ',
        loading: 'กำลังโหลด…',
        ready: 'พร้อมใช้งาน',
        pendingFriend: 'รอส่งรหัส',
        disconnected: 'ยังไม่เชื่อมต่อ',
        loadError: 'โหลดสถานะ LINE ไม่สำเร็จ',
        retry: 'ลองอีกครั้ง',
        intro: 'สมาชิกแต่ละคนเชื่อมต่อ LINE ของตนเองกับบัญชี Pearnly Cowork',
        setupDescription: 'เชื่อมต่อบัญชีนี้กับ Pearnly Cowork LINE โดยทำตามขั้นตอนด้านล่าง',
        stepAdd: 'เพิ่ม Pearnly Cowork เป็นเพื่อน',
        stepAddDescription: 'สแกน QR หรือค้นหาด้วย Bot ID',
        stepCode: 'ส่งรหัส 6 หลักนี้ให้ Bot',
        stepCodeDescription: 'รหัสใช้ได้ 10 นาที',
        stepWait: 'รอให้การเชื่อมต่อเสร็จสิ้น',
        stepWaitDescription: 'หน้านี้จะอัปเดตอัตโนมัติ',
        scanQr: 'สแกนด้วย LINE',
        openLine: 'เปิดใน LINE',
        botId: 'LINE ID',
        codeLoading: 'กำลังสร้างรหัส…',
        codeExpires: 'หมดอายุใน {time}',
        codeExpired: 'รหัสหมดอายุแล้ว',
        refreshCode: 'เปลี่ยนรหัส',
        codeError: 'สร้างรหัสไม่สำเร็จ',
        connectedAs: 'เชื่อมต่อในชื่อ',
        connectedAt: 'เชื่อมต่อเมื่อ',
        readyTitle: 'LINE พร้อมใช้งาน',
        readyDescription: 'เปิดห้องแชต Pearnly Cowork LINE ได้ทันที',
        disconnect: 'ยกเลิกการเชื่อมต่อ',
        disconnecting: 'กำลังยกเลิก…',
        disconnectConfirm: 'ยกเลิกการเชื่อมต่อ Pearnly Cowork LINE ของคุณ?',
        disconnectedToast: 'ยกเลิกการเชื่อมต่อ LINE แล้ว',
        actionError: 'ดำเนินการไม่สำเร็จ กรุณาลองอีกครั้ง',
    },
    en: {
        productName: 'Pearnly Cowork LINE',
        productDescription: 'Upload, review, edit, and choose a push target in LINE',
        manage: 'Manage',
        loading: 'Loading…',
        ready: 'Ready',
        pendingFriend: 'Send code',
        disconnected: 'Not connected',
        loadError: 'Could not load your LINE status',
        retry: 'Try again',
        intro: 'Each employee connects their own LINE to their Pearnly Cowork account.',
        setupDescription: 'Connect this account to Pearnly Cowork LINE in the steps below.',
        stepAdd: 'Add Pearnly Cowork as a friend',
        stepAddDescription: 'Scan the QR code or search by Bot ID.',
        stepCode: 'Send this 6-digit code to the Bot',
        stepCodeDescription: 'The code is valid for 10 minutes.',
        stepWait: 'Wait for binding to finish',
        stepWaitDescription: 'This page updates automatically.',
        scanQr: 'Scan with LINE',
        openLine: 'Open in LINE',
        botId: 'LINE ID',
        codeLoading: 'Generating code…',
        codeExpires: 'Expires in {time}',
        codeExpired: 'Code expired',
        refreshCode: 'New code',
        codeError: 'Could not generate a code',
        connectedAs: 'Connected as',
        connectedAt: 'Connected on',
        readyTitle: 'LINE is ready',
        readyDescription: 'You can open the Pearnly Cowork LINE chat now.',
        disconnect: 'Disconnect',
        disconnecting: 'Disconnecting…',
        disconnectConfirm: 'Disconnect your Pearnly Cowork LINE?',
        disconnectedToast: 'LINE disconnected',
        actionError: 'The action failed. Please try again.',
    },
    zh: {
        productName: 'Pearnly Cowork LINE',
        productDescription: '在 LINE 上传、识别、编辑，再选择推送目标',
        manage: '管理',
        loading: '加载中…',
        ready: '可以使用',
        pendingFriend: '待发送绑定码',
        disconnected: '未连接',
        loadError: '无法读取你的 LINE 连接状态',
        retry: '重试',
        intro: '每位员工分别把自己的 LINE 绑定到本人的 Pearnly Cowork 账号。',
        setupDescription: '按下面步骤，把当前账号绑定到 Pearnly Cowork LINE。',
        stepAdd: '添加 Pearnly Cowork 为好友',
        stepAddDescription: '扫描二维码，或在 LINE 搜索下面的 Bot ID。',
        stepCode: '把这组 6 位数字发给 Bot',
        stepCodeDescription: '绑定码 10 分钟内有效。',
        stepWait: '等待绑定完成',
        stepWaitDescription: '发送成功后，本页会自动显示“已绑定”。',
        scanQr: '使用 LINE 扫码',
        openLine: '在 LINE 打开',
        botId: 'LINE ID',
        codeLoading: '正在生成绑定码…',
        codeExpires: '{time} 后过期',
        codeExpired: '绑定码已过期',
        refreshCode: '换一个',
        codeError: '无法生成绑定码',
        connectedAs: '连接账号',
        connectedAt: '连接时间',
        readyTitle: 'LINE 已可使用',
        readyDescription: '现在可以直接打开 Pearnly Cowork LINE 对话。',
        disconnect: '解除连接',
        disconnecting: '正在解除…',
        disconnectConfirm: '确认解除你本人的 Pearnly Cowork LINE？',
        disconnectedToast: 'LINE 已解除连接',
        actionError: '操作失败，请重试。',
    },
    ja: {
        productName: 'Pearnly Cowork LINE',
        productDescription: 'LINE でアップロード、認識、編集、送信先の選択まで完了',
        manage: '管理',
        loading: '読み込み中…',
        ready: '利用可能',
        pendingFriend: 'コード送信待ち',
        disconnected: '未連携',
        loadError: 'LINE の連携状態を読み込めませんでした',
        retry: '再試行',
        intro: '従業員ごとに自分の LINE を Pearnly Cowork アカウントへ連携します。',
        setupDescription: '次の手順で、このアカウントを Pearnly Cowork LINE に連携します。',
        stepAdd: 'Pearnly Cowork を友だち追加',
        stepAddDescription: 'QR コードを読み取るか、Bot ID で検索します。',
        stepCode: 'この6桁コードを Bot に送信',
        stepCodeDescription: 'コードの有効期限は10分です。',
        stepWait: '連携完了を待つ',
        stepWaitDescription: '送信後、この画面は自動的に更新されます。',
        scanQr: 'LINEで読み取る',
        openLine: 'LINEで開く',
        botId: 'LINE ID',
        codeLoading: 'コードを発行中…',
        codeExpires: '有効期限 {time}',
        codeExpired: 'コードの有効期限が切れました',
        refreshCode: '新しいコード',
        codeError: 'コードを発行できませんでした',
        connectedAs: '連携アカウント',
        connectedAt: '連携日時',
        readyTitle: 'LINE を利用できます',
        readyDescription: 'Pearnly Cowork LINE のトークを開けます。',
        disconnect: '連携を解除',
        disconnecting: '解除中…',
        disconnectConfirm: '自分の Pearnly Cowork LINE 連携を解除しますか？',
        disconnectedToast: 'LINE 連携を解除しました',
        actionError: '操作に失敗しました。もう一度お試しください。',
    },
};

type Identity = {
    connected: boolean;
    friendshipReady: boolean;
    displayName: string;
    connectedAt: string;
};

type BindingCode = {
    code: string;
    expiresAt: number;
    botFriendUrl: string;
    botBasicId: string;
};

const DEFAULT_LINE_URL = 'https://line.me/R/ti/p/@pearnly';
let phase: Phase = 'loading';
let identity: Identity | null = null;
let bindingCode: BindingCode | null = null;
let summaryRoot: HTMLElement | null = null;
let drawerRoot: HTMLElement | null = null;
let loadRequest: Promise<void> | null = null;
let codeRequest: Promise<void> | null = null;
let codeError = false;
let actionPending = false;
let countdownTimer: ReturnType<typeof setInterval> | null = null;
let pollTimer: ReturnType<typeof setInterval> | null = null;

function language(): Language {
    const value = (window._currentLang || localStorage.getItem('mrpilot_lang') || 'th').slice(0, 2);
    return value === 'en' || value === 'zh' || value === 'ja' ? value : 'th';
}

function copy(): Copy {
    return COPY[language()];
}

function normalizeIdentity(payload: Record<string, unknown>): Identity {
    const source = (payload.data || payload) as Record<string, unknown>;
    return {
        connected: Boolean(source.connected ?? source.bound),
        friendshipReady: Boolean(source.friendship_ready),
        displayName: String(source.display_name || source.line_display_name || ''),
        connectedAt: String(source.connected_at || source.bound_at || ''),
    };
}

function formatConnectedAt(value: string): string {
    if (!value) return '—';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString(language());
}

function lineIcon(): string {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11.5a7.5 7.5 0 01-8 7.46L7 22l1.2-4.1A7.5 7.5 0 1120 11.5z"/><path d="M8 11h.01M12 11h.01M16 11h.01"/></svg>';
}

function renderSummary(): void {
    if (!summaryRoot) return;
    const text = copy();
    summaryRoot.querySelectorAll<HTMLElement>('[data-cowork-line-copy]').forEach((node) => {
        const key = node.dataset.coworkLineCopy as keyof Copy;
        if (text[key]) node.textContent = text[key];
    });
    const status = summaryRoot.querySelector<HTMLElement>('#cowork-line-status-summary');
    const row = summaryRoot.querySelector<HTMLElement>('#cowork-line-integration-row');
    if (!status) return;
    status.className = `auto-status-pill cowork-line-status is-${phase}`;
    status.textContent =
        phase === 'ready'
            ? text.ready
            : phase === 'pendingFriend'
              ? text.pendingFriend
              : phase === 'disconnected'
                ? text.disconnected
                : phase === 'error'
                  ? text.loadError
                  : text.loading;
    row?.classList.toggle('connected', phase === 'ready');
    row?.classList.toggle('pending', phase === 'pendingFriend');
}

function renderBindingSetup(): string {
    const text = copy();
    const codeContent = codeError
        ? `<div class="linebot-error">${text.codeError}</div>`
        : `<div class="linebot-code" data-cowork-line-code>${bindingCode?.code || '——————'}</div>`;
    const friendUrl = bindingCode?.botFriendUrl || DEFAULT_LINE_URL;
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data=${encodeURIComponent(friendUrl)}`;
    return `<div class="card linebot-card"><div class="linebot-bind-intro">${text.setupDescription}</div><a class="linebot-open-line" href="${friendUrl}" target="_blank" rel="noopener">${text.openLine}</a><div class="linebot-steps"><div class="linebot-step"><div class="linebot-step-no">1</div><div class="linebot-step-body"><div class="linebot-step-title">${text.stepAdd}</div><div class="linebot-step-desc">${text.stepAddDescription}</div><div class="linebot-qr-wrap"><div class="linebot-qr-box"><img src="${qrUrl}" alt="${text.scanQr}"></div><div class="linebot-bot-id">${text.botId}: <span class="linebot-bot-id-val" data-cowork-line-bot-id></span></div></div></div></div><div class="linebot-step"><div class="linebot-step-no">2</div><div class="linebot-step-body"><div class="linebot-step-title">${text.stepCode}</div><div class="linebot-step-desc">${text.stepCodeDescription}</div><div class="linebot-code-wrap">${codeContent}<button class="btn btn-ghost btn-tiny" type="button" data-cowork-line-action="refresh-code" style="min-height:44px;"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg><span>${codeError ? text.retry : text.refreshCode}</span></button></div><div class="linebot-code-expires" data-cowork-line-expires>${text.codeLoading}</div></div></div><div class="linebot-step"><div class="linebot-step-no">3</div><div class="linebot-step-body"><div class="linebot-step-title">${text.stepWait}</div><div class="linebot-step-desc">${text.stepWaitDescription}</div></div></div></div></div>`;
}

function renderDrawer(): void {
    if (!drawerRoot) return;
    const text = copy();
    if (phase === 'loading') {
        drawerRoot.innerHTML = `<div class="cowork-line-panel"><p class="cowork-line-panel__intro">${text.intro}</p><div class="cowork-line-panel__skeleton" aria-label="${text.loading}"><span class="pu-skeleton"></span><span class="pu-skeleton"></span></div></div>`;
        return;
    }
    if (phase === 'error') {
        drawerRoot.innerHTML = `<div class="cowork-line-panel"><p class="cowork-line-panel__intro">${text.intro}</p><div class="pu-error"><span class="pu-error__icon">${lineIcon()}</span><h3 class="pu-error__title">${text.loadError}</h3><button class="pu-btn pu-btn--outline" type="button" data-cowork-line-action="retry">${text.retry}</button></div></div>`;
        wireDrawerActions();
        return;
    }
    if (phase !== 'ready') {
        drawerRoot.innerHTML = `<div class="cowork-line-panel">${renderBindingSetup()}</div>`;
        const codeNode = drawerRoot.querySelector<HTMLElement>('[data-cowork-line-code]');
        const botId = drawerRoot.querySelector<HTMLElement>('[data-cowork-line-bot-id]');
        if (codeNode && bindingCode) codeNode.textContent = bindingCode.code;
        if (botId) botId.textContent = bindingCode?.botBasicId || '@pearnly';
        wireDrawerActions();
        updateCountdown();
        return;
    }
    drawerRoot.innerHTML = `<div class="cowork-line-panel"><p class="cowork-line-panel__intro">${text.intro}</p><div class="cowork-line-panel__card"><div class="cowork-line-panel__identity"><span class="cowork-line-panel__avatar">${lineIcon()}</span><div class="cowork-line-panel__identity-text"><div class="cowork-line-panel__name" data-cowork-line-name></div><div class="cowork-line-panel__meta">${text.connectedAt}: <span data-cowork-line-date></span></div></div></div><div class="cowork-line-panel__friendship is-ready"><strong>${text.readyTitle}</strong><p>${text.readyDescription}</p><a class="pu-btn pu-btn--primary" href="${DEFAULT_LINE_URL}" target="_blank" rel="noopener">${text.openLine}</a></div><div class="cowork-line-panel__actions"><button class="pu-btn pu-btn--danger" type="button" data-cowork-line-action="disconnect">${actionPending ? text.disconnecting : text.disconnect}</button></div></div></div>`;
    const name = drawerRoot.querySelector<HTMLElement>('[data-cowork-line-name]');
    const date = drawerRoot.querySelector<HTMLElement>('[data-cowork-line-date]');
    if (name) name.textContent = identity?.displayName || text.connectedAs;
    if (date) date.textContent = formatConnectedAt(identity?.connectedAt || '');
    wireDrawerActions();
}

function wireDrawerActions(): void {
    drawerRoot
        ?.querySelectorAll<HTMLButtonElement>('[data-cowork-line-action]')
        .forEach((button) => {
            button.disabled = actionPending || Boolean(codeRequest);
            button.addEventListener('click', () => {
                const action = button.dataset.coworkLineAction;
                if (action === 'retry') void refreshCoworkLineIdentity(true);
                if (action === 'refresh-code') void fetchBindingCode(true);
                if (action === 'disconnect') void disconnect();
            });
        });
}

function clearCodeTimers(): void {
    if (countdownTimer) clearInterval(countdownTimer);
    if (pollTimer) clearInterval(pollTimer);
    countdownTimer = null;
    pollTimer = null;
}

function updateCountdown(): void {
    const target = drawerRoot?.querySelector<HTMLElement>('[data-cowork-line-expires]');
    if (!target || !bindingCode) return;
    const remaining = bindingCode.expiresAt - Date.now();
    if (remaining <= 0) {
        target.textContent = copy().codeExpired;
        target.classList.add('expiring');
        return;
    }
    const seconds = Math.floor(remaining / 1000);
    const time = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
    target.textContent = copy().codeExpires.replace('{time}', time);
    target.classList.remove('expiring');
}

function startCodeTimers(): void {
    clearCodeTimers();
    updateCountdown();
    countdownTimer = setInterval(updateCountdown, 1000);
    pollTimer = setInterval(() => void checkIdentity(), 3000);
}

async function fetchBindingCode(force = false): Promise<void> {
    if (codeRequest || phase === 'ready') return codeRequest || Promise.resolve();
    if (bindingCode && !force && bindingCode.expiresAt > Date.now()) return;
    codeError = false;
    if (force) bindingCode = null;
    renderDrawer();
    const request = (async () => {
        try {
            const response = await fetch('/api/cowork-line/binding-code', {
                method: 'POST',
                headers: authHeaders(true),
                body: '{}',
            });
            if (!response.ok) throw new Error('binding-code');
            const payload = await response.json();
            const data = payload.data || payload;
            bindingCode = {
                code: String(data.code || ''),
                expiresAt: new Date(String(data.expires_at || '')).getTime(),
                botFriendUrl: String(data.bot_friend_url || DEFAULT_LINE_URL),
                botBasicId: String(data.bot_basic_id || '@pearnly'),
            };
            if (!/^\d{6}$/.test(bindingCode.code) || Number.isNaN(bindingCode.expiresAt)) {
                throw new Error('binding-code-shape');
            }
            startCodeTimers();
        } catch {
            bindingCode = null;
            codeError = true;
        } finally {
            renderDrawer();
        }
    })();
    codeRequest = request;
    try {
        await request;
    } finally {
        if (codeRequest === request) codeRequest = null;
        renderDrawer();
    }
}

async function checkIdentity(): Promise<void> {
    try {
        const response = await fetch('/api/cowork-line/identity', { headers: authHeaders() });
        if (!response.ok) return;
        identity = normalizeIdentity(await response.json());
        if (identity.connected && identity.friendshipReady) {
            phase = 'ready';
            bindingCode = null;
            clearCodeTimers();
            renderSummary();
            renderDrawer();
        }
    } catch {
        return;
    }
}

async function disconnect(): Promise<void> {
    if (actionPending) return;
    const confirmed = await window.showConfirm?.(copy().disconnectConfirm, { danger: true });
    if (!confirmed) return;
    actionPending = true;
    renderDrawer();
    try {
        const response = await fetch('/api/cowork-line/identity', {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error('disconnect');
        identity = { connected: false, friendshipReady: false, displayName: '', connectedAt: '' };
        bindingCode = null;
        phase = 'disconnected';
        window.showToast?.(copy().disconnectedToast, 'success');
        renderSummary();
        void fetchBindingCode();
    } catch {
        window.showToast?.(copy().actionError, 'error');
    } finally {
        actionPending = false;
        renderDrawer();
    }
}

export async function refreshCoworkLineIdentity(force = false): Promise<void> {
    if (loadRequest && !force) return loadRequest;
    phase = 'loading';
    renderSummary();
    renderDrawer();
    const request = (async () => {
        try {
            const response = await fetch('/api/cowork-line/identity', { headers: authHeaders() });
            if (!response.ok) throw new Error('identity');
            identity = normalizeIdentity(await response.json());
            phase = identity.connected
                ? identity.friendshipReady
                    ? 'ready'
                    : 'pendingFriend'
                : 'disconnected';
        } catch {
            identity = null;
            phase = 'error';
        } finally {
            renderSummary();
            renderDrawer();
            if (phase === 'disconnected' || phase === 'pendingFriend') void fetchBindingCode();
        }
    })();
    loadRequest = request;
    try {
        await request;
    } finally {
        if (loadRequest === request) loadRequest = null;
    }
}

export function initCoworkLineSummary(root: HTMLElement): void {
    summaryRoot = root;
    renderSummary();
    window.subscribeI18n?.('cowork-line-identity', () => {
        renderSummary();
        renderDrawer();
    });
    void refreshCoworkLineIdentity();
}

export function mountCoworkLineIdentity(root: HTMLElement): void {
    drawerRoot = root;
    renderDrawer();
    if (phase === 'disconnected' || phase === 'pendingFriend') void fetchBindingCode();
    if (!identity && phase !== 'loading') void refreshCoworkLineIdentity(true);
}
