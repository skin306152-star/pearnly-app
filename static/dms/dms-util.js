/* Pearnly DMS · 壳内共享全局(供移植自主站的身份证向导直接调用,不改其调用点)。
 * 主站里这些是散落全局(escapeHtml/showToast/pearnlyConfirm/subscribeI18n/t);独立壳
 * 把它们收在这一处最小实现。t 直指 dt(DMS 词典),向导代码里的 t('dx-*') 原样可用。 */
(function () {
    'use strict';

    function escapeHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
    window.escapeHtml = escapeHtml;

    // t():向导代码全程用 t(),这里指向 DMS 词典 dt()。语言由 dms-i18n.js 维护。
    window.t = function (key, vars) {
        return typeof window.dt === 'function' ? window.dt(key, vars) : key;
    };

    // 轻量 toast(四态提示复用):顶部居中,自动消隐。error/warn/success/info 配色。
    var toastTimer = null;
    window.showToast = function (msg, kind) {
        var host = document.getElementById('dms-toast');
        if (!host) {
            host = document.createElement('div');
            host.id = 'dms-toast';
            document.body.appendChild(host);
        }
        host.className = 'dms-toast show ' + (kind || 'info');
        host.textContent = msg || '';
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            host.className = 'dms-toast';
        }, 3200);
    };

    // pearnlyConfirm():体系内确认模态(遮罩 + 卡片 + 取消/确定)· 替代原生 confirm。
    // 原生弹窗违反全站弹窗硬闸(裸系统样式、无法主题/i18n)· 这里自建轻量壳,视觉沿用
    // 向导的遮罩/卡片令牌 + .btn/.btn.primary。返回 Promise<bool>,调用点(dms-connect /
    // dms-intake-erp-cards 的停用确认)不改。msg 为已本地化文案,title 缺省用 dms-confirm-title。
    window.pearnlyConfirm = function (msg, title) {
        return new Promise(function (resolve) {
            var prev = document.getElementById('dms-confirm-overlay');
            if (prev) prev.remove();
            var dt = window.dt;
            var tt =
                title || (typeof dt === 'function' ? dt('dms-confirm-title') : 'Please confirm');
            var okT = typeof dt === 'function' ? dt('dms-confirm-ok') : 'OK';
            var cancelT = typeof dt === 'function' ? dt('dms-confirm-cancel') : 'Cancel';
            var ov = document.createElement('div');
            ov.id = 'dms-confirm-overlay';
            ov.style.cssText =
                'position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);' +
                'display:flex;align-items:center;justify-content:center;padding:16px;';
            ov.innerHTML =
                '<div class="dms-confirm-card" role="dialog" aria-modal="true" style="background:var(--card);' +
                'border-radius:14px;width:min(400px,100%);padding:22px 24px;color:var(--ink);' +
                'box-shadow:0 12px 40px rgba(0,0,0,.18);">' +
                '<div style="font-size:16px;font-weight:700;margin-bottom:8px;">' +
                escapeHtml(tt) +
                '</div><div style="font-size:14px;color:var(--ink2);line-height:1.5;margin-bottom:18px;">' +
                escapeHtml(msg || '') +
                '</div><div style="display:flex;gap:10px;justify-content:flex-end;">' +
                '<button type="button" class="btn" id="dms-confirm-cancel">' +
                escapeHtml(cancelT) +
                '</button><button type="button" class="btn primary" id="dms-confirm-ok">' +
                escapeHtml(okT) +
                '</button></div></div>';
            document.body.appendChild(ov);
            function done(result) {
                ov.remove();
                document.removeEventListener('keydown', onKey);
                resolve(result);
            }
            function onKey(e) {
                if (e.key === 'Escape') done(false);
                else if (e.key === 'Enter') done(true);
            }
            ov.querySelector('#dms-confirm-ok').addEventListener('click', function () {
                done(true);
            });
            ov.querySelector('#dms-confirm-cancel').addEventListener('click', function () {
                done(false);
            });
            ov.addEventListener('click', function (e) {
                if (e.target === ov) done(false);
            });
            document.addEventListener('keydown', onKey);
            var cancelEl = ov.querySelector('#dms-confirm-cancel');
            if (cancelEl) cancelEl.focus(); // 焦点落取消,防误触确定
        });
    };

    // subscribeI18n():向导/连接卡注册语言变更回调。壳顶栏切语言后统一触发一次。
    var subs = {};
    window.subscribeI18n = function (name, cb) {
        if (typeof cb === 'function') subs[name] = cb;
    };
    window._dmsRunI18n = function () {
        Object.keys(subs).forEach(function (k) {
            try {
                subs[k]();
            } catch (e) {
                /* 单个订阅者出错不阻断其余重渲 */
            }
        });
    };
})();
