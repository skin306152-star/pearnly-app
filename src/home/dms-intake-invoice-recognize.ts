// ============================================================
// 录入工作台 · 发票/收据识别机制(从 dms-intake-invoice.ts 抽出 · 控行数 <500)
//
// 同步老路(/api/ocr/recognize · 90s 超时 + 网络重试一次)与异步路(flag OCR_ASYNC_WEB
// 开 · /api/ocr/submit + _ocrPollJob 轮询)共用同一份错误码映射 / 成功落地逻辑。
// 共享状态 recState(本批去重/自动推送计数 + 当前 client_id)与在飞请求控制器 ctrls
// 由 startRecognize 起批时重置、结束后读取,故在此 export。
// ============================================================
/* global token, _userInfo */
import { authHeaders } from './dms-intake-core.js';
import { IV, w } from './dms-intake-invoice.js';
import type { Dict, IvFile, IvInvoice, IvResult } from './dms-intake-invoice.js';

// 在飞请求控制器集合(停止时一次性 abort · startRecognize/stopRecognize 共用)
export const ctrls = new Set<AbortController>();
// 一批识别的共享态:去重/自动推送计数 + 当前 client_id 归属(startRecognize 重置 + 读取)
export const recState = {
    dupWarn: [] as unknown[],
    autoPushed: 0,
    cidCache: null as unknown,
};

// 失败码 → 文件状态(同步/异步两路共用 · 同一 err.<code> i18n 词表 + 同 canRetry 判定)
function ocrErrCode(d: Dict): string {
    const detail = (d.detail as { code?: string } | string) || 'unknown';
    return typeof detail === 'string' ? detail : detail.code || 'unknown';
}
function setOcrError(f: IvFile, code: string) {
    f.status = 'error';
    f.errorKey = 'err.' + code;
    f.canRetry =
        !/file_too_large|too_many_pages|not_invoice|monthly_limit|need_api_key|not_pdf/.test(code);
}
// done 响应(同步 d / 异步 job.result 同形)落地为成功结果
function ingestOcrSuccess(f: IvFile, d: Dict) {
    f.status = 'success';
    f.canRetry = false;
    IV.results.push(ingestResult(d));
    if (((d.duplicate_warnings as unknown[]) || []).length)
        recState.dupWarn.push(...(d.duplicate_warnings as unknown[]));
    if (d.auto_pushed) recState.autoPushed++;
}

// 单张识别:AbortController + 90s 超时;网络/超时失败自动重试一次;用户停止则取消。
// flag OCR_ASYNC_WEB 开 → 走 submit + 轮询(无 90s 上限 · 后台 worker 跑 · 见 recognizeAsync)。
export async function recognizeOne(f: IvFile, isRetry: boolean) {
    f.status = isRetry ? 'retrying' : 'processing';
    if (_userInfo && _userInfo.ocr_async_web) return recognizeAsync(f);
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 90000);
    ctrls.add(ctrl);
    let netErr = false;
    try {
        const form = new FormData();
        form.append('file', f.file, f.name);
        if (recState.cidCache != null) form.append('client_id', String(recState.cidCache));
        const r = await fetch('/api/ocr/recognize', {
            method: 'POST',
            headers: authHeaders(),
            body: form,
            signal: ctrl.signal,
        });
        const d = (await r.json().catch(() => ({}))) as Dict;
        if (!r.ok) {
            setOcrError(f, ocrErrCode(d));
            return;
        }
        ingestOcrSuccess(f, d);
    } catch {
        netErr = true;
    } finally {
        clearTimeout(timer);
        ctrls.delete(ctrl);
    }
    if (netErr) {
        if (IV.aborted) {
            f.status = 'error';
            f.errorKey = 'status-cancelled';
            f.canRetry = false;
            return;
        }
        if (!isRetry) return recognizeOne(f, true); // 网络/超时 → 静默重试一次
        f.status = 'error';
        f.errorKey = 'dxi-recognize-fail';
        f.canRetry = true;
    }
}

// 异步分支:submit 秒回 job_id → _ocrPollJob 轮询到 done/failed → 成功落地或按码标错。
// 域失败(error_code 与同步 HTTP detail 同词表)走 setOcrError;传输失败(timeout/poll_unreachable)兜底可重试。
async function recognizeAsync(f: IvFile) {
    try {
        const form = new FormData();
        form.append('file', f.file, f.name);
        if (recState.cidCache != null) form.append('client_id', String(recState.cidCache));
        const sr = await fetch('/api/ocr/submit', {
            method: 'POST',
            headers: authHeaders(),
            body: form,
        });
        const sd = (await sr.json().catch(() => ({}))) as Dict;
        if (!sr.ok || !sd.job_id) {
            setOcrError(f, ocrErrCode(sd));
            return;
        }
        const job = await window._ocrPollJob(String(sd.job_id), token, {});
        if (job.status === 'done' && job.result) {
            ingestOcrSuccess(f, job.result as Dict);
            return;
        }
        if (IV.aborted) {
            f.status = 'error';
            f.errorKey = 'status-cancelled';
            f.canRetry = false;
            return;
        }
        if (job.error_code && !/poll_unreachable|timeout/.test(job.error_code)) {
            setOcrError(f, job.error_code);
        } else {
            f.status = 'error';
            f.errorKey = 'dxi-recognize-fail';
            f.canRetry = true;
        }
    } catch {
        f.status = 'error';
        f.errorKey = 'dxi-recognize-fail';
        f.canRetry = true;
    }
}

// 后端响应 → 复核用 IvResult(多发票 invoices[] 逐张;单票兜底 mergeFields)
function ingestResult(d: Dict): IvResult {
    const pages = (d.pages as unknown[]) || [];
    const raw = (d.invoices as Array<Record<string, unknown>>) || [];
    // 后端揪出的"发票号格式偏离多数派"张(1-based index)→ 标到对应票
    const fmtWarnIdx = new Set(
        ((d.invoice_format_warnings as Array<{ invoice_index?: number }>) || []).map(
            (w0) => w0.invoice_index
        )
    );
    const invoices: IvInvoice[] = raw.length
        ? raw.map((x, i) => ({
              fields: (x.fields as Dict) || {},
              history_id: (x.history_id as string) || null,
              idx: (x.source_index as number) || i + 1,
              total: (x.source_total as number) || raw.length,
              fmtWarn: fmtWarnIdx.has((x.source_index as number) || i + 1),
              pageIndices: (x.page_indices as number[]) || [],
          }))
        : [
              {
                  fields: w.mergeFields ? w.mergeFields(pages) : (pages[0] as Dict) || {},
                  history_id: (d.history_id as string) || null,
                  idx: 1,
                  total: 1,
              },
          ];
    return {
        filename: (d.filename as string) || '',
        invoices,
        history_ids: (d.history_ids as string[]) || (d.history_id ? [d.history_id as string] : []),
        invoice_count: (d.invoice_count as number) || invoices.length,
        needs_review:
            !!d.needs_review || ((d.missed_invoice_warnings as unknown[]) || []).length > 0,
        from_cache: !!d.from_cache,
    };
}
