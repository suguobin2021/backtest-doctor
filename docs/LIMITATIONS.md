# What Backtest Doctor does not prove

**A passed audit is not proof of a legitimate trading edge.** Input fields are supplied by the caller and are not independently sourced from a point-in-time market-data vendor.

- `ohlcv`: validates local structural consistency, not completeness of the historical investible universe, official delisting records, exchange downtime or vendor accuracy.
- `ledger`: checks declared signal-bar-close/entry/next-bar ordering. It does not inspect strategy AST, prove actual fillability, reconstruct liquidity, detect every repainting indicator or verify exchange trades.
- `stability`: uses reported per-trade gross return fractions, simple per-trade cost subtraction and a sequential, non-overlapping, equal-equity proxy. It does not reconstruct real leverage, borrow, funding, portfolio NAV, concurrent positions or actual costs.
- `bundle`: aggregates independent diagnostics. A passing bundle does not prove that the three CSVs refer to the same trades, same universe, or same sampling window.

Reports omit raw input values, filenames, symbols and account details. Rows and aggregate metrics may still be sensitive in some circumstances: review before distribution. The tool assumes the local filesystem and Python environment are trustworthy.
