# Quickstart: prove the CLI works without real trading data

All inputs in this guide are **synthetic**. No account, trading system, private strategy, or market-data export is needed. The tool operates offline and does not transmit your CSV rows.

## 1. Install from the public source

Requires Python 3.10 or newer and Git. On macOS/Linux, run:

```sh
git clone https://github.com/suguobin2021/backtest-doctor.git
cd backtest-doctor
python3 -m venv .venv
.venv/bin/python -m pip install --no-deps .
.venv/bin/python -m backtest_doctor --version
```

On Windows PowerShell, replace `python3` with `py -3` and each `.venv/bin/python` with `.venv/Scripts/python.exe`. Do not upload your own CSV files to a third-party service to try this demo.

Install from stable PyPI with `python -m pip install backtest-doctor`; version pinning `backtest-doctor==0.4.1` is recommended for reproducibility.

## 2. Pass an OHLCV structure check

```sh
.venv/bin/python -m backtest_doctor ohlcv examples/ohlcv_good.csv
```

Expect a JSON result containing `"status":"PASS"` and exit code **0**. This means the supplied rows passed **implemented** checks only.

## 3. Detect an intentionally invalid fill

```sh
.venv/bin/python -m backtest_doctor ledger examples/ledger_bad.csv
```

Expect `"status":"FAIL"` and exit code **1**. A non-zero exit is the **expected result for this synthetic negative test**, not an installation error. If you want a successful ledger sample, use `examples/ledger_good.csv`.

## 4. Generate an offline HTML report

```sh
.venv/bin/python -m backtest_doctor bundle \
  --ohlcv-file examples/ohlcv_good.csv \
  --ledger-file examples/ledger_good.csv \
  --stability-file examples/stability_demo.csv \
  --html local-audit-report.html
```

Expect `"status":"WARN"` with exit **0**: there are only four illustrative trades, so sample-size warnings are intentional. The HTML file is self-contained and includes aggregate findings rather than raw CSV rows. The CLI will not overwrite an existing output file. Do not publish the report without reviewing its aggregated information.

Pass `--fail-on-warn` if warnings must fail your own CI pipeline.

## 5. Know the limits

The tool checks declared timestamps and elementary candle structure. It does not execute your strategy, prove actual fillability, detect all look-ahead biases, or establish a profitable strategy. The example returns are invented.

See [Limitations](LIMITATIONS.md) and [Security](../SECURITY.md).
