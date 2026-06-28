"""
==========================
  系统配置 — 盯盘参数
==========================
"""

# ─── 监控股票列表 ───
# 格式：["代码", "显示名称"]
# 支持美股、港股、A股（需加后缀）
WATCH_LIST = [
    ("AAPL",   "苹果"),
    ("TSLA",   "特斯拉"),
    ("NVDA",   "英伟达"),
    ("MSFT",   "微软"),
    ("GOOGL",  "谷歌"),
    ("AMZN",   "亚马逊"),
    ("META",   "Meta"),
    ("600519.SS", "贵州茅台"),
    ("0700.HK",   "腾讯控股"),
]

# ─── 数据拉取 ───
FETCH_PERIOD   = "5d"       # 拉取多少天的数据
FETCH_INTERVAL = "5m"       # 数据粒度（1m/2m/5m/15m/30m/1h/1d）
REFRESH_SECONDS = 60        # 刷新间隔（秒）

# ─── 信号阈值 ───
CHANGE_THRESHOLD  = 2.0     # 涨跌幅 > 此值（%）触发信号分
VOLUME_MULTIPLIER = 2.0     # 成交量 > 均值 × 此倍数触发信号分

# ─── 预警阈值 ───
ALERT_CHANGE  = 2.0         # 涨跌幅 > 此值（%）触发预警
ALERT_VOLUME  = 2.0         # 放量 > 均值 × 此倍数触发预警
ALERT_BREAKOUT = True       # 突破/跌破均线是否预警

# ─── 代理（Clash Verge） ───
# 如果不需要代理，设为 None
HTTP_PROXY   = "http://127.0.0.1:7890"
HTTPS_PROXY  = "http://127.0.0.1:7890"

# ─── UI ───
CLEAR_SCREEN = True          # 每次刷新前是否清屏
SHOW_TIMESTAMP = True        # 显示上次更新时间
