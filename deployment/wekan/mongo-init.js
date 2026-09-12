/* First boot only, on a new persistent MongoDB volume. */
/* global db, process */
const password = process.env.WORK_MONGO_PASSWORD;
if (!password || !/^[A-Za-z0-9_-]{32,}$/.test(password)) {
    throw new Error('A generated URL-safe MongoDB application password is required');
}
db.getSiblingDB('wekan').createUser({
    user: 'wekan',
    pwd: password,
    roles: [{ role: 'readWrite', db: 'wekan' }],
});
