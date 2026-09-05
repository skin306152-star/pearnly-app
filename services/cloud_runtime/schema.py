"""One-shot schema gate, executed before a new revision receives traffic."""

import logging


class SchemaFailures(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.failures = []
        self.locations = set()

    def emit(self, record):
        self.failures.append(record.getMessage())
        self.locations.add(f"{record.name}.{record.funcName}")


def migrate() -> None:
    failures = SchemaFailures()
    root = logging.getLogger()
    root.addHandler(failures)
    try:
        from services.auth.schema import _ensure_schema
        from services.startup import _boot_schema_ddl
        from services.users.columns import ensure_user_profile_columns
        from services.cloud_tasks.store import ensure_table

        _ensure_schema()
        _boot_schema_ddl()
        ensure_user_profile_columns()
        ensure_table()
    finally:
        root.removeHandler(failures)
    if failures.failures:
        locations = ", ".join(sorted(failures.locations))
        raise RuntimeError(
            f"Schema gate reported failures in {locations}; revision must not receive traffic"
        )


if __name__ == "__main__":
    migrate()
