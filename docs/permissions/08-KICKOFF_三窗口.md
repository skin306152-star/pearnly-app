# 权限完善 · 三窗口施工 KICKOFF(2026-06-11)

> 依据 = `07-完善方案_五阶段.md`(G1-G4)+ 桌面原型 `Pearnly_权限完善_UI预览/01-交互原型.html`(Zihao 拍板后开工)。
> 文件归属按下表切死,谁越界谁回滚。与在跑的银行对账两窗口零文件交集。

## 文件归属(防撞表)

| 窗口 | 独占文件 | 禁碰 |
|---|---|---|
| 权限① 后端·席位+日志 | routes/console_invite_routes.py · routes/console_team_routes.py · services/team/** · 各自 tests | services/authz/** · static/** |
| 权限② 后端·角色+遮蔽 | **新建** routes/console_roles_routes.py · services/authz/**(registry/seed)· services/{purchase,inventory,pos} 读路径序列化层 · 各自 tests | routes/console_team_routes.py · routes/console_invite_routes.py · static/** |
| 权限③ 前端·console | static/console/**(console.js/console-i18n.js)· 成本列显 -- 的 src/home 与 static/pos 报表文件 | 一切 .py |

⚠️ 两个共享点:① app.py 各窗口可能各加一行 include_router → commit 前 `git pull --rebase`;② STATE 状态卡收尾必先 pull 再写。
⚠️ 权限③ 开工前提 = **前端窗口(丝滑+打包收编)已收尾 push**(它独占 static/console+src/home+build),且权限①②的 API 已上线。

## 窗口① 任务(后端 · G1+G2)

1. **席位 enforce**:create_invitation 入口 count(active memberships)+count(pending invitations) ≥ plan.seats_max → 422 `team.seat_limit`;撤回/移除后可再邀;cashier 不计席。配单测+真库 E2E(满→422→撤回→可邀)。
2. **安全日志**:`GET /api/team/security-events` 加 `?type=&actor=&from=&to=` + 游标分页;新增 `GET /api/team/security-events/export`(CSV·UTF-8 BOM·与筛选参数一致·上限 5000 行);新事件 role.create/update/delete 落 operation_logs 的 action 类型先注册(②会用)。
3. 守门:authz 闸/全量单测/每新文件带测试;只 add 自己 pathspec。

## 窗口② 任务(后端 · G3+G4)

1. **第一步先写守门测试**:`_seed_roles` 只刷 `tenant_id IS NULL` 预设行,custom 角色重启不被覆盖(07 §四的唯一风险点,测试先行钉死)。
2. **自定义角色**:新 `routes/console_roles_routes.py`(GET/POST/PATCH/DELETE /api/team/roles·owner/admin)·roles 表插 `(tenant_id, key='custom:<slug>', permissions=[勾选码])`·resolver 零改动·DELETE 前查 memberships 引用计数(在用→422 人话)·role.create/update/delete 落审计。
3. **敏感字段遮蔽**:registry 加 `field.cost.view`/`field.payroll.view`(62→64·预设角色按现状含 cost·矩阵单测随更);进项/库存/POS 报表序列化层按码过滤成本列(无码→null);导出同样遮蔽。
4. 真库 E2E:建角色→分配→矩阵即时生效→删被拦→重启 seed 不覆盖→无 cost 码成员 API 拿不到成本明文。

## 窗口③ 任务(前端 · 等①②上线+前端窗口收尾)

照桌面原型 100% 照搬行为(三 tab/三步向导/日志筛选分页导出/席位满提示/在用角色删除拦),工程形态走 console 既有 can()/api 协议+console-i18n 四语(原型标准化中文为底稿);成本列在主程序进项/库存/POS 报表按 `field.cost.view` 显 --;真浏览器 E2E+浅暗截图;改 console 静态文件 bump ?v=。

## 完工判定

07 §五验收清单 V1-V8 全勾(每窗口勾自己的部分,③ 收口全量);每小阶段五角色 agent 审查;push 即上线纪律照旧。
