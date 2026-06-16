# -*- coding: utf-8 -*-
"""第 8 道机械闸 · 路由权限覆盖(docs/permissions/05 · OWASP 漏门靠机器拦)。

每条 FastAPI 路由必须满足其一:
  1. 源码可见的守门(require_perm 系 / 九旧门 / 登录态 / 文件内鉴权 helper)
  2. PUBLIC_ROUTES 显式白名单(为何公开必须写注释)
  3. DELEGATED_ROUTES(转发给已守门实现的别名,逐条注明委托点)
不满足 = exit 1 + 缺门清单。挂 pre-push + CI。

用法:python scripts/check_authz_coverage.py [--quiet]
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.authz_route_inventory import collect_routes  # noqa: E402

# 真公开面:每条必须带"为何公开"注释。新增公开路由必须在这里登记。
PUBLIC_ROUTES = {
    # 页面服务(SPA 外壳,鉴权在前端 boot + 后端 API)
    ("GET", "/"),
    ("GET", "/login"),
    ("GET", "/home"),
    ("GET", "/admin"),
    ("GET", "/admin/{rest:path}"),
    ("GET", "/pos"),
    ("GET", "/pos/{rest:path}"),
    ("GET", "/pos-sw.js"),  # PWA Service Worker 脚本(公开静态 · 前端鉴权同 /pos)
    ("GET", "/console"),
    ("GET", "/console/{rest:path}"),
    ("GET", "/invite/{token}"),
    ("GET", "/reset"),
    ("GET", "/terms"),
    ("GET", "/privacy"),
    # 健康/元信息(监控与前端版本探测,无敏感数据)
    ("GET", "/api/health"),
    ("GET", "/api/ready"),
    ("GET", "/api/contact"),
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/contact"),
    ("GET", "/api/version"),
    # 登录/注册/找回(登录前链路,自身就是发证点)
    ("POST", "/api/login"),
    ("POST", "/api/auth/send_email_code"),
    ("POST", "/api/auth/verify_email_code"),
    ("POST", "/api/auth/forgot_password"),
    ("POST", "/api/auth/reset_password"),
    ("GET", "/api/auth/google/start"),
    ("GET", "/api/auth/google/callback"),
    ("GET", "/api/auth/line/start"),
    ("GET", "/api/auth/line/callback"),
    # OAuth 回调(state 即凭证)
    ("GET", "/api/erp/xero/auth/callback"),
    ("GET", "/api/integrations/google/callback"),  # Google 外流授权回调 · state CSRF 即凭证
    # webhook(签名校验在实现内:LINE signature / GitHub secret)
    ("POST", "/api/line/webhook"),
    ("POST", "/api/line/liff/auth"),  # LIFF id_token 即凭证(LINE verify 验签)
    ("GET", "/api/line/liff/config"),  # 仅返回公开 LIFF ID(非密)· 前端 liff.init 用
    ("GET", "/liff/purchase/{doc_id}"),  # LIFF 页入口·跳 /home 复核屏(前端 LIFF 鉴权)
    ("GET", "/liff/purchase-inbox/{item_id}"),  # LIFF 入口·跳 /home 待归类页(前端 LIFF 鉴权)
    ("POST", "/internal/deploy"),
    ("GET", "/internal/deploy/log"),
    ("GET", "/internal/deploy/manual"),
    ("GET", "/internal/deploy/status"),
    ("GET", "/internal/install-playwright"),
    ("POST", "/internal/install-playwright"),
    # POS 设备绑定/PIN(店铺码与 PIN 即凭证 · docs/pos/04 §1b)
    ("POST", "/api/pos/auth/pin"),
    ("POST", "/api/pos/bind"),
    ("GET", "/api/pos/cashiers"),
    # 邀请接受公开页数据(token 即凭证 · 只存哈希单次使用)
    ("GET", "/api/invitations/{token}/preview"),
    ("POST", "/api/invitations/{token}/accept"),
    # 分享链接(token 即凭证)
    ("GET", "/api/sales/documents/shared/{token}/pdf"),
}

# 别名/委托:endpoint 把请求原样转发给已守门的实现(委托点注明)。
DELEGATED_ROUTES = {
    ("GET", "/api/v1/history"),  # → history_routes v0(内部 get_current_user)
    ("GET", "/api/v1/history/{record_id}"),  # 同上
    ("PUT", "/api/v1/history/{record_id}"),  # 同上
    ("DELETE", "/api/v1/history/{record_id}"),  # 同上
    ("GET", "/api/v1/me"),  # → /api/me 实现
    ("GET", "/api/v1/ocr/quota"),  # → app.get_quota(内部鉴权)
    ("POST", "/api/v1/ocr/recognize"),  # → ocr_recognize_routes(内部鉴权)
    ("POST", "/api/v1/ocr/export"),  # → 导出 v0 实现
    ("POST", "/api/v1/rd/lookup"),  # → rd v0 实现
    ("POST", "/api/v1/rd/verify"),  # 同上
    ("POST", "/api/me/link_line"),  # 实现内 _get_user_safe 鉴权
    ("POST", "/api/me/link_line_dev"),  # 同上
    ("GET", "/api/me/plan"),  # 同上
    ("DELETE", "/api/recon/task/{task_id}"),  # → batch_delete_tasks(已 require_perm)
}


def main() -> int:
    quiet = "--quiet" in sys.argv
    rows = collect_routes()
    missing = []
    for r in rows:
        if not r["file"].startswith(("routes/", "app.py", "core/")):
            continue  # fastapi 自带 /docs /openapi.json
        if r["gate"] != "public":
            continue
        for method in r["methods"].split("/"):
            key = (method, r["path"])
            if key not in PUBLIC_ROUTES and key not in DELEGATED_ROUTES:
                missing.append(r)
                break
    if missing:
        print("AUTHZ COVERAGE FAIL — 以下路由无可见守门且不在公开白名单:")
        for r in missing:
            print(f"  {r['methods']:10} {r['path']:55} {r['file']}::{r['endpoint']}")
        print("修法:路由加 require_perm(码),或确属公开则进 PUBLIC_ROUTES(带为何公开注释)。")
        return 1
    if not quiet:
        print(f"authz coverage OK · {len(rows)} routes · 公开白名单 {len(PUBLIC_ROUTES)} 条")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
    os.environ.setdefault("JWT_SECRET", "coverage-dummy-secret-16chars")
    sys.exit(main())
