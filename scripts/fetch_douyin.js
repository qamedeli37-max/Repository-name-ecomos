const https = require('https');
const fs = require('fs');
const path = require('path');

const API_URL = 'https://redfox.hk/story/api/dyData/query';
const API_KEY = 'ak_695c6d6963c74dab92699a98229d7828';

function fmtDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function getDateRange(period, offset = 1) {
  const today = new Date();
  if (period === 'day') {
    const d = new Date(today);
    d.setDate(d.getDate() - offset);
    const s = fmtDate(d);
    return { start: s, end: s };
  }
  if (period === 'week') {
    const dayOfWeek = today.getDay() || 7;
    const daysSinceMonday = dayOfWeek - 1;
    const thisMonday = new Date(today);
    thisMonday.setDate(today.getDate() - daysSinceMonday);
    const targetMonday = new Date(thisMonday);
    targetMonday.setDate(thisMonday.getDate() - 7 * offset);
    const targetSunday = new Date(targetMonday);
    targetSunday.setDate(targetMonday.getDate() + 6);
    return { start: fmtDate(targetMonday), end: fmtDate(targetSunday) };
  }
  if (period === 'month') {
    let m = today.getMonth() - offset;
    let y = today.getFullYear();
    if (m < 0) { m += 12; y -= 1; }
    return { start: fmtDate(new Date(y, m, 1)), end: fmtDate(new Date(y, m + 1, 0)) };
  }
  return { start: fmtDate(today), end: fmtDate(today) };
}

function isDataUpdated(period) {
  const now = new Date();
  const hour = now.getHours(), min = now.getMinutes(), day = now.getDate(), wd = now.getDay() || 7;
  if (period === 'day') return hour > 17 || (hour === 17 && min >= 30);
  if (period === 'week') return wd !== 1 || hour > 17 || (hour === 17 && min >= 30);
  return true;
}

function getSmartOffset(period) {
  return isDataUpdated(period) ? 1 : 2;
}

const PERIOD_MAP = { day: 'days', week: 'weeks', month: 'months' };
const PERIOD_LABELS = { day: '日榜', week: '周榜', month: '月榜' };

