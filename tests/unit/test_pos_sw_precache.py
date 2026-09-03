#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_sw_precache.py

收银台两个离线外壳 Service Worker 的预缓存行为(static/pos/cashier-sw.js = /cashier 现在的家,
static/pos/pos-sw.js = 还留在 /pos 的老设备)。真 node 跑 install / activate / fetch 事件、真读
它往假 Cache 里放了什么 —— 不是 grep 源码里有没有出现 'scan.js'。

钉死六条:
  1. 断网还能卖货却扫不了码 = 半个功能。扫码引擎与解码器产物
     必须跟外壳一起进预缓存。
  2. cashier-sw 的 fetch 是白名单式的:解码器不在名单里,连联网那次的顺手回填都没有,
     缓存里永远不会有它们。预缓存和白名单少任何一样,离线扫码都是零。
  3. 缓存按完整 URL 匹配:预缓存的 ?v 必须等于页面上 dist bundle 的 ?v(scan-loader.js 运行时
     就是从那里抠的)。漂一位 = 缓存了一条谁也不会请求的记录,等于没缓存。
  4. addAll 全有全无:解码器任意一个拉不到,不许把外壳一起丢掉(那就连收银台都开不了)。
  5. 换版本号要真的换掉旧缓存,否则店里那台机器永远跑着旧 bundle。
  6. 两个 SW 只删自己那一族缓存。CacheStorage 是按源的:作用域隔离导航,不隔离缓存。
     这条此前照不出来,因为假 CacheStorage 里只放了一个 SW 的键 —— 一个 SW 的世界里
     「删掉不是我的」永远无害。反证必须让两个 SW 的缓存键同时存在,而且用的是对方 install
     时真开出来的那个名字(不是测里手打的字符串,那样只是拿桩验桩)。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POS_DIR = PROJECT_ROOT / "static" / "pos"
SCAN_PRODUCTS = (
    "/static/dist/scan.js",
    "/static/dist/barcode-detector.js",
    "/static/dist/zxing_reader.wasm",
    "/static/dist/zxing.js",
)

# 文件 → (外壳 URL, 缓存名前缀)。/cashier 是收银台现在的家;/pos 留给还没迁的老设备。
WORKERS = {
    "cashier-sw.js": ("/cashier", "pearnly-cashier-v"),
    "pos-sw.js": ("/pos", "pearnly-pos-v"),
}

