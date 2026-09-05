"""Use the candidate image, environment and mounts for one schema execution."""

from copy import deepcopy
import json
import sys


def render_job(service):
    spec = deepcopy(service["spec"]["template"]["spec"])
    container = spec["containers"][0]
    container.pop("ports", None)
    container.pop("startupProbe", None)
    for item in container["env"]:
        if item["name"] == "PEARNLY_RUNTIME_ROLE":
            item["value"] = "schema"
    spec.pop("containerConcurrency", None)
    spec["maxRetries"] = 0
    spec["timeoutSeconds"] = "900"
    return {
        "apiVersion": "run.googleapis.com/v1",
        "kind": "Job",
        "metadata": {"name": "pearnly-schema"},
        "spec": {
            "template": {
                "metadata": {"annotations": {"run.googleapis.com/execution-environment": "gen2"}},
                "spec": {
                    "taskCount": 1,
                    "parallelism": 1,
                    "template": {
                        "spec": spec,
                    },
                },
            }
        },
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as source:
        print(json.dumps(render_job(json.load(source)), indent=2))
