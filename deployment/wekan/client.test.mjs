import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('./client.js', import.meta.url), 'utf8');

function page(fetch) {
    let click;
    const navigations = [];
    const alerts = [];
    const context = {
        window: {
            fetch,
            Meteor: {
                logout() {
                    throw new Error('native logout reloads before bridge revocation');
                },
            },
            location: { assign: (url) => navigations.push(url) },
        },
        document: {
            addEventListener(_name, handler, capture) {
                assert.equal(capture, true);
                click = handler;
            },
            createElement: () => ({ setAttribute() {} }),
            body: { prepend: (element) => alerts.push(element.textContent) },
        },
        setTimeout() {},
    };
    vm.runInNewContext(source, context);
    return {
        click() {
            let intercepted = 0;
            click({
                target: { closest: () => true },
                preventDefault: () => intercepted++,
                stopImmediatePropagation: () => intercepted++,
            });
            assert.equal(intercepted, 2);
        },
        navigations,
        alerts,
    };
}

test('logout waits for bridge revocation before returning to COWORK', async () => {
    let resolve;
    const response = new Promise((done) => (resolve = done));
    const p = page((url, options) => {
        assert.equal(url, '/_pearnly/logout');
        assert.equal(options.method, 'POST');
        return response;
    });
    p.click();
    assert.deepEqual(p.navigations, []);
    resolve({ ok: true, json: async () => ({ url: 'https://pearnly.com/cowork' }) });
    await new Promise(setImmediate);
    assert.deepEqual(p.navigations, ['https://pearnly.com/cowork']);
    assert.deepEqual(p.alerts, []);
});

test('failed revocation leaves the page with a retry message', async () => {
    const p = page(async () => ({ ok: false }));
    p.click();
    await new Promise(setImmediate);
    assert.deepEqual(p.navigations, []);
    assert.equal(p.alerts.length, 1);
});
