// ============================================================
// REFACTOR-WB-modularize · 文件夹监听 IO 层(IndexedDB + 权限 + 上传 + 扫描遍历)从 folder-watcher.js 拆出
//
// 无业务状态的工具:openDB/idbGet/idbPut/idbDel/idbClear · ensurePermission · uploadOne ·
// isFileStable · walkDir。folder-watcher.js 经 ESM import 调用。
// ============================================================
/* global token */
const VALID_EXTS = /\.(pdf|jpe?g|png|webp)$/i;
const DB_NAME = 'mrpilot_folder_watcher';
const DB_VERSION = 1;
let _dbPromise: Promise<IDBDatabase> | null = null;

// ---------- IndexedDB ----------
function openDB() {
    if (_dbPromise) return _dbPromise;
    _dbPromise = new Promise((resolve, reject) => {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = (e: Event) => {
            const db = (e.target as IDBOpenDBRequest).result;
            if (!db.objectStoreNames.contains('handles')) db.createObjectStore('handles');
            if (!db.objectStoreNames.contains('seen')) db.createObjectStore('seen');
            if (!db.objectStoreNames.contains('config')) db.createObjectStore('config');
        };
        req.onsuccess = (e: Event) => resolve((e.target as IDBOpenDBRequest).result);
        req.onerror = (e: Event) => reject((e.target as IDBOpenDBRequest).error);
    });
    return _dbPromise;
}

function idbGet(store: string, key: IDBValidKey) {
    return openDB().then(
        (db: IDBDatabase) =>
            new Promise((resolve, reject) => {
                const tx = db.transaction(store, 'readonly');
                const req = tx.objectStore(store).get(key);
                req.onsuccess = () => resolve(req.result);
                req.onerror = () => reject(req.error);
            })
    );
}
function idbPut(store: string, key: IDBValidKey, value: unknown) {
    return openDB().then(
        (db: IDBDatabase) =>
            new Promise<void>((resolve, reject) => {
                const tx = db.transaction(store, 'readwrite');
                tx.objectStore(store).put(value, key);
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            })
    );
}
function idbDel(store: string, key: IDBValidKey) {
    return openDB().then(
        (db: IDBDatabase) =>
            new Promise<void>((resolve, reject) => {
                const tx = db.transaction(store, 'readwrite');
                tx.objectStore(store).delete(key);
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            })
    );
}
function idbClear(store: string) {
    return openDB().then(
        (db: IDBDatabase) =>
            new Promise<void>((resolve, reject) => {
                const tx = db.transaction(store, 'readwrite');
                tx.objectStore(store).clear();
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            })
    );
}

// ---------- 权限 ----------
async function ensurePermission(handle: any) {
    if (!handle) return false;
    try {
        const opts = { mode: 'read' };
        let perm = await handle.queryPermission(opts);
        if (perm === 'granted') return true;
        perm = await handle.requestPermission(opts);
        return perm === 'granted';
    } catch (e) {
        console.warn('[folder] permission check failed:', e);
        return false;
    }
}

// ---------- 上传单个文件 ----------
async function uploadOne(file: File) {
    const fd = new FormData();
    fd.append('file', file, file.name);
    fd.append('source', 'folder');
    // v101 · Bug 2 对冲 · 后端可能只从 query/header 读 source
    const resp = await fetch('/api/ocr/recognize?source=folder', {
        method: 'POST',
        headers: {
            Authorization: 'Bearer ' + token,
            'X-Source': 'folder',
        },
        body: fd,
    });
    if (!resp.ok) {
        let errCode = 'http_' + resp.status;
        try {
            const j = await resp.json();
            errCode =
                j && j.detail
                    ? typeof j.detail === 'string'
                        ? j.detail
                        : j.detail.code || JSON.stringify(j.detail)
                    : errCode;
        } catch {}
        throw new Error(errCode);
    }
    return await resp.json();
}

// ---------- 等文件写完(检测 size 不变 3s)----------
async function isFileStable(handle: any) {
    try {
        const f1 = await handle.getFile();
        const s1 = f1.size;
        await new Promise((r) => setTimeout(r, 3000));
        const f2 = await handle.getFile();
        return f2.size === s1 && s1 > 0;
    } catch {
        return false;
    }
}

// v118.24 · 递归遍历目录 · 子文件夹也扫
async function walkDir(handle: any, prefix: string, candidates: any[], depth: number) {
    if (depth > 10) return; // 防深度爆栈
    let perm;
    try {
        perm = await handle.queryPermission({ mode: 'read' });
    } catch {
        perm = 'denied';
    }
    if (perm !== 'granted') return;
    for await (const entry of handle.values()) {
        const relPath = prefix ? `${prefix}/${entry.name}` : entry.name;
        if (entry.kind === 'file') {
            if (!VALID_EXTS.test(entry.name)) continue;
            let f;
            try {
                f = await entry.getFile();
            } catch {
                continue;
            }
            // seenKey 含相对路径 · 避免不同子文件夹同名文件互相误判
            const seenKey = `${relPath}::${f.size}::${f.lastModified}`;
            const seen = await idbGet('seen', seenKey);
            if (seen) continue;
            candidates.push({ entry, file: f, seenKey, relPath });
        } else if (entry.kind === 'directory') {
            try {
                await walkDir(entry, relPath, candidates, depth + 1);
            } catch (e) {
                /* 单个子目录失败不影响整体 */
            }
        }
    }
}
export { idbGet, idbPut, idbDel, idbClear, ensurePermission, uploadOne, isFileStable, walkDir };
