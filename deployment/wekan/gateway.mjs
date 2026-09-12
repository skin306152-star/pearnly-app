/* The only public path to WeKan, including attachments and live DDP connections. */
import http from 'node:http';
import https from 'node:https';
import { readFileSync } from 'node:fs';
import { randomBytes, timingSafeEqual } from 'node:crypto';
import { cookieCodec, readCookie, upstreamHeaders } from './cookies.mjs';

const origin = new URL(process.env.PEARNLY_ORIGIN);
const serviceOrigin = new URL(process.env.PEARNLY_SERVICE_ORIGIN || origin);
const publicUrl = new URL(process.env.WORK_BRIDGE_URL);
const backend = new URL(process.env.WEKAN_UPSTREAM || 'http://wekan:8080');
const secret = process.env.WORK_BRIDGE_SECRET || '';
if (secret.length < 32) throw new Error('WORK_BRIDGE_SECRET must contain at least 32 characters');
const secure = publicUrl.protocol === 'https:';
if (!secure && process.env.PEARNLY_ENV !== 'development') throw new Error('HTTPS required');
const codec = cookieCodec(secret);
const clientScript = readFileSync(new URL('./client.js', import.meta.url));
const sessionName = secure ? '__Host-pearnly-work' : 'pearnly-work';
const stateName = secure ? '__Host-pearnly-work-state' : 'pearnly-work-state';
const attrs = `; Path=/; HttpOnly; SameSite=Lax${secure ? '; Secure' : ''}`;
const transport = backend.protocol === 'https:' ? https : http;
const json = (res, status, body) => {
    res.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(body));
};

async function service(path, body) {
    const response = await fetch(new URL('/api/work/service/' + path, serviceOrigin), {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + secret, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(8000),
        redirect: 'error',
    });
    if (!response.ok) throw new Error('service authorization failed');
    return response.json();
}

async function identity(req) {
    const cookie = codec.open(readCookie(req.headers, sessionName), 'session');
    if (!cookie) throw new Error('session required');
    const current = await service('session', { session: cookie.session });
    return { ...current, session: cookie.session };
}

function redirect(res, url, cookies = []) {
    res.writeHead(303, {
        Location: url,
        'Set-Cookie': cookies,
        'Cache-Control': 'no-store',
        'Referrer-Policy': 'no-referrer',
    });
    res.end();
}

async function formBody(req) {
    const chunks = [];
    let size = 0;
    for await (const chunk of req) {
        size += chunk.length;
        if (size > 4096) throw new Error('body too large');
        chunks.push(chunk);
    }
    return new URLSearchParams(Buffer.concat(chunks).toString());
}

function proxy(req, res, current) {
    const upstream = transport.request(
        {
            hostname: backend.hostname,
            port: backend.port,
            method: req.method,
            path: req.url,
            headers: upstreamHeaders(req.headers, current, publicUrl.host, secure),
        },
        (response) => {
            res.writeHead(response.statusCode, {
                ...response.headers,
                'Cache-Control': 'private, no-store',
            });
            response.pipe(res);
        }
    );
    upstream.on('error', () => {
        if (!res.headersSent) json(res, 502, { error: 'work.unavailable' });
        else res.destroy();
    });
    req.on('aborted', () => upstream.destroy());
    res.on('close', () => upstream.destroy());
    req.pipe(upstream);
}

