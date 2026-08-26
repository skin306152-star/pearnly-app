// Prettier 格式闸 · 基于 HEAD 已提交字节的全仓检查
//
// 为什么不用 `npm run format:check`(= prettier --check "**/*"):
//   它读工作树文件。Windows core.autocrlf=true 时检出 CRLF,prettier endOfLine:auto
//   虽接受任意行尾,但其他规则(如 printWidth)对 CRLF 内容的度量与 LF 不同,导致
//   本地绿 CI 红(或反过来)。本脚本从 git blob 读字节(LF),与工作树换行符无关。
//
// 为什么不只查本次改动文件(pre-push 旧做法):
//   本地只查 diff 而 CI 查全仓 → 两边口径不一致 → 漏网之鱼在 CI 才暴露。
//   统一为全仓检查后,本地 push 前就能拦截 CI 会报的红。
//
// 用法: node scripts/check_prettier_committed.mjs
// 退出码: 0 = 全仓格式合规 · 1 = 有文件未格式化(列表打到 stderr)
//
// 设计约束:
//   - 只读 HEAD 树(git ls-tree + git cat-file --batch),不碰工作树
//   - 尊重 .prettierignore(prettier.getFileInfo + ignorePath)
//   - 单次 Node 进程启动,批量处理(~1300 文件 < 15s)
//   - 零外部依赖(只用 prettier devDep + stdlib)

import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import prettier from 'prettier';

// ── 0. Prettier 版本漂移闸(fail-closed)────────────────────────
// 本机 npx 可能装了比 lockfile 更新的 prettier → 本地假绿 CI 真红(2026-08-27 实锤:
// 本机 3.9.6 vs lock 3.8.3,5 个文件本地过 CI 挂)。从 HEAD blob 读 lockfile 的
// 锁定版本(不读工作树,防未提交的 lock 改动干扰),与运行中 prettier.version 严格比对。
const lockBlob = execFileSync('git', ['show', 'HEAD:package-lock.json'], {
    encoding: 'utf8',
    maxBuffer: 10 * 1024 * 1024,
});
const lockJson = JSON.parse(lockBlob);
const expectedVersion = lockJson.packages?.['node_modules/prettier']?.version;
if (!expectedVersion) {
    process.stderr.write(
        '❌ 无法从 HEAD:package-lock.json 读取 prettier 锁定版本 · 请检查 lockfile 完整性\n'
    );
    process.exit(1);
}
if (prettier.version !== expectedVersion) {
    process.stderr.write(
        `❌ prettier 版本漂移: 运行中 ${prettier.version} ≠ 锁定 ${expectedVersion}\n` +
            `   本地与 CI 用不同版本 → 格式判断不一致 → 本地绿 CI 红。\n` +
            `   修法: npm ci(严格按 lockfile 重装)\n`
    );
    process.exit(1);
}

// ── 0b. Prettier 配置文件工作树漂移闸(fail-closed)──────────────
// 共享脚本从 HEAD blob 读文件内容,但 resolveConfig/getFileInfo 仍读工作树的
// .prettierrc.json/.prettierignore。若它们有未提交改动(如本地调了 tabWidth),
// 本地用新规则判绿、CI 干净检出用旧规则判红 → 又一种本地/CI 不一致。
// 校验:工作树文件字节必须与 HEAD blob 完全一致;不一致时 exit 1 提示先 commit 或恢复。
// CI 干净 checkout 自然通过(工作树 == HEAD)。
const CONFIG_FILES = ['.prettierrc.json', '.prettierignore'];
for (const cfg of CONFIG_FILES) {
    let headBytes;
    try {
        headBytes = execFileSync('git', ['show', `HEAD:${cfg}`], { maxBuffer: 1 * 1024 * 1024 });
    } catch {
        // HEAD 中没有此文件(如新建仓库)→ 跳过(工作树也没有则无影响;有则下面会检测到)
        continue;
    }
    let wtBytes;
    try {
        wtBytes = readFileSync(cfg);
    } catch {
        process.stderr.write(
            `❌ prettier 配置漂移: 工作树缺少 ${cfg}(HEAD 中有) · 请 git checkout -- ${cfg} 恢复\n`
        );
        process.exit(1);
    }
    if (!headBytes.equals(wtBytes)) {
        process.stderr.write(
            `❌ prettier 配置漂移: ${cfg} 工作树内容与 HEAD 不一致\n` +
                `   resolveConfig/getFileInfo 读工作树配置,脚本读 HEAD 文件内容 → 规则不匹配。\n` +
                `   修法: git add ${cfg} && git commit(让 HEAD 追上工作树)\n` +
                `         或 git checkout -- ${cfg}(让工作树回到 HEAD)\n`
        );
        process.exit(1);
    }
}

const EXT_RE = /\.(js|mjs|ts|css|html|json)$/;

