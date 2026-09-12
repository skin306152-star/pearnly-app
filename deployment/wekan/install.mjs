/* Fail closed if an upstream release changes the native account-creation methods.
 * Meteor 3 account creation is asynchronous. The pinned bundle omits await in
 * these two native methods; our bridge introduces an additional async account write.
 * AST insertion preserves every native permission check and all surrounding code.
 */
import { parse } from 'acorn';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

function walk(node, visit, parent) {
    if (!node || typeof node !== 'object') return;
    if (typeof node.type === 'string') visit(node, parent);
    for (const value of Object.values(node)) {
        if (Array.isArray(value)) value.forEach((child) => walk(child, visit, node));
        else if (value && typeof value === 'object') walk(value, visit, node);
    }
}

export function awaitNativeCreation(source) {
    const tree = parse(source, { ecmaVersion: 'latest', sourceType: 'script' });
    const expected = new Map([
        ['setCreateUser', 0],
        ['inviteUserToBoard', 0],
    ]);
    const insertions = [];
    walk(tree, (node) => {
        const name = node.type === 'Property' && (node.key.name || node.key.value);
        if (!expected.has(name)) return;
        if (!node.value.async) throw new Error('Native account method is no longer async');
        let calls = 0;
        let enrollments = 0;
        walk(node.value.body, (call, parent) => {
            if (
                call.type === 'CallExpression' &&
                call.callee.type === 'MemberExpression' &&
                ['createUser', 'sendEnrollmentEmail'].includes(call.callee.property.name)
            ) {
                if (call.callee.property.name === 'createUser') calls += 1;
                else enrollments += 1;
                if (parent.type !== 'AwaitExpression') insertions.push(call.start);
            }
        });
        if (calls !== 1) throw new Error('Native account creation shape changed: ' + name);
        if (enrollments !== (name === 'inviteUserToBoard' ? 1 : 0))
            throw new Error('Native enrollment shape changed: ' + name);
        expected.set(name, expected.get(name) + 1);
    });
    if ([...expected.values()].some((count) => count !== 1))
        throw new Error('Native account methods missing or duplicated');
    for (const offset of insertions.sort((a, b) => b - a))
        source = source.slice(0, offset) + 'await ' + source.slice(offset);
    parse(source, { ecmaVersion: 'latest', sourceType: 'script' });
    return source;
}

// Meteor's SockJS transport deliberately copies a fixed header list.
// Extend that list with only the two identity headers set by our private proxy.
export function includeIdentityHeaders(source) {
    const tree = parse(source, { ecmaVersion: 'latest', sourceType: 'script' });
    const matches = [];
    walk(tree, (node) => {
        if (node.type !== 'ArrayExpression') return;
        const values = node.elements.map((item) => item?.value);
        if (!values.includes('x-forwarded-for') || !values.includes('user-agent')) return;
        matches.push(node);
    });
    if (matches.length !== 1) throw new Error('Native WebSocket header list changed');
    const list = matches[0];
    const missing = ['x-pearnly-session', 'x-pearnly-user-id'].filter(
        (name) => !list.elements.some((item) => item.value === name)
    );
    const insertion = missing.map((name) => JSON.stringify(name)).join(',');
    return insertion
        ? source.slice(0, list.start + 1) + insertion + ',' + source.slice(list.start + 1)
        : source;
}

// Pearnly permits username-only accounts. Native invitation already adds the
// member, then unconditionally dereferences its email and reports a false failure.
// Skip only that optional notification when this recipient has no email.
export function allowUsernameInvitation(source) {
    const tree = parse(source, { ecmaVersion: 'latest', sourceType: 'script' });
    const patches = [];
    walk(tree, (node) => {
        if (node.type !== 'Property' || (node.key.name || node.key.value) !== 'inviteUserToBoard')
            return;
        for (const statement of node.value.body.body) {
            if (statement.type !== 'TryStatement') continue;
            const recipients = new Set();
            walk(statement.block, (member) => {
                if (
                    member.type === 'MemberExpression' &&
                    member.property.name === 'address' &&
                    member.object.type === 'MemberExpression' &&
                    member.object.property.value === 0 &&
                    member.object.object.type === 'MemberExpression' &&
                    member.object.object.property.name === 'emails'
                ) {
                    const recipient = member.object.object.object;
                    if (recipient.type !== 'Identifier')
                        throw new Error('Native invitee shape changed');
                    recipients.add(recipient.name);
                }
            });
            if (recipients.size === 1)
                patches.push({ offset: statement.start, user: [...recipients][0] });
        }
    });
    if (patches.length !== 1) throw new Error('Native invitation email block changed');
    const { offset, user } = patches[0];
    const guard = `if(!${user}.emails?.[0]?.address)return{username:${user}.username,email:null};`;
    return source.slice(0, offset) + guard + source.slice(offset);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
    const root = process.argv[2] || '/build/programs/server';
    const manifestPath = root + '/program.json';
    const manifest = JSON.parse(readFileSync(manifestPath));
    const index = manifest.load.findIndex((entry) => entry.path === 'app/app.js');
    if (index < 0 || manifest.load.some((entry) => entry.path === 'packages/pearnly-bridge.js'))
        throw new Error('Unexpected Meteor manifest');
    const appPath = root + '/app/app.js';
    writeFileSync(
        appPath,
        allowUsernameInvitation(awaitNativeCreation(readFileSync(appPath, 'utf8')))
    );
    const ddpPath =
        root + '/npm/node_modules/meteor/ddp-server/node_modules/sockjs/lib/transport.js';
    writeFileSync(ddpPath, includeIdentityHeaders(readFileSync(ddpPath, 'utf8')));
    manifest.load.splice(index, 0, { path: 'packages/pearnly-bridge.js' });
    writeFileSync(manifestPath, JSON.stringify(manifest));
}
