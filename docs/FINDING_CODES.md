# Finding codes and investigation guide

`--explain` adds fixed, data-free descriptions only for detected codes. It does not inspect strategy source code, prove causal timing, or give a verified fix. Do not publish aggregate reports without reviewing them.

```sh
python -m backtest_doctor ledger examples/ledger_bad.csv --explain
```

| Code | Meaning | Investigation |
| --- | --- | --- |
| `AMBIGUOUS_SAME_BAR_EXIT` | Stop and target are both declared hit within one bar. | Use lower-timeframe or execution evidence and document the intrabar priority rule. |
| `DUPLICATE_TIMESTAMP` | Two or more candle rows share a timestamp. | Check whether duplicate candles represent duplicated imports or legitimate distinct intervals. |
| `EMPTY_LEDGER` | No declared trade timing rows were supplied. | Provide signal-close, entry, and next-open timestamps from a reproducible trade export. |
| `EMPTY_OHLCV` | No OHLCV rows were supplied. | Export at least one timestamped candle and verify the input file is not empty. |
| `FINDING_LIMIT_REACHED` | The diagnostics limit was reached. | Address the first listed failures, then rerun on a bounded subset or corrected export. |
| `INVALID_CANDLE_GEOMETRY` | OHLC values violate high/low envelope consistency. | Compare the candle to original source data and check adjustment/aggregation procedures. |
| `INVALID_NUMERIC_FIELD` | A required candle field is not a finite number. | Check numeric formatting, missing values, and exporter conversions. |
| `INVALID_PRICE_OR_VOLUME` | A price is nonpositive or volume is negative. | Check source adjustments, units, and upstream data quality; do not clamp values blindly. |
| `INVALID_TIMESTAMP` | A timestamp is invalid or lacks an explicit timezone. | Check the original time source and export timezone-aware ISO timestamps; never assume UTC. |
| `INVALID_TRADE_RETURN` | A settled trade has an invalid timestamp or return. | Check timezone, return units, and whether the record is settled; do not guess missing returns. |
| `IRREGULAR_CADENCE` | A positive interval differs from the declared cadence. | Check sessions, exchange downtime, and missing bars; do not fill gaps without evidence. |
| `LOOKAHEAD_OR_SAME_BAR_ENTRY` | An entry was not strictly after the declared signal bar close. | Reconcile indicator availability, decision timestamp, and execution timing; do not shift timestamps to hide the violation. |
| `LOW_TRADE_COUNT` | The sample contains fewer than 30 valid trades. | Collect additional genuinely out-of-sample trades before interpreting stability measures. |
| `MISSING_LEDGER_COLUMN` | A trade timing row is missing a required timestamp field. | Verify the ledger export and expected column names without synthesizing timing evidence. |
| `MISSING_OHLCV_COLUMN` | A candle row is missing one or more required OHLCV fields. | Verify the exported header and column mapping; do not invent missing prices. |
| `NEXT_BAR_EXECUTION_VIOLATION` | Declared next-bar timing is inconsistent with the entry. | Check the next executable bar open and ensure entry was not recorded before it. |
| `NO_VALID_TRADES` | No valid settled trade returns remained after validation. | Check required fields and source export quality before computing performance metrics. |
| `NON_MONOTONIC_TIMESTAMP` | Candle timestamps did not increase strictly. | Inspect the export ordering and any overlapping data partitions before sorting. |
| `SHORT_TIME_COVERAGE` | Valid trades span fewer than three distinct calendar months. | Extend the independent observation period; avoid treating a short window as robust evidence. |
| `SIGNAL_CAUSALITY_NOT_VERIFIED` | The trade-summary CSV does not establish when signals became knowable. | Supply a separately auditable signal-to-fill ledger before making causal claims. |
| `UNDEFINED_COMPOUNDING_COST_SCENARIO` | A cost-stressed return cannot be compounded as a simple trade proxy. | Inspect return-unit assumptions and cost magnitude; do not interpret the undefined proxy as account NAV. |
