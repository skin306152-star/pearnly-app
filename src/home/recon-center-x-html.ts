// 对账中心 · 重设计外壳 HTML(2026-06-14 · 落地 design-reference/pearnly_reconciliation_redesign_v2.html)
//
// 静态骨架由 page-reconcile.ts 运行期注入 #page-reconcile;动态部分(上传卡内容 / 余额值 /
// 结果指标 / 模板列表)由 recon-center-x.ts 控制器填充。作用域类名前缀 .rcx-。
// 字段对应 / 内容确认两个弹窗复用全局 window.ReconMapping / window.ReconReview(不在此声明)。
//
// 文案走 data-i18n(key 前缀 rcx-);page-reconcile.ts 注入后做初译,切语言由 applyLang 覆盖。

export const RCX_HTML = `
<div class="rcx" id="rcx-root">
  <div class="rcx-head">
    <div class="rcx-head-text">
      <h1 class="rcx-h1" data-i18n="rcx-title">对账中心</h1>
      <div class="rcx-sub" data-i18n="rcx-subtitle">上传原始文件，系统自动选择合适的读取方式，并集中提示需要确认的内容</div>
    </div>
    <div class="rcx-actions">
      <button class="rcx-btn" id="rcx-guide-btn" type="button">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.7 9a2.6 2.6 0 1 1 3.7 2.4c-.9.5-1.4 1.1-1.4 2.1"/><path d="M12 17h.01"/></svg>
        <span data-i18n="rcx-guide-btn">导入说明</span>
      </button>
      <button class="rcx-btn rcx-primary" id="rcx-template-btn" type="button">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" aria-hidden="true"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4"/><path d="M9 12h6M9 16h6"/></svg>
        <span data-i18n="rcx-template-center">模板中心</span>
      </button>
    </div>
  </div>

  <div class="rcx-segmented" id="rcx-tabs" role="tablist">
    <button class="rcx-seg active" data-rcx-tab="bank" role="tab" aria-selected="true" data-i18n="rcx-tab-bank">银行对账</button>
    <button class="rcx-seg" data-rcx-tab="tax" role="tab" aria-selected="false" data-i18n="rcx-tab-tax">销项税报告核查</button>
    <button class="rcx-seg" data-rcx-tab="income" role="tab" aria-selected="false" data-i18n="rcx-tab-income">收入对账</button>
  </div>

  <section class="rcx-banner" id="rcx-banner">
    <div class="rcx-banner-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" aria-hidden="true"><path d="m12 3 1.3 3.7L17 8l-3.7 1.3L12 13l-1.3-3.7L7 8l3.7-1.3z"/><path d="m18.5 13 .8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z"/></svg>
    </div>
    <div class="rcx-banner-copy">
      <b data-i18n="rcx-banner-title">优先使用 Pearnly 标准模板，导入更快、结果更稳定</b>
      <p data-i18n="rcx-banner-desc">标准模板可直接按字段读取，减少格式差异带来的重复确认。不是强制要求，您仍可上传现有文件。</p>
      <div class="rcx-benefits">
        <span class="rcx-benefit" data-i18n="rcx-benefit-1">更快完成导入</span>
        <span class="rcx-benefit" data-i18n="rcx-benefit-2">减少人工确认</span>
        <span class="rcx-benefit" data-i18n="rcx-benefit-3">字段完整性检查</span>
        <span class="rcx-benefit" data-i18n="rcx-benefit-4">适合批量处理</span>
      </div>
    </div>
    <div class="rcx-banner-actions">
      <button class="rcx-btn rcx-sm" id="rcx-banner-download" type="button" data-i18n="rcx-download-page-templates">下载本页模板</button>
      <button class="rcx-btn rcx-text rcx-sm" id="rcx-banner-hide" type="button" data-i18n="rcx-hide-banner">暂不提示</button>
    </div>
  </section>

  <section class="rcx-preflight">
    <div class="rcx-preflight-head">
      <b data-i18n="rcx-flow-title">本次对账流程</b>
      <span data-i18n="rcx-flow-note">结果指标将在对账完成后显示</span>
    </div>
    <div class="rcx-steps">
      <div class="rcx-step"><div class="rcx-step-no">1</div><div><b data-i18n="rcx-step1-t">上传文件</b><span data-i18n="rcx-step1-s">支持常用格式</span></div></div>
      <div class="rcx-step"><div class="rcx-step-no">2</div><div><b data-i18n="rcx-step2-t">导入前检查</b><span data-i18n="rcx-step2-s">确认字段与余额</span></div></div>
      <div class="rcx-step"><div class="rcx-step-no">3</div><div><b data-i18n="rcx-step3-t">执行对账</b><span data-i18n="rcx-step3-s">匹配两侧记录</span></div></div>
      <div class="rcx-step"><div class="rcx-step-no">4</div><div><b data-i18n="rcx-step4-t">处理差异</b><span data-i18n="rcx-step4-s">仅处理异常项</span></div></div>
    </div>
  </section>

  <section class="rcx-workspace" id="rcx-workspace">
    <div class="rcx-workspace-head">
      <b id="rcx-task-title" data-i18n="rcx-task-bank">银行对账 · 主操作</b>
      <span class="rcx-status-badge" data-i18n="rcx-auto-method">自动选择读取方式</span>
    </div>
    <div class="rcx-upload-grid">
      <div class="rcx-upload-card" id="rcx-card-left" data-side="left"></div>
      <div class="rcx-plus">＋</div>
      <div class="rcx-upload-card" id="rcx-card-right" data-side="right"></div>
    </div>

    <div class="rcx-balance" id="rcx-balance">
      <div class="rcx-balance-head">
        <b data-i18n="rcx-balance-title">余额预检</b>
        <div class="rcx-legend">
          <span><i class="rcx-dot rcx-dot-green"></i><span data-i18n="rcx-confirmed">已确认</span></span>
          <span><i class="rcx-dot rcx-dot-yellow"></i><span data-i18n="rcx-need-confirm">需要确认</span></span>
        </div>
      </div>
      <div class="rcx-balance-grid">
        <div class="rcx-balance-item">
          <label><span data-i18n="rcx-gl-closing">GL 期末余额</span> <span class="rcx-source-tag" id="rcx-gl-source" data-i18n="rcx-await-upload">待上传</span></label>
          <div class="rcx-balance-value" id="rcx-gl-end">—</div>
        </div>
        <div class="rcx-balance-item">
          <label><span data-i18n="rcx-st-closing">账单期末余额</span> <span class="rcx-source-tag" id="rcx-st-source" data-i18n="rcx-await-upload">待上传</span></label>
          <div class="rcx-balance-value" id="rcx-st-end">—</div>
        </div>
        <div class="rcx-balance-item">
          <label data-i18n="rcx-st-opening">账单期初余额</label>
          <div class="rcx-balance-value" id="rcx-st-start">—</div>
        </div>
        <div class="rcx-balance-item">
          <label data-i18n="rcx-gl-opening">GL 期初余额</label>
          <div class="rcx-balance-value" id="rcx-gl-start">—</div>
        </div>
      </div>
      <div class="rcx-balance-summary">
        <span data-i18n="rcx-opening-diff">期初差额（账单期初 − GL 期初）</span>
        <strong id="rcx-opening-diff">—</strong>
      </div>
    </div>

    <div class="rcx-bottom">
      <div class="rcx-ready" id="rcx-ready-text" data-i18n="rcx-ready-await">请上传两份文件后开始对账</div>
      <div class="rcx-bottom-btns">
        <button class="rcx-btn" id="rcx-clear-btn" type="button" data-i18n="rcx-clear">清空</button>
        <button class="rcx-btn rcx-primary" id="rcx-start-btn" type="button" disabled data-i18n="rcx-start">开始对账</button>
      </div>
    </div>
  </section>

  <section class="rcx-history" id="rcx-history">
    <div class="rcx-history-head">
      <b data-i18n="rcx-hist-title">最近对账</b>
      <span data-i18n="rcx-hist-tip">点击任意记录可重新查看其对账结果</span>
    </div>
    <div class="rcx-history-empty" id="rcx-history-empty" style="display:none"></div>
    <div class="rcx-history-list" id="rcx-history-list"></div>
  </section>

  <section class="rcx-processing" id="rcx-processing" aria-live="polite">
    <div class="rcx-processing-icon">↻</div>
    <h3 data-i18n="rcx-processing-title">正在执行对账</h3>
    <p id="rcx-processing-text" data-i18n="rcx-processing-wait">正在执行对账，请稍候……</p>
    <small id="rcx-processing-sub"></small>
  </section>

  <section class="rcx-results" id="rcx-results">
    <div class="rcx-results-head">
      <div>
        <b data-i18n="rcx-result-done">对账完成</b>
        <span data-i18n="rcx-result-hint">结果指标只在任务完成后展示，点击指标可筛选对应记录</span>
      </div>
      <div class="rcx-results-head-btns">
        <button class="rcx-btn rcx-sm" id="rcx-back-btn" type="button" data-i18n="rcx-back">返回</button>
        <button class="rcx-btn rcx-sm" id="rcx-export-btn" type="button" data-i18n="rcx-export">导出结果</button>
      </div>
    </div>
    <div class="rcx-kpis" id="rcx-kpis">
      <button class="rcx-kpi rcx-kpi-primary active" data-filter="all" type="button">
        <label data-i18n="rcx-kpi-rate">匹配率</label>
        <strong id="rcx-kpi-rate">—</strong>
        <p id="rcx-kpi-rate-sub"></p>
      </button>
      <button class="rcx-kpi" data-filter="matched" type="button">
        <label data-i18n="rcx-kpi-matched">已匹配</label>
        <strong id="rcx-kpi-matched">—</strong>
        <p data-i18n="rcx-kpi-matched-sub">无需继续处理</p>
      </button>
      <button class="rcx-kpi" data-filter="difference" type="button">
        <label data-i18n="rcx-kpi-diff">待处理差异</label>
        <strong id="rcx-kpi-diff">—</strong>
        <p data-i18n="rcx-kpi-diff-sub">建议优先确认</p>
      </button>
      <button class="rcx-kpi" data-filter="unmatched" type="button">
        <label data-i18n="rcx-kpi-unmatched">未匹配</label>
        <strong id="rcx-kpi-unmatched">—</strong>
        <p data-i18n="rcx-kpi-unmatched-sub">暂未找到对应记录</p>
      </button>
    </div>
    <div class="rcx-result-body">
      <div class="rcx-priority-card">
        <div class="rcx-card-title">
          <b data-i18n="rcx-priority">优先处理</b>
          <span data-i18n="rcx-priority-sub">按影响程度排序</span>
        </div>
        <div class="rcx-issue-list" id="rcx-issue-list"></div>
        <button class="rcx-btn rcx-primary rcx-full" id="rcx-handle-btn" type="button"></button>
      </div>
      <div class="rcx-detail-card">
        <div class="rcx-card-title">
          <b id="rcx-detail-title" data-i18n="rcx-detail">结果明细</b>
          <span id="rcx-detail-count" data-i18n="rcx-detail-all">显示全部记录</span>
        </div>
        <div class="rcx-table-wrap">
          <table class="rcx-table">
            <thead id="rcx-detail-head"></thead>
            <tbody id="rcx-detail-rows"></tbody>
          </table>
        </div>
        <div class="rcx-pager" id="rcx-pager"></div>
      </div>
    </div>
  </section>

  <section class="rcx-fail" id="rcx-fail">
    <div class="rcx-fail-icon">!</div>
    <h3 data-i18n="rcx-fail-title">对账未完成</h3>
    <p id="rcx-fail-text"></p>
    <div class="rcx-fail-actions">
      <button class="rcx-btn" id="rcx-fail-back" type="button" data-i18n="rcx-fail-back">返回文件检查</button>
      <button class="rcx-btn rcx-primary" id="rcx-fail-retry" type="button" data-i18n="rcx-fail-retry">重试</button>
    </div>
  </section>
</div>

<div class="rcx-overlay" id="rcx-tplpanel-overlay"></div>
<aside class="rcx-tplpanel" id="rcx-tplpanel" aria-hidden="true" role="dialog" aria-modal="true" aria-labelledby="rcx-tplpanel-title">
  <div class="rcx-tplpanel-head">
    <h2 id="rcx-tplpanel-title" data-i18n="rcx-tplpanel-bank">银行对账模板</h2>
    <button class="rcx-icon-btn" id="rcx-tplpanel-close" type="button" aria-label="close">✕</button>
  </div>
  <div class="rcx-tplpanel-body">
    <div class="rcx-tplpanel-intro">
      <b data-i18n="rcx-tplpanel-intro-t">标准模板为什么更适合高频对账？</b>
      <p data-i18n="rcx-tplpanel-intro-p">字段位置统一，可直接读取并检查缺失内容。使用次数越多，越能减少重复整理和人工确认。</p>
    </div>
    <div id="rcx-template-list"></div>
  </div>
  <div class="rcx-tplpanel-footer">
    <button class="rcx-btn rcx-primary rcx-full" id="rcx-tplpanel-download-all" type="button" data-i18n="rcx-download-all">下载当前对账所需全部模板</button>
  </div>
</aside>

<div class="rcx-overlay" id="rcx-modal-overlay"></div>
<div class="rcx-modal" id="rcx-guide-modal" role="dialog" aria-modal="true" aria-labelledby="rcx-guide-title">
  <div class="rcx-modal-head"><h2 id="rcx-guide-title" data-i18n="rcx-guide-title-h">三种导入方式</h2><button class="rcx-icon-btn rcx-modal-close" type="button" aria-label="close">✕</button></div>
  <div class="rcx-modal-body">
    <div class="rcx-guide-card">
      <div class="rcx-guide-icon rcx-guide-std" data-i18n="rcx-recommend">推荐</div>
      <div class="rcx-guide-meta"><b data-i18n="rcx-method-std">标准模板读取</b><p data-i18n="rcx-method-std-p">字段固定、直接读取、导入前检查。适合高频对账和批量处理，通常需要确认的内容最少。</p></div>
    </div>
    <div class="rcx-guide-card">
      <div class="rcx-guide-icon rcx-guide-tbl" data-i18n="rcx-tag-table">表格</div>
      <div class="rcx-guide-meta"><b data-i18n="rcx-method-table">普通表格读取</b><p data-i18n="rcx-method-table-p">适用于现有 Excel 或 CSV。首次确认字段对应关系后，下次可复用保存的设置。</p></div>
    </div>
    <div class="rcx-guide-card">
      <div class="rcx-guide-icon rcx-guide-scan" data-i18n="rcx-tag-file">文件</div>
      <div class="rcx-guide-meta"><b data-i18n="rcx-method-file">文件内容读取</b><p data-i18n="rcx-method-file-p">系统读取文件内容，只提示不清晰或有歧义的字段，不要求用户检查整份文件。</p></div>
    </div>
  </div>
  <div class="rcx-modal-foot"><button class="rcx-btn rcx-primary rcx-modal-close" type="button" data-i18n="rcx-got-it">知道了</button></div>
</div>
`;
