# 视觉照搬机械闸(治"施工不照搬设计稿,反复返工")

> 反复踩:设计稿好好的,施工"凭印象重画",按钮/布局/令牌都走样,Zihao 一次次打回。靠自觉没用 →
> 做成机械校验:生产页面的关键视觉令牌必须 == 设计稿,不一致 CI 红。同 check_ui_consistency 思路。

## 怎么查(Playwright · getComputedStyle 比对)

测试 `tests/visual/test_design_fidelity.spec.js`:
1. **映射表**(稿 ↔ 生产页 ↔ 关键选择器):
   | 设计稿(桌面/file://) | 生产页(本地反代/dev) | 关键选择器 |
   |---|---|---|
   | Pearnly_餐厅POS_UI预览/05-桌台管理.html | /home #page-pos-tables | 主按钮 / 卡片 / 区域tab / 桌台卡 |
   | Pearnly_POS_UI预览/13-收款设置.html | /home #page-pos-payment | 容器宽/对齐 / 开关 / 卡片 |
   | Pearnly_POS_UI预览/14-收银设置-平铺页.html | /home #page-pos-settings | tab / pane / 容器 |
   | Pearnly_采购_UI预览/02-拍照识别确认.html | … | 字段卡 / 主按钮 |
2. **比对项**(对每个关键选择器,getComputedStyle 稿 vs 生产 必须一致):
   - 主色 `#2563EB`(rgb(37,99,235))· 圆角 · box-shadow · font-size · padding/gap · font-family · 无 emoji 图标(线性 svg)。
   - 容器:max-width / 对齐(左对齐不居中飘)。
3. **不一致 = fail**,输出"哪个页/哪个选择器/稿是 X 生产是 Y"。

## 令牌基线(从设计稿 :root · 全 POS/采购页统一)
`--blue #2563EB · --blue-d #1D4ED8 · --ink #111827 · --ink2 #6B7280 · --bg #f4f4f0 · --card #fff · --line #e8e8e3 · 圆角 14/10 · 阴影 0 4-8px rgba(17,24,39,.05-.08) · body 13.5-14px · tabular-nums 金额`。

## 跑在哪
- pre-push(改 `static/pos/**` 或 `src/home/{pos,inventory,purchase}-*` 时触发)+ CI。
- 不一致红,挡 push。文档说明"加新页怎么补映射"。

## 范围
先覆盖 POS/采购的照搬稿页(桌台/收款/收银设置/采购主屏+识别);其余 home 页沿用 check_ui_consistency。

> 本闸 = "照搬"从口头铁律变机械强制。施工窗口改完跑它,红了就是没照搬,自己回去对齐,不用 Zihao 肉眼抓。
