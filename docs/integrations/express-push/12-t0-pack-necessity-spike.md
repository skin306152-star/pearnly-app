# T0 施工单 · 逆向 spike:DBF 直写单「不跑 PACK」是否报表可见

> 派自 `11-production-readiness-dispatch.md`。PM:Claude。施工窗口:在**有真 Express 的 Windows 机**上跑(本机·`D:\_express_audit` 工具链已备)。
> **本单是验证性 spike,不是改产品代码。** 目标 = 拿确定性证据回答一个问题,据此裁决 T1 删/加密。
> 入口必读:`D:\_express_audit\PITFALLS_AND_FLOW.md`(环境/坑/还原全在那)。

---

## 1. 要回答的唯一问题

> companion 的 DBF writer 写完一张单(已设 `CMPLAPP='Y'` + per-write `_reindex()` 重建 CDX),**在完全不跑 PACK** 的情况下,会计下次打开自己的 Express 看报表/放大镜,**这张单见不见得到?**

答案决定 T1 形态:
- **见得到** → 夜间 PACK 非必需 → `express_pw` 可整字段删除(首选)。
- **见不到** → 记录"差的那步具体是什么",评估能否由 writer 端补齐(免登录),否则才落到"存密码 + 无人值守 PACK"。

## 2. 背景事实(已实证 · 别重新质疑)

- `PITFALLS_AND_FLOW.md` §0:可见性关键是 `APTRN/ARTRN.CMPLAPP='Y'`(**writer 已设**),不是 STCRD 明细行。
- `dbf_writer.py:321` / `dbf_sales.py`:每次写完调 `_reindex()` 重建涉及表的 CDX。
- `config.py`:`pack_enabled` 默认 **off**;`express_pw` 唯一活跃消费者 = `pack_runner.login_and_open`(夜间 PACK 登录)。RPA 暂泊。
- 报表号:**241 = 进项赊购**、**141 = 销项赊销**(导航/日期坑见 PITFALLS §3)。
- ⚠️ 既往 `partB_write.py + p32_pack + p32_report` 的验证链**一直带着 PACK**,所以"不 PACK 是否可见"从没被干净隔离过——这正是本 spike 要补的缺口。

## 3. 账套安全铁律(每一步都守 · 违反即中止)

1. **只碰 DATAT**(`\\accserver\ACCOUNT\70EXP\test`)。真账套 PDATAT/58ASIASP/korn/57ASCRD 绝不碰。
2. **写前 robocopy 备份**,跑完 `/MIR` 还原回基线,核对 8 表行数 == 基线(PITFALLS §0 表 + §3 还原块)。
3. 任何 PACK/登录脚本自带"读弹窗真实路径"硬闸——本 spike **刻意不跑 PACK**,只在第 5 步登录看报表时用到 Express。
4. 跑脚本前置:`$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'`。

## 4. 执行步骤(确定性 · 都有现成脚本)

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
$py32='D:\py311-x86\python.exe'; $py64='C:\Users\skin3\AppData\Local\Programs\Python\Python311\python.exe'
$ts=Get-Date -Format 'yyyyMMdd-HHmmss'
```

1. **备份基线**:`robocopy '\\accserver\ACCOUNT\70EXP\test' "D:\datat_restore_src_$ts" /E /COPY:DAT`,并 `verify_baseline.py` 记录写前行数。
2. **确认 Express 未在跑**(PACK 占用检测口径):`tasklist | findstr /i expressi.exe` 应为空;若在跑先 `Stop-Process -Name ExpressI -Force`。
3. **写一张全新非存货单**:`& $py64 D:\_express_audit\partB_write.py`(写 IV + RR·落 2558 账期·走 writer 真实护栏:CMPLAPP=Y + per-write reindex)。记下本次单号(脚本打印·形如 `IV5812NN-00X`/`RR5812NN-00X`)。
   - ⚠️ 若 `partB_write.py` 单号与历史撞,改其日期/序号产新号,确保是**本次新写、PACK 从未碰过**的单。
4. **【关键:跳过 PACK】** —— 不跑任何 `p32_pack*.py`。直接进下一步。
5. **全新登录开报表查可见性**:
   - `& $py32 D:\_express_audit\p32_diag.py` → `& $py32 D:\_express_audit\p32_open_and_probe.py`(登录 BIT9/BIT9 → 公司 grid **行2=DATAT** → 工作日 31/12/2558 → 读路径验 TEST)。
   - `& $py32 D:\_express_audit\p32_report141.py run241 20151201 20151231`(进项·**月区间**)。
   - `& $py32 D:\_express_audit\p32_report141.py run141 20151201 20151231`(销项·月区间)。
   - 截图自动落 `D:\_express_audit\shots\`。在报表里**找第 3 步的单号在不在**。
   - 补充:若报表中心难判,另开采购/销售放大镜(单据查询)按单号直查一次。
6. **对照组(仅当第 5 步"见不到"时跑)**:再跑 `p32_pack.py`(硬闸 PASS 才 PACK)→ 重出同区间报表 → 确认 PACK 后**变可见**。这一步确证"差的就是 PACK 那步全系统重整",而非写错/日期错/账期错等别的原因。
7. **还原 + 清理**(PITFALLS §0):`Stop-Process -Name ExpressI -Force` → `robocopy "D:\datat_restore_src_$ts" '\\accserver\ACCOUNT\70EXP\test' /MIR` → 删 writer 自建的服务器侧 `test_pearnly_bak_*` → `verify_baseline.py` 核对 8 表行数回基线。

## 5. 判定与交付

把结论 + 截图证据写进 **`13-pack-necessity-findings.md`**,含:
- 第 3 步写的单号、写后行数 diff。
- 第 5 步**不 PACK** 时:241/141 报表 + 放大镜各自**可见/不可见**(贴图,命名 `EVIDENCE_noPACK_241_*`/`_141_*`)。
- (若不可见)第 6 步 PACK 后是否转可见(贴图)+ 推断差的是哪步。
- 还原后行数 == 基线 的核对结果。
- **一句话裁决**:`PACK 非必需 → T1 删字段` / `PACK 必需 → 评估 writer 端补齐 or 需无人值守(回 PM)`。

## 6. 红线 / 不要做

- ❌ 不改 companion 任何产品代码(纯验证·只用 `_express_audit` 脚本)。
- ❌ 不碰 DATAT 以外任何账套;不跳过备份/还原。
- ❌ 不靠"我 grep 到 CMPLAPP=Y 所以一定可见"下结论——**必须真报表/放大镜出图为准**(自欺红线:看渲染不看类名)。
- ❌ 单日区间查报表(Express 单日有 `Message#9106` 怪癖)→ 一律月区间。
- ✅ 全程命令贴进 findings,PM 读证据判,施工窗口不替 PM 下产品裁决。

## 7. 验收(PM)

PM 读 `13-pack-necessity-findings.md`:① 证据是真报表/放大镜出图、非代码推断;② 还原行数回基线(没污染 DATAT);③ 裁决与证据自洽。通过即据此发 T1(删字段 or 回 PM 议无人值守)。
