# barcode-detector / zxing-wasm

Pearnly 自托管的摄像头条码兜底，不依赖商业 SDK、账号、在线服务或 CDN。

- `ponyfill.js`: `barcode-detector` 3.2.2 的 IIFE ponyfill，来源
  <https://github.com/Sec-ant/barcode-detector>。
- `zxing_reader.wasm`: `zxing-wasm` 3.1.3 的 reader-only WASM，来源
  <https://github.com/Sec-ant/zxing-wasm>。
- 两个项目都是 MIT 许可，许可全文分别保存在同目录的 `*-LICENSE`。
- 运行时只请求 `/static/dist/*` 同源资产，以满足 CSP 和收银台离线缓存；不得改回 CDN。

升级时从 npm 发布包复制上述两个文件，更新 `version` 和 SHA-256 断言，然后运行
`node scripts/build-home-js.mjs`。不要直接修改上游产物；Pearnly 行为写在
`static/scan/scan-wasm-shim.js`。
