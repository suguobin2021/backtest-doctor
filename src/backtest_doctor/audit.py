"""Offline CSV diagnostics; accepts no executable strategy code.

Reports intentionally contain finding *codes* and row numbers, never input values,
file paths, credentials, symbols, or strategy-level identifiers.
"""
from __future__ import annotations

import csv
import io
import math
import os
import stat
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 64
MAX_FIELD_BYTES = 131_072
MAX_FINDINGS = 2_000


def _time(value):
    value = str(value).strip()
    if value.endswith('Z'):
        value = value[:-1] + '+00:00'
    stamp = datetime.fromisoformat(value)
    if stamp.utcoffset() is None:
        raise ValueError('timezone required')
    return stamp.astimezone(timezone.utc)


def _num(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('non-finite number')
    return number


def _finding(code, row=None, severity='ERROR'):
    return {'code': code, 'row': row, 'severity': severity}


def _push(findings, code, row=None, severity='ERROR'):
    if len(findings) < MAX_FINDINGS:
        findings.append(_finding(code, row, severity))
    elif len(findings) == MAX_FINDINGS:
        findings.append(_finding('FINDING_LIMIT_REACHED', severity='ERROR'))


def _base(kind, findings, count, extras=None):
    errors = sum(f['severity'] == 'ERROR' for f in findings)
    warnings = sum(f['severity'] == 'WARNING' for f in findings)
    return {
        'report_schema_version': '0.4',
        'audit_type': kind,
        'status': 'FAIL' if errors else ('WARN' if warnings else 'PASS'),
        'errors': errors,
        'warnings': warnings,
        'rows_examined': count,
        'findings': findings,
        'metrics': extras or {},
        'data_policy': 'aggregate-only; no raw inputs included',
    }


def read_csv(path):
    """Read at most 10 MiB from a regular file, with no symlink following.

    The byte cap is enforced even if the file grows after the initial stat.
    This is not a general sandbox against hostile mounts or filesystem races.
    """
    path = Path(path)
    if path.is_symlink():
        raise ValueError('symlink input is prohibited')
    flags = os.O_RDONLY
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as handle:
        st = os.fstat(handle.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_FILE_BYTES:
            raise ValueError('input is not a regular file or is too large')
        raw = handle.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError('input exceeds file size limit')
    content = raw.decode('utf-8-sig')
    csv.field_size_limit(MAX_FIELD_BYTES)
    reader = csv.DictReader(io.StringIO(content, newline=''), strict=True)
    headers = reader.fieldnames
    if (not headers or len(headers) > MAX_COLUMNS or any(not h for h in headers)
            or len(set(headers)) != len(headers)):
        raise ValueError('invalid or duplicate CSV columns')
    rows = []
    for i, row in enumerate(reader, start=1):
        if i > MAX_ROWS:
            raise ValueError('input exceeds row safety limit')
        if None in row or any(v is None for v in row.values()):
            raise ValueError('malformed CSV row')
        rows.append(row)
    return rows


def audit_ohlcv(rows, interval_seconds=None):
    findings, seen, prior = [], set(), None
    required = ('timestamp', 'open', 'high', 'low', 'close', 'volume')
    if interval_seconds is not None and (type(interval_seconds) is not int or interval_seconds <= 0):
        raise ValueError('interval must be positive integer')
    if not rows:
        _push(findings, 'EMPTY_OHLCV')
    for idx, row in enumerate(rows, start=2):
        if not all(k in row for k in required):
            _push(findings, 'MISSING_OHLCV_COLUMN', idx)
            continue
        try:
            stamp = _time(row['timestamp'])
        except (ValueError, TypeError, OverflowError):
            _push(findings, 'INVALID_TIMESTAMP', idx)
            continue
        if stamp in seen:
            _push(findings, 'DUPLICATE_TIMESTAMP', idx)
        seen.add(stamp)
        if prior is not None:
            if stamp <= prior:
                _push(findings, 'NON_MONOTONIC_TIMESTAMP', idx)
            if interval_seconds is not None and stamp > prior:
                delta = (stamp-prior).total_seconds()
                if delta != interval_seconds:
                    _push(findings, 'IRREGULAR_CADENCE', idx, 'WARNING')
        prior = stamp
        try:
            op, hi, lo, cl, vol = (_num(row[k]) for k in required[1:])
        except (TypeError, ValueError, OverflowError):
            _push(findings, 'INVALID_NUMERIC_FIELD', idx)
            continue
        if min(op, hi, lo, cl) <= 0 or vol < 0:
            _push(findings, 'INVALID_PRICE_OR_VOLUME', idx)
        if hi < max(op, cl, lo) or lo > min(op, cl, hi):
            _push(findings, 'INVALID_CANDLE_GEOMETRY', idx)
    return _base('ohlcv', findings, len(rows))


def audit_ledger(rows):
    findings = []
    required = ('signal_bar_close', 'entry_time', 'next_bar_open')
    if not rows:
        _push(findings, 'EMPTY_LEDGER')
    for idx, row in enumerate(rows, start=2):
        if not all(k in row for k in required):
            _push(findings, 'MISSING_LEDGER_COLUMN', idx)
            continue
        try:
            signal, entry, next_open = (_time(row[k]) for k in required)
        except (ValueError, TypeError, OverflowError):
            _push(findings, 'INVALID_TIMESTAMP', idx)
            continue
        if entry <= signal:
            _push(findings, 'LOOKAHEAD_OR_SAME_BAR_ENTRY', idx)
        if next_open <= signal or entry < next_open:
            _push(findings, 'NEXT_BAR_EXECUTION_VIOLATION', idx)
        if (row.get('stop_hit', '').strip().lower() in ('true', '1', 'yes')
                and row.get('target_hit', '').strip().lower() in ('true', '1', 'yes')):
            _push(findings, 'AMBIGUOUS_SAME_BAR_EXIT', idx, 'WARNING')
    return _base('ledger', findings, len(rows))


def _pf(values):
    gains = sum(x for x in values if x > 0)
    losses = -sum(x for x in values if x < 0)
    if not math.isfinite(gains) or not math.isfinite(losses):
        return None
    return round(gains / losses, 6) if losses and math.isfinite(gains/losses) else None


def _compound_and_drawdown(values):
    equity = peak = 1.0
    worst = 0.0
    for value in values:
        if value <= -1:
            return None, None
        equity *= 1.0 + value
        if not math.isfinite(equity):
            return None, None
        peak = max(peak, equity)
        worst = max(worst, 1.0 - equity / peak)
    return round(equity - 1, 6), round(worst, 6)


def audit_stability(rows, costs=(0, 8, 20)):
    findings, parsed = [], []
    costs = tuple(costs)
    if not costs or len(costs) > 20:
        raise ValueError('invalid cost scenarios')
    for cost in costs:
        if not isinstance(cost, (float, int)) or not math.isfinite(cost) or cost < 0:
            raise ValueError('cost must be finite and non-negative')
    for idx, row in enumerate(rows, start=2):
        try:
            stamp = _time(row['exit_time'])
            ret = _num(row['gross_return'])
            if ret <= -1:
                raise ValueError('return is -100% or less')
        except (KeyError, ValueError, TypeError, OverflowError):
            _push(findings, 'INVALID_TRADE_RETURN', idx)
            continue
        parsed.append((stamp, ret))
    parsed.sort(key=lambda v: v[0])
    if len(parsed) < 30:
        _push(findings, 'LOW_TRADE_COUNT', severity='WARNING')
    if len({(t.year, t.month) for t, _ in parsed}) < 3:
        _push(findings, 'SHORT_TIME_COVERAGE', severity='WARNING')
    metrics = {'interpretation': 'sequential non-overlapping, equal-equity trade proxy; not actual portfolio NAV'}
    if parsed:
        monthly = defaultdict(float)
        for stamp, ret in parsed:
            monthly[(stamp.year, stamp.month)] += ret
        metrics['positive_month_fraction'] = round(sum(x > 0 for x in monthly.values())/len(monthly), 6)
        metrics['excluded_invalid_trades'] = len(rows) - len(parsed)
        for cost in costs:
            net = [ret - cost/10000 for _, ret in parsed]
            compound, mdd = _compound_and_drawdown(net)
            if compound is None:
                _push(findings, 'UNDEFINED_COMPOUNDING_COST_SCENARIO', severity='WARNING')
            metrics[f'cost_{cost:g}bps'] = {
                'trade_count': len(net),
                'win_rate': round(sum(x > 0 for x in net)/len(net), 6),
                'expectancy': round(sum(net)/len(net), 8),
                'profit_factor': _pf(net),
                'compounded_trade_return_proxy': compound,
                'max_drawdown_proxy': mdd,
            }
    else:
        _push(findings, 'NO_VALID_TRADES')
    return _base('stability', findings, len(rows), metrics)
