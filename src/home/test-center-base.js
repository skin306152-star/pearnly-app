// ============================================================
// REFACTOR-WB-modularize · 测试中心(skin-only)数据 + 状态 store + 工具 + markdown 导出 从 IIFE 中心化
// ============================================================
// ---------- 配置 ----------
const VERSION = 'v118.28.5';
const LS_RESULTS = 'pearnly_tc_results_' + VERSION;

// 测试账号 user_id 白名单(skin OAuth · 详见 STATE_PEARNLY.md 账号分工)
const ALLOWED_USER_IDS = [
    '468b50c1-5593-4fd6-990d-515ce8085563', // skin306152@gmail.com Google OAuth
];

// ---------- v118.28.5.2 测试清单 ----------
const CHECKLIST = [
    // A · 异常栏 page-head 修复(BUG 1)
    {
        id: 'A1',
        group: 'A · 异常栏 page-head(BUG1)',
        desc: '手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行',
    },
    {
        id: 'A2',
        group: 'A · 异常栏 page-head(BUG1)',
        desc: '副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排',
    },
    {
        id: 'A3',
        group: 'A · 异常栏 page-head(BUG1)',
        desc: '客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度',
    },
    // B · 客户管理 page-head 修复(BUG 2)
    {
        id: 'B1',
        group: 'B · 客户管理 page-head(BUG2)',
        desc: '手机宽度进客户管理 · 标题「客户管理」横排正常',
    },
    {
        id: 'B2',
        group: 'B · 客户管理 page-head(BUG2)',
        desc: '副标题「为每家客户单独归档发票…」横排正常 · 不竖排',
    },
    {
        id: 'B3',
        group: 'B · 客户管理 page-head(BUG2)',
        desc: '「+ 新建客户」按钮换到新一行 · 不挤标题',
    },
    // C · 客户卡片(BUG 3)
    {
        id: 'C1',
        group: 'C · 客户卡片(BUG3)',
        desc: '客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断',
    },
    // D · 历史发票表头(BUG 4)
    {
        id: 'D1',
        group: 'D · 历史表头(BUG4)',
        desc: '手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排',
    },
    {
        id: 'D2',
        group: 'D · 历史表头(BUG4)',
        desc: '行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行',
    },
    // E · 对账客户切换器(BUG 6)
    {
        id: 'E1',
        group: 'E · 对账切换器(BUG6)',
        desc: '手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边',
    },
    { id: 'E2', group: 'E · 对账切换器(BUG6)', desc: '下拉宽度自适应屏幕 · 不超出屏幕右边' },
    // F · 通用设置(本版含 v28.5.1 全部内容 · 顺手回归)
    { id: 'F1', group: 'F · 通用设置回归', desc: '设置 → 个人资料 · 没有「界面语言」4 按钮卡' },
    {
        id: 'F2',
        group: 'F · 通用设置回归',
        desc: '左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于',
    },
    {
        id: 'F3',
        group: 'F · 通用设置回归',
        desc: '系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留',
    },
    // G · 移动端 settings tabs(v28.5.1 chip 风格)
    {
        id: 'G1',
        group: 'G · 移动端 settings(回归)',
        desc: '手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格',
    },
    // H · 现网功能不破
    {
        id: 'H1',
        group: 'H · 回归',
        desc: 'OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作',
    },
    {
        id: 'H2',
        group: 'H · 回归',
        desc: '4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)',
    },
    // I · 三档 viewport
    { id: 'I1', group: 'I · 三档移动 viewport', desc: 'iPhone SE 375 · 上述 BUG 1-6 都修了' },
    { id: 'I2', group: 'I · 三档移动 viewport', desc: 'Galaxy S 360 · 上述 BUG 1-6 都修了' },
    {
        id: 'I3',
        group: 'I · 三档移动 viewport',
        desc: 'iPhone 12 Pro 414 · 上述 BUG 1-6 都修了',
    },
];

export const S = {
    results: {}, // { 'A1': 'pass'|'fail'|'skip', ... }
    logFilter: 'all',
    bound: false,
    renderScheduled: false,
    checkN: 0,
};

function _t(key, fallback, vars) {
    let s = typeof t === 'function' ? t(key) : null;
    if (!s || s === key) s = fallback;
    if (vars)
        Object.keys(vars).forEach(function (k) {
            s = String(s).replace('{' + k + '}', String(vars[k]));
        });
    return s;
}

function _loadResults() {
    try {
        const raw = localStorage.getItem(LS_RESULTS);
        S.results = raw ? JSON.parse(raw) : {};
        if (typeof S.results !== 'object' || !S.results) S.results = {};
    } catch (_) {
        S.results = {};
    }
}
function _saveResults() {
    try {
        localStorage.setItem(LS_RESULTS, JSON.stringify(S.results));
    } catch (_) {
        /* silent · localStorage 私模/配额 */
    }
}

function _fmtTime(ts) {
    const d = new Date(ts);
    const pad = function (n) {
        return n < 10 ? '0' + n : '' + n;
    };
    return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
}

