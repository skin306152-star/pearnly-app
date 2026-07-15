(function () {
    const root = document.getElementById('pearnly-auth-root');
    const currentLang = () =>
        window.PearnlyCurrentLang || localStorage.getItem('mrpilot_lang') || 'th';

    function icon(name) {
        const common =
            'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
        const paths = {
            user: '<path d="M20 21a8 8 0 0 0-16 0"/><circle cx="12" cy="7" r="4"/>',
            lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
            mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
            eye: '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"/><circle cx="12" cy="12" r="3"/>',
            shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-5"/>',
            cloud: '<path d="M17.5 19H8a6 6 0 1 1 1.2-11.9A7 7 0 0 1 21 12a4 4 0 0 1-3.5 7Z"/>',
            bag: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
            chat: '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z"/>',
            phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.6a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.5-1.2a2 2 0 0 1 2.1-.5c.8.3 1.7.5 2.6.6a2 2 0 0 1 1.8 2Z"/>',
        };
        return `<svg ${common}>${paths[name]}</svg>`;
    }

    function generateFingerprint() {
        try {
            const parts = [
                navigator.userAgent || '',
                navigator.language || '',
                `${screen.width}x${screen.height}x${screen.colorDepth || ''}`,
                String(new Date().getTimezoneOffset()),
                String(navigator.hardwareConcurrency || 0),
                String(navigator.deviceMemory || 0),
                navigator.platform || '',
            ];
            let hash = 0;
            const text = parts.join('|');
            for (let i = 0; i < text.length; i += 1) {
                hash = (hash << 5) - hash + text.charCodeAt(i);
                hash |= 0;
            }
            const fp = `${Math.abs(hash).toString(36)}_${text.length.toString(36)}_${Date.now().toString(36).slice(-4)}`;
            localStorage.setItem('mrpilot_fp', fp);
            return fp;
        } catch (_err) {
            return `fp_err_${Math.random().toString(36).slice(2, 10)}`;
        }
    }

    const FP = generateFingerprint();

    root.innerHTML = `
    <div class="auth-stage">
    <main class="auth-shell" aria-label="Pearnly authentication">
      <section class="brand-panel" aria-label="Pearnly welcome">
        <img class="brand-logo" src="/static/landing/logo.png" alt="Pearnly" />
        <div class="welcome-copy">
          <h1>สวัสดีครับ !</h1>
          <p>พร้อมลุยงานไปด้วยกันนะครับ</p>
        </div>
        <div class="spark spark-a">✦</div>
        <div class="spark spark-b">✦</div>
        <div class="work-bubble">
          <div class="mini-bars" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
          <p>งานวันนี้<br />ราบรื่นดีมากเลยครับ</p>
        </div>
        <div class="cat-wrap">
          <img class="cat-art" src="/static/landing/cat-illustration.png" alt="Pearnly assistant cat" />
        </div>
        <div class="check-card" aria-label="Workflow checklist">
          <div class="check-row"><span class="tick">✓</span><span>ปิดจบ</span></div>
          <div class="check-row"><span class="tick">✓</span><span>ตรวจสอบเอกสาร</span></div>
          <div class="check-row"><span class="tick">✓</span><span>กระทบยอด</span></div>
          <div class="check-row"><span class="tick">✓</span><span>พร้อมวิเคราะห์</span></div>
        </div>
        <div class="check-heart" aria-hidden="true">♥</div>
        <article class="quote-card">
          <header><span class="quote-icon">${icon('chat')}</span><span>Quote วันนี้</span></header>
          <blockquote>ความสำเร็จไม่ได้มาจากการทำงานหนักเพียงวันเดียว<br />แต่มาจากการทำสิ่งเล็ก ๆ อย่างสม่ำเสมอ</blockquote>
          <footer>- PEARNLY Daily Inspiration</footer>
        </article>
      </section>

      <section class="auth-card" aria-label="Login and registration">
        <button class="m-sheet-close" type="button" id="m-sheet-close" aria-label="Close">&times;</button>
        <div class="auth-mode" role="tablist" aria-label="Authentication mode">
          <button class="mode-btn active" type="button" data-mode="login" role="tab" aria-selected="true">เข้าสู่ระบบ</button>
          <button class="mode-btn" type="button" data-mode="signup" role="tab" aria-selected="false">สมัครใช้งาน</button>
        </div>
        <div class="auth-heading">
          <h2 id="auth-title">ยินดีต้อนรับกลับ</h2>
          <p id="auth-subtitle">เข้าสู่ระบบเพื่อต่อยอดงานของคุณ</p>
        </div>

        <form class="auth-form active" id="form-login" autocomplete="on">
          <div class="form-stack">
            <div class="form-row">
              <label for="li-username">ชื่อผู้ใช้งาน (Username)</label>
              <div class="field"><span class="field-icon">${icon('user')}</span><input id="li-username" name="username" type="text" autocomplete="username" placeholder="กรอกชื่อผู้ใช้งาน" /></div>
            </div>
            <div class="form-row">
              <label for="li-password">รหัสผ่าน (Password)</label>
              <div class="field"><span class="field-icon">${icon('lock')}</span><input id="li-password" name="password" type="password" autocomplete="current-password" placeholder="กรอกรหัสผ่าน" /><button class="toggle-password" type="button" data-toggle-password="li-password" aria-label="Show password">${icon('eye')}</button></div>
            </div>
            <div class="form-split">
              <label class="checkline"><input id="li-remember" type="checkbox" checked /> <span>จำการเข้าสู่ระบบ</span></label>
              <button class="link-btn" id="forgot-btn" type="button">ลืมรหัสผ่าน ?</button>
            </div>
            <button class="primary-btn" id="btn-login" type="submit">เข้าสู่ระบบ</button>
          </div>
          <div class="divider"><span>หรือ</span></div>
          <div class="sso-row">
            <button class="outline-btn" type="button" data-sso="google"><span class="google-mark">G</span>เข้าสู่ระบบด้วย Google</button>
            <button class="outline-btn" type="button" data-sso="line"><span class="line-mark">LINE</span>เข้าสู่ระบบด้วย LINE</button>
          </div>
          <p class="legal-line">การเข้าใช้งานถือว่ายอมรับ <a href="/terms" target="_blank" rel="noopener">บริการ</a> และ <a href="/privacy" target="_blank" rel="noopener">ความเป็นส่วนตัว</a></p>
        </form>

        <form class="auth-form" id="form-signup" autocomplete="on">
          <div class="form-stack">
            <div class="form-row">
              <label for="su-email">อีเมล</label>
              <div class="field"><span class="field-icon">${icon('mail')}</span><input id="su-email" name="email" type="email" autocomplete="email" placeholder="hello@company.com" /></div>
            </div>
            <div class="form-row">
              <label for="su-code">รหัสยืนยัน</label>
              <div class="code-field"><div class="field"><input id="su-code" name="verification_code" type="text" inputmode="numeric" autocomplete="one-time-code" placeholder="กรอกรหัส" /></div><button class="send-code-btn" id="btn-send-code" type="button">ส่งรหัส</button></div>
            </div>
            <div class="form-row">
              <label for="su-password">รหัสผ่าน</label>
              <div class="field"><span class="field-icon">${icon('lock')}</span><input id="su-password" name="password" type="password" autocomplete="new-password" placeholder="อย่างน้อย 8 ตัวอักษร" /><button class="toggle-password" type="button" data-toggle-password="su-password" aria-label="Show password">${icon('eye')}</button></div>
            </div>
            <div class="form-row">
              <label for="su-password-confirm">ยืนยันรหัสผ่าน</label>
              <div class="field"><span class="field-icon">${icon('lock')}</span><input id="su-password-confirm" name="password_confirm" type="password" autocomplete="new-password" placeholder="กรอกรหัสผ่านอีกครั้ง" /></div>
            </div>
            <div class="register-options">
              <label class="checkline"><input id="su-agree" type="checkbox" /> <span>ยอมรับ <a href="/terms" target="_blank" rel="noopener">บริการ</a> และ <a href="/privacy" target="_blank" rel="noopener">ความเป็นส่วนตัว</a></span></label>
              <label class="checkline"><input id="su-newsletter" type="checkbox" checked /> <span>รับอัปเดตผลิตภัณฑ์และคำแนะนำ</span></label>
            </div>
            <button class="primary-btn" id="btn-step1" type="submit">สร้างบัญชี</button>
          </div>
        </form>

        <div class="auth-message" id="auth-message" role="status" aria-live="polite"></div>
        <aside class="support-card" aria-label="Pearnly support">
          <div class="support-head">
            <img src="/static/landing/support-avatar.png" alt="" />
            <div><strong>ต้องการความช่วยเหลือ ?</strong><span>สอบถามทีมงาน PEARNLY ได้ผ่านช่องทางด้านล่าง</span></div>
          </div>
          <div class="contact-grid">
            <a class="contact-item" href="mailto:hello@pearnly.com"><span class="contact-dot email">${icon('mail')}</span><span>Email</span></a>
            <a class="contact-item" href="https://line.me/R/ti/p/@pearnly" target="_blank" rel="noopener"><span class="contact-dot line">${icon('chat')}</span><span>@pearnly</span></a>
            <a class="contact-item" href="tel:0868892228"><span class="contact-dot phone">${icon('phone')}</span><span>086-889-2228</span></a>
          </div>
        </aside>
      </section>
    </main>
    <div class="m-backdrop" id="m-backdrop"></div>
    <div class="m-dock">
      <button class="m-login-cta" type="button" id="m-login-cta">เข้าสู่ระบบ / สมัครใช้งาน</button>
      <nav class="m-contact" aria-label="Contact">
        <a href="mailto:hello@pearnly.com">${icon('mail')}<span>Email</span></a>
        <a href="https://line.me/R/ti/p/@pearnly" target="_blank" rel="noopener">${icon('chat')}<span>@pearnly</span></a>
        <a href="tel:0868892228">${icon('phone')}<span>086-889-2228</span></a>
      </nav>
      <ul class="m-secure" aria-label="Trust">
        <li class="m-sec-item">${icon('shield')}<b>ปลอดภัย</b></li>
        <li class="m-sec-item">${icon('cloud')}<b>เข้าถึงทุกที่</b></li>
        <li class="m-sec-item">${icon('lock')}<b>ข้อมูลปลอดภัย</b></li>
      </ul>
    </div>
    <footer class="security-footer" aria-label="Security information">
      <div class="security-item"><span class="security-icon">${icon('shield')}</span><div><strong>ปลอดภัย มั่นใจทุกข้อมูล</strong><span>มาตรฐานความปลอดภัยระดับสากล</span></div></div>
      <div class="security-item"><span class="security-icon">${icon('cloud')}</span><div><strong>เข้าถึงได้ทุกที่ ทุกเวลา</strong><span>ใช้งานได้บนทุกอุปกรณ์</span></div></div>
      <div class="security-item"><span class="security-icon">${icon('lock')}</span><div><strong>ข้อมูลของคุณปลอดภัย</strong><span>เราไม่เปิดเผยข้อมูลให้บุคคลที่สาม</span></div></div>
    </footer>
    <div class="copyright">© 2026 PEARNLY Co., Ltd. All rights reserved.</div>
    </div>
    <div class="modal-overlay" id="forgot-modal" aria-hidden="true">
      <div class="forgot-modal" role="dialog" aria-modal="true" aria-labelledby="forgot-title">
        <h3 id="forgot-title">รีเซ็ตรหัสผ่าน</h3>
        <p>กรอกอีเมลที่ลงทะเบียนไว้ เราจะส่งลิงก์รีเซ็ตให้ทางอีเมล</p>
        <div class="field"><span class="field-icon">${icon('mail')}</span><input id="forgot-email" type="email" autocomplete="email" placeholder="hello@company.com" /></div>
        <div class="modal-actions">
          <button class="secondary-btn" id="forgot-close" type="button">ยกเลิก</button>
          <button class="primary-btn" id="forgot-submit" type="button">ส่งลิงก์</button>
        </div>
      </div>
    </div>`;

    const message = document.getElementById('auth-message');
    const T = (key) => (window.PearnlyMsg ? window.PearnlyMsg(key) : key);

    function setMessage(text, type) {
        message.textContent = text || '';
        message.className = `auth-message ${type || ''}`.trim();
    }

    function setBusy(button, busy, label) {
        if (!button) return;
        if (!button.dataset.label) button.dataset.label = button.textContent;
        button.disabled = busy;
        button.textContent = busy ? label : button.dataset.label;
    }

    function switchMode(mode) {
        const isSignup = mode === 'signup';
        document.querySelector('.auth-card').classList.toggle('signup-mode', isSignup);
        document.querySelectorAll('.mode-btn').forEach((btn) => {
            const active = btn.dataset.mode === mode;
            btn.classList.toggle('active', active);
            btn.setAttribute('aria-selected', String(active));
        });
        document.getElementById('form-login').classList.toggle('active', !isSignup);
        document.getElementById('form-signup').classList.toggle('active', isSignup);
        setMessage('', '');
        // 标题/副标题随模式 + 语言由 i18n 统一设置(读 form-signup.active)
        if (window.PearnlyApplyLanguage) window.PearnlyApplyLanguage();
    }

    document.querySelectorAll('.mode-btn').forEach((btn) => {
        btn.addEventListener('click', () => switchMode(btn.dataset.mode));
    });

    document.addEventListener('click', (event) => {
        const toggle = event.target.closest('[data-toggle-password]');
        if (toggle) {
            const input = document.getElementById(toggle.dataset.togglePassword);
            input.type = input.type === 'password' ? 'text' : 'password';
            return;
        }
        const sso = event.target.closest('[data-sso]');
        if (sso && sso.dataset.sso === 'google') {
            window.location.href = '/api/auth/google/start';
        }
        if (sso && sso.dataset.sso === 'line') {
            window.location.href = '/api/auth/line/start';
        }
    });

    document.getElementById('form-login').addEventListener('submit', async (event) => {
        event.preventDefault();
        const username = document.getElementById('li-username').value.trim();
        const password = document.getElementById('li-password').value;
        const remember = document.getElementById('li-remember').checked;
        if (!username || !password) {
            setMessage(T('enterCred'), 'error');
            return;
        }
        const button = document.getElementById('btn-login');
        setBusy(button, true, T('loggingIn'));
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, remember, entry: 'main' }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.access_token) {
                setMessage(
                    data.detail === 'account_locked' ? T('accountLocked') : T('wrongCred'),
                    'error'
                );
                setBusy(button, false);
                return;
            }
            localStorage.setItem('mrpilot_token', data.access_token);
            localStorage.setItem('mrpilot_lang', currentLang());
            localStorage.setItem('pearnly_entry', 'main');
            setMessage(T('loginSuccess'), 'success');
            window.setTimeout(() => {
                window.location.href = data.is_super_admin ? '/admin/cost' : '/home';
            }, 400);
        } catch (_err) {
            setMessage(T('netError'), 'error');
            setBusy(button, false);
        }
    });

    let codeTimer = null;
    let codeSeconds = 0;

    function updateCodeButton() {
        const button = document.getElementById('btn-send-code');
        button.disabled = codeSeconds > 0;
        button.textContent = codeSeconds > 0 ? `${T('resend')} (${codeSeconds}s)` : T('sendCode');
    }

    function startCodeCountdown(seconds) {
        codeSeconds = seconds || 60;
        updateCodeButton();
        if (codeTimer) clearInterval(codeTimer);
        codeTimer = setInterval(() => {
            codeSeconds -= 1;
            updateCodeButton();
            if (codeSeconds <= 0) clearInterval(codeTimer);
        }, 1000);
    }

    document.getElementById('btn-send-code').addEventListener('click', async () => {
        const email = document.getElementById('su-email').value.trim().toLowerCase();
        if (!email || !email.includes('@') || !email.includes('.')) {
            setMessage(T('invalidEmail'), 'error');
            return;
        }
        const button = document.getElementById('btn-send-code');
        setBusy(button, true, '...');
        try {
            const response = await fetch('/api/auth/send_email_code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    purpose: 'signup',
                    lang: currentLang(),
                }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                const codes = {
                    email_already_registered: 'emailRegistered',
                    resend_too_fast: 'resendTooFast',
                    hourly_limit_reached: 'hourlyLimit',
                    disposable_email_not_allowed: 'disposableEmail',
                };
                setMessage(T(codes[data.detail] || '') || T('sendFail'), 'error');
                setBusy(button, false);
                return;
            }
            setMessage(T('codeSent'), 'success');
            startCodeCountdown(data.resend_after || 60);
        } catch (_err) {
            setMessage(T('netError'), 'error');
            setBusy(button, false);
        }
    });

    document.getElementById('form-signup').addEventListener('submit', async (event) => {
        event.preventDefault();
        const email = document.getElementById('su-email').value.trim().toLowerCase();
        const password = document.getElementById('su-password').value;
        const confirm = document.getElementById('su-password-confirm').value;
        const verificationCode = document.getElementById('su-code').value.trim();
        if (!email || !email.includes('@') || !email.includes('.'))
            return setMessage(T('invalidEmail'), 'error');
        if (password.length < 8 || !/[a-zA-Z]/.test(password) || !/\d/.test(password))
            return setMessage(T('weakPassword'), 'error');
        if (password !== confirm) return setMessage(T('pwMismatch'), 'error');
        if (!/^\d{4,8}$/.test(verificationCode)) return setMessage(T('enterCode'), 'error');
        if (!document.getElementById('su-agree').checked)
            return setMessage(T('agreeRequired'), 'error');
        const button = document.getElementById('btn-step1');
        setBusy(button, true, T('creatingAccount'));
        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    verification_code: verificationCode,
                    full_name: null,
                    company_name: null,
                    role: '',
                    monthly_volume: '',
                    country: 'TH',
                    phone: null,
                    line_id: null,
                    signup_source: null,
                    invite_code: null,
                    newsletter_opt_in: document.getElementById('su-newsletter').checked,
                    fingerprint: FP,
                }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                const codes = {
                    email_already_registered: 'emailRegistered',
                    verification_code_invalid: 'codeInvalid',
                    verification_code_expired: 'codeExpired',
                    password_too_weak: 'passwordTooWeak',
                };
                setMessage(T(codes[data.detail] || '') || T('signupFail'), 'error');
                setBusy(button, false);
                return;
            }
            localStorage.setItem('mrpilot_token', data.token);
            localStorage.setItem('mrpilot_lang', currentLang());
            setMessage(T('signupSuccess'), 'success');
            window.setTimeout(() => {
                window.location.href = '/home';
            }, 600);
        } catch (_err) {
            setMessage(T('netError'), 'error');
            setBusy(button, false);
        }
    });

    const forgotModal = document.getElementById('forgot-modal');
    document
        .getElementById('forgot-btn')
        .addEventListener('click', () => forgotModal.classList.add('show'));
    document
        .getElementById('forgot-close')
        .addEventListener('click', () => forgotModal.classList.remove('show'));
    forgotModal.addEventListener('click', (event) => {
        if (event.target === forgotModal) forgotModal.classList.remove('show');
    });

    // 手机端:底部登录按钮上拉登录框(桌面端这些元素 display:none · 桌面恒显示表单)
    const authStage = document.querySelector('.auth-stage');
    const mOpenSheet = () => authStage && authStage.classList.add('m-auth-open');
    const mCloseSheet = () => authStage && authStage.classList.remove('m-auth-open');
    const mLoginCta = document.getElementById('m-login-cta');
    if (mLoginCta) mLoginCta.addEventListener('click', mOpenSheet);
    const mSheetClose = document.getElementById('m-sheet-close');
    if (mSheetClose) mSheetClose.addEventListener('click', mCloseSheet);
    const mBackdrop = document.getElementById('m-backdrop');
    if (mBackdrop) mBackdrop.addEventListener('click', mCloseSheet);

    document.getElementById('forgot-submit').addEventListener('click', async () => {
        const email = document.getElementById('forgot-email').value.trim().toLowerCase();
        if (!email || !email.includes('@')) {
            setMessage(T('invalidEmail'), 'error');
            return;
        }
        const button = document.getElementById('forgot-submit');
        setBusy(button, true, T('forgotSending'));
        try {
            await fetch('/api/auth/forgot_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, fingerprint: FP }),
            });
            forgotModal.classList.remove('show');
            setMessage(T('forgotSent'), 'success');
        } catch (_err) {
            setMessage(T('netError'), 'error');
        } finally {
            setBusy(button, false);
        }
    });
})();
