# Portable CSV column aliases (experimental)

Backtest Doctor reads local, regular CSV files. To audit a file that uses a different
set of column headings, pass a **declarative JSON mapping**. This only renames
field labels for the documented checks. It does **not** integrate with a
backtesting framework, execute a strategy, infer trade semantics, or correct an
incorrect timestamp or return convention.

```sh
python -m backtest_doctor bundle \
  --ohlcv-file examples/ohlcv_alias.csv \
  --ledger-file examples/ledger_alias.csv \
  --stability-file examples/stability_alias.csv \
  --columns examples/columns_synthetic.json
```

The result is WARN due to the deliberately small synthetic sample, with exit
code 0 unless --fail-on-warn is passed. The example is made-up data and has no
connection to a live strategy, broker, exchange, or account.

```json
{
  "ohlcv": {"timestamp": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"},
  "ledger": {"signal_bar_close": "SignalClose", "entry_time": "Entered", "next_bar_open": "NextOpen"},
  "stability": {"exit_time": "Exited", "gross_return": "GrossReturn"}
}
```

Each left-hand key is a canonical Backtest Doctor column and the value is the
exact source CSV column. All unspecified canonical fields must already
use canonical names. Unknown names, duplicates, collisions, missing mapped
columns, oversized or symlinked JSON inputs are rejected.

**This is not a vendor adapter.** Some frameworks use percentage points
(1.5 means 1.5%) while Backtest Doctor expects fractions (0.015 means 1.5%).
Column mapping cannot correct semantic errors; check them separately.

Privacy: the local CLI reports aggregate diagnostic data but does not echo
raw inputs, source column labels or paths. GitHub-hosted Actions run on GitHub
infrastructure; do not use hosted CI for private trading data without a
separate data-handling approval.
