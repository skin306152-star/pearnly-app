# POS 项目 · 09 施工规约(进场必读 · 销项血泪 → 硬清单)

> 施工队(任何窗口/AI)进场前必读。每条都对应一类销项踩过的坑或主项目铁律。**违反任一 = 返工**。提交前逐条自检。

## A. 前后端对接(治"死按钮/字段读错/裸错误码")
1. **响应只认信封**:成功 `body.ok===true` 读 `body.data`,失败读 `body.error.code`。**绝不靠 HTTP 码判业务成败**,绝不裸读顶层字段(销项 RD 接口读 `body.data.*` 嵌套坑)。见 04 §0.1。
2. **按钮 enabled 条件照 05 矩阵**;**边界/守卫检查别排在动作分支前面**(销项第5步"开出"死按钮根因 = go() 边界检查排在 doIssue 前,永不可达)。先判能不能点,再绑动作,确保动作可达。
3. **错误码必本地化 + 统一兜底(治"失败弹裸码/英文/HTTP")**:照搬销项 `salesErrMsg` 范式(`src/home/sales-common.ts:124-137`)。
   - 写 `posErrText(code)`:`body.error.code`(`pos.xxx`)→ 当前语言文案(查 06 字典);**查不到返 null**,绝不抛原始码。
   - 写 `posErrMsg(code, fallbackKey)`:查不到就回退一句**本地化兜底**(如 `t('pos.unexpected')`),保证用户永远看到人话。
   - **所有 确认/完成/删除/创建/保存/收款 失败统一走 `posErrMsg`** → `showToast(posErrMsg(body.error?.code, 'pos.unexpected'), 'error')`。
   - **禁止** `showToast(err)` / 直接拼 `detail` / `HTTP ${status}` / 英文原文给用户。
   - 后端**只返 code**(不返英文消息给前端展示);新增 code 必同步进 06 + i18n,否则 `check_i18n` 红。
   - catch 网络异常也走兜底文案(`t('pos.unexpected')` 或离线态 `pos.offline_saved`),不暴露异常栈。
4. **取鉴权资源带 Bearer**:图片/PDF/二维码等也要带 `Authorization`(销项 `<img>` 401 坑 → 用 fetch→blob)。
5. **每个按钮真接通**:施工后照 05 逐个 E2E 点,接口 404/占位 = 死按钮 = 未完成。不留"假功能"(销项模板编辑假功能坑)。

## B. 四态与边界(治"白屏/500/转圈不停")
6. **四态全做**(07):每个 fetch 必 try/catch → 出错态;空/加载/出错都要有 UI,不许整屏崩。
7. **边界返码而非 500**:坏输入/坏文件返 4xx + 友好码(销项坏图 500→422 坑)。后端 except 兜住,前端友好提示。

## C. 数据/钱/时间/隔离
8. **钱 Decimal**(`numeric(14,2)`),**数量 `numeric(14,3)`**(拆零/称重),**绝不 float**。
9. **时间 UTC 存**、本地显示;日期用 date(效期/账期)。
10. **多租户 + 账套隔离**:每表 `tenant_id`+`workspace_client_id`,**RLS policy 必加**(POS 涉钱,后端硬隔离,不只前端藏)。
11. **幂等**:可离线写带 `client_uuid` UNIQUE,服务端去重(防补传双扣)。
12. **库存只追加流水**:`inventory_transactions` immutable + 同事务 upsert `inventory_stock`;改库存=记冲销,不改历史。
13. **FEFO**:批次品按 `expiry_date ASC` 扣;近效期预警。

## D. Schema / 部署
14. **schema 走 Alembic**(0021+)+ 配 `ensure_*` + `services/startup.py` 注册(prod 无自动迁移,双跑模型)。
15. **prod 迁移走 ssh+pearnly+psql**(经授权,见销项 prod 运维通道记忆);加表同步 RLS policy。
16. **改前端 bump `?v=`**(/pos 资源 immutable 缓存,不 bump 用户拿不到改动)。

