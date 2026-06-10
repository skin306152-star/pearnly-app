# 全站设计评审结论 + 修复总清单 · 2026-06-10

> 来源:35 面真浏览器截图(25 屏浅色 + 24 暗夜 + 4 弹窗)× 8 个独立评审 agent 对照 DESIGN_SYSTEM 逐屏挑刺。
> 总诊断:**绝大多数屏只完成了"浅色 happy path"的视觉皮**。暗夜换肤、空态组件、按钮主次、图标 Lucide 化、文案去 AI/去自曝五件系统性的事全站半成品。
> 本文档 = 唯一修复清单。修完一项打勾 + 写 commit。配合 `UI_MIGRATION_STATUS.md`(grep 实证 punch list)、`UI_SURFACE_INVENTORY.md`(80+ 面逐项验收)。

## 一、系统性大刀(一处修全站好 · 按杠杆排序)

### S1 · 蓝绿双主色收口(根因级)✅ 已修完 · commit `74a56a5a` · 2026-06-10 已上线 prod
- [x] `static/home-01-base.css` 浅色 `:root`:`--blue:#2563EB→#0E7C66`、`--blue-weak:#EAF1FE→#E4F4F0`、`--blue-50..800` 全换 emerald 阶。
- [x] 暗夜 `:root.dark`:`--blue:#5B8DEF→#2DD4A7`、`--blue-weak:#16223A→#11261F`。
- [x] 复核 `home-45-kit.css:482`(引 --blue 的 banner)翻绿后语义 OK(info banner = 品牌淡绿,与 amber/red 区分清晰;实物源 kit-final.html :root 已同步收口)。
- [x] 残留裸蓝清零(主 app):rules 弹窗、module-settings、onboarding-business、pos-cashiers/sales-account/向导色盘默认色、erp-exc chip、cust-row-btn.primary、bank-filter、accent-color ×6、`rgba(37,99,235,α)` 焦点圈 11 处、头像渐变 indigo-500 漏迁 → 全走 var(--blue)/var(--accent-deep)。integrations tab/ws-modal 本就走令牌,随翻自动变(真浏览器复核 ✓)。
- 效果:238 处 --blue 引用 + badge/hint 一次性翻绿;lint 主 app 旧蓝 0 残留(剩 POS/admin 独立 SPA,本轮范围外);dist 与 prod 字节级 0 残留。
- 验:保真闸 PASS · lint-ui/tsc/prettier 绿 · 真浏览器浅+暗截图(dashboard/exceptions/integrations/rules/settings · `scripts/_s1_shot.cjs` 可复用)。

