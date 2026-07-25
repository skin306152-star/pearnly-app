# -*- coding: utf-8 -*-
"""教程「安装小助手」章的 14 张配图驱动:开一个隔离的配对窗,逐个摆出待截图的状态。

为什么不直接跑 companion 的 main.py
    main.py 开头就 single_instance.acquire() 拿命名互斥量 PearnlyCompanionSingleInstance。
    Zihao 机器上常年有一个在用实例持着它,第二个进程只会拿到 ERROR_ALREADY_EXISTS 直接退出
    ——截不到图。反过来若先杀掉在用实例再跑,等于把生产用的推送通道停了。
    所以这里绕过 main.py,直接构造 PairingDialog / 复用 TrayApp._build_menu:
    出图用的是真实生产控件,但不碰互斥量、不起 poll worker、不建托盘图标。

为什么要重定向 APPDATA(由 orchestrate.ps1 在启动本进程前设好)
    config.py 在 import 期就按 %APPDATA%/Pearnly 定死配置/日志路径并 mkdir。PairingDialog 会
    读写这份配置(账套选择、科目映射)。不重定向 = 截图过程直接改写 Zihao 在用实例的
    companion.json,下次它启动就带着演示账套跑真推送。重定向后所有写入落在 scratch 副本里。

握手协议(和 orchestrate.ps1 配对)
    需要整窗成图时写 state.txt=READY:<tag>[:<hwnd>],然后轮询 go.txt 等外部放行。
    PrintWindow 必须由别的进程发:自进程发消息给自己的窗口,会在 Qt 事件循环里死等自己。

用法: driver.py <lang> <outdir> <handshake_dir> [--expect-empty]
"""

import os
import sys
import time
from pathlib import Path

LANG = sys.argv[1]
OUT = Path(sys.argv[2])
HS = Path(sys.argv[3])
EXPECT_EMPTY = "--expect-empty" in sys.argv
OUT.mkdir(parents=True, exist_ok=True)
HS.mkdir(parents=True, exist_ok=True)

COMPANION_SRC = (
    os.environ.get("PEARNLY_COMPANION_SRC") or r"C:\Users\skin3\Desktop\pearnly-companion"
)
sys.path.insert(0, COMPANION_SRC)

from PySide6.QtCore import QPoint, QRect, Qt  # noqa: E402
from PySide6.QtGui import QPainter, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.companion.gui_pairing import PairingDialog  # noqa: E402
from src.companion.gui_tray import TrayApp  # noqa: E402
from src.companion.i18n import t  # noqa: E402


def log(msg: str) -> None:
    print(msg, flush=True)


def wait_for_go(tag: str, hwnd: int = 0) -> None:
    payload = f"READY:{tag}" + (f":{hwnd}" if hwnd else "")
    (HS / "state.txt").write_text(payload, encoding="utf-8")
    go = HS / "go.txt"
    for _ in range(600):
        # PowerShell 5.1 的 utf8 输出带 BOM,读回要先剥掉再比对
        if go.exists() and go.read_text(encoding="utf-8-sig").strip() == tag:
            go.unlink()
            return
        app.processEvents()
        time.sleep(0.1)
    raise TimeoutError(f"外部截图未在时限内放行: {tag}")


def save(pm: QPixmap, shot: str) -> None:
    p = OUT / f"{shot}.{LANG}.png"
    pm.save(str(p), "PNG")
    log(f"SAVED {p} {pm.width()}x{pm.height()}")


def crop(dlg, top_w, bottom_w, pad_top=3, pad_bottom=12) -> QPixmap:
    """按控件几何裁窗口客户区的一段(纯窗口内容,绝不会带进桌面上的别的东西)。"""
    y1 = top_w.mapTo(dlg, QPoint(0, 0)).y() - pad_top
    y2 = bottom_w.mapTo(dlg, QPoint(0, 0)).y() + bottom_w.height() + pad_bottom
    y1 = max(0, y1)
    return dlg.grab(QRect(0, y1, dlg.width(), y2 - y1))


def compose_popup(dlg, combo) -> QPixmap:
    """窗口 + 展开的下拉列表拼成一张:两块都是自家控件各自 grab,不截屏、不碰桌面。"""
    combo.showPopup()
    for _ in range(20):
        app.processEvents()
        time.sleep(0.03)
    pop = combo.view().window()
    pm_d, pm_p = dlg.grab(), pop.grab()
    dpr = pm_d.devicePixelRatio() or 1.0
    off = pop.geometry().topLeft() - dlg.mapToGlobal(QPoint(0, 0))
    w = max(pm_d.width() / dpr, off.x() + pm_p.width() / dpr)
    h = max(pm_d.height() / dpr, off.y() + pm_p.height() / dpr)
    canvas = QPixmap(int(w * dpr), int(h * dpr))
    canvas.setDevicePixelRatio(dpr)
    canvas.fill(Qt.white)
    p = QPainter(canvas)
    p.drawPixmap(0, 0, pm_d)
    p.drawPixmap(off.x(), off.y(), pm_p)
    p.end()
    combo.hidePopup()
    app.processEvents()
    return canvas


