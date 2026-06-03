// 把 home.html 里零散的浏览器全局脚本合并压缩成两个 bundle,按原加载位置分组:
//   pre.js  = main.js 之前(defer): recon-mapping + recon-review
//   post.js = main.js 之后(defer): version-banner + erp-mrerp-connect + erp-log-enhance
// 分组 = 原 DOM 顺序,保住相对 main.js 的执行时序(脚本依赖 main.js 设的全局 +
// erp-log-enhance 依赖 erp-mrerp-connect 的 window._mrerpConnectShared)。
// 每个文件独立 minify 后用 `;` 拼接 = 等价于原来各自一个 <script>(同享全局作用域)。
// i18n-data.js 是 715KB 纯数据(window.I18N),保留独立 <script>,不并入。
//
// 用法: node scripts/build-home-js.mjs

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { transformSync } from 'esbuild';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const BUNDLES = [
    { out: 'static/dist/pre.js', files: ['recon-mapping.js', 'recon-review.js'] },
    {
        out: 'static/dist/post.js',
        files: ['version-banner.js', 'erp-mrerp-connect.js', 'erp-log-enhance.js'],
    },
    {
        // 着陆页:顺序 landing→scale→i18n→mascot(defer · 保原 DOM 时序)
        out: 'static/dist/landing.js',
        files: [
            'landing/landing.js',
            'landing/landing-scale.js',
            'landing/landing-i18n.js',
            'landing/mascot-scene.js',
        ],
    },
];

for (const b of BUNDLES) {
    const parts = b.files.map((f) => {
        const src = fs.readFileSync(path.join(ROOT, 'static', f), 'utf8');
        return transformSync(src, { loader: 'js', minify: true }).code;
    });
    // `;` 兜底 ASI · 每段已是独立 minified 脚本,合并后顶层全局与原多 <script> 等价
    const code = parts.join(';\n');
    fs.mkdirSync(path.join(ROOT, path.dirname(b.out)), { recursive: true });
    fs.writeFileSync(path.join(ROOT, b.out), code);
    console.log(`✅ ${b.out} · ${b.files.length} 文件 → ${code.length} 字节`);
}
