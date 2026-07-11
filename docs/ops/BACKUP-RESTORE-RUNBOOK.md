# Pearnly Backup & Restore Runbook

Owner: prod ops. Scope: nightly backup of upload originals (`/opt/mrpilot/storage`)
and the Supabase Postgres database, plus how to restore and how often we prove it works.

## What runs, where

| Piece | Value |
|---|---|
| Script | `/opt/mrpilot/scripts/ops/pearnly_backup.sh` (tracked in repo `scripts/ops/`) |
| Schedule | `/etc/cron.d/pearnly-backup` — `0 20 * * *` UTC = **03:00 Asia/Bangkok** (low-peak) |
| Backup root | `/var/backups/pearnly` (outside `/opt/mrpilot`, so `git-deploy` never touches it) |
| Storage backups | `/var/backups/pearnly/storage/<UTC-ts>/` + `<UTC-ts>.manifest.sha256` |
| DB dumps | `/var/backups/pearnly/db/pearnly_db_<UTC-ts>.sql.gz` |
| Logs | `/var/backups/pearnly/backup.log` (script), `cron.log` (cron wrapper) |
| Retention | 7 days, rotated inside the script (only its own files) |
| pg_dump | PostgreSQL client **17** (PGDG repo); prod DB is 17.6 |

How it works: storage is snapshotted with `rsync -a --delete --link-dest=<prev>` so each
night is a full browsable tree but unchanged files are hardlinks to the previous night
(first snapshot ~1 GB, subsequent nights only the delta). The DB is `pg_dump | gzip`, run
against the Supabase **session pooler** (port 5432 — the transaction pooler on 6543 does
not support pg_dump; the script rewrites the port automatically). Every run verifies file
count + byte count against the live source, freezes a per-file sha256 manifest, and checks
the gzip integrity + non-empty size of the dump. If free space is below the watermark the
run aborts **before writing** so a backup can never fill the disk and take prod down.

## RPO / RTO (honest current state)

- **RPO ≈ 24 h** — backups run once nightly; worst case you lose up to a day of new uploads
  and DB writes since the last 03:00 run.
- **RTO** — storage restore is a file copy (minutes). DB restore is `gunzip | psql` into a
  target (tens of minutes for this dataset). No automation; follow the steps below.

### Offsite gap — READ THIS

**These backups live on the same physical disk as prod** (`/dev/vda2`). They protect against
accidental deletion, file corruption, and app bugs. They do **NOT** protect against loss of
the host / disk failure — if the Vultr box dies, both prod and these backups die with it.

Why not offsite yet (decision-tree outcome, 2026-07-11):
- The old Tokyo fallback box (`45.76.53.194`) is decommissioned (unreachable).
- No `rclone`/`aws` on the host and no object-storage bucket provisioned; the only key
  present is Supabase's, i.e. the **same provider as the primary DB** (circular for the DB
  dump, weak independence), and its per-object size limit forces a fragile multipart upload.

**To close the gap (needs Zihao to green-light one):**
1. Provision Vultr Object Storage (~$5/mo, S3-compatible), `apt-get install rclone`, add a
   `rclone` push of `/var/backups/pearnly` at the end of the script. Cleanest true offsite.
2. Or stand up a second small VPS with a disk and `rsync` the backup root to it nightly.
3. Or enable Supabase PITR/daily backups on the DB side (covers DB only, not upload files).

Until one of these is done, treat "disk/host loss" as **not covered**.

## Restore: upload originals

```bash
# List available snapshots (newest last)
ls -1 /var/backups/pearnly/storage/ | grep '^20'

SNAP=/var/backups/pearnly/storage/<UTC-ts>

# Verify the snapshot is intact before trusting it
( cd "$SNAP" && sha256sum -c "$SNAP.manifest.sha256" ) | grep -v ': OK$'   # empty = all good

# Restore everything (or a single workorder/pdf subtree) back into place
rsync -a "$SNAP/" /opt/mrpilot/storage/
# ...or a single dir: rsync -a "$SNAP/workorders/<id>/" /opt/mrpilot/storage/workorders/<id>/
```

## Restore: database

Restore into a **temporary** database first and sanity-check before ever touching prod.
Use pg_dump/psql **17** to match the dump.

```bash
DUMP=/var/backups/pearnly/db/pearnly_db_<UTC-ts>.sql.gz
gzip -t "$DUMP"                                  # integrity check

# Into a scratch DB (example: a throwaway target you control)
gunzip -c "$DUMP" | psql "<scratch-connection-url>"
```

Notes:
- The dump is a full plain-SQL dump of all non-system schemas (`public`, `auth`, ...).
- Restoring into a **vanilla** Postgres logs harmless errors for Supabase-only extensions
  (`pg_graphql`, `vault`, ...) — app tables and data still load. For a faithful restore,
  target a Supabase-compatible instance (or restore into Supabase directly). Also use a
  psql that matches the dumping client (17.10) to avoid `\restrict` meta-command noise.
- Never restore straight over prod without a verified dry run first.

## Restore drill (proven 2026-07-11)

- **Storage:** 3 sample originals restored from the snapshot — sha256 matched live source
  byte-for-byte and were present in the frozen manifest.
- **DB:** dump imported into an ephemeral `postgres:17` container — 156/157 public tables
  and exact row counts (`users`=43, `ocr_history`=516) landed. (The 1 skipped table depends
  on a Supabase extension absent from vanilla PG; restore into Supabase-compatible target.)

Re-run this drill quarterly, or after any change to the DB schema or the backup script.

## Operating notes

- **Run manually:** `bash /opt/mrpilot/scripts/ops/pearnly_backup.sh`
- **Skip DB (files only):** `SKIP_DB=1 bash .../pearnly_backup.sh`
- **Watermark floor:** `MIN_FREE_GB` (default 10). The run needs the floor OR one full copy
  of storage free, whichever is larger, or it aborts before writing.
- **Check health:** `tail -20 /var/backups/pearnly/backup.log` — last line `=== backup OK`.
  A non-zero exit / missing "OK" line means investigate (usually disk space or DB reach).
- **Deploy note:** the script is deployed by `git-deploy` like any repo file; the cron file
  in `/etc/cron.d/` and the installed `postgresql-client-17` package are host-side, added
  once, and are not managed by deploys.
