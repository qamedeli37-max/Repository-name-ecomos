---
name: proxy-diagnostics
description: "Check Clash Verge proxy status, test node connectivity, subscription health, and network diagnostics."
---

# Proxy Diagnostics

Fast checkup for 科学上网/翻墙 connectivity. Use when user says their proxy/机场 is down, slow, or not working.

## Quick status check

```powershell
# 1. Is Clash Verge running?
Get-Process clash-verge -ErrorAction SilentlyContinue | Format-Table Id, StartTime, CPU, WorkingSet64

# 2. Check config dir
$clashDir = "$env:APPDATA\io.github.clash-verge-rev.clash-verge-rev"
Get-ChildItem $clashDir -Filter *.yaml | Select-Object Name, Length, LastWriteTime

# 3. Check recent logs for errors
Get-Content "$clashDir\logs\latest.log" -Tail 20
```

## Subscription health

```powershell
# Check if subscription URL responds
$profile = Get-Content "$env:APPDATA\io.github.clash-verge-rev.clash-verge-rev\profiles.yaml"
$url = ($profile | Select-String -Pattern "url:\s*(.+)" | ForEach-Object { $_.Matches.Groups[1].Value }) | Select-Object -First 1
if ($url) {
    try { $r = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 10 -UseBasicParsing; Write-Host "Sub OK: $($r.StatusCode)" }
    catch { Write-Host "Sub FAIL: $_" }
}
```

## Node connectivity test

```powershell
# Test proxy server reachability (ping)
$servers = @("tqt-cn2.woaitutu520.com", "h-k-t.51feitu.com")  # update based on actual config
foreach ($s in $servers) { Test-Connection -ComputerName $s -Count 1 -Quiet }
```

## Throughput test (via Clash proxy)

```powershell
$proxy = New-Object System.Net.WebProxy("http://127.0.0.1:7897")
$wc = New-Object System.Net.WebClient
$wc.Proxy = $proxy
try { $wc.DownloadString("https://www.google.com/generate_204"); Write-Host "Proxy OK" }
catch { Write-Host "Proxy FAIL: $_" }
$wc.Dispose()
```

## Subscription info (桐希's淘气兔)

Subscription URL pattern: `http://47.97.81.77:88/tqt/tk/<token>`
Server domains: `tqt-cn2.woaitutu520.com`, `h-k-t.51feitu.com`
Website panel: `woaitutu520.com` (often 502)

Read remaining traffic, expiry date from proxy node names:

```powershell
Get-Content "$env:APPDATA\io.github.clash-verge-rev.clash-verge-rev\profiles\*.yaml" |
  Select-String -Pattern "剩余流量|到期|重置|套" | Select-Object -First 5
```

Check subscription from profiles.yaml:

```powershell
Get-Content "$env:APPDATA\io.github.clash-verge-rev.clash-verge-rev\profiles.yaml" |
  Select-String -Pattern "url:|upload:|download:|total:|expire:|name:" | Select-String -NotMatch "Merge|Script|merge|script"
```
