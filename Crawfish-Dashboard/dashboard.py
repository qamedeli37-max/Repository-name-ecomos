"""
核心 Web 界面 — Streamlit 盯盘仪表盘
"""
import time
import streamlit as st
import pandas as pd

from config import STOCKS, REFRESH_INTERVAL
from data_fetcher import StockDataFetcher
from strategy import signal_scorer

# ─── 页面配置 ───
st.set_page_config(
    page_title="小龙虾实时盯盘",
    page_icon="🦞",
    layout="wide",
)

# ─── 数据获取（带缓存，ttl=30s） ───
@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(_fetcher: StockDataFetcher) -> pd.DataFrame:
    return _fetcher.fetch_batch(STOCKS)


# ─── 等级 Emoji ───
LEVEL_EMOJI = {"S": "⭐", "A": "📈", "B": "➖", "C": "📉"}

# ─── 颜色工具 ───
def change_color(val: float) -> str:
    return "color: #26a69a" if val >= 0 else "color: #ef5350"


def arrow(val: float) -> str:
    return "▲" if val >= 0 else "▼"


def fmt_vol(v: int) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(v)


# ══════════════════════════════════════
# 主布局
# ══════════════════════════════════════

st.markdown(
    "<h1 style='text-align:center; color:#58a6ff;'>"
    "🦞 小龙虾实时盯盘</h1>",
    unsafe_allow_html=True,
)

fetcher = StockDataFetcher()
df = fetch_data(fetcher)

if df.empty:
    st.error("⚠ 无法获取股票数据，请检查网络/代理设置。")
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

# ─── 对每只股票执行评分 ───
rows = []
for _, r in df.iterrows():
    sig = signal_scorer(r.to_dict())
    rows.append({
        "股票代码": r["Symbol"],
        "现价": f"${r['Current_Price']:.2f}",
        "涨跌幅": f"{arrow(r['Change_Pct'])} {r['Change_Pct']:+.2f}%",
        "MA5": f"${r['MA5']:.2f}",
        "成交量": fmt_vol(r["Volume"]),
        "信号等级": f"{LEVEL_EMOJI[sig['level']]} {sig['level']}({sig['level_label']})",
        "信号详情": sig["signal_detail"],
        "预警": "🚨" if sig["need_alert"] else "✅",
    })

display_df = pd.DataFrame(rows)

# ─── 高亮行（淡红/淡绿） ───
def highlight_rows(row):
    idx = row.name
    alert_flag = False
    for _, r_orig in df.iterrows():
        sig = signal_scorer(r_orig.to_dict())
        if sig["need_alert"] and r_orig["Symbol"] == display_df.iloc[idx]["股票代码"]:
            alert_flag = True
            break
    if alert_flag:
        change_val = df.iloc[idx]["Change_Pct"]
        if change_val > 0:
            return ["background-color: #1a3a2a"] * len(row)
        return ["background-color: #3a1a1a"] * len(row)
    return [""] * len(row)


styled_df = display_df.style.apply(highlight_rows, axis=1).format(
    na_rep="—"
)

st.dataframe(
    styled_df,
    width="stretch",
    height=360,
    column_config={
        "股票代码": st.column_config.TextColumn("股票代码", width="small"),
        "现价": st.column_config.TextColumn("现价", width="small"),
        "涨跌幅": st.column_config.TextColumn("涨跌幅", width="small"),
        "MA5": st.column_config.TextColumn("MA5", width="small"),
        "成交量": st.column_config.TextColumn("成交量", width="small"),
        "信号等级": st.column_config.TextColumn("信号等级", width="medium"),
        "信号详情": st.column_config.TextColumn("信号详情", width="medium"),
        "预警": st.column_config.TextColumn("预警", width="small"),
    },
    hide_index=True,
)

# ─── 预警详情报表 ───
alert_rows = []
has_alert = False
for _, r in df.iterrows():
    sig = signal_scorer(r.to_dict())
    if sig["need_alert"]:
        has_alert = True
        alert_rows.append({
            "股票": r["Symbol"],
            "现价": f"${r['Current_Price']:.2f}",
            "涨跌幅": f"{r['Change_Pct']:+.2f}%",
            "放量比": f"{sig['vol_ratio']:.1f}x",
            "信号": sig["signal_detail"],
            "详情": sig["alert_reason"],
        })

if has_alert:
    st.markdown(
        "<h3 style='color:#ef5350;'>🚨 预警监控</h3>",
        unsafe_allow_html=True,
    )
    alert_df = pd.DataFrame(alert_rows)
    st.dataframe(
        alert_df.style.apply(
            lambda row: ["background-color: #3a1a1a"] * len(row), axis=1
        ),
        width="stretch",
        hide_index=True,
    )

    # ─── 需求规定的分隔线 + 预警格式 ───
    for _, a in enumerate(alert_rows, 1):
        separator = "=" * 45
        alert_block = f"{separator}\n预警 #{a['股票']}\n{separator}"
        st.code(alert_block, language="text")
else:
    st.info("✅ 暂无预警，市场平稳")

# ─── 统计摘要 ───
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("监控股票", len(df))
with col2:
    st.metric("数据成功", len(df))
with col3:
    has_alert_count = sum(1 for _, r in df.iterrows()
                          if signal_scorer(r.to_dict())["need_alert"])
    st.metric("预警数量", has_alert_count, delta_color="inverse")
with col4:
    st.metric("刷新周期", f"{REFRESH_INTERVAL}s")

# ─── 自动刷新（等待后 rerun） ───
time.sleep(REFRESH_INTERVAL)
st.rerun()
