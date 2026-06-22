# T1 施工单 · 立 canonical「Express 登录」凭证 + DPAPI 加密(双录入方式共用)

> 派自 `11-production-readiness-dispatch.md` T1。Owner 2026-06-22 拍板:存(不删),DPAPI 加密,且做成方法无关的「Express 登录」凭证。
> 决策依据:`13-pack-necessity-findings.md`(PACK 必需 → 密码删不掉)。
> 施工窗口:companion repo `D:\pearnly-companion`(主)+ pearnly-app FE(配对向导一处)。**改 companion 每新文件 ≥1 测试 · Conventional Commits · 去 AI 味 · 单文件 <500。**

---

## 1. 目标(一段话)

把客户的 Express 登录密码从「明文存 `%APPDATA%` config」改成「DPAPI 机器+用户双绑加密」,并把这个凭证立成**方法无关的「Express 登录」**:一处输入、一处加密存储、一个统一解密收口,按录入方式分流给不同消费方——**直录(DBF)喂夜间 PACK 登录;未来模拟录入(RPA)当驱动 Express 的登录口**。RPA 上线直接复用,不另起密码框、不返工。

## 2. 边界 / 红线

- **net-new 隔离**:只动凭证的存/取/输入。**不碰 DBF 写盘逻辑**(`dbf_writer`/`dbf_sales` 一行不动)、不碰云端、不碰队列/心跳。
- 加密层与「谁消费」**解耦**:将来加 RPA 消费方时,加密/存储层零改动。
- 只加密**密码**(`express_pw`);`express_user`(账号名如 BIT9·非密)保持明文,`load_express_login()` 返回 (user 明文, pw 解密)。
- 不引重型加密库(cryptography/pynacl 一律不要)——DPAPI 是 OS 自带,走 `win32crypt` 或 ctypes 直调。
- 日志/异常**绝不**出现密码明文或 DPAPI blob(沿用既有"只元信息"纪律)。

## 3. 实现要点

### 3.1 新模块 `secret_store.py`(companion · 64 位)
- `save_express_pw(plaintext: str) -> str`:`CryptProtectData`(用户态·机器+用户双绑·不开 `LOCAL_MACHINE` flag)→ base64 → 返回存盘字符串。
- `load_express_login(cfg) -> (user, pw)`:读 `express_user`(明文)+ 解密 `express_pw` blob → 明文 pw**只在内存**、用完不留。解密失败抛 `CredentialUnavailable`(自定义·调用方兜底)。
- 纯函数 + 一个 DPAPI 薄封装;≥1 测试文件。

### 3.2 config 语义(`config.py`)
- 字段保留 `express_user` / `express_pw`,但**语义注释改为「Express 登录(直录跑 PACK / RPA 当登录口·方法无关)」**,删掉一切"PACK 密码"措辞。
- 新增 `pw_enc_version: int = 0`(0=明文/未迁移·1=DPAPIv1),标记加密方案,便于将来轮换。

### 3.3 存量迁移(启动时·幂等)
- companion 启动加载 config 后:若 `express_pw` 非空且 `pw_enc_version==0` → 视为明文 → `save_express_pw` 加密回写 + 置 `pw_enc_version=1` + 清明文。一次性、幂等(已是 v1 不重复处理)。
- 迁移失败(写盘异常等)不崩主循环:记元信息日志、跳过、下次启动重试。

### 3.4 配对落盘(`pairing.py`)
- `pairing.pair` 收到 `express_pw` → 经 `save_express_pw` 加密后写 config + 置 `pw_enc_version=1`。**配对路径明文 pw 不落盘**。
- ⚠️ **两个配对入口都走这条**:FE 向导(§3.6)与 companion.exe 本地 PySide6 配对窗 `gui_pairing.py`(`self.pw.text()` → `pairing.pair(express_pw=...)`)都汇到 `pairing.pair`,加密收口在此一处即可覆盖两者。`gui_pairing` 已 `setEchoMode(Password)`,确认其不把 pw 写日志即可。

