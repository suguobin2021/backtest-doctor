# GitHub Actions integration (experimental)

Use the composite action in another public repository, **with synthetic test
fixtures first**. A consumer workflow example (after checking out your own
repo) is:

```yaml
name: Audit example backtest exports
on: [pull_request]
permissions:
  contents: read
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: suguobin2021/backtest-doctor/.github/actions/audit@main
        with:
          ohlcv-file: examples/ohlcv_good.csv
          ledger-file: examples/ledger_good.csv
          stability-file: examples/stability_demo.csv
          fail-on-warn: 'false'
```

Replace the example paths with CSV files that match the documented schemas.
The sample has **four synthetic trades** and returns WARN (low trade count),
which exits 0 unless `fail-on-warn: 'true'` is selected. A genuinely invalid
ledger returns FAIL and exits 1. The caller must check its own datasets and
permissions, since no private datasets are bundled.

**Versioning:** `@main` is suitable only for initial testing. For reproducible
production CI, pin the action to an audited full commit SHA from the main
branch that includes `.github/actions/audit/action.yml`. The older
`v0.4.0rc1` tag predates the action and must not be used for this feature.

**Privacy:** execution occurs on GitHub-hosted runners, NOT the user's private
machine. GitHub Actions may retain console output; JSON reports contain
aggregate statistics and row numbers. Do not run this on sensitive private
trade files unless your own data-handling policy permits processing on that
runner. The CLI itself does not transmit trade records or API requests, but
its packaging dependencies can be downloaded during installation.

**Limits:** the action checks exported CSV fields, not trading strategies or
alpha source code. A PASS is not proof of causality or future profitability.

## Optional mapped CSV columns

Supply columns-file: examples/columns_synthetic.json to map alternate CSV headings.
See the column mapping guide; never send private trading data to hosted CI without authorization.
