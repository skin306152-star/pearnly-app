# zxing-js/library · 供货说明

| 项 | 值 |
| --- | --- |
| 上游 | https://github.com/zxing-js/library |
| 版本 | 0.21.3(见同目录 `version`) |
| 许可 | Apache-2.0(全文见同目录 `LICENSE`,随产物一起分发) |
| 取自 | Odoo 18 社区版 `addons/web/static/lib/zxing-library/zxing-library.js`,字节一致 |
| 用途 | 摄像头扫商品条码。浏览器原生 `BarcodeDetector` 不存在时(iOS Safari 全系、桌面 Firefox/Safari)才用它兜底 |

## 为什么 vendor 进仓库,不走 npm

1. **CSP 只允许 self**:`services/security/headers.py` 的 `script-src 'self'`,任何 CDN 域都会被浏览器拦掉。要用就必须自己 serve。
2. **要能离线**:收银台是 PWA(`static/pos/pos-sw.js` cache-first),店里断网也得能扫码。依赖外网域名的方案在断网时直接哑掉。
3. **不进任何 bundle**:压完仍有几百 KB,并进首屏 bundle 会让泰国移动网络下的开机时间明显变长。构建脚本把它单独压成 `static/dist/zxing.js`,只在真的没有原生 `BarcodeDetector` 时由 `static/scan/scan-camera.js` 现拉。
4. **npm 依赖只在构建期存在**:本仓库的前端产物进 git、服务器零 node,运行时没有 `node_modules` 可读。

## 改版本怎么改

1. 换掉 `zxing-library.js` 与 `version`,`LICENSE` 若上游变更同步替换。
2. 跑 `node scripts/build-home-js.mjs` 重出 `static/dist/zxing.js`。
3. `static/scan/scan-zxing-shim.js` 只用 `BarcodeFormat` / `DecodeHintType` / `MultiFormatReader` / `BinaryBitmap` / `HybridBinarizer` / `HTMLCanvasElementLuminanceSource` 这几个导出,升级后先确认它们还在。

## 不要改这个文件夹里的 JS

`zxing-library.js` 是第三方产物,已在 `.prettierignore` 与 `eslint.config.mjs` 的 ignores 里。要改行为改 `static/scan/scan-zxing-shim.js`,别改上游源码 —— 否则下次升级你的改动无声消失。
