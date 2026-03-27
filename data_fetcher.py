from __future__ import annotations

import os
from typing import Optional

import pandas as pd
from tvDatafeed import Interval, TvDatafeed


# Map simple timeframe strings to tvDatafeed intervals.
INTERVAL_MAP = {
    "5M": Interval.in_5_minute,
    "15M": Interval.in_15_minute,
    "30M": Interval.in_30_minute,
    "1D": Interval.in_daily,
    "1W": Interval.in_weekly,
    "1M": Interval.in_monthly,
    "4H": Interval.in_4_hour,
    "1H": Interval.in_1_hour,
}


def _to_interval(timeframe: str) -> Interval:
    key = timeframe.upper()
    if key not in INTERVAL_MAP:
        raise ValueError(f"Unsupported timeframe '{timeframe}'.")
    return INTERVAL_MAP[key]


class TVDataFetcher:
    """Small wrapper around TVDatafeed with sane defaults."""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        # Fall back to env vars if explicit credentials are not passed.
        username = username or os.getenv("TV_USERNAME") or os.getenv("TRADINGVIEW_USERNAME")
        password = password or os.getenv("TV_PASSWORD") or os.getenv("TRADINGVIEW_PASSWORD")
        # TvDatafeed handles None creds by using existing session/cookies if present.
        self.client = TvDatafeed(username=username, password=password)

    def fetch(self, symbol: str, exchange: str = "FOREXCOM", timeframe: str = "1D", bars: int = 5) -> pd.DataFrame:
        interval = _to_interval(timeframe)
        try:
            df = self.client.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=bars)
        except Exception as exc:
            print(f"warning: fetch failed for {exchange}:{symbol} {timeframe} - {exc}")
            return pd.DataFrame()
        if df is None or len(df) == 0:
            return pd.DataFrame()
        return df.rename(columns=str.lower)
