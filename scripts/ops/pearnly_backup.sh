#!/usr/bin/env bash
#
# Pearnly nightly backup — storage originals (rsync hardlink-incremental) + pg_dump.
#
# Landing = local same-disk snapshots (decision-tree option 3). This protects
# against accidental deletion, file corruption and app bugs. It does NOT protect
# against disk/hardware loss of the host — that needs true offsite (see
# docs/ops/BACKUP-RESTORE-RUNBOOK.md "RPO/RTO & offsite gap").
#
# Idempotent, safe to re-run. Never logs the DB connection string. Aborts before
# writing if free space is below the watermark so a runaway backup can't fill the
# disk and take prod down.
#
# Usage:
#   pearnly_backup.sh            full nightly run (default)
#   pearnly_backup.sh _check_free PATH MIN_GB      (internal, for tests)
#   pearnly_backup.sh _rotate DIR DAYS             (internal, for tests)
#   pearnly_backup.sh _offsite_sync SNAP_DIR DUMP_FILE   (internal, for tests)
#
# Config via env (defaults suit prod):
#   BACKUP_ROOT          where backups live                     (/var/backups/pearnly)
#   STORAGE_SRC          originals to snapshot                  (/opt/mrpilot/storage)
#   ENV_FILE             file holding DATABASE_URL              (/opt/mrpilot/.env)
#   RETENTION_DAYS       snapshots/dumps to keep                (7)
#   MIN_FREE_GB          hard floor of free space (GB)          (10)
#   LOG_FILE             append log here                        ($BACKUP_ROOT/backup.log)
#   SKIP_DB              set to 1 to skip pg_dump               (unset)
#
# Optional offsite stage (runs after the core backup; never fails the run —
# see offsite_sync() below). Unset PEARNLY_OFFSITE_REMOTE = skipped entirely.
#   PEARNLY_OFFSITE_REMOTE  rclone remote:path, any S3-compatible backend or a
#                           plain local path for testing        (unset = off)
#   RCLONE_BIN              rclone binary to invoke             (rclone)
#   OFFSITE_STATUS_FILE     last offsite outcome                ($BACKUP_ROOT/offsite_last_status)

set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/pearnly}"
STORAGE_SRC="${STORAGE_SRC:-/opt/mrpilot/storage}"
ENV_FILE="${ENV_FILE:-/opt/mrpilot/.env}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
MIN_FREE_GB="${MIN_FREE_GB:-10}"
LOG_FILE="${LOG_FILE:-$BACKUP_ROOT/backup.log}"
PEARNLY_OFFSITE_REMOTE="${PEARNLY_OFFSITE_REMOTE:-}"
RCLONE_BIN="${RCLONE_BIN:-rclone}"
OFFSITE_STATUS_FILE="${OFFSITE_STATUS_FILE:-$BACKUP_ROOT/offsite_last_status}"

