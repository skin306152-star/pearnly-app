/* global liff */
(() => {
    'use strict';
    const $ = (id) => document.getElementById(id);
    const labels = {
        attention: 'รอดำเนินการ',
        all: 'ทั้งหมด',
        review: 'รอตรวจรับ',
        blocked: 'ติดปัญหา',
        doing: 'กำลังทำ',
        pending: 'ยังไม่เริ่ม',
        done: 'เสร็จแล้ว',
    };
    let token = '',
        expires = 0,
        current = null,
        version = '',
        filter = 'all',
        timer,
        busy = false,
        lastSync = 0,
        generation = 0,
        failures = 0;
    const fingerprints = new Map();
    function el(tag, text, cls) {
        const node = document.createElement(tag);
        node.textContent = text;
        if (cls) node.className = cls;
        return node;
    }
    async function post(path, body) {
        const response = await fetch('/api/cowork-line/work-live/' + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            cache: 'no-store',
            signal: AbortSignal.timeout(30000),
        });
        const data = await response.json();
        if (!response.ok) {
            const error = new Error('request_failed');
            error.status = response.status;
            throw error;
        }
        return data;
    }
    function match(task, key) {
        return (
            key === 'all' ||
            (key === 'attention'
                ? task.overdue || ['blocked', 'review'].includes(task.status)
                : task.status === key)
        );
    }
    function render() {
        if (!current) return;
        const tasks = current.tasks;
        $('workspace').hidden = false;
        $('title').textContent = current.role === 'owner' ? 'ภาพรวมงานทีม' : 'งานของฉัน';
        const active = tasks.filter((t) => t.status !== 'cancelled');
        const done = active.filter((t) => t.status === 'done').length;
        $('completed').textContent = current.mapping_ready ? done + ' / ' + active.length : '—';
        $('progress').hidden = !current.mapping_ready;
        $('progress').value = active.length ? Math.round((done * 100) / active.length) : 0;
        const selected = $('board').value;
        if (JSON.stringify(current.boards) !== $('board').dataset.catalog) {
            $('board').replaceChildren(
                ...current.boards.map((b) => {
                    const o = el('option', b.title);
                    o.value = b._id;
                    return o;
                })
            );
            $('board').dataset.catalog = JSON.stringify(current.boards);
        }
        $('board').value = current.board || selected;
        $('board').disabled = !current.boards.length;
        $('filters').replaceChildren(
            ...Object.entries(labels).map(([key, label]) => {
                const b = el('button', label + ' ' + tasks.filter((t) => match(t, key)).length);
                b.type = 'button';
                b.setAttribute('aria-pressed', String(key === filter));
                b.onclick = () => {
                    filter = key;
                    render();
                };
                return b;
            })
        );
        const open = new Set(
            [...$('tasks').querySelectorAll('details[open]')].map((n) => n.dataset.id)
        );
        const query = $('search').value.trim().toLocaleLowerCase();
        const selectedTasks = tasks.filter(
            (t) =>
                match(t, filter) &&
                (t.title + ' ' + t.assignees.join(' ')).toLocaleLowerCase().includes(query)
        );
        const priority = (t) =>
            t.overdue
                ? 0
                : ({ review: 1, blocked: 2, doing: 3, pending: 4, done: 6, cancelled: 7 }[
                      t.status
                  ] ?? 5);
        selectedTasks.sort((a, b) => priority(a) - priority(b));
        $('empty').hidden = selectedTasks.length > 0;
        $('tasks').replaceChildren(
            ...selectedTasks.map((t) => {
                const node = document.createElement('details');
                node.dataset.id = t.id;
                node.dataset.state = t.status;
                node.open = open.has(t.id);
                const value = JSON.stringify(t);
                if (fingerprints.has(t.id) && fingerprints.get(t.id) !== value)
                    node.classList.add('updated');
                fingerprints.set(t.id, value);
                const summary = document.createElement('summary'),
                    heading = el('div', '', 'task-heading');
                heading.append(el('h2', t.title), el('span', t.status_label, 'badge'));
                summary.append(
                    heading,
                    el(
                        'p',
                        (t.assignees.join(', ') || 'ยังไม่ระบุผู้รับผิดชอบ') +
                            ' · ' +
                            t.due +
                            (t.overdue ? ' · เกินกำหนด' : ''),
                        'meta'
                    )
                );
                const body = el('div', '', 'body');
                body.append(el('p', t.description || 'ยังไม่มีรายละเอียด'));
                if (t.latest_comment)
                    body.append(el('strong', 'ความคืบหน้าล่าสุด'), el('p', t.latest_comment));
                node.append(summary, body);
                return node;
            })
        );
    }
    async function sync() {
        clearTimeout(timer);
        if (busy || document.hidden) return;
        busy = true;
        const requestGeneration = generation;
        try {
            if (!token || Date.now() > expires) {
                const session = await post('auth', { id_token: liff.getIDToken() });
                token = session.token;
                expires = Date.now() + (session.expires_in - 60) * 1000;
            }
            const data = await post('read', { token, board: $('board').value });
            if (requestGeneration !== generation) return;
            if (data.version !== version) {
                current = data;
                version = data.version;
                render();
            }
            lastSync = Date.now();
            failures = 0;
            $('connection').dataset.state = 'online';
            $('connection').textContent =
                'อัปเดตอัตโนมัติ · ล่าสุด ' +
                new Date(lastSync).toLocaleTimeString('th-TH', {
                    timeZone: 'Asia/Bangkok',
                    hour12: false,
                });
            $('error').hidden = true;
            $('retry').hidden = true;
        } catch (error) {
            failures++;
            if ([401, 403].includes(error.status)) {
                token = '';
                expires = 0;
                current = null;
                version = '';
                $('workspace').hidden = true;
                $('tasks').replaceChildren();
                if (error.status === 403) $('board').replaceChildren();
            }
            $('connection').dataset.state = 'offline';
            $('connection').textContent = lastSync
                ? 'การเชื่อมต่อขัดข้อง · ข้อมูลล่าสุด ' +
                  new Date(lastSync).toLocaleTimeString('th-TH', {
                      timeZone: 'Asia/Bangkok',
                      hour12: false,
                  })
                : 'ยังเชื่อมต่อไม่ได้';
            $('error').textContent = [401, 403].includes(error.status)
                ? 'กรุณาเปิดจาก LINE และตรวจสอบว่าบัญชีเชื่อมต่อกับทีมแล้วครับ'
                : 'ข้อมูลอาจยังไม่เป็นปัจจุบัน ระบบจะลองเชื่อมต่อใหม่ครับ';
            $('error').hidden = false;
            $('retry').hidden = false;
        } finally {
            busy = false;
            if (!document.hidden)
                timer = setTimeout(
                    sync,
                    requestGeneration !== generation
                        ? 0
                        : Math.min(30000, 5000 * Math.max(1, failures))
                );
        }
    }
    $('board').onchange = () => {
        generation++;
        current = null;
        version = '';
        $('filters').replaceChildren();
        $('completed').textContent = '…';
        $('tasks').replaceChildren();
        $('connection').textContent = 'กำลังโหลดบอร์ด…';
        sync();
    };
    $('search').oninput = render;
    $('retry').onclick = sync;
    $('close').onclick = () => {
        if (liff.isInClient?.()) liff.closeWindow();
        else history.back();
    };
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) clearTimeout(timer);
        else sync();
    });
    window.addEventListener('offline', () => {
        $('connection').dataset.state = 'offline';
        $('connection').textContent = 'ออฟไลน์ · ข้อมูลอาจยังไม่เป็นปัจจุบัน';
    });
    window.addEventListener('online', sync);
    async function start() {
        try {
            const response = await fetch('/api/cowork-line/intake/liff/config', {
                cache: 'no-store',
            });
            const config = await response.json();
            await liff.init({ liffId: config.data?.liff_id });
            if (!liff.isLoggedIn()) {
                liff.login();
                return;
            }
            const board = new URLSearchParams(location.search).get('board');
            if (board) {
                const option = el('option', 'กำลังโหลด…');
                option.value = board;
                $('board').append(option);
            }
            await sync();
        } catch {
            $('connection').textContent = 'เปิดหน้านี้จากเมนูงานใน LINE เพื่อเชื่อมต่อครับ';
            $('retry').hidden = false;
            $('retry').onclick = () => location.reload();
        }
    }
    start();
})();
