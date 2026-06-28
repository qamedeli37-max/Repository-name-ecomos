@'
# Stock & Crypto Watchlist Monitor
# Data Sources:
#   US Stocks: Sina Finance (hq.sinajs.cn)
#   Crypto:    Gate.io (data.gateapi.io)
param(
  [int]$AlertPct = 2,
  [int]$VolumeSpike = 2,
  [int]$CryptoPct = 2,
  [switch]$Quiet
)

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
$StateFile = Join-Path $ScriptDir 'watchlist_state.json'

$US_STOCKS = @(
  @{code='aapl'; name='Apple'},
  @{code='msft'; name='Microsoft'},
  @{code='googl'; name='Google'},
  @{code='amzn'; name='Amazon'},
  @{code='nvda'; name='NVIDIA'},
  @{code='meta'; name='Meta'},
  @{code='tsla'; name='Tesla'},
  @{code='amd'; name='AMD'},
  @{code='intc'; name='Intel'},
  @{code='crm'; name='Salesforce'},
  @{code='adbe'; name='Adobe'},
  @{code='nflx'; name='Netflix'},
  @{code='tsm'; name='TSMC'},
  @{code='asml'; name='ASML'},
  @{code='qcom'; name='Qualcomm'},
  @{code='avgo'; name='Broadcom'},
  @{code='mu'; name='Micron'},
  @{code='mrvl'; name='Marvell'},
  @{code='nke'; name='Nike'},
  @{code='dis'; name='Disney'},
  @{code='wmt'; name='Walmart'},
  @{code='cost'; name='Costco'},
  @{code='mcd'; name='McDonalds'},
  @{code='sbux'; name='Starbucks'},
  @{code='orcl'; name='Oracle'}
)

$CRYPTO_LIST = @(
  @{symbol='btc_usdt'; code='BTC'; name='Bitcoin'},
  @{symbol='eth_usdt'; code='ETH'; name='Ethereum'},
  @{symbol='sol_usdt'; code='SOL'; name='Solana'},
  @{symbol='xrp_usdt'; code='XRP'; name='XRP'},
  @{symbol='doge_usdt'; code='DOGE'; name='Dogecoin'},
  @{symbol='ada_usdt'; code='ADA'; name='Cardano'},
  @{symbol='dot_usdt'; code='DOT'; name='Polkadot'},
  @{symbol='avax_usdt'; code='AVAX'; name='Avalanche'},
  @{symbol='link_usdt'; code='LINK'; name='Chainlink'},
  @{symbol='sui_usdt'; code='SUI'; name='Sui'},
  @{symbol='bnb_usdt'; code='BNB'; name='BNB'},
  @{symbol='uni_usdt'; code='UNI'; name='Uniswap'},
  @{symbol='apt_usdt'; code='APT'; name='Aptos'},
  @{symbol='op_usdt'; code='OP'; name='Optimism'},
  @{symbol='arb_usdt'; code='ARB'; name='Arbitrum'},
  @{symbol='near_usdt'; code='NEAR'; name='NEAR'},
  @{symbol='atom_usdt'; code='ATOM'; name='Cosmos'}
)

# Helpers
function Get-BigNumber($n) {
  if ($n -ge 1e12) { return "$([math]::Round($n/1e12, 2))T" }
  if ($n -ge 1e9)  { return "$([math]::Round($n/1e9, 2))B" }
  if ($n -ge 1e6)  { return "$([math]::Round($n/1e6, 2))M" }
  return "$([math]::Round($n, 0))"
}

function Format-Price($p) {
  if ($p -ge 1000)   { return $p.ToString('N2') }
  if ($p -ge 1)      { return $p.ToString('N2') }
  if ($p -ge 0.01)   { return $p.ToString('N4') }
  return $p.ToString('N6')
}

function UpArrow($v) { if ($v -gt 0) { return '&#x1F7E2;' } elseif ($v -lt 0) { return '&#x1F534;' } else { return '&#x26AA;' } }
function Sign($v) { if ($v -gt 0) { return '+' } else { return '' } }

function Load-State {
  if (Test-Path $StateFile) {
    try { return (Get-Content $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json) } catch {}
  }
  return @{ prices=@{}; volumes=@{}; high=@{}; low={} }
}

