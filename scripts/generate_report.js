const fs = require('fs');

const CAT_DISPLAY = {
  '全部': '全品类', '化妆美容': '美妆类', '美食': '美食类',
  '旅行': '旅行类', '数码科技': '科技类', '游戏': '游戏类',
  '健康医学': '健康类', '亲子': '亲子类', '身体锻炼': '运动类',
  '学习教育': '教育类', '动物': '动物类', '潮流风尚': '时尚类',
  '居家装修': '家居类', '影视': '影视类', '音乐': '音乐类',
  '舞蹈才艺': '舞蹈类', '明星娱乐': '娱乐类', '体育': '体育类',
  '情感': '情感类', '财富理财': '理财类', '二次元': '二次元类',
  '小剧场': '小剧场类', '汽车': '汽车类', '三农': '三农类',
  '人文': '人文类', '颜值造型': '颜值类', '个人才艺': '才艺类',
  '生活vlog': '生活类',
};

function formatNum(val) {
  if (val == null || val === '-' || val === '') return '-';
  const s = String(val).toLowerCase().trim();
  if (s.includes('w')) return s;
  if (s.includes('亿')) return s;
  const n = parseInt(s);
  if (isNaN(n) || n === 0) return '-';
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿';
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w';
  return String(n);
}

function parseNum(val) {
  if (val == null || val === '-' || val === '') return 0;
  const n = parseFloat(String(val).toLowerCase().replace(/w/g, ''));
  return isNaN(n) ? 0 : n;
}

function fmtInteraction(num) {
  if (num >= 100000) return Math.floor(num / 10000) + 'w+';
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w+';
  return String(num);
}

const PERIOD_UPDATE = { day: '每日17:30', week: '每周一17:30', month: '每月2号9点' };