function _esc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function _toast(msg, type) {
    try {
        if (typeof showToast === 'function') showToast(msg, type || 'info');
        else alert(msg);
    } catch (_) {
        /* silent · toast 失败兜 alert 也失败 · 外层吞 */
    }
}

function _copyToClipboard(text) {
    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard
                .writeText(text)
                .then(function () {
                    _toast(_t('tc-toast-copied', '已复制到剪贴板'), 'success');
                })
                .catch(function () {
                    _fallbackCopy(text);
                });
        } else {
            _fallbackCopy(text);
        }
    } catch (_) {
        _fallbackCopy(text);
    }
}
function _fallbackCopy(text) {
    try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(ta);
        _toast(
            ok ? _t('tc-toast-copied', '已复制') : _t('tc-toast-copy-fail', '复制失败'),
            ok ? 'success' : 'error'
        );
    } catch (_) {
        _toast(_t('tc-toast-copy-fail', '复制失败'), 'error');
    }
}

// ---------- 复制 markdown ----------
function _buildResultsMarkdown() {
    const lines = [];
    const now = new Date();
    const acct = (_userInfo && (_userInfo.email || _userInfo.username)) || '—';
    lines.push('# Pearnly ' + VERSION + ' 测试结果');
    lines.push('- 账号:' + acct);
    lines.push('- 时间:' + now.toISOString().replace('T', ' ').slice(0, 19));
    const total = CHECKLIST.length;
    const pass = CHECKLIST.filter(function (it) {
        return S.results[it.id] === 'pass';
    }).length;
    const fail = CHECKLIST.filter(function (it) {
        return S.results[it.id] === 'fail';
    }).length;
    const skip = CHECKLIST.filter(function (it) {
        return S.results[it.id] === 'skip';
    }).length;
    const undone = total - pass - fail - skip;
    lines.push(
        '- 进度:' +
            (pass + fail + skip) +
            ' / ' +
            total +
            ' · ✅ ' +
            pass +
            ' · ❌ ' +
            fail +
            ' · ⏭ ' +
            skip +
            ' · 未测 ' +
            undone
    );
    lines.push('');
    lines.push('| ID | 描述 | 状态 |');
    lines.push('|---|---|---|');
    CHECKLIST.forEach(function (it) {
        const st = S.results[it.id];
        const sym = st === 'pass' ? '✅' : st === 'fail' ? '❌' : st === 'skip' ? '⏭' : '⬜';
        lines.push('| ' + it.id + ' | ' + it.desc.replace(/\|/g, '\\|') + ' | ' + sym + ' |');
    });
    // 失败项重点
    const fails = CHECKLIST.filter(function (it) {
        return S.results[it.id] === 'fail';
    });
    if (fails.length > 0) {
        lines.push('');
        lines.push('## ❌ 失败项');
        fails.forEach(function (it) {
            lines.push('- **' + it.id + '** · ' + it.desc);
        });
    }
    // 异常日志最近 30 条
    const logs = (window._pearnlyTcLogs || []).slice(-30).reverse();
    if (logs.length > 0) {
        lines.push('');
        lines.push('## 🔴 异常日志(最近 ' + logs.length + ' 条)');
        logs.forEach(function (e) {
            lines.push('- `' + _fmtTime(e.ts) + '` · **' + e.type + '** · ' + e.summary);
            if (e.detail) {
                let d;
                try {
                    d = JSON.stringify(e.detail);
                } catch (_) {
                    d = String(e.detail);
                }
                if (d && d !== '{}') lines.push('  - ' + d.slice(0, 600));
            }
        });
    }
    return lines.join('\n');
}
function _buildLogsMarkdown(limit) {
    const logs = (window._pearnlyTcLogs || []).slice(-limit).reverse();
    if (logs.length === 0) return '(暂无异常日志)';
    const lines = ['# Pearnly 异常日志(最近 ' + logs.length + ' 条)'];
    const acct = (_userInfo && (_userInfo.email || _userInfo.username)) || '—';
    lines.push('- 账号:' + acct);
    lines.push('- 当前页:' + (currentRoute || '?'));
    lines.push('- UA:' + navigator.userAgent);
    lines.push('');
    logs.forEach(function (e) {
        lines.push('## `' + _fmtTime(e.ts) + '` · ' + e.type);
        lines.push('- ' + e.summary);
        if (e.detail) {
            lines.push('```');
            try {
                lines.push(JSON.stringify(e.detail, null, 2).slice(0, 2000));
            } catch (_) {
                lines.push(String(e.detail).slice(0, 2000));
            }
            lines.push('```');
        }
    });
    return lines.join('\n');
}

export {
    VERSION,
    LS_RESULTS,
    ALLOWED_USER_IDS,
    CHECKLIST,
    _t,
    _loadResults,
    _saveResults,
    _fmtTime,
    _esc,
    _toast,
    _copyToClipboard,
    _buildResultsMarkdown,
    _buildLogsMarkdown,
};
