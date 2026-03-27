---
name: mmxm-swing-point-scanner-itp
description: Run and maintain the Intermediate Term Perspective (ITP) FX alert workflow for manual LTP-selected pairs using tvDatafeed, last-5-candle pulls, ongoing-candle trimming, and vectorized liquidity-run checks. Use when an agent needs to monitor active LTP pairs for intraday alerts, update the ITP watchlist, or package the workflow as a reusable skill for OpenClaw or Codex.
---

# MMXM Swing Point Scanner - ITP

ITP means Intermediate Term Perspective.

Use this skill to run the ITP alert layer after LTP has already selected the pairs manually.

Operational rule:

- When the user says "run ITP", treat that as a recurring heartbeat job, not a one-shot scan.
- Ensure the 15-minute scheduler is active or update it if the watchlist changes.
- Do not switch to lower-timeframe confirmation inside this skill.

## Workflow

1. Read the manual watchlist JSON.
2. Keep only pairs marked active by LTP.
3. Fetch FX data with `tvDatafeed`.
4. Pull the last 5 candles on the model's reference timeframe by default.
5. Trim the ongoing candle before detection.
6. Compare the latest closed candle to the previous candle on the same timeframe.
7. Emit alerts when the latest candle runs the previous candle high or low.
8. Save alert state so the same event does not repeat on every scan.

## Default models

- `ltp_daily = true` -> monitor H4 candles and alert when the latest closed H4 candle runs the previous H4 high/low
- `ltp_weekly = true` -> monitor daily candles and alert when the latest closed daily candle runs the previous daily high/low
- `ltp_monthly = true` -> monitor weekly candles and alert when the latest closed weekly candle runs the previous weekly high/low

## Alert rules

- Treat every result as an alert, not a trade signal.
- Do not place orders or make final trading decisions.
- No lower-timeframe confirmation layer is used in this skill.
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

You can override the candle count or batch settings with CLI args.

The 15-minute heartbeat is the scheduler cadence. The scan itself evaluates the latest closed candle on the reference timeframe.

## Implementation notes

- Keep the logic vectorized where possible.
- Return boolean-style alert records with metadata.
- Handle tvDatafeed failures per symbol so one timeout does not stop the full run.
- Persist alert state locally under `state/`.
- Keep the watchlist manual and explicit so another agent can update it without guessing.
