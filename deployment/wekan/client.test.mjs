import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('./client.js', import.meta.url), 'utf8');

// The smallest DOM this script touches: the boot class on <html>, the title and
// the two app-name metas in <head>, the body it prepends errors to, and the
// capture-phase click listener that owns the logout button.
function fakeDom({ title = 'Wekan', appName = 'Wekan', appleName = 'Wekan' } = {}) {
    const classes = new Set();
    const titleNode = { textContent: title };
    const metas = {};
    for (const [name, content] of [
        ['application-name', appName],
        ['apple-mobile-web-app-title', appleName],
    ]) {
        metas[name] = {
            getAttribute: () => content,
            setAttribute: (_key, value) => {
                metas[name].value = value;
            },
        };
    }
    const observers = [];
    return {
        classes,
        titleNode,
        metas,
        observers,
        document: {
            documentElement: {
                classList: {
                    add: (name) => classes.add(name),
                    contains: (name) => classes.has(name),
                },
            },
            head: {},
            body: { prepend() {} },
            querySelector(selector) {
                if (selector === 'head > title') return titleNode;
                const meta = /^meta\[name="(.+)"\]$/.exec(selector);
                return meta ? (metas[meta[1]] ?? null) : null;
            },
            createElement: () => ({ setAttribute() {} }),
        },
        MutationObserver: class {
            constructor(callback) {
                observers.push(callback);
            }
            observe() {}
        },
    };
}

function page(fetch, options = {}) {
    let click;
    let loginCallback;
    const navigations = [];
    const alerts = [];
    const dom = fakeDom(options);
    const context = {
        window: {
            fetch,
            Meteor: {
                startup: (callback) => callback(),
                logout() {
                    throw new Error('native logout reloads before bridge revocation');
                },
            },
            Package: {
                'accounts-base': {
                    Accounts: {
                        callLoginMethod({ userCallback }) {
                            loginCallback = userCallback;
                        },
                    },
                },
            },
            location: { assign: (url) => navigations.push(url) },
        },
        document: Object.assign(dom.document, {
            addEventListener(_name, handler, capture) {
                assert.equal(capture, true);
                click = handler;
            },
            body: { prepend: (element) => alerts.push(element.textContent) },
        }),
        MutationObserver: dom.MutationObserver,
        setTimeout() {},
    };
    vm.runInNewContext(source, context);
    return {
        dom,
        alerts,
        click() {
            let intercepted = 0;
            click({
                target: { closest: () => true },
                preventDefault: () => intercepted++,
                stopImmediatePropagation: () => intercepted++,
            });
            assert.equal(intercepted, 2);
        },
        login(error) {
            assert.ok(loginCallback, 'the page did not ask to log in');
            loginCallback(error);
        },
        navigations,
    };
}

test('the boot cover is lifted only after the Pearnly login succeeds', () => {
    const p = page(async () => ({ ok: true }));
    assert.equal(p.dom.classes.has('pearnly-ready'), false);
    p.login(undefined);
    assert.equal(p.dom.classes.has('pearnly-ready'), true);
});

test('a failed login shows the retry message and still lifts the cover', () => {
    const p = page(async () => ({ ok: true }));
    p.login(new Error('pearnly-login-required'));
    assert.equal(p.dom.classes.has('pearnly-ready'), true);
    assert.equal(p.alerts.length, 1);
});

test('the stock product name is replaced in the tab and the app-name metas', () => {
    const p = page(async () => ({ ok: true }), {
        title: 'Wekan - บอร์ดทั้งหมด / ติดดาว',
    });
    assert.equal(p.dom.titleNode.textContent, 'Pearnly - บอร์ดทั้งหมด / ติดดาว');
    assert.equal(p.dom.metas['application-name'].value, 'Pearnly');
    assert.equal(p.dom.metas['apple-mobile-web-app-title'].value, 'Pearnly');
});

test('a board title keeps its own name and only the product segment is renamed', () => {
    const p = page(async () => ({ ok: true }), { title: 'งานขาย - WeKan' });
    assert.equal(p.dom.titleNode.textContent, 'งานขาย - Pearnly');
});

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
