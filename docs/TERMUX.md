# Android Termux guide

The owner verified **Android aarch64 Termux / Python 3.13.13** can install and import prerelease 0.4.0rc4. This proves only installation and version reporting, **not** end-to-end Android audit correctness.

Stable PyPI is published. Install the default stable package on Termux:

```sh
pkg install python git -y
python -m pip install backtest-doctor
python -m backtest_doctor --version
```

The historical verified prerelease can still be pinned explicitly:

```sh
python -m pip install --pre "backtest-doctor==0.4.0rc4"
```

For safe local demos, clone only the public repository:

```sh
git clone https://github.com/suguobin2021/backtest-doctor.git
cd backtest-doctor
python -m backtest_doctor ohlcv examples/ohlcv_good.csv
python -m backtest_doctor ledger examples/ledger_bad.csv --explain
```

The first invented fixture should return PASS. The second intentionally returns FAIL and exit code 1 because its fabricated trading timestamps are inconsistent. No private trading files are needed. Git/pip download public code over the network; the auditing runtime does not transmit your input CSV.
