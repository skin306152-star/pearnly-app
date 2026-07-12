/*
 * Pearnly POS · pos-offline.js · 离线 outbox + 同步引擎(08 ADR-2/3/5/6)
 *
 * 断网开单:本地算价(POS.totals)+ 生成终端临时号 + 写持久 outbox + 乐观扣缓存库存 + 立即出小票,
 * 不等网络。联网恢复:按 sold_at 顺序批量 POST /api/pos/sales/sync,client_uuid 幂等;成功移出
 * outbox,失败保留重试。持久层 = IndexedDB(崩溃/重开不丢);IndexedDB 不可用时回落 localStorage。
 *
 * 号说明:后端 sync 会以服务端连号入库(联网即权威),离线临时号(OFF-…)仅用于即时小票;不双扣
 * 由 client_uuid UNIQUE 保证(04 §0.3)。商品快照供离线选品,联网全量拉时回填。
 */
(function () {
    const POS = (window.POS = window.POS || {});
    const state = POS.state;
    const VAT_RATE = 7; // 对齐后端 services/pos/sale.VAT_RATE

    // ── 持久层:IndexedDB 优先,失败回落 localStorage ──
    const DB_NAME = 'pearnly_pos';
    const LS_OUTBOX = 'pos_outbox';
    const LS_KV = 'pos_kv';
    let dbp = null;

    function openDB() {
        if (dbp) return dbp;
        dbp = new Promise((res, rej) => {
            let r;
            try {
                r = indexedDB.open(DB_NAME, 1);
            } catch (e) {
                return rej(e);
            }
            r.onupgradeneeded = () => {
                const db = r.result;
                if (!db.objectStoreNames.contains('outbox'))
                    db.createObjectStore('outbox', { keyPath: 'client_uuid' });
                if (!db.objectStoreNames.contains('kv'))
                    db.createObjectStore('kv', { keyPath: 'k' });
            };
            r.onsuccess = () => res(r.result);
            r.onerror = () => rej(r.error);
        });
        return dbp;
    }
    function reqP(req) {
        return new Promise((res, rej) => {
            req.onsuccess = () => res(req.result);
            req.onerror = () => rej(req.error);
        });
    }
    function lsRead(key) {
        try {
            return JSON.parse(localStorage.getItem(key) || (key === LS_OUTBOX ? '[]' : '{}'));
        } catch (_) {
            return key === LS_OUTBOX ? [] : {};
        }
    }
    function lsWrite(key, val) {
        try {
            localStorage.setItem(key, JSON.stringify(val));
        } catch (_) {}
    }

    async function outboxPut(rec) {
        try {
            const os = (await openDB()).transaction('outbox', 'readwrite').objectStore('outbox');
            return await reqP(os.put(rec));
        } catch (_) {
            const list = lsRead(LS_OUTBOX).filter((x) => x.client_uuid !== rec.client_uuid);
            list.push(rec);
            lsWrite(LS_OUTBOX, list);
        }
    }
    async function outboxAll() {
        try {
            const os = (await openDB()).transaction('outbox', 'readonly').objectStore('outbox');
            return (await reqP(os.getAll())) || [];
        } catch (_) {
            return lsRead(LS_OUTBOX);
        }
    }
    async function localReceipt(key) {
        const mapped = await kvGet('receipt_' + key);
        if (mapped) return mapped;
        const record = (await outboxAll()).find(
            (item) => item.client_uuid === key || item.receipt_no === key
        );
        return record
            ? {
                  status: record.status,
                  client_uuid: record.client_uuid,
                  temporary_receipt_no: record.receipt_no,
                  last_error: record.last_error,
              }
            : null;
    }
    async function outboxDel(clientUuid) {
        try {
            const os = (await openDB()).transaction('outbox', 'readwrite').objectStore('outbox');
            return await reqP(os.delete(clientUuid));
        } catch (_) {
            lsWrite(
                LS_OUTBOX,
                lsRead(LS_OUTBOX).filter((x) => x.client_uuid !== clientUuid)
            );
        }
    }
    async function kvGet(k) {
        try {
            const os = (await openDB()).transaction('kv', 'readonly').objectStore('kv');
            const r = await reqP(os.get(k));
            return r ? r.v : undefined;
        } catch (_) {
            return lsRead(LS_KV)[k];
        }
    }
    async function kvSet(k, v) {
        try {
            const os = (await openDB()).transaction('kv', 'readwrite').objectStore('kv');
            return await reqP(os.put({ k: k, v: v }));
        } catch (_) {
            const m = lsRead(LS_KV);
            m[k] = v;
            lsWrite(LS_KV, m);
        }
    }

    // ── 终端临时号(OFF-<终端>-<年>-<序>)· 仅离线即时小票用 ──
    async function nextLocalReceiptNo() {
        if (!state.terminalId) throw new POS.PosErr('pos.terminal_not_found', 409, null, true);
        const term = 'T' + String(state.terminalId).padStart(2, '0');
        let device = await kvGet('offline_device_id');
        if (!device) {
            device = POS.uuid().replace(/-/g, '').slice(0, 8).toUpperCase();
            await kvSet('offline_device_id', device);
        }
        const year = new Date().getFullYear();
        const key = 'recv_seq_' + device + '_' + term + '_' + year;
        const seq = (Number(await kvGet(key)) || 0) + 1;
        await kvSet(key, seq);
        return 'OFF-' + device + '-' + term + '-' + year + '-' + String(seq).padStart(6, '0');
    }

    // ── 商品快照(离线选品)──
    let snapshot = null;
    async function loadSnapshot() {
        if (snapshot) return snapshot;
        snapshot = (await kvGet('catalog')) || null;
        return snapshot;
    }
    function cacheCatalog(items) {
        if (!items || !items.length) return;
        snapshot = items;
        kvSet('catalog', items);
    }
    function hasSnapshot() {
        return !!(snapshot && snapshot.length);
    }
    function filterCached(q, cat) {
        const items = snapshot || [];
        return POS.filterCatalog ? POS.filterCatalog(items, q, cat) : items;
    }
    // 乐观扣缓存库存(ADR-5)· 允许转负不拦单
    function decrementCache(lines) {
        if (!snapshot) return;
        for (const l of lines || []) {
            const p = snapshot.find((x) => x.id === l.product_id);
            if (p && p.stock) {
                const factor = (p.units || []).find((u) => u.unit_name === l.sell_unit) || {};
                const base = Number(factor.factor || 1) * Number(l.qty || 0);
                p.stock.qty_base = String(Math.max(0, Number(p.stock.qty_base || 0) - base));
            }
        }
        kvSet('catalog', snapshot);
    }
    function canDeductCache(lines) {
        if (!snapshot) return false;
        const required = {};
        for (const line of lines || []) {
            const product = snapshot.find((item) => item.id === line.product_id);
            const qty = Number(line.qty);
            if (!product || !product.stock || !Number.isFinite(qty) || qty <= 0) return false;
            const unit = (product.units || []).find((item) => item.unit_name === line.sell_unit);
            if (!unit || !Number.isFinite(Number(unit.factor)) || Number(unit.factor) <= 0)
                return false;
            required[line.product_id] =
                Number(required[line.product_id] || 0) + Number(unit.factor) * qty;
        }
        return Object.keys(required).every((id) => {
            const product = snapshot.find((item) => item.id === id);
            return Number(product.stock.qty_base || 0) >= required[id];
        });
    }

    // ── 离线建单:本地算价 + 写 outbox + 出小票 ──
    async function enqueueSale(payload) {
        if (!canDeductCache(payload.lines))
            throw new POS.PosErr('pos.out_of_stock', 409, null, true);
        const totals = POS.totals.localTotals(
            (payload.lines || []).map((l) => ({
                qty: l.qty,
                unit_price: l.unit_price,
                discount: l.line_discount,
                vat_applicable: l.vat_applicable !== false,
            })),
            {
                vat_rate: VAT_RATE,
                price_includes_vat: !!payload.price_includes_vat,
                header_discount_amount:
                    payload.header_discount && payload.header_discount.type === 'amount'
                        ? payload.header_discount.value
                        : 0,
                header_discount_pct:
                    payload.header_discount && payload.header_discount.type === 'pct'
                        ? payload.header_discount.value
                        : 0,
            }
        );
        const paid = (payload.payments || []).reduce((s, p) => s + Number(p.amount || 0), 0);
        const grand = Number(totals.grand_total);
        const change = paid > grand ? (paid - grand).toFixed(2) : '0.00';
        const receiptNo = await nextLocalReceiptNo();
        const rec = {
            client_uuid: payload.client_uuid,
            payload: payload,
            receipt_no: receiptNo,
            grand_total: totals.grand_total,
            vat_amount: totals.vat_amount,
            sold_at: payload.sold_at,
            status: 'pending',
            tries: 0,
            last_error: null,
            next_retry_at: null,
        };
        await outboxPut(rec);
        decrementCache(payload.lines);
        updateBadge();
        return {
            sale: {
                id: payload.client_uuid,
                receipt_no: receiptNo,
                grand_total: totals.grand_total,
                vat_amount: totals.vat_amount,
                paid_total: paid.toFixed(2),
                change_amount: change,
                status: 'pending',
                temporary_receipt: true,
            },
            stock_applied: true,
            deduped: false,
            offline: true,
        };
    }

    // ── 同步引擎(联网即冲)──
    let syncing = false;
    async function pendingCount() {
        return (await outboxAll()).length;
    }
    function failureState(status) {
        if (status === 401 || status === 403) return 'auth_paused';
        if (status === 409 || status === 422) return 'blocked';
        return 'retrying';
    }
    function retryAt(tries) {
        return Date.now() + Math.min(300000, 1000 * 2 ** Math.min(tries, 8));
    }
    function authMarker(token) {
        let hash = 2166136261;
        for (let i = 0; i < String(token || '').length; i += 1) {
            hash ^= String(token).charCodeAt(i);
            hash = Math.imul(hash, 16777619);
        }
        return (hash >>> 0).toString(36);
    }
    async function markFailure(it, status, code) {
        it.tries = Number(it.tries || 0) + 1;
        it.status = failureState(status);
        it.last_error =
            code || (status === 401 || status === 403 ? 'pos.login_required' : 'pos.sync_failed');
        it.next_retry_at = it.status === 'retrying' ? retryAt(it.tries) : null;
        it.paused_auth_marker = it.status === 'auth_paused' ? authMarker(state.token) : null;
        delete it.paused_token;
        await outboxPut(it);
    }
    async function sync() {
        if (syncing || !state.online || !state.token) return;
        const now = Date.now();
        const records = await outboxAll();
        for (const record of records) {
            if (
                record.status === 'auth_paused' &&
                state.token &&
                authMarker(state.token) !== record.paused_auth_marker
            ) {
                record.status = 'pending';
                record.last_error = null;
                record.paused_auth_marker = null;
                delete record.paused_token;
                await outboxPut(record);
            }
        }
        const items = records.filter(
            (it) =>
                it.status !== 'blocked' &&
                it.status !== 'auth_paused' &&
                Number(it.next_retry_at || 0) <= now
        );
        if (!items.length) {
            updateBadge();
            return;
        }
        syncing = true;
        updateBadge('syncing');
        try {
            items.sort((a, b) => String(a.sold_at).localeCompare(String(b.sold_at)));
            const data = await POS.data.syncSales(items.map((it) => it.payload));
            const results = (data && data.results) || [];
            const byUuid = {};
            results.forEach((r) => (byUuid[r.client_uuid] = r));
            for (const it of items) {
                const r = byUuid[it.client_uuid];
                if (!r || r.client_uuid !== it.client_uuid) {
                    await markFailure(it, 0, 'pos.sync_invalid_response');
                    continue;
                }
                if (r.ok) {
                    const mapping = {
                        status: 'synced',
                        client_uuid: it.client_uuid,
                        temporary_receipt_no: it.receipt_no,
                        sale_id: r.sale_id,
                        receipt_no: r.receipt_no,
                        synced_at: new Date().toISOString(),
                    };
                    await kvSet('receipt_' + it.client_uuid, mapping);
                    await kvSet('receipt_' + it.receipt_no, mapping);
                    const saved = await kvGet('receipt_' + it.receipt_no);
                    if (
                        !saved ||
                        saved.client_uuid !== it.client_uuid ||
                        saved.receipt_no !== r.receipt_no
                    ) {
                        await markFailure(it, 0, 'pos.sync_mapping_failed');
                        continue;
                    }
                    await outboxDel(it.client_uuid); // 含 deduped:true 也算成功
                    window.dispatchEvent(new CustomEvent('pos:sale-synced', { detail: saved }));
                    continue;
                }
                await markFailure(it, Number(r.status || 422), r.error && r.error.code);
            }
        } catch (error) {
            for (const it of items) await markFailure(it, Number(error.status || 0), error.code);
        } finally {
            syncing = false;
            updateBadge();
        }
    }

    // ── UI 角标:待同步 N 单(08 ADR-6)──
    async function updateBadge(forceState) {
        const pill = document.getElementById('sync-pill');
        const txt = document.getElementById('sync-txt');
        if (!pill || !txt) return;
        if (forceState === 'syncing') {
            pill.style.display = '';
            pill.classList.add('busy');
            txt.textContent = POS.t('posui.sync.syncing');
            return;
        }
        const records = await outboxAll();
        const blocked = records.filter((it) => it.status === 'blocked').length;
        const authPaused = records.filter((it) => it.status === 'auth_paused').length;
        const retrying = records.filter((it) => it.status === 'retrying').length;
        const n = records.length;
        pill.classList.remove('busy');
        pill.classList.toggle('blocked', blocked > 0);
        if (authPaused > 0) {
            pill.style.display = '';
            txt.textContent = POS.tf('posui.sync.auth_paused', { n: authPaused });
            pill.title = POS.t('posui.sync.auth_paused_help');
        } else if (blocked > 0) {
            pill.style.display = '';
            txt.textContent = POS.tf('posui.sync.blocked', { n: blocked });
            pill.title = POS.t('posui.sync.blocked_help');
        } else if (retrying > 0) {
            pill.style.display = '';
            txt.textContent = POS.tf('posui.sync.retrying', { n: retrying });
            pill.title = POS.t('posui.sync.retrying_help');
        } else if (n > 0) {
            pill.style.display = '';
            txt.textContent = POS.tf('posui.sync.pending', { n: n });
            pill.title = POS.t('posui.sync.pending_help');
        } else {
            pill.style.display = 'none';
            pill.title = '';
        }
    }

    let heartbeat = null;
    function init() {
        loadSnapshot();
        updateBadge();
        // 联网恢复 → 冲;心跳兜底(漏过 online 事件 / 部分失败重试退避用整分钟轮询)
        window.addEventListener('online', () => sync());
        if (heartbeat) clearInterval(heartbeat);
        heartbeat = setInterval(() => sync(), 30000);
        // 启动即尝试补传上次未传(崩溃恢复)
        sync();
    }

    POS.offline = {
        init: init,
        enqueueSale: enqueueSale,
        sync: sync,
        pendingCount: pendingCount,
        cacheCatalog: cacheCatalog,
        hasSnapshot: hasSnapshot,
        filterCached: filterCached,
        updateBadge: updateBadge,
        findReceipt: localReceipt,
    };
})();
