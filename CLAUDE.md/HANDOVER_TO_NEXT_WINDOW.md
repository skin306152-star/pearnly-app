# 交接备忘 · 下窗口接手必读

> 最后更新：2026-05-13 · v4.10.1 收尾

---

## 今天完成

| 版本 | 内容 | 状态 |
|---|---|---|
| v4.9.6.4 | 销项税对账 13/13 case 全过 | ✅ |
| v4.10.0 | vat_recon_tasks DB + 后端 API（6 CRUD + 5 路由） | ✅ |
| v4.10.1 | 撤 toggle/BETA/email gate + KPI 4卡 + 任务列表 + 标题区跟随子模块 | ✅ 线上 |

---

## 关键决策（不懂就翻 CLAUDE.md）

1. **4 语铁律**：th/en/zh/ja 都是真产品语言 · 泰国首发 · 字典顺序 th→en→zh→ja（开发优先级）
2. **adm-* 简化**：超管后台只要 zh+th 2 语 · 节省 ~274 翻译单元
3. **字典存量顺序不动**：home.js 历史顺序 zh→en→th→ja · 新增 key 按 th→en→zh→ja 写入各语言块
4. **settings.json 默认 plan mode** 已设（大任务先 plan 再 execute）

---

## 下窗口先做：v4.10.2

### A. 顺手修 v4.10.1 5 个残留（先做 · 快）

**⑤ 最高优先级 · 下载 410 bug**
- 问题：旧任务（v4.10.0 前）点下载箭头 → 触发 href 下载 → 后端返回 download.json 错误
- 根因：老任务无 raw_data（410 Gone） · 前端当 href 直接触发没处理状态码
- 修法：下载按钮改 `fetch` 异步 · 看状态码：
  - 410 → toast "数据已过期 · 请重新对账"（4 语见下）
  - 200 → 正常触发 Excel 下载（blob → a.click）
- 4 语 toast key: `vex-download-expired`
  - zh: 数据已过期 · 请重新对账
  - en: Data expired · please re-run reconciliation
  - th: ข้อมูลหมดอายุ · กรุณากระทบยอดใหม่
  - ja: データ期限切れ · 再度照合してください
- 验证：旧任务点下载 = toast ✓ / 新任务（v4.10.0 后）点下载 = 正常 Excel ✓
- 设计预期：v4.10.0 前的老任务永远 410 · 用户需重新对账才能下载

**① 状态列显示英文"done"**
- 位置：home.js `_renderVexTaskList` 里 badge 渲染
- 修法：badge 文字改 `t('vex-status-' + row.status)` · 已有 4 语 key（v4.10.1 已加）

**② 客户列兜底显示英文"client"**
- 问题：OCR 没抽到客户名时 fallback 显示硬编码 "client"
- 修法：空值时显示 `t('vex-client-all')`（全部客户 4 语）；有名称显示原文（不翻）
- 新增 4 语 key: `vex-client-all`
  - zh: 全部客户 · en: All Clients · th: ทุกลูกค้า · ja: 全顧客

**③ 标题区重复**
- 问题：顶部 page-head 有标题 + 销项税主区内又有一模一样的标题 → 视觉重复
- 修法：删主区重复标题 HTML 元素（保留 page-head 那个）

**④ 底部死代码**
- 位置：home.html 销项税对账 pane 底部"还没有对账任务"文字 + 旧上传区
- 修法：完全删除（死代码 · 新任务列表已覆盖）

### B. v4.10.2 详情抽屉（主体功能）

- 540px 右侧 drawer
- 5 个分区：① 任务概览 ② 核对摘要 ③ 差异明细表 ④ 文件溯源 ⑤ 操作区
- 详细规格见 MODULE_SALE_VAT_RECON_PRD.md 或本次对话历史

---

## 已知小问题（不是 bug · 是设计）

- v4.10.0 之前的老任务永远 410（没有 raw_data）· 用户需重新对账才能下载 · **这是设计预期**
- home.js i18n 字典顺序历史是 zh→en→th→ja · 不改（10k+ 行 · 风险高）

---

## 文件位置速查

| 文件 | 路径 | 用途 |
|---|---|---|
| 前端主文件 | D:\Users\Skin\Desktop\pearnly_project\home.js | i18n + JS 逻辑 |
| 前端 HTML | D:\Users\Skin\Desktop\pearnly_project\home.html | 结构 |
| 前端 CSS | D:\Users\Skin\Desktop\pearnly_project\home.css | 样式 |
| 销项税对账路由 | D:\Users\Skin\Desktop\pearnly_project\vat_excel_routes.py | API |
| 销项税对账导出 | D:\Users\Skin\Desktop\pearnly_project\vat_excel_export.py | Excel 生成 |
| 服务器 | root@45.76.53.194 /opt/mrpilot/ | 生产环境 |
| cache bust 当前 | v=11841000 | home.js + home.css |

---

*本文件每次收尾覆盖重写 · 始终是最新状态*
