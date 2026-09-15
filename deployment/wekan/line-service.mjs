/* Server-to-server LINE adapter. Native REST remains the only task writer. */
import { createHash, createHmac, timingSafeEqual } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { realpath } from 'node:fs/promises';
import path from 'node:path';

export function verifyLine(headers, method, path, secret, now = Date.now()) {
    const encoded = headers['x-pearnly-line'] || '';
    const supplied = headers['x-pearnly-line-signature'] || '';
    const expected = createHmac('sha256', secret).update(encoded).digest('hex');
    if (
        supplied.length !== expected.length ||
        !timingSafeEqual(Buffer.from(supplied), Buffer.from(expected))
    )
        throw new Error('signature');
    const value = JSON.parse(Buffer.from(encoded, 'base64url').toString());
    if (
        value.method !== method ||
        value.path !== path ||
        value.expires * 1000 < now ||
        value.expires * 1000 > now + (lineRoute(method, path) === 'file' ? 330000 : 90000) ||
        !value.identity?.user_id ||
        !value.identity?.tenant_id ||
        value.identity.is_platform_admin !== false
    )
        throw new Error('identity');
    return value;
}

export function lineRoute(method, path) {
    const id = '[A-Za-z0-9_-]{1,100}';
    if (method === 'GET' && new RegExp(`^/_pearnly/line/context(/${id})?$`).test(path))
        return 'context';
    if (
        method === 'GET' &&
        new RegExp(`^/_pearnly/line/records/${id}/${id}/(history|files)/[0-9]{1,5}$`).test(path)
    )
        return 'records';
    if (method === 'GET' && new RegExp(`^/_pearnly/line/file/${id}/${id}/${id}$`).test(path))
        return 'file';
    if (method === 'POST' && path === '/_pearnly/line/api/boards') return 'native';
    if (method === 'POST' && new RegExp(`^/_pearnly/line/member/${id}$`).test(path))
        return 'member';
    if (method === 'POST' && new RegExp(`^/_pearnly/line/attachments/${id}/${id}$`).test(path))
        return 'attachment';
    const base = `/_pearnly/line/api/boards/${id}`;
    if (method === 'POST' && new RegExp(`^${base}/lists$`).test(path)) return 'native';
    if (method === 'POST' && new RegExp(`^${base}/lists/${id}/cards$`).test(path)) return 'native';
    if (method === 'PUT' && new RegExp(`^${base}/lists/${id}/cards/${id}$`).test(path))
        return 'native';
    if (method === 'POST' && new RegExp(`^${base}/cards/${id}/comments$`).test(path))
        return 'native';
    return null;
}

const json = (res, status, data) => {
    res.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(data));
};

async function payload(req) {
    const chunks = [];
    let size = 0;
    for await (const part of req) {
        size += part.length;
        if (size > 15 * 1024 * 1024) throw new Error('size');
        chunks.push(part);
    }
    return Buffer.concat(chunks);
}

