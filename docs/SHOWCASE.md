# Reproducible offline demonstrations

Backtest Doctor checks evidence structure, **not** strategy alpha. All fixtures are invented and suitable for public sharing.

## Bad candle and clean candle

```sh
python -m backtest_doctor ohlcv examples/ohlcv_good.csv
python -m backtest_doctor ohlcv examples/ohlcv_bad.csv --explain
```

## Impossible fill timing

```sh
python -m backtest_doctor ledger examples/ledger_bad.csv --explain
```

The intentionally invalid ledger returns FAIL / exit code 1. It is a successful negative test, not an installation error.

## Caution about fees and sample size

```sh
python -m backtest_doctor stability examples/stability_demo.csv --explain
python -m backtest_doctor import-trades examples/vectorbt_synthetic.csv --framework vectorbt --additional-cost-bps 20 --explain
```

This stresses already-reported returns using a hypothetical extra 20 bps per trade. Four synthetic trades cannot establish a statistically reliable edge, and the simplified compounding proxy is not account NAV.

## Contributing

See https://github.com/suguobin2021/backtest-doctor/issues and submit minimal **synthetic** reproductions only. Useful requests include source format mismatches, redaction mistakes, diagnostics false positives, documentation issues, and cross-platform portability. Do not post keys, personal records, actual fills or unpublished strategies. No paid stars, automated spam, or manufactured endorsements.
