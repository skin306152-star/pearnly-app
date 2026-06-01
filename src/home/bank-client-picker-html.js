// ============================================================
// REFACTOR-WB-C3 (2026-06-01) · 银行对账 session 客户绑定弹窗 inner 从 home.html 抽出 · 运行期注入
//
// home.html 留空壳 <div id="bank-client-picker-modal">(modal-overlay · display:none)· 本模块 eval 时注入 inner。
// bank-recon.js(main.js 内 import 在本模块之后)bindEvents()(load() 按需·automation bank tab 点击触发)才绑
// [data-bank-client-picker-close]/btn-bank-client-picker-save · eval 注入恒早于首次 load · import 置 bank-recon.js 前。
// i18n:注入后子树补译 · verbatim inner · 0 改结构。
// ============================================================
import { wbInject } from './wb-inject.js';

const HTML = `
    <div class="modal" style="max-width: 420px;">
        <div class="modal-head">
            <div class="modal-title" data-i18n="bank-client-picker-title">绑定客户</div>
            <button class="modal-close" data-bank-client-picker-close aria-label="close">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
            </button>
        </div>
        <div class="modal-body">
            <div class="bank-client-picker-hint" data-i18n="bank-client-picker-hint">把这份对账绑定到客户后 · 只有分到该客户的员工能看见 / 操作</div>
            <div class="bank-client-picker-list" id="bank-client-picker-list">
                <div class="bank-empty" data-i18n="assign-loading">加载中…</div>
            </div>
        </div>
        <div class="modal-foot">
            <button class="btn btn-ghost btn-small" data-bank-client-picker-close>
                <span data-i18n="assign-cancel">取消</span>
            </button>
            <button class="btn btn-primary btn-small" id="btn-bank-client-picker-save">
                <span data-i18n="assign-save">保存</span>
            </button>
        </div>
    </div>
`;
wbInject('bank-client-picker-modal', HTML);
