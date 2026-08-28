/* Pearnly DMS · MR.ERP DMS 连接向导 + 设置页连接卡。
 * DMS 地址写死隐藏(只此一个实例),向导只维护一组有修改权限的账号密码。
 * 这组凭据同时用于连接、查重、建档和改写;销售人员仍用自己的账号匹配提成归属,需要改写
 * 客户档时由服务端继承老板的这组凭据。保存 adapter=mrerp_dms · auto_push=false,凭据明文
 * 只在本次请求内存在,路由经 KMS 加密后落地。挂 window.DXCONNECT +
 * window._mrerpDmsOpenWizard。 */
(function (root) {
    'use strict';
    var DEFAULT_URL = 'https://www.mrerp4sme.com/dms/index.php';
    var authHeaders = root.DXAPI.authHeaders;
    var _ep = null;
    var _hostSel = null;
    var _onSaved = null;

    function esc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(s == null ? '' : s)
            : String(s);
    }
    function t(k) {
        return typeof root.t === 'function' ? root.t(k) : k;
    }
    function toast(m, k) {
        if (typeof root.showToast === 'function') root.showToast(m, k || 'info');
    }

    function loadEndpoint(force) {
        return fetch('/api/erp/endpoints', { headers: authHeaders() })
            .then(function (r) {
                return r.ok ? r.json() : { items: [] };
            })
            .then(function (data) {
                var items = (data && data.items) || [];
                _ep =
                    items.find(function (e) {
                        return e && (e.adapter || '').toLowerCase() === 'mrerp_dms';
                    }) || null;
                return _ep;
            })
            .catch(function () {
                _ep = null;
                return null;
            });
    }

    function hasCredential(ep) {
        var cfg = (ep && ep.config) || {};
        return !!(
            (cfg.admin_username_enc && cfg.admin_password_enc) ||
            (cfg.username_enc && cfg.password_enc)
        );
    }

    // ── 设置页连接卡(复用向导上下文卡的 .dx-erp-* 视觉,不自创卡片体系) ──
    function renderCard() {
        var host = _hostSel && document.querySelector(_hostSel);
        if (!host) return;
        var configured = !!_ep;
        var enabled = configured ? _ep.enabled !== false : true;
        var status = !configured
            ? t('dms-card-not-connected')
            : enabled
              ? t('dms-card-connected')
              : t('dms-card-disabled-pill');
        var adminBadge =
            configured && hasCredential(_ep)
                ? '<span class="dx-badge blue" style="margin-left:6px">' +
                  esc(t('dms-card-admin-badge')) +
                  '</span>'
                : '';
        var acts = !configured
            ? '<button type="button" class="dx-erp-cta" id="btn-dms-connect">' +
              esc(t('dms-card-connect')) +
              '</button>'
            : '<button type="button" class="dx-erp-toggle" id="btn-dms-edit">' +
              esc(t('dms-card-edit')) +
              '</button><button type="button" class="dx-erp-toggle" id="btn-dms-test">' +
              esc(t('dms-card-test')) +
              '</button><button type="button" class="dx-erp-toggle" id="btn-dms-toggle">' +
              esc(t(enabled ? 'dms-card-disable' : 'dms-card-enable')) +
              '</button>';
        host.innerHTML =
            '<div class="dmsx"><div class="dx-erp-card' +
            (configured && enabled ? ' is-connected' : '') +
            (configured && !enabled ? ' is-disabled' : '') +
            '"><div class="dx-erp-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="22" height="22"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2.1"/><path d="M6 16c.7-1.4 1.9-2.1 3-2.1s2.3.7 3 2.1M14 10h4M14 14h4"/></svg></div>' +
            '<div class="dx-erp-info"><b>' +
            esc(t('dms-card-title')) +
            '</b><span class="dx-erp-status">' +
            esc(status) +
            '</span>' +
            adminBadge +
            '</div><div class="dx-erp-acts">' +
            acts +
            '</div></div></div>';
    }

    // ── 向导弹窗 ──
    function closeWizard() {
        var ov = document.getElementById('dms-wizard-overlay');
        if (ov) ov.remove();
        document.removeEventListener('keydown', onEsc);
    }
    function onEsc(e) {
        if (e.key === 'Escape') closeWizard();
    }
    function wizErr(msg) {
        var el = document.getElementById('dms-w-err');
        if (el) {
            el.textContent = msg || '';
            el.style.display = msg ? '' : 'none';
        }
    }
    function field(labelKey, id, type, value, ph) {
        return (
            '<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--ink2);margin-bottom:5px;">' +
            esc(t(labelKey)) +
            '</span><input id="' +
            id +
            '" type="' +
            type +
            '" value="' +
            esc(value || '') +
            '" placeholder="' +
            esc(ph || '') +
            '" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line);border-radius:8px;font-size:14px;background:var(--card);color:var(--ink);"></label>'
        );
    }
    function credentialFieldsHtml() {
        var configured = hasCredential(_ep);
        var ph = configured ? t('dms-wizard-admin-configured') : '';
        return (
            '<div style="margin:6px 0 14px;padding-top:14px;border-top:1px solid var(--line);">' +
            '<div style="font-size:13px;font-weight:700;color:var(--ink);margin-bottom:3px;">' +
            esc(t('dms-wizard-admin-title')) +
            '</div><div style="font-size:11px;color:var(--ink2);margin-bottom:12px;line-height:1.5;">' +
            esc(t('dms-wizard-admin-desc')) +
            '</div>' +
            field('dms-wizard-admin-user', 'dms-w-admin-user', 'text', '', ph) +
            field('dms-wizard-admin-pass', 'dms-w-admin-pass', 'password', '', ph) +
            '</div>'
        );
    }
    function openWizard() {
        closeWizard();
        var ov = document.createElement('div');
        ov.id = 'dms-wizard-overlay';
        ov.style.cssText =
            'position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;';
        ov.innerHTML =
            '<div class="dms-wizard" role="dialog" aria-modal="true" style="background:var(--card);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;">' +
            '<div style="font-size:17px;font-weight:700;margin-bottom:4px;color:var(--ink);">' +
            esc(t('dms-wizard-title')) +
            '</div><div style="font-size:13px;color:var(--ink2);margin-bottom:18px;">' +
            esc(t('dms-card-desc')) +
            '</div>' +
            credentialFieldsHtml() +
            '<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div>' +
            '<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn" id="dms-w-cancel">' +
            esc(t('dms-wizard-cancel')) +
            '</button><button type="button" class="btn primary" id="dms-w-save">' +
            esc(t('dms-wizard-save')) +
            '</button></div></div>';
        document.body.appendChild(ov);
        document.addEventListener('keydown', onEsc);
        ov.addEventListener('click', function (e) {
            if (e.target === ov) closeWizard();
        });
        var userEl = document.getElementById('dms-w-admin-user');
        if (userEl) userEl.focus();
    }

    function saveWizard() {
        // DMS 地址写死(界面隐藏)· 编辑态沿用已存 system_url,新建用 DEFAULT_URL。
        var url = ((_ep && _ep.config && _ep.config.system_url) || DEFAULT_URL).trim();
        var user = (val('dms-w-admin-user') || '').trim();
        var pass = val('dms-w-admin-pass') || '';
        var enteredPair = !!(user && pass);
        if (!url || (!enteredPair && (!hasCredential(_ep) || user || pass))) {
            return wizErr(t('dms-wizard-required'));
        }
        var saveBtn = document.getElementById('dms-w-save');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = t('dms-wizard-saving');
        }
        wizErr('');
        // 新凭据走明文内存测试;编辑时两项都留空则测试服务端已保存的密文,不回传秘密。
        var testPath = enteredPair
            ? '/api/erp/test-connection'
            : '/api/erp/endpoints/' + encodeURIComponent(_ep.id) + '/test-connection?refresh=1';
        var testOptions = { method: 'POST', headers: authHeaders(enteredPair) };
        if (enteredPair) {
            testOptions.body = JSON.stringify({
                adapter: 'mrerp_dms',
                config: { system_url: url, username: user, password: pass },
            });
        }
        fetch(testPath, testOptions)
            .then(function (tr) {
                return tr
                    .json()
                    .catch(function () {
                        return {};
                    })
                    .then(function (td) {
                        return { ok: tr.ok, data: td };
                    });
            })
            .then(function (res) {
                if (!res.ok || !res.data.ok) {
                    var fr =
                        (res.data.error_friendly &&
                            (res.data.error_friendly[root.DXI18N && root.DXI18N.lang] ||
                                res.data.error_friendly.en)) ||
                        t('dms-connect-fail-generic');
                    resetSaveBtn(saveBtn);
                    return wizErr(fr);
                }
                // 2) 保存端点。新输入同时写入主凭据和管理员凭据;后端也会再次归一兜底。
                var cfg = { system_url: url };
                if (enteredPair) {
                    cfg.username_enc = user;
                    cfg.password_enc = pass;
                    cfg.admin_username_enc = user;
                    cfg.admin_password_enc = pass;
                }
                var method = _ep && _ep.id ? 'PATCH' : 'POST';
                var path =
                    _ep && _ep.id
                        ? '/api/erp/endpoints/' + encodeURIComponent(_ep.id)
                        : '/api/erp/endpoints';
                var body =
                    method === 'POST'
                        ? {
                              name: 'MR.ERP DMS',
                              adapter: 'mrerp_dms',
                              config: cfg,
                              is_default: false,
                              auto_push: false,
                          }
                        : { config: cfg, auto_push: false };
                return fetch(path, {
                    method: method,
                    headers: authHeaders(true),
                    body: JSON.stringify(body),
                }).then(function (sr) {
                    if (!sr.ok) {
                        return sr
                            .json()
                            .catch(function () {
                                return {};
                            })
                            .then(function (sd) {
                                var code =
                                    (sd && sd.detail && (sd.detail.code || sd.detail)) ||
                                    'save_failed';
                                resetSaveBtn(saveBtn);
                                wizErr(t('dms-save-fail') + ' (' + esc(String(code)) + ')');
                                throw new Error('save_failed');
                            });
                    }
                    closeWizard();
                    toast(t('dms-connect-ok'), 'success');
                    return loadEndpoint(true).then(function () {
                        renderCard();
                        if (typeof _onSaved === 'function') _onSaved();
                    });
                });
            })
            .catch(function (e) {
                if (e && e.message === 'save_failed') return;
                resetSaveBtn(saveBtn);
                wizErr(t('dms-connect-fail-generic'));
            });
    }
    function resetSaveBtn(btn) {
        if (btn) {
            btn.disabled = false;
            btn.textContent = t('dms-wizard-save');
        }
    }
    function val(id) {
        var el = document.getElementById(id);
        return el ? el.value : '';
    }

    function testSaved() {
        if (!_ep || !_ep.id) return;
        toast(t('dms-test-running'), 'info');
        fetch('/api/erp/endpoints/' + encodeURIComponent(_ep.id) + '/test-connection?refresh=1', {
            method: 'POST',
            headers: authHeaders(),
        })
            .then(function (r) {
                return r.json().catch(function () {
                    return {};
                });
            })
            .then(function (d) {
                toast(
                    d && d.ok ? t('dms-test-ok') : t('dms-test-fail'),
                    d && d.ok ? 'success' : 'error'
                );
            })
            .catch(function () {
                toast(t('dms-test-fail'), 'error');
            });
    }

    function toggleEnabled() {
        if (!_ep || !_ep.id) return;
        var enabling = _ep.enabled === false;
        var pre = !enabling ? root.pearnlyConfirm(t('dms-confirm-disable')) : Promise.resolve(true);
        pre.then(function (ok) {
            if (!ok) return;
            fetch('/api/erp/endpoints/' + encodeURIComponent(_ep.id), {
                method: 'PATCH',
                headers: authHeaders(true),
                body: JSON.stringify({ enabled: enabling }),
            })
                .then(function (r) {
                    if (!r.ok) throw new Error('http_' + r.status);
                    toast(enabling ? t('dms-enabled-toast') : t('dms-disabled-toast'), 'success');
                    return loadEndpoint(true).then(renderCard);
                })
                .catch(function () {
                    toast(t('dms-save-fail'), 'error');
                });
        });
    }

    // 设置页 click 委托(挂一次)· 按钮 id 与主站保持一致。
    var wired = false;
    function wireOnce() {
        if (wired) return;
        wired = true;
        document.addEventListener('click', function (ev) {
            var tg = ev.target;
            if (tg.closest('#btn-dms-connect') || tg.closest('#btn-dms-edit')) {
                ev.preventDefault();
                openWizard();
            } else if (tg.closest('#dms-w-cancel')) {
                ev.preventDefault();
                closeWizard();
            } else if (tg.closest('#dms-w-save')) {
                ev.preventDefault();
                saveWizard();
            } else if (tg.closest('#btn-dms-test')) {
                ev.preventDefault();
                testSaved();
            } else if (tg.closest('#btn-dms-toggle')) {
                ev.preventDefault();
                toggleEnabled();
            }
        });
    }

    // 设置页挂载入口:host 选择器容纳连接卡。
    function mount(hostSel) {
        _hostSel = hostSel;
        wireOnce();
        loadEndpoint(true).then(renderCard);
    }

    // 向导上下文卡入口(dms-intake-erp-cards.js 的「配置」按钮)· DMS SPA 里这是向导
    // 唯一开口(mount() 只服务主站设置页,本 SPA 从不调用它)· 之前漏了 wireOnce() ·
    // 保存/取消/测试/启停四个按钮的委托点击从未挂上 → 向导「连接并保存」在 /dms 里点了
    // 没反应(真浏览器验收 DL-4b 撞见 · wireOnce() 幂等,补调不影响主站设置页路径)。
    root._mrerpDmsOpenWizard = function (ep, onSaved) {
        _onSaved = onSaved || null;
        _ep = ep || _ep;
        wireOnce();
        loadEndpoint(false).then(openWizard);
    };

    if (typeof root.subscribeI18n === 'function') root.subscribeI18n('dms-connect', renderCard);
    root.DXCONNECT = { mount: mount };
})(typeof self !== 'undefined' ? self : this);
