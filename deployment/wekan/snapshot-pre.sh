#!/usr/bin/env bash
# Google guest-flush hook for the dedicated work-data disk.
set -euo pipefail
test ! -e /run/pearnly-work-snapshot.lock
touch /run/pearnly-work-snapshot.lock
trap '/etc/google/snapshots/post.sh' ERR
systemd-run --quiet --unit=pearnly-work-snapshot-thaw --on-active=240s \
  /etc/google/snapshots/post.sh
timeout 20 docker exec pearnly-work-mongo-1 mongosh --quiet --eval \
  "db.getSiblingDB('admin').auth('work-root',process.env.MONGO_INITDB_ROOT_PASSWORD); db.getSiblingDB('admin').fsyncLock();" >/dev/null
sync
fsfreeze -f /srv/pearnly-work
