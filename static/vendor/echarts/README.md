# Apache ECharts · 供货说明

| 项 | 值 |
| --- | --- |
| 上游 | https://github.com/apache/echarts |
| 版本 | 5.6.0(见同目录 `version`) |
| 许可 | Apache-2.0(全文见同目录 `LICENSE`,随产物一起分发) |
| 取自 | npm `echarts@5.6.0` 的 `dist/echarts.common.min.js`,字节一致 |
| 用途 | 超管「OCR 引擎」页(`/admin/engine`)的每页成本柱图与入口占比环形图 |

## 为什么是 common 构建,不是完整包

`echarts.common.min.js`(664KB)含折线/柱状/饼图 + tooltip / legend / markLine —— 成本面板要的
参考线(`markLine`)和图例都在里面。完整包 1.02MB 多出来的是地图/桑基/树图等本页用不上的图表;
`echarts.simple.min.js` 更小,但没有 `markLine`,画不出「当前定价 ฿1.50/页」那条参考线。

## 为什么 vendor 进仓库,不走 npm

1. **CSP 只允许 self**:`services/security/headers.py` 的 `script-src 'self'`,任何 CDN 域都会被浏览器拦掉。
2. **npm 依赖只在构建期存在**:前端产物进 git、服务器零 node,运行时没有 `node_modules` 可读。
3. **不进任何 bundle**:超管后台七个页面只有这一页画图,合进 `dist/admin.css`/`admin.js` 会让另外
   六页白背 664KB。`static/admin/admin-engine-charts.js` 在进入该页时才现拉,拉失败画成错误态带重试。

## 改版本怎么改

1. 换掉 `echarts.common.min.js` 与 `version`,`LICENSE` 若上游变更同步替换。
2. 确认新版仍导出 `echarts.init` / `echarts.getInstanceByDom`(验收脚本靠后者读真实 option)。
3. 跑 `node scripts/_admin_engine_ui_verify.cjs` 真浏览器复验柱图参考线与配色。

## 不要改这个文件夹里的 JS

它是第三方产物,已在 `.prettierignore` 与 `eslint.config.mjs` 的 ignores 里(`static/vendor/`)。
要改行为改 `static/admin/admin-engine-charts.js`,别改上游源码 —— 否则下次升级你的改动无声消失。
