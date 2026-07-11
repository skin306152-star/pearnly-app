/* Pearnly AI · English dict shard 2 (G1b · monthly report package) -- loaded alongside
 * ai-i18n.js, merged into window.__AI_I18N_EN__ (split reason same as ai-i18n-en.js header:
 * single-file <500-line hard rule, shard continues). */
Object.assign(window.__AI_I18N_EN__, {
    fin_title: 'Monthly Report Package',
    fin_disabled_t: 'Report package not generated',
    fin_disabled_s:
        'This work order has not enabled the report package, or has not reached the reconcile step',
    fin_period_label: 'Period {period}',
    fin_balanced_chip: 'Balanced',
    fin_unbalanced_chip: 'Out of balance',
    fin_bs_title: 'Balance Sheet',
    fin_bs_assets: 'Assets',
    fin_bs_liabilities: 'Liabilities',
    fin_bs_equity: 'Equity',
    fin_bs_current_earnings: 'Current period earnings (retained)',
    fin_bs_totals_note: 'Assets {assets} = Liabilities {liabilities} + Equity {equity}',
    fin_bs_empty: 'No asset/liability accounts',
    fin_pl_title: 'Profit & Loss',
    fin_pl_revenue: 'Revenue',
    fin_pl_expense: 'Expense',
    fin_pl_net_profit: 'Net profit {amount}',
    fin_pl_empty: 'No revenue/expense accounts',
    fin_tb_title: 'Trial Balance',
    fin_tb_totals_note: 'Total debit {debit} · Total credit {credit}',
    fin_tb_empty: 'No account balances',
    fin_aging_title: 'AR/AP Aging',
    fin_aging_not_wired_note:
        'AR/AP aging needs a subledger and due-date data source, not yet wired for this work order pipeline',
    fin_depreciation_title: 'Depreciation Schedule',
    fin_depreciation_not_wired_note:
        'Depreciation schedule needs a fixed-asset register, not yet wired for this work order pipeline',
    fin_not_wired_chip: 'Not wired',
    fin_unclassified_hint: '{n} unclassified account(s) not included in the reports above',
});
