/* One durable activity cursor on the stateful work service, never Cloud Run. */
export async function startLineEvents(db, service, schedule = setInterval) {
    const cursors = db.collection('pearnly_line_event_cursor');
    await cursors.updateOne(
        { _id: 'owner' },
        { $setOnInsert: { at: new Date() } },
        { upsert: true }
    );
    let busy = false;
    const tick = async () => {
        if (busy) return;
        busy = true;
        try {
            const cursor = await cursors.findOne({ _id: 'owner' });
            const settled = new Date(Date.now() - 5000);
            const events = await db
                .collection('activities')
                .find({
                    activityType: 'moveCard',
                    createdAt: { $lte: settled },
                    $or: [
                        { createdAt: { $gt: cursor.at } },
                        { createdAt: cursor.at, _id: { $gt: cursor.id || '' } },
                    ],
                })
                .sort({ createdAt: 1, _id: 1 })
                .limit(100)
                .toArray();
            // A timestamp plus id preserves all events sharing a millisecond.
            for (const event of events) {
                if (!event.boardId || !event.cardId || !event.listId) continue;
                const latest = await db.collection('activities').findOne(
                    {
                        activityType: 'moveCard',
                        boardId: event.boardId,
                        cardId: event.cardId,
                    },
                    { sort: { createdAt: -1, _id: -1 }, projection: { _id: 1 } }
                );
                if (latest?._id !== event._id) continue;
                if (event.createdAt > new Date(Date.now() - 23 * 3600000)) {
                    await service('line-event', {
                        board_id: event.boardId,
                        card_id: event.cardId,
                        event_id: event._id,
                        list_id: event.listId,
                    });
                }
            }
            const last = events[events.length - 1];
            if (events.length === 100)
                await cursors.updateOne(
                    { _id: 'owner' },
                    { $set: { at: last.createdAt, id: last._id } }
                );
            else if (settled > cursor.at)
                await cursors.updateOne({ _id: 'owner' }, { $set: { at: settled, id: '' } });
        } catch (error) {
            console.warn('LINE work events pending:', error.message);
        } finally {
            busy = false;
        }
    };
    const timer = schedule(tick, 30000);
    timer.unref();
    return timer;
}
