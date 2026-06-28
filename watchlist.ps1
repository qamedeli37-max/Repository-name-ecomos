param(
  [int]$AlertPct = 2,
  [int]$VolumeSpike = 3,
  [int]$CryptoPct = 2
)

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
$StateFile = Join-Path $ScriptDir 'watchlist_state.json'

$US_STOCKS = @(
  @{code='aapl'; name='Apple'}, @{code='msft'; name='Microsoft'}, @{code='googl'; name='Google'},
  @{code='amzn'; name='Amazon'}, @{code='nvda'; name='NVIDIA'}, @{code='meta'; name='Meta'},
  @{code='tsla'; name='Tesla'}, @{code='amd'; name='AMD'}, @{code='intc'; name='Intel'},
  @{code='crm'; name='Salesforce'}, @{code='adbe'; name='Adobe'}, @{code='nflx'; name='Netflix'},
  @{code='tsm'; name='TSMC'}, @{code='asml'; name='ASML'}, @{code='qcom'; name='Qualcomm'},
  @{code='avgo'; name='Broadcom'}, @{code='mu'; name='Micron'}, @{code='mrvl'; name='Marvell'},
  @{code='nke'; name='Nike'}, @{code='dis'; name='Disney'}, @{code='wmt'; name='Walmart'},
  @{code='cost'; name='Costco'}, @{code='mcd'; name='McDonalds'}, @{code='sbux'; name='Starbucks'},
  @{code='orcl'; name='Oracle'}, @{code='pltr'; name='Palantir'}
)

$CRYPTO_LIST = @(
  @{symbol='btc_usdt'; code='BTC'; name='Bitcoin'}, @{symbol='eth_usdt'; code='ETH'; name='Ethereum'},
  @{symbol='sol_usdt'; code='SOL'; name='Solana'}, @{symbol='xrp_usdt'; code='XRP'; name='XRP'},
  @{symbol='doge_usdt'; code='DOGE'; name='Dogecoin'}, @{symbol='ada_usdt'; code='ADA'; name='Cardano'},
  @{symbol='dot_usdt'; code='DOT'; name='Polkadot'}, @{symbol='avax_usdt'; code='AVAX'; name='Avalanche'},
  @{symbol='link_usdt'; code='LINK'; name='Chainlink'}, @{symbol='sui_usdt'; code='SUI'; name='Sui'},
  @{symbol='bnb_usdt'; code='BNB'; name='BNB'}, @{symbol='uni_usdt'; code='UNI'; name='Uniswap'},
  @{symbol='apt_usdt'; code='APT'; name='Aptos'}, @{symbol='op_usdt'; code='OP'; name='Optimism'},
  @{symbol='arb_usdt'; code='ARB'; name='Arbitrum'}, @{symbol='near_usdt'; code='NEAR'; name='NEAR'},
  @{symbol='atom_usdt'; code='ATOM'; name='Cosmos'}, @{symbol='sei_usdt'; code='SEI'; name='Sei'},
  @{symbol='strk_usdt'; code='STRK'; name='StarkNet'}
)

function Get-Big($n) {
  if ($n -ge 1e12) { return "$([math]::Round($n/1e12, 2))T" }
  if ($n -ge 1e9)  { return "$([math]::Round($n/1e9, 2))B" }
  if ($n -ge 1e6)  { return "$([math]::Round($n/1e6, 2))M" }
  return "$([math]::Round($n, 0))"
}

function Fmt-Price($p) {
  if ($p -ge 1000)  { return $p.ToString('N2') }
  if ($p -ge 1)     { return $p.ToString('N2') }
  if ($p -ge 0.01)  { return $p.ToString('N4') }
  return $p.ToString('N6')
}

function Sign($v) { if ($v -gt 0) { return '+' } else { return '' } }

function Load-State {
  if (Test-Path $StateFile) {
    try { return (Get-Content $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json) } catch {}
  }
  return @{ prices=@{}; volumes=@{} }
}

function Save-State($state) {
  $state | ConvertTo-Json -Compress -Depth 10 | Set-Content $StateFile -Encoding UTF8
}

function Parse-Sina($line) {
  try {
    $parts = $line -split '"'
    if ($parts.Count -lt 2) { return $null }
    $csv = $parts[1] -split ','
    if ($csv.Count -lt 14) { return $null }
    $code = (($line -split '=')[0] -replace 'var hq_str_gb_','').ToUpper()
    return @{
      code = $code; name = $csv[0]
      price = [double]$csv[1]; changePct = [double]$csv[2]
      change = [double]$csv[4]; prevClose = [double]$csv[5]
      high = [double]$csv[6]; low = [double]$csv[7]
      high52w = [double]$csv[8]; low52w = [double]$csv[9]
      volume = [long]$csv[10]; marketCap = [double]$csv[12]
    }
  } catch { return $null }
}

function Fetch-US {
  $cl = ($US_STOCKS | ForEach-Object { "gb_$($_.code)" }) -join ','
  try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add('Referer', 'https://finance.sina.com.cn')
    $raw = $wc.DownloadString("https://hq.sinajs.cn/list=$cl")
    $results = @()
    foreach ($line in ($raw -split "`n" | Where-Object { $_ -match 'hq_str' })) {
      $r = Parse-Sina $line
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
      $wc.Headers.Add('User-Agent', 'Mozilla/5.0')
      $json = $wc.DownloadString("https://data.gateapi.io/api2/1/ticker/$($c.symbol)") | ConvertFrom-Json
      if ($json.result -eq 'true') {
        $results += @{
          code = $c.code; name = $c.name
          price = [double]$json.last
          high24h = [double]$json.high24hr; low24h = [double]$json.low24hr
          volume = [double]$json.baseVolume
          changePct = [double]$json.percentChange
        }
      }
    } catch { }
    Start-Sleep -Milliseconds 50
  }
  return $results
}

