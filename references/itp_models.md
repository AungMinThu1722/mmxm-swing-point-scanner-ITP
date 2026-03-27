# ITP Models

## Purpose

Use this layer to alert on liquidity runs after LTP has already selected the pair.
The scan compares the latest closed candle to the previous candle on the same reference timeframe.

## Trigger cadence

- Default scan heartbeat: every 15 minutes
- Use 5-minute or 1-minute scans only if you need faster alerts
- Keep the monitor alert-only and human-reviewed

## Model mapping

### Daily LTP

- `ltp_daily = true`
- Monitor H4 candles
- Alert if the latest closed H4 candle runs the previous H4 high or low

### Weekly LTP

- `ltp_weekly = true`
- Monitor daily candles
- Alert if the latest closed daily candle runs the previous daily high or low

### Monthly LTP

- `ltp_monthly = true`
- Monitor weekly candles
- Alert if the latest closed weekly candle runs the previous weekly high or low

## Output meaning

- `run_high = true` means price traded above the reference high
- `run_low = true` means price traded below the reference low
- Alerts are not final trade decisions
- No lower-timeframe confirmation layer is used in this skill
