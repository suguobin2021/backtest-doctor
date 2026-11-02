# PyPI publishing via Trusted Publisher (no permanent tokens)

## Verified first publication — 2026-11-03

**Backtest Doctor 0.4.0rc4 is available on PyPI as a prerelease.** It was uploaded from the immutable `v0.4.0rc4` tag using `.github/workflows/publish-pypi.yml` and the `pypi` environment, with GitHub OIDC rather than permanent API keys.

The [official publishing run](https://github.com/suguobin2021/backtest-doctor/actions/runs/41543443737) succeeded. Both PyPI artifacts were downloaded from the public index, their SHA256 hashes verified, and their code compared with the exact public Git tag commit `d45ca5ea63ff96f3d1c67a96a00984b368cb24d8`. Public-source and distribution allowlist checks passed. Isolated installs and synthetic smoke tests passed on Linux Python 3.10 and Python 3.12.

To install this **prerelease** (requires Python 3.10+):

```sh
python -m pip install --pre "backtest-doctor==0.4.0rc4"
python -m backtest_doctor --version
```

Project: https://pypi.org/project/backtest-doctor/0.4.0rc4/

Do **not** claim that a stable `0.4.0` is already available. The framework CSV adapters remain experimental and no real account data or proprietary datasets were used.

## Future releases

1. Review a public-only PR, the exact source change set, security allowlist, and synthetic cross-platform CI.
2. Update `pyproject.toml` and `src/backtest_doctor/__init__.py` consistently. Create a **new**, immutable tag matching the version; never re-use a version or move an existing tag.
3. Use the existing `publish-pypi.yml` workflow on that tag with `DRY_RUN` first. Use `PUBLISH` only after the specific artifacts and target have been approved.
4. Retain the GitHub `pypi` Environment, PyPI Trusted Publisher, and per-job `id-token: write`; do not store PyPI secrets in the repository.
5. Independently inspect PyPI hashes, distribution content, and fresh installations on at least two supported Python versions after every release.

GitHub Environment required-reviewer protection and tag restrictions are recommended, but **were not independently confirmed enabled**. Publishing a final `0.4.0` also requires stability review of the experimental adapters.

Official docs:
- https://docs.pypi.org/trusted-publishers/using-a-publisher/
- https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
- https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