export async function lineService(req, res, next, deps) {
    const { secret, nativeUser, db, Accounts, Meteor, actor, service } = deps;
    const route = lineRoute(req.method, req.url);
    if (!route) return json(res, 404, { error: 'route' });
    const envelope = verifyLine(req.headers, req.method, req.url, secret);
    const raw = await payload(req);
    if (createHash('sha256').update(raw).digest('hex') !== envelope.body) throw new Error('body');
    let identity = envelope.identity;
    if (route === 'file') {
        identity = await service('line-actor', {
            ...identity.line_binding,
            user_id: identity.user_id,
            tenant_id: identity.tenant_id,
        });
        if (
            identity.user_id !== envelope.identity.user_id ||
            identity.tenant_id !== envelope.identity.tenant_id
        )
            throw new Error('identity');
    }
    const user = await nativeUser(identity);
    if (user.services.pearnly.tenantId !== envelope.identity.tenant_id) throw new Error('tenant');
    const boardId = ['context', 'attachment', 'file', 'member', 'records'].includes(route)
        ? req.url.split('/')[4]
        : req.url.split('/')[5];
    const employee = identity.work_role === 'employee';
    if (!employee && identity.work_role !== 'owner') throw new Error('role');
    const membership = {
        userId: user._id,
        isActive: true,
        ...(!employee ? { isAdmin: true } : {}),
    };
    const cardScope = employee ? { assignees: user._id } : {};
    let board;
    if (boardId) {
        board = await db.collection('boards').findOne({
            _id: boardId,
            archived: { $ne: true },
            members: { $elemMatch: membership },
        });
        if (!board) return json(res, 403, { error: 'board' });
    }
    if (route === 'file') {
        const [, , , , , cardId, fileId] = req.url.split('/');
        const file = await db
            .collection('attachments')
            .findOne({ _id: fileId, 'meta.boardId': boardId, 'meta.cardId': cardId });
        if (
            !file ||
            !(await db.collection('cards').findOne({ _id: cardId, boardId, ...cardScope }))
        )
            return json(res, 404, { error: 'file' });
        const root = await realpath(process.env.WRITABLE_PATH || process.cwd());
        const location = await realpath(file.versions?.original?.path || file.path);
        if (!location.startsWith(root + path.sep)) throw new Error('file path');
        res.writeHead(200, {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': "attachment; filename*=UTF-8''" + encodeURIComponent(file.name),
            'Cache-Control': 'no-store',
            'X-Content-Type-Options': 'nosniff',
        });
        const stream = createReadStream(location);
        stream.on('error', () => res.destroy());
        res.on('close', () => stream.destroy());
        stream.pipe(res);
        return;
    }
    if (route === 'records') {
        const [, , , , , cardId, kind, page] = req.url.split('/');
        if (
            !(await db
                .collection('cards')
                .findOne({ _id: cardId, boardId, archived: { $ne: true }, ...cardScope }))
        )
            return json(res, 404, { error: 'card' });
        const files = kind === 'files';
        const items = await db
            .collection(files ? 'attachments' : 'card_comments')
            .find(
                files ? { 'meta.boardId': boardId, 'meta.cardId': cardId } : { boardId, cardId },
                { projection: files ? { name: 1, meta: 1 } : { text: 1, createdAt: 1, userId: 1 } }
            )
            .sort({ createdAt: -1, _id: 1 })
            .skip(Number(page) * 6)
            .limit(7)
            .toArray();
        return json(res, 200, { items: items.slice(0, 6), more: items.length > 6 });
    }
    if (route === 'context') {
        if (!board) {
            const boards = await db
                .collection('boards')
                .find(
                    {
                        archived: { $ne: true },
                        members: {
                            $elemMatch: membership,
                        },
                    },
                    { projection: { title: 1 } }
                )
                .sort({ title: 1 })
                .limit(201)
                .toArray();
            return json(res, 200, { userId: user._id, boards });
        }
        const members = (board.members || [])
            .filter((m) => m.isActive && (!employee || m.userId === user._id))
            .map((m) => m.userId);
        const [lists, cards, people, comments, attachments, lanes] = await Promise.all([
            db
                .collection('lists')
                .find({ boardId, archived: { $ne: true } })
                .sort({ sort: 1 })
                .toArray(),
            db
                .collection('cards')
                .find(
                    { boardId, archived: { $ne: true }, ...cardScope },
                    {
                        projection: {
                            title: 1,
                            description: 1,
                            listId: 1,
                            boardId: 1,
                            swimlaneId: 1,
                            assignees: 1,
                            members: 1,
                            dueAt: 1,
                            modifiedAt: 1,
                            userId: 1,
                        },
                    }
                )
                .sort({ modifiedAt: -1, _id: 1 })
                .limit(2001)
                .toArray(),
            Meteor.users
                .rawCollection()
                .find(
                    { _id: { $in: members }, loginDisabled: { $ne: true } },
                    { projection: { username: 1, profile: 1, 'services.pearnly.id': 1 } }
                )
                .toArray(),
            db
                .collection('card_comments')
                .find({ boardId })
                .sort({ createdAt: -1 })
                .limit(500)
                .toArray(),
            db
                .collection('attachments')
                .find(
                    { 'meta.boardId': boardId },
                    { projection: { name: 1, type: 1, size: 1, meta: 1 } }
                )
                .limit(500)
                .toArray(),
            db
                .collection('swimlanes')
                .find({ boardId, archived: { $ne: true } })
                .sort({ sort: 1 })
                .toArray(),
        ]);
        return json(res, 200, {
            userId: user._id,
            board: { _id: board._id, title: board.title },
            lists,
            cards,
            people: people.map((p) => ({
                _id: p._id,
                name: p.profile?.fullname || p.username,
                user_id: p.services?.pearnly?.id,
            })),
            comments: comments.filter((x) => cards.some((c) => c._id === x.cardId)),
            attachments: attachments.filter((x) => cards.some((c) => c._id === x.meta?.cardId)),
            lanes,
        });
    }
    let body = raw.length ? JSON.parse(raw) : {};
    const parts = req.url.split('/');
    const cardId =
        route === 'attachment'
            ? parts[5]
            : parts[6] === 'cards'
              ? parts[7]
              : parts[8] === 'cards'
                ? parts[9]
                : null;
    let card;
    if (cardId) {
        card = await db
            .collection('cards')
            .findOne({ _id: cardId, boardId, archived: { $ne: true }, ...cardScope });
        if (!card || (parts[6] === 'lists' && card.listId !== parts[7]))
            return json(res, 409, { error: 'card_changed' });
    }
    if (employee) {
        const member = board?.members.find((m) => m.userId === user._id && m.isActive);
        const move =
            req.method === 'PUT' &&
            Object.keys(body).length === 1 &&
            typeof body.listId === 'string' &&
            envelope.allowed_lists?.includes(body.listId);
        const comment =
            req.method === 'POST' &&
            parts[8] === 'comments' &&
            Object.keys(body).length === 1 &&
            typeof body.comment === 'string';
        if (
            !card ||
            !envelope.allowed_sources?.includes(card.listId) ||
            identity.work_readonly ||
            member?.isCommentOnly ||
            member?.isNoComments ||
            !(move || comment || route === 'attachment')
        )
            return json(res, 403, { error: 'employee_action' });
    }
    if (
        board &&
        body.assignees &&
        (!Array.isArray(body.assignees) ||
            body.assignees.some(
                (id) => !(board.members || []).some((m) => m.userId === id && m.isActive)
            ))
    )
        return json(res, 403, { error: 'assignee' });
    for (const listId of [parts[6] === 'lists' ? parts[7] : null, body.listId].filter(Boolean)) {
        if (
            !(await db
                .collection('lists')
                .findOne({ _id: listId, boardId, archived: { $ne: true } }))
        )
            return json(res, 403, { error: 'list' });
    }
    // One durable receipt per explicit confirmation. An interrupted write is
    // deliberately not repeated: native APIs do not promise idempotent creation.
    if (!/^[A-Za-z0-9_-]{10,100}$/.test(envelope.operation || '')) throw new Error('operation');
    const receipts = db.collection('pearnly_line_receipts');
    const key = user._id + ':' + envelope.operation;
    const fingerprint = createHash('sha256')
        .update(req.method + req.url)
        .update(raw)
        .digest('hex');
    const previous = await receipts.findOne({ _id: key });
    if (previous) {
        if (previous.fingerprint !== fingerprint)
            return json(res, 409, { error: 'operation_conflict' });
        if (!previous.response) return json(res, 409, { error: 'operation_uncertain' });
        return json(res, previous.status, previous.response);
    }
    try {
        await receipts.insertOne({ _id: key, fingerprint, createdAt: new Date() });
    } catch {
        return json(res, 409, { error: 'operation_busy' });
    }
    if (route === 'member') {
        if (
            body.member?.tenant_id !== envelope.identity.tenant_id ||
            body.member?.is_platform_admin !== false
        )
            throw new Error('member tenant');
        const member = await nativeUser(body.member);
        if (member.services.pearnly.tenantId !== envelope.identity.tenant_id)
            throw new Error('member tenant');
        if (!board.members.some((m) => m.userId === member._id && m.isActive))
            await deps.invite(member.username, boardId, user._id);
        const confirmed = await db.collection('boards').findOne({
            _id: boardId,
            members: { $elemMatch: { userId: member._id, isActive: true } },
        });
        if (!confirmed) return json(res, 409, { error: 'member_not_added' });
        const response = { _id: member._id };
        await receipts.updateOne({ _id: key }, { $set: { response, status: 200 } });
        return json(res, 200, response);
    }
    if (route === 'attachment') {
        const bytes = Buffer.from(body.data || '', 'base64');
        if (!bytes.length || bytes.length > 10 * 1024 * 1024 || !card)
            return json(res, 422, { error: 'attachment' });
        const options = {
            fileId: createHash('sha256').update(key).digest('hex').slice(0, 20),
            name: String(body.name || 'attachment')
                .split(/[\\/]/)
                .pop()
                .slice(0, 120),
            type: body.type || 'application/octet-stream',
            size: bytes.length,
            userId: user._id,
            meta: { boardId, cardId, listId: card.listId, swimlaneId: card.swimlaneId },
        };
        const allowed = await deps.attachments.onBeforeUpload?.call(deps.attachments, options);
        if (allowed !== undefined && allowed !== true)
            return json(res, 422, { error: 'attachment_rejected' });
        options.meta.fileId = options.fileId;
        const file = await deps.attachments.writeAsync(bytes, options, true);
        const response = { _id: file._id };
        await receipts.updateOne({ _id: key }, { $set: { response, status: 200 } });
        return json(res, 200, response);
    }
    const stamped = Accounts._generateStampedLoginToken();
    const hashed = Accounts._hashStampedToken(stamped);
    await Meteor.users.updateAsync(user._id, { $push: { 'services.resume.loginTokens': hashed } });
    const clean = () =>
        Meteor.users
            .updateAsync(user._id, {
                $pull: { 'services.resume.loginTokens': { hashedToken: hashed.hashedToken } },
            })
            .catch(() => {});
    res.once('finish', clean);
    res.once('close', clean);
    const chunks = [];
    const write = res.write.bind(res);
    const end = res.end.bind(res);
    res.write = (chunk, ...args) => {
        if (chunk) chunks.push(Buffer.from(chunk));
        return write(chunk, ...args);
    };
    res.end = (chunk, ...args) => {
        if (chunk) chunks.push(Buffer.from(chunk));
        let response;
        try {
            response = JSON.parse(Buffer.concat(chunks).toString());
        } catch {
            /* uncertain */
        }
        if (response)
            receipts
                .updateOne(
                    { _id: key },
                    {
                        $set: { response, status: res.statusCode },
                    }
                )
                .then(() => end(chunk, ...args))
                .catch(() => end(chunk, ...args));
        else end(chunk, ...args);
        return res;
    };
    req.url = req.url.replace('/_pearnly/line', '');
    req.headers.authorization = 'Bearer ' + stamped.token;
    delete req.headers['x-pearnly-line'];
    delete req.headers['x-pearnly-line-signature'];
    req.body = body;
    // The signed raw body has already been parsed. Both legacy and current
    // body-parser must skip reading this consumed IncomingMessage again.
    req._body = true;
    req.headers['content-length'] = '0';
    delete req.headers['transfer-encoding'];
    req.headers['content-type'] = 'application/x-pearnly-parsed';
    actor.withValue(user._id, next);
}
