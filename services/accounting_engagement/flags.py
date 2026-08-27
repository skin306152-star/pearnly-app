"""ERP 到 Cowork 关系层灰度闸。"""

from typing import Optional

ERP_COWORK_ENGAGEMENTS_KEY = "erp_cowork_engagements"


def enabled_for(tenant_id: Optional[str]) -> bool:
    """默认关闭；设置缺失或读取失败均不放量。"""
    if not tenant_id:
        return False
    try:
        from services.platform_settings import store

        return store.is_enabled_for_user(ERP_COWORK_ENGAGEMENTS_KEY, str(tenant_id))
    except Exception:
        return False