function postRequest(payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const url = new URL(API_URL);
    const opts = {
      hostname: url.hostname, path: url.pathname, method: 'POST',
      headers: {
        'Content-Type': 'application/json', 'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-API-KEY': API_KEY, 'Content-Length': Buffer.byteLength(data),
      },
    };
    const req = https.request(opts, (res) => {
      let body = '';
      res.on('data', (chunk) => (body += chunk));
      res.on('end', () => {
        try { resolve(JSON.parse(body)); }
        catch (e) { reject(new Error('JSON parse error: ' + body.slice(0, 200))); }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function parseNum(val) {
  if (val == null || val === '-' || val === '') return 0;
  const n = parseFloat(String(val).toLowerCase().replace(/w/g, '').trim());
  return isNaN(n) ? 0 : n;
}

function fmtW(val) {
  if (val == null || val === '-' || val === '') return '-';
  const s = String(val).toLowerCase().trim();
  if (s.includes('w')) return Math.floor(parseFloat(s.replace('w', ''))) + 'w+';
  if (s.includes('亿')) return s;
  const n = parseInt(s);
  if (isNaN(n) || n === 0) return '-';
  if (n >= 10000) return Math.floor(n / 10000) + 'w+';
  return String(n);
}

function calculateScores(items) {
  const extract = (item, keys) => { for (const k of keys) { const v = item[k]; if (v != null) return parseNum(v); } return 0; };
  const fL = items.map(i => extract(i, ['followers', 'fansCount', 'fans']));
  const faL = items.map(i => extract(i, ['newFans', 'fansGrowth']));
  const liL = items.map(i => extract(i, ['newLikes', 'likedGrowth']));
  const shL = items.map(i => extract(i, ['newShares', 'sharedGrowth']));
  const coL = items.map(i => extract(i, ['newComments', 'commentsGrowth']));
  const mx = a => Math.max(...a, 1);
  const maxF = mx(fL), maxFa = mx(faL), maxLi = mx(liL), maxSh = mx(shL), maxCo = mx(coL);
  const ln = (v, m) => (v <= 0 || m <= 1) ? 0 : Math.log(v + 1) / Math.log(m + 1) * 100;
  return items.map((_, i) => {
    const score = ln(fL[i], maxF) * 0.20 + ln(faL[i], maxFa) * 0.20 +
      ln(liL[i], maxLi) * 0.20 + ln(shL[i], maxSh) * 0.20 + ln(coL[i], maxCo) * 0.20;
    return { ...items[i], comprehensiveScore: Math.round(score * 10) / 10 };
  });
}

async function main() {
  const args = process.argv.slice(2);
  const period = args.find(a => ['day', 'week', 'month'].includes(a)) || 'day';
  const category = args.find(a => !['day', 'week', 'month'].includes(a) && !a.startsWith('--')) || '全部';
  const outputIdx = args.indexOf('--output');
  const outputPath = outputIdx >= 0 ? args[outputIdx + 1] : null;
  const limit = 50;

  const offset = getSmartOffset(period);
  const { start, end } = getDateRange(period, offset);
  const dateType = PERIOD_MAP[period];
  const periodLabel = PERIOD_LABELS[period];

  console.error(`[INFO] 周期=${period} 日期=${start}至${end} 赛道=${category}`);

  const result = await postRequest({
    dateType, rankDate: start, type: category,
    source: '抖音每日最具影响力账号-ClawHub',
  });

  if (result.code !== 2000) {
    console.error(`[ERROR] code=${result.code}: ${result.msg || result.message || '未知'}`);
    process.exit(3);
  }

  let items = result.data || [];
  const total = items.length;
  const scored = calculateScores(items);
  scored.sort((a, b) => b.comprehensiveScore - a.comprehensiveScore);
  scored.forEach((item, i) => { item.rank = i + 1; });

  const normalized = {
    period, dateStart: start, dateEnd: end,
    date: start === end ? start : `${start}至${end}`,
    category, periodLabel, total,
    list: scored.slice(0, limit).map(item => ({
      rank: item.rank,
      accountName: item.accountName || '',
      category: item.category || category,
      comprehensiveScore: item.comprehensiveScore,
      followers: item.fansCount || item.followers || null,
      newFans: item.fansGrowth || item.newFans || null,
      newLikes: item.likedGrowth || item.newLikes || null,
      newComments: item.commentsGrowth || item.newComments || null,
      newShares: item.sharedGrowth || item.newShares || null,
      profileUrl: item.accountLink || item.profileUrl || '',
    })),
  };

  if (outputPath) {
    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify(normalized, null, 2), 'utf-8');
    console.error(`[INFO] 已保存: ${outputPath}`);
  }

  // Markdown
  const updateRule = { day: '每日17:30', week: '每周一17:30', month: '每月2号9点' }[period];
  const catDisplay = category === '全部' ? '全品类' : category + '类';
  const dateDisplay = `${start.slice(0,4)}年${start.slice(5,7)}月${start.slice(8)}日`;
  const lines = [
    `📊 抖音${periodLabel} · ${catDisplay}`, '',
    `数据日期：${dateDisplay}`,
    `共 ${total} 个账号上榜（展示 TOP ${Math.min(limit, total)} 条）`, '',
    `💡 榜单说明：${updateRule}，与实时数据存在差异`, '',
    '📐 综合评分：根据总粉丝数、新增粉丝增量、新增点赞/分享/评论加权计算，满分100', '',
    '| 排名 | 账号名 | 综合评分 | 总粉丝数 | 新增粉丝 | 新增点赞 | 新增评论 | 新增分享 |',
    '|:---:|--------|:-------:|:-------:|:-------:|:-------:|:-------:|:-------:|:-------:|',
  ];
  const emoji = ['🥇', '🥈', '🥉'];
  for (const item of normalized.list.slice(0, 20)) {
    const rs = item.rank <= 3 ? `${emoji[item.rank-1]} ${item.rank}` : String(item.rank);
    const nl = item.profileUrl ? `[${item.accountName}](${item.profileUrl})` : item.accountName;
    lines.push(`| ${rs} | ${nl} | ${item.comprehensiveScore} | ${fmtW(item.followers)} | ${fmtW(item.newFans)} | ${fmtW(item.newLikes)} | ${fmtW(item.newComments)} | ${fmtW(item.newShares)} |`);
  }
  console.log('\n' + lines.join('\n'));
}

main().catch(e => { console.error('[FATAL]', e.message); process.exit(1); });
