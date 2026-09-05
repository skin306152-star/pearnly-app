#!/usr/bin/env bash
set -euo pipefail
sha=${1:?exact SHA required}
image=${2:?immutable image digest required}
[[ "$sha" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ "$image" =~ ^asia-southeast1-docker.pkg.dev/pearnly/pearnly-app/app@sha256:[0-9a-f]{64}$ ]] || exit 2
project=pearnly
region=asia-southeast1
worker_url=https://pearnly-worker-112074003592.asia-southeast1.run.app
render_dir=$(mktemp -d)
trap 'rm -rf "$render_dir"' EXIT
gcloud run services list --project="$project" --region="$region" --format='value(metadata.name)' > "$render_dir/services"
for role in worker web; do
  if grep -Fxq "pearnly-$role" "$render_dir/services"; then
    gcloud run services describe "pearnly-$role" --project="$project" --region="$region" --format=json > "$render_dir/$role-previous.json"
  else
    echo '{}' > "$render_dir/$role-previous.json"
  fi
  secret_version=$(gcloud secrets versions list "pearnly-${role}-env" --project="$project" --filter='state=ENABLED' --sort-by='~createTime' --limit=1 --format='value(name)')
  secret_version=${secret_version##*/}
  python deployment/cloud-run/render_service.py \
    --role "$role" --project "$project" --image "$image" \
    --secret-version "$secret_version" --account "pearnly-${role}@${project}.iam.gserviceaccount.com" \
    --files-bucket pearnly-app-files-112074003592 --temp-bucket pearnly-app-temp-112074003592 \
    --installers-bucket pearnly-app-installers-112074003592 --worker-url "$worker_url" \
    > "$render_dir/$role.json"
  revision="pearnly-$role-${sha:0:12}-s$secret_version"
  echo "$revision" > "$render_dir/$role-revision"
  python deployment/cloud-run/verify_release.py --prepare "$render_dir/$role.json" "$render_dir/$role-previous.json" "$revision"
done
# A single workflow concurrency group serializes the one-shot schema gate.
python deployment/cloud-run/render_job.py "$render_dir/worker.json" > "$render_dir/schema.json"
gcloud run jobs replace "$render_dir/schema.json" --project="$project" --region="$region" --quiet
gcloud run jobs execute pearnly-schema --project="$project" --region="$region" --wait --quiet
# Both candidates must pass before either existing traffic allocation changes.
for role in worker web; do
  revision=$(cat "$render_dir/$role-revision")
  gcloud run services replace "$render_dir/$role.json" --project="$project" --region="$region" --quiet
  # Service-scoped grants preserve existing public IAM; initial Web stays private.
  invokers=(pearnly-deploy)
  if [[ "$role" == worker ]]; then
    invokers+=(pearnly-web pearnly-tasks)
  fi
  for invoker in "${invokers[@]}"; do
    gcloud run services add-iam-policy-binding "pearnly-$role"       --member="serviceAccount:$invoker@$project.iam.gserviceaccount.com"       --role=roles/run.invoker --project="$project" --region="$region" --quiet >/dev/null
  done
  python deployment/cloud-run/verify_release.py --sha "$sha" --image "$image" --role "$role" --revision "$revision" --candidate
done
for role in worker web; do
  revision=$(cat "$render_dir/$role-revision")
  gcloud run services update-traffic "pearnly-$role" --to-revisions="$revision=100" --project="$project" --region="$region" --quiet
  python deployment/cloud-run/verify_release.py --sha "$sha" --image "$image" --role "$role" --revision "$revision"
done
