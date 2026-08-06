/*
 * scripts/_smoke_server.cjs · 4 支 _*_smoke.cjs 共用的本地静态/桩服务器
 *
 * _inv_scan_smoke / _pos_scan_smoke / _sales_dashboard_smoke / _scan_smoke 各自内嵌过一段
 * 几乎同构的 createServer(静态根 = 仓库根,懒加载的 /static/dist/*.js 在 file:// 下不成立,
 * 必须走同源 HTTP)。抽到这里单一事实源,行为与各脚本旧内嵌段零变化:静态根 + 可选默认首页
 * + 404 体文案用参数对齐差异;routes 桩表(前缀 → 状态/体/类型)是模块 API,当前 4 支都没传。
 * 调用方 await startStaticServer({...}) 拿 {address().port},再拼 http://127.0.0.1:<port>/。
 */
const fs = require('fs');
const http = require('http');
const path = require('path');

const MIME = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' };

/**
 * 仓库根静态服务器。
 * @param {object} opts
 * @param {string} opts.root 静态根(路径前缀越界一律 404)
 * @param {string} [opts.index=''] 裸路径 / 的默认首页;'' = 不映射,目录 → 404
 * @param {string} [opts.notFoundBody='<!doctype html><title>404</title>'] 404 响应体
 * @param {Array<{prefix: string, status?: number, body: string, contentType?: string}>} [opts.routes]
 *        命中前缀先于静态文件响应的桩表(供需要假 API 的脚本用)
 * @returns {Promise<http.Server>} 已监听 127.0.0.1 随机端口
 */
function startStaticServer({ root, index = '', notFoundBody = '<!doctype html><title>404</title>', routes = [] }) {
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        for (const r of routes) {
            if (rel.startsWith(r.prefix)) {
                res.writeHead(r.status || 200, { 'content-type': r.contentType || 'text/html' });
                res.end(r.body);
                return;
            }
        }
        const fp = path.join(root, rel || index);
        if (!fp.startsWith(root) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
            res.writeHead(404, { 'content-type': 'text/html' });
            res.end(notFoundBody);
            return;
        }
        res.writeHead(200, {
            'content-type': MIME[path.extname(fp)] || 'application/octet-stream',
        });
        fs.createReadStream(fp).pipe(res);
    });
    return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

module.exports = { startStaticServer, MIME };
