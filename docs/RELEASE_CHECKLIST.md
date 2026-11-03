# Backtest Doctor release checklist

## Safety (must pass)

- [x] Code and fixtures are created from public-source software and synthetic examples only.
- [x] No access to or copying from private private trading, exchange-data, or research databases.
- [x] A clean, new history is prepared; no private repository history is imported.
- [x] Source + sdist + wheel allowlist checks, secret/path scans, no network/runtime-code-execution AST gate.
- [x] Public GitHub tree and v0.4.0rc4 prerelease were independently verified on 2026-11-02.
- [ ] Enable GitHub branch protection (requires repository administrator setting).

## Compatibility

- [x] Python 3.10 and 3.12 on Linux: V0.3 wheel 52/52 tests, earlier stage.
- [x] GitHub CI for 3.10 / 3.11 / 3.12 / 3.13 completed on 2026-11-02; ongoing checks must be green before another release.
- [x] Windows and macOS GitHub CI completed successfully on 2026-11-02.

## Distribution

- [x] GitHub repo created and initial audited public-source commit pushed.
- [x] v0.4.0rc4 GitHub prerelease attached to audited commit.
- [x] PyPI 0.4.0rc4 published and listed by the public Simple API.
- [x] PyPI OIDC trusted publishing confirmed by successful GitHub Actions upload.
- [x] README now documents the verified PyPI prerelease with explicit --pre installation.

GitHub publication and PyPI publication are separate milestones. Fail closed: no credential disclosure, no auto-publish via personal access tokens embedded in config.

## New P0 gates

- [ ] Publish stable package only from a reviewed matching Git tag.
- [x] PyPI Trusted Publisher activated by first successful upload, with no long-lived token.
- [x] PyPI wheel/sdist independently checked; installed on Python 3.10 and 3.12.
- [x] Offline source allowlist + wheel/sdist content gate implemented in `tools/verify_release.py`.
- [x] Beginner synthetic guide added in `docs/QUICKSTART.md`.

## Stable release readiness (2026-11-03)

- [x] Public upstream backtesting.py / vectorbt / Freqtrade field contracts reviewed, with timezone and fee limitations explicit.
- [x] Added Termux, reproducible public synthetic showcase and contributor issue templates.
- [ ] Stable version Git tag + verified GitHub artifacts and PyPI publication completed.
- [ ] PyPI stable source equivalence and clean Python 3.10/3.12 installs confirmed.
- [ ] Required-reviewer / protected-tag settings activated by repository administrator; app cannot configure them.
