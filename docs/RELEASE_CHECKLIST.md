# Backtest Doctor release checklist

## Safety (must pass)

- [x] Code and fixtures are created from public-source software and synthetic examples only.
- [x] No access to or copying from private private trading, exchange-data, or research databases.
- [x] A clean, new history is prepared; no private repository history is imported.
- [x] Source + sdist + wheel allowlist checks, secret/path scans, no network/runtime-code-execution AST gate.
- [ ] Confirm public GitHub repository exists and inspect the *actual published tree*.
- [ ] Enable GitHub branch protection and verify Actions matrix in new repository.

## Compatibility

- [x] Python 3.10 and 3.12 on Linux: V0.3 wheel 52/52 tests, earlier stage.
- [ ] Current release candidate wheel 3.10 / 3.11 / 3.12 / 3.13 full suite.
- [ ] Windows and macOS CI green (do not claim support before real test runs).

## Distribution

- [ ] GitHub repo created and initial clean-history commit pushed.
- [ ] Tag/release is created from audited commit.
- [ ] PyPI package ownership/name availability checked by authenticated publisher.
- [ ] PyPI trusted publishing configured for exact repo/workflow before uploading.
- [ ] Only after a verified package URL exists, change README install instruction from conditional to unconditional.

GitHub publication and PyPI publication are separate milestones. Fail closed: no credential disclosure, no auto-publish via personal access tokens embedded in config.