const server = http.createServer(async (req, res) => {
    const path = (req.url || '').split('?')[0];
    // Never accept a Host chosen to point at another upstream or cookie origin.
    if (req.headers.host !== publicUrl.host) return json(res, 421, { error: 'invalid host' });
    try {
        if (path === '/_pearnly/health' && req.method === 'GET') {
            try {
                const ready = await fetch(new URL('/_pearnly/ready', backend), {
                    headers: { Authorization: 'Bearer ' + secret },
                    signal: AbortSignal.timeout(3000),
                    redirect: 'error',
                });
                return json(res, ready.ok ? 200 : 503, { ok: ready.ok });
            } catch {
                return json(res, 503, { ok: false });
            }
        }
        if (path === '/_pearnly/start' && req.method === 'GET') {
            const entry =
                new URL(req.url, publicUrl).searchParams.get('entry') === 'main'
                    ? 'main'
                    : 'cowork';
            const state = randomBytes(32).toString('base64url');
            const cookie = codec.seal({ state, exp: Date.now() + 90000 }, 'state');
            return redirect(res, new URL('/work?entry=' + entry + '&state=' + state, origin).href, [
                `${stateName}=${cookie}${attrs}; Max-Age=90`,
            ]);
        }
        if (path === '/_pearnly/consume' && req.method === 'POST') {
            if (req.headers.origin !== origin.origin)
                return json(res, 403, { error: 'invalid origin' });
            const pending = codec.open(readCookie(req.headers, stateName), 'state');
            const body = await formBody(req);
            const state = body.get('state') || '';
            if (
                !pending ||
                state.length !== pending.state.length ||
                !timingSafeEqual(Buffer.from(state), Buffer.from(pending.state))
            )
                return json(res, 401, { error: 'invalid state' });
            const data = await service('consume', { ticket: body.get('ticket'), state });
            const exp = Date.parse(data.expires_at);
            const session = codec.seal({ session: data.session, exp }, 'session');
            return redirect(res, '/', [
                `${sessionName}=${session}${attrs}; Max-Age=${Math.max(0, Math.floor((exp - Date.now()) / 1000))}`,
                `${stateName}=${attrs}; Max-Age=0`,
                ...['meteor_login_token', 'meteor_user_id', 'meteor_login_token_expires'].map(
                    (name) => `${name}=${attrs}; Max-Age=0`
                ),
            ]);
        }
        if (path === '/_pearnly/logout' && req.method === 'POST') {
            if (req.headers.origin !== publicUrl.origin)
                return json(res, 403, { error: 'invalid origin' });
            const cookie = codec.open(readCookie(req.headers, sessionName), 'session');
            if (cookie) await service('revoke', { session: cookie.session });
            const url = new URL('/cowork', origin).href;
            const cookies = [
                sessionName,
                'meteor_login_token',
                'meteor_user_id',
                'meteor_login_token_expires',
            ].map((name) => `${name}=${attrs}; Max-Age=0`);
            if (req.headers.accept?.includes('application/json')) {
                res.setHeader('Set-Cookie', cookies);
                return json(res, 200, { url });
            }
            return redirect(res, url, cookies);
        }
        const current = await identity(req);
        if (path === '/_pearnly/client.js' && req.method === 'GET') {
            res.writeHead(200, {
                'Content-Type': 'application/javascript',
                'Cache-Control': 'no-store',
            });
            return res.end(clientScript);
        }
        proxy(req, res, current);
    } catch {
        if (req.method === 'GET' && req.headers.accept?.includes('text/html'))
            return redirect(res, new URL('/work', origin).href);
        json(res, 401, { error: 'work.session_expired' });
    }
});

server.on('upgrade', async (req, socket, head) => {
    try {
        if (req.headers.host !== publicUrl.host || req.headers.origin !== publicUrl.origin)
            throw new Error('invalid origin');
        const current = await identity(req);
        const upstream = transport.request({
            hostname: backend.hostname,
            port: backend.port,
            path: req.url,
            headers: upstreamHeaders(req.headers, current, publicUrl.host, secure),
        });
        upstream.on('upgrade', (response, peer, peerHead) => {
            socket.write(`HTTP/1.1 ${response.statusCode} Switching Protocols\r\n`);
            for (const [name, value] of Object.entries(response.headers))
                socket.write(`${name}: ${value}\r\n`);
            socket.write('\r\n');
            if (peerHead.length) socket.write(peerHead);
            if (head.length) peer.write(head);
            socket.pipe(peer).pipe(socket);
            let checking = false;
            const timer = setInterval(async () => {
                if (checking) return;
                checking = true;
                try {
                    await service('session', { session: current.session });
                } catch {
                    peer.destroy();
                    socket.destroy();
                } finally {
                    checking = false;
                }
            }, 5000);
            const close = () => {
                clearInterval(timer);
                peer.destroy();
                socket.destroy();
            };
            socket.on('close', close).on('error', close);
            peer.on('close', close).on('error', close);
        });
        upstream.on('response', () => socket.destroy());
        upstream.on('error', () => socket.destroy());
        socket.on('error', () => upstream.destroy());
        upstream.end();
    } catch {
        socket.end('HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n');
    }
});
server.listen(Number(process.env.PORT || 8096), '0.0.0.0');