## E. 工程标准(主项目铁律)
17. **单文件 <500 行**;新模块独立:`services/pos/*`、`services/inventory/*`、`routes/pos_*.py`、`routes/inventory_*.py`;前端 /pos 独立 SPA(plain script 或独立入口)+ 主程序库存模块走 `src/home/*`(不进 home.js)。
18. **每个新文件 ≥1 测试**(契约/集成);契约测试断言信封 + 幂等 + 鉴权 + RLS(04 §9)。
19. **去 AI 味**:无废话注释/无 emoji 注释/无 console.log 残留/无泛化命名;注释解释 why。`check_ai_smell` pre-push 第7道会拦。
20. **4 语 i18n 齐**(th/en/zh/ja),`check_i18n --strict` 闸;新 key 各语言块按 th→en→zh→ja。
21. **commit** 守门 6 道全绿 + 署名 Opus 4.8;整顿期 commit 带 task id(POS 为破例新功能,注明 `POS-<PO号>` + RATCHET-EXEMPT 新文件)。

## F. /pos PWA 专属(离线特有)
22. **service worker 版本化**:更新外壳要能让旧缓存失效(版本号),不卡用户在旧版;但**不得清空 outbox**(未传单)。
23. **IndexedDB schema 版本化**:结构升级走 onupgradeneeded,不丢 outbox。
24. **outbox 持久 + 启动恢复**:绝不放内存;崩溃/重开后自动续传。
25. **本地 totals 与服务端 `totals.py` 等价测试**(防金额分歧,见 08 ADR-4)。

## H. 视觉照搬(治"照着画却画不出概念稿" · 最易翻车)
> 销项坑:施工窗口把概念稿当"参考"凭印象重画 → 上线的不是拍板那张。**概念稿 = 唯一视觉真理(ground truth,同铁律#8"真样本是唯一真理"),照搬不重画。**
27. **逐字搬 DOM + CSS,不"用现有组件重做"**:打开 `桌面/Pearnly_POS_UI预览/<对应屏>.html` 源码,把它的 HTML 结构 + `<style>` 直接移植进生产代码(/pos 的 css、`home-NN-pos.css`),**不要**改用看起来差不多的现有类。
28. **CSS 令牌整块移植**:概念稿 `:root` 里的色值/字号/间距/圆角/阴影**原样搬**进 POS 专属样式表,数值一个不改(主蓝 `#2563EB`、圆角、`tabular-nums`、卡片阴影等)。POS 用自己的样式表,不污染也不被现有 home.css 覆盖。
29. **只准改三处**:① 假数据 → 接口绑定(04)② 写死文案 → i18n key(06/4语)③ 补四态(07)。**视觉(布局/颜色/间距/字号/圆角/阴影)一个像素不动。**
30. **禁止"理解后重画"**:不凭记忆 paraphrase 概念稿;任何细节有疑问回看预览文件源码,以它为准。
31. **像素级验收**:真浏览器截图 vs 概念稿截图**侧拼比对** + `getComputedStyle` 断言关键令牌(主色/圆角/字号/间距/阴影)与概念稿一致;**不一致 = 未完成,回去对齐**(不是"差不多就行")。

## G. 高敏(本项目已授权免在场,但仍负责)
26. POS 高敏块(cashier 鉴权/登录分流)**按图+PO 施工,不卡 Zihao 在场**(2026-06-07 授权);**仍以真账号 E2E 为闸**;改到所有人共用的现有登录流程,push 前自验老板/会计/超管登录不破。

## 提交前自检(逐条打勾)
`[ ]信封 [ ]按钮可达+真通 [ ]错误码本地化 [ ]鉴权资源带token [ ]四态 [ ]边界返码 [ ]Decimal/UTC [ ]RLS [ ]幂等 [ ]流水immutable [ ]Alembic+ensure+startup [ ]bump?v= [ ]<500+独立模块 [ ]每文件测试 [ ]去AI味 [ ]4语 [ ]守门6道 [ ]视觉照搬概念稿(令牌逐字搬+像素比对) [ ](PWA)SW/IDB版本+outbox持久+totals等价 [ ]E2E真账号过`
