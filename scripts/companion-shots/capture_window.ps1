# 按窗口标题或句柄抓单个窗口成 PNG(不抓全屏、不激活、不移动目标窗口)。
#
# 为什么用 PrintWindow 而不是「截屏再裁」
#   ① 截屏拿的是桌面合成结果:目标窗被别的窗口盖住、或滚出屏幕边界的部分,截到的是遮挡物
#      或空白。PrintWindow 要求窗口自己把内容重绘到给定 HDC,与叠放次序和屏幕大小无关。
#   ② 截屏会把 Zihao 桌面上碰巧开着的东西一起录进公开教程图里。PrintWindow 只画目标窗口。
#   ③ 裁剪要先知道窗口在屏幕上的坐标,多屏 / 混合 DPI 下这个坐标经常算错半个边框。
#   PW_RENDERFULLCONTENT(flags=2)是关键:不带它,DirectComposition 渲染的现代控件会画成黑块。
#
# 为什么坐标取 DWM 扩展边框而不是 GetWindowRect
#   Win10+ 的 GetWindowRect 把不可见的阴影投影边距也算进去,按它开位图会在四周留灰边。
#   DWMWA_EXTENDED_FRAME_BOUNDS 返回的是真实可见边界。
#
# 用法: powershell -NoProfile -File capture_window.ps1 -TitleLike "Pearnly*" -OwnerPid 1234 -Out shot.png
param(
  [string]$TitleLike = "*",
  [int]$OwnerPid = 0,
  [long]$Hwnd = 0,          # 直接指定句柄(无标题的弹出菜单等,按标题找不到)
  [Parameter(Mandatory=$true)][string]$Out
)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinCap {
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr l);
  public delegate bool EnumWindowsProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr h, int attr, out RECT r, int size);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("shcore.dll")] public static extern int SetProcessDpiAwareness(int v);
  public struct RECT { public int Left, Top, Right, Bottom; }
  public const int DWMWA_EXTENDED_FRAME_BOUNDS = 9;
  public const uint PW_RENDERFULLCONTENT = 2;
}
"@

# 高 DPI 下不设 DPI 感知会拿到被虚拟化的缩放坐标 → 截出来糊/裁切
try { [void][WinCap]::SetProcessDpiAwareness(2) } catch {}

$hwnd = [IntPtr]::Zero
$title = ""
if ($Hwnd -ne 0) { $hwnd = [IntPtr]$Hwnd; $title = "(by-hwnd)" }
$cb = [WinCap+EnumWindowsProc]{
  param($h, $l)
  if (-not [WinCap]::IsWindowVisible($h)) { return $true }
  if ([WinCap]::IsIconic($h)) { return $true }   # 最小化窗口抓不到内容,跳过
  $sb = New-Object System.Text.StringBuilder 512
  [void][WinCap]::GetWindowTextW($h, $sb, 512)
  $t = $sb.ToString()
  if (-not $t) { return $true }
  if ($t -notlike $script:TitleLike) { return $true }
  if ($script:OwnerPid -gt 0) {
    $p = 0; [void][WinCap]::GetWindowThreadProcessId($h, [ref]$p)
    if ($p -ne $script:OwnerPid) { return $true }
  }
  $script:hwnd = $h; $script:title = $t
  return $false
}
if ($Hwnd -eq 0) { [void][WinCap]::EnumWindows($cb, [IntPtr]::Zero) }

if ($hwnd -eq [IntPtr]::Zero) { Write-Error "no visible window matching '$TitleLike'"; exit 1 }

$r = New-Object WinCap+RECT
if ([WinCap]::DwmGetWindowAttribute($hwnd, [WinCap]::DWMWA_EXTENDED_FRAME_BOUNDS, [ref]$r, 16) -ne 0) {
  [void][WinCap]::GetWindowRect($hwnd, [ref]$r)
}
$w = $r.Right - $r.Left; $h2 = $r.Bottom - $r.Top
if ($w -le 0 -or $h2 -le 0) { Write-Error "bad window rect ${w}x${h2}"; exit 1 }

$bmp = New-Object System.Drawing.Bitmap($w, $h2)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [WinCap]::PrintWindow($hwnd, $hdc, [WinCap]::PW_RENDERFULLCONTENT)
$g.ReleaseHdc($hdc)
$g.Dispose()
if (-not $ok) { $bmp.Dispose(); Write-Error "PrintWindow failed"; exit 1 }

$dir = Split-Path -Parent $Out
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
"OK hwnd=$hwnd size=${w}x${h2} title='$title' -> $Out"