function generateHTML(data, outputPath) {
  const items = data.list || [];
  const period = data.period || 'day';
  const dateStart = data.dateStart || '';
  const dateEnd = data.dateEnd || '';
  const category = data.category || '全部';
  const total = data.total || items.length;
  const displayedCount = items.length;
  const dateDisplay = dateStart === dateEnd ? dateStart : `${dateStart} 至 ${dateEnd}`;
  const periodLabel = { day: '日榜', week: '周榜', month: '月榜' }[period] || '日榜';
  const catDisplay = CAT_DISPLAY[category] || category + '类';
  const isAllCategory = category === '全部';
  const updateRule = PERIOD_UPDATE[period] || '每日17:30';

  // Stats
  let maxInteraction = 0;
  for (const item of items) {
    const likes = parseNum(item.newLikes);
    const comments = parseNum(item.newComments);
    const shares = parseNum(item.newShares);
    const interaction = likes + comments + shares;
    if (interaction > maxInteraction) maxInteraction = interaction;
  }

  // Build rows
  const rows = [];
  for (const item of items) {
    const rank = item.rank;
    const rankClass = rank <= 3 ? `rank-${rank}` : 'rank-other';
    const lnk = item.profileUrl || '#';
    const score = typeof item.comprehensiveScore === 'number' ? Math.round(item.comprehensiveScore) : item.comprehensiveScore;

    const catCol = isAllCategory ? `      <td class="category">${item.category || '-'}</td>\n` : '';

    rows.push(
`    <tr>
      <td><span class="rank-badge ${rankClass}">${rank}</span></td>
      <td><a href="${lnk}" target="_blank" class="account-name" title="点击查看抖音主页">${item.accountName}</a></td>
${catCol}      <td><span class="score">${score}</span></td>
      <td>${formatNum(item.followers)}</td>
      <td class="interaction">${formatNum(item.newFans)}</td>
      <td class="interaction">${formatNum(item.newLikes)}</td>
      <td class="interaction">${formatNum(item.newComments)}</td>
      <td class="interaction">${formatNum(item.newShares)}</td>
    </tr>`
    );
  }

  const catTh = isAllCategory ? '      <th>赛道</th>\n' : '';
  const displayHint = displayedCount >= total
    ? `共 ${total} 个账号上榜`
    : `共 ${total} 个账号上榜（展示 TOP ${displayedCount} 条）`;

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>抖音${periodLabel} · ${dateDisplay}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", Arial, sans-serif;
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
    min-height: 100vh;
    padding: 24px;
    color: #e0e0e0;
  }
  .header {
    text-align: center;
    margin-bottom: 32px;
  }
  .header .logo { font-size: 48px; margin-bottom: 8px; }
  .header h1 { font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 6px; }
  .header .meta { font-size: 13px; color: #888; }
  .notice {
    background: #1a1a3e;
    border-left: 4px solid #00d4ff;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 24px;
    font-size: 13px;
    color: #b0b0d0;
  }
  .stats-bar { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
  .stat-card {
    flex: 1; min-width: 120px;
    background: #1e1e3a;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }
  .stat-card .num { font-size: 28px; font-weight: 700; color: #00d4ff; }
  .stat-card .label { font-size: 12px; color: #888; margin-top: 4px; }
  .table-wrap {
    background: #16162e;
    border-radius: 16px;
    overflow-x: auto;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    margin-bottom: 24px;
  }
  table { width: 100%; border-collapse: collapse; min-width: 700px; }
  thead th {
    background: linear-gradient(135deg, #00d4ff, #007bff);
    color: #fff;
    padding: 14px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
  }
  tbody tr { border-bottom: 1px solid #2a2a4a; transition: background 0.15s; }
  tbody tr:hover { background: #1e1e42; }
  tbody tr:last-child { border-bottom: none; }
  td { padding: 12px 16px; font-size: 14px; vertical-align: middle; }
  .rank-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 32px; height: 32px; border-radius: 50%;
    font-weight: 700; font-size: 14px;
  }
  .rank-1 { background: #FFD700; color: #5d4000; }
  .rank-2 { background: #C0C0C0; color: #3d3d3d; }
  .rank-3 { background: #CD7F32; color: #fff; }
  .rank-other { background: #2a2a4a; color: #aaa; }
  .account-name { font-weight: 600; color: #00d4ff; text-decoration: none; cursor: pointer; }
  .account-name:hover { color: #fff; text-decoration: underline; }
  .score { font-weight: 700; color: #00d4ff; }
  .interaction { font-weight: 500; color: #ff6b9d; }
  .category { color: #aaa; font-size: 12px; }
  .export-bar { text-align: center; margin-bottom: 16px; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
  .btn {
    padding: 10px 24px; border-radius: 24px; border: none;
    cursor: pointer; font-size: 14px; font-weight: 600;
    transition: transform 0.1s, box-shadow 0.1s;
  }
  .btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,212,255,0.3); }
  .btn-primary { background: linear-gradient(135deg, #00d4ff, #007bff); color: #fff; }
  .btn-secondary { background: #2a2a4a; color: #00d4ff; border: 2px solid #00d4ff; }
  #subscription-section { margin-top: 40px; padding: 24px; background: #1a1a3e; border-radius: 12px; }
  #subscription-section h3 { margin: 0 0 16px 0; font-size: 18px; color: #00d4ff; }
  #subscription-section div[style*="font-weight: 500"] { color: #ccc; }
  .cat-tag { background: #2a2a4a; padding: 4px 10px; border-radius: 16px; font-size: 13px; color: #aaa; }
  .footer { text-align: center; font-size: 12px; color: #555; padding: 16px; }
  @media print {
    .export-bar { display: none; }
    body { background: #fff; padding: 0; color: #000; }
    .table-wrap { box-shadow: none; }
    .header h1 { color: #000; }
    .stat-card .num { color: #000; }
    .account-name { color: #0066cc; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="logo">🎮</div>
  <h1>抖音${periodLabel} · ${catDisplay}</h1>
  <div class="meta">数据日期：${dateDisplay} &nbsp;|&nbsp; ${displayHint}</div>
</div>

<div class="notice">
  💡 <strong>榜单说明</strong>：${updateRule}，与实时数据存在差异。<br>
  📐 <strong>综合评分（满分100）</strong>：根据达人在抖音的 <strong>总粉丝数</strong>、周期内的 <strong>粉丝增量</strong>、<strong>点赞增量</strong>、<strong>分享增量</strong> 以及 <strong>评论增量</strong> 加权计算所得。
</div>

<div class="stats-bar">
  <div class="stat-card"><div class="num">${displayedCount}</div><div class="label">展示条数</div></div>
  <div class="stat-card"><div class="num">${fmtInteraction(maxInteraction)}</div><div class="label">最高互动</div></div>
</div>

<div class="export-bar">
  <button class="btn btn-primary" onclick="window.print()">🖨️ 打印 / 导出 PDF</button>
  <button class="btn btn-secondary" id="downloadImgBtn" onclick="downloadAsImage()">📷 保存为图片</button>
</div>

<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<script>
async function downloadAsImage() {
  const btn = document.getElementById('downloadImgBtn');
  btn.textContent = '⏳ 生成中...';
  btn.disabled = true;
  try {
    const element = document.querySelector('.table-wrap');
    const canvas = await html2canvas(element, {
      scale: 2, backgroundColor: '#16162e', useCORS: true
    });
    const link = document.createElement('a');
    link.download = '抖音${periodLabel}_${dateDisplay.replace(/[\/:\s-]/g, '')}.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
    btn.textContent = '✅ 下载成功';
    setTimeout(() => { btn.textContent = '📷 保存为图片'; btn.disabled = false; }, 2000);
  } catch(e) {
    alert('生成图片失败，请尝试使用浏览器截图');
    btn.textContent = '📷 保存为图片';
    btn.disabled = false;
  }
}
</script>

<div class="table-wrap">
<table>
  <thead>
    <tr>
      <th>排名</th>
      <th>账号名</th>
${catTh}      <th>综合评分</th>
      <th>总粉丝数</th>
      <th>新增粉丝</th>
      <th>新增点赞</th>
      <th>新增评论</th>
      <th>新增分享</th>
    </tr>
  </thead>
  <tbody>
${rows.join('\n')}
  </tbody>
</table>
</div>

<div id="subscription-section">
  <h3>📬 订阅服务</h3>
  <div style="margin-bottom: 12px;">
    <div style="font-weight: 500; color: #ccc;">1️⃣ 是否需要订阅每日/周/月的抖音账号最新排名？</div>
  </div>
  <div>
    <div style="font-weight: 500; color: #ccc; margin-bottom: 8px;">2️⃣ 是否需要订阅具体赛道的账号表现？我们支持：</div>
    <div style="display: flex; flex-wrap: wrap; gap: 6px;">
      <span class="cat-tag">个人才艺</span><span class="cat-tag">生活vlog</span><span class="cat-tag">财富理财</span>
      <span class="cat-tag">二次元</span><span class="cat-tag">居家装修</span><span class="cat-tag">学习教育</span>
      <span class="cat-tag">小剧场</span><span class="cat-tag">数码科技</span><span class="cat-tag">旅行</span>
      <span class="cat-tag">美食</span><span class="cat-tag">化妆美容</span><span class="cat-tag">动物</span>
      <span class="cat-tag">亲子</span><span class="cat-tag">汽车</span><span class="cat-tag">情感</span>
      <span class="cat-tag">三农</span><span class="cat-tag">健康医学</span><span class="cat-tag">潮流风尚</span>
      <span class="cat-tag">舞蹈才艺</span><span class="cat-tag">颜值造型</span><span class="cat-tag">人文</span>
      <span class="cat-tag">音乐</span><span class="cat-tag">影视</span><span class="cat-tag">身体锻炼</span>
      <span class="cat-tag">体育</span><span class="cat-tag">明星娱乐</span><span class="cat-tag">游戏</span>
    </div>
  </div>
</div>

<script>
// Add row click to open profile
document.querySelectorAll('.account-name').forEach(el => {
  el.addEventListener('click', function(e) { e.stopPropagation(); });
});
</script>
</body>
</html>`;

  fs.writeFileSync(outputPath, html, 'utf-8');
  console.error(`[INFO] HTML 报告已生成: ${outputPath}`);
  return outputPath;
}

// Main
const args = process.argv.slice(2);
const inputPath = args[0];
const outputPath = args[1];

if (!inputPath) {
  console.error('用法: node generate_report.js <input.json> [output.html]');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
const period = data.period || 'day';
const dateStr = (data.dateStart || '').replace(/-/g, '');
const cat = data.category || '全部';
const periodName = { day: '日榜', week: '周榜', month: '月榜' }[period] || '榜';
const outFile = outputPath || `抖音${cat}${periodName}${dateStr}.html`;

generateHTML(data, outFile);
