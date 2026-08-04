/*
 * Pearnly AI · ai-steward-md.js · 管家正文的迷你 markdown 渲染(S1 会话流改版)
 *
 * 只覆盖管家回复真实会出现的形状:### 标题 / - 列表 / | 表格 | / ```代码块``` /
 * **粗体** / `行内码` / 段落(单换行折 <br>)。不是通用 markdown 引擎 —— 语法面越大,
 * 注入面越大;所有文本先过 esc 再套标记,后端回复里的 <script> 永远是字面量。
 *
 * 表格数字列右对齐:首行数据以 ฿ 或数字开头的列标 num(会计看金额列必须右对齐,
 * 同 ai-body 表格约定);表格整体包一层横滚容器,页面本体永不出横向滚动条。
 *
 * 纯函数零 DOM 零 i18n:node(tests/unit/test_ai_steward_md.py)直接 require 断言。
 */
(function (root) {
    'use strict';

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function inline(s) {
        return esc(s)
            .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
            .replace(/`([^`]+)`/g, '<code>$1</code>');
    }

    // 整格都得像个数(可带 ฿/负号/千分位/百分号)才算数字列 —— 只看首字符会把
    // 「7-Eleven」这类以数字开头的商户名也右对齐(实测踩过)。
    function isNum(v) {
        return /^[฿-]?[\d,.]+%?$/.test(v) && /\d/.test(v);
    }

    function tableHtml(rows) {
        var cells = rows
            .map(function (r) {
                return r
                    .replace(/^\||\|$/g, '')
                    .split('|')
                    .map(function (c) {
                        return c.trim();
                    });
            })
            .filter(function (r) {
                // 分隔行(|---|---|)不是数据。
                return !/^[-\s|:]+$/.test(r.join(''));
            });
        if (!cells.length) return '';
        var head =
            '<tr>' +
            cells[0]
                .map(function (c, i) {
                    var num = cells.length > 1 && cells[1][i] != null && isNum(cells[1][i]);
                    return '<th' + (num ? ' class="num"' : '') + '>' + inline(c) + '</th>';
                })
                .join('') +
            '</tr>';
        var body = cells
            .slice(1)
            .map(function (r) {
                return (
                    '<tr>' +
                    r
                        .map(function (c) {
                            return (
                                '<td' + (isNum(c) ? ' class="num"' : '') + '>' + inline(c) + '</td>'
                            );
                        })
                        .join('') +
                    '</tr>'
                );
            })
            .join('');
        return (
            '<div class="stw-md-tblwrap"><table><thead>' +
            head +
            '</thead><tbody>' +
            body +
            '</tbody></table></div>'
        );
    }

    // opts.codeCopyLabel:代码块「复制」按钮文字(i18n 归调用方,本层零词典)。
    // 不传就不摆按钮 —— 摆一颗没字的按钮比没有更糟。
    function render(src, opts) {
        var copyLabel = (opts && opts.codeCopyLabel) || '';
        var lines = String(src == null ? '' : src).split('\n');
        var html = '';
        var i = 0;
        while (i < lines.length) {
            var line = lines[i];
            if (/^```/.test(line)) {
                var j = i + 1;
                var buf = [];
                while (j < lines.length && !/^```/.test(lines[j])) {
                    buf.push(lines[j]);
                    j += 1;
                }
                var copyBtn = copyLabel
                    ? '<button type="button" class="stw-linkbtn" data-action="stw-copy-md-code">' +
                      esc(copyLabel) +
                      '</button>'
                    : '';
                html +=
                    '<div class="stw-md-code"><div class="stw-md-code-hd"><span>' +
                    esc(line.slice(3) || 'text') +
                    '</span>' +
                    copyBtn +
                    '</div><pre>' +
                    esc(buf.join('\n')) +
                    '</pre></div>';
                i = j + 1;
                continue;
            }
            if (/^###\s/.test(line)) {
                html += '<h4>' + inline(line.slice(4)) + '</h4>';
                i += 1;
                continue;
            }
            if (/^\|/.test(line)) {
                var k = i;
                var rows = [];
                while (k < lines.length && /^\|/.test(lines[k])) {
                    rows.push(lines[k]);
                    k += 1;
                }
                html += tableHtml(rows);
                i = k;
                continue;
            }
            if (/^- /.test(line)) {
                var m = i;
                var items = [];
                while (m < lines.length && /^- /.test(lines[m])) {
                    items.push(lines[m].slice(2));
                    m += 1;
                }
                html +=
                    '<ul>' +
                    items
                        .map(function (x) {
                            return '<li>' + inline(x) + '</li>';
                        })
                        .join('') +
                    '</ul>';
                i = m;
                continue;
            }
            if (!line.trim()) {
                i += 1;
                continue;
            }
            var p = i;
            var pbuf = [];
            while (p < lines.length && lines[p].trim() && !/^(\||###\s|- |```)/.test(lines[p])) {
                pbuf.push(lines[p]);
                p += 1;
            }
            html += '<p>' + pbuf.map(inline).join('<br>') + '</p>';
            i = p;
        }
        return html;
    }

    var api = { render: render, inline: inline, esc: esc, isNum: isNum };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.stewardMd = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
