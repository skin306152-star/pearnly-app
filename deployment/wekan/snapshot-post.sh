#!/usr/bin/env bash
# Idempotent thaw; also invoked by a safety timer if the guest agent fails.
set -euo pipefail
test -e /run/pearnly-work-snapshot.lock || exit 0
fsfreeze -u /srv/pearnly-work 2>/dev/null || true
timeout 20 docker exec pearnly-work-mongo-1 mongosh --quiet --eval \
  "db.getSiblingDB('admin').auth('work-root',process.env.MONGO_INITDB_ROOT_PASSWORD); if(db.getSiblingDB('admin').runCommand({currentOp:1}).fsyncLock) db.getSiblingDB('admin').fsyncUnlock();" >/dev/null
rm /run/pearnly-work-snapshot.lock
systemctl stop pearnly-work-snapshot-thaw.timer || true
