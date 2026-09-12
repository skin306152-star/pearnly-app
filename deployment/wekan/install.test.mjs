import test from 'node:test';
import assert from 'node:assert/strict';
import { awaitNativeCreation, includeIdentityHeaders, allowUsernameInvitation } from './install.mjs';
import vm from 'node:vm';

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
    await context.methods.inviteUserToBoard({ username: 'mail-user', emails: [{ address: 'a@example.test' }] });
    assert.deepEqual(context.sent, ['a@example.test']);
    context.allowed = false;
    await assert.rejects(context.methods.inviteUserToBoard({ username: 'denied' }));
    assert.deepEqual(context.added, ['employee', 'mail-user']);
    assert.throws(() => allowUsernameInvitation('methods={}'));
});
