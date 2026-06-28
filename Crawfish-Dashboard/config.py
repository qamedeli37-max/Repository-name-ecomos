"""
配置层 — 盯盘参数
"""

# 监控股票列表（美股代码）
STOCKS = ["AAPL", "TSLA", "NVDA", "MSFT"]

# 刷新间隔（秒）
REFRESH_INTERVAL = 60

# 数据拉取周期 & 粒度
FETCH_PERIOD = "5d"
FETCH_INTERVAL = "5m"

# 代理（Clash Verge 混合端口）
HTTP_PROXY = "http://127.0.0.1:7890"
HTTPS_PROXY = "http://127.0.0.1:7890"

# 预警阈值
ALERT_CHANGE_PCT = 2.0
ALERT_VOLUME_RATIO = 2.0
