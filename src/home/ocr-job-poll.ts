// ============================================================
// 缺口④ · 网页 OCR 异步任务前端轮询 _ocrPollJob
//
// submit 秒回 job_id → 轮询 GET /api/ocr/jobs/{id} 到 done/failed → 调用方拿 job.result
// (同形 recognize 响应)直接 ingestResult 渲染。镜像 recon-job-poll 的容错策略:
// 瞬时网络/网关错误容忍重试,只在超时或真失败才停。OCR 终态只有 done/failed
// (不像对账有 needs_review/needs_mapping)。
//
// 暴露 window._ocrPollJob(被 dms-intake-invoice / folder-watcher 经 window. 运行期调)。
// flag OCR_ASYNC_WEB 关时前端不会调用本工具(走同步老路)。
// ============================================================
/* eslint-disable no-useless-assignment -- 防御式初始化 `let job = null`,与 recon-job-poll 同范式 */
(function () {
    'use strict';
    // 轮询任务到 done/failed · 返回最终 job(或 {status:'timeout'/'failed'})。onProgress(progress, job) 每轮回调。
    window._ocrPollJob = async function (jobId, token, opts) {
        opts = opts || {};
        const intervalMs = opts.intervalMs || 1500;
        const maxMs = opts.maxMs || 20 * 60 * 1000; // 20 分钟硬上限(同 recon)
        const start = Date.now();
        let softFails = 0;
        for (;;) {
            let job = null;
            try {
                const r = await fetch('/api/ocr/jobs/' + encodeURIComponent(jobId), {
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
                if (job.status === 'done' || job.status === 'failed') return job;
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
