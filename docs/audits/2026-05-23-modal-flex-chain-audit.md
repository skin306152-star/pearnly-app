# Modal Flex-Chain Audit · BUG-FIX-P0.4(2026-05-23)

> **触发**:`docs/audits/2026-05-22-ocr-recon-audit.md` Phase 0 · P0.4 ·
> v118.34.39(settings 左栏 side-nav)+ v118.35.0.35(settings 右栏 content)修过同款 bug 2 次 ·
> 现在 audit 全项目 · 找其它 modal 是否同款 flex-chain + overflow:auto 病 · 列清单 · 留修法预案
>
> **结论**:6 个 modal/drawer 类型扫了 · 2 个**潜在风险** · 当前 0 个有真 bug 报告 ·
> 不预修 max-height(铁律 #21:整改不污染 · 不引入未触发的新风险)· 但加 `min-height: 0` 防御性兜底 2 处

---

## 1. 病因回顾(给下次接力 agent 看)

**病 pattern**(settings modal 当年的 bug):
- 父 modal `display: flex; flex-direction: column; max-height: 85vh / 92vh`
- 子 body `overflow-y: auto; flex: 1`(**没** `min-height: 0`)
- 子 sub-section(side-nav / form / table 等)拉伸超过 modal 时:
  - 浏览器 zoom 偏移(67/75/80/90/100/142% 都有人撞)→ px rounding → flex 高度解析失败
  - `min-height` 默认 `auto`(等于内容高度)· flex item 至少跟内容一样高 · 不会 shrink
  - `flex: 1` 不能让子小于内容 · 子高度 > 父 modal max-height
  - 父 modal `overflow: hidden` 把超出部分切掉 · 子的 `overflow: auto` 永远不触发滚动条
  - 用户看不到 modal 底部字段(国家 / LINE ID / 联系我们 等)

**修法 pattern**(2 次都用同款):
1. v118.34.39 / v118.35.0.35:直接给受害子设 `max-height: calc(min(85vh, 100vh - 64px) - 80px) !important`
2. 配 `min-height: 0 !important` · `overflow-y: auto/scroll !important`
3. bypass flex chain · 子自己卡死高度 · 不靠父 flex 推

---

## 2. Audit 结果 · 6 个 modal/drawer 类型

| # | 类 | 位置 | 高度 | 内部 | overflow | 风险 | 措施 |
|---|---|---|---|---|---|---|---|
| 1 | `.modal` | home.css L1924 | `max-height: 92vh` | flex column | `.modal-body overflow-y:auto + flex:1` **缺 min-height:0** | **🔴 高** | **加 `min-height: 0` 防御**(P0.4 改) |
| 2 | `.rd-modal` | home.css L1276 | `max-height: 85vh` | flex column | `.rd-modal-body overflow-y:auto + flex:1 + min-height:0` | 🟡 中 | watch only · 不改(已有防御) |
| 3 | `.drawer` | home.css L820 | `height: 100vh` | flex column | `.drawer-body overflow-y:auto + flex:1` **缺 min-height:0** | 🟡 中 | **加 `min-height: 0` 防御**(P0.4 改) |
| 4 | `.log-detail-box` | home.css L2723 | `max-height: 85vh` | 单 div · 不用 flex | 直接 `overflow-y:auto` | 🟢 低 | 健康 · 不动 |
| 5 | `.admin-modal` | home.css L4368 | `max-height: 90vh` | 单 div · 不用 flex | 直接 `overflow-y:auto` | 🟢 低 | 健康 · 不动 |
| 6 | `.add-emp-modal` | home.css L3256 | 无 max-height | 短表单 · 不用 flex | `overflow: hidden` | 🟢 低 | 健康 · 不需要滚 · 不动 |

`.modal` 是项目里**最常用**的通用 modal(套餐对比 / 充值 / 一般 confirm 等都用它)· 修这个收益最大。

---

## 3. 当前措施(P0.4 v118.35.0.40)

### 加 `min-height: 0` 防御 2 处

```css
/* home.css L1960-1964 改 */
.modal-body {
    padding: 20px;
    overflow-y: auto;
    flex: 1;
    min-height: 0;  /* P0.4 v118.35.0.40 · 防 flex chain + overflow:auto 不触发(settings 同款病预防) */
}

/* home.css L872 改 */
.drawer-body { flex: 1; overflow-y: auto; padding: 14px 20px 80px;
               min-height: 0; /* P0.4 v118.35.0.40 · 同 .modal-body 防御 */
}
```

### 为啥不直接镜像 settings 同款修法?

settings 同款修法 = `max-height: calc(min(85vh, 100vh - 64px) - 80px) !important`

**不预先用是 3 个理由**:
1. 当前**没真 bug 报告**(. modal / .drawer 当前在生产没用户撞)
2. `max-height: calc(...) !important` 会**覆盖**子 sub-section 自己的 max-height · 引入未知 layout 变化
3. settings 修法用的 -80px / -64px magic number 是针对 settings layout 的(header 64px + footer 80px)· 套到 .modal 不一定准

**触发条件**:
- 用户报告"通用 modal 看不到底部字段"
- DevTools 抓出 .modal-body 高度 > .modal max-height
- 那时再用 settings 同款修法 · 调整 magic number 匹配 .modal 实际 header/foot

---

## 4. 修法预案(将来撞 bug 直接抄)

### .modal 撞 bug 时:

```css
/* home.html 顶部内联 <style> 加(scoped 到具体场景) */
.modal-overlay.show .modal {
    /* 防 flex chain 不传力 */
}
.modal-overlay.show .modal-body {
    max-height: calc(min(92vh, 100vh - 40px) - var(--modal-headfoot-height, 100px)) !important;
    min-height: 0 !important;
    overflow-y: auto !important;
}
```

`--modal-headfoot-height` 默认 100px(.modal-head ~50px + .modal-foot ~50px)· 具体 modal 可覆盖。

### .drawer 撞 bug 时:

```css
/* drawer-body 实际上父高度卡死(100vh)· 子 flex:1 应该不会撞 · 但保险起见 */
.drawer-body {
    max-height: calc(100vh - 60px) !important;  /* 60px = drawer-header 高度 */
    min-height: 0 !important;
    overflow-y: auto !important;
}
```

---

## 5. 整顿期 D 阶段建议(借 P0.4 reward)

**REFACTOR-D 集成测试** 应加 modal 滚动 E2E:
- Playwright 测各 modal 在 100% / 80% / 67% zoom 下能否滚到底部
- 覆盖 `.modal` / `.rd-modal` / `.drawer` 3 个高风险类
- 自动化跑这条 + viewport 多档(640px / 768px / 1024px / 1920px)
- 任何 modal 内容超过 viewport 都能滚到底

未来加这套测试 = 直接捕获 settings 当年那种 bug · 不用等用户报告。

---

## 6. 接力 agent 必读

- `.modal` / `.drawer` 已加 `min-height: 0` 防御 · 不要再加任何 max-height 设置(等 bug 报告再加)
- 看到通用 modal 滚不到底报告 · 第一反应:**加 max-height calc · 别想其它**(已吃 settings 5 轮教训)
- 看到 .rd-modal 滚不到底 · 同款修法 · 用 85vh - 100px(header 16x2 + foot 12x2 + content padding 16x2 ≈ 88px)

---

**Audit 完成**:2026-05-23 · Claude Opus 4.7 (1M context) + Zihao 拍板(P0.4 task)。
**单一权威源**:整改 Phase 0 收尾审计文档 · 跟 `2026-05-22-ocr-recon-audit.md` 同级。
