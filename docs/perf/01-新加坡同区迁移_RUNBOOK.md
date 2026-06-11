# 新加坡同区迁移 RUNBOOK(app 日本东京 → Vultr Singapore)

> 性能 P0。根因见 `docs/perf/INTERACTION_AUDIT.md`:app 在东京、Supabase 在新加坡,
> 每条 SQL 跨区往返 69ms,2-worker 串行放大成首屏 22 请求 11.7s。
> SG 测试机实测到 Supabase RTT = **1.0ms**(69 倍差距),这是全部优化里杠杆最大的一刀。
> 执行窗口照本文逐步走;**切流量前必须 Zihao 确认**(运维拓扑不碰业务代码,但影响全站)。

## 0. 前置验证(已在跑)

| 项 | 状态 |
|---|---|
| Google Vision 可达(历史封锁风险) | SG 测试机 `139.180.185.166` 哨兵每 5 分钟打 `vision.googleapis.com`,日志 `/root/google_probe.log`。截至 2026-06-11 02:00 UTC:104 条全 `vision=403`(到达应用层=IP 干净),0 异常 |
| 通过门槛 | 日志干净 ≥24h(2026-06-11 17:26 UTC 满,≈泰国时间 06-12 00:26,正好低峰) |
| 合规 | 泰国 PDPA 无数据本地化要求;RD 不管存哪;FlowAccount 同样跑新加坡。已查实 |
| 曼谷方案 | 不可行(Supabase/Vultr 均无曼谷机房),远期再议 |

判异常:日志出现非 403(000/超时/连接失败)→ 停,报 Zihao 换机重测。

## 1. 目标机

- Vultr **Singapore**,新开正式机(测试机 root 密码两度走过聊天,**不转正**,验证完 Destroy)。
- 规格:东京现机是 1c/2G(用量 ~600M/2G、磁盘 25G/52G)。同档 vc2-1c-2gb 起步即可;
  若想给 workers=4 留余量可选 2c/4G(差价小,Zihao 拍板)。
- 开机即:导入 SSH key(本机 id_ed25519 + Zihao 的)、`PasswordAuthentication no`、ufw 放行 22/80/443。

## 2. 装机(可在切换前任意时间做,不影响线上)

```bash
apt update && apt install -y nginx git python3.12-venv certbot python3-certbot-nginx rsync
```

1. **部署 key + ssh 配置**(从日本机拷,GitHub 拉代码用):
   ```bash
   rsync -a root@45.76.53.194:/root/.ssh/{github_pearnly,github_pearnly.pub} /root/.ssh/
   rsync -a root@45.76.53.194:/root/.ssh/config /root/.ssh/config   # 含 Host github-pearnly 段
   ```
2. **代码**:`git clone git@github-pearnly:skin306152-star/pearnly-app.git /opt/mrpilot`
   然后 `git -C /opt/mrpilot remote rename origin pearnly`(git-deploy.sh 写死 `REMOTE=pearnly`;
   该脚本由 app.py 启动时自动重写,不必手拷)。
3. **venv**(最慢一步,含 torch;趁早做):
   ```bash
   python3 -m venv /opt/mrpilot/venv
   /opt/mrpilot/venv/bin/pip install -r /opt/mrpilot/requirements.txt
   /opt/mrpilot/venv/bin/playwright install --with-deps chromium
   ```
4. **数据 + 配置**(`.env` 机器对机器直拷,绝不进聊天/上下文):
   ```bash
   rsync -a root@45.76.53.194:/opt/mrpilot/.env /opt/mrpilot/.env
   rsync -a root@45.76.53.194:/opt/mrpilot/{storage,var,backups} /opt/mrpilot/
   rsync -a root@45.76.53.194:/etc/letsencrypt/ /etc/letsencrypt/
   rsync -a root@45.76.53.194:/etc/nginx/sites-available/{pearnly.com,00-default-deny} /etc/nginx/sites-available/
   rsync -a root@45.76.53.194:/etc/systemd/system/mrpilot.service /etc/systemd/system/
   ln -s /etc/nginx/sites-available/pearnly.com /etc/nginx/sites-enabled/
   ln -s /etc/nginx/sites-available/00-default-deny /etc/nginx/sites-enabled/
   rm -f /etc/nginx/sites-enabled/default && nginx -t
   ```
5. **起服务**:`systemctl daemon-reload && systemctl enable --now mrpilot nginx`
   (unit 保持 `--workers 2` 原样;workers=4 另有 DDL advisory lock 前置,不混进本次)。
6. **本机自检**(还没切流量,用 Host 头打):
   ```bash
   curl -s http://127.0.0.1:7860/api/health
   curl -sk https://127.0.0.1/api/version -H 'Host: pearnly.com'
   journalctl -u mrpilot --since '5 min ago' | grep -ciE 'error|traceback'   # 应为 0
   ```

## 3. 切换(低峰 · Zihao 确认后才动)

DNS 在 **Cloudflare 且橙云代理**(pearnly.com 解析到 Cloudflare IP,源站 IP 对外不可见),
所以切换 = Cloudflare 面板改 A 记录源站 IP,**秒级生效,无 DNS 传播等待**。

1. 切前最后一次增量同步:`rsync -a root@45.76.53.194:/opt/mrpilot/{storage,var}/ ...`(追平切换间隙新落盘的票图)。
2. Cloudflare DNS:`pearnly.com` + `www` 的 A 记录 45.76.53.194 → 新机 IP(保持橙云)。
3. 观察 15 分钟:
   - `curl https://pearnly.com/api/version` 200;
   - 新机 `journalctl -u mrpilot -f` 无 ERROR;日本机 access log 流量归零;
   - 真账号过一遍:登录 → 首屏(感受提速)→ 传一张真票 OCR(验 Google Vision 出口)→ LINE 发图(验 webhook,走 Cloudflare 与源站 IP 无关);
   - 推一个 docs commit 验 GitHub webhook → 自动部署链路(webhook 打 pearnly.com,自动跟着 DNS 走)。
4. **回滚**:Cloudflare 把源站 IP 改回 45.76.53.194,秒级。日本机切换后**原样保留 ≥1 周**不动。

## 4. 风险对照

| 风险 | 结论 |
|---|---|
| Google Vision 封 IP | 哨兵 24h 实测干净(本次迁移的唯一硬前置) |
| LINE webhook / Bot | 配置的是 https://pearnly.com URL,走 Cloudflare,不感知源站 IP |
| Gmail SMTP | 账号鉴权无 IP 白名单,出口 IP 变化无影响 |
| Supabase 连接 | Pooler 连接串不限源 IP;同区后连接更稳 |
| 票图/PDF 本地盘 | `storage/`+`var/` rsync 两次(装机一次+切前增量) |
| 证书续期 | letsencrypt 整目录拷过来,到期 certbot 在新机正常续(nginx 插件配置随 sites-available 走) |

## 5. 收尾(切换稳定后)

1. **密钥轮换(顺手清 06-08 泄漏债)**:迁移后全套密钥本就过手,是轮换 `DATABASE_URL` 密码 /
   `JWT_SECRET`(会全员登出,低峰做)/ LINE token 的最佳时机。高敏,Zihao 在场逐项做。
2. SG 测试机 `139.180.185.166` Destroy(密码已泄,不留);观察期满退订日本机。
3. 更新文档里的服务器 IP(`AGENTS.md` §5、`CLAUDE.md/CLAUDE.md` 服务器表、相关 memory)。
4. 记忆 `sg-migration-probe-inflight` 改写为 shipped。