log() { printf '%s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*" | tee -a "$LOG_FILE" >&2; }
die() { log "ERROR $*"; exit 1; }

# Free GB on the filesystem holding a path (integer, floor).
free_gb() {
  local path="$1"
  local avail_kb
  avail_kb="$(df -Pk "$path" | awk 'NR==2 {print $4}')"
  echo $(( avail_kb / 1024 / 1024 ))
}

# Exit 0 if free space at PATH >= MIN_GB, else 1. No side effects.
check_free() {
  local path="$1" min_gb="$2" have
  have="$(free_gb "$path")"
  if [ "$have" -lt "$min_gb" ]; then
    log "watermark: only ${have}GB free at ${path}, need >=${min_gb}GB"
    return 1
  fi
  log "watermark: ${have}GB free at ${path} (floor ${min_gb}GB) OK"
  return 0
}

# Delete direct children of DIR older than DAYS (mtime). Only touches DIR's own
# entries — never follows outside. Used for both snapshot dirs and dump files.
rotate() {
  local dir="$1" days="$2"
  [ -d "$dir" ] || return 0
  # -mtime +N matches strictly older than N+1 days; keep last DAYS days.
  find "$dir" -mindepth 1 -maxdepth 1 -mtime "+$((days - 1))" -print0 |
    while IFS= read -r -d '' entry; do
      log "rotate: removing $entry"
      rm -rf -- "$entry"
    done
}

# Newest existing snapshot dir (for rsync --link-dest), or empty.
latest_snapshot() {
  local sdir="$1"
  [ -d "$sdir" ] || return 0
  find "$sdir" -mindepth 1 -maxdepth 1 -type d | sort | tail -1
}

snapshot_storage() {
  local ts="$1"
  local sdir="$BACKUP_ROOT/storage"
  local dst="$sdir/$ts"
  mkdir -p "$sdir"
  local link_arg=() prev
  prev="$(latest_snapshot "$sdir")"
  if [ -n "$prev" ]; then
    link_arg=(--link-dest="$prev")
    log "storage: incremental against $(basename "$prev")"
  else
    log "storage: first full snapshot"
  fi
  # Trailing slash on src copies contents; --delete keeps snapshot an exact mirror.
  rsync -a --delete "${link_arg[@]}" "$STORAGE_SRC/" "$dst/" ||
    die "rsync failed"
  echo "$dst"
}

verify_storage() {
  local dst="$1"
  local src_files dst_files src_bytes dst_bytes
  src_files="$(find "$STORAGE_SRC" -type f | wc -l)"
  dst_files="$(find "$dst" -type f | wc -l)"
  src_bytes="$(find "$STORAGE_SRC" -type f -printf '%s\n' | awk '{s+=$1} END{print s+0}')"
  dst_bytes="$(find "$dst" -type f -printf '%s\n' | awk '{s+=$1} END{print s+0}')"
  log "verify: src ${src_files}f/${src_bytes}b  snapshot ${dst_files}f/${dst_bytes}b"
  [ "$src_files" = "$dst_files" ] || die "file count mismatch (src=$src_files dst=$dst_files)"
  [ "$src_bytes" = "$dst_bytes" ] || die "byte count mismatch (src=$src_bytes dst=$dst_bytes)"
  # Freeze a manifest with per-file sha256 so a restore drill can prove integrity.
  ( cd "$dst" && find . -type f -exec sha256sum {} + | sort ) > "$dst.manifest.sha256"
  log "verify: manifest -> $dst.manifest.sha256 ($(wc -l < "$dst.manifest.sha256") files)"
}

# Derive a session-mode connection for pg_dump. Supabase's transaction pooler
# (:6543) does not support pg_dump; the session pooler is :5432 on the same host.
dump_url() {
  local url="$1"
  echo "$url" | sed -E 's#:6543/#:5432/#'
}

dump_db() {
  local ts="$1"
  local ddir="$BACKUP_ROOT/db"
  local out="$ddir/pearnly_db_$ts.sql.gz"
  mkdir -p "$ddir"
  [ -f "$ENV_FILE" ] || die "env file not found: $ENV_FILE"
  local db_url
  db_url="$(grep -oP '^DATABASE_URL=\K[^\r\n]+' "$ENV_FILE" | tr -d '"'"'"'"')"
  [ -n "$db_url" ] || die "DATABASE_URL empty in env"
  command -v pg_dump >/dev/null || die "pg_dump not installed (apt-get install postgresql-client-17)"
  # --no-owner/--no-privileges: restore into any role without ownership errors.
  if ! PGCONNECT_TIMEOUT=30 pg_dump "$(dump_url "$db_url")" \
        --no-owner --no-privileges 2>>"$LOG_FILE" | gzip -c > "$out"; then
    rm -f "$out"
    die "pg_dump failed"
  fi
  gzip -t "$out" || die "dump gzip corrupt: $out"
  local sz
  sz="$(stat -c '%s' "$out")"
  [ "$sz" -gt 1024 ] || die "dump suspiciously small (${sz}b): $out"
  log "db: dump -> $out (${sz}b)"
  echo "$out"
}

# Push the latest storage snapshot + latest pg_dump to an rclone remote.
# Optional and isolated by design: an unconfigured or failing offsite stage
# must never fail the core backup (cron depends on that). Failure is logged
# loudly and recorded in OFFSITE_STATUS_FILE, but this function always
# returns 0 — callers must not wrap it in anything that would trip `set -e`.
offsite_sync() {
  local storage_dst="$1" dump_file="$2"

  if [ -z "$PEARNLY_OFFSITE_REMOTE" ]; then
    log "offsite: not configured, skipped"
    return 0
  fi

  mkdir -p "$(dirname "$OFFSITE_STATUS_FILE")"

  if ! command -v "$RCLONE_BIN" >/dev/null 2>&1; then
    log "ERROR offsite: rclone binary not found ($RCLONE_BIN)"
    printf 'FAIL %s rclone-not-found\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" > "$OFFSITE_STATUS_FILE"
    return 0
  fi

  local ok=1

  # `sync` mirrors only the newest snapshot dir to a fixed remote path, so
  # unchanged files (same size+modtime as last night, thanks to the local
  # hardlink chain) are skipped by rclone instead of re-uploaded whole.
  if "$RCLONE_BIN" sync "$storage_dst" "$PEARNLY_OFFSITE_REMOTE/storage/latest" \
       >>"$LOG_FILE" 2>&1; then
    log "offsite: storage synced -> $PEARNLY_OFFSITE_REMOTE/storage/latest"
  else
    log "ERROR offsite: storage sync failed ($PEARNLY_OFFSITE_REMOTE/storage/latest)"
    ok=0
  fi

  if [ -n "$dump_file" ] && [ -f "$dump_file" ]; then
    if "$RCLONE_BIN" copyto "$dump_file" "$PEARNLY_OFFSITE_REMOTE/db/pearnly_db_latest.sql.gz" \
         >>"$LOG_FILE" 2>&1; then
      log "offsite: db dump synced -> $PEARNLY_OFFSITE_REMOTE/db/pearnly_db_latest.sql.gz"
    else
      log "ERROR offsite: db dump sync failed ($PEARNLY_OFFSITE_REMOTE/db/pearnly_db_latest.sql.gz)"
      ok=0
    fi
  fi

  if [ "$ok" = 1 ]; then
    printf 'OK %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" > "$OFFSITE_STATUS_FILE"
    log "offsite: OK"
  else
    printf 'FAIL %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" > "$OFFSITE_STATUS_FILE"
    log "offsite: FAIL (see ERROR lines above)"
  fi
  return 0
}

run() {
  mkdir -p "$BACKUP_ROOT"
  mkdir -p "$(dirname "$LOG_FILE")"
  exec 9>"$BACKUP_ROOT/.lock"
  flock -n 9 || die "another backup run holds the lock"
  log "=== backup start (retention=${RETENTION_DAYS}d floor=${MIN_FREE_GB}GB) ==="
  [ -d "$STORAGE_SRC" ] || die "storage source missing: $STORAGE_SRC"

  # Watermark BEFORE writing: need the floor plus room for one full copy.
  local storage_gb needed
  storage_gb="$(( $(du -sBG "$STORAGE_SRC" | awk '{gsub(/G/,"",$1); print $1}') + 1 ))"
  needed=$(( MIN_FREE_GB > storage_gb ? MIN_FREE_GB : storage_gb ))
  check_free "$BACKUP_ROOT" "$needed" || die "insufficient free space, aborting before write"

  local ts dst dump_file=""
  ts="$(date -u +'%Y%m%d_%H%M%S')"
  dst="$(snapshot_storage "$ts")"
  verify_storage "$dst"
  if [ "${SKIP_DB:-0}" != "1" ]; then dump_file="$(dump_db "$ts")"; fi

  # Offsite is best-effort and isolated from the exit code of the run — see
  # offsite_sync()'s own contract comment.
  offsite_sync "$dst" "$dump_file"

  rotate "$BACKUP_ROOT/storage" "$RETENTION_DAYS"
  # snapshot manifests share the storage dir; prune orphaned manifests too.
  find "$BACKUP_ROOT/storage" -maxdepth 1 -name '*.manifest.sha256' -mtime "+$((RETENTION_DAYS - 1))" -delete 2>/dev/null || true
  rotate "$BACKUP_ROOT/db" "$RETENTION_DAYS"

  log "=== backup OK ($ts) ==="
}

main() {
  case "${1:-run}" in
    run) run ;;
    _check_free) check_free "$2" "$3" ;;
    _rotate) rotate "$2" "$3" ;;
    _dump_url) dump_url "$2" ;;
    _offsite_sync) offsite_sync "$2" "${3:-}" ;;
    *) die "unknown subcommand: $1" ;;
  esac
}

main "$@"
