/*
 * Pearnly POS · pos-sw.js · 离线外壳 Service Worker(08 ADR-1)
 *
 * 缓存 /pos 外壳(HTML/CSS/JS/i18n)→ 断网仍能开机收银。策略:
 *  - /api/*  : 不拦,放行让其自然失败 → 前端走 IndexedDB outbox(pos-offline.js)。
 *  - 其余同源 GET(外壳/静态): cache-first + 联网回填;离线导航回落已缓存的 /pos。
 * 缓存名带版本号,改外壳 bump 即可让旧缓存失效(对齐 ?v= 缓存破)。
 */
const CACHE = 'pearnly-pos-v11850965';
const CORE = ['/pos'];

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
                    .catch(() => caches.match('/pos'))
        )
    );
});
