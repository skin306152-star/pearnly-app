# Cloud Run storage contract

This document describes the Pearnly FastAPI storage layout. It does not change the
separate ERPNext VM, MariaDB, Redis, Frappe Sites or their backups. Deployment status
and the active revision belong in the deployment runbook and STATE status card;
the layout below alone is not evidence of a completed migration.

## Persistent paths

Cloud Storage volumes preserve the existing absolute paths recorded in Postgres.
Both Web and Worker must mount the same buckets at the same paths.

| Container path | Contents | Retention |
| --- | --- | --- |
| `/opt/mrpilot/storage` | PDFs, knowledge files, images, workorders, steward attachments, slips | Permanent business files |
| `/opt/mrpilot/uploads` | VAT reconciliation Excel files | Permanent business files |
| `/opt/mrpilot/var` | `ocr_jobs`, `recon_jobs`, asynchronous task input files | Temporary; lifetime must exceed the task retry window |
| `/app/static/companion` | Installer files, manifests and version archives | Read-only in serving containers |

The uploads mount may use the permanent files bucket with `only-dir=uploads`.
Its objects must not be placed in the temporary bucket: completed VAT tasks retain
absolute references to these Excel files. Keep the storage root layout intact
when copying the original server; do not add another `storage/` prefix underneath
the mount. Preserve every referenced filename, including existing encrypted files.

`PDF_STORAGE_DIR`, `IMAGE_STORAGE_DIR`, `WORKORDER_STORAGE_DIR`,
`STEWARD_STORAGE_DIR` and `SLIPS_STORAGE_ROOT` already default to the persistent
paths above. `OCR_JOBS_STAGE_DIR` and `RECON_JOBS_STAGE_DIR` default to the two job
directories under `/opt/mrpilot/var`. Changing these paths requires accounting for
old absolute references, not just changing environment variables.

## Volume semantics

Use `implicit-dirs` and disable metadata caching for mutable shared volumes:
`metadata-cache-ttl-secs=0;stat-cache-max-size-mb=0;type-cache-max-size-mb=0`.
Do not enable directory listing or file caching for the shared mutable paths.
Read-only installer mounts can use caching when immutable versioned paths are
used; a mutable latest manifest must remain promptly visible.

Cloud Storage FUSE is not a POSIX shared disk. It provides neither a distributed
file lock nor an atomic multi-file transaction. Existing UUID material/image
writes finish and close before their references are submitted to a task or saved.
Keep this ordering. Business-job claims and ownership must remain in Postgres;
never use a file existence check as the concurrency lock. Rewrites of the same
artifact require the business task's exclusive ownership.

PDF health probes use unique filenames so simultaneous instance startup checks
cannot delete one another's probes. Application encryption and authenticated,
tenant-scoped download routes remain unchanged. Buckets must be private; storage
IAM does not replace the application's tenant checks.

The reconciliation OCR cache and importer mapping cache use temporary-file
renames. Keep these best-effort caches local using
`PEARNLY_OCR_CACHE_DIR=/tmp/ocr-cache` and
`RECON_AI_MAPPING_CACHE_DIR=/tmp/ai-mapping-cache`; cache eviction can cause a
repeat AI call but must not lose a business document. Do not use their rename
semantics as a Cloud Storage transaction guarantee.

## Migration validation

1. Inventory source paths, object counts, byte totals and checksums. Copy files
   without decrypting or transforming their contents.
2. Stop old-server writers before the final synchronization and traffic switch.
   Keep the old server and a recoverable copy until destination verification.
3. Compare the final source and destination inventories/checksums, including
   installers and files outside the old `storage` directory.
4. In one candidate Cloud Run execution, write a uniquely named probe, close it,
   then read it from a separate execution with the same mounted layout. Verify
   its bytes and delete only this probe. Repeat for each writable mount.
5. Read representative old encrypted and plaintext documents through the
   authenticated application routes. Validate a new Web upload consumed by
   Worker and the generated download. Confirm unauthorized tenant access fails.
6. Verify installer version, size and SHA-256 against the source release and
   ensure its download works after replacing the local static directory mount.

Local tests validate application contracts, not GCS mount behavior. Record real
Cloud Run mount checks and user/device acceptance separately.

## Deployment tools

`deployment/cloud-run/render_service.py` renders a Cloud Run service document
(JSON, accepted as YAML) with explicit image digest, numeric secret version,
service account and bucket arguments. It does not grant public invocation.
Configure Web invocation separately; Worker must retain IAM authentication and
grant invocation only to the designated Web/task identities. Worker uses public
ingress with IAM so authenticated Cloud Tasks requests can reach its endpoint.

The container runs as UID/GID 10001; GCS volume ownership matches this identity.
Chromium is installed during the image build, shared by both roles. Environment
secrets are mounted at `/secrets/runtime.env`, not copied into the build context.

Run `python deployment/cloud-run/storage-probe.py --phase write --nonce TOKEN`
inside a mounted candidate execution, using a unique 16–80 character token.
Run `--phase read` with the same token in a separate execution, then
`--phase cleanup` to remove only those named probes. `--chromium` launches the
baked browser and renders a local page without calling an external ERP.

Web and Worker request limits are both 1,800 seconds; the internal proxy uses the
same read timeout with a 30-second connection timeout. This does not extend the
external Cloudflare proxy timeout. Long operations should use durable tasks and
poll their status; a synchronous operation can still lose its client connection
at the edge. Cloudflare currently documents a default 125-second proxy read
timeout; verify the actual routing product and zone configuration when diagnosing
a timeout. See [Cloudflare error 524](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/).

The internal proxy replaces inbound forwarded host/protocol headers with
`PEARNLY_PUBLIC_HOST` (default `pearnly.com`) and HTTPS. User authorization stays
intact while a separately minted service identity authenticates to Worker.

Reference: [Google Cloud Run storage volume documentation](https://docs.cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts).
