"""Synthetic only; uses zero production data and no external network."""
import io
import json
import os
import stat
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone, timedelta

from backtest_doctor.audit import audit_ohlcv, audit_ledger, audit_stability, read_csv, MAX_FINDINGS
from backtest_doctor.cli import main

GOOD_BAR = {'timestamp':'2026-01-01T00:00:00Z','open':'10','high':'11','low':'9','close':'10','volume':'1'}
GOOD_TRADE = {'exit_time':'2026-01-01T00:00:00Z','gross_return':'0.02'}

class HardeningTests(unittest.TestCase):
    def test_empty_ohlcv_fails(self):
        self.assertEqual(audit_ohlcv([])['status'], 'FAIL')

    def test_empty_ledger_fails(self):
        self.assertEqual(audit_ledger([])['status'], 'FAIL')

    def test_empty_csv_fails_closed(self):
        with TemporaryDirectory() as d:
            f = Path(d)/'empty.csv'
            f.write_text('timestamp,open,high,low,close,volume\n')
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(['ohlcv',str(f)])
            self.assertEqual(code, 1)
            self.assertIn('EMPTY_OHLCV', output.getvalue())

    def test_duplicate_headers_rejected(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'dup.csv'
            p.write_text('timestamp,timestamp,open\n1,2,3\n')
            with self.assertRaises(ValueError):
                read_csv(p)

    def test_malformed_csv_unclosed_quote_rejected(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'bad.csv'
            p.write_text('timestamp,open\n"unfinished,10\n')
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = main(['ohlcv',str(p)])
            self.assertEqual(code, 2)
            self.assertNotIn('unfinished',stderr.getvalue())

    def test_header_extra_column_rejected(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'bad.csv'
            p.write_text('a,b\n1,2,3\n')
            with self.assertRaises(ValueError):
                read_csv(p)

    def test_too_big_file_rejected(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'large.csv'
            with p.open('wb') as f:
                f.truncate(10*1024*1024+1)
            with self.assertRaises(ValueError):
                read_csv(p)

    def test_timezone_normalization_detects_duplicate(self):
        b = GOOD_BAR.copy()
        alt = GOOD_BAR.copy()
        alt['timestamp']='2026-01-01T08:00:00+08:00'
        codes = {f['code'] for f in audit_ohlcv([b,alt])['findings']}
        self.assertIn('DUPLICATE_TIMESTAMP',codes)

    def test_output_symlink_refused(self):
        if os.name == "nt":
            self.skipTest("Windows symlink creation needs an elevated account")
        with TemporaryDirectory() as d:
            target=Path(d)/'protected.txt';target.write_text('KEEP')
            out=Path(d)/'out.html';out.symlink_to(target)
            with redirect_stderr(io.StringIO()),redirect_stdout(io.StringIO()):
                code=main(['ohlcv',str(Path(__file__).resolve().parents[1]/'examples/ohlcv_good.csv'),'--html',str(out)])
            self.assertEqual(code,2)
            self.assertEqual(target.read_text(),'KEEP')

    def test_output_private_permissions(self):
        with TemporaryDirectory() as d:
            out=Path(d)/'result.html'
            with redirect_stdout(io.StringIO()):
                code=main(['ohlcv',str(Path(__file__).resolve().parents[1]/'examples/ohlcv_good.csv'),'--html',str(out)])
            self.assertEqual(code,0)
            if os.name == 'posix':
                self.assertEqual(stat.S_IMODE(out.stat().st_mode),0o600)

    def test_input_report_has_no_sensitive_values(self):
        token='SYNTHETIC_REDACTION_PROBE'
        row=GOOD_BAR.copy();row['open']=token
        r=audit_ohlcv([row]); self.assertNotIn(token,json.dumps(r))

    def test_invalid_interval_fails_closed(self):
        with self.assertRaises(ValueError):audit_ohlcv([GOOD_BAR],0)

    def test_invalid_negative_cost_fails_closed(self):
        with self.assertRaises(ValueError):audit_stability([GOOD_TRADE],costs=(-1,))

    def test_insufficient_stability_evidence_is_warn(self):
        r=audit_stability([GOOD_TRADE])
        self.assertEqual(r['status'],'WARN')
        self.assertIn('LOW_TRADE_COUNT',{x['code'] for x in r['findings']})
        self.assertIn('not actual portfolio NAV',r['metrics']['interpretation'])

    def test_too_large_cost_invalidates_compounding_not_report(self):
        r=audit_stability([GOOD_TRADE],costs=(11000,))
        self.assertIsNone(r['metrics']['cost_11000bps']['compounded_trade_return_proxy'])
        self.assertIn('UNDEFINED_COMPOUNDING_COST_SCENARIO',{x['code'] for x in r['findings']})

    def test_nan_and_infinity_in_returns_fail(self):
        for val in ('NaN','inf','-inf'):
            r=audit_stability([{'exit_time':GOOD_TRADE['exit_time'],'gross_return':val}])
            self.assertEqual(r['status'],'FAIL')

    def test_future_entry_detected(self):
        row={'signal_bar_close':'2026-01-01T00:05:00Z','next_bar_open':'2026-01-01T00:00:00Z','entry_time':'2026-01-01T00:00:00Z'}
        r=audit_ledger([row]);self.assertEqual(r['status'],'FAIL')

    def test_finding_count_bounded(self):
        rows=[dict(GOOD_BAR,open='oops') for _ in range(MAX_FINDINGS+100)]
        r=audit_ohlcv(rows)
        self.assertLessEqual(len(r['findings']),MAX_FINDINGS+1)
        self.assertEqual(r['findings'][-1]['code'],'FINDING_LIMIT_REACHED')

    def test_no_raw_fields_in_report(self):
        r=audit_ledger([{'signal_bar_close':'trade_data_secret','entry_time':'secret_token','next_bar_open':'token'}])
        self.assertNotIn('trade_data_secret',json.dumps(r))
        self.assertNotIn('secret_token',json.dumps(r))

    def test_strict_warning_ci_exit_code(self):
        with TemporaryDirectory() as d:
            f=Path(d)/'trades.csv'
            f.write_text('exit_time,gross_return\n2026-01-01T00:00:00Z,0.02\n')
            out=io.StringIO()
            with redirect_stdout(out):
                code=main(['stability',str(f),'--fail-on-warn'])
            self.assertEqual(code,1)
            self.assertEqual(json.loads(out.getvalue())['status'],'WARN')

    def test_warning_default_exit_code(self):
        with TemporaryDirectory() as d:
            f=Path(d)/'trades.csv'
            f.write_text('exit_time,gross_return\n2026-01-01T00:00:00Z,0.02\n')
            with redirect_stdout(io.StringIO()):
                code=main(['stability',str(f)])
            self.assertEqual(code,0)

    def test_report_schema_and_type(self):
        self.assertEqual(audit_ohlcv([GOOD_BAR])['report_schema_version'],'0.4')
        self.assertEqual(audit_ohlcv([GOOD_BAR])['audit_type'],'ohlcv')

if __name__=='__main__': unittest.main()
