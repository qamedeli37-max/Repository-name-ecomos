"""
====================
  数据获取层
  负责从 yfinance 拉取行情数据
====================
"""

import os
import sys

# ── 设置 HTTP 代理（在 import yfinance 之前生效） ──
from config import HTTP_PROXY, HTTPS_PROXY

if HTTP_PROXY:
    os.environ["HTTP_PROXY"] = HTTP_PROXY
    os.environ["http_proxy"] = HTTP_PROXY
if HTTPS_PROXY:
    os.environ["HTTPS_PROXY"] = HTTPS_PROXY
    os.environ["https_proxy"] = HTTPS_PROXY

import yfinance as yf
import pandas as pd


def fetch_single(symbol: str, period: str = "5d", interval: str = "5m") -> pd.DataFrame | None:
    """获取单只股票的 OHLCV 数据"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            return None
        cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        return df[cols]
    except Exception as e:
        # 保留错误信息用于调试（不打印到界面）
        return None


def compute_metrics(df: pd.DataFrame) -> dict | None:
    """
    从 DataFrame 计算各项指标。
    返回:
        price, prev_close, change_pct, high, low, volume,
        volume_mean, ma5, above_ma5, volume_ratio
    """
    if df is None or len(df) < 2:
        return None

    try:
        close  = df["Close"].dropna()
        volume = df["Volume"].dropna()
        high   = df["High"].dropna()
        low    = df["Low"].dropna()
        open_  = df["Open"].dropna()

        if len(close) < 2:
            return None

        latest      = close.iloc[-1]
        prev_close  = close.iloc[-2]
        change_pct  = ((latest - prev_close) / prev_close) * 100.0

        # MA5 (用最近 5 根收盘价)
        ma5     = close.tail(5).mean()
        above_ma5 = latest > ma5

        # 成交量均值 (最近 5 根)
        volume_mean = volume.tail(5).mean()
        current_vol = volume.iloc[-1]
        volume_ratio = current_vol / volume_mean if volume_mean > 0 else 1.0

        return {
            "price":        round(float(latest), 2),
            "prev_close":   round(float(prev_close), 2),
            "open":         round(float(open_.iloc[-1]), 2),
            "high":         round(float(high.iloc[-1]), 2),
            "low":          round(float(low.iloc[-1]), 2),
            "change_pct":   round(float(change_pct), 2),
            "volume":       int(current_vol),
            "volume_mean":  int(volume_mean),
            "volume_ratio": round(float(volume_ratio), 2),
            "ma5":          round(float(ma5), 2),
            "above_ma5":    bool(above_ma5),
        }
    except Exception:
        return None


def fetch_all(symbols: list[str], period: str = "5d", interval: str = "5m") -> dict[str, dict | None]:
    """批量获取多只股票数据并计算指标"""
    results = {}
    for sym in symbols:
        try:
            df = fetch_single(sym, period, interval)
            metrics = compute_metrics(df)
            results[sym] = metrics
        except Exception:
            results[sym] = None
    return results