def show_tray_menu():
    """用托盘真实建菜单的代码(TrayApp._build_menu)出图,不建托盘图标、不起 poll worker。

    返回 (menu, hwnd)。菜单要真弹出来让外部 PrintWindow 抓——Qt 自绘 grab() 拿不到
    原生弹出菜单的内边距/圆角,出来的图不像会计实际看到的样子。
    """

    class _Stub:
        def __init__(self, lang: str) -> None:
            self.lang = lang
            self.tray = self
            self.menu = None

        def setContextMenu(self, m) -> None:
            self.menu = m

        def _repair(self) -> None: ...
        def _open_logs(self) -> None: ...
        def _quit(self) -> None: ...
        def _do_update(self) -> None: ...

    stub = _Stub(LANG)
    TrayApp._build_menu(stub)
    menu = stub.menu
    stub._status_action.setText(t("st_idle", LANG))
    # show() 而非 popup():popup 会做全局鼠标/键盘抓取,会打断 Zihao 正在做的事。
    menu.show()
    scr = QApplication.primaryScreen().availableGeometry()
    menu.move(scr.right() - menu.width() - 24, scr.bottom() - menu.height() - 12)
    for _ in range(30):
        app.processEvents()
        time.sleep(0.03)
    return menu, int(menu.winId())


app = QApplication(sys.argv[:1])
dlg = PairingDialog(lang=LANG)
# 硬保险:配对会真连云端换 token 并写 HKCU 开机自启,还可能把在用实例的 endpoint 顶掉。
# 拆掉信号而非置灰——置灰会让配图里的「配对」按钮看起来不可用,误导会计;拆信号则外观
# 照旧,误点也绝对不会执行。
dlg.pair_btn.clicked.disconnect()
dlg.show()

# 等探测落到终态:找到账套 / 或红字「未自动找到 Express」(\\accserver 解析不了要等超时)。
browse_hint = t("browse_hint", LANG)
deadline = time.time() + 180
settled = ""
while time.time() < deadline:
    app.processEvents()
    time.sleep(0.1)
    if dlg._sets and dlg.account.count():
        settled = "sets"
        break
    if dlg.status.text() == browse_hint:
        settled = "empty"
        break
log(f"SETTLED {settled} status={dlg.status.text()!r} sets={len(dlg._sets)}")
if not settled:
    raise TimeoutError("探测未落到终态")

dlg._fit_to_content()
for _ in range(10):
    app.processEvents()
    time.sleep(0.05)

if EXPECT_EMPTY:
    assert settled == "empty", "本轮要的是「未找到 Express」态"
    wait_for_go("noexpress")
else:
    assert settled == "sets", "本轮要的是「已找到账套」态"
    wait_for_go("pairwindow")
    save(crop(dlg, dlg.sec_connect, dlg.token), "setup-02-paircode")
    save(compose_popup(dlg, dlg.account), "setup-03-accountpick")
    save(crop(dlg, dlg.status, dlg.pair_btn, pad_top=8), "setup-05-actions")

    # 科目映射要先选账套才会去读该账套 GLACC —— 不选就是 6 个「正在读取…」的空壳,配图无意义。
    dlg.account.setCurrentIndex(0)
    for _ in range(200):
        app.processEvents()
        time.sleep(0.05)
        if dlg.acc_combos["revenue_acc"].isEnabled():
            break
    log("CHART loaded=" + str(dlg.acc_combos["revenue_acc"].currentText()))
    dlg._toggle_advanced()
    for _ in range(20):
        app.processEvents()
        time.sleep(0.05)
    # 展开后内容高过本机屏幕(窗口自适应封顶 94% 屏高)→ 滚动条一出,顶部会切出半行残影。
    # 解开高度上限让窗口按内容长满:等同会计在更高屏幕上看到的样子,且不留半行伪影。
    # PrintWindow 抓的是窗口自身的绘制表面,超出屏幕的部分照样完整。
    host = dlg._scroll.widget()
    host.layout().activate()
    dlg.setMaximumHeight(16777215)
    dlg.resize(dlg.width(), host.sizeHint().height() + dlg._chrome_h + 4)
    for _ in range(10):
        app.processEvents()
        time.sleep(0.05)
    wait_for_go("advanced")
    menu, menu_hwnd = show_tray_menu()
    wait_for_go("traymenu", hwnd=menu_hwnd)
    menu.hide()
    app.processEvents()

(HS / "state.txt").write_text("DONE", encoding="utf-8")
dlg.close()
app.processEvents()
log("DONE")