function Save-State($state) {
  $state | ConvertTo-Json -Compress -Depth 10 | Set-Content $StateFile -Encoding UTF8
}

# Parse Sina Finance US stock CSV
function Parse-SinaLine($line) {
  # Format: var hq_str_gb_aapl="苹果,298.6700,0.92,2026-06-18 22:34:04,2.7200,298.1100,300.4599,295.6200,317.4000,195.8050,26754602,...";
  try {
    $parts = $line -split '"'
    if ($parts.Count -lt 2) { return $null }
    $csv = $parts[1] -split ','
    if ($csv.Count -lt 14) { return $null }
    
    $code = ($line -split '=')[0] -replace 'var hq_str_gb_',''
    return @{
      code = $code.ToUpper()
      name = $csv[0]
      price = [double]$csv[1]
      changePct = [double]$csv[2]
      change = [double]$csv[4]
      prevClose = [double]$csv[5]
      high = [double]$csv[6]
      low = [double]$csv[7]
      high52w = [double]$csv[8]
      low52w = [double]$csv[9]
      volume = [long]$csv[10]
      marketCap = [double]$csv[12]
    }
  } catch { return $null }
}

function Fetch-USStocks {
  $codeList = ($US_STOCKS | ForEach-Object { "gb_$($_.code)" }) -join ','
  $url = "https://hq.sinajs.cn/list=$codeList"
  try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add('Referer', 'https://finance.sina.com.cn')
    $raw = $wc.DownloadString($url)
    $lines = $raw -split "`n" | Where-Object { $_ -ne '' }
    $results = @()
    foreach ($line in $lines) {
      $r = Parse-SinaLine $line
      if ($r -and $r.price -gt 0) { $results += $r }
    }
    return $results
  } catch { return @() }
}

function Fetch-Crypto {
  $results = @()
  foreach ($c in $CRYPTO_LIST) {
    try {
      $wc = New-Object System.Net.WebClient
      $json = $wc.DownloadString("https://data.gateapi.io/api2/1/ticker/$($c.symbol)") | ConvertFrom-Json
      if ($json.result -eq 'true') {
        $results += @{
          code = $c.code
          name = $c.name
          price = [double]$json.last
          high24h = [double]$json.high24hr
          low24h = [double]$json.low24hr
          volume = [double]$json.baseVolume
          changePct = [double]$json.percentChange
        }
      }
    } catch { }
  }
  return $results
}

# ===== MAIN =====
$now = Get-Date
$timeStr = $now.ToString('yyyy-MM-dd HH:mm:ss')
$state = Load-State

$stockResults = Fetch-USStocks
$cryptoResults = Fetch-Crypto
$allAlerts = @()

# Check stock alerts
foreach ($s in $stockResults) {
  $key = "us:$($s.code)"
  $oldPrice = $state.prices.$key
  $oldVol = $state.volumes.$key
  
  if ($oldPrice -and [double]$oldPrice -gt 0) {
    $pctChange = (($s.price - [double]$oldPrice) / [double]$oldPrice) * 100
    if ([math]::Abs($pctChange) -ge $AlertPct) {
      $allAlerts += @{
        sev = 'price'
        item = "$($s.code)($($s.name))"
        detail = "短线波动 $(Sign $pctChange)$($pctChange.ToString('F2'))%"
        price = $s.price
        changePct = $pctChange
      }
    }
    
    if ($oldVol -and [long]$oldVol -gt 0 -and $s.volume -gt 0) {
      $volRatio = [double]$s.volume / [double]$oldVol
      if ($volRatio -ge $VolumeSpike) {
        $allAlerts += @{
          sev = 'volume'
          item = "$($s.code)($($s.name))"
          detail = "放量 x$($volRatio.ToString('F1'))"
          price = $s.price
          changePct = $s.changePct
        }
      }
    }
  }
  
  $state.prices | Add-Member $key $s.price -Force
  $state.volumes | Add-Member $key $s.volume -Force
}

