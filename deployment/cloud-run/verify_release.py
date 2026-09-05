"""Gate Cloud Run traffic on the candidate image and its actual HTTP runtime."""

import argparse
import json
import subprocess
import urllib.request
from pathlib import Path

PROJECT = "pearnly"
REGION = "asia-southeast1"


def gcloud(*args):
    return subprocess.check_output(["gcloud", *args], text=True).strip()


def candidate_service(service, previous, revision):
    """Pin existing serving revisions so latestRevision cannot switch traffic."""
    service["spec"]["template"]["metadata"]["name"] = revision
    traffic = []
    for item in previous.get("status", {}).get("traffic", []):
        if item.get("tag") == "candidate" and not item.get("percent", 0):
            continue
        entry = {key: item[key] for key in ("revisionName", "percent", "tag") if key in item}
        if entry.get("tag") == "candidate":
            entry.pop("tag")
        if "revisionName" not in entry:
            raise ValueError("existing traffic has no resolved revision")
        traffic.append(entry)
    if previous and sum(item.get("percent", 0) for item in traffic) != 100:
        raise ValueError("cannot preserve existing traffic allocation")
    traffic.append(
        {"revisionName": revision, "tag": "candidate", "percent": 0 if previous else 100}
    )
    service["spec"]["traffic"] = traffic
    return service


def check_revision(revision, expected_revision, image):
    if revision["metadata"]["name"] != expected_revision:
        raise ValueError("revision identity mismatch")
    if revision["spec"]["containers"][0]["image"] != image:
        raise ValueError("revision image mismatch")
    if not any(
        c.get("type") == "Ready" and c.get("status") == "True"
        for c in revision["status"]["conditions"]
    ):
        raise ValueError("revision not ready")
    actual_digest = revision["status"].get("imageDigest", "")
    if actual_digest.split("@")[-1] != image.split("@")[-1]:
        raise ValueError("resolved image digest mismatch")


def check_runtime(payload, sha, revision, role):
    if payload != {"sha": sha, "revision": revision, "role": role}:
        raise ValueError("HTTP runtime identity mismatch")


def check_readiness(payload):
    if payload.get("ready") is not True:
        raise ValueError("application readiness failed")
    if payload.get("ok") is False or payload.get("status") in {"error", "failed", "not_ready"}:
        raise ValueError("application readiness failed")


def probe(url, token):
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    # Do not follow redirects to an old production host or another revision.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    with urllib.request.build_opener(NoRedirect).open(request, timeout=180) as response:
        if response.status != 200:
            raise ValueError("HTTP gate failed")
        return json.load(response)


def verify(args):
    service = json.loads(
        gcloud(
            "run",
            "services",
            "describe",
            f"pearnly-{args.role}",
            "--project=" + PROJECT,
            "--region=" + REGION,
            "--format=json",
        )
    )
    revision = json.loads(
        gcloud(
            "run",
            "revisions",
            "describe",
            args.revision,
            "--project=" + PROJECT,
            "--region=" + REGION,
            "--format=json",
        )
    )
    check_revision(revision, args.revision, args.image)
    if args.candidate:
        candidates = [
            t
            for t in service["status"]["traffic"]
            if t.get("tag") == "candidate" and t.get("revisionName") == args.revision
        ]
        if len(candidates) != 1:
            raise ValueError("candidate tag missing or ambiguous")
        url = candidates[0]["url"]
    else:
        active = [t for t in service["status"]["traffic"] if t.get("percent", 0)]
        if (
            len(active) != 1
            or active[0].get("revisionName") != args.revision
            or active[0]["percent"] != 100
        ):
            raise ValueError("traffic does not serve the verified revision")
        url = service["status"]["url"]
    token = gcloud(
        "auth",
        "print-identity-token",
        "--impersonate-service-account=pearnly-deploy@pearnly.iam.gserviceaccount.com",
        "--audiences=" + service["status"]["url"],
    )
    probe(url + "/api/health", token)
    ready = probe(url + "/api/ready", token)
    check_readiness(ready)
    check_runtime(
        probe(url + "/internal/runtime-version", token), args.sha, args.revision, args.role
    )
    print(
        json.dumps(
            {
                "role": args.role,
                "revision": args.revision,
                "image": args.image,
                "sha": args.sha,
                "url": url,
                "candidate": args.candidate,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", nargs=3, metavar=("SERVICE", "PREVIOUS", "REVISION"))
    parser.add_argument("--sha")
    parser.add_argument("--image")
    parser.add_argument("--role", choices=("web", "worker"))
    parser.add_argument("--revision")
    parser.add_argument("--candidate", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        path, previous, revision = args.prepare
        candidate = candidate_service(
            json.loads(Path(path).read_text()), json.loads(Path(previous).read_text()), revision
        )
        Path(path).write_text(json.dumps(candidate, indent=2) + "\n")
    else:
        if not all((args.sha, args.image, args.role, args.revision)):
            parser.error("verification requires sha, image, role and revision")
        verify(args)


if __name__ == "__main__":
    main()
