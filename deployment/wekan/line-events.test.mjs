import { test } from 'node:test';
import assert from 'node:assert/strict';
import { startLineEvents } from './line-events.mjs';

test('superseded moves are skipped and the latest target accompanies the event', async () => {
    const events = ['doing', 'review'].map((listId, index) => ({
        _id: String(index),
        boardId: 'b',
        cardId: 'c',
        listId,
        createdAt: new Date(Date.now() - 10000 + index),
    }));
    const calls = [];
    const cursor = { at: new Date(Date.now() - 60000) };
    const cursors = { updateOne: async () => {}, findOne: async () => cursor };
    const activities = {
        find: () => ({ sort: () => ({ limit: () => ({ toArray: async () => events }) }) }),
        findOne: async () => events[1],
    };
    let tick;
    await startLineEvents(
        { collection: (name) => (name === 'activities' ? activities : cursors) },
        async (...args) => calls.push(args),
        (fn) => {
            tick = fn;
            return { unref() {} };
        }
    );
    await tick();
    assert.deepEqual(calls, [
        ['line-event', { board_id: 'b', card_id: 'c', event_id: '1', list_id: 'review' }],
    ]);
});
