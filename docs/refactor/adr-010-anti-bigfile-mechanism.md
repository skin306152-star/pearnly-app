# ADR-010 · 防屎山 4 件套机械闸(Anti-bigfile Mechanism)

**状态**:Accepted(2026-05-28 · 窗口 C 拍 · REFACTOR-WC-P4)
**关联铁律**:#17(新功能 4 不许)· #21(整改期不污染未来整顿)· #23(8 条硬门槛)· **#27(防屎山 4 条)· #28(新功能 4 问)**
**关联代码**:`scripts/check_file_size.py` · `scripts/check_line_ratchet.py` · `.github/workflows/ci.yml` `lint-size` job · `tests/unit/test_anti_bigfile.py`

---

## 1. 背景(Context)

Pearnly 的巨石史:

| 文件 | 整顿前(2026-05-22) | 一夜自主 loop 后(2026-05-28)| 目标 |
|---|---|---|---|
| `app.py` | 10,060 行 | 3,288 行 | < 500 |
| `db.py` | 9,255 行 | 819 行 | < 500 |
| `home.js` | 33,768 行(单函数 12,694)| 6,190 行 | < 200 |
| `home.html` | 6,568 行 | 4,410 行 | < 1,000 |
| `home.css` | 16,124 行 | 0 行 | < 500 |
| `auth_signup.py` | 2,400+ | 2,379 | < 500 |
| `login.html` | 5,000+ | 4,997 | < 1,000 |

