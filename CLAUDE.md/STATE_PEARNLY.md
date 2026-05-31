# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 主控瘦身重写)

- **模式**:整顿封锁期 · 0 新功能 · 综合进度 **93%**(已过 90% 目标线)。
- **达标项**:测试 100%(2111 unit/220 int/18 E2E)· 工程化 100%(9/9)· db.py/home.css 达标 · app.py 4523→1727 · home.js 6190→5344。
- **剩余瓶颈**:① **home.js 5344→目标200**(还差5144·最大硬骨头·前端主逻辑·拆它高风险需逐块验)② app.py 1727→500(剩 ocr_recognize/LINE 高敏·需可靠 E2E 闸)③ 模块化 75%(缺 CSS 模块化)。
- **UI 修复(主控直改·真浏览器验过·全闭环)**:全站按钮黑→蓝(home-38收口.btn-primary)· 删除按钮实心红(.btn-danger)· 复选框勾选蓝(全局accent)· 忘记密码/改密框.cpw-* · 首页快速操作2×2卡片 · favicon ?v=2绕CF缓存 · 异常栏批量栏(选中才显示+变体)。
- **⚠️关键机制(易踩)**:改 src/*.js 源码必须 npm run build + git add static/dist 提交,否则 prod 跑旧bundle(部署不重建dist·见记忆 c3-commits-source-only-dist-rebuilt)。纯.css/.html不用(nginx直接serve)。
- **测试账号**:真数据账号 18685123459(有账套/异常·绕账套弹窗=点个人卡片+JS移除)· e2e_1/2/3余额充满999999。
- **待 Zihao 拍板**:① 进度纠正方向(文档曾占46%commit·STATE已从382KB瘦身) ② home.js死拗到200还是放宽 ③ 窗口数(3→1专攻?)。
- **最后 commit**:见 git log --oneline -5。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
