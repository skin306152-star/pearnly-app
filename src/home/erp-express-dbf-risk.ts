// ============================================================
// src/home/erp-express-dbf-risk.js · DBF 直写风险确认弹窗(brief P7)
//
// 录入方式选「直写数据 DBF」时弹出 · 克制但严肃(非吓人红屏)· 列要点 +
// 勾选「我已了解并接受风险」才激活「确认使用直写」。全站令牌 · 暗夜随令牌。
// 暴露 (window).ExpressDbfRisk.confirm(): Promise<boolean>。
// 全局桥:t / escapeHtml。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    function _esc(s: any) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function _t(k: string) {
        try {
            var v = typeof t === 'function' ? t(k) : k;
            return v || k;
        } catch (e) {
            return k;
        }
    }

    function openRisk(): Promise<boolean> {
        return new Promise(function (resolve) {
            var prev = document.getElementById('exp-dbf-overlay');
            if (prev) prev.remove();
            var points = ['exp-dbf-p1', 'exp-dbf-p2', 'exp-dbf-p3', 'exp-dbf-p4']
                .map(function (k) {
                    return '<div>· ' + _esc(_t(k)) + '</div>';
                })
                .join('');
            var ov = document.createElement('div');
            ov.id = 'exp-dbf-overlay';
            ov.className = 'exp-wiz-overlay';
            ov.innerHTML =
                '<div class="exp-risk-modal" role="dialog" aria-modal="true">' +
                '<div class="exp-wiz-title">' +
                _esc(_t('exp-dbf-risk-title')) +
                '</div>' +
                '<div class="exp-notice danger">' +
                _esc(_t('exp-dbf-risk-lead')) +
                '</div>' +
                '<div class="exp-risk-points">' +
                points +
                '</div>' +
                '<label class="exp-risk-ack"><input type="checkbox" id="exp-dbf-ack">' +
                '<span>' +
                _esc(_t('exp-dbf-risk-ack')) +
                '</span></label>' +
                '<div class="exp-wiz-footer"><button type="button" class="btn btn-ghost" id="exp-dbf-cancel">' +
                _esc(_t('exp-dbf-risk-back')) +
                '</button><div class="exp-wiz-foot-right">' +
                '<button type="button" class="btn btn-primary" id="exp-dbf-accept" disabled>' +
                _esc(_t('exp-dbf-risk-accept')) +
                '</button></div></div></div>';
            document.body.appendChild(ov);

            var done = function (val: boolean) {
                ov.remove();
                document.removeEventListener('keydown', onEsc);
                resolve(val);
            };
            var onEsc = function (e: KeyboardEvent) {
                if (e.key === 'Escape') done(false);
            };
            document.addEventListener('keydown', onEsc);
            ov.addEventListener('click', function (e) {
                var tg = e.target as HTMLElement;
                if (tg === ov || tg.closest('#exp-dbf-cancel')) return done(false);
                if (tg.closest('#exp-dbf-accept')) {
                    var ack = document.getElementById('exp-dbf-ack') as HTMLInputElement;
                    if (ack && ack.checked) done(true);
                }
            });
            ov.addEventListener('change', function (e) {
                var tg = e.target as HTMLElement;
                if (tg && tg.id === 'exp-dbf-ack') {
                    var btn = document.getElementById('exp-dbf-accept') as HTMLButtonElement;
                    if (btn) btn.disabled = !(tg as HTMLInputElement).checked;
                }
            });
        });
    }

    (window as any).ExpressDbfRisk = { confirm: openRisk };
})();