整顿期(2026-05-22 起约 5-8 个月)在做"拆 + 删"· 已立 12 条铁律(#17 / #21 / #23 等)预防"再塞巨石"。

**问题**:**全靠人自律**。
- 铁律 #17 / #21 / #23 都是"不许塞"的预防 · 没有 CI 兜底
- AI vibe-code(Claude / Codex / Copilot)+ 接力 agent 多 · 自律失效成本极低
- 拆完一个台阶(如 db.py 9k → 1k)· 没机械闸防"下次糊回去"

**真实风险案例**(本会话观察):
- 2026-05-28 一夜自主 loop 抽出 13 个 service 域 · db.py 拆掉 -48% · 但若下一波"新功能"窗口不读铁律 #21,
  仍可能直接在 db.py 加 `def get_new_feature_data()` · 因为"看起来还有空间"
- home.js 拆 v2 模块过程中,有几次差点在 home.js 里加 IIFE 兼容 shim(铁律 #17 第 4 条更正过)
- 现在没有任何"行数比上 commit 多就 CI 红"的机制 · 全靠 reviewer 抓

**Zihao 2026-05-28 拍板**:窗口 C 期间做 4 件套机械闸 · 不靠人自律 · 塞了就 CI 红。

---

## 2. 决策(Decision)

立**防屎山 4 件套机械闸**(铁律 #27)· 自动化兜底铁律 #17 / #21 / #23:

### 件 #1 · 文件行数硬上限 ≤ 500(`scripts/check_file_size.py`)

**核心规则**:
- 任何"代码文件"超 500 行 = fail
- 监控范围:历史巨石(7 个根文件)+ 所有 `*_routes.py` + 所有 `services/**/*.py` + 所有 `src/home/**/*.{js,css}`
- 例外白名单:`EXEMPT_CURRENT_BIG_FILES` 字典(历史巨石短期豁免 · 写当前实际行数 · 棘轮强制只准减不准增)

**为什么 500**:
- Google 内部惯例(C++ Style Guide):函数尽量 < 40 行,文件 < 1000 但理想 < 500
- Anthropic Claude code 推荐(整顿期目标):每个文件 100-500 行
- Pearnly 现有 1641 个单测多数 < 200 行 · 拆得动就拆 · 真不行豁免一段时间

**例外**:
- `tests/` / `scripts/` / `static/dist/` / `node_modules/` 等:不算业务代码 · 路径模式豁免
- `static/i18n-data.js`(2499 key × 4 语 = ~10k 行词典):数据 · 不是代码

### 件 #2 · 行数棘轮 · 只许减不许增(`scripts/check_line_ratchet.py`)

**核心规则**:
- 任何 commit 让监控文件净增长(`+N - -M > 0`)= fail
- 透明豁免:commit message 显式包含 `RATCHET-EXEMPT: <file> +<N> · <理由> · 删除 deadline = <vXXX>`

**实现**:跑 `git diff HEAD~1..HEAD --numstat` · 解析监控文件 · 净增长 > 0 即 fail

**为什么允许透明豁免**:
- 现实中需要"加 4 行兼容 shim"等场景(本会话 charge.py / billing 抽出时多次)
- 完全禁止会逼 reviewer 拒所有 PR · 反而走"绕过自律"路径
- 透明豁免 = 必须 commit message 写明白 + 设 deadline · 整顿期 grep 能审计

### 件 #3 · 新功能必带独立文件 + ≥ 1 测试

**核心规则**(铁律 #27.3 + #28 新功能 4 问):
- 写新功能前必答 4 问:① 领域 ② 新建文件确切路径 ③ 测试在哪 ④ 删什么旧文件
- 落地依赖 PR 模板自检 + reviewer 拍门(CI 端难真验"是不是新功能" · 主要靠人)
- 强化措辞:新增 `xxx_routes.py` 必带 `tests/unit/test_xxx_routes_contract.py`(已有 30+ 例)

**为什么不能 CI 强制**:
- "是不是新功能"是 semantic · 不是 syntactic · CI 看不懂
- 只能用"新加 router 必带对应 test"等 syntactic heuristic · 但容易绕(改名 / 嵌入)
- 铁律 #28 的真正威力在 AI / 人 写代码前的 30 秒强制问答 · 是流程而非工具

### 件 #4 · 替换旧实现必须同 PR 删旧代码

**核心规则**(铁律 #27.4):
- 抽 `services/X/foo.py` 出 `db.py` · 同一 commit 必删 db.py 老 `foo` 函数(本会话 B2 拆搬删模式实证)
- 反例:留两套并存"先观察一阵子" · 那一阵子永远不到

**例外**:re-export shim(同函数名 + `as` 别名)可保留 · 必须打 `# 兼容 re-export · 删除 deadline = vXXX` 注释 · deadline 过下个窗口必须先删

---

## 3. 替选方案(Alternatives Considered)

### 替选 A · 只靠 reviewer 拍门(现状)
- ✅ 灵活
- ❌ 自律失效成本低 · AI vibe-code + 接力多 → 必然糊回去
- ❌ 已经踩过坑(home.js 单函数 12,694 行就是这么来的)
- **拒绝**:全靠人 = 必然失败,机械闸是底线

### 替选 B · pre-commit hook(本地强制)
- ✅ 比 CI 早一步抓
- ❌ 本地可绕过(`--no-verify`)· 不可信
- ❌ 多 OS 配置烦(Windows + macOS + Linux)· 维护成本
- **不选**:转上 CI · 留 pre-commit 为可选

### 替选 C · 改 git hooks server-side(GitHub pre-receive)
- ✅ 不可绕
- ❌ GitHub 私库需要 Enterprise(贵)· 现状是 Pro 私库
- **不可行**

### 替选 D · 一刀切 fail 模式(立刻挡 push)
- ✅ 最快见效
- ❌ 历史巨石(home.js 6190 / app.py 3288 / db.py 819 等)目前没拆完,立 fail 模式 = 所有 push 都红
- ❌ 整顿期主线 push 不动 = 项目停摆
- **拒绝**:必须 warning 模式过渡 · 等 Loop 1 拆完巨石再切

### 替选 E · 给所有文件一个统一 ceiling(如 800)
- ✅ 简单
- ❌ 仍然容忍"800 行的中等巨石"· 没真正激励拆模块
- **不选**:500 更激进 · 例外走"豁免清单 + 棘轮" combo · 拆完台阶就把豁免值往下调

### 替选 F · 用第三方工具(SonarQube / CodeClimate / qlty)
- ✅ 功能多
- ❌ 收费 / 自建运维成本高
- ❌ Pearnly 整顿期定位是"工具简单 · 概念清晰" · 不引复杂依赖
- **不选**:两个 Python 脚本 + 19 守门测试 < 1000 行 · 完全够用 · 维护成本极低

---

## 4. 实现(Implementation)· 2026-05-28 已落地

### 4.1 脚本

| 文件 | 行数 | 用途 |
|---|---|---|
| `scripts/check_file_size.py` | ~220 | 件 #1 · 文件超 500 行 fail |
| `scripts/check_line_ratchet.py` | ~250 | 件 #2 · 净增长 fail + 透明豁免 |

零依赖(纯 Python 标准库)· 任何 Python 3.11 环境跑得动。

### 4.2 CI 集成

`.github/workflows/ci.yml` 加 `lint-size` job(跟 `lint` / `test` job 并列):
```yaml
lint-size:
  name: lint-size (REFACTOR-WC-P1 · anti-bigfile · WARNING mode)
  runs-on: ubuntu-latest
  continue-on-error: true  # warning 模式 · 红但不挡 push
  steps:
    - name: Checkout (full history · 棘轮需要 HEAD~1)
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - name: 防屎山闸 #1 · 文件行数 ≤ 500
      run: python scripts/check_file_size.py
    - name: 防屎山闸 #2 · 棘轮 · 监控文件只许减不许增
      run: |
        if [ "${{ github.event_name }}" = "pull_request" ]; then
          python scripts/check_line_ratchet.py --base origin/${{ github.base_ref }} --head HEAD
        else
          python scripts/check_line_ratchet.py
        fi
```

### 4.3 守门测试

`tests/unit/test_anti_bigfile.py` · 19 测试:
- `CheckFileSizeTests` × 9:count_lines / CRLF 不重复 / 空文件 / 缺失 / 路径豁免 / OK / FAIL / at-limit / 监控范围一致性
- `CheckLineRatchetTests` × 7:首 commit 优雅 / 缩减放行 / 净增长 fail / RATCHET-EXEMPT 放行 / 非监控不报 / services 增长 fail / routes 增长 fail
- `CheckFileSizeIsMonitoredTests` × 1:两脚本根文件清单一致

跑法:`python -m unittest tests.unit.test_anti_bigfile -v` · 19/19 PASS。

### 4.4 文档

- CLAUDE.md 加铁律 #27(4 条防屎山)+ #28(新功能 4 问)· 项目宪法层
- 本 ADR(决策记录)
- `docs/ONBOARDING.md` §6 / `docs/refactor/WINDOW_C_COMPLETE.md`(收尾)

---

## 5. 切硬门触发条件(Switch to fail mode)

**当前(2026-05-28 起)**:`continue-on-error: true` warning 模式 · CI 红但不挡 push。

**切 fail 模式的两个必要条件**:
1. `python scripts/refactor_progress.py` 显示**代码规模平均 ≥ 80%**
2. **Zihao 拍板"切硬门"**

**切的方式**:
- 编辑 `.github/workflows/ci.yml` · 删 `lint-size` job 下的 `continue-on-error: true` 一行
- commit message:`chore(ci): 防屎山闸切 fail 模式 · 整顿期硬门激活 · REFACTOR-WC-G8`
- 此后任何 commit 涨监控文件 = CI 红挡 push · 整顿期就不会再糊回去

**预估时机**:
- 主控估计:Loop 1(app.py / home.js / home.html 巨石拆解)再跑 30-50 轮 · 2026-08 前能到 80%
- 期间发现"已豁免文件"行数掉到 500 以下 · 同步把它从 `EXEMPT_CURRENT_BIG_FILES` 字典里删条目

---

## 6. 风险 & 缓解(Risks & Mitigations)

| 风险 | 触发概率 | 缓解 |
|---|---|---|
| 棘轮误伤合理 commit(如拆出一个 service 但 db.py 净增 4 行 shim)| 中 | 透明豁免:commit 加 `RATCHET-EXEMPT: <file> +<N> · 理由` |
| 历史巨石豁免值"先到这里"· 不真往下拆 | 低 | refactor_progress.py 每月跑 · 数字没动 = Zihao 追责 |
| 切 fail 模式时机错(早了挡 push / 晚了无意义)| 中 | 80% 阈值是经验值 · Zihao 拍板决定真正切换时机 |
| AI 接力不读铁律 #28 · 直接塞巨石 | 高 | PR 模板 + CODEOWNERS auto-review + 月度审计(grep `REFACTOR-` commit) |
| 监控清单维护(两脚本 / refactor_progress 不一致)| 低 | `tests/unit/test_anti_bigfile.py::test_two_scripts_root_files_match` 守门 |

---

## 7. 验证(How we'll know it works)

**短期(整顿期内 · 1-3 个月)**:
- `scripts/check_file_size.py` 跑出来的违规清单 · 每月减少(意味拆出的模块都 ≤ 500)
- `scripts/check_line_ratchet.py` 跑出来的净增长违规数 → 长期 0(说明没人在巨石里加东西)
- `RATCHET-EXEMPT:` commit 数量低(< 5/月)· 高了说明铁律 #27.4 没落实

**中期(整顿期末 · 5-8 个月)**:
- `EXEMPT_CURRENT_BIG_FILES` 字典里条目 = 0(所有历史巨石都拆到 < 500)
- `lint-size` job 切到 fail 模式 · 跑全绿
- Pearnly 综合进度 ≥ 90%(refactor_progress.py)

**长期(整顿期后)**:
- 新功能进来一律走"新建独立文件 + 带测试"
- 老开发回来不需要 30 分钟摸索"这功能塞哪儿"· 看目录结构 + 铁律 #28 4 问就能写

---

## 8. 后续相关 ADR

- ADR-011 · 3 窗口并行策略(本 ADR 是窗口 C 产出 · ADR-011 写 3 窗口分工)
- 未来:ADR-012 · 切 fail 模式 retrospective(切完之后写 · 总结实际效果)

---

## 9. 参考

- CLAUDE.md 铁律 #17 / #21 / #23 / #27 / #28
- ADR-007 services 抽取
- ADR-008 batch 并行重构
- ADR-009 自主重构 loop
- `scripts/refactor_progress.py`(整顿进度数字)
- `tests/unit/test_anti_bigfile.py`(守门测试)
- Google C++ Style Guide(行数 / 函数大小经验值)