NODE_HARNESS = r"""
const fs = require('fs');
const jobs = JSON.parse(process.argv[1]);

// 假 Cache:addAll 照真 API 的语义做成全有全无(任意一个失败整批不落地)——
// 正是这一点让「解码器混进外壳清单」变成「一个 404 干掉整个离线外壳」。
function mkCaches(failing, existingKeys, store) {
    const cache = {
        addAll(list) {
            if (list.some((u) => failing.includes(u))) return Promise.reject(new Error('404'));
            store.cached.push(...list);
            return Promise.resolve();
        },
        add(u) {
            if (failing.includes(u)) return Promise.reject(new Error('404'));
            store.cached.push(u);
            return Promise.resolve();
        },
        put: () => Promise.resolve(),
        // 真 Cache.match:只有真进了这个缓存的 URL 才算命中。activate 的「外壳到底落地没有」
        // 就靠它判 —— 给个恒 null / 恒命中的桩等于把要验的那道门拆掉。
        match: (u) => Promise.resolve(store.cached.indexOf(u) >= 0 ? { ok: true } : null),
    };
    global.caches = {
        open(name) {
            store.opened.push(name);
            return Promise.resolve(cache);
        },
        keys: () => Promise.resolve(existingKeys),
        delete(k) {
            store.deleted.push(k);
            return Promise.resolve(true);
        },
        match: () => Promise.resolve(null),
    };
}

const ORIGIN = 'https://pearnly.test';

async function run(src, failing, existingKeys) {
    const listeners = {};
    const store = { opened: [], cached: [], deleted: [], served: [] };
    mkCaches(failing, existingKeys, store);
    global.self = {
        addEventListener(type, fn) {
            (listeners[type] = listeners[type] || []).push(fn);
        },
        skipWaiting: () => Promise.resolve(),
        clients: { claim: () => Promise.resolve() },
        location: { origin: ORIGIN },
    };
    (0, eval)(src);
    const fire = async (type) => {
        let waited = null;
        for (const fn of listeners[type] || []) fn({ waitUntil: (p) => (waited = p) });
        if (waited) await waited;
    };
    let installOk = true;
    try {
        await fire('install');
    } catch (e) {
        installOk = false;
    }
    // 装失败时浏览器根本不会走到 activate,这里照样放一遍是故意的:activate 自己也得挡住
    // 「新缓存空着就把旧缓存清光」,不能只靠 install 那一道。
    await fire('activate');
    // fetch 那条路:SW 接管了才有机会 cache-first / 联网回填。没接管 = 这个 URL 永远进不了缓存。
    for (const path of [
        '/static/dist/scan.js',
        '/static/dist/barcode-detector.js',
        '/static/dist/zxing_reader.wasm',
        '/static/dist/zxing.js',
        '/api/pos/sales',
    ]) {
        let taken = false;
        for (const fn of listeners.fetch || []) {
            fn({
                request: { method: 'GET', url: ORIGIN + path + '?v=1' },
                respondWith: () => (taken = true),
            });
        }
        if (taken) store.served.push(path);
    }
    store.installOk = installOk;
    return store;
}

(async () => {
    const R = {};
    const src = {};
    const mine = {}; // SW 文件 → 它 install 时真开出来的缓存名
    for (const job of jobs) {
        src[job.name] = fs.readFileSync(job.path, 'utf8');
        R[job.name] = { ok: await run(src[job.name], [], []) };
        mine[job.name] = R[job.name].ok.opened[0];
    }
    for (const job of jobs) {
        const ok = R[job.name].ok;
        // 同一台机器上另外那个 SW 真会留下的缓存名 —— 取自它自己刚才 install 的产物,
        // 不在这里手打字符串(手打的名字改一次命名就悄悄失配,闸从此空转)。
        const others = jobs.filter((j) => j.name !== job.name).map((j) => mine[j.name]);
        // 自己这一族的上一版:上次部署留下的就长这样(版本号那截不同,前缀一样)。
        const ownStale = mine[job.name].replace(/[0-9]+$/, '0');
        Object.assign(R[job.name], {
            // 解码器 404(部署漏传 / CDN 还没热)时的表现
            flaky: await run(src[job.name], ok.cached.filter((u) => u.includes('scan.js')), []),
            // 换了版本号:自己这一族的旧缓存必须被清掉,当前这个和别人那一族都不许动。
            // 「别人那一族」是本条的要害:CacheStorage 按源共享,作用域拦不住 caches.delete()。
            evict: await run(src[job.name], [], [ownStale, ...others, mine[job.name]]),
            // 部署重启那十几秒 nginx 对外壳回 502,而这台机器里已经躺着一份上一版的缓存。
            // 上一轮只跑过「解码器 404 且 existingKeys 为空」——那两个条件恰好都躲开了这条路。
            shellDown: await run(src[job.name], [job.shell], [ownStale, ...others, mine[job.name]]),
        });
        R[job.name].siblings = others;
        R[job.name].ownStale = ownStale;
    }
    process.stdout.write(JSON.stringify(R));
})().catch((e) => {
    process.stderr.write(String((e && e.stack) || e));
    process.exit(1);
});
"""


def _pos_bundle_version() -> str:
    """页面上 dist bundle 的 ?v —— scan-loader.js 运行时就是从这里抠出懒加载 URL 的。"""
    html = (POS_DIR / "pos.html").read_text(encoding="utf-8")
    m = re.search(r"/static/dist/pos\.js\?v=(\d+)", html)
    assert m, "pos.html 里找不到 dist/pos.js?v= · 判据失效比断言失败更危险"
    return m.group(1)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过 SW 行为测试")
class PosSwPrecacheTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        jobs = [
            {"name": n, "path": str(POS_DIR / n), "shell": shell}
            for n, (shell, _) in WORKERS.items()
        ]
        proc = subprocess.run(
            ["node", "-e", NODE_HARNESS, "--", json.dumps(jobs)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            raise AssertionError("node 跑挂了:\n" + proc.stderr.decode("utf-8", "replace"))
        cls.r = json.loads(proc.stdout.decode("utf-8"))
        cls.v = _pos_bundle_version()

    def test_shell_is_precached(self):
        for name, (shell, _) in WORKERS.items():
            self.assertIn(shell, self.r[name]["ok"]["cached"], f"{name} 没预缓存外壳")

    def test_decoder_products_are_precached_so_offline_can_still_scan(self):
        # 收银台离线能卖货、扫码却拉不到解码器 = 断网时这台机器只剩一半。
        for name in WORKERS:
            for url in SCAN_PRODUCTS:
                self.assertTrue(
                    any(c.startswith(url) for c in self.r[name]["ok"]["cached"]),
                    f"{name}:{url} 没进 install 预缓存 · 断网就扫不了码",
                )

    def test_decoder_products_pass_the_fetch_allowlist(self):
        # cashier-sw 的 fetch 是白名单式的:不在名单里连联网那次的顺手回填都没有,
        # 预缓存万一失败就再没有第二次机会。
        for name in WORKERS:
            for url in SCAN_PRODUCTS:
                self.assertIn(url, self.r[name]["ok"]["served"], f"{name} 的 fetch 不接管 {url}")
            self.assertNotIn(
                "/api/pos/sales", self.r[name]["ok"]["served"], f"{name} 把 /api 也接管了"
            )

    def test_precached_urls_carry_the_same_fingerprint_the_page_asks_for(self):
        # 缓存按完整 URL 匹配。scan-loader.js 拼的是 <bundle>?v=<页面上的 v>,
        # SW 缓存别的 v 就是缓存了一条谁也不会请求的记录。
        for name in WORKERS:
            for url in SCAN_PRODUCTS:
                self.assertIn(f"{url}?v={self.v}", self.r[name]["ok"]["cached"])

    def test_cache_name_tracks_the_bundle_version(self):
        for name, (_, prefix) in WORKERS.items():
            self.assertEqual(self.r[name]["ok"]["opened"][0], f"{prefix}{self.v}")

    def test_a_missing_decoder_product_does_not_take_the_shell_down(self):
        # addAll 全有全无:把解码器混进外壳清单,一个 404 就让离线连收银台都开不了。
        for name, (shell, _) in WORKERS.items():
            flaky = self.r[name]["flaky"]
            self.assertTrue(flaky["installOk"], f"{name} 因为解码器 404 整个挂了")
            self.assertIn(shell, flaky["cached"], f"{name} 的外壳被 404 连累丢掉了")
            self.assertIn(f"/static/dist/zxing.js?v={self.v}", flaky["cached"])

    def test_activate_evicts_stale_versions_only(self):
        # 不清旧缓存 = 店里那台机器永远跑着旧 bundle,扫码功能压根不存在。
        for name in WORKERS:
            self.assertEqual(self.r[name]["evict"]["deleted"], [self.r[name]["ownStale"]])

    def test_neither_worker_deletes_the_other_ones_offline_shell(self):
        # 真机复现:开一次 /cashier → caches.keys() 从 ['pearnly-pos-v…'] 变成
        # ['pearnly-cashier-v…'],断网回 /pos 是 net::ERR_FAILED;反过来点一下老 /pos,
        # 断网开在用的收银台同样 ERR_FAILED —— 不是离线模式,是彻底打不开、货卖不了。
        # 判据的要害在 setUpClass 那边:两个 SW 的缓存键必须同时摆进 caches.keys(),
        # 而且用对方 install 时真开出来的名字。只放一个键时「删掉不是我的」永远无害。
        for name in WORKERS:
            siblings = self.r[name]["siblings"]
            self.assertTrue(siblings, "判据失效:另一个 SW 的缓存名没进这一轮的 caches.keys()")
            for other in siblings:
                for phase in ("evict", "shellDown"):
                    self.assertNotIn(
                        other,
                        self.r[name][phase]["deleted"],
                        f"{name}({phase})删掉了 {other} · 另一台机器的离线外壳被抹平",
                    )

    def test_cache_families_do_not_share_a_prefix(self):
        # 上一条靠前缀分家。两族前缀若互为前缀(pearnly-pos- / pearnly-pos-x)就又会互删,
        # 而那时上面那条仍然绿 —— 判据本身的前提得有人守。
        prefixes = [p for _, p in WORKERS.values()]
        for a in prefixes:
            for b in prefixes:
                if a is not b:
                    self.assertFalse(a.startswith(b), f"{a} 与 {b} 互为前缀 · 分不了家")

    def test_each_worker_really_opens_the_cache_name_its_family_claims(self):
        # 上面两条都建立在「这个 SW 的缓存名以 WORKERS 里那个前缀打头」上;SW 里改了命名而
        # 这里没跟着改,前缀过滤会一个都删不掉(缓存永远堆着),而那两条照样绿。
        for name, (_, prefix) in WORKERS.items():
            opened = self.r[name]["ok"]["opened"][0]
            self.assertTrue(opened.startswith(prefix), f"{name} 开的是 {opened},不在 {prefix} 一族")

    def test_a_502_on_the_shell_never_replaces_a_working_old_cache(self):
        # 本批 bump 了缓存名,而这条正好在部署自己那十几秒里触发:nginx 重启期间外壳回 502
        # → 旧代码 catch 里照样 skipWaiting → activate 无条件删光旧缓存、新缓存空的
        # → 此后断网打开就是浏览器网络错误页,不是「离线模式」,是彻底打不开、货卖不了。
        for name, (shell, _) in WORKERS.items():
            down = self.r[name]["shellDown"]
            self.assertNotIn(shell, down["cached"], "判据失效:这一档外壳本来就该拉不到")
            self.assertFalse(down["installOk"], f"{name}:外壳没落地,这版 SW 却装成功了")
            self.assertEqual(
                down["deleted"], [], f"{name}:新缓存空着就把旧缓存删了 · 离线外壳一次清零"
            )


class SwRegistrationFingerprintTests(unittest.TestCase):
    """注册 SW 那个 URL 上的指纹(static/pos/pos.js)。

    它此前写死成 `?v=11911102` 一直没人动,而外壳早发到 12043xxx —— 各造一套版本号必然漂,
    而漂了不报任何错。修法是让它跟着页面走(scan-loader.js 的 assetVersion() 抠的就是
    <script src="/static/dist/pos.js?v=">),所以这道闸盯的是「有没有人又写死一个数」。

    两个 SW 自己的 V 只能写死(SW 不进 bundle、读不到页面),那一份由上面
    test_cache_name_tracks_the_bundle_version 守。"""

    BUNDLED = tuple(p for p in sorted(POS_DIR.glob("*.js")) if not p.name.endswith("-sw.js"))

    def test_the_registration_url_is_built_from_the_page_fingerprint(self):
        src = (POS_DIR / "pos.js").read_text(encoding="utf-8")
        calls = re.findall(r"\.register\(([^;]*?),\s*\{", src, flags=re.S)
        # 一条都找不到时「没有写死的指纹」是空话 —— 闸得先证明自己看到了那次调用。
        self.assertEqual(
            len(calls), 1, f"pos.js 里的 serviceWorker.register 调用有 {len(calls)} 处"
        )
        self.assertNotRegex(calls[0], r"\?v=\d", "注册 URL 又写死了指纹 · 它不会跟着发版走")
        self.assertIn("swV", calls[0], "注册 URL 没带页面指纹")
        self.assertRegex(
            src,
            r"swV\s*=\s*\(window\.PearnlyScanCamera && window\.PearnlyScanCamera\.assetVersion\(\)\)",
        )

    def test_no_bundled_pos_source_hardcodes_an_asset_fingerprint(self):
        # 进 bundle 的文件都读得到页面上的 ?v,写死一个数就只有一个下场:漂。
        self.assertTrue(self.BUNDLED, "判据失效:一个被监控的源文件都没扫到")
        for path in self.BUNDLED:
            hits = re.findall(r"\?v=\d[\w.-]*", path.read_text(encoding="utf-8"))
            self.assertEqual(hits, [], f"{path.name} 里写死了资源指纹 {hits}")

    def test_cashier_registration_explicitly_checks_for_updates(self):
        src = (POS_DIR / "pos.js").read_text(encoding="utf-8")
        self.assertIn("updateViaCache: 'none'", src)
        self.assertIn(".then((registration) => registration.update())", src)


if __name__ == "__main__":
    unittest.main()
