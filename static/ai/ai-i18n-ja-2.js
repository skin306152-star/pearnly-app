/* Pearnly AI · 日本語辞書分割 2(G1b · 月次レポートパッケージ)——ai-i18n.js と一緒に読み込み、
 * window.__AI_I18N_JA__ にマージ(分割理由は ai-i18n-ja.js 冒頭コメントと同じ:単一ファイル
 * 500 行未満の鉄則、分割継続)。*/
Object.assign(window.__AI_I18N_JA__, {
    fin_title: '月次レポートパッケージ',
    fin_disabled_t: 'レポートパッケージ未生成',
    fin_disabled_s:
        'このワークオーダーはレポートパッケージが未有効化、または照合ステップに未到達です',
    fin_period_label: '期間 {period}',
    fin_balanced_chip: '一致',
    fin_unbalanced_chip: '差異あり',
    fin_bs_title: '貸借対照表',
    fin_bs_assets: '資産',
    fin_bs_liabilities: '負債',
    fin_bs_equity: '純資産',
    fin_bs_current_earnings: '当期損益（未処分利益）',
    fin_bs_totals_note: '資産 {assets} = 負債 {liabilities} + 純資産 {equity}',
    fin_bs_empty: '資産・負債科目なし',
    fin_pl_title: '損益計算書',
    fin_pl_revenue: '収益',
    fin_pl_expense: '費用',
    fin_pl_net_profit: '当期純利益 {amount}',
    fin_pl_empty: '収益・費用科目なし',
    fin_tb_title: '試算表',
    fin_tb_totals_note: '借方合計 {debit} ・ 貸方合計 {credit}',
    fin_tb_empty: '科目残高なし',
    fin_aging_title: '売掛金・買掛金年齢表',
    fin_aging_not_wired_note:
        '売掛金・買掛金の年齢分析には補助元帳と支払期日データが必要ですが、本ワークオーダーではまだ接続されていません',
    fin_depreciation_title: '減価償却台帳',
    fin_depreciation_not_wired_note:
        '減価償却台帳には固定資産台帳が必要ですが、本ワークオーダーではまだ接続されていません',
    fin_not_wired_chip: '未接続',
    fin_unclassified_hint: '未分類の科目が{n}件あり、上記レポートには含まれていません',
});
