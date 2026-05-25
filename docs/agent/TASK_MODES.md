# TASK_MODES.md · 任务模式识别与执行

> Zihao 常只说「继续」或一句话。先**识别模式**再动手。每个模式有固定步骤、工具、产出、禁忌。
> 配合 `AGENTS.md`(命令)+ `ACCEPTANCE_PLAYBOOKS.md`(验收剧本)使用。

## 如何识别(关键词 → 模式)

| Zihao 说 | 模式 |
|---|---|
| 「测一下 / 跑验收 / 这个能用吗 / Codex 报告」 | **测试项目 / UI 验收** |
| 「继续 / 接着重整 / 拆文件 / 抽 router」 | **重整长跑** |
| 「报错 / 500 / 推不动 / 失败 / 用户说不行」 | **线上排障** |
| 「方案 / 怎么设计 / 调研 / 对比 / 这套对吗」 | **产品方案** |
| 给真实账号/token + 「触发一次 / 验一下」 | **UI 验收(真账号)** |

不确定就问一句确认,别默认改代码。

---

## 模式 1 · 测试项目

**目标**:按固定剧本验收一个模块,输出通过/失败清单,不"看起来可以"。

步骤:
1. 定位模块对应剧本(`ACCEPTANCE_PLAYBOOKS.md`)。
2. 跑剧本里的命令(单测 / 集成 / 真账号 API)。
3. 逐项记录:输入 → 实际输出 → 预期 → PASS/FAIL。
4. 失败项给真实证据(日志/响应体/栈),不猜。

禁忌:把 sync mock 当 async 证据(铁律 #13);只跑单测就声称"async 路由通"。

---

## 模式 2 · 重整长跑

**目标**:小步拆巨石(app.py/home.js/db.py),0 业务逻辑改,每步可回退。

步骤:
1. 选**边界清晰**的一片(一个 router / 一个 cohesive 域 / 一个 IIFE)。纠缠太深(load-order 装饰器/裸名调)就跳过。
2. 整片搬到独立文件(`*_routes.py` / `src/home/*` / `services/<domain>/*.py`)· 用 re-export 让调用点零改动。
3. **每片带契约测试**(函数在新位置 + re-export 同一对象防漂移)。
4. 5 道守门全绿(black/ruff/imports/i18n/unit)→ 本地 commit(message 含 `REFACTOR-<id>`)。
5. **抽前必 re-grep 当前行号**(每次删除后行号下移)。

禁忌:不留半拆;不在预算偏紧时硬开核心耦合区;不碰 auth/OCR 热路径/计费除非 Zihao 在场。

---

## 模式 3 · 线上排障

**铁律:先复现 + 查日志,不先改代码(铁律 #25)。**

步骤:
1. **磁盘**:`ssh root@45.76.53.194 "df -h /"`(>85% 是头号嫌疑·铁律 #24:满盘→Nginx 500→前端 `Unexpected token '<'`)。
2. **抓真栈**:`journalctl -u mrpilot --since '...' | grep -iE 'ERR_|Traceback|<关键词>'`。不猜根因。
3. **分类**(见 `ERROR_CODES_AND_STATES.md`):用户数据错 / 业务拒绝 / 技术错 / 环境错。
4. **复现**:能本地用真 adapter + sandbox(test01)复现就复现(铁律 #25 "用测试证根因")。
5. 定位后**修一类不修一处**(铁律 #1:grep 同类 pattern 一次修全)。
6. 修后**在重启后的新进程**上复测(`systemctl show mrpilot -p ActiveEnterTimestamp` ≥ push 时间)。
7. 真 bug 必补守门测试。

实战要点:500≠504(不是超时);uvicorn 日志查不到该 POST = 卡在 Nginx 没到应用;`--workers 2` 下进程内锁无效(要 pg advisory / DB lease)。

禁忌:报"上传 500"先怀疑代码——先查磁盘;凭直觉盲调字节级格式——拿真样本对照(铁律 #8)。

---

## 模式 4 · 产品方案

**目标**:先梳业务流 + 找冲突,再给可执行文案。不上来写代码。

步骤:
1. 读现状代码(只读)搞清真实数据模型——**别信文档措辞,信代码**(本项目踩过:`clients` 表注释写"客户公司",实际被当买方用)。
2. 找**内部冲突**:用户的两条要求是否在现数据结构下互斥?(踩过:"所有上传归属登录客户" + "按真实买方推 ERP" 在共用 client_id 下冲突)。
3. 涉及账务/钱/权限/登录 → 先用 `AskUserQuestion` 把岔路问清,**选错会污染生产数据**。
4. 复用现有模块(列出来),不重造(本项目重试队列/去重/preflight/切换器多已存在)。
5. 输出:最小改动方案 + 涉及文件 + 验收标准 + 红线 + 分相上线顺序。写设计文档,不改业务代码。

禁忌:从零设计而不看现有代码;把"看起来缺的"当真缺(先 grep)。

---

## 模式 5 · UI 验收(真账号)

**目标**:用真账号/token 走真 UI/API 路径,产出可独立复核的证据(给 Codex/Zihao)。

步骤(以 MR.ERP 推送为例,实测命令见 `ACCEPTANCE_PLAYBOOKS.md`):
1. 真 token「用完即弃」(`POST /api/login`),不提交、不打印全文。
2. 走真 API(与 UI 同路径):`/api/erp/push` 等。
3. 抓全验收字段:账号/tenant、history_id、endpoint_id、log_id、匹配 or 自动建、status、error_msg/response_body、bill_no。
4. **状态以唯一来源为准**:推送看 `erp_push_logs`(`/api/erp/logs/{id}` 的 response_body 里有 `mrerp_bill_no`)。
5. 老 PHP 系统:返码 ≠ 真写库(铁律 #9)→ 最终以 ERP 报表/listing 为准(这步常交给 Codex 独立核)。

禁忌:往**付费用户真账套**推测试数据(污染真账)——只用 sandbox(TEST2019/test01)endpoint;测试账号 endpoint 用完恢复 `enabled=false`,别长期开自动推送。
