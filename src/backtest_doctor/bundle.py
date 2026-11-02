"""Aggregation of independently audited, local CSV artifacts (never raw data)."""
from __future__ import annotations

from .audit import audit_ohlcv, audit_ledger, audit_stability


def audit_bundle(*, ohlcv_rows, ledger_rows, stability_rows, interval_seconds=None):
    """All three files are required; reports contain only aggregate diagnostics.

    This does not establish independence, sufficient sample size or a genuine edge.
    """
    reports = {
        'ohlcv': audit_ohlcv(ohlcv_rows, interval_seconds=interval_seconds),
        'ledger': audit_ledger(ledger_rows),
        'stability': audit_stability(stability_rows),
    }
    n_error = sum(v['errors'] for v in reports.values())
    n_warn = sum(v['warnings'] for v in reports.values())
    return {
        'report_schema_version': '0.4',
        'audit_type': 'bundle',
        'status': 'FAIL' if n_error else ('WARN' if n_warn else 'PASS'),
        'errors': n_error,
        'warnings': n_warn,
        'rows_examined': sum(v['rows_examined'] for v in reports.values()),
        'findings': [
            {'source': key, 'code': f['code'], 'severity': f['severity'], 'row': f['row']}
            for key, report in reports.items() for f in report['findings']
        ],
        'metrics': {
            'sections': {k: {'status': v['status'], 'errors': v['errors'],
                             'warnings': v['warnings'], 'rows_examined': v['rows_examined']}
                         for k, v in reports.items()},
            'stability': reports['stability']['metrics'],
            'interpretation': 'Independent static audits; passing does not prove causality or profitability',
        },
        'data_policy': 'aggregate-only; no raw inputs included',
    }
