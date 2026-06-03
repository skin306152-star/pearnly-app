// 把可读的 home.html / login.html 源压缩成 minified 产物到 static/dist/,
// 路由层改读这俩(见 routes/pages_routes.py)。源保持可读,产品 view-source 精简成一行。
//
// 用法: node scripts/build-html-minify.mjs

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { minify } from 'html-minifier-terser';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

// 保守但有效:折叠标签间空白 + 压内联 JS(鉴权 bootstrap),保留 data-i18n / 属性引号 / 自闭合斜杠
const OPTS = {
    collapseWhitespace: true,
    conservativeCollapse: true, // 至少留一个空格,防 inline 元素(span/a)粘连
    removeComments: true,
    minifyJS: true,
    minifyCSS: true,
    keepClosingSlash: true,
    caseSensitive: true,
};

// 源(根目录·可读) → 产物(dist·minified)。home/login 经 FileResponse 读产物。
// admin.html 由 StaticFiles 直接 serve(无源/产物分离机制)+ 超管页防抄需求低 · 留可读源不压。
const TARGETS = [
    { src: 'home.html', out: 'static/dist/home.html' },
    { src: 'login.html', out: 'static/dist/login.html' },
];

for (const t of TARGETS) {
    const srcPath = path.join(ROOT, t.src);
    const html = fs.readFileSync(srcPath, 'utf8');
    const min = await minify(html, OPTS);
    const outPath = path.join(ROOT, t.out);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, min);
    console.log(`✅ ${t.out} · ${html.length}→${min.length} 字节`);
}
