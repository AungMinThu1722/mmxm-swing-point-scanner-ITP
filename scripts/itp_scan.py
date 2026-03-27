from __future__ import annotations

import argparse
import json
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
    trigger_side: str
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


def _desired_side(bias: Optional[str]) -> Optional[str]:
    normalized = (bias or "").strip().lower()
    if normalized in {"aim_for_range_high", "aim_for_swing_high", "bullish", "buy"}:
        return "low"
    if normalized in {"aim_for_range_low", "aim_for_swing_low", "bearish", "sell"}:
        return "high"
    return None


def _alert_key(symbol: str, model: str, reference_timeframe: str, reference_ts: str, side: str) -> str:
    return f"{symbol}|{model}|{reference_timeframe}|{reference_ts}|{side}"


def _scan_symbol(
    fetcher: TVDataFetcher,
    symbol: str,
    symbol_cfg: Dict[str, Any],
    bars: int,
    trim_ongoing: int,
    state_alerts: Dict[str, Any],
) -> List[AlertRecord]:
    exchange = symbol_cfg.get("exchange", "FOREXCOM")
    models = _build_models(symbol_cfg)
    alerts: List[AlertRecord] = []

    if not models:
        return alerts

    for model in models:
        ref_df = fetcher.fetch(
            symbol=symbol,
            exchange=exchange,
            timeframe=model["reference_timeframe"],
            bars=bars,
        )
        if trim_ongoing > 0 and len(ref_df) > trim_ongoing:
            ref_df = ref_df.iloc[:-trim_ongoing]
        if len(ref_df) < 2:
            continue

        current_row = ref_df.iloc[-1]
        previous_row = ref_df.iloc[-2]
        current_ts = str(ref_df.index[-1])
        current_high = float(current_row["high"])
        current_low = float(current_row["low"])
        previous_high = float(previous_row["high"])
        previous_low = float(previous_row["low"])
        desired_side = _desired_side(model.get("bias"))
        if desired_side == "high":
            run_high = current_high > previous_high
            run_low = False
            triggered = run_high
        elif desired_side == "low":
            run_low = current_low < previous_low
            run_high = False
            triggered = run_low
        else:
            run_high = current_high > previous_high
            run_low = current_low < previous_low
            triggered = run_high or run_low

        if not triggered:
            continue

        side = desired_side
        if side is None:
            side = "high" if run_high else "low"

        key = _alert_key(symbol, model["name"], model["reference_timeframe"], current_ts, side)
        alert_new = key not in state_alerts
        alerted_at = _now_iso() if alert_new else state_alerts[key]["alerted_at"]

        alerts.append(
            AlertRecord(
                symbol=symbol,
                exchange=exchange,
                model=model["name"],
                bias=model.get("bias"),
                trigger_timeframe=model["reference_timeframe"],
                reference_timeframe=model["reference_timeframe"],
                reference_label=model["reference_label"],
                trigger_side=side,
                reference_high=previous_high,
                reference_low=previous_low,
                current_high=current_high,
                current_low=current_low,
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
    parser.add_argument("--bars", type=int, default=5, help="Candles to fetch per reference timeframe")
    parser.add_argument("--trim-ongoing", type=int, default=1, help="Trim latest ongoing candle")
    parser.add_argument("--batch-size", type=int, default=9, help="Symbols per batch")
    parser.add_argument("--sleep-between-batches", type=float, default=2.0, help="Seconds between batches")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    records = scan_itp(
        watchlist_path=Path(args.watchlist),
        state_path=Path(args.state),
        bars=args.bars,
        trim_ongoing=args.trim_ongoing,
        batch_size=args.batch_size,
        sleep_between_batches=args.sleep_between_batches,
    )
    print(json.dumps(records, indent=2, default=str))
