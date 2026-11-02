# Contributing

1. Discuss changes in an issue or pull request and keep each contribution focused on a reproducible validation rule.
2. Include a minimal **synthetic** test fixture. Do not share account, market-vendor, proprietary strategy, portfolio, PnL, or private trading data.
3. Keep the runtime standard-library-only, fully offline, deterministic, compatible with Python 3.10+, and free from dynamic code execution.
4. Document false-positive conditions and what a result **does not** establish.
5. Run `PYTHONPATH=src python -m unittest discover -s tests -v` before submitting. CI covers Linux, Windows and macOS after publication.

No trading signals, execution accounts, proprietary parameters, real order histories or exchange data belong in this repository.
