// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 v2 结果渲染(汇总/明细/解析诊断/导出)· 从 bank-recon-v2.js 抽出
// verbatim 0 改逻辑。读 S.currentTask / S.allRows / S.currentFilter。
// ============================================================
import { S } from './bank-recon-v2-store.js';
import { $, fmtNum, fmtDate, esc2 } from './bank-recon-v2-helpers.js';
import { _brv2RenderAnchorAudit } from './bank-recon-v2-anchor.js';

// ── 显示/隐藏结果折叠区 ──────────────────────────────────────────
function showResultSections(show: boolean) {
    const sc = $('brv2-summary-collapse');
    const dc = $('brv2-detail-collapse');
    const eb = $('brv2-export-btn');
    const nb = $('brv2-new-btn');
    const pi = $('brv2-parse-info-wrap');
    if (sc) sc.style.display = show ? '' : 'none';
    if (dc) dc.style.display = show ? '' : 'none';
    if (eb) eb.style.display = show ? '' : 'none';
    if (nb) nb.style.display = show ? '' : 'none';
    if (!show && pi) pi.style.display = 'none';
    // v118.35.0.56 · 重置时一并清掉警告条(不匹配/跳过提示)· 防残留误导
    const wn = $('brv2-warnings');
    if (!show && wn) {
        wn.style.display = 'none';
        wn.innerHTML = '';
    }
}

