/* Loaded as a server-only Meteor package before the native app package.
 * The integration wraps identity creation; native board roles/methods stay in WeKan.
 */
/* global Package, process, URL, fetch, AbortSignal */
Package['core-runtime'].queue('pearnly-bridge', function () {
    const { Meteor } = Package.meteor;
    const { Accounts } = Package['accounts-base'];
    const { WebApp, WebAppInternals } = Package.webapp;
    const secret = process.env.WORK_BRIDGE_SECRET || '';
    const origin = new URL(process.env.PEARNLY_ORIGIN);
    const serviceOrigin = new URL(process.env.PEARNLY_SERVICE_ORIGIN || origin);
    const trusted = (process.env.PEARNLY_TRUSTED_PROXY_IPS || '').split(',').map((ip) => ip.trim());
    if (secret.length < 32 || !trusted.filter(Boolean).length)
        throw new Error('Pearnly bridge configuration required');
    const httpActor = new Meteor.EnvironmentVariable();
    function actorId() {
        try {
            return Meteor.userId() || httpActor.get();
        } catch {
            return httpActor.get();
        }
    }

    async function service(path, body) {
        const response = await fetch(new URL('/api/work/service/' + path, serviceOrigin), {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + secret, 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            signal: AbortSignal.timeout(8000),
            redirect: 'error',
        });
        const data = await response.json();
        if (!response.ok)
            throw new Meteor.Error('pearnly-account', data.detail || 'Pearnly account unavailable');
        return data;
    }

    // A bridge-created identity is explicitly provided by the authenticated server
    // handler below, never by public Accounts.createUser options.
    const register = Accounts.onCreateUser;
    Accounts.onCreateUser = function (nativeHook) {
        return register.call(this, async (options, user) => {
            if (user.authenticationMethod === 'pearnly' && user.services?.pearnly?.id) {
                const result = await nativeHook({ ...options, from: 'admin' }, user);
                result.isAdmin = user.services.pearnly.platformAdmin === true;
                result.profile = { ...result.profile, language: 'th' };
                return result;
            }
            const caller = actorId();
            if (!caller) throw new Meteor.Error('pearnly-login-required');
            const actor = await Meteor.users.findOneAsync(caller);
            if (!actor?.services?.pearnly?.id) throw new Meteor.Error('pearnly-login-required');
            const result = await nativeHook(options, user);
            if (!result) return result;
            if (options.password && typeof options.password !== 'string')
                throw new Meteor.Error('pearnly-use-cowork-signup');
            const account = await service('members', {
                actor_id: actor.services.pearnly.id,
                request_id: Accounts._hashLoginToken(
                    actor.services.pearnly.id +
                        '\0' +
                        (options.username || options.email).trim().toLowerCase()
                )
                    .replace(/\+/g, '-')
                    .replace(/\//g, '_')
                    .replace(/=+$/, ''),
                account: options.username || options.email,
                email: options.email || null,
                password: options.password || null,
                display_name: user.profile?.fullname || options.username || '',
            });
            result.services = { ...result.services };
            result.services.pearnly = {
                id: account.user_id,
                tenantId: account.tenant_id,
                creatorId: actor.services.pearnly.id,
            };
            delete result.services.password;
            result.authenticationMethod = 'pearnly';
            result.profile = { ...result.profile, language: actor.profile?.language || 'th' };
            // WeKan's native code chooses its site-admin flag. It is never sent
            // back as a Pearnly owner/admin grant.
            return result;
        });
    };

    async function nativeUser(identity) {
        let user = await Meteor.users.findOneAsync({ 'services.pearnly.id': identity.user_id });
        if (!user) {
            const id = await Accounts.insertUserDoc(
                {},
                {
                    username: identity.username,
                    authenticationMethod: 'pearnly',
                    profile: { fullname: identity.display_name, language: 'th' },
                    ...(identity.email
                        ? { emails: [{ address: identity.email, verified: false }] }
                        : {}),
                    services: {
                        pearnly: {
                            id: identity.user_id,
                            tenantId: identity.tenant_id,
                            platformAdmin: identity.is_platform_admin === true,
                        },
                    },
                }
            ).catch(async (error) => {
                // Two tabs may materialize the same immutable Pearnly identity.
                const existing = await Meteor.users.findOneAsync({
                    'services.pearnly.id': identity.user_id,
                });
                if (existing) return existing._id;
                throw error;
            });
            user = await Meteor.users.findOneAsync(id);
        }
        if (!user || user.loginDisabled) throw new Meteor.Error('pearnly-account-disabled');
        return user;
    }

    function trustedPeer(req) {
        return trusted.includes((req.socket?.remoteAddress || '').replace(/^::ffff:/, ''));
    }

    // Resolve registered COWORK users before the native new-account branch.
    // An invitation never resets an existing account or changes its COWORK role.
    const createNativeUser = Accounts.createUser;
    Accounts.createUser = async function (options) {
        if (!options.password && options.email && actorId()) {
            try {
                const identity = await service('lookup', { account: options.email });
                return (await nativeUser({ ...identity, email: options.email }))._id;
            } catch (error) {
                if (error.reason !== 'work.account_not_found') throw error;
            }
        }
        return createNativeUser.call(this, options);
    };
    Accounts.sendEnrollmentEmail = async function (userId) {
        const user = await Meteor.users.findOneAsync(userId);
        const identity = user?.services?.pearnly;
        if (!identity?.id) throw new Meteor.Error('pearnly-invitation-unavailable');
        if (!identity.creatorId) return { ok: true }; // Registered Pearnly user already has a login.
        return service('enroll', { actor_id: identity.creatorId, user_id: identity.id });
    };

    Meteor.startup(async () => {
        await Meteor.users
            .rawCollection()
            .createIndex({ 'services.pearnly.id': 1 }, { unique: true, sparse: true });
        Meteor.settings.public.headerLoginId = 'x-pearnly-user-id';
        Accounts.config({ forbidClientAccountCreation: true });
        Meteor.onConnection(async (connection) => {
            const id = connection.httpHeaders?.['x-pearnly-user-id'];
            if (!id) return connection.close();
            let closed = false;
            let observer;
            connection.onClose(() => {
                closed = true;
                observer?.stop();
            });
            observer = await Meteor.users
                .find({ 'services.pearnly.id': id }, { fields: { loginDisabled: 1 } })
                .observeChangesAsync({
                    added(_id, fields) {
                        if (fields.loginDisabled) connection.close();
                    },
                    changed(_id, fields) {
                        if (fields.loginDisabled) connection.close();
                    },
                    removed() {
                        connection.close();
                    },
                });
            if (closed) observer.stop();
        });
        Accounts.registerLoginHandler('pearnly', async function (options) {
            if (options.pearnly !== true) return undefined;
            const session = this.connection?.httpHeaders?.['x-pearnly-session'];
            if (!session) throw new Meteor.Error('pearnly-login-required');
            const identity = await service('session', { session });
            return { userId: (await nativeUser(identity))._id };
        });
        Accounts.validateLoginAttempt(async (attempt) => {
            if (!attempt.allowed || !attempt.user) return false;
            const session = attempt.connection?.httpHeaders?.['x-pearnly-session'];
            if (!session) return false;
            const identity = await service('session', { session });
            return attempt.user.services?.pearnly?.id === identity.user_id;
        });
        // Local password changes must use the shared Pearnly account, so there is
        // never a second independently valid password for the same employee.
        for (const name of ['changePassword', 'setPassword', 'resetPassword', 'forgotPassword']) {
            if (Meteor.server.method_handlers[name]) {
                Meteor.server.method_handlers[name] = function () {
                    throw new Meteor.Error(
                        'pearnly-password',
                        'กรุณาจัดการรหัสผ่านที่ Pearnly COWORK'
                    );
                };
            }
        }
        WebApp.rawHandlers.use(async (req, res, next) => {
            try {
                if (!trustedPeer(req)) {
                    res.writeHead(403);
                    res.end();
                    return;
                }
                if (
                    req.url === '/_pearnly/ready' &&
                    req.headers.authorization === 'Bearer ' + secret
                ) {
                    await Meteor.users.findOneAsync({}, { fields: { _id: 1 } });
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end('{"ok":true}');
                    return;
                }
                // Public WeKan registration is replaced by Pearnly signup.
                // Native permission-checked admin creation and board invitations
                // remain available; this route has no member-management gate.
                if ((req.url || '').split('?')[0] === '/users/register') {
                    res.writeHead(403);
                    res.end();
                    return;
                }
                const session = req.headers['x-pearnly-session'];
                const identity = await service('session', { session });
                if (identity.user_id !== req.headers['x-pearnly-user-id'])
                    throw new Error('identity mismatch');
                const user = await nativeUser(identity);
                const cookies = Object.fromEntries(
                    (req.headers.cookie || '').split(';').map((part) => {
                        const i = part.indexOf('=');
                        return [part.slice(0, i).trim(), decodeURIComponent(part.slice(i + 1))];
                    })
                );
                const url = new URL(req.url, process.env.ROOT_URL);
                const tokens = [
                    req.headers.authorization?.replace(/^Bearer\s+/i, ''),
                    req.headers['x-auth-token'],
                    url.searchParams.get('authToken'),
                    url.searchParams.get('access_token'),
                    cookies.meteor_login_token,
                    cookies.wekan_login_token,
                ].filter(Boolean);
                const allowed = new Set(
                    (user.services?.resume?.loginTokens || []).map((item) => item.hashedToken)
                );
                if (tokens.some((token) => !allowed.has(Accounts._hashLoginToken(token))))
                    throw new Error('HTTP identity mismatch');
                if (req.headers['x-user-id'] && req.headers['x-user-id'] !== user._id)
                    throw new Error('API identity mismatch');
                if (req.method === 'GET' && req.headers.accept?.includes('text/html')) {
                    const stamped = Accounts._generateStampedLoginToken();
                    const hashed = Accounts._hashStampedToken(stamped);
                    const expires = Accounts._tokenExpiration(stamped.when).toISOString();
                    await Meteor.users.updateAsync(user._id, {
                        $push: { 'services.resume.loginTokens': hashed },
                    });
                    const secure = process.env.ROOT_URL.startsWith('https:') ? '; Secure' : '';
                    const attrs = '; Path=/; HttpOnly; SameSite=Lax' + secure;
                    res.setHeader('Set-Cookie', [
                        `meteor_login_token=${encodeURIComponent(stamped.token)}${attrs}`,
                        `meteor_user_id=${encodeURIComponent(user._id)}${attrs}`,
                        `meteor_login_token_expires=${encodeURIComponent(expires)}${attrs}`,
                    ]);
                }
                httpActor.withValue(user._id, next);
            } catch {
                res.writeHead(401, { 'Cache-Control': 'no-store' });
                res.end();
            }
        });
        WebAppInternals.registerBoilerplateDataCallback('pearnly-return', (_req, data) => {
            data.head =
                (data.head || '') +
                '<script src="/_pearnly/client.js" defer></script>' +
                '<style>#pearnly-return{position:fixed;bottom:12px;left:12px;z-index:10000;padding:8px 12px;background:#fff;color:#222;border:1px solid #ddd;border-radius:6px;text-decoration:none;font:14px sans-serif}</style>';
            data.body =
                (data.body || '') +
                `<a id="pearnly-return" href="${origin.origin}/cowork">← COWORK</a>`;
            return data;
        });
    });
    return {};
});
