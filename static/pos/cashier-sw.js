/*
 * Pearnly POS · cashier-sw.js · 收银台新家(/cashier)离线外壳 Service Worker(PS-5 迁址)。
 *
 * 与老 pos-sw.js(scope /pos · 老设备用)同款策略,只是作用域/缓存指向 /cashier:
 *  - /api/*  : 不拦,放行让其自然失败 → 前端走 IndexedDB outbox(pos-offline.js)。
 *  - 其余同源 GET(外壳/静态): cache-first + 联网回填;离线导航回落已缓存的 /cashier。
 * 缓存名带版本号,改外壳 bump 即可让旧缓存失效(对齐 ?v= 缓存破)。
 * 独立于 /pos 旧 SW:老收银设备的 /pos SW 原样不动,两作用域互不干扰。
 */
// 版本号跟 pos.html 里 dist/pos.js 的 ?v= 保持一致(同 pos-sw.js):/cashier 是收银台现在的家,
// 外壳 cache-first,不换缓存名就等于在用的机器永远拿旧 pos.html —— 新加的扫码层在店里压根不存在。
const V = '12060012';
// 前缀 = 「这一族缓存是我的」的唯一凭据(见 dropStaleCaches)。CACHE 由它拼出来,两处不分家。
const PREFIX = 'pearnly-cashier-v';
const CACHE = PREFIX + V;
const CORE = ['/cashier'];
// 扫码那两个产物不写在 HTML 里,是 scan-loader.js 运行时现拼 URL 拉的(?v 抠自页面上 pos.js
// 的 ?v,所以这里跟 CACHE 共用同一个 V,漂不开)。它们既得进 install 清单,也得过 isCashierAsset
// 那道门 —— 少任何一样,断网时缓存里永远不会有解码器:还能卖货,却扫不了码。
const SCAN = ['/static/dist/scan.js', '/static/dist/zxing.js'];
const SCAN_URLS = SCAN.map((p) => p + '?v=' + V);

function isCashierAsset(pathname) {
    return (
        pathname === '/cashier' ||
        pathname.startsWith('/cashier/') ||
        pathname === '/cashier-sw.js' ||
        pathname.startsWith('/static/pos/') ||
        pathname.startsWith('/static/brand/') ||
        pathname === '/static/dist/pos.js' ||
        pathname === '/static/dist/pos.css' ||
        SCAN.indexOf(pathname) >= 0
    );
}

// 外壳没落地就不许上位:activate 会删掉所有别名缓存,而这一版缓存是空的。部署重启那十几秒
// nginx 对 /cashier 回 502,恰好开着页面的那台 iPad 就会被 catch 里的 skipWaiting 推上位 ——
// 旧缓存删掉、新缓存空的,此后断网打开 /cashier 是浏览器网络错误页,不是「离线模式」,是彻底
// 打不开、货卖不了。装不上就让这版装失败:旧 SW 与旧缓存原样留着,下次导航再试一次。
self.addEventListener('install', (e) => {
    e.waitUntil(
        caches
            .open(CACHE)
            // addAll 是全有全无:解码器任意一个拉不到就会把外壳一起丢掉,断网连收银台都开不了。
            // 外壳必须先自己落地,解码器尽力而为(拉不到时留给 fetch 那条 cache-first 回填)。
            .then((c) =>
                c
                    .addAll(CORE)
                    .then(() => Promise.all(SCAN_URLS.map((u) => c.add(u).catch(() => null))))
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
            .then((c) => c.match(CORE[0]))
            .then((shell) => (shell ? dropStaleCaches() : null))
            .then(() => self.clients.claim())
    );
});

// 只删自己这一族。作用域只管导航,管不了缓存:CacheStorage 按源共享,caches.keys() 在这里
// 同样列得出老 /pos SW 那一族,而删除时没有任何作用域保护。「不是我这个就删」于是变成:
// 收银台装一次新 SW 就把老设备的 /pos 离线外壳抹掉(反过来老设备点一下 /pos 也会抹掉这台在用的
// 收银台)—— 断网再开是浏览器网络错误页,不是离线模式,是彻底打不开、货卖不了。
// 认不出来历的缓存宁可留着:多占几 MB 换不掉一台收银机。
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
    if (!isCashierAsset(url.pathname)) return;
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
