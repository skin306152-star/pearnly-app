// ============================================================
// REFACTOR-WB-C3 (2026-06-01) · 客户编辑 / 账套主体编辑弹窗 inner 从 home.html 抽出 · 运行期注入
//
// home.html 留两个空壳 <div id="client-modal-mask"> / <div id="wsclient-modal-mask">(modal-mask · display:none)·
// 本模块 eval 时注入 inner。clients.js(main.js 内 import 在本模块之后)在 DOMContentLoaded handler 里
// 带 null 守卫绑 client-modal-* / wsclient-modal-* close/cancel/save/delete/archive/mask · openClientModal
/// openWsClientModal 用户开弹窗时才读 inner。模块 eval(defer)早于 DOMContentLoaded → 元素届时恒在场。
// import 置 clients.js 前(确定性·非竞态)· 镜像 modal-assign-clients.js 范式。verbatim inner · 0 改结构。
// i18n:注入后子树补译(镜像 applyLang)· 切语言由 applyLang 全文扫描覆盖。
// ============================================================
import { wbInject } from './wb-inject.js';

const CLIENT_HTML = `
        <div class="modal client-modal" role="dialog">
            <div class="modal-header">
                <div class="modal-title" id="client-modal-title" data-i18n="client-modal-new">新建客户</div>
                <button class="modal-close" id="client-modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-row">
                    <label data-i18n="client-field-name">客户名称 *</label>
                    <input type="text" id="client-input-name" maxlength="200" data-i18n-placeholder="client-field-name-ph">
                </div>
                <div class="form-row form-row-2col">
                    <div>
                        <label data-i18n="client-field-short">简称</label>
                        <input type="text" id="client-input-short" maxlength="80">
                    </div>
                    <div>
                        <label data-i18n="client-field-tax">税号</label>
                        <input type="text" id="client-input-tax" maxlength="20">
                    </div>
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-address">地址</label>
                    <input type="text" id="client-input-address" maxlength="500">
                </div>
                <div class="form-row form-row-2col">
                    <div>
                        <label data-i18n="client-field-party-type">买方类型</label>
                        <select id="client-input-party-type">
                            <option value="" data-i18n="client-party-unset">未指定</option>
                            <option value="company" data-i18n="client-party-company">公司</option>
                            <option value="individual" data-i18n="client-party-individual">个人</option>
                            <option value="foreigner" data-i18n="client-party-foreigner">外国</option>
                            <option value="anonymous" data-i18n="client-party-anonymous">匿名</option>
                        </select>
                    </div>
                    <div>
                        <label data-i18n="client-field-branch">总公司 / 分店</label>
                        <input type="text" id="client-input-branch" maxlength="120" data-i18n-placeholder="client-field-branch-ph">
                    </div>
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-promptpay">PromptPay 收款号</label>
                    <input type="text" id="client-input-promptpay" maxlength="40">
                </div>
                <div class="form-row form-row-2col">
                    <div>
                        <label data-i18n="client-field-contact">联系人</label>
                        <input type="text" id="client-input-contact" maxlength="100">
                    </div>
                    <div>
                        <label data-i18n="client-field-phone">电话</label>
                        <input type="text" id="client-input-phone" maxlength="50">
                    </div>
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-email">邮箱</label>
                    <input type="email" id="client-input-email" maxlength="200">
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-color">标识颜色</label>
                    <div class="color-picker" id="client-color-picker">
                        <span class="color-swatch active" data-color="#111111" style="background:#111111"></span>
                        <span class="color-swatch" data-color="#ef4444" style="background:#ef4444"></span>
                        <span class="color-swatch" data-color="#f59e0b" style="background:#f59e0b"></span>
                        <span class="color-swatch" data-color="#10b981" style="background:#10b981"></span>
                        <span class="color-swatch" data-color="#8b5cf6" style="background:#8b5cf6"></span>
                        <span class="color-swatch" data-color="#ec4899" style="background:#ec4899"></span>
                        <span class="color-swatch" data-color="#06b6d4" style="background:#06b6d4"></span>
                        <span class="color-swatch" data-color="#6b7280" style="background:#6b7280"></span>
                    </div>
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-notes">备注</label>
                    <textarea id="client-input-notes" maxlength="1000" rows="2"></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-danger client-modal-delete-btn" id="client-modal-delete" style="display:none;">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3a1 1 0 011-1h2a1 1 0 011 1v2M5 5l1 9a1 1 0 001 1h2a1 1 0 001-1l1-9"/>
                    </svg>
                    <span data-i18n="client-delete">删除客户</span>
                </button>
                <div class="modal-footer-right">
                    <button class="btn btn-ghost" id="client-modal-cancel" data-i18n="client-cancel">取消</button>
                    <button class="btn btn-primary" id="client-modal-save" data-i18n="client-save">保存</button>
                </div>
            </div>
        </div>
    `;
const WSCLIENT_HTML = `
        <div class="modal" role="dialog" style="max-width:440px;">
            <div class="modal-header">
                <div class="modal-title" id="wsclient-modal-title" data-i18n="wsclient-modal-new">新建账套主体</div>
                <button class="modal-close" id="wsclient-modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-row">
                    <label data-i18n="wsclient-field-name">账套主体名称 *</label>
                    <input type="text" id="wsclient-input-name" maxlength="200" data-i18n-placeholder="wsclient-field-name-ph" placeholder="公司名称,例如 BAKELAB">
                </div>
                <div class="form-row">
                    <label data-i18n="wsclient-field-tax">税号</label>
                    <input type="text" id="wsclient-input-tax" maxlength="30">
                </div>
                <div class="form-row">
                    <label data-i18n="wsclient-field-address">地址</label>
                    <input type="text" id="wsclient-input-address" maxlength="500" data-i18n-placeholder="wsclient-field-address-ph" placeholder="开票地址(印在税票上)">
                </div>
                <div class="form-row">
                    <label data-i18n="wsclient-field-branch">总公司 / 分公司</label>
                    <input type="text" id="wsclient-input-branch" maxlength="120" data-i18n-placeholder="wsclient-field-branch-ph" placeholder="สำนักงานใหญ่(总公司)或 สาขาที่ 1">
                </div>
                <div class="form-row">
                    <label data-i18n="wsclient-field-phone">电话</label>
                    <input type="text" id="wsclient-input-phone" maxlength="50">
                </div>
                <div class="form-row form-row-check">
                    <label class="wsclient-switch-row">
                        <span class="wsclient-switch-title" data-i18n="wsclient-field-vat">已注册 VAT(可开税务发票)</span>
                        <input type="checkbox" class="btn-toggle" id="wsclient-input-vat" checked>
                    </label>
                </div>
                <div class="wsclient-modal-note" data-i18n="wsclient-note">账套主体 = 你的公司(发票卖方)。它和右上角切换器、登录弹窗共用,这里改了那边同步。</div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-danger" id="wsclient-modal-archive" style="display:none;">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h12M4 4v9a1 1 0 001 1h6a1 1 0 001-1V4M6 4V2.5a1 1 0 011-1h2a1 1 0 011 1V4"/></svg>
                    <span data-i18n="wsclient-archive">归档</span>
                </button>
                <div class="modal-footer-right">
                    <button class="btn btn-ghost" id="wsclient-modal-cancel" data-i18n="client-cancel">取消</button>
                    <button class="btn btn-primary" id="wsclient-modal-save" data-i18n="client-save">保存</button>
                </div>
            </div>
        </div>
    `;
wbInject('client-modal-mask', CLIENT_HTML);
wbInject('wsclient-modal-mask', WSCLIENT_HTML);
