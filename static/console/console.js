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
        customRoles: [],
        ws: [],
        seatsMax: 0,
        seatsUsed: 0,
        seatsPending: 0,
        secLoaded: false,
        expanded: null,
        // 安全日志:游标分页累积 + 当前筛选
        logEvents: [],
        logCursor: null,
        logMore: false,
        logType: 'all',
        logActor: 'all',
        wiz: null,
    };
    // 权限码目录(镜像 services/authz/registry · 62 模块码按域分组,2 字段码是底部敏感开关)。
    // 组标题键:cross 用 pg_cross,其余复用 mod_*;每码标签 = pc_<码下划线化>。
    var PERM_GROUPS = [
        {
            key: 'cross',
            title: 'pg_cross',
            codes: [
                'team.member.view',
                'team.member.invite',
                'team.member.edit_role',
                'team.member.scope',
                'team.member.remove',
                'team.member.toggle',
                'billing.view',
                'billing.manage',
                'ownership.transfer',
                'settings.org.view',
                'settings.org.edit',
                'settings.modules.manage',
                'settings.workspace.manage',
                'audit.log.view',
            ],
        },
        {
            key: 'sales',
            title: 'mod_sales',
            codes: [
                'sales.doc.view',
                'sales.doc.create',
                'sales.doc.edit',
                'sales.doc.delete',
                'sales.doc.approve',
                'sales.doc.export',
                'sales.product.view',
                'sales.product.manage',
                'sales.settings.manage',
            ],
        },
        {
            key: 'purchase',
            title: 'mod_purchase',
            codes: [
                'purchase.doc.view',
                'purchase.doc.create',
                'purchase.doc.edit',
                'purchase.doc.delete',
                'purchase.doc.approve',
                'purchase.supplier.manage',
                'purchase.settings.manage',
            ],
        },
        {
            key: 'acct',
            title: 'mod_acct',
            codes: [
                'acct.entry.view',
                'acct.entry.review',
                'acct.entry.approve',
                'acct.coa.manage',
                'acct.ledger.export',
                'acct.settings.manage',
            ],
        },
        {
            key: 'tax',
            title: 'mod_tax',
            codes: [
                'tax.filing.view',
                'tax.filing.create',
                'tax.filing.approve',
                'tax.settings.manage',
            ],
        },
        {
            key: 'recon',
            title: 'mod_recon',
            codes: ['recon.view', 'recon.create', 'recon.approve', 'recon.export'],
        },
        { key: 'ar', title: 'mod_ar', codes: ['ar.view', 'ar.create', 'ar.edit'] },
        {
            key: 'kb',
            title: 'mod_kb',
            codes: ['kb.doc.view', 'kb.doc.create', 'kb.doc.delete', 'kb.ask'],
        },
        {
            key: 'inv',
            title: 'mod_inv',
            codes: ['inv.view', 'inv.create', 'inv.approve', 'inv.report.view'],
        },
        {
            key: 'pos',
            title: 'mod_pos',
            codes: [
                'pos.admin.manage',
                'pos.report.view',
                'pos.sale.operate',
                'pos.shift.operate',
                'pos.refund.approve',
            ],
        },
        { key: 'intake', title: 'mod_intake', codes: ['intake.upload', 'intake.classify'] },
    ];
    // 连 admin 都没有的提权码 · 自定义角色禁选(后端 roles_store 同样剔除,前端只为显式禁灰)
    var FORBIDDEN_CODES = ['billing.manage', 'ownership.transfer'];
    var FIELD_COST = 'field.cost.view';
    var FIELD_PAYROLL = 'field.payroll.view';
    function pcKey(code) {
        return 'pc_' + code.replace(/\./g, '_');
    }
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
        if (k && k.indexOf('custom:') === 0) {
            var c = S.customRoles.find(function (x) {
                return x.key === k;
            });
            return c ? c.name : k;
        }
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
    // 自定义角色的模块分组(后端 custom 行只返 permissions[],组芯片前端从前缀派生)
    function customGroups(c) {
        var seen = {};
        (c.permissions || []).forEach(function (p) {
            seen[p.split('.', 1)[0]] = 1;
        });
        return Object.keys(seen);
    }
    function customAssignCard(c, on) {
        return (
            '<div class="rolecard' +
            (on ? ' on' : '') +
            '" data-role="' +
            esc(c.key) +
            '"><div class="rn">' +
            esc(c.name) +
            '<span class="rc-count">' +
            ct('rc_inuse', { n: c.member_count || 0 }) +
            '</span></div><div class="rd">' +
            ct('chip_n_perms', { n: c.permission_count }) +
            '</div>' +
            modChips(customGroups(c)) +
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
        $('view-roles').style.display = v === 'roles' ? '' : 'none';
        $('view-security').style.display = v === 'security' ? '' : 'none';
        if (v === 'roles') renderRoles();
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
            api('GET', '/api/team/roles/custom'),
        ])
            .then(function (rs) {
                S.members = rs[0].members || [];
                S.seatsMax = rs[0].seats_max || 0;
                S.seatsUsed = rs[0].seats_used || 0;
                S.seatsPending = rs[0].seats_pending || 0;
                S.invites = rs[1].invitations || [];
                S.roles = rs[2].roles || [];
                S.ws = rs[3].clients || [];
                S.customRoles = rs[4].roles || [];
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
        renderRoles();
        if (S.secLoaded) renderSecurity();
    }

    // ── 屏1 · 成员列表 + 行内展开
    function seatFull() {
        return S.seatsMax > 0 && S.seatsUsed >= S.seatsMax;
    }
    function renderMembers() {
        // 席位计量(PEAK 吸收):有 seats_max 显「当前用户 N/M」,满员追加升级提示
        var full = seatFull();
        $('teamStat').textContent = S.seatsMax
            ? ct('seats_count', { n: S.members.length, m: S.seatsMax })
            : ct('act_n_members', { n: S.members.length });
        var pending = ct('act_n_pending', { n: S.invites.length });
        $('teamStat2').textContent = full
            ? pending + ' · ' + ct('seats_full')
            : S.seatsMax
              ? pending + ' · ' + ct('seat_remaining', { n: Math.max(0, S.seatsMax - S.seatsUsed) })
              : pending;
        // 满员警示条(G1 后端 422 enforce 的前端对位 · 释放席位/升级指引)
        var upbar = full
            ? '<div class="upbar"><span><b>' +
              esc(ct('seat_full_short')) +
              '</b> ' +
              esc(ct('seat_full_banner', { u: S.seatsUsed, m: S.seatsMax })) +
              '</span><button class="btn sec sm" id="seatUpgrade">' +
              ct('seat_learn_more') +
              '</button></div>'
            : '';
        if (S.members.length <= 1 && !S.invites.length) {
            $('membersBox').innerHTML =
                upbar +
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
                upbar + '<div class="card">' + S.members.map(rowHtml).join('') + '</div>';
        }
        var up = $('seatUpgrade');
        if (up)
            up.onclick = function () {
                location.href = '/home#billing';
            };
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
        var roleCards =
            S.roles
                .filter(function (r) {
                    return r.assignable;
                })
                .map(function (r) {
                    return roleCardHtml(r, r.key === m.role_key);
                })
                .join('') +
            S.customRoles
                .filter(function (c) {
                    return c.is_active;
                })
                .map(function (c) {
                    return customAssignCard(c, c.key === m.role_key);
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
                        // 统一分配入口:系统预设与 custom:<slug> 同走 /role-assign
                        api('PUT', '/api/team/members/' + m.id + '/role-assign', {
                            role_key: rk,
                        })
                            .then(function () {
                                toast(
                                    ct('toast_role_assigned', {
                                        nm: m.username,
                                        role: roleName(rk),
                                    })
                                );
                                loadAll();
                            })
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
        // 席位满:不发请求,直接人话拦(后端 422 team.seat_limit 为兜底)
        if (seatFull()) {
            toast(ct('err_team_seat_limit'));
            return;
        }
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

    // ── 屏2 · 角色 tab(预设只读卡 + 自定义角色卡 + 三步向导入口)
    // 预设码集镜像 registry(无后端目录端点);提交后端再 sanitize,镜像漂移安全。
    var PRESET_CODES = {
        viewer: [
            'sales.doc.view',
            'sales.doc.export',
            'sales.product.view',
            'purchase.doc.view',
            'acct.entry.view',
            'acct.ledger.export',
            'tax.filing.view',
            'recon.view',
            'recon.export',
            'ar.view',
            'kb.doc.view',
            'inv.view',
            'inv.report.view',
            'pos.report.view',
        ],
        clerk: [
            'sales.doc.view',
            'sales.doc.create',
            'sales.doc.edit',
            'sales.doc.delete',
            'sales.product.view',
            'purchase.doc.view',
            'purchase.doc.create',
            'purchase.doc.edit',
            'purchase.doc.delete',
            'acct.entry.view',
            'tax.filing.view',
            'tax.filing.create',
            'recon.view',
            'recon.create',
            'ar.view',
            'ar.create',
            'ar.edit',
            'kb.doc.view',
            'kb.doc.create',
            'kb.doc.delete',
            'kb.ask',
            'inv.view',
            'inv.create',
            'inv.report.view',
            'intake.upload',
            'intake.classify',
        ],
        accountant: [
            'sales.doc.view',
            'sales.doc.create',
            'sales.doc.edit',
            'sales.doc.delete',
            'sales.doc.approve',
            'sales.doc.export',
            'sales.product.view',
            'sales.product.manage',
            'purchase.doc.view',
            'purchase.doc.create',
            'purchase.doc.edit',
            'purchase.doc.delete',
            'purchase.doc.approve',
            'purchase.supplier.manage',
            'acct.entry.view',
            'acct.entry.review',
            'acct.entry.approve',
            'acct.coa.manage',
            'acct.ledger.export',
            'tax.filing.view',
            'tax.filing.create',
            'tax.filing.approve',
            'recon.view',
            'recon.create',
            'recon.approve',
            'recon.export',
            'ar.view',
            'ar.create',
            'ar.edit',
            'kb.doc.view',
            'kb.doc.create',
            'kb.doc.delete',
            'kb.ask',
            'inv.view',
            'inv.create',
            'inv.approve',
            'inv.report.view',
            'pos.report.view',
            'intake.upload',
            'intake.classify',
        ],
    };
    function allModuleCodes() {
        var out = [];
        PERM_GROUPS.forEach(function (g) {
            g.codes.forEach(function (c) {
                if (FORBIDDEN_CODES.indexOf(c) < 0) out.push(c);
            });
        });
        return out;
    }
    function presetCodes(base) {
        return base === 'admin' ? allModuleCodes() : PRESET_CODES[base] || PRESET_CODES.clerk;
    }

    function renderRoles() {
        var box = $('rolesBox');
        if (!box) return;
        var canManage = can('team.member.edit_role');
        var presets = S.roles
            .map(function (r) {
                return (
                    '<div class="rrow"><div class="ic-r">' +
                    esc(roleName(r.key).slice(0, 1)) +
                    '</div><div class="rmain"><div class="rt">' +
                    esc(roleName(r.key)) +
                    ' <span class="badge-ro">' +
                    ct('badge_preset') +
                    '</span></div><div class="rdsc">' +
                    ct('roledesc_' + r.key) +
                    '</div><div class="rchips"><span class="rchip">' +
                    ct('chip_n_perms', { n: r.permission_count }) +
                    '</span><span class="rchip">' +
                    ct('rc_inuse', { n: r.member_count || 0 }) +
                    '</span></div></div><div class="racts"><button class="btn sec sm" data-vrole="' +
                    esc(r.key) +
                    '">' +
                    ct('btn_viewperm') +
                    '</button></div></div>'
                );
            })
            .join('');
        var customCards = S.customRoles
            .map(function (c) {
                var costHidden = (c.permissions || []).indexOf(FIELD_COST) < 0;
                return (
                    '<div class="rrow custom"><div class="ic-r">' +
                    esc(c.name.slice(0, 1)) +
                    '</div><div class="rmain"><div class="rt">' +
                    esc(c.name) +
                    (c.is_active ? '' : ' <span class="badge-ro">' + ct('status_off') + '</span>') +
                    '</div><div class="rchips"><span class="rchip">' +
                    ct('chip_n_perms', { n: c.permission_count }) +
                    '</span><span class="rchip">' +
                    ct('rc_inuse', { n: c.member_count || 0 }) +
                    '</span>' +
                    (costHidden
                        ? '<span class="rchip warn">' + ct('chip_cost_hidden') + '</span>'
                        : '') +
                    '</div></div>' +
                    (canManage
                        ? '<div class="racts"><button class="btn sec sm" data-erole="' +
                          esc(c.id) +
                          '">' +
                          ct('btn_edit') +
                          '</button><button class="btn danger sm" data-delrole="' +
                          esc(c.id) +
                          '">' +
                          ct('btn_delrole') +
                          '</button></div>'
                        : '') +
                    '</div>'
                );
            })
            .join('');
        box.innerHTML =
            '<div class="card"><div class="sect-h">' +
            ct('roletab_preset_h') +
            ' · ' +
            S.roles.length +
            '</div>' +
            presets +
            '</div><div class="card"><div class="sect-h">' +
            ct('roletab_custom_h') +
            ' · ' +
            S.customRoles.length +
            (canManage
                ? '<span class="spacer"></span><button class="btn pri sm" id="btnNewRole">' +
                  ct('btn_newrole') +
                  '</button>'
                : '') +
            '</div>' +
            (S.customRoles.length
                ? customCards
                : '<div class="empty" style="border:0;margin:0"><div class="e1">' +
                  ct('roles_empty') +
                  '</div><div class="e2">' +
                  ct('roles_empty2') +
                  '</div></div>') +
            '</div>';
        box.querySelectorAll('[data-vrole]').forEach(function (b) {
            b.onclick = function () {
                openRoleView(b.getAttribute('data-vrole'));
            };
        });
        box.querySelectorAll('[data-erole]').forEach(function (b) {
            b.onclick = function () {
                openWizard(b.getAttribute('data-erole'));
            };
        });
        box.querySelectorAll('[data-delrole]').forEach(function (b) {
            b.onclick = function () {
                delRole(b, b.getAttribute('data-delrole'));
            };
        });
        var nr = $('btnNewRole');
        if (nr)
            nr.onclick = function () {
                openWizard(null);
            };
    }

    function openRoleView(key) {
        var r = S.roles.find(function (x) {
            return x.key === key;
        });
        if (!r) return;
        $('roleViewTitle').textContent = ct('viewrole_title', { name: roleName(key) });
        $('roleViewBody').innerHTML =
            '<div class="wizhint">' +
            ct('viewrole_body', { d: ct('roledesc_' + key), n: r.permission_count }) +
            '</div>' +
            modChips(r.permission_groups) +
            (can('team.member.edit_role')
                ? '<div style="display:flex;justify-content:flex-end;margin-top:14px"><button class="btn pri sm" id="rvNew">' +
                  ct('viewrole_basenew') +
                  '</button></div>'
                : '');
        $('roleViewMask').classList.add('open');
        var nb = $('rvNew');
        if (nb)
            nb.onclick = function () {
                $('roleViewMask').classList.remove('open');
                openWizard(null, r.assignable ? key : 'accountant');
            };
    }

    function delRole(btn, id) {
        var c = S.customRoles.find(function (x) {
            return String(x.id) === String(id);
        });
        if (!c) return;
        // 在用拦截前移:有成员在用直接人话拦,不进二次确认(对齐原型「先转移」)
        if (c.member_count > 0) {
            toast(ct('err_team_role_in_use', { n: c.member_count }));
            return;
        }
        // 删除走 console 既有两段式确认(同移除成员)
        armConfirm(btn, function () {
            api('DELETE', '/api/team/roles/' + id)
                .then(function () {
                    toast(ct('toast_role_deleted'));
                    loadAll();
                })
                .catch(function (e) {
                    // 兜底:并发下后端 422 {code,member_count}
                    var detail = e && e.code;
                    if (detail && typeof detail === 'object' && detail.code === 'team.role_in_use')
                        toast(ct('err_team_role_in_use', { n: detail.member_count || 0 }));
                    else toast(errMsg(e));
                });
        });
    }

    // ── 三步向导(新建 / 编辑自定义角色)
    function openWizard(editId, baseKey) {
        var edit = editId
            ? S.customRoles.find(function (x) {
                  return String(x.id) === String(editId);
              })
            : null;
        var sel = {};
        var base = baseKey || 'clerk';
        var srcCodes = edit ? edit.permissions || [] : presetCodes(base);
        allModuleCodes().forEach(function (c) {
            sel[c] = srcCodes.indexOf(c) >= 0;
        });
        S.wiz = {
            step: 1,
            base: base,
            name: edit ? edit.name : '',
            cost: srcCodes.indexOf(FIELD_COST) >= 0,
            payroll: srcCodes.indexOf(FIELD_PAYROLL) >= 0,
            editId: editId || null,
            version: edit ? edit.version : null,
            sel: sel,
            open: {},
        };
        $('wizTitle').textContent = ct(edit ? 'wiz_edit_title' : 'wiz_new_title');
        $('wizardMask').classList.add('open');
        renderWizard();
    }
    function wizCount() {
        var n = 0;
        Object.keys(S.wiz.sel).forEach(function (c) {
            if (S.wiz.sel[c]) n++;
        });
        return n;
    }
    function applyBase(base) {
        S.wiz.base = base;
        var codes = presetCodes(base);
        var sel = {};
        allModuleCodes().forEach(function (c) {
            sel[c] = codes.indexOf(c) >= 0;
        });
        S.wiz.sel = sel;
        S.wiz.cost = codes.indexOf(FIELD_COST) >= 0;
        S.wiz.payroll = codes.indexOf(FIELD_PAYROLL) >= 0;
    }
    function renderWizard() {
        var w = S.wiz,
            body,
            foot;
        if (w.step === 1) {
            body =
                '<div class="wizhint">' +
                ct('wiz_step1_h') +
                '</div>' +
                ['admin', 'accountant', 'clerk', 'viewer']
                    .map(function (k) {
                        return (
                            '<div class="basecard' +
                            (w.base === k ? ' on' : '') +
                            '" data-wbase="' +
                            k +
                            '"><div class="ic-r">' +
                            esc(roleName(k).slice(0, 1)) +
                            '</div><div><div class="bt">' +
                            esc(roleName(k)) +
                            '</div><div class="bd">' +
                            ct('roledesc_' + k) +
                            '</div></div></div>'
                        );
                    })
                    .join('');
        } else if (w.step === 2) {
            body =
                '<div class="wizhint">' +
                ct('wiz_step2_h', { n: wizCount() }) +
                '</div>' +
                PERM_GROUPS.map(function (g) {
                    var on = g.codes.filter(function (c) {
                        return w.sel[c];
                    }).length;
                    var total = g.codes.length;
                    var allOn = on === total;
                    var cls = allOn ? 'on' : on ? 'half' : '';
                    var codesHtml = g.codes
                        .map(function (c) {
                            var locked = FORBIDDEN_CODES.indexOf(c) >= 0;
                            return (
                                '<div class="pgcode' +
                                (locked ? ' locked' : '') +
                                '"' +
                                (locked ? '' : ' data-wcode="' + c + '"') +
                                '><span class="cbx' +
                                (w.sel[c] ? ' on' : '') +
                                '"></span>' +
                                ct(pcKey(c)) +
                                (locked
                                    ? ' <span class="note">' + ct('wiz_forbidden_note') + '</span>'
                                    : '') +
                                '</div>'
                            );
                        })
                        .join('');
                    return (
                        '<div class="permgrp' +
                        (w.open[g.key] ? ' open' : '') +
                        '"><div class="pgh" data-wgrp="' +
                        g.key +
                        '"><span class="cbx ' +
                        cls +
                        '" data-wgall="' +
                        g.key +
                        '"></span>' +
                        ct(g.title) +
                        '<span class="cnt">' +
                        on +
                        '/' +
                        total +
                        '</span><span class="car">▾</span></div><div class="pgcodes">' +
                        codesHtml +
                        '</div></div>'
                    );
                }).join('') +
                '<div class="sens"><span class="sw' +
                (w.cost ? ' on' : '') +
                '" data-wsens="cost"></span><div><div class="st">' +
                ct('wiz_sens_cost_t') +
                '</div><div class="sd">' +
                ct('wiz_sens_cost_d') +
                '</div></div></div><div class="sens"><span class="sw' +
                (w.payroll ? ' on' : '') +
                '" data-wsens="payroll"></span><div><div class="st">' +
                ct('wiz_sens_payroll_t') +
                '</div><div class="sd">' +
                ct('wiz_sens_payroll_d') +
                '</div></div></div>';
        } else {
            body =
                '<div class="wizhint">' +
                ct('wiz_step3_h') +
                '</div><div class="field"><label>' +
                ct('wiz_name_label') +
                '</label><input id="wizName" value="' +
                esc(w.name) +
                '" placeholder="' +
                esc(ct('wiz_name_ph')) +
                '"></div><div class="wizhint">' +
                ct('wiz_confirm_base', { base: roleName(w.base), n: wizCount() }) +
                (w.cost ? '' : ct('wiz_confirm_cost')) +
                (w.payroll ? '' : ct('wiz_confirm_payroll')) +
                '<br>' +
                ct('wiz_confirm_apply') +
                '</div>';
        }
        foot =
            '<span class="steps">' +
            ct('wiz_step_of', { s: w.step }) +
            '</span>' +
            (w.step > 1
                ? '<button class="btn sec" id="wizPrev">' + ct('btn_prev') + '</button>'
                : '') +
            (w.step < 3
                ? '<button class="btn pri" id="wizNext">' + ct('btn_next') + '</button>'
                : '<button class="btn pri" id="wizDone">' +
                  ct(w.editId ? 'btn_savechg' : 'btn_create') +
                  '</button>');
        $('wizBody').innerHTML = body;
        $('wizFoot').innerHTML = foot;
        bindWizard();
    }
    function bindWizard() {
        var w = S.wiz;
        $('wizBody')
            .querySelectorAll('[data-wbase]')
            .forEach(function (el) {
                el.onclick = function () {
                    applyBase(el.getAttribute('data-wbase'));
                    renderWizard();
                };
            });
        $('wizBody')
            .querySelectorAll('[data-wgrp]')
            .forEach(function (el) {
                el.onclick = function (ev) {
                    if (ev.target.hasAttribute('data-wgall')) return;
                    var g = el.getAttribute('data-wgrp');
                    w.open[g] = !w.open[g];
                    renderWizard();
                };
            });
        $('wizBody')
            .querySelectorAll('[data-wgall]')
            .forEach(function (el) {
                el.onclick = function (ev) {
                    ev.stopPropagation();
                    var key = el.getAttribute('data-wgall');
                    var grp = PERM_GROUPS.find(function (x) {
                        return x.key === key;
                    });
                    var selectable = grp.codes.filter(function (c) {
                        return FORBIDDEN_CODES.indexOf(c) < 0;
                    });
                    var allOn = selectable.every(function (c) {
                        return w.sel[c];
                    });
                    selectable.forEach(function (c) {
                        w.sel[c] = !allOn;
                    });
                    w.open[key] = true;
                    renderWizard();
                };
            });
        $('wizBody')
            .querySelectorAll('[data-wcode]')
            .forEach(function (el) {
                el.onclick = function () {
                    var c = el.getAttribute('data-wcode');
                    w.sel[c] = !w.sel[c];
                    var g = PERM_GROUPS.find(function (x) {
                        return x.codes.indexOf(c) >= 0;
                    });
                    if (g) w.open[g.key] = true;
                    renderWizard();
                };
            });
        $('wizBody')
            .querySelectorAll('[data-wsens]')
            .forEach(function (el) {
                el.onclick = function () {
                    var k = el.getAttribute('data-wsens');
                    w[k] = !w[k];
                    renderWizard();
                };
            });
        var nameEl = $('wizName');
        if (nameEl)
            nameEl.oninput = function () {
                w.name = nameEl.value;
            };
        var prev = $('wizPrev');
        if (prev)
            prev.onclick = function () {
                w.step--;
                renderWizard();
            };
        var next = $('wizNext');
        if (next)
            next.onclick = function () {
                w.step++;
                renderWizard();
            };
        var done = $('wizDone');
        if (done) done.onclick = submitWizard;
    }
    function submitWizard() {
        var w = S.wiz;
        var name = (w.name || '').trim();
        if (!name) {
            toast(ct('err_team_role_name_invalid'));
            w.step = 3;
            renderWizard();
            return;
        }
        var codes = Object.keys(w.sel).filter(function (c) {
            return w.sel[c];
        });
        if (w.cost) codes.push(FIELD_COST);
        if (w.payroll) codes.push(FIELD_PAYROLL);
        if (!codes.length) {
            toast(ct('err_team_role_permissions_empty'));
            return;
        }
        var done = $('wizDone');
        if (done) done.disabled = true;
        var req = w.editId
            ? api('PATCH', '/api/team/roles/' + w.editId, {
                  name: name,
                  permissions: codes,
                  version: w.version,
              })
            : api('POST', '/api/team/roles', { name: name, permissions: codes });
        req.then(function () {
            $('wizardMask').classList.remove('open');
            toast(ct(w.editId ? 'toast_role_updated' : 'toast_role_created', { name: name }));
            S.wiz = null;
            loadAll();
        }).catch(function (e) {
            if (done) done.disabled = false;
            toast(errMsg(e));
        });
    }

    // ── 屏3 · 安全日志
    function logFiltered() {
        return S.logType !== 'all' || S.logActor !== 'all';
    }
    function logQuery() {
        var q = [];
        if (S.logType !== 'all') q.push('type=' + encodeURIComponent(S.logType));
        if (S.logActor !== 'all') q.push('actor=' + encodeURIComponent(S.logActor));
        return q;
    }
    function loadSecurity() {
        S.logCursor = null;
        S.logEvents = [];
        $('secBox').innerHTML = '<div class="skeleton"><i></i><i></i><i></i></div>';
        fetchLogPage(true);
    }
    function fetchLogPage(reset) {
        var q = logQuery();
        if (!reset && S.logCursor) q.push('cursor=' + encodeURIComponent(S.logCursor));
        api('GET', '/api/team/security-events' + (q.length ? '?' + q.join('&') : ''))
            .then(function (j) {
                S.logEvents = (reset ? [] : S.logEvents).concat(j.events || []);
                S.logCursor = j.next_cursor || null;
                S.logMore = !!j.next_cursor;
                S.secLoaded = true;
                renderSecurity();
            })
            .catch(function () {
                if (reset)
                    $('secBox').innerHTML =
                        '<div class="empty"><div class="e1">' + ct('load_fail') + '</div></div>';
            });
    }
    function exportLog() {
        var q = logQuery();
        fetch('/api/team/security-events/export' + (q.length ? '?' + q.join('&') : ''), {
            headers: { Authorization: 'Bearer ' + S.token },
        })
            .then(function (r) {
                if (!r.ok) throw 0;
                return r.blob();
            })
            .then(function (b) {
                var url = URL.createObjectURL(b);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'security-events.csv';
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
            })
            .catch(function () {
                toast(ct('err_generic'));
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
            case e.action === 'role.create':
                return ct('ev_role_create', { a: a, t: t2 });
            case e.action === 'role.update':
                return ct('ev_role_update', { a: a, t: t2 });
            case e.action === 'role.delete':
                return ct('ev_role_delete', { a: a, t: t2 });
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
    function logBar() {
        var types = ['all', 'team', 'role', 'scope', 'ownership', 'member'];
        var typeOpts = types
            .map(function (t) {
                return (
                    '<option value="' +
                    t +
                    '"' +
                    (S.logType === t ? ' selected' : '') +
                    '>' +
                    ct('logf_type_' + t) +
                    '</option>'
                );
            })
            .join('');
        var actorOpts =
            '<option value="all"' +
            (S.logActor === 'all' ? ' selected' : '') +
            '>' +
            ct('logf_actor_all') +
            '</option>' +
            S.members
                .map(function (m) {
                    return (
                        '<option value="' +
                        esc(m.username) +
                        '"' +
                        (S.logActor === m.username ? ' selected' : '') +
                        '>' +
                        esc(m.username) +
                        '</option>'
                    );
                })
                .join('');
        return (
            '<div class="logbar"><select id="logType">' +
            typeOpts +
            '</select><select id="logActor">' +
            actorOpts +
            '</select>' +
            (logFiltered()
                ? '<button class="btn ghost sm" id="logClear">' + ct('log_clear') + '</button>'
                : '') +
            '<span class="spacer"></span><button class="btn sec sm" id="logExport">' +
            ct('log_export') +
            '</button></div>'
        );
    }
    function renderSecurity() {
        var evs = S.logEvents || [];
        var rows;
        if (!evs.length) {
            rows =
                '<div class="empty" style="border:0"><div class="e1">' +
                ct(logFiltered() ? 'log_filtered_empty' : 'sec_empty') +
                '</div>' +
                (logFiltered()
                    ? '<button class="btn ghost sm" id="logClear2">' + ct('log_clear') + '</button>'
                    : '<div class="e2">' + ct('sec_empty2') + '</div>') +
                '</div>';
        } else {
            rows = evs
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
        var pager =
            '<div class="pager"><span>' +
            ct('log_count_loaded', { n: evs.length }) +
            '</span>' +
            (S.logMore
                ? '<button class="btn sec sm" id="logMore">' + ct('log_more') + '</button>'
                : '') +
            '</div>';
        $('secBox').innerHTML = logBar() + rows + (evs.length ? pager : '');
        var ts = $('logType');
        if (ts)
            ts.onchange = function () {
                S.logType = ts.value;
                loadSecurity();
            };
        var as = $('logActor');
        if (as)
            as.onchange = function () {
                S.logActor = as.value;
                loadSecurity();
            };
        ['logClear', 'logClear2'].forEach(function (id) {
            var b = $(id);
            if (b)
                b.onclick = function () {
                    S.logType = 'all';
                    S.logActor = 'all';
                    loadSecurity();
                };
        });
        var ex = $('logExport');
        if (ex) ex.onclick = exportLog;
        var more = $('logMore');
        if (more)
            more.onclick = function () {
                more.disabled = true;
                fetchLogPage(false);
            };
    }

    boot();
})();
