# 状态语言 · 全站状态的唯一视觉词典(B1 · 2026-07-26 Zihao 拍板 15 类)

> 活样例:`pearnly.com/ai` 打开后 URL 直达 `#/states`(不进侧栏——词典页给装配新页面的人查,
> 不是业务入口)。实现:令牌+组件 `static/ai/ai-states.css`,样例拼装 `static/ai/ai-states-render.js`,
> 挂载 `static/ai/ai-states.js`。今后所有页面(含智能管家)表达状态一律从这里取"脸",
> 不许自造——按钮 159 变体 / modal 127 类的碎片化教训(2026-07-24 全站 UI 审计)就是这么来的。

## 1. 八大色系令牌(每系 bg / fg / line 三值)

语义层 `--st-*` 定义在 `ai-states.css`,色值全部引用 `ai-theme.css`(hex 只许出现在那里;
执行蓝 `--exec` / AI 紫 `--brain` / 警告橙 `--alert` 三族是 B1 补进 ai-theme 的新色相,
饱和度与既有 good/warn/crit 同档,米色底上一个柔和度)。

| 色系 | 语义 | 令牌 | 底层值(ai-theme.css) |
|---|---|---|---|
| 绿 | 正常 / 完成 / 通过 | `--st-ok-bg/-fg/-line` | `--good*` |
| 黄 | 等待 / 待处理 / 排队 | `--st-wait-bg/-fg/-line` | `--warn*` |
| 蓝 | 执行中 / 上传中 / 审核中 | `--st-run-bg/-fg/-line` | `--exec*`(新) |
| 紫 | AI 在做(思考/工具/OCR/生成) | `--st-ai-bg/-fg/-line` | `--brain*`(新) |
| 橙 | 警告 / 降级 / 需补料 | `--st-warn-bg/-fg/-line` | `--alert*`(新) |
| 红 | 错误 / 失败 / 驳回 / 锁定 | `--st-err-bg/-fg/-line` | `--crit*` |
| 灰黑 | 禁用 / 已取消 / 无权限 | `--st-off-bg/-fg/-line` | `--neutral-soft`/`--mut`/`--hair2` |
| 白 | 空 / 无数据 | `--st-empty-bg/-fg/-line` | `--surface`/`--faint`/`--hair` |

组件取色一律走色族修饰类 `.st-ok/.st-wait/.st-run/.st-ai/.st-warn/.st-err/.st-off/.st-empty`
(把三值装进 `--st-bg/--st-fg/--st-line`,徽章/进度/动画通吃,一个类切换整族)。

## 2. 组件清单(类名 = ai-states.css 里的唯一拼法)

| 组件 | 类名 | 用途 |
|---|---|---|
| 徽章(胶囊) | `.st-badge` + 色族类 | 一切离散状态的标准脸(同矩阵「已冻结/无需申报」形制) |
| 进度条 | `.st-bar`(`--p` 0~100)| 有可数进度的任务 |
| 进度环 | `.st-ring`(`--p`)| 紧凑位置的百分比 |
| 步骤 | `.st-steps`(`<i class="on">` 已完成段)| 流程走到第几步 |
| 计数 | `.st-count` | 27/128 文件、Token 用量这类分子/分母 |
| 排队 | `.st-queue` | 前面还有 N 个 |
| 预计剩余 | `.st-eta` | ETA 文案 |
| 骨架屏 | `.st-skeleton` | 加载中(存量 `.skel` 不动,新页面用这个名) |
| 流光 | `.st-shimmer` | 正被处理的卡片/文件扫光 |
| 呼吸 | `.st-pulse` | 活着但没有可数进度(AI 思考中) |
| 三点 | `.st-dots` | 短等待(调用工具/生成回答) |
| 徽章跳动 | `.st-badge-bounce` | 新通知到达,跳 3 下即停 |
| 按钮七态 | `.st-btn`(+`[disabled]`/`.is-loading`/`.is-success`/`.is-error`;`.is-hover`/`.is-active` 仅样例页静态展示)| default/hover/active/disabled/loading/success/error |
| AI 可解释卡 | `.st-explain`(`.on` 展开)| 结论 + 可展开「依据:票面/历史/规则」 |

