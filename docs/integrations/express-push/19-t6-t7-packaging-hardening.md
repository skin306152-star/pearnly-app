# T6+T7 施工单 · 小助手打包收口(瘦身 + 防逆向)

> 来源:Owner 2026-06-22「把 T6 瘦身 / T7 防盗做完,这项彻底闭环再上线」。companion repo `D:\pearnly-companion`(packaging)。
> **两件都改打包、要一起重打一起重验** → 合一张单、一个窗口、一轮验证。
> ⚠️ **排程铁律(PM 定)**:本单是**最后一步**。**必须在窗口1+2 的功能改动(T1/T2/T5/T8)落地 + Owner 功能真机验收【之后】才做**——因为打包改动(排除/混淆)正是冻结 exe 翻车的高发区(cp874/stdout/PACK 有前科)。先有一个功能正确的已知好版本,再优化打包,再重验,最后上线。

---

## A. T6 · 瘦身(对症 · 大肥肉已定位)

**病灶(PM 已读真码)**:`companion.exe` ~110MB 主因 = **opencv(cv2)+numpy(~60MB+)**。它们**只被模拟录入/校准模块用**(`calibration` / `calibration_ui` / `ocr_verifier` / `field_engine` / `matching/field_locator`),而 **RPA 暂泊、直录 DBF 主路完全不用**。甩不掉的原因 = `main.py:34` 顶层 `import cv2` 把它钉进了包(`pack_runner.spec` 已排 cv2/numpy 故才 14MB,`companion.spec` 没排)。

**改法**:
1. **cv2/numpy 改懒加载**:把 `main.py:34` 及各 RPA/校准模块的 `import cv2 / import numpy` 从模块顶层挪进**真正用到的函数体内**(只有跑模拟录入/校准时才 import)。直录路径不触发。
2. **`companion.spec` `excludes` 增** `cv2`、`numpy`,以及纯 RPA/校准模块(`calibration*`/`ocr_verifier`/`field_engine`/`matching*`/`pyautogui`/`pytesseract`/`mss` 等只服务 RPA 的)。**代码留在 repo(懒加载·不删)**——将来 RPA 上线用**另一套 build profile** 重新 include 即可(可扩展性:核心不动、按 method 出包,零代码删改)。
3. **PySide6 只用 QtCore/QtGui/QtWidgets**(实测 import 仅这三)→ `excludes` 掉未用 Qt 模块(QtNetwork/QtQml/QtQuick/QtWebEngine/Qt3D/QtMultimedia/QtCharts/QtSql/QtTest/QtPdf 等)+ 相应 Qt DLL/plugins。
4. **UPX**:当前 `upx=False`。可评估开 UPX 进一步压,但 ⚠️ **UPX 壳会抬高杀软/SmartScreen 误报**(与 T7 混淆叠加更甚)→ **默认仍 False**,除非实测装机不被拦再开。
- **目标**:companion.exe 去 opencv 后大幅缩水(~110MB→预期 40-50MB 级),setup.exe 124.5MB 同比大降,客户下载/装机门槛降一截。

## B. T7 · 防逆向 / 防盗源码

**病灶**:PyInstaller exe 可被 `pyinstxtractor` 轻易解包 → `.pyc` → 反编译近还原源码(DBF 过账 schema / 映射 / 未来 PACK 键序 = 我们的护城河)。

**改法(务实·主)**:
1. **PyArmor 混淆**:对 companion 包字节码混淆(运行时解密),再过 PyInstaller。**companion.exe 与 pack_runner.exe 都做**。解包出来是混淆字节码,非干净源码 → 抬高抄袭门槛。
2. **凭证已 DPAPI**(T1)·不在本单。
- **诚实边界(PM)**:本地二进制**没有绝对防护**——决心够大的对手仍能逆向(我们逆 Express 也是这么来的)。PyArmor 是**性价比最高的抬门槛**,不是铁壁。真护城河是整合+OCR+产品本身。**未来更强项(单列·不阻塞)**:把最专有的映射/过账规则改成运行时从云端拉(不焙进 exe)——但 DBF 写盘逻辑必须本地,只能部分云化。

## B2. 图标换成 Pearnly logo(Owner 2026-06-22·并入本打包棒)

**病灶**:`companion.spec` 无 `icon=` → companion.exe 用 PyInstaller 通用图标 → 桌面快捷方式显示通用"文件夹+箭头"。

**改法**(同属打包·三处一致):
1. 把 `pearnly-app/static/brand/app-icon-1024.png`(方形 App 图标·权威源)转**多尺寸 Windows `.ico`**(16/32/48/64/128/256),放 `D:\pearnly-companion\assets\pearnly.ico`(进 git)。
2. `companion.spec`(及 `pack_runner.spec` 一致)EXE() 加 `icon='...pearnly.ico'`。
3. `installer.iss`:`SetupIconFile=...pearnly.ico`(安装程序自身图标)+ 桌面快捷方式图标随 exe 内嵌图标(或 `IconFilename` 显式指)。
4. **托盘图标** `gui_tray` 的 `QSystemTrayIcon`/`QIcon` 用同一 logo(`app-icon` PNG·托盘用 PNG 即可)→ 三处(exe/快捷方式/托盘)视觉一致。
- 验收:装完桌面快捷方式 + 任务栏 + 托盘都是 Pearnly logo·非通用图标(截图)。

## C. ⚠️ 交互与红线(两件叠加必看)
- **混淆 + 未签名**(T3 签名你已冻)→ 杀软/SmartScreen 更易报毒。上线初期可接受,客户反馈被拦再议签名解冻。
- **混淆/排除 = 重打包 → 冻结 exe 翻车高发**:cp874 中文 print / `console=False` stdout=None / cv2 懒加载漏改导致直录路径仍 import / Qt 模块排过头托盘/配对窗起不来。**全部靠重打后真机重验兜底**(下方 D)。
- **不碰功能逻辑**:本单只改 import 时机 + spec + 混淆,**DBF 写盘/PACK/配对/队列的行为一行不改**。

## D. 验证(重打后真机重验 · 这是上线前的闸)
1. **瘦身实证**:出包,companion.exe / setup.exe 体积对比(贴前后 MB)。
2. **直录主路不退化**(最关键):用瘦身+混淆后的 frozen 包,DATAT 跑完整链——配对(探测+选账套)→ 托盘 worker 直写一张(借贷平·ack)→ **加密凭证经 frozen pack_runner.exe 解密→登录→PACK→报表可见**。写前 robocopy 备份、完事 /MIR 还原回 8 表基线。
3. **托盘 + 配对窗**起得来、能最小化(T5)、无缺模块报错。
4. **懒加载验证**:直录全程 grep 日志/进程,**确认没 import cv2/numpy/PySide6 多余模块**(漏改会暴露)。
5. **防逆向实证**:对出的 exe 跑 `pyinstxtractor` → 确认拿到的是混淆字节码、反编译不出干净源码(贴证据)。
6. **回归**:companion 单测全绿(混淆/排除不破单测)。

## E. 交付
- companion:cv2/numpy 懒加载改 + `companion.spec` excludes + PyArmor 接入打包流程 + 重打三件套(companion.exe/pack_runner.exe/setup.exe)。
- 报告:体积前后对比 + D 的 6 项真机/解包证据 + 单测 + commit(companion master)。
- 产物:新 setup.exe scp prod `static/companion/` + bump `home.html ?v=`(换安装包必破缓存)。

> 排程:**窗口1+2 功能落地 + Owner 真机验收 → 本单(瘦身+混淆)→ 重打真机重验(D)→ 上线 → Owner 真实用户实测**。本单是闭环最后一棒。
