/*
 * Pearnly POS 餐厅业态 · pos-restaurant.js · 业态分流 + 屏1 桌台总览 + 屏2 点单
 * 业态=restaurant 时 /pos 登录开班后进桌台流(零售/药房仍走 pos-cashier 主屏)。数据走 /api/pos/restaurant/*
 * (POS.apiFetch 信封),失败统一 posErrMsg。视觉照搬概念稿 01/02。屏3 厨房 + 屏4 埋单在 pos-restaurant-ops.js。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const $ = (id) => document.getElementById(id);
    const fmt = POS.fmt;

    const R = (POS.restaurant = POS.restaurant || {});
    const ws = () => state.workspaceClientId;

    // ── 餐厅数据(信封 · 无 mock · 真后端)──
    const RD = (R.data = {
        tables: (areaId) =>
            POS.apiFetch(
                'GET',
                '/api/pos/restaurant/tables?workspace_client_id=' +
                    ws() +
                    (areaId ? '&area_id=' + areaId : '')
            ),
        openTable: (tableId, party) =>
            POS.apiFetch('POST', '/api/pos/restaurant/tables/' + tableId + '/open', {
                workspace_client_id: ws(),
                party_size: party,
            }),
        session: (sid) =>
            POS.apiFetch(
                'GET',
                '/api/pos/restaurant/sessions/' + sid + '?workspace_client_id=' + ws()
            ),
        addLines: (sid, lines) =>
            POS.apiFetch('POST', '/api/pos/restaurant/sessions/' + sid + '/lines', {
                workspace_client_id: ws(),
                lines,
            }),
        updateLine: (sid, lid, body) =>
            POS.apiFetch(
                'PATCH',
                '/api/pos/restaurant/sessions/' + sid + '/lines/' + lid,
                Object.assign({ workspace_client_id: ws() }, body)
            ),
        deleteLine: (sid, lid) =>
            POS.apiFetch(
                'DELETE',
                '/api/pos/restaurant/sessions/' +
                    sid +
                    '/lines/' +
                    lid +
                    '?workspace_client_id=' +
                    ws()
            ),
        sendKitchen: (sid) =>
            POS.apiFetch('POST', '/api/pos/restaurant/sessions/' + sid + '/send-kitchen', {
                workspace_client_id: ws(),
            }),
    });

    // ── 业态分流 ──
    R.ensureBusinessType = async function () {
        if (state.businessType == null) {
            try {
                const b = await POS.data.bootstrap();
                const cfg = (b.modules && b.modules.pos && b.modules.pos.config) || {};
                state.businessType = cfg.business_type || 'retail';
            } catch (_) {
                state.businessType = 'retail';
            }
        }
        return state.businessType === 'restaurant';
    };
    R.enter = function () {
        POS.showView('rtables');
        renderTables();
    };

    // ════════════════ 屏 1 · 桌台总览 ════════════════
    let activeZone = null;

    function stLabel(s) {
        return POS.t('posui.rest.st.' + s);
    }

    async function renderTables() {
        const grid = $('rt-grid');
        if (!grid) return;
        grid.innerHTML = '<div class="rstate">' + POS.t('posui.loading') + '</div>';
        let data;
        try {
            data = await RD.tables(activeZone);
        } catch (e) {
            grid.innerHTML =
                '<div class="rstate">' + POS.posErrMsg(e.code, 'pos.unexpected') + '</div>';
            return;
        }
        renderZones(data.areas || []);
        const tables = data.tables || [];
        if (!tables.length) {
            grid.innerHTML = '<div class="rstate">' + POS.t('posui.rest.tables.empty') + '</div>';
            return;
        }
        grid.innerHTML = tables.map(tableCard).join('');
        grid.querySelectorAll('.t').forEach((el) => {
            el.addEventListener('click', () =>
                onTableTap(tables.find((t) => String(t.id) === el.dataset.tid))
            );
        });
    }

    function renderZones(areas) {
        const box = $('rt-zones');
        if (!box) return;
        const all =
            '<div class="zone' +
            (activeZone === null ? ' on' : '') +
            '" data-zone="">' +
            POS.t('posui.rest.zone.all') +
            '</div>';
        box.innerHTML =
            all +
            areas
                .map(
                    (a) =>
                        '<div class="zone' +
                        (activeZone === a.id ? ' on' : '') +
                        '" data-zone="' +
                        a.id +
                        '">' +
                        (a.name || '') +
                        '</div>'
                )
                .join('');
        box.querySelectorAll('.zone').forEach((el) => {
            el.addEventListener('click', () => {
                activeZone = el.dataset.zone ? Number(el.dataset.zone) : null;
                renderTables();
            });
        });
    }

    function tableCard(t) {
        const peopleIcon =
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>';
        if (t.status === 'free') {
            return (
                '<div class="t free" data-tid="' +
                t.id +
                '"><div class="no">' +
                t.name +
                '<span class="st">' +
                stLabel('free') +
                '</span></div><div class="cap">' +
                POS.t('posui.rest.tap.open') +
                '</div><div class="mid"></div>' +
                '<div class="ft"><span class="amt">—</span><span></span></div></div>'
            );
        }
        return (
            '<div class="t ' +
            t.status +
            '" data-tid="' +
            t.id +
            '"><div class="no">' +
            t.name +
            '<span class="st">' +
            stLabel(t.status) +
            '</span></div><div class="cap">' +
            peopleIcon +
            (t.party_size || 0) +
            ' ' +
            POS.t('posui.rest.seats') +
            '</div><div class="mid"></div>' +
            '<div class="ft"><span class="amt tnum">฿' +
            fmt(t.amount) +
            '</span>' +
            '<span class="time">' +
            (t.minutes || 0) +
            ' ' +
            POS.t('posui.rest.min') +
            '</span></div></div>'
        );
    }

    function onTableTap(t) {
        if (!t) return;
        if (t.status === 'free') openTableModal(t);
        else enterOrder(t.session_id);
    }

    // ── 开台弹窗 ──
    let openTarget = null;
    let openParty = 2;
    function openTableModal(t) {
        openTarget = t;
        openParty = Math.min(t.seats || 2, 2) || 2;
        $('rt-open-sub').textContent = POS.t('posui.rest.open.sub').replace('{t}', t.name);
        renderPartyButtons(t.seats || 8);
        $('rt-open-mask').classList.add('show');
    }
    function renderPartyButtons(maxSeats) {
        const n = Math.max(8, maxSeats);
        const box = $('rt-open-ppl');
        box.innerHTML = Array.from({ length: n }, (_, i) => i + 1)
            .map(
                (v) =>
                    '<button data-ppl="' +
                    v +
                    '"' +
                    (v === openParty ? ' class="on"' : '') +
                    '>' +
                    v +
                    '</button>'
            )
            .join('');
        box.querySelectorAll('button').forEach((b) => {
            b.addEventListener('click', () => {
                openParty = Number(b.dataset.ppl);
                box.querySelectorAll('button').forEach((x) => x.classList.remove('on'));
                b.classList.add('on');
            });
        });
    }
    async function confirmOpen() {
        if (!openTarget) return;
        const btn = $('rt-open-go');
        btn.disabled = true;
        try {
            const r = await RD.openTable(openTarget.id, openParty);
            $('rt-open-mask').classList.remove('show');
            enterOrder(r.session.id);
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        } finally {
            btn.disabled = false;
        }
    }

    // ════════════════ 屏 2 · 点单 ════════════════
    let curSession = null;
    let dishes = [];
    let activeCat = null;

    R.curSession = () => curSession;
    R.reloadOrder = () => loadOrder(curSession.session.id);

    async function enterOrder(sessionId) {
        POS.showView('rorder');
        $('ro-dishes').innerHTML = '';
        await loadOrder(sessionId);
        loadDishes();
    }

    async function loadOrder(sessionId) {
        try {
            curSession = await RD.session(sessionId);
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
            POS.showView('rtables');
            renderTables();
            return;
        }
        renderHeader();
        renderPanel();
    }

    function renderHeader() {
        const s = curSession.session;
        $('ro-title').textContent = s.table_name;
        $('ro-meta').textContent =
            '· ' +
            (s.party_size || 0) +
            ' ' +
            POS.t('posui.rest.seats') +
            ' · ' +
            (s.minutes || 0) +
            ' ' +
            POS.t('posui.rest.min');
    }

    async function loadDishes() {
        try {
            dishes = await POS.data.products('', activeCat);
        } catch (e) {
            $('ro-dishes').innerHTML =
                '<div class="empty">' + POS.posErrMsg(e.code, 'pos.unexpected') + '</div>';
            return;
        }
        dishes.forEach((p) => (POS.nameCache[p.id] = p.name));
        if (!dishes.length) {
            $('ro-dishes').innerHTML =
                '<div class="empty">' + POS.t('posui.rest.menu.empty') + '</div>';
            return;
        }
        $('ro-dishes').innerHTML = dishes.map(dishCard).join('');
        $('ro-dishes')
            .querySelectorAll('.dish')
            .forEach((el) =>
                el.addEventListener('click', () =>
                    addDish(dishes.find((d) => d.id === el.dataset.pid))
                )
            );
    }

    function dishPrice(p) {
        const u = (p.units || []).find((x) => x.default_sell) ||
            (p.units || [])[0] || { price: '0' };
        return Number(u.price || 0);
    }
    function dishCard(p) {
        return (
            '<div class="dish" data-pid="' +
            p.id +
            '"><div class="img"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 11h18M5 11a7 7 0 0 1 14 0M12 3v2M2 21h20"/></svg></div>' +
            '<div class="m"><div class="n">' +
            POS.nm(p.name) +
            '</div><div class="p tnum">฿' +
            fmt(dishPrice(p)) +
            '</div></div></div>'
        );
    }

    // 同品无备注的草稿行合并加量;否则追加新草稿行。
    async function addDish(p) {
        if (!p) return;
        const existing = (curSession.draft_lines || []).find(
            (l) => l.product_id === p.id && !l.note
        );
        try {
            if (existing) {
                const r = await RD.updateLine(curSession.session.id, existing.id, {
                    qty: Number(existing.qty) + 1,
                });
                curSession.draft_lines = r.draft_lines;
            } else {
                const r = await RD.addLines(curSession.session.id, [{ product_id: p.id, qty: 1 }]);
                curSession.draft_lines = r.draft_lines;
            }
            renderPanel();
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        }
    }

    async function stepDraft(lid, delta) {
        const l = (curSession.draft_lines || []).find((x) => x.id === lid);
        if (!l) return;
        const q = Number(l.qty) + delta;
        try {
            const r =
                q <= 0
                    ? await RD.deleteLine(curSession.session.id, lid)
                    : await RD.updateLine(curSession.session.id, lid, { qty: q });
            curSession.draft_lines = r.draft_lines;
            renderPanel();
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        }
    }

    async function editNote(lid) {
        const l = (curSession.draft_lines || []).find((x) => x.id === lid);
        if (!l) return;
        const v = window.prompt(POS.t('posui.rest.note.prompt'), l.note || '');
        if (v === null) return;
        try {
            const r = await RD.updateLine(curSession.session.id, lid, { note: v });
            curSession.draft_lines = r.draft_lines;
            renderPanel();
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        }
    }

    function renderPanel() {
        const sent = curSession.sent_lines || [];
        const draft = curSession.draft_lines || [];
        $('ro-sub').textContent = POS.t('posui.rest.panel.counts')
            .replace('{s}', sent.length)
            .replace('{d}', draft.length);
        const sentHtml = sent
            .map(
                (l) =>
                    '<div class="ln sent"><div class="top1"><span class="nm" data-sent="' +
                    POS.t('posui.rest.ordered') +
                    '">' +
                    POS.nm(l.name) +
                    (Number(l.qty) > 1 ? ' ×' + Number(l.qty) : '') +
                    (l.note ? ' · ' + l.note : '') +
                    '</span><span class="amt tnum">฿' +
                    fmt(l.line_total) +
                    '</span></div></div>'
            )
            .join('');
        const draftHtml = draft
            .map(
                (l) =>
                    '<div class="ln"><div class="top1"><span class="nm">' +
                    POS.nm(l.name) +
                    '</span><div class="stp"><button data-dec="' +
                    l.id +
                    '">−</button><span class="q">' +
                    Number(l.qty) +
                    '</span><button data-inc="' +
                    l.id +
                    '">+</button></div>' +
                    '<span class="amt tnum">฿' +
                    fmt(l.line_total) +
                    '</span></div>' +
                    '<div class="opt" data-note="' +
                    l.id +
                    '">' +
                    (l.note ? '· ' + l.note : '+ ' + POS.t('posui.rest.note.add')) +
                    '</div></div>'
            )
            .join('');
        const lines = $('ro-lines');
        lines.innerHTML =
            sentHtml + draftHtml ||
            '<div class="empty">' + POS.t('posui.rest.panel.empty') + '</div>';
        lines
            .querySelectorAll('[data-dec]')
            .forEach((b) => (b.onclick = () => stepDraft(b.dataset.dec, -1)));
        lines
            .querySelectorAll('[data-inc]')
            .forEach((b) => (b.onclick = () => stepDraft(b.dataset.inc, 1)));
        lines
            .querySelectorAll('[data-note]')
            .forEach((b) => (b.onclick = () => editNote(b.dataset.note)));

        const orderedSub = sum(sent);
        const draftSub = sum(draft);
        $('ro-ordered').textContent = fmt(orderedSub);
        $('ro-draft').textContent = fmt(draftSub);
        $('ro-grand').textContent = fmt(orderedSub + draftSub);
        const sendBtn = $('ro-send');
        sendBtn.disabled = draft.length === 0;
        $('ro-send-cnt').textContent = POS.t('posui.rest.send').replace('{n}', draft.length);
        $('ro-bill').disabled = sent.length === 0 && draft.length === 0;
    }
    function sum(list) {
        return (list || []).reduce((s, l) => s + Number(l.line_total || 0), 0);
    }

    async function sendKitchen() {
        if (!(curSession.draft_lines || []).length) return;
        const btn = $('ro-send');
        btn.disabled = true;
        try {
            await RD.sendKitchen(curSession.session.id);
            POS.toast(POS.t('posui.rest.sent.toast'));
            await loadOrder(curSession.session.id);
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
            btn.disabled = false;
        }
    }

    // ── 渲染钩子(showView 调)+ 绑定 ──
    R.renderTables = renderTables;

    R.init = function () {
        $('rt-open-go').addEventListener('click', confirmOpen);
        $('rt-open-close').addEventListener('click', () =>
            $('rt-open-mask').classList.remove('show')
        );
        $('rt-kitchen-btn').addEventListener('click', () => POS.showView('rkitchen'));
        $('ro-back').addEventListener('click', () => {
            POS.showView('rtables');
            renderTables();
        });
        $('ro-send').addEventListener('click', sendKitchen);
        $('ro-bill').addEventListener('click', () => R.openBill && R.openBill(curSession));
        document
            .querySelectorAll('#rt-seg button')
            .forEach((b) => b.addEventListener('click', () => onSeg(b)));
        if (R.initOps) R.initOps();
    };

    function onSeg(b) {
        document.querySelectorAll('#rt-seg button').forEach((x) => x.classList.remove('on'));
        b.classList.add('on');
        if (b.dataset.svc !== 'dine_in') POS.toast(POS.t('posui.rest.svc.soon'));
    }
})();
