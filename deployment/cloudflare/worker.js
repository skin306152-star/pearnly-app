/* global URL, URLSearchParams, Response, Headers, Request, fetch */
const ORIGIN = 'https://pearnly-web-112074003592.asia-southeast1.run.app';

export default {
    async fetch(request) {
        const original = new URL(request.url);
        if (/\.(?:py|pyc|env|bak|log|sh|conf)$/.test(original.pathname)) {
            return new Response('Not found', { status: 404 });
        }
        if (original.pathname.startsWith('/internal/')) {
            return new Response('Not found', { status: 404 });
        }
        const state = original.searchParams.get('liff.state') || '';
        const stateQuery = new URLSearchParams(state.slice(state.indexOf('?') + 1));
        const dmsCredentials =
            ['/home/dms-booking', '/login/dms-booking', '/liff/dms-booking'].includes(
                original.pathname
            ) ||
            (['/home', '/login'].includes(original.pathname) &&
                stateQuery.get('credentials') === 'dms') ||
            [
                '/api/line/dms-booking/auth',
                '/api/line/dms-booking/config',
                '/api/line/dms-credentials',
            ].includes(original.pathname);
        const target = new URL(original.pathname + original.search, ORIGIN);
        const headers = new Headers(request.headers);
        headers.delete('host');
        headers.delete('x-serverless-authorization');
        headers.delete('x-pearnly-task-key');
        headers.set('x-forwarded-host', 'pearnly.com');
        headers.set('x-forwarded-proto', 'https');
        const cacheable =
            request.method === 'GET' &&
            original.pathname.startsWith('/static/') &&
            !original.pathname.endsWith('/latest.json') &&
            original.searchParams.has('v');
        const upstream = new Request(target, {
            method: request.method,
            headers,
            body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body,
            redirect: 'manual',
        });
        const response = await fetch(
            upstream,
            dmsCredentials
                ? { cache: 'no-store' }
                : {
                      cf: cacheable
                          ? {
                                cacheEverything: true,
                                cacheTtlByStatus: { '200-299': 86400, '400-599': -1 },
                            }
                          : { cacheTtl: 0 },
                  }
        );
        const result = new Response(response.body, response);
        if (dmsCredentials || original.pathname.endsWith('/latest.json')) {
            result.headers.set('cache-control', 'no-store');
        }
        const location = result.headers.get('location');
        if (location && location.startsWith(ORIGIN + '/')) {
            result.headers.set('location', original.origin + location.slice(ORIGIN.length));
        }
        return result;
    },
};
