// Stock & Crypto Monitor - v2
const EASTMONEY_BASE = 'https://push2.eastmoney.com/api/qt/stock/get';
const GATEIO_BASE = 'https://data.gateapi.io/api2/1/ticker/';
const STATE_FILE = require('path').join(__dirname, 'watchlist_state.json');

// Unique stock list (deduplicated)
const US_STOCKS = [
  { code: 'AAPL', name: '苹果' }, { code: 'MSFT', name: '微软' },
  { code: 'GOOGL', name: '谷歌' }, { code: 'AMZN', name: '亚马逊' },
  { code: 'NVDA', name: '英伟达' }, { code: 'META', name: 'Meta' },
  { code: 'TSLA', name: '特斯拉' }, { code: 'AMD', name: 'AMD' },
  { code: 'INTC', name: '英特尔' }, { code: 'CRM', name: 'Salesforce' },
  { code: 'ADBE', name: 'Adobe' }, { code: 'NFLX', name: '奈飞' },
  { code: 'TSM', name: '台积电' }, { code: 'ASML', name: 'ASML' },
  { code: 'QCOM', name: '高通' }, { code: 'AVGO', name: '博通' },
  { code: 'MU', name: '美光' }, { code: 'MRVL', name: 'Marvell' },
  { code: 'NKE', name: '耐克' }, { code: 'DIS', name: '迪士尼' },
  { code: 'WMT', name: '沃尔玛' }, { code: 'COST', name: '好市多' },
  { code: 'MCD', name: '麦当劳' }, { code: 'SBUX', name: '星巴克' }
];

const CRYPTO_LIST = [
  { symbol: 'btc_usdt', code: 'BTC', name: '比特币' },
  { symbol: 'eth_usdt', code: 'ETH', name: '以太坊' },
  { symbol: 'sol_usdt', code: 'SOL', name: 'Solana' },
  { symbol: 'xrp_usdt', code: 'XRP', name: '瑞波' },
  { symbol: 'doge_usdt', code: 'DOGE', name: '狗狗币' },
  { symbol: 'ada_usdt', code: 'ADA', name: 'Cardano' },
  { symbol: 'dot_usdt', code: 'DOT', name: 'Polkadot' },
  { symbol: 'avax_usdt', code: 'AVAX', name: 'Avalanche' },
  { symbol: 'link_usdt', code: 'LINK', name: 'Chainlink' },
  { symbol: 'sui_usdt', code: 'SUI', name: 'Sui' },
  { symbol: 'bnb_usdt', code: 'BNB', name: '币安币' },
  { symbol: 'uni_usdt', code: 'UNI', name: 'Uniswap' },
  { symbol: 'apt_usdt', code: 'APT', name: 'Aptos' },
  { symbol: 'op_usdt', code: 'OP', name: 'Optimism' },
  { symbol: 'arb_usdt', code: 'ARB', name: 'Arbitrum' },
  { symbol: 'near_usdt', code: 'NEAR', name: 'NEAR' },
  { symbol: 'atom_usdt', code: 'ATOM', name: 'Cosmos' },
  { symbol: 'matic_usdt', code: 'MATIC', name: 'Polygon' }
];

// Load/save state
function loadState() {
  try {
    return require(STATE_FILE);
  } catch { return { prices: {}, volumes: {}, high52w: {}, low52w: {} }; }
}

