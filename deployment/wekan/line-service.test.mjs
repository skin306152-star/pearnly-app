import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { lineRoute, verifyLine } from './line-service.mjs';
import { exposeAttachmentWriter } from './install.mjs';

test('LINE signatures bind identity, method, path and expiry', () => {
    const secret = 'local-test-secret'.repeat(3);
    const path = '/_pearnly/line/context';
    const encoded = Buffer.from(
        JSON.stringify({
            method: 'GET',
            path,
            expires: 1020,
            identity: { user_id: 'u', tenant_id: 't', is_platform_admin: false },
        })
    ).toString('base64url');
    const headers = {
        'x-pearnly-line': encoded,
        'x-pearnly-line-signature': createHmac('sha256', secret).update(encoded).digest('hex'),
    };
    assert.equal(verifyLine(headers, 'GET', path, secret, 1000000).identity.user_id, 'u');
    assert.throws(() => verifyLine(headers, 'POST', path, secret, 1000000));
    assert.throws(() => verifyLine(headers, 'GET', path + '/other', secret, 1000000));
    assert.throws(() => verifyLine(headers, 'GET', path, secret, 1021000));
    assert.throws(() =>
        verifyLine({ ...headers, 'x-pearnly-line': encoded + 'a' }, 'GET', path, secret, 1000000)
    );
});

test('only the owner workflow native routes are exposed', () => {
    assert.equal(lineRoute('POST', '/_pearnly/line/api/boards/b/lists/l/cards'), 'native');
    assert.equal(lineRoute('PUT', '/_pearnly/line/api/boards/b/lists/l/cards/c'), 'native');
    assert.equal(lineRoute('DELETE', '/_pearnly/line/api/boards/b'), null);
    assert.equal(lineRoute('POST', '/_pearnly/line/api/users'), null);
    assert.equal(lineRoute('GET', '/_pearnly/line/context/../private'), null);
    assert.equal(lineRoute('POST', '/_pearnly/line/api/boards/b/members/u'), null);
});

test('attachment installer preserves the native writer and rejects upstream drift', () => {
    const source =
        'const files = new FilesCollection({collectionName:"attachments", onAfterUpload(){ audit(); }});';
    const output = exposeAttachmentWriter(source);
    assert.match(output, /globalThis\.__pearnlyAttachments=new FilesCollection/);
    assert.match(output, /onAfterUpload\(\)\{ audit\(\); \}/);
    assert.throws(() => exposeAttachmentWriter('const files = {};'));
    assert.throws(() =>
        exposeAttachmentWriter(source + source.replace('const files', 'const other'))
    );
});
