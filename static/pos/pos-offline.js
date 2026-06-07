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
        const term = 'T' + String(state.terminalId || 1).padStart(2, '0');
        const year = new Date().getFullYear();
        const key = 'recv_seq_' + term + '_' + year;
        const seq = (Number(await kvGet(key)) || 0) + 1;
        await kvSet(key, seq);
        return 'OFF-' + term + '-' + year + '-' + String(seq).padStart(6, '0');
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
                p.stock.qty_base = String(Number(p.stock.qty_base || 0) - base);
            }
        }
        kvSet('catalog', snapshot);
    }

    // ── 离线建单:本地算价 + 写 outbox + 出小票 ──
    async function enqueueSale(payload) {
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
                status: 'completed',
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
    async function sync() {
        if (syncing || !state.online || !state.token) return;
        const items = await outboxAll();
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
                if (r && r.ok) await outboxDel(it.client_uuid); // 含 deduped:true 也算成功
            }
        } catch (_) {
            // 整批失败(网络抖动):保留 outbox,下次再冲
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
        const n = await pendingCount();
        pill.classList.remove('busy');
        if (n > 0) {
            pill.style.display = '';
            txt.textContent = POS.tf('posui.sync.pending', { n: n });
        } else {
            pill.style.display = 'none';
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
    };
})();
