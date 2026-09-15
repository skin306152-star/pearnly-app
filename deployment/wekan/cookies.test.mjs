import test from 'node:test';
import assert from 'node:assert/strict';
import { cookieCodec, upstreamHeaders } from './cookies.mjs';

test('session encryption rejects tampering, expired state and cross-purpose reuse', () => {
    const codec = cookieCodec('a'.repeat(32));
    const value = { session: 'opaque', exp: Date.now() + 10000 };
    const sealed = codec.seal(value, 'session');
    assert.deepEqual(codec.open(sealed, 'session'), value);
    assert.equal(codec.open(sealed, 'state'), null);
    assert.equal(codec.open('A' + sealed.slice(1), 'session'), null);
    assert.equal(cookieCodec('b'.repeat(32)).open(sealed, 'session'), null);
    assert.equal(codec.open(codec.seal({ exp: 1 }, 'state'), 'state'), null);
});

test('proxy ignores every client-supplied identity and forwarding header', () => {
    const headers = upstreamHeaders(
        {
            'x-pearnly-user-id': 'victim',
            'x-pearnly-session': 'stolen',
            'x-pearnly-admin': 'true',
            'x-forwarded-for': '127.0.0.1',
            'x-forwarded-host': 'evil',
            forwarded: 'evil',
            cookie: 'ordinary-cookie',
        },
        { user_id: 'alice', session: 'alice-session' },
        'work.pearnly.com',
        true
    );
    assert.equal(headers['x-pearnly-user-id'], 'alice');
    assert.equal(headers['x-pearnly-session'], 'alice-session');
    assert.equal(headers.host, 'work.pearnly.com');
    for (const name of ['x-pearnly-admin', 'x-forwarded-for', 'x-forwarded-host', 'forwarded'])
        assert.equal(headers[name], undefined);
});
