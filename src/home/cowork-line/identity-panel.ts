import { authHeaders } from '../dms-intake-core.js';

type Language = 'th' | 'en' | 'zh' | 'ja';
type Phase = 'loading' | 'ready' | 'pendingFriend' | 'disconnected' | 'error';

type Copy = {
    productName: string;
    productDescription: string;
    manage: string;
    loading: string;
    connected: string;
    ready: string;
    pendingFriend: string;
    disconnected: string;
    loadError: string;
    retry: string;
    intro: string;
    connectTitle: string;
    connectDescription: string;
    connect: string;
    connecting: string;
    connectedAs: string;
    connectedAt: string;
    connectSuccess: string;
    friendRequired: string;
    friendTitle: string;
    friendDescription: string;
    addFriend: string;
    checkFriendship: string;
    readyTitle: string;
    readyDescription: string;
    openLine: string;
    connectConflict: string;
    connectExpired: string;
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
        connected: 'เชื่อมต่อแล้ว',
        ready: 'พร้อมใช้งาน',
        pendingFriend: 'รอเพิ่มเพื่อน',
        disconnected: 'ยังไม่เชื่อมต่อ',
        loadError: 'โหลดสถานะ LINE ไม่สำเร็จ',
        retry: 'ลองอีกครั้ง',
        intro: 'การเชื่อมต่อนี้เป็นของบัญชีคุณเท่านั้น สมาชิกแต่ละคนเชื่อมต่อ LINE ของตนเอง',
        connectTitle: 'เชื่อมต่อ LINE ของคุณ',
        connectDescription: 'หลังเชื่อมต่อ คุณจะเปิด Pearnly Cowork LINE ด้วยบัญชีพนักงานนี้ได้',
        connect: 'เชื่อมต่อ LINE',
        connecting: 'กำลังเชื่อมต่อ…',
        connectedAs: 'เชื่อมต่อในชื่อ',
        connectedAt: 'เชื่อมต่อเมื่อ',
        connectSuccess: 'เชื่อมต่อ LINE สำเร็จ',
        friendRequired: 'เชื่อมต่อบัญชีแล้ว กรุณาเพิ่ม Pearnly เป็นเพื่อนให้เสร็จ',
        friendTitle: 'เพิ่ม Pearnly เป็นเพื่อน',
        friendDescription: 'เพิ่มเพื่อนแล้วกลับมากดตรวจสอบอีกครั้ง',
        addFriend: 'เพิ่มเพื่อนใน LINE',
        checkFriendship: 'ตรวจสอบอีกครั้ง',
        readyTitle: 'LINE พร้อมใช้งาน',
        readyDescription: 'เปิดห้องแชต Pearnly Cowork LINE ได้ทันที',
        openLine: 'เปิด Cowork LINE',
        connectConflict: 'LINE นี้เชื่อมต่อกับสมาชิกคนอื่นแล้ว',
        connectExpired: 'ลิงก์เชื่อมต่อหมดอายุ กรุณาลองใหม่',
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
        connected: 'Connected',
        ready: 'Ready',
        pendingFriend: 'Add friend',
        disconnected: 'Not connected',
        loadError: 'Could not load your LINE status',
        retry: 'Try again',
        intro: 'This connection belongs only to your account. Each employee connects their own LINE.',
        connectTitle: 'Connect your LINE',
        connectDescription: 'Once connected, Pearnly Cowork LINE opens as this employee account.',
        connect: 'Connect LINE',
        connecting: 'Connecting…',
        connectedAs: 'Connected as',
        connectedAt: 'Connected on',
        connectSuccess: 'LINE connected',
        friendRequired: 'Your account is connected. Add Pearnly as a friend to finish setup.',
        friendTitle: 'Add Pearnly as a friend',
        friendDescription: 'After adding the account, return here and check again.',
        addFriend: 'Add friend in LINE',
        checkFriendship: 'Check again',
        readyTitle: 'LINE is ready',
        readyDescription: 'You can open the Pearnly Cowork LINE chat now.',
        openLine: 'Open Cowork LINE',
        connectConflict: 'This LINE is already connected to another member',
        connectExpired: 'The connection link expired. Please try again.',
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
        connected: '已连接',
        ready: '可以使用',
        pendingFriend: '待添加好友',
        disconnected: '未连接',
        loadError: '无法读取你的 LINE 连接状态',
        retry: '重试',
        intro: '这里仅管理你本人的连接；每位员工分别连接自己的 LINE。',
        connectTitle: '连接你的 LINE',
        connectDescription: '连接后，Pearnly Cowork LINE 将使用当前员工账号打开。',
        connect: '连接 LINE',
        connecting: '正在连接…',
        connectedAs: '连接账号',
        connectedAt: '连接时间',
        connectSuccess: 'LINE 连接成功',
        friendRequired: '账号已绑定，请添加 Pearnly 好友后完成设置。',
        friendTitle: '添加 Pearnly 为好友',
        friendDescription: '添加后返回此处，再检查一次好友状态。',
        addFriend: '去 LINE 添加好友',
        checkFriendship: '重新检查',
        readyTitle: 'LINE 已可使用',
        readyDescription: '现在可以直接打开 Pearnly Cowork LINE 对话。',
        openLine: '打开 Cowork LINE',
        connectConflict: '该 LINE 已连接其他成员账号',
        connectExpired: '连接已过期，请重新发起。',
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
        connected: '連携済み',
        ready: '利用可能',
        pendingFriend: '友だち追加待ち',
        disconnected: '未連携',
        loadError: 'LINE の連携状態を読み込めませんでした',
        retry: '再試行',
        intro: 'ここでは本人の連携のみを管理します。従業員ごとに自分の LINE を連携します。',
        connectTitle: '自分の LINE を連携',
        connectDescription: '連携後、Pearnly Cowork LINE は現在の従業員アカウントで開きます。',
        connect: 'LINE を連携',
        connecting: '連携中…',
        connectedAs: '連携アカウント',
        connectedAt: '連携日時',
        connectSuccess: 'LINE を連携しました',
        friendRequired: 'アカウントを連携しました。Pearnly を友だち追加してください。',
        friendTitle: 'Pearnly を友だち追加',
        friendDescription: '追加後、この画面に戻ってもう一度確認してください。',
        addFriend: 'LINE で友だち追加',
        checkFriendship: 'もう一度確認',
        readyTitle: 'LINE を利用できます',
        readyDescription: 'Pearnly Cowork LINE のトークを開けます。',
        openLine: 'Cowork LINE を開く',
        connectConflict: 'この LINE は別のメンバーに連携されています',
        connectExpired: '連携リンクの有効期限が切れました。もう一度お試しください。',
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

const COWORK_LINE_URL = 'https://line.me/R/ti/p/@pearnly';

let phase: Phase = 'loading';
let identity: Identity | null = null;
let summaryRoot: HTMLElement | null = null;
let drawerRoot: HTMLElement | null = null;
let loadRequest: Promise<void> | null = null;
let actionPending = false;

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
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString(language());
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

function lineIcon(): string {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11.5a7.5 7.5 0 01-8 7.46L7 22l1.2-4.1A7.5 7.5 0 1120 11.5z"/><path d="M8 11h.01M12 11h.01M16 11h.01"/></svg>';
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
    if (phase === 'disconnected') {
        drawerRoot.innerHTML = `<div class="cowork-line-panel"><p class="cowork-line-panel__intro">${text.intro}</p><div class="pu-empty"><span class="pu-empty__icon">${lineIcon()}</span><h3 class="pu-empty__title">${text.connectTitle}</h3><p class="pu-empty__desc">${text.connectDescription}</p><button class="pu-btn pu-btn--primary pu-btn--lg" type="button" data-cowork-line-action="connect">${actionPending ? text.connecting : text.connect}</button></div></div>`;
        wireDrawerActions();
        return;
    }
    const friendship =
        phase === 'ready'
            ? `<div class="cowork-line-panel__friendship is-ready"><strong>${text.readyTitle}</strong><p>${text.readyDescription}</p><a class="pu-btn pu-btn--primary" href="${COWORK_LINE_URL}" target="_blank" rel="noopener">${text.openLine}</a></div>`
            : `<div class="cowork-line-panel__friendship is-pending"><strong>${text.friendTitle}</strong><p>${text.friendDescription}</p><div class="cowork-line-panel__friendship-actions"><a class="pu-btn pu-btn--primary" href="${COWORK_LINE_URL}" target="_blank" rel="noopener">${text.addFriend}</a><button class="pu-btn pu-btn--outline" type="button" data-cowork-line-action="connect">${actionPending ? text.connecting : text.checkFriendship}</button></div></div>`;
    drawerRoot.innerHTML = `<div class="cowork-line-panel"><p class="cowork-line-panel__intro">${text.intro}</p><div class="cowork-line-panel__card"><div class="cowork-line-panel__identity"><span class="cowork-line-panel__avatar">${lineIcon()}</span><div class="cowork-line-panel__identity-text"><div class="cowork-line-panel__name" data-cowork-line-name></div><div class="cowork-line-panel__meta">${text.connectedAt}: <span data-cowork-line-date></span></div></div></div>${friendship}<div class="cowork-line-panel__actions"><button class="pu-btn pu-btn--danger" type="button" data-cowork-line-action="disconnect">${actionPending ? text.disconnecting : text.disconnect}</button></div></div></div>`;
    const name = drawerRoot.querySelector<HTMLElement>('[data-cowork-line-name]');
    const date = drawerRoot.querySelector<HTMLElement>('[data-cowork-line-date]');
    if (name) name.textContent = identity?.displayName || text.connectedAs;
    if (date) date.textContent = formatConnectedAt(identity?.connectedAt || '');
    wireDrawerActions();
}

function wireDrawerActions(): void {
    if (!drawerRoot) return;
    drawerRoot
        .querySelectorAll<HTMLButtonElement>('[data-cowork-line-action]')
        .forEach((button) => {
            button.disabled = actionPending;
            button.addEventListener('click', () => {
                const action = button.dataset.coworkLineAction;
                if (action === 'retry') void refreshCoworkLineIdentity(true);
                if (action === 'connect') void connect();
                if (action === 'disconnect') void disconnect();
            });
        });
}

async function connect(): Promise<void> {
    if (actionPending) return;
    actionPending = true;
    renderDrawer();
    try {
        const response = await fetch('/api/cowork-line/connect/start', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({
                return_to: location.pathname + location.search + location.hash,
            }),
        });
        if (!response.ok) throw new Error('connect');
        const payload = await response.json();
        const data = payload.data || payload;
        if (!data.url) throw new Error('connect-url');
        window.location.assign(String(data.url));
    } catch {
        actionPending = false;
        renderDrawer();
        window.showToast?.(copy().actionError, 'error');
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
        identity = {
            connected: false,
            friendshipReady: false,
            displayName: '',
            connectedAt: '',
        };
        phase = 'disconnected';
        window.showToast?.(copy().disconnectedToast, 'success');
        renderSummary();
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
            const response = await fetch('/api/cowork-line/identity', {
                headers: authHeaders(),
            });
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
    const url = new URL(window.location.href);
    const connectResult = url.searchParams.get('cowork_line_connect');
    if (connectResult) {
        const message = {
            ok: copy().connectSuccess,
            friend_required: copy().friendRequired,
            conflict: copy().connectConflict,
            expired: copy().connectExpired,
            error: copy().actionError,
        }[connectResult];
        if (message) {
            window.showToast?.(
                message,
                connectResult === 'ok'
                    ? 'success'
                    : connectResult === 'friend_required'
                      ? 'info'
                      : 'error'
            );
        }
        url.searchParams.delete('cowork_line_connect');
        history.replaceState(null, '', url.pathname + url.search + url.hash);
    }
    window.subscribeI18n?.('cowork-line-identity', () => {
        renderSummary();
        renderDrawer();
    });
    void refreshCoworkLineIdentity();
}

export function mountCoworkLineIdentity(root: HTMLElement): void {
    drawerRoot = root;
    renderDrawer();
    if (!identity && phase !== 'loading') void refreshCoworkLineIdentity(true);
}
