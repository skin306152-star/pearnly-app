/* global liff */
(() => {
    'use strict';
    const $ = (id) => document.getElementById(id);
    const words = {
        th: [
            'เชื่อมต่อ LINE',
            'เชิญพนักงาน',
            'ชื่อพนักงาน',
            'บัญชีผู้ใช้',
            'รหัสผ่าน',
            'ยืนยัน',
            'กลับไปที่ LINE',
            'คัดลอกคำเชิญ',
            'กรอกบัญชีและรหัสผ่านที่ได้รับจากผู้เชิญ',
            'สร้างบัญชีพนักงานในทีมนี้ แล้วส่งคำเชิญให้พนักงานด้วยตัวคุณเอง',
        ],
        zh: [
            '绑定 LINE',
            '邀请员工',
            '员工姓名',
            '账号',
            '密码',
            '确定',
            '返回 LINE',
            '复制邀请',
            '输入邀请人提供的账号和密码',
            '在本团队创建员工账号，然后由你转发邀请给员工',
        ],
        en: [
            'Connect LINE',
            'Invite employee',
            'Employee name',
            'Account',
            'Password',
            'Confirm',
            'Back to LINE',
            'Copy invitation',
            'Enter the account and password provided by your inviter',
            'Create an employee in this team, then forward the invitation yourself',
        ],
        ja: [
            'LINE を連携',
            '従業員を招待',
            '従業員名',
            'アカウント',
            'パスワード',
            '確認',
            'LINE に戻る',
            '招待をコピー',
            '招待者から受け取ったアカウントとパスワードを入力',
            'このチームに従業員を作成し、招待を自分で送信してください',
        ],
    };
    let invite = false;
    let board = '';
    let idToken = '';
    let requestId = crypto.randomUUID();
    $('form').addEventListener('input', () => {
        requestId = crypto.randomUUID();
    });
    function render() {
        const w = words[$('language').value];
        document.documentElement.lang = $('language').value;
        $('title').textContent = w[invite ? 1 : 0];
        $('name-label').textContent = w[2];
        $('account-label').textContent = w[3];
        $('password-label').textContent = w[4];
        $('submit').textContent = w[5];
        $('close').textContent = w[6];
        $('copy').textContent = w[7];
        $('hint').textContent = w[invite ? 9 : 8];
        $('name-row').hidden = !invite;
        $('name').required = invite;
        $('password').autocomplete = invite ? 'new-password' : 'current-password';
    }
    async function post(path, body, token) {
        const response = await fetch(path, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: 'Bearer ' + token } : {}),
            },
            body: JSON.stringify(body),
            cache: 'no-store',
        });
        const data = await response.json();
        if (!response.ok)
            throw new Error(typeof data.detail === 'string' ? data.detail : 'request_failed');
        return data;
    }
    $('language').onchange = render;
    $('close').onclick = () => liff.closeWindow();
    $('copy').onclick = async () => {
        try {
            await navigator.clipboard.writeText($('invitation').value);
            $('status').textContent = 'คัดลอกแล้วครับ';
        } catch {
            $('invitation').focus();
            $('invitation').select();
            $('status').textContent = 'กรุณาคัดลอกข้อความที่เลือกครับ';
        }
    };
    $('form').onsubmit = async (event) => {
        event.preventDefault();
        $('submit').disabled = true;
        $('status').textContent = 'กำลังดำเนินการ…';
        try {
            if (invite) {
                const result = await post('/api/cowork-line/work-invite', {
                    id_token: idToken,
                    request_id: requestId,
                    board,
                    account: $('account').value.trim(),
                    password: $('password').value,
                    display_name: $('name').value.trim(),
                });
                $('invitation').value =
                    `เชิญร่วมทีม Pearnly\nบัญชี: ${result.account}\nรหัสผ่าน: ${$('password').value}\nเชื่อมต่อ LINE: ${result.connect_url}\nหลังเชื่อมต่อ กลับไปที่แชตแล้วเลือกเมนูงานครับ`;
                $('invitation').hidden = false;
                $('copy').hidden = false;
                $('status').textContent =
                    'สร้างบัญชีและเพิ่มเข้าทีมแล้วครับ กรุณาส่งคำเชิญให้พนักงาน';
            } else {
                const login = await post('/api/login', {
                    username: $('account').value.trim(),
                    password: $('password').value,
                    entry: 'cowork',
                    remember: false,
                });
                const connected = await post(
                    '/api/cowork-line/connect',
                    { id_token: idToken },
                    login.token
                );
                $('chat-link').href = connected.bot_friend_url;
                $('chat-link').hidden = false;
                $('status').textContent =
                    'เชื่อมต่อเรียบร้อยครับ กลับไปที่แชต พิมพ์ “เมนู” แล้วเลือกงาน';
            }
            $('password').value = '';
            $('form').hidden = true;
            $('close').hidden = false;
        } catch (error) {
            const reason = String(error.message);
            $('status').textContent = /conflict|already_connected/.test(reason)
                ? 'บัญชีหรือ LINE นี้เชื่อมต่ออยู่แล้วครับ กรุณาตรวจสอบบัญชี'
                : /account_exists/.test(reason)
                  ? 'บัญชีนี้มีอยู่แล้วครับ กรุณาเลือกสมาชิกเดิมจากเมนูทีม'
                  : 'ดำเนินการไม่สำเร็จครับ กรุณาตรวจสอบข้อมูลและลองอีกครั้ง';
            $('submit').disabled = false;
        }
    };
    render();
    (async () => {
        try {
            const response = await fetch('/api/cowork-line/intake/liff/config');
            const config = await response.json();
            if (!config.data?.liff_id) throw new Error('config');
            await liff.init({ liffId: config.data?.liff_id });
            if (!liff.isLoggedIn()) {
                liff.login({ redirectUri: location.href });
                return;
            }
            const params = new URLSearchParams(location.search);
            invite = params.get('draft') === 'invite';
            board = params.get('board') || '';
            idToken = liff.getIDToken();
            if (!idToken || (invite && !board)) throw new Error('identity');
            render();
            $('submit').disabled = false;
        } catch {
            $('status').textContent = 'กรุณาเปิดลิงก์นี้ใน LINE อีกครั้งครับ';
        }
    })();
})();
