# 🔘 按钮统一 · 主控接管执行计划(durable handoff)

> 2026-05-30 · Zihao 拍板「主控接管·一次性做完」· 窗口 B 已暂停按钮(REFACTOR-WB-BTN handoff complete `d30cd62`)。
> **本文是单一权威**:任何窗口(主控续/新窗口/重新指派 B)照此执行,不丢、不漏、不改坏功能。配套 OUTCOMES.md #1/#2/#3。
> 背景:之前自主"一条条 drip 改"产生 ① 变体不一致(主操作被做成白描边方框)② 漏删 ③ 改坏功能。本计划=一次性完整映射,消除判断漂移。

## 0. 铁律(每条都踩过坑)
- **绝不改 id / JS querySelector·getElementById·classList 钩子用的 class**——只动样式 class,否则 handler 断(忘记密码就是这么挂的同类)。
- **所有批量栏:选中才显示**(selected==0 → hidden/display:none),照发票记录 history-batch-bar。
- 改完**自己 Playwright 截图 + 读图核**(蓝/变体对/非黑/可点/无 console error),不烦 Zihao;只在"变体拿不准"时问。
- home.html 是 CRLF + .prettierignore;别 prettier --write;删大块 node split/join 保 CRLF。

## 1. 先修两个真 bug(优先)
### Bug A · 忘记密码按钮失效(真功能坏·根因已定位)
- 根因:`src/home/change-password.js` 在 **DOMContentLoaded** 时 `getElementById('cpw-forgot-link')` 绑 click;但设置面板是 C3 抽取后(`9ea57fa` page-settings.js)**运行期才注入** → 加载时按钮不存在 → handler 永不绑 → 死。
- markup 在 `src/home/page-settings.js:224` `<button class="cpw-forgot-link" id="cpw-forgot-link" ...>忘记当前密码?</button>`(id 完好)。
- **修法**:把 forgot-link 绑定(及同文件其它 cpw-* 在 DOMContentLoaded 直绑、但元素运行期才注入的)改成**事件委托**:`document.addEventListener('click', e => { if (e.target.closest('#cpw-forgot-link')) openForgotCurrentPwModal(); })`。委托对运行期注入免疫。⚠️先核 change-password.js 整个 bindEvents 是否都受同一 race(submit/eye/tab 可能也得改委托或改成面板打开时再 bind)。
- 验证:登录→设置→账户安全→点"忘记当前密码?"→弹窗出现。改密提交/眼睛切换也要能用。

### Bug B · 删桌面「上传图片」按钮(OUTCOMES #2·没执行)
- 位置:`home.html:466-483`(v113 注释 + `<span data-i18n="btn-upload-pic">上传图片</span>`)。
- **删桌面那颗·保留手机端 @media 拍照/相册入口·home.js L1818 函数别删**。
- 验证:桌面视口无该按钮、手机视口(390x844)仍有。

## 2. 全站按钮收编(完整映射·消除判断漂移)
变体(static/home-38-buttons.css 已全有·border-radius 9px):
- **btn-primary**(实心蓝 #2563eb)= 上下文里的**主操作**:重试/批量重试/直接重试/保存/确认/开始识别/提交/新建/连接/绑定并重试。
- **btn-danger**(红描边)= 删除/禁用:批量删除/删除/移除/禁用/停用。
- **btn-secondary**(白底描边)= 次要:取消/关闭/编辑/导出/修改/分配客户/发送改密链接。
- **btn-ghost**(幽灵)= 清除/去异常处理。
- **tab/chip/nav**(分段·非实心蓝)= 全部/客户不符/商品不符 chips、settings-tab、recon tabs、nav-item → 用 btn-secondary 或专门 tab 变体,**绝不做成实心蓝**(会破坏)。
- **btn-icon** = 纯图标(发票记录批量栏下载/删除图标)。**btn-sm** = 小尺寸修饰。

做法:逐模块,把旧杂牌类(tc-btn系/bank-filter-btn/email-interval-btn/dash-quick-btn/ob-btn-*/int-btn-view-logs/erp-map-*/folder-alt-btn/cpw-forgot-link/exc-retry-btn 等)+ 11 内联 style 按钮,换成上面对应变体;删旧类黑色 CSS(或改成变体);**保留钩子 class/id**。

### 窗口 B 已做(别重做·只核一致):bank-filter / 异常栏批量栏(erp-exc-batch 已是 primary/danger/ghost+hidden✓)/ erp-exc 行内重试 / 异常栏 OCR 重试(exc-retry-btn→btn-secondary)/ hist-batch-icon→btn-icon(`d30cd62`)。
### ⚠️ 已知做错/没做(要改):
- 异常栏(exceptions.js)exc-batch-bar 的批量重试/删除/取消若是白描边方框 → 改 primary/danger/ghost(主操作蓝)。
- 集成/推送日志(erp-integration / page-integrations):批量重推、推送失败弹窗"重试" 还黑 → 收编。
- 客户管理(设为当前/编辑/归档)· 团队管理(分配客户/发送改密链接/禁用/移除)· 设置各按钮 · Pearnly 访问日志导出CSV → 收编。
- 全站逐条核每个批量栏是否 hidden-when-empty。

## 3. 验收(Zihao 一次性审)
全部改完 → 主控/窗口跑 Playwright 截关键页(异常栏/集成/客户/设置/发票记录)自核 → 让 Zihao 看一遍关键页确认"蓝/变体对/选中才显示/忘记密码能点/上传图片没了" → OUTCOMES #1/#2/#3 划掉。
