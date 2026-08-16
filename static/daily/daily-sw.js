/*
 * Pearnly Daily · daily-sw.js · /daily 离线外壳 Service Worker(照 cashier-sw.js 范式)。
 *
 * 策略:严格在线(数据唯一源在服务端),SW 只缓存应用外壳与静态资源:
 *  - /api/*  : 不拦,放行让其自然失败 → 前端四态诚实(故障态可重试)。
 *  - 其余同源 GET(外壳/静态):cache-first + 联网回填;离线导航回落已缓存的 /daily。
 * 缓存名带版本号,改外壳 bump 即可让旧缓存失效(对齐 ?v= 缓存破)。
 */
const V = '4';
const PREFIX = 'pearnly-daily-v';
const CACHE = PREFIX + V;
const CORE = ['/daily'];

function isDailyAsset(pathname) {
    return (
        pathname === '/daily' ||
        pathname.startsWith('/daily/') ||
        pathname === '/daily-sw.js' ||
        pathname.startsWith('/static/daily/') ||
        pathname.startsWith('/static/brand/') ||
        pathname === '/static/dist/daily.js' ||
        pathname === '/static/dist/daily.css'
    );
}

// 外壳没落地就不许上位(同 cashier-sw 教训:activate 删旧缓存时新缓存必须已就绪,
// 否则部署重启窗口断网打开 /daily 是浏览器网络错误页)。
self.addEventListener('install', (e) => {
    e.waitUntil(
        caches
            .open(CACHE)
            .then((c) => c.addAll(CORE))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches
            .open(CACHE)
            .then((c) => c.match('/daily'))
            .then((hit) => {
                if (!hit) return;
                return caches
                    .keys()
                    .then((keys) =>
                        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
                    )
                    .then(() => self.clients.claim());
            })
    );
});

self.addEventListener('fetch', (e) => {
    const url = new URL(e.request.url);
    if (e.request.method !== 'GET' || url.origin !== self.location.origin) return;
    if (url.pathname.startsWith('/api/')) return;
    if (!isDailyAsset(url.pathname)) return;

    e.respondWith(
        caches.match(e.request).then((hit) => {
            if (hit) return hit;
            return fetch(e.request).then((resp) => {
                if (resp.ok && isDailyAsset(url.pathname)) {
                    const copy = resp.clone();
                    caches.open(CACHE).then((c) => c.put(e.request, copy));
                }
                return resp;
            });
        })
    );
});
