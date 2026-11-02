# PyPI publishing: guarded, manual, no permanent tokens

**Current state:** PyPI publication is not part of the GitHub prerelease. Do not promise `pip install backtest-doctor` until the PyPI project page and an installation from that index have been independently verified.

The repository contains a guarded workflow `.github/workflows/publish-pypi.yml`. It never runs from ordinary pushes or PRs. It requires manual execution against a matching `vX.Y.Z` **Git tag**, an explicit `PUBLISH` acknowledgement, a successful source/artifact gate, and a GitHub Environment named `pypi`. It uses OIDC Trusted Publishing rather than credentials placed in repository secrets or files.

## One-time setup by the PyPI account owner

1. Sign in to [PyPI](https://pypi.org/), preferably with two-factor authentication, and create a pending publisher for package `backtest-doctor`, **if that name is available**.
2. Set **Owner** = `suguobin2021`, **Repository** = `backtest-doctor`, **Workflow filename** = `publish-pypi.yml`, and **Environment name** = `pypi` (exactly).
3. In GitHub repository settings, create the environment `pypi` with release branch/tag restrictions as appropriate and required reviewer protection if available. Never create a PyPI long-lived token just for this workflow.
4. Prepare a **new** version tag from reviewed and CI-green source. Do not republish or move `v0.4.0rc1` and do not tag an unreviewed commit.
5. Run the workflow manually on that tag, enter `PUBLISH`, and inspect the release checks and upload logs. A no-op dry run can instead use `DRY_RUN`.
6. After publication, verify the package name, project owner, files and SHA256 on PyPI, then install it in a fresh environment on at least two Python versions and run the synthetic demos. Only then update README.

**Critical:** adding the workflow does not enroll a PyPI publisher, set up GitHub environment protections, or prove domain/package ownership. These are separate account-level actions. Never claim that a failed upload is a successful publication.

Official references:
- https://docs.pypi.org/trusted-publishers/using-a-publisher/
- https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
