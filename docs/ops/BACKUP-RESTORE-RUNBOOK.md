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
the host / disk failure — if the Vultr box dies, both prod and these backups die with it,
**until an offsite remote is configured** (see below — the interface exists now, activating
it is a config change, not a code change).

#### Decision record (Zihao, 2026-07-11)

Paid offsite (Vultr Object Storage etc.) is **deferred**. Interim plan: build the offsite
*interface* now (this section), wire it to a **free** S3-compatible bucket when someone has
five minutes to click through a dashboard, and leave the door open to swap in any paid
provider later — **without touching the script**, only the remote config + one env var.

The script (`scripts/ops/pearnly_backup.sh`) ships an optional stage that, when
`PEARNLY_OFFSITE_REMOTE` is set, pushes the latest storage snapshot + latest `pg_dump` to any
`rclone` remote via `rclone sync`/`copyto` (S3-compatible, provider-agnostic — the script
never hardcodes a vendor). It is unset today, so offsite is still **not covered** — but
turning it on is now a 5-step config change, not a code change.

#### Activating it: Option A — Supabase Storage S3 endpoint (existing project, zero new account)

Supabase Storage speaks the S3 API, so the already-provisioned Supabase project can host the
offsite copy with no new signup. This is *not* circular with the DB dump: the DB dump would
be moved to Supabase's **object storage** product, a separate subsystem from the Postgres
instance being dumped — losing the DB doesn't take the Storage bucket with it.

1. Supabase Dashboard → your project → **Settings → Storage** → note the **S3 Connection**
   panel (endpoint URL + region, e.g. `https://<project-ref>.supabase.co/storage/v1/s3`).
2. Same panel → **New access key** (or **Settings → API** for the service-role key) → generate
   an S3-compatible **Access Key ID / Secret Access Key** pair scoped to Storage.
3. Create a bucket for backups (Storage → New bucket, e.g. `pearnly-offsite`, private).
4. On the server: `rclone config create pearnly-offsite s3 provider=Other \
   endpoint=<endpoint from step 1> access_key_id=<from step 2> secret_access_key=<from step 2> \
   region=<region from step 1>`
5. `PEARNLY_OFFSITE_REMOTE=pearnly-offsite:pearnly-backups` in the cron environment (edit
   `/etc/cron.d/pearnly-backup` or a sourced env file) — **the script itself needs no change.**

#### Activating it: Option B — Cloudflare R2 (free 10 GB, backup instead)

Genuinely independent of both Vultr and Supabase — a real second provider — and free up to
10 GB (this dataset is ~1 GB).

1. Cloudflare Dashboard → **R2 Object Storage** → **Create bucket** (e.g. `pearnly-offsite`).
2. **R2 → Manage API tokens → Create API token** (scope: Object Read & Write, this bucket
   only) → note the generated **Access Key ID / Secret Access Key** + the account's S3
   **endpoint** (`https://<account-id>.r2.cloudflarestorage.com`, shown on the same page).
3. On the server: `rclone config create pearnly-offsite s3 provider=Cloudflare \
   endpoint=<endpoint from step 2> access_key_id=<...> secret_access_key=<...>`
4. `PEARNLY_OFFSITE_REMOTE=pearnly-offsite:pearnly-backups` in the cron environment.
5. (No step 5 — same as Option A, script needs no change.)

Either way, activation = **install rclone + write one remote config + set one env var.**
`rclone` on Ubuntu: `sudo -v ; curl https://rclone.org/install.sh | sudo bash` (official
installer, adds the binary to `/usr/bin/rclone`).

#### Checking offsite status

- **Per-run log line** in `backup.log`: `offsite: not configured, skipped` (remote unset —
  today's state) / `offsite: OK` (both storage + dump synced) / `offsite: FAIL (see ERROR
  lines above)` (remote configured but sync failed — core backup still succeeded).
- **Status file**: `$BACKUP_ROOT/offsite_last_status` (default
  `/var/backups/pearnly/offsite_last_status`) — one line, `OK <UTC-ts>` or `FAIL <UTC-ts>`.
  Absent = offsite has never run configured (matches the "not configured" log line).
- Offsite failure **never** fails the cron job or blocks core backups — see the script's
  `offsite_sync()` contract comment. A red `FAIL` here is a standalone alert to chase, not a
  backup-is-broken signal.

**Until a remote is configured, treat "disk/host loss" as not covered** — the interface is
ready, but nothing is plugged into it yet.

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
- **Offsite (optional):** unset by default (`offsite: not configured, skipped`). Activate per
  "Offsite gap" above. `PEARNLY_OFFSITE_REMOTE=<rclone remote:path>` turns it on;
  `RCLONE_BIN` (default `rclone`) and `OFFSITE_STATUS_FILE` (default
  `$BACKUP_ROOT/offsite_last_status`) are rarely-needed overrides. A failed offsite sync
  never fails the run — see log/status-file contract above.
- **Deploy note:** the script is deployed by `git-deploy` like any repo file; the cron file
  in `/etc/cron.d/` and the installed `postgresql-client-17` package are host-side, added
  once, and are not managed by deploys.
