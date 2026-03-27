# ITP Models

## Purpose

Use this layer to alert on liquidity runs after LTP has already selected the pair.

## Trigger cadence

- Default scan heartbeat: every 15 minutes
- Use 5-minute or 1-minute scans only if you need faster alerts
- Keep the monitor alert-only and human-reviewed

## Model mapping

### Daily LTP

- `ltp_daily = true`
- Watch the previous H4 candle high and low
- Alert if either level is run within the day

### Weekly LTP

- `ltp_weekly = true`
- Watch the previous daily candle high and low
- Alert if either level is run during the week

### Monthly LTP

- `ltp_monthly = true`
- Watch the previous weekly candle high and low
- Alert if either level is run during the month

## Output meaning

- `run_high = true` means price traded above the reference high
- `run_low = true` means price traded below the reference low
- Alerts are not final trade decisions
- Use lower-timeframe confirmation after the alert
