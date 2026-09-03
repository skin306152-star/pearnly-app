/*
 * Pearnly POS · pos-sw.js · 离线外壳 Service Worker(08 ADR-1)
 *
 * 缓存 /pos 外壳(HTML/CSS/JS/i18n)→ 断网仍能开机收银。策略:
 *  - /api/*  : 不拦,放行让其自然失败 → 前端走 IndexedDB outbox(pos-offline.js)。
 *  - 其余同源 GET(外壳/静态): cache-first + 联网回填;离线导航回落已缓存的 /pos。
 * 缓存名带版本号,改外壳 bump 即可让旧缓存失效(对齐 ?v= 缓存破)。
 */
// 版本号跟 pos.html 里 dist/pos.js 的 ?v= 保持一致:外壳 bundle 一变(本次并入扫码常驻层)
// 就换缓存名,否则离线缓存里那份旧 bundle 永远不会被换掉,店里那台机器扫码功能压根不存在。
const V = '12060017';
// 前缀 = 「这一族缓存是我的」的唯一凭据(见 dropStaleCaches)。CACHE 由它拼出来,两处不分家。
const PREFIX = 'pearnly-pos-v';
const CACHE = PREFIX + V;
const SHELL = ['/pos'];
// 扫码产物不写在 HTML 里,是 scan-loader.js 运行时现拼 URL 拉的(?v 抠自页面上 pos.js
// 的 ?v,所以这里跟 CACHE 共用同一个 V,漂不开)。不预缓存 = 断网还能卖货却扫不了码,而
// 离线可用正是这台机器存在的理由。缓存按完整 URL 匹配:少了 ?v 就是另一条记录,等于没缓存。
const SCAN = [
    '/static/dist/scan.js?v=' + V,
    '/static/dist/barcode-detector.js?v=' + V,
    '/static/dist/zxing_reader.wasm?v=' + V,
    '/static/dist/zxing.js?v=' + V,
];

// 外壳没落地就不许上位:activate 会删掉所有别名缓存,而这一版缓存是空的。部署重启那十几秒
// nginx 对 /pos 回 502,恰好开着页面的那台机器就会被 catch 里的 skipWaiting 推上位 —— 旧缓存
// 删掉、新缓存空的,此后断网打开就是浏览器网络错误页,不是「离线模式」,是彻底打不开。
// 装不上就让这版装失败:旧 SW 与旧缓存原样留着,下次导航再试一次。
self.addEventListener('install', (e) => {
    e.waitUntil(
        caches
            .open(CACHE)
            // addAll 是全有全无:扫码产物任意一个拉不到就会把外壳一起丢掉,断网连收银台都开不了。
            // 外壳必须先自己落地,扫码那两个尽力而为(拉不到时留给 fetch 那条 cache-first 回填)。
            .then((c) =>
                c.addAll(SHELL).then(() => Promise.all(SCAN.map((u) => c.add(u).catch(() => null))))
            )
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (e) => {
    // 再确认一次新缓存里真有外壳才清旧的:install 之后缓存也可能被系统回收,
    // 那时删旧缓存就是把这台机器的离线能力一次清零。
    e.waitUntil(
        caches
            .open(CACHE)
            .then((c) => c.match(SHELL[0]))
            .then((shell) => (shell ? dropStaleCaches() : null))
            .then(() => self.clients.claim())
    );
});

// 只删自己这一族。CacheStorage 是按源的、不按 SW 作用域分家:caches.keys() 在这里同样列得出
// /cashier 那个 SW 的缓存,而删除时没有任何作用域保护。「不是我这个就删」于是变成:老设备点一下
// /pos,在用的收银台离线外壳被整族抹掉 —— 那台机器断网再开是浏览器网络错误页,不是离线模式,
// 是彻底打不开、货卖不了(反过来同理)。认不出来历的缓存宁可留着:多占几 MB 换不掉一台收银机。
function dropStaleCaches() {
    return caches
        .keys()
        .then((keys) =>
            Promise.all(
                keys.filter((k) => k.startsWith(PREFIX) && k !== CACHE).map((k) => caches.delete(k))
            )
        );
}

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
