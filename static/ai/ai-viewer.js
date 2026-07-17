/*
 * Pearnly AI · ai-viewer.js · 原件查看器(生产同款交互框架)
 *
 * 移植自 src/home/image-viewer.ts(采购「复核单据」票图查看器同款):滚轮缩放 0.4~6 倍 +
 * 拖拽平移 + 触摸单指平移/双指 pinch + 旋转 90° + 复位 + 全屏 + 实时百分比,原生 transform
 * 作用在 <img>。CSS 见 ai-viewer.css(.pv-* 结构 1:1,视觉换 ai-theme 暖纸令牌)。
 *
 * 与生产版两处差异(Pearnly AI 工单制原图端点是单图,非多页 PDF):
 *   ①图源不是 page.png——本模块不自己 fetch,调用方传 key + loader(loader 返回
 *     Promise<objectURL>);缓存/LRU 淘汰(revoke)统一放这里,mount 与 preload 共用
 *     同一份,不各造一份 blob 缓存。
 *   ②无 X-Page-Count,不做翻页器(生产版 pv-pager 在此整段删除)。
 *
 * 文案(loading/noimg/hint)由调用方传入,本模块不绑 i18n。UMD 同 ai-router.js/ai-api.js
 * 先例:浏览器挂 window.AI.viewer,node(测试)走 module.exports。
 */
