/* Fail closed if an upstream release changes the native account-creation methods.
 * Meteor 3 account creation is asynchronous. The pinned bundle omits await in
 * these two native methods; our bridge introduces an additional async account write.
 * AST insertion preserves every native permission check and all surrounding code.
 */
import { parse } from 'acorn';
import {
    copyFileSync,
    existsSync,
    readFileSync,
    readdirSync,
    statSync,
    writeFileSync,
} from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// The picker offers these; every other language stays loadable for profiles
// that already selected one.
export const LANGUAGE_TAGS = ['th', 'en', 'zh-CN'];
// A phrase that identifies the file carrying the Thai text.
const THAI_MARKER = 'บอร์ดทั้งหมด';

function javascriptFiles(dir) {
    const found = [];
    for (const entry of readdirSync(dir)) {
        const full = path.join(dir, entry);
        if (statSync(full).isDirectory()) found.push(...javascriptFiles(full));
        else if (entry.endsWith('.js')) found.push(full);
    }
    return found;
}

function walk(node, visit, parent) {
    if (!node || typeof node !== 'object') return;
    if (typeof node.type === 'string') visit(node, parent);
    for (const value of Object.values(node)) {
        if (Array.isArray(value)) value.forEach((child) => walk(child, visit, node));
        else if (value && typeof value === 'object') walk(value, visit, node);
    }
}

// Expose only the native attachment writer to the authenticated LINE bridge.
// No collection or file is written by the installer.
export function exposeAttachmentWriter(source) {
    const tree = parse(source, { ecmaVersion: 'latest', sourceType: 'script' });
    const matches = [];
    walk(tree, (node) => {
        if (node.type !== 'NewExpression') return;
        if (
            node.arguments.some(
                (arg) =>
                    arg.type === 'ObjectExpression' &&
                    arg.properties.some(
                        (p) =>
                            (p.key?.name || p.key?.value) === 'collectionName' &&
                            p.value?.value === 'attachments'
                    )
            )
        )
            matches.push(node);
    });
    if (matches.length !== 1) throw new Error('Native attachment writer changed');
    const node = matches[0];
    return (
        source.slice(0, node.start) +
        '(globalThis.__pearnlyAttachments=' +
        source.slice(node.start, node.end) +
        ')' +
        source.slice(node.end)
    );
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

// The stock icon files are replaced in place, so their names are part of the
// upstream contract we depend on. The two Pearnly images are served by the
// gateway instead - they must ship in the image, but must not be copied into the
// WeKan bundle, whose asset server only answers paths its manifest already lists.
export const REPLACED_BRAND_FILES = [
    'favicon.ico',
    'favicon-16x16.png',
    'favicon-32x32.png',
    'apple-touch-icon.png',
];
export const SERVED_BRAND_FILES = ['pearnly-header-logo.png', 'pearnly-login-logo.png'];

export function installBrandAssets(appDir, sourceDir) {
    for (const name of [...REPLACED_BRAND_FILES, ...SERVED_BRAND_FILES]) {
        const source = path.join(sourceDir, name);
        if (!existsSync(source)) throw new Error('Missing Pearnly brand asset: ' + name);
    }
    for (const name of REPLACED_BRAND_FILES) {
        if (!existsSync(path.join(appDir, name)))
            throw new Error('Native brand asset moved upstream: ' + name);
        copyFileSync(path.join(sourceDir, name), path.join(appDir, name));
    }
    return REPLACED_BRAND_FILES;
}

// Several upstream translations are not Thai at all - a block of the Thai file
// is Vietnamese, which shows up in the UI (the create-board dialog offered
// "Mẫu" for Template). Pearnly ships Thai first, so those entries are corrected
// from i18n/th-overrides.json.
//
// The bundle embeds each language as `JSON.parse('<json>')` in one place, so
// the patch is applied to that literal: parse it, merge, write it back, and
// verify the result parses to exactly what was intended.
function decodeJsString(raw) {
    let out = '';
    for (let i = 0; i < raw.length; i += 1) {
        if (raw[i] !== '\\') {
            out += raw[i];
            continue;
        }
        const next = raw[(i += 1)];
        if (next === 'n') out += '\n';
        else if (next === 'r') out += '\r';
        else if (next === 't') out += '\t';
        else if (next === 'u') {
            out += String.fromCharCode(parseInt(raw.slice(i + 1, i + 5), 16));
            i += 4;
        } else out += next;
    }
    return out;
}

function encodeJsString(text) {
    return text
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r')
        .replace(/\u2028/g, '\\u2028')
        .replace(/\u2029/g, '\\u2029');
}

// The one `JSON.parse('<thai json>')` literal: at least 1500 entries, and at
// least four fifths of the values carrying Thai script.
function thaiTranslationBlock(source) {
    const found = [];
    const marker = 'JSON.parse(';
    for (let at = source.indexOf(marker); at >= 0; at = source.indexOf(marker, at + 1)) {
        const open = source.indexOf("'", at + marker.length);
        if (open < 0 || open > at + marker.length + 2) continue;
        let end = open + 1;
        while (end < source.length && source[end] !== "'") {
            end += source[end] === '\\' ? 2 : 1;
        }
        if (source[end] !== "'") continue;
        let parsed;
        try {
            parsed = JSON.parse(decodeJsString(source.slice(open + 1, end)));
        } catch {
            continue;
        }
        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) continue;
        const values = Object.values(parsed);
        if (values.length < 1500) continue;
        const thai = values.filter((value) => /[\u0E00-\u0E7F]/.test(String(value))).length;
        if (thai / values.length < 0.8) continue;
        found.push({ open, end, parsed });
    }
    if (found.length !== 1) throw new Error('Expected exactly one Thai translation block');
    return found[0];
}

