"""Render, or explicitly apply, Pearnly-only Monitoring resources; never create channels."""

import argparse
import json
import subprocess
import urllib.parse
import urllib.request

PROJECT = "pearnly"
BASE = "https://monitoring.googleapis.com/v3/projects/" + PROJECT
PREFIX = "Pearnly Cloud Run / "


def request(method, url, body=None):
    token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def listing(collection, key):
    result, cursor = [], ""
    while True:
        data = request(
            "GET",
            BASE
            + "/"
            + collection
            + ("?pageToken=" + urllib.parse.quote(cursor) if cursor else ""),
        )
        result.extend(data.get(key, []))
        cursor = data.get("nextPageToken")
        if not cursor:
            return result


def uptime():
    return {
        "displayName": PREFIX + "public readiness",
        "monitoredResource": {
            "type": "uptime_url",
            "labels": {"project_id": PROJECT, "host": "pearnly.com"},
        },
        "httpCheck": {
            "path": "/api/ready",
            "port": 443,
            "useSsl": True,
            "validateSsl": True,
            "requestMethod": "GET",
            "acceptedResponseStatusCodes": [{"statusValue": 200}],
        },
        "period": "900s",
        "timeout": "30s",
        "contentMatchers": [{"content": '"ready"\\s*:\\s*true', "matcher": "MATCHES_REGEX"}],
    }


def policy(name, condition, channels):
    return {
        "displayName": PREFIX + name,
        "combiner": "OR",
        "enabled": True,
        "notificationChannels": channels,
        "userLabels": {"managed_by": "pearnly-cloud-run"},
        "conditions": [{"displayName": name, **condition}],
        "documentation": {
            "mimeType": "text/markdown",
            "content": "Pearnly application only; ERPNext is a separate project. See repository docs/deployment/MIGRATION_STATUS.md. No channels means console incidents only, not delivered notifications.",
        },
    }


def policies(channels, uptime_id, queue):
    resource = 'resource.type="cloud_run_revision" AND resource.labels.project_id="pearnly" AND resource.labels.location="asia-southeast1" AND (resource.labels.service_name="pearnly-web" OR resource.labels.service_name="pearnly-worker")'
    threshold = {
        "filter": resource + ' AND metric.type="run.googleapis.com/container/memory/utilizations"',
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.85,
        "duration": "300s",
        "aggregations": [{"alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_PERCENTILE_99"}],
        "trigger": {"count": 1},
    }
    output = [policy("memory above 85 percent", {"conditionThreshold": threshold}, channels)]
    output.append(
        policy(
            "task queue backlog",
            {
                "conditionThreshold": {
                    "filter": 'resource.type="cloud_tasks_queue" AND resource.labels.project_id="pearnly" AND resource.labels.location="asia-southeast1" AND resource.labels.queue_id="'
                    + queue
                    + '" AND metric.type="cloudtasks.googleapis.com/queue/depth"',
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 10,
                    "duration": "600s",
                    "aggregations": [{"alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_MAX"}],
                    "trigger": {"count": 1},
                }
            },
            channels,
        )
    )
    logs = policy(
        "task failed or uncertain",
        {
            "conditionMatchedLog": {
                "filter": resource
                + ' AND ("cloud_task_failed" OR "cloud_task_uncertain" OR "cloud_task_delivery_pending" OR "cloud_queue_wakeup_pending")'
            }
        },
        channels,
    )
    logs["alertStrategy"] = {"notificationRateLimit": {"period": "900s"}, "autoClose": "86400s"}
    output.append(logs)
    output.append(
        policy(
            "public readiness unavailable",
            {
                "conditionThreshold": {
                    "filter": 'resource.type="uptime_url" AND metric.type="monitoring.googleapis.com/uptime_check/check_passed" AND metric.labels.check_id="'
                    + uptime_id
                    + '"',
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 1,
                    "duration": "0s",
                    "aggregations": [
                        {
                            "alignmentPeriod": "1200s",
                            "perSeriesAligner": "ALIGN_NEXT_OLDER",
                            "crossSeriesReducer": "REDUCE_COUNT_FALSE",
                            "groupByFields": ["resource.label.host"],
                        }
                    ],
                    "trigger": {"count": 1},
                }
            },
            channels,
        )
    )
    return output


def upsert(collection, desired, existing):
    matches = [item for item in existing if item.get("displayName") == desired["displayName"]]
    if len(matches) > 1:
        raise ValueError("duplicate managed display name; refuse ambiguous update")
    if not matches:
        return request("POST", BASE + "/" + collection, desired)
    current = matches[0]
    # Patch only owned fields; never delete unrelated resources or channel definitions.
    body = {**desired, "name": current["name"]}
    mask = ",".join(desired)
    return request(
        "PATCH",
        "https://monitoring.googleapis.com/v3/" + current["name"] + "?updateMask=" + mask,
        body,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--queue", required=True)
    parser.add_argument("--channel", action="append", default=[])
    args = parser.parse_args()
    if not args.queue.startswith("pearnly-") or any(
        c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in args.queue
    ):
        parser.error("queue must be an explicit pearnly- queue name")
    available = listing("notificationChannels", "notificationChannels")
    for channel in args.channel:
        if not any(c["name"] == channel and c.get("enabled", True) for c in available):
            parser.error(
                "channel must already exist and be enabled in project pe ar nly".replace(
                    "pe ar nly", PROJECT
                )
            )
    if not args.apply:
        print(
            json.dumps(
                {
                    "project": PROJECT,
                    "mode": "UNAPPLIED_PLAN",
                    "notificationsDelivered": bool(args.channel),
                    "uptime": uptime(),
                    "policies": policies(args.channel, "RESOLVED_ON_APPLY", args.queue),
                },
                indent=2,
            )
        )
        return
    check = upsert(
        "uptimeCheckConfigs", uptime(), listing("uptimeCheckConfigs", "uptimeCheckConfigs")
    )
    existing = listing("alertPolicies", "alertPolicies")
    for desired in policies(args.channel, check["name"].split("/")[-1], args.queue):
        result = upsert("alertPolicies", desired, existing)
        print(
            json.dumps(
                {
                    "name": result["name"],
                    "displayName": result["displayName"],
                    "notificationChannels": result.get("notificationChannels", []),
                }
            )
        )


if __name__ == "__main__":
    main()