JS 拼装统一走 `AI.statesRender.*`(badgeHtml/barHtml/ringHtml/stepsHtml/countHtml/queueHtml/
etaHtml/dotsHtml/btnHtml/explainCardHtml),别手写 HTML 串再抄一份类名。

## 3. 15 类 → 色族/组件 → 消费方

| # | 类别 | 用什么 | 现在谁消费 | 后续批次 |
|---|---|---|---|---|
| 一 | 数据状态 | ok/empty/err 徽章 + `.st-skeleton` | /ai 四态壳(ai-state.js 的 loading/empty/error) | 智能管家 M1 |
| 二 | 任务状态 | wait/run/ok/err/off 徽章 | 矩阵/看板工单态(ai-format chipHtml 语义同源) | 管家任务卡 |
| 三 | AI 状态 | ai 紫族 + `.st-pulse`/`.st-dots`/`.st-shimmer` | — (B1 新立) | 管家 M1 首个消费方 |
| 四 | 流程状态 | 徽章链 + `.st-steps` | 工单步骤条(step_intake…) | 管家流程页 |
| 五 | 系统状态 | ok/wait/warn/err/off 徽章 | — | 系统健康条 |
| 六 | 进度状态 | `.st-bar/.st-ring/.st-count/.st-eta/.st-queue/.st-steps` | 收料上传进度 | 管家跑批进度 |
| 七 | 风险状态 | ok/wait/warn/err 徽章 | 矩阵 risk 过滤 | 风险面板 |
| 八 | 审核状态 | wait/run/ok/err/warn 徽章 | 审核收件箱 | 管家审核卡 |
| 九 | 文件状态 | run 条 + ok/ai/err/off 徽章 | 收料清单 | 管家收料 |
| 十 | 通知状态 | warn 徽章 + `.st-badge-bounce` + `.st-queue` | — (铃铛尚无真数据) | 通知中心 |
| 十一 | 权限状态 | ok/wait/off/err 徽章 | — | 花名册/授权页 |
| 十二 | 按钮状态 | `.st-btn` 七态 | — (存量 .btn 不动) | 新页面按钮基线 |
| 十三 | AI 可解释状态 | `.st-explain` | — (B1 新立) | 管家判定卡 |
| 十四 | 颜色状态 | 八族 `--st-*` 令牌 | 本词典全部组件 | 一切新状态样式 |
| 十五 | 动画反馈 | `.st-skeleton/.st-shimmer/.st-pulse/.st-dots/.st-badge-bounce` | /ai 骨架屏(.skel 同配方) | 全站动效基线 |

## 4. 命名规范

- 令牌:`--st-<族>-<bg|fg|line>`,族名 = `ok/wait/run/ai/warn/err/off/empty` 闭集,不加新族。
- 组件类:`st-` 前缀 = 全站词典;`sts-` 前缀 = `#/states` 样例页私有布局,业务页面禁用。
- JS:纯拼装在 `AI.statesRender`,状态语义映射(业务码 → 色族)由各页自己的 render 层查表
  (参照 `ai-matrix-render.js` 的 `BADGE_CHIP` 先例),不塞进词典。
- 动画时长只用 `ai-theme.css` 的 `--dur-*` 令牌,组件层禁写死毫秒。

## 5. 三条铁规

1. **状态灯必绑证据,不许手工点绿。** 任何状态徽章/进度值必须由真实数据推导(后端字段、
   闸退出码、轮询结果),UI 不提供"把状态改成完成"的手工开关;`rows=0/failed/ERR_*`
   永不显示成功族(全站红线 #3 的视觉承接)。
2. **四态诚实。** 每个取数视图 loading/empty/error/ok 四态都要有,空态指路;加载用骨架
   不用假数据占位,错误态必带重试或出路。
3. **新页面禁自造状态样式。** 表达状态只许用本词典的令牌/组件;词典缺什么,先补词典
   (改 `ai-states.css` + 本文档 + `#/states` 样例)再用,不许在页面里就地发明。

## 6. i18n

样例页文案是内部规范页(不进侧栏、URL 直达),按 adm-* 超管键先例只写 zh+th
(`static/ai/ai-i18n-states.js`,en/ja 由 at() 回落 zh);守门测试
`tests/unit/test_ai_states_pure.py` 锁 zh/th key 集合一致 + 页面引用的每个 `sts_*` key
都真实存在(防深链落空的教训:被引用的标识符必须来自真实产物)。
