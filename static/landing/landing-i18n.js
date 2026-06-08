(function () {
    const langs = ['zh', 'th', 'en', 'ja'];
    const labels = { zh: '中', th: 'TH', en: 'EN', ja: '日' };
    const copy = {
        zh: {
            welcomeTitle: '您好 !',
            welcomeSub: '准备好一起把工作推进吧 💗',
            bubble: '今天的工作<br />会很顺利 😊',
            checklist: ['关账', '检查文件', '对账', '准备分析'],
            quoteLabel: '今日 Quote',
            quote: '成功不是来自某一天的拼命工作<br />而是来自每天稳定完成小事',
            quoteBy: '- PEARNLY Daily Inspiration',
            loginTab: '登录',
            signupTab: '注册',
            loginTitle: '欢迎回来 👋',
            loginSub: '登录系统，继续推进你的工作',
            signupTitle: '开始使用 Pearnly',
            signupSub: '创建账号并验证邮箱即可开始使用',
            username: '用户名',
            usernamePh: '请输入用户名',
            password: '密码',
            passwordPh: '请输入密码',
            remember: '记住登录状态',
            forgot: '忘记密码 ?',
            loginBtn: '登录',
            or: '或',
            google: '使用 Google 登录',
            lineLogin: '使用 LINE 登录',
            loginLegal:
                '登录即表示同意 <a href="/terms" target="_blank" rel="noopener">服务条款</a> 和 <a href="/privacy" target="_blank" rel="noopener">隐私政策</a>',
            email: '邮箱',
            emailPh: 'hello@company.com',
            code: '验证码',
            codePh: '请输入验证码',
            sendCode: '发送验证码',
            signupPassword: '密码',
            signupPasswordPh: '至少 8 个字符',
            confirmPassword: '确认密码',
            confirmPasswordPh: '请再次输入密码',
            agree: '我已同意 <a href="/terms" target="_blank" rel="noopener">服务条款</a> 和 <a href="/privacy" target="_blank" rel="noopener">隐私政策</a>',
            newsletter: '接收产品更新和使用建议',
            create: '创建账号',
            supportTitle: '需要帮助 ?',
            supportSub: '可以通过下方渠道联系 PEARNLY 团队',
            secure1: '安全，守护每一份数据',
            secure1Sub: '采用国际级安全标准',
            secure2: '随时随地访问',
            secure2Sub: '可在所有设备上使用',
            secure3: '你的数据很安全',
            secure3Sub: '我们不会向第三方披露数据',
            forgotTitle: '重置密码',
            forgotText: '输入注册邮箱，我们会发送密码重置链接。',
            cancel: '取消',
            sendLink: '发送链接',
        },
        th: {
            welcomeTitle: 'สวัสดีครับ !',
            welcomeSub: 'พร้อมลุยงานไปด้วยกันนะครับ 💗',
            bubble: 'งานวันนี้<br />ราบรื่นดีมากเลยครับ 😊',
            checklist: ['ปิดจบ', 'ตรวจสอบเอกสาร', 'กระทบยอด', 'พร้อมวิเคราะห์'],
            quoteLabel: 'Quote วันนี้',
            quote: 'ความสำเร็จไม่ได้มาจากการทำงานหนักเพียงวันเดียว<br />แต่มาจากการทำสิ่งเล็ก ๆ อย่างสม่ำเสมอ',
            quoteBy: '- PEARNLY Daily Inspiration',
            loginTab: 'เข้าสู่ระบบ',
            signupTab: 'สมัครใช้งาน',
            loginTitle: 'ยินดีต้อนรับกลับ 👋',
            loginSub: 'เข้าสู่ระบบเพื่อไปต่อกับงานของคุณ',
            signupTitle: 'เริ่มต้นกับ Pearnly',
            signupSub: 'สร้างบัญชีและยืนยันอีเมลเพื่อเริ่มใช้งาน',
            username: 'ชื่อผู้ใช้งาน',
            usernamePh: 'กรอกชื่อผู้ใช้งาน',
            password: 'รหัสผ่าน',
            passwordPh: 'กรอกรหัสผ่าน',
            remember: 'จำการเข้าสู่ระบบ',
            forgot: 'ลืมรหัสผ่าน ?',
            loginBtn: 'เข้าสู่ระบบ',
            or: 'หรือ',
            google: 'เข้าสู่ระบบด้วย Google',
            lineLogin: 'เข้าสู่ระบบด้วย LINE',
            loginLegal:
                'การเข้าใช้งานถือว่ายอมรับ <a href="/terms" target="_blank" rel="noopener">บริการ</a> และ <a href="/privacy" target="_blank" rel="noopener">ความเป็นส่วนตัว</a>',
            email: 'อีเมล',
            emailPh: 'hello@company.com',
            code: 'รหัสยืนยัน',
            codePh: 'กรอกรหัส',
            sendCode: 'ส่งรหัส',
            signupPassword: 'รหัสผ่าน',
            signupPasswordPh: 'อย่างน้อย 8 ตัวอักษร',
            confirmPassword: 'ยืนยันรหัสผ่าน',
            confirmPasswordPh: 'กรอกรหัสผ่านอีกครั้ง',
            agree: 'ยอมรับ <a href="/terms" target="_blank" rel="noopener">บริการ</a> และ <a href="/privacy" target="_blank" rel="noopener">ความเป็นส่วนตัว</a>',
            newsletter: 'รับอัปเดตผลิตภัณฑ์และคำแนะนำ',
            create: 'สร้างบัญชี',
            supportTitle: 'ต้องการความช่วยเหลือ ?',
            supportSub: 'สอบถามทีมงาน PEARNLY ได้ผ่านช่องทางด้านล่าง',
            secure1: 'ปลอดภัย มั่นใจทุกข้อมูล',
            secure1Sub: 'มาตรฐานความปลอดภัยระดับสากล',
            secure2: 'เข้าถึงได้ทุกที่ ทุกเวลา',
            secure2Sub: 'ใช้งานได้บนทุกอุปกรณ์',
            secure3: 'ข้อมูลของคุณปลอดภัย',
            secure3Sub: 'เราไม่เปิดเผยข้อมูลให้บุคคลที่สาม',
            forgotTitle: 'รีเซ็ตรหัสผ่าน',
            forgotText: 'กรอกอีเมลที่ลงทะเบียนไว้ เราจะส่งลิงก์รีเซ็ตให้ทางอีเมล',
            cancel: 'ยกเลิก',
            sendLink: 'ส่งลิงก์',
        },
        en: {
            welcomeTitle: 'Hello !',
            welcomeSub: 'Ready to move work forward together 💗',
            bubble: "Today's work<br />is flowing nicely 😊",
            checklist: ['Close', 'Check docs', 'Reconcile', 'Ready to analyze'],
            quoteLabel: 'Quote Today',
            quote: 'Success does not come from one hard day of work<br />but from doing small things consistently',
            quoteBy: '- PEARNLY Daily Inspiration',
            loginTab: 'Log in',
            signupTab: 'Sign up',
            loginTitle: 'Welcome back 👋',
            loginSub: 'Log in to continue your work',
            signupTitle: 'Start with Pearnly',
            signupSub: 'Create an account and verify email to begin',
            username: 'Username',
            usernamePh: 'Enter username',
            password: 'Password',
            passwordPh: 'Enter password',
            remember: 'Remember me',
            forgot: 'Forgot password ?',
            loginBtn: 'Log in',
            or: 'or',
            google: 'Continue with Google',
            lineLogin: 'Continue with LINE',
            loginLegal:
                'By logging in, you agree to the <a href="/terms" target="_blank" rel="noopener">Terms</a> and <a href="/privacy" target="_blank" rel="noopener">Privacy Policy</a>',
            email: 'Email',
            emailPh: 'hello@company.com',
            code: 'Verification code',
            codePh: 'Enter code',
            sendCode: 'Send code',
            signupPassword: 'Password',
            signupPasswordPh: 'At least 8 characters',
            confirmPassword: 'Confirm password',
            confirmPasswordPh: 'Enter password again',
            agree: 'I agree to the <a href="/terms" target="_blank" rel="noopener">Terms</a> and <a href="/privacy" target="_blank" rel="noopener">Privacy Policy</a>',
            newsletter: 'Send me product updates and tips',
            create: 'Create account',
            supportTitle: 'Need help ?',
            supportSub: 'Contact the PEARNLY team below',
            secure1: 'Safe for every file',
            secure1Sub: 'International security standards',
            secure2: 'Access anywhere',
            secure2Sub: 'Works across all devices',
            secure3: 'Your data stays safe',
            secure3Sub: 'We do not disclose data to third parties',
            forgotTitle: 'Reset password',
            forgotText: 'Enter your registered email. We will send a reset link.',
            cancel: 'Cancel',
            sendLink: 'Send link',
        },
        ja: {
            welcomeTitle: 'こんにちは !',
            welcomeSub: '一緒に仕事を進めましょう 💗',
            bubble: '今日の仕事も<br />スムーズです 😊',
            checklist: ['締め処理', '書類確認', '照合', '分析準備'],
            quoteLabel: '今日の Quote',
            quote: '成功は一日だけの努力からではなく<br />小さなことを積み重ねることから生まれます',
            quoteBy: '- PEARNLY Daily Inspiration',
            loginTab: 'ログイン',
            signupTab: '登録',
            loginTitle: 'おかえりなさい 👋',
            loginSub: 'ログインして作業を続けましょう',
            signupTitle: 'Pearnly を始める',
            signupSub: 'アカウントを作成し、メールを確認してください',
            username: 'ユーザー名',
            usernamePh: 'ユーザー名を入力',
            password: 'パスワード',
            passwordPh: 'パスワードを入力',
            remember: 'ログイン状態を保存',
            forgot: 'パスワードを忘れた ?',
            loginBtn: 'ログイン',
            or: 'または',
            google: 'Google でログイン',
            lineLogin: 'LINE でログイン',
            loginLegal:
                'ログインすると <a href="/terms" target="_blank" rel="noopener">利用規約</a> と <a href="/privacy" target="_blank" rel="noopener">プライバシー</a> に同意したものとします',
            email: 'メール',
            emailPh: 'hello@company.com',
            code: '確認コード',
            codePh: 'コードを入力',
            sendCode: 'コード送信',
            signupPassword: 'パスワード',
            signupPasswordPh: '8文字以上',
            confirmPassword: 'パスワード確認',
            confirmPasswordPh: 'もう一度入力',
            agree: '<a href="/terms" target="_blank" rel="noopener">利用規約</a> と <a href="/privacy" target="_blank" rel="noopener">プライバシー</a> に同意します',
            newsletter: '製品アップデートとヒントを受け取る',
            create: 'アカウント作成',
            supportTitle: 'お困りですか ?',
            supportSub: '下記から PEARNLY チームへお問い合わせください',
            secure1: 'すべてのデータを安全に',
            secure1Sub: '国際レベルの安全基準',
            secure2: 'いつでもどこでも',
            secure2Sub: 'すべての端末で利用可能',
            secure3: 'データは安全です',
            secure3Sub: '第三者へ開示しません',
            forgotTitle: 'パスワード再設定',
            forgotText: '登録メールを入力してください。再設定リンクを送信します。',
            cancel: 'キャンセル',
            sendLink: '送信',
        },
    };

    // 运行时反馈消息(校验/接口) · 按当前语言显示 · 经 window.PearnlyMsg(key) 取用
    const msg = {
        zh: {
            enterCred: '请输入用户名和密码',
            accountLocked: '账号已被临时锁定',
            wrongCred: '用户名或密码错误',
            loginSuccess: '登录成功',
            loggingIn: '正在登录...',
            netError: '网络异常，请重试',
            invalidEmail: '请输入正确的邮箱',
            emailRegistered: '该邮箱已注册',
            resendTooFast: '请稍候再重新发送',
            hourlyLimit: '发送过于频繁，请稍后再试',
            disposableEmail: '不支持临时邮箱',
            sendFail: '邮件发送失败，请重试',
            codeSent: '验证码已发送',
            sending: '正在发送...',
            weakPassword: '密码需至少 8 位，且包含字母和数字',
            pwMismatch: '两次输入的密码不一致',
            enterCode: '请输入验证码',
            agreeRequired: '请同意服务条款和隐私政策',
            codeInvalid: '验证码不正确',
            codeExpired: '验证码已过期',
            passwordTooWeak: '密码强度不足',
            signupFail: '注册失败，请重试',
            signupSuccess: '创建账号成功',
            creatingAccount: '正在创建账号...',
            forgotSent: '如果该邮箱已注册，我们会发送重置链接',
            forgotSending: '正在发送...',
            resend: '重新发送',
            sendCode: '发送验证码',
            sayFace: '喵~',
            sayPaw: '击掌!',
            sayBell: '叮铃 ♪',
            sayLaptop: '工作中…',
            sayMug: '☕',
            sayBubble: '你好呀',
            sayPlant: '🌱',
            sayCheck: '完成!',
        },
        th: {
            enterCred: 'กรุณากรอกชื่อผู้ใช้งานและรหัสผ่าน',
            accountLocked: 'บัญชีถูกล็อกชั่วคราว',
            wrongCred: 'ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง',
            loginSuccess: 'เข้าสู่ระบบสำเร็จ',
            loggingIn: 'กำลังเข้าสู่ระบบ...',
            netError: 'เครือข่ายขัดข้อง กรุณาลองใหม่',
            invalidEmail: 'กรุณากรอกอีเมลให้ถูกต้อง',
            emailRegistered: 'อีเมลนี้ลงทะเบียนแล้ว',
            resendTooFast: 'กรุณารอสักครู่ก่อนส่งใหม่',
            hourlyLimit: 'ส่งรหัสบ่อยเกินไป กรุณาลองใหม่ภายหลัง',
            disposableEmail: 'ไม่รองรับอีเมลชั่วคราว',
            sendFail: 'ส่งอีเมลไม่สำเร็จ กรุณาลองใหม่',
            codeSent: 'ส่งรหัสยืนยันแล้ว',
            sending: 'กำลังส่ง...',
            weakPassword: 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษรและมีทั้งตัวอักษรกับตัวเลข',
            pwMismatch: 'รหัสผ่านทั้งสองช่องไม่ตรงกัน',
            enterCode: 'กรุณากรอกรหัสยืนยัน',
            agreeRequired: 'กรุณายอมรับบริการและความเป็นส่วนตัว',
            codeInvalid: 'รหัสยืนยันไม่ถูกต้อง',
            codeExpired: 'รหัสยืนยันหมดอายุ',
            passwordTooWeak: 'รหัสผ่านยังไม่ปลอดภัยพอ',
            signupFail: 'สมัครใช้งานไม่สำเร็จ กรุณาลองใหม่',
            signupSuccess: 'สร้างบัญชีสำเร็จ',
            creatingAccount: 'กำลังสร้างบัญชี...',
            forgotSent: 'หากอีเมลนี้มีอยู่ในระบบ เราจะส่งลิงก์รีเซ็ตให้',
            forgotSending: 'กำลังส่ง...',
            resend: 'ส่งใหม่',
            sendCode: 'ส่งรหัส',
            sayFace: 'เหมียว~',
            sayPaw: 'ไฮไฟว์!',
            sayBell: 'กริ๊ง ♪',
            sayLaptop: 'พิมพ์งาน…',
            sayMug: '☕',
            sayBubble: 'สวัสดีครับ',
            sayPlant: '🌱',
            sayCheck: 'เสร็จงาน!',
        },
        en: {
            enterCred: 'Please enter username and password',
            accountLocked: 'Account temporarily locked',
            wrongCred: 'Incorrect username or password',
            loginSuccess: 'Login successful',
            loggingIn: 'Logging in...',
            netError: 'Network error, please try again',
            invalidEmail: 'Please enter a valid email',
            emailRegistered: 'This email is already registered',
            resendTooFast: 'Please wait before resending',
            hourlyLimit: 'Too many requests, try again later',
            disposableEmail: 'Disposable email not allowed',
            sendFail: 'Failed to send email, try again',
            codeSent: 'Verification code sent',
            sending: 'Sending...',
            weakPassword: 'Password must be 8+ characters with letters and numbers',
            pwMismatch: 'Passwords do not match',
            enterCode: 'Please enter the verification code',
            agreeRequired: 'Please accept the Terms and Privacy Policy',
            codeInvalid: 'Invalid verification code',
            codeExpired: 'Verification code expired',
            passwordTooWeak: 'Password too weak',
            signupFail: 'Sign up failed, please try again',
            signupSuccess: 'Account created',
            creatingAccount: 'Creating account...',
            forgotSent: "If this email exists, we'll send a reset link",
            forgotSending: 'Sending...',
            resend: 'Resend',
            sendCode: 'Send code',
            sayFace: 'Meow~',
            sayPaw: 'High five!',
            sayBell: 'Ding ♪',
            sayLaptop: 'Typing…',
            sayMug: '☕',
            sayBubble: 'Hi there',
            sayPlant: '🌱',
            sayCheck: 'Done!',
        },
        ja: {
            enterCred: 'ユーザー名とパスワードを入力してください',
            accountLocked: 'アカウントが一時的にロックされています',
            wrongCred: 'ユーザー名またはパスワードが正しくありません',
            loginSuccess: 'ログインしました',
            loggingIn: 'ログイン中...',
            netError: 'ネットワークエラー、もう一度お試しください',
            invalidEmail: '正しいメールを入力してください',
            emailRegistered: 'このメールは登録済みです',
            resendTooFast: '少し待ってから再送信してください',
            hourlyLimit: '送信が多すぎます。後でお試しください',
            disposableEmail: '使い捨てメールは使用できません',
            sendFail: 'メール送信に失敗しました',
            codeSent: '確認コードを送信しました',
            sending: '送信中...',
            weakPassword: 'パスワードは8文字以上で英字と数字を含めてください',
            pwMismatch: 'パスワードが一致しません',
            enterCode: '確認コードを入力してください',
            agreeRequired: '利用規約とプライバシーに同意してください',
            codeInvalid: '確認コードが正しくありません',
            codeExpired: '確認コードの有効期限が切れています',
            passwordTooWeak: 'パスワードが弱すぎます',
            signupFail: '登録に失敗しました',
            signupSuccess: 'アカウントを作成しました',
            creatingAccount: 'アカウント作成中...',
            forgotSent: '登録済みのメールであればリセットリンクを送信します',
            forgotSending: '送信中...',
            resend: '再送信',
            sendCode: 'コード送信',
            sayFace: 'ニャー~',
            sayPaw: 'ハイタッチ!',
            sayBell: 'チリン ♪',
            sayLaptop: '作業中…',
            sayMug: '☕',
            sayBubble: 'こんにちは',
            sayPlant: '🌱',
            sayCheck: '完了!',
        },
    };

    window.PearnlyMsg = (key) => {
        const lang = window.PearnlyCurrentLang || localStorage.getItem('mrpilot_lang') || 'th';
        return (msg[lang] || msg.th)[key] || '';
    };

    function setText(selector, value) {
        const el = document.querySelector(selector);
        if (el) el.textContent = value;
    }

    function setHtml(selector, value) {
        const el = document.querySelector(selector);
        if (el) el.innerHTML = value;
    }

    function setPlaceholder(selector, value) {
        const el = document.querySelector(selector);
        if (el) el.placeholder = value;
    }

    function applyLanguage(lang) {
        const c = copy[lang] || copy.th;
        window.PearnlyCurrentLang = lang;
        document.documentElement.lang = lang;
        localStorage.setItem('mrpilot_lang', lang);
        document.querySelectorAll('.language-switcher button').forEach((btn) => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });
        setText('.welcome-copy h1', c.welcomeTitle);
        setText('.welcome-copy p', c.welcomeSub);
        setHtml('.work-bubble p', c.bubble);
        document.querySelectorAll('.check-row span:last-child').forEach((el, i) => {
            el.textContent = c.checklist[i] || '';
        });
        setText('.quote-card header span:last-child', c.quoteLabel);
        setHtml('.quote-card blockquote', c.quote);
        setText('.quote-card footer', c.quoteBy);
        setText(".mode-btn[data-mode='login']", c.loginTab);
        setText(".mode-btn[data-mode='signup']", c.signupTab);
        const signup = document.getElementById('form-signup').classList.contains('active');
        setText('#auth-title', signup ? c.signupTitle : c.loginTitle);
        setText('#auth-subtitle', signup ? c.signupSub : c.loginSub);
        setText("label[for='li-username']", c.username);
        setPlaceholder('#li-username', c.usernamePh);
        setText("label[for='li-password']", c.password);
        setPlaceholder('#li-password', c.passwordPh);
        setText('.form-split .checkline span', c.remember);
        setText('#forgot-btn', c.forgot);
        setText('#btn-login', c.loginBtn);
        setText('.divider span', c.or);
        setHtml("[data-sso='google']", `<span class="google-mark">G</span> ${c.google}`);
        setHtml("[data-sso='line']", `<span class="line-logo">LINE</span> ${c.lineLogin}`);
        setHtml('#form-login .legal-line', c.loginLegal);
        setText("label[for='su-email']", c.email);
        setPlaceholder('#su-email', c.emailPh);
        setText("label[for='su-code']", c.code);
        setPlaceholder('#su-code', c.codePh);
        setText('#btn-send-code', c.sendCode);
        setText("label[for='su-password']", c.signupPassword);
        setPlaceholder('#su-password', c.signupPasswordPh);
        setText("label[for='su-password-confirm']", c.confirmPassword);
        setPlaceholder('#su-password-confirm', c.confirmPasswordPh);
        setHtml('.register-options .checkline:first-child span', c.agree);
        setText('.register-options .checkline:last-child span', c.newsletter);
        setText('#btn-step1', c.create);
        setText('.support-head strong', c.supportTitle);
        setText('.support-head span', c.supportSub);
        document.querySelectorAll('.security-item strong').forEach((el, i) => {
            el.textContent = [c.secure1, c.secure2, c.secure3][i];
        });
        document.querySelectorAll('.security-item div span').forEach((el, i) => {
            el.textContent = [c.secure1Sub, c.secure2Sub, c.secure3Sub][i];
        });
        // 手机端专属:底部登录按钮 + 安全三件短词(桌面端长文案 secure* 不动)
        setText('#m-login-cta', `${c.loginTab} / ${c.signupTab}`);
        const mSecShort = {
            zh: ['安全保障', '随时访问', '数据安全'],
            th: ['ปลอดภัย', 'เข้าถึงทุกที่', 'ข้อมูลปลอดภัย'],
            en: ['Secure', 'Anywhere', 'Private'],
            ja: ['安全', 'どこでも', 'データ保護'],
        }[lang] || ['ปลอดภัย', 'เข้าถึงทุกที่', 'ข้อมูลปลอดภัย'];
        document.querySelectorAll('.m-sec-item b').forEach((el, i) => {
            el.textContent = mSecShort[i] || '';
        });
        setText('#forgot-title', c.forgotTitle);
        setText('.forgot-modal p', c.forgotText);
        setPlaceholder('#forgot-email', c.emailPh);
        setText('#forgot-close', c.cancel);
        setText('#forgot-submit', c.sendLink);
    }

    function mountSwitcher() {
        const card = document.querySelector('.auth-card');
        if (!card || document.querySelector('.language-switcher')) return;
        const switcher = document.createElement('div');
        switcher.className = 'language-switcher';
        switcher.setAttribute('aria-label', 'Language');
        switcher.innerHTML = langs
            .map((lang) => `<button type="button" data-lang="${lang}">${labels[lang]}</button>`)
            .join('');
        switcher.addEventListener('click', (event) => {
            const button = event.target.closest('button[data-lang]');
            if (button) applyLanguage(button.dataset.lang);
        });
        card.insertBefore(switcher, card.firstChild);
    }

    window.PearnlyApplyLanguage = () =>
        applyLanguage(window.PearnlyCurrentLang || localStorage.getItem('mrpilot_lang') || 'th');
    mountSwitcher();
    window.PearnlyApplyLanguage();
})();
