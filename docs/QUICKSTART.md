# Quickstart: validate a public synthetic backtest without Git

Backtest Doctor inspects local evidence structures. It does **not** validate strategy source, claim a strategy has no look-ahead bias or determine whether it makes money.

## 1. Install the stable package

Requires Python 3.10 or later:

```sh
python -m pip install "backtest-doctor==0.4.1"
python -m backtest_doctor --version
```

This uses PyPI and should print `0.4.1`. On Windows, `py -3` can replace `python` if Python is registered through the Python launcher. Use a virtual environment if you want to avoid changing an existing Python installation.

## 2. Download one invented CSV and get a PASS

The following one-liner **downloads only a public, tagged synthetic example**. It does not access any private backtest data:

```sh
python -c "from urllib.request import urlretrieve; urlretrieve('https://raw.githubusercontent.com/suguobin2021/backtest-doctor/v0.4.1/examples/ohlcv_good.csv', 'synthetic_ohlcv.csv')"
python -m backtest_doctor ohlcv synthetic_ohlcv.csv --explain
```

Expected: output JSON has `"status": "PASS"` and `"rows_examined": 3`; exit code `0`. Only fixture download and initial installation use the network. `backtest_doctor` checks local rows offline.

## 3. Verify that the tool really detects an error

```sh
python -c "from urllib.request import urlretrieve; urlretrieve('https://raw.githubusercontent.com/suguobin2021/backtest-doctor/v0.4.1/examples/ledger_bad.csv', 'synthetic_bad_ledger.csv')"
python -m backtest_doctor ledger synthetic_bad_ledger.csv --explain
```

Expected: `"status": "FAIL"` with three diagnostic explanations, exit code `1`. This invented input **intentionally** declares impossible entry times. A nonzero exit status confirms the negative test is functioning. Do not paste real orders or account records in a public bug report.

These **exact three steps** were run on Linux with a fresh isolated PyPI `0.4.1` installation on 2026-11-11: normal candle test PASS (3 rows), fabricated bad ledger FAIL (3 explanations).

## 4. Optional: clone the public source for more examples

```sh
git clone https://github.com/suguobin2021/backtest-doctor.git
cd backtest-doctor
python -m backtest_doctor stability examples/stability_demo.csv --explain
python -m backtest_doctor import-trades examples/vectorbt_synthetic.csv --framework vectorbt --additional-cost-bps 20 --explain
```

These are deliberately tiny invented inputs; sample-size warnings are expected. The vectorbt integration reads a **limited settled-trade CSV**, not the vectorbt engine or a full portfolio NAV.

## 5. Generate a self-contained HTML report (from the cloned source)

```sh
python -m backtest_doctor bundle \
  --ohlcv-file examples/ohlcv_good.csv \
  --ledger-file examples/ledger_good.csv \
  --stability-file examples/stability_demo.csv \
  --html synthetic-audit-report.html
```

Expected `"status": "WARN"`, exit `0` because there are only four illustrative trades. The HTML contains aggregate diagnostics, not raw trade rows; review it before sharing. Use a **new output filename** because the CLI refuses to overwrite an existing report.

On Windows PowerShell, run the `bundle` invocation on one line or replace shell line continuations with PowerShell backticks. The `python -c` fixture download commands above work unchanged in PowerShell.

For CI, use `--fail-on-warn` to reject warnings with exit code `1`. Rejected input exits `2`.

## Privacy and scope

The installed CLI does not send your input CSV to any service. Package download, public synthetic-fixture download, and optional repository clone do use the network. Real trade and strategy data remain on your own computer. Do not post private datasets, credentials or proprietary strategies to public issues.

An audit `PASS` means only that the checks implemented here did not find a violation in the fields supplied. It does not prove point-in-time validity, execution fillability or investment performance. See [Limitations](LIMITATIONS.md) and [Security](../SECURITY.md).
