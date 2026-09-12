import { createCipheriv, createDecipheriv, createHash, randomBytes } from 'node:crypto';

export function cookieCodec(secret) {
    const key = createHash('sha256')
        .update('pearnly-work-cookie:' + secret)
        .digest();
    return {
        seal(value, purpose) {
            const iv = randomBytes(12);
            const cipher = createCipheriv('aes-256-gcm', key, iv);
            cipher.setAAD(Buffer.from(purpose));
            const body = Buffer.concat([cipher.update(JSON.stringify(value)), cipher.final()]);
            return Buffer.concat([iv, cipher.getAuthTag(), body]).toString('base64url');
        },
        open(value, purpose) {
            try {
                const raw = Buffer.from(value || '', 'base64url');
                const cipher = createDecipheriv('aes-256-gcm', key, raw.subarray(0, 12));
                cipher.setAAD(Buffer.from(purpose));
                cipher.setAuthTag(raw.subarray(12, 28));
                const data = JSON.parse(
                    Buffer.concat([cipher.update(raw.subarray(28)), cipher.final()])
                );
                return data.exp > Date.now() ? data : null;
            } catch {
                return null;
            }
        },
    };
}

export function readCookie(headers, name) {
    return (
        (headers.cookie || '')
            .split(';')
            .map((part) => part.trim())
            .find((part) => part.startsWith(name + '='))
            ?.slice(name.length + 1) || ''
    );
}

export function upstreamHeaders(input, identity, host, secure) {
    const headers = { ...input, host };
    for (const name of Object.keys(headers)) {
        if (
            name.startsWith('x-pearnly-') ||
            name.startsWith('x-forwarded-') ||
            name === 'forwarded'
        )
            delete headers[name];
    }
    headers['x-pearnly-user-id'] = identity.user_id;
    headers['x-pearnly-session'] = identity.session;
    headers['x-forwarded-proto'] = secure ? 'https' : 'http';
    return headers;
}
