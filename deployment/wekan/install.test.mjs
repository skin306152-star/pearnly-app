import test from 'node:test';
import assert from 'node:assert/strict';
import {
    awaitNativeCreation,
    includeIdentityHeaders,
    allowUsernameInvitation,
    installBrandAssets,
    REPLACED_BRAND_FILES,
    SERVED_BRAND_FILES,
} from './install.mjs';
import vm from 'node:vm';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

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
