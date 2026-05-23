/*
 * Pearnly · version-banner.js · v118.32.5.5.17
 * 实时新版本提示 · 独立 IIFE · 不引 home.js
 * 30 秒轮询 /api/version · 检测版本变化 → 顶部弹窗 · 4 语
 * 行为:
 *   - 首次拉到版本号 = baseline · 后续比对
 *   - 版本变化 → 显示 banner(top center · 不挡 sidebar)
 *   - [查看更新内容] → modal 显示 release_notes(4 语)
 *   - [现在刷新更新] → location.reload()
 *   - [稍后更新] → localStorage 存 30 分钟内不再弹同一版本
 */
(function _versionBannerIIFE() {
    'use strict';

    var POLL_INTERVAL = 30000; // 30 秒
    var SNOOZE_MS = 30 * 60 * 1000; // 30 分钟
    var LS_SNOOZE_KEY = 'pearnly_vb_snooze_until';
    var LS_SNOOZE_VER = 'pearnly_vb_snooze_version';
    var LS_LAST_SEEN = 'pearnly_vb_last_seen';

    var I18N = {
        zh: {
            title: 'Pearnly 新版本可用',
            view: '更新说明',
            refresh: '立即更新',
            later: '稍后',
            notesTitle: '更新说明',
            notesEmpty: '本次更新无说明',
            close: '关闭',
        },
        en: {
            title: 'Pearnly · new version available',
            view: 'Release notes',
            refresh: 'Update now',
            later: 'Later',
            notesTitle: 'Release notes',
            notesEmpty: 'No release notes for this version',
            close: 'Close',
        },
        th: {
            title: 'Pearnly · มีเวอร์ชันใหม่',
            view: 'รายละเอียดอัปเดต',
            refresh: 'อัปเดตเลย',
            later: 'ภายหลัง',
            notesTitle: 'รายละเอียดอัปเดต',
            notesEmpty: 'ไม่มีรายละเอียดสำหรับเวอร์ชันนี้',
            close: 'ปิด',
        },
        ja: {
            title: 'Pearnly · 新バージョン利用可能',
            view: 'リリースノート',
            refresh: '今すぐ更新',
            later: '後で',
            notesTitle: 'リリースノート',
            notesEmpty: 'このバージョンの更新内容はありません',
            close: '閉じる',
        },
    };

    function _curLang() {
        try {
            return localStorage.getItem('mrpilot_lang') || document.documentElement.lang || 'zh';
        } catch (_) {
            return 'zh';
        }
    }
    function _t(key) {
        var lang = _curLang();
        var dict = I18N[lang] || I18N.zh;
        return dict[key] || I18N.zh[key] || '';
    }

    function _injectStyle() {
        if (document.getElementById('vb-style')) return;
        var s = document.createElement('style');
        s.id = 'vb-style';
        s.textContent =
            '#vb-banner{position:fixed;top:14px;left:50%;transform:translateX(-50%);z-index:10001;background:#fff;border:1px solid #e8e8e3;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.12);padding:10px 12px 10px 16px;display:none;align-items:center;gap:12px;font-size:13px;color:#111;max-width:560px;width:calc(100% - 32px);font-family:inherit}' +
            '#vb-banner.show{display:flex}' +
            '#vb-banner-icon{flex-shrink:0;width:20px;height:20px;color:#111}' +
            '#vb-banner-text{flex:1;color:#111;font-weight:500}' +
            '#vb-banner-view{background:transparent;border:1px solid #e8e8e3;border-radius:6px;padding:5px 10px;font-size:12px;color:#555;cursor:pointer;font-family:inherit}' +
            '#vb-banner-view:hover{background:#f4f4f0;color:#111}' +
            '#vb-banner-refresh{background:#111;border:1px solid #111;border-radius:6px;padding:5px 12px;font-size:12px;color:#fff;font-weight:600;cursor:pointer;font-family:inherit}' +
            '#vb-banner-refresh:hover{background:#333}' +
            '#vb-banner-later{background:transparent;border:none;color:#999;cursor:pointer;font-size:16px;padding:2px 4px;line-height:1;font-family:inherit}' +
            '#vb-banner-later:hover{color:#111}' +
            '#vb-mask{position:fixed;inset:0;background:rgba(0,0,0,0.4);backdrop-filter:blur(3px);z-index:10002;display:none;align-items:center;justify-content:center;padding:20px}' +
            '#vb-mask.show{display:flex}' +
            '#vb-modal{background:#fff;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,0.25);max-width:520px;width:100%;max-height:80vh;overflow:auto;font-family:inherit}' +
            '#vb-modal-head{padding:16px 20px;border-bottom:1px solid #e8e8e3;display:flex;align-items:center;justify-content:space-between}' +
            '#vb-modal-title{font-size:15px;font-weight:700;color:#111}' +
            '#vb-modal-close{background:transparent;border:none;color:#999;cursor:pointer;font-size:20px;line-height:1;padding:2px 6px;font-family:inherit}' +
            '#vb-modal-close:hover{color:#111}' +
            '#vb-modal-body{padding:16px 20px;font-size:13px;color:#333;line-height:1.7;white-space:pre-wrap}' +
            '#vb-modal-foot{padding:12px 20px;border-top:1px solid #e8e8e3;display:flex;justify-content:flex-end;gap:8px}' +
            '@media (max-width:600px){#vb-banner{flex-wrap:wrap;gap:8px}#vb-banner-text{flex:1 0 100%;order:-1}}';
        document.head.appendChild(s);
    }

    function _renderBanner() {
        if (document.getElementById('vb-banner')) return;
        _injectStyle();
        var div = document.createElement('div');
        div.id = 'vb-banner';
        div.setAttribute('role', 'alert');
        div.innerHTML =
            '<svg id="vb-banner-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10a7 7 0 0 1 11.95-4.95M17 10a7 7 0 0 1-11.95 4.95"/><path d="M15 3v3h3"/><path d="M5 17v-3H2"/></svg>' +
            '<span id="vb-banner-text"></span>' +
            '<button id="vb-banner-view" type="button"></button>' +
            '<button id="vb-banner-refresh" type="button"></button>' +
            '<button id="vb-banner-later" type="button" aria-label="close">×</button>';
        document.body.appendChild(div);
        document.getElementById('vb-banner-view').addEventListener('click', _showModal);
        document.getElementById('vb-banner-refresh').addEventListener('click', function () {
            // v118.32.5.5.21 修 bug:点立即更新前 · 必须把 LS_LAST_SEEN 升到当前最新版本
            // 否则 reload 后 cur !== lastSeen → 弹窗又弹一次
            try {
                if (window._vbLatestVersion) {
                    localStorage.setItem(LS_LAST_SEEN, window._vbLatestVersion);
                }
                localStorage.removeItem(LS_SNOOZE_KEY);
                localStorage.removeItem(LS_SNOOZE_VER);
            } catch (_) {}
            location.reload();
        });
        document.getElementById('vb-banner-later').addEventListener('click', _snooze);
    }

    function _applyLangTexts() {
        var bt = document.getElementById('vb-banner-text');
        var bv = document.getElementById('vb-banner-view');
        var br = document.getElementById('vb-banner-refresh');
        if (bt) bt.textContent = _t('title');
        if (bv) bv.textContent = _t('view');
        if (br) br.textContent = _t('refresh');
        var mt = document.getElementById('vb-modal-title');
        var mc = document.getElementById('vb-modal-close');
        if (mt) mt.textContent = _t('notesTitle');
        if (mc) mc.setAttribute('aria-label', _t('close'));
    }

    function _showBanner() {
        _renderBanner();
        _applyLangTexts();
        var b = document.getElementById('vb-banner');
        if (b) b.classList.add('show');
    }
    function _hideBanner() {
        var b = document.getElementById('vb-banner');
        if (b) b.classList.remove('show');
    }
    function _snooze() {
        try {
            localStorage.setItem(LS_SNOOZE_KEY, String(Date.now() + SNOOZE_MS));
            if (window._vbLatestVersion)
                localStorage.setItem(LS_SNOOZE_VER, window._vbLatestVersion);
        } catch (_) {}
        _hideBanner();
    }

    function _showModal() {
        if (!document.getElementById('vb-mask')) {
            var mask = document.createElement('div');
            mask.id = 'vb-mask';
            mask.innerHTML =
                '<div id="vb-modal">' +
                '<div id="vb-modal-head"><div id="vb-modal-title"></div><button id="vb-modal-close" type="button">×</button></div>' +
                '<div id="vb-modal-body"></div>' +
                '<div id="vb-modal-foot"><button id="vb-modal-foot-close" class="btn" type="button" style="background:#111;color:#fff;border:none;border-radius:6px;padding:6px 14px;font-size:12px;cursor:pointer;font-family:inherit"></button></div>' +
                '</div>';
            document.body.appendChild(mask);
            var closeFn = function () {
                document.getElementById('vb-mask').classList.remove('show');
            };
            document.getElementById('vb-modal-close').addEventListener('click', closeFn);
            document.getElementById('vb-modal-foot-close').addEventListener('click', closeFn);
            mask.addEventListener('click', function (e) {
                if (e.target === mask) closeFn();
            });
        }
        var notes =
            (window._vbLatestNotes && window._vbLatestNotes[_curLang()]) ||
            (window._vbLatestNotes && window._vbLatestNotes.zh) ||
            _t('notesEmpty');
        document.getElementById('vb-modal-title').textContent = _t('notesTitle');
        document.getElementById('vb-modal-body').textContent = notes;
        document.getElementById('vb-modal-foot-close').textContent = _t('close');
        document.getElementById('vb-mask').classList.add('show');
    }

    function _isSnoozedFor(version) {
        try {
            var until = parseInt(localStorage.getItem(LS_SNOOZE_KEY) || '0', 10);
            var ver = localStorage.getItem(LS_SNOOZE_VER) || '';
            return until > Date.now() && ver === version;
        } catch (_) {
            return false;
        }
    }

    function _check() {
        fetch('/api/version', { cache: 'no-store' })
            .then(function (r) {
                return r.ok ? r.json() : null;
            })
            .then(function (j) {
                if (!j || !j.version) return;
                var cur = String(j.version);
                window._vbLatestVersion = cur;
                window._vbLatestNotes = j.release_notes || null;
                var lastSeen = '';
                try {
                    lastSeen = localStorage.getItem(LS_LAST_SEEN) || '';
                } catch (_) {}
                if (!lastSeen) {
                    // 首次启动 · 不弹 · 记 baseline
                    try {
                        localStorage.setItem(LS_LAST_SEEN, cur);
                    } catch (_) {}
                    return;
                }
                if (cur === lastSeen) return; // 版本未变
                // 版本已变 · 是否在 snooze 期内
                if (_isSnoozedFor(cur)) return;
                _showBanner();
            })
            .catch(function () {
                /* silent */
            });
    }

    // 切语言时同步更新已显示文本
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('version-banner', _applyLangTexts);
    } else {
        // 没有 subscribeI18n 也兜底监听切语言事件
        document.addEventListener('langChanged', _applyLangTexts);
    }

    // 启动
    function _start() {
        _check();
        setInterval(_check, POLL_INTERVAL);
        // 切回 tab 立即 check
        window.addEventListener('focus', _check);
        document.addEventListener('visibilitychange', function () {
            if (!document.hidden) _check();
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _start);
    } else {
        _start();
    }

    // 调试暴露
    window._versionBanner = {
        check: _check,
        show: _showBanner,
        hide: _hideBanner,
        snooze: _snooze,
        showModal: _showModal,
    };
})();