(function (root) {
    'use strict';

    // 照 ai-format.js escHtml 的转发先例:AI.state.esc 已加载就转发,没加载(独立跑
    // node 单测)才退化——本文件不重复维护一份转义逻辑。
    function esc(s) {
        if (root && root.AI && root.AI.state && typeof root.AI.state.esc === 'function') {
            return root.AI.state.esc(s);
        }
        return String(s == null ? '' : s);
    }

    // key(调用方给,如 item_id)→ objectURL · 封顶 20 · 淘汰即 revoke(防 blob 无限驻留)。
    var cache = new Map();
    var pending = new Map();
    var MAX = 20;
    function put(key, url) {
        cache.set(key, url);
        if (cache.size > MAX) {
            var oldest = cache.keys().next().value;
            var u = cache.get(oldest);
            cache.delete(oldest);
            if (u && typeof URL !== 'undefined' && URL.revokeObjectURL) URL.revokeObjectURL(u);
        }
    }

    // 取图:命中缓存直接返回;同 key 并发请求合并(在飞 promise 复用,不重复调 loader)。
    // loader 失败一律回落 null(不抛给调用方,noimg 由调用方按 null 判定,状态诚实但不炸)。
    function loadUrl(key, loader) {
        if (key == null) return Promise.resolve(null);
        if (cache.has(key)) return Promise.resolve(cache.get(key));
        if (pending.has(key)) return pending.get(key);
        var p = Promise.resolve()
            .then(loader)
            .then(function (url) {
                pending.delete(key);
                if (url) put(key, url);
                return url || null;
            })
            .catch(function () {
                pending.delete(key);
                return null;
            });
        pending.set(key, p);
        return p;
    }

    // preload 与 mount 走同一条 loadUrl(共享缓存)——只是不接结果,纯预热。
    function preload(key, loader) {
        if (key != null) loadUrl(key, loader);
    }

    // 取景框适配倍率(S3 §8a):原生分辨率的图缩到正好铺满取景框,小图不放大(≤1)。
    // 非法尺寸(0/负,图未载或容器未布局)回 1,调用方按"无适配"处理。
    function computeFitScale(natW, natH, vpW, vpH) {
        if (!(natW > 0) || !(natH > 0) || !(vpW > 0) || !(vpH > 0)) return 1;
        return Math.min(vpW / natW, vpH / natH, 1);
    }

    // 平移量夹取(S3 §8b):保证图至少 40px 留在取景框内;缩放后比框还小的轴直接归 0
    // (小图不许拖丢)。2026-07-17 Zihao 实锤:全屏里拖出的平移量带回小窗,整张图停在
    // 框外像"没加载",刷新才回——退出全屏/每次 apply 都过这道夹取。
    function clampPan(tx, ty, imgW, imgH, scale, vpW, vpH) {
        var w = imgW * scale;
        var h = imgH * scale;
        var maxX = (w + vpW) / 2 - 40;
        var maxY = (h + vpH) / 2 - 40;
        return {
            tx: w < vpW ? 0 : Math.max(-maxX, Math.min(maxX, tx)),
            ty: h < vpH ? 0 : Math.max(-maxY, Math.min(maxY, ty)),
        };
    }

    // 同单跨张保持(S3 §8c):stateKey(调用方给,如工单 id)→ {scaleRel, rot}。
    // 缩放存相对 fit 的倍率(各张图分辨率不同,绝对 scale 不可比);平移是单张图的事,不存。
    var viewByKey = new Map();

    var I_PLUS =
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 5v14M5 12h14"/></svg>';
    var I_MINUS =
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12h14"/></svg>';
    var I_ROT =
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a9 9 0 11-2.6-6.4"/><path d="M21 4v4h-4"/></svg>';
    var I_RESET =
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 4H4v4M16 4h4v4M16 20h4v-4M8 20H4v-4"/></svg>';
    var I_FULL =
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>';

    // 挂载骨架(调用方 innerHTML 挂进去后再 mountViewer/remountViewer 接交互)。
    function imageViewerHtml(o) {
        o = o || {};
        return (
            '<div class="pv-viewer"><img class="pv-img" alt="">' +
            (o.hint ? '<span class="pv-hint">' + esc(o.hint) + '</span>' : '') +
            '<div class="pv-empty">' +
            esc(o.noimg) +
            '</div>' +
            '<div class="pv-loading"><span class="pv-spin"></span>' +
            esc(o.loading) +
            '</div>' +
            '<div class="pv-tools">' +
            '<span class="pv-zoom">100%</span>' +
            '<button data-z="in" type="button" title="+">' +
            I_PLUS +
            '</button>' +
            '<button data-z="out" type="button" title="-">' +
            I_MINUS +
            '</button>' +
            '<button data-z="rot" type="button" title="rotate">' +
            I_ROT +
            '</button>' +
            '<button data-z="reset" type="button" title="reset">' +
            I_RESET +
            '</button>' +
            '<button data-z="full" type="button" title="full">' +
            I_FULL +
            '</button></div></div>'
        );
    }

    function loadInto(vp, img, key, loader, alive) {
        if (key == null) {
            vp.classList.add('noimg');
            return;
        }
        vp.classList.remove('noimg');
        var cached = cache.get(key);
        if (cached) {
            img.src = cached;
            return;
        }
        vp.classList.add('loading');
        loadUrl(key, loader).then(function (url) {
            if (!alive()) return;
            vp.classList.remove('loading');
            if (url) img.src = url;
            else vp.classList.add('noimg');
        });
    }

    // 挂到一个含 .pv-viewer 的根元素 · 接拖拽/缩放/旋转/全屏 + 载入 opts.key 的图。
    // 返回 cleanup(解绑 window 监听);每实例状态独立(闭包,同生产版)。
    function mountViewer(rootEl, opts) {
        opts = opts || {};
        var vp = rootEl.querySelector('.pv-viewer');
        var img = rootEl.querySelector('.pv-img');
        var zl = rootEl.querySelector('.pv-zoom');
        if (!vp || !img) return function () {};

        var scale = 1;
        var fit = 1; // 取景框适配倍率(载图后 computeFitScale 算出;显示口径 fit=100%)
        var tx = 0;
        var ty = 0;
        var rot = 0;
        var drag = false;
        var sx = 0;
        var sy = 0;
        var alive = true;
        var clamp = function (v, a, b) {
            return Math.max(a, Math.min(b, v));
        };
        // 缩放上下界随 fit 走:下界 fit×0.4,上界允许放过原生 100% 一点(§8a)。
        var clampScale = function (v) {
            return clamp(v, fit * 0.4, Math.max(fit * 8, 1));
        };
        var apply = function () {
            var p = clampPan(
                tx,
                ty,
                img.naturalWidth,
                img.naturalHeight,
                scale,
                vp.clientWidth,
                vp.clientHeight
            );
            tx = p.tx;
            ty = p.ty;
            img.style.transform =
                'translate(calc(-50% + ' +
                tx +
                'px), calc(-50% + ' +
                ty +
                'px)) scale(' +
                scale +
                ') rotate(' +
                rot +
                'deg)';
            // 百分比相对 fit:载入即 100% = 正好铺满取景框(不是相对原生像素)。
            if (zl) zl.textContent = Math.round((scale / fit) * 100) + '%';
        };
        // 图层按原生分辨率栅格化(§8a):此前 CSS 把大图先压到布局尺寸再 transform 放大,
        // 小窗 547% 全是糊的;布局宽=naturalWidth,取景框适配交给 fit 倍率。换图重载重算。
        img.onload = function () {
            img.style.width = img.naturalWidth + 'px';
            img.style.height = 'auto';
            fit = computeFitScale(
                img.naturalWidth,
                img.naturalHeight,
                vp.clientWidth,
                vp.clientHeight
            );
            scale = fit;
            tx = 0;
            ty = 0;
            var saved = opts.stateKey != null ? viewByKey.get(opts.stateKey) : null;
            if (saved) {
                scale = fit * saved.scaleRel; // §8c:同单上一张的缩放感受带过来
                rot = saved.rot;
            }
            apply();
        };
        var onWheel = function (e) {
            e.preventDefault();
            scale = clampScale(scale * (e.deltaY < 0 ? 1.12 : 0.89));
            apply();
        };
        var onDown = function (e) {
            drag = true;
            sx = e.clientX - tx;
            sy = e.clientY - ty;
            vp.classList.add('grabbing');
        };
        var onMove = function (e) {
            if (!drag) return;
            tx = e.clientX - sx;
            ty = e.clientY - sy;
            apply();
        };
        var onUp = function () {
            drag = false;
            vp.classList.remove('grabbing');
        };
        // 触摸:单指平移 + 双指 pinch 缩放(原生 transform 不会自动缩放 <img>,须自处理)。
        var pinchDist = 0;
        var pinchScale = 1;
        var dist2 = function (tl) {
            return Math.hypot(tl[0].clientX - tl[1].clientX, tl[0].clientY - tl[1].clientY);
        };
        var onTStart = function (e) {
            if (e.touches.length === 2) {
                pinchDist = dist2(e.touches);
                pinchScale = scale;
            } else if (e.touches.length === 1) {
                drag = true;
                sx = e.touches[0].clientX - tx;
                sy = e.touches[0].clientY - ty;
            }
        };
        var onTMove = function (e) {
            if (e.touches.length === 2) {
                e.preventDefault();
                scale = clampScale(pinchScale * (dist2(e.touches) / (pinchDist || 1)));
                apply();
            } else if (drag && e.touches.length === 1) {
                e.preventDefault();
                tx = e.touches[0].clientX - sx;
                ty = e.touches[0].clientY - sy;
                apply();
            }
        };
        var onTEnd = function () {
            drag = false;
            pinchDist = 0;
        };
        var onTools = function (e) {
            var b = e.target.closest('.pv-tools button');
            if (!b) return;
            e.stopPropagation();
            var z = b.dataset.z;
            if (z === 'in') scale = clampScale(scale * 1.2);
            else if (z === 'out') scale = clampScale(scale / 1.2);
            else if (z === 'rot') rot += 90;
            else if (z === 'reset') {
                scale = fit; // 复位=回取景框适配态(显示 100%),不是原生 1:1
                tx = 0;
                ty = 0;
                rot = 0;
            } else if (z === 'full') {
                if (document.fullscreenElement) {
                    if (document.exitFullscreen) document.exitFullscreen();
                } else if (vp.requestFullscreen) vp.requestFullscreen();
                return;
            }
            apply();
        };
        // §8b:退出全屏时取景框骤然变小,全屏里拖出的 tx/ty 会把图整张推出框外——
        // 按小窗尺寸重跑 clampPan(apply 内建)把图拽回可见区。
        var onFsChange = function () {
            if (!document.fullscreenElement) apply();
        };
        vp.addEventListener('wheel', onWheel, { passive: false });
        vp.addEventListener('mousedown', onDown);
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);
        vp.addEventListener('touchstart', onTStart, { passive: false });
        vp.addEventListener('touchmove', onTMove, { passive: false });
        vp.addEventListener('touchend', onTEnd);
        vp.addEventListener('click', onTools);
        document.addEventListener('fullscreenchange', onFsChange);
        img.style.transformOrigin = 'center';
        apply();
        loadInto(vp, img, opts.key, opts.loader, function () {
            return alive;
        });

        return function cleanup() {
            alive = false;
            if (opts.stateKey != null && fit > 0) {
                viewByKey.set(opts.stateKey, { scaleRel: scale / fit, rot: rot });
            }
            document.removeEventListener('fullscreenchange', onFsChange);
            window.removeEventListener('mousemove', onMove);
            window.removeEventListener('mouseup', onUp);
        };
    }

    // 换卡/换单常见模式:先清同 mountKey 的旧实例,再挂新的(不留旧监听/旧闭包)。
    // pane 为空或未渲 .pv-viewer(如已跳走)= 只清不挂。
    var _mounts = new Map();
    function remountViewer(mountKey, pane, opts) {
        var prevCleanup = _mounts.get(mountKey);
        if (prevCleanup) prevCleanup();
        _mounts.delete(mountKey);
        if (pane && pane.querySelector('.pv-viewer')) {
            _mounts.set(mountKey, mountViewer(pane, opts || {}));
        }
    }

    var api = {
        imageViewerHtml: imageViewerHtml,
        mountViewer: mountViewer,
        remountViewer: remountViewer,
        loadUrl: loadUrl,
        preload: preload,
        computeFitScale: computeFitScale,
        clampPan: clampPan,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.viewer = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
