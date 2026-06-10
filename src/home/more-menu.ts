// S9 4-bis · 行尾 ⋯ 菜单通用件(样式见 home-04 .more-wrap/.more-menu)
// 语义:点开关按钮 → 开本行关其他行;按钮为 null(点了别处/动作项)→ 全收。
export function toggleMoreMenu(scopeSel: string, btn: HTMLElement | null): boolean {
    const menus = document.querySelectorAll<HTMLElement>(scopeSel + ' .more-menu');
    if (!btn) {
        menus.forEach((m) => (m.hidden = true));
        return false;
    }
    const menu = btn.parentElement?.querySelector('.more-menu') as HTMLElement | null;
    menus.forEach((m) => m !== menu && (m.hidden = true));
    if (menu) menu.hidden = !menu.hidden;
    return true;
}
