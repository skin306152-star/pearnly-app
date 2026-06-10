/* 管理控制台 SPA(权限批3 · docs/permissions/04 屏1/2/3)。
   纯 plain-script,照 /pos 套路:boot 先验登录态 + can(team.member.view),
   不过 → 403 人话页;错误码经 console-i18n 翻 4 语,不裸露。 */
(function () {
    'use strict';
    var ICON_CROWN =
        '<svg class="crown" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11.56 3.27a.5.5 0 0 1 .88 0l2.95 5.6a1 1 0 0 0 1.52.3l4.27-3.67a.5.5 0 0 1 .8.52l-2.83 10.25a1 1 0 0 1-.96.73H5.81a1 1 0 0 1-.96-.73L2.02 6.02a.5.5 0 0 1 .8-.52l4.28 3.67a1 1 0 0 0 1.51-.3z"/></svg>';
    var ICON_MAIL =
        '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>';
    var BRAND_HTML =
        '<div class="brand"><img class="brand-icon" src="/static/brand/pwa-icon-192.png?v=1" alt="Pearnly"> Pearnly Console</div>';
    var S = {
        token: null,
        perms: [],
        roleKey: '',
        members: [],
        invites: [],
        roles: [],
        ws: [],
        seatsMax: 0,
        secLoaded: false,
        expanded: null,
    };
    // 角色「使用权」芯片(PEAK 吸收):业务模块逐个上色,管理类权限组并成一枚
    var MOD_ORDER = [
        'sales',
        'purchase',
        'acct',
        'tax',
        'recon',
        'ar',
        'inv',
        'pos',
        'kb',
        'intake',
    ];
    var ADMIN_GROUPS = ['team', 'settings', 'billing', 'audit', 'ownership'];
    var $ = function (id) {
        return document.getElementById(id);
    };
    var esc = function (s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    };

    function api(method, path, body) {
        return fetch(path, {
            method: method,
            headers: Object.assign(
                { Authorization: 'Bearer ' + S.token },
                body ? { 'Content-Type': 'application/json' } : {}
            ),
            body: body ? JSON.stringify(body) : undefined,
        }).then(function (r) {
            return r
                .json()
                .catch(function () {
                    return {};
                })
                .then(function (j) {
                    if (!r.ok)
                        throw {
                            status: r.status,
                            code: j.detail || (j.error && j.error.code) || 'generic',
                        };
                    return j;
                });
        });
    }
    function errMsg(e) {
        var code = e && e.code;
        // pydantic 校验 422 的 detail 是数组/对象 · 统一翻「输入格式不对」(同 invite.js)
        if (Array.isArray(code) || (code && typeof code === 'object')) code = 'invalid_input';
        var key = 'err_' + String(code || 'generic').replace(/\./g, '_');
        var s = ct(key);
        return s === key ? ct('err_generic') : s;
    }
    function toast(msg) {
        var el = $('toast');
        el.textContent = msg;
        el.classList.add('show');
        setTimeout(function () {
            el.classList.remove('show');
        }, 2200);
    }
    function can(code) {
        return S.perms.indexOf('*') >= 0 || S.perms.indexOf(code) >= 0;
    }
    function roleName(k) {
        return ct('role_' + k);
    }
    function roleGroups(key) {
        var r = S.roles.find(function (x) {
            return x.key === key;
        });
        return (r && r.permission_groups) || [];
    }
    function modChips(groups) {
        groups = groups || [];
        var html = MOD_ORDER.filter(function (g) {
            return groups.indexOf(g) >= 0;
        })
            .map(function (g) {
                return '<span class="modchip mod-' + g + '">' + ct('mod_' + g) + '</span>';
            })
            .join('');
        if (
            ADMIN_GROUPS.some(function (g) {
                return groups.indexOf(g) >= 0;
            })
        )
            html += '<span class="modchip mod-admin">' + ct('mod_admin') + '</span>';
        return html ? '<div class="modchips">' + html + '</div>' : '';
    }
    function roleCardHtml(r, on) {
        return (
            '<div class="rolecard' +
            (on ? ' on' : '') +
            '" data-role="' +
            r.key +
            '"><div class="rn">' +
            roleName(r.key) +
            '<span class="rc-count">' +
            ct('rc_inuse', { n: r.member_count || 0 }) +
            '</span></div><div class="rd">' +
            ct('roledesc_' + r.key) +
            '</div>' +
            modChips(r.permission_groups) +
            '</div>'
        );
    }
    function applyTexts() {
        document.querySelectorAll('[data-ct]').forEach(function (el) {
            el.textContent = ct(el.getAttribute('data-ct'));
        });
    }

    // ── 鉴权前置三态
    function gate(html) {
        $('gateView').style.display = 'grid';
        $('appShell').style.display = 'none';
        $('gateCard').innerHTML = BRAND_HTML + html;
    }
    function gateNeedLogin() {
        gate(
            '<h1>' +
                ct('need_login') +
                '</h1><div class="sub"></div><a class="btn pri" href="/login">' +
                ct('goto_login') +
                '</a>'
        );
    }
    function gateForbidden() {
        gate(
            '<h1>' +
                ct('forbidden_title') +
                '</h1><div class="sub">' +
                ct('forbidden_sub') +
                '</div><a class="btn sec" href="/home">' +
                ct('nav_back') +
                '</a>'
        );
    }

    function boot() {
        if (localStorage.getItem('console_dark') === '1')
            document.documentElement.classList.add('dark');
        applyTexts();
        var langSeg = $('langSeg');
        function syncLangSeg() {
            langSeg.querySelectorAll('b').forEach(function (b) {
                b.classList.toggle('on', b.getAttribute('data-lang') === window.CI18N.lang);
            });
        }
        syncLangSeg();
        langSeg.querySelectorAll('b').forEach(function (b) {
            b.onclick = function () {
                ctSetLang(b.getAttribute('data-lang'));
                syncLangSeg();
                applyTexts();
                renderAll();
            };
        });
        $('darkToggle').onclick = function () {
            var on = document.documentElement.classList.toggle('dark');
            localStorage.setItem('console_dark', on ? '1' : '0');
        };
        document.querySelectorAll('[data-close]').forEach(function (b) {
            b.onclick = function () {
                $(b.getAttribute('data-close')).classList.remove('open');
            };
        });
        document.querySelectorAll('.sb a[data-view]').forEach(function (a) {
            a.onclick = function () {
                switchView(a.getAttribute('data-view'));
            };
        });
        $('btnInvite').onclick = openInvite;
        $('btnHaveToken').onclick = openTransferAccept;

        S.token = localStorage.getItem('mrpilot_token');
        if (!S.token) return gateNeedLogin();
        api('GET', '/api/me/permissions')
            .then(function (j) {
                S.perms = (j.data && j.data.permissions) || [];
                S.roleKey = (j.data && j.data.role_key) || '';
                if (!can('team.member.view')) return gateForbidden();
                $('gateView').style.display = 'none';
                $('appShell').style.display = 'grid';
                loadAll();
            })
            .catch(function (e) {
                if (e.status === 401) return gateNeedLogin();
                gate(
                    '<h1>' +
                        ct('load_fail') +
                        '</h1><div class="sub"></div><button class="btn sec" onclick="location.reload()">' +
                        ct('retry') +
                        '</button>'
                );
            });
    }

    function switchView(v) {
        document.querySelectorAll('.sb a[data-view]').forEach(function (a) {
            a.classList.toggle('on', a.getAttribute('data-view') === v);
        });
        $('view-members').style.display = v === 'members' ? '' : 'none';
        $('view-security').style.display = v === 'security' ? '' : 'none';
        if (v === 'security' && !S.secLoaded) loadSecurity();
    }

    function loadAll() {
        $('membersBox').innerHTML =
            '<div class="card"><div class="skeleton"><i></i><i></i><i></i></div></div>';
        Promise.all([
            api('GET', '/api/team/members'),
            api('GET', '/api/team/invitations'),
            api('GET', '/api/team/roles'),
            api('GET', '/api/workspace/clients'),
        ])
            .then(function (rs) {
                S.members = rs[0].members || [];
                S.seatsMax = rs[0].seats_max || 0;
                S.invites = rs[1].invitations || [];
                S.roles = rs[2].roles || [];
                S.ws = rs[3].clients || [];
                renderAll();
            })
            .catch(function () {
                $('membersBox').innerHTML =
                    '<div class="empty"><div class="e1">' +
                    ct('load_fail') +
                    '</div><button class="btn sec" onclick="location.reload()">' +
                    ct('retry') +
                    '</button></div>';
            });
    }
    function renderAll() {
        applyTexts();
        renderMembers();
        renderPending();
        if (S.secLoaded) renderSecurity();
    }

    // ── 屏1 · 成员列表 + 行内展开
    function renderMembers() {
        // 席位计量(PEAK 吸收):有 seats_max 显「当前用户 N/M」,满员追加升级提示
        $('teamStat').textContent = S.seatsMax
            ? ct('seats_count', { n: S.members.length, m: S.seatsMax })
            : ct('act_n_members', { n: S.members.length });
        var pending = ct('act_n_pending', { n: S.invites.length });
        $('teamStat2').textContent =
            S.seatsMax && S.members.length >= S.seatsMax
                ? pending + ' · ' + ct('seats_full')
                : pending;
        if (S.members.length <= 1 && !S.invites.length) {
            $('membersBox').innerHTML =
                '<div class="card">' +
                S.members.map(rowHtml).join('') +
                '</div>' +
                '<div class="empty" style="margin-top:14px"><div class="e1">' +
                ct('inv_empty') +
                '</div><div class="e2">' +
                ct('inv_empty2') +
                '</div></div>';
        } else {
            $('membersBox').innerHTML =
                '<div class="card">' + S.members.map(rowHtml).join('') + '</div>';
        }
        S.members.forEach(function (m) {
            var row = $('m-' + m.id);
            if (row)
                row.onclick = function () {
                    toggleExpand(m);
                };
        });
    }
    function rowHtml(m) {
        var isOwner = m.role_key === 'owner';
        var scope =
            m.scope_mode === 'assigned'
                ? ct('scope_assigned', { n: (m.workspace_ids || []).length })
                : ct('scope_all');
        var status = m.is_active
            ? '<span class="pill ok">' + ct('status_active') + '</span>'
            : '<span class="pill off">' + ct('status_off') + '</span>';
        var login = m.last_login_at
            ? ct('last_login') + ' ' + m.last_login_at.slice(0, 10)
            : ct('never_login');
        return (
            '<div class="mrow" id="m-' +
            m.id +
            '">' +
            '<span class="av">' +
            esc((m.username || '?').slice(0, 2).toUpperCase()) +
            '</span>' +
            '<span class="who"><span class="nm">' +
            (isOwner ? ICON_CROWN + ' ' : '') +
            esc(m.username) +
            (m.is_self ? ' <span style="color:var(--ink3)">' + ct('you') + '</span>' : '') +
            '</span>' +
            (m.email ? '<div class="em">' + esc(m.email) + '</div>' : '') +
            '</span>' +
            '<span class="pill role">' +
            roleName(m.role_key) +
            '</span>' +
            '<span class="pill off">' +
            scope +
            '</span>' +
            status +
            '<span class="meta">' +
            login +
            '</span></div>' +
            '<div class="expand" id="x-' +
            m.id +
            '" style="display:none"></div>'
        );
    }
    function toggleExpand(m) {
        var el = $('x-' + m.id);
        var open = el.style.display !== 'none';
        document.querySelectorAll('.expand').forEach(function (e) {
            e.style.display = 'none';
        });
        if (!open) {
            el.style.display = '';
            el.innerHTML = expandHtml(m);
            bindExpandActions(m);
        }
    }
    function expandHtml(m) {
        // 使用权一行(PEAK 屏6 对位):该成员角色能碰哪些模块
        var accessHtml =
            '<div class="grp"><div class="lb">' +
            ct('grp_access') +
            '</div>' +
            modChips(roleGroups(m.role_key)) +
            '</div>';
        // owner 行:无操作;owner 本人行只给「转移所有权」
        if (m.role_key === 'owner') {
            if (m.is_self && can('ownership.transfer')) {
                return (
                    accessHtml +
                    '<div class="acts"><button class="btn sec" id="a-transfer">' +
                    ct('btn_transfer') +
                    '</button></div>'
                );
            }
            return accessHtml + '<div class="hint">' + ct('roledesc_owner') + '</div>';
        }
        if (m.is_self)
            return accessHtml + '<div class="hint">' + ct('err_team_cannot_modify_self') + '</div>';
        var roleCards = S.roles
            .filter(function (r) {
                return r.assignable;
            })
            .map(function (r) {
                return roleCardHtml(r, r.key === m.role_key);
            })
            .join('');
        var scopable = (
            S.roles.find(function (r) {
                return r.key === m.role_key;
            }) || {}
        ).scopable;
        var scopeHtml = '';
        if (scopable && can('team.member.scope')) {
            var wsOpts = S.ws
                .map(function (w) {
                    var on = (m.workspace_ids || []).indexOf(w.id) >= 0;
                    return (
                        '<label class="wsopt' +
                        (on ? ' on' : '') +
                        '"><input type="checkbox" data-ws="' +
                        w.id +
                        '"' +
                        (on ? ' checked' : '') +
                        '> ' +
                        esc(w.name) +
                        '</label>'
                    );
                })
                .join('');
            scopeHtml =
                '<div class="grp"><div class="lb">' +
                ct('grp_scope') +
                '</div>' +
                '<span class="seg" id="a-scopeseg"><b data-sm="all"' +
                (m.scope_mode !== 'assigned' ? ' class="on"' : '') +
                '>' +
                ct('scope_mode_all') +
                '</b><b data-sm="assigned"' +
                (m.scope_mode === 'assigned' ? ' class="on"' : '') +
                '>' +
                ct('scope_mode_assigned') +
                '</b></span>' +
                '<div class="wslist" id="a-wslist" style="' +
                (m.scope_mode === 'assigned' ? '' : 'display:none') +
                '">' +
                wsOpts +
                '</div>' +
                '<div class="hint">' +
                ct('scope_hint') +
                '</div>' +
                '<div class="acts"><button class="btn pri sm" id="a-scopesave">' +
                ct('btn_save') +
                '</button></div></div>';
        }
        return (
            accessHtml +
            '<div class="grp"><div class="lb">' +
            ct('grp_role') +
            '</div><div class="rolecards" id="a-roles">' +
            roleCards +
            '</div><div class="acts" id="a-roleconfirm" style="display:none"></div></div>' +
            scopeHtml +
            '<div class="grp"><div class="lb">' +
            ct('grp_danger') +
            '</div><div class="acts">' +
            '<button class="btn sec sm" id="a-toggle">' +
            ct(m.is_active ? 'btn_disable' : 'btn_enable') +
            '</button>' +
            '<button class="btn danger sm" id="a-remove">' +
            ct('btn_remove') +
            '</button></div></div>'
        );
    }
    function bindExpandActions(m) {
        var tr = $('a-transfer');
        if (tr)
            tr.onclick = function (ev) {
                ev.stopPropagation();
                openTransferInit();
            };
        var roles = $('a-roles');
        if (roles)
            roles.querySelectorAll('.rolecard').forEach(function (card) {
                card.onclick = function (ev) {
                    ev.stopPropagation();
                    var rk = card.getAttribute('data-role');
                    if (rk === m.role_key) return;
                    // 行内确认条(全站禁原生弹窗)
                    var bar = $('a-roleconfirm');
                    bar.style.display = '';
                    bar.innerHTML =
                        '<span class="hint">' +
                        ct('confirm_role', { role: roleName(rk) }) +
                        '</span><button class="btn pri sm" id="a-roleok">' +
                        ct('btn_save') +
                        '</button><button class="btn sec sm" id="a-rolecancel">' +
                        ct('btn_cancel') +
                        '</button>';
                    $('a-rolecancel').onclick = function (e2) {
                        e2.stopPropagation();
                        bar.style.display = 'none';
                    };
                    $('a-roleok').onclick = function (e2) {
                        e2.stopPropagation();
                        api('PUT', '/api/team/members/' + m.id + '/role', { role_key: rk })
                            .then(loadAll)
                            .catch(function (e) {
                                toast(errMsg(e));
                            });
                    };
                };
            });
        var seg = $('a-scopeseg');
        if (seg)
            seg.querySelectorAll('b').forEach(function (b) {
                b.onclick = function (ev) {
                    ev.stopPropagation();
                    seg.querySelectorAll('b').forEach(function (x) {
                        x.classList.remove('on');
                    });
                    b.classList.add('on');
                    $('a-wslist').style.display =
                        b.getAttribute('data-sm') === 'assigned' ? '' : 'none';
                };
            });
        var wsl = $('a-wslist');
        if (wsl)
            wsl.querySelectorAll('.wsopt').forEach(function (o) {
                o.onclick = function (ev) {
                    ev.stopPropagation();
                };
                o.querySelector('input').onchange = function () {
                    o.classList.toggle('on', this.checked);
                };
            });
        var ss = $('a-scopesave');
        if (ss)
            ss.onclick = function (ev) {
                ev.stopPropagation();
                var mode = seg.querySelector('b.on').getAttribute('data-sm');
                var ids = [].map.call(wsl.querySelectorAll('input:checked'), function (i) {
                    return parseInt(i.getAttribute('data-ws'), 10);
                });
                api('PUT', '/api/team/members/' + m.id + '/scope', {
                    scope_mode: mode,
                    workspace_ids: ids,
                })
                    .then(loadAll)
                    .catch(function (e) {
                        toast(errMsg(e));
                    });
            };
        var tg = $('a-toggle');
        if (tg)
            tg.onclick = function (ev) {
                ev.stopPropagation();
                var act = function () {
                    api('PATCH', '/api/team/members/' + m.id + '/active', {
                        is_active: !m.is_active,
                    })
                        .then(loadAll)
                        .catch(function (e) {
                            toast(errMsg(e));
                        });
                };
                if (m.is_active) armConfirm(tg, act);
                else act();
            };
        var rm = $('a-remove');
        if (rm)
            rm.onclick = function (ev) {
                ev.stopPropagation();
                armConfirm(rm, function () {
                    api('DELETE', '/api/team/members/' + m.id)
                        .then(loadAll)
                        .catch(function (e) {
                            toast(errMsg(e));
                        });
                });
            };
    }

    // 危险按钮两段式确认(替代原生弹窗):首点变「再点一次确认」,3.5s 不点自动还原
    function armConfirm(btn, fn) {
        if (btn.dataset.armed) {
            delete btn.dataset.armed;
            fn();
            return;
        }
        btn.dataset.armed = '1';
        var prev = btn.textContent;
        btn.classList.add('armed');
        btn.textContent = ct('confirm_step');
        setTimeout(function () {
            if (btn.dataset.armed) {
                delete btn.dataset.armed;
                btn.classList.remove('armed');
                btn.textContent = prev;
            }
        }, 3500);
    }

    // ── 待接受邀请
    function renderPending() {
        var card = $('pendingCard');
        if (!S.invites.length) {
            card.style.display = 'none';
            return;
        }
        card.style.display = '';
        $('pendingCount').textContent = S.invites.length;
        $('pendingBox').innerHTML = S.invites
            .map(function (iv) {
                return (
                    '<div class="mrow" style="cursor:default"><span class="av">' +
                    ICON_MAIL +
                    '</span>' +
                    '<span class="who"><span class="nm">' +
                    esc(iv.target) +
                    '</span><div class="em">' +
                    ct('inv_expire') +
                    ' ' +
                    iv.expires_at.slice(0, 10) +
                    '</div></span>' +
                    '<span class="pill role">' +
                    roleName(iv.role_key) +
                    '</span>' +
                    '<span class="meta"><button class="btn danger sm" data-rid="' +
                    iv.id +
                    '">' +
                    ct('btn_revoke') +
                    '</button></span></div>'
                );
            })
            .join('');
        $('pendingBox')
            .querySelectorAll('[data-rid]')
            .forEach(function (b) {
                b.onclick = function () {
                    api('DELETE', '/api/team/invitations/' + b.getAttribute('data-rid'))
                        .then(loadAll)
                        .catch(function (e) {
                            toast(errMsg(e));
                        });
                };
            });
    }

    // ── 屏2 · 邀请弹窗
    function openInvite() {
        var roleCards = S.roles
            .filter(function (r) {
                return r.assignable;
            })
            .map(function (r) {
                return roleCardHtml(r, r.key === 'accountant');
            })
            .join('');
        var wsOpts = S.ws
            .map(function (w) {
                return (
                    '<label class="wsopt"><input type="checkbox" data-ws="' +
                    w.id +
                    '"> ' +
                    esc(w.name) +
                    '</label>'
                );
            })
            .join('');
        $('inviteBody').innerHTML =
            '<div class="field"><label>' +
            ct('inv_channel') +
            '</label>' +
            '<span class="seg" id="iv-ch"><b class="on" data-ch="email">' +
            ct('inv_email') +
            '</b><b data-ch="line">' +
            ct('inv_line') +
            '</b></span></div>' +
            '<div class="field"><label id="iv-tlabel">' +
            ct('inv_target_email') +
            '</label><input id="iv-target" placeholder=""></div>' +
            '<div class="field"><label>' +
            ct('inv_role') +
            '</label><div class="rolecards" id="iv-roles">' +
            roleCards +
            '</div></div>' +
            '<div class="field"><label>' +
            ct('inv_scope') +
            '</label>' +
            '<span class="seg" id="iv-sm"><b class="on" data-sm="all">' +
            ct('scope_mode_all') +
            '</b><b data-sm="assigned">' +
            ct('scope_mode_assigned') +
            '</b></span>' +
            '<div class="wslist" id="iv-ws" style="display:none">' +
            wsOpts +
            '</div></div>' +
            '<div class="err" id="iv-err"></div>' +
            '<div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px"><button class="btn sec" data-close="inviteMask">' +
            ct('btn_cancel') +
            '</button><button class="btn pri" id="iv-send">' +
            ct('btn_send') +
            '</button></div>';
        $('inviteMask').classList.add('open');
        var ch = 'email';
        $('iv-ch')
            .querySelectorAll('b')
            .forEach(function (b) {
                b.onclick = function () {
                    $('iv-ch')
                        .querySelectorAll('b')
                        .forEach(function (x) {
                            x.classList.remove('on');
                        });
                    b.classList.add('on');
                    ch = b.getAttribute('data-ch');
                    $('iv-tlabel').textContent = ct(
                        ch === 'email' ? 'inv_target_email' : 'inv_target_line'
                    );
                };
            });
        $('iv-roles')
            .querySelectorAll('.rolecard')
            .forEach(function (c) {
                c.onclick = function () {
                    $('iv-roles')
                        .querySelectorAll('.rolecard')
                        .forEach(function (x) {
                            x.classList.remove('on');
                        });
                    c.classList.add('on');
                    var scopable = (
                        S.roles.find(function (r) {
                            return r.key === c.getAttribute('data-role');
                        }) || {}
                    ).scopable;
                    if (!scopable) {
                        $('iv-sm')
                            .querySelectorAll('b')
                            .forEach(function (x, i) {
                                x.classList.toggle('on', i === 0);
                            });
                        $('iv-ws').style.display = 'none';
                    }
                };
            });
        $('iv-sm')
            .querySelectorAll('b')
            .forEach(function (b) {
                b.onclick = function () {
                    $('iv-sm')
                        .querySelectorAll('b')
                        .forEach(function (x) {
                            x.classList.remove('on');
                        });
                    b.classList.add('on');
                    $('iv-ws').style.display =
                        b.getAttribute('data-sm') === 'assigned' ? '' : 'none';
                };
            });
        $('iv-ws')
            .querySelectorAll('.wsopt input')
            .forEach(function (i) {
                i.onchange = function () {
                    i.closest('.wsopt').classList.toggle('on', i.checked);
                };
            });
        $('inviteBody')
            .querySelectorAll('[data-close]')
            .forEach(function (b) {
                b.onclick = function () {
                    $('inviteMask').classList.remove('open');
                };
            });
        $('iv-send').onclick = function () {
            var role = $('iv-roles').querySelector('.rolecard.on');
            var sm = $('iv-sm').querySelector('b.on').getAttribute('data-sm');
            var ids = [].map.call($('iv-ws').querySelectorAll('input:checked'), function (i) {
                return parseInt(i.getAttribute('data-ws'), 10);
            });
            api('POST', '/api/team/invitations', {
                channel: ch,
                target: $('iv-target').value.trim(),
                role_key: role ? role.getAttribute('data-role') : '',
                scope_mode: sm,
                workspace_ids: ids,
            })
                .then(function (j) {
                    $('inviteBody').innerHTML =
                        '<div class="field"><label>' +
                        ct('inv_sent') +
                        ' · ' +
                        (ch === 'email'
                            ? ct(j.email_sent ? 'inv_email_ok' : 'inv_email_fail')
                            : ct('inv_line_tip')) +
                        '</label>' +
                        '<div class="copybox"><span id="iv-url">' +
                        esc(j.invite_url) +
                        '</span><button class="btn sec sm" id="iv-copy">' +
                        ct('btn_copy') +
                        '</button></div>' +
                        '<div class="hint">' +
                        ct('inv_expire') +
                        ' ' +
                        j.expires_at.slice(0, 10) +
                        '</div></div>' +
                        '<div style="display:flex;justify-content:flex-end"><button class="btn pri" id="iv-done">' +
                        ct('btn_close') +
                        '</button></div>';
                    $('iv-copy').onclick = function () {
                        navigator.clipboard.writeText(j.invite_url).then(function () {
                            toast(ct('copied'));
                        });
                    };
                    $('iv-done').onclick = function () {
                        $('inviteMask').classList.remove('open');
                        loadAll();
                    };
                })
                .catch(function (e) {
                    $('iv-err').textContent = errMsg(e);
                });
        };
    }

    // ── 所有权转移(发起 / 确认)
    function openTransferInit() {
        var admins = S.members.filter(function (m) {
            return m.role_key === 'admin';
        });
        var opts = admins
            .map(function (m) {
                return '<option value="' + m.id + '">' + esc(m.username) + '</option>';
            })
            .join('');
        $('transferBody').innerHTML =
            '<div class="hint" style="margin-bottom:10px">' +
            ct('transfer_tip') +
            '</div>' +
            '<div class="field"><label>' +
            ct('transfer_pick') +
            '</label><select id="tf-target">' +
            (opts || '<option value="">—</option>') +
            '</select></div>' +
            '<div class="err" id="tf-err"></div>' +
            '<div style="display:flex;justify-content:flex-end;gap:8px"><button class="btn sec" id="tf-cancel">' +
            ct('btn_cancel') +
            '</button><button class="btn pri" id="tf-go"' +
            (admins.length ? '' : ' disabled') +
            '>' +
            ct('btn_transfer') +
            '</button></div>';
        $('transferMask').classList.add('open');
        $('tf-cancel').onclick = function () {
            $('transferMask').classList.remove('open');
        };
        $('tf-go').onclick = function () {
            api('POST', '/api/ownership/transfer', { target_user_id: $('tf-target').value })
                .then(function (j) {
                    $('transferBody').innerHTML =
                        '<div class="field"><label>' +
                        ct('transfer_token_tip') +
                        '</label>' +
                        '<div class="copybox"><span>' +
                        esc(j.token) +
                        '</span><button class="btn sec sm" id="tf-copy">' +
                        ct('btn_copy') +
                        '</button></div>' +
                        '<div class="hint">' +
                        ct('inv_expire') +
                        ' ' +
                        j.expires_at.replace('T', ' ').slice(0, 16) +
                        '</div></div>' +
                        '<div style="display:flex;justify-content:flex-end"><button class="btn pri" id="tf-done">' +
                        ct('btn_close') +
                        '</button></div>';
                    $('tf-copy').onclick = function () {
                        navigator.clipboard.writeText(j.token).then(function () {
                            toast(ct('copied'));
                        });
                    };
                    $('tf-done').onclick = function () {
                        $('transferMask').classList.remove('open');
                    };
                })
                .catch(function (e) {
                    $('tf-err').textContent = errMsg(e);
                });
        };
    }
    function openTransferAccept() {
        $('transferBody').innerHTML =
            '<div class="field"><label>' +
            ct('transfer_input') +
            '</label><input id="ta-token"></div>' +
            '<div class="err" id="ta-err"></div>' +
            '<div style="display:flex;justify-content:flex-end;gap:8px"><button class="btn sec" id="ta-cancel">' +
            ct('btn_cancel') +
            '</button><button class="btn pri" id="ta-go">' +
            ct('btn_confirm_transfer') +
            '</button></div>';
        $('transferMask').classList.add('open');
        $('ta-cancel').onclick = function () {
            $('transferMask').classList.remove('open');
        };
        $('ta-go').onclick = function () {
            api('POST', '/api/ownership/transfer/accept', { token: $('ta-token').value.trim() })
                .then(function () {
                    $('transferMask').classList.remove('open');
                    toast(ct('transfer_done'));
                    setTimeout(function () {
                        location.reload();
                    }, 900);
                })
                .catch(function (e) {
                    $('ta-err').textContent = errMsg(e);
                });
        };
    }

    // ── 屏3 · 安全日志
    function loadSecurity() {
        $('secBox').innerHTML = '<div class="skeleton"><i></i><i></i><i></i></div>';
        api('GET', '/api/team/security-events?per_page=100')
            .then(function (j) {
                S.events = j.events || [];
                S.secLoaded = true;
                renderSecurity();
            })
            .catch(function () {
                $('secBox').innerHTML =
                    '<div class="empty"><div class="e1">' + ct('load_fail') + '</div></div>';
            });
    }
    function describeEvent(e) {
        var d = e.details || {};
        var a = '<b>' + esc(e.actor || '?') + '</b>',
            t2 = '<b>' + esc(e.target || '?') + '</b>';
        switch (true) {
            case e.action === 'team.invite':
                return ct('ev_team_invite', { a: a, t: t2, r: roleName(d.role_key || '') });
            case e.action === 'team.invite_revoke':
                return ct('ev_team_invite_revoke', { a: a });
            case e.action === 'team.member_join':
                return ct('ev_team_member_join', { t: t2, r: roleName(d.role_key || '') });
            case e.action === 'role.change':
                return ct('ev_role_change', {
                    a: a,
                    t: t2,
                    f: roleName(d.role_from || ''),
                    r: roleName(d.role_to || ''),
                });
            case e.action === 'scope.change':
                return ct('ev_scope_change', { a: a, t: t2 });
            case e.action === 'member.remove' || e.action === 'employee.remove':
                return ct('ev_member_remove', { a: a, t: t2 });
            case e.action === 'member.toggle' || e.action === 'employee.toggle':
                return ct(d.is_active ? 'ev_member_toggle_on' : 'ev_member_toggle_off', {
                    a: a,
                    t: t2,
                });
            case e.action === 'ownership.transfer_init':
                return ct('ev_ownership_init', { a: a, t: t2 });
            case e.action === 'ownership.transfer':
                return ct('ev_ownership_done', { t: a });
            default:
                return ct('ev_employee_legacy', { a: a, t: t2, act: esc(e.action) });
        }
    }
    function renderSecurity() {
        var evs = S.events || [];
        if (!evs.length) {
            $('secBox').innerHTML =
                '<div class="empty" style="border:0"><div class="e1">' +
                ct('sec_empty') +
                '</div><div class="e2">' +
                ct('sec_empty2') +
                '</div></div>';
            return;
        }
        $('secBox').innerHTML = evs
            .map(function (e) {
                return (
                    '<div class="logrow"><span class="tm">' +
                    (e.created_at || '').replace('T', ' ').slice(0, 16) +
                    '</span><span class="desc">' +
                    describeEvent(e) +
                    '</span></div>'
                );
            })
            .join('');
    }

    boot();
})();