function saveState(state) {
  require('fs').writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

async function fetchAllUS() {
  const results = [];
  for (const s of US_STOCKS) {
    try {
      const url = `${EASTMONEY_BASE}?secid=105.${s.code}&fields=f43,f44,f45,f46,f47,f48,f50,f57,f58,f116,f169,f170,f171`;
      const resp = await fetch(url);
      const json = await resp.json();
      if (json.data && json.data.f57) {
        const d = json.data;
        results.push({
          code: d.f57, name: d.f58 || s.name,
          price: (d.f43 || 0) / 1000,
          high: (d.f44 || 0) / 1000,
          low: (d.f45 || 0) / 1000,
          open: (d.f46 || 0) / 1000,
          volume: d.f47 || 0,
          change: (d.f169 || 0) / 1000,
          changePercent: (d.f170 || 0) / 100,
          marketCap: d.f116 || 0,
        });
      }
    } catch(e) { /* skip */ }
  }
  return results;
}

async function fetchAllCrypto() {
  const results = [];
  for (const c of CRYPTO_LIST) {
    try {
      const resp = await fetch(`${GATEIO_BASE}${c.symbol}`);
      const json = await resp.json();
      if (json.result === 'true') {
        results.push({
          code: c.code, name: c.name,
          price: parseFloat(json.last) || 0,
          high24h: parseFloat(json.high24hr) || 0,
          low24h: parseFloat(json.low24hr) || 0,
          volume: parseFloat(json.baseVolume) || 0,
          quoteVolume: parseFloat(json.quoteVolume) || 0,
          changePercent: parseFloat(json.percentChange) || 0,
        });
      }
    } catch(e) { /* skip */ }
  }
  return results;
}

function formatPrice(p) {
  if (p >= 1000) return p.toFixed(2);
  if (p >= 1) return p.toFixed(2);
  if (p >= 0.01) return p.toFixed(4);
  return p.toFixed(6);
}

function formatBigNum(n) {
  if (n >= 1e12) return (n / 1e12).toFixed(2) + 'T';
  if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
  return n.toString();
}

async function main() {
  const now = new Date();
  const beijingTime = now.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false });
  const state = loadState();
  const alerts = [];
  
  // Fetch data
  const stocks = (await fetchAllUS()).filter(s => s.price > 0);
  const cryptos = (await fetchAllCrypto()).filter(c => c.price > 0);
  
  // Check US stocks against history
  for (const s of stocks) {
    const key = `us:${s.code}`;
    const oldPrice = state.prices[key];
    const oldVol = state.volumes[key];
    
    // Track high/low
    if (!state.high52w[key] || s.price > state.high52w[key]) state.high52w[key] = s.price;
    if (!state.low52w[key] || s.price < state.low52w[key]) state.low52w[key] = s.price;
    
    // Check interval change
    if (oldPrice !== undefined && oldPrice > 0) {
      const intervalChange = ((s.price - oldPrice) / oldPrice) * 100;
      
      // ±2% trigger
      if (Math.abs(intervalChange) >= 2) {
        alerts.push({
          type: 'price',
          item: `${s.code}(${s.name})`,
          price: formatPrice(s.price),
          change: intervalChange,
          detail: `${intervalChange > 0 ? '📈' : '📉'} 短线波动 ${intervalChange > 0 ? '+' : ''}${intervalChange.toFixed(2)}%`
        });
      }
    }
    
    // Check volume spike
    if (oldVol !== undefined && oldVol > 0 && s.volume > 0) {
      const volRatio = s.volume / oldVol;
      if (volRatio >= 2) {
        alerts.push({
          type: 'volume',
          item: `${s.code}(${s.name})`,
          price: formatPrice(s.price),
          detail: `🔥 放量 ${volRatio.toFixed(1)}x`
        });
      }
    }
    
    state.prices[key] = s.price;
    state.volumes[key] = s.volume;
  }
  
  // Check crypto
  for (const c of cryptos) {
    const key = `crypto:${c.code}`;
    const oldPrice = state.prices[key];
    
    if (!state.high52w[key] || c.price > state.high52w[key]) state.high52w[key] = c.price;
    if (!state.low52w[key] || c.price < state.low52w[key]) state.low52w[key] = c.price;
    
    // Check 24h change
    if (Math.abs(c.changePercent) >= 2) {
      alerts.push({
        type: '24h',
        item: `${c.code}(${c.name})`,
        price: formatPrice(c.price),
        change: c.changePercent,
        detail: `${c.changePercent > 0 ? '📈' : '📉'} 24h ${c.changePercent > 0 ? '+' : ''}${c.changePercent.toFixed(2)}%`
      });
    }
    
    // Check interval change
    if (oldPrice !== undefined && oldPrice > 0) {
      const intervalChange = ((c.price - oldPrice) / oldPrice) * 100;
      if (Math.abs(intervalChange) >= 2) {
        alerts.push({
          type: 'price_crypto',
          item: `${c.code}(${c.name})`,
          price: formatPrice(c.price),
          change: intervalChange,
          detail: `${intervalChange > 0 ? '📈' : '📉'} 即时波动 ${intervalChange > 0 ? '+' : ''}${intervalChange.toFixed(2)}%`
        });
      }
    }
    
    state.prices[key] = c.price;
  }
  
  saveState(state);
  
  // === OUTPUT ===
  const lines = [];
  
  // Sort stocks by absolute change
  const sortedStocks = [...stocks].sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent));
  const sortedCrypto = [...cryptos].sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent));
  
  lines.push(`📊 **全球资产监控 | ${beijingTime}**`);
  lines.push('');
  
  // Top movers (both directions)
  lines.push('**🔥 涨幅TOP5**');
  const topGainers = sortedStocks.filter(s => s.changePercent > 0).slice(0, 5);
  topGainers.forEach(s => {
    lines.push(`🟢 ${s.code} $${formatPrice(s.price)}  +${s.changePercent.toFixed(2)}%`);
  });
  lines.push('');
  
  lines.push('**💀 跌幅TOP5**');
  const topLosers = sortedStocks.filter(s => s.changePercent < 0).slice(0, 5);
  topLosers.forEach(s => {
    lines.push(`🔴 ${s.code} $${formatPrice(s.price)}  ${s.changePercent.toFixed(2)}%`);
  });
  lines.push('');
  
  // Key stocks quick view
  lines.push('**📌 重点股**');
  const keyStocks = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META'];
  keyStocks.forEach(code => {
    const s = stocks.find(x => x.code === code);
    if (s) {
      const arrow = s.changePercent > 0 ? '🟢' : s.changePercent < 0 ? '🔴' : '⚪';
      const sign = s.changePercent > 0 ? '+' : '';
      lines.push(`${arrow} ${s.code} $${formatPrice(s.price)}  ${sign}${s.changePercent.toFixed(2)}%  |  量:${formatBigNum(s.volume)}`);
    }
  });
  lines.push('');
  
  // Crypto
  lines.push('**⛓ 加密货币**');
  sortedCrypto.forEach(c => {
    const arrow = c.changePercent > 0 ? '🟢' : c.changePercent < 0 ? '🔴' : '⚪';
    const sign = c.changePercent > 0 ? '+' : '';
    lines.push(`${arrow} ${c.code} $${formatPrice(c.price)}  ${sign}${c.changePercent.toFixed(2)}%`);
  });
  lines.push('');
  
  // Alerts
  if (alerts.length > 0) {
    lines.push('⚠️ **=== 盯盘提醒 ===**');
    alerts.forEach(a => {
      const prefix = a.type === '24h' ? '⏰' : '🚨';
      lines.push(`${prefix} ${a.detail}`);
      lines.push(`   ${a.item} | 现价: $${a.price}`);
    });
    lines.push('');
  }
  
  // Summary stats
  const gainers = stocks.filter(s => s.changePercent > 0).length;
  const losers = stocks.filter(s => s.changePercent < 0).length;
  const cryptoGainers = cryptos.filter(c => c.changePercent > 0).length;
  const cryptoLosers = cryptos.filter(c => c.changePercent < 0).length;
  
  lines.push(`📊 汇总: 美股 ${gainers}涨/${losers}跌 | 加密货币 ${cryptoGainers}涨/${cryptoLosers}跌`);
  
  const output = lines.join('\n');
  console.log(output);
}

main().catch(e => console.error('Error:', e.message));