export function applyThaiOverrides(source, { corrections, additions }) {
    const { open, end, parsed } = thaiTranslationBlock(source);
    for (const [key, value] of Object.entries(corrections)) {
        if (!(key in parsed)) throw new Error('Thai correction key is not in the bundle: ' + key);
        parsed[key] = value;
    }
    for (const [key, value] of Object.entries(additions)) {
        // Upstream shipping the key means our addition is stale and must go.
        if (key in parsed) throw new Error('Thai addition is already upstream: ' + key);
        parsed[key] = value;
    }
    const patched =
        source.slice(0, open + 1) + encodeJsString(JSON.stringify(parsed)) + source.slice(end);
    // Read the result back through the same scanner: an escaping mistake that
    // changed any entry must stop the build instead of shipping.
    const verified = thaiTranslationBlock(patched).parsed;
    if (JSON.stringify(verified) !== JSON.stringify(parsed))
        throw new Error('Thai translation patch did not survive a round trip');
    return patched;
}

// The language picker is filled from getSupportedLanguages(), which returns
// every language the bundle ships. Pearnly's market is Thai first, so the picker
// offers only Thai, English and Simplified Chinese. The other languages stay
// loadable: a profile that already selected one keeps working.
export function restrictLanguageList(source, tags) {
    const tree = parse(source, { ecmaVersion: 'latest', sourceType: 'script' });
    const matches = [];
    walk(tree, (node) => {
        if (node.type !== 'Property') return;
        if ((node.key.name || node.key.value) !== 'getSupportedLanguages') return;
        matches.push(node);
    });
    if (matches.length !== 1) throw new Error('Native getSupportedLanguages shape changed');
    const fn = matches[0].value;
    if (fn.type !== 'ArrowFunctionExpression' || fn.body?.type !== 'CallExpression')
        throw new Error('getSupportedLanguages is no longer an arrow returning a call');
    if (fn.body.callee?.property?.name !== 'map')
        throw new Error('getSupportedLanguages no longer maps the language table');
    const filter = `.filter((language)=>${JSON.stringify(tags)}.includes(language.tag))`;
    return source.slice(0, fn.body.end) + filter + source.slice(fn.body.end);
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
    const brandSource = process.argv[3] || '/opt/pearnly/branding';
    const webAppDir = process.argv[4] || '/build/programs/web.browser/app';
    const i18nDir = process.argv[5] || '/opt/pearnly/i18n';
    const overrides = JSON.parse(readFileSync(path.join(i18nDir, 'th-overrides.json'), 'utf8'));
    const manifestPath = root + '/program.json';
    const manifest = JSON.parse(readFileSync(manifestPath));
    const index = manifest.load.findIndex((entry) => entry.path === 'app/app.js');
    if (index < 0 || manifest.load.some((entry) => entry.path === 'packages/pearnly-bridge.js'))
        throw new Error('Unexpected Meteor manifest');
    const appPath = root + '/app/app.js';
    writeFileSync(
        appPath,
        applyThaiOverrides(
            exposeAttachmentWriter(
                allowUsernameInvitation(awaitNativeCreation(readFileSync(appPath, 'utf8')))
            ),
            overrides
        )
    );
    const ddpPath =
        root + '/npm/node_modules/meteor/ddp-server/node_modules/sockjs/lib/transport.js';
    writeFileSync(ddpPath, includeIdentityHeaders(readFileSync(ddpPath, 'utf8')));
    manifest.load.splice(index, 0, { path: 'packages/pearnly-bridge.js' });
    writeFileSync(manifestPath, JSON.stringify(manifest));
    const installed = installBrandAssets(webAppDir, brandSource);
    console.log('Pearnly brand assets installed:', installed.join(', '));
    // The client bundle ships the Thai text and the language picker, so both are
    // patched where they actually live: the file that carries the Thai data, and
    // the file that carries the language table.
    const browserRoot = path.dirname(webAppDir);
    let patchedThai = 0;
    let patchedLanguages = 0;
    for (const file of javascriptFiles(browserRoot)) {
        let source = readFileSync(file, 'utf8');
        let changed = false;
        if (source.includes(THAI_MARKER)) {
            source = applyThaiOverrides(source, overrides);
            patchedThai += 1;
            changed = true;
        }
        if (source.includes('getSupportedLanguages:')) {
            source = restrictLanguageList(source, LANGUAGE_TAGS);
            patchedLanguages += 1;
            changed = true;
        }
        if (changed) writeFileSync(file, source);
    }
    if (patchedThai !== 1) throw new Error('Expected one client file with Thai text');
    if (patchedLanguages !== 1) throw new Error('Expected one client file with the language table');
    console.log('Pearnly patched the client Thai text and the language picker.');
}
