"""Offline, bounded CSV adapters for *reported* settled trade returns.

These adapters cannot reconstruct signal timing from trade-summary exports.
No source code, pickle, native archives, account IDs, or proprietary data is read.
"""
from __future__ import annotations

import math
from .audit import _time, audit_stability

# All return columns are fractional returns, not percent points.
# backtesting.py ReturnPct / vectorbt Return / Freqtrade profit_ratio.
FORMATS = frozenset(('backtesting-py', 'vectorbt', 'freqtrade-csv'))
REQUIRED = {
    'backtesting-py': ('ExitTime', 'ReturnPct'),
    'vectorbt': ('Exit Timestamp', 'Return', 'Status'),
    'freqtrade-csv': ('close_date', 'profit_ratio', 'is_open'),
}


def audit_imported_trades(rows, framework: str, additional_cost_bps: float = 0):
    """Audit a CSV of already settled trades without copying identity columns.

    - Reported trade return may already incorporate fees and slippage.
    - Additional cost scenarios are *extra stress*, not actual fee estimates.
    - Missing/naive timestamps, open trades, and non-finite returns fail closed.
    """
    if framework not in FORMATS:
        raise ValueError('unsupported framework format')
    if not isinstance(additional_cost_bps, (int, float)) or not math.isfinite(additional_cost_bps) or additional_cost_bps < 0:
        raise ValueError('additional cost must be finite and nonnegative')
    if additional_cost_bps > 10_000:
        raise ValueError('additional cost exceeds 100 percent')
    if not rows:
        raise ValueError('empty import')

    ts_key, ret_key = REQUIRED[framework][:2]
    mapped = []
    for row in rows:
        if any(key not in row or row[key] is None or not str(row[key]).strip() for key in REQUIRED[framework]):
            raise ValueError('missing required framework field')
        # Do not silently convert timezone-naive pandas timestamps to UTC.
        timestamp = _time(row[ts_key])
        try:
            result = float(row[ret_key])
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('invalid reported trade return') from exc
        if not math.isfinite(result) or result <= -1:
            raise ValueError('nonfinite or impossible reported return')
        if framework == 'vectorbt' and row['Status'].strip().casefold() != 'closed':
            raise ValueError('unsettled vectorbt trade not supported')
        if framework == 'freqtrade-csv' and 'is_open' in row:
            state = row['is_open'].strip().casefold()
            if state not in ('false', '0', 'no'):
                raise ValueError('freqtrade open or unknown trade state')
        mapped.append({'exit_time': timestamp.isoformat(), 'gross_return': str(result)})

    scenarios = (0,) if additional_cost_bps == 0 else (0, additional_cost_bps)
    report = audit_stability(mapped, costs=scenarios)
    # The inherited audit API calls its input gross_return, but native exports
    # may *already* be net-of-fees. Never claim a reconstructed gross return.
    report['audit_type'] = 'framework-trades'
    report['metrics']['framework_format'] = framework
    report['metrics']['reported_return_basis'] = 'framework-provided trade return; fee inclusion not independently verified'
    report['metrics']['cost_scenario_interpretation'] = '0bps = unmodified reported return; positive bps = additional hypothetical per-trade drag'
    report['metrics']['signal_timing_verified'] = False
    report['findings'].append({'code': 'SIGNAL_CAUSALITY_NOT_VERIFIED', 'row': None, 'severity': 'WARNING'})
    report['warnings'] += 1
    if report['status'] != 'FAIL':
        report['status'] = 'WARN'
    return report
