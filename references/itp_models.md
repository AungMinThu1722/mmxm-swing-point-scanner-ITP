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
- If bias is `aim_for_range_high`, alert on H4 low run only
- If bias is `aim_for_range_low`, alert on H4 high run only

### Weekly LTP

- `ltp_weekly = true`
- Monitor daily candles
- If bias is `aim_for_range_high`, alert on daily low run only
- If bias is `aim_for_range_low`, alert on daily high run only

### Monthly LTP

- `ltp_monthly = true`
- Monitor weekly candles
- If bias is `aim_for_range_high`, alert on weekly low run only
- If bias is `aim_for_range_low`, alert on weekly high run only

## Output meaning

- `run_high = true` means price traded above the reference high
- `run_low = true` means price traded below the reference low
- Alerts are not final trade decisions
- No lower-timeframe confirmation layer is used in this skill
