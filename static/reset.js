// 重置密码落地页 · 凭邮件/LINE 链接里的 ?token= 设新密码 · 接 POST /api/auth/reset_password。
// 自包含 · 不依赖主 bundle(链接接入流要在任何状态下可用)。
(function () {
    'use strict';

    var I18N = {
        zh: {
            title: '重置密码',
            sub: '设置一个新密码 · 至少 8 位,含字母和数字。',
            labelNew: '新密码',
            labelConfirm: '确认新密码',
            submit: '重置密码',
            submitting: '提交中…',
            back: '返回登录',
            empty: '请填写新密码',
            short: '密码至少 8 位',
            weak: '密码需同时含字母和数字',
            mismatch: '两次输入的密码不一致',
            badLink: '链接无效或已失效 · 请重新申请重置邮件',
            invalidToken: '链接无效 · 请重新申请重置邮件',
            expired: '链接已过期 · 请重新申请重置邮件',
            used: '链接已使用过 · 请重新申请重置邮件',
            success: '密码已重置 · 正在跳转登录…',
            failed: '重置失败 · 请稍后重试',
        },
        th: {
            title: 'ตั้งรหัสผ่านใหม่',
            sub: 'ตั้งรหัสผ่านใหม่ · อย่างน้อย 8 ตัว มีตัวอักษรและตัวเลข',
            labelNew: 'รหัสผ่านใหม่',
            labelConfirm: 'ยืนยันรหัสผ่านใหม่',
            submit: 'ตั้งรหัสผ่านใหม่',
            submitting: 'กำลังส่ง…',
            back: 'กลับไปเข้าสู่ระบบ',
            empty: 'กรุณากรอกรหัสผ่านใหม่',
            short: 'รหัสผ่านอย่างน้อย 8 ตัว',
            weak: 'รหัสผ่านต้องมีทั้งตัวอักษรและตัวเลข',
            mismatch: 'รหัสผ่านไม่ตรงกัน',
            badLink: 'ลิงก์ไม่ถูกต้องหรือหมดอายุ · กรุณาขอลิงก์ใหม่',
            invalidToken: 'ลิงก์ไม่ถูกต้อง · กรุณาขอลิงก์ใหม่',
            expired: 'ลิงก์หมดอายุ · กรุณาขอลิงก์ใหม่',
            used: 'ลิงก์ถูกใช้ไปแล้ว · กรุณาขอลิงก์ใหม่',
            success: 'ตั้งรหัสผ่านใหม่แล้ว · กำลังไปหน้าเข้าสู่ระบบ…',
            failed: 'ตั้งรหัสผ่านไม่สำเร็จ · ลองใหม่อีกครั้ง',
        },
        en: {
            title: 'Reset password',
            sub: 'Set a new password · at least 8 characters with a letter and a number.',
            labelNew: 'New password',
            labelConfirm: 'Confirm new password',
            submit: 'Reset password',
            submitting: 'Submitting…',
            back: 'Back to login',
            empty: 'Please enter a new password',
            short: 'Password must be at least 8 characters',
            weak: 'Password needs both letters and numbers',
            mismatch: 'Passwords do not match',
            badLink: 'Invalid or expired link · request a new reset email',
            invalidToken: 'Invalid link · request a new reset email',
            expired: 'Link expired · request a new reset email',
            used: 'Link already used · request a new reset email',
            success: 'Password reset · redirecting to login…',
            failed: 'Reset failed · please try again',
        },
        ja: {
            title: 'パスワード再設定',
            sub: '新しいパスワードを設定 · 8 文字以上、英字と数字を含む。',
            labelNew: '新しいパスワード',
            labelConfirm: '新しいパスワード（確認）',
            submit: 'パスワードを再設定',
            submitting: '送信中…',
            back: 'ログインに戻る',
            empty: '新しいパスワードを入力してください',
            short: 'パスワードは 8 文字以上',
            weak: 'パスワードは英字と数字の両方が必要',
            mismatch: 'パスワードが一致しません',
            badLink: 'リンクが無効か期限切れです · 再送信してください',
            invalidToken: 'リンクが無効です · 再送信してください',
            expired: 'リンクの有効期限切れ · 再送信してください',
            used: 'リンクは使用済みです · 再送信してください',
            success: 'パスワードを再設定しました · ログインへ移動中…',
            failed: '再設定に失敗 · もう一度お試しください',
        },
    };

    var lang = pickLang();
    var dict = I18N[lang] || I18N.zh;
    var token = new URLSearchParams(location.search).get('token') || '';

    function pickLang() {
        var saved = '';
        try {
            saved = localStorage.getItem('mrpilot_lang') || '';
        } catch (e) {}
        var nav = (navigator.language || '').slice(0, 2);
        var cand = saved || nav;
        return I18N[cand] ? cand : 'zh';
    }

    function $(id) {
        return document.getElementById(id);
    }

    function applyLang() {
        document.documentElement.lang = lang;
        $('r-title').textContent = dict.title;
        $('r-sub').textContent = dict.sub;
        $('r-label-new').textContent = dict.labelNew;
        $('r-label-confirm').textContent = dict.labelConfirm;
        $('r-submit').textContent = dict.submit;
        $('r-back').textContent = dict.back;
        document.querySelectorAll('#r-langbar button').forEach(function (b) {
            b.classList.toggle('active', b.dataset.lang === lang);
        });
    }

    function setMsg(text, kind) {
        var el = $('r-msg');
        el.textContent = text || '';
        el.className = 'msg' + (kind ? ' ' + kind : '');
    }

    function strength(pw) {
        var s = 0;
        if (pw.length >= 8) s++;
        if (pw.length >= 12) s++;
        if (/[a-zA-Z]/.test(pw) && /\d/.test(pw)) s++;
        return Math.min(3, s);
    }

    function errMessage(detail) {
        if (detail === 'invalid_token') return dict.invalidToken;
        if (detail === 'token_expired') return dict.expired;
        if (detail === 'token_already_used') return dict.used;
        if (detail === 'password_too_short') return dict.short;
        if (detail === 'password_too_weak') return dict.weak;
        return dict.failed;
    }

    async function submit(e) {
        e.preventDefault();
        var pw = $('r-new').value;
        var cf = $('r-confirm').value;
        if (!pw || !cf) return setMsg(dict.empty, 'error');
        if (pw.length < 8) return setMsg(dict.short, 'error');
        if (!(/[a-zA-Z]/.test(pw) && /\d/.test(pw))) return setMsg(dict.weak, 'error');
        if (pw !== cf) return setMsg(dict.mismatch, 'error');

        var btn = $('r-submit');
        btn.disabled = true;
        btn.textContent = dict.submitting;
        setMsg('', '');
        try {
            var r = await fetch('/api/auth/reset_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token, new_password: pw }),
            });
            var data = await r.json().catch(function () {
                return {};
            });
            if (r.ok && data.ok) {
                setMsg(dict.success, 'success');
                setTimeout(function () {
                    location.href = '/login';
                }, 1500);
                return;
            }
            setMsg(errMessage(data.detail), 'error');
        } catch (err) {
            setMsg(dict.failed, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = dict.submit;
        }
    }

    function bind() {
        document.querySelectorAll('.eye').forEach(function (eye) {
            eye.addEventListener('click', function () {
                var inp = $(eye.dataset.target);
                if (inp) inp.type = inp.type === 'password' ? 'text' : 'password';
            });
        });
        $('r-new').addEventListener('input', function () {
            var bar = $('r-strength');
            bar.className =
                'strength-bar ' + ['', 'weak', 'medium', 'strong'][strength(this.value)];
        });
        $('r-form').addEventListener('submit', submit);
        $('r-langbar').addEventListener('click', function (e) {
            var b = e.target.closest('button[data-lang]');
            if (!b) return;
            lang = b.dataset.lang;
            dict = I18N[lang] || I18N.zh;
            try {
                localStorage.setItem('mrpilot_lang', lang);
            } catch (e2) {}
            applyLang();
            setMsg('', '');
        });
    }

    applyLang();
    bind();
    if (!token || token.length < 16) {
        setMsg(dict.badLink, 'error');
        $('r-submit').disabled = true;
    }
})();
