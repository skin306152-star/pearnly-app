// REFACTOR-A1.1 (2026-05-22) · Vite 6 build 配置
// 方案:本地 build · 产物进 git · 服务器零改动
// 输出:static/dist/main.js(固定文件名 · home.html 用 ?v= 老 cache_bust)
// 后续 A1.x 阶段再切换到 hash + manifest 模式
import { defineConfig } from 'vite';
import { resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
    build: {
        outDir: 'static/dist',
        emptyOutDir: true,
        sourcemap: true,
        minify: 'esbuild',
        target: 'es2020',
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'src/main.js'),
            },
            output: {
                entryFileNames: '[name].js',
                chunkFileNames: '[name].js',
                assetFileNames: '[name].[ext]',
            },
        },
    },
});
