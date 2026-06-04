// ============================================================
// REFACTOR-C1 (2026-05-27) · 对账异步任务前端轮询工具 recon-job-poll 从 home.js 抽出为 ES module
//
// 来源:home.js L6765-6830 · verbatim 0 改逻辑(仅 prettier 重排)。
// 暴露 window._reconPollJob / window._reconProgressText(被 bank-recon-v2 经 window. 运行期调用)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* eslint-disable no-useless-assignment -- verbatim 防御式初始化 `let job = null` 从 home.js 原样搬来 · 0 改逻辑 */

/* ============================================================
 * BUG-FIX-RECON-ASYNC #16 · 对账异步任务前端共用工具(三对账共用)
 * submit 秒回 job_id → 轮询 GET /api/recon/jobs/{id} 到 done/failed →
 * 用 result_id 调现有结果接口渲染。瞬时网络/网关错误容忍重试,只在超时/失败才停。
 * ⚠️ 暂塞 home.js(全局 window 工具 · 三个 recon IIFE 共用)· 迁出 deadline = REFACTOR-C1
 *    拆 home.js 时一并搬到 src/home/recon/job-poll.js(整顿期 C 阶段)。
 * ============================================================ */
(function () {
    'use strict';
    const _STAGE_LBL: Record<string, Record<string, string>> = {
        parse: { zh: '解析文件中', th: 'กำลังอ่านไฟล์', en: 'Parsing files', ja: 'ファイル解析中' },
        report: {
            zh: '读取报告中',
            th: 'กำลังอ่านรายงาน',
            en: 'Reading report',
            ja: 'レポート読込中',
        },
        reconcile: { zh: '对账中', th: 'กำลังกระทบยอด', en: 'Reconciling', ja: '照合中' },
        build: { zh: '生成中', th: 'กำลังสร้างไฟล์', en: 'Building', ja: '作成中' },
        persist: { zh: '保存中', th: 'กำลังบันทึก', en: 'Saving', ja: '保存中' },
        done: { zh: '完成', th: 'เสร็จสิ้น', en: 'Done', ja: '完了' },
    };
    // 「转圈处理中」旁的实时进度文案 · parse 阶段显示「共 X/Y 个文件」(Zihao 拍板:不加进度条)
    window._reconProgressText = function (progress, lang) {
        progress = progress || {};
        // 2026-05-24 修:旧版默认 zh + 调用方传的是启动时捕获的 lang → 泰语界面进度副文案显示中文。
        //   改为实时优先读当前 UI 语言 · 默认 th(首发市场)· 非法值兜底 th。
        lang = window._currentLang || lang || localStorage.getItem('mrpilot_lang') || 'th';
        if (!_STAGE_LBL.parse[lang]) lang = 'th';
        const stage = progress.stage || 'parse';
        const lbl = _STAGE_LBL[stage] || _STAGE_LBL.parse;
        const label = lbl[lang] || lbl.th || lbl.en;
        const total = progress.stage_total,
            done = progress.stage_done;
        if (stage === 'parse' && typeof total === 'number' && total > 0) {
            const cntL: string =
                (
                    {
                        zh: '共 {d}/{t} 个文件',
                        th: '{d}/{t} ไฟล์',
                        en: '{d}/{t} files',
                        ja: '{d}/{t} ファイル',
                    } as Record<string, string>
                )[lang] || '{d}/{t} files';
            return (
                label + ' · ' + cntL.replace('{d}', String(done || 0)).replace('{t}', String(total))
            );
        }
        return label;
    };
    // 轮询任务到 done/failed · 返回最终 job(或 {status:'timeout'})。onProgress(progress, job) 每轮回调。
    window._reconPollJob = async function (jobId, token, opts) {
        opts = opts || {};
        const intervalMs = opts.intervalMs || 1500;
        const maxMs = opts.maxMs || 20 * 60 * 1000; // 20 分钟硬上限
        const start = Date.now();
        let softFails = 0;
        for (;;) {
            let job = null;
            try {
                const r = await fetch('/api/recon/jobs/' + encodeURIComponent(jobId), {
                    headers: { Authorization: 'Bearer ' + token },
                });
                try {
                    job = await r.json();
                } catch (_) {
                    job = null;
                }
                if (!r.ok || !job || !job.ok) {
                    job = null;
                }
            } catch (_) {
                job = null;
            }
            if (job) {
                softFails = 0;
                if (opts.onProgress) {
                    try {
                        opts.onProgress(job.progress || {}, job);
                    } catch (_) {}
                }
                // S8 · needs_review 也终止轮询 · 交调用方弹逐行核对面板
                // BUG-FIX-RECON-GLCSV · needs_mapping 也终止轮询 · 交调用方弹『确认列对应』面板
                if (
                    job.status === 'done' ||
                    job.status === 'failed' ||
                    job.status === 'needs_review' ||
                    job.status === 'needs_mapping'
                )
                    return job;
            } else {
                // 瞬时错误容忍 · 连续 10 次(~15s)拿不到才放弃
                if (++softFails >= 10)
                    return { ok: false, status: 'failed', error_code: 'poll_unreachable' };
            }
            if (Date.now() - start > maxMs)
                return { ok: false, status: 'timeout', error_code: 'timeout' };
            await new Promise((res) => setTimeout(res, intervalMs));
        }
    };
})();
