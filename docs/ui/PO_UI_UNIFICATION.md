# PO · 全站 UI 标准化大整顿(给施工窗口)

> 一句话:**把已封板的设计"实物源"移植进生产代码,不是重新设计。** 偏离由机器闸拦,不靠自觉。
> 读这两份再动手:`docs/ui/DESIGN_SYSTEM.md`(标准)+ 本页(施工)。风格 = B(Emerald),已定,不再讨论。

## 🚫 铁律(防跑偏 · 违一条 = 返工)
1. **照搬,不设计**:组件/令牌/间距/圆角/色值,**逐字抄** `scripts/_mock/kit-final.html` + `dashboard-final.html` + `templates.html`。**不准自创组件、不准换色、不准改间距、不准"优化"成更好看的版本。**
2. **不重定义**:令牌值只来自实物源 `:root`。看到现有屏裸写 hex → 换成令牌,**不许发明新值**。
3. **不直接画 UI**:每屏先查 DESIGN_SYSTEM 第 4 节的"屏→模板映射",对号入座套模板骨架,再填 kit 组件。
4. **每屏过保真闸**:改完跑 `tests/visual/test_design_fidelity.spec.js`(生产页 vs 实物源快照,getComputedStyle 逐项),红 = 没搬对,改到绿。再跑真浏览器审计 `tests/e2e/_ui_audit.spec.js` 复看。
5. 守现有约束:改 `src/home/*.ts` 必 `npm run build` + `git add static/dist` + bump 两个 `?v=`;`home.html/css` 是 CRLF 禁 prettier 整文件;守门 6 道 + lint-ui 全绿;新文件 RATCHET-EXEMPT;push 即上线,未验收不推 master。

## 阶段(按序)
**PO-1 · 地基(令牌 + 组件 kit)**
- 把实物源 `:root` 两套令牌(浅 + 暗夜)落成全站 CSS 变量;补完剩余 ~2624 处裸 hex → 令牌(集中在 knowledge/bank-recon-v2/dms 等 ~20 文件)。
- 把 kit-final 的组件落成一套复用 CSS(唯一 `.btn/.fin/.sel/.ms/.bdg/.modal/.toast/.bnr/.sk/...`)+ 必要 TS 渲染助手。图标接 Lucide。
- 加暗夜开关(`.dark` 切 `:root`,记住偏好)。
- 验:kit 页生产渲染 vs `kit-final.html` 保真闸绿(浅+暗)。

**PO-2 · 页面模板组件化**
- 把 6 模板(概览/列表/详情/录入/设置/向导)做成共享骨架组件(对齐 `templates.html`)。
- 验:模板渲染 vs `templates.html` 快照绿。

**PO-3 · 逐屏迁移(套模板 + 接 kit)**
- 顺序:① **dashboard**(样板·照搬 `dashboard-final.html`)→ ② 旧屏批量:销项工作台/历史/对账/POS/知识库/异常等(按映射表对号)→ ③ 进项系列(已接近,主要换令牌/补暗夜)。
- 每屏:套对应模板骨架 → 填 kit 组件 → 令牌化 → 保真闸 + 审计 harness → 真账号双端真浏览器看 0 console error → 才算完。
- 顺手清审计发现的真 bug:dashboard 时间 i18n 原始键、对账"OCR 抽不准"自曝文案 + "3格/4格"、知识库双框、库存 spinner 空态、原生 select。

**全局修正项(每屏都要带上)**
1. **左上角 logo + 用户名 → logo + 「Pearnly」**:去掉用户名渲染,顶角固定品牌名;用户名挪进右上角头像菜单。
2. **流式自适应修复**:删掉各屏小固定 max-width(进项待归类 760 / 供应商 920 等),统一内容区流式居中填满(对标 history 屏);确保 50–200% 缩放都贴满不留死白、不跑偏。
3. **日期/历法收口(前端 · 见 DESIGN_SYSTEM §6)**:OCR 入口归一**已修 ✓**。剩前端:建一个共享 `formatDate()`(读历法偏好,默认佛历 พ.ศ.),显示/表格/CSV/PDF 全改走它;加全局历法开关(佛历/公历)接通。内部永远存公历。归 Window A(共享层)。

