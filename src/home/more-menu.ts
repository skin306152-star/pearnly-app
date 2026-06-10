// S9 4-bis · 行尾/工具条 ⋯ 菜单全局控制器(样式 home-04 .more-wrap/.more-menu)
// 结构约定:.more-wrap > button(开关)+ .more-menu(面板)。本模块在 document
// 捕获相位装一个委托统一管开关:点开关 = 开本菜单关其他;点菜单项/外部 = 全收。
// 捕获相位先于各屏自有委托,中间元素 stopPropagation 拦不住点外关;
// 关菜单发生在事件分发链确定之后,菜单项的业务 handler 照常收到点击。
export const MORE_SVG =
    '<svg viewBox="0 0 16 16" fill="currentColor" width="14" height="14"><circle cx="3" cy="8" r="1.3"/><circle cx="8" cy="8" r="1.3"/><circle cx="13" cy="8" r="1.3"/></svg>';

document.addEventListener(
    'click',
    (e) => {
        const toggle = (e.target as HTMLElement).closest(
            '.more-wrap > button'
        ) as HTMLElement | null;
        const own = toggle?.nextElementSibling as HTMLElement | null;
        document.querySelectorAll<HTMLElement>('.more-menu').forEach((m) => {
            if (m !== own) m.hidden = true;
        });
        if (own && own.classList.contains('more-menu')) own.hidden = !own.hidden;
    },
    true
);
