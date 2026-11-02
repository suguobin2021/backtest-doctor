"""Fail-closed public-source and distribution content gate.

Runs offline, relies only on the standard library, and never reads other project
folders. This is a defense-in-depth check, not a proof of absence of secrets.
"""
from __future__ import annotations

import argparse
import ast
import io
import re
import stat
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

EXPECTED_TRACKED = frozenset({
    '.github/actions/audit/action.yml',
    '.github/workflows/ci.yml',
    '.github/workflows/publish-rc.yml',
    '.github/workflows/publish-pypi.yml',
    '.gitignore',
    'CONTRIBUTING.md',
    'LICENSE',
    'MANIFEST.in',
    'README.md',
    'SECURITY.md',
    'docs/ACTION_USAGE.md',
    'docs/COLUMN_MAPPING.md',
    'docs/FRAMEWORK_TRADES.md',
    'docs/LIMITATIONS.md',
    'docs/QUICKSTART.md',
    'docs/PYPI_PUBLISHING.md',
    'docs/RELEASE_CHECKLIST.md',
    'examples/ledger_bad.csv',
    'examples/ledger_good.csv',
    'examples/columns_synthetic.json',
    'examples/ohlcv_alias.csv',
    'examples/backtesting_py_synthetic.csv',
    'examples/vectorbt_synthetic.csv',
    'examples/freqtrade_csv_synthetic.csv',
    'examples/ledger_alias.csv',
    'examples/stability_alias.csv',
    'examples/ohlcv_bad.csv',
    'examples/ohlcv_good.csv',
    'examples/stability_demo.csv',
    'pyproject.toml',
    'setup.py',
    'src/backtest_doctor/__init__.py',
    'src/backtest_doctor/__main__.py',
    'src/backtest_doctor/audit.py',
    'src/backtest_doctor/bundle.py',
    'src/backtest_doctor/cli.py',
    'src/backtest_doctor/report.py',
    'src/backtest_doctor/schema.py',
    'src/backtest_doctor/adapters.py',
    'tests/test_column_aliases.py',
    'tests/test_framework_adapters.py',
    'tests/test_bundle.py',
    'tests/test_doctor.py',
    'tests/test_hardening.py',
    'tests/test_release_gate.py',
    'tests/test_security_regression.py',
    'tests/test_upstream_optional.py',
    'tools/verify_release.py',
})

