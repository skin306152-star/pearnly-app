"""Persist supplier-specific purchase category choices from web edits."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def learn_category(cur, *, tenant_id, workspace_client_id, supplier, category_id, subcategory_id):
    if not category_id:
        return
    try:
        from services.expense import category_learning as learning_store
        from services.expense import merchant
        from services.purchase import categories as category_service

        supplier = supplier or {}
        name = supplier.get("name") or ""
        tax_id = str(supplier.get("tax_id") or "").strip()
        category_name = ""
        subcategory_name = ""
        for parent in category_service.get_tree(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        ):
            if parent.get("id") != category_id:
                continue
            category_name = parent.get("name") or ""
            for child in parent.get("children") or []:
                if child.get("id") == subcategory_id:
                    subcategory_name = child.get("name") or ""
            break

        keys = []
        if tax_id:
            keys.append(f"tax:{tax_id}")
        canonical_name = merchant.canonical_merchant(name, tax_id)
        if canonical_name:
            keys.append(f"seller:{canonical_name}")
        for key in keys:
            learning_store.learn(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                keyword=key,
                category_id=category_id,
                subcategory_id=subcategory_id,
                category_name=category_name,
                subcategory_name=subcategory_name,
            )
    except Exception as exc:
        logger.warning("purchase category learning skipped: %s", str(exc)[:160])


def learn_from_doc_edit(cur, tenant_id, workspace_client_id, data, lines):
    category_id = (data or {}).get("category_id")
    if not category_id:
        return
    subcategory_id = next(
        (
            line.get("subcategory_id")
            for line in (lines or [])
            if line.get("category_id") == category_id
        ),
        None,
    )
    learn_category(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        supplier=(data or {}).get("supplier"),
        category_id=category_id,
        subcategory_id=subcategory_id,
    )
