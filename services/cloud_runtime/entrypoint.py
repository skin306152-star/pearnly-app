"""Load a pinned Secret Manager environment before importing application modules."""

import os
from pathlib import Path


def load_environment() -> str:
    from dotenv import dotenv_values

    role = os.environ.get("PEARNLY_RUNTIME_ROLE", "")
    if role not in {"web", "worker", "schema"}:
        raise RuntimeError("PEARNLY_RUNTIME_ROLE must be web, worker or schema")
    secret = Path(os.environ.get("PEARNLY_RUNTIME_ENV_FILE", "/secrets/runtime.env"))
    if not secret.is_file():
        raise RuntimeError("Pinned runtime environment is missing")
    for key, value in dotenv_values(secret).items():
        if value is not None:
            os.environ.setdefault(key, value)
    return role


def main() -> None:
    role = load_environment()
    if role == "schema":
        from services.cloud_runtime.schema import migrate

        migrate()
        return
    from services.cloud_runtime.application import app
    from services.cloud_runtime.server import run

    run(app)


if __name__ == "__main__":
    main()
