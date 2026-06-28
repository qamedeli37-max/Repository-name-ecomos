"""
数据获取层 — StockDataFetcher
使用 yfinance 并行拉取 5 分钟线，含 3 次重试。
返回字段: Current_Price, Change_Pct, Volume, MA5, Avg_Volume
"""

import os
import time
import pandas as pd
import numpy as np

from config import HTTP_PROXY, HTTPS_PROXY

if HTTP_PROXY:
    os.environ.setdefault("HTTP_PROXY", HTTP_PROXY)
    os.environ.setdefault("http_proxy", HTTP_PROXY)
if HTTPS_PROXY:
    os.environ.setdefault("HTTPS_PROXY", HTTPS_PROXY)
    os.environ.setdefault("https_proxy", HTTPS_PROXY)

import yfinance as yf


class StockDataFetcher:
    """并行获取多只股票 5 分钟线数据，含重试"""

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    @staticmethod
    def fetch_batch(symbols: list[str]) -> pd.DataFrame:
        """
        批量获取股票数据，返回 DataFrame。
        列: Symbol | Current_Price | Change_Pct | Volume | MA5 | Avg_Volume
        """
        rows = []
        for sym in symbols:
            row = StockDataFetcher._fetch_single_with_retry(sym)
            if row is not None:
                rows.append(row)
        if not rows:
            return pd.DataFrame(columns=[
                "Symbol", "Current_Price", "Change_Pct",
                "Volume", "MA5", "Avg_Volume"
            ])
        return pd.DataFrame(rows)

    @staticmethod
    def _fetch_single_with_retry(symbol: str) -> dict | None:
        """对单只股票最多重试 3 次"""
        last_error = None
        for attempt in range(1, StockDataFetcher.MAX_RETRIES + 1):
            try:
                return StockDataFetcher._fetch_and_compute(symbol)
            except Exception as e:
                last_error = e
                if attempt < StockDataFetcher.MAX_RETRIES:
                    time.sleep(StockDataFetcher.RETRY_DELAY)
        return None

    @staticmethod
    def _fetch_and_compute(symbol: str) -> dict | None:
        """拉取并计算单只股票指标"""
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            period=StockDataFetcher.FETCH_PERIOD,
            interval=StockDataFetcher.FETCH_INTERVAL,
            auto_adjust=True,
        )
        if df is None or df.empty or len(df) < 2:
            return None

        close = df["Close"].dropna()
        volume = df["Volume"].dropna()

        latest_price = float(close.iloc[-1])
        prev_close = float(close.iloc[-2])
        change_pct = round(((latest_price - prev_close) / prev_close) * 100.0, 2)

        # MA5 (最近 5 根)
        ma5 = round(float(close.tail(5).mean()), 2)

        # 5 周期成交量均值
        avg_vol = int(volume.tail(5).mean())
        curr_vol = int(volume.iloc[-1])

        return {
            "Symbol": symbol,
            "Current_Price": latest_price,
            "Change_Pct": change_pct,
            "Volume": curr_vol,
            "MA5": ma5,
            "Avg_Volume": avg_vol,
        }


# 类级别的周期常量（覆盖 config import 延迟）
StockDataFetcher.FETCH_PERIOD = "5d"
StockDataFetcher.FETCH_INTERVAL = "5m"
