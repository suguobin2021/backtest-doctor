# Changelog

## 0.4.0 — stable core release

- Stable **core** offline audits: OHLCV structure, declared trade timing, trade-return cost stress and aggregate JSON/HTML reports.
- Explicit CSV header aliases, diagnostic explanations, synthetic-only GitHub composite Action.
- Experimental and limited closed-trade summary CSV adapters for backtesting.py, vectorbt and a manually prepared Freqtrade CSV subset.
- Zero runtime dependencies, explicit timezone inputs, bounded local files, static source and distribution allowlist.
- Python 3.10–3.13, Windows/macOS CI. Android Termux Python 3.13 was verified for prerelease installation/import; **not** full Android runtime coverage.
- Strict cost-input validation now rejects booleans instead of silently treating True as 1 bps.

## 0.4.0rc4
First verified PyPI OIDC prerelease, opt-in diagnostic explanations.

## 0.4.0rc3
Experimental framework CSV import-trades summaries.

## 0.4.0rc2
CSV header alias mapping.

## 0.4.0rc1
Initial reviewed offline audit prototype.

Passing diagnostics are not proof of trading strategy causality or profitability.
