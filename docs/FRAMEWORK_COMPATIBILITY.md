# Upstream framework interoperability: source-reviewed

Public upstream source/docs reviewed 2026-11-03. **These are experimental CSV-subset adapters, not native trade engine integrations.**

| Framework | Public source contract | Conversion required |
| --- | --- | --- |
| backtesting.py | stats['_trades'] contains fractional ReturnPct and ExitTime in upstream _stats.py | Localize or convert the original time index only if its actual timezone is known |
| vectorbt | Portfolio.trades.records_readable contains Exit Timestamp, Return (fraction) and Status | Integer bar positions are **not** dates; replace with actual known timezone-aware timestamps |
| Freqtrade | Public trade model exposes close_date, profit_ratio and is_open | Native backtesting ZIP includes strategy/config; **unsupported**. Manually export only three required columns to a local CSV |

Rows must be closed/settled. Input returns are **fractions**, so 0.01 represents +1%. Native returns can already be net of fees; cost_0bps is the unmodified reported return and additional cost bps are only hypothetical additional drag. No evidence of signal timing, funding, cash flows, full account NAV or actual execution is reconstructed.

Steps: (1) confirm the upstream version and documented column schema, (2) confirm known timezone and return unit, (3) produce a minimal CSV locally with no identifying fields, (4) run `python -m backtest_doctor import-trades sample.csv --framework vectorbt --explain`, substituting backtesting-py or freqtrade-csv as appropriate. Never upload confidential CSVs to GitHub Actions runners.

Public upstream references:
- https://github.com/kernc/backtesting.py/blob/master/backtesting/_stats.py
- https://vectorbt.dev/api/portfolio/trades/
- https://www.freqtrade.io/en/latest/backtesting/

A diagnostic PASS/WARN is not evidence of a profitable or forward-causal strategy.
