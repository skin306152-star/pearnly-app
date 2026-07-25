---
name: debug-prod-500
description: 生产报 500 / 上传失败 / 前端报 "Unexpected token '<'" / 接口没反应 / push 了线上却没变时的排障顺序 —— 先查磁盘、再查 nginx、再查 journalctl,确认跑的是新进程。线上出故障、判断"到底哪一层挂了"时用。
---

# 生产排障

先抓真因再改码。禁止靠猜。

## 1. 前端报 `Unexpected token '<', "<html>..."` → 第一嫌疑是磁盘满

不是代码 bug、不是超时、不是文件太大。真实案例:52G 盘 100% 满 → nginx 写不下上传请求体(`pwrite() failed (28: No space left on device)`)→ 返 HTML 500 → 前端 `res.json()` 炸。罪魁是 `/tmp` 堆了 28G 的 `pip-unpack-*`(每次部署 pip 解压 torch 不清理)。

```bash
ssh root@66.42.49.213 "df -h /; du -sh /tmp/* | sort -rh | head"
```

用量 >85% 先清理再部署:`rm -rf /tmp/pip-*`。

## 2. 分层定位(顺序别乱)

| 症状 | 结论 |
|---|---|
| 500 而不是 504 | 不是超时 |
| uvicorn 日志里**查不到那个 POST** | 请求卡在 nginx,没到应用 |
| nginx 日志 0 字节 | logrotate 半夜转过且没 `nginx -s reopen` → 真错误在 `error.log.1` |

```bash
ssh root@66.42.49.213 "journalctl -u mrpilot --since '5 min ago' | grep -iE 'Error|Traceback'"
ssh root@66.42.49.213 "tail -50 /var/log/nginx/error.log /var/log/nginx/error.log.1"
```

## 3. 确认你测的是新进程

`/api/version` 返 200 ≠ 新码生效。

```bash
ssh root@66.42.49.213 "systemctl show mrpilot -p ActiveEnterTimestamp"   # 要 ≥ 你 push 的时间
```

**push 了但线上没变**:git-deploy 的 fetch 撞 GitHub 超时会静默留旧 commit → ssh 重跑 `git-deploy.sh`。

## 4. 权限边界

只读诊断(查日志 / 查库 / 跑脚本 / git 操作)自己跑。**只有 prod 写操作**(装包 / 重启 / 改数据)被安全闸拦时才请 Zihao 点一下。

## 5. 数据库侧的两个真雷

- 长活事务读共享台账 × 首写时 `ensure_*` 跑 ALTER → 互等死锁,**部署后首次跑批必现**,mock 测不出来
- 生产库只读查询口子:`_gemini_key.local/dbq.py`(SELECT-only),`DATABASE_URL` 在 `_env_lines.txt`
