#!/usr/bin/env bash
# Dedicated new WeKan VM only. Data disk is retained independently of the VM.
set -euo pipefail

WORK_PROJECT=$(curl --fail --silent --show-error -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/project/project-id)
test "$WORK_PROJECT" = pearnly
WORK_DEVICE=/dev/disk/by-id/google-work-data
test -b "$WORK_DEVICE"
if ! blkid "$WORK_DEVICE" >/dev/null; then
  mkfs.ext4 -F "$WORK_DEVICE"
fi
test "$(blkid -s TYPE -o value "$WORK_DEVICE")" = ext4
WORK_DISK_UUID=$(blkid -s UUID -o value "$WORK_DEVICE")
mkdir -p /srv/pearnly-work /etc/docker /etc/systemd/system/docker.service.d
if ! grep -q "UUID=$WORK_DISK_UUID " /etc/fstab; then
  printf 'UUID=%s /srv/pearnly-work ext4 defaults 0 2\n' "$WORK_DISK_UUID" >> /etc/fstab
fi
mountpoint -q /srv/pearnly-work || mount /srv/pearnly-work
cat > /etc/docker/daemon.json <<'JSON'
{"data-root":"/srv/pearnly-work/docker"}
JSON
cat > /etc/systemd/system/docker.service.d/pearnly-work.conf <<'UNIT'
[Unit]
RequiresMountsFor=/srv/pearnly-work
UNIT
if ! command -v docker >/dev/null; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io docker-compose-v2 python3 curl ca-certificates
fi
systemctl daemon-reload
systemctl enable --now docker
docker compose version
printf 'Pearnly WeKan host ready; persistent Docker storage mounted.\n'