# ===== MAIN =====
$now = Get-Date
$timeStr = $now.ToString('yyyy-MM-dd HH:mm:ss')
$state = Load-State

$stocks = Fetch-US
$cryptos = Fetch-Crypto
$alerts = @()

# Stock alerts
foreach ($s in $stocks) {
  $key = "us:$($s.code)"
  $op = $state.prices.$key
  $ov = $state.volumes.$key
  
  if ($op -and [double]$op -gt 0) {
    $pc = (($s.price - [double]$op) / [double]$op) * 100
    if ([math]::Abs($pc) -ge $AlertPct) {
      $alerts += @{level='PRICE'; item="$($s.code)($($s.name))"; msg="短线 $(Sign $pc)$($pc.ToString('F2'))%"; px=$s.price; cp=$s.changePct}
    }
    if ($ov -and [long]$ov -gt 0 -and $s.volume -gt 0) {
      $vr = [double]$s.volume / [double]$ov
      if ($vr -ge $VolumeSpike) {
        $alerts += @{level='VOLUME'; item="$($s.code)($($s.name))"; msg="放量 x$($vr.ToString('F1'))"; px=$s.price; cp=$s.changePct}
      }
    }
  }
  $state.prices | Add-Member $key $s.price -Force
  $state.volumes | Add-Member $key $s.volume -Force
}

# Crypto alerts
foreach ($c in $cryptos) {
  $key = "crypto:$($c.code)"
  $op = $state.prices.$key
  
  if ($op -and [double]$op -gt 0) {
    $pc = (($c.price - [double]$op) / [double]$op) * 100
    if ([math]::Abs($pc) -ge $AlertPct) {
      $alerts += @{level='CRYPTO'; item="$($c.code)($($c.name))"; msg="即时 $(Sign $pc)$($pc.ToString('F2'))%"; px=$c.price; cp=$c.changePct}
    }
  }
  if ([math]::Abs($c.changePct) -ge $CryptoPct) {
    $alerts += @{level='24H'; item="$($c.code)($($c.name))"; msg="24h $(Sign $c.changePct)$($c.changePct.ToString('F2'))%"; px=$c.price; cp=$c.changePct}
  }
  $state.prices | Add-Member $key $c.price -Force
}

Save-State $state

# ===== OUTPUT =====
$ss = $stocks | Sort-Object { [math]::Abs($_.changePct) } -Descending
$sc = $cryptos | Sort-Object { [math]::Abs($_.changePct) } -Descending

$lines = @()
$lines += "====== Global Asset Monitor ======"
$lines += "Time: $timeStr CST"
$lines += ""

$gainers = $ss | Where-Object { $_.changePct -gt 0 }
$losers = $ss | Where-Object { $_.changePct -lt 0 }

if ($gainers.Count -gt 0) {
  $lines += ">> TOP GAINERS <<"
  $gainers | Select-Object -First 5 | ForEach-Object {
    $lines += "  + $($_.code) `$$(Fmt-Price $_.price)  (+$($_.changePct.ToString('F2'))%)"
  }
}
if ($losers.Count -gt 0) {
  $lines += ">> TOP LOSERS <<"
  $losers | Select-Object -First 5 | ForEach-Object {
    $lines += "  - $($_.code) `$$(Fmt-Price $_.price)  ($($_.changePct.ToString('F2'))%)"
  }
}
$lines += ""

$lines += ">> KEY STOCKS <<"
$keyCodes = @('AAPL','TSLA','NVDA','MSFT','GOOGL','AMZN','META')
foreach ($kc in $keyCodes) {
  $s = $stocks | Where-Object { $_.code -eq $kc }
  if ($s) {
    $lines += "  $($s.code) `$$(Fmt-Price $s.price)  $(Sign $s.changePct)$($s.changePct.ToString('F2'))% | Vol:$(Get-Big $s.volume) | Cap:$(Get-Big $s.marketCap)"
  }
}
$lines += ""

$lines += ">> CRYPTO <<"
$sc | ForEach-Object {
  $lines += "  $($_.code) `$$(Fmt-Price $_.price)  $(Sign $_.changePct)$($_.changePct.ToString('F2'))%"
}
$lines += ""

$urgent = $alerts | Where-Object { $_.level -ne '24H' }
$daily = $alerts | Where-Object { $_.level -eq '24H' }

if ($urgent.Count -gt 0) {
  $lines += "!! ALERTS: PRICE/VOLUME !!"
  foreach ($a in $urgent) {
    $lines += "  ! $($a.msg) -> $($a.item) @ `$$(Fmt-Price $a.px)"
  }
}
if ($daily.Count -gt 0) {
  $lines += "!! ALERTS: 24H CHANGE !!"
  foreach ($a in $daily) {
    $lines += "  $($a.msg) -> $($a.item) @ `$$(Fmt-Price $a.px)"
  }
}

$gc = ($stocks | Where-Object { $_.changePct -gt 0 }).Count
$lc = ($stocks | Where-Object { $_.changePct -lt 0 }).Count
$cgc = ($cryptos | Where-Object { $_.changePct -gt 0 }).Count
$clc = ($cryptos | Where-Object { $_.changePct -lt 0 }).Count

$lines += ""
$lines += "SUMMARY: | Stocks ${gc}U/${lc}D | Crypto ${cgc}U/${clc}D"

Write-Output ($lines -join "`n")
