"""Offline-only CLI. JSON and HTML reports redact input values and paths."""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

from . import __version__
from .audit import audit_ledger, audit_ohlcv, audit_stability, read_csv
from .bundle import audit_bundle
from .report import render_html
from .schema import load_columns, normalize_rows
from .adapters import FORMATS, audit_imported_trades


def _save_new_report(path, content):
    """Exclusive creation prevents accidental overwrite and output symlink following."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            out.write(content)
    except BaseException:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(prog='backtest-doctor', description='Offline CSV backtest audit; no strategy execution or telemetry')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('mode', choices=['ohlcv', 'ledger', 'stability', 'bundle', 'import-trades'])
    parser.add_argument('file', type=Path, nargs='?')
    parser.add_argument('--ohlcv-file', type=Path)
    parser.add_argument('--ledger-file', type=Path)
    parser.add_argument('--stability-file', type=Path)
    parser.add_argument('--interval-seconds', type=int)
    parser.add_argument('--framework', choices=sorted(FORMATS), help='Trade export CSV dialect (import-trades only)')
    parser.add_argument('--additional-cost-bps', type=float, default=0.0, help='Extra hypothetical cost stress for import-trades; 0 means no new fees')
    parser.add_argument('--html', type=Path, help='Create a privacy-minimal HTML report, without overwrite')
    parser.add_argument('--columns', type=Path, help='Local JSON canonical-to-source column aliases')
    parser.add_argument('--fail-on-warn', action='store_true', help='Exit 1 for WARN as well as FAIL (CI mode)')
    args = parser.parse_args(argv)
    try:
        columns = load_columns(args.columns) if args.columns is not None else {}
        if args.mode != 'import-trades' and (args.framework is not None or args.additional_cost_bps != 0):
            raise ValueError('framework settings require import-trades')
        if args.mode == 'import-trades':
            if (args.file is None or args.framework is None or args.columns is not None
                    or args.interval_seconds is not None or any((args.ohlcv_file, args.ledger_file, args.stability_file))):
                raise ValueError('import-trades requires CSV and framework only')
            report = audit_imported_trades(read_csv(args.file), args.framework, args.additional_cost_bps)
        elif args.mode == 'bundle':
            if (args.file is not None or args.ohlcv_file is None or args.ledger_file is None
                    or args.stability_file is None):
                raise ValueError('bundle requires three named inputs and no positional file')
            report = audit_bundle(
                ohlcv_rows=normalize_rows(read_csv(args.ohlcv_file), 'ohlcv', columns),
                ledger_rows=normalize_rows(read_csv(args.ledger_file), 'ledger', columns),
                stability_rows=normalize_rows(read_csv(args.stability_file), 'stability', columns),
                interval_seconds=args.interval_seconds,
            )
        else:
            if args.file is None or any((args.ohlcv_file, args.ledger_file, args.stability_file)):
                raise ValueError('invalid input selection')
            rows = normalize_rows(read_csv(args.file), args.mode, columns)
            if args.mode == 'ohlcv':
                report = audit_ohlcv(rows, args.interval_seconds)
            elif args.mode == 'ledger':
                report = audit_ledger(rows)
            else:
                report = audit_stability(rows)
        if args.html is not None:
            _save_new_report(args.html, render_html(report))
        print(json.dumps(report, allow_nan=False, sort_keys=True, separators=(',', ':')))
        return 1 if report['status'] == 'FAIL' or (args.fail_on_warn and report['status'] == 'WARN') else 0
    except (ValueError, OSError, UnicodeError, OverflowError, csv.Error):
        print('AUDIT_ERROR: invalid or inaccessible input (details redacted)', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
