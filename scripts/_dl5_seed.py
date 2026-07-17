# -*- coding: utf-8 -*-
"""DL-5 forensic harness · seed local DB (underscore = not shipped).

Idempotent: tenant + user + one enabled mrerp_dms endpoint (dmstest creds) +
dms_line / dms_portal flags flipped to rollout=all. Safe to rerun.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "DATABASE_URL", "postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly"
)

from scripts import _dl5_common as C  # noqa: E402


def _seed_tenant_user() -> None:
    import psycopg2

    with psycopg2.connect(C.DB_URL) as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO tenants
                 (id, name, tenant_type, status, used_this_month, quota_reset_at,
                  quota_alert_sent, member_count, created_at, updated_at)
               VALUES (%s, %s, 'firm', 'active', 0, CURRENT_DATE, false, 1, now(), now())
               ON CONFLICT (id) DO NOTHING""",
            (C.TENANT_ID, "DL5 E2E Tenant"),
        )
        cur.execute(
            """INSERT INTO users
                 (id, username, password_hash, tenant_id, role, plan)
               VALUES (%s, %s, %s, %s, 'owner', 'free')
               ON CONFLICT (id) DO UPDATE SET tenant_id = EXCLUDED.tenant_id""",
            (C.USER_ID, "dl5_e2e", "x", C.TENANT_ID),
        )
        conn.commit()


def _seed_endpoint() -> str:
    from core import db  # import via core.db to avoid the push_store circular import
    import psycopg2

    # Drop any prior DL5 mrerp_dms endpoints so resolve picks a clean one.
    with psycopg2.connect(C.DB_URL) as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM erp_endpoints WHERE user_id=%s AND adapter='mrerp_dms'", (C.USER_ID,)
        )
        conn.commit()
    cfg = dict(C.DMS_CFG)
    if os.environ.get("DL5_SINGLE_CRED") == "1":
        # dmstest is itself admin on the test site → route writes through the
        # user session (single-cred). Isolates the admin-writer defect.
        cfg.pop("admin_username", None)
        cfg.pop("admin_password", None)
    eid = db.create_erp_endpoint(C.USER_ID, C.ENDPOINT_NAME, "mrerp_dms", cfg, is_default=True)
    if not eid:
        raise RuntimeError("create_erp_endpoint failed")
    return eid


def _enable_flags() -> None:
    from services.platform_settings import store

    store.set_setting("dms_line", {"rollout": "all"}, True)
    store.set_setting("dms_portal", {"rollout": "all"}, True)


def main() -> None:
    _seed_tenant_user()
    eid = _seed_endpoint()
    _enable_flags()
    from core.feature_flags import dms_line_enabled_for, dms_portal_enabled_for

    print("endpoint_id:", eid)
    print("dms_line_enabled:", dms_line_enabled_for(C.TENANT_ID, C.USER_ID))
    print("dms_portal_enabled:", dms_portal_enabled_for(C.TENANT_ID, C.USER_ID))


if __name__ == "__main__":
    main()
