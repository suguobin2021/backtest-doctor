"""Synthetic-only adversarial regression checks; never touches production files."""
import io
import json
import random
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory

from backtest_doctor.audit import audit_ohlcv, audit_ledger, read_csv
from backtest_doctor.bundle import audit_bundle
from backtest_doctor.cli import main
from backtest_doctor.report import render_html

HERE = Path(__file__).resolve().parents[1] / 'examples'

class SecurityRegression(unittest.TestCase):
    def test_randomized_invalid_high_low_200_cases(self):
        r = random.Random(20261101)
        for _ in range(200):
            a,b = r.uniform(1,1000),r.uniform(1,1000)
            high,low = max(a,b),min(a,b)
            row={'timestamp':'2026-01-01T00:00:00Z','open':str((high+low)/2),
                 'high':str(low),'low':str(high),'close':str((high+low)/2),'volume':'1'}
            if high==low: continue
            codes={f['code'] for f in audit_ohlcv([row])['findings']}
            self.assertIn('INVALID_CANDLE_GEOMETRY',codes)

    def test_html_escaped_in_bundle_metrics_and_codes(self):
        report = audit_bundle(ohlcv_rows=[],ledger_rows=[],stability_rows=[])
        report['metrics']['poison']='<img src=x onerror=alert(1)>'
        report['findings'][0]['code']='<script>alert(1)</script>'
        rendered=render_html(report)
        self.assertNotIn('<script>',rendered)
        self.assertNotIn('<img src=x',rendered)
        self.assertIn('&lt;script&gt;',rendered)

    def test_read_csv_rejects_binary(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'binary.csv'; p.write_bytes(b'timestamp,open\n\xff,3')
            with self.assertRaises(UnicodeDecodeError): read_csv(p)

    def test_html_second_creation_refused(self):
        with TemporaryDirectory() as d:
            html=Path(d)/'report.html'
            cmd=['ohlcv',str(HERE/'ohlcv_good.csv'),'--html',str(html)]
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                first=main(cmd)
            old=html.read_bytes()
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                second=main(cmd)
            self.assertEqual(first,0)
            self.assertEqual(second,2)
            self.assertEqual(html.read_bytes(),old)

    def test_ledger_never_leaks_extra_sensitive_columns(self):
        secret='SECRET_SAVED_ACCOUNT_EXAMPLE_DO_NOT_PUBLISH'
        rows=[{'signal_bar_close':'bad','entry_time':'bad','next_bar_open':'bad',
               'position_account':secret,'strategy_parameter':secret}]
        report=audit_ledger(rows)
        self.assertNotIn(secret,json.dumps(report)+render_html(report))

    def test_bundle_fail_on_warn(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            code=main(['bundle','--ohlcv-file',str(HERE/'ohlcv_good.csv'),
                        '--ledger-file',str(HERE/'ledger_good.csv'),
                        '--stability-file',str(HERE/'stability_demo.csv'),
                        '--fail-on-warn'])
        self.assertEqual(code,1)

if __name__=='__main__':unittest.main()