// ── 1. 枚举 HEAD 树中所有匹配扩展名的文件 ──────────────────────
const lsTree = execFileSync('git', ['ls-tree', '-r', '--name-only', 'HEAD'], {
    encoding: 'utf8',
    maxBuffer: 50 * 1024 * 1024,
});
const candidates = lsTree
    .trim()
    .split('\n')
    .filter((f) => EXT_RE.test(f));

if (candidates.length === 0) {
    process.exit(0);
}

// ── 2. 过滤 .prettierignore ───────────────────────────────────
// fail-closed:getFileInfo 异常(如 .prettierignore 语法错/权限问题)不能静默跳过文件,
// 否则被跳过的文件永远不会被检查 → 闸报绿但实际有漏网之鱼。异常直接退出非零。
const fileInfoResults = await Promise.all(
    candidates.map(async (f) => {
        try {
            return await prettier.getFileInfo(f, { ignorePath: '.prettierignore' });
        } catch (err) {
            process.stderr.write(`❌ prettier.getFileInfo 异常(${f}): ${err?.message || err}\n`);
            process.exit(1);
        }
    })
);

const targets = [];
for (let i = 0; i < candidates.length; i++) {
    if (!fileInfoResults[i].ignored && fileInfoResults[i].inferredParser) {
        targets.push({ path: candidates[i], parser: fileInfoResults[i].inferredParser });
    }
}

if (targets.length === 0) {
    process.exit(0);
}

// ── 3. 批量读取 git blob 内容 ─────────────────────────────────
// git ls-tree -r HEAD 输出格式: <mode> <type> <sha>\t<path>
// 用 sha 通过 cat-file --batch 读取原始字节,避免逐文件 fork git show。
const lsTreeFull = execFileSync('git', ['ls-tree', '-r', 'HEAD'], {
    encoding: 'utf8',
    maxBuffer: 50 * 1024 * 1024,
});
const shaByPath = new Map();
for (const line of lsTreeFull.trim().split('\n')) {
    const tabIdx = line.indexOf('\t');
    if (tabIdx === -1) continue;
    const meta = line.slice(0, tabIdx); // "<mode> <type> <sha>"
    const filePath = line.slice(tabIdx + 1);
    const parts = meta.split(' ');
    if (parts.length >= 3) {
        shaByPath.set(filePath, parts[2]);
    }
}

// 用 cat-file --batch 批量读取:stdin 写 "<sha>\n",stdout 读 "<sha> blob <size>\n<data>"
const batchProc = spawnSync('git', ['cat-file', '--batch'], {
    input: targets.map((t) => shaByPath.get(t.path)).join('\n') + '\n',
    encoding: undefined, // raw Buffer
    maxBuffer: 200 * 1024 * 1024,
});

if (batchProc.status !== 0) {
    process.stderr.write(`git cat-file --batch failed: ${batchProc.stderr?.toString() || ''}\n`);
    process.exit(1);
}

const rawOutput = batchProc.stdout;
const contents = new Map();
let offset = 0;
for (const t of targets) {
    // header line: "<sha> blob <size>\n"
    const headerEnd = rawOutput.indexOf(0x0a, offset);
    if (headerEnd === -1) break;
    const header = rawOutput.slice(offset, headerEnd).toString('utf8');
    const sizeMatch = header.match(/blob (\d+)$/);
    if (!sizeMatch) {
        // missing object or other error line
        offset = headerEnd + 1;
        continue;
    }
    const size = parseInt(sizeMatch[1], 10);
    const dataStart = headerEnd + 1;
    const dataEnd = dataStart + size;
    contents.set(t.path, rawOutput.slice(dataStart, dataEnd));
    // skip trailing newline after blob data
    offset = dataEnd + 1;
}

// ── 4. Prettier check ────────────────────────────────────────
// resolveConfig 读 .prettierrc.json(含 overrides),内部有缓存,同目录文件不重复 IO。
// 不传 config 则 prettier 只用默认值(tabWidth=2 等),与项目实际规则不符 → 大量假红。
const failures = [];
const concurrency = 8;
let cursor = 0;

async function worker() {
    while (cursor < targets.length) {
        const idx = cursor++;
        const t = targets[idx];
        const buf = contents.get(t.path);
        if (!buf) continue;
        const source = buf.toString('utf8');
        try {
            const config = await prettier.resolveConfig(t.path);
            const ok = await prettier.check(source, { ...config, parser: t.parser });
            if (!ok) failures.push(t.path);
        } catch {
            failures.push(t.path);
        }
    }
}

await Promise.all(Array.from({ length: concurrency }, () => worker()));

// ── 5. 报告 ──────────────────────────────────────────────────
if (failures.length > 0) {
    failures.sort();
    process.stderr.write(
        `\n❌ prettier 格式不符(${failures.length} 个文件 · 基于 HEAD 已提交字节):\n`
    );
    for (const f of failures) {
        process.stderr.write(`  ${f}\n`);
    }
    process.stderr.write(`\n修法: npx prettier --write <file> 后重新 commit,再推。\n`);
    process.exit(1);
}
