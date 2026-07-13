// tests/e2e/_local_static_server.js · 本地 stub spec 共享的静态服务起停
// ============================================================
// _mc1b2/_ui1/_h1b 等「python http.server 静态服 static/dist + page.route stub /api/**」
// 范式的 spec 此前各抄一份 spawn+waitUp 样板,收到这里。下划线文件名不匹配 *.spec.js,
// Playwright 不当测试收。用法:
//   const localServer = require('./_local_static_server');
//   let server;
//   test.beforeAll(async () => { server = await localServer.start(PORT); });
//   test.afterAll(() => localServer.stop(server));
const { spawn } = require('child_process');
const http = require('http');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');

function waitUp(url, tries = 40) {
    return new Promise((resolve, reject) => {
        const hit = (n) => {
            http.get(url, (r) => {
                r.resume();
                resolve();
            }).on('error', () => {
                if (n <= 0) return reject(new Error('server not up'));
                setTimeout(() => hit(n - 1), 150);
            });
        };
        hit(tries);
    });
}

// 起 python -m http.server 服仓库根,等 readyPath(缺省 ai.html)可达后返回进程句柄。
async function start(port, readyPath) {
    const server = spawn('python', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
        cwd: ROOT,
        stdio: 'ignore',
    });
    await waitUp(`http://127.0.0.1:${port}${readyPath || '/static/dist/ai.html'}`);
    return server;
}

function stop(server) {
    if (server) server.kill();
}

module.exports = { start, stop, ROOT };