// ── 文件解析诊断表 ────────────────────────────────────────────────
function renderParseInfo(data: any) {
    const wrap = $('brv2-parse-info-wrap');
    const body = $('brv2-parse-info-body');
    if (!wrap || !body) return;
    const pi = data.parse_info;
    if (!pi) {
        wrap.style.display = 'none';
        return;
    }

    const lang = window._currentLang || 'zh';
    const L = {
        title: {
            zh: '文件解析状态',
            th: 'สถานะการอ่านไฟล์',
            en: 'File Parse Status',
            ja: 'ファイル解析状態',
        },
        type: { zh: '类型', th: 'ประเภท', en: 'Type', ja: '種別' },
        file: { zh: '文件名', th: 'ชื่อไฟล์', en: 'File', ja: 'ファイル' },
        rows: { zh: '解析行数', th: 'แถวที่พบ', en: 'Rows Found', ja: '解析行数' },
        bank: { zh: '银行/科目', th: 'ธนาคาร/บัญชี', en: 'Bank/Account', ja: '銀行/科目' },
        status: { zh: '状态', th: 'สถานะ', en: 'Status', ja: '状態' },
        stmt: { zh: '账单', th: 'บัญชีธนาคาร', en: 'Stmt', ja: '明細' },
        gl: { zh: '总账GL', th: 'GL', en: 'GL', ja: 'GL' },
        ok: { zh: '✓ 成功', th: '✓ สำเร็จ', en: '✓ OK', ja: '✓ 成功' },
        warn: { zh: '⚠ 0行', th: '⚠ 0 แถว', en: '⚠ 0 rows', ja: '⚠ 0行' },
        fail: { zh: '✗ 失败', th: '✗ ล้มเหลว', en: '✗ Failed', ja: '✗ 失敗' },
    };
    const t = (k: keyof typeof L) =>
        ((L[k] as Record<string, string>) || {})[lang] ||
        ((L[k] as Record<string, string>) || {}).zh ||
        k;

    const rows = [
        ...(pi.stmt_files || []).map((f: any) => ({
            ...f,
            _type: 'stmt',
            _extra: f.bank_code || '',
        })),
        ...(pi.gl_files || []).map((f: any) => ({
            ...f,
            _type: 'gl',
            _extra: (f.accounts || []).join(', '),
        })),
    ];

    // v118.35.0.19 · 错误提示词翻译层:把后端 raw 技术错误翻译成用户能懂的话(4 语)
    const _ERR_MAP = {
        stmt_headers_not_found: {
            zh: '认不出表头列 · 请确认文件含日期/金额/余额列',
            th: 'หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ',
            en: 'Cannot detect column headers · ensure file has date/amount/balance columns',
            ja: '列ヘッダーが認識できません · 日付/金額/残高列を確認してください',
        },
        stmt_no_rows: {
            zh: '文件里没有交易数据 · 请确认上传了正确的银行流水',
            th: 'ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง',
            en: 'No transaction rows found · please check the file',
            ja: '取引データが見つかりません · ファイルを確認してください',
        },
        file_not_supported: {
            zh: '不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV',
            th: 'ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV',
            en: 'File type not supported · please upload PDF / image / Excel / CSV',
            ja: 'このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード',
        },
        file_unreadable: {
            zh: '文件无法读取 · 可能已损坏或被加密',
            th: 'อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส',
            en: 'File cannot be read · may be corrupted or encrypted',
            ja: 'ファイルを読み取れません · 破損または暗号化の可能性',
        },
        ocr_failed: {
            zh: '文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传',
            th: 'อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF',
            en: 'Could not read file · try a clearer version or upload as PDF',
            ja: '読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行',
        },
        gl_headers_not_found: {
            zh: '认不出总账表头 · 请确认文件含科目/借方/贷方列',
            th: 'หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต',
            en: 'Cannot detect GL column headers · ensure account/debit/credit columns exist',
            ja: 'GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください',
        },
    };
    // raw error → error_code 正则映射(后端老路径未带 code 时兜底)
    const _rawToCode = (raw: any) => {
        const r = String(raw || '');
        if (/Cannot detect bank statement column headers/i.test(r)) return 'stmt_headers_not_found';
        if (/Cannot detect GL column headers/i.test(r)) return 'gl_headers_not_found';
        if (/No transaction rows found|no pages parsed/i.test(r)) return 'stmt_no_rows';
        if (/unsupported format/i.test(r)) return 'file_not_supported';
        if (/Cannot read Excel|file_unreadable/i.test(r)) return 'file_unreadable';
        if (
            /Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(
                r
            )
        )
            return 'ocr_failed';
        return null;
    };
    const _humanizeReconError = (row: any) => {
        const code: keyof typeof _ERR_MAP = row.error_code || _rawToCode(row.error);
        if (code && _ERR_MAP[code]) {
            const lng = window._currentLang || 'zh';
            return _ERR_MAP[code][lng as 'zh'] || _ERR_MAP[code].zh;
        }
        // 无法翻译 → 用通用 + 截断 raw(供技术支持参考)
        return String(row.error || '').slice(0, 80);
    };

    const statusCell = (row: any) => {
        if (!row.ok && row.error)
            return `<span style="color:#dc2626">${t('fail')} — ${esc2(_humanizeReconError(row))}</span>`;
        if (!row.rows) return `<span style="color:#d97706">${t('warn')}</span>`;
        return `<span style="color:#059669">${t('ok')} (${row.rows})</span>`;
    };

    body.innerHTML = `
        <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${t('title')}</div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
            <thead>
                <tr style="background:#f3f4f6;font-weight:600">
                    <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('type')}</th>
                    <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${t('file')}</th>
                    <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${t('rows')}</th>
                    <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('bank')}</th>
                    <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('status')}</th>
                </tr>
            </thead>
            <tbody>
                ${rows
                    .map(
                        (row) => `<tr>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${row._type === 'stmt' ? t('stmt') : t('gl')}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc2(row.file || '')}">${esc2(row.file || '')}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${row.rows || 0}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${esc2(row._extra || '')}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb">${statusCell(row)}</td>
                </tr>`
                    )
                    .join('')}
            </tbody>
        </table>`;
    wrap.style.display = '';
}