### 3.5 消费方收口
- **DBF 的 PACK**:`pack_runner.login_and_open` 当前直接拿明文 pw `type_keys(pw)`。改为从解密后的凭证拿。
  - ⚠️ **关键坑**:`pack_runner.exe` 是 **32 位独立 exe·不 import companion 包·自解析 json**(P4 既定·保 32 位依赖最小)。所以它**读不到** `secret_store`(那是 64 位 companion 模块)。→ pack_runner 内置一个 **~20 行 ctypes DPAPI 解密**(`crypt32.dll CryptUnprotectData`·32 位同用户可解 64 位同用户加的 blob·DPAPI 跨位数同用户通用),自己 base64-decode + 解密读出 pw。**绝不**走"把明文 pw 经 argv/env 传给 runner"(进程列表泄露);若必须跨进程传,只走 stdin 管道。首选 runner 自解。
  - 这段 ctypes 解密与 `secret_store` 的 DPAPI 调用是同一套 Win32 API,逻辑等价(一个用 win32crypt 一个用 ctypes·允许各一份·别为复用强行让 runner import 包破坏 32 位最小依赖)。
  - ⚠️ **runner 按 `pw_enc_version` 分流**:读到 `pw_enc_version==1` 才 DPAPI 解密;`0`/缺失 → 当明文用(向后兼容)。正常路径下迁移(§3.3)在 companion 启动时先于夜间 PACK 跑完、pw 已是 v1,但 runner 仍须容忍未迁移/独立直跑 runner.exe 的旧 config,绝不因解密一个明文串而崩。
- **未来 RPA**:留一个清晰 seam —— `rpa_flow` 的登录步将来也调 `load_express_login()`。本单不实现 RPA,只在注释/文档标明"此凭证 RPA 复用,勿做成 DBF 专用"。

### 3.6 凭证录入点 = 本地配对窗(✅ 施工修正·2026-06-22)
> **原稿假设错了**:本节原写"web 向导 `erp-express-wizard` 单登录框"。施工窗口指出并修正——**Express 账密的唯一录入点是 companion 本地 PySide6 配对窗 `gui_pairing.py`,云端网页绝不收**。理由:密码属于装 Express 的那台机器,经云端 web 收发等于客户会计密码过一趟云 = 安全倒退。**canon:Express 登录凭证只在本地输入、本地 DPAPI 加密、永不上云。**
- 录入点 = `gui_pairing.py`(已单框 + `setEchoMode(Password)`)→ `pairing.pair(express_pw=...)` → `save_express_pw` 加密落盘(§3.4)。本次只补"用途文案"(此密码用于登录你的 Express:夜间数据重整 / 未来模拟录入)。
- **pearnly-app web 向导零改动、无需 push**(它只生成配对码,不碰 Express 密码)。

## 4. 测试(施工窗口跑齐 · companion ≥3 新断言)

- `secret_store` round-trip:加密→解密 == 原文;blob 非明文;base64 可逆。
- 存量迁移幂等:明文 config 跑一次 → 变 v1 加密;再跑一次 → 不重复处理、结果不变。
- 解密失败兜底:伪造别的机器/用户的 blob(或损坏 blob)→ `load_express_login` 抛 `CredentialUnavailable`、不崩。
- pack_runner 的 ctypes 解密:对 `secret_store` 加的 blob 能解出同一明文(同用户)。
- **既有 16 个 companion 单测全绿**,不增不减语义。

## 5. 验收(真机清单 · 施工窗口跑齐交结果 · PM 读报告判)

1. **全新配对** → 看 config 文件:`express_pw` 是 base64(DPAPI blob)不是明文;`pw_enc_version==1`;`express_user` 仍明文。
2. **解密不破功能**:托盘 worker 正常跑一次 DBF 直写冒烟(借贷平、ack success)。
3. **PACK 链通**:配 `pack_enabled` + 触发一次(或 `p32_pack_unattended` 等价)→ pack_runner 用解密出的凭证登录 Express 成功跑完 PACK(DATAT·账套硬闸 PASS)。
4. **跨机/跨用户解不开**:同 config 拷到另一台机器/另一 Windows 用户 → 启动 → 解密失败 → 友好提示"请重新配对" → 不崩、不写脏账。
5. **存量迁移**:造一份明文 `express_pw`+`pw_enc_version=0` 的 config → 启动一次 → 明文消失、变 v1 加密、功能不变;再启动一次幂等。
6. **日志无明文**:grep 全程日志/stderr,无密码、无 blob。
7. **FE**:配对向导单个「Express 登录」框、DBF/RPA 切换都在、密码不回显;真机 playwright 走配对→生成配对码一遍(对齐 P4 既有 e2e)。

> 验收用 DATAT(`\\accserver\ACCOUNT\70EXP\test`)·写前 robocopy 备份·完事 `/MIR` 还原回 8 表基线(`PITFALLS_AND_FLOW.md` §0)。

## 6. 交付

- companion:`secret_store.py` + config/pairing/pack_runner 改动 + 测试,commit 推 companion master(`D:\pearnly-companion`·无 remote·本地 master)。
- pearnly-app:FE 单输入框改动 + dist + home.html `?v=` bump,按"未验收不 push master"——**真机验收过再 push**(push 即上线)。
- 报告含:真机 7 项清单结果 + 单测数 + commit + DATAT 还原核对。