# Check crypto alerts
foreach ($c in $cryptoResults) {
  $key = "crypto:$($c.code)"
  $oldPrice = $state.prices.$key
  
  if ($oldPrice -and [double]$oldPrice -gt 0) {
    $pctChange = (($c.price - [double]$oldPrice) / [double]$oldPrice) * 100
    if ([math]::Abs($pctChange) -ge $AlertPct) {
      $allAlerts += @{
        sev = 'price_crypto'
        item = "$($c.code)($($c.name))"
        detail = "即时波动 $(Sign $pctChange)$($pctChange.ToString('F2'))%"
        price = $c.price
        changePct = $c.changePct
      }
    }
  }
  
  if ([math]::Abs($c.changePct) -ge $CryptoPct) {
    $allAlerts += @{
      sev = '24h'
      item = "$($c.code)($($c.name))"
      detail = "24h $(Sign $c.changePct)$($c.changePct.ToString('F2'))%"
      price = $c.price
      changePct = $c.changePct
    }
  }
  
  $state.prices | Add-Member $key $c.price -Force
}

Save-State $state

# ===== OUTPUT =====
$sortedStocks = $stockResults | Sort-Object { [math]::Abs($_.changePct) } -Descending
$sortedCrypto = $cryptoResults | Sort-Object { [math]::Abs($_.changePct) } -Descending

$lines = @()
$lines += "=(Global Asset Monitor)= $timeStr CST"
$lines += ""

# Top gainers
$gainers = $sortedStocks | Where-Object { $_.changePct -gt 0 }
$losers = $sortedStocks | Where-Object { $_.changePct -lt 0 }

if ($gainers.Count -gt 0) {
  $lines += ">> UP TOP5 <<"
  $gainers | Select-Object -First 5 | ForEach-Object {
    $lines += "  G $($_.code) `$$(Format-Price $_.price)  (+$($_.changePct.ToString('F2'))%)"
  }
}

if ($losers.Count -gt 0) {
  $lines += ">> DOWN TOP5 <<"
  $losers | Select-Object -First 5 | ForEach-Object {
    $lines += "  R $($_.code) `$$(Format-Price $_.price)  ($($_.changePct.ToString('F2'))%)"
  }
}

$lines += ""

# Key stocks
$keyCodes = @('AAPL','TSLA','NVDA','MSFT','GOOGL','AMZN','META')
$lines += ">> KEY STOCKS <<"
foreach ($code in $keyCodes) {
  $s = $stockResults | Where-Object { $_.code -eq $code }
  if ($s) {
    $lines += "  $($s.code) `$$(Format-Price $s.price)  $(Sign $s.changePct)$($s.changePct.ToString('F2'))%  Vol:$(Get-BigNumber $s.volume)  MCap:$(Get-BigNumber $s.marketCap)"
  }
}
$lines += ""

# Crypto
$lines += ">> CRYPTO <<"
$sortedCrypto | ForEach-Object {
  $lines += "  $($_.code) `$$(Format-Price $_.price)  $(Sign $_.changePct)$($_.changePct.ToString('F2'))%"
}
$lines += ""

# Alerts
$highSeverityAlerts = $allAlerts | Where-Object { $_.sev -ne '24h' }
$lowSeverityAlerts = $allAlerts | Where-Object { $_.sev -eq '24h' }

if ($highSeverityAlerts.Count -gt 0) {
  $lines += "!! HIGH ALERTS !!"
  foreach ($a in $highSeverityAlerts) {
    $lines += "  !! $($a.detail) !! $($a.item) @ `$$(Format-Price $a.price)"
  }
}

if ($lowSeverityAlerts.Count -gt 0) {
  $lines += "!! 24H ALERTS !!"
  foreach ($a in $lowSeverityAlerts) {
    $lines += "  $($a.detail) $($a.item) @ `$$(Format-Price $a.price)"
  }
}

$gCount = ($stockResults | Where-Object { $_.changePct -gt 0 }).Count
$lCount = ($stockResults | Where-Object { $_.changePct -lt 0 }).Count
$cgCount = ($cryptoResults | Where-Object { $_.changePct -gt 0 }).Count
$clCount = ($cryptoResults | Where-Object { $_.changePct -lt 0 }).Count

$lines += "STOCK ${gCount}U/${lCount}D | CRYPTO ${cgCount}U/${clCount}D"

Write-Output ($lines -join "`n")
'@ | Set-Content -Path "C:\Users\Administrator\.openclaw\workspace\watchlist.ps1" -Encoding UTF8