## 屏 → 模板映射(对号入座 · 不判断)
- ① 概览:dashboard · 销售报表
- ② 列表:进项主屏 · 待归类 · 供应商 · 销项工作台 · 商品 · 客户 · 应收 · 历史 · 库存 · 异常 · 知识库 ·(OCR 上传=列表变体含上传头)
- ③ 详情:单据详情
- ④ 录入:进项录入 · 开票录入 · 对账(双上传分屏)
- ⑤ 设置:采购设置 · 开票设置 · 账套资料 · 集成 · 收银设置 · 账户设置(弹窗)
- ⑥ 向导:开票向导 · POS 开通

## 验收(每屏 + 整体)
- 保真闸绿(浅 + 暗)· 审计 harness 截图对得上目标 · 真账号双端 0 console error · 守门全绿。
- **每屏在 67% / 100% / 150% 浏览器缩放各看一遍:都贴满自适应,无大片右侧死白、不跑偏。**
- 左上角显示「logo + Pearnly」,无用户名。
- 整体:全站任意两屏并排看,组件/间距/色一致;暗夜一键翻无残留浅色;新加一个测试屏走决策树能落位。

## 并行作业(双窗口加速 · 防冲突设计)

前端是单一 bundle(`src/home/*` → `static/dist/main.js`),所以**不能从 0 同时开两窗**:基座是共享地基,必须**先由一个窗口做完并推上线**,另一窗口才能在其上并行迁屏。

**Window A(基座 + 共享层 + A 组屏)= 集成方,独占所有共享文件**
- 先做 PO-1 + PO-2(令牌浅/暗、组件 CSS kit、6 模板骨架、shell:logo+Pearnly/侧栏/顶栏/暗夜开关、formatDate+历法开关、补裸 hex)→ **push 上线(这是 B 的前置)**。
- 再做 A 组屏:dashboard · 上传识别 · 识别记录(history)· 对账中心 · 销售发票/工作台 · 应收 · 客户 · 销售报表。
- **独占共享文件**:组件 kit CSS、`app-shell-html`、`sidebar-nav`、`topbar/avatar`、`core-boot`、`module-nav`、`i18n-data`、`static/dist`、`formatDate`。

**Window B(B 组屏)= 只迁自己那几个 screen 文件**
- **等 A 推完基座后 `git pull --rebase` 再开工。**
- 做 B 组屏:进项主屏 · 待归类 · 供应商 · 采购设置 · 库存 · POS 各屏 · 知识库 · 异常。
- **绝不碰任何共享文件**;需新 i18n 键 → 让 A 加,或先用现有键。

**防撞铁律(两窗都遵守)**
1. 只 `git add <自己文件路径>`,**禁 `git add -A`**(共享树老坑)。
2. 共享文件**只 A 改**;B 改了 = 违规。
3. `static/dist` **只 A 提交**;B 只改 `src/home/*.ts`,由 A 统一 rebuild+提交 dist(或 B push 前 `pull --rebase` + 重 build)。push 串行,不同时推。
4. 各自挂保真闸 + 审计 harness;A 推基座后 B 必 pull。
5. 屏文件不重叠(见上分组)→ 天然无 .ts 冲突;唯一共享点是 dist/i18n,按上面规则归 A。

> 净效果:基座阶段串行(A 单干,半天),迁屏阶段双窗并行(~20 屏对半分)。提速主要在迁屏期,约 1.5×,不是 2×(基座是瓶颈)。

## 不在本 PO(单独排)
角色权限模型(合伙人需求·后端大活)· Onboarding/帮助/通知中心 · 无障碍深做 · 着陆页。
