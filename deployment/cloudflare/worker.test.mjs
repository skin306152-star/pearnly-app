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

test('dynamic pages and API responses bypass edge and browser caches', async () => {
    let observed;
    const previous = globalThis.fetch;
    globalThis.fetch = async (request, options) => {
        observed = { request, options };
        return new Response('ok', { headers: { 'Cache-Control': 'max-age=14400' } });
    };
    try {
        for (const path of [
            '/home/dms-booking?credentials=dms',
            '/api/line/dms-booking/config',
            '/api/line/dms-credentials',
            '/static/installers/latest.json',
        ]) {
            const response = await worker.fetch(new Request('https://pearnly.com' + path));
            assert.equal(observed.options.cache, 'no-store', path);
            assert.equal(response.headers.get('cache-control'), 'no-store', path);
        }
        const response = await worker.fetch(new Request('https://pearnly.com/api/line/dms-booking/auth', {
            method: 'POST', body: '{}', headers: { 'Content-Type': 'application/json' },
        }));
        assert.equal(observed.request.method, 'POST');
        assert.equal(await observed.request.text(), '{}');
        assert.equal(observed.options.cache, 'no-store');
        assert.equal(response.headers.get('cache-control'), 'no-store');
    } finally {
        globalThis.fetch = previous;
    }
});

test('versioned assets retain caching and private origin paths remain blocked', async () => {
    let options;
    const previous = globalThis.fetch;
    globalThis.fetch = async (_request, value) => {
        options = value;
        return new Response('asset');
    };
    try {
        await worker.fetch(new Request('https://pearnly.com/static/dms-booking-edit/dms-booking-api.js?v=6'));
        assert.equal(options.cf.cacheTtlByStatus['200-299'], 86400);
        assert.equal(options.cf.cacheTtlByStatus['400-599'], -1);
        assert.equal((await worker.fetch(new Request('https://pearnly.com/internal/x'))).status, 404);
        assert.equal((await worker.fetch(new Request('https://pearnly.com/config.env'))).status, 404);
    } finally {
        globalThis.fetch = previous;
    }
});
