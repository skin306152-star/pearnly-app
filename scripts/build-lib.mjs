// 前端资产打包脚本的共享 I/O(build-home-css / build-home-js / build-html-minify 共用)。
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

// 读源文件 + strip 开头 BOM。BOM 单独 <link>/<script> 时浏览器忽略,但合并进 bundle
// 中间就是非法字符,破坏紧跟的那条规则/语句(landing-auth.css 的 .auth-card 中招过)。
export function readSource(relPath) {
    const fp = path.join(ROOT, relPath);
    if (!fs.existsSync(fp)) throw new Error(`源缺失: ${relPath}`);
    return fs.readFileSync(fp, 'utf8').replace(/^\uFEFF/, '');
}

export function writeDist(relOut, code) {
    const fp = path.join(ROOT, relOut);
    fs.mkdirSync(path.dirname(fp), { recursive: true });
    fs.writeFileSync(fp, code);
    console.log(`✅ ${relOut} · ${code.length} 字节`);
}
