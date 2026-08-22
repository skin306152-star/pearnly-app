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
    # 同上:各入口 SPA 壳(只 FileResponse 打包好的 html,零业务数据)· 鉴权在各自 boot.js + 后端 API
    ("GET", "/ai"),
    ("GET", "/ai/{rest:path}"),
    ("GET", "/cashier"),
    ("GET", "/cashier/{rest:path}"),
    ("GET", "/dms"),
    ("GET", "/dms/{rest:path}"),
    ("GET", "/daily"),
    ("GET", "/daily/{rest:path}"),
    ("GET", "/daily-sw.js"),  # Daily PWA shell; invitation and tenant checks live in its APIs
    ("GET", "/earn"),
    ("GET", "/cashier-sw.js"),  # PWA Service Worker 脚本(公开静态 · 同 /pos-sw.js)
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
    ("POST", "/api/logout"),  # 退出 = 清会话/吊销 token,无需权限(自身即注销点)
    ("POST", "/api/auth/logout"),  # 同上 · /api/login 同源退出端点
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
    # 浏览器自动上报(无会话 · 只记一条截断日志后返 204 · body 有上限 · 不读写业务数据)
    ("POST", "/api/csp-report"),
    # webhook(签名校验在实现内:LINE signature / GitHub secret)
    ("POST", "/api/line/webhook"),
    ("POST", "/api/line/dms/webhook"),  # DMS channel · line_client.verify_signature 验签即凭证
    ("POST", "/api/line/liff/auth"),  # LIFF id_token 即凭证(LINE verify 验签)
    ("GET", "/api/line/liff/config"),  # 仅返回公开 LIFF ID(非密)· 前端 liff.init 用
    ("GET", "/liff/purchase/{doc_id}"),  # LIFF 页入口·跳 /home 复核屏(前端 LIFF 鉴权)
    ("GET", "/liff/dms-booking"),  # DMS LIFF 页面壳;业务数据仍需 JWT + 一次性 nonce
    ("GET", "/login/dms-booking"),  # 同一 LIFF 页面壳;保持在已登记的 /login 路径下
    ("GET", "/home/dms-booking"),  # 同一 LIFF 页面壳;生产 LIFF 的实际登记路径
    ("GET", "/api/line/dms-booking/config"),  # 公开返回非秘密 DMS LIFF ID
    ("POST", "/api/line/dms-booking/auth"),  # DMS LIFF id_token 经 LINE 验签即凭证
    ("GET", "/line/dms-portal"),  # 60 秒单次 opaque ticket 即凭证;DB 原子核销
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
    # 本月凭证打包下载(C-1)· token=时效签名(tenant+ws+period+落盘 rel+exp)即凭证 · verify_token 验签
    ("GET", "/api/purchase/proof-pdf/{token}"),
    # 泰语图卡出图 · LINE imagemap/图片按 baseUrl/{size} 取图 · ver 破缓存 · 仅固定卡(白名单)· 非敏感
    ("GET", "/api/line/card/{ver}/{card}/{size}"),
    # Express 本地 Agent 出站拉取 · Bearer agent token 即凭证(_auth_agent 验 sha256 · 只取本连接队列)·
    # 全程 ERP_PUSH_ENABLED 保护(off→404)· 客户内网 Agent 无会话,token 自身即鉴权
    ("POST", "/api/erp/agent/heartbeat"),
    ("POST", "/api/erp/agent/lease"),
    ("POST", "/api/erp/agent/ack"),
    # ERP 桥出站三端点 · Bearer brg_ 密钥即凭证(_auth_bridge 比对 sha256 · 只领本桥的 job)·
    # 桥在客户内网无网页会话;book_id 另受"必须在本桥 hello 上报清单内"约束;
    # 急停 ERP_BRIDGE_ENABLED=0 → 全部 404。管理端 /api/erp/bridges 两条走 require_perm。
    ("POST", "/api/erp/bridge/hello"),
    ("POST", "/api/erp/bridge/lease"),
    ("POST", "/api/erp/bridge/ack"),
}

# 已封死:handler 无条件 raise 403,不读写任何数据,也不需要鉴权(留路由壳只为不动 app 注册)。
# 自助模块管理与「入口定功能」冲突后封死(routes/pos_modules_routes.py 顶注 · 零前端消费者)。
# 判据:handler 第一行就 raise,没有任何分支能碰到数据 —— 解封时必须同时加真门。
SEALED_ROUTES = {
    ("GET", "/api/pos/admin/modules"),
    ("PUT", "/api/pos/admin/modules"),
    ("GET", "/api/pos/admin/business-presets"),
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
            if key not in PUBLIC_ROUTES | DELEGATED_ROUTES | SEALED_ROUTES:
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
