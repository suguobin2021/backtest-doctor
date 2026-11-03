# Framework trade-export CSV adapters (experimental)

The `import-trades` mode audits **closed trade return summaries**, using three explicitly documented CSV dialects. It is offline, reads one local CSV, and emits only aggregate diagnostics. It does not run the originating backtesting engine, execute strategies, open archives or network connections, and cannot verify causal signal timing from these fields.

## Quickstart with synthetic fixtures

Run from a clean checkout after `python -m pip install --no-deps .`:

```sh
python -m backtest_doctor import-trades examples/backtesting_py_synthetic.csv --framework backtesting-py
python -m backtest_doctor import-trades examples/vectorbt_synthetic.csv --framework vectorbt
python -m backtest_doctor import-trades examples/freqtrade_csv_synthetic.csv --framework freqtrade-csv
```

Each command should return `WARN` (and exit 0) because the fixtures contain only three **invented** closed trades and signal/entry evidence is unavailable. Use `--fail-on-warn` to enforce strict CI. To add an *additional hypothetical* 20 basis points of per-trade cost stress:

```sh
python -m backtest_doctor import-trades examples/vectorbt_synthetic.csv --framework vectorbt --additional-cost-bps 20
```

### CSV contract (case-sensitive)

| `--framework` | Required columns | Return meaning |
| --- | --- | --- |
| `backtesting-py` | `ExitTime`, `ReturnPct` | `ReturnPct` is a **fraction** from `Backtest.run()['_trades']`, not percent points |
| `vectorbt` | `Exit Timestamp`, `Return`, `Status` | `Return` is a **fraction** from `Portfolio.trades.records_readable`; `Status` must be `Closed` |
| `freqtrade-csv` | `close_date`, `profit_ratio`, `is_open` | `profit_ratio` is a **fraction** from a user-created CSV extraction; `is_open` must explicitly be false |

**All timestamps must include an explicit timezone** (`Z` or `+00:00`), and all rows must be settled. Inputs with naive timestamps, missing required columns, open trades, nonfinite returns, or invalid values fail closed with a redacted error. This is intentionally stricter than some native DataFrame exports. Add timezone information at the source only when it is independently known; never silently infer UTC.

**Important: no native Freqtrade ZIP/JSON support.** Freqtrade's current official backtesting output uses a ZIP containing strategy and config material. Do not feed that archive into this tool or publicly upload it. `freqtrade-csv` supports only an explicitly prepared CSV subset with the three columns above; it is not an endorsement of an upstream CSV export format.

For `backtesting.py`, obtain a DataFrame with `stats['_trades']` (the `ReturnPct` field is fractional). For `vectorbt`, use `portfolio.trades.records_readable`; the timestamps must be actual timezone-aware datetimes, not positional integer bar indices. Both frameworks use public APIs that may change; verify these schemas when upgrading.

### Fee accounting and privacy

Existing framework returns **may already include commissions or funding**. The `cost_0bps` scenario preserves each reported return unchanged; `--additional-cost-bps N` is an **extra hypothetical stress**, not reconstructed trading costs. Do not interpret the result as gross pre-fee performance or independently measured account NAV. Results are simplified sequential trade proxies; overlapping positions and cash flows are not modeled.

Only **synthetic** examples are committed. Real trade exports may contain tickers, private strategies, account fields, trade times or returns; keep them on machines and CI runners authorized for that data. The tool does not print raw values or paths, but *aggregate* performance can still be sensitive. The GitHub Action runs on GitHub-hosted runners: do not upload private exports just to test this feature.

References to upstream formats:
- [Backtesting.py source: `_stats.py`](https://github.com/kernc/backtesting.py/blob/master/backtesting/_stats.py)
- [Vectorbt trade records](https://vectorbt.dev/api/portfolio/trades/)
- [Freqtrade trade fields](https://www.freqtrade.io/en/stable/advanced-backtesting/)
- [Freqtrade ZIP output caveat](https://www.freqtrade.io/en/stable/backtesting/)

Additional public-only upstream field review and timezone/export guidance: [Framework compatibility](FRAMEWORK_COMPATIBILITY.md).
