# 编排:起一个隔离的配对窗子进程,在它摆好每个状态时用 PrintWindow 抓它自己的窗口。
#
# 分成两个进程是被迫的:PrintWindow 是同步消息,发给自己窗口会在自己的事件循环里死锁。
# 于是 driver.py 摆状态、写 state.txt 交棒,本脚本抓完写 go.txt 放行,来回握手。
#
# 隔离在这里落地(三条,缺一条就会碰到 Zihao 在用的那个实例):
#   ① APPDATA 指向 scratch 副本 —— companion config.py 在 import 期就按 %APPDATA%/Pearnly
#      定死配置与日志路径,不改这个环境变量就会写花在用实例的 companion.json。
#   ② PEARNLY_EXPRESS_ROOT 指向虚构数据根(make_fixture.py 造),不读真账套。
#   ③ -OwnerPid 锁死子进程 —— 按标题找窗时,杜绝误抓到在用实例弹出的同名窗口。
#
# 用法: powershell -NoProfile -File orchestrate.ps1 -Lang zh
#       powershell -NoProfile -File orchestrate.ps1 -Lang zh -Empty   # 出「未找到 Express」那张
param(
  [Parameter(Mandatory=$true)][ValidateSet("zh","th")][string]$Lang,
  [switch]$Empty,
  [string]$Work = (Join-Path $env:TEMP "pearnly-companion-shots"),
  [string]$Python = "C:\Users\skin3\AppData\Local\Programs\Python\Python311\python.exe"
)

$ErrorActionPreference = "Stop"
$Out = Resolve-Path (Join-Path $PSScriptRoot "..\..\static\guide\shots")
$Cap = Join-Path $PSScriptRoot "capture_window.ps1"
$Drv = Join-Path $PSScriptRoot "driver.py"
$HS  = Join-Path $Work "hs_$Lang"

if (Test-Path $HS) { Remove-Item -Recurse -Force $HS }
New-Item -ItemType Directory -Force $HS | Out-Null
New-Item -ItemType Directory -Force $Out | Out-Null

$env:APPDATA = Join-Path $Work "fakeappdata"
New-Item -ItemType Directory -Force $env:APPDATA | Out-Null
$env:PYTHONIOENCODING = "utf-8"
if ($Empty) {
  Remove-Item Env:\PEARNLY_EXPRESS_ROOT -ErrorAction SilentlyContinue
} else {
  $env:PEARNLY_EXPRESS_ROOT = Join-Path $Work "express\69EXP"
}

$argv = @($Drv, $Lang, $Out, $HS)
if ($Empty) { $argv += "--expect-empty" }
$log = Join-Path $HS "driver.log"
$err = Join-Path $HS "driver.err"
$p = Start-Process -FilePath $Python -ArgumentList $argv -PassThru -NoNewWindow -RedirectStandardOutput $log -RedirectStandardError $err
"driver pid=$($p.Id)"

$state = Join-Path $HS "state.txt"
$deadline = (Get-Date).AddSeconds(300)
$seen = @{}
while ((Get-Date) -lt $deadline) {
  if ($p.HasExited) { "driver exited code=$($p.ExitCode)"; break }
  if (Test-Path $state) {
    $s = (Get-Content $state -Raw).Trim()
    if ($s -eq "DONE") { "driver done"; break }
    if ($s -like "READY:*" ) {
      $rest = $s.Substring(6).Split(":")   # <tag>[:<hwnd>] —— 无标题的弹出菜单按句柄抓
      $tag = $rest[0]
      $hw = 0
      if ($rest.Count -gt 1) { $hw = [long]$rest[1] }
      if (-not $seen.ContainsKey($tag)) {
        $seen[$tag] = $true
        Start-Sleep -Milliseconds 700   # 等 Qt 把这一帧真画完,否则抓到过渡态
        $shot = switch ($tag) {
          "pairwindow" { "setup-01-pairwindow" }
          "advanced"   { "setup-04-advanced" }
          "traymenu"   { "setup-06-traymenu" }
          "noexpress"  { "setup-07-noexpress" }
          default      { "setup-xx-$tag" }
        }
        $dest = Join-Path $Out "$shot.$Lang.png"
        if ($hw -ne 0) {
          & powershell -NoProfile -ExecutionPolicy Bypass -File $Cap -Hwnd $hw -Out $dest
        } else {
          & powershell -NoProfile -ExecutionPolicy Bypass -File $Cap -TitleLike "Pearnly*" -OwnerPid $p.Id -Out $dest
        }
        Set-Content -Path (Join-Path $HS "go.txt") -Value $tag -Encoding ascii -NoNewline
      }
    }
  }
  Start-Sleep -Milliseconds 250
}
if (-not $p.HasExited) { Start-Sleep -Seconds 3 }
if (-not $p.HasExited) { $p.Kill() }
"--- driver stdout ---"
if (Test-Path $log) { Get-Content $log }
"--- driver stderr ---"
if (Test-Path $err) { Get-Content $err }
