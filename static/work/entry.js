/* Same-origin handoff page. The Pearnly access token never leaves this origin. */
(() => {
    'use strict';
    const copy = {
        th: [
            'การทำงานร่วมกัน',
            'กำลังเปิดพื้นที่ทำงาน…',
            'กลับไปที่ COWORK',
            'ลองอีกครั้ง',
            'กรุณาเข้าสู่ระบบ COWORK ก่อน',
            'ยังเปิดพื้นที่ทำงานไม่ได้ กรุณาลองอีกครั้ง',
        ],
        en: [
            'Work collaboration',
            'Opening your workspace…',
            'Back to COWORK',
            'Try again',
            'Please sign in to COWORK first.',
            'Unable to open your workspace. Please try again.',
        ],
        zh: [
            '工作协作',
            '正在进入工作协作…',
            '返回 COWORK',
            '重试',
            '请先登录 COWORK。',
            '暂时无法进入工作协作，请重试。',
        ],
        ja: [
            '共同作業',
            'ワークスペースを開いています…',
            'COWORK に戻る',
            '再試行',
            '先に COWORK にログインしてください。',
            'ワークスペースを開けません。もう一度お試しください。',
        ],
    };
    const lang = localStorage.getItem('mrpilot_lang') || 'th';
    const strings = copy[lang] || copy.th;
    document.documentElement.lang = copy[lang] ? lang : 'th';
    const status = document.getElementById('work-status');
    const retry = document.getElementById('work-retry');
    const params = new URLSearchParams(location.search);
    const entry = params.get('entry') === 'main' ? 'main' : 'cowork';
    const workPath = '/work?entry=' + entry;
    document.getElementById('work-back').href = entry === 'main' ? '/home' : '/cowork';
    document.getElementById('work-title').textContent = strings[0];
    status.textContent = strings[1];
    document.getElementById('work-back').textContent = strings[2];
    retry.textContent = strings[3];
    retry.addEventListener('click', () => location.replace(workPath));

    async function run() {
        const token = localStorage.getItem(
            entry === 'main' ? 'mrpilot_token' : 'mrpilot_token_cowork'
        );
        if (!token) {
            status.textContent = strings[4];
            return;
        }
        const state = params.get('state');
        history.replaceState(null, '', workPath);
        const handoff = /^[A-Za-z0-9_-]{43}$/.test(state || '');
        const response = await fetch(handoff ? '/api/work/tickets' : '/api/work/entry', {
            method: handoff ? 'POST' : 'GET',
            headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
            ...(handoff ? { body: JSON.stringify({ state }) } : {}),
        });
        if (response.status === 401 || response.status === 403) {
            status.textContent = strings[4];
            return;
        }
        if (!response.ok) throw new Error('work unavailable');
        const data = await response.json();
        if (!handoff) {
            location.replace(data.url + '?entry=' + entry);
            return;
        }
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = data.consume_url;
        for (const [name, value] of Object.entries({ ticket: data.ticket, state })) {
            const field = document.createElement('input');
            field.type = 'hidden';
            field.name = name;
            field.value = value;
            form.append(field);
        }
        document.body.append(form);
        form.submit();
        // A browser can block navigation without rejecting the preceding fetch.
        setTimeout(() => {
            status.textContent = strings[5];
            retry.hidden = false;
        }, 10000);
    }
    run().catch(() => {
        status.textContent = strings[5];
        retry.hidden = false;
    });
})();
