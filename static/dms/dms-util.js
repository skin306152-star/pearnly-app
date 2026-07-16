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

    // pearnlyConfirm():停用端点前的确认。原生 confirm 阻塞但语义诚实,停用是低频操作。
    window.pearnlyConfirm = function (msg) {
        return Promise.resolve(window.confirm(msg));
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
