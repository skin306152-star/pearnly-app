/*
 * Pearnly POS · cashier-sw.js · 收银台新家(/cashier)离线外壳 Service Worker(PS-5 迁址)。
 *
 * 与老 pos-sw.js(scope /pos · 老设备用)同款策略,只是作用域/缓存指向 /cashier:
 *  - /api/*  : 不拦,放行让其自然失败 → 前端走 IndexedDB outbox(pos-offline.js)。
 *  - 其余同源 GET(外壳/静态): cache-first + 联网回填;离线导航回落已缓存的 /cashier。
 * 缓存名带版本号,改外壳 bump 即可让旧缓存失效(对齐 ?v= 缓存破)。
 * 独立于 /pos 旧 SW:老收银设备的 /pos SW 原样不动,两作用域互不干扰。
 */
const CACHE = 'pearnly-cashier-v11871100';
const CORE = ['/cashier'];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches
            .open(CACHE)
            .then((c) => c.addAll(CORE))
            .then(() => self.skipWaiting())
            .catch(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches
            .keys()
            .then((keys) =>
                Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
            )
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (e) => {
    const req = e.request;
    if (req.method !== 'GET') return;
    const url = new URL(req.url);
    if (url.origin !== self.location.origin) return;
    if (url.pathname.startsWith('/api/')) return; // 放行 → 离线时自然失败,前端用 outbox
    e.respondWith(
        caches.match(req).then(
            (cached) =>
                cached ||
                fetch(req)
                    .then((res) => {
                        if (res && res.ok) {
                            const copy = res.clone();
                            caches.open(CACHE).then((c) => c.put(req, copy));
                        }
                        return res;
                    })
                    .catch(() => caches.match('/cashier'))
        )
    );
});