### S2 · 暗夜内层未换肤(阻断级)✅ 已修完 · commit `9efd4fed` · 2026-06-10 已上线 prod
- [x] **reconcile 历史表阻断**:vex-task/glv-history 表 td `--gray-900` 深字压深底 → `var(--ink)`;白表头/白空态卡随翻。
- [x] 内层白底残留:OCR/automation dropzone、history 斑马纹/hover、sales-account、receivables/vouchers 占位卡、exceptions 白 pill 下拉、knowledge tab(+顺手修 page-title `--ink-1` 未定义 fallback 暗夜不可见)。
- [x] disabled 按钮 / pill / toggle 轨道暗夜映射(home-38 全局:secondary/ghost/icon/disabled/toggle 全换语义令牌;primary 对齐 kit `--btn-blue`+`--accent-ink`,暗夜 = mint+深字与 A 组屏一致)。
- [→] 暗夜主按钮"荧光薄荷绿降饱和" = 要改封板令牌值(kit-final 暗夜 accent 就是 #2DD4A7),**Zihao-gated 未动**;现按封板值统一。
- 修法(已执行,16 个 CSS 包):`--gray-*/--slate-*/--c-fafaf8/background:#fff` 等不翻面值 → `var(--bg/--card/--line*/--ink*)` 语义令牌,浅色近字节等、暗夜随 `:root.dark` 翻。**剩余未扫文件(home-02/04/05/10/12/13/15/17/18/20/22/23/24/26/27/28/33/34/36/40)还有 ~70 处 `background:#fff`,补抓再评时一并清。**
- 验:真浏览器 11 屏×浅+暗截图复核(`scripts/_s1_shot.cjs`)· 保真闸 PASS · lint-ui D1/D2 绿 · prod 字节验证。

### S3 · 空态统一组件 ✅ 已修完 · commit `179123b9` · 2026-06-10 已上线 prod
- [x] kit 标准空态全局版 `.pn-empty`(home-45-kit.css·.ui .empty 镜像 + `.fill` 铺满垂直居中)。**新屏空态一律用它。**
- [x] "先选账套"四处统一:`window.wsEmptyHtml(btnId)`(workspace-switcher)· canonical 键 `ws-empty-title/sub/pick` 四语 · 术语统一 กิจการ(39:5 胜出)/ ja 帳簿。旧四套键停用未删(inv-need-workspace 弹窗仍引用)。
- [x] sales-products 文案错配 → 独立键 `sx-products-empty`(ยังไม่มีสินค้า)。
- [x] vouchers/receivables/cloud 删营销 checklist;v104/v107/v108 → cs-coming-soon(S5 两项顺带清)。
- 注:~16 屏各自写的旧空态没全收(只收了点名四处+占位页);逐屏迁 .pn-empty 并入"逐屏精修"阶段。

### S3-bis · 暗夜表单控件全局收口 ✅ 同 commit(Zihao 实测采购设置数字隐身)
- [x] 根因 = input/select/textarea 不继承 body 色(UA 默认黑字)→ 暗夜深字压深底。home-01-base 全局 `input,select,textarea{color:var(--ink)}` + placeholder ink3,一条规则治全站。
- [x] 显式硬编码漏网清零:line-email-modal/automation 模式条/向导灰勾。

### S4 · emoji/字符当图标 → Lucide ✅ 已修完 · commit `a49ad27f` · 2026-06-10 已上线 prod
> 实况:评审点名的 ⚖⭐🔔🍴✦ 已随 A/B 组屏迁移消失。本轮清掉真实残留:对账 KPI ⏱/✓/!/⚠、OCR 警示 ⚠/◌、「可开启功能」→ 箭头、✨ 学习提示前缀。剩余 lint 命中 = i18n 文字强调(评审标注可不动 · 💡📦💳🔴 类前缀归 S5 文案收口)/ test-center 内部页 / POS·admin 独立 SPA / **着陆页(Zihao 2026-06-10 拍板:不动 · 图标不要线性)**。
- ⚖️⚠️(dashboard 快捷卡)· ✨✦(侧栏 เปิดใช้งานระบบขาย)· →文本箭头 · ✓勾(vouchers/receivables)· ⭐(suppliers banner)· $字符(receivables)· 🔔(rules)· 🗑✎ · x字符(sales-account logo 删除)· 弧线断图字形(inventory 空态/pos-onboarding งานบริการ)· pos-onboarding 🍴/卡车。
- 修法:kit-final 的 Lucide 注入器,stroke2/currentColor/16-24px。

### S5 · 文案收口(露技术/自曝/版本号)✅ 已修完 · commit `de5a88a` · 2026-06-10
- [x] vouchers 副标题露「OCR」「AI แนะนำ」→ หลังสแกน/ระบบแนะนำ(cs-vouchers-desc/f1 四语)。
- [x] reconcile「OCR อ่านไม่แม่น? กรอกยอด 3 ช่องเอง」→「手动校正 3 个余额(可选 · 留空自动识别)」四语;同屏 brv2-anchor-prefill/audit 系键一并去 OCR。
- [x] automation dropzone 去 OCR(drop-hint 四语)。
- [x] exceptions 红 pill ความมั่นใจต่ำ →「ต้องตรวจสอบ/识别待确认」;history 统计带 ความมั่นใจสูง →「อ่านแม่นยำ/识别准确率」。
- [x] knowledge 副标题去 AI(kb-sub 四语)。
- [x] 版本号外泄 v104/v107/v108 → cs-coming-soon(S3 顺带已清)。
- [x] 细节:แตะ→คลิก(pur-inbox-sub 三语)· 中点「·」贴字 40 处机械补空格 · placeholder 裸斜杠扫描无真违规(命中均为泰语自然复合词)。

### S6 · 侧栏两主题不一致(module-nav 一处修)✅ 已修完 · commit `039a017` · 2026-06-10
- [x] 「即将上线」chip 内联 `#f3f4f6/#6b7280` 固定浅色暗夜白底压字 → 删内联走 `.nav-badge` 语义令牌 + `white-space:nowrap` 防两行换行挤压底部。**「暗夜多出一项」查实为抓图时模块状态不同 —— 导航渲染与主题无关,两主题同一棵树,非 bug。** 文案截断省略号 = `.nav-label` 标准 ellipsis,保留。
- [x] 侧栏激活态统一 ✅ commit `f72a10a5`:Claude 式导航重排(Zihao 2026-06-10 拍板·稿 `scripts/_mock/nav-claude.html`)— 激活态全站一套淡绿 pill(accent-weak+ink+accent 图标);同 commit:logo 进侧栏/分区小字标题/三级拍平/统一缩进网格/底部 pinned 用户卡/窄 rail Claude 化。settings 弹窗 tab 激活态若仍灰蓝,补抓时复核。

### S7 · 悬空飘卡 / 不铺满(~10 屏)✅ 已修完 · commit `039a017` · 2026-06-10
- [x] 占位卡铺满内容区垂直居中:`.coming-soon` + `.auto-coming-hero` 全局加 min-height+flex 居中(7 个占位页一处治)。
- [x] dashboard「+ 充值」悬空根因 = 余额卡 display:none 由 owner/加载态控制而按钮恒显 → 按钮与余额卡同生死(非主题差异)。
- [x] sales-account 预览卡 sticky 已存在(home-39:572)复核 OK;保存按钮 → 容器内右对齐;顺带修模板预览 `#111827` 固定深字暗夜隐身 → var(--ink)。

### S8 · KPI 卡墙 + 裸「—」✅ 已修完 · commit `039a017` · 2026-06-10
- [x] dashboard/reconcile/exceptions KPI 骨架裸「—」→「0」(计数语义下 0 诚实);exceptions 4 KPI 卡收成一条信息带(单卡四格分隔线 · 数字 26→20px 降与 tab 徽章的重复存在感)。
- [x] ฿ 与数字重叠 → ฿ 后垫 U+2009 窄空格(kit .bandtop .n 本就 tabular-nums);reconcile KPI ✓/△/! 字形图标 → Lucide svg + 第二卡内联 #f3f4f6 翻面(S4/S2 漏网顺带)。

### S9 · 按钮 4-bis retrofit ✅ 已修完 · commit `af8b2f95` · 2026-06-10(1 项 deferred)
> 通用件:`.more-wrap/.more-menu`(home-04 · 自含样式不依赖 .ui 作用域 · capture 相位点外关 · id 不变保既有绑定)。
- [x] ocr 一排 4 按钮 → 开始识别(主)+ 导出 split(次)+ ⋯(清空/自定义模板);自定义模板降菜单项。
- [x] sales-report 时间段 4 独立按钮 → segmented(.posrep .seg 单框分段);选中态 var(--card)→var(--accent-ink) 暗夜可读。
- [x] clients 账套主体行内 3 按钮 → 设为当前 + 编辑 + ⋯(归档红 · 二次确认已有 archiveWsClient)。
- [x] reconcile 对账记录行尾 3 裸图标 → 载入+导出 + ⋯(删除红 · _deleteTask 已有 showConfirm)。
- [x] rules 弹窗行尾 toggle+✎+🗑 → toggle 留行上,编辑/删除收 ⋯(rules 本地词典补 edit/del 四语;rsDelete 已有确认)。
- [x] purchase 三入口 → 拍票唯一主实心 + ⋯ 下拉(手动/LINE)。
- [→] **integrations 按连接态分化 = deferred**:集成页零状态接口,分化需 6 个后端状态聚合(google/gmail/line/folder/erp/notify),超 UI 刀范围;「清一色实心」视觉问题不存在(.int-btn-configure 本就幽灵描边)。后续做聚合 status 端点时一并。
- [x] pos-tables「+เพิ่มโซน」→ 主实心(顺带 .primary/.zone.on #fff → 令牌翻面);pos-cashiers 未选账套「加收银员」禁用(:disabled 样式)。

## 二、最差屏(逐屏精修顺序)
1. **reconcile** — 暗夜表阻断 + 空态裸— + 自曝文案 + 裸图标删除 + 占位图标
2. **automation/上传页** — 几乎集齐所有系统性问题
3. **sales-account** — 蓝绿同屏 + 预览不 sticky + 测试数据串入 + 保存悬底 + 模板暗夜白块
4. **vouchers** — AI/OCR/v104 + 营销页 + 巨白卡悬空
5. **receivables** — v107 + 卖点 checklist + 居中死白
6. **dashboard** — 两主题布局不一致 + 裸— + emoji + ฿重叠
7. **POS 三屏空态** — 三处三个样 + 术语混用 + 荧光绿

### S2-bis · 全局收尾 ✅ commit `a1d58008` · 2026-06-10(Zihao 实测两处 + 点名"全局排查不要点修")
- [x] 侧栏激活项 ink 底死 #fff 字暗夜不可读 → var(--card);暗夜品牌图(紫P猫)垫白色圆角底板(不改资产·改图=品牌级 Zihao 拍)。
- [x] 全站清零:全部 home-*.css + 15 个 TS 注入样式的 --gray/--slate/--c-*/#fff/#111 系不翻面固定色 → 语义令牌;rules/设置弹窗暗夜从白块变完整换肤;反色组件 8 处文字 → var(--card);图片预览遮罩固定深底。
- [x] **推送日志 tab 布局怪** ✅ commit `efadbaa`:今日统计并入「推送日志」标题行靠右(空态不再单飘 banner)· 删死占位 span · 去卡内孤立分隔线。同 commit 末批不翻面固定色:settings 移动端 tab `#fff!important`、对账锚点审计面板 `#fff7ed/#fed7aa` → 令牌;开关旋钮 #fff(配色轨成对)与暗夜品牌白垫板保留;home-18 amber 卡归 admin SPA 专项。
- [x] **Zihao 截图新 bug:商品管理暗夜表头白底** ✅ commit `06ca423`:home-39-sales.css 漏扫,sx-tbl 表头/hover/void 徽章/票样表头/模板预览 5 处不翻面固定色 → var(--bg) 等令牌。

## 三、还没看到的面(必须补抓再评 · 用户点名)
- [x] 修 `_ui_audit_full.spec.js` 行点击选择器(2026-06-10):按各屏真实渲染类名重写(.history-row[data-hid] / #pur-body .row[data-id] / sx-tbl tr.click / .cust-row .cust-cell-name / .exc-row[data-exc-id])。
- [x] L0.5 开票向导 5 步走步(只走步不开出 · 顺带抓步间校验错误态)+ L2 识别抽屉底部细节区,已入 spec。
- [ ] L0.5 真上传流程态(上传中/识别中/402/重复票)、对账双上传→结果、付款提交中 = **需专项**:对真账号有副作用(扣费/造数据),要配额度+清数据计划再跑。
- [ ] 系统生成文件:合规发票 PDF / 替代收据 / 税票 / 热敏小票 / 导出 Excel 版式 = 同上专项。
- [x] **2026-06-10 prod 补抓两轮已跑**(61 面 · scripts/_ui_audit_full/):L0 浅+暗 24 屏、L1 设置/规矩/ws-modal、L05 向导 5 步全拿到;prod 实证 S5 文案(อ่านแม่นยำ 0% · ผลการอ่านต้องตรวจสอบ)/S8 信息带/S9 进项主屏均已生效。
- [ ] 补抓遗留(下一轮 spec 再修):① cmdk openCmdk() 调了但面板没出(截到背景页)② camera-tips/help 无此全局函数(openers 表要换真名或删)③ L1 行点开抽屉 flaky(行渲染受套账/工作模式态影响 · 历史验收多轮过 = 非产品 bug · spec 要带 console 捕获 + JS 直点 + 固定 work_mode)④ 销项/客户 no row = e2e_3 该套账列表空,补种子再抓。
- [x] **补抓发现并已修:home-40 向导/票样 9 处不翻面固定色**(.sw-cart #fbfbf9 · 票样表头 #f3f3ee/#444/#e3e3dd · words #faf9f5 · 合计线 #111 · copy 徽章 #888 → 语义令牌)。

## 四、非代码项 / 拍板记录(2026-06-10 Zihao:「需要拍板的全按标准走」)
- [x] Codex 测试种子数据已清(2026-06-10 prod):BAKELAB 套账 Codex 页脚置 NULL · 27 个 Codex 商品停用(is_active=false)· 20 张 Codex 单据已是 void(连号合规保留不删)· 别租户的 Codex QA 数据不动(E2E 基线)。
- [拍板] **POS(static/pos)与 admin(static/admin)独立 SPA:按全站标准迁 Emerald** —— 排入后续窗口专项(两 SPA 自带蓝调色板 ~70 处,照 S1/S2 同套打法:令牌翻值+语义令牌收编)。
- [拍板] **暗夜主按钮 mint 不降饱和** —— kit-final 封板令牌(#2DD4A7+深字)即标准,该议题关闭。
- [拍板] **着陆页不动**(图标不要线性 · static/landing 永久排除)。
- integrations 品牌彩图标:保留品牌色但统一装 36 圆角中性方块(集成页惯例例外,设白名单)。

## 验收
每修一刀:`node scripts/ui_design_lint.mjs` 重跑 → 真浏览器浅+暗截图复核 → 保真闸。
**✅ lint 已挂闸(2026-06-10)**:`--gate` 棘轮模式(各类命中数对 `scripts/ui_lint_baseline.json` 只许降不许升)进 pre-push(前端改动触发)+ CI lint-ui job,FAIL 模式。存量(POS/admin SPA · i18n 文字强调 · @media max-width 等虚高项)在 baseline 内;命中下降后跑 `--update-baseline` 收紧。
