# Backtest Doctor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)

**An offline, zero-runtime-dependency integrity check for exported backtests.** Validate timestamped OHLCV data, declared signal-to-fill timing, and how aggregate trade returns change under transaction costs. Produce deterministic, minimal JSON and self-contained HTML reports without including raw trades or filenames.

> This tool checks the evidence you supply. It does **not** inspect or execute strategy source code; it cannot prove a strategy is free of look-ahead bias, overfitting, survivorship bias, or execution risk. `PASS` means only that the implemented checks found no violations in the supplied fields.

## Install

Requires Python 3.10+. The current PyPI distribution is a **prerelease**, not a stable release. Install the verified version explicitly:

```sh
python -m pip install --pre "backtest-doctor==0.4.0rc4"
python -m backtest_doctor --version
```

Alternatively, install from the [audited GitHub Release](https://github.com/suguobin2021/backtest-doctor/releases/tag/v0.4.0rc4) or from this source checkout:

```sh
python -m pip install .
python -m backtest_doctor --help
```

[PyPI project](https://pypi.org/project/backtest-doctor/0.4.0rc4/) · [Distribution guidance](docs/PYPI_PUBLISHING.md).

## 30-second synthetic demo

```sh
# Run from the repository root; ALL sample files are synthetic.
python -m backtest_doctor bundle \
  --ohlcv-file examples/ohlcv_good.csv \
  --ledger-file examples/ledger_bad.csv \
  --stability-file examples/stability_demo.csv \
  --html doctor-report.html --fail-on-warn
```

The intentionally bad ledger produces `FAIL` and exits **1**; this is expected, not an installation failure. Try `examples/ledger_good.csv` instead to see a clean causal timing check. Stability may still return `WARN` for small samples. The command exits `0` for PASS, `1` for FAIL (and WARN with `--fail-on-warn`), and `2` for rejected input. For an HTML report opened locally, use a **new filename**; the CLI will not overwrite an existing file.

For a **complete cross-platform, beginner-friendly walkthrough**, follow [the synthetic quickstart](docs/QUICKSTART.md). For the manual, secretless PyPI publishing process, see [the distribution guide](docs/PYPI_PUBLISHING.md).

For CI integration in other repositories, see the [experimental GitHub Action](docs/ACTION_USAGE.md).

Add `--explain` to any audit command for **fixed, data-free diagnostic explanations and investigation suggestions**. Explanations are opt-in, preserving the default JSON format. See the [finding guide](docs/FINDING_CODES.md).

**NEW: experimental framework-export CSV adapters:** inspect settled trade summaries from `backtesting.py`, `vectorbt`, or a manually prepared Freqtrade CSV subset (not native Freqtrade ZIP/JSON):

```sh
python -m backtest_doctor import-trades examples/backtesting_py_synthetic.csv --framework backtesting-py
python -m backtest_doctor import-trades examples/vectorbt_synthetic.csv --framework vectorbt
python -m backtest_doctor import-trades examples/freqtrade_csv_synthetic.csv --framework freqtrade-csv
```

These checks cannot verify causal signal timing, and they do not double-count framework-reported costs by default. See [framework CSV contracts, known limits and privacy model](docs/FRAMEWORK_TRADES.md).

For synthetic examples of alternate CSV column names (without copying any private exports), see [declarative column mapping](docs/COLUMN_MAPPING.md).

## Checks

| Mode | Input | Detects / summarizes |
| --- | --- | --- |
| `ohlcv` | CSV with `timestamp,open,high,low,close,volume` | Invalid candle geometry, duplicate/non-monotone timestamps, irregular cadence (when configured) |
| `ledger` | CSV with `signal_bar_close,entry_time,next_bar_open` | Entry before or at signal close; entry before claimed next bar; both stop and target hit within the same bar |
| `stability` | CSV with `exit_time,gross_return` | Trade count, time-coverage warnings, cost-scenario expectancy, PF, win rate, simplified sequential equity/drawdown proxies |
| `bundle` | All three CSVs | All checks, one aggregate report and exit status |

Single-mode invocation:

```sh
python -m backtest_doctor ohlcv examples/ohlcv_good.csv --interval-seconds 60
python -m backtest_doctor ledger examples/ledger_bad.csv
python -m backtest_doctor stability examples/stability_demo.csv
```

**Profit factor is undefined (reported as `null`) if no negative trades exist.** All stability returns are fractions: `0.01` means 1%. Compounded returns and drawdown are explicitly **proxies**, not portfolio NAV or account-level PnL. Overlapping trades, leverage, funding, slippage, execution limits and corporate actions are not reconstructed. Costs are specified in basis points per trade (default 0, 8, 20 bps).

## Privacy model

No networking, telemetry, trade execution, or strategy source evaluation. Reads local regular CSV files only (up to 10 MiB, 100,000 rows) and emits aggregate metrics and coded findings only. It is intentionally **not a security sandbox**: do not use it to evaluate untrusted adversarial filesystem access, and inspect reports before sharing. See [SECURITY.md](SECURITY.md).

This repo uses synthetic fixtures only. It has no live trading records, private quantitative research databases, exchange API keys, real account IDs, strategy-specific parameters, server credentials, or licensed market datasets. Only explicitly allowlisted code, docs, tests, and synthetic fixtures are bundled by the build process.

## Contribute and reproducibility

```sh
python -m unittest discover -s tests -v
python -m pip wheel . --no-deps -w dist
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [docs/LIMITATIONS.md](docs/LIMITATIONS.md), and [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md). MIT-licensed. No claim of investment performance or financial advice.
