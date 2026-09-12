import test from 'node:test';
import assert from 'node:assert/strict';
import { awaitNativeCreation, includeIdentityHeaders } from './install.mjs';

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
