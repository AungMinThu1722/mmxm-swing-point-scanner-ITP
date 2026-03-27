# MMXM Swing Point Scanner - ITP

Intermediate Term Perspective alert repo for manual LTP-selected FX pairs.

This project is designed as an educational alerting tool for traders who want intraday liquidity-run notices without sitting in front of the chart all day.
It does not place trades and it does not replace human judgment.
The final orderflow interpretation, trade decision, and risk management must always be made by a person.

## What ITP means

ITP means Intermediate Term Perspective.

It is the alert layer between your manual LTP filter and your lower-timeframe confirmation.

## Default logic

- `ltp_daily = true` -> watch previous H4 high/low within the day
- `ltp_weekly = true` -> watch previous daily high/low during the week
- `ltp_monthly = true` -> watch previous weekly high/low during the month

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
