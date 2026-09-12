# Pearnly / WeKan deployment

Production entry: **https://pearnly.com/cowork** → การทำงานร่วมกัน →
**https://work.pearnly.com**. Exact release identities and acceptance limits are in
[the deployment ledger](../../docs/deployment/MIGRATION_STATUS.md) and
[the task record](../../docs/project/WEKAN_SSO_20260912.md).

All COWORK accounts use one service. There is no firm allowlist, first-owner
configuration or per-firm activation. Pearnly's ordinary employee permissions
apply in COWORK; native WeKan site and board roles apply after entry. A native
WeKan administrator does not become a Pearnly owner or platform administrator.

## Source and authentication

The upstream checkout remains `/Users/skin/wekan`. The additive Docker image
pins the official multi-architecture WeKan image by digest; the local checkout
is a source reference, not proof of that image's source revision. The pinned
running image reports WeKan 11.58.0. Pearnly integration code lives here and in
`services/work_bridge`, `routes/work_bridge_routes.py` and `/work`.

The installer preserves native permission checks. It adds missing awaits in
the pinned `setCreateUser` and `inviteUserToBoard` account-creation and enrollment calls, and
allows username-only invitations to finish without attempting an absent email, and
extends SockJS's allowed request headers with the two private gateway identity
headers. It fails if those upstream code shapes change.

Pearnly's access token stays on the Pearnly origin. A 60-second, single-use
ticket is bound to a gateway browser-state cookie. The gateway receives an
opaque parent-session handle and stores it in an encrypted HttpOnly cookie.
All HTTP requests, files and WebSocket upgrades require a live parent session.
WebSockets revalidate that parent every five seconds and close on validation
failure (including the bounded service-request timeout). WeKan login/resume
tokens and HTTP authentication tokens must match the gateway's Pearnly identity.
Native account disable/delete also closes its active DDP connections.
The native logout button revokes the bridge session before returning to COWORK.

Native permission-checked employee creation writes an ordinary Pearnly employee
and retains WeKan's own role flags. The Pearnly password is the only login
password; native public signup is closed. Existing Pearnly email invitations
link by immutable account ID without resetting passwords or changing COWORK
membership. New email invitations use Pearnly's existing password-setup flow.
Pearnly account and tenant suspension govern access to Pearnly; WeKan role
changes and account suspension govern WeKan only.

## Durable hosting

Pearnly Web/Worker retain Cloud Run. The separate stateful service runs in GCP
project `pearnly`, zone `asia-southeast1-b`, on VM `pearnly-work` (e2-medium,
4 GiB). Static address: `136.85.65.80`; retained 30 GiB data disk:
`pearnly-work-data`, mounted at `/srv/pearnly-work`. Do not reuse or modify the ERPNext VM or its
project. The WeKan/MongoDB disk must not be an ephemeral Cloud Run filesystem.

`compose.yml` is the local stack. Add `compose.production.yml` for authenticated
MongoDB, explicit memory/log limits and Caddy TLS. Only Caddy's 80/443 ports are
public. Gateway 8096 binds loopback; WeKan 8080 and MongoDB 27017 have no host
port. The only SSH ingress should be Google IAP. Use a dedicated VM service
account with access only to its runtime secret and the image repository.

Create `work.pearnly.com` on the Pearnly DNS zone and point it to the new VM's
static address. Preserve the main/www Worker routes, other DNS records and
existing TLS policy. Pearnly and WeKan use the same site so the state cookie
remains compatible with the cross-origin form POST. Verify DNS and TLS before
publishing the COWORK entry configuration.

Populate `runtime.env.example` in Secret Manager with independent generated
secrets and an immutable `WORK_IMAGE` digest. MongoDB passwords must be URL-safe.
The application MongoDB user has only `readWrite` on database `wekan`; it is
created only when the data volume is empty. Changing environment variables
does not rotate an existing database user's password.

The host uses dedicated Secret Manager secret `pearnly-work-env`; Web and
Worker runtime secrets are separate. Fetch only the pinned secret version with
the host service account, write it root-owned mode 0600, and pull the immutable
image using short-lived registry authentication. Do not print secret contents.

From `/srv/pearnly-work/app`, after the exact source/image is verified:

```sh
docker compose --env-file /srv/pearnly-work/app/runtime.env -p pearnly-work \
  -f compose.yml -f compose.production.yml config --quiet
docker compose --env-file /srv/pearnly-work/app/runtime.env -p pearnly-work \
  -f compose.yml -f compose.production.yml up -d
```

The runtime file must be root-owned, mode 0600. Preserve database, files and
certificate volumes on image updates; never use `down -v` in production.
Use the application-consistent snapshot procedure below; test restoration from
a cloned disk and an isolated MongoDB container, never over the live database. Before changing MongoDB or
WeKan versions, take a version-labelled database/file backup and validate the
upgrade against its copy. Initial single-instance hosting has no automatic
failover; its capacity and monthly infrastructure cost require live readback.

## Application-consistent snapshots

The attached policy `pearnly-work-consistent-daily` snapshots the data disk at
20:00 UTC (03:00 Bangkok), retains seven days, and keeps automatic snapshots
when the source disk is deleted. It has `guestFlush=true` and regional storage
in `asia-southeast1`. The retained data disk contains Docker volumes, MongoDB,
attachments, Caddy certificates and the private runtime file.

Install the supplied hooks on this dedicated host:

```sh
sudo install -d /etc/google/snapshots
sudo install -m 755 snapshot-pre.sh /etc/google/snapshots/pre.sh
sudo install -m 755 snapshot-post.sh /etc/google/snapshots/post.sh
```

In `/etc/default/instance_configs.cfg`, preserve existing sections and add or
update `[Snapshots]` with `enabled = true` and `timeout_in_seconds = 60`, then
restart `google-guest-agent`. The pre-hook locks MongoDB, runs `sync`, and freezes
the data filesystem. The post-hook thaws it and unlocks MongoDB. A 240-second
systemd timer invokes the same idempotent thaw if the guest agent fails.
MongoDB lock status must be checked with the raw admin `currentOp` command;
`db.currentOp()` omits that flag in this mongosh version.

Recovery acceptance on 2026-09-12 restored snapshot
`pearnly-work-verified-20260912` to a separate disk, mounted the clone with normal
ext4 journal recovery, and copied its database into a disposable authenticated
MongoDB container with `--network none`. Both a database marker and attachment
volume bytes matched the originals. Temporary containers, copied data and clone
disks were removed after verification. This proves recovery from the manual
snapshot; the first scheduled execution is still to occur.

Before a version upgrade, take a guest-flush snapshot, verify hook completion and
an unlocked database, then validate that version against a clone. A live image
rollback must keep the same volumes and use a previously recorded digest.
See [Google's guest-flush instructions](https://docs.cloud.google.com/compute/docs/disks/creating-linux-application-consistent-pd-snapshots).

## Pearnly release order

1. Pass native login/creation/role/revocation acceptance and project gates.
2. Build the pinned addon for the VM architecture and record its registry digest.
3. Deploy the private persistent stack and TLS gateway; read back resource,
   image and volume identities. `/_pearnly/health` must verify native MongoDB
   access, not merely a running gateway process.
4. Add the same `WORK_BRIDGE_URL` and `WORK_BRIDGE_SECRET` to Pearnly's existing
   Web/Worker runtime secrets while preserving other fields.
5. Release the exact reviewed Pearnly master SHA using
   [the existing Cloud Run workflow](../../docs/deployment/CLOUD_RUN.md).
   Its serialized schema job applies the additive `0128_work_bridge` schema;
   do not run an independent production Alembic command.
6. Verify both Cloud Run revisions/digests/traffic/readiness, then normal user
   login, menu entry, native invitation, employee login, board roles, attachments
   and revocation on the formal URLs. Do not create test business documents in
   real customer workspaces or email real users for acceptance testing.

Keep the previous verified Pearnly revision and WeKan image. Code rollback
retains the additive identity tables and persistent volumes. Disabling WeKan
must not disable COWORK accounts or promote/demote their Pearnly roles.

## Acceptance limits

The formal browser login/menu/logout, native employee issuance through Pearnly,
board roles, file upload/download, revocation and backup restoration passed.
Actual invitation-email receipt and user-device acceptance remain unverified.
The pinned upstream's optional HTTP/DDP attachment-upload APIs fail; webpage
upload/download works and has been checked byte-for-byte. See the task record
for those exact failed API paths before implementing an API-based upload client.
