---
name: mmxm-swing-point-scanner-itp
description: Run and maintain the Intermediate Term Perspective (ITP) FX alert workflow for manual LTP-selected pairs using tvDatafeed, last-5-candle pulls, ongoing-candle trimming, and vectorized liquidity-run checks. Use when an agent needs to monitor active LTP pairs for intraday alerts, update the ITP watchlist, or package the workflow as a reusable skill for OpenClaw or Codex.
---

# MMXM Swing Point Scanner - ITP

ITP means Intermediate Term Perspective.

Use this skill to run the ITP alert layer after LTP has already selected the pairs manually.

## Workflow

1. Read the manual watchlist JSON.
2. Keep only pairs marked active by LTP.
3. Fetch FX data with `tvDatafeed`.
4. Pull the last 5 candles by default.
5. Trim the ongoing candle before detection.
6. Compare the trigger timeframe against the reference timeframe.
7. Emit alerts when liquidity is run.
8. Save alert state so the same event does not repeat on every scan.

## Default models

- `ltp_daily = true` -> watch previous H4 high/low within the day
- `ltp_weekly = true` -> watch previous daily high/low during the week
- `ltp_monthly = true` -> watch previous weekly high/low during the month

## Alert rules

- Treat every result as an alert, not a trade signal.
- Do not place orders or make final trading decisions.
- Use lower-timeframe confirmation after the alert.
- Keep the scan limited to the manually selected LTP pairs.

## Scripts

- `scripts/itp_scan.py` is the canonical runner.
- `references/itp_watchlist.example.json` shows the watchlist structure.
- `references/itp_models.md` explains the model mapping.
- `run_itp_heartbeat.ps1` is the one-shot wrapper for Task Scheduler.

## Running

Use the default 15-minute heartbeat:

```bash
python scripts/itp_scan.py
```

For Windows scheduling, use:

```powershell
.\run_itp_heartbeat.ps1
```

You can override the trigger timeframe or batch settings with CLI args or env vars.

Environment overrides:

- `ITP_TIMEFRAME`
- `ITP_BARS`
- `ITP_TRIM_ONGOING`
- `ITP_BATCH_SIZE`
- `ITP_SLEEP_BETWEEN_BATCHES`

## Implementation notes

- Keep the logic vectorized where possible.
- Return boolean-style alert records with metadata.
- Handle tvDatafeed failures per symbol so one timeout does not stop the full run.
- Persist alert state locally under `state/`.
- Keep the watchlist manual and explicit so another agent can update it without guessing.
