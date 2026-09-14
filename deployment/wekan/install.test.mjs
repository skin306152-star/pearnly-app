import test from 'node:test';
import assert from 'node:assert/strict';
import {
    awaitNativeCreation,
    includeIdentityHeaders,
    allowUsernameInvitation,
    installBrandAssets,
    applyThaiOverrides,
    restrictLanguageList,
    LANGUAGE_TAGS,
    REPLACED_BRAND_FILES,
    SERVED_BRAND_FILES,
} from './install.mjs';
import vm from 'node:vm';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

// A stand-in for the bundled Thai block: the same `JSON.parse('<json>')` shape,
// with an apostrophe and a quote so the escape round trip is exercised.
function fakeBundle(pairs) {
    const big = {};
    for (let i = 0; i < 1600; i += 1) big[`filler-${i}`] = 'ข้อความทดสอบ';
    Object.assign(big, pairs);
    const literal = JSON.stringify(big).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    return `chunk(e){e.exports=JSON.parse('${literal}')}`;
}

test('Thai overrides replace the upstream entries and survive the escape round trip', () => {
    const source = fakeBundle({
        template: 'Mẫu',
        yes: 'Có',
        "quote's": 'ข้อความ',
        quoted: 'มี "อัญประกาศ" ในข้อความ',
    });
    const patched = applyThaiOverrides(source, {
        corrections: { template: 'เทมเพลต', yes: 'ใช่' },
        additions: { 'collapse-card': 'ย่อการ์ด' },
    });
    assert.match(patched, /"template":"เทมเพลต"/);
    assert.match(patched, /"yes":"ใช่"/);
    assert.match(patched, /"collapse-card":"ย่อการ์ด"/);
    const parsed = JSON.parse(
        patched
            .slice(patched.indexOf("JSON.parse('") + 12, patched.lastIndexOf("')"))
            .replace(/\\'/g, "'")
            .replace(/\\\\/g, '\\')
    );
    assert.equal(parsed["quote's"], 'ข้อความ');
    assert.equal(parsed.quoted, 'มี "อัญประกาศ" ในข้อความ');
    assert.equal(parsed['filler-0'], 'ข้อความทดสอบ');
    assert.equal(parsed.template, 'เทมเพลต');
    assert.throws(
        () => applyThaiOverrides(source, { corrections: { 'not-in-bundle': 'x' }, additions: {} }),
        /not in the bundle/
    );
    assert.throws(
        () => applyThaiOverrides(source, { corrections: {}, additions: { template: 'x' } }),
        /already upstream/
    );
    assert.throws(
        () => applyThaiOverrides('const a=1;', { corrections: { template: 'x' }, additions: {} }),
        /exactly one Thai/
    );
});

test('the language picker keeps only the Pearnly languages, leaving the table intact', () => {
    const source =
        'const t={getSupportedLanguages:()=>Object.values(A).map(({name:e,code:n,tag:t,rtl:r})=>({name:e,code:n,tag:t,rtl:r})),other:1};';
    const patched = restrictLanguageList(source, LANGUAGE_TAGS);
    const context = {
        A: {
            th: { name: 'ไทย', code: 'th', tag: 'th' },
            ja: { name: '日本語', code: 'ja', tag: 'ja' },
            zh: { name: '简体中文', code: 'zh', tag: 'zh-CN' },
        },
    };
    vm.runInNewContext(patched.replace('const t=', 'result='), context);
    assert.deepEqual(
        Array.from(context.result.getSupportedLanguages(), (entry) => String(entry.tag)).sort(),
        ['th', 'zh-CN']
    );
    assert.equal(context.result.other, 1);
    assert.throws(() => restrictLanguageList('const t={};', LANGUAGE_TAGS), /shape changed/);
});

test('brand assets replace the stock icons and fail closed when upstream moves one', () => {
    const dir = mkdtempSync(path.join(tmpdir(), 'pearnly-brand-'));
    try {
        const source = path.join(dir, 'branding');
        const app = path.join(dir, 'app');
        mkdirSync(source);
        mkdirSync(app);
        for (const name of [...REPLACED_BRAND_FILES, ...SERVED_BRAND_FILES]) {
            writeFileSync(path.join(source, name), `pearnly ${name}`);
            if (REPLACED_BRAND_FILES.includes(name)) writeFileSync(path.join(app, name), 'stock');
        }
        assert.deepEqual(installBrandAssets(app, source), REPLACED_BRAND_FILES);
        assert.equal(readFileSync(path.join(app, 'favicon.ico'), 'utf8'), 'pearnly favicon.ico');
        // The gateway-served images stay in the image, out of the WeKan bundle:
        // its asset server would answer those URLs with the app page instead.
        assert.equal(existsSync(path.join(app, 'pearnly-header-logo.png')), false);
        // An upstream release that renames or drops a stock icon must stop the build.
        rmSync(path.join(app, 'favicon-32x32.png'));
        assert.throws(() => installBrandAssets(app, source), /moved upstream/);
        writeFileSync(path.join(app, 'favicon-32x32.png'), 'stock');
        // ...and so must a brand asset that never made it into the image.
        rmSync(path.join(source, 'pearnly-login-logo.png'));
        assert.throws(() => installBrandAssets(app, source), /Missing Pearnly brand asset/);
    } finally {
        rmSync(dir, { recursive: true, force: true });
    }
});

test('only missing awaits change; native authorization and awaited calls stay intact', () => {
    const src =
        'Meteor.methods({async setCreateUser(o){if(!allowed())throw Error();Accounts.createUser(o)},async inviteUserToBoard(o){if(!canInvite())throw Error();const id=await Accounts.createUser(o);Accounts.sendEnrollmentEmail(id);return id}})';
    const patched = awaitNativeCreation(src);
    assert.equal(
        patched,
        src
            .replace('Accounts.createUser(o)}', 'await Accounts.createUser(o)}')
            .replace('Accounts.sendEnrollmentEmail(id)', 'await Accounts.sendEnrollmentEmail(id)')
    );
    assert.equal(awaitNativeCreation(patched), patched);
    assert.throws(() => awaitNativeCreation('Meteor.methods({})'));
});

test('raw DDP receives only the two additional gateway identity headers', () => {
    const src = "const headerKeys=['x-forwarded-for','user-agent'];";
    const patched = includeIdentityHeaders(src);
    assert.equal(
        patched,
        'const headerKeys=["x-pearnly-session","x-pearnly-user-id",\'x-forwarded-for\',\'user-agent\'];'
    );
    assert.equal(includeIdentityHeaders(patched), patched);
    assert.throws(() => includeIdentityHeaders('const headers=[]'));
});

test('username invitation preserves authorization and membership while omitting absent email', async () => {
    const src = `methods={async inviteUserToBoard(user){
        if(!allowed)throw Error('denied');
        added.push(user.username);
        try{sent.push(user.emails[0].address)}catch(e){throw Error('email-fail')}
        return {username:user.username,email:user.emails[0].address}
    }}`;
    const context = { allowed: true, added: [], sent: [] };
    vm.runInNewContext(allowUsernameInvitation(src), context);
    assert.equal((await context.methods.inviteUserToBoard({ username: 'employee' })).email, null);
    assert.deepEqual(context.added, ['employee']);
    assert.deepEqual(context.sent, []);
    await context.methods.inviteUserToBoard({
        username: 'mail-user',
        emails: [{ address: 'a@example.test' }],
    });
    assert.deepEqual(context.sent, ['a@example.test']);
    context.allowed = false;
    await assert.rejects(context.methods.inviteUserToBoard({ username: 'denied' }));
    assert.deepEqual(context.added, ['employee', 'mail-user']);
    assert.throws(() => allowUsernameInvitation('methods={}'));
});
