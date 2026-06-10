/* 邀请接受公开页(/invite/{token} · docs/permissions/04)。
   四态:pending=注册表单 / expired·revoked·used·invalid=对应空态 / 载入 / 错。
   既有账号(1 人 1 租户)不支持入组——文案引导用新邮箱注册。 */
(function () {
    'use strict';
    var token = location.pathname.split('/').pop();
    var card = document.getElementById('card');
    var esc = function (s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    };

    var TX = {
        zh: {
            invited: '{tenant} 邀请你以「{role}」加入 Pearnly',
            sub: '设置你的账号即可开始(7 天内有效)',
            username: '用户名(登录用)',
            password: '密码(至少 8 位 · 含字母和数字)',
            email: '邮箱(选填 · 找回密码用)',
            join: '接受并创建账号',
            joining: '创建中…',
            done: '已加入!用刚设置的账号登录',
            login: '去登录',
            expired: '邀请已过期',
            expired2: '请联系邀请人重新发送',
            revoked: '邀请已被撤回',
            used: '邀请已被使用',
            invalid: '链接无效',
            invalid2: '请核对链接是否完整',
            fail: '载入失败,请刷新重试',
            have_account: '已有 Pearnly 账号?当前一个账号只能属于一家公司,请用新用户名注册。',
        },
        en: {
            invited: '{tenant} invites you to join Pearnly as {role}',
            sub: 'Set up your account to start (valid 7 days)',
            username: 'Username (for sign-in)',
            password: 'Password (8+ chars, letters + digits)',
            email: 'Email (optional, for recovery)',
            join: 'Accept & create account',
            joining: 'Creating…',
            done: 'Joined! Sign in with your new account',
            login: 'Sign in',
            expired: 'Invitation expired',
            expired2: 'Ask the inviter to send a new one',
            revoked: 'Invitation revoked',
            used: 'Invitation already used',
            invalid: 'Invalid link',
            invalid2: 'Check that the link is complete',
            fail: 'Failed to load, please refresh',
            have_account:
                'Already have a Pearnly account? One account belongs to one company — register a new username here.',
        },
        th: {
            invited: '{tenant} เชิญคุณเข้าร่วม Pearnly ในบทบาท {role}',
            sub: 'ตั้งค่าบัญชีเพื่อเริ่มใช้งาน (ลิงก์ใช้ได้ 7 วัน)',
            username: 'ชื่อผู้ใช้ (สำหรับเข้าระบบ)',
            password: 'รหัสผ่าน (8 ตัวขึ้นไป มีตัวอักษรและตัวเลข)',
            email: 'อีเมล (ไม่บังคับ ใช้กู้รหัสผ่าน)',
            join: 'ตอบรับและสร้างบัญชี',
            joining: 'กำลังสร้าง…',
            done: 'เข้าร่วมแล้ว! เข้าสู่ระบบด้วยบัญชีที่ตั้งไว้',
            login: 'เข้าสู่ระบบ',
            expired: 'คำเชิญหมดอายุ',
            expired2: 'ติดต่อผู้เชิญให้ส่งใหม่',
            revoked: 'คำเชิญถูกเพิกถอน',
            used: 'คำเชิญถูกใช้แล้ว',
            invalid: 'ลิงก์ไม่ถูกต้อง',
            invalid2: 'ตรวจสอบว่าลิงก์ครบถ้วน',
            fail: 'โหลดไม่สำเร็จ ลองรีเฟรช',
            have_account:
                'มีบัญชี Pearnly แล้ว? หนึ่งบัญชีอยู่ได้หนึ่งบริษัท กรุณาสมัครด้วยชื่อผู้ใช้ใหม่',
        },
        ja: {
            invited: '{tenant} があなたを {role} として Pearnly に招待しています',
            sub: 'アカウントを設定して開始(7 日間有効)',
            username: 'ユーザー名(ログイン用)',
            password: 'パスワード(8 文字以上・英数字)',
            email: 'メール(任意・復旧用)',
            join: '承諾してアカウント作成',
            joining: '作成中…',
            done: '参加しました!新しいアカウントでログイン',
            login: 'ログイン',
            expired: '招待の期限切れ',
            expired2: '招待者に再送を依頼してください',
            revoked: '招待は取り消されました',
            used: '招待は使用済みです',
            invalid: '無効なリンク',
            invalid2: 'リンクが完全か確認してください',
            fail: '読み込み失敗。再読み込みしてください',
            have_account:
                'Pearnly アカウントをお持ちですか?1 アカウント 1 会社のため、新しいユーザー名で登録してください。',
        },
    };
    var lang = localStorage.getItem('mrpilot_lang');
    if (!TX[lang]) lang = 'th';
    function t(k, vars) {
        var s = TX[lang][k] || TX.en[k] || k;
        if (vars)
            Object.keys(vars).forEach(function (x) {
                s = s.split('{' + x + '}').join(vars[x]);
            });
        return s;
    }
    function brand(html) {
        card.innerHTML =
            '<div class="brand"><img class="brand-icon" src="/static/brand/pwa-icon-192.png?v=1" alt="Pearnly"> Pearnly</div>' +
            html;
    }
    function emptyState(titleKey, subKey) {
        brand(
            '<h1>' +
                t(titleKey) +
                '</h1><div class="sub">' +
                (subKey ? t(subKey) : '') +
                '</div><a class="btn sec" href="/">Pearnly</a>'
        );
    }

    fetch('/api/invitations/' + encodeURIComponent(token) + '/preview')
        .then(function (r) {
            return r.json();
        })
        .then(function (j) {
            var st = j.status;
            if (st === 'pending') return renderForm(j);
            if (st === 'expired') return emptyState('expired', 'expired2');
            if (st === 'revoked') return emptyState('revoked', 'expired2');
            if (st === 'accepted') return emptyState('used', 'expired2');
            return emptyState('invalid', 'invalid2');
        })
        .catch(function () {
            brand('<h1>' + t('fail') + '</h1>');
        });

    function renderForm(j) {
        var roleKey = 'role_' + (j.role_key || '');
        var roleName = (window.CI18N.dict[lang] || {})[roleKey] || j.role_key;
        brand(
            '<h1>' +
                t('invited', { tenant: esc(j.tenant_name || 'Pearnly'), role: esc(roleName) }) +
                '</h1>' +
                '<div class="sub">' +
                t('sub') +
                '</div>' +
                '<div class="field"><label>' +
                t('username') +
                '</label><input id="f-user" autocomplete="username"></div>' +
                '<div class="field"><label>' +
                t('password') +
                '</label><input id="f-pass" type="password" autocomplete="new-password"></div>' +
                (j.email
                    ? ''
                    : '<div class="field"><label>' +
                      t('email') +
                      '</label><input id="f-email" type="email"></div>') +
                '<div class="err" id="f-err" style="margin-bottom:8px"></div>' +
                '<button class="btn pri" id="f-go" style="width:100%">' +
                t('join') +
                '</button>' +
                '<div class="hint" style="margin-top:12px">' +
                t('have_account') +
                '</div>'
        );
        document.getElementById('f-go').onclick = function () {
            var btn = this;
            btn.disabled = true;
            btn.textContent = t('joining');
            var emailEl = document.getElementById('f-email');
            fetch('/api/invitations/' + encodeURIComponent(token) + '/accept', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('f-user').value.trim(),
                    password: document.getElementById('f-pass').value,
                    email: emailEl ? emailEl.value.trim() || null : null,
                }),
            })
                .then(function (r) {
                    return r
                        .json()
                        .catch(function () {
                            return {};
                        })
                        .then(function (body) {
                            if (!r.ok) throw { code: body.detail || 'generic' };
                            brand(
                                '<h1>' +
                                    t('done') +
                                    '</h1><div class="sub"></div><a class="btn pri" href="/login" style="display:block;text-align:center">' +
                                    t('login') +
                                    '</a>'
                            );
                        });
                })
                .catch(function (e) {
                    // 任何失败(业务拒绝/校验 422 数组/网络)都复位按钮 + 显示人话错误
                    btn.disabled = false;
                    btn.textContent = t('join');
                    var code = e && e.code;
                    if (Array.isArray(code) || (code && typeof code === 'object'))
                        code = 'invalid_input';
                    var key = 'err_' + String(code || 'generic').replace(/\./g, '_');
                    var msg = window.ct(key);
                    var errEl = document.getElementById('f-err');
                    if (errEl) errEl.textContent = msg === key ? window.ct('err_generic') : msg;
                });
        };
    }
})();