RUNTIME = frozenset(p for p in EXPECTED_TRACKED if p.startswith('src/backtest_doctor/'))
FORBIDDEN_IMPORT_ROOTS = frozenset({
    'socket', 'subprocess', 'requests', 'httpx', 'urllib', 'http', 'ftplib',
    'paramiko', 'boto3', 'supabase', 'ccxt', 'pickle', 'marshal', 'ctypes',
})
FORBIDDEN_CALLS = frozenset({'eval', 'exec', 'compile', '__import__'})
SENSITIVE_MARKERS = (
    '/home/' + 'githubops/',
    '/var/lib/' + 'research-operations/',
    '/opt/' + 'shadow-pnl',
    'research-' + 'control-vault',
    'private-' + 'runtime/',
    '-----BEGIN ' + 'PRIVATE KEY-----',
)
TOKEN_PATTERNS = (
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{40,}\b'),
    re.compile(r'\bAKIA[A-Z0-9]{16}\b'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
)


class ReleaseGateError(ValueError):
    pass


def scan_text(data: bytes, label: str) -> None:
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ReleaseGateError(f'{label}: non-UTF8 payload') from exc
    for marker in SENSITIVE_MARKERS:
        if marker.casefold() in text.casefold():
            raise ReleaseGateError(f'{label}: sensitive marker detected')
    for pattern in TOKEN_PATTERNS:
        if pattern.search(text):
            raise ReleaseGateError(f'{label}: credential-like token detected')


def audit_runtime_ast(data: bytes, label: str) -> None:
    tree = ast.parse(data.decode('utf-8-sig'), filename=label)
    for node in ast.walk(tree):
        imports = []
        if isinstance(node, ast.Import):
            imports = [v.name for v in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports = [node.module]
        for name in imports:
            if name.split('.')[0] in FORBIDDEN_IMPORT_ROOTS:
                raise ReleaseGateError(f'{label}: forbidden runtime import {name}')
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_CALLS:
                raise ReleaseGateError(f'{label}: forbidden dynamic execution')
            if isinstance(func, ast.Attribute) and func.attr == 'system':
                if isinstance(func.value, ast.Name) and func.value.id == 'os':
                    raise ReleaseGateError(f'{label}: forbidden shell execution')


def _member_name_safe(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not name.startswith('/') and '\\' not in name and '..' not in p.parts


def check_source(root: Path) -> None:
    if not (root / '.git').exists():
        raise ReleaseGateError('source must be a Git checkout')
    proc = subprocess.run(
        ['git', '-C', str(root), 'ls-files', '-z'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    tracked = frozenset(x.decode('utf-8') for x in proc.stdout.split(b'\0') if x)
    if tracked != EXPECTED_TRACKED:
        missing = sorted(EXPECTED_TRACKED - tracked)
        extra = sorted(tracked - EXPECTED_TRACKED)
        raise ReleaseGateError(f'public source allowlist mismatch: missing={missing}; extra={extra}')
    for rel in sorted(tracked):
        p = root / rel
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 1024 * 1024:
            raise ReleaseGateError(f'{rel}: forbidden source type or size')
        contents = p.read_bytes()
        scan_text(contents, rel)
        if rel in RUNTIME:
            audit_runtime_ast(contents, rel)
    csv_paths = {p for p in tracked if p.endswith('.csv')}
    if not csv_paths or not all(x.startswith('examples/') for x in csv_paths):
        raise ReleaseGateError('only synthetic example CSV files may be tracked')
    print(f'PUBLIC_SOURCE_GATE=PASS;TRACKED_FILES={len(tracked)};RUNTIME_FILES={len(RUNTIME)}')


def _dist_members_wheel(path: Path, root: Path) -> None:
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ReleaseGateError('wheel archive CRC failed')
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ReleaseGateError('wheel duplicate entry')
        actual_code = set()
        for member in z.infolist():
            name = member.filename
            if not _member_name_safe(name) or member.is_dir():
                raise ReleaseGateError('wheel unsafe member')
            mode = (member.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ReleaseGateError('wheel link member')
            if name.startswith('backtest_doctor/') and name.endswith('.py'):
                if 'src/' + name not in RUNTIME:
                    raise ReleaseGateError('wheel unexpected Python module')
                actual_code.add('src/' + name)
                if z.read(name) != (root / ('src/' + name)).read_bytes():
                    raise ReleaseGateError('wheel code does not match source')
            elif re.fullmatch(r'backtest_doctor-[^/]+\.dist-info/(?:licenses/LICENSE|METADATA|WHEEL|RECORD|entry_points\.txt|top_level\.txt)', name):
                pass
            else:
                raise ReleaseGateError('wheel includes an unallowlisted member')
            scan_text(z.read(name), 'wheel:' + name)
        if actual_code != RUNTIME:
            raise ReleaseGateError('wheel missing runtime source module')


def _dist_members_sdist(path: Path, root: Path) -> None:
    with tarfile.open(path, 'r:gz') as t:
        members = t.getmembers()
        if len(members) != len({m.name for m in members}):
            raise ReleaseGateError('sdist duplicate entry')
        actual_source = set()
        for member in members:
            if not _member_name_safe(member.name) or not (member.isfile() or member.isdir()):
                raise ReleaseGateError('sdist unsafe member')
            relparts = PurePosixPath(member.name).parts
            if len(relparts) < 2:
                continue
            name = '/'.join(relparts[1:])
            if member.isdir():
                continue
            if name in EXPECTED_TRACKED and not name.startswith('.github/'):
                if t.extractfile(member).read() != (root / name).read_bytes():
                    raise ReleaseGateError('sdist tracked source mismatch')
                actual_source.add(name)
            elif re.fullmatch(r'(?:src/backtest_doctor\.egg-info/(?:PKG-INFO|SOURCES\.txt|dependency_links\.txt|entry_points\.txt|top_level\.txt)|PKG-INFO|setup\.cfg)', name):
                pass
            else:
                raise ReleaseGateError('sdist includes unallowlisted content')
            scan_text(t.extractfile(member).read(), 'sdist:' + name)
        if not RUNTIME.issubset(actual_source):
            raise ReleaseGateError('sdist missing runtime code')


def check_distributions(root: Path, dist_dir: Path) -> None:
    wheels = sorted(dist_dir.glob('*.whl'))
    sdists = sorted(dist_dir.glob('*.tar.gz'))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ReleaseGateError('expected exactly one wheel and one sdist')
    _dist_members_wheel(wheels[0], root)
    _dist_members_sdist(sdists[0], root)
    print('PUBLIC_DISTRIBUTION_GATE=PASS;WHEEL=1;SDIST=1')


def main() -> int:
    parser = argparse.ArgumentParser(description='Offline public-source release audit')
    parser.add_argument('--source', type=Path, default=Path('.'))
    parser.add_argument('--dist', type=Path, default=None)
    args = parser.parse_args()
    try:
        root = args.source.resolve()
        check_source(root)
        if args.dist is not None:
            check_distributions(root, args.dist.resolve())
    except (ReleaseGateError, OSError, subprocess.CalledProcessError, SyntaxError, zipfile.BadZipFile, tarfile.TarError) as exc:
        print('PUBLIC_RELEASE_GATE=FAIL;REASON=' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
