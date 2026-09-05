"""Render a pinned Cloud Run service as JSON (also valid YAML)."""

from __future__ import annotations

import argparse
import json
import re


def render_service(
    *,
    role,
    image,
    secret_version,
    project,
    account,
    files_bucket,
    temp_bucket,
    installers_bucket,
    worker_url="",
    region="asia-southeast1",
):
    if role not in {"web", "worker"}:
        raise ValueError("role must be web or worker")
    if not re.fullmatch(r".+@sha256:[0-9a-f]{64}", image):
        raise ValueError("image must be pinned by sha256 digest")
    if not re.fullmatch(r"[1-9][0-9]*", str(secret_version)):
        raise ValueError("secret version must be a positive numeric version")
    mount_options = (
        "implicit-dirs,metadata-cache-ttl-secs=0,stat-cache-max-size-mb=0,"
        "type-cache-max-size-mb=0,uid=10001,gid=10001"
    )
    volumes = []
    mounts = []
    buckets = {"files": files_bucket, "temp": temp_bucket, "installers": installers_bucket}
    for name, bucket, path, extra, readonly in (
        ("files", "files", "/opt/mrpilot/storage", "", False),
        ("uploads", "files", "/opt/mrpilot/uploads", ",only-dir=uploads", False),
        ("temp", "temp", "/opt/mrpilot/var", "", False),
        ("installers", "installers", "/app/static/companion", "", True),
    ):
        volumes.append(
            {
                "name": name,
                "csi": {
                    "driver": "gcsfuse.run.googleapis.com",
                    "readOnly": readonly,
                    "volumeAttributes": {
                        "bucketName": buckets[bucket],
                        "mountOptions": mount_options + extra,
                    },
                },
            }
        )
        mounts.append({"name": name, "mountPath": path})
    volumes.append(
        {
            "name": "runtime",
            "secret": {
                "secretName": f"pearnly-{role}-env",
                "items": [{"key": str(secret_version), "path": "runtime.env"}],
            },
        }
    )
    mounts.append({"name": "runtime", "mountPath": "/secrets"})
    env = {
        "PEARNLY_RUNTIME_ROLE": role,
        "PEARNLY_RUNTIME_ENV_FILE": "/secrets/runtime.env",
        "PEARNLY_OCR_CACHE_DIR": "/tmp/ocr-cache",
        "RECON_AI_MAPPING_CACHE_DIR": "/tmp/ai-mapping-cache",
        "GOOGLE_CLOUD_PROJECT": project,
        "GOOGLE_CLOUD_LOCATION": region,
    }
    if worker_url:
        env["PEARNLY_WORKER_URL"] = worker_url
    return {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service",
        "metadata": {
            "name": f"pearnly-{role}",
            "annotations": {"run.googleapis.com/ingress": "all"},
        },
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "autoscaling.knative.dev/minScale": "0",
                        "autoscaling.knative.dev/maxScale": "2",
                        "run.googleapis.com/execution-environment": "gen2",
                        "run.googleapis.com/cpu-throttling": "true",
                        "run.googleapis.com/startup-cpu-boost": "true",
                    }
                },
                "spec": {
                    "serviceAccountName": account,
                    "containerConcurrency": 4 if role == "web" else 1,
                    "timeoutSeconds": 1800,
                    "containers": [
                        {
                            "image": image,
                            "ports": [{"containerPort": 8080}],
                            "resources": {
                                "limits": {
                                    "cpu": "1",
                                    "memory": "1Gi" if role == "web" else "2Gi",
                                }
                            },
                            "env": [{"name": key, "value": value} for key, value in env.items()],
                            "volumeMounts": mounts,
                            "startupProbe": {
                                "httpGet": {"path": "/api/health", "port": 8080},
                                "periodSeconds": 5,
                                "timeoutSeconds": 3,
                                "failureThreshold": 48,
                            },
                        }
                    ],
                    "volumes": volumes,
                },
            },
            "traffic": [{"latestRevision": True, "percent": 100}],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=["web", "worker"], required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--secret-version", required=True)
    parser.add_argument("--project", default="pearnly")
    parser.add_argument("--account", required=True)
    parser.add_argument("--files-bucket", required=True)
    parser.add_argument("--temp-bucket", required=True)
    parser.add_argument("--installers-bucket", required=True)
    parser.add_argument("--worker-url", default="")
    parser.add_argument("--region", default="asia-southeast1")
    args = vars(parser.parse_args())
    print(json.dumps(render_service(**args), indent=2))


if __name__ == "__main__":
    main()
