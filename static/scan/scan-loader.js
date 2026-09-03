/*
 * Pearnly · scan-loader.js · 扫码引擎的常驻门面(首屏这层只有它和 scan-wedge.js)
 *
 * 为什么拆出这么薄一层:摄像头解码那套(scan-camera + shim → static/dist/scan.js)
 * 和 WASM 兜底都是「店员真的点了扫码」才用得上的东西,压进首屏
 * bundle 等于让每次开机都为一个未必会用到的功能付流量。但「能不能扫」这个判断必须在首屏
 * 就能回答 —— 按钮显不显示、显示了点下去该说什么,都靠它。
 *
 * 于是本文件先把 window.PearnlyScanCamera 建成一个只有能力探针 + 懒加载入口的壳:
 *   isSupported() / unsupportedReason()  首屏可答,不拉任何字节
 *   ensureLoaded()                       真要扫了才拉 dist/scan.js,scan-camera.js 往同一个
 *                                        对象上补 create(),调用方拿到的仍是这一个全局
 * 拿 window.PearnlyScanCamera.create 判断有没有加载过,不另设标志位(单一事实源)。
 */
(function (root) {
    'use strict';

    var doc = root && root.document;

    // 懒加载 URL 的 ?v 从页面上 dist bundle 的 ?v 抠 —— 与 src/home/asset-fingerprint.ts 同一
    // 招法。各造一套版本号必然漂,而 CDN 只按 URL 缓存:URL 不变,文件换了也永远发旧的
    // (2026-07-26 教程 JSON 真事故)。抠不到就不挂 ?v,别用空值污染 URL。
    function assetVersion() {
        if (!doc) return '';
        var tags = doc.querySelectorAll('script[src*="/static/dist/"]');
        for (var i = 0; i < tags.length; i++) {
            var m = tags[i].src.match(/[?&]v=([^&]+)/);
            if (m) return m[1];
        }
        return '';
    }

    function versioned(url) {
        var v = assetVersion();
        return v ? url + (url.indexOf('?') >= 0 ? '&' : '?') + 'v=' + v : url;
    }

    var pending = {};

    // 同源 <script> 注入(CSP script-src 'self' 下唯一可行的动态加载法)。
    // 同一 URL 并发调用共享同一个 Promise;失败时清掉记录,让重试按钮真的能重试。
    function loadScript(url) {
        if (pending[url]) return pending[url];
        pending[url] = new Promise(function (resolve, reject) {
            if (!doc) {
                reject(new Error('no document'));
                return;
            }
            var el = doc.createElement('script');
            el.src = versioned(url);
            el.async = true;
            el.onload = function () {
                resolve();
            };
            el.onerror = function () {
                delete pending[url];
                el.remove();
                reject(new Error('load failed: ' + url));
            };
            (doc.head || doc.documentElement).appendChild(el);
        });
        return pending[url];
    }

    // 能力探针分三档,对应三种完全不同的话术(见 unsupportedReason)。
    // Odoo 的坑:它在非 HTTPS 下让扫码按钮静默消失,店员只觉得「功能没了」。
    function unsupportedReason() {
        // 只有明确 false 才判不安全上下文:老浏览器/node 里 isSecureContext 是 undefined,
        // 把「读不到」当「不安全」会在能扫的机器上把功能关掉。
        if (root && root.isSecureContext === false) return 'insecure_context';
        var md = root && root.navigator && root.navigator.mediaDevices;
        if (!md || !md.getUserMedia) return 'no_camera_api';
        return null;
    }

    function isSupported() {
        return unsupportedReason() === null;
    }

    var CAMERA_BUNDLE = '/static/dist/scan.js';

    // 幂等:重复调用不会重复注入,加载失败可以直接再调一次(loadScript 已清掉失败记录)。
    function ensureLoaded() {
        var api = root.PearnlyScanCamera;
        if (api && typeof api.create === 'function') return Promise.resolve(api);
        return loadScript(CAMERA_BUNDLE).then(function () {
            var loaded = root.PearnlyScanCamera;
            if (!loaded || typeof loaded.create !== 'function') {
                throw new Error('scan.js loaded but create() missing');
            }
            return loaded;
        });
    }

    var shell = {
        assetVersion: assetVersion,
        assetUrl: versioned,
        loadScript: loadScript,
        ensureLoaded: ensureLoaded,
        isSupported: isSupported,
        unsupportedReason: unsupportedReason,
    };

    if (typeof module !== 'undefined' && module.exports) module.exports = shell;
    if (root) {
        // scan.js 后到,往同一个对象上补 create();壳的方法不被覆盖。
        root.PearnlyScanCamera = root.PearnlyScanCamera || {};
        for (var k in shell) {
            if (Object.prototype.hasOwnProperty.call(shell, k))
                root.PearnlyScanCamera[k] = shell[k];
        }
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
