from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from data_fetcher import TVDataFetcher


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WATCHLIST = ROOT / "references" / "itp_watchlist.example.json"
DEFAULT_STATE = ROOT / "state" / "itp_state.json"

MODEL_SPECS = {
    "daily": {"reference_timeframe": "4H", "reference_label": "previous H4 candle", "watch_flag": "ltp_daily"},
    "weekly": {"reference_timeframe": "1D", "reference_label": "previous daily candle", "watch_flag": "ltp_weekly"},
    "monthly": {"reference_timeframe": "1W", "reference_label": "previous weekly candle", "watch_flag": "ltp_monthly"},
}


@dataclass
class AlertRecord:
    symbol: str
    exchange: str
    model: str
    bias: Optional[str]
    trigger_timeframe: str
    reference_timeframe: str
    reference_label: str
    reference_high: Optional[float]
    reference_low: Optional[float]
    current_high: Optional[float]
    current_low: Optional[float]
    run_high: bool
    run_low: bool
    alert_key: str
    alert_new: bool
    alerted_at: Optional[str]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _batched(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _build_models(symbol_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    models: List[Dict[str, Any]] = []
    for model_name, spec in MODEL_SPECS.items():
        enabled = bool(symbol_cfg.get(spec["watch_flag"], False))
        if enabled:
            models.append(
                {
                    "name": model_name,
                    "bias": symbol_cfg.get(f"{model_name}_bias"),
                    "reference_timeframe": spec["reference_timeframe"],
                    "reference_label": spec["reference_label"],
                }
            )
    return models


def _alert_key(symbol: str, model: str, reference_timeframe: str, reference_ts: str, side: str) -> str:
    return f"{symbol}|{model}|{reference_timeframe}|{reference_ts}|{side}"


def _scan_symbol(
    fetcher: TVDataFetcher,
    symbol: str,
    symbol_cfg: Dict[str, Any],
    trigger_timeframe: str,
    bars: int,
    trim_ongoing: int,
    state_alerts: Dict[str, Any],
) -> List[AlertRecord]:
    exchange = symbol_cfg.get("exchange", "FOREXCOM")
    models = _build_models(symbol_cfg)
    alerts: List[AlertRecord] = []

    if not models:
        return alerts

    trigger_df = fetcher.fetch(symbol=symbol, exchange=exchange, timeframe=trigger_timeframe, bars=bars)
    if trim_ongoing > 0 and len(trigger_df) > trim_ongoing:
        trigger_df = trigger_df.iloc[:-trim_ongoing]
    if trigger_df.empty:
        return alerts

    trigger_high = float(trigger_df["high"].max())
    trigger_low = float(trigger_df["low"].min())

    for model in models:
        ref_df = fetcher.fetch(symbol=symbol, exchange=exchange, timeframe=model["reference_timeframe"], bars=bars)
        if trim_ongoing > 0 and len(ref_df) > trim_ongoing:
            ref_df = ref_df.iloc[:-trim_ongoing]
        if ref_df.empty:
            continue

        ref_row = ref_df.iloc[-1]
        ref_ts = str(ref_df.index[-1])
        ref_high = float(ref_row["high"])
        ref_low = float(ref_row["low"])
        run_high = trigger_high > ref_high
        run_low = trigger_low < ref_low

        for side, is_triggered in (("high", run_high), ("low", run_low)):
            if not is_triggered:
                continue

            key = _alert_key(symbol, model["name"], model["reference_timeframe"], ref_ts, side)
            alert_new = key not in state_alerts
            alerted_at = _now_iso() if alert_new else state_alerts[key]["alerted_at"]

            alerts.append(
                AlertRecord(
                    symbol=symbol,
                    exchange=exchange,
                    model=model["name"],
                    bias=model.get("bias"),
                    trigger_timeframe=trigger_timeframe,
                    reference_timeframe=model["reference_timeframe"],
                    reference_label=model["reference_label"],
                    reference_high=ref_high,
                    reference_low=ref_low,
                    current_high=trigger_high,
                    current_low=trigger_low,
                    run_high=run_high,
                    run_low=run_low,
                    alert_key=key,
                    alert_new=alert_new,
                    alerted_at=alerted_at,
                )
            )

            if alert_new:
                state_alerts[key] = {
                    "alerted_at": alerted_at,
                    "symbol": symbol,
                    "model": model["name"],
                    "side": side,
                }

    return alerts


def scan_itp(
    watchlist_path: Path = DEFAULT_WATCHLIST,
    state_path: Path = DEFAULT_STATE,
    trigger_timeframe: str = "15M",
    bars: int = 5,
    trim_ongoing: int = 1,
    batch_size: int = 9,
    sleep_between_batches: float = 2.0,
) -> List[Dict[str, Any]]:
    watchlist = _load_json(watchlist_path, {})
    state = _load_json(state_path, {"alerts": {}})
    state_alerts = state.get("alerts", {})

    fetcher = TVDataFetcher()
    symbols = list(watchlist.keys())
    results: List[Dict[str, Any]] = []

    for batch in _batched(symbols, batch_size if batch_size > 0 else len(symbols)):
        for symbol in batch:
            symbol_cfg = watchlist[symbol] or {}
            alerts = _scan_symbol(
                fetcher=fetcher,
                symbol=symbol,
                symbol_cfg=symbol_cfg,
                trigger_timeframe=trigger_timeframe,
                bars=bars,
                trim_ongoing=trim_ongoing,
                state_alerts=state_alerts,
            )
            results.extend(asdict(alert) for alert in alerts)
        if sleep_between_batches > 0:
            time.sleep(sleep_between_batches)

    state["alerts"] = state_alerts
    state["updated_at"] = _now_iso()
    _save_json(state_path, state)
    return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Intermediate Term Perspective alert monitor.")
    parser.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST), help="Path to the ITP watchlist JSON")
    parser.add_argument("--state", default=str(DEFAULT_STATE), help="Path to the alert state JSON")
    parser.add_argument("--timeframe", default=os.getenv("ITP_TIMEFRAME", "15M"), help="Trigger timeframe, usually 15M")
    parser.add_argument("--bars", type=int, default=int(os.getenv("ITP_BARS", "5")), help="Candles to fetch per timeframe")
    parser.add_argument("--trim-ongoing", type=int, default=int(os.getenv("ITP_TRIM_ONGOING", "1")), help="Trim latest ongoing candle")
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("ITP_BATCH_SIZE", "9")), help="Symbols per batch")
    parser.add_argument("--sleep-between-batches", type=float, default=float(os.getenv("ITP_SLEEP_BETWEEN_BATCHES", "2")), help="Seconds between batches")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    records = scan_itp(
        watchlist_path=Path(args.watchlist),
        state_path=Path(args.state),
        trigger_timeframe=args.timeframe,
        bars=args.bars,
        trim_ongoing=args.trim_ongoing,
        batch_size=args.batch_size,
        sleep_between_batches=args.sleep_between_batches,
    )
    print(json.dumps(records, indent=2, default=str))