// ── Export helper (fetch+blob so Auth header is sent) ─────────────
async function _brv2Export(taskId: any) {
    const token = localStorage.getItem('mrpilot_token') || '';
    const l = window._currentLang || 'zh';
    try {
        const resp = await fetch('/api/recon/bank-v2/' + taskId + '/export?lang=' + l, {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            if (window.showToast) window.showToast(err.detail || 'Export failed', 'error');
            return;
        }
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') || '';
        const m = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const filename = m ? m[1].replace(/['"]/g, '') : 'reconciliation.xlsx';
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        if (window.showToast) window.showToast('Export error: ' + (e as Error).message, 'error');
    }
}

// ── Render results ────────────────────────────────────────────────
// v118.35.0.54 · 输入不匹配 / 跳过文件 警告条(期间/规模对不上 · 不让用户看不懂差额)
function _brv2RenderWarnings(warnings: any, skipped: any) {
    const host = $('brv2-summary-collapse');
    let box = $('brv2-warnings');
    const _l = window._currentLang || 'zh';
    const skipLbl =
        {
            zh: '⏭ 已跳过无法识别的文件:',
            th: '⏭ ข้ามไฟล์ที่อ่านไม่ได้:',
            en: '⏭ Skipped unreadable file:',
            ja: '⏭ 読み取れないファイルをスキップ:',
        }[_l] || '⏭ ';
    const msgs: string[] = [];
    (skipped || []).forEach((fn: any) => msgs.push(skipLbl + ' ' + fn));
    (warnings || []).forEach((w: any) => msgs.push(w));
    if (!msgs.length) {
        if (box) box.style.display = 'none';
        return;
    }
    if (!box) {
        box = document.createElement('div');
        box.id = 'brv2-warnings';
        if (host && host.parentNode) host.parentNode.insertBefore(box, host);
        else return;
    }
    box.style.cssText =
        'display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;' +
        'border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6';
    box.innerHTML = msgs.map((m) => '<div>' + esc2(m) + '</div>').join('');
}

function renderResults(data: any) {
    // Always render parse diagnostics (shown on both success and failure)
    renderParseInfo(data);
    // v118.35.0.54 · 输入不匹配 / 跳过文件 警告条
    _brv2RenderWarnings(data.warnings || [], data.skipped_files || []);

    // If parse failed, show error toast but still display the diagnostics panel
    if (!data.ok && data.error) {
        if (window.showToast) window.showToast(data.error, 'error');
    }

    const stats = data.stats || {};
    const summary = data.summary || {};

    const matched = stats.matched || 0;
    const glOnly = (stats.gl_debit_only || 0) + (stats.gl_credit_only || 0);
    const stmtOnly = (stats.stmt_withdrawal_only || 0) + (stats.stmt_deposit_only || 0);
    const fdiff = Number(summary.formula_diff || 0);
    const diffOk = Math.abs(fdiff) < 0.05;

    // KPI strip (3 cards)
    if ($('brv2-kpi-matched')) $('brv2-kpi-matched')!.textContent = matched;
    if ($('brv2-kpi-diff')) $('brv2-kpi-diff')!.textContent = fmtNum(fdiff);
    if ($('brv2-kpi-unmatched')) $('brv2-kpi-unmatched')!.textContent = glOnly + stmtOnly;
    // 差额图标颜色
    const diffIcon = $('brv2-kpi-diff-icon');
    if (diffIcon) {
        diffIcon.style.background = diffOk ? '#d1fae5' : '#fee2e2';
        diffIcon.style.color = diffOk ? '#065f46' : '#b91c1c';
    }

    // Formula collapse 小标题
    const formulaSub = $('brv2-formula-sub');
    if (formulaSub) {
        const _fl = window._currentLang || 'zh';
        formulaSub.textContent = diffOk
            ? { zh: '✓ 平衡', th: '✓ สมดุล', en: '✓ Balanced', ja: '✓ 一致' }[_fl] || '✓ 平衡'
            : ({ zh: '差 ', th: 'ต่าง ', en: 'Diff ', ja: '差 ' }[_fl] || '差 ') + fmtNum(fdiff);
    }

    // Detail collapse 小标题
    const detailSub = $('brv2-detail-sub');
    if (detailSub) {
        const _dl = window._currentLang || 'zh';
        const _rowLbl =
            { zh: '共 {n} 行', th: 'ทั้งหมด {n} แถว', en: '{n} rows', ja: '計 {n} 行' }[_dl] ||
            '共 {n} 行';
        detailSub.textContent = _rowLbl.replace('{n}', S.allRows.length as unknown as string);
    }

    // 公式表
    function setFrm(id: any, val: any, neg?: any) {
        const el = $(id);
        if (!el) return;
        el.textContent =
            (neg && val > 0 ? '(' : '') + fmtNum(neg ? -val : val) + (neg && val > 0 ? ')' : '');
    }
    setFrm('brf-gl-close', summary.gl_closing || 0);
    setFrm('brf-open-diff', summary.opening_diff || 0);
    setFrm('brf-gl-debit-only', summary.gl_debit_only_amount || 0, true);
    setFrm('brf-gl-credit-only', summary.gl_credit_only_amount || 0);
    setFrm('brf-stmt-wd-only', summary.stmt_withdrawal_only_amount || 0, true);
    setFrm('brf-stmt-dep-only', summary.stmt_deposit_only_amount || 0);
    setFrm('brf-calc-close', summary.formula_stmt_closing || 0);
    setFrm('brf-stmt-close', summary.stmt_closing || 0);
    if ($('brf-diff')) {
        $('brf-diff')!.textContent = fmtNum(fdiff);
    }

    // 差额卡片颜色 (v118.33.12.0 · 横向公式卡片)
    const diffCell = $('brv2-fcell-diff');
    if (diffCell) {
        diffCell.classList.toggle('brv2-fcell-diff-ok', diffOk);
    }

    // 导出按钮事件
    const exportBtn = $('brv2-export-btn');
    if (exportBtn) {
        exportBtn.onclick = () => {
            if (!S.currentTask) return;
            _brv2Export((S.currentTask as any).task_id);
        };
    }

    // P0.3 BUG-B-T3 v118.35.0.39 · 渲染 anchor 手动录入对照(只在 summary._anchor_overrides 非空时显示)
    _brv2RenderAnchorAudit(summary);

    showResultSections(true);
    renderTable();
}

function renderTable() {
    const tbody = $('brv2-tbody');
    if (!tbody) return;

    const rows = (S.allRows as any[]).filter((r) => {
        if (S.currentFilter === 'all') return true;
        if (S.currentFilter === 'matched') return r.match_status === 'matched';
        if (S.currentFilter === 'gl_only') return r.match_status.startsWith('gl_');
        if (S.currentFilter === 'stmt_only') return r.match_status.startsWith('stmt_');
        return true;
    });

    if (rows.length === 0) {
        const noRows =
            { zh: '无记录', th: 'ไม่มีรายการ', en: 'No rows', ja: '行なし' }[
                window._currentLang || 'zh'
            ] || '无记录';
        tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${noRows}</td></tr>`;
        return;
    }

    const _lang2 = window._currentLang || 'zh';
    const T_OCR_WARN_BAL = {
        zh: 'OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF',
        th: 'การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ',
        en: 'Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF',
        ja: '残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください',
    }[_lang2];
    const T_OCR_LOW_CONF = {
        zh: 'OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF',
        th: 'OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ',
        en: 'OCR low confidence · digit was blurry or hard to read — verify against the original PDF',
        ja: 'OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください',
    }[_lang2];

    tbody.innerHTML = rows
        .map((r) => {
            const st = r.match_status;
            const layer = r.match_layer;

            let rowClass = '';
            let badge = '';
            if (st === 'matched') {
                if (layer === 1) {
                    rowClass = 'matched';
                    badge = '<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>';
                }
                if (layer === 2) {
                    rowClass = 'matched-l2';
                    badge = '<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>';
                }
                if (layer === 3) {
                    rowClass = 'matched-l3';
                    badge = '<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>';
                }
            } else if (st === 'gl_debit_only' || st === 'gl_credit_only') {
                rowClass = 'gl-only';
                badge = '<span class="brv2-status-badge brv2-badge-gl-only">GL</span>';
            } else {
                rowClass = 'stmt-only';
                const stmtLbl =
                    { zh: '账单', th: 'บัญชี', en: 'Stmt', ja: '明細' }[_lang2] || '账单';
                badge = `<span class="brv2-status-badge brv2-badge-stmt-only">${stmtLbl}</span>`;
            }

            // v118.33.13.0 · OCR accuracy warning icons (balance check, confidence)
            let warnIcons = '';
            if (r.stmt_balance_ok === false) {
                warnIcons += `<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${esc2(T_OCR_WARN_BAL)}">⚠</span>`;
                rowClass += ' brv2-row-warn';
            }
            if (r.stmt_confidence === 'low') {
                warnIcons += `<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${esc2(T_OCR_LOW_CONF)}">◌</span>`;
                if (!rowClass.includes('brv2-row-warn')) rowClass += ' brv2-row-warn-soft';
            }

            return `<tr class="${rowClass.trim()}">
          <td>${badge}${warnIcons}</td>
          <td>${esc2(fmtDate(r.stmt_date))}</td>
          <td title="${esc2(r.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc2(r.stmt_desc)}</td>
          <td class="num">${r.stmt_withdrawal ? fmtNum(r.stmt_withdrawal) : ''}</td>
          <td class="num">${r.stmt_deposit ? fmtNum(r.stmt_deposit) : ''}</td>
          <td>${esc2(fmtDate(r.gl_date))}</td>
          <td title="${esc2(r.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc2(r.gl_doc_no)}</td>
          <td class="num">${r.gl_debit ? fmtNum(r.gl_debit) : ''}</td>
          <td class="num">${r.gl_credit ? fmtNum(r.gl_credit) : ''}</td>
          <td>${layer ? 'L' + layer : '—'}</td>
        </tr>`;
        })
        .join('');
}

export { showResultSections, renderResults, renderTable, _brv2Export };
