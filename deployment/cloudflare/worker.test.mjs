import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('./worker.js', import.meta.url));
const worker = (await import('data:text/javascript;base64,' + source.toString('base64'))).default;
// Node requires a duplex hint for streams; Workers accepts them without it.
const NativeRequest = globalThis.Request;
globalThis.Request = class extends NativeRequest {
    constructor(input, options) {
        super(input, { ...options, duplex: 'half' });
    }
};

test('DMS portal, credentials and LIFF auth bypass cache', async () => {
    let options;
    const previous = globalThis.fetch;
    globalThis.fetch = async (_request, value) => {
        options = value;
        return new Response('ok', { headers: { 'cache-control': 'max-age=14400' } });
    };
    try {
        for (const path of [
            '/dms',
            '/dms/',
            '/dms/records',
            '/api/dms/geo?level=province',
            '/api/dms/customer-fields',
            '/api/line/dms-booking/paints?nonce=draft-1',
            '/api/line/dms-booking/draft?nonce=draft-1',
            '/api/line/dms-portal/ticket',
            '/home/dms-booking?credentials=dms',
            '/login/dms-booking',
            '/liff/dms-booking',
            '/home?liff.state=%2Fdms-booking%3Fcredentials%3Ddms',
            '/login?liff.state=%3Fcredentials%3Ddms',
            '/api/line/dms-booking/config',
            '/api/line/dms-booking/auth',
            '/api/line/dms-credentials',
        ]) {
            const response = await worker.fetch(new Request('https://pearnly.com' + path));
            assert.equal(options.cache, 'no-store', path);
            assert.equal(response.headers.get('cache-control'), 'no-store', path);
        }
    } finally {
        globalThis.fetch = previous;
    }
});

test('other products retain original fetch options and response headers', async () => {
    let options;
    const previous = globalThis.fetch;
    try {
        for (const header of [
            undefined,
            'private, max-age=300',
            'public, max-age=31536000, immutable',
            'no-store',
        ]) {
            globalThis.fetch = async (_request, value) => {
                options = value;
                return new Response('ok', { headers: header ? { 'cache-control': header } : {} });
            };
            for (const path of [
                '/',
                '/home',
                '/login',
                '/erp',
                '/cowork',
                '/ai',
                '/daily',
                '/pos',
                '/cashier',
                '/earn',
                '/dms-pick',
                '/api/history',
                '/api/uploads/image',
                '/api/erp/agent/lease',
                '/api/billing',
                '/home?liff.state=%3Fflow%3Derp-intake%26draft%3Dx',
                '/static/brand/logo.png',
            ]) {
                for (const method of ['GET', 'POST']) {
                    const response = await worker.fetch(
                        new Request('https://pearnly.com' + path, { method })
                    );
                    assert.deepEqual(options, { cf: { cacheTtl: 0 } }, path);
                    assert.equal(response.headers.get('cache-control'), header ?? null, path);
                }
            }
        }
        await worker.fetch(new Request('https://pearnly.com/static/dist/pos.js?v=1'));
        assert.equal(options.cf.cacheTtlByStatus['200-299'], 86400);
        assert.equal(options.cf.cacheTtlByStatus['400-599'], -1);
        const latest = await worker.fetch(
            new Request('https://pearnly.com/static/installers/latest.json')
        );
        assert.deepEqual(options, { cf: { cacheTtl: 0 } });
        assert.equal(latest.headers.get('cache-control'), 'no-store');
        assert.equal(
            (await worker.fetch(new Request('https://pearnly.com/internal/x'))).status,
            404
        );
    } finally {
        globalThis.fetch = previous;
    }
});
