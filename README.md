# MMXM Swing Point Scanner - ITP

Intermediate Term Perspective alert repo for manual LTP-selected FX pairs.

This project is designed as an educational alerting tool for traders who want intraday liquidity-run notices without sitting in front of the chart all day.
It does not place trades and it does not replace human judgment.
The final orderflow interpretation, trade decision, and risk management must always be made by a person.

## What ITP means

ITP means Intermediate Term Perspective.

It is the alert layer between your manual LTP filter and your lower-timeframe confirmation.
In this repo, ITP is a recurring heartbeat job, not a one-shot scan.

## Default logic

- `ltp_daily = true` -> monitor H4 candles; if bias is `aim_for_range_high`, alert on H4 low run only, and if bias is `aim_for_range_low`, alert on H4 high run only
- `ltp_weekly = true` -> monitor daily candles; if bias is `aim_for_range_high`, alert on daily low run only, and if bias is `aim_for_range_low`, alert on daily high run only
- `ltp_monthly = true` -> monitor weekly candles; if bias is `aim_for_range_high`, alert on weekly low run only, and if bias is `aim_for_range_low`, alert on weekly high run only

## Prerequisites

- Python 3.11+ installed
- `pandas` and `tvDatafeed` available in your environment
- internet access to TradingView data endpoints
- optional TradingView credentials if you want to try authenticated access

## Included files

- `SKILL.md` for agent instructions
- `scripts/itp_scan.py` for the alert monitor
- `references/itp_models.md` for the model map
- `references/itp_watchlist.example.json` for the manual watchlist format
- `install.ps1` for copying the skill into a Codex-style skills workspace

## Use

Run the alert monitor:

```powershell
python .\scripts\itp_scan.py
```

Run the heartbeat wrapper once for Task Scheduler:

```powershell
.\run_itp_heartbeat.ps1
```

Install into a Codex skills workspace:

```powershell
.\install.ps1
```

You can also provide a destination:

```powershell
.\install.ps1 -Destination "$HOME\.codex\skills\mmxm-swing-point-scanner-ITP"
```

## For other agents

Any agent that understands `SKILL.md`-style bundles can use this repository directly.
The watchlist stays manual so another agent can update the pair list without guessing the trading intent.

## Task Scheduler

Schedule `run_itp_heartbeat.ps1` to repeat every 15 minutes.
The script runs one scan and exits, which is safer than a long-lived loop if a run takes longer than expected.
The scan itself checks the latest closed candle on the reference timeframe only.
No lower-timeframe confirmation layer is used inside this repo.
The cron job keeps running on schedule; state is used to avoid repeating the same alert, not to stop scheduling.
